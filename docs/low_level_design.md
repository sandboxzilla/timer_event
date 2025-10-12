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
        -__running: bool
        -__paused: bool
        -__pause_event: threading.Event
        -__lock: Lock
        -__queue: Queue
        -__max_queue_size: int
        -__overflow_policy: str
        -__error_policy: str
        -__on_error: Optional[Callable]
        -__on_dispatch: Optional[Callable]
        +__init__(name: str, max_queue_size: Optional[int] = None, ...)
        +subscribe(name: str, on_event: Callable, cookie: Any = None) SubscriptionHandle
        +unsubscribe(name: str)
        +post(payload, **kwargs)
        +__call__(payload, **kwargs)
        +__iadd__(handler)
        +__isub__(handler)
        +pause()
        +unpause()
        +stop(wait: bool = True)
        +subscriber_count: int
        +queue_size: int
        +max_queue_size: Optional[int]
        +__enter__()
        +__exit__()
        -__post()
        -__notify_dispatch()
    }
    class TimerEvent {
        -__kwargs: dict
        -__interval: float
        -__interval_lock: threading.Lock
        -__done: threading.Event
        -__wake: threading.Event
        -__ticker_lock: threading.Lock
        -__ticker_thread: Optional[threading.Thread]
        -__ticker_started: bool
        -__emit_immediately: bool
        +__init__(interval: float, name: str = None, auto_start: bool = True, **kwargs)
        +start_timer()
        +change_interval(interval: float, apply_immediately: bool = False)
        +stop(wait: bool = True)
        +is_timer_running()
        +__enter__()
        -__run_loop()
        -__current_interval()
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
        alt stop sentinel
            Dispatcher->>Dispatcher: break
        else
            opt paused
                Dispatcher->>PauseEvent: wait()
            end
            loop for name, handler in Registry
                Dispatcher->>Dispatcher: clone packet
                Dispatcher->>Callback: handler(packet_copy)
                opt metrics
                    Dispatcher->>Metrics: on_dispatch(subscriber, packet copy)
                end
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
    participant Ticker as internal ticker thread
    participant Wake as wake event
    participant Done as stop event
    participant Dispatcher as EventThread.__post

    Init->>Base: super().__init__(interval=..., **kwargs)
    Init->>Ticker: start_timer() (auto-start optional)
    loop until Done set
        Ticker->>Wake: wait(current interval)
        alt wake triggered
            Wake->>Ticker: interval changed or stop requested
            opt emit immediately
                Ticker->>Dispatcher: post(time())
            end
        else interval elapsed
            Ticker->>Dispatcher: post(time())
        end
    end
    Init->>Done: set()
    Init->>Base: super().stop()
```

## Data Structures & Concurrency Notes
- **Packet Template (`__packet`)** – Mutable dictionary seeded during construction (`event`, optional metadata). Each `post` copies the template, merges overrides, and writes the current `payload`.
- **Subscriber Registry (`__subscribers`)** – Maps subscriber name to a dictionary containing `on_event` and `cookie`. Access is serialized with `__lock`; the dispatcher snapshots the mapping before iterating to tolerate concurrent subscription churn.
- **Queue (`__queue`)** – `queue.Queue` whose `maxsize` is governed by `max_queue_size`; overflow policy determines whether writers block, drop packets, or raise.
- **Pause Control** – `__pause_event` gates dispatch; while cleared, the dispatcher blocks before invoking subscribers but continues accepting posts into the queue.
- **Error Handling** – `__error_policy` chooses between continuing, stopping, or re-raising on subscriber failure; `__on_error` is invoked on each exception.
- **Metrics Hook** – optional `on_dispatch` callback executes after each successful subscriber invocation, receiving a copy of the packet for external observability.
- **Timer Coordination** – `TimerEvent` drives posting through a dedicated ticker thread that waits on `__wake`/`__done` events and respects runtime interval changes.

## Known Limitations (Informing Future Work)
- `queue_size` relies on `Queue.qsize()`, which is an approximation on some Python implementations; treat it as advisory telemetry.
- `on_dispatch` exceptions are logged but otherwise ignored to preserve delivery guarantees.
- `TimerEvent` instances cannot be restarted once `stop()` (or context exit) has been invoked; construct a new timer instead.
