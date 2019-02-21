# -*- coding: utf-8 -*-
# @Author: longzx
# @Date: 2018-03-08 20:56:26
"""
爬虫常用工具包
将一些通用的功能进行封装
"""
from functools import wraps
from random import choice, randint
from time import ctime, sleep, time
from urllib.parse import quote

import pymysql
import requests
from requests.exceptions import RequestException
from app.models import Fiction, Fiction_Content, Fiction_Lst
from app import db
import re

#请求头
headers = {}
headers[
    'Accept'] = 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8'
headers['Accept-Encoding'] = 'gzip, deflate, br'
headers['Accept-Language'] = 'zh-CN,zh;q=0.9'
headers['Connection'] = 'keep-alive'
headers['Upgrade-Insecure-Requests'] = '1'

agents = [
    "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.1",
    "Mozilla/5.0 (X11; CrOS i686 2268.111.0) AppleWebKit/536.11 (KHTML, like Gecko) Chrome/20.0.1132.57 Safari/536.11",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1092.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.6 (KHTML, like Gecko) Chrome/20.0.1090.0 Safari/536.6",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/19.77.34.5 Safari/537.1",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.9 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.0) AppleWebKit/536.5 (KHTML, like Gecko) Chrome/19.0.1084.36 Safari/536.5",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 5.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_8_0) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1063.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1062.0 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.1 Safari/536.3",
    "Mozilla/5.0 (Windows NT 6.2) AppleWebKit/536.3 (KHTML, like Gecko) Chrome/19.0.1061.0 Safari/536.3",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    "Mozilla/5.0 (Windows NT 6.2; WOW64) AppleWebKit/535.24 (KHTML, like Gecko) Chrome/19.0.1055.1 Safari/535.24",
    'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/64.0.3282.140 Safari/537.36'
]


def get_one_page(url, proxies=None, sflag=1):
    #获取给定的url页面
    while True:
        try:
            headers['User-Agent'] = choice(agents)
            # 控制爬取速度
            if sflag:
                print('放慢下载速度。。。。。。')
                sleep(randint(1, 3))

            print('正在下载:', url)
            if proxies:
                r = requests.get(url, headers=headers, timeout=5, proxies=proxies)
            else:
                r = requests.get(url, headers=headers, timeout=5)

        except Exception as r:
            print('errorinfo:', r)
            continue
        else:
            if r.status_code == 200:
                r.encoding = r.apparent_encoding
                print('爬取成功！！！')
                return r.text
            else:
                continue


def get_baidu_search_urls(keyword, timeout=5):
    url = u'https://www.baidu.com/baidu?wd='+quote(keyword)+'&tn=monline_dg&ie=utf-8'
    headers['User-Agent'] = choice(agents)
    r = requests.get(url ,timeout=timeout, headers=headers)
    if r.status_code==200:
        html = r.text
    else:
        html = u''
        print ('[ERROR]' + url + u'get此url返回的http状态码不是200')

    o_urls = re.findall(r'href\=\"http\:\/\/www\.baidu\.com\/link\?url\=[\w|-]+\" class\=\"c\-showurl\"', html)
    o_urls = list(set(o_urls))  # 去重
    result_urls = []
    for string in o_urls:
        url = re.match(r'href=\"(.*)\" class=(.*)', string, re.M|re.I).group(1)
        real_url = get_real(url)
        # if "qidian" not in real_url:
        if "biqu" in real_url and 'm.' not in real_url:
            result_urls.append(real_url)
    return result_urls


def get_real(o_url):
    # 获取重定向url指向的网址
    r = requests.get(o_url, allow_redirects=False)  # 禁止自动跳转
    if r.status_code == 302:
        try:
            return r.headers['location']  # 返回指向的地址
        except:
            pass
    return o_url  # 返回源地址


def append_diff_url(first, last):
    if 'www.biquge.info' in first:
        return first + last
    if 'www.biquguo.com' in first:
        return first + last

    url = first.split('//')
    first = url[-1].split('/')[0]
    result = first + last
    result = re.sub(r'\/{2,}', '/', result)
    if 'http' in url[0]:
        result = url[0] + '//' + result
    return result


# 生成fiction_id
def generate_fiction_id(fiction_name):
    if type(fiction_name) is not str: return ''
    tmp = ''
    for x in map(ord, fiction_name.replace(' ', '')):
        tmp += str(x)
    return tmp


def insert_fiction(fiction_name, fiction_id, fiction_real_url, fiction_img,
                   fiction_author, fiction_comment):
    fiction = Fiction().query.filter_by(fiction_id=fiction_id).first()
    if fiction is None:
        fiction = Fiction(
            fiction_name=fiction_name,
            fiction_id=fiction_id,
            fiction_real_url=fiction_real_url,
            fiction_img=fiction_img,
            fiction_author=fiction_author,
            fiction_comment=fiction_comment)
        db.session.add(fiction)
        db.session.commit()
    else:
        print('记录已存在，无需下载')


def insert_fiction_lst(fiction_name, fiction_id, fiction_lst_url,
                       fiction_lst_name, fiction_real_url):
    fl = Fiction_Lst().query.filter_by(
        fiction_id=fiction_id, fiction_lst_url=fiction_lst_url).first()
    if fl is None:
        fl = Fiction_Lst(
            fiction_name=fiction_name,
            fiction_id=fiction_id,
            fiction_lst_url=fiction_lst_url,
            fiction_lst_name=fiction_lst_name,
            fiction_real_url=fiction_real_url)
        db.session.add(fl)
        db.session.commit()


def insert_fiction_content(fiction_url, fiction_content, fiction_id):
    fc = Fiction_Content(
        fiction_id=fiction_id,
        fiction_content=fiction_content,
        fiction_url=fiction_url)
    db.session.add(fc)
    db.session.commit()


def update_fiction(fiction_id, update_time, new_content, new_url):
    fiction = Fiction().query.filter_by(fiction_id=fiction_id).first()
    fiction.update = update_time
    fiction.new_content = new_content
    fiction.new_url = new_url
    db.session.add(fiction)
    db.session.commit()


def delete_fiction(fiction_name):
    fiction = Fiction().query.filter_by(fiction_name=fiction_name).first()
    db.session.delete(fiction)
    db.session.commit()
