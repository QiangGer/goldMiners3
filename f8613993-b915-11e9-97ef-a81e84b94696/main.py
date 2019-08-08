# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals
from gm.api import *


# 这是获取股票开盘价的逻辑
# 应该写成接口给做t使用

def init(context):
    subscribe(symbols='SZSE.300115', frequency='1d', count=15)
    # subscribe(symbols='SHSE.600410,SZSE.002945,SZSE.002512,SHSE.600171,SZSE.002384,SZSE.300115,SZSE.000563,SZSE.002093,SHSE.600536', frequency='1d', count=5, wait_group=True)


def on_bar(context, bars):
    for bar in bars:
        print(bar['symbol'], bar['eob'], bar['open'])
    # print(bars)


if __name__ == '__main__':
    run(strategy_id='strategy_1', filename='main.py', mode=MODE_BACKTEST, token='token_id',
        backtest_start_time='2019-01-02 08:00:00', backtest_end_time='2019-01-02 16:00:00')
