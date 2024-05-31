
# from fubon_neo.sdk import FubonSDK, Order
# from fubon_neo.constant import TimeInForce, OrderType, PriceType, MarketType, BSAction
from fubon_neo.sdk  import FubonSDK

import sys
import os
# 把当前文件所在文件夹的父文件夹路径加入到PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from normal import method


from IPython.display import display, clear_output
from urllib.request import urlopen
import pandas
pandas.set_option("display.max_rows", 1000)    #設定最大能顯示1000rows
pandas.set_option("display.max_columns", 1000) #設定最大能顯示1000columns
# from pylab import mpl
# mpl.rcParams['font.sans-serif'] = ['Microsoft YaHei']  
# # 指定默認字形：解決plot不能顯示中文問題
# mpl.rcParams['axes.unicode_minus'] = False
import datetime
import requests
import sched
import time
import json

from bs4 import BeautifulSoup
import re

# selenium
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.select import Select   # 使用 Select 對應下拉選單
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import csv

g_schedule = sched.scheduler(time.time, time.sleep)

def initialization():

    try: 

        path = method.PathGetCurrent()

        method.FileDelete(method.PathJoin(path, 'PASS'))
        method.FileDelete(method.PathJoin(path, 'FAIL'))
        method.FileDelete(method.PathJoin(path, 'STOP'))
        method.FileDelete(method.PathJoin(path, 'RELOAD'))
        
        config = method.PyConfigParser()
        config.read(method.PathJoin(path, 'config.ini'))

        #[env]
        output_file_name = method.ConfigGet(config, 'env', 'output_file_name', 'output.txt')
        method.FileDelete(method.PathJoin(path, output_file_name))

        #[logger]
        logger_file_name = method.ConfigGet(config, 'logger', 'file_name', 'sys.log')
        method.FileDelete(method.PathJoin(path, logger_file_name))

        return config, path
    
    except Exception as e:
        method.Logging(config, path, 'ERROR', '{}'.format(e))
        raise

def tableColor(val):
    if val > 0:
        color = 'red'
    elif val < 0:
        color = 'green'
    else:
        color = 'white'
    return 'color: %s' % color

