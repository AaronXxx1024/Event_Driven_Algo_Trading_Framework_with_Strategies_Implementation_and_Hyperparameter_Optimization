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
from queue import Queue

import numpy as np
import pandas as pd
import modin.pandas as mpd
from pandas_datareader import DataReader

from event import MarketEvent


class DataHandler:
    """
    An abstract base class. It will be used for standardization of
    extensive data component class cooperated with other component
    class.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def update_bars(self):

        raise NotImplementedError("Should implement update_bars()")

    @abstractmethod
    def get_latest_bars(self, symbol, N:int = None):

        raise NotImplementedError("Should implement get_latest_bars()")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):

        raise NotImplementedError("Should implement get_latest_bars_datetime()")

    @abstractmethod
    def get_latest_bar_values(self, symbol, val_type, N:int = None):

        raise NotImplementedError("Should implement get_latest_bar_values()")


class HistoricalDataHandler(DataHandler):
    """

    :param events:
    :param csv_path: absolute path where you save your data files.
    :param symbol_list:
    :param method:
    """

    def __init__(self,
                 events: Queue,
                 symbol_list: list,
                 csv_path:str = None,
                 factor_path=None,
                 trade_day: list = None,
                 method='csv',
                 start=None,
                 end=None,
                 n: int = None,
                 freq: int = None,
                 single_factor_test=False
                 ):

        self.events = events
        self.symbol_list = symbol_list
        self.csv_path = csv_path
        self.factors_path = factor_path
        self.trade_day = trade_day
        self.start = start
        self.end = end
        self.n = n
        self.freq = freq

        # 单因子测试开关
        self.single_factor_test = single_factor_test
        if self.single_factor_test:
            pass

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self._data_reader_(method, start, end)

        # 创建换仓日列表，对应的持仓名单
        # 同时设置一个换仓按钮，在换仓日，当要卖出的所有股票都已经卖出是，将其从False调为True
        # 然后开始根据当期要更换的股票数目，计算每股可分配的资金
        # 当要买入的股票都已经买入时，再将这个按钮调回False
        self.swap_dates = self._get_swap_dates()
        self.swap_lists = self._get_swap_lists()

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
            self._open_csv()
        elif method == 'sql':
            #todo: load data from sql database
            
            pass
        else:
            msg = "You have to choose one way to load data."
            raise KeyError(msg)

    def _open_csv(self):
        """
        Open csv based on symbol list.
        --------------------------------------------------------
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

    def _get_swap_dates(self):
        """
        根据建仓日，换仓频率和回测区间，计算所有的调仓日，并以列表的形式，储存在数据组件类中。
        :return: self.swap_dates = swap_dates
        """

        swap_dates = []
        start_pos = pos_find(self.trade_day, str(self.start.date()))

        length = len(self.trade_day)
        i = start_pos

        while i < length:
            swap_dates.append(self.trade_day[i])
            i += self.freq

        return swap_dates

    def _get_swap_lists(self):
        """
        根据换仓日期，择股数量，计算换仓日应持有的股票列表（来源于上一个有效交易日），
        并以字典+列表的形式，储存在数据组件类中
        :return: self.swap_lists = swap_lists
        """

        swap_lists = {}

        for swap in self.swap_dates:
            # 得到换仓日在有效交易日的排名, 需确保这个不是有效交易日的第一天
            current_swap_date_pos = pos_find(self.trade_day, swap)
            # 持仓列表应该参照的日期
            last_date = self.trade_day[current_swap_date_pos - 1]
            path = self.factors_path + '/{}.csv'.format(last_date)
            df = pd.read_csv(path, index_col=0)
            df.sort_values(by='north_holding_rank', inplace=True)
            swap_list = list(df.iloc[:self.n, 4])
            swap_lists[swap] = swap_list

        return swap_lists

    def update_bars(self):
        """
        Loop over symbol list, update the latest N bars
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

    def get_latest_bars(self, symbol:str, N: int = None):
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
        :return: pandas.Timestamp
        """
        return self.get_latest_bars(symbol)[0]

    def get_latest_bar_values(self, symbol:str, val_type:str, N:int = None):
        """

        :param symbol:
        :param val_type: Select one of {'high', 'low', 'open', 'close', 'volume', 'adj_close'}
        :param N:
        :return:
        """
        if N is None:
            return getattr(self.get_latest_bars(symbol)[1], val_type)
        else:
            try:
                bars_list = self.get_latest_bars(symbol, N)
            except KeyError:
                print("Input symbol is not in the historical data set")
                raise
            else:
                return np.array([getattr(b[1], val_type) for b in bars_list])

# 辅助函数
def pos_find(data:list, target):

    for i, v in enumerate(data):
        if target == v:
            return i