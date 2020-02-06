#与服务器连接，实现登录、检测状态、登出等
import socket
from PyQt5 import QtCore, QtGui, QtWidgets
import sys
#import Ui_logininterface
#服务器ip地址和端口号
HOST = '166.111.140.57'
PORT = 8000
PASSWARD = 'net2019'#密码规定了是net2019

#login operation
def login(userid):
    ackmsg = 'error'
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    try:
        s.settimeout(1)         #处理网络连接异常
        s.connect((HOST,PORT))
    except socket.timeout:    
        pass   #什么也不操作
    else:
        sendmsg = userid+'_'+PASSWARD
        s.send(sendmsg.encode('utf-8'))
        result = s.recv(1024)
        feed = s.getsockname()[0]
        s.close()
        if result==b'lol':
            ackmsg = feed
        else:
            ackmsg = 'none'
    finally:
        return ackmsg


    #with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
    #s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)#建立一个新的套接字,ipv4/tcp
    #    s.connect((HOST,PORT))
    #    sendmsg = userid+'_'+PASSWARD
    #    s.send(sendmsg.encode('utf-8'))
    #    result = s.recv(1024)
    #    feed = s.getsockname()[0]
    #    s.close()
    #    if result==b'lol':
    #        ackmsg = feed
    #    else:
    #        ackmsg = 'none'


def getfriip(userid):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)#建立一个新的套接字,ipv4/tcp
    s.connect((HOST,PORT))
    sendmsg = 'q'+userid
    s.send(sendmsg.encode('utf-8'))
    ipadr = s.recv(1024).decode('utf-8')
    s.close()
    return ipadr

def querystate(userid):
    ip = getfriip(userid)
    if ip=='n':
        return False
    else:
        return True


def logout(userid):
    s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)#建立一个新的套接字,ipv4/tcp
    s.connect((HOST,PORT))
    sendmsg = 'logout'+userid
    s.send(sendmsg.encode('utf-8'))
    result = s.recv(1024)
    s.close()
    if result==b'loo':
        return True
    else:
        return False

#直接把该文件当作脚本时运行,可以用来测试是否与服务器连接正确
if __name__ == "__main__":
    userid = '2017011626'
    if login(userid):
        print("ok")
        
    querystate(userid)
    logout(userid)
