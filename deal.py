#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import time
import btcchina

access_key = ""
secret_key = ""

def get_current_price(bc,type="bid"):
  result = bc.get_market_depth()
  price = result["market_depth"][type][0]["price"]
  return price

def process_order(bc,amount=1.0,price="current",type="sell"):
  if type=="sell":
    if price=="current":
      price = get_current_price(bc,"bid")
    
    final = raw_input("你将以"+str(price)+"的价格出售"+str(amount)+"的比特币，确认请输入Y:")
    if(final.lower()=='y'):
      bc.sell(price,amount)
  elif type=="buy":
    if price=="current":
      price= get_current_price(bc,"ask")
    final = raw_input("你将以"+str(price)+"的价格买入"+str(amount)+"的比特币，确认请输入Y:")
    if(final.lower()=='y'):
      bc.buy(price,amount)
  else:
    pass

if __name__ == '__main__':
  bc = btcchina.BTCChina(access_key,secret_key)
  result = bc.get_account_info()
  title = result["profile"]["username"].title()
  message = ''
  while True:
    print '''Dear %s, Please input your directions:
             s: sell bitcoins
             b: buy bitcoins
             c: cancel order
             ss: sell all bitcoins at current price''' %(title)
    c = raw_input('请输入您要执行的交易:')
    try:
      if c.lower()=='s':
        cc = raw_input('请输入您要卖出的比特币数量，全部卖出请直接按ENTER:')
        price = raw_input('请您出价,当前价格请直接按ENTER:')
        if cc=="":
          res=bc.get_account_info()
          cc=res["balance"]["btc"]["amount"]
        else:
          cc=float(cc)
        if price=="":
          price="current"
        else:
          price=float(price)
        process_order(bc,cc,price,"sell");
      elif c.lower()=='b':
        cc = raw_input('请输入您要买入的比特币数量:')
        price = raw_input('请您出价,当前价格请直接按ENTER:')
        cc=float(cc)
        if price=="":
            price="current"
        else:
           price=float(price)
        process_order(bc,cc,price,"buy");
      elif c.lower()=='c':
        pass
      elif c.lower()=='ss':
        res=bc.get_account_info()
        cc=res["balance"]["btc"]["amount"]
        price="current"
        process_order(bc,cc,price,"sell");
      else:
        print "Can't find your command."  
    except ValueError:
      print "Please check your input."
