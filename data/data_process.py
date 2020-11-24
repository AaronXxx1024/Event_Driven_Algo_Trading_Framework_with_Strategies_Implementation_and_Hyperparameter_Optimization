"""
根据目的或者回测策略，对数据库中的数据进行相应的清洗，或对其进行相应的统计测试，以满足策略需求。
"""

__author__ = 'Han Xiao (Aaron)'

from pandas import Series, DataFrame
from numpy import cumsum, log10, polyfit, sqrt, std, subtract, ndarray

import statsmodels.tsa.stattools as tsa
import statsmodels.api as sm
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import hurst
import quandl

class TS:
    """
    输入Financial Time Series Data，并根据目的对这个时间序列做各种检测；
    """
    def __init__(self, data):
        self.data = data
        if not isinstance(self.data, (Series, DataFrame, ndarray, list)):
            c = type(self.data)
            msg = "Input data type should be the following: Series, DataFrame, ndarray, list, but get {0}"
            raise ValueError(msg.format(c))

    def augmented_dickey_fuller(self):
        #todo 整合模型输出结果
        return tsa.adfuller(self.data, 1)

    def hurst(self, col=None):
        """
        Use Hurst Exponent method to test ts data's behaviour.
        :return: A comparison of Hurst Exponent test result and 3 criteria.
        """
        if isinstance(self.data, DataFrame) and col is not None:
            ts = np.array(self.data[col])
        else:
            ts = np.array(self.data)
        lags = range(2, 100)
        tau = [sqrt(std(subtract(ts[lag:], ts[:-lag]))) for lag in lags]
        poly = polyfit(log10(lags), log10(tau), 1)
        H = poly[0] * 2.0
        return print('H for GBM, MR and TR are 0.5, 0 and 1, separately. H for input ts is {}'.format(H))

    def cadf(self, ts1:str, ts2:str):
        if not isinstance(self.data, DataFrame):
            msg = "Required 2d data"
            raise ValueError(msg)
        formula = '{0} ~ {1}'.format(ts1, ts2)
        ols = sm.OLS.from_formula(formula, self.data).fit()
        beta = ols.params[1]
        self.data['res'] = self.data[ts1] - beta * self.data[ts2]
        return tsa.adfuller(self.data['res'])

#%%
if __name__ == '__main__':
    import pandas_datareader
    bkng = pandas_datareader.DataReader('BKNG','yahoo','2010-01-01','2019-12-31')
    expe = pandas_datareader.DataReader('EXPE','yahoo','2010-01-01','2019-12-31')
    df = pd.DataFrame({'bkng':bkng['Adj Close']})
    df = df.join(expe['Adj Close'])
    df.rename(columns={'Adj Close':'expe'}, inplace=True)

    # plot price series
    df['bkng_scale'] = df['bkng'] / 10
    df.iloc[:,1:].plot()
    plt.show()

    # plot
    df.plot(x='bkng_scale',y='expe',kind='scatter')
    plt.show()

    a = TS(df)
    print(a.cadf('expe','bkng'))
    print(a.hurst('res'))
