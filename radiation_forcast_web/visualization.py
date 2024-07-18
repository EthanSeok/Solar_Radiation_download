import os
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import statsmodels.api as sm
import streamlit as st
import numpy as np

def save_and_update_data(new_df, filename, output_dir):
    filepath = os.path.join(output_dir, filename)
    if os.path.exists(filepath):
        existing_df = pd.read_csv(filepath)
        combined_df = pd.concat([existing_df, new_df]).drop_duplicates(subset=['fcstDate', 'fcstTime']).reset_index(drop=True)
    else:
        combined_df = new_df

    combined_df.to_csv(filepath, index=False, encoding='utf-8-sig')
    return combined_df

def save_asos_data(asos_df, stn_ids, year, month, output_dir):
    asos_cache_dir = os.path.join(output_dir, 'cache', 'ASOS')
    os.makedirs(asos_cache_dir, exist_ok=True)
    filename = f'ASOS_{stn_ids}_{year}_{month}.csv'
    filepath = os.path.join(asos_cache_dir, filename)
    asos_df.to_csv(filepath, index=False, encoding='utf-8-sig')

def filename_parsing(folder_path):
    maru_today_filenames = []
    maru_tomorrow_filenames = []
    asos_filenames = []

    for filename in os.listdir(folder_path):
        if 'today' in filename:
            maru_today_filenames.append(filename)
        elif 'tomorrow' in filename:
            maru_tomorrow_filenames.append(filename)
        elif 'ASOS' in filename:
            asos_filenames.append(filename)

    return maru_today_filenames, maru_tomorrow_filenames, asos_filenames

def generate_date_range(start_date, end_date):
    # Ensure start_date and end_date are in string format
    start = datetime.strptime(start_date.strftime("%Y-%m-%d"), "%Y-%m-%d")
    end = datetime.strptime(end_date.strftime("%Y-%m-%d"), "%Y-%m-%d")
    date_range = []
    while start <= end:
        date_range.append(start.strftime("%Y_%m"))
        start += timedelta(days=1)
    return list(set(date_range))  # 중복 제거

def file_pattern(asos_folder_path, maru_folder_path, start_date, end_date, stn_ids, reg_cd):
    maru_today_filenames, maru_tomorrow_filenames, _ = filename_parsing(maru_folder_path)
    _, _, asos_filenames = filename_parsing(asos_folder_path)
    date_range = generate_date_range(start_date, end_date)

    filtered_asos = []
    filtered_today = []
    filtered_tomorrow = []

    for date in date_range:
        for filename in asos_filenames:
            if date in filename and stn_ids in filename:
                filtered_asos.append(filename)
        for filename in maru_today_filenames:
            if date in filename and reg_cd in filename:
                filtered_today.append(filename)
        for filename in maru_tomorrow_filenames:
            if date in filename and reg_cd in filename:
                filtered_tomorrow.append(filename)

    return filtered_asos, filtered_today, filtered_tomorrow

def concat_files(folder_path, filenames):
    dfs = []
    for filename in filenames:
        filepath = os.path.join(folder_path, filename)
        df = pd.read_csv(filepath)
        dfs.append(df)
    if dfs:
        return pd.concat(dfs, ignore_index=True)
    else:
        return pd.DataFrame()

