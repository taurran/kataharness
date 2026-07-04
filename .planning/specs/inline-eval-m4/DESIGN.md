---
spec: inline-eval-m4
title: "Freeze/Float M4 — the inline evaluator/reroll: confidence-scheduled, checkpoint-chunked corrective action"
status: draft-pending-grill-and-freeze-gate
created: 2026-07-04
baseline: master 0daf746 (M1 complete; pytest 2306/3 skip, validator 47/0/0, Snyk medium+ 0)
provenance: >-
  Freeze/Float doctrine (validated draft v2, operator-held) M4 slot; scheduling principles adapted from
  DeepSeek DSpark ("DSpark: Confidence-Scheduled Speculative Decoding with Semi-Autoregressive Generation",
  DeepSeek + Peking University, 2026-06; github.com/deepseek-ai/DeepSpec, MIT). Mechanism-level ideas only —
  no DSpark code is applicable (it is inference-layer); what is borrowed is the SCHEDULER DISCIPLINE.
tags: [kata/freeze-float, kata/spine, inline-eval, M4]
---

# M4 — Inline evaluator/reroll (the smaller loop, sharpened)

## Mission (the operator's framing, verbatim-level)

Sharpen the smaller evaluation loop into CORRECTIVE ACTION at chunk level, so that **the outer KataHarness
loop runs fewer times because rejections happen at a lower level** — without adding overhead that makes the
mechanism counterproductive. The outer loop's fix cycles and gate rejections are the waste pool; M4 moves
detection down one level (checkpoint chunks) and recovery down one level (reroll-from-last-good-commit),
while the existing default-FAIL final gate keeps unmoved final authority.

**End state:** M4 shipped + one live-proof run ⇒ tag **v0.2.0**, the "final" ingestable release for the
operator's downstream platform (the sanctioned KataHarness → PokeVault → MindBridge direction, D30).

## Doctrine + provenance (what is borrowed, and what is deliberately NOT)

DSpark's architecture (parallel drafter + Markov head + confidence head + hardware-aware prefix scheduler)
is token-granular inference machinery — **not adoptable** by a harness over hosted models. Five of its
*principles* are adopted, with the harness translation pinned here so the builder inherits intent:

| DSpark principle | M4 translation |
|---|---|
| Verifier's final say makes speculation lossless | The task gate + kata-evaluate stay the fail-closed authority; M4 is detection-only ahead of them. A disabled/mistuned M4 degrades to today's behavior exactly. |
| Score ACCEPTANCE LENGTH, not pass/fail | Primary metric = **clean-checkpoint streak** (chunks before first trip) per task-class — powers sizing, thresholds, and the "longer safe tasks" payoff. |
| Confidence head is a SEPARATE cheap module, never the drafter self-scoring | Triggers are rule-verifiable durable artifacts only; worker self-assessment NEVER gates (D33 no-self-cert, D136). |
| Cut early on low confidence; long leash on deterministic content | One-dial risk score per checkpoint with per-task-class thresholds: code = long leash (cheap verifiable signals), research/debug = shorter chunks, class-specific signals. |
| Calibrate the scorer against cached verifier outputs | Thresholds calibrated from LOGGED (signal-vector → eventual gate verdict) history — telemetry ships FIRST (P0), conservative defaults until data exists. |

**Explicitly rejected:** fixed-cadence mid-task LLM evaluation (the overhead spiral — an LLM judge costs
~1 chunk to judge 1 chunk; periodic judgment on green work is a net loss, estimated −40..−100%);
token/realtime granularity (our verifier is priced per call, not per parallel pass); any rich rule-engine
in place of the one-dial score.

## Expected value (the honest numbers; P0 exists to replace them with data)

