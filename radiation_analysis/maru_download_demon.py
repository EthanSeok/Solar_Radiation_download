import os
import pandas as pd
import time
import random
from tqdm import tqdm
import solar_panel_radiation_download

def preprocess_sitation(stn, reg):
    reg['sido'] = reg['지역명'].str.split(' ').str[0]
    reg['sig'] = reg['지역명'].str.split(' ').str[1].str[:-1]
    station = pd.merge(stn, reg, left_on='지점명', right_on='sig')
    return station

def main():
    stn = pd.read_excel('../assets/지점코드.xlsx')
    reg = pd.read_csv('../assets/태양광 발전 예측_지역번호.csv')
    reg['번호'] = reg['번호'].apply(lambda x: str(x).ljust(10, '0'))

    reg_cds = reg['번호'].unique()
    start_date = '2024-07-01'  # 시작 날짜
    end_date = '2024-07-18'  # 종료 날짜
    base_dates = pd.date_range(start=start_date, end=end_date).strftime('%Y%m%d')

    output_dir = 'output/cache/maru'
    os.makedirs(output_dir, exist_ok=True)

    for reg_cd in reg_cds:
        site = reg[reg['번호'] == reg_cd]['지역명'].values[0]
        for date in tqdm(base_dates):
            try:
                today_df, tomorrow_df = solar_panel_radiation_download.process_weather_data(date, reg_cd, site)

                if not today_df.empty:
                    solar_panel_radiation_download.save_filtered_data_by_month(today_df, output_dir, 'today', reg_cd)
                if not tomorrow_df.empty:
                    solar_panel_radiation_download.save_filtered_data_by_month(tomorrow_df, output_dir, 'tomorrow', reg_cd)

                # 0~10초 사이의 랜덤한 시간 동안 대기
                time.sleep(random.uniform(0, 10))

            except Exception as e:
                print(f"Error processing date {date} for reg_cd {reg_cd}: {e}")
                continue

if __name__ == "__main__":
    main()
