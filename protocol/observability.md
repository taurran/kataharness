# protocol/observability.md — log-reader orientation for KataHarness runs

Read this FIRST when dispatched to review, evaluate, audit, or forensically inspect a KataHarness run
(gate agent, inline evaluator, forensics pass, calibration work). It tells you where every observability
artifact lives, how each schema reads, and the gotchas that produce a silently-wrong read. It documents
WHAT EXISTS at v0.2.0, plus the v0.2.1 additions (each marked below) — it does not describe anything unbuilt.

## Where everything lives

| Artifact | Path | Written by | Durability |
|---|---|---|---|
| Telemetry ledger | `.planning/telemetry-ledger.md` (harness repo) or the `telemetryLedger` locator in `.kata-settings.json` (target repo) | `kata_telemetry.build_ledger_row` + `append_ledger_row` at closeout | **Committed**, human-gated commit (D141(b), telemetry-ledger.md:6-9) |
| Board | `.kata/board.md` at the integration/target-repo root | Workers (`CLAIM`/`PROGRESS`/`DONE`/`NOTE`/`BLOCK`/`ESCALATE` self-stamped) + orchestrator (`DECISION`) + the seam (`PHASE`/`VERDICT`/`SPAWN`/`DOWN`/`DENY`) — protocol/cursor.md:73-86 | **Gitignored**, session-local; durably snapshotted to `refs/kata/trail` (orphan ref) after every integration commit via `kata_trail.snapshot_board` (SKILL.md:625-629, kata_trail.py:82) |
| Per-task telemetry | `.kata/telemetry/<taskId>.json` | `kata_telemetry.write_task_telemetry` (kata_telemetry.py:951-974) | **Gitignored**, session-local (`.kata/` is never committed) |
| Checkpoint trailers | `Kata-Checkpoint: {...}` trailer in commit messages on the task's **active attempt branch** (`<task>` or `<task>-attemptN`) | Worker, via `kata_telemetry emit-trailer` CLI (kata_telemetry.py:1314-1364) | **Committed** as part of normal task-branch history — durable as long as the branch/ref survives |
| Preflight | `.kata/preflight.json` | `kata_preflight.py` (N3 schema; kata_preflight.py:6,535-568) | **Gitignored**, session-local |
| Handoff | `.planning/HANDOFF.md` | [[kata-handoff]] — frontmatter carries `kind: manual/self/boundary` provenance (v0.2.1, CA-L21; protocol/handoff.md:18,41) | **Committed**, durable. Staleness rule (v0.2.1, CA-L19): protocol/handoff.md §Staleness |
| Reports (v0.2.1, live) | `.kata/reports/<runId>-<taskId>-<agent>-<kind>.md` | Review/eval/forensics agents (gate agents, inline evaluators, etc.); `<runId>` is the **seam-minted** run id (`kata_dispatch.run_start` → `run-<utc-compact>-<hex>`, trust-model W3) — no longer a key nothing writes | **Gitignored**, session-local. **If a DECISION line or a ledger row cites a report's contents, the citing artifact must quote/durably restate what it needs** — never point a durable citation at a file that can vanish with the session. |

Rule of thumb: if it must survive past this session (a DECISION, a ledger row, a calibration input), it
lives in the ledger, in a commit trailer, or on `refs/kata/trail`. Everything under `.kata/` is scratch —
useful in-run, not citable after the fact unless re-derived from a committed artifact.

## How to read the ledger

- **Row format:** one JSON object per line, below the header block; only lines starting with `{` are rows
  (telemetry-ledger.md:4-5, `read_ledger`). **A malformed row RAISES — never skip-and-average**
  (kata_telemetry.py:516-571, MED-9b). Do not hand-parse around a bad row; treat the raise as a stop
  signal and escalate.
- **v1 vs v2 vs v3:** an absent `v` reads as v1 (the pre-schema shape). v2 is additive: `perTask`
  (`{taskId: {tokensIn, tokensOut, wallClockS}}`, explicit nulls, never fabricated), `failureKinds`
  (`[{taskId, kind, at}]`, orchestrator-classified at gate time — never worker-classified, D33), and
  `degraded` (`[{scope, reason}]`) — telemetry-ledger.md:11-22, D142 (DECISIONS.md:2131-2151).
  **v3 (v0.2.1, CA-L40) is additive over v2:** `build_ledger_row` now emits `v: 3` with one new column,
  `parentTokens` (`{"<phase>": int|null}` — per-phase parent-context token readings, explicit nulls for
  honest absence, never fabricated; kata_telemetry.py:1213-1281). Read it via the `parent_tokens_of(row)`
  accessor (kata_telemetry.py:600-625): a v3 row returns the map verbatim with its nulls PRESERVED; a
  v1/v2/absent-field row degrades to `{}` — the discriminator is field PRESENCE, not the version number
  (the `failure_kinds_of` pattern). Known versions are exactly `{1, 2, 3}` (`_KNOWN_LEDGER_VERSIONS`,
  kata_telemetry.py:70); a **present-but-unknown** version (e.g. a future v4) RAISES fail-closed
  (kata_telemetry.py:562-567); only absent-`v` silently maps to v1. **No backfill** — row 1 (v1) stands
  as originally written, and pre-v3 rows are never rewritten (telemetry-ledger.md:20,
  kata_telemetry.py:526-531).