def run_1(config, path, df_table, **kwargs):#基本市況
    
    try: 

        result = False
        data = ''

        for i in range(1):

            # clear_output(wait=True)

            if isinstance(df_table, pandas.DataFrame) == False:
                df_table = pandas.read_csv('list.txt', header=None, sep='\t')
                display(df_table)
        
            targets = []
            for i in df_table.index:
                line = ''.join(df_table.iloc[i])
                if not line or line[0] == '#': continue
                kwargs = eval(line)

                code = kwargs.get('code', '')
                if not code: continue
                targets.append(code)

            # print(targets)
            # 組成stock_list
            stock_list = '|'.join('tse_{}.tw'.format(target) for target in targets) 
            
            #　query data
            query_url = "http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch="+ stock_list
            data = json.loads(urlopen(query_url).read())
            # data_string = ",".join(str(element) for element in data['msgArray'])
            # method.Logging(config, path_current_dir, 'INFO', data_string)

            # 過濾出有用到的欄位
            columns = ['c','n','z','tv','v','o','h','l','y']
            df = pandas.DataFrame(data['msgArray'], columns=columns)
            df.columns = ['股票代號','公司簡稱','當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']
            df.insert(9, "漲跌百分比", 0.0)
            # print(df.dtypes)
            # df[['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']] = df[['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']].astype(float)
            # print(df.dtypes)
   
            # display(df)
            # 新增漲跌百分比
            for x in range(len(df.index)):
                if df['當盤成交價'].iloc[x] != '-':
                    df.loc[x, ['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']] = df.loc[x, ['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']].astype(float).round(2)
                    # df.loc[x, ['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']] = df.loc[x, ['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']].round(2)
                    # df.iloc[x, [2,3,4,5,6,7,8]] = df.iloc[x, [2,3,4,5,6,7,8]].astype(float)
                    df.loc[x, '漲跌百分比'] = ((df.loc[x, '當盤成交價'] - df.loc[x, '昨收價'])/df.loc[x, '昨收價'] * 100).round(2)
                    # df.loc[x, '漲跌百分比'] = df.loc[x, '漲跌百分比'].round(2)
            
            
            
            # show table
            display(df)

            for i in df_table.index:
                line = ''.join(df_table.iloc[i])
                if not line or line[0] == '#': continue
                kwargs = eval(line)

                code = kwargs.get('code', '')
                if not code: continue

                df_serial = df.loc[(df['股票代號'] == code), ['當盤成交價']]
                if  df_serial.at[df_serial.index[0], '當盤成交價'] != '-':
                    price = float(df_serial.at[df_serial.index[0], '當盤成交價'])
                     # 停利點
                    target_profit = kwargs.get('target_profit', '')
                    if target_profit and price >= float(target_profit):
                        print('code : {}, price : {}, target_profit : {}'.format(code, df_serial.at[df_serial.index[0], '當盤成交價'], target_profit))
                        
                    # 停損點
                    target_loss = kwargs.get('target_loss', '')
                    if target_loss and price <= float(target_loss):
                        print('code : {}, price : {}, target_loss : {}'.format(code, df_serial.at[df_serial.index[0], '當盤成交價'], target_loss))

               
                    df_serial = df.loc[(df['股票代號'] == code), ['漲跌百分比']]
                    status = float(df_serial.at[df_serial.index[0], '漲跌百分比'])
                    # 漲跌幅
                    level = kwargs.get('level', '')
                    if level and status >= float(level):
                        print('code : {}, price : {}, level : {}'.format(code, df_serial.at[df_serial.index[0], '漲跌百分比'], level))

                    # 警報
                    alarm = kwargs.get('alarm', 'False')
                    if alarm == 'True':
                        # 警報間隔時間             
                        alarm_interval = float(kwargs.get('alarm_interval', '1'))
     
            # reload df_table
            if method.PathIsExist(method.PathJoin(path_current_dir, 'RELOAD')) == True:
                while(method.PathIsExist(method.PathJoin(path_current_dir, 'RELOAD'))):
                    method.FileDelete(method.PathJoin(path, 'RELOAD'))
                df_table = None

            # 紀錄更新時間
            time = datetime.datetime.now()  
            print("更新時間:" + str(time.hour)+":"+str(time.minute)+":"+str(time.second))
            # 判斷爬蟲終止條件
            start_time = datetime.datetime.strptime(str(time.date())+'9:30', '%Y-%m-%d%H:%M')
            end_time =  datetime.datetime.strptime(str(time.date())+'23:30', '%Y-%m-%d%H:%M')

            if time >= start_time and time <= end_time:
                g_schedule.enter(1, 0, run_1, argument=(config, path, df_table,))

            result = True

    except Exception as e:
        raise e
    finally:
        # return ''
        pass

