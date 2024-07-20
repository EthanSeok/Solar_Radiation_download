import requests
import pandas as pd
import os
import ssl
from requests.adapters import HTTPAdapter
from datetime import datetime, timedelta
from tqdm import tqdm


class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)


def fetch_weather_data(start_date, end_date, stn_ids):
    startDt = start_date.replace('-', '')
    endDt = end_date.replace('-', '')

    url = "https://apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList"
    params = {
        'serviceKey': 'NUWyH1Kqtd0zBtafgGKfLZdKrkgPFsnd+xCWP3z1mL+MksCGA08gjaNn0Kd2qUrnvtWE8VYexjpnZYAKTUtk0g==',
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

            if 'body' not in data['response'] or 'items' not in data['response']['body']:
                print("No data available for the given dates.")
                return None

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


def save_data(df, region_code, cache_dir):
    df['year'] = pd.to_datetime(df['tm']).dt.year.astype(str)
    df['month'] = pd.to_datetime(df['tm']).dt.month.astype(str).str.zfill(2)

    for (year, month), group in df.groupby(['year', 'month']):
        year_month_dir = os.path.join(cache_dir, str(region_code), year)
        os.makedirs(year_month_dir, exist_ok=True)
        filename = os.path.join(year_month_dir, f"{month}.csv")
        group.to_csv(filename, index=False, encoding='utf-8-sig')
        # print(f"Saved cache: {filename}")


def cache_to_final(region_code, cache_dir, output_dir):
    current_year_month = datetime.now().strftime('%Y_%m')
    cached_files = [os.path.join(root, f)
                    for root, _, files in os.walk(cache_dir)
                    for f in files if f.startswith(f"{region_code}") and not f"_{current_year_month}.csv" in f]
    all_data = []

    for file in cached_files:
        df = pd.read_csv(file)
        all_data.append(df)


def process_asos_data(asos):
    asos = asos.copy()
    asos['일시'] = pd.to_datetime(asos['tm'], format='%Y-%m-%d %H:%M')
    asos['날짜'] = asos['일시'].dt.date
    asos['시간'] = asos['일시'].dt.strftime('%H:%M')
    asos['icsr'] = asos['icsr'].replace('', 0)
    asos = asos[['stnNm', '날짜', '시간', 'icsr', 'ta', 'ws', 'tm']]
    asos.rename(columns={'icsr': '일사(MJ/m2)', 'stnNm': '지점', 'ta': '온도', 'ws': '풍속'}, inplace=True)
    return asos


def main():
    start_date = '2024-06-01'  # 시작 날짜
    end_date = '2024-07-17'  # 종료 날짜
    stn_ids = '146'  # 기상청 측후소

    output_dir = 'output'
    cache_dir = os.path.join(output_dir, 'cache', 'ASOS')
    os.makedirs(cache_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    start_date_obj = datetime.strptime(start_date, '%Y-%m-%d')
    end_date_obj = datetime.strptime(end_date, '%Y-%m-%d')

    current_date = start_date_obj

    while current_date <= end_date_obj:
        next_month = (current_date.replace(day=28) + timedelta(days=4)).replace(day=1)
        fetch_end_date = min(end_date_obj, next_month - timedelta(days=1))

        asos_df = fetch_weather_data(current_date.strftime('%Y-%m-%d'), fetch_end_date.strftime('%Y-%m-%d'), stn_ids)
        if asos_df is not None:
            asos_df = process_asos_data(asos_df)
            save_data(asos_df, stn_ids, cache_dir)
        else:
            print(
                f"No data fetched for period: {current_date.strftime('%Y-%m-%d')} to {fetch_end_date.strftime('%Y-%m-%d')}")

        current_date = next_month

    cache_to_final(stn_ids, cache_dir, output_dir)


if __name__ == "__main__":
    main()
