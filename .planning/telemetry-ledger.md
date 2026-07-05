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
> (`[{taskId, kind, at}]`, orchestrator-classified at gate time from `FAILURE_KINDS`; per-AREA
> entries — final-gate fix-loop areas and ladder events — carry `area:<name>` in the `taskId`
> field, and plan task ids must NEVER begin `area:`), `degraded`
> (`[{scope, reason}]`). Rows with absent `v` read as v1; v1 rows read as `unclassified`
> kinds / null cost (`failure_kinds_of`) — **no backfill; row 1 stands as written.** —
> `calibration: true` rows are EXCLUDED from `class_median` (toy durations must never bias
> real medians); `tokensIn`/`tokensOut` nullable (host-dependent, the usage_meter honesty).
> τ calibration unlocks at ≥3 instrumented runs; the slack class-median source unlocks at
> ≥5 samples per class (A1-Q3).

<!-- rows below this line — append only, never edit or delete a row -->
{"v":1,"utc":"2026-07-04T19:03:44Z","runId":"m4p0-t5-calibration-2026-07-04","target":"scratch/strutil (calibration exercise)","tasks":2,"checkpoints":4,"zeroCheckpointTasks":0,"firstPassAcceptanceByClassTier":{"code\u00d7sonnet":1.0},"streaksByClass":{"code":[2,2]},"fixCycles":0,"gateRejections":0,"taskDurationsByClass":{"code":[2.21,3.5]},"wallClockS":342.9,"tokensIn":null,"tokensOut":116105,"effectiveModes":{"T-A":"telemetry","T-B":"telemetry"},"calibration":true}
{"v":2,"utc":"2026-07-04T20:38:54Z","runId":"m4p1-dogfood-build-2026-07-04","target":"KataHarness (self, P1 dogfooded build)","tasks":4,"checkpoints":10,"zeroCheckpointTasks":0,"firstPassAcceptanceByClassTier":{"code\u00d7opus":1.0},"streaksByClass":{"code":[3,2,3,2]},"fixCycles":0,"gateRejections":0,"taskDurationsByClass":{"code":[11.1,7.2,9.5,3.6]},"wallClockS":1882.2,"tokensIn":null,"tokensOut":509407,"effectiveModes":{"m4p1-W1":"telemetry","m4p1-W2":"telemetry","m4p1-W3":"telemetry","m4p1-W4":"telemetry"},"perTask":{"m4p1-W1":{"tokensIn":null,"tokensOut":115127,"wallClockS":665.1},"m4p1-W2":{"tokensIn":null,"tokensOut":111428,"wallClockS":433.2},"m4p1-W3":{"tokensIn":null,"tokensOut":185088,"wallClockS":568.2},"m4p1-W4":{"tokensIn":null,"tokensOut":97764,"wallClockS":215.7}},"failureKinds":[],"degraded":[]}
{"v":2,"utc":"2026-07-04T21:40:07Z","runId":"m4p2-dogfood-build-2026-07-04","target":"KataHarness (self, P2 dogfooded build)","tasks":2,"checkpoints":4,"zeroCheckpointTasks":0,"firstPassAcceptanceByClassTier":{"code\u00d7opus":1.0},"streaksByClass":{"code":[2,2]},"fixCycles":0,"gateRejections":0,"taskDurationsByClass":{"code":[15.8,4.5]},"wallClockS":1216.5,"tokensIn":null,"tokensOut":211919,"effectiveModes":{"m4p2-X1":"telemetry","m4p2-X2":"telemetry"},"perTask":{"m4p2-X1":{"tokensIn":null,"tokensOut":110096,"wallClockS":945.6},"m4p2-X2":{"tokensIn":null,"tokensOut":101823,"wallClockS":270.9}},"failureKinds":[],"degraded":[]}
{"v":2,"utc":"2026-07-04T21:50:52Z","runId":"m4-liveproof-2026-07-04","target":"scratch/textstat-lp arm-on (live proof: float n=0->1 + ladder firing)","tasks":3,"checkpoints":7,"zeroCheckpointTasks":0,"firstPassAcceptanceByClassTier":{"code\u00d7sonnet":0.667},"streaksByClass":{"code":[2,2,0]},"fixCycles":0,"gateRejections":0,"taskDurationsByClass":{"code":[2.4,2.5,3.8]},"wallClockS":523.5,"tokensIn":null,"tokensOut":266344,"effectiveModes":{"TP":"on","TD":"on","TF":"on"},"perTask":{"TP":{"tokensIn":null,"tokensOut":55633,"wallClockS":145.1},"TD":{"tokensIn":null,"tokensOut":54625,"wallClockS":147.5},"TF":{"tokensIn":null,"tokensOut":156086,"wallClockS":230.9}},"failureKinds":[{"taskId":"TF","kind":"test-regression","at":"2026-07-04T21:45:00Z"}],"degraded":[],"calibration":true}
{"v":3,"utc":"2026-07-04T23:30:00Z","runId":"ca-c11-liveproof-2026-07-04","target":"scratch/c11 smoke-repo rerun + CA-A11 fixture battery (calibration exercise)","tasks":1,"checkpoints":1,"zeroCheckpointTasks":0,"firstPassAcceptanceByClassTier":{"code×haiku":0.0},"streaksByClass":{"code":[0]},"fixCycles":0,"gateRejections":0,"taskDurationsByClass":{"code":[5.6]},"wallClockS":335.3,"tokensIn":null,"tokensOut":72347,"effectiveModes":{"T-F":"on"},"perTask":{"T-F":{"tokensIn":null,"tokensOut":72347,"wallClockS":335.3}},"failureKinds":[{"taskId":"T-F","kind":"test-regression","at":"2026-07-04T23:25:00Z"}],"degraded":[],"parentTokens":{},"calibration":true}