def run_2(config, path, df_table, **kwargs):#基本市況
    
    try: 

        result = False
        data = ''

        for i in range(1):

            url = 'https://tw.tradingview.com/symbols/TWSE-2330/'
            res = requests.get(url)

            soup = BeautifulSoup(res.text,'html.parser')

            url = 'https://tw.tradingview.com/markets/stocks-taiwan/sectorandindustry-industry/'
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/111.25 (KHTML, like Gecko) Chrome/99.0.2345.81 Safari/123.36'}
            res = requests.get(url,headers=headers)

            soup = BeautifulSoup(res.text,'html.parser')

            dfs = pandas.DataFrame()

            for line in soup.find_all(class_='tv-screener__symbol'):
                # 取得各產業網址
                href = 'https://tw.tradingview.com'+line['href']
                industry = line.text
                # 去除部門資料
                if ('-sector' not in href)&('investment-trusts' not in href):
                    r = requests.get(href)
                    stocks = pandas.read_html(r.text,header=0)[0].applymap(lambda s:str(s).replace(' ',''))['Unnamed: 0']

                    for sid in stocks:

                        # 處理股票代號格式
                        stock_id = ''.join([s for s in sid if s.isdigit()])
                        if len(stock_id)>4:
                            stock_id = stock_id[1:5]

                        # 使用re搜尋str中在stock_id後所有的文字
                        name = re.search(f"{stock_id}.*",sid).group()[4:]

                        dfs = dfs.append(pandas.DataFrame({
                            '公司簡稱':name,
                            '產業族群':industry
                             },index=[stock_id]))

            display(dfs)

            # clear_output(wait=True)

            if isinstance(df_table, pandas.DataFrame) == False:
                df_table = pandas.read_csv('list.txt', header=None, sep='\t')
                display(df_table)
        
            targets = []
            for i in df_table.index:
                line = ''.join(df_table.iloc[i])
                if not line or line[0] == '#': continue
                kwargs = eval(line)

                code = kwargs.get('code', '')
                if not code: continue
                targets.append(code)

            # print(targets)
            # 組成stock_list
            stock_list = '|'.join('tse_{}.tw'.format(target) for target in targets) 
            
            #　query data
            query_url = "http://mis.twse.com.tw/stock/api/getStockInfo.jsp?ex_ch="+ stock_list
            data = json.loads(urlopen(query_url).read())
            # data_string = ",".join(str(element) for element in data['msgArray'])
            # method.Logging(config, path_current_dir, 'INFO', data_string)

            # 過濾出有用到的欄位
            columns = ['c','n','z','tv','v','o','h','l','y']
            df = pandas.DataFrame(data['msgArray'], columns=columns)
            df.columns = ['股票代號','公司簡稱','當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']
            df.insert(9, "漲跌百分比", 0.0)
            # print(df.dtypes)
            # df[['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']] = df[['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']].astype(float)
            # print(df.dtypes)
   
            # display(df)
            # 新增漲跌百分比
            for x in range(len(df.index)):
                if df['當盤成交價'].iloc[x] != '-':
                    df.loc[x, ['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']] = df.loc[x, ['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']].astype(float).round(2)
                    # df.loc[x, ['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']] = df.loc[x, ['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']].round(2)
                    # df.iloc[x, [2,3,4,5,6,7,8]] = df.iloc[x, [2,3,4,5,6,7,8]].astype(float)
                    df.loc[x, '漲跌百分比'] = ((df.loc[x, '當盤成交價'] - df.loc[x, '昨收價'])/df.loc[x, '昨收價'] * 100).round(2)
                    # df.loc[x, '漲跌百分比'] = df.loc[x, '漲跌百分比'].round(2)
            
            
            
            # show table
            display(df)

            for i in df_table.index:
                line = ''.join(df_table.iloc[i])
                if not line or line[0] == '#': continue
                kwargs = eval(line)

                code = kwargs.get('code', '')
                if not code: continue

                df_serial = df.loc[(df['股票代號'] == code), ['當盤成交價']]
                if  df_serial.at[df_serial.index[0], '當盤成交價'] != '-':
                    price = float(df_serial.at[df_serial.index[0], '當盤成交價'])
                     # 停利點
                    target_profit = kwargs.get('target_profit', '')
                    if target_profit and price >= float(target_profit):
                        print('code : {}, price : {}, target_profit : {}'.format(code, df_serial.at[df_serial.index[0], '當盤成交價'], target_profit))
                        
                    # 停損點
                    target_loss = kwargs.get('target_loss', '')
                    if target_loss and price <= float(target_loss):
                        print('code : {}, price : {}, target_loss : {}'.format(code, df_serial.at[df_serial.index[0], '當盤成交價'], target_loss))

               
                    df_serial = df.loc[(df['股票代號'] == code), ['漲跌百分比']]
                    status = float(df_serial.at[df_serial.index[0], '漲跌百分比'])
                    # 漲跌幅
                    level = kwargs.get('level', '')
                    if level and status >= float(level):
                        print('code : {}, price : {}, level : {}'.format(code, df_serial.at[df_serial.index[0], '漲跌百分比'], level))

                    # 警報
                    alarm = kwargs.get('alarm', 'False')
                    if alarm == 'True':
                        # 警報間隔時間             
                        alarm_interval = float(kwargs.get('alarm_interval', '1'))
     
            # reload df_table
            if method.PathIsExist(method.PathJoin(path_current_dir, 'RELOAD')) == True:
                while(method.PathIsExist(method.PathJoin(path_current_dir, 'RELOAD'))):
                    method.FileDelete(method.PathJoin(path, 'RELOAD'))
                df_table = None

            # 紀錄更新時間
            time = datetime.datetime.now()  
            print("更新時間:" + str(time.hour)+":"+str(time.minute)+":"+str(time.second))
            # 判斷爬蟲終止條件
            start_time = datetime.datetime.strptime(str(time.date())+'9:30', '%Y-%m-%d%H:%M')
            end_time =  datetime.datetime.strptime(str(time.date())+'23:30', '%Y-%m-%d%H:%M')

            if time >= start_time and time <= end_time:
                g_schedule.enter(1, 0, run_2, argument=(config, path, df_table,))

            result = True

    except Exception as e:
        raise e
    finally:
        # return ''
        pass


