

from flask import Flask, request

# 載入 json 標準函式庫，處理回傳的資料格式
import json

# 載入 LINE Message API 相關函式庫
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError
from linebot.models import MessageEvent, TextMessage, TextSendMessage


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

def run(popen, **kwargs):
    
    try: 

        result = False
        data = ''

        for i in range(1):

            # command = kwargs.get('command', '')
            # flag = kwargs.get('flag', '')
            # timeout = kwargs.get('timeout', '5')
            # loop = kwargs.get('loop', 'Flase')
            # test_pass = kwargs.get('test_pass', '')
            # test_fail = kwargs.get('test_fail', '')
            # delay_time = kwargs.get('delay_time', '0')
            # interface = kwargs.get('interface', '0')

            # if '(path)' in command: command = command.replace('(path)', path_current_dir)
            # if '(path)' in interface: interface = interface.replace('(path)', path_current_dir)

            # if command == 'delay':
            #     if int(delay_time) != 0 :
            #         method.Logging(config, path_current_dir, 'INFO', 'delay({})'.format(delay_time))
            #         sleep(int(delay_time))

            # else:

            #     if command == 'open':
            #         command = ''
            #         popen = subprocess_popen(command, flag, timeout, popen, fd_r, fd_w, interface)

            #     if popen == None:
            #         raise RuntimeError('subprocess no open')
            #         break

            #     data = subprocess_write(command, flag, timeout,  popen, fd_r, fd_w)

            #     if test_pass : 
            #         if test_pass not in data :
            #             result = False
            #             break
            #     if test_fail:
            #         if test_fail in data :
            #             result = False
            #             break

            #     if loop == 'True':
            #         while(True):
            #             if method.PathIsExist(method.PathJoin(path_current_dir, 'STOP')) == True: 
            #                 break
            #             sleep(1)

            result = True

    except Exception as e:
        raise e
    finally:
        if result == True and not data: data = 'done.'
        elif result == False and not data: data = 'failed.'
        return popen, result, data
    
app = Flask(__name__)

@app.route("/", methods=['POST'])
def linebot():
    body = request.get_data(as_text=True)                    # 取得收到的訊息內容
    try:
        json_data = json.loads(body)                         # json 格式化訊息內容
        access_token = 'wHFWR8uoU5DPESeIXurDUKb2EF4+jWlv5pY5b3edhMx+YnAE7upqtPS+YsSM7Y4LH4SzjUnCqR/++lNmM11wplUnPDNzd/9FYxwNcbRacJJJYprt8hGEbn54XDwngR39VeImULabemmixOKSHSd4YgdB04t89/1O/w1cDnyilFU='
        secret = '354e355942f534dd2a5b5f8604d912e2'
        line_bot_api = LineBotApi(access_token)              # 確認 token 是否正確
        handler = WebhookHandler(secret)                     # 確認 secret 是否正確
        signature = request.headers['X-Line-Signature']      # 加入回傳的 headers
        handler.handle(body, signature)                      # 綁定訊息回傳的相關資訊
        tk = json_data['events'][0]['replyToken']            # 取得回傳訊息的 Token
        type = json_data['events'][0]['message']['type']     # 取得 LINe 收到的訊息類型
        if type=='text':
            msg = json_data['events'][0]['message']['text']  # 取得 LINE 收到的文字訊息
            print(msg)                                       # 印出內容
            reply = msg
            line_bot_api.event
        else:
            reply = '你傳的不是文字呦～'
        print(reply)
        line_bot_api.reply_message(tk,TextSendMessage(reply))# 回傳訊息
    except:
        print(body)                                          # 如果發生錯誤，印出收到的內容
    return 'OK'                                              # 驗證 Webhook 使用，不能省略

@app.route("/")
def home():
    user_id = 'U5e44338732da5113558c7c2ebc93ccb4'
    access_token = 'wHFWR8uoU5DPESeIXurDUKb2EF4+jWlv5pY5b3edhMx+YnAE7upqtPS+YsSM7Y4LH4SzjUnCqR/++lNmM11wplUnPDNzd/9FYxwNcbRacJJJYprt8hGEbn54XDwngR39VeImULabemmixOKSHSd4YgdB04t89/1O/w1cDnyilFU='
    line_bot_api = LineBotApi(access_token)
    try:
        msg = request.args.get('msg')   # 取得網址的 msg 參數
        if msg != None:
        # 如果有 msg 參數，觸發 LINE Message API 的 push_message 方法
            line_bot_api.push_message(user_id, TextSendMessage(text=msg))
            return msg
        else:
            return 'OK'
    except:
        print('error')

if __name__ == '__main__':
    pass

    try:       
        
        config, path_current_dir =  initialization()
        
        app.run(host='0.0.0.0', port=5001)


        # mode = method.ConfigGet(config, 'env', 'mode', 'script')
        # popen = None
        # result = True
        # data = ''
        # method.FileDelete(method.PathJoin(path_current_dir, './sub.log'))
        # fd_w = open(method.PathJoin(path_current_dir, './sub.log'), 'w')
        # fd_r = open(method.PathJoin(path_current_dir, './sub.log'), 'r')
        
        # if mode == 'script':
        #     with open(method.PathJoin(path_current_dir, 'script.txt'), newline='', encoding='utf-8') as csvfile:
        #         rows = csv.reader(csvfile)
        #         for row in rows:
        #             data = ', '.join(row)
        #             if not data or data[0] == '#': continue
        #             kwargs = eval(data)
                    
        #             popen, result, data = subprocess_run(popen, **kwargs)
        #             if  result == False:
        #                 break
        # elif mode == 'socket':
              
        #     HOST = '127.0.0.1'
        #     PORT = 8383
        #     conn = None
        #     end = False
        #     data = ''

        #     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        #     s.bind((HOST, PORT))
        #     s.listen(1)

        #     method.Logging(config, path_current_dir, 'INFO', 'socket server start at {}:{}'.format(HOST, PORT))

        #     while True:
        #         conn, addr = s.accept()
        #         method.Logging(config, path_current_dir, 'INFO', 'socket Connected by {}'.format(addr))
        #         conn.send('R: socket Connected by {}\r\n'.format(addr).encode())

        #         while True:
                    
        #             try: 
        #                 recv = conn.recv(1024)
        #                 recv = recv.decode()
        #                 recv = recv.strip()
        #                 recv = recv.replace('\n', '').replace('\r', '') 
        #                 if not recv or recv == 'close':
        #                     data = 'close'
        #                     break
        #                 elif recv == 'exit':
        #                     data = 'exit'
        #                     break

        #                 kwargs = eval(recv)
        #                 if type(kwargs).__name__ != 'dict' :
        #                     data = 'Unknow'
        #                     continue

        #                 popen, result, data = subprocess_run(popen, **kwargs)
        #             except Exception as e:
        #                 data = '{}'.format(e)
        #                 pass
        #             finally:
        #                 if data: conn.send('R: {}\r\n'.format(data).encode())

        #         if data == 'exit': break
        #         elif data == 'close': conn.close()

    except Exception as e:
        result = False
        method.Logging(config, path_current_dir, 'ERROR', '{}'.format(e))
    
    finally:
        # if mode == 'script':
        #     if popen != None:
        #         fd_w.close()
        #         fd_r.close()
        #         popen.kill()
        #     if result == True:
        #         method.FileCreate('{}\\PASS'.format(path_current_dir))
        #     else:
        #         method.FileCreate('{}\\FAIL'.format(path_current_dir))
        # elif mode == 'socket':
        #     if conn != None:
        #         conn.close()

        
        method.Logging(config, path_current_dir, 'INFO', 'Finish.')
    
        
        