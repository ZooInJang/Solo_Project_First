from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import schedule
import time
import os
import datetime
import numpy as np
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense
import warnings

# 불필요한 로그 삭제
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings('ignore')

# 스크래핑 모듈 (동적 크롤링)
def scrape():
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    driver = webdriver.Chrome(options=options)

    try:
        url = "https://www.dhlottery.co.kr/lt645/intro"
        driver.get(url)
        time.sleep(2)

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        data_tags = soup.find_all('div', {'class': 'result-ballBox'})

        numbers = []

        for data_tag in data_tags:
            number_tags = data_tag.find_all('div', class_='result-ball')
            numbers = [tag.text.strip() for tag in number_tags if tag.text.strip().isdigit()][:6]

        print(numbers)
        return numbers

    finally:
        driver.quit()

# 스크래핑한 값을 지정한 파일에 저장하는 작업의 모듈
def job():
    numbers = scrape()
    if len(numbers) != 6:
        print("숫자 6개를 가져오지 못했습니다. 스킵합니다.")
        return

    last_line = None
    if os.path.exists('data.txt'):
        with open('data.txt', 'r') as f:
            lines = f.readlines()
            if lines:
                last_line = lines[-1].strip()

    if last_line != str(numbers):
        with open('data.txt', 'a') as f:
            f.write("%s\n" % numbers)

    with open('last_run.txt', 'w') as f:
        f.write(str(datetime.datetime.now()))

# 프로그램 시작 시 마지막 실행 시간 확인
if os.path.exists('last_run.txt'):
    with open('last_run.txt', 'r') as f:
        last_run = datetime.datetime.strptime(f.read().strip(), '%Y-%m-%d %H:%M:%S.%f')
        if datetime.datetime.now() - last_run > datetime.timedelta(days=7):
            job()

# 프로그램 시작 전에 먼저 1번 실행
job()

# 시계열 학습용 데이터셋 생성
def create_dataset(data, time_steps=5):
    X, y = [], []
    for i in range(len(data) - time_steps):
        X.append(data[i:i+time_steps])   # 입력: time_steps 회차
        y.append(data[i+time_steps])     # 출력: 다음 회차
    return np.array(X), np.array(y)

# 예측 함수
def predict():
    if not os.path.exists('data.txt'):
        print("데이터 파일이 없습니다.")
        return

    with open('data.txt', 'r') as f:
        lines = f.readlines()

    data = [eval(line.strip()) for line in lines if len(line.strip()) > 0]
    if len(data) < 10:
        print("충분한 데이터가 없습니다.")
        return

    # 숫자 정규화
    normalized_data = np.array(data, dtype=float) / 45.0

    # 시계열 데이터셋 생성 (최근 5회차 → 다음 회차)
    time_steps = 5
    X, y = create_dataset(normalized_data, time_steps)

    # 입력 형태: (샘플 수, time_steps, 6)
    X = np.reshape(X, (X.shape[0], time_steps, 6))
    y = np.reshape(y, (y.shape[0], 6))

    # LSTM 모델 정의
    model = Sequential()
    model.add(LSTM(64, activation='relu', return_sequences=True, input_shape=(time_steps, 6)))
    model.add(LSTM(32, activation='relu'))
    model.add(Dense(6, activation='linear'))

    model.compile(optimizer='adam', loss='mse')
    model.fit(X, y, epochs=200, verbose=0)

    # 마지막 5회차를 입력으로 사용해 다음 회차 예측
    last_input = normalized_data[-time_steps:]
    last_input = np.reshape(last_input, (1, time_steps, 6))
    prediction = model.predict(last_input)

    prediction = prediction * 45
    prediction = np.round(prediction).astype(int)[0]

    # 중복 제거 및 범위 보정
    prediction = np.clip(prediction, 1, 45)
    prediction = list(set(prediction))
    while len(prediction) < 6:
        prediction.append(np.random.randint(1, 46))

    print("예측된 다음 회차 번호 :", sorted(prediction))

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