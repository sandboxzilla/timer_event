# Timer Event Low-Level Design (2025-10-11)

## Module Inventory
```mermaid
flowchart TD
    subgraph src/timer_event
        A[event_thread.py]
        B[timer_event.py]
        C[__init__.py]
    end
    subgraph tests
        D[test_event_thread.py]
        E[test_timer_event.py]
    end
    A --> B:::import
    C --> A
    C --> B
    classDef import stroke:#0366d6,stroke-width:2px;
```

## Class Structure
```mermaid
classDiagram
    direction TB
    class EventThread {
        -__packet: dict
        -__subscribers: Dict[str, Dict[str, Any]]
        -__continue_thread: bool
        -__pause_broadcasting: bool
        -__lock: Lock
        -__queue: Queue
        +__init__(name: str, **kwargs)
        +subscribe(name: str, on_event: Callable, cookie: Any = None)
        +unsubscribe(name: str)
        +post(payload, **kwargs)
        +__call__(payload, **kwargs)
        +__iadd__(handler)
        +__isub__(handler)
        +pause()
        +unpause()
        +stop()
        -__post()
    }
    class TimerEvent {
        -__kwargs: dict
        -__interval: float
        -__done: threading.Event
        -__timer: threading.Timer
        +__init__(interval: float, name: str = None, **kwargs)
        -__run()
        +stop()
    }
    EventThread <|-- TimerEvent
```

## Internal Dispatch Workflow
```mermaid
sequenceDiagram
    participant Poster as EventThread.post
    participant Queue as queue.Queue
    participant Dispatcher as EventThread.__post
    participant Registry as __subscribers dict
    participant Callback as Subscriber Handler

    Poster->>Poster: copy template (__packet)
    Poster->>Poster: update payload & overrides
    Poster->>Queue: put_nowait(packet)
    loop until __continue_thread is False
        Dispatcher->>Queue: get()
        alt payload is None
            Dispatcher->>Dispatcher: sentinel -> break loop
        else paused flag true
            Dispatcher->>Dispatcher: discard packet
        else
            loop for name, handler in Registry
                Dispatcher->>Dispatcher: packet["dest"]=name
                Dispatcher->>Dispatcher: packet["cookie"]=handler["cookie"]
                Dispatcher->>Callback: handler["on_event"](packet)
            end
        end
    end
    Dispatcher->>Registry: clear() on stop()
```

## EventThread Lifecycle States
```mermaid
stateDiagram-v2
    [*] --> Starting
    Starting --> Running : Thread.start()
    Running --> Paused : pause()
    Paused --> Running : unpause()
    Running --> Stopping : stop()
    Paused --> Stopping : stop()
    Stopping --> Stopped : join() + clear subscribers
    Stopped --> [*]
```

## TimerEvent Scheduling Loop
```mermaid
sequenceDiagram
    participant Init as TimerEvent.__init__
    participant Base as EventThread.__init__
    participant Timer as threading.Timer
    participant Done as threading.Event
    participant Dispatcher as EventThread.__post

    Init->>Base: super().__init__(interval=..., **kwargs)
    Init->>Done: instantiate (unset)
    Init->>Timer: create(function=__run, interval, **kwargs)
    Init->>Timer: start()
    loop while not Done.is_set()
        Timer->>Init: __run()
        Init->>Dispatcher: post(time())
    end
    Init->>Done: set() on stop()
    Init->>Base: super().stop()
    Init->>Timer: join()
```

## Data Structures & Concurrency Notes
- **Packet Template (`__packet`)** – Mutable dictionary seeded during construction (`event`, optional metadata). Each `post` copies the template, merges overrides, and writes the current `payload`.
- **Subscriber Registry (`__subscribers`)** – Maps subscriber name to a dictionary containing `on_event` and `cookie`. Access is serialized with `__lock` for modifications but iteration occurs without taking a snapshot.
- **Queue (`__queue`)** – Unbounded `queue.Queue` used to hand off work between producers and the dispatcher thread.
- **Flags** – `__continue_thread` governs the dispatcher loop; `__pause_broadcasting` toggled by `pause()` / `unpause()` without locking in the latter.
- **Timer Coordination** – `TimerEvent` retains arbitrary `**kwargs` both for packet defaults and for `threading.Timer`, so callers must avoid keys unsupported by the timer constructor.

## Known Limitations (Informing Future Work)
- Dispatcher iterates over `__subscribers` while holding no lock; concurrent modification can raise `RuntimeError`.
- Paused events are discarded permanently; there is no buffering or backpressure mechanism.
- Callback exceptions propagate and terminate the dispatcher thread.
- `TimerEvent` begins emitting immediately upon construction and cannot restart once stopped.
