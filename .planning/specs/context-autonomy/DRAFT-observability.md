# protocol/observability.md — log-reader orientation for KataHarness runs

Read this FIRST when dispatched to review, evaluate, audit, or forensically inspect a KataHarness run
(gate agent, inline evaluator, forensics pass, calibration work). It tells you where every observability
artifact lives, how each schema reads, and the gotchas that produce a silently-wrong read. It documents
WHAT EXISTS at v0.2.0, plus one v0.2.1 addition (marked below) — it does not describe anything unbuilt.

## Where everything lives

| Artifact | Path | Written by | Durability |
|---|---|---|---|
| Telemetry ledger | `.planning/telemetry-ledger.md` (harness repo) or the `telemetryLedger` locator in `.kata-settings.json` (target repo) | `kata_telemetry.build_ledger_row` + `append_ledger_row` at closeout | **Committed**, human-gated commit (D141(b), telemetry-ledger.md:6-9) |
| Board | `.kata/board.md` at the integration/target-repo root | Workers (`CLAIM`/`PROGRESS`/`DONE`/`NOTE`/`BLOCK`/`ESCALATE` self-stamped) + orchestrator (`DECISION`) — protocol/board.md:6-20 | **Gitignored**, session-local; durably snapshotted to `refs/kata/trail` (orphan ref) after every integration commit via `kata_trail.snapshot_board` (SKILL.md:528-535, kata_trail.py:1-25) |
| Per-task telemetry | `.kata/telemetry/<taskId>.json` | `kata_telemetry.write_task_telemetry` (kata_telemetry.py:757-779) | **Gitignored**, session-local (`.kata/` is never committed) |
| Checkpoint trailers | `Kata-Checkpoint: {...}` trailer in commit messages on the task's **active attempt branch** (`<task>` or `<task>-attemptN`) | Worker, via `kata_telemetry emit-trailer` CLI (kata_telemetry.py:959-1006) | **Committed** as part of normal task-branch history — durable as long as the branch/ref survives |
| Preflight | `.kata/preflight.json` | `kata_preflight.py` (N3 schema; kata_preflight.py:6,523-530) | **Gitignored**, session-local |
| Reports (v0.2.1) | `.kata/reports/<runId>-<taskId>-<agent>-<kind>.md` | Review/eval/forensics agents (gate agents, inline evaluators, etc.) | **Gitignored**, session-local. **If a DECISION line or a ledger row cites a report's contents, the citing artifact must quote/durably restate what it needs** — never point a durable citation at a file that can vanish with the session. |

Rule of thumb: if it must survive past this session (a DECISION, a ledger row, a calibration input), it
lives in the ledger, in a commit trailer, or on `refs/kata/trail`. Everything under `.kata/` is scratch —
useful in-run, not citable after the fact unless re-derived from a committed artifact.

## How to read the ledger

- **Row format:** one JSON object per line, below the header block; only lines starting with `{` are rows
  (telemetry-ledger.md:26, `read_ledger`). **A malformed row RAISES — never skip-and-average**
  (kata_telemetry.py:490-541, MED-9b). Do not hand-parse around a bad row; treat the raise as a stop
  signal and escalate.
- **v1 vs v2:** an absent `v` reads as v1 (the pre-schema shape). v2 is additive: `perTask`
  (`{taskId: {tokensIn, tokensOut, wallClockS}}`, explicit nulls, never fabricated), `failureKinds`
  (`[{taskId, kind, at}]`, orchestrator-classified at gate time — never worker-classified, D33), and
  `degraded` (`[{scope, reason}]`) — telemetry-ledger.md:11-22, D142 (DECISIONS.md:2131-2151). A
  **present-but-unknown** version RAISES; only absent-`v` silently maps to v1. **No backfill** — row 1
  (v1) stands as originally written (telemetry-ledger.md:20, kata_telemetry.py:500-503).
- **`calibration: true` rows are EXCLUDED from `class_median`** — toy/dogfood durations must never bias a
  real class median (kata_telemetry.py:576-596, gate v2 F6). Two of the four rows currently in the ledger
  carry `calibration: true` (telemetry-ledger.md:27,30) — don't fold their `taskDurationsByClass` into any
  median you compute by hand either.
