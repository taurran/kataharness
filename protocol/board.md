# protocol/board.md — append-only coordination board schema

Canonical schema for the machine-coordination board consumed by [[kata-board]] and [[kata-orchestrate]].
Machine state — kept separate from durable Obsidian docs ([[STANDARDS]] §5).

- **Location:** `.kata/board.md` in the target repo's integration worktree.
- **Append-only:** agents append lines; no agent edits or deletes a prior line (no last-writer clobber —
  [[LESSONS-LEARNED]] L3).
- **Line format:** `<ISO-8601-UTC> | <agent-id> | <TYPE> | <task-id> | <one-line message>`
- **TYPE vocabulary:**
  | TYPE | Author | Meaning |
  |---|---|---|
  | `CLAIM` | worker | worker self-stamped start of a task — appended by the worker, with the worker's own process clock, to the shared `.kata/board.md` at the integration/target-repo root (not the per-task worktree's `.kata/`) |
  | `DONE` | worker | worker self-stamped end of a task — appended by the worker, with the worker's own process clock, to the shared `.kata/board.md` at the integration/target-repo root, after task `<verify>` passes; signals ready for the orchestrator gate |
  | `BLOCK` | worker | cannot proceed (environment/dependency) |
  | `ESCALATE` | worker | the frozen plan is unclear/wrong — needs an orchestrator decision (never re-plan) |
  | `NOTE` | worker | lateral info for peers |
  | `DECISION` | orchestrator only | a deliberate ruling resolving a BLOCK/ESCALATE |
  | `PROGRESS` | worker | granular progress heartbeat; `msg` carries `<step>/<n> <label>` (e.g. `3/5 writing tests`) |

`CLAIM`/`DONE` are the worker-self-stamped start/end of a task; because the worker authors them with its own process clock, the board is the artifact-of-record for concurrency (it does not depend on orchestrator-written timestamps).

- **PROGRESS is opt-in, ignored by the coordination logic, and read only by the dashboard** — the DECISION/BLOCK/ESCALATE invariants are unchanged.
- **Invariants:** workers never author `DECISION`; every `BLOCK`/`ESCALATE` is answered by a `DECISION`
  before the task resumes; the board is the countable audit trail for the drift ledger.

## Concurrency evidence (`.kata/concurrency.json`)

**Purpose.** Because board timestamps were historically written by the orchestrator, they correctly recorded
concurrency but could not, on their own, distinguish live concurrent execution from a faithful sequential
replay. Worker self-stamped `CLAIM`/`DONE` entries (K4) close this gap: each timestamp is authored by the
worker's own process clock, making concurrency provable from artifacts alone. After every run the orchestrator
runs the canonical snippet below against the shared `.kata/board.md` to emit `.kata/concurrency.json` — a
machine-readable concurrency evidence artifact the evaluator can read independently. (See
`.planning/specs/ws2-loop-autonomy/AUDIT.md` §7.)

**Per-run board (run-isolation — required for the artifact to be honest).** The snippet computes over the
whole board, so `.kata/board.md` MUST contain **only the current run's events**. The orchestrator therefore
**rotates any pre-existing board at run start** — move `.kata/board.md` to `.kata/board.<utc>.archive.md` (or
truncate it) before the first `CLAIM` — so prior-run `CLAIM`/`DONE` pairs cannot contaminate this run's
`maxInFlight`/`overlaps`. Without this, stale rows (including older orchestrator-stamped ones) would be folded
in and the `worker-clock` provenance claim would be false for those rows.

**Clock-trust assumption.** The proof rests on worker process clocks. It assumes all workers **share a
synchronized clock** (true for same-host subagents today). Cross-host clock skew — the multi-machine /
multi-model direction of Phase 5 — invalidates `overlaps` and can yield negative `sec`; **revisit this snippet
before any multi-machine run** (a skew-tolerant or orchestrator-issued monotonic stamp).

**Schema (K5):**

```json
{
  "maxInFlight": 3,
  "genuinelyParallel": true,
  "workerCount": 4,
  "workers": { "<task-id>": { "agent": "<id>", "start": "<iso>", "end": "<iso>", "sec": 39.0 } },
  "overlaps": [ ["<iso-start>", "<iso-end>"] ],
  "source": "board.md CLAIM/DONE self-stamps (worker-clock); per-run board + synchronized clocks assumed"
}
```

**Canonical snippet (single source of truth — K3; orchestrator runs this in-context at the gate):**

```python
import json, sys
from datetime import datetime
from pathlib import Path

kata = Path(sys.argv[1])                       # the run's .kata/ dir (integration root)
board = (kata / "board.md").read_text(encoding="utf-8")

# Pair earliest CLAIM (start) / latest DONE (end) per task from the self-stamped board.
# - earliest CLAIM / latest DONE => a re-dispatched task's full in-flight span is kept
#   (a naive last-write CLAIM would erase a real overlap and undercount concurrency).
# - a row whose timestamp is not ISO-8601 is skipped, never crashes the emit.
# Assumes a per-run board (the orchestrator rotates .kata/board.md at run start) and a
# synchronized worker clock (see the run-isolation + clock-trust notes above).
starts, ends, owner = {}, {}, {}
for raw in board.splitlines():
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 5:
        continue
    ts, agent, typ, task, _msg = parts[:5]
    try:
        when = datetime.fromisoformat(ts)
    except ValueError:
        continue                               # non-ISO / corrupted row — skip, don't abort
    if typ == "CLAIM":
        if task not in starts or when < starts[task]:
            starts[task] = when                # earliest CLAIM = true in-flight start
        owner.setdefault(task, agent)
    elif typ == "DONE":
        if task not in ends or when > ends[task]:
            ends[task] = when                  # latest DONE = true in-flight end

workers, intervals = {}, []
for task in sorted(starts):
    if task not in ends:
        continue                               # still in-flight / unterminated; skip
    s, e = starts[task], ends[task]
    workers[task] = {"agent": owner[task], "start": s.isoformat(), "end": e.isoformat(),
                     "sec": round((e - s).total_seconds(), 1)}  # negative => clock skew (see note)
    intervals.append((s, e, task))

# Sweep interval endpoints for max concurrent in-flight + overlap windows (>=2).
events = sorted([(s, +1) for s, _e, _t in intervals] + [(e, -1) for _s, e, _t in intervals])
active = max_in_flight = 0
overlaps, win_start = [], None
for ts, delta in events:
    prev = active; active += delta
    if prev < 2 <= active: win_start = ts
    if prev >= 2 > active and win_start is not None:
        overlaps.append([win_start.isoformat(), ts.isoformat()]); win_start = None
    max_in_flight = max(max_in_flight, active)

out = {"maxInFlight": max_in_flight, "genuinelyParallel": max_in_flight >= 2,
       "workerCount": len(workers), "workers": workers, "overlaps": overlaps,
       "source": "board.md CLAIM/DONE self-stamps (worker-clock); per-run board + synchronized clocks assumed"}
(kata / "concurrency.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
```

Run form (Windows; `python` not on PATH): `uv run --directory tools python - <abs-path-to-.kata> <<'PY' … PY`.

**Evidence, not a gate trigger (K6).** `concurrency.json` is parallelism evidence. A single-worker run
legitimately has `maxInFlight:1`/`genuinelyParallel:false` — that is **not** a failure. `kata-evaluate`
reads this artifact to corroborate rubric item 4 (ownership / conflict-free concurrent merges) when a run
claims parallel work; it is **never** a stand-alone default-FAIL trigger and is never tiered.
