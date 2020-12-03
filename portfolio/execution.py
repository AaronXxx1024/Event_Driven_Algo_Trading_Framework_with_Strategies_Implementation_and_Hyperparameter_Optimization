"""

"""

__author__ = "Han Xiao (Aaron)"

from abc import ABCMeta, abstractmethod
import datetime
import queue

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

    def __init__(self, events:queue.Queue):
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
                commission=None)
            self.events.put(fill_event)







