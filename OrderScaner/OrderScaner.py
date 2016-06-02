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

VERSION = '0.1.8'

#==============================================================================
# Table line
#==============================================================================

class tableLine(object):
    
    def __init__(self, table, order):
        
            # data (list of widgets for table)
        self.data = []
        
            # links to order of lines and mother table
        self.order = order
        self.table = table   
        
            # create widgets with data from order
        self.createData()
        
    def createData(self):
    
        """ 
        read data from orders and create list of created widgets
        index in list = columnIndex in table 
            
        example: 
            table.char = 0
            data[0] = 'CharName'
        """
        
        self.data = []
    
        order = self.order
        
            # char and item Name
        self.data.append(QTableWidgetItem(order.charName))
        self.data.append(QTableWidgetItem(order.itemName))
        
            # count
        self.data.append(QTableWidgetItem('/'.join(
                                                   [str(order.remaining), 
                                                    str(order.entered)]
                                                   )))
            # price
        self.data.append(QTableWidgetItem(str(order.price)))
        
            # date
        date = order.checkDate
            
        if date == 0:
            self.data.append(QTableWidgetItem('Never')) 
        else:
                # date from second to year,month,day
                # from year,month,day to string with setted format
            date = time.localtime(date)
            self.data.append(QTableWidgetItem(time.strftime("%H:%M:%S", date)))   
            
            # attension,alarm Icons and set to it icons
        self.data.append(QTableWidgetItem(''))
        self.setAttension(order.attension)
        
        self.data.append(QTableWidgetItem(''))
        self.setAlarm(order.alarm)

            # cb scan enabled

        # create new
        self.CB_Scan = QCheckBox(' Enable')
        self.CB_Scan.setChecked(order.scan)
        self.CB_Scan.stateChanged.connect(self.btn_setScan)

        # update
        self.data.append(self.CB_Scan)
        self.setScan(order.scan)
        
            # list scan mode
        self.List_ScanMode = QComboBox()
        self.List_ScanMode.addItem('Station')
        self.List_ScanMode.addItem('Solar system')
        self.List_ScanMode.addItem('Region')
        self.List_ScanMode.currentIndexChanged.connect(self.btn_setScanMode)
        
        self.data.append(self.List_ScanMode)
        self.setScanMode(order.scanMode)
        
            # region, solar system and region name
        self.data.append(QTableWidgetItem(order.regionName))
        self.data.append(QTableWidgetItem(order.solarSystemName))
        self.data.append(QTableWidgetItem(order.stationName))    
    
    def update(self):
    
        """ modify  datas from orders
        """
        
        order = self.order
        
        self.data[0].setText(order.charName)
        self.data[1].setText(order.itemName)
        
            # count
        self.data[2].setText('/'.join( [str(order.remaining), 
                                        str(order.entered)] ))
            # price
        self.data[3].setText(str(order.price))
        
            # date
        date = order.checkDate
            
        if date == 0:
            self.data[4].setText('Never')
        else:
                # date from second to year,month,day
                # from year,month,day to string with setted format
            date = time.localtime(date)
            self.data[4].setText(time.strftime("%H:%M:%S", date)) 
            
            # update icons (need for situation, when order is not top)
        item = self.data[self.table.attension]
        item.setIcon(self.table.attensionIcon[order.attension])
        
        item = self.data[self.table.alarm]
        item.setIcon(self.table.alarmIcon[order.alarm])

            # scanEnabled and scanMode list
        self.setScan(order.scan)
        self.setScanMode(order.scanMode)
        
            # region, solar system and region name
        self.data[9].setText(order.regionName)
        self.data[10].setText(order.solarSystemName)
        self.data[11].setText(order.stationName)
    
            # modify attension and alarm
        if not order.alarm and order.scan:
                        
            if not order.top():
                
                    # if haven't set attention's flag yet, print new price
                if not order.attension:
                    print(order.itemName, order.marketPrice)
                
                    # if order can be modify - red cross; else - orange
                if order.modifiable():
                    self.setAttension(1)
                else:
                    self.setAttension(2)
    
    def btn_setScan(self,value):
        
        self.setAlarm(0)
        self.setAttension(0)
        
        self.setScan(value)
        
    def btn_setScanMode(self,value):
        
        self.setAlarm(0)
        self.setAttension(0)
        
        self.setScanMode(value)
    
    def setScan(self, value):
        
        """ 
        set enable/disbale scan for order.
        
        value = True: set enabled
        value = False: set disabled
        """

        if value:
            self.order.scan = 1
            self.CB_Scan.setText('Enable')
        else:
            self.order.scan = 0
            self.CB_Scan.setText('Disable')
            
    def setScanMode(self, value):
        
        """
        set scan mode for order
        """
        
        self.order.scanMode = value
        
    def setAttension(self, value):
        
        """
        set attension to order and icon to widget
        """
        
        self.order.attension = value
        
        item = self.data[self.table.attension]
        item.setIcon(self.table.attensionIcon[value])
        
    def setAlarm(self, value):
        
        """
        set alarm to order and icon to widget
        """
        
        self.order.alarm = value
        
        item = self.data[self.table.alarm]
        item.setIcon(self.table.alarmIcon[value])


