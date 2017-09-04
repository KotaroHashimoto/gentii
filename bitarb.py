#!/usr/bin/env python3

from json import load
from datetime import datetime
from threading import Thread
from time import sleep
from oandapy import API
import datetime as dt
import ssl
from sys import version_info, exit

if version_info.major == 2 and version_info.minor == 7:
    from urllib2 import urlopen, Request
    from Tkinter import *
elif version_info.major == 3 and version_info.minor == 6:
    from urllib.request import urlopen, Request
    from tkinter import *
else:
    print('Please install python2.7.x or python3.6.x')
    exit(1)


class Window(Thread):

    PERIOD = 1.5
    FONT = 'Arial'
    FSIZE = 12

    def __init__(self, title):
        Thread.__init__(self)
    
        self.root = Tk()
        self.root.title(title)

        self.str = StringVar()
        self.str.set('')
        Label(self.root, textvariable = self.str, font = (Window.FONT, Window.FSIZE)).pack()

        Label(text = 'Exchange' + (' '*8) + '\tLast\tAsk\tBid', font = (Window.FONT, Window.FSIZE)).pack()
        
        self.root.bind('<MouseWheel>', self.onMouseWheel)
        self.root.bind('<Up>', self.expand)
        self.root.bind('<Right>', self.expand)
        self.root.bind('<Down>', self.shrink)
        self.root.bind('<Left>', self.shrink)

    def run(self):
    
        while True:
            try:
                self.str.set(datetime.now().strftime('%Y/%m/%d  %H:%M:%S'))
                sleep(Window.PERIOD)

            except:
                sleep(10)
                continue

    def update(self, delta):
    
        Window.FSIZE = Window.FSIZE + delta
    
        for widget in self.root.children.values():
            widget.configure(font = (Window.FONT, Window.FSIZE))

    def onMouseWheel(self, mouseEvent):
        self.update(1 if 0 < mouseEvent.delta else -1)

    def expand(self, keyEvent):
        self.update(1)

    def shrink(self, keyEvent):
        self.update(-1)


class OANDA(Thread):

    PRICE = {'USD_JPY':1} #, 'EUR_JPY':1, 'GBP_JPY':1, 'CNY_JPY':1, 'USD_CNY':1}
    
    def __init__(self, root, symbol, display = True):
        Thread.__init__(self)
        
        if symbol == 'USD_JPY':
            Label(root).pack()

        self.lstr = StringVar()
        self.lstr.set('')
        self.label = Label(root, textvariable = self.lstr, font = (Window.FONT, Window.FSIZE))

        if display:
            self.label.pack()

        self.symbol = symbol

        self.oanda = API(environment='practice', access_token='f80296b600eddebbb0402eeabce34139-55d481314b19c1127978ecd05c9dca65')

    def run(self):

        while True:
            try:
                prices = self.oanda.get_prices(instruments = self.symbol).get('prices')

                up = (prices[0].get('ask') + prices[0].get('bid')) / 2.0
                self.label.configure(fg = ('black' if OANDA.PRICE[self.symbol] == up else ('red' if OANDA.PRICE[self.symbol] > up else 'green')))
                OANDA.PRICE[self.symbol] = up
            
                if 'CNY_JPY' == self.symbol:
                    ask = str(int(1000 * prices[0].get('ask')))
                    bid = str(int(1000 * prices[0].get('bid')))
                    self.lstr.set(self.symbol.replace('_', '/') + ':  \t\t ' + ask[:2] + '.' + ask[2:] + '\t ' + bid[:2] + '.' + bid[2:])
                elif 'USD_CNY' == self.symbol:
                    ask = str(int(10000 * prices[0].get('ask')))
                    bid = str(int(10000 * prices[0].get('bid')))
                    self.lstr.set(self.symbol.replace('_', '/') + ':  \t\t ' + ask[:1] + '.' + ask[1:] + '\t ' + bid[:1] + '.' + bid[1:])
                else:
                    ask = str(int(1000 * prices[0].get('ask')))
                    bid = str(int(1000 * prices[0].get('bid')))
                    self.lstr.set(self.symbol.replace('_', '/') + ':  \t\t' + ask[:3] + '.' + ask[3:] + '\t' + bid[:3] + '.' + bid[3:])

            except:
                self.label.configure(fg = 'gray')
                sleep(10)
                self.label.configure(fg = 'black')
                continue


