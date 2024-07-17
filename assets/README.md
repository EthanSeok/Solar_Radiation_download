## 날씨마루 지점 확인 방법

### 1. 날씨마루 홈페이지 접속
- [날씨마루 홈페이지](https://bd.kma.go.kr/kma2020/fs/energySelect1.do?pageNum=5&menuCd=F050701000#none)에 접속.
- 지도에서 원하는 지역 클릭

![image](https://github.com/user-attachments/assets/253ada86-f133-4a1c-a1fe-7c1dc9e79a27)


<br>

- 아래로 이동하여 기상 탭을 눌러 결과 확인
  
![image](https://github.com/user-attachments/assets/6ff83b7c-9d57-44df-a5c7-cb01776061ba)

<br>

- 그래프에 마우스 우클릭 후 검사 클릭

![image](https://github.com/user-attachments/assets/d7268a9d-5f4f-452d-a520-54f5be77eb10)

<br>

- sources -> energySelect1... -> javascript:sigunguClick() 숫자 확인

![image](https://github.com/user-attachments/assets/cca0423e-2eee-49e8-bc5f-bcfcd591914c)

<br>

- 지점코드는 총 10자리 숫자로 뒤에 10자리 수가 되도록 0을 붙여준다.
- 예를 들어 전주시 덕진구가 `45113`라면 `4511300000`로 만들어주면 된다.
