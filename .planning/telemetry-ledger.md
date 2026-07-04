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
> taskDurationsByClass, wallClockS, tokensIn, tokensOut, effectiveModes}` —
> `calibration: true` rows are EXCLUDED from `class_median` (toy durations must never bias
> real medians); `tokensIn`/`tokensOut` nullable (host-dependent, the usage_meter honesty).
> τ calibration unlocks at ≥3 instrumented runs; the slack class-median source unlocks at
> ≥5 samples per class (A1-Q3).

<!-- rows below this line — append only, never edit or delete a row -->
