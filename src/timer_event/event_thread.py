#!/usr/bin/env python3
"""Thread-safe event dispatch primitives with backpressure and metrics hooks.

Example
=======
>>> from timer_event import EventThread
>>> with EventThread(
...     "alerts",
...     max_queue_size=128,
...     overflow_policy="drop_oldest",
...     error_policy="continue",
... ) as bus:
...     handle = bus.subscribe("printer", lambda packet: print(packet["payload"]))
...     bus.post({"msg": "ready"})
...     handle.unsubscribe()

The dispatcher runs on a dedicated thread, buffering posts in ``queue.Queue``
with configurable overflow policies. Subscriptions return lightweight handles,
and lifecycle utilities such as ``stop(wait=False)``, ``is_paused``, and
``queue_size`` enable tight runtime control.

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

from typing import Any, Callable, Dict, Optional, Tuple, Union
from queue import Queue, Full, Empty
from threading import Thread, Lock, Event as ThreadEvent, current_thread
import logging

LOGGER = logging.getLogger(__name__)

_STOP_SENTINEL = object()

_VALID_OVERFLOW_POLICIES = {"block", "drop_newest", "drop_oldest", "error"}
_VALID_ERROR_POLICIES = {"continue", "stop", "raise"}


class SubscriptionHandle:
    """
    Lightweight wrapper returned by ``EventThread.subscribe`` for ergonomic
    unsubscription without tracking string names manually.
    """

    __slots__ = ("__event_thread", "__name", "__active", "__lock")

    def __init__(self, event_thread: "EventThread", name: str):
        self.__event_thread = event_thread
        self.__name = name
        self.__active = True
        self.__lock = Lock()

    @property
    def name(self) -> str:
        return self.__name

    @property
    def active(self) -> bool:
        with self.__lock:
            return self.__active

    def unsubscribe(self) -> None:
        with self.__lock:
            if not self.__active:
                return
            self.__active = False
        self.__event_thread.unsubscribe(self.__name)

    def __repr__(self) -> str:
        state = "active" if self.active else "inactive"
        return f"<SubscriptionHandle name={self.__name!r} state={state}>"


class EventThread(Thread):
    """Thread-backed publish/subscribe dispatcher.

    `EventThread` decouples producers from subscribers by queuing posts inside
    ``queue.Queue`` and delivering them on a dedicated worker thread. The API
    supports:

    * Optional queue backpressure (`max_queue_size`, `overflow_policy`).
    * Configurable failure handling (`error_policy`, `on_error`).
    * Success instrumentation via `on_dispatch`.
    * Lightweight subscription handles for ergonomic teardown.
    * Lifecycle helpers (`pause`, `unpause`, `stop(wait=...)`, context manager
      support, `is_running`, `queue_size`, etc.).
    """

    def __init__(self,
                 name: str,
                 *,
                 max_queue_size: Optional[int] = None,
                 overflow_policy: str = "block",
                 error_policy: str = "continue",
                 on_error: Optional[Callable[[Exception, str, Dict[str, Any]], None]] = None,
                 on_dispatch: Optional[Callable[[str, Dict[str, Any]], None]] = None,
                 **kwargs):
        """
        Initializes the EventThread object.

        Args:
            name (str): The name of the event.
            max_queue_size (Optional[int]): Maximum number of packets permitted
                in the queue. If ``None`` (default) the queue is unbounded.
            overflow_policy (str): Behaviour when the queue is full.
                Supported values: ``"block"`` (default), ``"drop_newest"``,
                ``"drop_oldest"``, ``"error"``.
            error_policy (str): Behaviour when a subscriber raises an
                exception. Supported values: ``"continue"`` (default),
                ``"stop"``, ``"raise"``.
            on_error (Optional[Callable]): Optional callback invoked with
                ``(exc, subscriber_name, packet_copy)`` when a handler raises.
            on_dispatch (Optional[Callable]): Optional hook invoked after
                a subscriber successfully processes a packet. Receives
                ``(subscriber_name, packet_copy)``.
            **kwargs: Optional arguments for the event packet.

        Returns:
            None
        """
        self.__lock = Lock()
        self.__pause_event = ThreadEvent()
        self.__pause_event.set()

        self.__overflow_policy = overflow_policy.lower()
        if self.__overflow_policy not in _VALID_OVERFLOW_POLICIES:
            raise ValueError(f"Invalid overflow_policy '{overflow_policy}'. "
                             f"Expected one of {_VALID_OVERFLOW_POLICIES}")

        self.__error_policy = error_policy.lower()
        if self.__error_policy not in _VALID_ERROR_POLICIES:
            raise ValueError(f"Invalid error_policy '{error_policy}'. "
                             f"Expected one of {_VALID_ERROR_POLICIES}")

        self.__on_error = on_error
        self.__on_dispatch = on_dispatch

        self.__packet = kwargs
        self.__packet["event"] = name
        if "dest" not in self.__packet:
            self.__packet["dest"] = None
        if "payload" not in self.__packet:
            self.__packet["payload"] = None
        if "cookie" not in self.__packet:
            self.__packet["cookie"] = None

        self.__subscribers: dict = {}
        self.__running = True
        self.__paused = False

        if max_queue_size is not None and max_queue_size < 0:
            raise ValueError("'max_queue_size' must be non-negative or None")
        queue_size = 0 if max_queue_size in (None, 0) else max_queue_size
        self.__queue = Queue(maxsize=queue_size)
        self.__max_queue_size = queue_size

        super().__init__(name=self.__packet["event"] + "T", target=self.__post, daemon=True)
        self.start()

    def subscribe(self, name: str, on_event: callable, cookie: Any = None) -> SubscriptionHandle:
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
            SubscriptionHandle: Handle that can be used to unsubscribe.
        """
        with self.__lock:
            if name in self.__subscribers:
                raise ValueError(f"Subscriber '{name}' already exists for event '{self.__packet['event']}'")
            self.__subscribers[name] = {"on_event": on_event, "cookie": cookie}
        return SubscriptionHandle(self, name)

    def unsubscribe(self, name: str) -> 'EventThread':
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
        try:
            while True:
                packet = self.__queue.get()
                if packet is _STOP_SENTINEL:
                    break

                self.__pause_event.wait()

                with self.__lock:
                    subscribers: Tuple[Tuple[str, Dict[str, Any]], ...] = tuple(self.__subscribers.items())

                stop_requested = False
                for name, handler in subscribers:
                    packet_for_handler = packet.copy()
                    packet_for_handler["dest"] = name
                    packet_for_handler["cookie"] = handler.get("cookie")
                    callback = handler.get("on_event")
                    try:
                        callback(packet_for_handler)
                        self.__notify_dispatch(name, packet_for_handler)
                    except Exception as exc:
                        self.__handle_callback_exception(exc, name, packet_for_handler)
                        if self.__error_policy == "raise":
                            raise
                        if self.__error_policy == "stop":
                            stop_requested = True
                            break

                if stop_requested:
                    break
        finally:
            with self.__lock:
                self.__running = False
                self.__subscribers.clear()
            self.__pause_event.set()

    def post(self, payload, **kwargs):
        """
        Puts the triggered event payload in to the process queue.

        Args:
            payload: The payload for the event.
            **kwargs: Optional keyword arguments to update the event packet.
            
        Returns:
            self: The EventThread instance.
        """
        if not self.__running:
            raise RuntimeError("EventThread has been stopped")

        with self.__lock:
            packet = self.__packet.copy()
            packet.update(kwargs)
            packet["payload"] = payload
        self.__enqueue(packet)
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

    def stop(self, wait: bool = True):
        """
        Stops the event processing thread, clears the subscribers list,
        and optionally joins the thread (if called from outside the dispatcher).

        Args:
            wait (bool): When ``True`` (default), block until the dispatcher
                thread terminates. When ``False``, signal shutdown and return
                immediately while the dispatcher exits in the background.

        Returns:
            None
        """
        with self.__lock:
            if self.__running:
                self.__running = False
                should_signal = True
            else:
                should_signal = False

        if not should_signal:
            if wait and self.is_alive() and self is not current_thread():
                self.join()
            return

        self.__pause_event.set()
        self.__enqueue(_STOP_SENTINEL, bypass_overflow=True)

        if wait and self is not current_thread():
            self.join()

        with self.__lock:
            self.__subscribers.clear()

    def pause(self):
        """
        Pauses the event from broadcasting triggered events

        Returns:
            self: The EventThread instance.
        """
        with self.__lock:
            self.__paused = True
        self.__pause_event.clear()
        return self

    def unpause(self):
        """
        Unpauses the event to continue broadcasting triggered events 
        
        Returns:
            self: The EventThread instance.
        """
        with self.__lock:
            self.__paused = False
        self.__pause_event.set()
        return self

    def __enqueue(self, item: Any, bypass_overflow: bool = False) -> None:
        """
        Enqueue a packet respecting overflow policy.
        """
        if bypass_overflow or self.__max_queue_size == 0:
            self.__queue.put(item)
            return

        if self.__overflow_policy == "block":
            self.__queue.put(item)
            return

        while True:
            try:
                self.__queue.put_nowait(item)
                return
            except Full:
                if self.__overflow_policy == "drop_newest":
                    LOGGER.warning("Dropping newest event for '%s' due to full queue", self.__packet["event"])
                    return
                if self.__overflow_policy == "error":
                    raise RuntimeError("Event queue is full")
                if self.__overflow_policy == "drop_oldest":
                    try:
                        self.__queue.get_nowait()
                    except Empty:
                        continue
                else:
                    raise RuntimeError(f"Unhandled overflow policy '{self.__overflow_policy}'")

    def __handle_callback_exception(self, exc: Exception, subscriber: str, packet: Dict[str, Any]) -> None:
        """
        Handle exceptions thrown by subscriber callbacks according to the
        configured error policy.
        """
        if self.__on_error:
            try:
                self.__on_error(exc, subscriber, packet)
            except Exception:  # pragma: no cover - defensive
                LOGGER.exception("Exception in on_error handler for subscriber '%s'", subscriber)

        LOGGER.exception("Subscriber '%s' raised an exception", subscriber, exc_info=exc)

    def __notify_dispatch(self, subscriber: str, packet: Dict[str, Any]) -> None:
        if not self.__on_dispatch:
            return
        try:
            self.__on_dispatch(subscriber, packet.copy())
        except Exception:  # pragma: no cover - defensive
            LOGGER.exception("Exception in on_dispatch handler for subscriber '%s'", subscriber)

    @property
    def is_paused(self) -> bool:
        with self.__lock:
            return self.__paused

    @property
    def is_running(self) -> bool:
        with self.__lock:
            return self.__running

    @property
    def subscriber_count(self) -> int:
        with self.__lock:
            return len(self.__subscribers)

    @property
    def queue_size(self) -> int:
        return self.__queue.qsize()

    @property
    def max_queue_size(self) -> Optional[int]:
        return None if self.__max_queue_size == 0 else self.__max_queue_size

    def __enter__(self) -> "EventThread":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.stop()
        return False


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
