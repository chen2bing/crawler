#!/usr/bin/python
# -*- coding:utf-8 -*-
import requests
from bs4 import BeautifulSoup
import json
from my_email import Email
import sys


# reload(sys)
# sys.setdefaultencoding('utf8')


if __name__ == "__main__":
    #########################################################################
    # 初始设置
    email_info = {
        'account': '***',
        'pwd': '***',
        'receivers': ['***']
    }
    login_info = {
        'usrname': '***',
        'pwd': '***'
    }
    history_file = './history.txt'
    ###########################################################################

    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
    }
    # 登录
    session = requests.session()
    post_url = 'https://passport.ustc.edu.cn/login?service=http%3A%2F%2Fyjs%2Eustc%2Eedu%2Ecn%2Fdefault%2Easp'
    login_data = {
        'model': 'uplogin.jsp',
        'service': 'http://yjs.ustc.edu.cn/default.asp',
        'warn': '',
        'showCode': '',
        'username': login_info['usrname'],
        'password': login_info['pwd'],
        'button': ''
    }
    r = session.post(post_url, headers=headers, data=login_data, timeout=5)
    # 获取讲座内容
    url = 'http://yjs.ustc.edu.cn/bgzy/m_bgxk_up.asp'
    main_page = session.get(url, timeout=5, headers=headers)
    html_src = main_page.content.decode('gb2312')
    soup = BeautifulSoup(html_src, 'html.parser')
    # 提取所有表项
    main_table = soup.find('table', attrs={'id': 'table_info'})
    all_tr = main_table.find_all('tr', attrs={'class': 'bt06'})
    # 读取报告记录
    with open(history_file, 'r') as f:
        lt_lst = json.load(f)
    # 依次处理每一行表项
    lecture_info = []
    for tr in all_tr:
        # 提取一行中的所有td
        tds = tr.find_all('td')
        # 报告的id
        lt_id = tds[1].string
        # 检查是否是新的
        if lt_id not in lt_lst:
            # 添加
            lt_lst.append(lt_id)
            # 提取完整信息，发邮件
            lecture = {
                'id': lt_id,
                'title': tds[2].find('a').string.replace('\r\n\t\t\t\t\t\t', ''),
                'speaker': tds[4].string,
                'location': (tds[6].string + '，')[:tds[6].string.find('，')],
                'time': tds[7].string,
                'ddl': tds[8].string
            }
            # 添加到讲座信息列表
            lecture_info.append(lecture)
    # 发邮件
    if len(lecture_info) > 0:
        email_title = '有新讲座可选啦~~'
        email_text = ''
        for li in lecture_info:
            email_text += '标题：' + li['title'] + '\r\n'
            email_text += '报告人：' + li['speaker'] + '\r\n'
            email_text += '地点：' + li['location'] + '\r\n'
            email_text += '时间：' + li['time'] + '\r\n'
            email_text += '选课截止时间：' + li['ddl'] + '\r\n'
            email_text += '--------------------------------------\r\n'
        my_email = Email(email_info['account'], email_info['pwd'])
        my_email.send_email(email_info['receivers'], email_title, email_text)
    # 写入新的lt_lst
    with open(history_file, 'w') as f:
        json.dump(lt_lst, f)
