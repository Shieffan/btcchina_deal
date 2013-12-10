#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sys
import logging 
import requests
from time import sleep
from daemonize import Daemonize
import ConfigParser
import btcchina
from mymail import send_mail

default_encoding = 'utf-8'
if sys.getdefaultencoding() != default_encoding:
    reload(sys)
    sys.setdefaultencoding(default_encoding)

cwd = os.path.dirname(os.path.realpath(__file__))
pid = os.path.join(cwd,"tmp/daemon.pid") 
logger = logging.getLogger(__name__) 
logger.setLevel(logging.DEBUG) 
logger.propagate = False
fh = logging.FileHandler(os.path.join(cwd,"tmp/daemon.log"), "a+")
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s;%(levelname)s:%(message)s","%Y-%m-%d %H:%M:%S")
fh.setFormatter(formatter)
logger.addHandler(fh) 
keep_fds = [fh.stream.fileno()]


cf = ConfigParser.ConfigParser()
cf.read(os.path.join(cwd,"btc.conf"))  
try:
    sender_login = cf.get("email", "login")
    sender_pass = cf.get("email","pass")
    sender_smtp = cf.get("email","sender_smtp")
    receiver = cf.get("email","receiver")
    use_mail = True
except:
    use_mail = False


def mail(subject="",message=""):
    global use_mail,sender_login,sender_pass,sender_smtp,receiver
    if use_mail:
        sender_addr = sender_login+"@"+sender_smtp.split(":")[0]
        send_mail(from_addr=sender_addr, to_addr_list=[receiver],subject=subject, message=message,login=sender_login, password=sender_pass,smtpserver=sender_smtp)
    else:
        return None

