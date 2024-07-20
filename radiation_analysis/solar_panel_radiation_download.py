import requests
import pandas as pd
import json
import os
from datetime import datetime, timedelta

def fetch_forecast_data(base_date, reg_cd):
    url = "https://bd.kma.go.kr/kma2020/energy/energyGeneration.do"
    params = {
        'baseDate': base_date,
        'fcstTime': 1000,
        'regCd': reg_cd
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.text
        data = json.loads(data)
        result = data['result']
        df = pd.DataFrame(result)

        try:
            df['baseDate'] = pd.to_datetime(df['baseDate'], format='%Y%m%d')
            df['fcstDate'] = pd.to_datetime(df['fcstDate'], format='%Y%m%d')
        except KeyError:
            return pd.DataFrame(), pd.DataFrame()

        df['regCd'] = reg_cd

        today = df[df['baseDate'] == df['fcstDate']]
        tomorrow = df[df['baseDate'] != df['fcstDate']]
        return today, tomorrow
    else:
        return pd.DataFrame(), pd.DataFrame()

def process_weather_data(base_date, reg_cd, site):
    today, tomorrow = fetch_forecast_data(base_date, reg_cd)

    if today.empty and tomorrow.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Select relevant columns
    today = today[['fcstDate', 'fcstTime', 'srad', 'regCd', 'temp', 'wspd']]
    tomorrow = tomorrow[['fcstDate', 'fcstTime', 'srad', 'regCd', 'temp', 'wspd']]

    # Convert fcstTime to hh:mm format and fcstDate to datetime
    today['fcstTime'] = today['fcstTime'].apply(
        lambda x: pd.to_datetime(str(x).zfill(4), format='%H%M').strftime('%H:%M'))
    tomorrow['fcstTime'] = tomorrow['fcstTime'].apply(
        lambda x: pd.to_datetime(str(x).zfill(4), format='%H%M').strftime('%H:%M'))

    today['fcstDate'] = pd.to_datetime(today['fcstDate'])
    tomorrow['fcstDate'] = pd.to_datetime(tomorrow['fcstDate'])

    # Create tm column with timestamp
    today['tm'] = today.apply(lambda row: pd.to_datetime(f"{row['fcstDate'].strftime('%Y-%m-%d')} {row['fcstTime']}"), axis=1)
    tomorrow['tm'] = tomorrow.apply(lambda row: pd.to_datetime(f"{row['fcstDate'].strftime('%Y-%m-%d')} {row['fcstTime']}"), axis=1)

    # Rename columns to Korean
    today = today.rename(columns={'srad': '예측광량', 'regCd': '지역코드', 'temp': '예측온도', 'wspd': '예측풍속'})
    tomorrow = tomorrow.rename(columns={'srad': '예측광량', 'regCd': '지역코드', 'temp': '예측온도', 'wspd': '예측풍속'})

    today['지역명'] = site
    tomorrow['지역명'] = site

    return today, tomorrow

def save_filtered_data_by_month(df, output_dir, prefix, reg_cd):
    df['year'] = df['fcstDate'].dt.year.astype(str)
    df['month'] = df['fcstDate'].dt.month.astype(str).str.zfill(2)

    for (year, month), group in df.groupby(['year', 'month']):
        year_dir = os.path.join(output_dir, prefix, reg_cd, year)
        os.makedirs(year_dir, exist_ok=True)
        file_name = os.path.join(year_dir, f"{month}.csv")

        if os.path.exists(file_name):
            existing_df = pd.read_csv(file_name)
            group = pd.concat([existing_df, group], ignore_index=True)

        group.to_csv(file_name, index=False, encoding='utf-8-sig')
        # print(f"Saved cache: {file_name}")

def main():
    start_date = '2019-03-01'  # 시작 날짜
    end_date = '2019-03-31'  # 종료 날짜
    reg_cd = '4180000000'  # 태양광 발전량 예측 지점코드
    site = '경기도 연천군'

    base_dates = pd.date_range(start=start_date, end=end_date).strftime('%Y%m%d')

    output_dir = 'output/cache/maru'
    os.makedirs(output_dir, exist_ok=True)

    all_today_df = pd.DataFrame()
    all_tomorrow_df = pd.DataFrame()

    for date in base_dates:
        try:
            today_df, tomorrow_df = process_weather_data(date, reg_cd, site)
            all_today_df = pd.concat([all_today_df, today_df], ignore_index=True)
            all_tomorrow_df = pd.concat([all_tomorrow_df, tomorrow_df], ignore_index=True)
        except Exception as e:
            print(f"Error processing date {date}: {e}")
            continue

    save_filtered_data_by_month(all_today_df, output_dir, 'today', reg_cd)
    save_filtered_data_by_month(all_tomorrow_df, output_dir, 'tomorrow', reg_cd)

if __name__ == "__main__":
    main()
