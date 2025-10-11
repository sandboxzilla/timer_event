# Timer Event Low-Level Design

> **Document scope:** Describes the current implementation prior to the refactor outlined in `design_architecture_review.md`. Behavior noted here (e.g., lossy pause, lack of exception handling) is known to be problematic and scheduled for correction.

## Module: `src/timer_event/event_thread.py`
### Class `EventThread(Thread)`
- **Constructor**
  - Parameters: `name: str`, `**kwargs` (default packet fields).
  - Initializes a `Lock`, populates `__packet` defaults (`event`, `dest`, `payload`, `cookie`), creates empty subscriber dict, queue (`Queue()`), flags (`__continue_thread=True`, `__pause_broadcasting=False`), and starts the thread by calling `Thread.__init__` with `target=self.__post` followed by `self.start()`.
- **Private State**
  - `__packet: dict` – template dictionary copied per post.
  - `__subscribers: Dict[str, Dict[str, Any]]` – maps subscriber name to handler info (`on_event`, `cookie`).
  - `__queue: Queue` – unbounded FIFO of packet dictionaries.
  - `__lock: Lock` – guards subscriber and template mutation.
  - Flags: `__continue_thread`, `__pause_broadcasting`.
- **Public Methods**
  - `subscribe(name, on_event, cookie=None) -> EventThread`: Inserts handler dict under lock.
  - `unsubscribe(name) -> EventThread`: Removes entry if present.
  - `post(payload, **kwargs) -> EventThread`: Copies `__packet`, merges overrides, sets `payload`, enqueues via `put_nowait`.
  - `pause()/unpause() -> EventThread`: Flip pause flag (`unpause` lacks locking).
  - `stop() -> None`: Sets continue flag false, enqueues sentinel (`payload=None`), joins thread, clears subscribers.
  - Operator overloads `__call__`, `__iadd__`, `__isub__` to support shorthand posting and subscription.
- **Dispatcher Loop (`__post`)**
  - Runs until `__continue_thread` is false.
  - Retrieves packet with `queue.get()`.
  - If `payload is not None` and not paused: iterates `__subscribers.items()`, mutates `packet["dest"]`/`["cookie"]`, invokes callback.
  - If paused, discards packet silently (no requeue).

## Module: `src/timer_event/timer_event.py`
### Class `TimerEvent(EventThread)`
- **Constructor**
  - Parameters: `interval: float`, `name: Optional[str] = None`, `**kwargs`.
  - Validates interval ≥ 0, stores `__kwargs`, derives default name (`"{interval}sRepeatingTimer"`), initializes `__done = threading.Event()`.
  - Calls `super().__init__(name=name, interval=interval, **__kwargs)` to seed packet template with interval.
  - Creates `__timer = threading.Timer(interval=interval, function=self.__run, **__kwargs)` and starts it immediately.
- **Private State**
  - `__interval: float` – polling period.
  - `__kwargs: dict` – reused for both packet defaults and Timer kwargs.
  - `__done: threading.Event` – signals shutdown.
  - `__timer: threading.Timer` – periodic driver.
- **Private Methods**
  - `__run()`: While not `__done.is_set()`, calls `self.post(time())`, then waits on `__done` for interval seconds.
- **Public Overrides**
  - `stop()`: Sets `__done`, calls `super().stop()` to halt dispatcher, joins timer thread.

## Module: `src/timer_event/__init__.py`
- Re-exports `EventThread` and `TimerEvent`.
- Contains package metadata/docstring.

## Data Structures & Packet Format
- Packet dictionary keys:
  - `event`: event name (string from constructor).
  - `dest`: subscriber name currently being invoked (mutated per callback).
  - `payload`: opaque client-supplied object or timer timestamp.
  - `cookie`: arbitrary object attached during subscription.
  - Additional custom keys inserted via constructor kwargs or `post` overrides.

## Error & State Handling
- No explicit error propagation; callback exceptions bubble up and terminate dispatcher.
- Queue operations are non-blocking (`put_nowait`), which raises `queue.Full` if a bounded queue is introduced later.
- `stop()` can be called multiple times; only first invocation performs shutdown logic.
- There is no explicit restart; new instance required after `stop()`.

## Extension Points
- Override `EventThread.__post` to change broadcasting semantics.
- Subclass `TimerEvent` to alter payload contents (e.g., computed metrics) or scheduling strategy by overriding `__run`.
- Wrap `post` to transform payloads (serialization, validation) before enqueueing.

## Pending Refactor Checklist
Referencing `design_architecture_review.md`, planned low-level changes include:
- Guard subscriber iteration with copies and per-callback packet cloning.
- Introduce structured error handling around callbacks.
- Rework pause/stop to buffer or drain events rather than dropping them.
- Replace `threading.Timer` usage with a controllable loop that supports lazy start and dynamic intervals.
This checklist should be updated as each item is implemented so the document remains a faithful representation of the code.
