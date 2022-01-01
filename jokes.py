"""
    功能：爬取知乎关于笑话的提问下的前100个回答，事先提供提问的ID列表
    作者：cbb
    日期：2020/8/18
"""
import requests
from bs4 import BeautifulSoup
import re


class Jokes(object):
    def __init__(self, zh_cookie, question_index_list, output_file_path):
        """
        初始化
        :param zh_cookie: 知乎的cookie
        :param question_index_list:  爬取网页的列表
        :param output_file_path:  文件输出路径
        """
        self.cookie = zh_cookie
        self.index_list = question_index_list
        self.jokes_list = []
        self.file_path = output_file_path

    def __get_html(self, cookie, url):
        """
        获取相应提问的网页源码
        :param url: 网页的Url
        :param cookie: 网站cookie
        :return: 网页源码（str）
        """
        headers = {
            'Cookie': cookie,
            'user-agent': 'Mozilla/5.0'
        }
        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.encoding = 'utf-8'
        except:
            print("抓取页面异常")
            return -1
        # 返回网页源码
        return r.text

    def __get_jokes_from_html(self, html_code):
        """
        从网页源码中提取出笑话
        :param html_code: 网页源码
        :return:
        """
        soup = BeautifulSoup(html_code, 'html.parser')
        # 获取提问的标题
        title = soup.find('title').string
        self.jokes_list.append(title)

        # <body>中的回答与<script>中的重复，所以只获取<script>中所有回答
        answers_from_script = soup.find('script', attrs={'id': 'js-initialData'}).string
        # 用正则表达式找出所有段落
        all_p = re.findall(r'\\u003Cp\\u003E.*?\\u003C\\u002Fp\\u003E', answers_from_script)
        # 遍历、存储
        for pt in all_p:
            joke_str = pt[13:-19]
            if len(joke_str) > 5 and joke_str not in self.jokes_list:
                self.jokes_list.append(joke_str)

    def __get_jokes_from_json(self, json_code):
        """
        从网页动态加载的json中提取笑话
        :param json_code: json源码
        :return: 笑话（str列表）
        """
        # 用正则表达式找出所有段落
        all_p = re.findall(r'\\u003cp\\u003e.*?\\u003c/p\\u003e', json_code)
        # 遍历、存储
        for pt in all_p:
            joke_str = pt[13:-14]
            if len(joke_str) > 5 and joke_str not in self.jokes_list:
                self.jokes_list.append(joke_str)

    def __output(self):
        """
        将保存的笑话写出
        :return:
        """
        file_name = self.jokes_list[0]
        # 过滤winsows文件名的非法字符
        file_name = re.sub(r'[\/:*?"<>|]', '', file_name)
        # 开始写出
        print("提取完成，开始写出（" + file_name + ")")
        file = self.file_path + file_name + '.txt'
        with open(file, 'w', encoding='utf-8') as f:
            for jt in self.jokes_list:
                # 清理
                joke_str = jt.strip()
                # 如果含有特殊字符（链接），跳过
                rst = re.search(r'(\\u003Ca|\\u003ca)', joke_str)
                if rst:
                    continue
                # 将<br>替换为'\n'
                joke_str = re.sub(r'\\u003cbr/\\u003e', '\n', joke_str)
                # 如果含有数字标号、&、<b>、<i>，去掉
                joke_str = re.sub(r'(\\u003cb\\u003e|\\u003Cb\\u003E|\\u003c/b\\u003e|\\u003C\\u002Fb\\u003E|'
                                  r'\\u0026.*;|\\u003ci\\u003e|\\u003c/i\\u003e|\d.*、|\d.*\.|\d )', '', joke_str)

                # 写入文件中
                joke_str = joke_str.strip() + "\n"
                if len(joke_str) > 5:
                    f.write(joke_str)

        # 清理笑话缓冲池
        print("写入完成（" + file_name + ")")
        self.jokes_list.clear()
        return True

    def start(self):
        """
        开始爬取
        :return:
        """
        # 获取爬取的问题个数
        qst_sum = len(self.index_list)
        qst_n = 0
        # 遍历整个提问列表，依次提取
        for index in self.index_list:
            print("开始提取")
            # 获取网页源码
            url = 'https://zhihu.com/question/' + str(index)
            html_code = self.__get_html(self.cookie, url)
            # 从网页源码中提取笑话
            self.__get_jokes_from_html(html_code)
            # 从动态加载的json中提取笑话
            for offset in range(1, 21):
                url = 'https://www.zhihu.com/api/v4/questions/' + str(index) + \
                      '/answers?include=data%5B%2A%5D.is_normal%2Cadmin_closed_comment%2Creward_info%2Cis_collapsed%2Cannotation_action%2Cannotation_detail%2Ccollapse_reason%2Cis_sticky%2Ccollapsed_by%2Csuggest_edit%2Ccomment_count%2Ccan_comment%2Ccontent%2Ceditable_content%2Cvoteup_count%2Creshipment_settings%2Ccomment_permission%2Ccreated_time%2Cupdated_time%2Creview_info%2Crelevant_info%2Cquestion%2Cexcerpt%2Crelationship.is_authorized%2Cis_author%2Cvoting%2Cis_thanked%2Cis_nothelp%2Cis_labeled%2Cis_recognized%2Cpaid_info%2Cpaid_info_content%3Bdata%5B%2A%5D.mark_infos%5B%2A%5D.url%3Bdata%5B%2A%5D.author.follower_count%2Cbadge%5B%2A%5D.topics&limit=5&offset=' \
                      + str(offset*5) + '&platform=desktop&sort_by=default'
                json_code = self.__get_html(self.cookie, url)
                self.__get_jokes_from_json(json_code)
            # 写出
            if not self.__output():
                return False
            # 计数+1并打印进度
            qst_n += 1
            print("已完成：" + str(qst_n) + "/" + str(qst_sum))


if __name__ == "__main__":
    # 知乎的Cookie，其实并不需要
    zhihu_cookie = ''
    # 提问的数字ID
    questions_list = [341002197, 364543542, 23547779]
    # 输出文件存储路径
    file_path = "D:/jokes/"

    my_jokes = Jokes(zhihu_cookie, questions_list, file_path)
    my_jokes.start()
