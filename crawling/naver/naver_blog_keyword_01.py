# # Library

import requests
from bs4 import BeautifulSoup as bs

import time, os, random
import pandas as pd
import numpy as np
from datetime import datetime

from selenium import webdriver
import chromedriver_autoinstaller as ca

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ## chrome driver 설치

# USB error 메세지 발생 해결을 위한 코드
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])

# 현재 크롬 버전 확인
chrome_ver = ca.get_chrome_version().split('.')[0]
chrome_ver

# # 크롬 드라이버 확인 및 설치(처음 한번만 실행)
# ca.install(True)

# # 페이지 접속

# url = 'https://section.blog.naver.com/BlogHome.naver?directoryNo=0&currentPage=1&groupId=0' # 네이버 블로그 홈

# ## requests 테스트
# - 페이지 접속 가능 여부확인
#     - 가능할 경우 출력 : <Response [200]>

# req = requests.get(url)
# print(req)

# 한글 깨짐 해결 코드
# # html = req.content.decode('utf-8') # 한글 깨짐 해결
# # soup = bs(html, 'html.parser')

# soup = bs(req.text, 'html.parser')
# soup.title.text

# request로 수집 에러
keyword = '아이폰 16' # 검색어
page_num = 1 # 페이지 번호
rangetype = 'ALL' # 검색 범위
orderby = 'sim' # 정렬 순서

