"""
处理数据并与框架的其他组成部分完成联动
"""

__author__ = 'Han Xiao (Aaron)'

from abc import ABCMeta, abstractmethod
import datetime
import os, os.path

import numpy as np
import pandas as pd

from event import MarketEvent

from pandas_datareader import DataReader

class DataHandler:
    """

    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_latest_bars(self, symbol, N:int = None):
        """

        :param symbol:
        :param N:
        :return:
        """
        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        """

        :param symbol:
        :return:
        """
        raise NotImplementedError("Should implement get_latest_bars_datetime()")

    @abstractmethod
    def get_latest_bar_values(self, symbol, val_type, N:int = None):
        """

        :param symbol:
        :param val_type:
        :param N:
        :return:
        """
        raise NotImplementedError("Should implement get_latest_bar_values()")

    @abstractmethod
    def update_bars(self):
        """

        :return:
        """
        raise NotImplementedError("Should implement update_bars()")


class HistoricalDataHandler(DataHandler):
    """

    :param events:
    :param csv_path:
    :param symbol_list:
    :param method:
    """

    def __init__(self, events:MarketEvent, symbol_list:list, csv_path:str = None, method='online',
                 start=None, end=None):
        """

        """
        self.events = events
        self.symbol_list = symbol_list
        self.csv_path = csv_path

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self._data_reader_(method, start, end)

    def _data_reader_(self, method:str, start, end):
        if method == 'online':
            for symbol in self.symbol_list:
                if start is None and end is None:
                    self.symbol_data[symbol] = DataReader(symbol, 'yahoo')
                else:
                    self.symbol_data[symbol] = DataReader(symbol, 'yahoo', start, end)
            pass
        elif method == 'csv':
            self._open_convert_csv()
        elif method == 'sql':
            #todo: load data from sql database
            pass
        else:
            msg = "You have to choose one way to load data."
            raise KeyError(msg)

    def _open_convert_csv(self):
        """

        :return:
        """
        for symbol in self.symbol_list:
            path = self.csv_path + '/{}.csv'.format(symbol)
            self.symbol_data[symbol] = pd.read_csv(
                path, header=0, index_col=0, parse_dates=True,
                names = [
                    'datetime', 'high', 'low', 'open', 'close', 'volume', 'adj_close'
                ]
            )

            self.latest_symbol_data[symbol] = []

        #for symbol in self.symbol_list:
        #    self.symbol_data[symbol] = self.symbol_data[symbol].reindex(
        #        index=comb_index, method='pad').iterrows()

    def get_latest_bars(self, symbol, N:int = None):
        """

        :param N:
        :param symbol:
        :return:
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("Input symbol is not in the historical data set")
            raise
        else:
            if N is None:
                return bars_list[-1:]
            else:
                return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        """

        :param symbol:
        :return:
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("Input symbol is not in the historical data set")
            raise
        else:
            return bars_list[-1].index.values()

    def get_latest_bar_values(self, symbol, val_type, N:int = None):
        """

        :param symbol:
        :param val_type:
        :param N:
        :return:
        """
        if N is None:
            try:
                bars_list = self.latest_symbol_data[symbol]
            except KeyError:
                print("Input symbol is not in the historical data set")
                raise
            else:
                return getattr(bars_list[-1][1], val_type)
        else:
            try:
                bars_list = self.get_latest_bars(symbol, N)
            except KeyError:
                print("Input symbol is not in the historical data set")
                raise
            else:
                return np.array([getattr(b[1], val_type) for b in bars_list])

    def update_bars(self):
        for symbol in self.symbol_list:
            bar = self.symbol_data[symbol].last('1D')
            if bar is not None:
                self.latest_symbol_data[symbol].append(bar)
        # self.events.put(MarketEvent())
        # todo put???

#%% test
sp500 = ['bkng','expe']
mydir = '/Users/aaronx-mac/PycharmProjects/Learning/Github/Event_Driven_Algo_Trading_Framework_with_Strategies_Implementation_and_Hyperparameter_Optimization/data'
data500 = HistoricalDataHandler(events=MarketEvent(), symbol_list=sp500,
                                csv_path=mydir, method='csv')





