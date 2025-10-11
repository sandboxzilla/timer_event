# Timer Event High-Level Design (2025-10-11)

## System Context
The `timer_event` package runs entirely within a single Python process. Client threads create `EventThread` or `TimerEvent` instances, post payloads, and receive callbacks on library-managed threads. The implementation depends on the Python standard library (`threading`, `queue`, `time`) and has no external service requirements.

```mermaid
flowchart LR
    subgraph Client Threads
        A[Publisher Thread]
        B[Consumer Modules]
    end
    subgraph timer_event Library
        C(EventThread Dispatcher Thread)
        D[[queue.Queue]]
        E[[Subscriber Callback Registry]]
    end
    subgraph Standard Library
        F(threading.Timer)
        G(threading.Event<br/>(Timer Done))
    end

    A -->|post(payload)| D
    D --> C
    C -->|invoke(packet)| B
    B -.->|subscribe() / unsubscribe()| E
    E -.-> C
    F -->|time tick| C
    G -.-> F
    B -.->|pause()/stop()| C
```

## Core Responsibilities
- **EventThread** – Owns the dispatcher thread, queue, and subscriber registry. Accepts posts from any thread and forwards packets to each subscriber sequentially.
- **TimerEvent** – Subclass of `EventThread` that schedules periodic posts using `threading.Timer` and coordinates shutdown through `threading.Event`.
- **Subscribers** – Client-provided callables invoked with the packet dictionary assembled by `EventThread`.

## Event Dispatch Sequence
```mermaid
sequenceDiagram
    participant Publisher as Publisher Thread
    participant EventThread as EventThread.post()
    participant Queue as queue.Queue
    participant Dispatcher as Dispatcher Thread (__post)
    participant Subscriber as Subscriber Callback

    Publisher->>EventThread: post(payload, **overrides)
    EventThread->>EventThread: merge template + overrides
    EventThread->>Queue: put_nowait(packet)
    Dispatcher->>Queue: get()
    alt payload is not None AND not paused
        loop for each subscriber
            Dispatcher->>Subscriber: on_event(packet with dest/cookie)
        end
    else paused or null payload
        Dispatcher->>Dispatcher: discard packet
    end
```

## Timer-Driven Flow
```mermaid
sequenceDiagram
    participant Caller as Caller
    participant TimerEvent as TimerEvent.__init__
    participant Timer as threading.Timer
    participant Done as threading.Event
    participant Dispatcher as EventThread Dispatcher

    Caller->>TimerEvent: TimerEvent(interval, name?, **kwargs)
    TimerEvent->>Dispatcher: super().__init__(interval=..., **kwargs)
    TimerEvent->>Timer: start(function=__run, interval)
    loop every interval
        Timer->>TimerEvent: __run()
        TimerEvent->>Dispatcher: post(time())
    end
    Caller->>TimerEvent: stop()
    TimerEvent->>Done: set()
    TimerEvent->>Dispatcher: super().stop()
    TimerEvent->>Timer: join()
```

## Deployment & Integration Considerations
- All callbacks execute on the dispatcher thread. Long-running or blocking work should be delegated to worker pools to prevent stalling other subscribers.
- Pausing currently drops queued packets; use `stop()` when lossless shutdown is required.
- Each `TimerEvent` instance creates both a dispatcher thread (inherited) and a dedicated `threading.Timer` thread; budget thread resources accordingly.
- The package is thread-safe at the API boundary (queue protects posts), but subscriber mutation during dispatch shares the packet object and must be handled carefully by consumers.
