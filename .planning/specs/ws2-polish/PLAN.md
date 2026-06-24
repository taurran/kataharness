---
title: "WS-2 polish — worker self-timestamping + artifact-provable concurrency"
status: FROZEN
date: 2026-06-24
spec: ws2-polish
source: >-
  .planning/specs/ws2-loop-autonomy/AUDIT.md §5.2 (concurrency-evidence artifact) + §7 (worker
  self-timestamping follow-up) — the honest gap that durable board.md timestamps are orchestrator-written
  and therefore cannot distinguish live concurrency from a faithful replay.
ownership:
  A: [protocol/board.md]
  B: [skills/coordinate/kata-orchestrate/SKILL.md]
  C: [skills/evaluate/kata-evaluate/SKILL.md, .planning/HANDOFF.md]
waves:
  - [A]
  - [B, C]
depends_on:
  A: []
  B: [A]
  C: [A]
tags:
  - kata/plan
  - ws2
  - concurrency
  - no-new-python
---

# WS-2 polish — make worker concurrency provable from artifacts (no new committed Python)

**Goal.** Close the WS-2 honest gap: today the durable `.kata/board.md` timestamps are
*orchestrator-written*, so they record concurrency correctly but cannot, on their own, distinguish live
concurrency from a faithful replay. After this change a run's **workers self-stamp their own start/end**
into the shared board, and the gate derives a **`.kata/concurrency.json`** evidence artifact a
fresh-context evaluator can read — concurrency becomes provable from artifacts alone.

**Architecture.** All-Markdown change. The concurrency computation is an **embedded in-context snippet**
stored as a fenced block in `protocol/board.md` (the contract source of truth) and run by the orchestrator
at the integration gate — **no new `tools/` module**. The worker self-stamp is a structured requirement of
the dispatch contract. This build is therefore **non-code-bearing** (`codeBearing:false`).

## Global constraints (every slice inherits these)
- **No new committed `tools/` Python** (memory `prefer-in-context-over-new-python`). The snippet lives in a
  `.md` fenced block; it is documentation the orchestrator runs in-context, not an imported module. Do **not**
  add a `.py` file (a `.py` extension would flip the run to `codeBearing:true`).
- **Append-only board + single-writer state (L3) unchanged.** Workers still call only
  `append_event`/`append_progress`; only the orchestrator writes `state.json`. The snippet **only reads**
  `board.md`.
- **`.kata/` stays gitignored** — `concurrency.json` is a run artifact, never committed.
- Conventional commits; project trailer. Stage specific files. Match each file's existing voice/structure.

## LOCKED decisions (verbatim; workers MUST NOT re-decide)
- **K1 — No new committed Python.** The concurrency artifact is produced by the embedded snippet in
  `protocol/board.md`, run in-context at the gate. No `tools/concurrency.py` (or any new `.py`).
- **K2 — Non-code-bearing run.** All edits are `.md`; the snippet is doc text, not shipped logic ⇒
  `footprint.json.codeBearing:false` ⇒ no mutation-proof requirement (validated in-context instead).
- **K3 — Single source of truth.** The canonical concurrency **schema + snippet** live **only** in
  `protocol/board.md`. `kata-orchestrate` and `kata-evaluate` reference them **by pointer** — never paste a
  second copy of the snippet body (DRY-by-pointer).
