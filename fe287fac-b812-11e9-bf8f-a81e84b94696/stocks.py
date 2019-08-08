# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals

try:
    import talib
except:
    print('请安装TA-Lib库')
from gm.api import *

'''
    不再多写注释，需要的去参考没有封装成遗传算法函数的工程
'''


# 由于run函数封闭问题，须添加环境变量用于遗传算法
result = 0
fastperiod = 12
slowperiod = 26
signalperiod = 9

stocks = ['SHSE.600410', 'SZSE.002945', 'SZSE.002512', 'SHSE.600171', 'SZSE.002384', 'SZSE.300115', 'SZSE.000563',
          'SZSE.002093', 'SHSE.600536']
value = [5.949999809, 9.22, 5.309999943, 9.31000042, 11.30000019, 8.210000038, 2.700000048, 7.340000153, 20.94000053]
percents = [0.120598277, 0.103147739, 0.120661155, 0.109094458, 0.094569491, 0.102509434, 0.116582871, 0.108237585,
            0.12459899]


def init(context):
    context.first = [0 for i in range(len(stocks))]

    subscribe(symbols=['SHSE.600410', 'SZSE.002945', 'SZSE.002512', 'SHSE.600171', 'SZSE.002384', 'SZSE.300115',
                       'SZSE.000563', 'SZSE.002093', 'SHSE.600536'], frequency='300s', count=35 * 9, wait_group=True)

    context.trade_n = [2000, 1000, 2000, 1000, 800, 1200, 4000, 1400, 500]

    context.day = [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]

    context.ending = [1 for i in range(len(stocks))]

    context.turnaround = [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]

    context.total = [10100, 5500, 11300, 5800, 4100, 6200, 21500, 7300, 2900]

    # 绑定环境变量到context
    context.slowperiod = slowperiod
    context.fastperiod = fastperiod
    context.signalperiod = signalperiod


def on_bar(context, bars):
    for bar in bars:
        context.symbol = bar['symbol']
        if context.first[stocks.index(context.symbol)] == 0:
            order_volume(symbol=context.symbol, volume=context.total[stocks.index(context.symbol)],
                         side=PositionSide_Long,
                         order_type=OrderType_Market, position_effect=PositionEffect_Open)
            # print(context.now,context.symbol, '以市价单开多仓',context.total[stocks.index(context.symbol)],'股')
            context.first[stocks.index(context.symbol)] = 1.
            context.day[stocks.index(context.symbol)][-1] = bar.bob.day
            context.day[stocks.index(context.symbol)][0] = bar.bob.day

        day = bar.bob.strftime('%Y-%m-%d %H:%M:%S')
        context.day[stocks.index(context.symbol)][-1] = bar.bob.day

        # 若为新的一天,获取可用于回转的昨仓
        if str(context.day[stocks.index(context.symbol)][-1]) != str(context.day[stocks.index(context.symbol)][0]):
            context.ending[stocks.index(context.symbol)] = 0
            context.turnaround[stocks.index(context.symbol)] = [0, 0]

        # 若有可用的昨仓则操作
        if context.total[stocks.index(context.symbol)] >= 0 and str(
                context.ending[stocks.index(context.symbol)]) == str(0):
            # 获取时间序列数据
            symbol = context.symbol

            recent_data = context.data(symbol=symbol, frequency='300s', count=35, fields='close')
            # 计算MACD线
            macd, signal, hist = talib.MACD(recent_data['close'].values, context.fastperiod, context.slowperiod,
                                            context.signalperiod)
            ma_5 = talib.MA(recent_data['close'].values, 5)
            ma_20 = talib.MA(recent_data['close'].values, 10)

            if macd[-1] < 0 and signal[-1] < 0 and macd[-2] < signal[-2] and macd[-1] > signal[-1] and ma_5[-1] > ma_20[
                -1]:

                # 多空单向操作都不能超过昨仓位,否则最后无法调回原仓位
                if context.turnaround[stocks.index(context.symbol)][0] + context.trade_n[stocks.index(context.symbol)] < \
                        context.total[stocks.index(context.symbol)]:
                    # 计算累计仓位
                    context.turnaround[stocks.index(context.symbol)][0] += context.trade_n[stocks.index(context.symbol)]
                    order_volume(symbol=context.symbol, volume=context.trade_n[stocks.index(context.symbol)],
                                 side=PositionSide_Long,
                                 order_type=OrderType_Market, position_effect=PositionEffect_Open)
                    # print(context.now,symbol, '市价单开多仓', context.trade_n[stocks.index(context.symbol)], '股')

            elif macd[-1] > 0 and signal[-1] > 0 and macd[-2] > signal[-2] and macd[-1] < signal[-1] or ma_5[-1] < \
                    ma_20[-1]:

                if context.turnaround[stocks.index(context.symbol)][1] + context.trade_n[stocks.index(context.symbol)] < \
                        context.total[stocks.index(context.symbol)]:
                    context.turnaround[stocks.index(context.symbol)][1] += context.trade_n[stocks.index(context.symbol)]
                    order_volume(symbol=context.symbol, volume=context.trade_n[stocks.index(context.symbol)],
                                 side=PositionSide_Short,
                                 order_type=OrderType_Market, position_effect=PositionEffect_Close)
                    # print(context.now,symbol, '市价单平多仓', context.trade_n[stocks.index(context.symbol)], '股')

            # 临近收盘时若仓位数不等于昨仓则回转所有仓位
            if day[11:16] == '14:55' or day[11:16] == '14:57':
                position = context.account().position(symbol=context.symbol, side=PositionSide_Long)
                if position['volume'] != context.total[stocks.index(context.symbol)]:
                    order_target_volume(symbol=context.symbol, volume=context.total[stocks.index(context.symbol)],
                                        order_type=OrderType_Market, position_side=PositionSide_Long)
                    # print(context.now,context.symbol,'市价单回转仓位操作...')
                    context.ending[stocks.index(context.symbol)] = 1
            # 更新过去的日期数据
            context.day[stocks.index(context.symbol)][0] = context.day[stocks.index(context.symbol)][-1]


def main(Fastperiod, Slowperiod, Signalperiod):
    global fastperiod
    global slowperiod
    global signalperiod

    # main函数接收外部传来的值，用于遗传算法修改macd参数
    fastperiod = Fastperiod
    slowperiod = Slowperiod
    signalperiod = Signalperiod

    run(strategy_id='17a0ab6c-33e7-11e8-bdb0-00ffe31f5606',
        filename='stocks.py',
        mode=MODE_BACKTEST,
        token='{{token}}',
        backtest_start_time='2019-01-01 08:00:00',
        backtest_end_time='2019-08-01 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=500000,
        backtest_commission_ratio=0.0003,
        backtest_slippage_ratio=0.0001)
    return result


def on_backtest_finished(context, indicator):
    global result
    result = context.account().cash.pnl


if __name__ == '__main__':
    '''
    strategy_id策略ID,由系统生成
    filename文件名,请与本文件名保持一致
    mode实时模式:MODE_LIVE回测模式:MODE_BACKTEST
    token绑定计算机的ID,可在系统设置-密钥管理中生成
    backtest_start_time回测开始时间
    backtest_end_time回测结束时间
    backtest_adjust股票复权方式不复权:ADJUST_NONE前复权:ADJUST_PREV后复权:ADJUST_POST
    backtest_initial_cash回测初始资金
    backtest_commission_ratio回测佣金比例
    backtest_slippage_ratio回测滑点比例
    '''
    main()
