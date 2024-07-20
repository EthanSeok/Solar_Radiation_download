import os
import pandas as pd
import time
import random
from datetime import datetime, timedelta
from tqdm import tqdm
import solar_panel_radiation_download


def preprocess_sitation(stn, reg):
    reg['sido'] = reg['지역명'].str.split(' ').str[0]
    reg['sig'] = reg['지역명'].str.split(' ').str[1].str[:-1]

    station = pd.merge(stn, reg, left_on='지점명', right_on='sig')
    return station


def file_exists(output_dir, prefix, reg_cd, year, month):
    year_dir = os.path.join(output_dir, 'cache', 'maru', prefix, str(reg_cd), year)
    file_name = os.path.join(year_dir, f"{month}.csv")
    file_exists = os.path.exists(file_name)
    print(f"Checking if file exists: {file_name} - Exists: {file_exists}")
    if not file_exists:
        if os.path.exists(year_dir):
            print(f"Directory listing for {year_dir}: {os.listdir(year_dir)}")
        else:
            print(f"Directory {year_dir} does not exist")
    return file_exists


def main():
    stn = pd.read_excel('../assets/지점코드.xlsx')
    reg = pd.read_csv('../assets/태양광 발전 예측_지역번호.csv')
    reg['번호'] = reg['번호'].apply(lambda x: str(x).ljust(10, '0'))

    start_date = '2019-01-01'  # 시작 날짜
    end_date = '2024-07-17'  # 종료 날짜

    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    # 월별 날짜 범위를 생성
    base_dates = pd.date_range(start=start_date, end=end_date, freq='MS').strftime('%Y-%m')

    for reg_cd in tqdm(reg['번호'].unique(), desc="MARU Data Download"):
        site = reg[reg['번호'] == reg_cd]['지역명'].iloc[0]
        for year_month in base_dates:
            year, month = year_month.split('-')

            if file_exists(output_dir, 'today', reg_cd, year, month):
                print(f"Skipping MARU 'today' data for region {reg_cd} for {year_month}")
            else:
                try:
                    start_of_month = f"{year_month}-01"
                    end_of_month = (datetime.strptime(start_of_month, '%Y-%m-%d') + pd.offsets.MonthEnd(1)).strftime(
                        '%Y-%m-%d')
                    date_range = pd.date_range(start=start_of_month, end=end_of_month).strftime('%Y%m%d')
                    today_df, _ = solar_panel_radiation_download.process_weather_data(date_range, reg_cd, site)
                    solar_panel_radiation_download.save_filtered_data_by_month(today_df,
                                                                               os.path.join(output_dir, 'cache',
                                                                                            'maru'), 'today', reg_cd)
                except KeyError as e:
                    print(f"Skipping 'today' date {date_range} for region {reg_cd} due to KeyError: {e}")
                    pass

            # Check for 'tomorrow' data
            if file_exists(output_dir, 'tomorrow', reg_cd, year, month):
                print(f"Skipping MARU 'tomorrow' data for region {reg_cd} for {year_month}")
            else:
                try:
                    _, tomorrow_df = solar_panel_radiation_download.process_weather_data(date_range, reg_cd, site)
                    solar_panel_radiation_download.save_filtered_data_by_month(tomorrow_df,
                                                                               os.path.join(output_dir, 'cache',
                                                                                            'maru'), 'tomorrow', reg_cd)
                except KeyError as e:
                    print(f"Skipping 'tomorrow' date {date_range} for region {reg_cd} due to KeyError: {e}")
                    pass

            time.sleep(random.uniform(0, 8))


if __name__ == "__main__":
    main()
