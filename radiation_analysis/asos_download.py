import requests
import pandas as pd
import os
import ssl
from requests.adapters import HTTPAdapter

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
        'serviceKey': '',
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

def save_data(df, region_code, output_dir):
    df = df[['지점', '날짜', '시간', '일사(MJ/m2)', '온도', '풍속']]
    filename = os.path.join(output_dir, f"weather_data_{region_code}.csv")
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    print(f"Saved: {filename}")

def process_asos_data(asos):
    asos = asos.copy()
    asos['일시'] = pd.to_datetime(asos['tm'], format='%Y-%m-%d %H:%M')
    asos['날짜'] = asos['일시'].dt.date
    asos['시간'] = asos['일시'].dt.strftime('%H:%M')
    asos['icsr'] = asos['icsr'].replace('', 0)
    asos = asos[['stnNm', '날짜', '시간', 'icsr', 'ta', 'ws']]
    asos.rename(columns={'icsr': '일사(MJ/m2)', 'stnNm':'지점', 'ta': '온도', 'ws': '풍속'}, inplace=True)
    return asos

def main():
    start_date = '2024-06-01'  # 시작 날짜
    end_date = '2024-07-14'    # 종료 날짜
    stn_ids = '146'            # 기상청 측후소

    output_dir = 'output'
    os.makedirs(output_dir, exist_ok=True)

    asos_df = fetch_weather_data(start_date, end_date, stn_ids)
    if asos_df is not None:
        asos_df = process_asos_data(asos_df)
        save_data(asos_df, stn_ids, output_dir)
    else:
        print("No data fetched.")


if __name__ == "__main__":
    main()
