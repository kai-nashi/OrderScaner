# -*- coding: utf-8 -*-
"""
Created on Sat Mar 12 17:48:47 2016

@author: Paniker
"""

import os
import sys
import PyQt4
import configparser

from PyQt4 import QtGui, uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 
# PyQt4.QtCore.QString

import APIManager_APIAdd

    # === WINDOW ===

class Window_APIManager(QtGui.QDialog):

    def __init__(self):
        
            # WINDOW SETTING
        super(Window_APIManager, self).__init__()
        uic.loadUi(os.getcwd()+'/forms/APIManager.ui', self)
        self.setWindowModality(Qt.ApplicationModal)
        self.setWindowTitle('API Manager')
        self.setFixedSize(self.width(),self.height())
        
            # VARS
        self.window_APIAdd = APIManager_APIAdd.Window_APIAdd()   
        self.keys = []
        
            # ELEMENT PROPERTIES
        self.BTN_Add.released.connect(self._BTN_APIAdd)
        self.BTN_Edit.released.connect(self._BTN_APIEdit)
        self.BTN_Delete.released.connect(self._BTN_APIDelete)
        self.BTN_Close.released.connect(self.close)
        
        #self.TableAPI.cellClicked.connect(self._TableAPI_SelectRow)
        
            # INIT
        self._TableAPI_Init()
        self._APILoads()
        self._TableAPI_Update()
        
        # === BTNS ===

    def _BTN_APIAdd(self):
        self.window_APIAdd.LE_Name.setText('')
        self.window_APIAdd.LE_KEY.setText('')
        self.window_APIAdd.LE_VC.setText('')
        self.window_APIAdd.show()
        self.window_APIAdd.closeWithFunction = self._APIAdd
        
    def _BTN_APIEdit(self):
        
        row = self.TableAPI.currentRow()
        
        if row >= 0:        
            name = self.keys[row][0]
            key = self.keys[row][1]
            vc = self.keys[row][2]
            
            print(name, key, vc)
        
            self.window_APIAdd.row = row
            self.window_APIAdd.oldName = name
            
            self.window_APIAdd.LE_Name.setText(name)
            self.window_APIAdd.LE_KEY.setText(key)
            self.window_APIAdd.LE_VC.setText(vc)
            self.window_APIAdd.show()
            self.window_APIAdd.closeWithFunction = self._APIUpdate
        
    def _BTN_APIDelete(self):
        
            # debug message
        print('Delete key')
        
            # get row and delete it
        row = self.TableAPI.currentRow()
        
            # if any selected
        if row >= 0:
            
            name = self.keys[row][0]
        
            del self.keys[row]
        
                # delete key section in config
            self._API_DeleteInINI(name)     
        
                # update config section keys and table
            self._APISave()
            self._TableAPI_Update()
        
            # OTHER
    def _APILoads(self):
        
            # CREATE CONFIG
        config = configparser.ConfigParser()
        config.read('config.ini')
    
            # READ DATA
        name = config['KEYS']['name']
        key = config['KEYS']['key']
        vc = config['KEYS']['vc']
        
            # if config has any keys
        if name!='':
        
                # SPLIT DATA
            name = name.split(',')
            key = key.split(',')
            vc = vc.split(',')
        
                # DO AS NEED
        
            self.keys = []
            
            for i in range(len(key)):
                newKey = []
                newKey.append(name[i])
                newKey.append(key[i])
                newKey.append(vc[i])
            
                self.keys.append(newKey)
        
    def _APIAdd(self):
        
            # debug message
        print('Get data')
        
            # read data
        name = self.window_APIAdd.name
        key = self.window_APIAdd.key
        vc = self.window_APIAdd.vc
        
            # create new key list and add it to other
        newKey = [name, key, vc]
        self.keys.append(newKey)
        
            # add section for key in config
        self._API_AddToINI(name,key,vc)
        
            # update section keys and update table
        self._APISave()
        self._TableAPI_Update()
        
    def _APIUpdate(self):
        
        row = self.window_APIAdd.row
        
        if row >= 0:
            
            oldName = self.window_APIAdd.oldName
            name = self.window_APIAdd.name
            key = self.window_APIAdd.key
            vc = self.window_APIAdd.vc
        
            newKey = [name, key, vc, oldName]
            self.keys[row] = newKey
        
            self._API_UpdateSection(name, key, vc, oldName)
        
            self._APISave()
            self._TableAPI_Update()
        
    def _APISave(self):
        
        config = configparser.ConfigParser()

        config.read('config.ini')
        
            # update section KEYS
        name = ''
        key = ''
        vc = ''
        
        if len(self.keys) >= 1:
            
            name = self.keys[0][0]
            key = self.keys[0][1]
            vc = self.keys[0][2]
            
            for i in range(len(self.keys)-1):
                name = name + ',' + self.keys[i+1][0]
                key = key + ',' + self.keys[i+1][1]
                vc = vc + ',' + self.keys[i+1][2]
        
        config.set('KEYS', 'name', name)
        config.set('KEYS', 'key', key)
        config.set('KEYS', 'vc', vc)

        with open('config.ini', 'w') as configfile:    # save
            config.write(configfile)
        
    def _API_AddToINI(self, name, key, vc):
        
            # read config
        config = configparser.ConfigParser()
        config.read('config.ini')
        
            # add section with new name
        config.add_section(name)

            # update items
        config.set(name,'key',key)
        config.set(name,'vc',vc)
        config.set(name,'id','')
        config.set(name,'show','')
        config.set(name,'name','')
        
            # dsave config
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        
    def _API_DeleteInINI(self, name):
        
            # read config
        config = configparser.ConfigParser()
        config.read('config.ini')

            # remove section
        config.remove_section(name)
        
            # save config
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
            
    def _API_UpdateSection(self, name, key, vc, oldName = None):
        
            # read config
        config = configparser.ConfigParser()
        config.read('config.ini')

            # if section exist
        if config.has_section( name ):
            config.set(name, 'key', key)
            config.set(name, 'vc', vc)
            
            # if no section with name
        else:
                
                # if have oldName, try to find it and if found
            if oldName != None:
                if config.has_section( oldName ):
                    
                        # get all items from old
                    items = config.items(oldName)

                        # add section with new name
                    config.add_section(name)
        
                        # copy all items from oldName to new
                    for item in items:
                        config.set(name,item[0],item[1])
                        
                        # update key and vc
                    config.set(name,'key',key)
                    config.set(name,'vc',vc)
    
                        # remove renamed section
                    config.remove_section(oldName)

            # save config
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        
    def _TableAPI_Init(self):
        
            # title, colums and eaders
        self.TableAPI.setWindowTitle("Set QTableWidget Header Alignment")
        self.TableAPI.setColumnCount(3)
        self.TableAPI.setHorizontalHeaderLabels(['Name','Key','Verification Code'])
        
            # colum size
        self.TableAPI.setColumnWidth(0,100)
        self.TableAPI.setColumnWidth(1,50)
        self.TableAPI.setColumnWidth(2,550)
        
    def _TableAPI_Update(self):

        self.TableAPI.setRowCount(len(self.keys))
        
        for i in range(len(self.keys)):
            for j in range(len(self.keys[i])):
                self.TableAPI.setItem(i, j, QTableWidgetItem( str(self.keys[i][j])) )

"""
if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Window_APIManager()
    window.show()
    sys.exit(app.exec_())
"""