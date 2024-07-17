import os
import pandas as pd
from asos_download import fetch_weather_data, save_data, process_asos_data
from solar_panel_radiation_download import process_weather_data, merge_data
from visualization import radiation_scatter, radiation_line, temp_scatter, temp_line, wind_scatter, wind_line


def main():
    start_date = '2024-07-01'  # 시작 날짜
    end_date = '2024-07-16'    # 종료 날짜
    stn_ids = '146'            # 기상청 측후소
    reg_cd = '4511300000'  # 태양광 발전량 예측 지점코드

    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    asos_df = fetch_weather_data(start_date, end_date, stn_ids)
    if asos_df is not None:
        asos = process_asos_data(asos_df)
        save_data(asos, stn_ids, output_dir)
    else:
        print("No data fetched.")

    base_dates = pd.date_range(start=start_date, end=end_date).strftime('%Y%m%d')
    today_df, tomorrow_df = process_weather_data(base_dates, reg_cd)
    merged_today, merged_tomorrow = merge_data(asos, today_df, tomorrow_df)

    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    today_df.to_csv(os.path.join(output_dir, 'today_df.csv'), index=False, encoding='utf-8-sig')
    tomorrow_df.to_csv(os.path.join(output_dir, 'tomorrow_df.csv'), index=False, encoding='utf-8-sig')
    merged_today.to_csv(os.path.join(output_dir, 'merged_today.csv'), index=False, encoding='utf-8-sig')
    merged_tomorrow.to_csv(os.path.join(output_dir, 'merged_tomorrow.csv'), index=False, encoding='utf-8-sig')

    fig_output_dir = 'output/figures'
    os.makedirs(fig_output_dir, exist_ok=True)

    # Define the date range
    start_date = '2024-07-12' ## 그래프 시작 날짜
    end_date = '2024-07-15' ## 그래프 종료 날짜

    radiation_scatter(merged_today, merged_tomorrow, fig_output_dir, start_date, end_date)
    temp_scatter(merged_today, merged_tomorrow, fig_output_dir, start_date, end_date)
    radiation_line(merged_today, merged_tomorrow, fig_output_dir, start_date, end_date)
    temp_line(merged_today, merged_tomorrow, fig_output_dir, start_date, end_date)
    wind_scatter(merged_today, merged_tomorrow, fig_output_dir, start_date, end_date)
    wind_line(merged_today, merged_tomorrow, fig_output_dir, start_date, end_date)

if __name__ == "__main__":
    main()
