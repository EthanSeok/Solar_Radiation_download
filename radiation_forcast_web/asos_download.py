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

def process_asos_data(asos):
    asos = asos.copy()
    asos['일시'] = pd.to_datetime(asos['tm'], format='%Y-%m-%d %H:%M')
    asos['날짜'] = asos['일시'].dt.date
    asos['시간'] = asos['일시'].dt.strftime('%H:%M')
    asos['icsr'] = asos['icsr'].replace('', 0)
    asos = asos[['stnNm', '날짜', '시간', 'icsr', 'ta', 'ws', 'tm']]
    asos.rename(columns={'icsr': '일사(MJ/m2)', 'stnNm':'지점', 'ta': '온도', 'ws': '풍속'}, inplace=True)
    return asos


