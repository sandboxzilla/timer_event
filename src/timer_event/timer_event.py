#!/bin/python3
#
#  Copyright (c) 2023  Erol Yesin/SandboxZilla
#
#  Permission is hereby granted, free of charge, to any person obtaining a copy of this
#  software and associated documentation files (the "Software"), to deal in the Software
#  without restriction, including without limitation the rights to use, copy, modify,
#  merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
#  permit persons to whom the Software is furnished to do so.
#
#  THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
#  INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
#  PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
#  HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
#  OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
#  SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#

__author__ = "Erol Yesin"

from threading import Timer
from threading import Event as Done
from time import time
from .event import Event


class TimerEvent(Event):
    """
    A class that inherits from time.Timer to create a repeated timer feature.
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
        super().__init__(name=name, interval=self.__interval, **self.__kwargs)
        self.__timer = Timer(interval=self.__interval, function=self.__target, **self.__kwargs)
        self.__timer.start()

    def __target(self):
        """
        The internal timer method.  
        Used by the Timer to initiate a timed event.

        Returns:
            None
        """
        while not self.__done.is_set():
            self.post(time())
            self.__done.wait(self. __interval)

    def stop(self):
        """
        Stops the timer.

        Returns:
            None
        """
        self.__done.set()
        super().stop()
        self.__timer.join()
