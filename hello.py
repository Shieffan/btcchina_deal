#!/usr/bin/python
# -*- coding: utf-8 -*-
import ConfigParser
import btcchina
from flask import Flask,render_template,request,flash,redirect,url_for,jsonify,session

app = Flask(__name__)
app.secret_key = '33jlj53lk%#43-=43%#$/654&%^$f'

cf = ConfigParser.ConfigParser()
cf.read("btc.conf")    

info_access_key = cf.get("info", "access_key")
info_secret_key = cf.get("info", "secret_key")

deal_access_key = cf.get("deal", "access_key")
deal_secret_key = cf.get("deal", "secret_key")

cf_username = cf.get("user", "name")
cf_password = cf.get("user", "pass")

bc = btcchina.BTCChina(info_access_key,info_secret_key)
bc_deal = btcchina.BTCChina(deal_access_key,deal_secret_key)


@app.before_request
def before_request():
    if 'logged_in' not in session and request.endpoint != 'login':
        if request.is_xhr:
            return jsonify(code=-2,message="You are not logged in.")
        else:
            return render_template('login.html')



@app.route('/login',methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form["name"]
        password = request.form["password"]
        if is_valid(username,password):
            session["logged_in"] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html',message="Login Failed.")
    else:
        if 'logged_in' in session:
            return redirect(url_for('index'))
        else:
            return render_template('login.html')


def is_valid(username,password):
    if username==cf_username and password==cf_password:
        return True
    else:
        return False


@app.route('/')
def index():
    try:
        cf.read("btc.conf")
        config = {}
        LOW_SELL_RATIO = float(cf.get("risk", "low_sell_ratio"))
        config["LOW_SELL_RATIO"] = LOW_SELL_RATIO if LOW_SELL_RATIO<1 else 1
        HIGH_SELL_RATIO = float(cf.get("risk", "high_sell_ratio"))
        config["HIGH_SELL_RATIO"] = HIGH_SELL_RATIO if HIGH_SELL_RATIO>1 else 1
        FALLDOWN_SELL = float(cf.get("risk", "falldown_sell"))
        config["FALLDOWN_SELL"] = FALLDOWN_SELL if FALLDOWN_SELL>0 else 0

    except:
        return "Read config file error.Please make sure that btc.conf file exists and synatax right."
    
    return render_template('index.html',config=config)


@app.route('/get_info',methods=['GET'])
def get_info():
    if request.is_xhr:
        try:
            result = bc.get_account_info()
            title = result["profile"]["username"].title()
            btc_amount = result["balance"]["btc"]["amount"] or 0
            cny_amount = result["balance"]["cny"]["amount"] or 0
            f_btc_amount = result["frozen"]["btc"]["amount"] or 0
            f_cny_amount = result["frozen"]["cny"]["amount"] or 0
            message = "<p>%s, you currently have %g bitcoins and %g RMB, frozen %g bitcoins, %g RMB.</p>" % (title,float(btc_amount),float(cny_amount),float(f_btc_amount),float(f_cny_amount))
            code = 0
        except:
            message = "Something wrong happened."
            code = -1

        return jsonify(message=message,code=code)

    else:
        return "Illegal Request."

@app.route('/get_price',methods=['GET'])
def get_price():
    if request.is_xhr:
        try:
            result = bc.get_market_depth()
            bid_price = result["market_depth"]['bid'][0]["price"]
            ask_price = result["market_depth"]['ask'][0]["price"]
            message = "<ul><li>Bid Price: %g</li><li>Ask Price: %g</li></ul>" % (bid_price,ask_price)
            code = 0
        except:
            message = "Something wrong happened."
            code = -1

        return jsonify(message=message,code=code)

    else:
        return "Illegal Request."

@app.route('/get_undeal_orders',methods=['GET'])
def get_undeal_orders():
    if request.is_xhr:
        try:
            result = bc.get_orders(None,True)
            if len(result["order"]):
                orders=result["order"]
                message = "You have %d undeal orders." % len(result["order"])
                return jsonify(code=0,orders=orders,message=message)
            else:
                message="You have no undeal orders"
                return jsonify(code=1,message=message)
        except:
            message = "Something wrong happened."
            return jsonify(message=message,code=-1)

    else:
        return "Illegal Request."



@app.route('/sell_all',methods=['post'])
def sell_all():
    if request.is_xhr:
        try:
            res=bc.get_account_info()
            cc=float(res["balance"]["btc"]["amount"])
            if cc<0.0001:
                code = -1
                message = "You have no bitcoins now."
            else:
                result = bc.get_market_depth()
                price = float(result["market_depth"]['bid'][0]["price"])-0.1
                res = bc_deal.sell(str(price),str(cc-0.00001))
                if res==True:
                    code = 0
                    message = "Sell all your %g bitcoins at price %g successfully." %(cc,price)
                else:
                    try:
                        code = -1
                        message = "操作未完成，服务器返回：" + res["message"]
                    except:
                        code = -1
                        message = "Server communicate with btcchina timeout."
                   
        except Exception as e:
            code = -1
            message = "Error: %s" % e

        return jsonify(message=message,code=code)
    else:
        return "Illegal Request."

@app.route('/cancel_order',methods=['post'])
def cancel_order():
    if request.is_xhr:
        try:
            id = request.form["id"]
            res = bc_deal.cancel(int(id))
            
            if res==True:
                code = 0
                message = "Cancel order %s successfully" % id
            else:
                try:
                    code = -1
                    message = "操作未完成，服务器返回：" + res["message"]
                except:
                    code = -1
                    message = "Server communicate with btcchina timeout."
                   
        except Exception as e:
            code = -1
            message = "Error: %s" % e

        return jsonify(message=message,code=code)
    else:
        return "Illegal Request."



@app.route('/update',methods=['POST'])
def updateConfig():
    if request.is_xhr:
        low = float(request.form["low"]) if float(request.form["low"])<1 else 1
        high = float(request.form["high"]) if float(request.form["high"])>1 else 1
        fall = float(request.form["fall"]) if float(request.form["fall"])>0 else 0
        try:
            cf = ConfigParser.ConfigParser()
            cf.read("btc.conf")
            cf.set("risk", "low_sell_ratio",low)
            cf.set("risk", "high_sell_ratio",high)
            cf.set("risk", "falldown_sell",fall)
            cf.write(open('btc.conf','w'))
            
            code = 0
            message = "Update config successfully!"
        except Exception as e:
            code = -1
            message = "Updating config file failed: %s<br/>Please reload this page." % e

        return jsonify(code=code,message=message)

    else:
        return "Illegal Request."

if __name__ == '__main__':
    app.run(debug=True)
