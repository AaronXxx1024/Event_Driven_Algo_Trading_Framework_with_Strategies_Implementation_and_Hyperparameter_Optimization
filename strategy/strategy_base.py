"""

"""

__author__ = "Han Xiao (Aaron)"

from abc import ABCMeta, abstractmethod

import datetime
from queue import Queue

from event import MarketEvent
from data.data import HistoricalDataHandler


class Strategy:
    """

    """

    __metaclass__ = ABCMeta

    def __init__(self, data:HistoricalDataHandler, event:Queue):
        self.data = data
        self.event = event

    @abstractmethod
    def calculate_signals(self, event:MarketEvent):
        """

        :return:
        """
        raise NotImplementedError("Should implement calculate_signals()")













