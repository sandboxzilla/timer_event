# Timer Event

Lightweight, thread-safe helpers for broadcasting events and emitting recurring callbacks in Python.

## Features
- `EventThread` runs a dispatcher thread so producers can `post()` payloads without blocking.
- `TimerEvent` extends `EventThread` with a fixed-interval timer that posts the current timestamp as soon as the instance is constructed.
- Subscriber cookies and per-post overrides let you enrich packets with contextual metadata.

## Install
```bash
pip install -e .
```

## Quick Start
```python
from timer_event import EventThread, TimerEvent

bus = EventThread("alerts", severity="info")

def handle(packet):
    print(packet["event"], packet["payload"], packet["cookie"])

bus.subscribe("printer", handle, cookie={"source": "demo"})
bus.post({"msg": "something happened"})

timer = TimerEvent(interval=2.0, name="heartbeat")
timer.subscribe("tick", handle)
# TimerEvent starts its internal threads immediately; no explicit start() call.

# ... application logic ...

timer.stop()  # Always stop timers to release threads.
bus.stop()    # EventThread instances cannot be restarted once stopped.
```

## Developer Workflow
- `python -m unittest discover -s tests -v` — run the regression suite.
- `python -m build` — create source and wheel distributions for release.

## Documentation
Detailed docs live in `docs/`. Start with:
- `architecture_overview.md` — system context and component map.
- `high_level_design.md` — goals, use cases, current capabilities.
- `low_level_design.md` — implementation walkthrough of the current release.
- `design_architecture_review.md` — prioritized remediation plan for known flaws (race conditions, pause semantics, error handling).
- `timer_event_manual.md` — man-page style usage reference.
- `AGENTS.md` — contributor guidelines.

## Contributing
Please read `AGENTS.md` for coding standards, testing expectations, and pull request tips.
