# -*- coding: utf-8 -*-
"""
Created on Wed Mar  9 18:16:25 2016

@author: Paniker
"""

import os
import sys
import threading
import PyQt4
import time

import configparser

from PyQt4 import QtGui, QtCore, uic
from PyQt4.QtGui import * 
from PyQt4.QtCore import * 
# PyQt4.QtCore.QString

import EVE_Orders

import APIManager
import CharManager
import Settings

#==============================================================================
#     WINDOW
#==============================================================================

class trayMassanger():
    
    def __init__(self, workDir):
        
        super(trayMassanger, self).__init__()
        
        self.dir =  workDir
        
            # tray settings
        self.tray = QtGui.QSystemTrayIcon()
        
        self.tray.setIcon(QtGui.QIcon( self.dir+'/images/icon.PNG') )
        self.tray.show()
        
    def _OrdersAlarm(self, ordersAlarm):

            # create vars for sort orders
        sellOrdersMessage = []
        buyOrdersMessage = []
        
            # for all orders need to alarm
        for order in ordersAlarm:
            
                # create message
            message = order.itemName
            message = message + ' [' + order.solarSystemName + ']'
            
                # sort message
            if order.bid == 0:
                sellOrdersMessage.append(message)
            else:
                buyOrdersMessage.append(message)

            # if message was not empty
        if len(sellOrdersMessage) or len(buyOrdersMessage):
            
            message = ''
            
                # if have to alarm about sell orders
            if len(sellOrdersMessage) > 0:
                
                    # add title
                message = message + 'Sell orders:\n'
                
                    # add orders
                for line in sellOrdersMessage:
                    message = message + line + '\n'
    
                # empty string between sell and buy orders
            if message != '':
                message = message + '\n'
                
                # if have to alarm about buy orders
            if len(buyOrdersMessage) > 0:
                
                    # add title
                message = message + 'Buy orders:\n'
                
                    # add orders
                for line in buyOrdersMessage:
                    message = message + line + '\n'
                
                # show message
            self._Message_Show('Time to 0.1 war',message)
        
    def _Message_Show(self, title, message): 
        
        print('Show tray message')
        self.tray.showMessage(title,message)