- **K4 — Worker self-stamp contract.** Each worker appends `CLAIM` (start) when it begins and `DONE` (end)
  when its verify passes, to the **shared** `.kata/board.md` at the **integration/target-repo root** (not the
  per-task worktree's `.kata/`), via `kata_board.append_event` using the worker's **own process clock**. That
  is what makes the timestamp worker-authored and the concurrency artifact-provable.
- **K5 — `concurrency.json` schema is fixed (the proven shape):**
  ```json
  {
    "maxInFlight": 3,
    "genuinelyParallel": true,
    "workerCount": 4,
    "workers": { "<task-id>": { "agent": "<id>", "start": "<iso>", "end": "<iso>", "sec": 39.0 } },
    "overlaps": [ ["<iso-start>", "<iso-end>"] ],
    "source": "board.md CLAIM/DONE self-stamps (worker-clock)"
  }
  ```
- **K6 — Evidence, not a new gate item.** `concurrency.json` is parallelism **evidence**. A single-worker
  run legitimately has `maxInFlight:1`/`genuinelyParallel:false` — that is **not** a failure.
  `kata-evaluate` reads it to *corroborate* rubric item 4 (ownership / conflict-free concurrent merges) when
  a run claims parallel work; it is **never** a stand-alone default-FAIL trigger and never tiered.
- **K7 — `kata_board` is unchanged.** No edit to `tools/kata_board.py` — `append_event` already stamps UTC at
  call time, so a worker calling it self-stamps by construction. This PLAN wires the *contract*, not the tool.

## Canonical concurrency snippet (slice A embeds this verbatim into `protocol/board.md`)
Stored as a fenced ```` ```python ```` block. It reads `<kata>/board.md`, pairs `CLAIM`(start)/`DONE`(end)
per task, computes per-task wall-clock + max concurrent in-flight + overlap windows (≥2), and writes
`<kata>/concurrency.json`. **Proven** against a sample board (maxInFlight 3, sequential task correctly
excluded) before freeze.

```python
import json, sys
from datetime import datetime
from pathlib import Path

kata = Path(sys.argv[1])                       # the run's .kata/ dir (integration root)
board = (kata / "board.md").read_text(encoding="utf-8")

# Pair CLAIM(start)/DONE(end) per task from the self-stamped board.
starts, ends, owner = {}, {}, {}
for raw in board.splitlines():
    parts = [p.strip() for p in raw.split("|")]
    if len(parts) < 5:
        continue
    ts, agent, typ, task, _msg = parts[:5]
    if typ == "CLAIM":
        starts[task] = ts; owner[task] = agent
    elif typ == "DONE":
        ends[task] = ts

workers, intervals = {}, []
for task in sorted(starts):
    if task not in ends:
        continue                               # still in-flight / unterminated; skip
    s = datetime.fromisoformat(starts[task]); e = datetime.fromisoformat(ends[task])
    workers[task] = {"agent": owner[task], "start": starts[task], "end": ends[task],
                     "sec": round((e - s).total_seconds(), 1)}
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
       "source": "board.md CLAIM/DONE self-stamps (worker-clock)"}
(kata / "concurrency.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
```

Run form (Windows; `python` not on PATH): `uv run --directory tools python - <abs-path-to-.kata> <<'PY' … PY`.

---

## Slice A — contract (`protocol/board.md`) · wave 1
**read_first:** this PLAN (the snippet + K1–K7); current `protocol/board.md`.
**action:**
1. In the **TYPE vocabulary** table, sharpen the `CLAIM` and `DONE` rows to state they are the worker's
   **self-stamped start/end** — appended by the worker, with the worker's own clock, to the **shared**
   `.kata/board.md` at the integration root (K4). Add one sentence under the table: *"`CLAIM`/`DONE` are the
   worker-self-stamped start/end of a task; because the worker authors them with its own process clock, the
   board is the artifact-of-record for concurrency (it does not depend on orchestrator-written timestamps)."*
2. Add a new section **"## Concurrency evidence (`.kata/concurrency.json`)"** that: (a) states the purpose
   (close the orchestrator-written-timestamp gap so concurrency is provable from artifacts alone — cite
   AUDIT §7); (b) documents the **K5 schema** (table or JSON block); (c) embeds the **canonical snippet
   verbatim** from this PLAN as a fenced ```` ```python ```` block; (d) states K6 (evidence, not a gate
   trigger; single-worker `maxInFlight:1` is legitimate). This file is the **single source of truth** for
   both the schema and the snippet (K3).
**acceptance:**
- The `CLAIM`/`DONE` self-stamp framing (K4) is present and explicit about *worker clock* + *shared board*.
- The new section contains the K5 schema AND the snippet body **verbatim** (byte-for-byte matches this PLAN's
  snippet — it is the copy other slices point to).
- K6 stated (single-worker run is not a failure). Append-only/L3 wording untouched.
**verify:** `cd tools && uv run python validate_skills.py` (36/0 — board.md isn't a skill but run it to confirm
no breakage), then manually re-run the snippet against a throwaway 2-worker sample board and confirm it emits a
well-formed `concurrency.json` with `maxInFlight:2`.

## Slice B — producer (`skills/coordinate/kata-orchestrate/SKILL.md`) · wave 2 (depends_on: A)
**read_first:** this PLAN (K3/K4); slice A's frozen `protocol/board.md` section; current `kata-orchestrate`
"The loop" worker-prompt block (the bulleted MUST-carry list) + "Final gate" section.
**action:**
1. In the worker-prompt MUST-carry list (under "The loop", step 2), ADD one required bullet: *"self-stamp
   `CLAIM` (start) to the shared `.kata/board.md` at the integration root via `kata_board.append_event` with
   your own clock when you begin, and `DONE` (end) when your verify passes — so concurrency is provable from
   artifacts (`protocol/board.md` → Concurrency evidence)."* Make explicit the shared-root path (the carried
   S3b lesson: `.kata/` lives at the integration/target root, not the per-task worktree).
