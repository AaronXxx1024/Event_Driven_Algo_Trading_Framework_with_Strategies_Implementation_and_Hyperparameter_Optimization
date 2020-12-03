"""
Component unit class: HistoricalDataHandler(DataHandler)
--------------------------------------------------------

where DataHandler is an abstract base class, with mandatory
functions that could be used for picking up and processing
data.

In HistoricalDataHandler, there are 3 ways that you can access
data (Online Source(like Yahoo), local csv file and SQL).

Todo: more data-cleaning functions used in time-series data, factor model or machine learning

Within Framework:
-----------------

"""

__author__ = 'Han Xiao (Aaron)'

from abc import ABCMeta, abstractmethod
import datetime
from queue import Queue

import numpy as np
import pandas as pd
import modin.pandas as mpd
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
                 symbol_list: list,
                 events:Queue = Queue(),
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
        combined_index = None
        for symbol in self.symbol_list:
            path = self.csv_path + '/{}.csv'.format(symbol)
            self.symbol_data[symbol] = pd.read_csv(
                path, header=0, index_col=0, parse_dates=True,
                names = [
                    'datetime', 'high', 'low', 'open', 'close', 'volume', 'adj_close'
                ]
            )

            if combined_index is None:
                combined_index = self.symbol_data[symbol].index
            else:
                combined_index.union(self.symbol_data[symbol].index)

            self.latest_symbol_data[symbol] = []

        # todo time index combine
        for symbol in self.symbol_list:
            self.symbol_data[symbol] = self.symbol_data[symbol].reindex(
                index=combined_index, method='pad').iterrows()

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

        for symbol in self.symbol_list:
            try:
                bar = next(self.symbol_data[symbol])
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[symbol].append(bar)
        self.events.put(MarketEvent())

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

#%%
from timeit import Timer
sp500 = ['bkng','expe']
mydir = '/Users/aaronx-mac/PycharmProjects/Learning/Github/Event_Driven_Algo_Trading_Framework_with_Strategies_Implementation_and_Hyperparameter_Optimization/data'
def read(path, slist):
    data = {}
    for s in slist:
        p = path+'/{}.csv'.format(s)
        data[s] = pd.read_csv(p)
    return data

#t1 = Timer("old(mydir, sp500)", "from __main__ import old,mydir,sp500")
#print(t1.repeat(5,20))
a = pd.read_csv(mydir + '/bkng.csv',header=0, index_col=0, parse_dates=True,
                names = [
                    'datetime', 'high', 'low', 'open', 'close', 'volume', 'adj_close'
                ])
#%%
def loop_1(df, N=100):
    period = "{}D".format(N)
    result = []
    bar = df.last(period)
    result.append(bar)
    return result

def loop_2(df, N=100):
    result = []
    result.append(df.iloc[-N:])
    return result

def loop_3(df:pd.DataFrame, N=100):
    result = []
    bars = df.iloc[-N:].iterrows()
    for _ in range(N):
        result.append(next(bars))
    return result

a1 = loop_1(a)
a2 = loop_2(a)
a3 = loop_3(a)

t1 = Timer("loop_1(a)", "from __main__ import loop_1, a")
t2 = Timer("loop_2(a)", "from __main__ import loop_2, a")
t3 = Timer("loop_3(a)", "from __main__ import loop_3, a")
print(t1.repeat(3,10))
print(t2.repeat(3,10))
print(t3.repeat(3,10))
#%%
data = HistoricalDataHandler(symbol_list=sp500, csv_path=mydir)
record = []
for _ in range(100):
    data.update_bars()
while True:
    if data.continue_backtest:
        data.update_bars()
    else:
        break

    bars = data.get_latest_bar_values('bkng', 'adj_close', 100)
    if bars is not None and bars != []:
        short = np.mean(bars[-30:])
        long = np.mean(bars[-100:])
        record.append((short,long))

