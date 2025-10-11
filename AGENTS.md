# Repository Guidelines

## Project Structure & Module Organization
Core package code lives in `src/timer_event/`: `event_thread.py` implements the thread-backed publisher, `timer_event.py` adds interval scheduling, and `__init__.py` exposes the public API. Tests reside in `tests/` and mirror the module names (`test_event_thread.py`, `test_timer_event.py`) to keep coverage aligned with features. Reference materials and design notes belong in `docs/`, while project-wide metadata is in `pyproject.toml`, `setup.cfg`, and `README.md`. Keep any new assets colocated with the component they support and document non-obvious paths inside `README.md` or `docs/`.

## Build, Test, and Development Commands
- `pip install -e .` installs the package in editable mode so local changes are importable immediately.
- `python -m build` creates source and wheel artifacts; run it before publishing a release.
- `python -m unittest discover -s tests -v` executes the current regression suite; add `-k pattern` when iterating on a single class.
- `python -m timer_event.timer_event` can be used in a scratch script to smoke-test timers; keep examples inside `docs/` or `tests/fixtures`.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation and descriptive, lower_snake_case symbols. Public classes should include module-level docstrings that explain threading semantics and expected payload structure. Type hints, dataclass-style dictionaries, and short comments (one line) are encouraged when they clarify packet formats or locking expectations. Export new symbols through `src/timer_event/__init__.py` to maintain a clean top-level API.

## Testing Guidelines
Use the standard-library `unittest` framework already present in `tests/`. Name new files `test_<module>.py` and test methods `test_<behavior>` so they auto-discover cleanly. Favor deterministic tests: keep sleep intervals minimal, guard against race conditions with synchronization primitives, and assert both subscriber side effects and thread teardown (e.g., call `stop()`).

## Commit & Pull Request Guidelines
Recent history favors concise, Title Case subject lines (e.g., “Add Timer Cleanup Hook”); keep them under ~70 characters and use present tense. Reference issues inline (`Fix race in TimerEvent (#45)`) and describe behavioral changes plus test coverage in the commit body or PR description. Each PR should note reproduction steps, new/updated tests, documentation updates, and any concurrency implications or cleanup steps for the reviewers.

## Thread Safety & Runtime Tips
Callbacks run on the event broadcaster thread, so avoid long I/O or acquire locks that could deadlock; wrap slow work in background tasks instead. Always pair `start()` with `stop()` in examples, fixtures, and tests to prevent orphaned threads. When introducing shared state, protect it with `threading.Lock` or queues and document the contract so downstream agents can extend the system safely.
