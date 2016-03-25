# -*- coding: utf-8 -*-
"""
Created on Fri Mar 18 23:18:42 2016

@author: Paniker
"""
import os
import sys
import PyQt4
import configparser

from PyQt4 import QtGui, uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 

class Window_Settings(QtGui.QDialog):
    
    def __init__(self):
        
            # INIT SUPER CLASS AND SHOW WINDOW
        super(Window_Settings, self).__init__()
        uic.loadUi('forms/Settings.ui', self)
        self.show()
        
            # VARS
        self.path = ''
        self.alarmOn = 1
        self.alarmTime = 10000
        self.loopScan = 1
        
        self.widgets = []
        self.tableHeaders = {0:'Char',
                             1:'Item',
                             2:'Count',
                             3:'Price',
                             4:'Last check',
                             5:'Attension',
                             6:'Alarm',
                             7:'Check',
                             8:'Range',
                             9:'Region',
                             10:'Solar system',
                             11:'Station'}
        
        self.closeWithFunction = None
        
            # ELEMENTS
        self.LE_Path.editingFinished.connect( self.settings_update )
        
        self.CB_AlarmEnable.stateChanged.connect( self.settings_update )
        self.CB_LoopScan.stateChanged.connect( self.settings_update )
        
        self.SB_AlarmTime.valueChanged.connect( self.settings_update )
        
            # BTNS
        
        # main
        self.BTN_ChangePath.released.connect( self.settings_newPath )
        
        self.BTN_Default.released.connect( self.settings_default )
        self.BTN_Ok.released.connect( self.settings_save )
        self.BTN_Close.released.connect( self.close )
        
        # tableSell
        self.BTN_TableSettings_Up.released.connect(self.settings_tableSettings_MoveUp)
        self.BTN_TableSettings_Down.released.connect(self.settings_tableSettings_MoveDown)
        self.BTN_TableSettings_SetOn.released.connect(self.settings_tableSettings_SetOn)
        self.BTN_TableSettings_SetOff.released.connect(self.settings_tableSettings_SetOff)
        
            # INIT CODE
        self.settings_tableSettings_update(self.List_TableSettings_Off,
                                           self.List_TableSettings_On)
        
        self.settings_load()
        self.window_update()
        
    def closeEvent(self, QCloseEvent):
        if self.closeWithFunction != None:
            self.closeWithFunction()

    def settings_load(self):
        
        print('Load settings')
        
            # read config
        config = configparser.ConfigParser()
        config.read('config.ini')
        
            # read settings
        
        self.path = config['MAIN']['marketlogs']
        self.alarmOn = int( config['MAIN']['alarmEnable'] )
        self.alarmTime = int( config['MAIN']['alarmTime'] )
        self.loopScan = int( config['MAIN']['loopScan'] )
        
            # check alarm timmer
        if self.alarmTime < 10000:
            self.alarmTime = 10000
        
            # table settings
        
        # load enabled columns
        TableSettings = config['MAIN']['tableSettings']
        TableSettings = TableSettings.split(',')
        
        self.TableSettings_enabled = []
        
        # if settings for table sell has elements
        if TableSettings != ['']:
            for item in TableSettings:
                self.TableSettings_enabled.append(int(item))
        
        #update orderBuy settings  
        self.settings_tableSettings_update(self.List_TableSettings_Off,
                                           self.List_TableSettings_On, 
                                           self.TableSettings_enabled)
        
    def window_update(self):
        
            # CB buged, two near and next set
            # ignored read variable from other place, only vars in function
        
            # Main
        path = self.path
        
        alarmEnable = self.alarmOn
        loopScan = self.loopScan
        
        alarmTime = self.alarmTime/1000
        
        self.LE_Path.setText( path )
        
        self.CB_AlarmEnable.setChecked( alarmEnable )
        self.CB_LoopScan.setChecked( loopScan )
        
        self.SB_AlarmTime.setValue( alarmTime )
        
    def settings_newPath(self):
        
        newPath = PyQt4.QtGui.QFileDialog.getExistingDirectory(self, "Open Directory", self.path,
                                                               QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        
        if len(newPath):
            self.path = newPath.replace('\\','/') + '/'
            self.LE_Path.setText( self.path )
        
    def settings_update(self):
        
        self.path = self.LE_Path.text()
        
        self.alarmOn = int (self.CB_AlarmEnable.isChecked() )
        self.loopScan = int( self.CB_LoopScan.isChecked() )
        
        self.alarmTime = self.SB_AlarmTime.value() * 1000
        
    def settings_default(self):
        
        self.path = ''
        self.alarmOn = 1
        self.alarmTime = 10000
        self.loopScan = 1
        
        self._UpdateWindow()
        
    def settings_save(self):
        
            # DEBUG
        print('Path:', self.path)
        
        print('Alarm On:', self.alarmOn)
        print('Loop scan:', self.loopScan)
        
        print('AlarmTime:', self.alarmTime)
        
        print('Table:', self.TableSettings_enabled)
        
            # read config
        config = configparser.ConfigParser()
        config.read('config.ini')
        
            # set settings
        config.set('MAIN','marketlogs', self.path)

        config.set('MAIN','alarmEnable', str(self.alarmOn) )
        config.set('MAIN','loopScan', str(self.loopScan) ) 

        config.set('MAIN','alarmTime', str(self.alarmTime) )
            
            # save table settings
            
        # sell
        enabled = []

        for i in self.TableSettings_enabled:
            enabled.append(str(i))
        
        config.set('MAIN','tableSettings', ','.join(enabled))
        
            # save config
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        
        self.close()
        
    def settings_tableSettings_update(self, listOff, listOn, enabled = []):
        
        listOn.clear()
        listOff.clear()
        
        items = []
        
            # create list widgets
        for i in range(len(self.tableHeaders)):
            
            item = QListWidgetItem(self.tableHeaders[i])
            item.id = i
            
            items.append(item)
            
            # add active widgets to listOn
        for i in enabled:
            for item in items:
                
                if item.id == i:
                    listOn.addItem(item)
                    items.remove(item)
                
            # other add to listOff
        for item in items:
            listOff.addItem(item)

    def settings_tableSettings_MoveUp(self):
        
        listOn = self.List_TableSettings_On
        listOff = self.List_TableSettings_Off
        enabled = self.TableSettings_enabled
        
            # get selected item
        item = listOn.currentItem()
        
            # if item
        if item:
            
            index = listOn.currentRow()
            
                # if index >= 1 (0 can't up)
            if index:
                
                    # modify enabled list
                enabled.remove(item.id)
                enabled.insert(index-1,item.id)
                
                    # update listOn
                self.settings_tableSettings_update(listOff, listOn, enabled)
        
                    # set selected uped item
                listOn.setCurrentRow(index-1)
                
    def settings_tableSettings_MoveDown(self):
        
        listOn = self.List_TableSettings_On
        listOff = self.List_TableSettings_Off
        enabled = self.TableSettings_enabled
        
            # get selected item
        item = listOn.currentItem()
        
            # if item
        if item:
            
            index = listOn.currentRow()
            
                # if index < index of last element
            if index < listOn.count()-1:
                
                    # modify enabled list
                enabled.remove(item.id)
                enabled.insert(index+1,item.id)
                
                    # update listOn
                self.settings_tableSettings_update(listOff, listOn, enabled)
        
                    # set selected uped item
                listOn.setCurrentRow(index+1)
                
    def settings_tableSettings_SetOn(self):
        
        listOn = self.List_TableSettings_On
        listOff = self.List_TableSettings_Off
        enabled = self.TableSettings_enabled
        
        item = listOff.currentItem()
        
        if item:
            
            enabled.append(item.id)
            self.settings_tableSettings_update(listOff, listOn, enabled)
            
            listOn.setCurrentRow(listOn.count()-1)
        
    def settings_tableSettings_SetOff(self):
        
        listOn = self.List_TableSettings_On
        listOff = self.List_TableSettings_Off
        enabled = self.TableSettings_enabled
        
        item = listOn.currentItem()
        
        if item:
            
            enabled.remove(item.id)
            self.settings_tableSettings_update(listOff, listOn, enabled)
            
            for i in range(listOff.count()):
                
                itemInList = listOff.item(i)
                
                if itemInList.id == item.id:
                    listOff.setCurrentRow(i)
                    break  

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Window_Settings()
    sys.exit(app.exec_())
