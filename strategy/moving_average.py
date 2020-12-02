"""

"""

__author__ = "Han Xiao (Aaron)"

import datetime

import numpy as np
import pandas as pd
import statsmodels.api as sm

# Component unit class
from event import SignalEvent
from data.data import HistoricalDataHandler
from strategy.strategy import Strategy
from portfolio.portfolio import Portfolio
from portfolio.backtest import Backtest
from portfolio.execution import ExecutionHandler


class MovingAverageCross(Strategy):
    """

    """

    def __init__(self, bars:HistoricalDataHandler,
                 events, short_window:int = 100, long_window:int = 400):
        """

        :param bars:
        :param events:
        :param short_window:
        :param long_window:
        """
        self.bars = bars
        self.symbol_list = self.bars.symbol_list
        self.events = events
        self.short_window = short_window
        self.long_window = long_window

        self.bought = {symbol:'out' for symbol in self.symbol_list}

    def calculate_signals(self, event):
        """

        :param event:
        :return:
        """
        if event.type == 'Market':
            for symbol in self.symbol_list:
                bars = self.bars.get_latest_bar_values(symbol, 'adj_close', N=self.long_window)
                bars_date = self.bars.get_latest_bar_datetime(symbol)
                if bars is not None and bars != []:
                    short_sma = np.mean(bars[-self.short_window:])
                    long_sma = np.mean(bars[-self.long_window:])

                    dt = datetime.datetime.utcnow()

                    if short_sma > long_sma and self.bought[symbol] == 'out':
                        sig_dir = 'long'
                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0)
                        self.events.put(signal)
                        self.bought[symbol] = 'long'
                    elif short_sma < long_sma and self.bought[symbol] == 'long':
                        sig_dir = 'exit'
                        signal = SignalEvent(1, symbol, dt, sig_dir, 1.0)
                        self.events.put(signal)
                        self.bought[symbol] = 'out'


if __name__ == '__main__':
    csv_path = ''
    symbol_list = ['bkng']
    initial_capital = 100000.0
    heartbeat = 0.0
    start = None

    mac = Backtest(csv_path=csv_path,
                   symbol_list=symbol_list,
                   initial_capital=initial_capital,
                   heartbeat=heartbeat,
                   start=start,
                   data_handler=HistoricalDataHandler(),
                   execution_handler=ExecutionHandler(),
                   portfolio=Portfolio(),
                   strategy=MovingAverageCross()
                   )

    mac.simulate_trading()