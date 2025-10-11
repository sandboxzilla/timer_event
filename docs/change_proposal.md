# Timer Event Change Proposal

## Executive Summary
`timer_event` v0.9.1 ships with critical threading and lifecycle defects that compromise reliability and developer ergonomics. This proposal delivers a staged programme of work that:
- Hardens core concurrency primitives (snapshot subscribers, clone packets, isolate callback failures).
- Introduces robust flow control (pause buffering, queue bounds, graceful stop).
- Replaces the tight coupling between construction and scheduling with a configurable timer engine.
- Enhances observability, configurability, and packaging hygiene so the library is easier to adopt and extend.
By executing the plan below in three stages, we can mitigate risk, maintain release cadence, and keep documentation current.

## Stage 1 — Core Stabilization (P0)
### Objectives
- Eliminate race conditions and handler interference.
- Ensure dispatcher threads survive callback failures.
- Provide lossless or predictable behaviour when pausing, resuming, and stopping.

### Deliverables
1. **Thread-Safe Dispatch**
   - Copy subscriber registry under lock before iterating.
   - Clone packet dictionaries (or convert to immutable structures) per handler.
2. **Error Isolation**
   - Wrap handler invocation in `try/except`, emit structured diagnostics, and expose a policy hook (`"continue"`, `"halt"`, `"raise"`).
3. **Pause & Stop Semantics**
   - Refactor `pause()` to buffer or block events (configurable).
   - Implement `stop(wait=True/False)` with queue draining options.
4. **Tests & Docs**
   - Add regression tests for races, error handling, and pause/stop behaviour.
   - Update README, manual, and design docs to reflect new guarantees.

### Success Criteria
- Dispatcher survives injected exceptions; callbacks after pause resume with no dropped events (unless configured otherwise).
- Test suite covers concurrent subscribe/unsubscribe scenarios.
- Documentation communicates updated semantics consistently.

## Stage 2 — Timer & API Evolution (P1)
### Objectives
- Decouple timer scheduling from constructor timing.
- Improve developer ergonomics for subscription management and introspection.

### Deliverables
1. **Timer Engine**
   - Replace `threading.Timer` with a managed loop that supports lazy `start()`, `stop()`, `change_interval()`, and pause-aware waiting.
   - Allow jitter or cron-like strategies via pluggable scheduler interface (optional stretch goal).
2. **Subscription Handles**
   - Return handle objects from `subscribe()` with `.unsubscribe()` and `.pause()` helpers; enforce unique names or eliminate name requirement.
3. **Lifecycle & Metrics**
   - Surface state inspection APIs (`is_running`, `is_paused`, `subscriber_count`, queue length).
   - Add logging/metrics hooks for callback duration and failures.
4. **Developer Experience**
   - Introduce context managers (`with TimerEvent(...) as timer:`) for safe setup/teardown.
   - Provide helper factories for common payload patterns.

### Success Criteria
- Timer can be instantiated without immediate emission; starting/stopping is explicit and deterministic.
- Subscription handles simplify usage and reduce naming collisions.
- Observability hooks allow external monitoring without modifying core code.

## Stage 3 — Packaging, Tooling, and Documentation (P2)
### Objectives
- Cement quality gates that keep the codebase healthy post-refactor.
- Align public artefacts (metadata, docs, examples) with the evolved design.

### Deliverables
1. **Tooling & CI**
   - Add linting (`ruff`/`flake8`) and formatting (`black`) to the workflow.
   - Configure automated tests (GitHub Actions) covering supported Python versions.
2. **Packaging Hygiene**
   - Fix metadata inconsistencies (`LICENSE`, bug tracker URL), publish updated wheels.
   - Provide changelog summarizing migration steps for downstream users.
3. **Documentation Refresh**
   - Update architecture/design documents to describe the new implementation, removing “Planned Changes” sections once complete.
   - Expand the manual with advanced scheduling examples, diagnostics usage, and migration guidance.
4. **Community Enablement**
   - Establish contribution templates, issue forms, and PR checklists aligned with the new workflows.

### Success Criteria
- CI pipeline runs formatting, linting, tests on every PR; failures block merges.
- Published package metadata passes `twine check` and reflects support matrix.
- Docs provide coherent, up-to-date guidance without referencing deprecated behaviour.

## Dependencies & Risks
- Stage 1 must complete before Stage 2 to avoid layering new features on unstable foundations.
- Timer engine redesign may surface additional edge cases; budget time for iterative testing.
- Introducing bounded queues and buffering policies can break existing assumptions; document defaults and migration paths carefully.

## Governance
- Maintain `docs/refactoring_plan.md` as the live status tracker.
- After each stage, cut a minor release (e.g., 0.10.0, 0.11.0, 1.0.0) and archive updated design docs.
- Encourage short-lived branches and incremental PRs to keep review load manageable.
