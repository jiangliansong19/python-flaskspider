import requests
import sys
from bs4 import BeautifulSoup
from pymysql.err import ProgrammingError
from app.xiaoshuo.spider_tools import *
from app.models import Fiction_Lst, Fiction_Content, Fiction
from random import choice
import re


# 输入小说名字, 抓取小说介绍等信息
def search_fiction(name, flag=1):

    if name is None: raise Exception('小说名字必须输入！！！')

    # 从百度搜索获取小说网站
    urls = get_baidu_search_urls(name)
    if len(urls) == 0:
        raise Exception("{} 找不到!".format(name))
    else:
        fiction_url = choice(urls)
        print(fiction_url)


    html = get_one_page(fiction_url, sflag=flag)
    soup = BeautifulSoup(html, 'lxml')

    # 获取小说封面图
    imgs = soup.find_all('img', {'alt': name})
    fiction_img = ""
    if len(imgs): 
        fiction_img = imgs[0]
        if 'src' in fiction_img.attrs:
            fiction_img = fiction_img['src']
            if 'http' not in fiction_img:
                fiction_img = fiction_url + fiction_img

    # 获取小说作家笔名
    fiction_author = "未知"
    fiction_author_search = re.search(r'>作.*者[:|：](.*?)<', html, re.M|re.I)
    if fiction_author_search:
        fiction_author = fiction_author_search.group(1)

    fiction_comment = "主角狂霸拽··"

    insert_fiction(name, generate_fiction_id(name), fiction_url, fiction_img, fiction_author, fiction_comment)
    return name, fiction_url


# 小说章节列表
def get_fiction_list(fiction_name, fiction_url, flag=1):
    
    fiction_html = get_one_page(fiction_url, sflag=flag)
    chapter_list = []
    a_list = re.findall(r'<a href=\".*?\.html\".*?>第.*?章.*?</a>', fiction_html)
    for obj in a_list:
        x = re.search(r'<a href=\"(.*?)\.html\".*?>第(.*?)章(.*?)</a>', obj)
        chapter_name = '第%s章%s' % (x.group(2),x.group(3))
        chapter_url = (x.group(1) + '.html')
        chapter_real_url = append_diff_url(fiction_url, chapter_url)
        chapter = (fiction_name, generate_fiction_id(fiction_name), chapter_url.replace('/','_'), chapter_name, chapter_real_url)
        chapter_list.append(chapter)

    if len(chapter_list): print(chapter_list[0])

    if len(chapter_list) == 0:
        delete_fiction(fiction_name)
        raise Exception('{} 小说不存在！！！'.format(fiction_name))
    return chapter_list

    # # 更新最新章节
    # update_fiction(
    #     fiction_id=fiction_id,
    #     update_time=updatetime,
    #     new_content=new_content,
    #     new_url=new_url)


# 下载每一章的内容
def get_fiction_content(fiction_id, chapter_real_url, chapter_url, flag=1):
    print('此章节不存在，需下载')
    html = get_one_page(chapter_real_url, sflag=flag)
    soup = BeautifulSoup(html, 'lxml')
    content = soup.find(id='content')
    if not content:
        content = soup.find(id='book_text')
    f_content = str(content)
    insert_fiction_content(chapter_url, f_content, fiction_id)


# 保存小说的章节列表
def save_fiction_lst(fiction_lst):
    total = len(fiction_lst)
    if Fiction().query.filter_by(fiction_id=fiction_lst[0][1]) == total:
        print('此小说已存在！！，无需下载')
        return 1
    for item in fiction_lst:
        insert_fiction_lst(*item)


def down_fiction_lst(f_name):
    # 1.搜索小说
    args = search_fiction(f_name, flag=0)
    # 2.获取小说目录列表
    fiction_lst = get_fiction_list(*args, flag=0)
    # 3.保存小说目录列表
    flag = save_fiction_lst(fiction_lst)
    print('下载小说列表完成！！')


def down_fiction_content(fiction_id, f_real_url, f_url):
    get_fiction_content(fiction_id, f_real_url, f_url, flag=0)
    print('下载章节完成！！')


def update_fiction_lst(f_name, f_url):
    # 1.获取小说目录列表
    fiction_lst = get_fiction_list(
        fiction_name=f_name, fiction_url=f_url, flag=0)
    # 2.保存小说目录列表
    flag = save_fiction_lst(fiction_lst)
    print('更新小说列表完成！！')
