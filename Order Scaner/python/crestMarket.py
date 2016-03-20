# -*- coding: utf-8 -*-
"""
Created on Thu Mar 10 17:12:17 2016

@author: Paniker
"""

from urllib import request
import json
import time

def _Order_Update(order):
    
        # not find yet
    order.exist = 0
    
        # load all orders for itemID from crest
    data = _Item_Load( order.itemID, order.bid )
    
        # prices
    prices = []
    
        #
    for i in range(int(data["totalCount_str"])):
        
            # read orderID and stationID
        read_OrderID = int(data["items"][i]["id"])
        read_StationID = int(data["items"][i]["location"]["id"])
        
            # read price
        read_Price = float(data["items"][i]["price"])
        
            # read remaining/entered
        read_Remaining = int(data["items"][i]["volume"])
        read_Entered = int(data["items"][i]["volumeEntered"])
        
            # read date
        read_Date = data["items"][i]["issued"]
        read_Date = time.strptime(read_Date, "%Y-%m-%dT%H:%M:%S")
        read_Date = time.mktime(read_Date)
        
            # if order is mine
        if read_OrderID == order.id:
            
                # update count (crest may lags and count may became bigger)
            if read_Remaining < order.remaining:
                
                    # order updated
                order.updated = 1
                
                    # updated remaining
                order.remaining = read_Remaining
            
                # if order.date is newer then date order we have
            if read_Date > order.date:

                    # order updated
                order.updated = 1

                    # reset alarm
                order.alarm = 0
                order.attension = 0
                
                # update price, date, remaining/entered
                order.price = read_Price
                order.date = read_Date
            
                order.remaining = read_Remaining
                order.entered = read_Entered
        
            # if order is not mine
        else:
                # if scan only station price
            if order.scanMode:
                if read_StationID == order.stationID:
                    prices.append(read_Price)
            
                # if scan region
            else:
                prices.append(read_Price)
    
        # if find other prices
    if len(prices):
        
            # if buy order - set max buy price
            # if sell order - set min sell price
        if order.bid:
            order.marketPrice =  max(prices)
        else:
            order.marketPrice =  min(prices)

def _Item_GetPrice(itemID,bid,stationID = None):

    data = _Item_Load(itemID,bid)

    prices = []

    i = 0
    
    while i<int(data["totalCount_str"]):
        
        if stationID == None:
            prices.append(float(data["items"][i]["price"]))
        else:
            if int(data["items"][i]["location"]["id"]) == stationID:
                prices.append(float(data["items"][i]["price"]))
        i=i+1

    if bid:
        return max(prices)
    else:
        return min(prices)
        
def _Item_Load(itemID,bid):

    if bid:
        orderType = 'buy'
    else:
        orderType = 'sell'
    
    url = "https://public-crest.eveonline.com/market/10000002/orders/"+orderType+"/?type=https://public-crest.eveonline.com/types/"+str(itemID)+"/"
    
    data_file = request.urlopen(url).read().decode('utf-8')
    #request.urlretrieve(url, "D:/result.json")
    
    #with open('D:/result.json') as data_file:
    data = json.loads(data_file)
    
    return data
    
#a = _Item_GetPrice(11577,0,60003760)
#print(a)
    
"""
if __name__ == '__main__':
    
    import EVE_Orders

    order = EVE_Orders.newOrder()
    order.id = 4472018785
    order.itemID = 11577
    order.stationID = 60003760

    _Order_Update(order)

    print(order.remaining, order.marketPrice)
"""