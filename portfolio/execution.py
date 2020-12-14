"""

"""

__author__ = "Han Xiao (Aaron)"

from abc import ABCMeta, abstractmethod
import datetime
from queue import Queue

from event import FillEvent, OrderEvent

class Execution:
    """

    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def execute_order(self, event:OrderEvent):
        """

        :param event:
        :return:
        """
        raise NotImplementedError("Should implement execute_order")


class ExecutionHandler(Execution):
    """

    """

    def __init__(self, events:Queue):
        """

        :param events:
        """
        self.events = events

    def execute_order(self, event:OrderEvent):
        """

        :param event:
        :return:
        """
        if event.type == "Order":
            fill_event = FillEvent(
                time_stamp=datetime.datetime.utcnow(),
                symbol=event.symbol,
                exchange='ARCA',
                quantity=event.quantity,
                direction=event.direction,
                # set fill_cost to 0 since we use historical close price for stock purchase cost
                fill_cost=0,
                commission=None)
            self.events.put(fill_event)