if __name__ == '__main__':
    pass

    try:       

        config, path_current_dir = initialization()

        sdk = FubonSDK()
   
        # accounts = sdk.login('F126310472', 'A93040156B', "您的憑證位置", "您的憑證密碼") #若有歸戶，則會回傳多筆帳號資訊

        # acc = accounts.data[0]

        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--disable-notifications")
        # chrome_options.add_argument('--headless')
        chrome_options.add_argument('--start-maximized')
        # chrome_options.add_argument('--start-minimized')
        chrome_options.add_argument('--ignore-certificate-errors')

        # if ChromeDriverManagerMode == '0':
        driver = webdriver.Chrome(options=chrome_options)
        # elif ChromeDriverManagerMode == '1':
        #     driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        # elif ChromeDriverManagerMode == '2':
        #     chromedriver_bin = method.PathGetCurrent('chromedriver\\win64\\124.0.6367.91\\chromedriver.exe')
        #     driver = webdriver.Chrome(service=webdriver.ChromeService(executable_path=chromedriver_bin), options=chrome_options)

        data = 'https://tw.tradingview.com/screener/'
        driver.get(data)
        # print(driver.page_source)
        soup = BeautifulSoup(driver.page_source,'html.parser')
        #class="apply-common-tooltip tickerNameBox-GrtoTeat tickerName-GrtoTeat
        # for line in soup.find_all(['a'], title=['2330 − 台積電', '2308 − 台達電']):
        #         print(line)
        #         print(line.text)
        #         print(line.name)
        #         print('{}'.format(line['class']))
        #         print('{}'.format(line['title']))
        #         print('{}'.format(line['target']))
        #         print('{}'.format(line['href']))

        time.sleep(4)
        count = 1
        for line in soup.find_all(['tr']):         
             print(count)
             count =count + 1



        code_list = ['2330', '2317', '6744']
        for code in code_list:
            condition = {'data-rowkey': 'TWSE:{}'.format(code)}
            for line in soup.find_all(['tr'], attrs=condition):
                # print(line)
                print(line.text)
                print(line.text[line.text.find('D')+1:line.text.find('TWD')])
                print(line.text[line.text.find('TWD')+3:line.text.find('%')])
                print(line.text[line.text.find('%')+1:2])
                # print(line.name)

        # 每秒定時器
        # g_schedule.enter(1, 0, run_2, argument=(config, path_current_dir, None))
        # g_schedule.run()

    except Exception as e:
        result = False
        method.Logging(config, path_current_dir, 'ERROR', '{}'.format(e))
    
    finally:

        method.Logging(config, path_current_dir, 'INFO', 'Finish.')
    
        
        