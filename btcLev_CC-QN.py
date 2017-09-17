#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# QUOINEX / Coincheck がこの数値％以上となったら QUOINEX BTC売り、Coincheck BTC買い
SellQN_BuyCC_Percentage = 1

# QUOINEX / Coincheck がこの数値％以下となったら QUOINEX BTC買い、Coincheck BTC売り
BuyQN_SellCC_Percentage = -1

# １回に取引するBTCの枚数
BTC_Trade_Amount = 1.0


# QUOINEX トークンID
QN_Key = ''

# QUOINEX APIシークレット
QN_Secret = ''


# Coincheck APIキー
CC_Key = ''

# Coincheck シークレットキー
CC_Secret = ''


from datetime import datetime
import pybitflyer
from json import loads, dump
import ssl
from math import floor
import sys
import json
import requests
import time
import hmac
import hashlib



class Quoine():

    token_id = None
    api_secret = None
    api_endpoint = None

    def __init__(self):

        Quoine.token_id = QN_Key
        Quoine.api_secret = QN_Secret
        Quoine.api_endpoint = 'https://api.quoine.com'
    
    def watch(self):

        url = Quoine.api_endpoint + '/products/5/price_levels'
        r = requests.get(url)
        if r.status_code == 200:
            if r.text == "null":
                print("No content returned for URL %s" % url)

                self.ask = [None, None]
                self.bid = [None, None]

            else:
                data = loads(r.text)

                self.ask = [float(data['sell_price_levels'][0][0]), float(data['sell_price_levels'][0][1])]
                self.bid = [float(data['buy_price_levels'][0][0]), float(data['buy_price_levels'][0][1])]

                return 'Quoine: ask' + str(self.ask) + ', bid' + str(self.bid)


        else:
            self.ask = [None, None]
            self.bid = [None, None]

            print("\nError %s while calling URL %s:\n" % (r.status_code,url))


    def orderQuoine(self, side, amount):

        order = {}
        order['order_type'] = 'market'
        order['product_id'] = 5 #BTCJPY
        order['side'] = side
        order['quantity'] = amount
        order['leverage_level'] = 1
        order['price'] = str(self.bid[0] if side == 'sell' else self.ask[0])
        order['order_direction'] = 'netout'
        order['currency_pair_code'] = 'BTCJPY'
        order['product_code'] = 'CASH'

        path = '/orders/'
        body = dumps(order)
        timestamp = str(int(time()))
        auth_payload = {
            'path': path,
            'nonce': timestamp,
            'token_id': Quoine.token_id
            }
        sign = jwt.encode(auth_payload, Quoine.api_secret, algorithm='HS256')


        response = requests.post(
            Quoine.api_endpoint+path
            ,data = body
            ,headers = {
                'X-Quoine-API-Version': '2',
                'X-Quoine-Auth': sign,
                'Content-Type': 'application/json'
                })

#        print(response.status_code)
#        print(response.text)
#        print(response.headers)


    def sell(self, am):
        self.orderQuoine('sell', am)

    def buy(self, am):
        self.orderQuoine('buy', am)


class CCApiCall:

    def __init__(self):
        self.api_key = CC_Key
        self.api_secret = CC_Secret
        self.api_endpoint = 'https://coincheck.com'

    def get_api_call(self,path):
        timestamp = str(int(time.time()))
        text = timestamp + self.api_endpoint + path
        sign = hmac.new(bytes(self.api_secret.encode('ascii')), bytes(text.encode('ascii')), hashlib.sha256).hexdigest()
        request_data=requests.get(
            self.api_endpoint+path
            ,headers = {
                'ACCESS-KEY': self.api_key,
                'ACCESS-NONCE': timestamp,
                'ACCESS-SIGNATURE': sign,
                'Content-Type': 'application/json'
                })
        return request_data

    def post_api_call(self,path,body):
        body = json.dumps(body)
        timestamp = str(int(time.time()))
        text = timestamp + self.api_endpoint + path + body
        sign = hmac.new(bytes(self.api_secret.encode('ascii')), bytes(text.encode('ascii')), hashlib.sha256).hexdigest()
        request_data=requests.post(
            self.api_endpoint+path
            ,data= body
            ,headers = {
                'ACCESS-KEY': self.api_key,
                'ACCESS-NONCE': timestamp,
                'ACCESS-SIGNATURE': sign,
                'Content-Type': 'application/json'
                })
        return request_data

    
