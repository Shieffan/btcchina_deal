#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import time
import requests
import ConfigParser
import math
import math
import btcchina
from colorama import init,Fore,Style
from select import select
init(autoreset=True)


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


def get_current_price(type="bid"):
    r = requests.get('https://data.btcchina.com/data/orderbook',timeout=5) 
    result = r.json()
    if type=="bid" or type=='ask':
        type+='s'
        orders = result[type]
        if type=="asks":
            orders=orders[::-1]
        count = 0.0
        money = 0.0
        for i in orders:
            count+=i[1]
            money+=i[1]*i[0]
            price = money/count
            if count>=10:
                break
        return price
    elif type=='both':
        bid = get_current_price('bid')
        ask = get_current_price('ask')
        return [bid,ask]
    else:
        return None

def process_order(bc,amount=1.0,price="current",type="sell",confirmed="n"):
    if type=="sell":
        if price=="current":
            price = float(get_current_price("bid"))
        if confirmed=="y":
            final = "y"
        else:
            final = raw_input(Fore.YELLOW+"\r你将以"+str(price)+"的价格出售"+str(amount)+"的比特币，共计"+str(price*amount)+"元确认请输入Y: ")
        if final.lower()=='y':
            res = bc.sell(str(price),str(amount-0.00001))
            if res==True:
                print Fore.GREEN+"\r交易已成功受理！"
            else:
                try:
                    print Fore.RED+"\r操作未完成，服务器返回：" + res["message"]
                except:
                    print Fore.RED+"\r未知错误，业务未受理!"
            print "正在返回主菜单..."
        else:
            print "交易已取消,正在返回主菜单..."
    elif type=="buy":
        if price=="current":
            price= float(get_current_price("ask"))
        final = raw_input(Fore.YELLOW+"\r你将以"+str(price)+"的价格买入"+str(amount)+"的比特币，共计"+str(price*amount)+"元确认请输入Y: ")
        if final.lower()=='y':
            res = bc.buy(str(price),str(amount))
            if res==True:
                print Fore.GREEN+"\r交易已成功受理！"
            else:
                try:
                    print Fore.RED+"\r操作未完成，服务器返回：" + res["message"]
                except:
                    print Fore.RED+"\r未知错误，业务未受理!"
            print "正在返回主菜单..."
        else:
            print "交易已取消,正在返回主菜单..."
    else:
        print "交易指令不存在，调用错误!正在返回主菜单..."

def cancel_order(bc,order_id):
    final = raw_input(Fore.RED+"\r你将取消挂单"+str(order_id)+",确认请输入Y: ")
    if final.lower()=='y':
        res = bc.cancel(order_id)
        if res==True:
            print Fore.GREEN+"\r挂单已取消！"
        else:
            try:
                print Fore.RED+"\r操作未完成，服务器返回：" + res["message"]
            except:
                print Fore.RED+"\r未知错误，业务未受理!"
        print "正在返回主菜单..."
    else:
        print "操作已取消,正在返回主菜单..."

def cancel_orders(bc,order_ids):
    final =raw_input(Fore.RED+"\r你将取消所有挂单,挂单id:"+str(order_ids)+"确认请输入Y: ")
    if final.lower()=='y':
        for id in order_ids:
            res = bc.cancel(id)
            if res==True:
                print Fore.GREEN+"\r挂单"+str(id)+"已取消！"
            else:
                try:
                    print Fore.RED+"\r操作未完成，服务器返回：" + res["message"]
                except:
                    print Fore.RED+"\r未知错误，业务未受理!"
        print "正在返回主菜单..."
    else:
        print "操作已取消，正在返回主菜单..."


if __name__ == '__main__':
    bc = btcchina.BTCChina(info_access_key,info_secret_key)
    bc_deal = btcchina.BTCChina(deal_access_key,deal_secret_key)
    while True:
        try:
            result = bc.get_account_info()
            title = result["profile"]["username"].title()
            btc_amount = result["balance"]["btc"]["amount"] or 0
            cny_amount = result["balance"]["cny"]["amount"] or 0
            f_btc_amount = result["frozen"]["btc"]["amount"] or 0
            f_cny_amount = result["frozen"]["cny"]["amount"] or 0
            bid_price,ask_price = get_current_price("both")
            os.system('clear')
            print '''%s%s,您目前可用%g个比特币以及%g元人民币,冻结%g比特币,%g元人民币.
                                \r当前Bid Price %g,当前Ask Price %g.请输入您要执行的交易类型:
                                \r\tb: 买入比特比(或直接Enter)
                                \r\ts: 卖出比特币
                                \r\tc: 取消挂单
                                \r\tss: 以当前价卖出所有的比特币(sss不确认直接卖出)
                                \r\tcc: 取消所有挂单
                                \r\tr: 刷新信息'''    %(Fore.RESET,title,float(btc_amount),float(cny_amount),float(f_btc_amount),float(f_cny_amount),float(bid_price),float(ask_price))

            c = raw_input('\r请输入您要执行的操作: ')
            c = c.strip()
            
            try:
                if c.lower()=='s':
                    cc = raw_input('\r请输入您要卖出的比特币数量，全部卖出请直接按ENTER: ')
                    price = raw_input('\r请您出价,当前价格请直接按ENTER: ')
                    if cc=="":
                        res=bc.get_account_info()
                        fee=float(res['profile']['trade_fee'])/100
                        #cc=float(res["balance"]["btc"]["amount"])*(1-fee)
                        cc=float(res["balance"]["btc"]["amount"])
                        cc = math.floor(cc*1000)/1000
                    else:
                        cc=float(cc)
                    if price=="":
                        price="current"
                    else:
                        price=float(price)
                    process_order(bc_deal,cc,price,"sell")
                elif c.lower()=='b' or c.lower()=='':
                    cc = raw_input('\r请输入您要买入的比特币数量: ')
                    price = raw_input('\r请您出价,当前价格请直接按ENTER: ')
                    cc=float(cc)
                    if price=="":
                            price="current"
                    else:
                         price=float(price)
                    process_order(bc_deal,cc,price,"buy")
                elif c.lower()=='c':
                    cc = raw_input('\r请输入您要取消的挂单id: ')
                    cc = int(cc)
                    cancel_order(bc_deal,cc)
                elif c.lower()=='ss' or c.lower()=='sss':
                    res=bc.get_account_info()
                    fee=float(res['profile']['trade_fee'])/100
                    #cc=float(res["balance"]["btc"]["amount"])*(1-fee)
                    cc=float(res["balance"]["btc"]["amount"])
                    cc = math.floor(cc*1000)/1000
                    price="current"
                    if c.lower()=='ss':
                        process_order(bc_deal,cc,price,"sell")
                    else:
                        process_order(bc_deal,cc,price,"sell","y")
                elif c.lower()=='cc':
                    print "\rFetch your undeal orders..."
                    result = bc.get_orders(None,True)
                    undeal_ids=[o["id"] for o in result["order"]]
                    if len(undeal_ids)>0:
                        cancel_orders(bc_deal,undeal_ids) 
                elif c.lower()=='r':
                    print Style.BRIGHT + Fore.YELLOW+"\r正在刷新信息..."+ Style.RESET_ALL
                    continue
                else:
                    print "\r交易指令不存在！正在返回主菜单..."
                    time.sleep(1)
            except ValueError:
                print "\r请检查您的输入是否正确。正在返回主菜单..."
                time.sleep(1)
            except Exception as e:
                print e

        except Exception as e:
            print "\n!!!Error: %s ..\nRetring..." % e
            time.sleep(1)
