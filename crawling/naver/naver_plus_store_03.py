# %% [markdown]
# # Library

# %%
import requests
from bs4 import BeautifulSoup as bs

import time, os, random
import pandas as pd
import re
import numpy as np

from selenium import webdriver
import chromedriver_autoinstaller as ca

from selenium.webdriver.common.by import By
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys

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
# ## chrome driver 실행

# %%
# 웹드라이버 실행
driver = webdriver.Chrome(options=options)

# %% [markdown]
# ## 페이지 접속

# %%
# 페이지 주소
url = 'https://shopping.naver.com/ns/home'

# %% [markdown]
# ### requests 테스트
# - 페이지 접속 가능 여부확인
#     - 가능할 경우 출력 : <Response [200]>

# %%
# req = requests.get(url)
# print(req)
# html = req.content.decode('utf-8') # 한글 깨짐 해결 코드
# soup = bs(html, 'html.parser')
# soup.title.text

# %% [markdown]
# ### selenium 작동

# %%
driver.get(url)
driver.implicitly_wait(10) # 페이지 로드 될 때까지 기다리지만 로드 되는 순간 종료
# driver.maximize_window() # 브라우져 창 최대화

# %% [markdown]
# ### 검색 창에 검색어 입력

# %%
# 검색창 정보
search_window_xpath = '//*[@id="gnb-gnb"]/div[2]/div/div[2]/div[1]/form/div/div/div/div/input' # 검색 입력창
search_window = driver.find_element(By.XPATH, search_window_xpath)

# 검색어
search_keyword = '아이라인'

# 검색창에 검색어 입력
search_window.send_keys(search_keyword)

# 검색 창 요소가 존재할 때까지 기다림
search_window = WebDriverWait(driver, 10).until(
    EC.presence_of_element_located((By.XPATH, search_window_xpath))
)

# 검색 창에 엔터 입력
search_window.send_keys(Keys.ENTER)
driver.implicitly_wait(10)

# %%
# 스크롤해야 정보가 로드되는 페이지
# 페이지 스크롤 다운
scroll_num = 10

# 데이터 담을 데이터프레임 생성
raw_df = pd.DataFrame()