2. In **"## Final gate"**, after the gate-artifact-emit step (the `gate_emit` step 2), ADD a step: *"Emit the
   concurrency evidence — run the canonical snippet from `protocol/board.md` (Concurrency evidence) against the
   run's `.kata/` to produce `.kata/concurrency.json`."* Reference the snippet **by pointer** to
   `protocol/board.md` (K3 — do not paste the snippet body here). Note it is evidence the evaluator reads (K6),
   not a gate that can fail a sequential run.
**acceptance:**
- Worker-prompt list has the self-stamp requirement naming `kata_board.append_event`, *own clock*, *shared
  integration-root board* (K4).
- Final gate has a concurrency-emit step that points to `protocol/board.md` and does **not** duplicate the
  snippet (K3).
- No change to dispatch/frontier/escalation/gate logic beyond these additive lines; `model: fable`, frontmatter,
  and the WS-3 narration section untouched.
**verify:** `cd tools && uv run python validate_skills.py` (36/0) — the skill still parses and the README index
columns regenerate unchanged.

## Slice C — consumer + recipe (`skills/evaluate/kata-evaluate/SKILL.md`, `.planning/HANDOFF.md`) · wave 2 (depends_on: A)
**read_first:** this PLAN (K5/K6); slice A's frozen `protocol/board.md` section; current `kata-evaluate`
"Artifact paths and canonical producer" table; `.planning/HANDOFF.md` §5 (the orchestration recipe).
**action:**
1. `kata-evaluate`: add a row to the **"Artifact paths and canonical producer"** table for
   `.kata/concurrency.json` (the K5 fields, summarized) and one sentence: *"Optional parallelism evidence — for
   a run that claims concurrent work, read it to corroborate rubric item 4 (ownership / conflict-free concurrent
   merges); `genuinelyParallel:false` on a legitimately single-worker run is **not** a finding (K6). Never a
   stand-alone default-FAIL trigger."* Keep the evaluator **no-write** (it only reads). Do **not** add a new
   rubric item.
2. `.planning/HANDOFF.md` §5 (the recipe): in step 3 (dispatch workers) note workers self-stamp `CLAIM`/`DONE`
   to the shared board; in step 5 (gate / `gate_emit`) add *"…and emit `.kata/concurrency.json` via the
   `protocol/board.md` snippet"*. Keep it to the existing terse recipe style.
**acceptance:**
- `kata-evaluate` artifact table includes `concurrency.json`; the no-write property and the K6 "evidence-not-a-
  gate" framing are explicit; no new rubric item; frontmatter/allowed-tools (no Write/Edit) untouched.
- HANDOFF §5 mentions worker self-stamp (step 3) + concurrency emit (step 5), terse, consistent with the
  existing numbered recipe.
**verify:** `cd tools && uv run python validate_skills.py` (36/0).

---

## Integration & gate (orchestrator, after the frontier drains)
1. Octopus-merge A → then B + C (disjoint files; no conflict) into the integration branch; `cd tools && uv sync`.
2. Gate: `uv run pytest -q` (**447**, unchanged — non-code-bearing) + `validate_skills.py` (**36/0**). No Snyk
   needed (no new/changed Python). Emit `.kata/RESULT.json` via `gate_emit` (footprint over `protocol/ skills/
   .planning/` ⇒ expect `codeBearing:false`, K2).
3. **Dogfood self-proof:** the wave-2 workers (B + C) self-stamp `CLAIM`/`DONE` to **this run's** shared
   `.kata/board.md`; after integration, run the snippet → emit `.kata/concurrency.json` for THIS build and
   confirm `maxInFlight:2` (B+C overlapped) — living proof the feature works on its own construction.
4. Fresh-context **Opus** `kata-evaluate` (no-write, default-FAIL): grades the diff + reads the emitted
   artifacts incl. `concurrency.json`. Must PASS.
5. Operator gate → merge to master, push, remove worktrees, checkpoint STATE/HANDOFF/BACKLOG, push.
