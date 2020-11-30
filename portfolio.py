"""

"""

__author__ = "Han Xiao (Aaron)"

import datetime
from math import floor
import queue

import numpy as np
import pandas as pd

from event import FillEvent, OrderEvent
from data.data import HistoricalDataHandler
import performance


class Portfolio:
    """

    """

    def __init__(self, bars: HistoricalDataHandler, events, start, initial_capital=100000.0):
        """

        :param bars:
        :param events:
        :param start:
        :param initial_capital:
        """
        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start = start
        self.initial_capital = initial_capital

        self.all_positions = self.construct_all_positions()
        self.current_positions = {symbol:0 for symbol in self.symbol_list}

        self.all_holdings = self.construct_all_holdings()
        self.current_holdings = self.construct_current_holdings()

    def construct_all_positions(self):
        """

        :return:
        """
        position = {symbol:0 for symbol in self.symbol_list}
        position['start'] = self.start
        return [position]

    def construct_all_holdings(self):
        """

        :return:
        """
        holding = {symbol:0.0 for symbol in self.symbol_list}
        holding['start'] = self.start
        holding['cash'] = self.initial_capital
        holding['commission'] = 0.0
        holding['balance'] = self.initial_capital
        return [holding]

    def construct_current_holdings(self):
        """

        :return:
        """
        holding = {symbol:0.0 for symbol in self.symbol_list}
        holding['cash'] = self.initial_capital
        holding['commission'] = 0.0
        holding['balance'] = self.initial_capital
        return holding

    def update_time_index(self, event):
        """

        :param event:
        :return:
        """

















