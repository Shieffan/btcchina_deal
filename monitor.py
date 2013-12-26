#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import datetime
from select import select
import ConfigParser
from prettytable import PrettyTable
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

access_key = cf.get("info", "access_key")
secret_key = cf.get("info", "secret_key")

def generate_info(bc):
    result = bc.get_account_info()
    title = result["profile"]["username"].title()
    btc_amount = result["balance"]["btc"]["amount"] or 0
    cny_amount = result["balance"]["cny"]["amount"] or 0
    f_btc_amount = result["frozen"]["btc"]["amount"] or 0
    f_cny_amount = result["frozen"]["cny"]["amount"] or 0
    message = "%s, you currently have %g bitcoins and %g RMB, frozen %g bitcoins,%g RMB.\n" % (title,float(btc_amount),float(cny_amount),float(f_btc_amount),float(f_cny_amount))
    result = bc.get_transactions("all",1)
    t = result["transaction"][0]
    try:
        price = abs(float(t["cny_amount"])/float(t["btc_amount"]))
        price = "with price CNY:" + str(price)
    except:
        price = ""
    message += "Last transaction: "+t["type"].upper()+ " " + str(abs(float(t["btc_amount"]))) + " bitcoins, "+str(abs(float(t["cny_amount"]))) + " RMB " + price+" at "+ datetime.datetime.fromtimestamp(t["date"]).strftime('%Y-%m-%d %H:%M:%S')
    message += "\nInfo updated at "+time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()));
    return message

def refresh_price(bc,count):
    sys.stdout.write("Fetching the newest market depth...")
    sys.stdout.flush()
    result = bc.get_market_depth(count)
    x = PrettyTable(["No.","Bid", "Bid Amount", "Ask", "Ask Amount"])
    x.align = "l"
    x.align["No."] = "c"
    x.padding_width = 2
    bid_money_total=0.0
    bid_amount_total=0.0
    ask_money_total=0.0
    ask_amount_total=0.0
    i = 0
    for b,a in zip(result["market_depth"]["bid"],result["market_depth"]["ask"]):
        bid_amount_total+=b["amount"]
        bid_money_total+=b["price"]*b["amount"]
        ask_amount_total+=a["amount"]
        ask_money_total+=a["price"]*a["amount"]
        i+=1
        x.add_row([i,b["price"],b["amount"],a["price"],a["amount"]])
    x.add_row(["Ave.","{:.2f}".format(bid_money_total/bid_amount_total),"฿"+str(bid_amount_total),"{:.2f}".format(ask_money_total/ask_amount_total),"฿"+str(ask_amount_total)])
    print '\r'+x.get_string()
    print "Market depth updated at " + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))

def refresh_undeal_orders(bc):
    sys.stdout.write("Fetching your undeal orders...")
    sys.stdout.flush()
    result = bc.get_orders(None,True)
    if len(result["order"]):
        x = PrettyTable(["Order Type", "Price", "Amount", "Origin Amount","Order ID"])
        x.align = "l"
        x.padding_width = 2
        for o in result["order"]:
            x.add_row([o["type"],o["price"],"{:g}".format(float(o["amount"])),"{:g}".format(float(o["amount_original"])),o["id"]])
        print '\r'+x.get_string(sortby="Order Type")
        print("Undeal Order updated at " + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))
    else:
        print("\rYou have no undeal orders till " + time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time())))

if __name__ == '__main__':
    bc = btcchina.BTCChina(access_key,secret_key)
    info = generate_info(bc)
    i = 0
    count = 10
    while 1:
        try:
            os.system('clear')
            print info
            refresh_price(bc,count)
            refresh_undeal_orders(bc)
            timeout = 15
            print "Change market depth item numbers:",
            sys.stdout.flush()
            num, _, _ = select([sys.stdin], [], [], timeout)
            if num:
                num = sys.stdin.readline()
                num = num.strip()
                if num:
                    try:
                        count = int(num)
                    except:
                        pass
            else:
                print "Refreshing info..."
            i+=1
            if i>=2:
                info = generate_info(bc)
                i=0
        except Exception as e:
            print "\n!!!Error: %s ..\nRetring..." % e
            time.sleep(2)