- **`failureKinds` area prefix:** final-gate fix-loop areas and ladder events carry `area:<name>` in the
  `taskId` field of a `failureKinds` entry; plan task ids must NEVER begin `area:` — that prefix is the
  discriminator between a per-task and a per-area classification (telemetry-ledger.md:17-18).
  `failure_kinds_of(row)` (kata_telemetry.py:544-569) is the correct reader accessor: it returns
  `failureKinds` verbatim on a v2 row, maps a v1/field-absent row with `gateRejections > 0` to
  `[{"kind": "unclassified"}]`, and to `[]` otherwise. `unclassified` is a **reader-side sentinel only** —
  never a producible value; if you see it in a v2 row's `failureKinds` list, something upstream produced
  it wrong.
- **Cost columns are honest, not complete.** `tokensIn`/`tokensOut` (row-level and per-task) are nullable
  — host-dependent, the usage-meter honesty (kata_telemetry.py:16-17, 845-854). A `null` means "not
  surfaced by this host," not zero. Never treat null as 0 in an average; never fabricate a value to fill
  the gap.
- **Unlock thresholds:** τ-calibration work needs **≥3 instrumented runs**; the slack class-median source
  needs **≥5 samples per class** before `class_median` returns non-`None` (telemetry-ledger.md:23-24,
  kata_telemetry.py:572-596, `min_samples=5` default). Below threshold, treat the metric as "not yet
  meaningful," not "zero."

## How to read checkpoints

- **Trailer shape (schema v1):** `{"v":1, "i":<int>=0, "verify":{"exit":<int>, "passed"?, "failed"?,
  "skipped"? (nullable ints)}, "lint"? (nullable int), "evidence"? (sha256 hex)}` — one
  `Kata-Checkpoint:` trailer per commit, never more than one (a second trailer on the same commit RAISES —
  ambiguous evidence, v2-MED-5, kata_telemetry.py:187-217).
- **`evidence` is a git-blob-sha digest, not a hash of file contents directly.** It's the sha256 over the
  sorted `"<path>:<blob-sha>"` entries for the chunk's changed paths (kata_telemetry.py:319-402). Stamp
  mode (worker, pre-commit) reads staged blobs via `ls-files -s`; verify mode (gate, post-commit) reads
  `ls-tree <sha>`, falling back to the parent tree for a path the chunk deleted (`"<path>:ABSENT"`). Both
  modes must round-trip to the identical digest for a clean chunk — a mismatch means the chunk's actual
  diff doesn't match what was staged when the trailer was emitted.
- **Malformed trailer / scan failure ⇒ treat-as-triggered, never a silent pass.** A `TelemetryError` from
  `parse_checkpoint_trailer` or `scan_checkpoints` is the documented fail-safe: under `inlineEval: on` it
  is treat-as-triggered + surfaced (ladder line `@<sha|SCAN-ERR> score ERR verdict <v>`, SKILL.md:567-574);
  under P0/`telemetry` mode it's recorded as a malformed-signal event but never blocks
  (SKILL.md:429-432). Either way — **never skip-and-average, never silently accept.**
  A `SCAN-ERR` adjudication covers its scan window once and does not re-fire on restart.
- **Merge commits are never a trailer source.** `scan_checkpoints` walks the branch's own non-merge
  commits; a merge commit (>1 parent) that itself carries a trailer RAISES (undefined chunk diff on a
  multi-parent commit), a trailer-free merge is silently skipped — not an error (kata_telemetry.py:224-262).
- **Index continuity across attempts.** A reroll/correct fresh dispatch continues the checkpoint index
  from the anchor checkpoint's `i` (anchor at `i=k` ⇒ fresh session's first trailer is `--index k+1`,
  SKILL.md:651-654). When there is no last-good checkpoint to anchor on, the reroll anchors at the task's
  **dispatch base** instead (SKILL.md:642-643) — i.e. the fresh attempt's checkpoint stream starts fresh
  from index 0 in that case (inferred from the anchor/index-continuity rule; not spelled out as a
  standalone "index 0" statement in the source — verify against the specific run's ladder DECISION lines
  before treating a `k+1` computation as certain).

