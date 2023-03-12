#!/bin/python3
#
#  Copyright (c) 2019-2023.  Erol Yesin/SandboxZilla
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
#

__author__ = "Erol Yesin"
version = "0.7"

from typing import Any, Union
from queue import Queue
from threading import Thread, Lock


class Event(Thread):
    """
    A class for creating and managing events with callback routines.

    Attributes:
        packet (dict): A template dictionary containing the event name, destination, payload, and cookie.
        cb_routines (dict): A dictionary containing the callback routines for the event.
        continue_thread (bool): A boolean indicating whether the thread should continue running.
        lock (Lock): A lock for thread safety.
        queue (Queue): A queue for storing events.

    Methods:
        subscribe(name: str, on_event: callable, cookie: Any = None) -> Event:
            Subscribes to an event with a callback routine and an optional cookie.
        unsubscribe(name: str) -> Event:
            Unsubscribes from an event.
        post(payload, **kwargs) -> Event:
            Posts an event with a payload and optional arguments.
        __call__(payload, **kwargs) -> Event:
            Calls an event with a payload and optional arguments.
        __iadd__(handler: (dict, callable)) -> Event:
            Adds a callback routine to an event.
        __isub__(handler: (dict, callable, str)) -> Event:
            Removes a callback routine from an event.
    """

    def __init__(self, name: str, **kwargs):
        """
        Initializes the Event object.

        Args:
            name (str): The name of the event.
            **kwargs: Optional arguments for the event packet.

        Returns:
            None
        """
        self.__lock = Lock()

        self.__packet = kwargs
        self.__packet["event"] = name
        if "dest" not in self.__packet:
            self.__packet["dest"] = None
        if "payload" not in self.__packet:
            self.__packet["payload"] = None
        if "cookie" not in self.__packet:
            self.__packet["cookie"] = None

        self.__subscribers: dict = {}
        self.__continue_thread = True
        self.__queue = Queue()

        super().__init__(name=self.__packet["event"] + "T", target=self.__post)
        self.start()

    def subscribe(self, name: str, on_event: callable, cookie: Any = None) -> 'Event':
        """
        Subscribes to an event with a callback routine and an optional cookie.

        Args:
            name (str): The name of the event to subscribe to.
            on_event (callable): The callback routine to execute when the event is triggered.
            cookie (Any): An optional cookie to pass to the callback routine.

        Returns:
            Event: The Event object.
        """
        with self.__lock:
            self.__subscribers[name] = {"on_event": on_event, "cookie": cookie}
        return self

    def unsubscribe(self, name: str) -> 'Event':
        """
        Unsubscribes from an event.

        Args:
            name (str): The name of the event to unsubscribe from.

        Returns:
            Event: The Event object.
        """
        with self.__lock:
            if name in self.__subscribers:
                del self.__subscribers[name]
        return self

    def __post(self) -> None:
        """
        Posts an event to the subscribers.

        Returns:
            None
        """
        while self.__continue_thread:
            packet = self.__queue.get()
            if packet["payload"] is not None:
                for name, handler in self.__subscribers.items():
                    packet["dest"] = name
                    packet["cookie"] = handler["cookie"]
                    handler["on_event"](packet)

    def post(self, payload, **kwargs):
        """
        Puts an event payload in to the process queue.

        Returns:
            self
        """
        with self.__lock:
            packet = self.__packet.copy()
            packet.update(kwargs)
            packet["payload"] = payload
            self.__queue.put_nowait(packet)
        return self

    def __call__(self, payload, **kwargs):
        return self.post(payload=payload, **kwargs)

    def __iadd__(self, handler: Union[dict, callable]):
        with self.__lock:
            if isinstance(handler, dict):
                if 'on_event' not in handler or not callable(handler["on_event"]):
                    return self
                if 'cookie' not in handler:
                    handler['cookie'] = None
                if 'name' not in handler:
                    handler['name'] = str(handler["on_event"])
            else:
                handler = {"name": str(handler),
                           "on_event": handler,
                           "cookie": None}
        self.subscribe(**handler)
        return self

    def __isub__(self, handler: Union[dict, callable, str]):
        with self.__lock:
            if isinstance(handler, dict):
                handler = handler["name"]
            elif callable(handler):
                handler = str(handler)
        self.unsubscribe(handler)
        return self

    def stop(self):
        if self.__continue_thread:
            self.__continue_thread = False
            self.post(None)
            self.join()
            self.__subscribers.clear()
