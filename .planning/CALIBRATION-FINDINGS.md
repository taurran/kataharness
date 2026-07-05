# Telemetry Calibration Findings — real-run signals for M4 scorer tuning

> **Purpose.** Durable log of faults + calibration datapoints DETECTED VIA TELEMETRY (and adjacent
> gate/process signals) during real KataHarness runs. This is the raw material for the **calibration
> follow-on task** (τ/weights tuning; the M4.1 learned-scorer candidate). Operator-directed capture,
> 2026-07-04. Append-only; each finding dated + sourced. **Do not tune inline** — collect, then
> calibrate as a deliberate gated task with the ledger + this log as inputs.

Related: `.planning/telemetry-ledger.md` (the committed calibration rows) · `tools/kata_risk.py`
(the scorer under calibration) · `specs/inline-eval-m4/DESIGN.md` (A1-Q3/Q4 weights+τ) ·
`specs/context-autonomy/` (the run that produced most of these).

---

## RUN: context-autonomy v0.2.1 build (2026-07-04, ~23 tasks, telemetry mode)

Method: workers dispatched `inlineEval: telemetry` (record-only); each emitted `Kata-Checkpoint`
trailers. Correctness authority was the fresh-context default-FAIL task-gate battery (M4-L8: the
gate is authority; the inline ladder is additive early-warning — NOT run as governing loop this
build). AFTER the build, the M4 scheduler scorer (`kata_risk.should_trigger`) was run RETROACTIVELY
over all worker checkpoints to observe what the ladder WOULD have done. 57 checkpoints scored.

### FINDING C-1 [HIGH — false-positive class] — suite-level verify red triggers on cross-task artifacts
- **Signal:** 13 of 57 checkpoints scored **0.60 → trigger=True**. **All 13 are FALSE POSITIVES.**
  Every one is a `verify.exit=1 / failed=1` where the single failing test is
  `test_real_tree_readme_in_sync` — the README skill-index vs bumped-frontmatter mismatch, a **benign
  cross-task mechanical artifact** resolved once at integration via `validate_skills.py --write`. It
  is NOT the worker's own owned-file logic failing. **True-positive triggers this run: 0.**
- **Root cause:** `kata_risk` treats the trailer's `verify.exit != 0` as the hard `verify_fail`
  signal (weight 0.60, alone > τ_code 0.50). But the worker's committed verify runs the WHOLE suite,
  which includes a test that fails for reasons outside the worker's owned files (a sibling task's
  index bump not yet synced). The signal is **suite-scoped; it should be owned-file-scoped.**
- **Calibration/fix candidates (for the follow-on, do not apply now):**
  1. Scope the worker verify (and thus the trailer's verify block) to the task's OWNED-FILE tests,
     not the whole suite — the cleanest fix; makes `verify_fail` mean "this chunk broke something it
     owns."
  2. OR: a known-benign-red exclusion list keyed on test-id (`test_real_tree_readme_in_sync` is a
     structural cross-task test — arguably it should never be a per-task verify signal).
  3. OR: trailer carries both suite-exit AND owned-file-exit; scorer reads the latter.
  4. τ note: does NOT help here — 0.60 hard signal clears any τ ≤ 0.60; this is a SIGNAL-DEFINITION
     bug, not a threshold-tuning one. Recorded so calibration doesn't mis-attribute it to τ.
- **Evidence:** retroactive scan, 2026-07-04; e.g. C3 `68b36cf` i=1 exit=1 failed=1 → 0.60/True;
  C1 `5cfce05`, A4 `7537274`, C9 `094b116` identical shape. Reproduce:
  `scan_checkpoints(repo, <worker-branch>, <base>)` + `should_trigger(rec, task_class='code')`.

### FINDING C-2 [POSITIVE datapoint — green-path economics hold at scale]
- **Signal:** 44 of 57 checkpoints scored **0.0 (no trigger, zero LLM calls)** — the happy path.
- **Why it matters:** the M4 <1% green-run overhead thesis (M4-L1, AT-RISK per the gap audit) is
  directionally CONFIRMED at real multi-task scale: the overwhelming majority of real checkpoints
  cost zero evaluator calls. This is the first non-arranged evidence for the green-path cost claim.
  Feed to the <1% re-measurement (gap-audit item 2) with real module sizes.

### FINDING C-3 [MEDIUM — verdict variance by evaluator tier] (from SMOKE-2 F1, corroborated)
- **Signal:** on the same defect flavor, a **sonnet** evaluator returned `correct`; a **haiku**
  evaluator returned `reroll` (both economy-tier; anchor issued no verdict). n=1 vs n=1 — observation,
  not statistics.
- **Calibration need:** the ladder's ACTION (continue/correct/reroll) is tier-sensitive, and the two
  legal verdicts have different cost (reroll discards the chunk). **The ledger should carry
  `verdict × tier`** so τ/verdict calibration can eventually pin an evaluator tier (or a
  quorum/escalation rule) for the inline eval. Named in kata-evaluate SKILL 0.3.1.
- **Fix candidate:** pin the inline-eval verdict tier, OR add a cheap-then-escalate rule (haiku
  screens, sonnet adjudicates a reroll before the kill). Follow-on.

### FINDING C-4 [LOW — stale-expectation, NOT a fault] (from SMOKE-1 F5)
- `class_median('code')` returns **8.35** (median of the six non-calibration code samples); the
  handoff's "returns None at min_samples=5" expectation was a **miscount** (6 samples ≥ 5). Mechanism
  correct; calibration exclusion HOLDS. Recorded so calibration doesn't chase a phantom.

---

## Gate/process signals from the same run (not telemetry-scored, but calibration-adjacent)

These were caught by the fresh-context gate battery, not the scorer — logged because they inform how
much the AUTONOMOUS loop (without the human gate) would need the scorer/RS to catch:

- **G-1 [security]:** Windows implicit-`cmd.exe` on `.bat`/`.cmd`/`.com` children defeats a
  `shell=False` no-shell design (statusline chain wrapper, A2). A POSIX-shaped threat model misses
  it. Lesson: platform-specific execution semantics need a platform lens in review. FIXED in-run
  (gate → fold → SHIP); `.snyk` acceptance for the residual CWE-78 false positive.
- **G-2 [doc-drift]:** the observability doc (C4) shipped from a pre-build draft with 11 stale
  file:line citations + a materially-stale ledger-version section (taught v1/v2 as current; code now
  emits v3). Lesson: docs authored against a pre-build tree MUST re-verify citations post-integration.
  FIXED (rework, ~40 cites re-audited).
- **G-3 [logic]:** the Fable premium decline arm was conflated across cases — a literal conductor
  would hard-stop a legitimate offer-decline (kills the run OP-2 protects). Lesson: control-flow prose
  with per-case behavior needs per-case gating stated explicitly. FIXED (rework).

## Next
Calibration follow-on task (deliberate, gated): ingest this log + the telemetry ledger; prioritize
**C-1** (signal-definition, highest-frequency false positive); re-measure green-path overhead with
**C-2** data; wire **verdict×tier** ledger columns for **C-3**. Do NOT tune τ before fixing C-1's
signal definition — the current τ never gets a fair test while the verify signal is suite-scoped.