## How to read the board

- **Line grammar:** `<ISO-8601-UTC> | <agent-id> | <TYPE> | <task-id> | <one-line message>`
  (protocol/board.md:9).
- **`CLAIM`/`DONE` are worker self-stamped**, using the worker's own process clock — this is what makes
  the board provable evidence of concurrency rather than an orchestrator's account of it (protocol/board.md:13-14,21).
  `PROGRESS` is a mandated liveness heartbeat (`<done>/<owned> <label>`, F3) — excluded from coordination
  logic, read by the liveness monitor and the M4 slack estimator (protocol/board.md:19,23-31).
- **`DECISION` lines are orchestrator-only** and resolve a `BLOCK`/`ESCALATE`, or record a ladder event —
  `ladder: <task> trigger <n> @<sha> score <s> verdict <v>` (SKILL.md:610-614). The `@<sha>` on a ladder
  line is what makes cursor recovery sound after a conductor restart: adjudicated shas recount from these
  lines and are never re-triggered (SKILL.md:616-618).
- **Archives + trail snapshots.** The orchestrator rotates any pre-existing board at run start — moved to
  `.kata/board.<utc>.archive.md` (or truncated) — so `.kata/board.md` holds only the current run's events
  (protocol/board.md:45-50). Each integration commit additionally triggers a `refs/kata/trail` snapshot of
  the board (`kata_trail.snapshot_board`, SKILL.md:528-535) — this is the durable copy to read if the
  live `.kata/board.md` is gone or has since been rotated/archived.

## The gotchas

- **Use fork refs, not the current integration head, when scanning a task's checkpoints after it has
  merged.** `scan_checkpoints(repo_root, branch, integration_ref)` walks `branch ^integration_ref`
  (kata_telemetry.py:224-262); once `branch` has merged into integration, integration's current head is a
  *descendant* of the task branch, so re-running the scan against today's integration head returns
  nothing — a silent, vacuous scan, not an error. Pin `integration_ref` to the task's original dispatch
  base / fork-point sha for a post-merge review (see the merge-base-scoped, three-dot lane-check rule at
  SKILL.md:393-402 for the same principle applied to drift).
- **Never skip-and-average a malformed ledger row.** `read_ledger` raises; that's the contract
  (kata_telemetry.py:490-541, MED-9b). Escalate, don't route around it.
- **Calibration rows never enter medians.** Filter `"calibration": true` out of any hand-computed
  aggregate, the same way `class_median` does (kata_telemetry.py:576-596).
- **Token columns may be null — host-dependent, never fabricate.** A `null` `tokensIn`/`tokensOut` is
  honest absence, not zero (kata_telemetry.py:16-17).
- **Board timestamps are process clocks, not a synchronized global clock.** They're accurate for ordering
  within one writer and for proving overlap on a single host, but skew is possible at the margins across
  writers — the concurrency-evidence snippet documents this assumption explicitly and flags it as a
  revisit item before any multi-machine run (protocol/board.md:52-55).
- **`.kata/` is session-local.** Anything under it (board, telemetry, preflight, reports) can vanish with
  the session. A durable citation (a DECISION, a ledger row, a finding you want to survive review) must
  point at a committed artifact (the ledger, a commit trailer) or a trail ref (`refs/kata/trail`) — never
  bare at a `.kata/*` path.

## What a review dispatch should receive

Give the log-reading agent a pointer block, not inlined telemetry prose:

```
Read protocol/observability.md first (orientation for this run's artifacts).
Run: <runId>          e.g. m4p1-dogfood-build-2026-07-04
Refs: integration=<branch/sha>  trail=refs/kata/trail@<sha-or-"latest">  fork-point=<sha>
```

That's the whole brief. The agent derives everything else — ledger row, board state, checkpoint trailers,
per-task telemetry — by reading the artifacts this doc points at, from that run id and those refs.
