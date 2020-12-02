"""
处理数据并与框架的其他组成部分完成联动
"""

__author__ = 'Han Xiao (Aaron)'

from abc import ABCMeta, abstractmethod
import datetime
from queue import Queue

import numpy as np
import pandas as pd
from pandas_datareader import DataReader

from event import MarketEvent
from data import data_process as dp


class DataHandler:
    """

    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def update_bars(self):
        """

        :return:
        """
        raise NotImplementedError("Should implement update_bars()")

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


class HistoricalDataHandler(DataHandler):
    """

    :param events:
    :param csv_path:
    :param symbol_list:
    :param method:
    """

    def __init__(self,
                 events:Queue,
                 symbol_list:list,
                 csv_path:str = None,
                 method='csv',
                 start=None,
                 end=None):
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
        Open csv based on symbol list.

        Save data in dict attribute self.symbol_data[symbol] and
        create the corresponding empty symbol in dict attribute
        self.latest_symbol_data[symbol].

        Example:
        --------
        self.latest_symbol_data = {symbol:[]}
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
        # todo time index combine
        #for symbol in self.symbol_list:
        #    self.symbol_data[symbol] = self.symbol_data[symbol].reindex(
        #        index=comb_index, method='pad').iterrows()

    def update_bars(self, N: int = 1):
        """
        Loop over symbol list , update the latest N bars
        info in dict attribute self.latest_symbol_data.

        Example:
        --------
        self.latest_symbol_data = {symbol:[latest_N_bars]}
        """
        # todo: 哪种方式返回最新的bar
        # 这里其实有个问题，如果我用last函数返回最后几个时间戳，但如果不是连续时间
        # 要求3天，其实是可以只返回2天/1天的
        # 所以使用iterrows来迭代行是可行的
        # 根据后续组件的具体情况，看是否要进行修正

        period = "{}D".format(N)

        for symbol in self.symbol_list:
            bar = self.symbol_data[symbol].last(period)
            if bar is not None:
                self.latest_symbol_data[symbol].append(bar)
        # self.events.put(MarketEvent())
        # todo put???

    def get_latest_bars(self, symbol, N: int = None):
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
                return bars_list[-1]
            else:
                return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol:str):
        """
        Get info about the latest time index based on input symbol.
        :return: numpy.datetime64
        """
        return self.get_latest_bars(symbol).index.values[0]

    def get_latest_bar_values(self, symbol, val_type:str, N:int = None):
        """

        :param symbol:
        :param val_type:
        :param N:
        :return:
        """
        if N is None:
            return getattr(self.get_latest_bars(symbol), val_type)
        else:
            try:
                bars_list = self.get_latest_bars(symbol, N)
            except KeyError:
                print("Input symbol is not in the historical data set")
                raise
            else:
                return np.array([getattr(b[1], val_type) for b in bars_list])



#%% test
sp500 = ['bkng','expe']
mydir = '/Users/aaronx-mac/PycharmProjects/Learning/Github/Event_Driven_Algo_Trading_Framework_with_Strategies_Implementation_and_Hyperparameter_Optimization/data'
data500 = HistoricalDataHandler(events=MarketEvent(), symbol_list=sp500,
                                csv_path=mydir, method='csv')
df = pd.read_csv(
                mydir+'/bkng.csv', header=0, index_col=0, parse_dates=True,
                names = [
                    'datetime', 'high', 'low', 'open', 'close', 'volume', 'adj_close'
                ]
            )





