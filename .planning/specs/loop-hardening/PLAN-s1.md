---
date: 2026-06-21
spec: loop-hardening
sprint: S1 — Live telemetry → dashboard tails reality
status: FROZEN — partitions S1 into disjoint slices for an orchestrated foreground-parallel build
roadmapRef: ./ROADMAP.md · baseline: v0.1.0-alpha.2 (3ed18d3)
closes: G1 (no live board/state) · G2 (dashboard never tailed reality)
tags: [plan, loop-hardening, sprint-s1, telemetry, dashboard, heartbeats, frozen]
---

# S1 — Live telemetry → the dashboard tails reality · frozen PLAN

Make a real orchestrated run **emit** the coordination board + state, with **PROGRESS heartbeats** for smooth
live bars, and make the dashboard render it **accurately and in real time** — plus a **replay/demo driver** so the
operator can watch it animate immediately. New title **改善の型**. Two disjoint slices, Sonnet workers in isolated
worktrees → integration gate → fresh-context `kata-evaluate`. **After S1: STOP for operator demo.**

## LOCKED decisions (do NOT re-decide)
- **PROGRESS heartbeat is a new board TYPE (opt-in, ignored by coordination logic).** Line stays the 5-field
  `protocol/board.md` shape: `<utc> | <agent> | PROGRESS | <task> | <step>/<n> <label>` (the `msg` field carries
  `<step>/<n> <label>`, e.g. `3/5 writing tests`). Only the dashboard reads it.
- **Single-writer state (L3 preserved):** ONLY the orchestrator writes `.kata/state.json` (atomic). Workers ONLY
  append to `.kata/board.md`. The emitter library enforces this separation by having distinct functions.
- **Smooth-bar mapping (frozen contract both slices build against):** for an `in-progress` task that has a latest
  `PROGRESS` heartbeat `step/n`, `percent = round(step / n * 100)` (clamp 0–100). With no heartbeat, fall back to
  the existing stepped `status_to_percent`. Other statuses keep their stepped values.
- **Title:** dashboard header text = `KATAHARNESS ⛩ 改善の型` (kaizen no kata = "the Improvement Kata").
- **Observer stays read-only;** the emitter is the only writer to `.kata/`. BC: absent the emitter, the dashboard
  still works on a stepped board (no heartbeats) and the harness behaves as today.

## Wave DAG
```
Wave 1 (parallel):  S1a telemetry-emitter ──┐
                    S1b dashboard-heartbeats+title+demo ──┘   (disjoint files; build against the frozen
Integration:        octopus-merge → pytest + validator → LIVE demo (replay driver animates the dashboard)    PROGRESS contract)
                    → fresh-context kata-evaluate
```

## Task S1a — telemetry emitter + the PROGRESS board type
**Owns (disjoint):** `tools/kata_board.py` (NEW), `tools/tests/test_kata_board.py` (NEW), `protocol/board.md` (EDIT).
**read_first:** `protocol/board.md`, `protocol/state.md`, this PLAN's LOCKED section.
**action:** Build `kata_board.py` — the single emitter both orchestrator and workers use to write the coordination
files (composes nothing; pure file I/O with a `..`-guard like `gate_emit`):
- `append_event(kata_dir, agent, type, task, msg)` → append one `protocol/board.md` line (ISO-UTC now); create
  `board.md` if absent. `append_progress(kata_dir, agent, task, step, n, label)` → convenience wrapping
  `append_event` with `type="PROGRESS"`, `msg=f"{step}/{n} {label}"`.
- `write_state(kata_dir, state)` → **atomic** single-writer write of `.kata/state.json` (write temp + replace).
  `update_task(kata_dir, state, task, status)` convenience that mutates a task's status and re-writes (orchestrator
  use). Enforce the worker/orchestrator split in docstrings (workers call append_*; only orchestrator calls
  write_state/update_task).
- `protocol/board.md` (EDIT): add the **`PROGRESS`** TYPE row (Author: worker; Meaning: granular progress
  heartbeat; `msg` = `<step>/<n> <label>`) + a one-line note that it is **opt-in, ignored by coordination logic,
  read only by the dashboard** (no change to the DECISION/BLOCK/ESCALATE invariants).
**verify (default-FAIL):** `cd tools && uv run pytest tests/test_kata_board.py -q` (TDD red→green). Cover:
append_event writes a well-formed 5-field line + creates the file; append_progress formats `step/n label` and
TYPE=PROGRESS; write_state round-trips JSON atomically; update_task changes one task + preserves others; the
`..`-guard rejects a traversal `kata_dir`. Full suite + `validate_skills.py` stay green.
**acceptance:** a sequence of append_event/append_progress + write_state produces a `board.md` the dashboard model
can parse and a valid `state.json`; PROGRESS line matches the frozen format; single-writer separation documented.
**threat model:** writes only under the operator-supplied `kata_dir` (`..`-guard); no exec; the repo's own files.

