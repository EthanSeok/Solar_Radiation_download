import streamlit as st
import requests
import pandas as pd
import os
import ssl
from requests.adapters import HTTPAdapter
from datetime import datetime


class SSLAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.set_ciphers('DEFAULT@SECLEVEL=1')
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

def fetch_weather_data(start_date, end_date, stn_ids, service_key):
    startDt = start_date.replace('-', '')
    endDt = end_date.replace('-', '')

    url = "https://apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList"
    params = {
        'serviceKey': service_key,
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
                st.write("...")
                return None

            items = data['response']['body']['items']['item']
            df = pd.json_normalize(items)
            all_data.append(df)

            if params['pageNo'] == 1:
                total_count = data['response']['body']['totalCount']
                total_pages = (total_count // int(params['numOfRows'])) + (total_count % int(params['numOfRows']) > 0)

            params['pageNo'] += 1
        else:
            st.write(f"Error: {response.status_code}")
            break

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        return final_df
    else:
        return None

def save_data(df, region_code, cache_dir):
    df['year_month'] = pd.to_datetime(df['tm']).dt.to_period('M').astype(str).str.replace('-', '_')

    for year_month, group in df.groupby('year_month'):
        filename = os.path.join(cache_dir, f"ASOS_{region_code}_{year_month}.csv")
        group.to_csv(filename, index=False, encoding='utf-8-sig')
        # st.write(f"Saved cache: {filename}")

def cache_to_final(region_code, cache_dir, output_dir):
    current_year_month = datetime.now().strftime('%Y_%m')
    cached_files = [os.path.join(cache_dir, f) for f in os.listdir(cache_dir) if f.startswith(f"ASOS_{region_code}") and not f"_{current_year_month}.csv" in f]
    all_data = []

    for file in cached_files:
        df = pd.read_csv(file)
        all_data.append(df)

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        # final_filename = os.path.join(output_dir, f"weather_data_{region_code}.csv")
        # final_df.to_csv(final_filename, index=False, encoding='utf-8-sig')
        # st.write(f"Saved final data: {final_filename}")
    else:
        st.write("No cached data to concatenate.")

def process_asos_data(asos):
    asos = asos.copy()
    asos['일시'] = pd.to_datetime(asos['tm'], format='%Y-%m-%d %H:%M')
    asos['날짜'] = asos['일시'].dt.date
    asos['시간'] = asos['일시'].dt.strftime('%H:%M')
    asos['icsr'] = asos['icsr'].replace('', 0)
    asos = asos[['stnNm', '날짜', '시간', 'icsr', 'ta', 'ws', 'tm']]
    asos.rename(columns={'icsr': '일사(MJ/m2)', 'stnNm':'지점', 'ta': '온도', 'ws': '풍속'}, inplace=True)
    return asos
