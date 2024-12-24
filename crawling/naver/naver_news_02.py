# %% [markdown]
# # Library

# %%
import requests
from bs4 import BeautifulSoup as bs

import time, os, random
import pandas as pd
import numpy as np

from selenium import webdriver
import chromedriver_autoinstaller as ca

from selenium.webdriver.common.by import By

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# %% [markdown]
# ## chrome driver 설치

# %%
# USB error 메세지 발생 해결을 위한 코드
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])

# %%
# 현재 크롬 버전 확인
chrome_ver = ca.get_chrome_version().split('.')[0]

# %%
# # 크롬 드라이버 확인 및 설치(처음 한번만 실행)
# ca.install(True)

# %% [markdown]
# # 페이지 접속

# %%
# 페이지 주소
while True:
    try:
        section_number = int(input('뉴스의 섹션 번호를 입력하세요(1:정치, 2:경제, 3:사회, 4:생활/문화, 5:IT/과학, 6:세계): '))
    except:
        continue
    if section_number == 1:
        url = 'https://news.naver.com/section/100' # 네이버 뉴스 > 정치
        print('정치 섹션의 뉴스를 크롤링합니다.')
        break
    elif section_number == 2:
        url = 'https://news.naver.com/section/101' # 네이버 뉴스 > 경제
        print('경제 섹션의 뉴스를 크롤링합니다.')
        break
    elif section_number == 3:
        url = 'https://news.naver.com/section/102' # 네이버 뉴스 > 사회
        print('사회 섹션의 뉴스를 크롤링합니다.')
        break
    elif section_number == 4:
        url = 'https://news.naver.com/section/103' # 네이버 뉴스 > 생활/문화
        print('생활/문화 섹션의 뉴스를 크롤링합니다.')
        break
    elif section_number == 5:
        url = 'https://news.naver.com/section/105' # 네이버 뉴스 > IT/과학
        print('IT/과학 섹션의 뉴스를 크롤링합니다.')
        break
    elif section_number == 6:
        url = 'https://news.naver.com/section/104' # 네이버 뉴스 > 세계
        print('세계 섹션의 뉴스를 크롤링합니다.')
        break

# %% [markdown]
# ## requests 테스트
# - 페이지 접속 가능 여부확인
#     - 가능할 경우 출력 : <Response [200]>

# %%
# req = requests.get(url)
# print(req)
# html = req.content.decode('utf-8') # 한글 깨짐 해결 코드
# soup = bs(html, 'html.parser')
# soup.title.text

# %% [markdown]
# ## selenium 작동

# %%
# 웹드라이버 실행
driver = webdriver.Chrome(options=options)

# %%
driver.get(url)
driver.implicitly_wait(10) # 페이지 로드 될 때까지 기다리지만 로드 되는 순간 종료
# driver.maximize_window() # 브라우져 창 최대화

# %% [markdown]
# ## 헤드라인 뉴스 섹션 로드

# %%
# 헤드라인 뉴스
headline_news_more_view_button_xpath = '//*[@id="newsct"]/div[1]/div[2]/a' # 헤드라인 더 보기 버튼

# 헤드라인 더 보기 버튼 로딩 대기
headline_news_more_view_button = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, headline_news_more_view_button_xpath))
)

# 헤드라인 더보기 버튼 클릭
headline_news_more_view_button.click()
driver.implicitly_wait(10)

# %% [markdown]
# # 헤드라인 뉴스 수집

# %%
page = driver.page_source
soup = bs(page, 'html.parser')

# %%
# 헤드라인 뉴스 섹션
headline_news_section = soup.select_one('ul.sa_list')

# %%
# 뉴스 타이들 리스트
headline_news_list = headline_news_section.select('li.sa_item._SECTION_HEADLINE')
print('헤드라인 뉴스 개수 :', len(headline_news_list))

# %% [markdown]
# # 수집한 데이터 전처리

# %%
link_list = []
title_list = []
content_list = []
press_list = []
related_news_count_list = []

for i in range(len(headline_news_list)):
    # 기사 내용 섹션
    news_content_section = headline_news_list[i].select_one('div.sa_text')

    # 기사 링크
    try:
        link = news_content_section.select_one('a.sa_text_title._NLOG_IMPRESSION')['href']
    except:
        link = np.nan
        print(i, '기사 링크 없음')
    
    # 타이틀
    try:
        title = news_content_section.select_one('strong.sa_text_strong').text.strip()
    except:
        title = np.nan
        print(i, '타이틀 없음')
    
    # 기사 내용
    try:
        content = news_content_section.select_one('div.sa_text_lede').text.strip()
    except:
        content = np.nan
        print(i, '기사 내용 없음')
    
    ## 언론사
    try:
        press = news_content_section.select_one('div.sa_text_press').text
    except:
        press = np.nan
        print(i, '언론사 없음')
    
    ## 관련 뉴스 개수
    try:
        related_news_count = int(news_content_section.select_one('span.sa_text_cluster_num').text)
    except:
        related_news_count = np.nan
        print(i, '관련 뉴스 개수 없음')
    
    # 정보 리스트에 담기
    link_list.append(link)
    title_list.append(title)
    content_list.append(content)
    press_list.append(press)
    related_news_count_list.append(related_news_count)

# %%
data_dict = {
    '번호': range(1, len(link_list)+1),
    '기사 링크': link_list,
    '기사 제목': title_list,
    '기사 내용': content_list,
    '언론사': press_list,
    '관련 뉴스 개수': related_news_count_list
    }
df = pd.DataFrame(data_dict)

# %% [markdown]
# # 데이터 출력

# %%
current_date = time.strftime('%Y%m%d')

# %%
current_datetime = time.strftime('%Y%m%d_%p_%I%M%S')

# %%
# 현재 경로 확인
code_path = os.getcwd().replace('\\', '/')

# %%
# 수집한 파일 저장할 폴더 생성
    # 1:정치, 2:경제, 3:사회, 4:생활/문화, 5:IT/과학, 6:세계
if section_number == 1:
    section = 'politics'
    print('정치 섹션의 뉴스를 출력합니다.')
elif section_number == 2:
    section = 'economy'
    print('경제 섹션의 뉴스를 출력합니다.')
elif section_number == 3:
    section = 'society'
    print('사회 섹션의 뉴스를 출력합니다.')
elif section_number == 4:
    section = 'life_culture'
    print('생활/문화 섹션의 뉴스를 출력합니다.')
elif section_number == 5:
    section = 'it_science'
    print('IT/과학 섹션의 뉴스를 출력합니다.')
elif section_number == 6:
    section = 'world'
    print('세계 섹션의 뉴스를 출력합니다.')
    
crawled_folder_path = os.path.join(code_path, 'crawled_data', 'naver_news', section, current_date)
os.makedirs(crawled_folder_path, exist_ok=True)
print('파일 저장 위치 :', crawled_folder_path)

# %%
# 엑셀 파일로 출력
df.to_excel(os.path.join(crawled_folder_path, f'naver_news_{section}_{current_datetime}.xlsx'), index=False)

# %%
driver.quit()
print('크롤링을 종료합니다.')

# %% [markdown]
# # END


