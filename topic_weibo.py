# 根据话题爬取微博，可以设定话题和爬取页数

import requests
import re
import time
from pyquery import PyQuery as pq
import pymongo
import random
import datetime

# 设定请求头
headers = {
    'User-agent': '',
    'Cookie': '',
}

# 请求网页
def get_html(url):
    response = requests.get(url, headers=headers)
    if response.status_code == 200:  # 状态为200即为爬取成功
        html = response.text
        return html
    else:
        print('访问出错')
        return None

# 获取微博信息
def get_weibo(url, topic):
    html = get_html(url)
    doc = pq(html)
    items = doc.find('.card').items()
    for item in items:
        # 去除空值结果
        if item.find('.content .txt').text() == '':
            pass
        else:
            # 对日期清洗
            str_p = item.find('.from').text()
            if '年' in str_p:
                pattern = re.compile('(\d+年\d+月\d+日 \d+:\d+)')
                str_p = str(re.findall(pattern, str_p)[0])
                str_p = str_p.replace('年', '-')
                str_p = str_p.replace('月', '-')
                str_p = str_p.replace('日', '')
                date = datetime.datetime.strptime(str_p, '%Y-%m-%d %H:%M')
            elif '月' in str_p:
                pattern = re.compile('(\d+月\d+日 \d+:\d+)')
                str_p = str(re.findall(pattern, str_p)[0])
                str_p = str_p.replace('月', '-')
                str_p = str_p.replace('日', '')
                str_p = '2022-' + str_p
                date = datetime.datetime.strptime(str_p, '%Y-%m-%d %H:%M')
            elif '-' in str_p:
                try:
                    pattern = re.compile('\d+\-\d+\-\d+ \d+:\d+')
                    str_p = str(re.findall(pattern, str_p)[0])
                    date = datetime.datetime.strptime(str_p, '%Y-%m-%d %H:%M')
                except:
                    print('可能出错：', str_p) #打印出错结果
                    date = None
            else:
                print('可能出错：', str_p) #打印出错结果
                date = None
            # 日期清洗结束，定义爬取结果
            result = {
                '微博内容': item.find('.content .txt').text().replace('\n', ' ').replace('\ue627', ' '), # 将微博内容中的特殊符号变为空格
                '发布时间': date,
                '用户名': item.find('.content .info .name').text(),
                '点赞数': item.find('.card-act ul li').eq(2).text().replace('赞', '0'),
                '评论数': item.find('.card-act ul li').eq(1).text().replace('评论', '0'),
                '转发数': item.find('.card-act ul li').eq(0).text().replace('转发', '0'),
                '话题': topic,
            }
            print(result)
            save_to_mongo(result)

# 保存数据，储存至MongoDB
def save_to_mongo(result):
    # 设定Mongo参数
    MONGO_URL = 'localhost'
    MONGO_DB = 'weibo'
    MONGO_COLLECTION = 'weibo_content'
    client = pymongo.MongoClient(MONGO_URL)
    db = client[MONGO_DB]
    try:
        # 设定哪几项重复则不上传
        if db[MONGO_COLLECTION].update_one({"微博内容": result['微博内容'], '发布时间': result['发布时间']}, {'$set': result}, upsert=True):
            print(' 存储到 MongoDB 成功 ')
    except Exception:
        print(' 存储到 MongoDB 失败 ')

if __name__ == '__main__':
    # 设定爬取话题
    topics = ['最让你心疼的女二号', '影视剧副线cp有多甜']
    # 设定爬取页数范围
    page = range(1, 5)
    for t in topics:
        print('正在爬取话题#{t}#'.format(t=t))
        for p in page:
            print('正在爬取第{p}页'.format(p=p))
            url = 'https://s.weibo.com/weibo?q=%23{t}%23&page={p}'.format(t=t, p=p)
            get_weibo(url, t)
            # 设定每爬一页的等待时间
            time.sleep(random.randint(2, 7))