- **`calibration: true` rows are EXCLUDED from `class_median`** — toy/dogfood durations must never bias a
  real class median (kata_telemetry.py:766-791, gate v2 F6). Two of the four rows currently in the ledger
  carry `calibration: true` (telemetry-ledger.md:27,30) — don't fold their `taskDurationsByClass` into any
  median you compute by hand either.
- **`failureKinds` area prefix:** final-gate fix-loop areas and ladder events carry `area:<name>` in the
  `taskId` field of a `failureKinds` entry; plan task ids must NEVER begin `area:` — that prefix is the
  discriminator between a per-task and a per-area classification (telemetry-ledger.md:17-18).
  `failure_kinds_of(row)` (kata_telemetry.py:572-598) is the correct reader accessor: it returns
  `failureKinds` verbatim on a v2 row, maps a v1/field-absent row with `gateRejections > 0` to
  `[{"kind": "unclassified"}]`, and to `[]` otherwise. `unclassified` is a **reader-side sentinel only** —
  never a producible value; if you see it in a v2 row's `failureKinds` list, something upstream produced
  it wrong.
- **Cost columns are honest, not complete.** `tokensIn`/`tokensOut` (row-level and per-task) are nullable
  — host-dependent, the usage-meter honesty (kata_telemetry.py:908-910, 1033-1038). A `null` means "not
  surfaced by this host," not zero. Never treat null as 0 in an average; never fabricate a value to fill
  the gap.
- **Unlock thresholds:** τ-calibration work needs **≥3 instrumented runs**; the slack class-median source
  needs **≥5 samples per class** before `class_median` returns non-`None` (telemetry-ledger.md:23-24,
  kata_telemetry.py:766-791, `min_samples=5` default). Below threshold, treat the metric as "not yet
  meaningful," not "zero."
- **Adaptive-tiering calibration columns (D150 / M4 Amendment #6 — ADDITIVE OPTIONAL keys on the v3
  row; NO v4 exists):** `verdictByTier` (`{"<verdict>×<tier>": n}` — standing verdicts under their
  deciding tier, overturned screen verdicts under `overturned×<screen-tier>`; the C-3 τ/verdict
  calibration input) and `tierEvents` (`[{at, dispatch, from, to, reason}]` — the adaptive move audit
  trail). Read via the absent-honest accessors `verdict_by_tier_of(row)` / `tier_events_of(row)`
  (`{}`/`[]` on pre-amendment rows, never fabricated); aggregate via `verdict_by_tier_totals(rows)` and
  `overturn_rate(rows)` — both EXCLUDE `calibration: true` rows by default and return
  not-yet-meaningful sentinels below `min_samples`, the `class_median` discipline exactly.

## How to read checkpoints

- **Trailer shape (schema v1):** `{"v":1, "i":<int>=0, "verify":{"exit":<int>, "owned"?, "passed"?,
  "failed"?, "skipped"? (nullable ints)}, "lint"? (nullable int), "evidence"? (sha256 hex)}` — one
  `Kata-Checkpoint:` trailer per commit, never more than one (a second trailer on the same commit RAISES —
  ambiguous evidence, v2-MED-5, kata_telemetry.py:213-243).
