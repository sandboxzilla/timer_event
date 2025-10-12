# Timer Event

Lightweight, thread-safe helpers for broadcasting events and emitting recurring callbacks in Python.

## Features
- `EventThread` runs a dispatcher thread so producers can `post()` payloads without blocking.
- Configurable queue controls: set `max_queue_size`, choose overflow behaviour (`block`, `drop_newest`, `drop_oldest`, `error`), and pause dispatch without losing buffered events.
- Error policies and hooks let you decide how to react when a subscriber raises (`continue`, `stop`, `raise`, plus optional `on_error` callback) and collect metrics through `on_dispatch`.
- `TimerEvent` extends `EventThread` with a controllable ticker: lazy start, dynamic `change_interval`, and shared queue/error semantics.
- Context manager support (`with EventThread(...)`) guarantees `stop()` on exit, while `subscribe()` returns lightweight handles and introspection properties (`is_running`, `queue_size`, etc.) keep monitoring simple.

## Install
```bash
pip install -e .
```

## Quick Start
```python
from timer_event import EventThread, TimerEvent

def handle_packet(packet):
    print(packet["event"], packet["payload"], packet["cookie"])

with EventThread(
    "alerts",
    severity="info",
    max_queue_size=1024,
    overflow_policy="drop_oldest",
    error_policy="continue",
    on_dispatch=lambda name, packet: print("metrics", name),
) as bus, TimerEvent(interval=2.0, name="heartbeat", auto_start=False) as timer:
    printer = bus.subscribe("printer", handle_packet, cookie={"source": "demo"})
    bus.post({"msg": "something happened"})

    timer.start_timer()  # optional when auto_start=False
    timer.subscribe("tick", handle_packet)
    timer.change_interval(1.0, apply_immediately=True)

    # ... application logic ...

    printer.unsubscribe()
# Exiting the context automatically stops both dispatcher threads.
```

## Runtime Controls
- Inspect dispatcher state with `is_running`, `is_paused`, `subscriber_count`, and `queue_size`/`max_queue_size`.
- Use `stop(wait=False)` for fire-and-forget shutdowns or keep the default `wait=True` to drain the queue before exit.
- Attach lightweight metrics via `on_dispatch(subscriber, packet)` or failure hooks via `on_error`.

## Developer Workflow
- `python -m unittest discover -s tests -v` — run the regression suite.
- `python -m build` — create source and wheel distributions for release.

## Documentation
Detailed docs live in `docs/`. Start with:
- `architecture_overview.md` — system context and component map.
- `high_level_design.md` — goals, use cases, current capabilities.
- `low_level_design.md` — implementation walkthrough of the current release.
- `design_architecture_review.md` — historical review of pre-0.10.0 shortcomings and their remediation.
- `timer_event_manual.md` — man-page style usage reference (includes queue/error policy configuration).
- `AGENTS.md` — contributor guidelines.

## Contributing
Please read `AGENTS.md` for coding standards, testing expectations, and pull request tips.
