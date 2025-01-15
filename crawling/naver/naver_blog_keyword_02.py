# %% [markdown]
# # Library

# %%
import requests
from bs4 import BeautifulSoup as bs

import time, os, random, re
import pandas as pd
import numpy as np
from datetime import datetime

from selenium import webdriver
import chromedriver_autoinstaller as ca

# %% [markdown]
# ## chrome driver 설치

# %%
# USB error 메세지 발생 해결을 위한 코드
options = webdriver.ChromeOptions()
options.add_experimental_option("excludeSwitches", ["enable-logging"])
options.add_argument('headless')  # headless 모드 설정

# %%
# 현재 크롬 버전 확인
chrome_ver = ca.get_chrome_version().split('.')[0]
chrome_ver

# %%
# # 크롬 드라이버 확인 및 설치(처음 한번만 실행)
# ca.install(True)

# %% [markdown]
# ## requests 테스트
# - 페이지 접속 가능 여부확인
#     - 가능할 경우 출력 : <Response [200]>

# %%
# req = requests.get(url)
# print(req)

# 한글 깨짐 해결 코드
# # html = req.content.decode('utf-8') # 한글 깨짐 해결
# # soup = bs(html, 'html.parser')

# soup = bs(req.text, 'html.parser')
# soup.title.text

# %% [markdown]
# # 크롤링

# %% [markdown]
# ## 검색어 입력

# %%
keyword = '아이폰 16' # 검색어

# %% [markdown]
# ## 검색 옵션 설정

# %%
rangetype = 'WEEK' # 검색 범위(기간 전체 : ALL, 최근 1주 : WEEK, 최근 1개월 : MONTH, 기간 입력 : PERIOD)
orderby = 'sim' # 정렬 순서(관련도순 : sim, 최신순 : recentdate)

# rangetype이 PERIOD인 경우 시작일과 종료일 설정 
startdate = '2025-01-01' # 형식: YYYY-mm-dd(예. 2025-01-01)
enddate = '2025-01-02' # 형식: YYYY-mm-dd(예. 2025-01-01)
current_date = datetime.today().strftime('%Y-%m-%d')
if startdate > enddate:
    startdate, enddate = enddate, startdate # 시작일이 종료일보다 크면 종료일로 변경
if startdate > current_date:
    startdate, enddate = current_date, current_date # 시작일이 현재 날짜보다 크면 현재 날짜로 변경
if enddate > current_date:
    enddate = current_date # 종료일이 현재 날짜보다 크면 현재 날짜로 변경

# %% [markdown]
# ## 봇 실행

# %%
# 웹드라이버 실행
driver = webdriver.Chrome(options=options)

# %% [markdown]
# ## 검색 결과 개수 확인

# %%
# 검색 결과 개수 확인
sheet_name_list = ['글', '블로그']
for tab_option in sheet_name_list:
    page_num = 1
    if tab_option == '글':
        if rangetype == 'PERIOD':
            keyword_url = f'https://section.blog.naver.com/Search/Post.naver?pageNo={page_num}&rangeType={rangetype}&orderBy={orderby}&&startDate={startdate}&endDate={enddate}&keyword={keyword}'
        else:
            keyword_url = f'https://section.blog.naver.com/Search/Post.naver?pageNo={page_num}&rangeType={rangetype}&orderBy={orderby}&keyword={keyword}'

        driver.get(keyword_url)
        driver.implicitly_wait(10) # 페이지 로드 될 때까지 기다리지만 로드 되는 순간 종료
        time.sleep(random.uniform(1, 3))

        page = driver.page_source
        soup = bs(page, 'html.parser')
        
        area_list_search = soup.select_one('div.area_list_search')
        list_search_post = area_list_search.select('div.list_search_post')

        # 검색 결과 개수
        raw_post_search_number = soup.select_one('div.search_information em.search_number').text
        post_search_number = int(re.sub('[^0-9]', '', raw_post_search_number))

        # 검색 결과 페이지 수
        max_post_search_page_num = int(np.ceil(post_search_number / len(list_search_post)))

        if rangetype == 'PERIOD':
            print('='*50)
            print('검색어 :', keyword)
            print('글/블로그 선택 :', tab_option)
            print('검색 범위 :', rangetype.replace('PERIOD', '기간 입력'))
            print('검색 시작일 :', startdate)
            print('검색 종료일 :', enddate)
            print('정렬 순서 :', orderby.replace('sim', '관련도순').replace('recentdate', '최신순'))
            print('검색 결과 개수 :', post_search_number)
            print('검색 결과 페이지 수 :', max_post_search_page_num)
        else:
            print('검색어 :', keyword)
            print('글/블로그 선택 :', tab_option)
            print('검색 범위 :', rangetype.replace('ALL', '기간 전체').replace('WEEK', '최근 1주').replace('MONTH', '최근 1개월'))
            print('정렬 순서 :', orderby.replace('sim', '관련도순').replace('recentdate', '최신순'))
            print('검색 결과 개수 :', post_search_number)
            print('검색 결과 페이지 수 :', max_post_search_page_num)
        print()

    elif tab_option == '블로그':
        keyword_url = f'https://section.blog.naver.com/Search/Blog.naver?pageNo={page_num}&orderBy={orderby}&keyword={keyword}'

        driver.get(keyword_url)
        driver.implicitly_wait(10) # 페이지 로드 될 때까지 기다리지만 로드 되는 순간 종료
        time.sleep(random.uniform(1, 3))

        page = driver.page_source
        soup = bs(page, 'html.parser')

        area_list_search = soup.select_one('div.area_list_search')
        list_search_blog = area_list_search.select('div.list_search_blog')

        # 검색 결과 개수
        raw_blog_search_number = soup.select_one('div.search_information em.search_number').text
        blog_search_number = int(re.sub('[^0-9]', '', raw_blog_search_number))

        # 검색 결과 페이지 수
        max_blog_search_page_num = int(np.ceil(blog_search_number / len(list_search_blog)))
        
        print('='*50)
        print('검색어 :', keyword)
        print('글/블로그 선택 :', tab_option)
        print('정렬 순서 :', orderby.replace('sim', '관련도순').replace('recentdate', '최신순'))
        print('검색 결과 개수 :', blog_search_number)
        print('검색 결과 페이지 수 :', max_blog_search_page_num)