for scnum in range(scroll_num):

    # 페이지 수프에 담기
    page = driver.page_source
    soup = bs(page, 'html.parser')

    # 상품 섹션 추출
    products_section = soup.select_one('div#composite-card-list')

    # 상품 리스트
    product_list = products_section.select('li.compositeCardContainer_composite_card_container__jr8cb.composite_card_container div.basicProductCard_basic_product_card__TdrHT.basicProductCard_view_type_grid2__vKr1n')
    print('상품 리스트 개수 :', len(product_list))

    detail_link_list = []
    img_src_list = []
    title_list = []
    original_price_list = []
    discount_rate_list = []
    price_list = []
    delivery_price_list = []

    for i in range(len(product_list)):
        # 상세 페이지 링크
        try:
            detail_link = product_list[i].select_one('a.basicProductCard_link__urzND._nlog_click._nlog_impression_element')['href']
        except:
            print(i)
            # print('상세페이지링크없음')
        # 이미지 링크
        try:
            img_src = product_list[i].select_one('div.productCardThumbnail_thumbnail__KzO1N img.autoFitImg_auto_fit_img__fIpj4.autoFitImg_full_height__QCTGq.productCardThumbnail_image__Li6iz.scale')['src']
        except:
            print(i)
            # print('이미지링크없음')
        
        # 상품 정보 섹션
        product_info_section = product_list[i].select_one('div.basicProductCardInformation_basic_product_card_information__7v_uc')
        
        ## 상품 제목
        try:
            title = product_info_section.select_one('strong.basicProductCardInformation_title__Bc_Ng').text
        except:
            print(i)
            # print('상품제목없음')
        
        ## 원래가격
        try:
            raw_original_price = product_info_section.select_one('span.priceTag_original_price__jyZRY').text
            original_price = int(re.sub('[^0-9]', '', raw_original_price))
        except:
            original_price = np.nan
            # print('원래가격없음')

        ## 할인률
        try:
            raw_discount_rate = product_info_section.select_one('span.priceTag_discount__F_ZXz').text
            discount_rate = int(re.sub('[^0-9]', '', raw_discount_rate)) / 100
        except:
            discount_rate = np.nan
            # print('할인률없음')

        ## 현재가격
        try:
            raw_price = product_info_section.select_one('span.priceTag_inner_price__TctbK').text
            price = int(re.sub('[^0-9]', '', raw_price))
        except:
            print(i)
            # print('현재가격없음')
            
        ## 배송비
        try:
            raw_delivery_price = product_info_section.select_one('div.productCardPrice_delivery_price__AiyD2').text
            delivery_price = int(re.sub('[^0-9]', '', raw_delivery_price))
        except:
            delivery_price = np.nan
            # print('배송비없음')

        # 정보 리스트에 담기
        detail_link_list.append(detail_link)
        img_src_list.append(img_src)
        title_list.append(title)
        original_price_list.append(original_price)
        discount_rate_list.append(discount_rate)
        delivery_price_list.append(delivery_price)
        price_list.append(price)

    # # 정보 리스트 개수 확인
    # print('스크롤 횟수 :', scnum)
    # print('detail_link_list 원소 개수 :', len(detail_link_list))
    # print('img_src_list 원소 개수 :', len(img_src_list))
    # print('title_list 원소 개수 :', len(title_list))
    # print('original_price_list 원소 개수 :', len(original_price_list))
    # print('discount_rate_list 원소 개수 :', len(discount_rate_list))
    # print('price_list 원소 개수 :', len(price_list))
    # print('delivery_price_list 원소 개수 :', len(delivery_price_list))

    # 데이터프레임 생성
    data_dict = {
    '상세페이지링크':detail_link_list,
    '이미지링크':img_src_list,
    '제품제목':title_list,
    '원래가격':original_price_list,
    '할인률':discount_rate_list,
    '현재가격':price_list,
    '배송비':delivery_price_list
    }
    some_df = pd.DataFrame(data_dict)
    raw_df = pd.concat([raw_df, some_df], axis=0)

    # 페이지 스크롤 다운
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # 문서 높이 만큼 스크롤
    time.sleep(random.uniform(1, 3)) # 랜덤 시간 대기
    driver.implicitly_wait(10)

print('데이터 수집 완료')

# %%
# 중복 데이터 정리
print(raw_df.shape)
df = raw_df.drop_duplicates().reset_index(drop=True)
df['번호'] = df.index + 1
df = df[['번호', '상세페이지링크', '이미지링크', '제품제목', '원래가격', '할인률', '현재가격', '배송비']]
print(df.shape)

# %%

# %%
# # 무한 페이지 스크롤다운
# last_page_height = driver.execute_script("return document.documentElement.scrollHeight")

# while True:
#     driver.execute_script("window.scrollTo(0, document.body.scrollHeight);") # 문서 높이 만큼 스크롤
#     # driver.execute_script("window.scrollTo(0, document.documentElement.scrollHeight);") # # 문서 높이 만큼 스크롤(위 코드와 동일한 기능)
#     time.sleep(random.uniform(1, 3))
#     driver.implicitly_wait(10) # 페이지 로드 될 때까지 기다리지만 로드 되는 순간 종료

#     new_page_height = driver.execute_script("return document.documentElement.scrollHeight")
#     if new_page_height == last_page_height:
#         break
#     else:
#         last_page_height = new_page_height

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
crawled_folder_path = os.path.join(code_path, 'crawled_data', 'naver_plus_store', current_date)

# %%
os.makedirs(crawled_folder_path, exist_ok=True)

# %%
# 엑셀 파일로 출력
df.to_excel(os.path.join(crawled_folder_path, f'naver_{search_keyword}_{current_datetime}.xlsx'), index=False)

# %%
driver.quit()

# %% [markdown]
# # END