class Exchange(Thread):

    def __init__(self, root, name, url, last, sask, sbid):
        Thread.__init__(self)
    
        self.name = name
        self.url = url
        self.last = last
        self.sask = sask
        self.sbid = sbid

        self.str = StringVar()
        self.str.set('')
        self.label = Label(root, textvariable = self.str, font = (Window.FONT, Window.FSIZE))
        self.label.pack()

        self.ask = 0
        self.bid = 0
        self.p = 0

    def run(self):

        while True:
            try:
                data = load(urlopen(Request(self.url, headers = {'User-Agent':'Hoge Browser'})))

                self.ask = int(data[self.sask])
                self.bid = int(data[self.sbid])
        
                up = int(data[self.last])
                self.label.configure(fg = ('black' if self.p == up else ('red' if self.p > up else 'green')))
                self.p = up
        
                a = str(self.ask)
                b = str(self.bid)
                l = str(self.p)
                
                self.str.set(self.name + (' ' * (20 - len(self.name))) + '\t' + l[:3] + ',' + l[3:] + '\t' +  a[:3] + ',' + a[3:] + '\t' +  b[:3] + ',' + b[3:])
                sleep(Window.PERIOD)

            except Exception as e:
                print('Exchange ', e, ', ', self.name)
                self.label.configure(fg = 'gray')
                sleep(10)
                self.label.configure(fg = 'black')
                continue


class ForExchange(Exchange):

    def __init__(self, root, name, url, last, sask, sbid):    
        if name == 'Quoine USD':
            Label(root).pack()

        Exchange.__init__(self, root, name, url, last, sask, sbid)

        self.rask = 0
        self.rbid = 0
        self.rp = 0
        
        if 'Houbi' == self.name or 'BTCC' == self.name or 'OKCoinCN' == self.name:
            self.base = 'CNY_JPY'
        else:
            self.base = 'USD_JPY'

    def run(self):
    
        while True:
            try:
                if self.name == 'coinbase':
                    data = {}
                    data[self.last] = load(urlopen(Request(self.url + self.last, headers = {'User-Agent':'Hoge Browser'})))['data']['amount']
                    data[self.sask] = load(urlopen(Request(self.url + self.sask, headers = {'User-Agent':'Hoge Browser'})))['data']['amount']
                    data[self.sbid] = load(urlopen(Request(self.url + self.sbid, headers = {'User-Agent':'Hoge Browser'})))['data']['amount']
                else:
                    data = load(urlopen(Request(self.url, headers = {'User-Agent':'Hoge Browser'})))

                if self.name == 'BTC-e':
                    data = data['btc_usd']
                elif self.name == 'Poloniex':
                    XemExchange.POLOXEMBTC = data['BTC_XEM']
                    data = data['USDT_BTC']
                elif 'OKCoin' in self.name or 'Houbi' == self.name or 'BTCC' == self.name :
                    data = data['ticker']
                elif self.name == 'Kraken':
                    data = data['result']['XXBTZUSD']

                if self.name == 'Kraken':
                    self.rask = float(data[self.sask][0])
                    self.rbid = float(data[self.sbid][0])
                    self.rp = float(data[self.last][0])
                else:
                    self.rask = float(data[self.sask])
                    self.rbid = float(data[self.sbid])
                    self.rp = float(data[self.last])

                self.ask = self.rask * OANDA.PRICE[self.base]
                self.bid = self.rbid * OANDA.PRICE[self.base]
                up = self.rp * OANDA.PRICE[self.base]

                self.label.configure(fg = ('black' if self.p == up else ('red' if self.p > up else 'green')))
                self.p = up

                a = str(round(self.ask))
                b = str(round(self.bid))
                l = str(round(self.p))

                self.str.set(self.name + (' ' * (20 - len(self.name))) + '\t' + l[:3] + ',' + l[3:] + '\t' +  a[:3] + ',' + a[3:] + '\t' +  b[:3] + ',' + b[3:])
                sleep(Window.PERIOD)

            except:
                self.label.configure(fg = 'gray')
                sleep(10)
                self.label.configure(fg = 'black')
                continue