- **`verify.exit` vs `verify.owned` scoping (Amendment #5/C-1).** `verify.exit` is the worker's FULL
  committed verify (the suite run); the optional `verify.owned` is the exit of the OWNED-FILE-scoped run
  (the worker's own test files only). The scorer's `verify_fail` reads `owned` when present-and-non-null,
  else falls back to the suite exit — the fallback leg is the C-1 false-positive-prone population (a
  sibling task's cross-task suite red, e.g. a README-index sync test, is not the worker's defect).
  Calibration tells the two populations apart by field presence; absent `owned` in a pre-amendment row is
  "not measured," never backfilled (kata_risk.py `_verify_fail`; CALIBRATION-FINDINGS.md C-1).
- **`evidence` is a git-blob-sha digest, not a hash of file contents directly.** It's the sha256 over the
  sorted `"<path>:<blob-sha>"` entries for the chunk's changed paths (kata_telemetry.py:345-429). Stamp
  mode (worker, pre-commit) reads staged blobs via `ls-files -s`; verify mode (gate, post-commit) reads
  `ls-tree <sha>`, falling back to the parent tree for a path the chunk deleted (`"<path>:ABSENT"`). Both
  modes must round-trip to the identical digest for a clean chunk — a mismatch means the chunk's actual
  diff doesn't match what was staged when the trailer was emitted.
- **Malformed trailer / scan failure ⇒ treat-as-triggered, never a silent pass.** A `TelemetryError` from
  `parse_checkpoint_trailer` or `scan_checkpoints` is the documented fail-safe: under `inlineEval: on` it
  is treat-as-triggered + surfaced (ladder line `@<sha|SCAN-ERR> score ERR verdict <v>`, SKILL.md:665-671);
  under P0/`telemetry` mode it's recorded as a malformed-signal event but never blocks
  (SKILL.md:469-472). Either way — **never skip-and-average, never silently accept.**
  A `SCAN-ERR` adjudication covers its scan window once and does not re-fire on restart.
- **Merge commits are never a trailer source.** `scan_checkpoints` walks the branch's own non-merge
  commits; a merge commit (>1 parent) that itself carries a trailer RAISES (undefined chunk diff on a
  multi-parent commit), a trailer-free merge is silently skipped — not an error (kata_telemetry.py:250-288).
- **Index continuity across attempts.** A reroll/correct fresh dispatch continues the checkpoint index
  from the anchor checkpoint's `i` (anchor at `i=k` ⇒ fresh session's first trailer is `--index k+1`,
  SKILL.md:753-756). When there is no last-good checkpoint to anchor on, the reroll anchors at the task's
  **dispatch base** instead (SKILL.md:744-745) — the dispatch base carries no checkpoint trailer, so with
  `k` absent **the fresh attempt indexes from 0** at that base (CA-L44 F2, stated rule).

## How to read the board

- **Line grammar (6-field, post-cursor-migration):** `<utc> | <seq> | <agent-id> | <TYPE> | <task-id> | <one-line message>`
  — the digits-only `seq` field is the primary parse discriminator and the old 5-field form parses
  NOWHERE (protocol/cursor.md:38,54-58).
- **`CLAIM`/`DONE` are worker self-stamped**, using the worker's own process clock — this is what makes
  the board provable evidence of concurrency rather than an orchestrator's account of it (protocol/cursor.md:75-76).
  `PROGRESS` is a mandated liveness heartbeat (`<done>/<owned> <label>`, F3) — excluded from coordination
  logic, read by the liveness monitor and the M4 slack estimator (protocol/cursor.md:80,97-105).
- **`DECISION` lines are orchestrator-only** and resolve a `BLOCK`/`ESCALATE`, or record a ladder event —
  `ladder: <task> trigger <n> @<sha> score <s> verdict <v>` (SKILL.md:713-715). The `@<sha>` on a ladder
  line is what makes cursor recovery sound after a conductor restart: adjudicated shas recount from these
  lines and are never re-triggered (SKILL.md:719-721).
- **`tier:` DECISION lines record every adaptive-tiering move (D150, AT-L7)** —
  `tier: <task|dispatch> <from>-><to> reason <event:<name>|failbump|streak|complexity|anchor-switch-reset|budget-exhausted>`
  (rendered/parsed by `kata_adaptive.render_tier_decision`/`recount_from_decisions`). These lines are
  ALSO the durable recount trail: after a conductor restart, premium budget spend and per-task bump
  state rebuild from them (the thrash-budget recount pattern); a malformed `tier:` payload RAISES at
  recount — a corrupt trail must never silently under-count premium spend (D136).
- **Archives + trail snapshots.** The orchestrator rotates any pre-existing board at run start — moved to
  `.kata/board.<utc>.archive.md` (or truncated) — so `.kata/board.md` holds only the current run's events
  (protocol/cursor.md:166-176). Each integration commit additionally triggers a `refs/kata/trail` snapshot of
  the board (`kata_trail.snapshot_board`, SKILL.md:625-629) — this is the durable copy to read if the
  live `.kata/board.md` is gone or has since been rotated/archived.

## The gotchas

- **Use fork refs, not the current integration head, when scanning a task's checkpoints after it has
  merged.** `scan_checkpoints(repo_root, branch, integration_ref)` walks `branch ^integration_ref`
  (kata_telemetry.py:250-288); once `branch` has merged into integration, integration's current head is a
  *descendant* of the task branch, so re-running the scan against today's integration head returns
  nothing — a silent, vacuous scan, not an error. Pin `integration_ref` to the task's original dispatch
  base / fork-point sha for a post-merge review (see the merge-base-scoped, three-dot lane-check rule at
  SKILL.md:434-436 for the same principle applied to drift).
- **Never skip-and-average a malformed ledger row.** `read_ledger` raises; that's the contract
  (kata_telemetry.py:516-571, MED-9b). Escalate, don't route around it.
- **Calibration rows never enter medians.** Filter `"calibration": true` out of any hand-computed
  aggregate, the same way `class_median` does (kata_telemetry.py:766-791).
- **Token columns may be null — host-dependent, never fabricate.** A `null` `tokensIn`/`tokensOut` is
  honest absence, not zero (kata_telemetry.py:908-910). The v3 `parentTokens` column carries the same
  contract: nulls preserved, never coerced to zero (`parent_tokens_of`, kata_telemetry.py:600-625).
- **Cursor ordering lives in seq space, not wall-clock.** Ordering of record is `(runId, seq)` + parent
  fold-order with file position as the tie-break; the `utc` field is recorded for humans and is
  informational only — **never load-bearing**. This closes the pre-migration process-clock-skew
  assumption (the old board derived concurrency from worker process clocks), so the multi-machine /
  multi-model direction needs no skew-tolerant stamp for ordering to hold (protocol/cursor.md:112-122).
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
