"""

"""

__author_ = "Han Xiao (Aaron)"

import datetime
import pprint
import queue
import time

# component class unit
from data.data import HistoricalDataHandler
from portfolio.execution import ExecutionHandler
from portfolio.portfolio import Portfolio
from strategy.strategy import Strategy


class Backtest:
    """

    """

    def __init__(self,
                 csv_path,
                 symbol_list,
                 initial_capital,
                 heartbeat,
                 start,
                 data_handler:HistoricalDataHandler,
                 execution_handler:ExecutionHandler,
                 portfolio:Portfolio,
                 strategy:Strategy):
        """

        :param csv_path:
        :param symbol_list:
        :param initial_capital:
        :param heartbeat:
        :param start:
        :param data_handler:
        :param execution_handler:
        :param portfolio:
        :param strategy:
        """
        self.csv_path = csv_path
        self.symbol_list = symbol_list
        self.initial_capital = initial_capital
        self.heartbeat = heartbeat
        self.start = start
        self.data_handler = data_handler
        self.portfolio = portfolio
        self.strategy = strategy
        self.execution_handler = execution_handler

        self.event = queue.Queue()

        self.signals = 0
        self.orders = 0
        self.fill = 0
        self.num_starts = 1

        self._generate_trading_instances()

    def _generate_trading_instances(self):
        """


        """
        self.data_handler = HistoricalDataHandler(events=self.event,
                                                  symbol_list=self.symbol_list,
                                                  csv_path=self.csv_path,
                                                  method='csv')
        #todo 策略部分需根据具体策略或者策略类进行调整
        self.strategy = Strategy()
        self.portfolio = Portfolio(bars=self.data_handler,
                                   events=self.event,
                                   start= self.start,
                                   initial_capital=self.initial_capital)
        self.execution_handler = ExecutionHandler(events=self.event)

    def _run_backtest(self):
        """

        :return:
        """
        i = 0
        while True:
            i += 1
            print(i)
            # Update the market bars
            if self.data_handler.continue_backtest:
                self.data_handler.update_bars()
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
                            self.strategy.calculate_signals()
                            self.portfolio.update_time_index(event)
                        elif event.type == "Signal":
                            self.signals += 1
                            self.portfolio.update_signal(event)
                        elif event.type == "Order":
                            self.orders += 1
                            self.execution_handler.execute_order(event)
                        elif event.type == "Fill":
                            self.fill += 1
                            self.portfolio.update_fill(event)

            time.sleep(self.heartbeat)

    def _output_performance(self):
        """

        :return:
        """
        pass

    def simulate_trading(self):
        """

        :return:
        """
        self._run_backtest()
        self._output_performance()
