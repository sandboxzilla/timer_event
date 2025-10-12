# Timer Event Refactoring Plan

This plan operationalizes the recommendations captured in `design_architecture_review.md`. Items are grouped by theme and should be addressed roughly in the order listed. Update the status column as work progresses.

> **Status (2025-10-12):** Stage P0 and P1 work shipped and the entries below remain for historical context. Only P2 items are still active.

| Priority | Area | Action | Status |
|----------|------|--------|--------|
| P0 | Thread Safety | Snapshot subscribers under lock and clone packets per callback to prevent race conditions. | DONE |
| P0 | Thread Safety | Wrap callback execution in `try/except`, report failures, and allow policy configuration (continue vs. halt). | DONE |
| P0 | Event Flow | Redesign `pause()` to buffer or block instead of dropping events; add optional queue bounds and overflow modes. | DONE |
| P1 | Event Flow | Support graceful `stop(wait=True)` semantics that drain remaining events before shutdown. | DONE |
| P1 | Timer Scheduling | Replace `threading.Timer` with a controllable loop that supports lazy start, interval changes, and pause synchronization. | DONE |
| P1 | API Ergonomics | Provide subscription handles or enforce unique names with explicit errors; expose `is_paused`/`subscriber_count`. | DONE |
| P2 | Observability | Surface metrics/log hooks for queue depth, callback duration, and error counts. | TODO |
| P2 | Packaging | Reconcile metadata (`LICENSE`, bug tracker URL) and add lint/test automation (`ruff`, `black`, CI). | TODO |
| P2 | Docs & Examples | Refresh README and docs once refactor lands; add context manager examples and timer lifecycle diagrams. | IN PROGRESS |

## Execution Notes
- Implement and merge changes in small, well-tested increments; update this table and the design documents after each milestone.
- Add regression coverage for each behavioural fix (pause buffering, exception handling, timer lifecycle, queue overflow).
- Keep `design_architecture_review.md` as the authoritative rationale; this plan focuses on execution ordering.
