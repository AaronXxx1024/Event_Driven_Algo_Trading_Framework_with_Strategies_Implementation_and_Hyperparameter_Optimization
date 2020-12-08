"""

"""

__author__ = "Han Xiao (Aaron)"

from abc import ABCMeta, abstractmethod

import datetime
import queue

import numpy as np
import pandas as pd

from event import SignalEvent
from data.data import HistoricalDataHandler


class Strategy:
    """

    """

    __metaclass__ = ABCMeta

    #def __init__(self, data:HistoricalDataHandler, event:queue.Queue):
    #    self.data = data
    #    self.event = event

    @abstractmethod
    def calculate_signals(self, event):
        """

        :return:
        """
        raise NotImplementedError("Should implement calculate_signals()")













