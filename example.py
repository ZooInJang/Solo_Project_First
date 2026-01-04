from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time

# 스크래핑 모듈 (동적 크롤링)
def scrape():
    # 크롬 드라이버 옵션 설정
    options = Options()
    options.add_argument("--headless")  # 창 없이 실행
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")

    # 크롬 드라이버 실행 (드라이버 경로는 환경에 맞게 설정)
    driver = webdriver.Chrome(options=options)

    try:
        url = "https://www.dhlottery.co.kr/lt645/intro"
        driver.get(url)
        time.sleep(2)  # 자바스크립트 로딩 대기

        soup = BeautifulSoup(driver.page_source, 'html.parser')
        data_tags = soup.find_all('div', {'class': 'result-ballBox'})

        numbers = []

        for data_tag in data_tags:
            # 'id'는 태그가 아니라 속성이므로 find_all('id')는 잘못된 사용입니다.
            number_tags = data_tag.find_all('div', class_='result-ball')
            numbers = [tag.text.strip() for tag in number_tags if tag.text.strip().isdigit()][:6]

            print(numbers)

        return numbers

    finally:
        driver.quit()

# 테스트 실행
scrape()