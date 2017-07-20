__author__ = 'Nick Sarris (ngs5st)'

import datetime
import hashlib
import hmac
import json
import time

import urllib.parse
import urllib.request
from Scripts.functions import *

import pandas as pd
import requests

class Market:

    public_api_url = ''
    pairs = []
    allowed_periods = []

    def __init__(self): pass
    def get_historical_data(self, pair, start, end, period): pass
    def get_orderbook(self, pair, depth): pass
    def get_trade_history(self, pair, start, end): pass
    def get_ticker(self): pass

class MarketError(Exception):

    def __init__(self, message):
        Exception.__init__(self, message)

class PoloniexMarket(Market):

    public_api_url = "https://poloniex.com/public?command="
    trading_api_url = "https://poloniex.com/tradingApi"
    allowed_periods = [300, 900, 1800, 7200, 14400, 86400]
    pairs = """BTC_LSK BTC_ETH BTC_LTC BTC_DAO BTC_MAID BTC_FCT USDT_BTC BTC_DASH 
               BTC_SJCX BTC_XMR USDT_ETH BTC_SC BTC_VOX BTC_XRP BTC_BTS BTC_DOGE 
               BTC_AMP BTC_DGB BTC_NBT BTC_SYS BTC_XEM BTC_EXP BTC_STR BTC_DCR BTC_NXT 
               USDT_LTC BTC_XVC BTC_XCP BTC_CLAM BTC_RADS BTC_BLK BTC_QORA BTC_BTCD 
               BTC_RDD BTC_RBY USDT_DASH BTC_C2 BTC_NSR BTC_VRC BTC_SDC BTC_GAME 
               BTC_BCN BTC_VTC BTC_PPC BTC_DIEM BTC_NAUT BTC_IOC BTC_FLO BTC_BCY 
               BTC_GEMZ XMR_MAID BTC_MINT BTC_BURST BTC_SWARM XMR_LTC USDT_NXT 
               BTC_BBR BTC_EMC2 BTC_XMG USDT_XMR BTC_EXE XMR_DASH BTC_XDN BTC_XUSD 
               BTC_SILK BTC_GRC""".split(' ')

    def __init__(self, api_key='', secret='', kraken_withdrawl_address=''):
        Market.__init__(self)
        self.api_key = api_key
        self.secret = secret
        self.kraken_withdrawl_address = kraken_withdrawl_address
        self.nonce = datetime_to_timestamp(datetime.datetime.now())

    def get_historical_data(self, pair, start, end=None, period=1800):
        if period not in PoloniexMarket.allowed_periods:
            raise MarketError("Not allowed periods. Allowed periods are %s" % PoloniexMarket.allowed_periods)
        if end is None or end < start or type(end) is not int:
            end = 9999999999
        url = "%sreturnChartData&currencyPair=%s&start=%s&end=%s&period=%s" % (PoloniexMarket.public_api_url, pair, start, end, period)
        r = requests.get(url)
        result = json.loads(r.text)
        columns = ['high', 'low', 'open', 'close', 'volume', 'quoteVolume', 'weightedAverage']
        data = [[d['high'], d['low'], d['open'], d['close'], d['volume'], d['quoteVolume'], d['weightedAverage']] for d in result]
        return pd.DataFrame(data=data, index=[timestamp_to_datetime(d['date']) for d in result], columns=columns)

    def get_orderbook(self, pair, depth):
        if pair not in PoloniexMarket.pairs:
            raise MarketError("This pair doesn't exist")
        url = "%sreturnOrderBook&currencyPair=%s&depth=%s" % (PoloniexMarket.public_api_url, pair, depth)
        r = requests.get(url)
        result = json.loads(r.text)
        return {'seq': result['seq'],
                'isFrozen': int(result['isFrozen']),
                'bids': [[float(bid[0]), float(bid[1])] for bid in result['bids']],
                'asks': [[float(ask[0]), float(ask[1])] for ask in result['asks']]
                }

    def get_trade_history(self, pair, start, end=None):
        if pair not in PoloniexMarket.pairs:
            raise MarketError("This pair doesn't exist")
        if end is None or end < start or type(end) not in [int]:
            end = 9999999999
        url = "%sreturnTradeHistory&currencyPair=%s&start=%s&end=%s" % (PoloniexMarket.public_api_url, pair, start, end)
        r = requests.get(url)
        result = json.loads(r.text)
        columns = ['type', 'rate', 'amount', 'total']
        data = [[d['type'], d['rate'], d['amount'], d['total']] for d in result]
        return pd.DataFrame(data=data, columns=columns, index=[datestring_to_datetime(d['date']) for d in result])

    def get_ticker(self):
        url = "%sreturnTicker" % PoloniexMarket.public_api_url
        r = requests.get(url)
        result = json.loads(r.text)
        columns = ['last', 'lowestAsk', 'highestBid', 'percentChange', 'baseVolume', 'quoteVolume']
        data = [[float(result[key]['last']), float(result[key]['lowestAsk']), float(result[key]['highestBid']), float(result[key]['percentChange']), float(result[key]['baseVolume']), float(result[key]['quoteVolume'])] for key in sorted(result.keys())]
        return pd.DataFrame(data=data, columns=columns, index=sorted(result.keys()))

    @staticmethod
    def wallet_to_csv(typical_prices, btc, eth, now, file_name, prediction, last_prediction, is_first_time):
        """
        :param now: the date at which you add data
        :param typical_prices: the list of the last typical prices
        :param btc: the total amount of bitcoins you hava at that time (before buying/selling)
        :param eth: idem but for ethereum
        :param file_name: the filename in which you want to write
        :param prediction: your prediction (1 or -1)
        :param last_prediction: your last prediction (1 or -1)
        :param is_first_time: is it the first time you run the loop ?
        :return: VOID. Write into to file. Doesn't overwritte but append text
        """
        with open(file_name, 'a') as f:
            # if not is_first_time:
            #     f.write(np.sign((typical_prices[-1] - typical_prices[-2])*last_prediction))
            #     print 'was it a good choice : %s' % str((typical_prices[-1] - typical_prices[-2])*last_prediction)
            #     f.write('\n')
            f.write(now.isoformat())
            f.write(';')
            f.write(str(typical_prices[-1]))
            f.write(';')
            f.write(str(btc))
            f.write(';')
            f.write(str(eth))
            f.write(';')
            btc_amount = float(btc) + float(eth)*(typical_prices[-1])
            f.write(str(btc_amount))
            f.write(';')
            f.write(str(prediction))
            f.write(';')
            f.write('\n')

    def _api_query(self, nonce, command, **kwargs):
        """
        a general function to be used to query the poloniex trading api
        :param nonce:
        :param command:
        :param kwargs:
        :return:
        """
        data = {'nonce': nonce, 'command': command}
        for key in kwargs:
            data[key] = kwargs[key]
        sign = hmac.new(self.secret, urllib.parse.urlencode(data), hashlib.sha512).hexdigest()
        headers = {'Key': self.api_key, 'Sign': sign}
        ret = urllib.request.urlopen(urllib.request.Request('https://poloniex.com/tradingApi',
                                     urllib.parse.urlencode(data), headers))
        jsonRet = json.loads(ret.read())
        return jsonRet

    def _nonce(self):
        now = datetime_to_timestamp(datetime.datetime.now())
        if now > self.nonce:
            self.nonce = now
            return now
        else:
            self.nonce += 1
            return self.nonce

    def balances(self):
        """
        :return: a dict giving all your cryptocurrencies amounts
        """
        return self._api_query(self._nonce(), "returnBalances")

    def complete_balances(self):
        """
        :return: a dict giving all your cryptomonnaies amounts, with the btc value and what's on order
        """
        return self._api_query(self._nonce(), "returnCompleteBalances")

    def my_open_orders(self, pair):
        """
        :param pair: can be all. Or one of the elements of PoloniexMarket.pairs
        :return: a list of dict giving your open orders at the current time
        """
        kwargs = {'currencyPair': pair}
        return self._api_query(self._nonce(), "returnOpenOrders", **kwargs)

    def buy(self, pair, rate, amount, fill_or_kill=0, immediate_or_cancel=0, post_only=0):
        """
        places a limit buy order in a given market
        :param post_only: 0 or 1. 1 if no portion of it fills immediately; this guarantees you will never pay the taker fee on any part of the order that fills.
        :param immediate_or_cancel: 0 or 1. 1 if it can be partially or completely filled, but any portion of the order that cannot be filled immediately will be canceled rather than left on the order book.
        :param fill_or_kill: 0 or 1. 1 if it will either fill in its entirety or be completely aborted.
        :param pair: an element of PoloniexMarket.pairs
        :param rate: the price
        :param amount: how much you want to buy
        :return:
        """
        kwargs = {"currencyPair": pair,
                  "rate": rate,
                  "amount": amount,
                  "fillOrKill": fill_or_kill,
                  "immediateOrCancel": immediate_or_cancel,
                  "postOnly": post_only
                  }
        return self._api_query(self._nonce(), "buy", **kwargs)

    def sell(self, pair, rate, amount, fill_or_kill=0, immediate_or_cancel=0, post_only=0):
        """
        places a limit buy order in a given market
        :param post_only: 0 or 1. 1 if no portion of it fills immediately; this guarantees you will never pay the taker fee on any part of the order that fills.
        :param immediate_or_cancel: 0 or 1. 1 if it can be partially or completely filled, but any portion of the order that cannot be filled immediately will be canceled rather than left on the order book.
        :param fill_or_kill: 0 or 1. 1 if it will either fill in its entirety or be completely aborted.
        :param pair: an element of PoloniexMarket.pairs
        :param rate: the price
        :param amount: how much you want to buy
        :return:
        """
        kwargs = {"currencyPair": pair,
                  "rate": rate,
                  "amount": amount,
                  "fillOrKill": fill_or_kill,
                  "immediateOrCancel": immediate_or_cancel,
                  "postOnly": post_only
                  }
        return self._api_query(self._nonce(), "sell", **kwargs)

    def cancel_order(self, order_number):
        """
        :param order_number:
        :return:
        """
        kwargs = {"orderNumber": order_number}
        return self._api_query(self._nonce(), "cancelOrder", **kwargs)

    def withdraw(self, currency, amount, address=None):
        if address is None:
            address = self.kraken_withdrawl_address
        kwargs = {"currency": currency, "amount": amount, "address": address}
        return self._api_query(self._nonce(), "withdraw", **kwargs)
