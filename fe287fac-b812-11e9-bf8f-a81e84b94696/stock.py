# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals

try:
    import talib
except:
    print('请安装TA-Lib库')
from gm.api import *

# 由于run函数封闭问题，须添加环境变量用于遗传算法
result = 0
fastperiod = 12
slowperiod = 26
signalperiod = 9

'''
遗传算法优化macd参数
用于单只股票的日内回转
'''


def init(context):
    # 设置标的股票
    context.symbol = 'SHSE.002401'
    # 用于判定第一个仓位是否成功开仓
    context.first = 0
    # 订阅该股票, bar频率为5min
    subscribe(symbols=context.symbol, frequency='300s', count=35)
    # 日内回转每次交易1000股
    context.trade_n = 1000
    # 获取昨今天的时间，格式为[今天，昨天]，这里和股票组合的不一样，那一个我改过了
    context.day = [0, 0]
    # 用于判断是否触发了回转逻辑的计时
    context.ending = 0

    # 绑定环境变量到context
    context.slowperiod = slowperiod
    context.fastperiod = fastperiod
    context.signalperiod = signalperiod


def on_bar(context, bars):
    bar = bars[0]
    if context.first == 0:
        # 最开始配置仓位
        # 需要保持的总仓位
        context.total = 10000
        # 购买10000股浦发银行股票
        order_volume(symbol=context.symbol, volume=context.total, side=PositionSide_Long,
                     order_type=OrderType_Market, position_effect=PositionEffect_Open)
        # print(context.symbol, '以市价单开多仓10000股')
        context.first = 1.
        day = bar.bob.strftime('%Y-%m-%d')
        context.day[-1] = day[-2:]
        # 每天的仓位操作
        context.turnaround = [0, 0]
        return

    # 更新最新的日期
    day = bar.bob.strftime('%Y-%m-%d %H:%M:%S')
    context.day[0] = bar.bob.day
    # 若为新的一天,获取可用于回转的昨仓
    if context.day[0] != context.day[-1]:
        context.ending = 0
        context.turnaround = [0, 0]
    if context.ending == 1:
        return

    # 若有可用的昨仓则操作
    if context.total >= 0:
        # 获取时间序列数据
        symbol = bar['symbol']
        recent_data = context.data(symbol=symbol, frequency='300s', count=35, fields='close')

        # 计算MACD线
        # DIF组成的线叫做MACD线，DEA组成的线叫做Signal线，DIFF减DEA，得Hist
        macd, signal, hist = talib.MACD(recent_data['close'].values, context.fastperiod, context.slowperiod,
                                        context.signalperiod)
        ma_5 = talib.MA(recent_data['close'].values, 5)
        ma_20 = talib.MA(recent_data['close'].values, 20)

        # 根据一定的规则买入
        if macd[-1] < 0 and signal[-1] < 0 and macd[-2] < signal[-2] and macd[-1] > signal[-1] and ma_5[-1] > ma_20[-1]:
            # 多空单向操作都不能超过昨仓位,否则最后无法调回原仓位
            if context.turnaround[0] + context.trade_n < context.total:
                # 计算累计仓位
                context.turnaround[0] += context.trade_n
                order_volume(symbol=context.symbol, volume=context.trade_n, side=PositionSide_Long,
                             order_type=OrderType_Market, position_effect=PositionEffect_Open)
                # print(symbol, '市价单开多仓', context.trade_n, '股')
        # 卖出也有规则
        elif macd[-1] > 0 and signal[-1] > 0 and macd[-2] > signal[-2] and macd[-1] < signal[-1] or ma_5[-1] < ma_20[
            -1]:
            if context.turnaround[1] + context.trade_n < context.total:
                context.turnaround[1] += context.trade_n
                order_volume(symbol=context.symbol, volume=context.trade_n, side=PositionSide_Short,
                             order_type=OrderType_Market, position_effect=PositionEffect_Close)
                # print(symbol, '市价单平多仓', context.trade_n, '股')
        # 临近收盘时若仓位数不等于昨仓则回转所有仓位
        if day[11:16] == '14:55' or day[11:16] == '14:57':
            position = context.account().position(symbol=context.symbol, side=PositionSide_Long)
            if position['volume'] != context.total:
                order_target_volume(symbol=context.symbol, volume=context.total, order_type=OrderType_Market,
                                    position_side=PositionSide_Long)
                # print(context.now,'市价单回转仓位操作...')
                context.ending = 1
        # 更新过去的日期数据
        context.day[-1] = context.day[0]


def main(Fastperiod, Slowperiod, Signalperiod):
    global fastperiod
    global slowperiod
    global signalperiod

    # main函数接收外部传来的值，用于遗传算法修改macd参数
    fastperiod = Fastperiod
    slowperiod = Slowperiod
    signalperiod = Signalperiod

    run(strategy_id='17a0ab6c-33e7-11e8-bdb0-00ffe31f5606',
        filename='stock.py',
        mode=MODE_BACKTEST,
        token='b8a7db2f3f7632c1000ef9a845146be81641b101',
        backtest_start_time='2019-01-01 08:00:00',
        backtest_end_time='2019-06-01 15:00:00',
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
