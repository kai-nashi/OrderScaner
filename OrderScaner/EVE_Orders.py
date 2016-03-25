# -*- coding: utf-8 -*-
"""
Created on Thu Mar 10 14:00:50 2016

@author: Paniker
"""

import os
import urllib
from urllib import request
import xml.etree.ElementTree as ET
import time

import CrestMarket

import threading

#==============================================================================
#  ORDER
#==============================================================================

class newOrder:
    
    def __init__(self):
        
        super(newOrder, self).__init__()        
        
            # flag for update, if 0 - order wasn't find when update
            # that mean that order canceled or fullfid
        self.exist = 1
        self.updated = 0
        
            # id and bid
        self.id = 0
        self.bid = 0
        
            # itemID and Name
        self.itemID = 20
        self.itemName = 'ERROR'
        
            # charId and Name
        self.charID = 0
        self.charName = 'ERROR'       
        
            # remaining/entered
        self.remaining = -1
        self.entered = -1
        
            # order range
            # 32767 - solarSystem
        self.range = 32767
        
            # price per utin and alarm
        self.price = -1
        self.marketPrice = 0       
        
        self.alarm = 0
        self.attension = 0
        
            # stationID and Name
            # 60003760 - Jita IV - Moon 4 - Caldari Navy Assembly Plant
        self.stationID = 60003760
        self.stationName = 'ERROR'
        
            # solarSystemID and Name
            # 30000142 - Jita
        self.solarSystemID = 30000142
        self.solarSystemName = 'ERROR'
        
            # regionID and Name
            # 10000002 - The Forge
        self.regionID = 10000002
        self.regionName = 'ERROR'

            # orderDate and last check date
        self.date = 0
        self.dateLoad = 0
        self.checkDate = 0
        
            # escrow
        self.escrow = 0
        
            # scan settings
        self.scan = 1
        self.scanMode = 0
            # scanMode 0 - station
            # scanMode 1 - solarSystem (NOT WORK YET)
            # scanMode 2 - region (ALWAYS IF SCANMODE != 0)
        
    def modifiable(self):
        
        if self.date + 300 <= self.checkDate:
            return 1
        else:
            return 0
            
    def top(self):
        
            # if buy order
        if self.bid:
            
                # if data was checked
            if self.marketPrice:
                
                if self.marketPrice >= self.price:
                    return 0
                else:
                    return 1
                    
            else:
                return 1
        
            #if sell order
        else:
            
                # if data was checked
            if self.marketPrice:
                if self.marketPrice <= self.price:
                    return 0
                else:
                    return 1
                
                # if data was not checked
            else:
                return 1
        
    def updateLocation(self):

        tree = ET.parse('data/stations.xml')
        root = tree.getroot()

        for child in root:
            
            stationID = int( child.get('stationID', default = '0') )
            
            if stationID == self.stationID:
                
                self.stationName = child.get('name', default = '[ERROR NAME]')
                
                self.solarSystemID = int( child.get('solarSystemID', default = '0') )
                self.solarSystemName = child.get('solarSystemName', default = '0')
                
                self.regionID = int( child.get('regionID', default = '0') )
                self.regionName = child.get('regionName', default = '0')
                
                break

    def updateItemName(self):
        
        tree = ET.parse('data/items.xml')
        root = tree.getroot()

        for child in root:
            
            itemID = int( child.get('id', default = '0') )
            
            if itemID == self.itemID:
                
                self.itemName = child.get('name', default = '[ERROR NAME]')
                
                break
#==============================================================================
# ORDER LOADER /// FROM FILE ///
#==============================================================================

class ordersLoader_FromFile(threading.Thread):
    
    def __init__(self, path = '/', charID = None, orderType = None):
        
        super(ordersLoader_FromFile, self).__init__()
        
        """
        Loads orders from API with bid = orderType
        """
        
        self.orders = []
        
        self.path = path
        self.charID = charID
        self.orderType = orderType
        

        
    def run(self):
            
        if self.charID != None:

            if self.orderType != None:
                self.orders = orders_LoadFromFile(self.path, self.charID, self.orderType)
            else:
                self.orders = orders_LoadFromFile(self.path, self.charID)

#==============================================================================
# ORDER LOADER /// FROM API ///
#==============================================================================

