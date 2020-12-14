"""

"""

__author__ = "Han Xiao (Aaron)"

import numpy as np
import pandas as pd
from pandas import Series, DataFrame
from scipy.stats import norm


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

def get_VaR(ret:Series, value:float, confidence:float = 0.99, method='var-cor'):
    """
    Calculate Value-at-Risk based on input return series and confidence level.
    --------------------------------------------------------
    :param ret: return series, preferred pd.Series.
    :param value: Portfolio value.
    :param confidence: Confidence level, preferred 0.99 or 0.95.
    :param method: Calculation method, default is 'variance-covariance method'
    (based on normality assumptions of return series). Alternative method could be
    'Monte Carlo method' (based on an underlying, potentially non-normal, distribution)
    and historical bootstrapping.
    --------------------------------------------------------
    :return: Potential loss value in given confidence level.
    """
    if not isinstance(ret, Series):
        raise ValueError("Input series should be pd.Series")
    mu, sigma = ret.mean(), ret.std()
    if method == 'var-cor':
        alpha = norm.ppf(1-confidence, mu, sigma)
        return value - value * (alpha + 1)
    elif method == 'mc':
        pass
    elif method == 'boots':
        pass


