#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import sqlite3
import requests
from time import sleep
from mymail import send_mail
import ConfigParser
from daemonize import Daemonize
cwd = os.path.dirname(os.path.realpath(__file__))
pid = os.path.join(cwd,"tmp/notify.pid") 
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
    while True:
        mail_body=""
        try:
            r = requests.get('https://data.btcchina.com/data/ticker') 
            result = r.json()
            price = float(result['ticker']['last'])
        except:
            sleep(5)
            continue

        try:
            ids = []
            for row in c.execute("SELECT * FROM price_notify"):
                if row[1]==0 and price<row[2]:
                    mail_body+='Current price %g is lower than %g.\n' %(price,row[2])
                    ids.append((row[0],))

                if row[1]==1 and price>row[2]:
                    mail_body+='Current price %g is higher than %g.\n' %(price,row[2])
                    ids.append((row[0],))
            if len(ids):
                c.executemany("DELETE FROM price_notify WHERE id=?",ids)
                conn.commit()
            if mail_body:
                mail("Price Notification",mail_body)
        except:
            pass

    


if __name__ == '__main__':
    try:
        daemon = Daemonize(app="btcchina_notify", pid=pid, action=main)
        daemon.start()
    except Exception as e:
        pass