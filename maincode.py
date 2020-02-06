import Ui_mainwin
import Ui_logininterface
import Ui_chatwindow
import Server
import chat
import loginop
import socket
import datetime
import sys
import os
import threading
import pickle
import ntpath
from PyQt5 import QtCore
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

class mainwindow(QMainWindow,Ui_mainwin.Ui_Form):
    overprogram = QtCore.pyqtSignal()
    def __init__(self,parent=None,fri={},hostid=''):
        super(mainwindow,self).__init__(parent)
        self.setupUi(self)
        self.set_item(fri) 
        self.hostid = hostid
    def closeEvent(self, event):
        reply = QMessageBox.question(self,'本程序',"是否要退出程序？",
                                               QMessageBox.Yes | QMessageBox.No,
                                               QMessageBox.No)
        if reply == QMessageBox.Yes:
            result = Server.logout(self.hostid)
            if result==True:
                self.overprogram.emit() #向主函数发出结束线程的信号
                event.accept()
            else:
                QMessageBox.about(self,"提示","账号没有正确登出，请重试")
                event.ignore()
        else:
            event.ignore()

    def set_item(self,fri):
        self.listWidget.clear()
        for friid in fri:
            layoutmain = QHBoxLayout()
            imag = QLabel()  #头像显示，暂不用
            imag.setFixedSize(30,30)
            layoutmain.addWidget(imag)
            layoutmain.addWidget(QLabel(''))
            if fri[friid][1] == 'n':
                layoutmain.addWidget(QLabel("离线"))
            else:
                layoutmain.addWidget(QLabel("在线"))
            item = QListWidgetItem()
            item.setSizeHint(QtCore.QSize(300,50))
            item.setText(friid)
            widget = QWidget()
            widget.setLayout(layoutmain)
            self.listWidget.addItem(item)
            self.listWidget.setItemWidget(item,widget)
            
class loginwindow(QMainWindow,Ui_logininterface.Ui_Form):
    def __init__(self,parent=None):
        super(loginwindow,self).__init__(parent)
        self.setupUi(self)
        #self.lineEdit

