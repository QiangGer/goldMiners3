# coding=utf-8
from __future__ import print_function, absolute_import, unicode_literals

try:
    import talib
except:
    print('请安装TA-Lib库')
from gm.api import *

'''
本文件写于2019年8月hdu数学建模期间
掘金量化3平台的日内回转交易模型
回测投资组合stocks的工程文件

收盘平仓逻辑的position获取可能存在问题，有的时间段会获取不到部分股票的数据，猜测和股票涨停有关或者是官方bug也可能是代码逻辑问题，不过多考虑。
'''

# 这是投资组合的股票成员们
stocks = ['SHSE.600410', 'SZSE.002945', 'SZSE.002512', 'SHSE.600171', 'SZSE.002384', 'SZSE.300115', 'SZSE.000563',
          'SZSE.002093', 'SHSE.600536']
# 这是股票成员们在回测第一条的开盘价，从另一个工程中获得
# 因为做题仓促，没有写接口自动获取，而是在另一工程中打印后从命令行中粘贴而来
value = [5.949999809, 9.22, 5.309999943, 9.31000042, 11.30000019, 8.210000038, 2.700000048, 7.340000153, 20.94000053]
# 这是股票成员们的投资比例，由队友通过数学方法获得
percents = [0.120598277, 0.103147739, 0.120661155, 0.109094458, 0.094569491, 0.102509434, 0.116582871, 0.108237585,
            0.12459899]


def init(context):
    # 设置股票的标
    # 股票的标就是股票的ID，应绑定在context的symbol属性上
    # 官方的文档给出了多个股票应绑定在sumbols上的说明，但操作起来好像有问题，遂放弃，转投全局变量
    # 股票投资组合的逻辑比较复杂，再结合看不了函数源码，为了应对题目写了以下大量的二维数组

    # context.symbol = 'SZSE.002945'

    # 用于判定第一个仓位是否成功开仓
    context.first = [0 for i in range(len(stocks))]

    # 订阅bar频率为5min
    # bar应该是每五分钟的一次行情，每次订阅成功后会执行on_bar函数
    # 参数count的具体含义不是很明白，似乎设置成多少都不会影响结果，没有深究
    # 注意wait_group参数，当时没看文档，被搞得很惨
    subscribe(symbols=['SHSE.600410', 'SZSE.002945', 'SZSE.002512', 'SHSE.600171', 'SZSE.002384', 'SZSE.300115',
                       'SZSE.000563', 'SZSE.002093', 'SHSE.600536'], frequency='300s', count=35 * 9, wait_group=True)
    # 日内回转每次操作的股票数量
    # 为持仓量的20%左右，手动输入的
    # 应该用数学表达式计算，但取整不是很方便，于是便电脑计算后人工取整，再手动输入
    context.trade_n = [2000, 1000, 2000, 1000, 800, 1200, 4000, 1400, 500]
    # 获取昨今天的时间，格式为[昨天，今天]
    context.day = [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]
    # 用于判断是否今天不能再去操作了
    context.ending = [1 for i in range(len(stocks))]

    # 这个是可以操作的仓位数量，一边买入，一边卖出
    context.turnaround = [[0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0], [0, 0]]

    # 这是股票的最大持仓量
    # 这是根据本金，投资比例和股票开盘价算出来的
    # 手动输入的理由同上
    context.total = [10100, 5500, 11300, 5800, 4100, 6200, 21500, 7300, 2900]


