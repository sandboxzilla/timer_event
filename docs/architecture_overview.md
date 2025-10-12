# Timer Event Architecture Overview

## Purpose
The `timer_event` package provides a lightweight event-bus abstraction backed by Python threads. It targets small services and desktop utilities that need to broadcast arbitrary payloads (events) to callbacks and, optionally, emit them on a fixed cadence.

## System Context
- **Clients** import `EventThread` or `TimerEvent` and register callbacks.
- **TimerEvent** extends the event bus to schedule periodic emissions using the standard library (`threading.Timer`, `threading.Event`, `queue.Queue`).
- No external services are required; all side effects are confined to in-process threads.

## Component Breakdown
| Component | Responsibility | Key Collaborators |
|-----------|----------------|-------------------|
| `EventThread` | Manages subscriber registry, enqueues payloads, broadcasts packets on a background thread; returns subscription handles for lifecycle management. | `queue.Queue`, `threading.Thread`, client callbacks |
| `TimerEvent` | Builds on `EventThread` to post timestamps via an internal ticker thread with changeable intervals. | `threading.Event`, `threading.Thread`, `time.time` |
| Tests (`tests/`) | Validate subscription, timer cadence, pause/unpause, stop behavior. | `unittest`, real-time sleeps |
| Packaging (`pyproject.toml`, `setup.cfg`, `setup.py`) | Distribute library to PyPI-compatible tooling. | `setuptools`, PEP 517 |

## Thread Model
1. **Producer threads** (callers of `post`) enqueue packets in `EventThread.__queue`.
2. **Dispatcher thread** (created inside `EventThread.__init__`) drains the queue and invokes each subscriber sequentially.
3. **Timer thread** (`threading.Timer`) inside `TimerEvent` repeatedly calls the dispatcher via `post(time())`.
4. Optional **client threads** run callback logic; long-running operations must be handled carefully to avoid blocking other subscribers.

## Data Flow
```
Client code -> EventThread.post(payload) -> Queue -> Dispatcher thread
Dispatcher thread -> Subscriber registry -> Callback(packet dict)
TimerEvent -> ticker thread -> EventThread.post(current_time)
```
Packets are simple dictionaries combining defaults provided at construction with per-post overrides and runtime metadata (`event`, `dest`, `payload`, `cookie`).

## Operational Considerations
- `pause()` and `unpause()` control a synchronisation gate; while paused, the dispatcher thread blocks and buffered events accumulate according to the configured `overflow_policy` (`block`, `drop_newest`, `drop_oldest`, `error`).
- `stop(wait=True)` signals the dispatcher with an internal sentinel, drains the queue, and joins the worker thread; pass `wait=False` for non-blocking shutdown. A stopped instance cannot be restarted.
- `error_policy` governs subscriber failures: continue (default), stop the dispatcher, or re-raise to callers. Optional hooks `on_error` and `on_dispatch` expose structured diagnostics for failures and successes respectively.
- Inspect runtime state via `subscriber_count`, `queue_size`, `max_queue_size`, `is_running`, and `is_paused`.
- Threads start automatically when objects are constructed; context managers (`with EventThread(...)`) guarantee cleanup even on exceptional exits.

## Future Evolution Hooks
- Introduce structured event objects instead of raw dicts to improve type safety.
- Add optional scheduling strategies (cron/jitter) via pluggable timer backends.
- Build first-class observability adapters (metrics/log sinks) on top of the `on_dispatch`/`on_error` hooks.

## Planned Changes
Remaining actions (aligned with the P2 roadmap):
- Add automated packaging/tooling checks (lint, format, CI) to preserve the new guarantees.
- Expand documentation with context-manager recipes, diagnostics guidance, and advanced scheduling examples.
- Formalize observability integrations (metrics/log exports) using the existing hook surface.
