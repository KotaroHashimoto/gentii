#!/usr/bin/env python3

# 通知価格差[円]
Price_Diff_To_Alert = 5000

# 価格チェック時間間隔[分]
Monitor_Period = 10

# 通知メール先
Mail_To = "hoge@fuga.pi.yo"

from json import load
from time import sleep
import ssl
from sys import version_info, exit
import os

if version_info.major == 2 and version_info.minor == 7:
    from urllib2 import urlopen, Request
elif version_info.major == 3 and version_info.minor == 6:
    from urllib.request import urlopen, Request
else:
    print('Please install python2.7.x or python3.6.x')
    exit(1)


# 取引所ごとに価格や板の情報を保持するクラス
class Exchange:

    def __init__(self, name, url, last, sask, sbid):
        self.name = name #取引所名
        self.url = url #取引所のAPIアクセス用URL
        self.last = last #最終取引価格キー
        self.sask = sask #最高買値キー
        self.sbid = sbid #最安売値キー

        self.ask = 0 #最高買値
        self.bid = 0 #最安売値
        self.p = 0 #最終取引価格

    def update(self):

        # 最新価格取得
        data = load(urlopen(Request(self.url, headers = {'User-Agent':'Hoge Browser'})))

        # 価格情報更新
        self.ask = int(data[self.sask])
        self.bid = int(data[self.sbid])
        self.p = int(data[self.last])
        

if __name__ == '__main__':

    ssl._create_default_https_context = ssl._create_unverified_context

    # 監視する取引所リスト
    base = [ \
#        Exchange('bitFlyer FX', 'https://api.bitflyer.jp/v1/getticker?product_code=FX_BTC_JPY', 'ltp', 'best_ask', 'best_bid'), \
        Exchange('bitFlyer', 'https://api.bitflyer.jp/v1/getticker?product_code=BTC_JPY', 'ltp', 'best_ask', 'best_bid'), \
        Exchange('Zaif', 'https://api.zaif.jp/api/1/ticker/btc_jpy', 'last', 'ask', 'bid'), \
        Exchange('coincheck', 'https://coincheck.com/api/ticker', 'last', 'ask', 'bid'), \
#        Exchange('Quoine JPY', 'https://api.quoine.com/products/5', 'last_traded_price', 'market_ask', 'market_bid'), \
#        Exchange('BtcBox', 'https://www.btcbox.co.jp/api/v1/ticker/', 'last', 'sell', 'buy'), \
        ]

    while True:

        minp = 100000000
        maxp = 0

        minName = ''
        maxName = ''
        msg = ''

        for e in base:
            while e.p == 0:
                e.update()

        # 価格が最も開いている取引所を調べる
        for e in base:

            # 最安値の取引所と価格
            if e.p < minp:
                minp = e.p
                minName = e.name

            # 最高値の取引所と価格
            if maxp < e.p:
                maxp = e.p
                maxName = e.name

            # 指定価格差以上開いていたものを通知対象にする
            for et in base:
                if Price_Diff_To_Alert < abs(e.p - et.p) and et.p < e.p:
                    msg += e.name + '(' + str(e.p) + ') - ' + et.name + '(' + str(et.p) + '), 価格差:' + str(e.p - et.p) + '円    '

        for e in base:
            e.p = 0

        # 最も価格差が開いていた取引所
        sbj = maxName + ' - ' + minName + ', 価格差:' + str(maxp - minp) + '円'
        print(sbj)
        # 指定価格差が開いていたらメール通知
        if Price_Diff_To_Alert < maxp - minp:
            os.system('py mail.py \"yahoo\" \"' + Mail_To + '\" \"' + sbj + '\" \"' + msg + '\"')


        # 指定時間スリープ
        sleep(Monitor_Period * 60)
