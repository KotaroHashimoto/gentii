#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# bitFlyer / Coincheck がこの数値％以上となったら bitFlyer BTC売り、Coincheck BTC買い
SellbitFlyer_BuyCC_Percentage = 1

# bitFlyer / Coincheck がこの数値％以下となったら bitFlyer BTC買い、Coincheck BTC売り
BuybitFlyer_SellCC_Percentage = -1

# １回に取引するBTCの最大枚数
Max_BTC_Trade_Amount = 0.1

# １トレード後に開ける間隔 [秒]
Mask_After_Trade_Sec = 5


# 各口座に残しておく最低のJPY, BTC量
Min_JPY_Amount = 10000
Min_BTC_Amount = 0.02


# bitFlyer APIキー
BF_Key = ''

# bitFlyer シークレットキー
BF_Secret = ''


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


class BF:

#    public = None
    private = None

    BTC = 0
    JPY = 0

    def __init__(self):
        
        BF.private = pybitflyer.API(api_key = BF_Key, api_secret = BF_Secret)
#        BF.public = pybitflyer.API()

    def watch(self):

        res = BF.private.getbalance()

        for c in res:
            if c['currency_code'] == 'BTC':
                BF.BTC = c['amount']
            if c['currency_code'] == 'JPY':
                BF.JPY = c['amount']

        res = BF.private.board(product_code = 'BTC_JPY')

        self.ask = [float(res['asks'][0]['price']), float(res['asks'][0]['size'])]
        self.bid = [float(res['bids'][0]['price']), float(res['bids'][0]['size'])]

        return 'bitFlyer: ask' + str(self.ask) + ', bid' + str(self.bid)

    def sell(self, am):
        res = BF.private.sendchildorder(product_code = 'BTC_JPY', \
                                 child_order_type = 'MARKET', \
                                 side = 'SELL', \
                                 size = am)
        
        return res

    def buy(self, am):
        res = BF.private.sendchildorder(product_code = 'BTC_JPY', \
                                 child_order_type = 'MARKET', \
                                 side = 'BUY', \
                                 size = am)
        
        return res


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
    
#    public = None
    private = None

    BTC = 0
    JPY = 0

    def __init__(self):

        CC.private = CCApiCall()

    def watch(self):

        res = CC.private.get_api_call(CC.BALANCE).json()
        CC.JPY = floor(float(res['jpy']))
        CC.BTC = float(res['btc'])
        
        res = CC.private.get_api_call(CC.ORDERBOOK).json()
        
        self.ask = [float(res['asks'][0][0]), float(res['asks'][0][1])]
        self.bid = [float(res['bids'][0][0]), float(res['bids'][0][1])]

        return 'Coincheck: ask' + str(self.ask) + ', bid' + str(self.bid)

    def sell(self, am):

        body = {
            'pair': 'btc_jpy',
            'order_type': 'market_sell',
            'amount': am
            }

        CC.private.post_api_call(CC.ORDER, body).json()
        
    def buy(self, am):
        
        body = {
            'pair': 'btc_jpy',
            'order_type': 'market_buy',
            'market_buy_amount': floor(am * self.ask[0])
            }

        CC.private.post_api_call(CC.ORDER, body).json()

        
class Position:

    DIFF = 0

    def __init__(self):
        pass

    def diff(self, bask, bbid, cask, cbid):

        if cask[0] < bbid[0]:
            bf = bbid[0]
            cc = cask[0]
        elif bask[0] < cbid[0]:
            bf = bask[0]
            cc = cbid[0]

        else:
            bf = 1
            cc = 1

        Position.DIFF = 100 * (bf / cc - 1)

        return ' (+' if 0 < Position.DIFF else ' (' + str(round(Position.DIFF, 2)) + '%) '


    def operation(self, bask, bbid, cask, cbid):

        if BuybitFlyer_SellCC_Percentage < Position.DIFF and Position.DIFF < SellbitFlyer_BuyCC_Percentage:
            return (None, 0)

        elif SellbitFlyer_BuyCC_Percentage <= Position.DIFF:
            return ('Sell bitFlyer', round(min(bbid[1], cask[1]), 3))

        elif Position.DIFF <= BuybitFlyer_SellCC_Percentage:
            return ('Buy bitFlyer', round(min(bask[1], cbid[1]), 3))


    def checkFund(self, op, amount, bask, cask):

        if 'Sell bitFlyer' == op:
            if BF.BTC - Min_BTC_Amount < amount or CC.JPY - Min_JPY_Amount < amount * cask[0]:
                return False
            else:
                return True

        elif 'Buy bitFlyer' == op:

            if BF.JPY - Min_JPY_Amount < amount * bask[0] or CC.BTC - Min_BTC_Amount < amount:
                return False
            else:
                return True

        else:
            return True


if __name__ == '__main__':

    bf = BF()
    cc = CC()
    pos = Position()

    while(True):

        try:
            b = bf.watch()
            c = cc.watch()
            d = pos.diff(bf.ask, bf.bid, cc.ask, cc.bid)

            print(b + d + c, end = '\r')

            op, amount = pos.operation(bf.ask, bf.bid, cc.ask, cc.bid)
            if pos.checkFund(op, amount, bf.ask, cc.ask):
                if op == 'Sell bitFlyer':
                    print('\nSell bitFlyer BTC, Buy Coincheck BTC: ' + str(amount)  + '\n')
                    print(cc.buy(amount))
                    print(bf.sell(amount))
                    time.sleep(Mask_After_Trade_Sec)

                elif op == 'Buy bitFlyer':
                    print('\nBuy bitFlyer BTC, Sell Coincheck, BTC: ' + str(amount)  + '\n')
                    print(bf.buy(amount))
                    print(cc.sell(amount))
                    time.sleep(Mask_After_Trade_Sec)

            else:
                print('\nFunds not enough.\n')
                    
            time.sleep(1.5)

        except Exception as e:
            print(e)
            time.sleep(10)
