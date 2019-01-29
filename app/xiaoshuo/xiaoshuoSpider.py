# -*- coding: utf-8 -*-
# @Author: longzx
# @Date: 2018-03-10 21:41:55
# @cnblog:http://www.cnblogs.com/lonelyhiker/

import requests
import sys
from bs4 import BeautifulSoup
from pymysql.err import ProgrammingError
from app.xiaoshuo.spider_tools import get_baidu_search_urls,get_one_page, update_fiction, insert_fiction, insert_fiction_content, insert_fiction_lst
from app.models import Fiction_Lst, Fiction_Content, Fiction
from random import choice
import re

#输入小说名字, 抓取小说介绍等信息
def search_fiction(name, flag=1):

    if name is None: raise Exception('小说名字必须输入！！！')

    #从百度搜索获取小说网站
    urls = get_baidu_search_urls(name)
    if len(urls) == 0:
        print("{} 找不到!".format(name))
    else:
        fiction_url = urls[0]
        
    print(fiction_url)
    html = get_one_page(fiction_url, sflag=flag)
    soup = BeautifulSoup(html, 'lxml')
    

    #获取小说封面图片
    imgs = soup.find_all('img', {'alt': name})
    fiction_img = ""
    if len(imgs): 
        fiction_img = imgs[0]
        if 'src' in fiction_img.attrs:
            fiction_img = fiction_img['src']
            if 'http' not in fiction_img:
                fiction_img = fiction_url + fiction_img

    #获取小说作家 笔名
    fiction_author = re.search(r'>作.*者[:|：](.*)<', html, re.M|re.I).group(1)
    fiction_comment = "主角狂霸拽··"
    fictions = (name, fiction_url, fiction_img, fiction_author,
                fiction_comment)
    save_fiction_url(fictions)
    return name, fiction_url

# 获取小说章节名，url
def get_fiction_list(fiction_name, fiction_url, flag=1):
    
    fiction_html = get_one_page(fiction_url, sflag=flag)
    soup = BeautifulSoup(fiction_html, 'lxml')
    # 找到目标区域
    dd_list = []
    dl_list = soup.find_all("dl")
    for dl in dl_list: 
        if len(dl.find_all("dd")) > 30:
            target_dl = dl
            dd_list = target_dl.find_all('dd')
            break
        else:
            raise Exception('{} 小说不存在！！！'.format(fiction_name))
    else:
        raise Exception('{} 小说不存在！！！'.format(fiction_name))
    
    fiction_id = fiction_url.split('/')[-2]
    # # 更新最新章节
    # update_fiction(
    #     fiction_id=fiction_id,
    #     update_time=updatetime,
    #     new_content=new_content,
    #     new_url=new_url)

    fiction_list = []
    for item in dd_list:
        fiction_lst_name = item.a.text.strip()
        fiction_lst_url = item.a['href'].split('/')[-1].strip('.html')
        fiction_real_url = fiction_url + fiction_lst_url + '.html'
        lst = (fiction_name, fiction_id, fiction_lst_url, fiction_lst_name,
               fiction_real_url)
        fiction_list.append(lst)
    return fiction_list

# 下载每一章的内容
def get_fiction_content(fiction_url, flag=1):
    fiction_id = fiction_url.split('/')[-2]
    # fiction_conntenturl = fiction_url.split('/')[-1].strip('.html')
    fc = Fiction_Content().query.filter_by(
        fiction_id=fiction_id, fiction_url=fiction_url).first()
    if fc is None:
        print('此章节不存在，需下载')
        html = get_one_page(fiction_url, sflag=flag)
        soup = BeautifulSoup(html, 'lxml')
        content = soup.find(id='content')
        f_content = str(content)
        save_fiction_content(fiction_url, f_content)
    else:
        print('此章节已存在，无需下载！！！')

# 保存小说的一些概览数据
def save_fiction_url(fictions):
    args = (fictions[0], fictions[1].split('/')[-2], fictions[1], fictions[2],
            fictions[3], fictions[4])
    insert_fiction(*args)


# 保存小说的章节列表
def save_fiction_lst(fiction_lst):
    total = len(fiction_lst)
    if Fiction().query.filter_by(fiction_id=fiction_lst[0][1]) == total:
        print('此小说已存在！！，无需下载')
        return 1
    for item in fiction_lst:
        insert_fiction_lst(*item)


# 保存单独的一章的文本
def save_fiction_content(fiction_url, fiction_content):
    fiction_id = fiction_url.split('/')[-2]
    fiction_conntenturl = fiction_url.split('/')[-1].strip('.html')
    insert_fiction_content(fiction_conntenturl, fiction_content, fiction_id)


def down_fiction_lst(f_name):
    # 1.搜索小说
    args = search_fiction(f_name, flag=0)
    # 2.获取小说目录列表
    fiction_lst = get_fiction_list(*args, flag=0)
    # 3.保存小说目录列表
    flag = save_fiction_lst(fiction_lst)
    print('下载小说列表完成！！')


def down_fiction_content(f_url):
    get_fiction_content(f_url, flag=0)
    print('下载章节完成！！')


def update_fiction_lst(f_name, f_url):
    # 1.获取小说目录列表
    fiction_lst = get_fiction_list(
        fiction_name=f_name, fiction_url=f_url, flag=0)
    # 2.保存小说目录列表
    flag = save_fiction_lst(fiction_lst)
    print('更新小说列表完成！！')
