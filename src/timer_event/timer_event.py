#!/usr/bin/env python3
"""TimerEvent: interval-driven wrapper around :class:`EventThread`.

Example
=======
>>> from timer_event import TimerEvent
>>> from threading import Event
>>> stop_flag = Event()
>>> def on_tick(packet):
...     print(packet["payload"])
...     stop_flag.set()
>>> with TimerEvent(interval=0.5, auto_start=False) as ticker:
...     ticker.subscribe("printer", on_tick)
...     ticker.start_timer()
...     ticker.change_interval(0.25, apply_immediately=True)
...     stop_flag.wait(timeout=2)

The ticker runs in its own daemon thread and respects the same overflow,
error-handling, and instrumentation hooks as :class:`EventThread`.

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

from __future__ import annotations

from threading import Event as ThreadEvent, Lock, Thread
from time import time
from typing import Callable, Optional, Dict, Any

from .event_thread import EventThread

__author__ = "Erol Yesin"
__version__ = "0.9.1"


class TimerEvent(EventThread):
    """Periodic emitter built on :class:`EventThread`.

    Features:

    * Internal ticker thread with lazy start (`auto_start=False` + `start_timer()`).
    * Runtime interval changes via :meth:`change_interval`.
    * Shares all queue/error/metrics hooks with :class:`EventThread`.
    * Context-manager friendly; exiting the block stops both ticker and dispatcher.
    """

    def __init__(self,
                 interval: float,
                 name: Optional[str] = None,
                 *,
                 max_queue_size: Optional[int] = None,
                 overflow_policy: str = "block",
                 error_policy: str = "continue",
                 on_error: Optional[Callable[[Exception, str, Dict[str, Any]], None]] = None,
                 auto_start: bool = True,
                 **kwargs):
        if interval < 0.0:
            raise ValueError("'interval' must be a non-negative number")

        kwargs = dict(kwargs or {})
        control_kwargs = {
            "max_queue_size": max_queue_size,
            "overflow_policy": overflow_policy,
            "error_policy": error_policy,
            "on_error": on_error,
        }
        thread_params = {k: v for k, v in control_kwargs.items() if v is not None}

        if name is None:
            name = f"{interval}sRepeatingTimer"

        self.__interval_lock = Lock()
        self.__interval = interval
        self.__emit_immediately = False
        self.__wake = ThreadEvent()
        self.__done = ThreadEvent()
        self.__ticker_lock = Lock()
        self.__ticker_thread: Optional[Thread] = None
        self.__ticker_started = False

        super().__init__(name=name, interval=interval, **thread_params, **kwargs)

        if auto_start:
            self.start_timer()

    def start_timer(self) -> "TimerEvent":
        """Start the internal ticker thread if it is not already running."""
        with self.__ticker_lock:
            if self.__ticker_started:
                return self
            self.__ticker_started = True
            self.__wake.clear()
            self.__ticker_thread = Thread(
                target=self.__run_loop,
                name=f"{self.name}-Ticker",
                daemon=True,
            )
            self.__ticker_thread.start()
        return self

    def change_interval(self, interval: float, *, apply_immediately: bool = False) -> "TimerEvent":
        """
        Update the cadence for future ticks.

        Args:
            interval: New interval in seconds. Must be non-negative.
            apply_immediately: If True, schedule the next tick immediately
                using the new interval.
        """
        if interval < 0.0:
            raise ValueError("'interval' must be a non-negative number")
        with self.__interval_lock:
            self.__interval = interval
            if apply_immediately:
                self.__emit_immediately = True
        self.__wake.set()
        return self

    def stop(self, wait: bool = True):
        """Stop the ticker and dispatcher threads.

        Args:
            wait (bool): When ``True`` (default) block until both ticker and
                dispatcher threads terminate. When ``False`` return
                immediately after signalling shutdown.
        """
        self.__done.set()
        self.__wake.set()
        with self.__ticker_lock:
            ticker = self.__ticker_thread
        super().stop(wait=wait)
        if ticker is not None and ticker.is_alive():
            if wait:
                ticker.join()
            else:
                ticker.join(timeout=0)
        with self.__ticker_lock:
            self.__ticker_started = False
            self.__ticker_thread = None
        self.__wake.clear()

    def is_timer_running(self) -> bool:
        with self.__ticker_lock:
            return bool(self.__ticker_thread and self.__ticker_thread.is_alive())

    def __enter__(self) -> "TimerEvent":
        super().__enter__()
        if not self.is_timer_running():
            self.start_timer()
        return self

    def __run_loop(self) -> None:
        while not self.__done.is_set():
            wait_for = self.__current_interval()
            triggered = self.__wake.wait(wait_for)
            if self.__done.is_set():
                break

            if triggered:
                self.__wake.clear()
                with self.__interval_lock:
                    emit_now = self.__emit_immediately
                    self.__emit_immediately = False
                if emit_now:
                    self.post(time())
                continue

            self.post(time())

    def __current_interval(self) -> float:
        with self.__interval_lock:
            return self.__interval


if __name__ == "__main__":
    from time import sleep

    def print_time(packet):
        print(f"Current time: {packet['payload']}")

    te = TimerEvent(interval=0.5)
    handle = te.subscribe("time_printer", print_time)
    sleep(3)
    handle.unsubscribe()
    te.stop()
