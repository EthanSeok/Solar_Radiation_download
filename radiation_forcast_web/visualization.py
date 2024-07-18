import pandas as pd
import streamlit as st
import plotly.graph_objects as go

def visualize_data():
    today_df = pd.read_csv('output/today_df.csv')
    tomorrow_df = pd.read_csv('output/tomorrow_df.csv')

    st.header("시각화")

    # 예측 날짜와 시간 결합
    today_df['timestamp'] = pd.to_datetime(today_df['fcstDate'].astype(str) + ' ' + today_df['fcstTime'],
                                           format='%Y-%m-%d %H:%M')
    tomorrow_df['timestamp'] = pd.to_datetime(tomorrow_df['fcstDate'].astype(str) + ' ' + tomorrow_df['fcstTime'],
                                              format='%Y-%m-%d %H:%M')

    # 날짜 범위 선택
    start_date = st.date_input("그래프 시작 날짜", today_df['timestamp'].min().date())
    end_date = st.date_input("그래프 종료 날짜", today_df['timestamp'].max().date())

    # 선택된 날짜 범위 내의 데이터 필터링
    filtered_today_df = today_df[
        (today_df['timestamp'] >= pd.to_datetime(start_date)) & (today_df['timestamp'] <= pd.to_datetime(end_date))]
    filtered_tomorrow_df = tomorrow_df[
        (tomorrow_df['timestamp'] >= pd.to_datetime(start_date)) & (tomorrow_df['timestamp'] <= pd.to_datetime(end_date))]

    # 그래프 표시 버튼
    if st.button("시각화"):
        # 예측광량 데이터 프레임 병합
        combined_radiation_df = pd.concat([
            filtered_today_df[['timestamp', '예측광량']].assign(day='Today'),
            filtered_tomorrow_df[['timestamp', '예측광량']].assign(day='Tomorrow')
        ])

        # 예측온도 데이터 프레임 병합
        combined_temp_df = pd.concat([
            filtered_today_df[['timestamp', '예측온도']].assign(day='Today'),
            filtered_tomorrow_df[['timestamp', '예측온도']].assign(day='Tomorrow')
        ])

        # 예측풍속 데이터 프레임 병합
        combined_wind_df = pd.concat([
            filtered_today_df[['timestamp', '예측풍속']].assign(day='Today'),
            filtered_tomorrow_df[['timestamp', '예측풍속']].assign(day='Tomorrow')
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