if __name__ == '__main__':

    ssl._create_default_https_context = ssl._create_unverified_context

    window = Window('BTC/JPY Live Price')

    base = [ \
#        Future(window.root, 'bF Future This Week', 'https://api.bitflyer.jp/v1/getticker?product_code=BTCJPY', 'ltp', 'best_ask', 'best_bid', 1), \
#        Future(window.root, 'bF Future Next Week', 'https://api.bitflyer.jp/v1/getticker?product_code=BTCJPY', 'ltp', 'best_ask', 'best_bid', 2), \
#        Exchange(window.root, 'bitFlyer FX', 'https://api.bitflyer.jp/v1/getticker?product_code=FX_BTC_JPY', 'ltp', 'best_ask', 'best_bid'), \
        Exchange(window.root, 'bitFlyer', 'https://api.bitflyer.jp/v1/getticker?product_code=BTC_JPY', 'ltp', 'best_ask', 'best_bid'), \
        Exchange(window.root, 'BtcBox', 'https://www.btcbox.co.jp/api/v1/ticker/', 'last', 'sell', 'buy'), \
        Exchange(window.root, 'Zaif', 'https://api.zaif.jp/api/1/ticker/btc_jpy', 'last', 'ask', 'bid'), \
        Exchange(window.root, 'coincheck', 'https://coincheck.com/api/ticker', 'last', 'ask', 'bid'), \
        Exchange(window.root, 'Quoine JPY', 'https://api.quoine.com/products/5', 'last_traded_price', 'market_ask', 'market_bid'), \
        ]

    foreign = [ \
        ForExchange(window.root, 'Quoine USD', 'https://api.quoine.com/products/1', 'last_traded_price', 'market_ask', 'market_bid'), \
        ForExchange(window.root, 'Poloniex', 'https://poloniex.com/public?command=returnTicker', 'last', 'lowestAsk', 'highestBid'), \
        ForExchange(window.root, 'Kraken', 'https://api.kraken.com/0/public/Ticker?pair=XBTUSD', 'c', 'a', 'b'), \
        ForExchange(window.root, 'Bitstamp', 'https://www.bitstamp.net/api/v2/ticker/btcusd/', 'last', 'ask', 'bid'), \
        ForExchange(window.root, 'Bitfinex', 'https://api.bitfinex.com/v1/pubticker/BTCUSD', 'last_price', 'ask', 'bid'), \
        ForExchange(window.root, 'GDAX', 'https://api.gdax.com/products/BTC-USD/ticker', 'price', 'ask', 'bid'), \
        ForExchange(window.root, 'coinbase', 'https://api.coinbase.com/v2/prices/BTC-USD/', 'spot', 'buy', 'sell'), \
        ForExchange(window.root, 'BTC-e', 'https://btc-e.com/api/3/ticker/btc_usd', 'last', 'buy', 'sell'), \
        ForExchange(window.root, 'OKCoinCOM', 'https://www.okcoin.com/api/v1/ticker.do?symbol=btc_usd', 'last', 'sell', 'buy'), \
#        ForExchange(window.root, 'OKCoin this wk', 'https://www.okcoin.com/api/v1/future_ticker.do?symbol=btc_usd&contract_type=this_week', 'last', 'sell', 'buy'), \
#        ForExchange(window.root, 'OKCoin next wk', 'https://www.okcoin.com/api/v1/future_ticker.do?symbol=btc_usd&contract_type=next_week', 'last', 'sell', 'buy'), \
#        ForExchange(window.root, 'OKCoin quarter', 'https://www.okcoin.com/api/v1/future_ticker.do?symbol=btc_usd&contract_type=quarter', 'last', 'sell', 'buy'), \
#        ForExchange(window.root, 'Houbi', 'http://api.huobi.com/staticmarket/ticker_btc_json.js', 'last', 'sell', 'buy'), \
#        ForExchange(window.root, 'BTCC', 'https://pro-data.btcc.com/data/pro/ticker?symbol=XBTCNY', 'Last', 'AskPrice', 'BidPrice'), \
#        ForExchange(window.root, 'OKCoinCN', 'https://www.okcoin.cn/api/v1/ticker.do?symbol=btc_usd', 'last', 'sell', 'buy'), \
        ]

    oanda = [OANDA(window.root, currencyPair) for currencyPair in OANDA.PRICE.keys()] #この行の先頭の#を外すと為替レート表示
#    oanda = [OANDA(window.root, currencyPair, False) for currencyPair in OANDA.PRICE.keys()] #この行の先頭の#を外すと為替レート非表示

    exchangeList = tuple([window] + base + foreign + oanda)

    for e in exchangeList:
        e.setDaemon(True)
        e.start()

    window.root.mainloop()