class chatwindow(QMainWindow,Ui_chatwindow.Ui_Form):
    closechatwin = QtCore.pyqtSignal(str)
    def __init__(self,parent=None,sinfo=(),rinfo=(),conserver=None,record=[]):
        super(chatwindow,self).__init__(parent)
        self.setupUi(self)
        self.sinfo = sinfo
        self.rinfo = rinfo
        self.conserver = conserver
        self.record = record
        self.sport = 9999
        self.textEdit.setReadOnly(True)

    def closeEvent(self,event):
        self.conserver.overthread()#结束进程 还应当向主界面发信号
        self.closechatwin.emit(self.rinfo[0])
        #self.sleep(0.5)
        event.accept()
    
    def changeinfo(self,sinfo,rinfo):
        self.sinfo = sinfo
        self.rinfo = rinfo

    def sendmsgtext(self):
        #增加空信息的处理
        text = self.plainTextEdit.toPlainText()
        self.plainTextEdit.clear()
        dt = datetime.datetime.now()
        t = dt.strftime('%Y/%m/%d %H:%M:%S')
        self.textEdit.append('我'+' '+t+'\n')
        self.textEdit.append(text+'\n')
        raddr = (self.rinfo[2],self.sport)
        self.conserver.sendmsg((self.rinfo[2],12345),text,'TEXT',self.sinfo)
        self.conserver.sendmsg((self.rinfo[2],9696),text,'TEXT',self.sinfo)
        #多余了其实，前面那块也可以拿到这里封装，就不用再函数里封装了
        data = {}
        data['type'] = 'TEXT'
        data['sender'] = self.sinfo
        data['content'] = text 
        data['time'] = t
        self.record.append(data)
        #self,raddr,cont,msgtype,info
    
    def displayonemsg(self,data):
        curid = data['sender'][0]
        if data['type'] == 'TEXT':
            self.textEdit.append(data['sender'][0]+' '+data['time']+'\n')
            self.textEdit.append(data['content']+'\n')
            self.record.append(data)
        if data['type'] == 'FILE':
            self.textEdit.append('收到一个文件')
            self.textEdit.append(data['sender'][0]+' '+data['time']+'\n')
            self.textEdit.append(data['content']+'\n')
            self.record.append(data)

    def displaymsg(self,msgpack):
        #文件处理之后处理
        curid = msgpack[0]['sender'][0]
        for i in range(len(msgpack)):
            if msgpack[i]['type'] == 'TEXT':
                data = msgpack[i]
                self.textEdit.append(data['sender'][0]+' '+data['time']+'\n')
                self.textEdit.append(data['content']+'\n')
                self.record.append(data)
            if msgpack[i]['type'] == 'FILE':
                self.textEdit.append('收到一个文件')
                self.textEdit.append(data['sender'][0]+' '+data['time']+'\n')
                self.textEdit.append(data['content']+'\n')
                self.record.append(data)
    
    def sendmsgfile(self):
        options = QFileDialog.Options()
        filename,_ = QFileDialog.getOpenFileName(self,'选择文件','','All Files(*.*)',options=options)
        self.conserver.sendmsg((self.rinfo[2],12345),filename,'FILE',self.sinfo)
        self.conserver.sendmsg((self.rinfo[2],9696),filename,'FILE',self.sinfo)
        dt = datetime.datetime.now()
        t = dt.strftime('%Y/%m/%d %H:%M:%S')
        data = {}
        data['type'] = 'FILE'
        data['sender'] = self.sinfo
        data['content'] = ntpath.basename(filename) 
        data['time'] = t
        self.textEdit.append('发送一个文件')
        self.textEdit.append('我'+' '+data['time']+'\n')
        self.textEdit.append(data['content']+'\n')
        self.record.append(data)

    def saverecording(self):
        with open('data/'+self.sinfo[0]+'/'+self.rinfo[0]+'.pkl','wb') as f:
            pickle.dump(self.record,f,pickle.HIGHEST_PROTOCOL)
    
    def readrecord(self):
        with open('data/'+self.sinfo[0]+'/'+self.rinfo[0]+'.pkl','rb') as f:
            self.record = pickle.load(f)
        self.displaymsg(self.record)



class mythread(QtCore.QThread):
    updatesingnal = QtCore.pyqtSignal(object)
    def __init__(self,parent=None,frdstate=[],hostid=''):
        super(mythread,self).__init__(parent)
        self.state = True
        self.frdstate = frdstate
        self.hostid = hostid
        self.overevent = threading.Event()
    def overthread(self):
        self.overevent.set()
        #self.state = False
        #self.wait()

    def upcurfrdstate(self,frd):
        self.frdstate = frd      #检查时一定检查最新的好友列表

    def run(self):
        threading.Thread(target=self.checkstate,name='check').start()
        #while self.state:
        #    #自己的状态也要检查以防掉线
        #    curstate = []
        #    curstate.append((self.hostid,Server.getfriip(self.hostid)))
        #    for i in range(1,len(self.frdstate)):
        #        curstate.append((self.frdstate[i],Server.getfriip(self.frdstate[i])))
        #    self.updatesingnal.emit(curstate)
        #    self.sleep(1)
    
    def checkstate(self):
        while not self.overevent.is_set():
            curstate = []
            #自己的状态也要检查以防掉线
            curstate.append((self.hostid,Server.getfriip(self.hostid)))
            for i in range(1,len(self.frdstate)):
                curstate.append((self.frdstate[i],Server.getfriip(self.frdstate[i])))
            self.updatesingnal.emit(curstate)
            self.sleep(1)
    #def overthread():
    #    self.state = False