#==============================================================================
# Tray messanger
#==============================================================================

class trayMassanger(object):
    
    def __init__(self):
        
        super(trayMassanger, self).__init__()
        
        self.scaning = 0
        self.iconScaning = QtGui.QMovie("images/iconScaning.GIF")
        self.iconScaning.frameChanged.connect(self.iconUpdate)
        
            # alarm settings
        self.alarmWithSound = 1
        self.alarmWAV = QSound("sounds/alarm2.WAV")
        
            # tray settings
        self.tray = QtGui.QSystemTrayIcon()
        
        self.iconScaning.jumpToFrame(0)
        icon = QtGui.QIcon()
        icon.addPixmap(self.iconScaning.currentPixmap())
        self.tray.setIcon(icon)        
        
        self.tray.show()
        
        print(self.iconScaning.isValid())
        
    def setScaning(self, scaning):
        
        self.scaning = scaning
        
        if self.scaning:
            self.iconScaning.start()
            self.iconScaning.jumpToFrame(0)
        else:
            self.iconScaning.stop()
            self.iconScaning.jumpToFrame(0)
            
        icon = QtGui.QIcon()
        icon.addPixmap(self.iconScaning.currentPixmap())
        self.tray.setIcon(icon)
        
    def iconUpdate(self):
        
        if not self.scaning:
            self.iconScaning.stop()
            self.iconScaning.jumpToFrame(0)
            
        icon = QtGui.QIcon()
        icon.addPixmap(self.iconScaning.currentPixmap())
        self.tray.setIcon(icon)
        
    def showMessage_fromOrders(self, ordersAlarm):

            # create vars for sort orders
        sellOrdersMessage = []
        buyOrdersMessage = []
        
            # for all orders need to alarm
        for order in ordersAlarm:
            
                # if order is not to delete
            if order.exist:
                
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
                
                # alarmSound
            if self.alarmWithSound:
                self.alarmWAV.play()
                
                # show message
            self.showMessage('Time to 0.1 war',message)
        
    def showMessage(self, title, message): 
        
        print('Show tray message: ', 
              time.strftime("%H:%M:%S", time.localtime()),
              end = ' ')
        
        self.tray.showMessage(title,message)
        
        print('ok')

#==============================================================================
#     WINDOW
#==============================================================================

