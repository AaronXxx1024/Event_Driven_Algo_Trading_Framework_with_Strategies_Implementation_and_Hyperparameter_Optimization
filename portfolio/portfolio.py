"""

"""

__author__ = "Han Xiao (Aaron)"

from event import FillEvent, OrderEvent, SignalEvent
from data.data import HistoricalDataHandler


class Portfolio:
    """

    """

    def __init__(self,
                 bars: HistoricalDataHandler,
                 events,
                 start,
                 initial_capital=100000.0):
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
        position['datetime'] = self.start
        return [position]

    def construct_all_holdings(self):
        """

        :return:
        """
        holding = {symbol:0.0 for symbol in self.symbol_list}
        holding['datetime'] = self.start
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
        holding['total'] = self.initial_capital
        return holding

    def update_time_index(self, event):
        """

        :param event:
        :return:
        """
        latest_datetime = self.bars.get_latest_bar_datetime(self.symbol_list[0])

        # update positions
        position = {symbol:0 for symbol in self.symbol_list}
        position['datetime'] = latest_datetime

        for symbol in self.symbol_list:
            position[symbol] = self.current_positions[symbol]
        self.all_positions.append(position)

        # update holdings
        holding = {symbol:0.0 for symbol in self.symbol_list}
        holding['datetime'] = latest_datetime
        holding['cash'] = self.current_holdings['cash']
        holding['commission'] = self.current_holdings['commission']
        holding['total'] = self.current_holdings['cash']

        for symbol in self.symbol_list:
            market_value = self.current_holdings[symbol] * \
                           self.bars.get_latest_bar_values(symbol=symbol, val_type='adj_close')
            holding[symbol] = market_value
            holding['total'] += market_value
        self.all_holdings.append(holding)

    def update_positions_from_FillEvent(self, fill:FillEvent):
        """

        :param fill:
        :return:
        """
        fill_dir = _fill_check(fill)
        self.current_positions[fill.symbol] += fill_dir * fill.quantity

    def update_holdings_from_FillEvent(self, fill:FillEvent):
        """

        :param fill:
        :return:
        """
        fill_dir = _fill_check(fill)
        fill_cost = self.bars.get_latest_bar_values(fill.symbol, 'adj_close')
        cost = fill_dir * fill_cost * fill.quantity
        self.current_holdings[fill.symbol] += cost
        self.current_holdings['commission'] += fill.commission
        self.current_holdings['cash'] -= cost + fill.commission
        self.current_holdings['total'] -= cost + fill.commission

    def update_fill(self, fill:FillEvent):
        """
        Input FillEvent and update positions and holdings accordingly.

        :param fill: class FillEvent
        """
        if fill.type == 'Fill':
            self.update_positions_from_FillEvent(fill)
            self.update_holdings_from_FillEvent(fill)

    def generate_order(self, signal:SignalEvent, quantity:int = 100, order_type:str = 'market'):
        """

        :param signal:
        :param quantity:
        :param order_type:
        :return:
        """
        cur_positions = self.current_positions[signal.symbol]
        if signal.signal_type == 'long' and cur_positions == 0:
            return OrderEvent(symbol=signal.symbol, order_type=order_type, quantity=quantity, direction='buy')
        elif signal.signal_type == 'short' and cur_positions == 0:
            return OrderEvent(symbol=signal.symbol, order_type=order_type, quantity=quantity, direction='sell')
        elif signal.signal_type == 'exit' and cur_positions > 0:
            return OrderEvent(symbol=signal.symbol, order_type=order_type, quantity=quantity, direction='sell')
        elif signal.signal_type == 'exit' and cur_positions < 0:
            return OrderEvent(symbol=signal.symbol, order_type=order_type, quantity=abs(quantity), direction='buy')

    def update_signal(self, event:SignalEvent):
        if event.type == 'Signal':
            self.events.put(self.generate_order(event))

    def create_equity_curve_df(self):
        pass

    def output_summary_stats(self):
        pass

def _fill_check(fill:FillEvent):
    if fill.direction == 'buy':
        return 1
    elif fill.direction == 'sell':
        return -1
    else:
        return 0

















