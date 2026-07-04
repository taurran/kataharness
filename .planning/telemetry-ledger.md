# M4 telemetry ledger — git-durable calibration data (M4-L10)

> The committed, append-only calibration ledger for the Freeze/Float M4 inline evaluator.
> One JSON object per line below the marker; **only lines beginning with `{` are rows**
> (`kata_telemetry.read_ledger` — a malformed row RAISES, never skip-and-average).
> Written at run closeout via `kata_telemetry.build_ledger_row` + `append_ledger_row`;
> the commit carrying a row is **human-gated** (D141(b) — board-`DECISION`-recorded approval;
> target-repo runs locate this file via `.kata-settings.json` `telemetryLedger` and route the
> row through a second explicitly human-gated commit in this repo).
>
> Row schema v1: `{v, utc, runId, target, calibration, tasks, checkpoints, zeroCheckpointTasks,
> firstPassAcceptanceByClassTier, streaksByClass, fixCycles, gateRejections,
> taskDurationsByClass, wallClockS, tokensIn, tokensOut, effectiveModes}`.
> **Schema v2 (P0.1, DESIGN Amendment #4 — additive):** v1 fields + `perTask` (per-task
> `{tokensIn, tokensOut, wallClockS}`, explicit nulls, never fabricated), `failureKinds`
> (`[{taskId, kind, at}]`, orchestrator-classified at gate time from `FAILURE_KINDS`), `degraded`
> (`[{scope, reason}]`). Rows with absent `v` read as v1; v1 rows read as `unclassified`
> kinds / null cost (`failure_kinds_of`) — **no backfill; row 1 stands as written.** —
> `calibration: true` rows are EXCLUDED from `class_median` (toy durations must never bias
> real medians); `tokensIn`/`tokensOut` nullable (host-dependent, the usage_meter honesty).
> τ calibration unlocks at ≥3 instrumented runs; the slack class-median source unlocks at
> ≥5 samples per class (A1-Q3).

<!-- rows below this line — append only, never edit or delete a row -->
{"v":1,"utc":"2026-07-04T19:03:44Z","runId":"m4p0-t5-calibration-2026-07-04","target":"scratch/strutil (calibration exercise)","tasks":2,"checkpoints":4,"zeroCheckpointTasks":0,"firstPassAcceptanceByClassTier":{"code\u00d7sonnet":1.0},"streaksByClass":{"code":[2,2]},"fixCycles":0,"gateRejections":0,"taskDurationsByClass":{"code":[2.21,3.5]},"wallClockS":342.9,"tokensIn":null,"tokensOut":116105,"effectiveModes":{"T-A":"telemetry","T-B":"telemetry"},"calibration":true}