Addressable waste pool ≈ 7% of run tokens (first-pass gate acceptance ~85% historical; fix loop ≈ 0.5×
task cost). Failure-salvage alone ≈ 1.5–2% tokens. The dominant term is second-order: a mid-task safety
net lets planned task size grow ~1.5×, cutting per-task fixed overhead (dispatch context, worktree, gate
ceremony) ⇒ **~5–10% tokens, ~10–20% wall-clock typical; ~25–35% wall-clock on long-task/failure-heavy
runs; floor ≈ break-even tokens (bad trigger precision) while retaining most wall-clock gain.** Not
DSpark's 60–85% — their baseline acceptance was 45.7% and their verifier is free; ours is 85% and paid.

## LOCKED decisions (proposed — the freeze-gate attacks these)

- **M4-L1 — PRIME DIRECTIVE: zero happy-path overhead.** Every M4 mechanism MUST be a no-op while signals
  are green. No periodic evaluation of any kind. Acceptance criterion: instrumented green-run token
  overhead **< 1%** vs baseline. The success metric of the milestone is **outer-loop reduction**: gate
  rejections + fix cycles per unit of work measurably drop (telemetry-proven), not "inline evals ran."

- **M4-L2 — Chunk = the checkpoint commit; recovery = reroll-from-last-good-commit.** Workers already
  commit at checkpoints (kata-orchestrate step 5 cadence); the commit stream IS the draft-prefix
  structure. A reroll kills the worker's session and dispatches a FRESH session from the last good commit
  with a corrective brief — **kill-and-restart, never in-flight steering** (this is what makes M4 work
  under ACP file-only visibility, M4-L9). Accepted prefix chunks are never redone (reject-suffix
  semantics, mirroring both DSpark rejection sampling and the M1 invalidation cascade).

