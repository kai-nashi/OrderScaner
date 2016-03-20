# -*- coding: utf-8 -*-
"""
Created on Sat Mar 12 20:16:31 2016

@author: Paniker
"""

import os
import configparser

import PyQt4
from PyQt4 import QtGui, uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

class Window_APIAdd(QtGui.QDialog):

    def __init__(self):
        
            # WINDOW SETTING
        super(Window_APIAdd, self).__init__()
        uic.loadUi(os.getcwd()+'/forms/APIManager_APIAdd.ui', self)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Add API')
        self.setFixedSize(self.width(),self.height())
        
            # VARS
        self.row = None
        self.name = ''
        self.oldName = ''
        self.key = ''
        self.vc = ''
        
        self.closeWithFunction = None
        
            # ELEMENT PROPERTIES
        self.BTN_OK.released.connect(self._AddAPIKey)
        self.BTN_Cancel.released.connect(self.close)
        
            # FUNCTION
        
    def _AddAPIKey(self):
        
        self.oldName = self.name
        self.name = self.LE_Name.text()
        self.key = self.LE_KEY.text()
        self.vc = self.LE_VC.text()
        
        self.key = self.key.replace(' ', '')
        self.vc = self.vc.replace(' ', '')
        
        if self.oldName != self.name:
        
            if self._ValidName(self.name):
            
                if self.closeWithFunction != None:
                    self.closeWithFunction()

                self.close()
        else:
            if self.closeWithFunction != None:
                self.closeWithFunction()

        self.close()
            
        
    def _ValidName(self, name):
        
            # read config
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        if config.has_section(name):
            return 0
        else:
            return 1

"""
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Window_APIAdd()
    window.show()
    sys.exit(app.exec_())
"""