#!/bin/env python
# -*- encoding: utf-8 -*-

##
#   @file MainWindow.py
#   @brief メインウインドウ



import thread
import struct

import optparse
import sys,os,platform
import traceback
import re
import time
import random
import commands
import math
import imp

import codecs


from PyQt4 import QtCore, QtGui

##
# @brief 書き込むファイルを開く
# @param n ファイル本体名
# @param ext 拡張子
# @return ファイルストリーム
def writefileInit(n, ext):
    
    if ext == ".sh":
        f = codecs.open(n+ext, 'w', "utf-8")
        f.write("#!/bin/sh\n")
        #f.write("PATH=/bin:/usr/bin:/sbin:/usr/sbin:/usr/local/bin\n")
        #f.write("script_dir=$(cd $(dirname ${BASH_SOURCE:-$0}); pwd)\n")
        #f.write("cd ${script_dir}\n")
        f.write("cd `dirname $0`\n")
    elif ext == ".bat":
        f = codecs.open(n+ext, 'w', "utf-8")
        f.write("cd /d %~dp0\n")
    return f

##
# @brief リリースビルド、デバッグビルド、インストール、アンインストールを行うバッチファイルを生成
# @param dname ディレクトリパス
# @param ext 拡張子
def createBuildFile(dname, ext):
    
    #f = writefileInit(dname+"/"+"Install",ext)
    f = writefileInit(os.path.join(dname,"Install"),ext)
    if ext == ".sh":
        f.write("make install\n")
    elif ext == ".bat":
        f.write("cmake --build . --config Release --target install\n")
    f.close()

    
    #f = writefileInit(dname+"/"+"unInstall",ext)
    f = writefileInit(os.path.join(dname,"unInstall"),ext)
    if ext == ".sh":
        f.write("make uninstall\n")
    elif ext == ".bat":
        f.write("cmake --build . --config Release --target uninstall\n")
    f.close()

    
    #f = writefileInit(dname+"/"+"BuildRelease",ext)
    f = writefileInit(os.path.join(dname,"BuildRelease"),ext)
    f.write("cmake --build . --config Release\n")
    f.close()

    
    #f = writefileInit(dname+"/"+"BuildDebug",ext)
    f = writefileInit(os.path.join(dname,"BuildDebug"),ext)
    f.write("cmake --build . --config Debug\n")
    f.close()

##
# @brief プロジェクト作成スクリプトのファイル名取得
# @param name 名前
# @return ファイル名
def getFileName(name):
    tmp = name.split(" ")
    filaname = ""
    for t in tmp:
        filaname += t + "_"

    filaname += "Genarate"

    return filaname

##
# @brief プロジェクト作成スクリプトの作成
# @param dname ディレクトリパス
# @param name 名前
# @param ext 拡張子
# @param path RTC.xmlの存在するディレクトリ
def createFile(dname, name, ext, path="./"):
    
    filename = getFileName(name)

    
    #f = writefileInit(dname+"/"+filename,ext)
    f = writefileInit(os.path.join(dname,filename),ext)
    cmd = "cmake "+path+"/"+" -G \""+name+"\""
    if ext == ".bat":
        cmd += " -D CMAKE_INSTALL_PREFIX=\"C:/OpenRTM-aist\" " + path+"/"
    f.write(cmd+"\n")

    xmlFile = os.path.join(path,"RTC.xml")
    relPath = os.path.relpath(os.path.join(dname,xmlFile))
    
    if os.path.exists(relPath):
        
        if ext == ".sh":
            cmd = "cp " + xmlFile.replace("\\","/") + " " + "RTC.xml"
        elif ext == ".bat":
            cmd = "copy " + xmlFile.replace("/","\\") + " " + "RTC.xml"
        f.write(cmd+"\n")

    f.close()

    
    


##
# @brief バイナリファイルより文字読み込みする関数
# @param ifs ファイルストリーム
# @return 文字列
def ReadString(ifs):
    s = struct.unpack("i",ifs.read(4))[0]
    a = ifs.read(s)

    return a


##
# @brief バイナリファイルに文字保存する関数
# @param a 文字列
# @param ofs ファイルストリーム
def WriteString(a, ofs):
    
    a2 = a + "\0"
    s = len(a2)
    
    d = struct.pack("i", s)
    ofs.write(d)
    
    ofs.write(a2)