class mainoperation():
    def __init__(self):
        self.log = loginwindow()
        self.mainwin = mainwindow()
        #self.chatwin = window()#暂时以主页面代替
        self.hostip = ''
        self.info = 9999
        self.friends = {}
        self.friid = []
        self.chatlists = []  #当前已经打开的好友聊天窗口
        self.chatwins = {}
        self.message = []
        #self.user = chat.Clientchatserver(' ',port)
        self.log.pushButton.clicked.connect(self.logop)
        self.mainwin.pushButton_4.clicked.connect(self.openmessbar)
        #self.mainwin.pushButton_3.clicked.connect()
        recvDir = 'data/recvfile/'   #新建存放文件的文件夹
        if not os.path.exists(recvDir):
            os.makedirs(recvDir)

    def logop(self):
        userid = self.log.lineEdit.text()
        password = self.log.lineEdit_2.text()
        if password != 'net2019':
            QMessageBox.about(self.log,"提示","密码错误，请重新输入!")
        else:
            self.hostip = Server.login(userid)
            self.hostid = userid
            #修改昵称功能，同时要用到数据库
            self.name = userid
            if self.hostip == 'none':
                QMessageBox.about(self.log,"提示","用户不存在，请重新输入!")
                self.log.lineEdit_2.clear()
            elif self.hostip == 'error':
                QMessageBox.about(self.log,"提示","连接异常，请检查网络连接")
                self.log.lineEdit_2.clear()
            else:
                record = 'data/'+self.hostid+'/'   #新建存放记录的文件夹
                if not os.path.exists(record):
                    os.makedirs(record)
                recordpath = 'data/'+self.hostid+'/'+self.hostid+'frds.pkl'
                if os.path.isfile(recordpath):
                    self.loadfrirecord()  #读取记录信息
                else:
                    self.friid.append(self.hostid)
                self.mainwin = mainwindow(fri=self.friends,hostid=self.hostid)
                self.log.close()
                self.mainwin.show()
                self.updateop = mythread(frdstate= self.friid,hostid= self.hostid)
                self.updateop.start()
                self.updateop.updatesingnal.connect(self.updatefri)
                self.user = chat.Clientchatserver(ip=self.hostip,port=9999)
                self.user.receivedmsg.connect(self.dealrecvinfo)
                self.mainwin.pushButton_4.clicked.connect(self.openmessbar)
                self.mainwin.pushButton_3.clicked.connect(self.searchfrds)
                self.mainwin.listWidget.itemDoubleClicked.connect(self.openchatwin)
                self.mainwin.overprogram.connect(self.frirecord) #记录下自己的好友信息
                self.mainwin.overprogram.connect(self.user.overthread) #结束这个监听的线程
                self.mainwin.overprogram.connect(self.updateop.overthread) #结束这个更新好友的线程
                #开始监听是否有人给自己发消息
                threading.Thread(target=self.user.start,name='beginlisten').start()
        
    def frirecord(self):
        with open('data/'+self.hostid+'/'+self.hostid+'frds.pkl','wb') as f:
            pickle.dump(self.friends,f,pickle.HIGHEST_PROTOCOL)

    def loadfrirecord(self):
        self.friid.append(self.hostid)
        with open('data/'+self.hostid+'/'+self.hostid+'frds.pkl','rb') as f:
            self.friends = pickle.load(f)
        for frdid in self.friends:
            self.friid.append(frdid)
    
    def updatefri(self,firstate):
        if firstate[0][1] == 'n':
            QMessageBox.about(self.mainwin,"提示","由于网络问题你已经下线，请重新登录。")
            #下线问题好好处理
            #self.sleep(1)
            self.mainwin.close()
        else:
            for i in range(1,len(firstate)):
                self.friends[firstate[i][0]] = (self.friends[firstate[i][0]][0],firstate[i][1])
                #控制刷新状态
            self.mainwin.set_item(self.friends)
            self.mainwin.pushButton_4.setText('消息'+str(self.message.__len__()))
            for i in range(len(self.chatlists)):
                if self.friends[self.chatlists[i]][1] == 'n':
                    self.chatwins[self.chatlists[i]].pushButton_2.setEnabled(False)
                    self.chatwins[self.chatlists[i]].plainTextEdit.setPlainText('好友已离线，暂时不可以发消息')
                else:
                    self.chatwins[self.chatlists[i]].pushButton_2.setEnabled(True)
                    if self.chatwins[self.chatlists[i]].plainTextEdit.toPlainText() == '好友已离线，暂时不可以发消息':
                        self.chatwins[self.chatlists[i]].plainTextEdit.clear()
                    

    def updatechatlist(self,friid):
        self.chatlists.remove(friid)
        self.chatwins.pop(friid)
        


    def searchfrds(self):
        serchid = self.mainwin.lineEdit.text()
        if serchid == self.hostid:
            QMessageBox.about(self.mainwin,"提示","这个账号是本账号")
        else:
            ip = Server.getfriip(serchid)
            if ip == 'n' or ip == 'Please send the correct message.':
                QMessageBox.about(self.mainwin,"提示","这个用户不存在，请重新查找")
            else:
                #这东西还是有点用 friid记得更新
                self.friid.append(serchid)
                self.updateop.upcurfrdstate(self.friid)
                self.friends[serchid] = (serchid,ip)
                self.mainwin.set_item(self.friends)

  
    def dealrecvinfo(self,data):
        #处理收到的信息
        sourceinfo = data['sender']#格式为(id(unique),name,sourceip)
        if sourceinfo[0] not in self.friends:
            #将这个人加为好友
            self.friends[sourceinfo[0]] = (sourceinfo[1],sourceinfo[2])
            QMessageBox.about(self.mainwin,"初识",sourceinfo[1]+"已成为你的好友")
            #if len(self.friid) !=0:  ##用来更新好友信息的列表，只有id，其实有点多余，改一下用friends，收回刚才的话
            #    self.updateop.overthread()
            self.friid.append(sourceinfo[0])
            self.updateop.upcurfrdstate(self.friid)
            #self.mainwin.set_item(self.friends)
            #加好友信息就不会在消息里提示了
        if sourceinfo[0] not in self.chatwins:
            self.message.append(data)
            self.mainwin.pushButton_4.setText('消息'+str(self.message.__len__()))

    #####发信息的函数
    def openchatwin(self,item):  
        firid = item.text()
        #判断是否在线，不在线不能聊天
        if self.friends[firid][1] == 'n':
            QMessageBox.about(self.mainwin,'提示','TA现在不在线，不能发送消息哦')
        elif firid in self.chatlists:
            pass
        else:
            #更新当前已打开的聊天窗口字典
            if firid not in self.chatlists:
                self.chatlists.append(firid)
            senderinfo = (self.hostid,self.name,self.hostip)
            receiverinfo = (firid,self.friends[firid][0],self.friends[firid][1])
            curserver =  chat.Clientchatserver(ip=self.hostip,port=9878)#监听多个时端口号应该要处理一下
            self.chatwins[firid] = chatwindow(sinfo = senderinfo,rinfo= receiverinfo,conserver= curserver)
            recordpath = 'data/'+self.hostid+'/'+firid+'.pkl'
            if os.path.isfile(recordpath):
                self.chatwins[firid].readrecord()  #读取记录信息
            self.chatwins[firid].show()
            self.chatwins[firid].conserver.receivedmsg.connect(self.chatwins[firid].displayonemsg)
            self.chatwins[firid].pushButton_2.clicked.connect(self.chatwins[firid].sendmsgtext)
            self.chatwins[firid].pushButton_4.clicked.connect(self.chatwins[firid].sendmsgfile)
            self.chatwins[firid].closechatwin.connect(self.chatwins[firid].saverecording)#保存聊天记录方便下次查看
            self.chatwins[firid].closechatwin.connect(self.updatechatlist)
            self.chatwins[firid].conserver.run()
            #threading.Thread(target=self.newchatformfirst,name='newchatformnon',args=(self.chatwins[firid],)).start()

    def openmessbar(self):
        if len(self.message) == 0:
            QMessageBox.about(self.mainwin,"提示","暂时没有人发消息······")
        else:
            msgpack = []
            dellist = []
            msgpack.append(self.message[-1])
            for i in range(len(self.message)-1):
                #改成元素搜索，索引会报错
                if self.message[i]['sender'] == self.message[-1]['sender']:
                    msgpack.append(self.message[i])
                    dellist.append(i)
            self.message.remove(self.message[-1])
            for i in range(len(dellist)-1,-1,-1):
                self.message.remove(self.message[dellist[i]])
                    
            #刷新主界面的消息个数
            self.mainwin.pushButton_4.setText('消息'+str(self.message.__len__()))
            #self.chatlists[self.message[-1]['sender'][0]] = self.friends[self.message[-1]['sender'][0]]#有啥用？
            curid = msgpack[0]['sender'][0]
            if curid not in self.chatlists:
                self.chatlists.append(curid)
            #发送者自己的信息
            senderinfo = (self.hostid,self.name,self.hostip)
            receiverinfo = msgpack[0]['sender']
            curserver =  chat.Clientchatserver(ip=self.hostip,port=9878)#监听多个时端口号应该要处理一下
            self.chatwins[curid] = chatwindow(sinfo = senderinfo,rinfo= receiverinfo,conserver= curserver)
            recordpath = 'data/'+self.hostid+'/'+curid+'.pkl'
            if os.path.isfile(recordpath):
                self.chatwins[curid].readrecord()  #读取记录信息
            self.chatwins[curid].show()
            self.chatwins[curid].conserver.receivedmsg.connect(self.chatwins[curid].displayonemsg)
            self.chatwins[curid].pushButton_2.clicked.connect(self.chatwins[curid].sendmsgtext)
            self.chatwins[curid].displaymsg(msgpack)
            self.chatwins[curid].conserver.run()
            #threading.Thread(target=self.newchatform,name='newchatformx',args=(msgpack,self.chatwins[curid])).start()

    def newchatformfirst(self,window):
        #window.conserver.receivedmsg.connect(self.displayonemsg)
        #chatwindow = chatwindow(sinfo = senderinfo,rinfo= receiverinfo,conserver= curserver)
        #self.chatwins[receiveid].pushButton_2.clicked.connect(self.chatwins[receiveid].sendmsgtext)
        #window.pushButton_2.clicked.connect(window.sendmsgtext)
        window.conserver.start()
        #app = QApplication(sys.argv)
        #self.chatwins[receiveid].show()
        #chatwin = chatwindow(sinfo = senderinfo,rinfo= receiverinfo)

    def newchatform(self,msgpack,window):
        #window.conserver.receivedmsg.connect(self.displayonemsg)
        #window.pushButton_2.clicked.connect(window.sendmsgtext)
        #window.displaymsg(msgpack)
        window.conserver.start()
        
    
    #或许放到第三个线程类的函数中会更好
    def displayonemsg(self,data):
        curid = data['sender'][0]
        if data['type'] == 'TEXT':
            self.chatwins[curid].textEdit.setText(data['sender'][0]+' '+data['time']+'\n')
            self.chatwins[curid].textEdit.setText(data['content']+'\n')

    def displaymsg(self,msgpack):
        #文件处理之后处理
        curid = msgpack[0]['sender'][0]
        for i in range(len(msgpack)):
            if msgpack[i]['type'] == 'TEXT':
                data = msgpack[i]
                self.chatwins[curid].textEdit.setText(data['sender'][0]+' '+data['time']+'\n')
                self.chatwins[curid].textEdit.setText(data['content']+'\n')

    ##### 传送文件功能
    
    #####下线和关闭程序处理  
        

if __name__ == "__main__":
    app = QApplication(sys.argv)
    logoper = mainoperation()
    logoper.log.show()
    sys.exit(app.exec_())
    os.system("pause")