def visualize_data(start_date, end_date, stn_ids, reg_cd):
    st.header("시각화")
    start_date = st.date_input("그래프 시작 날짜", value= start_date)
    end_date = st.date_input("그래프 종료 날짜", value= end_date + timedelta(days=2))
    stn_ids = st.text_input("기상청 측후소 번호", value=stn_ids)
    reg_cd = st.text_input("날씨마루 지점 코드", value=reg_cd)

    asos_folder_path = 'output/cache/ASOS'
    maru_folder_path = 'output/cache/maru'

    asos_files, today_files, tomorrow_files = file_pattern(asos_folder_path, maru_folder_path, start_date, end_date, stn_ids, reg_cd)

    asos_df = concat_files(asos_folder_path, asos_files)
    today_df = concat_files(maru_folder_path, today_files)
    tomorrow_df = concat_files(maru_folder_path, tomorrow_files)


    # timestamp 컬럼 생성
    today_df['timestamp'] = pd.to_datetime(today_df['fcstDate'].astype(str) + ' ' + today_df['fcstTime'],
                                           format='%Y-%m-%d %H:%M')
    tomorrow_df['timestamp'] = pd.to_datetime(tomorrow_df['fcstDate'].astype(str) + ' ' + tomorrow_df['fcstTime'],
                                              format='%Y-%m-%d %H:%M')

    today_df = today_df.sort_values(by='timestamp').reset_index(drop=True)
    tomorrow_df = tomorrow_df.sort_values(by='timestamp').reset_index(drop=True)

    today_df = today_df.drop_duplicates(subset=['timestamp'])
    tomorrow_df = tomorrow_df.drop_duplicates(subset=['timestamp'])


    # 선택된 날짜 범위 내의 데이터 필터링
    filtered_today_df = today_df[
        (today_df['timestamp'] >= pd.to_datetime(start_date)) & (today_df['timestamp'] <= pd.to_datetime(end_date))]
    filtered_tomorrow_df = tomorrow_df[
        (tomorrow_df['timestamp'] >= pd.to_datetime(start_date)) & (tomorrow_df['timestamp'] <= pd.to_datetime(end_date))]

    # 선택 옵션 추가
    options = st.multiselect(
        "출력할 그래프 선택",
        ["예측 그래프", "예측 산점도 그래프", "ASOS 비교 그래프", 'ASOS 비교 산점도 그래프']
    )

    # 그래프 표시 버튼
    if st.button("시각화"):
        if "예측 그래프" in options:
            # 예측광량 데이터 프레임 병합
            combined_radiation_df = pd.concat([
                filtered_today_df[['timestamp', '예측광량']].assign(day='Today'),
                filtered_tomorrow_df[['timestamp', '예측광량']].assign(day='Tomorrow')
            ])

            # 예측광량 그래프
            fig_rad = go.Figure()
            fig_rad.add_trace(go.Scatter(x=combined_radiation_df[combined_radiation_df['day'] == 'Today']['timestamp'],
                                         y=combined_radiation_df[combined_radiation_df['day'] == 'Today']['예측광량'],
                                         mode='lines',
                                         name='Today',
                                         line=dict(color='#FFD700')))
            fig_rad.add_trace(go.Scatter(x=combined_radiation_df[combined_radiation_df['day'] == 'Tomorrow']['timestamp'],
                                         y=combined_radiation_df[combined_radiation_df['day'] == 'Tomorrow']['예측광량'],
                                         mode='lines',
                                         name='Tomorrow',
                                         line=dict(color='#FFA500', dash='dash')))
            fig_rad.update_layout(title='예측광량', xaxis_title='Timestamp', yaxis_title='Radiation')
            st.plotly_chart(fig_rad)

            # 예측온도 데이터 프레임 병합
            combined_temp_df = pd.concat([
                filtered_today_df[['timestamp', '예측온도']].assign(day='Today'),
                filtered_tomorrow_df[['timestamp', '예측온도']].assign(day='Tomorrow')
            ])

            # 예측온도 그래프
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(x=combined_temp_df[combined_temp_df['day'] == 'Today']['timestamp'],
                                          y=combined_temp_df[combined_temp_df['day'] == 'Today']['예측온도'],
                                          mode='lines',
                                          name='Today',
                                          line=dict(color='#FF6347')))
            fig_temp.add_trace(go.Scatter(x=combined_temp_df[combined_temp_df['day'] == 'Tomorrow']['timestamp'],
                                          y=combined_temp_df[combined_temp_df['day'] == 'Tomorrow']['예측온도'],
                                          mode='lines',
                                          name='Tomorrow',
                                          line=dict(color='#FF4500', dash='dash')))
            fig_temp.update_layout(title='예측온도', xaxis_title='Timestamp', yaxis_title='Temperature')
            st.plotly_chart(fig_temp)

            # 예측풍속 데이터 프레임 병합
            combined_wind_df = pd.concat([
                filtered_today_df[['timestamp', '예측풍속']].assign(day='Today'),
                filtered_tomorrow_df[['timestamp', '예측풍속']].assign(day='Tomorrow')
            ])

            # 예측풍속 그래프
            fig_wind = go.Figure()
            fig_wind.add_trace(go.Scatter(x=combined_wind_df[combined_wind_df['day'] == 'Today']['timestamp'],
                                          y=combined_wind_df[combined_wind_df['day'] == 'Today']['예측풍속'],
                                          mode='lines',
                                          name='Today',
                                          line=dict(color='#1E90FF')))
            fig_wind.add_trace(go.Scatter(x=combined_wind_df[combined_wind_df['day'] == 'Tomorrow']['timestamp'],
                                          y=combined_wind_df[combined_wind_df['day'] == 'Tomorrow']['예측풍속'],
                                          mode='lines',
                                          name='Tomorrow',
                                          line=dict(color='#4169E1', dash='dash')))
            fig_wind.update_layout(title='예측풍속', xaxis_title='Timestamp', yaxis_title='Wind Speed')
            st.plotly_chart(fig_wind)

        if "예측 산점도 그래프" in options:
            # 예측 광량 산점도
            merge_radiation_df = pd.merge(
                filtered_today_df[['timestamp', '예측광량']].assign(day='Today'),
                filtered_tomorrow_df[['timestamp', '예측광량']].assign(day='Tomorrow'),
                how='inner', on=['timestamp'], suffixes=('_Today', '_Tomorrow')
            )

            today_data = merge_radiation_df['예측광량_Today']
            tomorrow_data = merge_radiation_df['예측광량_Tomorrow']

            # 선형 회귀 모델 적합
            X = sm.add_constant(tomorrow_data)  # 독립 변수에 상수 추가
            model = sm.OLS(today_data, X).fit()

            # R² 값과 RMSE 계산
            r_squared = model.rsquared
            rmse = np.sqrt(model.mse_resid)

            # 산점도 플롯 생성
            fig_rad_scatter = go.Figure()
            fig_rad_scatter.add_trace(go.Scatter(
                x=tomorrow_data,
                y=today_data,
                mode='markers',
                name='Data'
            ))

            # 추세선 추가
            fig_rad_scatter.add_trace(go.Scatter(
                x=tomorrow_data,
                y=model.predict(X),
                mode='lines',
                line=dict(color='red'),
                name=f'Trendline (R²={r_squared:.2f}, RMSE={rmse:.2f})'
            ))

            # 레이아웃 업데이트 (1:1 비율로 설정)
            fig_rad_scatter.update_layout(
                title='Today 와 Tomorrow 예측광량 비교',
                xaxis_title='Tomorrow 예측광량',
                yaxis_title='Today 예측광량',
                xaxis=dict(scaleanchor="y", scaleratio=1),
                yaxis=dict(scaleanchor="x", scaleratio=1)
            )

            # Plotly 차트 표시
            st.plotly_chart(fig_rad_scatter)

            # 예측 온도 산점도
            merge_temp_df = pd.merge(
                filtered_today_df[['timestamp', '예측온도']].assign(day='Today'),
                filtered_tomorrow_df[['timestamp', '예측온도']].assign(day='Tomorrow'),
                how='inner', on=['timestamp'], suffixes=('_Today', '_Tomorrow')
            )

            today_data = merge_temp_df['예측온도_Today']
            tomorrow_data = merge_temp_df['예측온도_Tomorrow']

            # 선형 회귀 모델 적합
            X = sm.add_constant(tomorrow_data)  # 독립 변수에 상수 추가
            model = sm.OLS(today_data, X).fit()

            # R² 값과 RMSE 계산
            r_squared = model.rsquared
            rmse = np.sqrt(model.mse_resid)

            # 산점도 플롯 생성
            fig_temp_scatter = go.Figure()
            fig_temp_scatter.add_trace(go.Scatter(
                x=tomorrow_data,
                y=today_data,
                mode='markers',
                name='Data'
            ))

            # 추세선 추가
            fig_temp_scatter.add_trace(go.Scatter(
                x=tomorrow_data,
                y=model.predict(X),
                mode='lines',
                line=dict(color='red'),
                name=f'Trendline (R²={r_squared:.2f}, RMSE={rmse:.2f})'
            ))

            # 레이아웃 업데이트 (1:1 비율로 설정)
            fig_temp_scatter.update_layout(
                title='Today 와 Tomorrow 예측온도 비교',
                xaxis_title='Tomorrow 예측온도',
                yaxis_title='Today 예측온도',
                xaxis=dict(scaleanchor="y", scaleratio=1),
                yaxis=dict(scaleanchor="x", scaleratio=1)
            )

            # Plotly 차트 표시
            st.plotly_chart(fig_temp_scatter)

            # 예측 풍속 산점도
            merge_wind_df = pd.merge(
                filtered_today_df[['timestamp', '예측풍속']].assign(day='Today'),
                filtered_tomorrow_df[['timestamp', '예측풍속']].assign(day='Tomorrow'),
                how='inner', on=['timestamp'], suffixes=('_Today', '_Tomorrow')
            )

            today_data = merge_wind_df['예측풍속_Today']
            tomorrow_data = merge_wind_df['예측풍속_Tomorrow']

            # 선형 회귀 모델 적합
            X = sm.add_constant(tomorrow_data)  # 독립 변수에 상수 추가
            model = sm.OLS(today_data, X).fit()

            # R² 값과 RMSE 계산
            r_squared = model.rsquared
            rmse = np.sqrt(model.mse_resid)

            # 산점도 플롯 생성
            fig_wind_scatter = go.Figure()
            fig_wind_scatter.add_trace(go.Scatter(
                x=tomorrow_data,
                y=today_data,
                mode='markers',
                name='Data'
            ))

            # 추세선 추가
            fig_wind_scatter.add_trace(go.Scatter(
                x=tomorrow_data,
                y=model.predict(X),
                mode='lines',
                line=dict(color='red'),
                name=f'Trendline (R²={r_squared:.2f}, RMSE={rmse:.2f})'
            ))

            # 레이아웃 업데이트 (1:1 비율로 설정)
            fig_wind_scatter.update_layout(
                title='Today 와 Tomorrow 예측풍속 비교',
                xaxis_title='Tomorrow 예측풍속',
                yaxis_title='Today 예측풍속',
                xaxis=dict(scaleanchor="y", scaleratio=1),
                yaxis=dict(scaleanchor="x", scaleratio=1)
            )

            # Plotly 차트 표시
            st.plotly_chart(fig_wind_scatter)

        if "ASOS 비교 그래프" in options:
            # 예측광량 데이터 프레임 병합
            combined_radiation_df = pd.concat([
                filtered_today_df[['timestamp', '예측광량']].assign(day='Today'),
                filtered_tomorrow_df[['timestamp', '예측광량']].assign(day='Tomorrow')
            ])

            combined_radiation_df['예측광량'] = combined_radiation_df['예측광량'] * 0.0036

            # 예측광량 그래프
            fig_rad = go.Figure()
            fig_rad.add_trace(go.Scatter(x=asos_df['tm'],
                                        y=asos_df['일사(MJ/m2)'],
                                        mode='lines',
                                        name='ASOS',
                                        line=dict(color='#FF4000')))

            fig_rad.add_trace(go.Scatter(x=combined_radiation_df[combined_radiation_df['day'] == 'Today']['timestamp'],
                                         y=combined_radiation_df[combined_radiation_df['day'] == 'Today']['예측광량'],
                                         mode='lines',
                                         name='Today',
                                         line=dict(color='#FFD700')))
            fig_rad.add_trace(
                go.Scatter(x=combined_radiation_df[combined_radiation_df['day'] == 'Tomorrow']['timestamp'],
                           y=combined_radiation_df[combined_radiation_df['day'] == 'Tomorrow']['예측광량'],
                           mode='lines',
                           name='Tomorrow',
                           line=dict(color='#FFA500', dash='dash')))

            fig_rad.update_layout(title='일사(MJ/m2)', xaxis_title='Timestamp', yaxis_title='Radiation')
            st.plotly_chart(fig_rad)


            # 예측온도 데이터 프레임 병합
            combined_temp_df = pd.concat([
                filtered_today_df[['timestamp', '예측온도']].assign(day='Today'),
                filtered_tomorrow_df[['timestamp', '예측온도']].assign(day='Tomorrow')
            ])

            # 예측온도 그래프
            fig_temp = go.Figure()
            fig_temp.add_trace(go.Scatter(x=asos_df['tm'],
                                          y=asos_df['온도'],
                                          mode='lines',
                                          name='Today',
                                          line=dict(color='#FFBF00')))
            fig_temp.add_trace(go.Scatter(x=combined_temp_df[combined_temp_df['day'] == 'Today']['timestamp'],
                                          y=combined_temp_df[combined_temp_df['day'] == 'Today']['예측온도'],
                                          mode='lines',
                                          name='Today',
                                          line=dict(color='#FF6347')))
            fig_temp.add_trace(go.Scatter(x=combined_temp_df[combined_temp_df['day'] == 'Tomorrow']['timestamp'],
                                          y=combined_temp_df[combined_temp_df['day'] == 'Tomorrow']['예측온도'],
                                          mode='lines',
                                          name='Tomorrow',
                                          line=dict(color='#FF4500', dash='dash')))
            fig_temp.update_layout(title='예측온도', xaxis_title='Timestamp', yaxis_title='Temperature')
            st.plotly_chart(fig_temp)


            # 예측풍속 데이터 프레임 병합
            combined_wind_df = pd.concat([
                filtered_today_df[['timestamp', '예측풍속']].assign(day='Today'),
                filtered_tomorrow_df[['timestamp', '예측풍속']].assign(day='Tomorrow')
            ])

            # 예측풍속 그래프
            fig_wind = go.Figure()
            fig_wind.add_trace(go.Scatter(x=asos_df['tm'],
                                          y=asos_df['풍속'],
                                          mode='lines',
                                          name='Today',
                                          line=dict(color='#A4A4A4')))
            fig_wind.add_trace(go.Scatter(x=combined_wind_df[combined_wind_df['day'] == 'Today']['timestamp'],
                                          y=combined_wind_df[combined_wind_df['day'] == 'Today']['예측풍속'],
                                          mode='lines',
                                          name='Today',
                                          line=dict(color='#1E90FF')))
            fig_wind.add_trace(go.Scatter(x=combined_wind_df[combined_wind_df['day'] == 'Tomorrow']['timestamp'],
                                          y=combined_wind_df[combined_wind_df['day'] == 'Tomorrow']['예측풍속'],
                                          mode='lines',
                                          name='Tomorrow',
                                          line=dict(color='#4169E1', dash='dash')))
            fig_wind.update_layout(title='예측풍속', xaxis_title='Timestamp', yaxis_title='Wind Speed')
            st.plotly_chart(fig_wind)

        if "ASOS 비교 산점도 그래프" in options:
            # 예측 광량 산점도
            filtered_today_df['timestamp'] = pd.to_datetime(filtered_today_df['timestamp'])
            filtered_tomorrow_df['timestamp'] = pd.to_datetime(filtered_tomorrow_df['timestamp'])
            asos_df['tm'] = pd.to_datetime(asos_df['tm'])

            merge_radiation_df = pd.merge(
                filtered_today_df[['timestamp', '예측광량']].assign(day='Today'),
                filtered_tomorrow_df[['timestamp', '예측광량']].assign(day='Tomorrow'),
                how='inner', on=['timestamp'], suffixes=('_Today', '_Tomorrow')
            )

            merge_radiation_df = pd.merge(merge_radiation_df, asos_df[['tm', '일사(MJ/m2)']], left_on='timestamp',
                                          right_on='tm', how='inner')
            merge_radiation_df['예측광량_Today'] = merge_radiation_df['예측광량_Today'] * 0.0036
            merge_radiation_df['예측광량_Tomorrow'] = merge_radiation_df['예측광량_Tomorrow'] * 0.0036


            today_data = merge_radiation_df['예측광량_Today']
            asos = merge_radiation_df['일사(MJ/m2)']

            # 선형 회귀 모델 적합
            X = sm.add_constant(asos)  # 독립 변수에 상수 추가
            model = sm.OLS(today_data, X).fit()

            # R² 값과 RMSE 계산
            r_squared = model.rsquared
            rmse = np.sqrt(model.mse_resid)

            # 산점도 플롯 생성
            fig_rad_scatter = go.Figure()
            fig_rad_scatter.add_trace(go.Scatter(
                x=asos,
                y=today_data,
                mode='markers',
                name='Data'
            ))

            # 추세선 추가
            fig_rad_scatter.add_trace(go.Scatter(
                x=asos,
                y=model.predict(X),
                mode='lines',
                line=dict(color='red'),
                name=f'Trendline (R²={r_squared:.2f}, RMSE={rmse:.2f})'
            ))

            # 레이아웃 업데이트 (1:1 비율로 설정)
            fig_rad_scatter.update_layout(
                title='Today 와 ASOS 광량 비교',
                xaxis_title='ASOS 광량',
                yaxis_title='Today 예측광량',
                xaxis=dict(scaleanchor="y", scaleratio=1),
                yaxis=dict(scaleanchor="x", scaleratio=1)
            )

            # Plotly 차트 표시
            st.plotly_chart(fig_rad_scatter)

            # 예측 광량 산점도
            filtered_today_df['timestamp'] = pd.to_datetime(filtered_today_df['timestamp'])
            filtered_tomorrow_df['timestamp'] = pd.to_datetime(filtered_tomorrow_df['timestamp'])
            asos_df['tm'] = pd.to_datetime(asos_df['tm'])

            merge_radiation_df = pd.merge(
                filtered_today_df[['timestamp', '예측광량']].assign(day='Today'),
                filtered_tomorrow_df[['timestamp', '예측광량']].assign(day='Tomorrow'),
                how='inner', on=['timestamp'], suffixes=('_Today', '_Tomorrow')
            )

            merge_radiation_df = pd.merge(merge_radiation_df, asos_df[['tm', '일사(MJ/m2)']], left_on='timestamp',
                                          right_on='tm', how='inner')
            merge_radiation_df['예측광량_Today'] = merge_radiation_df['예측광량_Today'] * 0.0036
            merge_radiation_df['예측광량_Tomorrow'] = merge_radiation_df['예측광량_Tomorrow'] * 0.0036


            Tomorrow_data = merge_radiation_df['예측광량_Tomorrow']
            asos = merge_radiation_df['일사(MJ/m2)']

            # 선형 회귀 모델 적합
            X = sm.add_constant(asos)  # 독립 변수에 상수 추가
            model = sm.OLS(today_data, X).fit()

            # R² 값과 RMSE 계산
            r_squared = model.rsquared
            rmse = np.sqrt(model.mse_resid)

            # 산점도 플롯 생성
            fig_rad_scatter = go.Figure()
            fig_rad_scatter.add_trace(go.Scatter(
                x=asos,
                y=Tomorrow_data,
                mode='markers',
                name='Data'
            ))

            # 추세선 추가
            fig_rad_scatter.add_trace(go.Scatter(
                x=asos,
                y=model.predict(X),
                mode='lines',
                line=dict(color='red'),
                name=f'Trendline (R²={r_squared:.2f}, RMSE={rmse:.2f})'
            ))

            # 레이아웃 업데이트 (1:1 비율로 설정)
            fig_rad_scatter.update_layout(
                title='Tomorrow 와 ASOS 광량 비교',
                xaxis_title='ASOS 광량',
                yaxis_title='Tomorrow 예측광량',
                xaxis=dict(scaleanchor="y", scaleratio=1),
                yaxis=dict(scaleanchor="x", scaleratio=1)
            )

            # Plotly 차트 표시
            st.plotly_chart(fig_rad_scatter)

# if __name__ == "__main__":
#     visualize_data()
