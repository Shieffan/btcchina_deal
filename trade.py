#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import requests
from datetime import datetime
import sqlite3
from time import sleep
import logging
cwd = os.path.dirname(os.path.realpath(__file__))
pid = os.path.join(cwd,"tmp/trade.pid") 
requests_log = logging.getLogger("requests")
requests_log.setLevel(logging.WARNING)
from daemonize import Daemonize

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
    interval = 15
    seq = 0
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
            sleep(5)
            continue

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
