#!/bin/env python
# -*- encoding: utf-8 -*-

##
#   @file SettingRTCConf.py
#   @brief 



import thread



import sys,os,platform
import re
import time
import random
import commands
import math
import imp





from PyQt4 import QtCore, QtGui

import AutoBuildWindow.MainWindow






        
##
# @brief 
def main():
    
    app = QtGui.QApplication([""])
    mainWin = AutoBuildWindow.MainWindow.MainWindow()
    mainWin.show()
    app.exec_()
    
    
    

    
    
    
if __name__ == "__main__":
    main()
