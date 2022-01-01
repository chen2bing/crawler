"""
爬取热门和排行榜
"""
import requests
import os
import time


class HotRank(object):
    def __init__(self, fpath):
        """
        初始化
        :param fpath: 文件目录
        """
        self.path = fpath

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
            r = requests.get(url, headers=headers, timeout=3)
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

    def __crawl_hot(self):
        """
        爬取热门视频，包括时间、视频名称、视频号、类型、up主名字、up主id、播放量、点赞、投币、收藏、分享数
        :return:
        """
        results = []
        # 当前时间
        current_time = time.strftime("%Y-%m-%d %H-%M", time.localtime())
        for i in range(1, 11):
            url = 'http://api.bilibili.com/x/web-interface/popular?ps=20&pn=' + str(i)
            data_src = self.__get_html(url)
            while data_src == -1:
                time.sleep(1)
                data_src = self.__get_html(url)
            # 提取视频列表
            start_i = data_src.find('[')
            end_i = data_src.rfind(']')
            mv_lst_str = data_src[start_i:end_i+1]
            mv_lst = eval(mv_lst_str)
            # 逐个处理
            for mvt in mv_lst:
                mv_info = {}
                # 时间
                mv_info['time'] = current_time
                # 视频名称、bv号、类型
                mv_info['title'] = mvt['title'].replace(',', '，')
                mv_info['mv_id'] = mvt['bvid']
                mv_info['mv_type'] = mvt['tname']
                # up主id、名字
                up_info = mvt['owner']
                mv_info['up_name'] = up_info['name']
                mv_info['up_id'] = up_info['mid']
                # 点赞、投币、收藏、分享数
                mv_stat = mvt['stat']
                mv_info['view'] = mv_stat['view']
                mv_info['like'] = mv_stat['like']
                mv_info['coin'] = mv_stat['coin']
                mv_info['favorite'] = mv_stat['favorite']
                mv_info['share'] = mv_stat['share']
                results.append(mv_info)
        # 写出
        fpath = self.path + '/hot/' + current_time + '.csv'
        self.__makedir(fpath)
        with open(fpath, 'w', encoding='gb18030') as f:
            f.write('time,mv_title,mv_id,mv_type,up_name,up_id,view,like,coin,favorite,share\n')
            for dt in results:
                # 格式：time,mv_title,mv_id,mv_type,up_name,up_id,view,like,coin,favorite,share
                lst = list(dt.values())
                lst = [str(x) for x in lst]
                line = ','.join(lst) + '\n'
                f.write(line)

    def __crawl_rank(self):
        """
        爬取排行榜，包括时间、排名、视频名称、视频号、类型、up主名字、up主id、播放量、点赞、投币、收藏、分享数
        :return:
        """
        results = []
        # 当前时间
        current_time = time.strftime("%Y-%m-%d %H-%M", time.localtime())
        url = 'http://api.bilibili.com/x/web-interface/ranking/v2?rid=0&type=all'
        data_src = self.__get_html(url)
        while data_src == -1:
            time.sleep(1)
            data_src = self.__get_html(url)
        # 提取视频列表
        start_i = data_src.find('[')
        end_i = data_src.rfind(']')
        mv_lst_str = data_src[start_i:end_i + 1]
        mv_lst = eval(mv_lst_str)
        # 逐个处理
        rank = 1
        for mvt in mv_lst:
            mv_info = {}
            # 时间
            mv_info['time'] = current_time
            # 排名
            mv_info['rank'] = rank
            # 视频名称、bv号、类型
            mv_info['title'] = mvt['title'].replace(',', '，')
            mv_info['mv_id'] = mvt['bvid']
            mv_info['mv_type'] = mvt['tname']
            # up主id、名字
            up_info = mvt['owner']
            mv_info['up_name'] = up_info['name']
            mv_info['up_id'] = up_info['mid']
            # 点赞、投币、收藏、分享数
            mv_stat = mvt['stat']
            mv_info['view'] = mv_stat['view']
            mv_info['like'] = mv_stat['like']
            mv_info['coin'] = mv_stat['coin']
            mv_info['favorite'] = mv_stat['favorite']
            mv_info['share'] = mv_stat['share']
            results.append(mv_info)
            rank += 1
        # 写出
        fpath = self.path + '/rank/' + current_time + '.csv'
        self.__makedir(fpath)
        with open(fpath, 'w', encoding='gb18030') as f:
            f.write('time,rank,mv_title,mv_id,mv_type,up_name,up_id,view,like,coin,favorite,share\n')
            for dt in results:
                # 格式：time,rank,mv_title,mv_id,mv_type,up_name,up_id,view,like,coin,favorite,share
                lst = list(dt.values())
                lst = [str(x) for x in lst]
                line = ','.join(lst) + '\n'
                f.write(line)
        pass

    def start(self):
        """
        启动
        :return:
        """
        self.__crawl_hot()
        self.__crawl_rank()


if __name__ == "__main__":
    path = 'D:/up'
    hr = HotRank(path)
    hr.start()
