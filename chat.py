import socket
import threading
import json
import datetime
import ast
import ntpath
from PyQt5 import QtCore


class Clientchatserver(QtCore.QThread):
    receivedmsg = QtCore.pyqtSignal(object)
    def __init__(self,parent=None,ip='',port=''):
        super(Clientchatserver,self).__init__(parent)
        self.addr = (ip,port)
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.clients = {}
        self.friends = {}
        self.constate = False
        self.overevent = threading.Event()
        
        
    def run(self):
        self.sock.bind(self.addr)
        self.sock.listen()         #开始监听是否有连接接入
        #有连接接入时建立一个新线程来通信
        threading.Thread(target=self.acceptclient,name='accept').start()

    def acceptclient(self):
        while not self.overevent.is_set():
            try:
                self.sock.settimeout(0.5)
                s,raddr = self.sock.accept()
            except socket.timeout:    
                pass
            except:
                raise
            else:
                fri = self.friends.get(raddr)
                if fri==None:
                    self.friends['id'] = 'unknown' #有人搜寻自动加为好友
                self.clients[raddr] = s#更新套接字
            #s,raddr = self.sock.accept()  #也会产生阻塞 
            #fri = self.friends.get(raddr)
            #if fri==None:
            #    self.friends['id'] = 'unknown' #有人搜寻自动加为好友
            #self.clients[raddr] = s#更新套接字

            #新建线程专门利用这个套接字和一个用户通信，包括接收信息
                threading.Thread(target=self.recvmsg,name='recv',args=(s,raddr,self.receivedmsg)).start()
        #threading.Thread(target=self.sendmsg,name='send',args=(s,raddr)).start()
    def overthread(self):
        self.overevent.set()
    
    #暂时没用
    def connectclient(self,ip,port):
        s = self.clients.get((ip,port))
        if s==None:
            s= socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            ###
            ###
            ###
            #注意异常处理！！
            s.connect((ip,port))
            raddr = (ip,port) 
            self.clients[raddr] = s
        #新建线程专门利用这个套接字和一个用户通信，包括接收和信息和发送信息
        threading.Thread(target=self.recvmsg,name='recv',args=(s,raddr)).start()
        threading.Thread(target=self.sendmsg,name='send',args=(s,raddr)).start()
        


    def recvmsg(self,sock,raddr,receivedmsg):
        print(raddr)
        #这个套接字一直循环一遍随时接收消息      
        data = b''
        while True:
            partdata = sock.recv(1024)
            data += partdata
            if len(partdata)<1024:
                break
        if data != b'':
            #scnn = data.decode('utf-8')
            data = ast.literal_eval(data.decode('utf-8'))
            #data = json.loads(data.decode('utf-8'))#单引号会报错
            if data['type'] == 'TEXT':
                receivedmsg.emit(data)
            if data['type'] == 'FILE':
                filename = data['content']
                sock.send(b'ACK') #开始接收文件
                #放在该程序的data/recvfile目录下
                with open('data/recvfile/'+filename,'wb') as recvfile:
                    part = sock.recv(1024)
                    while part:
                        recvfile.write(part)
                        part = sock.recv(1024)
                receivedmsg.emit(data)   #方便在聊天框中显示收到文件消息提示
    
    def sendmsg(self,raddr,cont,msgtype,info):
        data = {}
        data['type'] = msgtype
        data['sender'] = info
        data['content'] = cont 
        dt = datetime.datetime.now()
        data['time'] = dt.strftime('%Y/%m/%d %H:%M:%S')
        if msgtype=='TEXT':
            threading.Thread(target=self.sendmsgtext_thread,name='send',args=(raddr,data)).start()
        if msgtype=='FILE':
            threading.Thread(target=self.sendmsgfile_thread,name='send',args=(raddr,data)).start()

    def sendmsgtext_thread(self,raddr,data):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(raddr)
        except:
            raise
        else:
            s.sendall(str(data).encode('utf-8'))    
            s.close()

    def sendmsgfile_thread(self,raddr,data):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.connect(raddr)
        except:
            raise
        else:
            path = data['content']
            data['content'] = ntpath.basename(path) #得到文件名，去除前面的路径
            s.sendall(str(data).encode('utf-8'))
            response = s.recv(1024)
            #文件内容比较复杂，需要单独发送，不能放到字典里再发送
            if response==b'ACK':
                with open(path,'rb') as sendfile:
                    while True:
                        #考虑到文件的大小范围很大，每次发送1024个字节
                        part = sendfile.read(1024)
                        if not part:
                            break
                        s.sendall(part)
            s.close()

#        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:##异常处理，重点解决
#            s.connect(raddr)
#            s.sendall(str(data).encode('utf-8'))    
#            s.close()

    
        


if __name__ == "__main__":
    myip = '183.172.90.70'
    port1 = 9999
    port2 = 9782
    chat = Clientchatserver(myip,port1)
    threading.Thread(target=chat.start,name='listen')
    chat.connectclient(myip,port2)
