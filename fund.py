import requests
import time
from selenium import webdriver
import os
import json
from bs4 import BeautifulSoup


class Fund(object):
    def __init__(self, dir):
        self.file_dir = dir
        pass

    def __get_html_src(self, url):
        """
        从url获取源码
        :param url: URL
        :return: 源码
        """
        # 爬取首页
        headers = {
            'Cookie': 'l=v; _uuid=AEF47032-A43C-46D2-5A3A-F717F2DBA70791057infoc; buvid3=1E5CEA50-B7FD-4571-904D-46589D4AEFFA143088infoc; sid=j2bdba3z; DedeUserID=435408620; DedeUserID__ckMd5=053adfa053858233; SESSDATA=34a07e04%2C1621062412%2C7037a*b1; bili_jct=7925adca3b451ef1e8954bfa7f1e610b; bp_video_offset_435408620=441204599996697805; dy_spec_agreed=1; CURRENT_FNVAL=80; blackside_state=1; PVID=2; bp_t_offset_435408620=458153034866998414',
            'user-agent': 'Mozilla/5.0'
        }
        try:
            r = requests.get(url, headers=headers, timeout=2)
            r.encoding = 'utf-8'
        except Exception:
            print("抓取页面异常：" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()))
            return -1
        # 返回网页源码
        return r.text

    def __get_html(self, url):
        """
        对__get_html_src出现获取失败的情况，重复调用
        :param url:
        :return:
        """
        html_src = self.__get_html_src(url)
        while html_src == -1:
            print('爬取异常，稍后重试...')
            time.sleep(1)
            html_src = self.__get_html_src(url)
        return html_src

    def __write_to_file(self, file_name, data):
        """
        将数据写出
        :param file_name: 文件名
        :param data: 写入的数据
        :return:
        """
        file_path = self.file_dir + '/' + file_name
        # 如果文件不存在
        if not os.path.exists(file_path):
            with open(file_path, 'w') as of:
                of.write(data)

    def get_fund_info(self):
        """
        从天天基金爬取基金信息
        :return:
        """
        # 获取基金id列表
        fund_list = []
        file_path = self.file_dir + '/id_list.txt'
        # 如果文件存在
        if os.path.exists(file_path):
            print('基金列表已存在，开始读取')
            with open(file_path, 'r') as of:
                fund_list = json.load(of)
            print('基金列表读取成功')
        # 否则生成
        else:
            fund_list_url = 'http://fund.eastmoney.com/data/fundranking.html#tall;c0;r;s6yzf;pn10000;'
            # 设置URL
            target_url = fund_list_url
            # 设置参数
            ch_options = webdriver.ChromeOptions()
            # 不启动界面
            ch_options.add_argument('--headless')
            # 不加载图片,加快访问速度
            ch_options.add_experimental_option("prefs", {"profile.mamaged_default_content_settings.images": 2})
            # 设置为开发者模式，防止被各大网站识别出来使用了Selenium
            ch_options.add_experimental_option('excludeSwitches', ['enable-automation'])
            # ch_options.add_experimental_option("debuggerAddress", "127.0.0.1:9999")
            ch_options.add_argument('--proxy--server=127.0.0.1:8080')
            ch_options.add_argument('--disable-infobars')  # 禁用浏览器正在被自动化程序控制的提示
            ch_options.add_argument('--incognito')
            # ch_options.add_argument('--no-sandbox')
            # 启动Chrome
            wd = webdriver.Chrome(options=ch_options)
            # 切换到目标页面
            wd.get(target_url)
            # 最大等待时间为60s
            wd.implicitly_wait(60)

            tbody = wd.find_element_by_id('dbtable').find_element_by_tag_name('tbody')
            tr_lst = tbody.find_elements_by_tag_name('tr')
            tr_n = len(tr_lst)
            counter = 0
            for tr in tr_lst:
                counter += 1
                if counter % 100 == 0:
                    print('爬取基金列表进度：', counter, ' / ', tr_n)
                td_lst = tr.find_elements_by_tag_name('td')
                fund_id = td_lst[2].find_element_by_tag_name('a').text
                fund_list.append(fund_id)
            # 写出
            print('爬取基金列表完毕，开始写出')
            # 如果文件不存在
            if not os.path.exists(file_path):
                with open(file_path, 'w') as of:
                    json.dump(fund_list, of)

        # 逐个获取基金的信息
        session = requests.Session()
        headers = {
            'Cookie': 'l=v; _uuid=AEF47032-A43C-46D2-5A3A-F717F2DBA70791057infoc; buvid3=1E5CEA50-B7FD-4571-904D-46589D4AEFFA143088infoc; sid=j2bdba3z; DedeUserID=435408620; DedeUserID__ckMd5=053adfa053858233; SESSDATA=34a07e04%2C1621062412%2C7037a*b1; bili_jct=7925adca3b451ef1e8954bfa7f1e610b; bp_video_offset_435408620=441204599996697805; dy_spec_agreed=1; CURRENT_FNVAL=80; blackside_state=1; PVID=2; bp_t_offset_435408620=458153034866998414',
            'user-agent': 'Mozilla/5.0'
        }
        fund_info_lst = []
        year_lst = ['2018', '2019', '2020', '2021']
        n_fund = len(fund_list)
        counter = 0
        for fid in fund_list:
            counter += 1
            if counter % 10 == 0:
                print('已处理：', counter, ' / ', n_fund)
            fund_info = {}
            # 获取源码
            url = 'http://fundf10.eastmoney.com/jbgk_' + str(fid) + '.html'
            html_src = self.__get_html(url)
            soup = BeautifulSoup(html_src, 'html.parser')
            info_table = soup.find('table', attrs={'class': 'info w790'})
            tr_lst = info_table.find_all('tr')
            # 基金代码 index
            fund_info['index'] = str(fid).strip()
            # 基金简称 name
            fund_name = tr_lst[0].find_all('td')[-1].string
            fund_info['name'] = fund_name.strip()
            # 基金类型 type
            fund_type = tr_lst[1].find_all('td')[-1].string
            fund_info['type'] = fund_type.strip()
            # 成立日期 date
            fund_date_and_size = tr_lst[2].find_all('td')[-1].string
            fund_date = fund_date_and_size[:fund_date_and_size.find(' ')]
            fund_info['date'] = fund_date.strip()
            # 资产规模 amount
            fund_amount = str(tr_lst[3].find_all('td')[0])
            fund_amount = fund_amount[fund_amount.find('>')+1:fund_amount.find('（')]
            fund_info['amount'] = fund_amount.strip()
            # 管理人 admin
            fund_admin = tr_lst[4].find_all('td')[0].find('a').string
            fund_info['admin'] = fund_admin.strip()
            # 经理 manager
            fund_manager = tr_lst[5].find_all('td')[0].find('a').string
            fund_info['manager'] = fund_manager.strip()

            # 获取历史净值
            lsjz_lst = []
            url = 'http://danjuanapp.com/djapi/fund/nav/history/' + str(fid) + '?size=2000&page=1'
            # html_src = self.__get_html(url)
            html_src = session.get(url, headers=headers).text
            try:
                data = eval(html_src)
                total_pages = int(data['data']['total_pages'])
                for i in range(1, total_pages + 1):
                    url = 'http://danjuanapp.com/djapi/fund/nav/history/' + str(fid) + '?size=2000&page=' + str(i)
                    # html_src = self.__get_html(url)
                    html_src = session.get(url, headers=headers).text
                    data = eval(html_src)
                    lsjz_t = data['data']['items']
                    for lt in lsjz_t:
                        lsjz_date = lt['date']
                        lsjz_value = float(lt['value'])
                        lsjz_lst.append((lsjz_date, lsjz_value))
            except Exception:
                continue

            # 按年份升序排列
            lsjz_lst.sort()

            # 计算近四年的年收益率和最大回撤
            year_income = {}
            flags = {}
            for yl in year_lst:
                year_income[yl+'_s'] = 0.0
                year_income[yl+'_e'] = 0.0
                flags[yl] = False

            # 计算最大回撤
            max_drawdown = -1.0   # 最大回撤
            max_value = -1.0      # 当前历史最大净值
            for ll in lsjz_lst:
                date = ll[0]
                value = ll[1]
                # 更新当前历史最大净值和最大回撤
                if value > max_value:
                    max_value = value
                if max_value - value > max_drawdown:
                    max_drawdown = max_value - value
                # 获取指定年第一天和最后一天的收益
                its_year = date[:4]
                if its_year in year_lst:
                    if not flags[its_year]:
                        year_income[its_year+'_s'] = value
                        flags[its_year] = True
                    year_income[its_year + '_e'] = value
            # 计算指定年收益
            for yl in year_lst:
                year_income[yl] = year_income[yl+'_e'] - year_income[yl+'_s']
            # 保存
            fund_info['max_drawdown'] = round(max_drawdown, 4)
            for yl in year_lst:
                fund_info[yl] = round(year_income[yl], 4)
            # 最近一天
            last_day = lsjz_lst[-1][0]
            last_value = lsjz_lst[-1][1]
            # 计算近1年、半年、3个月、1个月的收益率
            target_days = {
                'day_1year': str(int(last_day[:4])-1) + last_day[4:],
                'day_0.5year': last_day[:5] + ('0' + str((int(last_day[5:7])+12-6) % 12))[-2:] + '-' + last_day[8:],
                'day_3month': last_day[:5] + ('0' + str((int(last_day[5:7])+12-3) % 12))[-2:] + '-' + last_day[8:],
                'day_1month': last_day[:5] + ('0' + str((int(last_day[5:7])+12-1) % 12))[-2:] + '-' + last_day[8:],
                'day_1week': last_day[:8] + ('0' + str((int(last_day[-2:])+31-7) % 31))[-2:]
            }
            incomes = {
                '1year': -1,
                '0.5year': -1,
                '3month': -1,
                '1month': -1,
                '1week': -1
            }
            for ll in lsjz_lst[::-1]:
                date = ll[0]
                value = ll[1]
                if incomes['1year'] == -1 and date <= target_days['day_1year']:
                    incomes['1year'] = last_value - value
                if incomes['0.5year'] == -1 and date <= target_days['day_0.5year']:
                    incomes['0.5year'] = last_value - value
                if incomes['3month'] == -1 and date <= target_days['day_3month']:
                    incomes['3month'] = last_value - value
                if incomes['1month'] == -1 and date <= target_days['day_1month']:
                    incomes['1month'] = last_value - value
                if incomes['1week'] == -1 and date <= target_days['day_1week']:
                    incomes['1week'] = last_value - value
            fund_info['1year'] = round(incomes['1year'], 4)
            fund_info['0.5year'] = round(incomes['0.5year'], 4)
            fund_info['3month'] = round(incomes['3month'], 4)
            fund_info['1month'] = round(incomes['1month'], 4)
            fund_info['1week'] = round(incomes['1week'], 4)
            # 保存
            fund_info_lst.append(fund_info)

        # 写出
        file_path = self.file_dir + '/fund.csv'
        with open(file_path, 'w') as of:
            output_str = '基金代码,基金简称,基金类型,成立日期,资产规模,管理人,经理,最大回撤'
            for yl in year_lst:
                output_str = output_str + ',' + yl + '年收益'
            output_str = output_str + ',近1年收益,近半年收益,近3月收益,近1月收益,近1周收益\n'
            of.write(output_str)
            for fi in fund_info_lst:
                value_lst = list(fi.values())
                fi_t = []
                for vl in value_lst:
                    fi_t.append(str(vl))
                output_str = ','.join(fi_t) + '\n'
                of.write(output_str)


if __name__ == "__main__":
    file_dir = 'D:/fund'
    fund = Fund(file_dir)
    fund.get_fund_info()