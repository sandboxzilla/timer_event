# Timer Event High-Level Design

## Goals & Non-Goals
- **Goals**
  - Provide a simple API to publish events to multiple subscribers safely across threads.
  - Offer a reusable timer facility that emits events at fixed intervals without custom scheduling code.
  - Remain dependency-light and compatible with CPython ≥ 3.6.
- **Non-Goals**
  - Deliver distributed messaging, persistence, or guarantees beyond in-process delivery.
  - Handle complex orchestration (retry policies, durable queues, metrics) out of the box.

> **Document scope:** This file reflects the current implementation (v0.9.1). Known gaps and remediation priorities are tracked in `design_architecture_review.md`; see “Future Work” below for a consolidation of those actions.

## Key Use Cases
1. **Ad-hoc event hub**: A GUI or CLI tool broadcasts state changes to listeners while isolating callback execution from UI threads.
2. **Periodic metrics collection**: A background timer samples system state every N seconds and forwards results to subscribers that aggregate or log data.
3. **Plugin hooks**: Plugins register callbacks on startup and receive structured payloads when core code posts events.

## Major Components
- **EventThread**
  - Owns a bounded-unbounded queue (current implementation uses an unbounded `Queue`).
  - Spawns a dispatcher thread on construction.
  - Maintains subscriber dictionary keyed by logical names.
  - Provides lifecycle controls (`post`, `pause`, `unpause`, `stop`).
- **TimerEvent**
  - Extends `EventThread`.
  - Starts a `threading.Timer` loop that posts the current epoch time (float) to the queue every configured interval.
  - Uses a `threading.Event` (`__done`) to coordinate shutdown.

## High-Level Flow
```
Client registers callback -> EventThread stores handler
Client posts payload / TimerEvent fires -> payload enqueued
Dispatcher thread dequeues payload -> iterates subscribers -> invokes callback(packet)
```

## Failure Handling
- Dispatcher catches no exceptions today; a thrown exception exits the dispatcher thread.
- Pause merely sets a flag; packets consumed while paused are dropped.
- `stop()` sends sentinel payload (`None`) to exit the dispatcher.
Improvements: wrap callbacks in try/except, support retry/skip strategies, and retain queue items while paused.

## Extensibility Points
- Additional event metadata: allow custom packet factory or dataclass payload.
- Alternate timer backends: implement strategy pattern for scheduling (cron, exponential backoff).
- Diagnostics hooks: pass events through middleware for logging/metrics before callbacks run.

## Deployment & Integration Guidance
- Use in-process contexts (microservices worker threads, CLI tooling).
- For multi-process or networked signalling, pair with external brokers (e.g., Redis pub/sub) or use `multiprocessing.Queue`.
- Integrate with frameworks by wrapping subscription lifecycle in app startup/shutdown hooks to guarantee `stop()` is called.

## Future Work
The current architecture has critical shortcomings (unsynchronized iteration, lossy pause semantics, fragile timer lifecycle). The actionable plan lives in `design_architecture_review.md`; headline items include:
1. Harden dispatcher thread-safety (snapshot subscribers, copy packets, isolate callback failures).
2. Redesign pause/queue handling to support buffering and backpressure.
3. Detach timer scheduling from construction and tolerate richer packet metadata.
4. Expand diagnostics and context manager ergonomics.
These improvements should be reflected here once implemented; until then this document should be read alongside the review to avoid assuming guarantees the code cannot yet provide.
