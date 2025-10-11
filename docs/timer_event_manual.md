% TIMER_EVENT(1) | Timer Event Utilities | October 2025

# NAME
timer_event — thread-based event broadcasting and periodic timer helper for Python applications

# SYNOPSIS
```python
from timer_event import EventThread, TimerEvent
```

# DESCRIPTION
`timer_event` offers two classes:
- `EventThread`: manages a background dispatcher thread that delivers posted payloads to registered callbacks.
- `TimerEvent`: extends `EventThread` by emitting callbacks on a fixed interval using Python's `threading.Timer`.

Both classes are designed for in-process use where lightweight pub/sub semantics are required without external brokers.

# INSTALLATION
Use an editable install while developing:
```
pip install -e .
```

# BASIC USAGE
## EventThread
```python
from timer_event import EventThread

bus = EventThread("sensor_events", location="lab-a")

def on_sensor(packet):
    print(packet["payload"], packet["cookie"])

bus.subscribe("sensor_logger", on_sensor, cookie={"level": "debug"})
bus.post({"temperature": 21.5})
bus.stop()
```

## TimerEvent
```python
from timer_event import TimerEvent
from threading import Event

stopped = Event()

def on_tick(packet):
    print(f"{packet['event']} @ {packet['payload']}")
    if packet["cookie"]["stop_flag"].is_set():
        timer.stop()

timer = TimerEvent(interval=2.0, name="heartbeat", stop_flag=stopped)
timer.subscribe("printer", on_tick, cookie={"stop_flag": stopped})
# ... later ...
stopped.set()
```

# COMMANDS
- `post(payload, **overrides)` — enqueue an event. Additional keyword arguments merge into the packet.
- `subscribe(name, callback, cookie=None)` — register a handler. `name` must be unique.
- `unsubscribe(name)` — remove a handler by name.
- `pause()` / `unpause()` — toggle dispatching (current implementation drops events while paused).
- `stop()` — halt dispatcher (and timer, if applicable) and release resources.

# ENVIRONMENT
No global configuration is required. The package depends solely on the Python standard library.

# DIAGNOSTICS
- Exceptions raised inside callbacks propagate and terminate the dispatcher thread.
- `stop()` is idempotent but instances cannot be restarted.
- Pausing discards queued items; ensure you flush state before pausing if data loss is unacceptable.

# FILES
- `src/timer_event/event_thread.py` — Event bus implementation.
- `src/timer_event/timer_event.py` — Timer extension.
- `tests/` — regression suite using `unittest`.
- `docs/` — architecture and design references.

# SEE ALSO
`threading` (Python standard library), `queue.Queue`, `sched` module for alternative scheduling strategies.

# AUTHORS
Erol Yesin and contributors.
