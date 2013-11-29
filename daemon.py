#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging 
from time import sleep
from daemonize import Daemonize
import ConfigParser
import btcchina

STOP_RATIO = 0.93
TOP_RATIO = 1.05
FALLDOWN = 100

pid = os.path.join(os.getcwd(),"tmp/daemon.pid") 
logger = logging.getLogger(__name__) 
logger.setLevel(logging.DEBUG) 
logger.propagate = False
fh = logging.FileHandler(os.path.join(os.getcwd(),"tmp/daemon.log"), "a")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s;%(levelname)s:%(message)s","%Y-%m-%d %H:%M:%S")
fh.setFormatter(formatter)
logger.addHandler(fh) 
keep_fds = [fh.stream.fileno()]

try:
    cf = ConfigParser.ConfigParser()
    cf.read("btc.conf")  
    info_access_key = cf.get("info", "access_key")
    info_secret_key = cf.get("info", "secret_key")
    deal_access_key = cf.get("deal", "access_key")
    deal_secret_key = cf.get("deal", "secret_key")
    logger.info("Read config successfully.")
except:
    logger.error("Parse config file error.Please make sure that btc.conf file exists.")



def main():
    global STOP_RATIO
    global FALLDOWN
    bc = btcchina.BTCChina(info_access_key,info_secret_key)
    bc_deal = btcchina.BTCChina(deal_access_key,deal_secret_key)
    logger.info("Daemon Started..")
    max_price = 0
    min_price = 0
    t_date = 0
    is_max = is_min = False
    prev_price = 0
    while True:
        logger.info("Refresh info..")
        try:
            result = bc.get_account_info()
            if float(result["balance"]["btc"]["amount"]) < 0.001:
                logger.info("You have no btccoins now...Let me sleep one minute :)")
                sleep(60)
            else:
                amount = float(result["balance"]["btc"]["amount"])
                #GET THE LAST BUYBTC TRANSACTION
                result = bc.get_transactions("buybtc",1)
                t = result["transaction"][0]
                last_price = abs(float(t["cny_amount"])/float(t["btc_amount"]))
                
                #CHECK IF CURRENT PRICE IS TOO LOWER THAN LAST TRANSACTION PRICE
                result = bc.get_market_depth()
                cur_price = float(result["market_depth"]['bid'][0]["price"])
                if t_date==int(t["date"]):
                    if cur_price > max_price:
                        is_max = True
                        max_price = cur_price
                    else:
                        is_max = False
                    if cur_price < min_price:
                        is_min = True
                        min_price = cur_price
                    else:
                        is_min =False
                else:
                    t_date=int(t["date"])
                    is_max = is_min = True
                    max_price = min_price = cur_price

                STOP_RATIO = float(STOP_RATIO)
                if STOP_RATIO > 1.0:
                    STOP_RATIO = 1.0
                ratio = cur_price/last_price

                if is_max==True:
                    logger.info("\n\r\033[1m\033[36m##Current, we have the highest price %g since your last buy transaction.\x1b[0m" % (max_price))
                
                if is_min==True:
                    logger.info("\n\r\033[1m\033[31m##Current, we have the lowest price %g since your last buy transaction.\x1b[0m" % (min_price))
                
                
                if ratio < STOP_RATIO:
                    #SELL ALL
                    logger.info("\n\r\033[1m$$_Ratio:\x1b[32m %g\x1b[0m; Current bid price %g; Your last buybtc price %g; Stop Ratio: %g;\n\r\033[1m\x1b[31mSelling all %g bitcons.\x1b[0m" % (ratio,cur_price,last_price,STOP_RATIO,amount))
                    res = bc_deal.sell(str(cur_price-0.1),str(amount-0.00001))
                    if res==True:
                        logger.info("$~_Commit order successfully！")
                        prev_price = 0
                        continue
                    else:
                        try:
                            logger.warning("$!_Failed, server says：" + res["message"])
                        except:
                            logger.error("$!_Failed, unknow error!")
                else:   
                    if ratio >= 1:
                        logger.info("\n\r\033[1m$#_Ratio:\x1b[32m %g\x1b[0m; Current bid price %g; Your last buybtc price %g; Sell Ratio: %g;\n\r\033[1m\x1b[33mDo nothing with total %g bitcoins.\x1b[0m" % (ratio,cur_price,last_price,STOP_RATIO,amount))
                    else:
                        logger.info("\n\r\033[1m$#_Ratio:\x1b[31m %g\x1b[0m; Current bid price %g; Your last buybtc price %g; Sell Ratio: %g;\n\r\033[1m\x1b[33mDo nothing with total %g bitcoins.\x1b[0m" % (ratio,cur_price,last_price,STOP_RATIO,amount))
                    if ratio >= TOP_RATIO:
                        logger.info("\n\r\033[1m\033[34m##Current, we have reach the high price-earnings ratio %.2f%%.\x1b[0m\n\rDon't you consider sell them all out ? Greed is the root of all evil. $_$" % ((TOP_RATIO-1)*100))
                    sleep(30)

                if prev_price - cur_price > FALLDOWN:
                    logger.info("\n\r\033[1m\x1b[32m!!We have to sell all your %g bitcoins because its price has fallen down %g RMB in the past 30 seconds.\x1b[0m" % (amount,prev_price - cur_price))
                    res = bc_deal.sell(str(cur_price-0.1),str(amount-0.00001))
                    if res==True:
                        logger.info("$~_Commit order successfully！")
                        prev_price = 0
                        continue
                else:
                    prev_price = cur_price

        except Exception as e:
            logger.error("\n!!!Error: %s ..\nRetring..." % e)
            sleep(5)


daemon = Daemonize(app="btcchina", pid=pid, action=main, keep_fds=keep_fds)
daemon.start()