keyword_url = f'https://section.blog.naver.com/Search/Post.naver?pageNo={page_num}&rangeType={rangetype}&orderBy={orderby}&keyword={keyword}'
req = requests.get(keyword_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'})
print(req)
soup = bs(req.text, 'html.parser')

# area_list_search = soup.select_one('div.area_list_search')
# list_search_post = area_list_search.select('div.list_search_post')
# list_search_post[0]

# ## keyword 입력

keyword = '아이폰 16' # 검색어

# ## 탭 선택(글, 블로그)

tab_option = '글' # 포스트, 블로그 선택
page_num = 1 # 페이지 번호
rangetype = 'ALL' # 검색 범위
orderby = 'sim' # 정렬 순서

if tab_option == '글':
    keyword_url = f'https://section.blog.naver.com/Search/Post.naver?pageNo={page_num}&rangeType={rangetype}&orderBy={orderby}&keyword={keyword}'
elif tab_option == '블로그':
    keyword_url = f'https://section.blog.naver.com/Search/Blog.naver?pageNo={page_num}&orderBy={orderby}&keyword={keyword}'

# ## selenium 작동

# 웹드라이버 실행
driver = webdriver.Chrome(options=options)

driver.get(keyword_url)
driver.implicitly_wait(10) # 페이지 로드 될 때까지 기다리지만 로드 되는 순간 종료
# driver.maximize_window() # 브라우져 창 최대화

# keyword = '아이폰 16' # 검색어
# keyword_input_xpath = '//*[@id="header"]/div[1]/div/div[2]/form/fieldset/div/input' # 검색창 xpath
# keyword_input_box = driver.find_element(By.XPATH, keyword_input_xpath)
# keyword_input_box.send_keys(keyword)
# time.sleep(random.uniform(1, 2))
# keyword_input_box.send_keys(Keys.ENTER)
# driver.implicitly_wait(10)

# # 정보 수집

# ### 🔧 글 선택
# - 참고 링크 : https://section.blog.naver.com/Search/Post.naver?pageNo={page_num}&rangeType=ALL&orderBy=sim&keyword={keyword}
# - 참고 링크 : https://section.blog.naver.com/Search/Post.naver?pageNo=1&rangeType=WEEK&orderBy=sim&startDate=2025-01-03&endDate=2025-01-10&keyword=아이폰 16
# - 참고 링크 : https://section.blog.naver.com/Search/Post.naver?pageNo=1&rangeType=PERIOD&orderBy=sim&startDate=2025-01-01&endDate=2025-01-13&keyword=아이폰 16
# - [⭕] rangeType 옵션(기간)
#     - 기간전체 : &rangeType=ALL
#     - 최근 1주 : &rangeType=WEEK
#     - 최근 1개월 : &rangeType=MONTH
#     - 기간 입력 : &rangeType=PERIOD&startDate=YYYY-mm-dd&endDate=YYYY-mm-dd
# 
# - [⭕] orderBy 옵션(관련도순, 최신순)
#     - 관련도순 : &orderBy=sim
#     - 최신순 : &orderBy=recentdate
# 
# - 수집할 페이지 옵션 추가
# - 수집할 페이지가 실제 페이지 수보다 많을 경우 예외 처리

page = driver.page_source
soup = bs(page, 'html.parser')
print(soup.title.text)

area_list_search = soup.select_one('div.area_list_search')
list_search_post = area_list_search.select('div.list_search_post')
list_search_post[0]

# 글 제목
post_num = 0
title = list_search_post[post_num].select_one('span.title').text
title

# 블로그 내용
text = list_search_post[post_num].select_one('a.text').text
text

# 글 작성자
name_author = list_search_post[post_num].select_one('em.name_author').text
name_author

# 블로그 이름
name_blog = list_search_post[post_num].select_one('span.name_blog').text
name_blog

# 글 작성 날짜
date = list_search_post[post_num].select_one('span.date').text
date

# 글 링크
desc_inner = list_search_post[post_num].select_one('a.desc_inner')['href']
desc_inner

list_search_post[1]

# 글 제목
post_num = 1
title = list_search_post[post_num].select_one('span.title').text
title

# 블로그 내용
text = list_search_post[post_num].select_one('a.text').text
text

# 글 작성자
name_author = list_search_post[post_num].select_one('em.name_author').text
name_author

# 블로그 이름
name_blog = list_search_post[post_num].select_one('span.name_blog').text
name_blog

# 글 작성 날짜
date = list_search_post[post_num].select_one('span.date').text
date

# 글 링크
text_link = list_search_post[post_num].select_one('a.desc_inner')['href']
text_link

area_list_search = soup.select_one('div.area_list_search')
list_search_post = area_list_search.select('div.list_search_post')

title_list = []
text_list = []
name_author_list = []
name_blog_list = []
date_list = []
text_link_list = []

for post in list_search_post:
    title = post.select_one('span.title').text
    text = post.select_one('a.text').text
    name_author = post.select_one('em.name_author').text
    name_blog = post.select_one('span.name_blog').text
    date = post.select_one('span.date').text
    text_link = post.select_one('a.desc_inner')['href']
    # print(title, text, name_author, name_blog, text_link)

    title_list.append(title)
    text_list.append(text)
    name_author_list.append(name_author)
    name_blog_list.append(name_blog)
    date_list.append(date)
    text_link_list.append(text_link)
print(len(title_list), len(text_list), len(name_author_list), len(name_blog_list), len(date_list), len(text_link_list))

driver.quit()

# 웹드라이버 실행
driver = webdriver.Chrome(options=options)

start = 5
end = 3
start, end = end, start
print(start, end)

keyword = '아이폰 16' # 검색어
tab_option = '글' # 포스트, 블로그 선택
rangetype = 'PERIOD' # 검색 범위(ALL, WEEK, MONTH, PERIOD)
orderby = 'sim' # 정렬 순서(sim, recentdate)

# rangetype이 PERIOD인 경우 시작일과 종료일 설정 
startdate = '2025-01-01' # 형식: YYYY-mm-dd(예. 2025-01-01)
enddate = '2025-01-10' # 형식: YYYY-mm-dd(예. 2025-01-01)
current_date = datetime.today().strftime('%Y-%m-%d')
if startdate > enddate:
    startdate, enddate = enddate, startdate # 시작일이 종료일보다 크면 종료일로 변경
if startdate > current_date:
    startdate, enddate = current_date, current_date # 시작일이 현재 날짜보다 크면 현재 날짜로 변경
if enddate > current_date:
    enddate = current_date # 종료일이 현재 날짜보다 크면 현재 날짜로 변경

title_list = []
text_list = []
name_author_list = []
name_blog_list = []
date_list = []
post_link_list = []

for page_num in range(1, 10):
    if tab_option == '글':
        if rangetype == 'PERIOD':
            keyword_url = f'https://section.blog.naver.com/Search/Post.naver?pageNo={page_num}&rangeType={rangetype}&orderBy={orderby}&&startDate={startdate}&endDate={enddate}&keyword={keyword}'
        else:
            keyword_url = f'https://section.blog.naver.com/Search/Post.naver?pageNo={page_num}&rangeType={rangetype}&orderBy={orderby}&keyword={keyword}'
    elif tab_option == '블로그':
        keyword_url = f'https://section.blog.naver.com/Search/Blog.naver?pageNo={page_num}&orderBy={orderby}&keyword={keyword}'


    driver.get(keyword_url)
    driver.implicitly_wait(10) # 페이지 로드 될 때까지 기다리지만 로드 되는 순간 종료
    time.sleep(random.uniform(1, 3))

    page = driver.page_source
    soup = bs(page, 'html.parser')
    # print(soup.title.text)
    
    area_list_search = soup.select_one('div.area_list_search')
    list_search_post = area_list_search.select('div.list_search_post')

    for post in list_search_post:
        title = post.select_one('span.title').text
        text = post.select_one('a.text').text
        name_author = post.select_one('em.name_author').text
        name_blog = post.select_one('span.name_blog').text
        date = post.select_one('span.date').text
        post_link = post.select_one('a.desc_inner')['href']

        title_list.append(title)
        text_list.append(text)
        name_author_list.append(name_author)
        name_blog_list.append(name_blog)
        date_list.append(date)
        post_link_list.append(post_link)

print(len(title_list), len(text_list), len(name_author_list), len(name_blog_list), len(date_list), len(post_link_list))

post_dict = {
    'title': title_list,
    'text': text_list,
    'name_author': name_author_list,
    'name_blog': name_blog_list,
    'date': date_list,
    'post_link': post_link_list
}
post_df = pd.DataFrame(post_dict)
post_df

new = post_df.drop_duplicates()
new.shape

# 현재 날짜
current_date = datetime.today().strftime('%Y%m%d')
current_date

# 현재 경로 확인
code_path = os.getcwd().replace('\\', '/')
code_path

# 수집한 파일 저장할 폴더 생성
crawled_folder_path = os.path.join(code_path, 'crawled_data', 'naver_blog', current_date)
os.makedirs(crawled_folder_path, exist_ok=True)

current_datetime = datetime.today().strftime('%Y%m%d_%p_%I%M%S')
current_datetime

# 저장할 파일 경로
file_path = os.path.join(crawled_folder_path, f'naver_blog_{current_datetime}.xlsx')
file_path



# ## 🔧 블로그 선택
# - 참고 링크 : https://section.blog.naver.com/Search/Blog.naver?pageNo=1&orderBy=sim&keyword=아이폰 16
# - 참고 링크 : https://section.blog.naver.com/Search/Blog.naver?pageNo=1&orderBy=recentdate&keyword=아이폰 16
# - [⭕] orderBy 옵션
#     - 관련도순 : &orderBy=sim
#     - 최신순 : &orderBy=recentdate
# 
# - 수집할 페이지 옵션 추가
# - 수집할 페이지가 실제 페이지 수보다 많을 경우 예외 처리

keyword = '아이폰 16' # 검색어
tab_option = '블로그' # 포스트, 블로그 선택
# rangetype = 'PERIOD' # 검색 범위(ALL, WEEK, MONTH, PERIOD)
orderby = 'sim' # 정렬 순서(sim, recentdate)

# # rangetype이 PERIOD인 경우 시작일과 종료일 설정 
# startdate = '2025-01-01' # 형식: YYYY-mm-dd(예. 2025-01-01)
# enddate = '2025-01-10' # 형식: YYYY-mm-dd(예. 2025-01-01)
# current_date = datetime.today().strftime('%Y-%m-%d')
# if startdate > enddate:
#     startdate, enddate = enddate, startdate # 시작일이 종료일보다 크면 종료일로 변경
# if startdate > current_date:
#     startdate, enddate = current_date, current_date # 시작일이 현재 날짜보다 크면 현재 날짜로 변경
# if enddate > current_date:
#     enddate = current_date # 종료일이 현재 날짜보다 크면 현재 날짜로 변경

if tab_option == '글':
    if rangetype == 'PERIOD':
        keyword_url = f'https://section.blog.naver.com/Search/Post.naver?pageNo={page_num}&rangeType={rangetype}&orderBy={orderby}&&startDate={startdate}&endDate={enddate}&keyword={keyword}'
    else:
        keyword_url = f'https://section.blog.naver.com/Search/Post.naver?pageNo={page_num}&rangeType={rangetype}&orderBy={orderby}&keyword={keyword}'
elif tab_option == '블로그':
    keyword_url = f'https://section.blog.naver.com/Search/Blog.naver?pageNo={page_num}&orderBy={orderby}&keyword={keyword}'

keyword_url

driver.get(keyword_url)
driver.implicitly_wait(10) # 페이지 로드 될 때까지 기다리지만 로드 되는 순간 종료
# driver.maximize_window() # 브라우져 창 최대화

page = driver.page_source
soup = bs(page, 'html.parser')
print(soup.title.text)

area_list_search = soup.select_one('div.area_list_search')
list_search_blog = area_list_search.select('div.list_search_blog')
list_search_blog[0]

# 블로그 제목
post_num = 0
text_blog = list_search_blog[post_num].select_one('em.text_blog').text
text_blog

# 블로그 내용
blog_intro = list_search_blog[post_num].select_one('p.blog_intro').text
blog_intro

# 글 작성자
name_author = list_search_blog[post_num].select_one('em.name_author').text
name_author

# 블로그 링크
blog_link = list_search_blog[post_num].select_one('a.name_blog')['href']
blog_link



# 블로그 제목
post_num = 1
text_blog = list_search_blog[post_num].select_one('em.text_blog').text
text_blog

# 블로그 내용
blog_intro = list_search_blog[post_num].select_one('p.blog_intro').text
blog_intro

list_search_blog[post_num].select_one('p.blog_intro').text == ''

# 글 작성자
name_author = list_search_blog[post_num].select_one('em.name_author').text
name_author

# 블로그 링크
blog_link = list_search_blog[post_num].select_one('a.name_blog')['href']
blog_link

area_list_search = soup.select_one('div.area_list_search')
list_search_blog = area_list_search.select('div.list_search_blog')

# 정보 수집
text_blog_list = []
blog_intro_list = []
name_author_list = []
blog_link_list = []
for blog in list_search_blog:
    text_blog = blog.select_one('em.text_blog').text
    if blog.select_one('p.blog_intro').text == '':
        blog_intro = np.nan
    else:
        blog_intro = blog.select_one('p.blog_intro').text
    name_author = blog.select_one('em.name_author').text
    blog_link = blog.select_one('a.name_blog')['href']
    # print(text_blog, blog_intro, name_author, blog_link)

    text_blog_list.append(text_blog)
    blog_intro_list.append(blog_intro)
    name_author_list.append(name_author)
    blog_link_list.append(blog_link)

print(len(text_blog_list), len(blog_intro_list), len(name_author_list), len(name_blog_list))

blog_dict = {
    'text_blog': text_blog_list,
    'blog_intro': blog_intro_list,
    'name_author': name_author_list,
    'blog_link': blog_link_list
}
blog_df = pd.DataFrame(blog_dict)

# ## 🔧 종합
# - 수집할 페이지 옵션 추가
# - 수집할 페이지가 실제 페이지 수보다 많을 경우 예외 처리

keyword = '아이폰 16' # 검색어

rangetype = 'PERIOD' # 검색 범위(ALL, WEEK, MONTH, PERIOD)
orderby = 'sim' # 정렬 순서(sim, recentdate)

# rangetype이 PERIOD인 경우 시작일과 종료일 설정 
startdate = '2025-01-01' # 형식: YYYY-mm-dd(예. 2025-01-01)
enddate = '2025-01-10' # 형식: YYYY-mm-dd(예. 2025-01-01)
current_date = datetime.today().strftime('%Y-%m-%d')
if startdate > enddate:
    startdate, enddate = enddate, startdate # 시작일이 종료일보다 크면 종료일로 변경
if startdate > current_date:
    startdate, enddate = current_date, current_date # 시작일이 현재 날짜보다 크면 현재 날짜로 변경
if enddate > current_date:
    enddate = current_date # 종료일이 현재 날짜보다 크면 현재 날짜로 변경

# 현재 날짜
current_date = datetime.today().strftime('%Y%m%d')
# 현재 경로 확인
code_path = os.getcwd().replace('\\', '/')
# 수집한 파일 저장할 폴더 생성
crawled_folder_path = os.path.join(code_path, 'crawled_data', 'naver_blog', current_date)
os.makedirs(crawled_folder_path, exist_ok=True)
# 저장할 파일 경로
current_datetime = datetime.today().strftime('%Y%m%d_%p_%I%M%S')
file_path = os.path.join(crawled_folder_path, f'naver_blog_{current_datetime}.xlsx')

# 웹드라이버 실행
driver = webdriver.Chrome(options=options)

sheet_name_list = ['글', '블로그']
with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
    for tab_option in sheet_name_list:
        if tab_option == '글':
            title_list = []
            text_list = []
            name_author_list = []
            name_blog_list = []
            date_list = []
            post_link_list = []
            for page_num in range(1, 10):
                if rangetype == 'PERIOD':
                    keyword_url = f'https://section.blog.naver.com/Search/Post.naver?pageNo={page_num}&rangeType={rangetype}&orderBy={orderby}&&startDate={startdate}&endDate={enddate}&keyword={keyword}'
                else:
                    keyword_url = f'https://section.blog.naver.com/Search/Post.naver?pageNo={page_num}&rangeType={rangetype}&orderBy={orderby}&keyword={keyword}'

                driver.get(keyword_url)
                driver.implicitly_wait(10) # 페이지 로드 될 때까지 기다리지만 로드 되는 순간 종료
                time.sleep(random.uniform(1, 3))

                page = driver.page_source
                soup = bs(page, 'html.parser')
                # print(soup.title.text)
                
                area_list_search = soup.select_one('div.area_list_search')
                list_search_post = area_list_search.select('div.list_search_post')

                for post in list_search_post:
                    title = post.select_one('span.title').text
                    text = post.select_one('a.text').text
                    name_author = post.select_one('em.name_author').text
                    name_blog = post.select_one('span.name_blog').text
                    date = post.select_one('span.date').text
                    post_link = post.select_one('a.desc_inner')['href']

                    title_list.append(title)
                    text_list.append(text)
                    name_author_list.append(name_author)
                    name_blog_list.append(name_blog)
                    date_list.append(date)
                    post_link_list.append(post_link)

            # print(len(title_list), len(text_list), len(name_author_list), len(name_blog_list), len(date_list), len(post_link_list))

            # 데이터 프레임 생성
            post_dict = {
                'title': title_list,
                'text': text_list,
                'name_author': name_author_list,
                'name_blog': name_blog_list,
                'date': date_list,
                'post_link': post_link_list
            }
            post_df = pd.DataFrame(post_dict)
            post_df.to_excel(writer, sheet_name=tab_option, index=False)
            print(post_df.shape)

        elif tab_option == '블로그':
            text_blog_list = []
            blog_intro_list = []
            name_author_list = []
            blog_link_list = []
            for page_num in range(1, 10):
                keyword_url = f'https://section.blog.naver.com/Search/Blog.naver?pageNo={page_num}&orderBy={orderby}&keyword={keyword}'

                driver.get(keyword_url)
                driver.implicitly_wait(10) # 페이지 로드 될 때까지 기다리지만 로드 되는 순간 종료
                time.sleep(random.uniform(1, 3))

                page = driver.page_source
                soup = bs(page, 'html.parser')
                # print(soup.title.text)

                area_list_search = soup.select_one('div.area_list_search')
                list_search_blog = area_list_search.select('div.list_search_blog')

                for blog in list_search_blog:
                    text_blog = blog.select_one('em.text_blog').text
                    if blog.select_one('p.blog_intro').text == '':
                        blog_intro = np.nan
                    else:
                        blog_intro = blog.select_one('p.blog_intro').text
                    name_author = blog.select_one('em.name_author').text
                    blog_link = blog.select_one('a.name_blog')['href']
                    # print(text_blog, blog_intro, name_author, blog_link)

                    text_blog_list.append(text_blog)
                    blog_intro_list.append(blog_intro)
                    name_author_list.append(name_author)
                    blog_link_list.append(blog_link)

                # print(len(text_blog_list), len(blog_intro_list), len(name_author_list), len(name_blog_list))
            blog_dict = {
                'text_blog': text_blog_list,
                'blog_intro': blog_intro_list,
                'name_author': name_author_list,
                'blog_link': blog_link_list
            }
            blog_df = pd.DataFrame(blog_dict)
            blog_df.to_excel(writer, sheet_name=tab_option, index=False)
            print(blog_df.shape)

    print('저장 파일 경로 :', file_path)
    print('저장완료')

driver.quit()

# # END