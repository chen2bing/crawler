"""
爬取顶会论文
注：运行时关闭代理
"""
import requests
import re
import time
import os
import json
from bs4 import BeautifulSoup


class GetPaperInfo(object):
    def __init__(self, fpath, syear, eyear):
        """
        初始化
        :param fpath: 文件路径
        :param syear: 开始年份
        :param eyear: 终止年份
        """
        self.file_path = fpath
        self.start_year = syear
        self.end_year = eyear

    def __get_html(self, url):
        """
        获取相应提问的网页源码
        :param url: 网页的Url
        :return: 网页源码（str）
        """
        headers = {
            'Cookie': '',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.128 Safari/537.36'
        }
        try:
            r = requests.get(url, headers=headers, timeout=10)
            r.encoding = 'utf-8'
        except Exception:
            print("抓取页面异常")
            return -1
        # 返回网页源码
        return r.text

    def __get_html_from_biying(self, title):
        """
        从必应学术获取该title的查询结果
        :param title: paper的title
        :return:
        """
        # 空格、冒号替换
        title_str = str(title).replace(' ', '+').replace(':', '%3A').replace('&', '%26')
        # 获取网页源码
        url = 'http://cn.bing.com/search?q=' + title_str
        data_src = self.__get_html(url)
        while data_src == -1:
            print('必应查询出错')
            print('url', url)
            time.sleep(2)
            data_src = self.__get_html(url)
        # 取前5个结果（标题）
        rst = re.findall(r'<h2>.*?</h2>', data_src)
        result = ';'.join(rst[:6])
        # 返回
        return result

    def __output(self, fpath, lst):
        """
        写出列表
        :param fpath: 文件路径
        :param lst: 列表
        :return:
        """
        # 检测路径，如果有具体文件名，创建之前的路径
        final_path = fpath
        if final_path.find('.') != -1:
            # 存在具体文件名，去掉文件
            final_path = final_path[:final_path.rfind('/')]
        # 创建目录
        folder = os.path.exists(final_path)
        if not folder:
            os.makedirs(final_path)
        # 写入
        with open(fpath, 'w') as f:
            json.dump(lst, f)

    def __get_paperinfo_from_ieee(self, data_src, paper_title):
        """
        从网页源码中提取ieee网址，访问并获取paper信息，返回
        :param data_src: 网页源码
        :param paper_title: 论文题目
        :return: paper_info（字典），包括标题、作者、摘要、关键词、doi。出错时返回-1
        """
        # 提取url
        rst = re.search(r'"https://ieeexplore.*?"', data_src)
        if rst:
            # 提取ieee链接
            url = str(rst.group(0)[1:-1]).replace('https', 'http')
            # 获取源码
            data_src = self.__get_html(url)
            while data_src == -1:
                print('ieee爬取出错')
                print('url', url)
                time.sleep(2)
                data_src = self.__get_html(url)
            # 提取paper信息
            rst = re.search(r'{"userInfo".*?};', data_src)
            if rst:
                results = {}  # paper信息
                # 提取paper信息
                paper_info = eval(rst.group(0)[:-1].replace('true', 'True').replace('false', 'False'))
                # 核查标题，如果不匹配，返回
                this_title = paper_info['displayDocTitle']
                if this_title != paper_title:
                    return -1
                results['title'] = this_title
                # 作者
                authors = []
                for ai in paper_info['authors']:
                    authors.append(ai['name'])
                results['authors'] = ','.join(authors)
                # 摘要
                results['abstract'] = paper_info['abstract']
                # 关键词
                keywords_lst = paper_info['keywords']
                for kl in keywords_lst:
                    if kl['type'].find('Author') != -1:
                        results['keywords'] = ','.join(kl['kwd'])
                # doi
                results['doi'] = paper_info['doi']
                # 返回
                return results
            else:
                print('ieee提取paper信息出错')
                return -1
        else:
            # 网页数据中没有ieee链接
            return -1

    def __get_paperinfo_from_acm(self, data_src, paper_title):
        """
        从网页数据中提取acm网址，访问并提取paper信息，返回
        :param data_src: 网页数据
        :param paper_title: 论文题目
        :return: paper_info（字典），包括：题目、作者、doi、摘要
        """
        # 提取acm网址
        rst = re.search(r'"https://dl.*?"', data_src)
        if rst:
            # 截取doi
            url = str(rst.group(0)[1:-1])
            doi_index = url.find('/10')
            url = 'http://dl.acm.org/doi' + url[doi_index:]
            # 获取源码
            data_src = self.__get_html(url)
            while data_src == -1:
                time.sleep(2)
                data_src = self.__get_html(url)
            # paper信息
            paper_info = {}
            # 解析html
            soup = BeautifulSoup(data_src, "html.parser")
            # 获取题目
            try:
                citation_e = soup.find('div', attrs={'class': 'citation'})
                this_title = citation_e.find('h1').string
                if this_title != paper_title:
                    return -1
                paper_info['title'] = this_title
                # 获取作者
                authors = []
                authors_e = citation_e.find('div', attrs={'id': 'sb-1'}).find_all('li', attrs={'class': 'loa__item'})
                for ae in authors_e:
                    author_name = ae.find('span', attrs={'class': 'loa__author-name'}).find('span').text
                    authors.append(author_name)
                paper_info['authors'] = ','.join(authors)
                # doi
                doi = citation_e.find('a', attrs={'class': 'issue-item__doi'}).text
                paper_info['doi'] = doi
                # 摘要
                abstract_e = soup.find('div', attrs={'class': 'hlFld-Abstract'})\
                    .find('div', attrs={'class': 'abstractSection abstractInFull'})\
                    .find('p')
                abstract = abstract_e.text
                paper_info['abstract'] = abstract
            except Exception:
                print('html解析失败')
                return -1
            # 返回
            return paper_info
        else:
            # 无acm网址
            return -1

    def __get_paperinfo(self, ptype, year):
        """
        从dblp.org网站上获得某年某会议的接收paper，然后爬取
        :param ptype: 类型，如infocom
        :param year: 年份，如2018
        :return:
        """
        # 输出提示信息
        pstr = '开始爬取' + str(year) + '年' + ptype + '论文'
        print(pstr)
        # 如果文件存在，直接终止
        file_path = self.file_path + ptype + '-' + str(year) + '.txt'
        if os.path.exists(file_path):
            print('该年该会议已爬取过')
            return
        title_lst = []  # paper的title列表
        defeat_lst = []   # 爬取失败的title列表
        # 获取某年某会议的网站源码
        url = 'http://dblp.org/db/conf/' + ptype + '/' + ptype + str(year) + '.html'
        data_src = self.__get_html(url)
        while data_src == -1:
            time.sleep(2)
            data_src = self.__get_html(url)
        # html解析
        soup = BeautifulSoup(data_src, "html.parser")
        # 分情况提取
        if ptype in ['infocom', 'sigcomm']:
            # 获取所有paper的title
            span_e = soup.find_all('span', attrs={'class': 'title'})[1:]
            for se in span_e:
                title_lst.append(se.text[:-1])
        elif ptype in ['mobicom']:
            cite_e = soup.find_all('cite', attrs={'class': 'data'})
            for ce in cite_e:
                page_e = ce.find_all('span', attrs={'itemprop': 'pagination'})
                # 有页码
                if len(page_e) > 0:
                    page_str = page_e[0].text
                    # 非单页码，有范围，例如1-3
                    if page_str.find('-') != -1:
                        page_lst = page_str.split('-')
                        # 处理冒号
                        for pi in range(len(page_lst)):
                            pl_i = page_lst[pi].find(':')
                            if pl_i != -1:
                                page_lst[pi] = page_lst[pi][pl_i+1:]
                        # 计算论文页数
                        page_dif = int(page_lst[1]) - int(page_lst[0])
                        # 多页，是paper
                        if page_dif > 5:
                            title_e = ce.find('span', attrs={'class': 'title'})
                            title_lst.append(title_e.text[:-1])
        # 计数，输出进度
        paper_sum = len(title_lst)
        count = 0
        # 开始爬取
        paper_info_lst = []
        for t in title_lst:
            # 从必应获取搜索结果
            data_src = self.__get_html_from_biying(t)
            # 提取ieee网址
            paper_info = self.__get_paperinfo_from_ieee(data_src, t)
            if paper_info == -1:
                # 提取acm网址
                paper_info = self.__get_paperinfo_from_acm(data_src, t)
            if paper_info == -1:
                # ieee和acm都没有
                print(t, '无法爬取（不在ieee或acm数据库）')
                defeat_lst.append(t)
            else:
                paper_info['type'] = ptype
                paper_info['year'] = year
                paper_info_lst.append(paper_info)
                count += 1
                pstr = '已爬取' + str(count) + '/' + str(paper_sum) + '篇'
                print(pstr)
        # 写出爬取成功的paper信息
        self.__output(file_path, paper_info_lst)
        # 写出爬取失败的paper的title
        file_path = self.file_path + ptype + '-' + str(year) + '-defeat.txt'
        self.__output(file_path, defeat_lst)
        # 输出提示信息
        crawl_sum = len(paper_info_lst)
        pstr = '成功爬取' + str(crawl_sum) + '/' + str(paper_sum) + '篇'
        print(pstr)

    def start(self):
        # 年份范围
        sy = self.start_year
        ey = self.end_year
        # 按年份爬取
        for i in range(sy, ey+1):
            # 获取infocom历年paper
            self.__get_paperinfo('infocom', i)
            # 获取sigcomm历年paper
            self.__get_paperinfo('sigcomm', i)
            # 获取mobicom历年paper
            self.__get_paperinfo('mobicom', i)


if __name__ == "__main__":
    path = 'D:/paper/'
    start_year = 2015
    end_year = 2017
    paper = GetPaperInfo(path, start_year, end_year)
    paper.start()

