"""
Component unit class: Backtest
---------------------
"""

__author_ = "Han Xiao (Aaron)"

import time
import datetime
import pprint
import queue
from queue import Queue
import threading

# component class unit
from data.data import HistoricalDataHandler
from portfolio.execution import ExecutionHandler
from portfolio.portfolio import Portfolio
import portfolio.performance


class Backtest:
    """

    """
    def __init__(self,
                 csv_path:str,
                 factor_path:str,
                 symbol_list:list,

                 initial_capital:float,
                 heartbeat,
                 strategy,
                 start,
                 end=None,

                 trade_day:list = None,
                 n: int = None,
                 freq:int = None,
                 position_swap_method:str = 'default',

                 single_factor_test=False,
                 factor_group:str = None,

                 data_handler=HistoricalDataHandler,
                 portfolio=Portfolio,
                 execution_handler=ExecutionHandler
                 ):

        """
        :param csv_path: Absolute path where you save your stock price data files (or other fundamental data).
        :param factor_path: Absolute path where you save your factor rank data.
        :param symbol_list: A list consisted of all tradable stock symbols.
        :param initial_capital:
        :param heartbeat:
        :param start:
        :param strategy:
        :param trade_day:
        :param n:
        :param freq:
        :param data_handler:
        :param portfolio:
        :param execution_handler:
        """

        self.csv_path = csv_path
        self.factor_path = factor_path
        self.symbol_list = symbol_list

        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start = start
        self.end = end

        self.event = Queue()
        self.trade_day = trade_day
        self.n = n
        self.freq = freq
        self.position_swap_method = position_swap_method

        self.single_factor_test = single_factor_test
        self.factor_group = factor_group

        # Instantiate component class
        self.data_handler = data_handler(events=self.event,
                                         symbol_list=self.symbol_list,
                                         csv_path=self.csv_path,
                                         factor_path=self.factor_path,
                                         trade_day=self.trade_day,
                                         method='csv',
                                         start=self.start,
                                         n=self.n,
                                         freq=self.freq,
                                         single_factor_test=self.single_factor_test,
                                         factor_group=self.factor_group)

        self.strategy = strategy(self.data_handler,
                                 self.event,
                                 self.n,
                                 self.freq)

        self.portfolio = portfolio(bars=self.data_handler,
                                   events=self.event,
                                   start=self.start,
                                   initial_capital=self.initial_capital,
                                   n=self.n,
                                   position_freq=self.freq)

        self.execution_handler = execution_handler(events=self.event)

        # event statistics
        self.signals = 0
        self.orders = 0
        self.fill = 0
        self.num_starts = 1

    def _run_backtest(self):
        """

        :return:
        """
        while True:
            # Update the market bars
            if self.data_handler.continue_backtest:
                self.data_handler.update_bars()
                self.portfolio.estimate_allocation()
            else:
                break

            # Handle the events
            while True:
                try:
                    event = self.event.get(False)
                except queue.Empty:
                    break
                else:
                    if event is not None:

                        if event.type == "Market":
                            # 信号计算与每日portfolio更新
                            self.strategy.calculate_signals(event)
                            self.portfolio.update_time_index()

                        elif event.type == "Signal":
                            # 交易信号处理与头寸计算
                            self.signals += 1
                            self.portfolio.update_signal(event)

                        elif event.type == "Order":
                            # 下单
                            self.orders += 1
                            self.execution_handler.execute_order(event)

                        elif event.type == "Fill":
                            # 完成订单与portfolio更新
                            self.fill += 1
                            self.portfolio.update_fill(event)

                    # print(len(threading.enumerate()))

            time.sleep(self.heartbeat)

    def _output_performance(self):
        """

        :return:
        """
        pass

    def backtesting(self):
        """

        :return:
        """
        self._run_backtest()
        # self._output_performance()
