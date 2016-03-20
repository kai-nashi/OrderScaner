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
        uic.loadUi(os.getcwd()+'/forms/Settings.ui', self)
        self.show()
        
            # VARS
        self.path = ''
        self.alarmOn = 1
        self.alarmTime = 10000
        self.loopScan = 1
        
        self.closeWithFunction = None
        
            # ELEMENTS
        self.LE_Path.editingFinished.connect( self._Settings_Update )
        
        self.CB_AlarmEnable.stateChanged.connect( self._Settings_Update )
        self.CB_LoopScan.stateChanged.connect( self._Settings_Update )
        
        self.SB_AlarmTime.valueChanged.connect( self._Settings_Update )
        
            # BTNS
        self.BTN_ChangePath.released.connect( self._Settings_NewPath )
        
        self.BTN_Default.released.connect( self._Settings_Default )
        self.BTN_Ok.released.connect( self._Settings_Save )
        self.BTN_Close.released.connect( self.close )
        
            # INIT CODE
        self._Settings_Load()
        self._Window_Update()
        
    def closeEvent(self, QCloseEvent):
        if self.closeWithFunction != None:
            self.closeWithFunction()
        
    def _Window_Update(self):
        
            # CB buged, two near and next set
            # ignored read variable from other place, only vars in function
        path = self.path
        
        alarmEnable = self.alarmOn
        loopScan = self.loopScan
        
        alarmTime = self.alarmTime/1000
        
        self.LE_Path.setText( path )
        
        self.CB_AlarmEnable.setChecked( alarmEnable )
        self.CB_LoopScan.setChecked( loopScan )
        
        self.SB_AlarmTime.setValue( alarmTime )
        
    def _Settings_NewPath(self):
        
        newPath = PyQt4.QtGui.QFileDialog.getExistingDirectory(self, "Open Directory", self.path,
                                                               QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        
        if len(newPath):
            self.path = newPath.replace('\\','/') + '/'
            self.LE_Path.setText( self.path )
        
    def _Settings_Update(self):
        
        self.path = self.LE_Path.text()
        
        self.alarmOn = int (self.CB_AlarmEnable.isChecked() )
        self.loopScan = int( self.CB_LoopScan.isChecked() )
        
        self.alarmTime = self.SB_AlarmTime.value() * 1000
        
    def _Settings_Default(self):
        
        self.path = ''
        self.alarmOn = 1
        self.alarmTime = 10000
        self.loopScan = 1
        
        self._UpdateWindow()
        
    def _Settings_Save(self):
        
            # DEBUG
        print( 'Path:', self.path )
        
        print( 'Alarm On:', self.alarmOn )
        print( 'Loop scan:', self.loopScan )
        
        print( 'AlarmTime', self.alarmTime )
        
            # read config
        config = configparser.ConfigParser()
        config.read('config.ini')
        
            # set settings
        config.set('MAIN','marketlogs', self.path)

        config.set('MAIN','alarmEnable', str(self.alarmOn) )
        config.set('MAIN','loopScan', str(self.loopScan) ) 

        config.set('MAIN','alarmTime', str(self.alarmTime) )
        
            # save config
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        
        self.close()
        
    def _Settings_Load(self):
        
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


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    window = Window_Settings()
    sys.exit(app.exec_())
