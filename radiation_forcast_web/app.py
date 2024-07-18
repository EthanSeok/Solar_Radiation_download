import streamlit as st
import os
import pandas as pd
from datetime import datetime
import asos_download
import solar_panel_radiation_download
from visualization import visualize_data


def filter_and_save(df, reg_cd, date_col, maru_cache_dir, prefix):
    df[date_col] = pd.to_datetime(df[date_col])
    df['year_month'] = df[date_col].dt.strftime('%Y_%m')
    for year_month, group in df.groupby('year_month'):
        filename = f"{prefix}_{year_month}_{reg_cd}.csv"
        group.to_csv(os.path.join(maru_cache_dir, filename), index=False, encoding='utf-8-sig')


def main():
    st.title("광량 예측 자료 수집 플랫폼")

    tabs = st.tabs(["ASOS & 날씨마루 자료 다운로드", "시각화"])

    today = datetime.today()
    first_day_of_month = today.replace(day=1)

    with tabs[0]:
        st.header("ASOS & 날씨마루 자료 다운로드")
        service_key = st.text_input("기상청 API 서비스키", value='NUWyH1Kqtd0zBtafgGKfLZdKrkgPFsnd+xCWP3z1mL+MksCGA08gjaNn0Kd2qUrnvtWE8VYexjpnZYAKTUtk0g==')
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
            asos_df = asos_download.fetch_weather_data(start_date_str, end_date_str, stn_ids, service_key)
            base_dates = pd.date_range(start=start_date, end=end_date).strftime('%Y%m%d')
            today_df, tomorrow_df = solar_panel_radiation_download.process_weather_data(base_dates, reg_cd)

            st.write("Today 예측 자료")
            st.write(today_df)
            st.write("Tomorrow 예측 자료")
            st.write(tomorrow_df)

            ## 결과 저장
            filter_and_save(today_df, reg_cd, 'fcstDate', maru_cache_dir, 'today')
            filter_and_save(tomorrow_df, reg_cd, 'fcstDate', maru_cache_dir, 'tomorrow')

            ## 파일 다운로드 버튼
            for year_month in today_df['year_month'].unique():
                filename = f'today_{year_month}_{reg_cd}.csv'
                st.download_button(label=f"Download Today's Forecast Data ({year_month})",
                                   data=today_df[today_df['year_month'] == year_month].to_csv(index=False,
                                                                                              encoding='utf-8-sig'),
                                   file_name=filename)

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