class OrderScaner(QtGui.QMainWindow):
    
    def __init__(self):
        
            # INIT SUPER CLASS AND SHOW WINDOW
        super(OrderScaner, self).__init__()
        
            # widnow settings
        uic.loadUi('forms/Main.ui', self)
        self.show()
        
            # MAIN VARS
        self.path = ''
        self.alarmOn = 1
        self.alarmTime = 10000
        self.alarmWithSound = 1
        self.loopScan = 1
        
        self.Window_APIManager = None
        self.Window_CharManager = None
        self.Window_Settings = None
        
        self.fulfilledWAV = QSound("sounds/fulfilled.WAV")
        
            # orders to alarm
        self.ordersForAlarm = []
        
            # TRAY
        # create tray messanger
        self.trayMessanger = trayMassanger()
        
        # timers for messanger
        self.trayMessangerTimer = QtCore.QTimer()
        self.trayMessangerTimer.timeout.connect(self.showMessage_fromOrders)
        self.trayMessangerTimer.start(self.alarmTime)
        
        self.chars = []
        self.myOrders = []        
        
            #   ORDERS
        # flag for scaning by row
        self.scanByRow = False  
                
        # loaders
        self.ordersSell_Loader = None
        self.ordersBuy_Loader = None
        
        # loaders timer
        self.loadersTimer = QtCore.QTimer()
        self.loadersTimer.timeout.connect(self.orderLoader_checker)
                                
        # scanTimer of scaners
        self.scanTimer = QtCore.QTimer()
        self.scanTimer.timeout.connect(self.orderScaner_checker)
        
            # MENU
        
                # Main
        self.action_APIManager.triggered.connect(self.open_APIManager)
        self.action_CharManager.triggered.connect(self.open_charManager)
        
        self.action_Settings.triggered.connect( self.open_settings )
        
        self.action_Exit.triggered.connect(self.close)
        
            # BTNS AND ETC
        
                # btns for load
        self.BTN_LoadAPI.released.connect(self.loadOrders_API)
        self.BTN_LoadFile.released.connect(self.loadOrders_file)
        
                # btns for scan
        self.BTN_ScanStart.released.connect(self.scan_start)
        self.BTN_ScanStop.released.connect(self.scan_stop)
        
           # INIT CODE
        
        # init tables
        self.tableOrders_init(self.Table_OrdersSell)
        self.tableOrders_init(self.Table_OrdersBuy)
        
        # load settings and chars
        self.settings_load()
        self.chars_update()
        
    def closeEvent(self, QCloseEvent):
        
        if self.scanByRow:
            self.scan_stop()

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
    def open_APIManager(self):
        print('Open [API Manager]')
        
        self.Window_APIManager = APIManager.Window_APIManager()
        self.Window_APIManager.show()
        
    def open_charManager(self):
        print('Open [API Manager]')
        
        self.Window_CharManager = CharManager.Window_CharManager()
        self.Window_CharManager.show()
    
        self.Window_CharManager.closeWithFunction = self.chars_update
        
    def open_settings(self):

        self.Window_Settings = Settings.Window_Settings()
        self.Window_Settings.show()
        
        self.Window_Settings.closeWithFunction = self.settings_load
        
            # === BTNS ===
        
    def loadOrders_API(self):
        
            # Stop scaning if it doing
        if self.scanByRow:
            self.scan_stop()
            
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
            char = self.chars[char] 

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

    def loadOrders_file(self):
        
            # Stop scaning if it doing
        if self.scanByRow:
            self.scan_stop()
            
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
            char = self.chars[char]
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
        
    def scan_start(self):
        
        print('Scan starting...')        
        
        self.trayMessanger.setScaning(1)
        
        self.BTN_ScanStart.setEnabled(False)
        self.BTN_ScanStop.setEnabled(True)
        
        self.Table_OrdersSell.scanRow = 0
        self.Table_OrdersBuy.scanRow = 0

        self.scanByRow = True
        
        self.scanTimer.start(2000)
        
    def scan_stop(self):
        
        print('Scan stoping...')
        
        self.trayMessanger.setScaning(0)
        
        self.BTN_ScanStart.setEnabled(True)
        self.BTN_ScanStop.setEnabled(False)
        
        self.scanByRow = False
        
        self.scanTimer.stop()
        
            # === OTHER ===
        
    def orderScaner_checker(self):
        
            # if sell orders exists, then check it
        if len(self.Table_OrdersSell.orders):
            self.tableOrders_checker(self.Table_OrdersSell)
        
            # if buy orders exists, then check it
        if len(self.Table_OrdersBuy.orders):
            self.tableOrders_checker(self.Table_OrdersBuy)
        
            # check not loop scan
        if not self.loopScan:

                # if scaned all sell orders and buy orders
            if self.Table_OrdersSell.scanRow == len(self.Table_OrdersSell.orders) \
                and self.Table_OrdersBuy.scanRow == len(self.Table_OrdersBuy.orders):
                
                    # set flag to scan fro m1 position
                self.Table_OrdersSell.updated = 1
                self.Table_OrdersBuy.updated = 1
                
                    # stopScan
                self.scan_stop()
        
    def showMessage_fromOrders(self):

        self.trayMessanger.showMessage_fromOrders(self.ordersForAlarm)
        self.ordersForAlarm = []

    def orderLoader_checker(self):
        
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
            
                # update lines
            self.tableOrders_createLines(self.Table_OrdersSell)
            self.tableOrders_createLines(self.Table_OrdersBuy)
            
                # update items
            self.tableOrders_updateItems(self.Table_OrdersSell)
            self.tableOrders_updateItems(self.Table_OrdersBuy)

                # update chars orders id
            self.myOrders_update()        

    def chars_update(self):
        
            # debug
        print('Updating char list...')
        
            # Stop scaning if it doing
        if self.scanByRow:
            self.scan_stop()  
        
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
                            self.chars.append( [charID[j], charName[j], 
                                                bool(int(charShow[j])),
                                                keys[i],vc[i]] )
    
        self.chars_updateList()
        
                # Table
    def chars_updateList(self):
        
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
            
    def myOrders_update(self):
        
        self.myOrders = []
        
        for order in self.Table_OrdersSell.orders:
            self.myOrders.append(order.id)
            
        for order in self.Table_OrdersBuy.orders:
            self.myOrders.append(order.id)
                
    def tableOrders_init(self, table):
        
        """
        Init table vars / header / column count / set index info
        """
        
            # vars
        table.orders = []
        table.lines = []
        table.updated = 0
        table.scanRow = 0
        table.scaner = None
        table.columnsEnabled = []
        
        # ids for columns
        table.char = 0
        table.itemName = 1
        table.count = 2
        table.price = 3
        table.lastCheck = 4
        table.attension = 5
        table.alarm = 6
        table.scanEnabled = 7
        table.scanMode = 8
        table.region = 9
        table.solarSystem = 10
        table.station = 11
        
        # column index
        table.columnIndex = {0:-1,
                             1:-1,
                             2:-1,
                             3:-1,
                             4:-1,
                             5:-1,
                             6:-1,
                             7:-1,
                             8:-1,
                             9:-1,
                             10:-1,
                             11:-1}        
        
        # column width
        table.columnWidth = {0:100,
                             1:250,
                             2:50,
                             3:75,
                             4:73,
                             5:22,
                             6:22,
                             7:60,
                             8:100,
                             9:75,
                             10:100,
                             11:250}
        
        # colum headers
        table.columnHeaders = {0:'Char Name',
                               1:'Item',
                               2:'Count',
                               3:'Price(Sum)',
                               4:'Last check',
                               5:'',
                               6:'',
                               7:'Check',
                               8:'Range',
                               9:'Region',
                               10:'Solar system',
                               11:'Station'}
        

        
                    # load attension icons
        table.attensionIcon = [QIcon('images/good.PNG'),
                               QIcon('images/bad.PNG'),
                               QIcon('images/wait.PNG')]
        
            # load message icons
        table.alarmIcon = [QIcon('images/messageOff.PNG'),
                           QIcon('images/messageOn.PNG')]
        
        self.tableOrders_setColumns(table)
        
    def tableOrders_setColumns(self, table):
        
        '''
        set columns count and headers
        '''
        
        print('modify columns')
        
        # columns count
        table.setColumnCount(len(table.columnsEnabled))
        
        # var for headers
        headers = []
        
        # init table data
        # i is id of columbn data (itemName, char, price...)
        for data in table.columnsEnabled:
            
            index = table.columnsEnabled.index(data)
            table.columnIndex[data] = index
            table.setColumnWidth(index, table.columnWidth[data])
            
            headers.append(table.columnHeaders[data])
        
        # headers
        table.setHorizontalHeaderLabels(headers)
        
    def tableOrders_createLines(self, table):
        
        """
        create lines from table.orders
        """
        
        print('Creating lines...')
        
        orders = table.orders
        table.lines = []       
        
            # for all order
        for order in orders:
            
                # create line
            line = tableLine(table, order)
            table.lines.append(line)
        
    def tableOrders_updateItems(self, table):
    
        print('Table Orders update item...')
        
            # clear old data
        table.clearContents()
        
            # set flag updated and update rows count
        table.updated = 1
        
            # restruct lines
        self.tableOrders_createLines(table)
        
            # update row count
        table.setRowCount(len(table.lines))
        
            # if lines not empty
        if len(table.lines):
        
                # for each row
            for row in range(len(table.lines)):
            
                    # get line object for row
                line = table.lines[row]
                line.createData()
            
                    # for each data column
                for dataColumn in table.columnsEnabled:
                
                        # get column index in table
                    column = table.columnsEnabled.index(dataColumn)              
                
                        # if it's column with TableWidgetItem them read at to table
                    if dataColumn != table.scanEnabled and dataColumn != table.scanMode:
                        table.setItem(row, column, line.data[dataColumn])
                    
                        # if it's not TableWidgetItem, set to cell widget
                    else:
                        table.setCellWidget(row, column, line.data[dataColumn])
                
    def tableOrders_checker(self, table):

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
                    table.scaner = EVE_Orders.ordersScaner_Row(table.orders, table.scanRow, self.myOrders)
                    table.scaner.start()
                
                    # if orders wasn't update then modify row
                else:
                    self.tableOrders_updateRow(table)
                    
            # if scaner don't exist
        else:
            
                # create and start it
            table.scaner = EVE_Orders.ordersScaner_Row(table.orders, table.scanRow, self.myOrders)
            table.scaner.start()
                
    def tableOrders_updateRow(self, table):
        
            # get scaned row
        row = table.scaner.row
        line = table.lines[row]
        order = line.order
        
            # update order info
        line.update()
        
            # if order is not find when it has been scaned
        if order.exist == 0:
            
                # remove order from orders
                # update myOrders
            table.orders.remove(order)
            self.myOrders_update()          
            
                # update items (at script for items restruct lines)
                # row - 1 (because next row now is current)
            self.tableOrders_updateItems(table)
            row = row - 1
            
                # if alarm enable
            if self.alarmOn:
                
                    # sound message about fulfilled
                if self.alarmWithSound:
                    self.fulfilledWAV.play()
                    
                    # tray message
                self.trayMessanger.showMessage('Orders is fulfilled',
                                               order.itemName +
                                               ' [' + order.solarSystemName + ']')
        else:
                # if order havn't alarmed yet
            if not order.alarm and order.scan:
                if order.modifiable() and not order.top() and self.alarmOn:
                
                    # set alarm for order and send it to tray messanger
                    line.setAlarm(1)
                    self.ordersForAlarm.append(order)
        
            # go to next row
        table.scanRow = row + 1
        
            # check that row in orders range
        if table.scanRow < len(table.orders):

                # create new scaner and start it
            table.scaner = EVE_Orders.ordersScaner_Row(table.orders, table.scanRow, self.myOrders)
            table.scaner.start()

            # if out of range
        else:
                # if loop scan
            if self.loopScan:
                
                    # go to first element
                table.scanRow = 0
                
                    # and create new scaner
                table.scaner = EVE_Orders.ordersScaner_Row(table.orders, table.scanRow, self.myOrders)
                table.scaner.start()
        
    def settings_load(self):
        
            # debug
        print('Load settings')
        
            # get dir
        workDir = os.getcwd()
        workDir = workDir.replace('\\','/')
        
            # get files in dir
        files = os.listdir(workDir)
        
            # if config is not found
        if 'config.ini' not in files:
            self.settings_createINI()        
        
            # read config
        config = configparser.ConfigParser()
        config.read('config.ini')
        
            # read settings
        self.path = config['MAIN']['marketlogs']
        self.alarmOn = int(config['MAIN']['alarmEnable'])
        self.alarmTime = int(config['MAIN']['alarmTime'])
        self.loopScan = int(config['MAIN']['loopScan'])
        
            # check alarm timmer
        if self.alarmTime < 10000:
            self.alarmTime = 10000
        
            # set alarm timer new time
        self.trayMessangerTimer.start(self.alarmTime)
        
            # sound Alarm
        self.alarmWithSound = int( config['MAIN']['alarmWithSound'] )
        
            # alarm sounds settings for tray
        if self.alarmOn:
            self.trayMessanger.alarmWithSound = self.alarmWithSound
        else:
            self.trayMessanger.alarmWithSound = 0
        
            # Table settings
    
        # load enabled columns
        TableSettings = config['MAIN']['tableSettings']
        TableSettings = TableSettings.split(',')
        
        TableSettings_enabled = []
        
        # if settings for table sell has elements
        if TableSettings != ['']:
            for item in TableSettings:
                TableSettings_enabled.append(int(item))
                
        # set tebleSettings enable to tables
        self.Table_OrdersSell.columnsEnabled = TableSettings_enabled
        self.Table_OrdersBuy.columnsEnabled = TableSettings_enabled
                
        # modify columns and items
        self.tableOrders_setColumns(self.Table_OrdersSell)
        self.tableOrders_updateItems(self.Table_OrdersSell)
        
        # modify columns and items
        self.tableOrders_setColumns(self.Table_OrdersBuy)
        self.tableOrders_updateItems(self.Table_OrdersBuy)
        
    def settings_createINI(self):
        
            # create empty config
        open('config.ini','w').close()
        
            # read new file
        config = configparser.ConfigParser()
        config.read('config.ini')
        
            # clear it
        config.clear()
        
            # add MAIN default settings
        config.add_section('MAIN')
        config.set('MAIN','marketlogs','')
        config.set('MAIN','alarmenable','1')
        config.set('MAIN','alarmtime','30000')
        config.set('MAIN','alarmwithsound','1')
        config.set('MAIN','loopscan','1')
        config.set('MAIN','tablesettings','0,1,2,3,4,5,6,7,8,9,10,11')
        
            # add KEYS default settings
        config.add_section('KEYS')
        config.set('KEYS','name','')
        config.set('KEYS','key','')
        config.set('KEYS','vc','')
        
            # save config
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
        
if __name__ == '__main__':
    
    app = QtGui.QApplication(sys.argv)
    
    window = OrderScaner()

    app.setActiveWindow(window)
    app.setWindowIcon(QtGui.QIcon('images/iconScaning.GIF'))
    
    sys.exit(app.exec_())

    #start the application's exec loop, return the exit code to the OS
    #exit(app.exec_())