"""

"""

__author_ = "Han Xiao (Aaron)"

import datetime
import pprint
import queue
from queue import Queue
import time

# component class unit
from data.data import HistoricalDataHandler
from portfolio.execution import ExecutionHandler
from portfolio.portfolio import Portfolio


class Backtest:
    """

    """

    def __init__(self,
                 csv_path:str,
                 symbol_list:list,
                 initial_capital,
                 heartbeat,
                 start,
                 strategy,
                 data_handler=HistoricalDataHandler,
                 portfolio=Portfolio,
                 execution_handler=ExecutionHandler
                 ):
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
        self.event = Queue()

        # Instantiate component class
        self.data_handler = data_handler(events=self.event,
                                         symbol_list=self.symbol_list,
                                         csv_path=self.csv_path,
                                         method='csv')

        self.strategy = strategy(self.data_handler,
                                 self.event)

        self.portfolio = portfolio(bars=self.data_handler,
                                   events=self.event,
                                   start= self.start,
                                   initial_capital=self.initial_capital)

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
                            self.strategy.calculate_signals(event)
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

    def backtesting(self):
        """

        :return:
        """
        self._run_backtest()
        self._output_performance()
