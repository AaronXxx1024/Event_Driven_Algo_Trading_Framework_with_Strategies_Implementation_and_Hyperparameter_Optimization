"""
算法交易的基层框架，其作用为串联包括数据分析，信号处理，回测，资产组合管理，风控在内的所有组成成分
"""

__author__ = "Han Xiao (Aaron)"

class Event:
    """

    """
    pass


class MarketEvent(Event):
    """

    """

    def __init__(self):
        self.type = 'Market'


class SignalEvent(Event):
    """

    """

    def __init__(self, strategy, symbol:str, datetime, signal_type:str, strength:float):
        """

        :param strategy:
        :param symbol:
        :param datetime:
        :param signal_type: 'long', 'short' or 'exit'
        :param strength:
        """
        self.type = 'Signal'
        self.strategy = strategy
        self.symbol = symbol
        self.datetime = datetime
        self.signal_type = signal_type
        self.strength = strength


class OrderEvent(Event):
    """

    """

    def __init__(self, symbol:str, order_type:str, quantity:int, direction:str, currency: str = None):
        """

        :param symbol:
        :param order_type: 'market' or 'limit'
        :param quantity:
        :param direction: 'buy' or 'sell'
        """

        self.type = 'Order'
        self.symbol = symbol
        self.order_type = order_type
        self.quantity = quantity
        self.direction = direction
        self.currency = currency

    def print_order(self):
        """
        :return: print order information
        """
        msg = "Order: Symbol={0}, Type={1}, Quantity={2}, Direction={3}, Currency={4}".format(
            self.symbol, self.order_type, self.quantity, self.direction, self.currency
        )
        print(msg)


class FillEvent(Event):
    """

    """

    def __init__(self, time_stamp, symbol:str, exchange, quantity, direction:str,
                 fill_cost, commission=None, currency: str = None):
        """

        :param time_stamp:
        :param symbol:
        :param exchange:
        :param quantity:
        :param direction:
        :param fill_cost:
        :param commission:
        :param currency:
        """

        self.type = 'Fill'
        self.time_stamp = time_stamp
        self.symbol = symbol
        self.exchange = exchange
        self.quantity = quantity
        self.direction = direction
        self.fill_cost = fill_cost
        self.currency = currency

        # Calculate commission
        if commission is None:
            self.commission = self.calculate_commission()
        else:
            self.commission = commission

    def calculate_commission(self):
        """
        Calculate the commission fee for each trade. Different brokers may have different charging standards.
        Used Interactive Brokers as default.

        Other fees like exchange fees haven't been included.
        :return: Float number of commission fee.

        ---------------
        Reference:

        """

        if self.quantity <= 500:
            commission_cost = max(1.3, 0.013 * self.quantity)
        else:
            commission_cost = max(1.3, 0.008 * self.quantity)
        return commission_cost