class ordersLoader_FromAPI(threading.Thread):
    
    def __init__(self,  key, vc, charID, charName = '', orderType = None):
        
        super(ordersLoader_FromAPI, self).__init__()
        
        """
        Loads orders from API with bid = orderType
        """
        
        self.orders = []
    
        self.key = key
        self.vc = vc
        self.charID = charID
        self.orderType = orderType
        self.charName = charName
        
    def run(self):
            
            # load orders
        if self.orderType != None:
            self.orders = orders_LoadFromAPI(self.key, self.vc, self.charID, self.orderType)
        else:
            self.orders = orders_LoadFromAPI(self.key, self.vc, self.charID)

            # and update orders charName
        for order in self.orders:
            order.charName = self.charName

#==============================================================================
# ORDER SCANER PER ROW
#==============================================================================

class ordersScaner_Row(threading.Thread):
    
    def __init__(self, orders=[], row=0, myOrders = None):
        
        super(ordersScaner_Row, self).__init__()
        
            # VARS
        self.myOrders = myOrders
        self.orders = orders
        self.row = row
        
    def run(self):
        
        if self.row < len(self.orders):
            order = self.orders[self.row]
            
            if order.scan:
                self.orders_UpdateCheckDate(order)
                CrestMarket.order_update(order, self.myOrders)
        
    def orders_UpdateCheckDate(self, order):
            
        url = "https://api.eveonline.com/server/ServerStatus.xml.aspx"

        file = request.urlopen(url)
        tree = ET.parse(file)
        
        date = tree.find('./currentTime')
        date = time.strptime(date.text, "%Y-%m-%d %H:%M:%S")
        date = time.mktime(date)
        
        order.checkDate = date
        
#==============================================================================
# FUNCTION BY MODUL
#==============================================================================
   
def orders_LoadFromFile(path, charID, bid = None):
    
        # get list of file
    files = os.listdir(path)
    
        # search files 'My orders...'
    filesOrder = []
    
    for file in files:
        if file.startswith('My Orders'):
            filesOrder.append(file)
            
        # get date of them
    filesOrder_Date = []
    
    for file in filesOrder:
        filesOrder_Date.append(os.path.getmtime(path+file))
        
        # find oldest and open it
    needFile_Index = filesOrder_Date.index(max(filesOrder_Date))
    file = open(path+filesOrder[needFile_Index], 'r')
    
        # create orders list from this
    orders = []      
    
    for line in file:
        
        if not line.startswith('orderID'):

                # do str readable
            orderString = line.split(',')

            #orderOld = []
                
                # if read order of char
            if charID == orderString[2]:
                
                    # create new orders
                order = newOrder()
                
                    # id
                order.id = int(orderString[0])
                
                    # bid
                if orderString[9] == 'True':
                    order.bid = 1
                else:
                    order.bid = 0 
        
                    # itemId and itemName
                order.itemID = int(orderString[1])
                order.itemName = 'ERROR'
        
                    # charID and charName
                order.charID = int(orderString[2])
                order.charName = orderString[3]     
        
                    # remaining/entered
                order.entered = int(orderString[11])
                order.remaining = int(float(orderString[12]))
        
                    # price and alarm (shoed tray message or no)
                order.price = float(orderString[10])
                order.alarm = 0
            
                    # order range (32767  = solarSystem)
                order.range = 32767
                
                    # stationID and Name
                order.stationID = int(orderString[6])
                order.stationName = orderString[7]
        
                    # solarSystemID and Name
                order.solarSystemID = int(orderString[19])
                order.solarSystemName = orderString[20]
                
                    # regionID and Name
                order.regionID = int(orderString[4])
                order.regionName = orderString[5]

                    # get date of order
                    # read string -> convert to year = x; month = x; ... ;
                    # and convert it to seconds
                date = orderString[13]                                          
                date = time.strptime(date, "%Y-%m-%d %H:%M:%S.000")
                date = time.mktime(date)
                
                order.date = date
                order.dateLoad = date

                    # last check (0 = never)
                order.checkDate = 0
        
                    # escrow for buy orders
                order.escrow = 0
                
                    # update itemName
                order.updateItemName()
                
                    # add order to orders
                if bid != None:                                                
                    if bid == order.bid:                                      
                        orders.append(order)                                 
                else:                                                           
                    orders.append(order) 

    orders = orders_UpdateItemName(orders)
    
    print(orders)
    return orders
    
