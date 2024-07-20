import os
import pandas as pd
import time
import random
from datetime import datetime, timedelta
import asos_download
from tqdm import tqdm
import json

def preprocess_sitation(stn, reg):
    reg['sido'] = reg['지역명'].str.split(' ').str[0]
    reg['sig'] = reg['지역명'].str.split(' ').str[1].str[:-1]

    station = pd.merge(stn, reg, left_on='지점명', right_on='sig')
    return station

def file_exists(output_dir, reg_cd, year, month):
    year_dir = os.path.join(output_dir, str(reg_cd), year)
    file_name = os.path.join(year_dir, f"{month}.csv")
    file_exists = os.path.exists(file_name)
    print(f"Checking if file exists: {file_name} - Exists: {file_exists}")
    if not file_exists:
        print(f"Directory listing for {year_dir}: {os.listdir(year_dir) if os.path.exists(year_dir) else 'Directory does not exist'}")
    return file_exists

def fetch_data_with_retry(start_date, end_date, stn_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            asos_df = asos_download.fetch_weather_data(start_date.strftime('%Y-%m-%d'),
                                                       end_date.strftime('%Y-%m-%d'), stn_id)
            return asos_df
        except json.JSONDecodeError as e:
            print(f"JSON decode error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                wait_time = random.uniform(5, 15)
                print(f"Retrying after {wait_time} seconds...")
                time.sleep(wait_time)
            else:
                print("Max retries reached. Skipping this period.")
                return None

def main():
    stn = pd.read_excel('../assets/지점코드.xlsx')
    reg = pd.read_csv('../assets/태양광 발전 예측_지역번호.csv')

    start_date = '2019-01-01'  # 시작 날짜
    end_date = '2024-07-17'  # 종료 날짜

    station = preprocess_sitation(stn, reg)

    output_dir = 'output'
    asos_cache_dir = os.path.join(output_dir, 'cache', 'ASOS')
    os.makedirs(asos_cache_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')
    today = datetime.today().strftime('%Y-%m')

    for stn_id in tqdm(station['지점코드'].unique(), desc="ASOS Data Download"):
        current_date = start_date_obj
        while current_date <= end_date_obj:
            year_month = current_date.strftime('%Y-%m')
            next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
            fetch_end_date = min(end_date_obj, next_month - timedelta(days=1))

            # Skip already downloaded data
            if file_exists(asos_cache_dir, stn_id, year_month[:4], year_month[5:7]):
                print(f"Skipping ASOS data for station {stn_id} for {year_month}")
                current_date = next_month
                continue

            # Fetch ASOS data with retry logic
            asos_df = fetch_data_with_retry(current_date, fetch_end_date, stn_id)
            if asos_df is not None:
                asos_df = asos_download.process_asos_data(asos_df)
                asos_download.save_data(asos_df, stn_id, asos_cache_dir)
            else:
                print(f"No data fetched for period: {current_date.strftime('%Y-%m-%d')} to {fetch_end_date.strftime('%Y-%m-%d')} for station {stn_id}")

            # Sleep to prevent API overload
            time.sleep(random.uniform(5, 15))

            current_date = next_month

    # Move cache to final output for ASOS data
    for stn_id in tqdm(station['지점코드'].unique(), desc="ASOS Data Finalizing"):
        asos_download.cache_to_final(stn_id, asos_cache_dir, output_dir)

if __name__ == "__main__":
    main()
