#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import datetime
from prettytable import PrettyTable
import btcchina

access_key = ""
secret_key = ""

def generate_info(bc):
  result = bc.get_account_info()
  message = result["profile"]["username"].title()+",you now have "+result["balance"]["btc"]["amount"] + " bitcons.\n"
  result = bc.get_transactions("buybtc",1)
  t = result["transaction"][0]
  price = -float(t["cny_amount"])/float(t["btc_amount"])
  message += "Your last bought "+t["btc_amount"] + " bitcoins with price CNY:" + str(price)+" at "+ datetime.datetime.fromtimestamp(t["date"]).strftime('%Y-%m-%d %H:%M:%S')
  message += "\nInfo updated at "+time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()));
  return message

def refresh_price(bc):
  print "Fetching the newest market depth...",
  sys.stdout.flush()
  result = bc.get_market_depth()
  x = PrettyTable(["Bid", "Bid Amount", "Ask", "Ask Amount"])
  x.align = "l"
  x.padding_width = 2
  for b,a in zip(result["market_depth"]["bid"],result["market_depth"]["ask"]):
    x.add_row([b["price"],b["amount"],a["price"],a["amount"]])
  print '\r'+x.get_string()
  print "Market depth updated at " + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

def refresh_undeal_orders(bc):
  print "Fetching your undeal orders...",
  sys.stdout.flush()
  result = bc.get_orders(None,True)
  if len(result["order"]):
    x = PrettyTable(["Order Type", "Price", "Amount", "Origin Amount","Order ID"])
    x.align = "l"
    x.padding_width = 2
    for o in result["order"]:
      x.add_row([b["type"],b["price"],a["amount"],a["amount_original"],b["id"]])
    print '\r'+x.get_string(sortby="Order Type")
    print "Undeal Order updated at " + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
  else:
    time.sleep(1)
    print "\rYou have no undeal orders till " + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

if __name__ == '__main__':
  bc = btcchina.BTCChina(access_key,secret_key)
  info = generate_info(bc)
  i = 0
  while 1:    
    os.system('clear')
    print info
    refresh_price(bc)
    refresh_undeal_orders(bc)
    time.sleep(10)
    i+=1
    if i==90:
      info = generate_info(bc)
      i=0