def orders_LoadFromAPI(key, vc, charID, orderType = None):
    
    """
    orderType set that orders type (0/1) you want to get
    
    None: all orders
    0: buy orders
    1: sell orders
    """
    
        # make url
    url = "https://api.eveonline.com/char/MarketOrders.xml.aspx?keyID="+key+"&vCode="+vc+"&characterID="+charID

        # open url and parse it from rool
    file = request.urlopen(url)
    
    tree = ET.parse(file)
    root = tree.getroot()

        # make clear array for orders
    orders = [];

        # for each orders
    for child in root.iterfind('./result/rowset/row'):

            # read data
        orderID =       int( child.get('orderID', default = '-1') )
        charID =        int( child.get('charID', default = '-1') )
        itemID =        int( child.get('typeID', default = '-1') )
        volRemaining =  int( child.get('volRemaining', default = '-1') )
        volEntered =    int( child.get('volEntered', default = '-1') )
        bid =           int( child.get('bid', default = '-1') )
        stationID =     int( child.get('stationID', default = '-1') )
        ordersState =   int( child.get('orderState', default = '-1') )
        orderRange =    int( child.get('range', default = '-1') )
        
        escrow =        float( child.get('escrow', default = '-1') )
        price =         float( child.get('price', default = '-1') )

            # get date of order
            # read string -> convert to year = x; month = x; ... ;
            # and convert it to seconds
        date = child.get('issued', default = '-1');
        date = time.strptime(date, "%Y-%m-%d %H:%M:%S")
        date = time.mktime(date)
        
            # date of last check price (0 = never)
        checkDate = 0

            # create new orders
        order = newOrder()
                
            # id and bid
        order.id = orderID
        order.bid = bid
        
            # itemId and itemName
        order.itemID = itemID
        order.itemName = 'ERROR'
        
            # charID and charName
        order.charID = charID
        order.charName = 'ERROR'   
        
            # x/x
        order.remaining = volRemaining
        order.entered = volEntered
        
            # price and alarm (shoed tray message or no)
        order.price = price
        order.alarm = 0
            
            # order range (32767  = solarSystem)
        order.range = orderRange
                
                # stationID and stationName
        order.stationID = stationID
        order.stationName = 'ERROR'
        
            # solarSystemID and Name
        order.solarSystemID = -1
        order.solarSystemName = 'ERROR'
        
            # regionID and Name
        order.regionID = -1
        order.regionName = 'ERROR'

            # get date of order
            # read string -> convert to year = x; month = x; ... ;
            # and convert it to seconds
        order.date = date
        order.dateLoad = date
                
                # last check (0 = never)
        order.checkDate = checkDate
        
            # escrow for buy orders
        order.escrow = escrow

            # if order didn't end
        if ordersState == 0:
            
                # if order type was selected
            if orderType != None:
                    
                    # if needed order type
                    #   add it
                if orderType == bid:    
                    orders.append(order)
                    
                # if order type wasn't select
            else:
                orders.append(order)

        # update location and item name
    orders = orders_UpdateLocation(orders)
    orders = orders_UpdateItemName(orders)

    print(orders)
    return orders
    
def orders_UpdateLocation(orders):
    
        # debug massage
    print('Update location of orders...')
    
        # open stations file
    tree = ET.parse('data/stations.xml')
    root = tree.getroot()

        # for each order
    for order in orders:
        
            # look from 1 position at xml
        for child in root:
            
                # read stationID from current line at xml
            stationID = int( child.get('stationID', default = '0') )
            
                # if it station where order
            if stationID == order.stationID:
                
                    # update stionName
                order.stationName = child.get('stationName', default = '[ERROR NAME]')
                
                    # update solarSystemID and Name
                order.solarSystemID = int( child.get('solarSystemID', default = '0') )
                order.solarSystemName = child.get('solarSystemName', default = '0')
                
                    # update regionID and Name
                order.regionID = int( child.get('regionID', default = '0') )
                order.regionName = child.get('regionName', default = '0')
                
                break
    
        # return modified list
    return orders
    
def orders_UpdateItemName(orders):
    
        # debug massage
    print('Update itemNames in orders...')
    
        # open stations file
    tree = ET.parse('data/items.xml')
    root = tree.getroot()

        # for each order
    for order in orders:
        
            # look from 1 position at xml
        for child in root:
            
                # read stationID from current line at xml
            itemID = int( child.get('id', default = '0') )
            
                # if it station where order
            if itemID == order.itemID:
                
                    # update stionName
                order.itemName = child.get('name', default = '[ERROR NAME]')
                
                break
    
        # return modified list
    return orders