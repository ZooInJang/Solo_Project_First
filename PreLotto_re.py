import schedule
import time
import os
import datetime
import json
import requests
from bs4 import BeautifulSoup
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import ast
import warnings

# 불필요한 로그 삭제
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # FATAL messages only
os.environ['PYTHONWARNINGS'] = 'ignore'   # Ignore Python warnings
warnings.filterwarnings('ignore')

# 스크래핑 모듈
def scrape():
    url = "https://www.dhlottery.co.kr/gameResult.do?method=byWin"
    request = requests.get(url)
    data = request.text

    soup = BeautifulSoup(data, 'html.parser')
    data_tags = soup.find_all('div', {'class': 'nums'})

    numbers = []

    for data_tag in data_tags:
        number_tags = data_tag.find_all('span')
        numbers = [tag.text for tag in number_tags][:6]  # 처음 6개 숫자만 저장

        print(numbers)

    return numbers

# 스크래핑한 값을 지정한 파일에 저장하는 작업의 모듈
def job():
    numbers = scrape()  # 스크래핑된 데이터
    last_line = None
    if os.path.exists('data.txt'):
        with open('data.txt', 'r') as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1].strip()  # 파일의 마지막 줄을 읽습니다.
    if last_line != str(numbers):  # 중복 데이터 방지
        with open('data.txt', 'a') as f:
            f.write("%s\n" % numbers)  # 새로운 데이터 저장
    with open('last_run.json', 'w') as f:
        json.dump({'last_run': str(datetime.datetime.now())}, f)

# 프로그램 시작 시 마지막 실행 시간 확인
if os.path.exists('last_run.json'):
    with open('last_run.json', 'r') as f:
        last_run = json.load(f)['last_run']
        last_run = datetime.datetime.strptime(last_run, '%Y-%m-%d %H:%M:%S.%f')
        if datetime.datetime.now() - last_run > datetime.timedelta(days=7):
            job()

# 프로그램 시작 전에 먼저 1번 실행
job()

# 예측 함수
def predict():
    with open('data.txt', 'r') as f:
        lines = f.readlines()

    lines = lines[:]
    data = [ast.literal_eval(line.strip()) for line in lines]

    # 데이터 정규화 (0~1 사이의 값으로 변환)
    normalized_data = np.array(data, dtype=float) / 50.0
    normalized_data = np.reshape(normalized_data, (normalized_data.shape[0], 6, 1))  # 6개 숫자로 변경

    # 모델 구성
    model = Sequential()
    model.add(LSTM(50, activation='relu', input_shape=(6, 1)))  # 6개 숫자로 입력 변경
    model.add(Dense(6))  # 출력도 6개로 변경

    model.compile(optimizer='adam', loss='mse')
    model.fit(normalized_data, normalized_data, epochs=200, verbose=0)

    # 다음 6개의 숫자 예측
    test_input = np.array([np.array(data[-1], dtype=float) / 45.0])
    test_input = np.reshape(test_input, (test_input.shape[0], 6, 1))  # 6개 숫자로 변경
    prediction = model.predict(test_input)

    prediction = prediction * 45  # 원래 범위로 변환
    prediction1 = np.round(prediction).astype(int)
    prediction2 = np.floor(prediction).astype(int)
    prediction3 = np.ceil(prediction).astype(int)

    print("반올림한 값 :", *prediction1[0])
    print("내림 값 :", *prediction2[0])
    print("올림 값 :", *prediction3[0])

# 스케줄링 설정
schedule.every().seconds.do(job)

# 메뉴
while True:
    print("1: 예측 실행")
    print("2: 종료")
    choice = input("원하는 작업을 선택하세요: ")

    if choice == '1':
        predict()
    elif choice == '2':
        break
    else:
        print("잘못된 선택입니다. 다시 선택해주세요.")

    schedule.run_pending()
    time.sleep(1)