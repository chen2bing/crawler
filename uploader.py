"""
爬取up主的粉丝量、观看量和点赞数
up主id来自每周必看
"""
import requests
import time
import os
import re
import json


class Uploader(object):
    def __init__(self, path):
        """
        初始化up主id列表
        :param path: 数据存储目录
        """
        self.ups = {}  # up主信息，键为id，值为name
        self.path = path

    def __get_html(self, url):
        """
        获取相应提问的网页源码
        :param url: 网页的Url
        :return: 网页源码（str）
        """
        headers = {
            'Cookie': '_uuid=A4C890AC-03D5-98E0-58E6-00E56DE99EBC45439infoc; buvid3=E0A38B13-3DA7-4EE5-866B-994B4757E7EE18535infoc; fingerprint=e2c8edf8db06a5e0533d32f2050df182; buvid_fp=E0A38B13-3DA7-4EE5-866B-994B4757E7EE18535infoc; buvid_fp_plain=E0A38B13-3DA7-4EE5-866B-994B4757E7EE18535infoc; SESSDATA=f8fa26fe,1632842974,600e9*41; bili_jct=abda794c35c596e8f1cff2d6be86152a; DedeUserID=435408620; DedeUserID__ckMd5=053adfa053858233; sid=c6l0io7v',
            'user-agent': 'Mozilla/5.0'
        }
        try:
            r = requests.get(url, headers=headers, timeout=30)
            r.encoding = 'utf-8'
        except Exception:
            print("抓取页面异常")
            return -1
        # 返回网页源码
        return r.text

    def __makedir(self, fpath):
        """
        根据路径创建文件目录
        :param fpath: 路径
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

    def __create_upinfo(self):
        """
        根据每周必看生成up主信息文件，包括id和名称
        :return:
        """
        up_info = {}
        # 获取总期数
        url = 'http://api.bilibili.com/x/web-interface/popular/series/list'
        data_src = self.__get_html(url)
        total_index = data_src.find('number')
        total = int(data_src[total_index+8: total_index+11])
        # 逐期查找up
        for i in range(1, total + 1):
            # 获取该期的数据
            url = 'http://api.bilibili.com/x/web-interface/popular/series/one?number=' + str(i)
            data_src = self.__get_html(url)
            # 获得该期所有的id和名字
            all_id = re.findall(r'mid.*?"name":".*?",', data_src)
            for idt in all_id:
                stt = idt[5:-2]
                index1 = stt.find(',')
                id_str = stt[:index1]
                index2 = stt.rfind('"')
                name_str = stt[index2+1:]
                up_info[id_str] = name_str
        # 写出
        fpath = self.path + '/upinfo/upinfo.txt'
        self.__makedir(fpath)
        with open(fpath, 'w') as f:
            json.dump(up_info, f)

    def __crawl(self):
        """
        爬取
        :return:
        """
        results = []
        upids = list(self.ups.keys())[:100]
        counter = 0
        # 遍历up主id列表
        for index in upids:
            counter += 1
            if counter % 100 == 0:
                pstr = '已爬取' + str(counter) + '个up'
                print(pstr)
            # 整理存储
            up_info = {
                'id': '',
                'name': '',
                'follower': '',
                'view': '',
                'likes': ''
            }
            # 获取粉丝数
            url = 'http://api.bilibili.com/x/relation/stat?vmid=' + str(index) + '&jsonp=jsonp'
            upfl_src = self.__get_html(url)
            rst = re.search(r'follower.*?}', upfl_src)
            if rst:
                up_info['follower'] = rst.group(0)[10:-1]
            # 获取播放数和喜欢数
            url = 'http://api.bilibili.com/x/space/upstat?mid=' + str(index) + '&jsonp=jsonp'
            upvl_src = self.__get_html(url)
            rst = re.search(r'view.*?}', upvl_src)
            if rst:
                up_info['view'] = rst.group(0)[6:-1]
            rst = re.search(r'likes.*?}', upvl_src)
            if rst:
                up_info['likes'] = rst.group(0)[7:-1]
            # 填写id
            up_info['id'] = index
            # 获取名字
            up_info['name'] = self.ups[index]
            # 添加至results列表
            results.append(up_info)
        # 获取当前时间
        current_day = time.strftime("%Y-%m-%d", time.localtime())
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        # 写出
        fpath = self.path + '/data/' + current_day + '.csv'
        self.__makedir(fpath)
        with open(fpath, 'w', encoding='gb18030') as f:
            f.write('time,id,name,follower,view,likes\n')
            for dt in results:
                # 格式：当前时间, id, name, follower, view, likes
                line = current_time + ',' + dt['id'] + ',' + dt['name'] + ',' + dt['follower'] + \
                       ',' + dt['view'] + ',' + dt['likes'] + '\n'
                f.write(line)

    def start(self):
        """
        启动
        :return:
        """
        fpath = self.path + '/upinfo/upinfo.txt'
        # 不存在up主id文件，开始爬取
        folder = os.path.exists(fpath)
        if not folder:
            # 没有up主信息文件，现在生成
            print('无up主信息，开始爬取')
            self.__create_upinfo()
            print('up主id整理完毕')
        # 读取up主id列表
        print('开始读取up主id')
        with open(fpath) as f:
            self.ups = json.load(f)
        print('id读取完毕，开始爬取')
        # 爬取
        self.__crawl()


if __name__ == "__main__":
    file_path = './up'
    ups = Uploader(file_path)
    ups.start()
