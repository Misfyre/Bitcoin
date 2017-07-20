__author__ = 'Nick Sarris (ngs5st)'

from API.bittrex_api import *

class CryptoBot():

    def __init__(self, key, secret):
        self.api = bittrex(key, secret)

    def single_buy(self, token):
        self.pair = 'BTC-' + token

        btc_balance = self.api.getbalance('BTC')['Balance']
        current_price = self.api.getticker(self.pair)
        trade_price = round(current_price['Last'] * 1.05, 8)
        trade_quantity = round(btc_balance * 0.99 /
                               trade_price, 8)

        print('Setting Orders: {} | {} | {}'.format(
            self.pair, trade_quantity, trade_price))

        self.api.buylimit(market=self.pair, quantity=trade_quantity, rate=trade_price)

if __name__ == '__main__':

    while True:
        token = input('Which Token?: ')
        CryptoBot('8fb004f8f3114b56b06a3d7ec9ede2f2',
                  'b17ca98186cf4f1db07766918b9b9837',
                  ).single_buy(token)