##
# @class MainWindow
# @brief メインウインドウ
#
class MainWindow(QtGui.QMainWindow):
    ##
    # @brief コンストラクタ
    # @param self
    def __init__(self):
        super(MainWindow, self).__init__()

        self.setWindowTitle(u"CMake用スクリプト自動作成ツール")
        
        self.cwidget = QtGui.QWidget()
        self.mainLayout = QtGui.QVBoxLayout()
        self.cwidget.setLayout(self.mainLayout)
        self.setCentralWidget(self.cwidget)

        self.fileListBox = QtGui.QComboBox()
        self.mainLayout.addWidget(self.fileListBox)

        self.addButton = QtGui.QPushButton(u"追加")
        self.mainLayout.addWidget(self.addButton)
        self.addButton.clicked.connect(self.addSlot)

        self.addPath = "."

        self.remButton = QtGui.QPushButton(u"削除")
        self.mainLayout.addWidget(self.remButton)
        self.remButton.clicked.connect(self.remSlot)

        self.createAction()
        self.createMenus()
        
        self.curFile = ""

        self.fileNameListWin = ["Visual Studio 8 2005 Win64","Visual Studio 8 2005","Visual Studio 9 2008 Win64",
                    "Visual Studio 9 2008","Visual Studio 10 2010 Win64","Visual Studio 10 2010",
                    "Visual Studio 11 2012 Win64","Visual Studio 11 2012","Visual Studio 12 2013 Win64",
                    "Visual Studio 12 2013","Visual Studio 14 2015 Win64","Visual Studio 14 2015"]
        self.fileNameListUnix = ["CodeBlocks - Unix Makefiles","Unix Makefiles"]


    ##
    # @brief 追加ボタンのスロット
    # @param self
    def addSlot(self):
        
        fileName = QtGui.QFileDialog.getOpenFileName(self,u"開く",self.addPath,"Text File (*.txt);;All Files (*)")
        if fileName.isEmpty():
            return
        ba = str(fileName.toLocal8Bit())
        if self.curFile == "":
            f = os.path.relpath(ba).replace("\\","/")
        else:
            dname = os.path.dirname(self.curFile)
            f = os.path.relpath(ba, dname).replace("\\","/")

        if self.fileListBox.findText(f) == -1:
            self.fileListBox.addItem(f)
            
        self.addPath = os.path.relpath(os.path.dirname(ba))
        #os.path.abspath(filename)
        #filename = os.path.abspath(filename)
        #dname = os.path.dirname(filename)
        #fname = os.path.basename(filename)
        #name, ext = os.path.splitext(fname)
        #pname = os.path.basename(dname)
        #os.path.relpath(compname).replace("\\","/")

    ##
    # @brief 削除ボタンのスロット
    # @param self
    def remSlot(self):
        self.fileListBox.removeItem(self.fileListBox.findText(self.fileListBox.currentText()))
        
    
    ##
    # @brief アクションの作成の関数
    # @param self
    def createAction(self):

        self.newAct = QtGui.QAction("&New...",self)
        self.newAct.setShortcuts(QtGui.QKeySequence.New)
        self.newAct.triggered.connect(self.newFile)
        


        self.openAct = QtGui.QAction("&Open...",self)
        self.openAct.setShortcuts(QtGui.QKeySequence.Open)
        self.openAct.triggered.connect(self.open)


        self.saveAct = QtGui.QAction("&Save",self)
        self.saveAct.setShortcuts(QtGui.QKeySequence.Save)
        self.saveAct.triggered.connect(self.save)

        self.saveAsAct = QtGui.QAction("&Save &As",self)
        self.saveAsAct.setShortcuts(QtGui.QKeySequence.SaveAs)
        self.saveAsAct.triggered.connect(self.saveAs)

    
    
    ##
    # @brief メニューの作成の関数
    # @param self
    def createMenus(self):

        self.fileMenu = self.menuBar().addMenu("&File")
        self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)


    
    ##
    # @brief ダイアログで選択したファイルのパスを取得
    # @param self
    def getFilePath(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,u"開く","","Config File (*.conf);;All Files (*)")
        if fileName.isEmpty():
            return ""
        ba = str(fileName.toLocal8Bit())
        #ba = ba.replace("/","\\")
        

        return ba

    
    ##
    # @brief ファイル読み込みスロット
    # @param self
    def open(self):
        
        

        filepath = self.getFilePath()
        if filepath == "":
            return
        self.fileListBox.clear()
        
        f = open(filepath, 'rb')
        m = struct.unpack("i",f.read(4))[0]
        for i in range(0,m):
            c = ReadString(f).replace("\0","")
            self.fileListBox.addItem(c)
        f.close()
        
        self.curFile = filepath
        
        
    ##
    # @brief スクリプトファイルを生成
    # @param self
    # @param filename ファイル名
    # @param dirname　ディレクトリパス
    def saveScriptFile(self, filename, dirname):
        filename = os.path.abspath(filename)
        dname = os.path.dirname(filename)
        fname = os.path.basename(filename)
        name, ext = os.path.splitext(fname)
        pname = os.path.basename(dname)
        
        mkdName = dirname+"/"+pname
        if not os.path.exists(mkdName):
            os.mkdir(mkdName)

        
        

        ddname = os.path.relpath(dname,mkdName).replace("\\","/")

        
        
        for n in self.fileNameListWin:
            createFile(mkdName,n,".bat",ddname)
            

        
        for n in self.fileNameListUnix:
            createFile(mkdName,n,".sh",ddname)
            

        createBuildFile(mkdName,".bat")
        createBuildFile(mkdName,".sh")

        return mkdName

    ##
    # @brief ファイルを保存
    # @param self
    # @param filename ファイル名  
    def saveFile(self, filename):
        filename = os.path.abspath(filename)
        dname = os.path.dirname(filename)
        fname = os.path.basename(filename)
        name, ext = os.path.splitext(fname)
        pname = os.path.basename(dname)
        
        if name != pname:
            dname = dname + "/" + name
            if not os.path.exists(dname):
                os.mkdir(dname)
            
                
        f = open(os.path.join(dname,fname), "wb")
        
        clist = []
        for c in range(0, self.fileListBox.count()):
            clist.append(str(self.fileListBox.itemText(c).toLocal8Bit()))
            
                
        d = struct.pack("i", len(clist))
        f.write(d)

        curDname = os.path.dirname(self.curFile)
        
            
        scripts = []

        
        
        if self.curFile == "":
            self.fileListBox.clear()
            for c in clist:
                
                s = self.saveScriptFile(c,dname)
                scripts.append(s)
                c = os.path.relpath(c,dname).replace("\\","/")
                self.fileListBox.addItem(c)
                WriteString(c , f )
        else:
            self.fileListBox.clear()
            for c in clist:
                cn = os.path.relpath(curDname,dname)
                c = os.path.relpath(c,cn)
                cn = os.path.relpath(dname,"./")
                
                cn = cn+"/"+c
                
                s = self.saveScriptFile(cn,dname)
                scripts.append(s)
                self.fileListBox.addItem(c)
                WriteString(c , f )
        
       
        f.close()

        self.writeScriptFile("Install",".bat",dname,scripts)
        self.writeScriptFile("Install",".sh",dname,scripts)

        self.writeScriptFile("unInstall",".bat",dname,scripts)
        self.writeScriptFile("unInstall",".sh",dname,scripts)

        self.writeScriptFile("BuildRelease",".bat",dname,scripts)
        self.writeScriptFile("BuildRelease",".sh",dname,scripts)

        self.writeScriptFile("BuildDebug",".bat",dname,scripts)
        self.writeScriptFile("BuildDebug",".sh",dname,scripts)

        
        for n in self.fileNameListWin:
            name = getFileName(n)
            self.writeScriptFile(name,".bat",dname,scripts)
            
            
            
            

        
        for n in self.fileNameListUnix:
            name = getFileName(n)
            self.writeScriptFile(name,".sh",dname,scripts)

        self.curFile = os.path.join(dname,fname)

    ##
    # @brief 指定したスクリプトファイルを実行するスクリプトファイルを生成
    # @param self
    # @param filename ファイル名
    # @param ext 拡張子
    # @param dname ディレクトリパス
    # @param scripts スクリプトファイルのリスト
    def writeScriptFile(self, filename, ext, dname, scripts):
        
        f = writefileInit(dname+"/"+filename,ext)
        for sc in scripts:
            p = os.path.relpath(sc,dname)
            if ext == ".sh":
                f.write("sh ")
                p.replace("\\","/")
                f.write(p+"/"+filename+ext+"\n")
            elif ext == ".bat":
                p.replace("/","\\")
                f.write("cmd /c "+p+"\\"+filename+ext+"\n")
            
        f.close()

    ##
    # @brief ファイル保存スロット
    # @param self
    # @return 成功でTrue、失敗でFalse
    def save(self):
        if self.curFile == "":
            return self.saveAs()
        else:
            self.saveFile(self.curFile)
            return True

    ##
    # @brief 別名ファイル保存スロット
    # @param self
    # @return 成功でTrue、失敗でFalse
    def saveAs(self):
        
        fileName = QtGui.QFileDialog.getSaveFileName(self,u"保存", "","Config File (*.conf);;All Files (*)")
        if fileName.isEmpty():
            return False

        ba = str(fileName.toLocal8Bit())

        self.saveFile(ba)
        #self.curFile = ba
        return True

	

    
    ##
    # @brief 初期化のスロット
    # @param self
    def newFile(self):
        self.curFile = ""
        self.fileListBox.clear()


        
    ##
    # @brief メッセージボックス表示
    # @param self
    # @param mes 表示する文字列
    def mesBox(self, mes):
        msgbox = QtGui.QMessageBox( self )
        msgbox.setText( mes )
        msgbox.setModal( True )
        ret = msgbox.exec_()
