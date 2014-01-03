#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import requests
from datetime import datetime
import sqlite3
import ConfigParser
from time import sleep
import logging
cwd = os.path.dirname(os.path.realpath(__file__))
pid = os.path.join(cwd,"tmp/trade.pid") 
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)
from daemonize import Daemonize
from mymail import send_mail

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


def main():
    conn = sqlite3.connect(os.path.join(cwd,'trade.db'))
    c = conn.cursor()
    c.execute("CREATE TABLE IF NOT EXISTS trade (date INTEGER NOT NULL, price REAL NOT NULL, amount REAL NOT NULL, tid INTEGER NOT NULL, type INTEGER NOT NULL)")
    c.execute("CREATE INDEX IF NOT EXISTS trade_idx ON trade(date ASC)")
    conn.commit()
    logging.basicConfig(filename=os.path.join(cwd,"tmp/trade.log"),format='%(asctime)s %(levelname)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S",level=logging.INFO)
    logging.info("Trade fetch daemon started...")
    c.execute("DELETE FROM trade")
    conn.commit()
    interval = 60
    seq = 0
    counter = 0
    last_notify_time = datetime.now()
    while True:
        try:
            if seq==0:
                r = requests.get('https://data.btcchina.com/data/historydata',timeout=60) 
                result = r.json()
                if len(result):
                    seq = result[-1]['tid']
            else:
                r = requests.get('https://data.btcchina.com/data/historydata?since='+seq,timeout=60)
                result = r.json()
                if len(result):
                    seq = result[-1]['tid']
        except Exception as e:
            logging.warn("Fetch trade history failed. Reason: %s. Retry in 5 seconds." % e)
            sleep(15)
            continue

        if len(result):
            items = []
            for t in result:
                type = 0 if t['type']=='sell' else 1
                item = (int(t['date']),float(t['price']),float(t['amount']),int(t['tid']),type)
                items.append(item)

            c.executemany('INSERT INTO trade VALUES (?,?,?,?,?)', items)
            conn.commit()

        if len(result)>=99:
            if interval>=10:
                interval -= 5
        else:
            if interval<=60:
                interval +=5

        if interval<=60:
            counter += 1
        else:
            counter -= 1
            if counter<=0:
                counter = 0

        if counter == 3:
            message = "We have encountered a trade volumn rush. Please check!"
            current = datetime.now()
            time_t = (current-last_notify_time).seconds
            if time_t>300:
                mail("Volumn Notification.",message)
                last_notify_time = current
            counter = 0

        if len(result):
            s_time = datetime.fromtimestamp(int(result[0]['date'])).strftime('%Y-%m-%d %H:%M:%S')
            e_time = datetime.fromtimestamp(int(result[-1]['date'])).strftime('%Y-%m-%d %H:%M:%S')
            logging.info("Saving trade from %s(%s) to %s(%s) successfully. Sleep %d seconds.\n" %(s_time,result[0]['tid'],e_time,result[-1]['tid'],interval))
            sleep(interval)


if __name__ == '__main__':
    try:
        daemon = Daemonize(app="btcchina_trade", pid=pid, action=main)
        daemon.start()
    except Exception as e:
        logging.error("Fatal Error:\n\r%s\n" % e)
