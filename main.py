
import sys
import os
# 把当前文件所在文件夹的父文件夹路径加入到PYTHONPATH
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from normal import method


from IPython.display import display, clear_output
from urllib.request import urlopen
import pandas
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

def run(config, path, targets, **kwargs):
    
    try: 

        pandas.options.mode.copy_on_write = True
        result = False
        data = ''

        for i in range(1):

            clear_output(wait=True)
    
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
   
            
            # 新增漲跌百分比
            for x in range(len(df.index)):
                if df['當盤成交價'].iloc[x] != '-':
                    df.loc[x, ['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']] = df.loc[x, ['當盤成交價','當盤成交量','累積成交量','開盤價','最高價','最低價','昨收價']].astype(float)
                    # df.iloc[x, [2,3,4,5,6,7,8]] = df.iloc[x, [2,3,4,5,6,7,8]].astype(float)
                    df.loc[x, '漲跌百分比'] = (df.loc[x, '當盤成交價'] - df.loc[x, '昨收價'])/df.loc[x, '昨收價'] * 100
                    print(df['漲跌百分比'].iloc[x])
            
            # 紀錄更新時間
            time = datetime.datetime.now()  
            print("更新時間:" + str(time.hour)+":"+str(time.minute)+":"+str(time.second))
            
            # show table
            df = df.style.applymap(tableColor, subset=['漲跌百分比'])
            display(df)
            
            start_time = datetime.datetime.strptime(str(time.date())+'9:30', '%Y-%m-%d%H:%M')
            end_time =  datetime.datetime.strptime(str(time.date())+'23:30', '%Y-%m-%d%H:%M')
            
            # 判斷爬蟲終止條件
            if time >= start_time and time <= end_time:
                g_schedule.enter(1, 0, run, argument=(config, path, targets,))

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

        # 欲爬取的股票代碼
        stock_list = ['1101','1102','1103','2330']

        # 每秒定時器
        g_schedule.enter(1, 0, run, argument=(config, path_current_dir,stock_list,))
        g_schedule.run()

    except Exception as e:
        result = False
        method.Logging(config, path_current_dir, 'ERROR', '{}'.format(e))
    
    finally:

        method.Logging(config, path_current_dir, 'INFO', 'Finish.')
    
        
        