def on_bar(context, bars):
    for bar in bars:
        context.symbol = bar['symbol']
        if context.first[stocks.index(context.symbol)] == 0:
            # 最开始配置仓位
            # 需要保持的总仓位
            order_volume(symbol=context.symbol, volume=context.total[stocks.index(context.symbol)],
                         side=PositionSide_Long,
                         order_type=OrderType_Market, position_effect=PositionEffect_Open)
            print(context.now, context.symbol, '以市价单开多仓', context.total[stocks.index(context.symbol)], '股')
            context.first[stocks.index(context.symbol)] = 1.
            context.day[stocks.index(context.symbol)][-1] = bar.bob.day
            context.day[stocks.index(context.symbol)][0] = bar.bob.day

        # 更新最新的日期
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
            # DIF组成的线叫做MACD线，DEA组成的线叫做Signal线，DIFF减DEA，得Hist
            macd, signal, hist = talib.MACD(recent_data['close'].values)
            ma_5 = talib.MA(recent_data['close'].values, 5)
            ma_10 = talib.MA(recent_data['close'].values, 10)

            # 金叉，且均线齐头排列，买入
            if (macd[-2] < signal[-2] and macd[-1] > signal[-1] and ma_5[-1] > ma_10[
                -1]):  # macd[-1]<0 and signal[-1]<0 and

                # 多空单向操作都不能超过昨仓位,否则最后无法调回原仓位
                if context.turnaround[stocks.index(context.symbol)][0] + context.trade_n[stocks.index(context.symbol)] < \
                        context.total[stocks.index(context.symbol)]:
                    # 计算累计仓位
                    context.turnaround[stocks.index(context.symbol)][0] += context.trade_n[stocks.index(context.symbol)]
                    order_volume(symbol=context.symbol, volume=context.trade_n[stocks.index(context.symbol)],
                                 side=PositionSide_Long,
                                 order_type=OrderType_Market, position_effect=PositionEffect_Open)
                    print(context.now, symbol, '市价单开多仓', context.trade_n[stocks.index(context.symbol)], '股')
            # 死叉，或者，或者，或者均线空排下降，卖出
            elif macd[-1] > 0 and signal[-1] > 0 and macd[-2] > signal[-2] and macd[-1] < signal[-1] or ma_5[-1] < \
                    ma_10[-1]:
                # elif  macd[-2] > signal[-2] and macd[-1] < signal[-1]:
                if context.turnaround[stocks.index(context.symbol)][1] + context.trade_n[stocks.index(context.symbol)] < \
                        context.total[stocks.index(context.symbol)]:
                    context.turnaround[stocks.index(context.symbol)][1] += context.trade_n[stocks.index(context.symbol)]
                    order_volume(symbol=context.symbol, volume=context.trade_n[stocks.index(context.symbol)],
                                 side=PositionSide_Short,
                                 order_type=OrderType_Market, position_effect=PositionEffect_Close)
                    print(context.now, symbol, '市价单平多仓', context.trade_n[stocks.index(context.symbol)], '股')

            # 临近收盘时若仓位数不等于昨仓则回转所有仓位
            if day[11:16] == '14:55' or day[11:16] == '14:57':
                position = context.account().position(symbol=context.symbol, side=PositionSide_Long)
                # 这个if应该是有问题的，但没自信深究了，最好不用if先跑，如果跑不动再研究
                if (position != None):
                    if position['volume'] != context.total[stocks.index(context.symbol)]:
                        order_target_volume(symbol=context.symbol, volume=context.total[stocks.index(context.symbol)],
                                            order_type=OrderType_Market, position_side=PositionSide_Long)
                        print(context.now, context.symbol, '市价单回转仓位操作...')
                        context.ending[stocks.index(context.symbol)] = 1
            # 更新过去的日期数据
            context.day[stocks.index(context.symbol)][0] = context.day[stocks.index(context.symbol)][-1]


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

    run(strategy_id='17a0ab6c-33e7-11e8-bdb0-00ffe31f5606',
        filename='main.py',
        mode=MODE_BACKTEST,
        token='{{token}}',
        backtest_start_time='2019-01-01 08:00:00',
        backtest_end_time='2019-07-31 16:00:00',
        backtest_adjust=ADJUST_PREV,
        backtest_initial_cash=500000,
        backtest_commission_ratio=0.0003,
        backtest_slippage_ratio=0.0001)
