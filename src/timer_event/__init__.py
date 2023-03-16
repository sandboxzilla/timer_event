#!/bin/python3

"""
timer_event package

Author: Erol Yesin
Version: 0.8.2

This package provides two classes for working with events:

1.  EventThread: A class for creating and managing events with callback
    routines.
    This class can be used independently of TimerEvent for handling 
    general event-driven scenarios without any time-based requirements.

2.  TimerEvent: A class that extends EventThread to create timer-based 
    events.
    This class is specifically designed for scenarios where events are 
    triggered after a certain period of time or at specific intervals.
    Note:   Since this class extends the EventThread class it uses most 
            all methods defined and documented in EvenThread class.

For detailed documentation and example usage on each class, refer to their
respective module files.

Copyright (c) 2023.  Erol Yesin/SandboxZilla

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

from .event_thread import EventThread
from .timer_event import TimerEvent
