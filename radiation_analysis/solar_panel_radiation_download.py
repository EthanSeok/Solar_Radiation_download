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

        df['baseDate'] = pd.to_datetime(df['baseDate'], format='%Y%m%d')
        df['fcstDate'] = pd.to_datetime(df['fcstDate'], format='%Y%m%d')
        df['regCd'] = reg_cd

        today = df[df['baseDate'] == df['fcstDate']]
        tomorrow = df[df['baseDate'] != df['fcstDate']]
        return today, tomorrow
    else:
        # print(f"Failed to retrieve data for baseDate {base_date}: {response.status_code}")
        return pd.DataFrame(), pd.DataFrame()

def process_weather_data(base_dates, reg_cd, site):
    today_df = pd.DataFrame()
    tomorrow_df = pd.DataFrame()

    for base_date in base_dates:
        today, tomorrow = fetch_forecast_data(base_date, reg_cd)
        today_df = pd.concat([today_df, today], ignore_index=True)
        tomorrow_df = pd.concat([tomorrow_df, tomorrow], ignore_index=True)

    # Select relevant columns
    today_df = today_df[['fcstDate', 'fcstTime', 'srad', 'regCd', 'temp', 'wspd']]
    tomorrow_df = tomorrow_df[['fcstDate', 'fcstTime', 'srad', 'regCd', 'temp', 'wspd']]

    # Convert fcstTime to hh:mm format and fcstDate to datetime
    today_df['fcstTime'] = today_df['fcstTime'].apply(
        lambda x: pd.to_datetime(str(x).zfill(4), format='%H%M').strftime('%H:%M'))
    tomorrow_df['fcstTime'] = tomorrow_df['fcstTime'].apply(
        lambda x: pd.to_datetime(str(x).zfill(4), format='%H%M').strftime('%H:%M'))

    today_df['fcstDate'] = pd.to_datetime(today_df['fcstDate'])
    tomorrow_df['fcstDate'] = pd.to_datetime(tomorrow_df['fcstDate'])

    # Create tm column with timestamp
    today_df['tm'] = today_df.apply(lambda row: pd.to_datetime(f"{row['fcstDate'].strftime('%Y-%m-%d')} {row['fcstTime']}"), axis=1)
    tomorrow_df['tm'] = tomorrow_df.apply(lambda row: pd.to_datetime(f"{row['fcstDate'].strftime('%Y-%m-%d')} {row['fcstTime']}"), axis=1)

    # Rename columns to Korean
    today_df = today_df.rename(columns={'srad': '예측광량', 'regCd': '지역코드', 'temp': '예측온도', 'wspd': '예측풍속'})
    tomorrow_df = tomorrow_df.rename(columns={'srad': '예측광량', 'regCd': '지역코드', 'temp': '예측온도', 'wspd': '예측풍속'})

    today_df['지역명'] = site
    tomorrow_df['지역명'] = site

    return today_df, tomorrow_df


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
    start_date = '2024-06-01'  # 시작 날짜
    end_date = '2024-07-18'  # 종료 날짜
    reg_cd = '4511300000'  # 태양광 발전량 예측 지점코드

    base_dates = pd.date_range(start=start_date, end=end_date).strftime('%Y%m%d')

    output_dir = 'output\cache\maru'
    os.makedirs(output_dir, exist_ok=True)

    all_today_df = pd.DataFrame()
    all_tomorrow_df = pd.DataFrame()

    for date in base_dates:
        today_df, tomorrow_df = process_weather_data([date], reg_cd)
        all_today_df = pd.concat([all_today_df, today_df], ignore_index=True)
        all_tomorrow_df = pd.concat([all_tomorrow_df, tomorrow_df], ignore_index=True)

    save_filtered_data_by_month(all_today_df, output_dir, 'today', reg_cd)
    save_filtered_data_by_month(all_tomorrow_df, output_dir, 'tomorrow', reg_cd)

if __name__ == "__main__":
    main()
