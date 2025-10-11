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
| `EventThread` | Manages subscriber registry, enqueues payloads, broadcasts packets on a background thread. | `queue.Queue`, `threading.Thread`, client callbacks |
| `TimerEvent` | Builds on `EventThread` to post timestamps at a configured interval. | `threading.Timer`, `threading.Event` (`Done`) |
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
TimerEvent -> threading.Timer -> EventThread.post(current_time)
```
Packets are simple dictionaries combining defaults provided at construction with per-post overrides and runtime metadata (`event`, `dest`, `payload`, `cookie`).

## Operational Considerations
- `pause()` and `unpause()` flip a flag checked by the dispatcher; during pause, events are discarded. Consumers that need lossless behavior must drain queue before pausing.
- `stop()` signals the dispatcher to exit, posts a sentinel (`payload=None`), waits for thread termination, and clears subscribers. A stopped instance cannot be restarted.
- Threads start automatically when objects are constructed. If clients must delay dispatch, they should modify the classes or guard subscriber registration carefully.

## Future Evolution Hooks
- Introduce structured event objects instead of raw dicts to improve type safety.
- Add lifecycle introspection (`is_running`, queue size) for observability.
- Support alternative scheduling strategies (crontab expressions, jitter control) via pluggable timer backends.

## Planned Changes
Pulled from `design_architecture_review.md` and `refactoring_plan.md`:
- Harden dispatcher thread-safety by snapshotting subscribers, copying packets per handler, and insulating callback failures.
- Redesign pause and queue management to support buffering/backpressure and graceful drains on `stop()`.
- Replace the `threading.Timer` dependency with an internal scheduler loop that allows lazy start, dynamic intervals, and synchronized pause/resume.
- Expose richer lifecycle and observability hooks (subscriber counts, queue depth, metrics/log callbacks).
- Standardize packaging metadata and CI automation to keep the architecture verifiable over time.
