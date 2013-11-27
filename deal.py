#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import ConfigParser
import btcchina

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
  reload(sys)
  sys.setdefaultencoding(default_encoding)

try:
  cf = ConfigParser.ConfigParser()    
  cf.read("btc.conf")  
except:
  print "Read config file error.Please make sure that btc.conf file exists." 

info_access_key = cf.get("info", "access_key") 
info_secret_key = cf.get("info", "secret_key") 

deal_access_key = cf.get("deal", "access_key") 
deal_secret_key = cf.get("deal", "secret_key") 


def get_current_price(bc,type="bid"):
  result = bc.get_market_depth()
  price = result["market_depth"][type][0]["price"]
  return price

def process_order(bc,amount=1.0,price="current",type="sell"):
  if type=="sell":
    if price=="current":
      price = float(get_current_price(bc,"bid"))
    
    final = raw_input("你将以"+str(price)+"的价格出售"+str(amount)+"的比特币，共计"+str(price*amount)+"元确认请输入Y: ")
    if(final.lower()=='y'):
      res = bc.sell(str(price),str(amount))
      if res==True:
        print "交易已成功受理！"
      else:
        try:
          print "服务器返回：" + res["message"]
        except:
          print "未知错误，业务未受理!"
      print "正在返回主菜单..."
    else:
      print "交易已取消,正在返回主菜单..."
  elif type=="buy":
    if price=="current":
      price= float(get_current_price(bc,"ask"))
    final = raw_input("你将以"+str(price)+"的价格买入"+str(amount)+"的比特币，共计"+str(price*amount)+"元确认请输入Y: ")
    if(final.lower()=='y'):
      res = bc.buy(str(price),str(amount))
      if res==True:
        print "交易已成功受理！"
      else:
        try:
          print "服务器返回：" + res["message"]
        except:
          print "未知错误，业务未受理!"
      print "正在返回主菜单..."
    else:
      print "交易已取消,正在返回主菜单..."
  else:
    print "交易指令不存在，调用错误!正在返回主菜单..."

def cancel_order(bc,order_id):
  final = raw_input("你将取消挂单"+str(order_id)+",确认请输入Y: ")
  if(final.lower()=='y'):
    res = bc.cancel(order_id)
    if res==True:
        print "挂单已取消！"
    else:
        try:
          print "服务器返回：" + res["message"]
        except:
          print "未知错误，业务未受理!"
    print "正在返回主菜单..."
  else:
    print "操作已取消,正在返回主菜单..."

if __name__ == '__main__':
  bc = btcchina.BTCChina(info_access_key,info_secret_key)
  bc_deal = btcchina.BTCChina(deal_access_key,deal_secret_key)
  while True:
    result = bc.get_account_info()
    title = result["profile"]["username"].title()
    btc_amount = result["balance"]["btc"]["amount"]
    cny_amount = result["balance"]["cny"]["amount"]
    bid_price = get_current_price(bc,type="bid")
    ask_price = get_current_price(bc,type="ask")
    os.system('clear')
    print '''%s,您目前拥有 %s 个比特币以及 %s 元人民币.
              \r当前Bid Price %s, 当前Ask Price %s. 请输入您要执行的交易类型：
              \r\ts: 卖出比特币
              \r\tb: 买入比特比
              \r\tc: 取消挂单
              \r\tss: 以当前价卖出所有的比特币
              \r\tr: 刷新信息'''  %(title,btc_amount,cny_amount,bid_price,ask_price)
    c = raw_input('请输入您要执行的操作: ')
    try:
      if c.lower()=='s':
        cc = raw_input('请输入您要卖出的比特币数量，全部卖出请直接按ENTER: ')
        price = raw_input('请您出价,当前价格请直接按ENTER: ')
        if cc=="":
          res=bc.get_account_info()
          cc=float(res["balance"]["btc"]["amount"])
        else:
          cc=float(cc)
        if price=="":
          price="current"
        else:
          price=float(price)
        process_order(bc_deal,cc,price,"sell")
      elif c.lower()=='b':
        cc = raw_input('请输入您要买入的比特币数量: ')
        price = raw_input('请您出价,当前价格请直接按ENTER: ')
        cc=float(cc)
        if price=="":
            price="current"
        else:
           price=float(price)
        process_order(bc_deal,cc,price,"buy")
      elif c.lower()=='c':
        cc = raw_input('请输入您要取消的挂单id: ')
        cc = int(cc)
        cancel_order(bc_deal,cc)
      elif c.lower()=='ss':
        res=bc.get_account_info()
        cc=float(res["balance"]["btc"]["amount"])
        price="current"
        process_order(bc_deal,cc,price,"sell")
      elif c.lower()=='r':
        print "正在刷新信息..."
        continue
      else:
        print "交易指令不存在！正在返回主菜单..."  
    except ValueError:
      print "请检查您的输入是否正确。正在返回主菜单..."
    except Exception as e:
      print e

    time.sleep(1)