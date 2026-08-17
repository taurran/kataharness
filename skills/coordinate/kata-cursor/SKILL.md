---
name: kata-cursor
description: >-
  The run's one durable temporal record — the CURSOR. Append-only, one log per run: it marks where in
  the process the run is sitting and where it is currently executing. Use whenever agents must claim
  tasks, report done, heartbeat, or ESCALATE an unknown without re-planning, and whenever a contract
  needs to READ the run's position instead of remembering it. Carries the seam-authored PHASE /
  VERDICT / SPAWN / DOWN / DENY record alongside the worker/orchestrator lines.
license: Apache-2.0
version: 0.2.0
category: coordinate
status: beta
agnostic: true
cost-weight: 2
allowed-tools: [Read, Bash]
source: adapted-from Claude Agent Teams protocol (agnostic file reimplementation); CryptoPortfolioPlanner LESSONS-LEARNED L3
tags:
  - kata/coordinate
  - kata/spine
  - cursor
  - board
  - mailbox
  - escalation
  - protocol
---

# kata-cursor — one durable temporal record per run

**The concept is the CURSOR**: it marks where in the process the run is sitting and where it is
currently executing. Shared single-writer state corrupts under concurrency ([[LESSONS-LEARNED]] L3),
so the cursor is **append-only**: every agent *appends* a whole line; no one rewrites a prior line.
There is exactly **one log per run** — no sidecar structured log, no second journal, no git-only
cursor.

> **Heritage names, stated not tidied.** This skill and its contract completed the board→cursor
> rename (`kata-board` → `kata-cursor`, `protocol/board.md` → `protocol/cursor.md`). **The runtime
> file is still `.kata/board.md` and the engine module is still `tools/kata_board.py`** — no frozen
> task renames either, and both are code-level identities rather than prose. Read "board" in those
> two places as the heritage spelling of "cursor"; everywhere else the concept is the cursor.

## Schema — canonical in `protocol/cursor.md`, never restated divergently

`.kata/board.md` at the target repo's **integration/target-repo root** (machine state — separate
from durable Obsidian docs, [[STANDARDS]] §5), not a per-task worktree's `.kata/`. A run-header
block, then one event per line, append-only, newest last:

```
RUN <run-id>
[prev-run: <run-id>]      # iteration chain (re-loop / loop-back)
[parent-run: <run-id>]    # tree structure (child runs)
<utc> | <seq>[~<parent-seq>] | <agent-id> | <TYPE> | <task-id> | <one-line message>
```

`TYPE` is a closed enumeration across **three disjoint writer classes**:

| Class | TYPEs | Author |
|---|---|---|
| worker | `CLAIM` · `DONE` · `BLOCK` · `ESCALATE` · `NOTE` · `PROGRESS` | the working agent |
| orchestrator | `DECISION` | [[kata-orchestrate]] only |
| seam | `PHASE` · `VERDICT` · `SPAWN` · `DOWN` · `DENY` | `tools/kata_dispatch.py` only |

**The old 5-field grammar parses NOWHERE.** A pre-migration line
(`<utc> | <agent> | <TYPE> | <task> | <msg>`) is a parse **REFUSAL**, never a silent skip, and one
legacy line aborts the whole parse — a silently skipped row is an invisible hole in the audit
trail. Full definitions, the BNF, the payload rules, and the concurrency-evidence schema live in
`protocol/cursor.md`, which is the source of truth.

## Append — through the engine, never hand-rolled

`tools/kata_board.py` is the **single writer and single canonical parser**; a second parser is a
second source of truth. Append through it, not through `printf`/`Add-Content`:

```
# argv[1] = the run's .kata/ dir (integration root).
uv run --directory tools python - <abs-path-to-.kata> <<'PY'
import sys, kata_board
print(kata_board.append_event(sys.argv[1], "<agent-id>", "<TYPE>", "<task-id>", "<msg>"))
PY
```

Seam TYPEs are **never** appended this way. They come from the seam functions in
`tools/kata_dispatch.py` — `phase()` (PHASE), `mint()` (SPAWN), `capture()` (VERDICT / DOWN),
`deny()` (DENY) — and a worker that hand-writes one is authoring another class's TYPE.

## Reading position — the cursor, never context memory

A contract that needs to know where the run is **reads the cursor**. It does not recall what it
believes it just did; a conversational recollection is not a position and does not survive a
compaction, a crash, or a fresh subagent.

- `kata_dispatch.phase_state(cursor)` → `{"open": [...], "closed": [...], "runClosed": bool}` —
  the folded position. Pure: no clock, no filesystem.
- `kata_dispatch.is_run_closed(cursor)` — the terminal `run-closed` test.
- `kata_board.read_cursor(kata_dir)` — the parse. An unparseable cursor is a **refusal**, never a
  silently empty fold.

The phase vocabulary is closed: `INITIATION · GRILL · AUTHORING · FREEZE · EXECUTION (wave=<n>) ·
FINAL-GATE · CLOSEOUT · LOOP-BACK`, with msg grammar
`open <PHASE> [k=v …] | close <PHASE> [k=v …] | run-closed [k=v …]`.

## Discipline

- **Workers** may append `CLAIM` / `DONE` / `BLOCK` / `ESCALATE` / `NOTE` / `PROGRESS`. They MUST
  NOT append `DECISION` or any seam TYPE, and MUST NOT edit a prior line.
- **Workers never re-plan.** If the frozen plan is unclear or seems wrong, append `ESCALATE` with
  the exact ambiguity and STOP — do not improvise (this is the no-drift spine).
- **Orchestrator** ([[kata-orchestrate]]) reads the cursor each cycle and is the only author of
  `DECISION`. Every `BLOCK` / `ESCALATE` must be answered by a `DECISION` before that task resumes.
- **`PROGRESS` is a mandated liveness heartbeat (F3)** — one per owned module completed AND at
  least once per `livenessDeadline`/2 of wall-clock; `msg` carries `<modulesDone>/<modulesOwned>
  <label>`. It is **excluded from the coordination logic and from concurrency evidence**: a missing
  PROGRESS never gates a task, it only trips the liveness monitor's staleness path (nudge →
  escalate → human-gated re-dispatch; never a blind kill).
- **Claim model:** the orchestrator *assigns* tasks; workers do not self-select, so `CLAIM` is a
  worker *announcing* it started its assigned task — not a lock.
- **`VERDICT` requires a payload pointer.** A VERDICT line without one is refused on write and on
  read.
- **Children never write the parent's log.** The parent's seam writes the `DOWN` record by reading
  the child cursor's terminal state at the next parent seam act.
- **Ordering of record is `(runId, seq)` + parent fold-order; wall-clock is NEVER load-bearing.**
  The `utc` field is recorded for humans and is informational only.
- The cursor is the countable audit trail for the drift ledger: escalations, decisions, denials,
  and verdicts are evidence, not an agent's account of them.

## Run isolation

`.kata/board.md` holds **only the current run's events** — the seam rotates any pre-existing cursor
at run start (`kata_board.start_run`, called by `kata_dispatch.run_start`) before the header write.
Without that, prior-run `CLAIM`/`DONE` pairs would contaminate this run's concurrency evidence.
Rotation happens only at run **start**: a crash-resume adopts the existing header's `runId` and
continues on the same cursor. A *resume* MUST NOT rotate.
