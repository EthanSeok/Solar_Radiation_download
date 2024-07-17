## 날씨마루 태양광 발전량 예측 - 광량, 온도, 풍속

### 목적

![image](https://github.com/user-attachments/assets/5bc18131-63e9-4be1-993c-49b8dad1e641)

- [날씨마루](https://bd.kma.go.kr/kma2020/fs/energySelect1.do?pageNum=5&menuCd=F050701000#none)에서 제공하는 태양광 발전량 및 예측 광량, 온도, 풍속 자료를 제공함.
- 날씨마루 데이터 전송 API를 이용하여 당일 및 다음날의 예측 광량, 온도, 풍속 자료를 수집하고자 함.
- 기상청에서 제공하는 시간별 종관 기상자료(ASOS)와 비교하여 정확도를 확인하고자 함.
- 원하는 날짜 범위의 데이터를 수집하여 저장하고, 시각화하는 코드를 제공하고자 함.

  
<br>

### 사용법

- google colab과 anaconda3 환경에서 사용가능

<br>

패키지 설치 방법

```
git clone https://github.com/EthanSeok/Solar_Radiation_forecast.git
cd Solar_Radiation_forecast/radiation_analysis
pip install -r requirements.txt
```

<br>

코드 구성은 다음과 같음

- [asos_download.py](https://github.com/EthanSeok/Solar_Radiation_forecast/blob/master/radiation_analysis/asos_download.py): 기상청 시간별 종관 기상자료(ASOS) 다운로드
- [solar_panel_radiation_download.py](https://github.com/EthanSeok/Solar_Radiation_forecast/blob/master/radiation_analysis/solar_panel_radiation_download.py): 날씨마루 당일 및 다음날 예측 광량, 온도, 풍속 자료 다운로드
- [visualization.py](https://github.com/EthanSeok/Solar_Radiation_forecast/blob/master/radiation_analysis/visualization.py): 시각화(scatterplot, lineplot)
- [main.py](https://github.com/EthanSeok/Solar_Radiation_forecast/blob/master/radiation_analysis/main.py): 날짜 지정 및 전체 실행 코드

<br>

- ASOS API를 이용하기 위해서 [공공데이터포털](https://www.data.go.kr/data/15057210/openapi.do)에서 사용 신청후 인증키를 받아야한다.
- 일반 인증키 (Decoding) 코드를 아래 코드에 붙여 넣는다.

```
## asos_download.py
url = "https://apis.data.go.kr/1360000/AsosHourlyInfoService/getWthrDataList"
params = {
    'serviceKey': '', ## serviceKey의 ''안에 인증키를 붙여넣는다.
```

<br>

- 아래 코드 부분을 수정하여 ASOS 및 날씨마루 기상 자료를 다운로드 하고 싶은 날짜 범위 및 지역을 지정 가능.
- 기상청 측후소는 [다음](https://data.kma.go.kr/data/grnd/selectAsosRltmList.do?pgmNo=36&openPopup=Y) URL에서 확인 가능.
- 날씨마루 지점 코드의 경우 [다음](https://github.com/EthanSeok/Solar_Radiation_forecast/blob/master/assets/README.md) 방법을 참고하여 확인 가능.

```
## main.py

start_date = '2024-07-01'  # 시작 날짜
end_date = '2024-07-16'    # 종료 날짜
stn_ids = '146'            # 기상청 측후소
reg_cd = '4511300000'  # 태양광 발전량 예측 지점코드
```

<br>

- 시각화의 경우도 아래 코드에서 원하는 날짜 범위를 지정하여 그릴 수 있음.

```
## main.py

# Define the date range
start_date = '2024-07-12'
end_date = '2024-07-15'
```

<br>

## 결과

<img src=https://github.com/user-attachments/assets/c6841b78-aef2-4bc2-95fd-85ee8c22ab6b width=600>

<img src=https://github.com/user-attachments/assets/b997728d-8c06-40fe-9e17-e61878daf16a width=600>


