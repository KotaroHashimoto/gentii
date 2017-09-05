#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Zaif / Bittrex がこの数値％以上となったら Zaif XEM売り、Bittrex XEM買い
SellZaif_BuyTrex_Percentage = 1

# Zaif / Bittrex がこの数値％以下となったら Zaif XEM買い、Bittrex XEM売り
BuyZaif_SellTrex_Percentage = -1

# 一回に取引するXEMの最大枚数
Max_Xem_Trade_Amount = 1000

# １トレード後に開ける間隔 [秒]
Mask_After_Trade_Sec = 5


# 最も安い売り板の価格 x Buy_Rate_Ratio の価格に指値買いが入る
Buy_Rate_Ratio = 2.0

# 最も高い買い板の価格 x Sell_Rate_Ratio の価格に指値売りが入る
Sell_Rate_Ratio = 0.5

# 手数料％: (価格差％ - Commission) ％だけ多くXEMを買う
Commission = 0.35


# Zaif APIキー
Zaif_Key = ''

# Zaif シークレットキー
Zaif_Secret = ''


# Bittrex APIキー
Trex_Key = ''

# Bittrex シークレットキー
Trex_Secret = ''



from datetime import datetime
from zaifapi.impl import ZaifPublicApi, ZaifTradeApi
from bittrex.bittrex import Bittrex
from oandapy import API
from math import floor
import sys
import json
import requests
import time
import hmac
import hashlib


class Zaif:

    private = None
    public = None

    BTCJPY = 1
    JPY = 0
    XEM = 0

    def __init__(self):
        
        Zaif.private = ZaifTradeApi(Zaif_Key, Zaif_Secret)
        Zaif.public = ZaifPublicApi()

    def watch(self):

        res = Zaif.private.get_info2()['funds']
        Zaif.JPY = res['jpy']
        Zaif.XEM = res['xem']

        Zaif.BTCJPY = Zaif.public.last_price('btc_jpy')['last_price']

        res = Zaif.public.depth('xem_jpy')

        self.ask = res['asks'][0]
        self.bid = res['bids'][0]

        return 'Zaif: ask' + str(self.ask) + ', bid' + str(self.bid)

    def sell(self, am):
        return self.private.trade(currency_pair = 'xem_jpy', action = 'ask', price = round(self.bid[0] * Sell_Rate_Ratio, 4), amount = am)

    def buy(self, am):
        return self.private.trade(currency_pair = 'xem_jpy', action = 'bid', price = round(self.ask[0] * Buy_Rate_Ratio, 4), amount = am)


class Trex:

    public = None
    private = None

    BTC = 0
    XEM = 0

    def __init__(self):
        
        Trex.public = Bittrex('', '')
        Trex.private = Bittrex(Trex_Key, Trex_Secret)

    def watch(self):

        Trex.BTC = Trex.private.get_balance('BTC')['result']['Balance']
        Trex.XEM = Trex.private.get_balance('XEM')['result']['Balance']

        res = Trex.public.get_orderbook('BTC-XEM', 'both')['result']

        self.ask = [res['sell'][0]['Rate'], res['sell'][0]['Quantity']]
        self.bid = [res['buy'][0]['Rate'], res['buy'][0]['Quantity']]

        return 'Trex: ask' + str(self.ask) + ', bid' + str(self.bid)

    def sell(self, am):
        return self.private.sell_limit('BTC-XEM', am, round(self.bid[0] * Sell_Rate_Ratio, 8))

    def buy(self, am):
        return self.private.buy_limit('BTC-XEM', am, round(self.ask[0] * Buy_Rate_Ratio, 8))


class Position:

    DIFF = 0

    def __init__(self):
        pass

    def diff(self, zask, zbid, task, tbid):

        if Zaif.BTCJPY * task[0] < zbid[0]:
            zaif = zbid[0]
            trex = Zaif.BTCJPY * task[0]
        elif zask[0] < Zaif.BTCJPY * tbid[0]:
            zaif = zask[0]
            trex = Zaif.BTCJPY * tbid[0]

        else:
            zaif = 1
            trex = 1

        Position.DIFF = 100 * (zaif / trex - 1)

        return ' ' + str(round(zaif/2, 2)) + (' (+' if 0 < Position.DIFF else ' (') + str(round(Position.DIFF, 2)) + '%) ' + str(round(trex/2, 2)) + ' '


    def operation(self, zask, zbid, task, tbid):

        if BuyZaif_SellTrex_Percentage < Position.DIFF and Position.DIFF < SellZaif_BuyTrex_Percentage:
            return (None, 0)

        elif SellZaif_BuyTrex_Percentage <= Position.DIFF:
            return ('Sell Zaif', floor(min(min(Max_Xem_Trade_Amount, zbid[1]), task[1])))

        elif Position.DIFF <= BuyZaif_SellTrex_Percentage:
            return ('Buy Zaif', floor(min(min(Max_Xem_Trade_Amount, zask[1]), tbid[1])))


    def checkFund(self, op, amount, zask, task):

        if 'Sell Zaif' == op:
            if Zaif.XEM < amount or Trex.BTC < round(amount * (100.0 + Position.DIFF - Commission) / 100.0) * task[0]:
                return False
            else:
                return True

        elif 'Buy Zaif' == op:

            if Zaif.JPY < round(amount * (100.0 + Position.DIFF - Commission) / 100.0) * zask[0] or Trex.XEM < amount:
                return False
            else:
                return True

        else:
            return True


if __name__ == '__main__':

    trex = Trex()
    zaif = Zaif()
    pos = Position()

    while(True):

        try:
            t = trex.watch()
            z = zaif.watch()
            d = pos.diff(zaif.ask, zaif.bid, trex.ask, trex.bid)

            print(z + d + t, end = '\r')

            op, amount = pos.operation(zaif.ask, zaif.bid, trex.ask, trex.bid)
            if pos.checkFund(op, amount, zaif.ask, trex.ask):
                if op == 'Sell Zaif':
                    print('\nSell Zaif XEM, Buy Trex, XEM: ' + str(amount)  + '\n')
                    print(trex.buy(round(amount * (100.0 + Position.DIFF - Commission) / 100.0, 3)))
                    print(zaif.sell(amount))
                    time.sleep(Mask_After_Trade_Sec)

                elif op == 'Buy Zaif':
                    print('\nBuy Zaif XEM, Sell Trex, XEM: ' + str(amount)  + '\n')
                    print(zaif.buy(round(amount * (100.0 + Position.DIFF - Commission) / 100.0, 1)))
                    print(trex.sell(amount))
                    time.sleep(Mask_After_Trade_Sec)

            else:
                print('\nFunds not enough.\n')
                    
            time.sleep(1.5)

        except Exception as e:
            print(e)
            time.sleep(10)

