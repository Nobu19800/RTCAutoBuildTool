#!/bin/env python
# -*- encoding: utf-8 -*-

##
#   @file .py
#   @brief 



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

def getFileName(name):
    tmp = name.split(" ")
    filaname = ""
    for t in tmp:
        filaname += t + "_"

    filaname += "Genarate"

    return filaname

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
        
        if os.name == 'posix':
            cmd = "cp " + xmlFile.replace("\\","/") + " " + "RTC.xml"
        elif os.name == 'nt':
            cmd = "copy " + xmlFile.replace("/","\\") + " " + "RTC.xml"
        f.write(cmd+"\n")

    f.close()

    
    

##
#バイナリファイルより文字読み込みする関数
##
def ReadString(ifs):
    s = struct.unpack("i",ifs.read(4))[0]
    a = ifs.read(s)

    return a

##
#バイナリファイルに文字保存する関数
##
def WriteString(a, ofs):
    
    a2 = a + "\0"
    s = len(a2)
    
    d = struct.pack("i", s)
    ofs.write(d)
    
    ofs.write(a2)



class MainWindow(QtGui.QMainWindow):
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

	

    def addSlot(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,u"開く","","Text File (*.txt);;All Files (*)")
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
        #os.path.abspath(filename)
        #filename = os.path.abspath(filename)
        #dname = os.path.dirname(filename)
        #fname = os.path.basename(filename)
        #name, ext = os.path.splitext(fname)
        #pname = os.path.basename(dname)
        #os.path.relpath(compname).replace("\\","/")
        
    def remSlot(self):
        self.fileListBox.removeItem(self.fileListBox.findText(self.fileListBox.currentText()))
        
    ##
    #アクションの作成の関数
    ##
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
    #メニューの作成の関数
    ##
    def createMenus(self):

	self.fileMenu = self.menuBar().addMenu("&File")
	self.fileMenu.addAction(self.newAct)
        self.fileMenu.addAction(self.openAct)
        self.fileMenu.addAction(self.saveAct)
        self.fileMenu.addAction(self.saveAsAct)


    

    def getFilePath(self):
        fileName = QtGui.QFileDialog.getOpenFileName(self,u"開く","","Config File (*.conf);;All Files (*)")
        if fileName.isEmpty():
            return ""
        ba = str(fileName.toLocal8Bit())
        #ba = ba.replace("/","\\")
        

        return ba

    ##
    #ファイル読み込みスロット
    ##
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
                
        f = open(dname+"/"+fname, "wb")
        
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
        
    def save(self):
        if self.curFile == "":
            return self.saveAs()
        else:
            self.saveFile(self.curFile)
            return True

    ##
    #ファイル保存のスロット
    ##
    def saveAs(self):
        
        fileName = QtGui.QFileDialog.getSaveFileName(self,u"保存", "","Config File (*.conf);;All Files (*)")
	if fileName.isEmpty():
            return False

	ba = str(fileName.toLocal8Bit())
	
        self.saveFile(ba)
        self.curFile = ba
        return True
	
	

    ##
    #初期化のスロット
    ##
    def newFile(self):
        self.curFile = ""
        self.fileListBox.clear()


        

    def mesBox(self, mes):
        msgbox = QtGui.QMessageBox( self )
        msgbox.setText( mes )
        msgbox.setModal( True )
        ret = msgbox.exec_()