## Task S1b — dashboard: heartbeat bars + new title + replay/demo driver
**Owns (disjoint):** `tools/kata_dash_model.py` (EDIT), `tools/kata_dash.py` (EDIT), `tools/kata_dash_demo.py`
(NEW), `tools/tests/test_kata_dash_model.py` (EDIT), `tools/tests/test_kata_dash_render.py` (EDIT),
`tools/tests/test_kata_dash_demo.py` (NEW).
**read_first:** the existing `kata_dash_model.py` + `kata_dash.py` + their tests, `protocol/board.md`, this PLAN's
LOCKED section (the PROGRESS format + smooth-bar mapping + title).
**action:**
- **`kata_dash_model.py`:** parse `PROGRESS` board lines; in `build_view_model`, for an `in-progress` task with a
  latest PROGRESS heartbeat, set `percent = round(step/n*100)` (clamp); no heartbeat ⇒ existing stepped value.
  Keep a `progressLabel` on the TaskRow if present (e.g. "writing tests") for display. Deterministic; extend tests.
- **`kata_dash.py`:** change the header text to `KATAHARNESS ⛩ 改善の型`; show the heartbeat `progressLabel` in the
  row status when present. No other behavior change. Update `test_kata_dash_render.py` (assert the new title +
  heartbeat label shows).
- **`tools/kata_dash_demo.py` (NEW):** a **replay driver** so the operator can watch the dashboard animate without
  a full harness run. `main(--kata-dir .kata --speed 1.0 --steps N)`: writes (via `kata_board`… but S1b can't
  import S1a in its worktree — so the demo driver writes board/state DIRECTLY using the same line/JSON shapes from
  the frozen contract, or imports `kata_board` lazily at integration) a realistic 2–3 worker run over ~20–30s:
  CLAIM → interleaved PROGRESS heartbeats (step/n climbing) → DONE → gated, with state.json updated each tick.
  This is what the operator runs in one terminal while `kata_dash.py` tails in another. Provide a `--once`
  self-check. Test it writes monotonic heartbeats + a parseable board (`test_kata_dash_demo.py`).
  *(Integration note: the demo driver SHOULD use `kata_board` from S1a once merged; in the S1b worktree, write the
  bytes directly per the frozen formats so the slice is testable alone — the integrator rewires it to call
  `kata_board` if cleaner.)*
**verify (default-FAIL):** `cd tools && uv run pytest tests/test_kata_dash_model.py tests/test_kata_dash_render.py
tests/test_kata_dash_demo.py -q` (red→green). Cover: heartbeat → smooth percent (e.g. 3/5 → 60), fallback to
stepped when no heartbeat, the new title string in build_frame, the demo driver emits monotonic PROGRESS +
parseable board. Full suite + validator stay green.
**acceptance:** a board containing `PROGRESS | … | 3/5 writing tests` yields a 60% bar with the label; the header
reads `改善の型`; the demo driver animates a believable run; existing dashboard behavior preserved (BC).
**threat model:** demo writes only under `--kata-dir` (`..`-guard); read-only render otherwise.

## Integration + the LIVE DEMO (the boundary artifact)
1. Octopus-merge `s1/emitter` + `s1/dashboard` → `s1/integration`. `uv sync` (no new deps expected).
2. Rewire `kata_dash_demo.py` to use `kata_board` (single source of truth) if the slices left it writing bytes
   directly. Full gate: `uv run pytest -q` (205 + new) · `validate_skills.py` 35/0 · Snyk (fix/doc-FP).
3. **Emit gate artifacts** via `gate_emit` (RESULT.json). **Fresh-context `kata-evaluate`** over this PLAN → PASS.
4. **Prep the live demo for the operator:** verify `uv run python tools/kata_dash_demo.py --kata-dir .kata` drives
   a board that `uv run python tools/kata_dash.py --kata-dir .kata` renders with **smoothly advancing bars +
   accurate state + the 改善の型 title**. Capture 2–3 snapshot frames (early/mid/done) in the REPORT so the
   transcript shows the progression, and give the operator the exact two-terminal commands to watch it live.
5. Merge to master only on the operator's S1 boundary nod (this sprint **stops for the demo**). Backout: tag
   `pre-s1` before merge.

## Ownership disjointness
| File | Owner |
|---|---|
| `tools/kata_board.py`, `tools/tests/test_kata_board.py`, `protocol/board.md` | S1a |
| `tools/kata_dash_model.py`, `tools/kata_dash.py`, `tools/kata_dash_demo.py`, `tools/tests/test_kata_dash_model.py`, `tools/tests/test_kata_dash_render.py`, `tools/tests/test_kata_dash_demo.py` | S1b |
| integration RESULT.json, demo rewire to kata_board | Integrator |
No file in two lanes. ✓