class CC:

    ORDERBOOK = '/api/order_books'
    BALANCE = '/api/accounts/balance'
    ORDER = '/api/exchange/orders'    
    POSITION = '/api/exchange/leverage/positions'
    
#    public = None
    private = None

    def __init__(self):

        CC.private = CCApiCall()

    def getPosID(self):

        res = CC.private.get_api_call(CC.POSITION).json()

        id = -1
        side = ''
        amount = -1

        if 0 < len(res['data']):
            id = res['data'][0]['id']
            side = res['data'][0]['side']
            amount = res['data'][0]['amount']

        return (id, side, amount)

    def watch(self):

        res = CC.private.get_api_call(CC.ORDERBOOK).json()
        
        self.ask = [float(res['asks'][0][0]), float(res['asks'][0][1])]
        self.bid = [float(res['bids'][0][0]), float(res['bids'][0][1])]

        return 'Coincheck: ask' + str(self.ask) + ', bid' + str(self.bid)

    def sell(self, id, side, am):

        if side == '':
            body = {
                'pair': 'btc_jpy',
                'order_type': 'leverage_sell',
                'amount': BTC_Trade_Amount
                }

        else:
            body = {
                'pair': 'btc_jpy',
                'order_type': 'close_long',
                'amount': am,
                'position_id': id
                }

        CC.private.post_api_call(CC.ORDER, body).json()
        

    def buy(self, id, side, am):
        
        if side == '':
            body = {
                'pair': 'btc_jpy',
                'order_type': 'leverage_buy',
                'amount': BTC_Trade_Amount
                }

        else:
            body = {
                'pair': 'btc_jpy',
                'order_type': 'close_short',
                'amount': am,
                'position_id': id
                }

        CC.private.post_api_call(CC.ORDER, body).json()

        
class Position:

    DIFF = 0

    def __init__(self):
        pass

    def diff(self, qask, qbid, cask, cbid):

        if cask[0] < qbid[0]:
            qn = qbid[0]
            cc = cask[0]
        elif qask[0] < cbid[0]:
            qn = qask[0]
            cc = cbid[0]

        else:
            qn = 1
            cc = 1

        Position.DIFF = 100 * (qn / cc - 1)

        return ' (+' if 0 < Position.DIFF else ' (' + str(round(Position.DIFF, 2)) + '%) '


    def operation(self, qask, qbid, cask, cbid):

        if BuyQN_SellCC_Percentage < Position.DIFF and Position.DIFF < SellQN_BuyCC_Percentage:
            return (None, 0)

        elif SellQN_BuyCC_Percentage <= Position.DIFF:
            return ('Sell Quoine', round(min(qbid[1], cask[1]), 3))

        elif Position.DIFF <= BuyQN_SellCC_Percentage:
            return ('Buy Quoine', round(min(qask[1], cbid[1]), 3))


    def checkFund(self, op, amount, qask, cask):
        return True


if __name__ == '__main__':

    qn = Quoine()
    cc = CC()
    pos = Position()

    while(True):

        try:
            q = qn.watch()
            c = cc.watch()
            d = pos.diff(qn.ask, qn.bid, cc.ask, cc.bid)

            print(q + d + c, end = '\r')

            op, amount = pos.operation(qn.ask, qn.bid, cc.ask, cc.bid)
            if pos.checkFund(op, amount, qn.ask, cc.ask):
                (id, side, amount) = cc.getPosID()

                if op == 'Sell Quoine' and side != 'buy':
                    print('\nSell Quoine BTC, Buy Coincheck BTC: ' + str(amount)  + '\n')
                    print(cc.buy(id, side, amount))
                    print(qn.sell(BTC_Trade_Amount))
                    time.sleep(Mask_After_Trade_Sec)

                elif op == 'Buy Quoine' and side != 'sell':
                    print('\nBuy QUoine BTC, Sell Coincheck, BTC: ' + str(amount)  + '\n')
                    print(cc.buy(id, side, amount))
                    print(qn.sell(BTC_Trade_Amount))
                    time.sleep(Mask_After_Trade_Sec)

            else:
                print('\nFunds not enough.\n')
                    
            time.sleep(1.5)

        except Exception as e:
            print('hoge', e)
            time.sleep(10)
