# -*- coding: utf-8 -*-
"""
Created on Sun Mar 13 18:18:50 2016

@author: Paniker
"""
import os
import sys
import xml.etree.ElementTree as ET

import configparser
import threading
import urllib
from urllib import request

import PyQt4
from PyQt4 import QtGui, uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

class charGetter(threading.Thread):
    
    def __init__(self, keyID = '', vCode = ''):
        
        super(charGetter, self).__init__()
        
        self.chars = []
        self.keyID = keyID
        self.vCode = vCode
        self.url = 'https://api.eveonline.com/account/Characters.xml.aspx?keyID='+self.keyID+'&vCode='+self.vCode
        
    def run(self):
        self._Url_Update()
        self._Chars_GetFromAPI()
        
    def _Url_Update(self):
        self.url = 'https://api.eveonline.com/account/Characters.xml.aspx?keyID='+self.keyID+'&vCode='+self.vCode

    def _Chars_GetFromAPI(self):
        
        file = request.urlopen(self.url)
        
        tree = ET.parse(file)
        root = tree.getroot()
        
        self.chars = []
        
        for child in root.iterfind('./result/rowset/row'):
            
            charID = child.get('characterID', default = '-1')
            charName =child.get('name', default = '-1')
            
            self.chars.append([charID, '0', charName])

class Window_CharManager(QtGui.QDialog):

    def __init__(self):
        
            # WINDOW SETTING
        super(Window_CharManager, self).__init__()
        uic.loadUi(os.getcwd()+'/forms/CharManager.ui', self)
        
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('Char Manager')
        self.setFixedSize(self.width(),self.height())
        
            # VARS
        self.closeWithFunction = None
        
        self.keysSection = ['']
        self.keys = ['']
        self.vc = ['']
        
        self.updatingKey = 0
        self.charGetter = charGetter(self.keys[self.updatingKey], self.vc[self.updatingKey])
        
        self.timer = PyQt4.QtCore.QTimer()
        self.timer.timeout.connect(self.timerAction)
        
        self.chars = []
                             
            # ELEMENT PROPERTIES
        self.BTN_Update.released.connect(self.char_update)  
                
        self.BTN_MakeActive.released.connect(self.makeActive)
        self.BTN_MakeNonActive.released.connect(self.makeNonActive)
        
        self.BTN_Save.released.connect(self.saveChars)
        
        self.BTN_Close.released.connect(self.close)

            # INIT
        #self._List_Update()
        
        self.chars_load()
               
    def closeEvent(self, QCloseEvent):
        if self.closeWithFunction != None:
            self.closeWithFunction()
        
            # FUNC
                # BTN
                
    def char_update(self):
        
        if len(self.keys):
            
            self.BTN_Update.setEnabled(False)
        
            self.chars = []
            self._List_Update()
        
            self.updatingKey = 0
        
            self.charGetter = charGetter(self.keys[self.updatingKey], self.vc[self.updatingKey])
            self.charGetter.start()
            
            self.timer.start(100)
        
    def makeActive(self):
        
        if self.ListChar_NonActive.currentItem():
        
            item = self.ListChar_NonActive.currentItem()
            
            array = item.array
            array[1] = '1'
            
            sectionID = item.sectionID
            index = item.arrayID
        
            self.chars[sectionID][index] = array

            self.ListChar_NonActive.setCurrentRow(-1)
            
            print(self.chars)
            
            self._List_Update()
            
    def makeNonActive(self):
        
        if self.ListChar_Active.currentItem():
        
            item = self.ListChar_Active.currentItem()
            
            array = item.array
            array[1] = '0'
            
            sectionID = item.sectionID
            index = item.arrayID
        
            self.chars[sectionID][index] = array

            self.ListChar_Active.setCurrentRow(-1)
            
            print(self.chars)
            
            self._List_Update()
        
                # OTHER
    def timerAction(self):
        
        if not self.charGetter.isAlive():
            
            print('Trying get chars from key...')
            self.chars.append(self.charGetter.chars)
            
            print(self.charGetter.chars)
            self._List_Update()
            
            self.updatingKey = self.updatingKey + 1
            
            if self.updatingKey < len(self.keys):
                self.charGetter = charGetter(self.keys[self.updatingKey], self.vc[self.updatingKey])
                self.charGetter.start()
            else:
                self.BTN_Update.setEnabled(True)
                self.timer.stop()
                
    def saveChars(self):
        
        config = configparser.ConfigParser()
        config.read('config.ini')
        
        print('Ok')
        
        for key in range(len(self.keysSection)):

            if len(self.chars[key]):

                charID = self.chars[key][0][0]
                charShow = self.chars[key][0][1]
                charName = self.chars[key][0][2]

                for char in range(len(self.chars[key])-1):
                
                    charID = charID + ',' + self.chars[key][char+1][0]
                    charShow = charShow + ',' + self.chars[key][char+1][1]
                    charName = charName + ',' + self.chars[key][char+1][2]
                    
                config.set(self.keysSection[key],'Id',charID)
                config.set(self.keysSection[key],'Show',charShow)
                config.set(self.keysSection[key],'Name',charName)
    
        with open('config.ini', 'w') as configfile:    # save
            config.write(configfile)
                
        print('Config saved')

    def chars_load(self):
        
            # read config
        config = configparser.ConfigParser()
        config.read('config.ini')
        
            # read keys name
        self.keysSection = config['KEYS']['name']
        self.keysSection = self.keysSection.split(',')
        
            # read keys key
        self.keys = config['KEYS']['key']
        self.keys = self.keys.split(',')
        
            # read keys vc
        self.vc = config['KEYS']['vc']
        self.vc = self.vc.split(',')
        
            # update chars
        self.chars = []
        
            # if config has chars
        if self.keysSection!=['']:
        
            for section in self.keysSection:
            
                charID = config[section]['Id']
                charID = charID.split(',')
            
                charShow = config[section]['Show']
                charShow = charShow.split(',')
            
                charName = config[section]['Name']
                charName = charName.split(',')
            
                charsInKey = []
            
                for i in range(len(charID)):
                    charsInKey.append([charID[i], charShow[i], charName[i]])
                
                self.chars.append(charsInKey)
            
        print(self.chars)
        
        self._List_Update()
            
    def _List_Update(self):
            
        self.ListChar_Active.clear()
        self.ListChar_NonActive.clear()
            
        for line in range(len(self.chars)):
            
            for index in range(len(self.chars[line])):

                item = QListWidgetItem(self.chars[line][index][2])
                
                item.sectionID = line
                item.arrayID = index
                item.array = self.chars[line][index]
        
                if self.chars[line][index][1] == '1':
                    self.ListChar_Active.addItem(item)
                else:
                    self.ListChar_NonActive.addItem(item)
        
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Window_CharManager()
    window.show()
    sys.exit(app.exec_())