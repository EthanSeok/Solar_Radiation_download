import requests
import pandas as pd
import json
import matplotlib.pyplot as plt
from matplotlib import font_manager, rc
import seaborn as sns
from sklearn.metrics import mean_squared_error, r2_score
import numpy as np
import ssl
import os
from urllib3 import poolmanager
from requests.adapters import HTTPAdapter

# Setting up font for matplotlib
font_path = "C:\\Users\\user\\AppData\\Local\\Microsoft\\Windows\\Fonts\\KoPub Dotum Medium.ttf"
font = font_manager.FontProperties(fname=font_path).get_name()
plt.rcParams['axes.unicode_minus'] = False
rc('font', family=font)


# SSL Adapter for requests
class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)


# Fetch weather data function
def fetch_weather_data(start_date, end_date, stn_ids):
    startDt = start_date.replace('-', '')
    endDt = end_date.replace('-', '')

    url = "https://apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList"
    params = {
        'serviceKey': '4qzg84zn4YqeIJdCdD28W33fT0kE1QLCEOjGnboUpC6fdBchohQUqmANqPCMlj/eRfog6xZdA5lys6kDaf6sPQ==',
        'numOfRows': '720',
        'pageNo': 1,
        'dataType': 'JSON',
        'dataCd': 'ASOS',
        'dateCd': 'HR',
        'startDt': startDt,
        'startHh': '01',
        'endDt': endDt,
        'endHh': '01',
        'stnIds': stn_ids
    }

    session = requests.Session()
    session.mount('https://', SSLAdapter())

    all_data = []
    total_pages = 1

    while params['pageNo'] <= total_pages:
        response = session.get(url, params=params)

        if response.status_code == 200:
            data = response.json()

            items = data['response']['body']['items']['item']
            df = pd.json_normalize(items)
            all_data.append(df)

            if params['pageNo'] == 1:
                total_count = data['response']['body']['totalCount']
                total_pages = (total_count // int(params['numOfRows'])) + (total_count % int(params['numOfRows']) > 0)

            params['pageNo'] += 1
        else:
            print(f"Error: {response.status_code}")
            break

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        return final_df
    else:
        return None


# Save weather data to CSV
def save_data(df, region_code, output_dir):
    df = df[['tm', 'icsr', 'ta', 'ws']]
    filename = os.path.join(output_dir, f"weather_data_{region_code}.csv")
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Saved: {filename}")


# Process ASOS data
def process_asos_data(asos):
    asos['일시'] = pd.to_datetime(asos['tm'], format='%Y-%m-%d %H:%M')
    asos['날짜'] = asos['일시'].dt.date
    asos['시간'] = asos['일시'].dt.strftime('%H:%M')
    asos = asos[['날짜', '시간', 'icsr']]
    asos.rename(columns={'icsr': '일사(MJ/m2)'}, inplace=True)
    return asos


# Fetch and process weather forecast data
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

    today_df = today_df[['fcstDate', 'fcstTime', 'srad']]
    tomorrow_df = tomorrow_df[['fcstDate', 'fcstTime', 'srad']]

    today_df['fcstTime'] = today_df['fcstTime'].apply(
        lambda x: pd.to_datetime(str(x).zfill(4), format='%H%M').strftime('%H:%M'))
    tomorrow_df['fcstTime'] = tomorrow_df['fcstTime'].apply(
        lambda x: pd.to_datetime(str(x).zfill(4), format='%H%M').strftime('%H:%M'))

    today_df['fcstDate'] = pd.to_datetime(today_df['fcstDate'])
    tomorrow_df['fcstDate'] = pd.to_datetime(tomorrow_df['fcstDate'])

    today_df['srad'] = pd.to_numeric(today_df['srad'], errors='coerce')
    tomorrow_df['srad'] = pd.to_numeric(tomorrow_df['srad'], errors='coerce')

    return today_df, tomorrow_df


def merge_data(asos, today_df, tomorrow_df):
    asos['날짜'] = pd.to_datetime(asos['날짜'])

    merged_today = pd.merge(asos, today_df, left_on=['날짜', '시간'], right_on=['fcstDate', 'fcstTime'],
                            how='inner').dropna(subset=['일사(MJ/m2)'])
    merged_tomorrow = pd.merge(asos, tomorrow_df, left_on=['날짜', '시간'], right_on=['fcstDate', 'fcstTime'],
                               how='inner').dropna(subset=['일사(MJ/m2)'])

    merged_today['srad'] = merged_today['srad'].apply(lambda x: x if pd.isna(x) else x * 0.0036)
    merged_tomorrow['srad'] = merged_tomorrow['srad'].apply(lambda x: x if pd.isna(x) else x * 0.0036)

    return merged_today, merged_tomorrow


def calculate_r2_rmse(y_true, y_pred):
    r2 = r2_score(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    return r2, rmse


def visualize(today, tomorrow):
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    sns.regplot(data=today, x='일사(MJ/m2)', y='srad', ax=ax[0], scatter_kws={'s': 50, 'color': 'black', 'alpha': 0.6},
                line_kws={'color': 'red'})
    sns.regplot(data=tomorrow, x='일사(MJ/m2)', y='srad', ax=ax[1], scatter_kws={'s': 50, 'color': 'black', 'alpha': 0.6},
                line_kws={'color': 'red'})

    today_r2, today_rmse = calculate_r2_rmse(today['일사(MJ/m2)'], today['srad'])
    tomorrow_r2, tomorrow_rmse = calculate_r2_rmse(tomorrow['일사(MJ/m2)'], tomorrow['srad'])

    ax[0].set_title(f'Today (R²={today_r2:.2f}, RMSE={today_rmse:.2f})')
    ax[1].set_title(f'Tomorrow (R²={tomorrow_r2:.2f}, RMSE={tomorrow_rmse:.2f})')

    max_value = max(today['일사(MJ/m2)'].max(), tomorrow['일사(MJ/m2)'].max(), today['srad'].max(), tomorrow['srad'].max())

    for a in ax:
        a.set_xlim(0, max_value)
        a.set_ylim(0, max_value)
        a.plot([0, max_value], [0, max_value], ls='--', color='black')
        a.set_aspect('equal', adjustable='box')

    plt.tight_layout()
    plt.show()


def main():
    start_date = '2024-06-01'  # 시작 날짜
    end_date = '2024-07-14'    # 종료 날짜
    stn_ids = '146'            # 기상청 측후소
    reg_cd = '4511300000'      # 태양광 발전량 예측 지점코드

    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    asos_df = fetch_weather_data(start_date, end_date, stn_ids)
    if asos_df is not None:
        save_data(asos_df, stn_ids, output_dir)

    asos = pd.read_csv(f'output/weather_data_{stn_ids}.csv')
    asos = process_asos_data(asos)

    base_dates = pd.date_range(start=start_date, end=end_date).strftime('%Y%m%d')
    today_df, tomorrow_df = process_weather_data(base_dates, reg_cd)
    merged_today, merged_tomorrow = merge_data(asos, today_df, tomorrow_df)
    visualize(merged_today, merged_tomorrow)

    merged_today.to_csv(os.path.join(output_dir, 'merged_today.csv'), index=False, encoding='utf-8-sig')
    merged_tomorrow.to_csv(os.path.join(output_dir, 'merged_tomorrow.csv'), index=False, encoding='utf-8-sig')


if __name__ == "__main__":
    main()