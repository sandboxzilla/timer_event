% TIMER_EVENT(1) | Timer Event Utilities | October 2025

# NAME
timer_event — thread-based event broadcasting and periodic timer helper for Python applications

# SYNOPSIS
```python
from timer_event import EventThread, TimerEvent
```

# DESCRIPTION
`timer_event` offers two classes and a helper type:
- `EventThread`: manages a background dispatcher thread that delivers posted payloads to registered callbacks.
- `TimerEvent`: extends `EventThread` with a dedicated ticker thread that emits callbacks at a configurable cadence.
- `SubscriptionHandle`: utility returned by `subscribe()` to simplify unsubscription.

Both classes are designed for in-process use where lightweight pub/sub semantics are required without external brokers.

# INSTALLATION
Use an editable install during development:
```
pip install -e .
```

# OPTIONS
The constructors accept several controls that shape runtime behaviour:
- `max_queue_size`: cap the number of buffered events; `None` (default) keeps the queue unbounded.
- `overflow_policy`: behaviour when the queue is full (`"block"`, `"drop_newest"`, `"drop_oldest"`, `"error"`).
- `error_policy`: response when a subscriber raises (`"continue"`, `"stop"`, `"raise"`).
- `on_error(exc, subscriber, packet)`: optional hook invoked whenever a handler raises.
- `on_dispatch(subscriber, packet)`: optional success hook fired after each subscriber is notified.
- `auto_start` (`TimerEvent` only): start the ticker immediately (default) or require an explicit `start_timer()`.

# BASIC USAGE
## EventThread
```python
from timer_event import EventThread

bus = EventThread(
    "sensor_events",
    location="lab-a",
    max_queue_size=512,
    overflow_policy="drop_oldest",
    error_policy="continue",
    on_dispatch=lambda name, packet: print("dispatched", name),
)

def on_sensor(packet):
    print(packet["payload"], packet["cookie"])

handle = bus.subscribe("sensor_logger", on_sensor, cookie={"level": "debug"})
bus.post({"temperature": 21.5})
handle.unsubscribe()
bus.stop()
```

## TimerEvent
```python
from timer_event import TimerEvent
from threading import Event

stop_signal = Event()

def on_tick(packet):
    print(f"{packet['event']} @ {packet['payload']}")
    if packet["cookie"]["stop_flag"].is_set():
        timer.stop()

timer = TimerEvent(
    interval=2.0,
    name="heartbeat",
    max_queue_size=128,
    overflow_policy="block",
    error_policy="continue",
    stop_flag=stop_signal,
)
timer.subscribe("printer", on_tick, cookie={"stop_flag": stop_signal})
# Dynamically adjust cadence later:
timer.change_interval(0.5, apply_immediately=True)

# ... later ...
stop_signal.set()
```

# CONTEXT MANAGER USAGE
```python
from timer_event import EventThread

with EventThread("jobs", max_queue_size=100) as bus:
    bus.subscribe("worker", lambda packet: print(packet))
    bus.post({"job": 1})
# dispatcher automatically stopped on exit
```

# COMMANDS
- `post(payload, **overrides)` — enqueue an event. Additional keywords merge into the packet.
- `subscribe(name, callback, cookie=None)` — register a handler. Returns a `SubscriptionHandle` exposing `.unsubscribe()`.
- `unsubscribe(name)` — remove a handler by name.
- `pause()` / `unpause()` — suspend and resume dispatch; buffered events remain in queue while paused.
- `stop(wait=True)` — halt dispatcher (and timer, if applicable). Pass `wait=False` for non-blocking shutdown.
- `start_timer()` — (TimerEvent) begin the ticker when `auto_start=False`.
- `change_interval(interval, apply_immediately=False)` — (TimerEvent) update the tick cadence; optionally fire immediately using the new schedule.

# RUNTIME BEHAVIOUR
- While paused, the dispatcher blocks on the pause event; new posts accumulate in the queue according to `overflow_policy`.
- Queue overflow policies:
  - `block` (default) waits until space is available.
  - `drop_newest` discards the incoming packet.
  - `drop_oldest` removes the oldest buffered packet to make room.
  - `error` raises `RuntimeError`.
- Error policies:
  - `continue` logs and skips the failing subscriber.
  - `stop` stops the dispatcher after the faulty handler.
  - `raise` re-raises the exception in the dispatcher thread.
- Properties such as `queue_size`, `max_queue_size`, `is_running`, and `is_paused` expose dispatcher state.
- `TimerEvent.is_timer_running()` reports the ticker status; `change_interval(..., apply_immediately=True)` wakes the ticker to apply new timing immediately.

# DIAGNOSTICS
- Configure logging for `timer_event.event_thread` to observe overflow warnings and subscriber exceptions.
- Use the `on_error` hook to surface failures and `on_dispatch` for lightweight success metrics.
- Properties: `is_running`, `is_paused`, `queue_size`, and `subscriber_count` expose dispatcher state.

# FILES
- `src/timer_event/event_thread.py` — Event bus implementation.
- `src/timer_event/timer_event.py` — Timer extension.
- `tests/` — regression suite using `unittest`.
- `docs/` — architecture and design references.

# SEE ALSO
`threading`, `queue.Queue`, `sched` — standard library modules for concurrency and scheduling.

# AUTHORS
Erol Yesin and contributors.