# %% [markdown]
# ### 수집할 포스트 페이지 수 설정

# %%
# 수집할 포스트 페이지 설정
while True:
    try:
        print(f'최대 포스트 페이지 수 : {max_post_search_page_num}')
        post_crawling_page_num = int(input(f"수집할 포스트 페이지 수를 입력하세요(숫자만 입력) : "))
        if post_crawling_page_num <= 0:
            print("0보다 큰 숫자를 입력하세요.")
            continue
        if post_crawling_page_num > max_post_search_page_num:
            print('입력한 숫자 :', post_crawling_page_num)
            print(f"입력한 숫자가 검색 결과 페이지 수보다 큽니다. {max_post_search_page_num}로 설정합니다.")
            post_crawling_page_num = max_post_search_page_num
        break
    except ValueError:
        print("유효한 숫자를 입력하세요.")

print(f"수집할 포스트 페이지 수: {post_crawling_page_num}")

# %% [markdown]
# ### 수집할 블로그 페이지 수 설정

# %%
# 수집할 블로그 페이지 설정
while True:
    try:
        print(f'최대 블로그 페이지 수 : {max_blog_search_page_num}')
        blog_crawling_page_num = int(input(f"수집할 블로그 페이지 수를 입력하세요(숫자만 입력) : "))
        if blog_crawling_page_num <= 0:
            print("0보다 큰 숫자를 입력하세요.")
            continue
        if blog_crawling_page_num > max_blog_search_page_num:
            print('입력한 숫자 :', blog_crawling_page_num)
            print(f"입력한 숫자가 검색 결과 페이지 수보다 큽니다. {max_blog_search_page_num}로 설정합니다.")
            blog_crawling_page_num = max_blog_search_page_num
        break
    except ValueError:
        print("유효한 숫자를 입력하세요.")

print(f"수집할 블로그 페이지 수: {blog_crawling_page_num}")

# %% [markdown]
# ## 데이터 저장 위치 설정

# %%
file_keyword = keyword.replace(' ', '_')
file_keyword

# %%
# 현재 날짜
current_date = datetime.today().strftime('%Y%m%d')
# 현재 경로 확인
code_path = os.getcwd().replace('\\', '/')
# 수집한 파일 저장할 폴더 생성
crawled_folder_path = os.path.join(code_path, 'crawled_data', 'naver_blog', current_date)
os.makedirs(crawled_folder_path, exist_ok=True)
# 저장할 파일 경로
current_datetime = datetime.today().strftime('%Y%m%d_%p_%I%M%S')
file_path = os.path.join(crawled_folder_path, f'naver_blog_{file_keyword}_{current_datetime}.xlsx')

# %% [markdown]
# ## 데이터 수집

# %%
# 페이지 수집
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
            author_blog_link_list = []

            for page_num in range(1, post_crawling_page_num + 1):
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
                    author_blog_link = post.select_one('a.author')['href']

                    title_list.append(title)
                    text_list.append(text)
                    name_author_list.append(name_author)
                    name_blog_list.append(name_blog)
                    date_list.append(date)
                    post_link_list.append(post_link)
                    author_blog_link_list.append(author_blog_link)

            # print(len(title_list), len(text_list), len(name_author_list), len(name_blog_list), len(date_list), len(post_link_list), len(author_blog_link_list))

            # 데이터 프레임 생성
            post_dict = {
                'title': title_list,
                'text': text_list,
                'name_author': name_author_list,
                'name_blog': name_blog_list,
                'date': date_list,
                'post_link': post_link_list,
                'author_blog_link': author_blog_link_list
            }
            post_df = pd.DataFrame(post_dict)
            post_df.to_excel(writer, sheet_name=tab_option, index=False)
            # print(post_df.shape)

        elif tab_option == '블로그':
            text_blog_list = []
            blog_intro_list = []
            name_author_list = []
            blog_link_list = []
            for page_num in range(1, blog_crawling_page_num + 1):
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

                # print(len(text_blog_list), len(blog_intro_list), len(name_author_list), len(blog_link_list))
            blog_dict = {
                'text_blog': text_blog_list,
                'blog_intro': blog_intro_list,
                'name_author': name_author_list,
                'blog_link': blog_link_list
            }
            blog_df = pd.DataFrame(blog_dict)
            blog_df.to_excel(writer, sheet_name=tab_option, index=False)
            # print(blog_df.shape)

    print('저장 파일 경로 :', file_path)
    print('저장완료')

# %%
driver.quit()

# %% [markdown]
# # END