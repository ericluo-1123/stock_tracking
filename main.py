
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

def run(config, path, df_table, **kwargs):
    
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
            
            # 紀錄更新時間
            time = datetime.datetime.now()  
            print("更新時間:" + str(time.hour)+":"+str(time.minute)+":"+str(time.second))
            
            # show table
            display(df)

            for i in df_table.index:
                line = ''.join(df_table.iloc[i])
                if not line or line[0] == '#': continue
                kwargs = eval(line)

                code = kwargs.get('code', '')
                if not code: continue

                # 停利點
                target_profit = kwargs.get('target_profit', '')
                if target_profit:
                    df_serial = df.loc[(df['股票代號'] == code), ['當盤成交價']]
                    # display(df_serial.index[0])
                    if df_serial.at[df_serial.index[0], '當盤成交價'] >= float(target_profit):
                        print('code : {}, price : {}, target_profit : {}'.format(code, df_serial.at[df_serial.index[0], '當盤成交價'], target_profit))
                    
                # 停損點
                target_loss = kwargs.get('target_loss', '')
                if target_loss:
                    df_serial = df.loc[(df['股票代號'] == code), ['當盤成交價']]
                    # display(df_serial.index[0])
                    if df_serial.at[df_serial.index[0], '當盤成交價'] <= float(target_loss):
                        print('code : {}, price : {}, target_loss : {}'.format(code, df_serial.at[df_serial.index[0], '當盤成交價'], target_loss))


                # 漲跌幅
                level = kwargs.get('level', '')
                if level:
                    df_serial = df.loc[(df['股票代號'] == code), ['漲跌百分比']]
                    # display(df_serial.index[0])
                    if df_serial.at[df_serial.index[0], '漲跌百分比'] >= float(level):
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

            # 判斷爬蟲終止條件
            start_time = datetime.datetime.strptime(str(time.date())+'9:30', '%Y-%m-%d%H:%M')
            end_time =  datetime.datetime.strptime(str(time.date())+'23:30', '%Y-%m-%d%H:%M')
            if time >= start_time and time <= end_time:
                g_schedule.enter(1, 0, run, argument=(config, path, df_table,))

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

        # 每秒定時器
        g_schedule.enter(1, 0, run, argument=(config, path_current_dir, None))
        g_schedule.run()

    except Exception as e:
        result = False
        method.Logging(config, path_current_dir, 'ERROR', '{}'.format(e))
    
    finally:

        method.Logging(config, path_current_dir, 'INFO', 'Finish.')
    
        
        