class OrderScaner(QtGui.QMainWindow):
    
    def __init__(self, workDir):
        
            # INIT SUPER CLASS AND SHOW WINDOW
        super(OrderScaner, self).__init__()
        
        self.dir = workDir
        self.verison = '0.1.1'
        
            # widnow settings
        uic.loadUi( self.dir + '/forms/Main.ui', self)
        self.setFixedSize(self.width(),self.height())
        self.show()
        
            # MAIN VARS
        self.path = ''
        self.alarmOn = 1
        self.alarmTime = 10000
        self.loopScan = 1
        
        self.Window_APIManager = None
        self.Window_CharManager = None
        self.Window_Settings = None
        
            # orders to alarm
        self.ordersForAlarm = []
        
            # TRAY
        # create tray messanger
        self.trayMessanger = trayMassanger(self.dir)
        
        # timers for messanger
        self.trayMessangerTimer = QtCore.QTimer()
        self.trayMessangerTimer.timeout.connect(self._OrdersAlarm)
        self.trayMessangerTimer.start(self.alarmTime)
        
        self.chars = []

            #   ORDERS
        # flag for scaning by row
        self.scanByRow = False  
                
        # loaders
        self.ordersSell_Loader = None
        self.ordersBuy_Loader = None
        
        # loaders timer
        self.loadersTimer = QtCore.QTimer()
        self.loadersTimer.timeout.connect(self._OrdersLoader_CheckThread)
                                
        # scanTimer of scaners
        self.scanTimer = QtCore.QTimer()
        self.scanTimer.timeout.connect(self._TimerAction)
        
            # MENU
        
                # Main
        self.action_APIManager.triggered.connect(self._Open_APIManager)
        self.action_CharManager.triggered.connect(self._Open_CharManager)
        
        self.action_Settings.triggered.connect( self._Open_Settings )
        
        self.action_Exit.triggered.connect(self.close)
        
            # BTNS AND ETC
        
                # btns for load
        self.BTN_LoadAPI.released.connect(self._BTN_LoadAPI)
        self.BTN_LoadFile.released.connect(self._BTN_LoadFile)
        
                # btns for scan
        self.BTN_ScanStart.released.connect(self._BTN_ScanStart)
        self.BTN_ScanStop.released.connect(self._BTN_ScanStop)
    
                # Table
        # sell scnaer
        self.Table_OrdersSell.orders = []
        self.Table_OrdersSell.updated = 0
        self.Table_OrdersSell.scanRow = 0
        self.Table_OrdersSell.scanEnd = 0
        self.Table_OrdersSell.scaner = None
           
        self.Table_OrdersBuy.orders = []
        self.Table_OrdersBuy.updated = 0
        self.Table_OrdersBuy.scanRow = 0
        self.Table_OrdersBuy.scanEnd = 0
        self.Table_OrdersBuy.scaner = None
           # INIT CODE
        
        self._LoadSettings()
        self._TableOrders_Init()
        self._Chars_Update()
        
    def closeEvent(self, QCloseEvent):
        
        if self.scanByRow:
            self._BTN_ScanStop()

        if self.ordersSell_Loader != None:
            self.ordersSell_Loader.join()
            
        if self.ordersBuy_Loader != None:
            self.ordersBuy_Loader.join()
            
        if self.Table_OrdersSell.scaner != None:
            if self.Table_OrdersSell.scaner.isAlive():
                self.Table_OrdersSell.scaner.join()
                
        if self.Table_OrdersBuy.scaner != None:
            if self.Table_OrdersBuy.scaner.isAlive():
                self.Table_OrdersBuy.scaner.join()

        self.trayMessanger.tray.hide()
        exit()
        
            # === MENU ACTIONS ===
    def _Open_APIManager(self):
        print('Open [API Manager]')
        
        self.Window_APIManager = APIManager.Window_APIManager()
        self.Window_APIManager.show()
        
    def _Open_CharManager(self):
        print('Open [API Manager]')
        
        self.Window_CharManager = CharManager.Window_CharManager()
        self.Window_CharManager.show()
    
        self.Window_CharManager.closeWithFunction = self._Chars_Update
        
    def _Open_Settings(self):

        self.Window_Settings = Settings.Window_Settings()
        self.Window_Settings.show()
        
        self.Window_Settings.closeWithFunction = self._LoadSettings
        
            # === BTNS ===
        
    def _BTN_LoadAPI(self):
        
            # Stop scaning if it doing
        if self.scanByRow:
            self._BTN_ScanStop()
            
            # set enable all btns
        self.BTN_LoadAPI.setEnabled(False)
        self.BTN_LoadFile.setEnabled(False)
        self.BTN_ScanStart.setEnabled(False)
        self.BTN_ScanStop.setEnabled(False)
        
            # get index of current char
        char = self.QCombo_Chars.currentIndex()
        
            # if it
            # load char info and load sell and buy orders
        if char >= 0:
            
                # read data of char
            char = self.chars[char] # first char is index=1 in list, but index=0 pos in chars

            key = char[3]
            vc = char[4]
            charID = char[0]
            charName = char[1]

                # debug message
            print('Load orders from API (charID, key, vc)',charID,key,vc)
            
                # create new loaders
            self.ordersSell_Loader = EVE_Orders.ordersLoader_FromAPI(key,vc,charID,charName,0)
            self.ordersBuy_Loader = EVE_Orders.ordersLoader_FromAPI(key,vc,charID,charName,1)
            
                # start them
            self.ordersBuy_Loader.start()
            self.ordersSell_Loader.start()
            
                # start timer for check it
            self.loadersTimer.start(1000)

    def _BTN_LoadFile(self):
        
            # Stop scaning if it doing
        if self.scanByRow:
            self._BTN_ScanStop()
            
            # set enable all btns
        self.BTN_LoadAPI.setEnabled(False)
        self.BTN_LoadFile.setEnabled(False)
        self.BTN_ScanStart.setEnabled(False)
        self.BTN_ScanStop.setEnabled(False)
        
            # debug message
        print('Loading orders from file...')
        
            # get index of current char
        char = self.QCombo_Chars.currentIndex()
        
            # if it
            # load char info and load sell and buy orders
        if char >= 0:
        
                # get data of char
            char = self.chars[char] # first char is index=1 in list, but index=0 pos in chars
            charID = char[0]
        
                # debug message
            print('Load orders from file (path, charID)',self.path, charID)
            
                # create new loaders
            self.ordersSell_Loader = EVE_Orders.ordersLoader_FromFile(self.path, charID,0)
            self.ordersBuy_Loader = EVE_Orders.ordersLoader_FromFile(self.path, charID,1)
            
                # start them
            self.ordersBuy_Loader.start()
            self.ordersSell_Loader.start()
            
                # start timer for check it
            self.loadersTimer.start(1000)
        
    def _BTN_ScanStart(self):
        
        print('Scan starting...')        
        
        self.BTN_ScanStart.setEnabled(False)
        self.BTN_ScanStop.setEnabled(True)
        
        self.Table_OrdersSell.scanRow = 0
        self.Table_OrdersBuy.scanRow = 0

        self.scanByRow = True
        
        self.scanTimer.start(2000)
        
    def _BTN_ScanStop(self):
        
        print('Scan stoping...')
        
        self.BTN_ScanStart.setEnabled(True)
        self.BTN_ScanStop.setEnabled(False)
        
        self.scanByRow = False
        
        self.scanTimer.stop()
        
            # === OTHER ===
        
    def _TimerAction(self):
        
            # if sell orders exists, then check it
        if len(self.Table_OrdersSell.orders):
            self._TableOrders_CheckScaner(self.Table_OrdersSell)
        
            # if buy orders exists, then check it
        if len(self.Table_OrdersBuy.orders):
            self._TableOrders_CheckScaner(self.Table_OrdersBuy)
        
            # check not loop scan
        if not self.loopScan:

                # if sell scan row = len sell orders and buy too
            if self.Table_OrdersSell.scanRow == len(self.Table_OrdersSell.orders) and self.Table_OrdersBuy.scanRow == len(self.Table_OrdersBuy.orders):
                
                    # good flag for restar scan, maybe rename?
                self.Table_OrdersSell.updated = 1
                self.Table_OrdersBuy.updated = 1
                
                    # stopScan
                self._BTN_ScanStop()
        
    def _OrdersAlarm(self):

        self.trayMessanger._OrdersAlarm(self.ordersForAlarm)
        self.ordersForAlarm = []

    def _OrdersLoader_CheckThread(self):
        
            # debug massage
        print('Checking loaders...')
        
            # link for loaders for convenience
        sellLoader = self.ordersSell_Loader
        buyLoader = self.ordersBuy_Loader

            # if loaders id ended work
        if not ( sellLoader.isAlive() or buyLoader.isAlive() ):
            
                # debug message
            print('Loading end. Read data')
            
                # stop timer
            self.loadersTimer.stop()
            
                # make btns active
            self.BTN_LoadAPI.setEnabled(True)
            self.BTN_LoadFile.setEnabled(True)
            self.BTN_ScanStart.setEnabled(True)
            
                # read data
            self.Table_OrdersSell.orders = sellLoader.orders
            self.Table_OrdersBuy.orders = buyLoader.orders
            
                # update tables
            self._TableOrders_Update(self.Table_OrdersSell)
            self._TableOrders_Update(self.Table_OrdersBuy)
    
    def _Chars_Update(self):
        
            # debug
        print('Updating char list...')
        
            # Stop scaning if it doing
        if self.scanByRow:
            self._BTN_ScanStop()  
        
            # read config
        config = configparser.ConfigParser()
        config.read('config.ini')
        
            # read keys name
        keysSection = config['KEYS']['name']
        keysSection = keysSection.split(',')
        
            # read keys key
        keys = config['KEYS']['key']
        keys = keys.split(',')
        
            # read keys vc
        vc = config['KEYS']['vc']
        vc = vc.split(',')
        
            # update chars
        self.chars = []
        
            # if config has keys
        if keysSection != ['']:
        
            for i in range(len(keysSection)):
            
                charID = config[keysSection[i]]['Id']
                charID = charID.split(',')         
            
                charShow = config[keysSection[i]]['Show']
                charShow = charShow.split(',')
            
                charName = config[keysSection[i]]['Name']
                charName = charName.split(',')
                    
                    # if any char in keys
                if charID != ['']:
                    
                        # for all chars in key
                    for j in range(len(charID)):
                        
                            # if char show, add it to QList
                        if bool(int(charShow[j])):
                            self.chars.append([charID[j], charName[j], bool(int(charShow[j])), keys[i], vc[i]])
    
        self._QComboChars_Update()
        
                # Table
    def _QComboChars_Update(self):
        
        """
        Update list of chars from self.chars
        """
        
        self.QCombo_Chars.clear()
        
            # if chars has chars
        if len(self.chars):
            
                # set enable all btns
            self.BTN_LoadAPI.setEnabled(True)
            self.BTN_LoadFile.setEnabled(True)
            self.BTN_ScanStart.setEnabled(True)
            self.BTN_ScanStop.setEnabled(False)

            for char in self.chars:
                self.QCombo_Chars.addItem(char[1])
                
            # if no chars
        else:
                # set enable all btns
            self.BTN_LoadAPI.setEnabled(False)
            self.BTN_LoadFile.setEnabled(False)
            self.BTN_ScanStart.setEnabled(False)
            self.BTN_ScanStop.setEnabled(False)
                
    def _TableOrders_Init(self):
        
        """
        Start set ordersTable headers / columnWidth
        """
        
            # title, colums and eaders
        self.Table_OrdersBuy.setWindowTitle("Set QTableWidget Header Alignment")
        self.Table_OrdersBuy.setColumnCount(7)
        self.Table_OrdersBuy.setHorizontalHeaderLabels(['Char Name','Item','Count','Price(Sum)','Last check','',''])
        
            # colum size
        self.Table_OrdersBuy.setColumnWidth(0,100)
        self.Table_OrdersBuy.setColumnWidth(1,184)
        self.Table_OrdersBuy.setColumnWidth(2,50)
        self.Table_OrdersBuy.setColumnWidth(3,75)
        self.Table_OrdersBuy.setColumnWidth(4,73)
        self.Table_OrdersBuy.setColumnWidth(5,22)
        self.Table_OrdersBuy.setColumnWidth(6,22)
        
        attension = [QIcon(self.dir+'/images/good.PNG'),
                     QIcon(self.dir+'/images/bad.PNG'),
                     QIcon(self.dir+'/images/wait.PNG')]
        
        alarm = [QIcon(self.dir+'/images/messageOff.PNG'),
                 QIcon(self.dir+'/images/messageOn.PNG')]
        
        self.Table_OrdersBuy.attension = attension
        self.Table_OrdersBuy.alarm = alarm
        
        
            # title, colums and eaders
        self.Table_OrdersSell.setWindowTitle("Set QTableWidget Header Alignment")
        self.Table_OrdersSell.setColumnCount(7)
        self.Table_OrdersSell.setHorizontalHeaderLabels(['Char Name','Item','Count','Price(Unit)','Last check','',''])
        
            # colum size
        self.Table_OrdersSell.setColumnWidth(0,100)
        self.Table_OrdersSell.setColumnWidth(1,184)
        self.Table_OrdersSell.setColumnWidth(2,50)
        self.Table_OrdersSell.setColumnWidth(3,75)
        self.Table_OrdersSell.setColumnWidth(4,73)
        self.Table_OrdersSell.setColumnWidth(5,22)
        self.Table_OrdersSell.setColumnWidth(6,22)
        
        attension = [QIcon(self.dir+'/images/good.PNG'),
                     QIcon(self.dir+'/images/bad.PNG'),
                     QIcon(self.dir+'/images/wait.PNG')]
        
        alarm = [QIcon(self.dir+'/images/messageOff.PNG'),
                 QIcon(self.dir+'/images/messageOn.PNG')]
        
        self.Table_OrdersSell.attension = attension
        self.Table_OrdersSell.alarm = alarm
        
    def _TableOrders_Update(self, table):
        
        """
        make from ordersArray (self.ordersBuy/self.ordersSell)
        array of widget to insert it to Table and do it!
        """
        
        print('Creating tableOrders...')
        
        orders = table.orders
        tableOrders = []
        
            # for all order
        for order in orders:    
            line = []
                
            line.append(QTableWidgetItem(order.charName))                          
            line.append(QTableWidgetItem(order.itemName))                                    
            line.append(QTableWidgetItem(str(order.remaining)+'/'+str(order.entered)))                      
            line.append(QTableWidgetItem(str(order.price)))                                  
            
            date = order.checkDate
            
            if date == 0:
                line.append(QTableWidgetItem('Never')) 
            else:
                date = time.gmtime(date)
                line.append(QTableWidgetItem(time.strftime("%H:%M:%S", date)))   
                # add icons
            # alarm
            item = QTableWidgetItem()
            item.setIcon( table.attension[order.attension] )
            line.append(item)
            # message shows
            item = QTableWidgetItem()
            item.setIcon( table.alarm[order.alarm] )
            line.append(item)
                
            tableOrders.append(line)

        self._TableOrders_UpdateItems(table, tableOrders)
        
        
    def _TableOrders_UpdateItems(self, table, tableOrders):
    
        print('Table Orders update item...')

        table.updated = 1
        table.setRowCount( len(tableOrders) )
        
        for i in range( len(tableOrders) ):
            for j in range( len(tableOrders[i])):
                table.setItem(i, j, tableOrders[i][j])
                
    def _TableOrders_CheckScaner(self, table):

            # get scaner of table
        scaner = table.scaner
        
            # if scnaer exist
        if scaner != None:
            
            # check thread is cancel work
            if not scaner.isAlive():
            
                # if orders was update
                if table.updated:
                
                    # set flag that scan restart
                    table.updated = 0
                
                    # set scar Row, scaner and start scan
                    table.scanRow = 0
                    table.scaner = EVE_Orders.ordersScaner_Row(table.orders, table.scanRow)
                    table.scaner.start()
                
                    # if orders wasn't update then modify row
                else:
                    self._TableOrders_UpdateRow(table)
                    
            # if scaner don't exist
        else:
            
                # create and start it
            table.scaner = EVE_Orders.ordersScaner_Row(table.orders, table.scanRow)
            table.scaner.start()
                
    def _TableOrders_UpdateRow(self, table):
        
            # get newPrice from scaner and scaned row
        row = table.scaner.row
        
            # get order from scaner
        order = table.scaner.orders[row] 
        
            # update orders
        table.orders[row] = order

            # read order checkDate -> make tb_year = x; tb_month = x; ... ;
            # tb_year = x... -> string date (H:M:S)
        date = order.checkDate
        date = time.localtime(date)
        date = time.strftime("%H:%M:%S", date)
        
            # and modify table item
        table.item(row,4).setText(date)
        
            # if newPrice
        if not order.alarm:
                        
            if not order.top():
                
                    # if can be modify - red cross; else - orange
                if order.modifiable():
                    order.attension = 1
                else:
                    order.attension = 2
                    
                print(order.itemName, order.marketPrice)
                        
                # if order can be modify it's not top and alarm is On
            if order.modifiable() and not order.top() and self.alarmOn:

                order.alarm = 1 
                self.ordersForAlarm.append(order)

            # update remaining and price in table, and update icons
        table.item(row,2).setText( str(order.remaining) + '/' + str(order.entered) )
        table.item(row,3).setText( str(order.price) )
        table.item(row,5).setIcon( table.attension[order.attension] )
        table.item(row,6).setIcon( table.alarm[order.alarm] )
        
            # go to next row
        table.scanRow = row + 1
        
            # check that row in orders range
        if table.scanRow < len(table.orders):

                # create new scaner and start it
            table.scaner = EVE_Orders.ordersScaner_Row(table.orders, table.scanRow)
            table.scaner.start()

            # if out of range
        else:
                # if loop scan
            if self.loopScan:
                
                    # go to first element
                table.scanRow = 0
                
                    # and create new scaner
                table.scaner = EVE_Orders.ordersScaner_Row(table.orders, table.scanRow)
                table.scaner.start()
        
    def _LoadSettings(self):
        
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
        
            # set alarm timer new time
        self.trayMessangerTimer.start(self.alarmTime)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    
    workDir = os.getcwd()
    workDir = workDir.replace('\\','/')
    print( workDir )
    
    window = OrderScaner(workDir)

    app.setActiveWindow(window)
    app.setWindowIcon(QtGui.QIcon(workDir+'/images/icon.PNG'))
    
    sys.exit(app.exec_())

    #start the application's exec loop, return the exit code to the OS
    #exit(app.exec_())