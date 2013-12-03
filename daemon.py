#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import logging 
from time import sleep
from daemonize import Daemonize
import ConfigParser
import btcchina


cwd = os.getcwd()
pid = os.path.join(cwd,"tmp/daemon.pid") 
logger = logging.getLogger(__name__) 
logger.setLevel(logging.DEBUG) 
logger.propagate = False
fh = logging.FileHandler(os.path.join(cwd,"tmp/daemon.log"), "a")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s;%(levelname)s:%(message)s","%Y-%m-%d %H:%M:%S")
fh.setFormatter(formatter)
logger.addHandler(fh) 
keep_fds = [fh.stream.fileno()]


def main():
    try:
        cf = ConfigParser.ConfigParser()
        cf.read(os.path.join(cwd,"btc.conf"))  
        info_access_key = cf.get("info", "access_key")
        info_secret_key = cf.get("info", "secret_key")
        deal_access_key = cf.get("deal", "access_key")
        deal_secret_key = cf.get("deal", "secret_key")
        logger.info("Read config successfully.")
    except:
        logger.error("Parse config file error.Please make sure that btc.conf file exists.")
   
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
            cf.read(os.path.join(cwd,"btc.conf"))  
        except:
            logger.error("Please check if btc.conf exists.")

        try:
            LOW_SELL_RATIO = float(cf.get("risk", "low_sell_ratio"))
            LOW_SELL_RATIO = LOW_SELL_RATIO if LOW_SELL_RATIO<1 else 0
        except:
            LOW_SELL_RATIO = 0

        try:
            HIGH_SELL_RATIO = float(cf.get("risk", "high_sell_ratio"))
            HIGH_SELL_RATIO = HIGH_SELL_RATIO if HIGH_SELL_RATIO>1 else 0
        except:
            HIGH_SELL_RATIO = 0

        try:
            FALLDOWN_SELL = float(cf.get("risk", "falldown_sell"))
            FALLDOWN_SELL = FALLDOWN_SELL if FALLDOWN_SELL>0 else 0
        except:
            FALLDOWN_SELL = 0

        try:
            LOW_SELL_PRICE = float(cf.get("risk", "low_sell_price"))
        except:
            LOW_SELL_PRICE = 0
            
        try:
            HIGH_SELL_PRICE = float(cf.get("risk","high_sell_price"))
        except:
            HIGH_SELL_PRICE = 0

        
        logger.info("\x1b[1mLOW_SELL_RATIO = %g; HIGH_SELL_RATIO = %g; FALLDOW_SELL = %g;\x1b[0m" %(LOW_SELL_RATIO,HIGH_SELL_RATIO,FALLDOWN_SELL))
        

        logger.info("\x1b[1mLOW_SELL_PRICE = %s; HIGH_SELL_PRICE = %s;\x1b[0m" %(LOW_SELL_PRICE,HIGH_SELL_PRICE))
        try:
            result = bc.get_account_info()
            if float(result["balance"]["btc"]["amount"]) < 0.001:
                logger.info("You have no btccoins now...Let me sleep one minute :)\n")
                prev_price = 0
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

                LOW_SELL_RATIO = float(LOW_SELL_RATIO)
                if LOW_SELL_RATIO > 1.0:
                    LOW_SELL_RATIO = 1.0
                ratio = cur_price/last_price

                if is_max==True:
                    logger.info("\n\r\033[1m\033[36m##The price reached the highest price %g since your last buy transaction.\x1b[0m" % (max_price))
                
                if is_min==True:
                    logger.info("\n\r\033[1m\033[31m##The price fell down to the lowest price %g since your last buy transaction.\x1b[0m" % (min_price))
                
                if LOW_SELL_PRICE and cur_price<LOW_SELL_PRICE:
                        logger.info("\n\r\033[1;31m$$_Ratio: %g; Current bid price %g; LOW_SELL_PRICE: %g;\n\rFuck, selling all %g bitcons.\x1b[0m" % (ratio,cur_price,LOW_SELL_PRICE,amount))
                        res = bc_deal.sell(str(cur_price-0.1),str(amount-0.00001))
                        if res==True:
                            logger.info("$~_Commit order successfully！\n")
                            prev_price = 0
                            continue
                        else:
                            try:
                                logger.warning("\033[1;31m$!_Failed, server says： %s \x1b[0m\n" % res["message"])
                            except:
                                logger.error("\033[1;31m$!_Failed, unknow error! \x1b[0m\n")

                if HIGH_SELL_PRICE and cur_price>HIGH_SELL_PRICE:
                        logger.info("\n\r\033[1;32m$$_Ratio: %g; Current bid price %g; HIGH_SELL_PRICE: %g;\n\rNice, selling all %g bitcons.\x1b[0m" % (ratio,cur_price,HIGH_SELL_PRICE,amount))
                        res = bc_deal.sell(str(cur_price-0.1),str(amount-0.00001))
                        if res==True:
                            logger.info("$~_Commit order successfully！\n")
                            prev_price = 0
                            continue
                        else:
                            try:
                                logger.warning("\033[1;31m$!_Failed, server says： %s \x1b[0m\n" % res["message"])
                            except:
                                logger.error("\033[1;31m$!_Failed, unknow error! \x1b[0m\n")

                if LOW_SELL_RATIO and ratio <= LOW_SELL_RATIO:
                    #SELL ALL
                    logger.info("\n\r\033[1;31m$$_Ratio: %g; Current bid price %g; Your last buybtc price %g; LOW_SELL_RATIO: %g;\n\rFuck, selling all %g bitcons.\x1b[0m" % (ratio,cur_price,last_price,LOW_SELL_RATIO,amount))
                    res = bc_deal.sell(str(cur_price-0.1),str(amount-0.00001))
                    if res==True:
                        logger.info("$~_Commit order successfully！\n")
                        prev_price = 0
                        continue
                    else:
                        try:
                            logger.warning("\033[1;31m$!_Failed, server says： %s \x1b[0m\n" % res["message"])
                        except:
                            logger.error("\033[1;31m$!_Failed, unknow error! \x1b[0m\n")

                if HIGH_SELL_RATIO and ratio >= HIGH_SELL_RATIO:
                    #SELL ALL
                    logger.info("\n\r\033[1;32m$$_Ratio: %g; Current bid price %g; Your last buybtc price %g; HIGH_SELL_RATIO: %g;\n\rNice, selling all %g bitcons.\x1b[0m" % (ratio,cur_price,last_price,HIGH_SELL_RATIO,amount))
                    res = bc_deal.sell(str(cur_price-0.1),str(amount-0.00001))
                    if res==True:
                        logger.info("$~_Commit order successfully！\n")
                        prev_price = 0
                        continue
                    else:
                        try:
                            logger.warning("\033[1;31m$!_Failed, server says： %s \x1b[0m\n" % res["message"])
                        except:
                            logger.error("\033[1;31m$!_Failed, unknow error! \x1b[0m\n")
                    

                if FALLDOWN_SELL and prev_price - cur_price > FALLDOWN_SELL:
                    logger.info("\n\r\033[1m\x1b[32m!!Sorry to sell all your %g bitcoins because its price has fallen down %g RMB in the past 30 seconds.\x1b[0m" % (amount,prev_price - cur_price))
                    try:
                        res = bc_deal.sell(str(cur_price-0.1),str(amount-0.00001))
                        if res==True:
                            logger.info("$~_Commit order successfully！\n")
                            prev_price = 0
                    except Exception as e:
                        logger.error("\n!!!Selling error: %s ...\n" % e)
                    continue
                else:
                    prev_price = cur_price

               
                if HIGH_SELL_RATIO and ratio >= 1:
                    logger.info("\n\r$#_Ratio:\x1b[1;32m %g\x1b[0m; Current bid price %g; Your last buybtc price %g; HIGH_SELL_RATIO %g;\n\r\033[1m\x1b[33mDo nothing with total %g bitcoins.\x1b[0m\n" % (ratio,cur_price,last_price,HIGH_SELL_RATIO,amount))
                
                if LOW_SELL_RATIO and ratio < 1:
                    logger.info("\n\r$#_Ratio:\x1b[1;31m %g\x1b[0m; Current bid price %g; Your last buybtc price %g; LOW_SELL_RATIO: %g;\n\r\033[1m\x1b[33mDo nothing with total %g bitcoins.\x1b[0m\n" % (ratio,cur_price,last_price,LOW_SELL_RATIO,amount))

                sleep(30)

        except Exception as e:
            logger.error("\n!!!Error: %s ..\nRetring...\n" % e)
            prev_price = 0
            sleep(5)


if __name__ == "__main__":
    try:
        daemon = Daemonize(app="btcchina", pid=pid, action=main, keep_fds=keep_fds)
        daemon.start()
    except Exception as e:
         logger.error("Fatal Error:\n\r%s\n" % e)