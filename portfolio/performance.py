"""

"""

__author__ = "Han Xiao (Aaron)"

import numpy as np
import pandas as pd
from pandas import Series, DataFrame


def get_annualised_sharpe(ret:Series, rf:Series = None, N=252):
    """
    Calculate annualised sharpe ratio based on input return series.
    :param ret: return series, preferred pd.Series.
    :param rf: risk-free rate series, preferred pd.Series.
    :param N: return time period.
    :return: Annualised sharpe ratio.
    """
    if not isinstance(ret, Series):
        raise ValueError("Input series should be pd.Series")
    if rf is None:
        return np.sqrt(N) * ret.mean() / ret.std()
    else:
        net_ret = ret - rf
        return np.sqrt(N) * net_ret.mean() / net_ret.std()

def get_sortino():
    pass

def get_calmar():
    pass