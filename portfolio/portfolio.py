"""
Component unit class: Portfolio
---------------------
"""

__author__ = "Han Xiao (Aaron)"

from queue import Queue
import datetime

import pandas as pd
import matplotlib.pyplot as plt

from event import FillEvent, OrderEvent, SignalEvent
from data.data import HistoricalDataHandler
import portfolio.performance as performance

from _util.cal_assist import compare_list, pos_find, keep_shared


class Portfolio:
    """

    """

    def __init__(self,
                 bars: HistoricalDataHandler,
                 events: Queue,
                 start,
                 initial_capital:float,
                 n:int,
                 position_freq:int):

        """

        :param bars:
        :param events:
        :param start:
        :param initial_capital:
        :param n:
        :param position_freq:
        """

        self.bars = bars
        self.events = events
        self.symbol_list = self.bars.symbol_list
        self.start = start
        self.initial_capital = initial_capital
        self.n = n
        self.position_freq = position_freq

        # 创建持仓统计和portfolio净值统计
        # self.all_positions = self.construct_all_positions()
        self.all_positions = []
        self.current_positions = {symbol:0 for symbol in self.symbol_list}

        # self.all_holdings = self.construct_all_holdings()
        self.all_holdings = []
        self.current_holdings = self.construct_current_holdings()

        # 记录在不同换仓日，可以用于分配的金额
        self.allocation_records = self._allocation_recording()

        # 导出策略表现
        self.equity_curve = None

    def construct_all_positions(self):
        """
        Market positions of holding tickers.
        :return:
        """
        position = {symbol:0 for symbol in self.symbol_list}
        position['datetime'] = datetime.datetime.strptime(self.bars.trade_day[0], '%Y-%m-%d')
        return [position]

    def construct_all_holdings(self):
        """
        Market value of holding tickers positions when market closes.
        :return:
        """
        holding = {symbol:0.0 for symbol in self.symbol_list}
        holding['datetime'] = datetime.datetime.strptime(self.bars.trade_day[0], '%Y-%m-%d')
        holding['cash'] = self.initial_capital
        # holding['commission'] = 0.0
        holding['total'] = self.initial_capital
        return [holding]

    def construct_current_holdings(self):
        """

        :return:
        """

        holding = {symbol:0.0 for symbol in self.symbol_list}
        holding['cash'] = self.initial_capital
        # holding['commission'] = 0.0
        holding['total'] = self.initial_capital

        return holding

    def construct_holding_records(self):
        """

        :return:
        """
        return {self.start:{"available_cap":self.initial_capital, 'holding_nums':0, 'avail_nums':self.n}}

    def update_time_index(self):
        """
        更新每日持仓量和持仓净值。
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
        # holding['commission'] = self.current_holdings['commission']
        holding['total'] = self.current_holdings['cash']

        # recalculate the market value of holding tickers
        if latest_datetime not in self.bars.swap_dates or latest_datetime == str(self.start.date()):
            for symbol in self.symbol_list:
                price = self.bars.get_latest_bar_values(symbol=symbol, val_type='close')
                if pd.isna(price):
                    price = 0.0
                market_value = self.current_positions[symbol] * price
                holding[symbol] = market_value
                holding['total'] += market_value

        elif latest_datetime in self.bars.swap_dates and latest_datetime != str(self.start.date()):
            # 先找出上期时间
            current_p = pos_find(self.bars.swap_dates, latest_datetime)
            last_swap_date = self.bars.swap_dates[current_p - 1]
            last_swap_list = self.bars.swap_lists[last_swap_date]
            # 交出对比先更新在换仓期不进行换仓的股票
            remain_list = keep_shared(last_swap_list, self.bars.swap_lists[latest_datetime])
            for symbol in remain_list:
                market_value = self.current_positions[symbol] * self.bars.get_latest_bar_values(symbol=symbol, val_type='close')
                holding[symbol] = market_value
                holding['total'] += market_value

        self.all_holdings.append(holding)
        print(latest_datetime, ': ', "Index updated!")

    def update_signal(self, event:SignalEvent):
        if event.type == 'Signal':
            self.events.put(self.generate_order(event))

    def generate_order(self, signal:SignalEvent, order_type:str = 'market'):
        """

        :param signal:
        :param order_type:
        :return:
        """

        if order_type == 'market':

            cur_positions = self.current_positions[signal.symbol]

            if signal.signal_type == 'long' and cur_positions == 0:
                quantity = self.capital_allocation_to_position(signal)
                return OrderEvent(symbol=signal.symbol, order_type=order_type, quantity=quantity, direction='buy')
        # elif signal.signal_type == 'short' and cur_positions == 0:
        # return OrderEvent(symbol=signal.symbol, order_type=order_type, quantity=quantity, direction='sell')
            elif signal.signal_type == 'exit' and cur_positions > 0:
                return OrderEvent(symbol=signal.symbol, order_type=order_type, quantity=cur_positions, direction='sell')
        # elif signal.signal_type == 'exit' and cur_positions < 0:
        # return OrderEvent(symbol=signal.symbol, order_type=order_type, quantity=abs(cur_positions), direction='buy')
        else:
            pass

    def capital_allocation_to_position(self, signal: SignalEvent):
        """

        :param signal:
        :return:
        """
        # 建仓日每股可分配资金核算
        if signal.datetime == str(self.start.date()):
            allocation_for_each = self.allocation_records[signal.datetime]
            quantity = self._position_count(signal.symbol, allocation_for_each)
            return quantity

        # 换仓日每股可分配资金核算
        else:
            # 首先确保已于换仓日卖出所有应换股
            # self._allocation_recording(signal)
            allocation_for_each = self.allocation_records[signal.datetime]
            quantity = self._position_count(signal.symbol, allocation_for_each)
            return quantity

    def _position_count(self, symbol:str, available_allocation:float):
        """
        根据可分配金额，根据A股交易以100股为一手的交易特性，计算应买入的持仓量。
        :param symbol: 股票代码
        :param available_allocation: 可分配金额
        :return: 某股票根据最新的open，可以购入的股份数
        """
        per_lot = self.bars.get_latest_bar_values(symbol=symbol, val_type='open') * 100 * 1.004
        n_lot = int(available_allocation / per_lot)
        return n_lot * 100

    def _allocation_recording(self, signal:SignalEvent = None):
        """
        记录每个换仓日，每个股票可用的金额
        ----------------------------
        1）建仓日
        如果是在建仓日，则每个个股的可用金额是 初始资金/持仓股票个数，并保存在portfolio组件类的属性：elf.allocation_records中；

        2）换仓日
        如果是在换仓日，只有在当所有要卖出的个股已全部出售，且正准备买第一个替换股票时，才会计算权重，确保等权重的实现。
        ----------------------------
        :param signal: 【option】，只有在非首个交易日，才会传入信号
        """
        if signal is None:
            allocation_for_each = self.initial_capital / self.n
            return {str(self.start.date()):allocation_for_each}
        else:
            pass

    def estimate_allocation(self):
        """

        :return:
        """
        current_cash = self.current_holdings['cash']

        current_date = self.bars.get_latest_bar_datetime(self.symbol_list[0])
        date = pd.to_datetime(current_date)

        if date > self.start.date() and current_date in self.bars.swap_lists:
            current_p = pos_find(self.bars.swap_dates, current_date)
            last_swap_date = self.bars.swap_dates[current_p - 1]
            last_swap_list = self.bars.swap_lists[last_swap_date]
            # 交出对比得到卖出名单和买入名单
            short_list, long_list = compare_list(last_swap_list, self.bars.swap_lists[current_date])
            # print(current_date, ': ', short_list)
            estimated_cash = 0

            if len(short_list) > 0:

                for short_symbol in short_list:
                    open_price = self.bars.get_latest_bar_values(short_symbol, 'open')
                    estimated_cash += open_price * self.current_positions[short_symbol] * (1 - 0.004)

                self.allocation_records[current_date] = (current_cash + estimated_cash) / len(long_list)
            else:
                self.allocation_records[current_date] = 0.0

    def reallocation(self):
        pass

    def update_positions_from_FillEvent(self, fill:FillEvent):
        """
        根据订单生成的FillEvent，更新持仓量。
        """
        # print(fill.symbol, fill.direction, fill.direction_num, fill.quantity)
        self.current_positions[fill.symbol] += fill.direction_num * fill.quantity
        self.all_positions[-1][fill.symbol] += fill.direction_num * fill.quantity

    def update_holdings_from_FillEvent(self, fill:FillEvent):
        """
        根据订单生成的FillEvent，更新当前的持仓量，现金余额（佣金双边千四），持仓市值（收盘价），最终加总得到资产组合总净值。
        """
        fill_cost = self.bars.get_latest_bar_values(fill.symbol, 'open')
        cost = fill.direction_num * fill_cost * fill.quantity

        commission = abs(cost) * 0.004
        if commission < 5.0:
            commission = 5.0

        # 将佣金纳入成本核算（现金变动）
        # 如果是买入，则会增大该数值，即购买成本
        # 如果是卖出，则会减小该数值，即回收现金
        total_cost_or_revenue = cost + commission

        # 更新资产净值
        current_price = self.bars.get_latest_bar_values(fill.symbol, 'close')
        current_value = fill.quantity * current_price

        if fill.direction_num == 1:
            self.current_holdings[fill.symbol] = current_value
            self.all_holdings[-1][fill.symbol] = current_value
        elif fill.direction_num == -1:
            current_value = 0.0
            self.current_holdings[fill.symbol] = current_value
            self.all_holdings[-1][fill.symbol] = current_value

        # self.current_holdings['commission'] += commission
        self.current_holdings['cash'] -= total_cost_or_revenue
        self.current_holdings['total'] -= (total_cost_or_revenue - current_value)

        # self.all_holdings[-1][fill.symbol] += total_cost_or_revenue
        # self.all_holdings[-1]['commission'] += commission
        self.all_holdings[-1]['cash'] -= total_cost_or_revenue
        self.all_holdings[-1]['total'] -= (total_cost_or_revenue - current_value)

    def update_holdings_records(self, fill:FillEvent):
        """

        :param fill:
        :return:
        """
        pass

    def update_fill(self, fill:FillEvent):
        """
        Input FillEvent and update positions and holdings accordingly.
        ------------
        :param fill: class FillEvent
        """
        if fill.type == 'Fill':
            self.update_positions_from_FillEvent(fill)
            self.update_holdings_from_FillEvent(fill)

    def create_equity_curve_df(self):
        """

        :return:
        """
        equity = pd.DataFrame(self.all_holdings[:-1])
        equity.set_index(keys='datetime', inplace=True)
        equity['return'] = equity['total'].pct_change()
        equity['cumulative_return'] = (1.0 + equity['return']).cumprod()
        self.equity_curve = equity
        self.equity_curve['cumulative_return'].plot()
        plt.legend()
        plt.show()

    def output_summary_stats(self):
        """
        :return: A table of portfolio properties.
        """

















