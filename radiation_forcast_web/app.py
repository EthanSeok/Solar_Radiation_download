import streamlit as st
import os
import pandas as pd
from datetime import datetime
import asos_download
import solar_panel_radiation_download
from visualization import visualize_data


def filter_and_save(df, reg_cd, date_col, cache_dir, prefix, process_asos=True):
    if df is None or df.empty:
        # st.warning(f"{prefix} 데이터가 비어 있습니다.")
        return
    df[date_col] = pd.to_datetime(df[date_col])
    df['year_month'] = df[date_col].dt.strftime('%Y_%m')
    for year_month, group in df.groupby('year_month'):
        filename = f"{prefix}_{year_month}_{reg_cd}.csv"
        print(group)
        if process_asos:
            group = asos_download.process_asos_data(group)
        group.to_csv(os.path.join(cache_dir, filename), index=False, encoding='utf-8-sig')


def file_exists_for_month(directory, prefix, reg_cd, year_month):
    filename = f"{prefix}_{year_month}_{reg_cd}.csv"
    return os.path.exists(os.path.join(directory, filename))


def get_last_date_from_file(filepath, date_col):
    df = pd.read_csv(filepath, parse_dates=[date_col])
    return df[date_col].max()


def main():
    st.title("광량 예측 자료 수집 플랫폼")

    tabs = st.tabs(["ASOS & 날씨마루 자료 다운로드", "시각화"])

    today = datetime.today()
    first_day_of_month = today.replace(day=1)

    with tabs[0]:
        st.header("ASOS & 날씨마루 자료 다운로드")
        service_key = st.text_input("기상청 API 서비스키",
                                    value='NUWyH1Kqtd0zBtafgGKfLZdKrkgPFsnd+xCWP3z1mL+MksCGA08gjaNn0Kd2qUrnvtWE8VYexjpnZYAKTUtk0g==')
        start_date = st.date_input("시작 날짜", value=first_day_of_month)
        end_date = st.date_input("종료 날짜", value=today.date())
        stn_ids = st.text_input("기상청 측후소", value='146')
        reg_cd = st.text_input("날씨마루 지점코드", value='4511300000')

        output_dir = 'output'
        cache_dir = os.path.join(output_dir, 'cache', 'ASOS')
        maru_cache_dir = os.path.join(output_dir, 'cache', 'maru')
        os.makedirs(cache_dir, exist_ok=True)
        os.makedirs(maru_cache_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)

        if st.button("자료 다운로드"):
            start_date_str = start_date.strftime('%Y-%m-%d')
            end_date_str = end_date.strftime('%Y-%m-%d')
            asos_df = None
            today_df = None
            tomorrow_df = None

            # ASOS 데이터 다운로드
            asos_file = os.path.join(cache_dir, f'ASOS_{start_date.strftime("%Y_%m")}_{stn_ids}.csv')
            if not os.path.exists(asos_file) or get_last_date_from_file(asos_file, 'tm') < pd.to_datetime(end_date_str):
                asos_df = asos_download.fetch_weather_data(start_date_str, end_date_str, stn_ids, service_key)
                date_col = 'tm'
                filter_and_save(asos_df, stn_ids, date_col, cache_dir, 'ASOS')

            base_dates = pd.date_range(start=start_date, end=end_date).strftime('%Y%m%d')

            # 날씨마루 데이터 다운로드
            today_file = os.path.join(maru_cache_dir, f'today_{start_date.strftime("%Y_%m")}_{reg_cd}.csv')
            tomorrow_file = os.path.join(maru_cache_dir, f'tomorrow_{start_date.strftime("%Y_%m")}_{reg_cd}.csv')

            if (not os.path.exists(today_file) or get_last_date_from_file(today_file, 'fcstDate') < pd.to_datetime(
                    end_date_str)) or (not os.path.exists(tomorrow_file) or get_last_date_from_file(tomorrow_file,
                                                                                                    'fcstDate') < pd.to_datetime(
                    end_date_str)):
                today_df, tomorrow_df = solar_panel_radiation_download.process_weather_data(base_dates, reg_cd)
                filter_and_save(today_df, reg_cd, 'fcstDate', maru_cache_dir, 'today', process_asos=False)
                filter_and_save(tomorrow_df, reg_cd, 'fcstDate', maru_cache_dir, 'tomorrow', process_asos=False)

            st.write("Today 예측 자료")
            if today_df is not None:
                st.write(today_df)
            else:
                # st.warning("Today 데이터가 없습니다.")
                if os.path.exists(today_file):
                    last_today_df = pd.read_csv(today_file)
                    st.write("가장 최근의 Today 데이터")
                    st.write(last_today_df)

            st.write("Tomorrow 예측 자료")
            if tomorrow_df is not None:
                st.write(tomorrow_df)
            else:
                # st.warning("Tomorrow 데이터가 없습니다.")
                if os.path.exists(tomorrow_file):
                    last_tomorrow_df = pd.read_csv(tomorrow_file)
                    st.write("가장 최근의 Tomorrow 데이터")
                    st.write(last_tomorrow_df)

            # 파일 다운로드 버튼
            if today_df is not None:
                for year_month in today_df['year_month'].unique():
                    filename = f'today_{year_month}_{reg_cd}.csv'
                    st.download_button(label=f"Download Today's Forecast Data ({year_month})",
                                       data=today_df[today_df['year_month'] == year_month].to_csv(index=False,
                                                                                                  encoding='utf-8-sig'),
                                       file_name=filename)

            if tomorrow_df is not None:
                for year_month in tomorrow_df['year_month'].unique():
                    filename = f'tomorrow_{year_month}_{reg_cd}.csv'
                    st.download_button(label=f"Download Tomorrow's Forecast Data ({year_month})",
                                       data=tomorrow_df[tomorrow_df['year_month'] == year_month].to_csv(index=False,
                                                                                                        encoding='utf-8-sig'),
                                       file_name=filename)

    with tabs[1]:
        visualize_data(start_date, end_date, stn_ids, reg_cd)


if __name__ == "__main__":
    main()
