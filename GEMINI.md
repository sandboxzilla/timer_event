# Gemini Project Context: timer_event

## Project Overview

This project, `timer_event`, is a lightweight Python library for thread-safe, event-driven programming. It provides two main classes:

*   `EventThread`: A thread-backed publisher/subscriber model that allows for non-blocking event posting and processing. It supports features like configurable queue sizes, overflow policies, and error handling.
*   `TimerEvent`: A subclass of `EventThread` that adds the functionality of emitting events at a regular interval.

The project is written in Python and is designed to be used as a library in other Python applications. It has no external dependencies.

## Building and Running

*   **Installation:** To install the package in editable mode, run:
    ```bash
    pip install -e .
    ```

*   **Running Tests:** To run the test suite, use the following command:
    ```bash
    python -m unittest discover -s tests -v
    ```

*   **Building:** To build the source and wheel distributions for release, run:
    ```bash
    python -m build
    ```

## Development Conventions

*   **Coding Style:** The project follows PEP 8, with 4-space indentation and `lower_snake_case` for variable and function names.
*   **Documentation:** Docstrings are used to explain the purpose and usage of modules and classes. Type hints are encouraged.
*   **Testing:** The project uses the standard `unittest` framework. Tests are located in the `tests/` directory and are named `test_<module>.py`. Tests should be deterministic and avoid long sleep intervals.
*   **Commits and PRs:** Commit messages should have a concise, Title Case subject line. Pull requests should include a description of the changes, reproduction steps for bugs, and details on new or updated tests.
*   **Thread Safety:** The library is designed to be thread-safe. Shared state is protected with `threading.Lock` or `queue.Queue`. Callbacks run on the event broadcaster thread, so long-running operations should be handled in the background to avoid blocking.

## QA Process

For detailed information on the QA process, bug reporting policy, and formatting guidelines, please refer to the `docs/qa_policy.md` document.