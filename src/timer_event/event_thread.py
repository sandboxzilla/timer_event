#!/bin/python3
"""
This module provides a thread-safe Event class for managing and triggering
events with callback routines.

Author: Erol Yesin
Version: 0.9.1

Classes:
    EventThread:    A class for creating and managing events with 
                    callback routines.
    Example:
        >>> from time import sleep
        ...
        >>> def my_callback(packet):
        ... ... print(packet["payload"])
        ...
        >>> ev = Event("example")
        >>> ev.subscribe("example_subscriber", my_callback)
        >>> ev.post("Hello, world!")
        >>> ### The sleep prevents race condition where the callback might 
        >>> ### get unsubscribed before the broadcast process
        >>> sleep(0.1)
        Hello, world!
        >>> ev.unsubscribe("example_subscriber")
        >>> ev.post("This won't be printed")
        >>> sleep(0.1)
        >>> ev.stop()
        ...


    Copyright (c) 2023.  Erol Yesin/SandboxZilla

    Permission is hereby granted, free of charge, to any person obtaining a
    copy of this software and associated documentation files (the "Software"),
    to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense,
    and/or sell copies of the Software, and to permit persons to whom the
    Software is furnished to do so.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
    FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
    DEALINGS IN THE SOFTWARE.

"""

__author__ = "Erol Yesin"
__version__ = "0.9.1"

from typing import Any, Union
from queue import Queue
from threading import Thread, Lock


class EventThread(Thread):
    """
        A class for creating and managing events with callback routines.
        The broadcasts are processed in a separate thread from the thread
        that receives the post, to eliminate any callback affecting the
        posting thread.  However, any wrongly written callback routine
        would affect the other callback routines, which share the same
        thread.

        Attributes:
            __packet (dict):    A template dictionary containing included
                                in each event broadcasting to each callback.
                                this dictionary includes all parameters passed
                                during initialiation of the EventThread 
                                instantiation.
                                The basic packet dictionary includes:
                                "event" =   The event name
                                "dest"  =   The callback
                                "payload" = The object included in the post
                                "cookie" =  The cookie if included when subscribing
            __subscribers (dict):   A dictionary of dictionaries containing the
                                    subscribers' name and callback routines.
            __continue_thread (bool):   A flag indicating whether the thread 
                                        should continue running.
            __pause_broadcasting (bbol):    A flag indicating that event should
                                            pause broadcasting
            __lock (Lock): A lock for thread safety.
            __queue (Queue): A queue for storing events.

        Methods:
            __post():
                Internal runner for processing the queued events.
            __call__(payload, **kwargs) -> Event:
                Calls an event with a payload and optional arguments.
            __iadd__(handler: (dict, callable)) -> Event:
                Adds a subscription.
            __isub__(handler: (dict, callable, str)) -> Event:
                Removes the subscription.
            subscribe(name: str, on_event: callable, cookie: Any = None) -> Event:
                Subscribes to an event with a callback routine and an optional cookie.
            unsubscribe(name: str) -> EventThread:
                Unsubscribes from an event.
            post(payload, **kwargs) -> EventThread:
                Posts an event with a payload and optional arguments into queue 
                for processing.
            pause() -> EventThread:
                Pauses broadcasting events
            unpause() -> EventThread:
                Unpauses the event to continue broadcasting events
            stop():
                Stops the event processing thread, clears the subscribers list.
                Note:   This can not be used as pause.  Once the EventThread 
                        instance is stopped it can not be restarted.
                        A new instance must be created after calling stop to
                        continue eventing, but the subscribers list will be lost
    """

    def __init__(self, name: str, **kwargs):
        """
        Initializes the EventThread object.

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
        self.__pause_broadcasting = False
        self.__queue = Queue()

        super().__init__(name=self.__packet["event"] + "T", target=self.__post)
        self.start()

    def subscribe(self, name: str, on_event: callable, cookie: Any = None) -> 'Event':
        """
        Subscribe to an event with a callback routine and an optional cookie.

        Args:
            name (str):     Name of the subscriber.  Must be unique for 
                            each subscriber
            on_event (callable): Callback routine to execute when the event 
                                 is triggered.
            cookie (Any):   Optional cookie passed to the callback routine 
                            in the packet.
        Returns:
            self: The EventThread instance.
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
            self: The EventThread instance.
        """
        with self.__lock:
            if name in self.__subscribers:
                del self.__subscribers[name]
        return self

    def __post(self) -> None:
        """
        Broadcasts the triggered event
        
        Returns:
            None
        """
        while self.__continue_thread:
            packet = self.__queue.get()
            if packet["payload"] is not None and not self.__pause_broadcasting:
                for name, handler in self.__subscribers.items():
                    packet["dest"] = name
                    packet["cookie"] = handler["cookie"]
                    handler["on_event"](packet)
            elif self.__pause_broadcasting:
                pass

    def post(self, payload, **kwargs):
        """
        Puts the triggered event payload in to the process queue.

        Args:
            payload: The payload for the event.
            **kwargs: Optional keyword arguments to update the event packet.
            
        Returns:
            self: The EventThread instance.
        """
        with self.__lock:
            packet = self.__packet.copy()
            packet.update(kwargs)
            packet["payload"] = payload
            self.__queue.put_nowait(packet)
        return self

    def __call__(self, payload, **kwargs):
        """
        Calls an event with a payload and optional arguments.

        Args:
            payload: The payload for the event.
            **kwargs: Optional keyword arguments to update the event packet.
            
        Returns:
            self: The EventThread instance.
        """
        return self.post(payload=payload, **kwargs)

    def __iadd__(self, handler: Union[dict, callable]):
        """
        Adds a callback routine to an event using the "+=" operator.

        Args:
            handler (Union[dict, callable]): A dictionary containing the 
                                             callback routine's details or a 
                                             callable object.
            Note:   If a name is not provided in a dictionary or only a callback
                    function is given than the string representation of the 
                    function will be used as the key.

        Returns:
            self: The EventThread instance.
        """
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
        """
        Removes a callback routine from an event using the "-=" operator.

        Args:
            handler (Union[dict, callable, str]): A dictionary containing 
            the callback routine's details, a callable object, or a string 
            representing the name of the handler.
            Note:   Provide the same argument as when subscribing.
            
        Returns:
            self: The EventThread instance.
        """
        with self.__lock:
            if isinstance(handler, dict):
                handler = handler["name"]
            elif callable(handler):
                handler = str(handler)
        self.unsubscribe(handler)
        return self

    def stop(self):
        """
        Stops the event processing thread, clears the subscribers list, 
        and joins the thread.
        
        Returns:
            None
        """
        if self.__continue_thread:
            self.__continue_thread = False
            self.post(None)
            self.join()
            self.__subscribers.clear()

    def pause(self):
        """
        Pauses the event from broadcasting triggered events

        Returns:
            self: The EventThread instance.
        """
        with self.__lock:
            self.__pause_broadcasting = True
        return self

    def unpause(self):
        """
        Unpauses the event to continue broadcasting triggered events 
        
        Returns:
            self: The EventThread instance.
        """
        self.__pause_broadcasting = False
        return self


if __name__ == "__main__":
    from time import sleep
    
    def my_callback(packet):
        print(packet["payload"])

    ev = EventThread("example")
    ev.subscribe("example_subscriber", my_callback)
    ev.post("Hello, world!")
    sleep(0.1)
    ev.unsubscribe("example_subscriber")
    ev.post("This won't be printed")
    sleep(0.1)
    ev.stop()
