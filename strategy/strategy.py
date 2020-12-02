"""

"""

__author__ = "Han Xiao (Aaron)"

from abc import ABCMeta, abstractmethod

import datetime
import queue

import numpy as np
import pandas as pd

from event import SignalEvent


class Strategy:
    """

    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def calculate_signals(self, event):
        """

        :return:
        """
        raise NotImplementedError("Should implement calculate_signals()")













