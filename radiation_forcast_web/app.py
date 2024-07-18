import streamlit as st
import os
import pandas as pd
from datetime import datetime
import asos_download
import solar_panel_radiation_download
from visualization import visualize_data

def main():
    st.title("광량 예측 자료 수집 플랫폼")

    tabs = st.tabs(["ASOS & 날씨마루 자료 다운로드", "시각화"])

    today = datetime.today()
    first_day_of_month = today.replace(day=1)

    with tabs[0]:
        st.header("ASOS & 날씨마루 자료 다운로드")
        service_key = st.text_input("기상청 API 서비스키")
        start_date = st.date_input("시작 날짜", value=first_day_of_month)
        end_date = st.date_input("종료 날짜", value=today.date())
        stn_ids = st.text_input("기상청 측후소", value='146')
        reg_cd = st.text_input("날씨마루 지점코드", value='4511300000')

        output_dir = 'output'
        cache_dir = os.path.join(output_dir, 'cache', 'ASOS')
        os.makedirs(cache_dir, exist_ok=True)
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
            today_df.to_csv(os.path.join(output_dir, 'today_df.csv'), index=False, encoding='utf-8-sig')
            tomorrow_df.to_csv(os.path.join(output_dir, 'tomorrow_df.csv'), index=False, encoding='utf-8-sig')

            ## 파일 다운로드 버튼
            st.download_button(label="Download Today's Forecast Data",
                               data=today_df.to_csv(index=False, encoding='utf-8-sig'), file_name='today_df.csv')
            st.download_button(label="Download Tomorrow's Forecast Data",
                               data=tomorrow_df.to_csv(index=False, encoding='utf-8-sig'),
                               file_name='tomorrow_df.csv')

            if asos_df is not None:
                asos_df = asos_download.process_asos_data(asos_df)
                asos_download.save_data(asos_df, stn_ids, cache_dir)
                asos_download.cache_to_final(stn_ids, cache_dir, output_dir)
                merged_today, merged_tomorrow = solar_panel_radiation_download.merge_data(asos_df, today_df, tomorrow_df)

                st.write("ASOS & 날씨마루 Today")
                st.write(merged_today)
                st.write("ASOS & 날씨마루 Tomorrow")
                st.write(merged_tomorrow)

                ## 결과 저장
                merged_today.to_csv(os.path.join(output_dir, 'merged_today.csv'), index=False, encoding='utf-8-sig')
                merged_tomorrow.to_csv(os.path.join(output_dir, 'merged_tomorrow.csv'), index=False,
                                       encoding='utf-8-sig')
                ## 파일 다운로드 버튼
                st.download_button(label="Download Merged Today's Data",
                                   data=merged_today.to_csv(index=False, encoding='utf-8-sig'),
                                   file_name='merged_today.csv')
                st.download_button(label="Download Merged Tomorrow's Data",
                                   data=merged_tomorrow.to_csv(index=False, encoding='utf-8-sig'),
                                   file_name='merged_tomorrow.csv')
            else:
                st.write("...")

    with tabs[1]:
        visualize_data()

if __name__ == "__main__":
    main()
