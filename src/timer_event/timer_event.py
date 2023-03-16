#!/bin/python3
"""
This module provides a TimerEvent class that inherits from the Event class to create a repeated timer feature.

Author: Erol Yesin
Version: 0.8.2

Classes:
    TimerEvent: A class that inherits from Event to create a repeated timer feature.

Example:
    >>> from time import sleep
    ...
    >>> def print_time(packet):
    ...... print(f"Current time: {packet['payload']}")
    ...
    >>> te = TimerEvent(interval=0.5)
    >>> te.subscribe("time_printer", print_time)
    >>> sleep(3)
    Current time: 1619443204.035818
    Current time: 1619443204.536033
    Current time: 1619443205.036167
    Current time: 1619443205.536299
    Current time: 1619443206.036424
    Current time: 1619443206.536167
    >>> te.unsubscribe("time_printer")
    >>> te.stop()

    Copyright (c) 2023.  Erol Yesin/SandboxZilla

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR I
    MPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.

"""
from event_thread import EventThread
from threading import Timer
from threading import Event as Done
from time import time

__author__ = "Erol Yesin"
__version__ = "0.8.2"


class TimerEvent(EventThread):
    """
    A class that extends Event to create a timer events.
    Attributes:
        __done (threading.Event): Event class from the build-in threading package.  Provides blocking until timed event is posted.
        __timer (threading.Timer): Timer class from the build-in threading package.  The actual timer heartbeat

    Methods:
        __target():
            The internal timer thread loop.  Used by the Timer to post a timed events.
        stop():
            Stops the timer and joins the internal timer thread.
            Note:   Once the TimerEvent instance is stopped it can not be restarted.
                    A new instance must be created after calling stop to continue eventing, and the subscribers must resubscribe.
                    If pause is the intention, use the 'pause' method.
    """

    def __init__(self, interval: float, name: str = None, **kwargs):
        """
        Initializes the RepeatedTimer object.

        Args:
            interval (float): The interval between timer events.
            function (callable): The function to execute on each timer event.
            args (tuple): Optional arguments for the function.
            kwargs (dict): Optional keyword arguments for the function.

        Returns:
            self
        """
        if interval < 0.0:
            raise ValueError("'interval' must be a non-negative number")
        self.__kwargs = kwargs if kwargs is not None else {}
        if name is None:
            name = f"{interval}sRepeatingTimer"
        self.__interval = interval
        self.__done = Done()
        super().__init__(name=name, interval=interval, **self.__kwargs)
        self.__timer = Timer(interval=interval, function=self.__target, **self.__kwargs)
        self.__timer.start()

    def __target(self):
        """
        The internal timer thread loop.  
        Used by the Timer to initiate a timed event.

        Returns:
            None
        """
        while not self.__done.is_set():
            self.post(time())
            self.__done.wait(self.__interval)

    def stop(self):
        """
        Stops the timer and joins the internal timer thread.

        Returns:
            None
        """
        self.__done.set()
        super().stop()
        self.__timer.join()


if __name__ == "__main__":
    from time import sleep
    
    def print_time(packet):
        print(f"Current time: {packet['payload']}")

    te = TimerEvent(interval=0.5)
    te.subscribe("time_printer", print_time)
    sleep(3)
    te.unsubscribe("time_printer")
    te.stop()