- **M4-L3 — Triggers are rule-verifiable durable artifacts ONLY (D136 extension; DeepSeek
  verifiable-rewards provenance).** The trigger inputs are: board `PROGRESS` slack ratio (elapsed vs
  estimate — the F3/M4 substrate); the per-checkpoint deterministic verify record (M4-L6 per class);
  footprint-vs-ownership drift (files touched outside the task's lane, via the F5 substrate); and
  class-specific signals (M4-L6). **A worker's self-reported confidence never gates** (D33). LLM judgment
  appears only AFTER a trigger (the inline evaluator), never AS a trigger.

- **M4-L4 — One dial: a composite risk score per checkpoint, one threshold τ per task class.**
  Score = weighted combination of the M4-L3 signals, normalized 0–1; `score > τ_class` ⇒ trigger. No rule
  engine, no per-signal thresholds exposed. τ defaults are conservative (trigger-shy) and are
  **calibrated from the P0 telemetry ledger** ((signal-vector, checkpoint-index) → eventual gate verdict)
  once ≥3 instrumented runs exist. Weights/τ live in `kata.config` under a single `inlineEval` block.

- **M4-L5 — The corrective-action ladder (operator-directed shape):**
  1. **Trigger #1** ⇒ inline evaluator (fresh-context, no-write, ECONOMY tier per M4-L7) reads ONLY the
     chunk diff + the task brief + the signal record; verdict ∈ {`continue` (false alarm — log it, feeds
     calibration), `correct` (proceed with a corrective NOTE injected into the next chunk's context),
     `reroll`}. **Reroll #1 is orchestrator-resolvable** (auto, board-logged `DECISION`, bounded): kill
     session, redispatch from last good commit with the corrective brief.
  2. **Trigger #2 on the same task** ⇒ **GROUNDING PASS before any second reroll** (operator amendment):
     the plan-guardian re-anchors the task against the FROZEN plan — is the task spec itself the defect?
     Output = a **tightened task brief** (clarified within plan bounds, orchestrator-authored, board
     `DECISION`), and ONLY then reroll #2. If the grounding pass finds the PLAN is wrong, that routes
     through the existing supersede path (deliberate, audited, human-gated where LOCKED text is touched)
     — **never a silent plan patch**. Repeated failure is treated as evidence about the SPEC, not just
     the worker.
  3. **Trigger #3** ⇒ `human-required` escalation (mirrors the thrash valve N=2 and the liveness ladder).
  The final gate runs unchanged regardless of ladder history (M4-L8).

- **M4-L6 — Task-class signal taxonomy (ALL THREE classes in scope; one scheduler, three signal adapters):**
  - **code**: per-checkpoint test run record (pass/fail/delta), lint/type-check exit, optional mutation
    spot-probe on the chunk, lane drift, slack ratio. Long leash (high τ) — content is deterministic.
  - **research**: per-chunk grounding artifacts — citation-integrity check results (the grounding gate's
    rule-verifiable leg), source-coverage vs the brief's required surfaces, scope drift (chunk topics vs
    brief), slack ratio. Shorter leash (lower τ) — open-ended content roots errors earlier (the DSpark
    context-conditional insight).
  - **debug**: hypothesis-cycle count without a confirmed reproduction, reproduction-status transitions
    (unreproduced→reproduced→fixed), diagnose-thrash (same hypothesis re-entered), slack ratio.
  Class detected from the task's plan metadata (module/run-shape), not inferred at runtime.
  **Phasing:** all three DESIGNED now; implementation P1 = code class end-to-end; P2 = research + debug
  adapters on the proven scheduler. (Assessment: code signals are mature today; research/debug signals
  reuse existing artifacts — grounding gate, diagnose protocol — so P2 is adapters, not new sensors.)

- **M4-L7 — Tier policy (the model-matrix optimization, folded in):** the inline evaluator runs at
  **economy tier (anchor −1), never anchor** — it is frequent, scoped work; anchor-tier inline eval is
  the overhead spiral in disguise. Anchor is reserved for: the M4-L5 grounding pass, human-required
  escalations, and the unchanged final gates. **Acceptance-driven routing (data-first):** P0 telemetry
  records acceptance per (task-class × tier); the closeout report surfaces where a cheap tier's
  fix-loop cost exceeds its token savings (route up) or where anchor does work a lower tier passes at
  parity (route down). v1 is REPORT-AND-RECOMMEND only — no automatic tier mutation (a D131 resolver
  behavior change would need its own gate).

- **M4-L8 — Lossless invariant + kill switch (BC).** M4 never replaces, weakens, or reorders the task
  gate, kata-evaluate, or the adversarial sweep. `kata.config.inlineEval: off | telemetry | on`;
  **absent ⇒ `off` (byte-for-byte BC — existing runs unchanged)**; bootstrap writes `telemetry` for new
  runs until calibration data exists, then offers `on`. Mistuned-M4 worst case = wasted inline-eval calls
  + logged false triggers; never worse output, never a skipped gate.

- **M4-L9 — ACP/file-only visibility contract (Quick-driven sessions are first-class).** Every M4 signal
  is a **durable artifact written at checkpoint time** (board line, git commit, per-checkpoint record
  file in the task worktree committed with the checkpoint) — never an in-session observation; the
  scheduler POLLS files at checkpoint granularity. Adapter contract (normative for adapters/*): (a) the
  worker context can append to the shared board at the integration root (the S3b shared-root rule);
  (b) the platform provides a session kill + fresh-dispatch primitive (reroll needs nothing else — no
  mid-session injection is required by design, M4-L2); (c) no M4 feature may depend on streaming
  output or shared session memory. If (a) or (b) is unavailable on a platform, M4 degrades to
  `telemetry` mode there — surfaced, never silent.

- **M4-L10 — Telemetry P0 (ships FIRST; pure measurement; zero behavior change).** Per task:
  {task-id, class, tier, chunk count, per-checkpoint signal vectors, first-trip index (streak),
  ladder events, gate verdict, fix-cycle count, wall-clock, token counts where the platform exposes
  them}. Per run: first-pass acceptance rate per class × tier; streak distributions. Hot storage
  `.kata/telemetry/` (disposable); a compact per-run summary row appended to a **committed ledger**
  (`.planning/telemetry-ledger.md`) so calibration data is git-durable (the durability lesson of M1-L3).
  P0 alone validates/refutes the Expected-value estimates above.

## Architecture sketch (the builder's mental model)

```
worker session (per task, per chunk):
  build chunk → run class verify (cheap, deterministic) → write checkpoint record
  → commit (checkpoint) → append PROGRESS (done/owned + slack fields)

scheduler (orchestrator loop, on checkpoint artifacts only):
  poll new checkpoint → compute risk score (M4-L4)
  score ≤ τ  → do nothing                                  [the happy path: zero added cost]
  score > τ  → ladder (M4-L5): inline eval (economy tier)
               → continue | correct-note | reroll(kill+redispatch from last good commit)
               → 2nd trigger: grounding pass → tightened brief → reroll
               → 3rd trigger: human-required

final gate: unchanged (M4-L8). telemetry (M4-L10) records everything at every step.
```

New/changed surfaces (the PLAN partitions these): a `tools/` risk-score + telemetry module
(pure, fail-closed per D136 where it drives decisions; telemetry itself is observability and may be
fail-soft); kata-orchestrate prose (checkpoint-record mandate in the dispatch template; the scheduler
loop; the ladder; the grounding-pass step); protocol/board.md (checkpoint-record pointer);
protocol/config.md (`inlineEval` block); kata-tdd/worker prose (per-checkpoint verify record);
kata.config bootstrap defaults; adapter contract note. Exact ownership map is PLAN work, not DESIGN.

## Success / acceptance criteria (checkable end-state)

1. **Outer-loop reduction proven:** on instrumented comparison runs (benchmark A/B machinery, D16),
   fix cycles + gate rejections per unit of work drop vs baseline, with green-run token overhead < 1%
   (M4-L1). If P0 telemetry shows the addressable pool or trigger precision cannot clear break-even,
   the milestone STOPS at P0 (telemetry retained, mechanism shelved) — the kill-switch metric is part
   of the design, not an afterthought.
2. All M4-L* invariants hold under the standard gauntlet: freeze-gate on this DESIGN (HOLD→SHIP),
   frozen PLAN, TDD + mutation proofs on all decision code, integration gate, fresh-context adversarial
   sweep, operator merge gate.
3. BC: `inlineEval` absent ⇒ byte-for-byte unchanged behavior (explicit tests); `telemetry` mode changes
   no dispatch/gate behavior.
4. ACP contract validated at least by protocol conformance (adapter checklist); live ACP proof deferred
   to the Quick adapter milestone (flagged, not silently claimed).
5. Snyk medium+ 0 on new tools; validator 0/0; bump-on-modify honored.

## Out of scope (named, so descoping is deliberate)

Automatic tier mutation from acceptance data (report-and-recommend only, M4-L7). In-flight session
steering (rejected by design, M4-L2/L9). Token-granular or fixed-cadence evaluation (rejected, doctrine).
Trained/learned confidence models (heuristic score + logged calibration only; a learned scorer is a
possible M4.1 once the ledger is deep). M2 (shadow tasks) and M3 (runtime re-partition) — unchanged
ship order. Live DSpark adoption for self-hosted worker tiers (a deployment choice under the
multi-model backlog item, zero harness code).

## Open questions for the grill (before freeze)

1. Corrective-NOTE injection on `correct` verdicts: next-chunk context via the dispatch brief (works in
   ACP kill/restart model) vs an in-worktree `NOTES.md` the worker must read at each chunk — pick the
   one that is verifiable, not just plausible.
2. Checkpoint-record format: extend the board PROGRESS msg vs a per-checkpoint JSON committed in the
   worktree — durability, parse cost, and the board's single-purpose discipline pull differently.
3. Slack-ratio estimates: where does the per-task time estimate come from (plan frontmatter? historical
   class median from the ledger?) — a bad estimate is the main false-trigger source.
4. τ defaults per class before any data exists — propose numbers and the rationale the gate can attack.
5. Does the debug class's ladder interact with kata-diagnose's own loop (double-ladder risk) — needs a
   precedence rule.
