import requests
import pandas as pd
import json
import os

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
        print(f"Failed to retrieve data for baseDate {base_date}: {response.status_code}")
        return pd.DataFrame(), pd.DataFrame()

def process_weather_data(base_dates, reg_cd):
    today_df = pd.DataFrame()
    tomorrow_df = pd.DataFrame()

    for base_date in base_dates:
        today, tomorrow = fetch_forecast_data(base_date, reg_cd)
        today_df = pd.concat([today_df, today], ignore_index=True)
        tomorrow_df = pd.concat([tomorrow_df, tomorrow], ignore_index=True)

    today_df = today_df[['fcstDate', 'fcstTime', 'srad', 'regCd', 'temp', 'wspd']]
    tomorrow_df = tomorrow_df[['fcstDate', 'fcstTime', 'srad', 'regCd', 'temp', 'wspd']]

    today_df['fcstTime'] = today_df['fcstTime'].apply(
        lambda x: pd.to_datetime(str(x).zfill(4), format='%H%M').strftime('%H:%M'))
    tomorrow_df['fcstTime'] = tomorrow_df['fcstTime'].apply(
        lambda x: pd.to_datetime(str(x).zfill(4), format='%H%M').strftime('%H:%M'))

    today_df['fcstDate'] = pd.to_datetime(today_df['fcstDate'])
    tomorrow_df['fcstDate'] = pd.to_datetime(tomorrow_df['fcstDate'])

    today_df = today_df.rename(columns={'srad':'예측광량', 'regCd':'지역코드', 'temp':'예측온도', 'wspd':'예측풍속'})
    tomorrow_df = tomorrow_df.rename(columns={'srad':'예측광량', 'regCd':'지역코드', 'temp':'예측온도', 'wspd':'예측풍속'})

    return today_df, tomorrow_df

def merge_data(asos, today_df, tomorrow_df):
    asos['날짜'] = pd.to_datetime(asos['날짜'])

    merged_today = pd.merge(asos, today_df, left_on=['날짜', '시간'], right_on=['fcstDate', 'fcstTime'],
                            how='inner').dropna(subset=['일사(MJ/m2)'])
    merged_tomorrow = pd.merge(asos, tomorrow_df, left_on=['날짜', '시간'], right_on=['fcstDate', 'fcstTime'],
                               how='inner').dropna(subset=['일사(MJ/m2)'])

    merged_today['예측광량'] = pd.to_numeric(merged_today['예측광량'], errors='coerce').fillna(0)
    merged_today['예측광량'] = merged_today['예측광량'].apply(lambda x: x * 0.0036)

    merged_tomorrow['예측광량'] = pd.to_numeric(merged_tomorrow['예측광량'], errors='coerce').fillna(0)
    merged_tomorrow['예측광량'] = merged_tomorrow['예측광량'].apply(lambda x: x * 0.0036)

    merged_today = merged_today.drop(columns=['fcstDate', 'fcstTime'])
    merged_tomorrow = merged_tomorrow.drop(columns=['fcstDate', 'fcstTime'])

    return merged_today, merged_tomorrow

def main():
    start_date = '2024-07-13'  # 시작 날짜
    end_date = '2024-07-14'    # 종료 날짜
    reg_cd = '4511300000'      # 태양광 발전량 예측 지점코드

    asos = pd.read_csv('output/weather_data_146.csv')

    base_dates = pd.date_range(start=start_date, end=end_date).strftime('%Y%m%d')
    today_df, tomorrow_df = process_weather_data(base_dates, reg_cd)
    merged_today, merged_tomorrow = merge_data(asos, today_df, tomorrow_df)

    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)
    today_df.to_csv(os.path.join(output_dir, 'today_df.csv'), index=False, encoding='utf-8-sig')
    tomorrow_df.to_csv(os.path.join(output_dir, 'tomorrow_df.csv'), index=False, encoding='utf-8-sig')
    merged_today.to_csv(os.path.join(output_dir, 'merged_today.csv'), index=False, encoding='utf-8-sig')
    merged_tomorrow.to_csv(os.path.join(output_dir, 'merged_tomorrow.csv'), index=False, encoding='utf-8-sig')


if __name__ == "__main__":
    main()