def get_must_sell_price(bc):
    try:
        r = requests.get('https://data.btcchina.com/data/orderbook',timeout=30) 
        result = r.json()
        bids = result['bids']
        count = 0.0
        money = 0.0
        for i in bids:
            count+=i[1]
            money+=i[1]*i[0]
            price = money/count
            if count>=15:
                break
        return price
    except requests.exceptions.RequestException,AttributeError:
        result = bc.get_market_depth(10)
        bid_money_total=0.0
        bid_amount_total=0.0
        for b in result["market_depth"]["bid"]:
            bid_amount_total+=b["amount"]
            bid_money_total+=b["price"]*b["amount"]
            if bid_amount_total>15:
                break
        price  = bid_money_total/bid_amount_total
        return price




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
        logger.error("Parse config file error.Please make sure that btc.conf file exists. Exiting..")
        sys.exit(-1)


    bc = btcchina.BTCChina(info_access_key,info_secret_key)
    bc_deal = btcchina.BTCChina(deal_access_key,deal_secret_key)
    logger.info("Daemon Started..")

    max_price = 0
    min_price = 0
    t_date = 0
    is_max = is_min = False
    prev_price = 0
    while True:
        logger.info("Read config..")
        try:
            cf.read(os.path.join(cwd,"btc.conf"))  
        except:
            logger.error("Please check if btc.conf exists.")

        try:
            USE_DAEMON = cf.get("global","use")
        except:
            USE_DAEMON = False

        if USE_DAEMON!="true":
            max_price = 0
            min_price = 0
            t_date = 0
            is_max = is_min = False
            prev_price = 0
            logger.info("DO_NOT_USE_DAEMON..Sleep 30 seconds.")
            sleep(30)
            continue

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
        logger.info("Refresh info..")
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
                r = requests.get('https://data.btcchina.com/data/ticker') 
                result = r.json()
                cur_price = float(result['ticker']['buy'])
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

                if is_max==True and prev_price!=0:
                    logger.info("\n\r\033[1m\033[36m##The price reached the highest price %g since your last buy transaction.\x1b[0m" % (max_price))
                
                if is_min==True and prev_price!=0:
                    logger.info("\n\r\033[1m\033[31m##The price fell down to the lowest price %g since your last buy transaction.\x1b[0m" % (min_price))
                
                if LOW_SELL_PRICE and cur_price<LOW_SELL_PRICE:
                        reason = "\n\r\033[1;31m$$_Ratio: %g; Current bid price %g; LOW_SELL_PRICE: %g;\n\rFuck, selling all %g bitcoins.\x1b[0m" % (ratio,cur_price,LOW_SELL_PRICE,amount)
                        logger.info(reason)
                        sell_price = get_must_sell_price(bc)
                        res = bc_deal.sell(str(sell_price-0.1),str(amount-0.00001))
                        if res==True:
                            reason = "$$_Ratio: %g; Current bid price %g; LOW_SELL_PRICE: %g;\n\rFuck, selling all %g bitcoins." % (ratio,cur_price,LOW_SELL_PRICE,amount)
                            mail("Sorry to sell all your bitcoins",reason+"\n\rSell with price "+str(sell_price) + " successfully！")
                            logger.info("$~_Commit order at price %g successfully！\n" % sell_price)
                            prev_price = 0
                            continue
                        else:
                            try:
                                logger.warning("\033[1;31m$!_Failed, server says： %s \x1b[0m\n" % res["message"])
                            except:
                                logger.error("\033[1;31m$!_Failed, unknow error! \x1b[0m\n")

                if HIGH_SELL_PRICE and cur_price>HIGH_SELL_PRICE:
                        reason = "\n\r\033[1;32m$$_Ratio: %g; Current bid price %g; HIGH_SELL_PRICE: %g;\n\rNice, selling all %g bitcoins.\x1b[0m" % (ratio,cur_price,HIGH_SELL_PRICE,amount)
                        logger.info(reason)
                        res = bc_deal.sell(str(cur_price-0.1),str(amount-0.00001))
                        if res==True:
                            reason = "$$_Ratio: %g; Current bid price %g; HIGH_SELL_PRICE: %g;\n\rNice, selling all %g bitcoins." % (ratio,cur_price,HIGH_SELL_PRICE,amount)
                            mail("Happly to sell all your bitcoins.",reason)
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
                    reason = "\n\r\033[1;31m$$_Ratio: %g; Current bid price %g; Your last buybtc price %g; LOW_SELL_RATIO: %g;\n\rFuck, selling all %g bitcoins.\x1b[0m" % (ratio,cur_price,last_price,LOW_SELL_RATIO,amount)
                    logger.info(reason)
                    sell_price = get_must_sell_price(bc)
                    res = bc_deal.sell(str(sell_price-0.1),str(amount-0.00001))
                    if res==True:
                        reason = "$$_Ratio: %g; Current bid price %g; Your last buybtc price %g; LOW_SELL_RATIO: %g;\n\rFuck, selling all %g bitcoins." % (ratio,cur_price,last_price,LOW_SELL_RATIO,amount)
                        mail("Sorry to sell all your bitcoins",reason+"\n\rSell with price "+str(sell_price) + " successfully！")
                        logger.info("$~_Commit order at price %g successfully！\n" % sell_price)
                        prev_price = 0
                        continue
                    else:
                        try:
                            logger.warning("\033[1;31m$!_Failed, server says： %s \x1b[0m\n" % res["message"])
                        except:
                            logger.error("\033[1;31m$!_Failed, unknow error! \x1b[0m\n")

                if HIGH_SELL_RATIO and ratio >= HIGH_SELL_RATIO:
                    #SELL ALL
                    reason = "\n\r\033[1;32m$$_Ratio: %g; Current bid price %g; Your last buybtc price %g; HIGH_SELL_RATIO: %g;\n\rNice, selling all %g bitcoins.\x1b[0m" % (ratio,cur_price,last_price,HIGH_SELL_RATIO,amount)
                    logger.info(reason)
                    res = bc_deal.sell(str(cur_price-0.1),str(amount-0.00001))
                    if res==True:
                        reason=  "$$_Ratio: %g; Current bid price %g; Your last buybtc price %g; HIGH_SELL_RATIO: %g;\n\rNice, selling all %g bitcoins." % (ratio,cur_price,last_price,HIGH_SELL_RATIO,amount)
                        mail("Happly to sell all your bitcoins.",reason)
                        logger.info("$~_Commit order successfully！\n")
                        prev_price = 0
                        continue
                    else:
                        try:
                            logger.warning("\033[1;31m$!_Failed, server says： %s \x1b[0m\n" % res["message"])
                        except:
                            logger.error("\033[1;31m$!_Failed, unknow error! \x1b[0m\n")
                    

                if FALLDOWN_SELL and prev_price - cur_price > FALLDOWN_SELL:
                    reason = "\n\r\033[1m\x1b[32m!!Sorry to sell all your %g bitcoins because its price has fallen down %g RMB in the past 30 seconds.\x1b[0m" % (amount,prev_price - cur_price)
                    logger.info(reason)
                    try:
                        sell_price = get_must_sell_price(bc)
                        res = bc_deal.sell(str(sell_price-0.1),str(amount-0.00001))
                        if res==True:
                            reason = "Sorry to sell all your %g bitcoins because its price has fallen down %g RMB in the past 30 seconds." % (amount,prev_price - cur_price)
                            mail("I am selling all your bitcoins",reason+"\n\rSell with price "+str(sell_price) + " successfully！")
                            logger.info("$~_Commit order at price %g successfully！\n" % sell_price)
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
        mail("Daemon exited..","Daemon exited unexpectedly: %s" % e)
