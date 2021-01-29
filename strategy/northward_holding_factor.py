"""
Component unit class: NorthwardHoldingFactor(Strategy)
---------------------
"""

import datetime
from queue import Queue
import sys
sys.setrecursionlimit(100000)

import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

# Component unit class
from event import SignalEvent, MarketEvent
from data.data import HistoricalDataHandler
from strategy.strategy_base import Strategy
from portfolio.portfolio import Portfolio
from portfolio.backtest import Backtest
from portfolio.execution import ExecutionHandler

# Specific strategy unit
from strategy.northward import northward_data
from strategy.northward.northward_data import trade_day

from _util.cal_assist import compare_list, pos_find


class NorthwardHoldingFactor(Strategy):
    """
    北向单因子交易策略 - 重仓因子
    ------------------------

    """

    def __init__(self,
                 data: HistoricalDataHandler,
                 event: Queue,
                 n: int,
                 freq: int):

        super().__init__(data, event, n, freq)
        self.bars = data
        self.symbol_list = self.bars.symbol_list
        self.events = event

        # 选择建仓日，择股数量和换仓频率
        self.start_date = self.bars.start
        self.N = n
        self.position_freq = freq

        # 创建化持仓列表
        self.holding = {symbol:'exit' for symbol in self.symbol_list}

        # 创建调仓日列表
        self.swap_dates = self.bars.swap_dates

        # 创建交易日目标股票名单，以字典+列表的形式储存
        self.swap_lists = self.bars.swap_lists

    def calculate_signals(self, event: MarketEvent):
        """
        Signal Calculation
        ------------------
        According to specific trading strategies, calculate trading signal.
        :param event: Basic event class, MarketEvent, used for triggering signal calculation.
        """

        if event.type == 'Market':
            bars_date = self.bars.get_latest_bar_datetime(self.symbol_list[0])

            # 如果当前的bar时间在调仓列表时间里，则开始计算信号
            # 同时将本期应持有的股票名单保存在策略类中
            # 在保证持有的股票数量不变的情况下
            if bars_date in self.swap_dates:

                if bars_date == str(self.start_date.date()):

                    for symbol in self.swap_lists[bars_date]:
                        self.place_order_from_signal(symbol, bars_date, 'long')

                else:
                    # 先找出上期时间
                    current_p = pos_find(self.bars.swap_dates, bars_date)
                    last_swap_date = self.bars.swap_dates[current_p - 1]
                    last_swap_list = self.swap_lists[last_swap_date]
                    # 交出对比得到卖出名单和买入名单
                    short_list, long_list = compare_list(last_swap_list, self.swap_lists[bars_date])
                    print('short_list:', short_list, 'long_list: ', long_list)

                    if short_list != [] and long_list != []:

                        merge = ['2019-07-19','2019-07-22', '2019-06-24', '2019-06-25', '2019-06-21', '2019-07-05',
                                 '2019-08-16','2019-08-02']
                        if self.bars.specific_events is not None and bars_date in merge:
                            if '000418.XSHE' in short_list:
                                short_list.remove('000418.XSHE')

                        for symbol in short_list:
                            self.place_order_from_signal(symbol, bars_date, 'exit')

                        for symbol in long_list:
                            # todo: 买入的替代品，可以按照等股票数量买，或者是因子排序，或者是动态市值加权
                            self.place_order_from_signal(symbol, bars_date, 'long')

    def place_order_from_signal(self, symbol:str, date, direction:str, other=None):
        """

        :param symbol:
        :param date:
        :param direction:
        :param other:
        :return:
        """

        signal = SignalEvent(1, symbol, date, direction, 1.0, other)
        self.events.put(signal)
        self.holding[symbol] = direction


# %% if __name__ == '__main__':
start = datetime.datetime(2017, 3, 24, 0, 0, 0)
all_stock_codes = northward_data.get_codes(path='G:/XH-雁丰/strategy/northward/stock_data/all_stock_codes.csv')

northward = Backtest(csv_path='G:/XH-雁丰/strategy/northward/stock_data/hsgt',
                     factor_path='G:/XH-雁丰/strategy/northward/north_holding/hsgt',
                     benchmark_path='G:/XH-雁丰/strategy/northward/hs300.csv',
                     symbol_list=all_stock_codes,
                     initial_capital=2000000.0,
                     heartbeat=0.0,
                     start=start,
                     strategy=NorthwardHoldingFactor,
                     trade_day=trade_day,
                     n=50,
                     freq=20)
                     # single_factor_test=True,
                     # factor_group='fourth')

northward.backtesting()
northward.portfolio.create_equity_curve_df()
northward.portfolio.output_summary_stats()
print('Backtest Completed!')

# northward.portfolio.equity_curve.to_csv("D:/XH-雁丰/strategy/northward/strategy_performance/single_factor/hsgt_top.csv")
# northward.portfolio.equity_curve.to_csv("G:/XH-雁丰/strategy/northward/strategy_performance/final/hsgt_50n_20d_24.csv")
#%%
df = pd.read_csv("G:/XH-雁丰/strategy/northward/strategy_performance/final/total.csv", index_col=0)
df['ret'] = df['total'].pct_change()
df['cumulative_ret'] = (1 + df['ret']).cumprod()
df['net_return'] = df['ret'] - df['hs300']
df['net_cumulative_ret'] = (1 + df['net_return']).cumprod()

#%%
import portfolio.performance
df = pd.read_csv("G:/XH-雁丰/strategy/northward/strategy_performance/final/total2.csv", index_col=0)
print(portfolio.performance.get_annualized_return(df['ret']))
print(portfolio.performance.get_annualised_sharpe(df['ret'], df['hs300']))
print(portfolio.performance.max_drawdown(df['50']))


