# Timer Event Design & Architecture Review

> **Status (2025-10-12):** All high-priority findings documented here were addressed in the Stage P0/P1 refactors (see `src/timer_event/event_thread.py` and `src/timer_event/timer_event.py`). The review remains as a historical record of the pre-0.10.0 architecture.

## Scope
I reviewed the key source modules (`src/timer_event/event_thread.py`, `src/timer_event/timer_event.py`, `src/timer_event/__init__.py`), the unit tests under `tests/`, and the packaging/configuration files (`pyproject.toml`, `setup.cfg`, `setup.py`, `README.md`). The recommendations below target correctness, performance, extensibility, and day-to-day developer ergonomics. All actionable items have since been implemented unless they are explicitly called out in the Stage P2 plan.

## High-Priority Findings
- `EventThread` iterates through `__subscribers` without holding a lock, so concurrent subscribe/unsubscribe operations can raise `RuntimeError` or produce missed callbacks. It also reuses the same `packet` dict for every subscriber, letting one handler mutate the payload seen by others (`src/timer_event/event_thread.py:197`).
- Pausing simply drops queued events because the worker thread consumes messages while `_pause_broadcasting` is set (`src/timer_event/event_thread.py:200-212`), breaking expectations for consumers that rely on pause as a backpressure mechanism.
- Callback exceptions are not contained; one failing handler tears down the worker thread silently, halting the event system (`src/timer_event/event_thread.py:205`).
- `TimerEvent` starts both the worker and timer threads inside `__init__`, which can emit events before subscribers are attached and couples timer scheduling to constructor timing (`src/timer_event/timer_event.py:97-108`).
- Timer kwargs are reused both for the event packet and for constructing `threading.Timer`. Any user-provided packet metadata that is not a valid `Timer` keyword (e.g., `topic="audit"`) will raise at runtime (`src/timer_event/timer_event.py:100-107`).
- Tests rely on globals, tight loops, and multi-second sleeps, leading to flaky CI and slow feedback (`tests/test_timer_event.py`).

## Recommendations

### Thread-Safety Foundations
- Lock around subscriber iteration by copying `__subscribers` under `self.__lock` before broadcasting. This removes the mutation hazard and guarantees snapshot semantics.
- Emit per-subscriber packet copies (or immutable namedtuples/dataclasses) so handlers cannot interfere with each other; consider switching the payload delivered to callbacks to a lightweight value object.
- Wrap handler invocation in `try/except`, log failures, and optionally expose a hook so clients can monitor dropped callbacks. Add a configurable policy: stop-on-error vs. continue.
- Replace the manual thread inheritance with composition (`threading.Thread` managed internally). That allows lazy start, better daemon control, and easier unit testing.

### Event Flow Control
- Redesign `pause()` to either block dequeueing or buffer packets until `unpause()` is called. A simple approach is to hold items in an auxiliary list and flush them when resuming; an advanced option is a bounded queue with backpressure and `post(..., timeout=...)`.
- Provide an optional `max_queue_size` with overflow strategies (`drop_oldest`, `raise`, `block`) to prevent unbounded memory growth during slow subscriber processing.
- Support `stop(wait=True)` and `close()` semantics so consumers can choose to drain remaining events gracefully.

### Timer Scheduling Model
- Split timer configuration (interval, start delay, jitter) from event payload metadata so `TimerEvent` can accept rich packet defaults without colliding with `threading.Timer` kwargs. Internally, store timer arguments separately and pass only `args`/`kwargs` to the `Timer`.
- Replace `threading.Timer` with a dedicated loop thread that sleeps for `interval`, compensates for drift, and respects pause/resume without dropping events. This also enables features like variable intervals or cron-like schedules.
- Defer starting the timer until `start()` is called (or until the first subscriber attaches) to eliminate the subscription race.
- Expose `change_interval(new_interval, apply_immediately=True)` so callers can retune timers without rebuilding objects.

### API Ergonomics & Extensibility
- Return rich subscription handles (objects with `unsubscribe()`/`pause()` methods) instead of relying on string keys. If strings remain, enforce uniqueness and raise on duplicates to catch configuration errors early.
- Offer context manager helpers (e.g., `with TimerEvent(...) as timer:`) that guarantee `stop()` is invoked and make demos safer.
- Document and expose thread state (`is_running`, `is_paused`, `subscriber_count`) to aid monitoring and integration with diagnostics dashboards.

### Reliability & Testing
- Rewrite tests to use `unittest.mock` with deterministic synchronization primitives (`threading.Event`) instead of globals and busy-wait loops. Keep wall-clock sleeps under 100 ms to speed up CI.
- Add regression tests for pause buffering, error-handling policies, and subscription churn under load.
- Introduce linting (`ruff` or `flake8`) and formatting (`black`) to enforce style and catch docstring typos automatically. Integrate them into a simple `make check` (or `tox`) pipeline.

### Packaging & Documentation
- Fix packaging inconsistencies: point `setup.cfg` to the existing `LICENSE.txt`, correct the double-`https` typo in `pyproject.toml` bug tracker, and expand `setup.py` (or remove it in favor of declarative metadata).
- Provide an architectural overview in `docs/` illustrating the thread topology and lifecycle states (created → started → paused → stopped).
- Update examples in `README.md` to reflect the new API contracts once concurrency fixes land, showing proper cleanup and error-handling patterns.

## Suggested Roadmap
1. Stabilize the threading core (locking, buffering, exception policy) and refactor `TimerEvent` scheduling.
2. Backfill tests and CI/lint tooling to lock in behavior.
3. Enhance ergonomics (subscription handles, context managers) and publish refreshed documentation.
4. Iterate on advanced features (dynamic intervals, metrics hooks) once the foundation is rock solid.
