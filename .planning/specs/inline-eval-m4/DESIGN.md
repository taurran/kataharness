---
spec: inline-eval-m4
title: "Freeze/Float M4 — the inline evaluator/reroll: confidence-scheduled, checkpoint-chunked corrective action"
status: FROZEN 2026-07-04 (grill Amendment #1 + gate v1 HOLD folds Amendment #2 + gate v2 SHIP-WITH-FIXES folds Amendment #3; pending operator commit gate)
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

- **M4-L1 — PRIME DIRECTIVE: zero happy-path overhead.** **No LLM evaluation of green work, ever** — LLM
  judgment appears only after a rule-based trigger. *(Gate v2 #9 wording precision: the design's happy path
  DOES compute rule-based signals + a risk score per checkpoint and the scheduler DOES poll durable
  artifacts — bounded mechanical cost, priced at module-sized chunks; the instrumented **< 1%** green-run
  overhead cap vs baseline is the operative, falsifiable criterion, measured per the M4-L10 path.)* The success metric of the milestone is **outer-loop reduction**: gate
  rejections + fix cycles per unit of work measurably drop (telemetry-proven), not "inline evals ran."

- **M4-L2 — Chunk = the checkpoint commit; recovery = reroll-from-last-good-commit.**
  *(Amended #2 — gate HIGH-1: the original premise "workers already commit at checkpoints" was FALSE —
  kata-orchestrate step 5 is the ORCHESTRATOR's once-per-task integration commit; the dispatch template and
  kata-tdd mandate no worker commit.)* **M4 INTRODUCES a mandated worker checkpoint-commit cadence**: the
  dispatch template (and kata-tdd worker prose) gains a per-chunk commit mandate on the task branch — this
  commit stream IS the draft-prefix structure. This makes worker task-branch commits **load-bearing**,
  a deliberate **partial supersede of D134** ("nothing load-bearing depends on it") recorded as **D141**:
  D134's task-granular re-dispatch remains the RESTORE semantics; M4 reroll anchoring is a new, additive
  consumer of the commit stream. A reroll kills the worker's session and dispatches a FRESH session from
  the last good commit with a corrective brief — **kill-and-restart, never in-flight steering** (this is
  what makes M4 work under ACP file-only visibility, M4-L9). Accepted prefix chunks are never redone
  (reject-suffix semantics, mirroring both DSpark rejection sampling and the M1 invalidation cascade).
  **Kill discipline (gate MED-5):** the kill must be CONFIRMED-DEAD before any fresh dispatch; a kill
  FAILURE ⇒ escalate `kind: human-required`, NEVER proceed-and-re-dispatch over a possibly-live worker
  (imports the contract-supersede abort-failure rule verbatim — the double-writer hazard). Adapter kill
  bindings are named per platform: Claude host = the host's background-task stop on the dispatched
  worker; LD6 off-host = OS process kill of the background subprocess; a platform with no kill binding ⇒
  M4 degrades to `telemetry` there (M4-L9c, surfaced). **Reroll topology (gate MED-10):** a reroll NEVER
  rewrites history on the existing task branch — it forks a NEW attempt branch (`<task>-attempt<n>`) at
  the anchor commit; the orchestrator logs the active attempt branch in the reroll `DECISION` line and the
  scheduler polls ONLY the active attempt branch (abandoned-suffix trailers are structurally out of scope);
  the killed attempt's worktree is removed+pruned (the existing abort route) before the fresh worktree
  opens at the anchor. After any reroll, "the task branch" everywhere in the loop (lane check, integrate,
  checkpoint steps 3–5) means the **ACTIVE attempt branch** (gate v2 #7; merge-base with integration stays
  the original fork point — single base — so the three-dot lane check is unchanged in behavior).

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
  - **code**: per-checkpoint test run record (pass/fail/delta), lint/type-check exit, lane drift, slack
    ratio. Long leash (high τ) — content is deterministic. *(Amended #2 — gate MED-8: the mutation
    spot-probe is REMOVED from the signal list — signals are computed every checkpoint, so a per-chunk
    probe is periodic happy-path work, the M4-L1 spiral in miniature; wall-clock cost would also escape
    the token-denominated tripwire. It survives only as a post-trigger tool the inline evaluator MAY run.)*
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

- **M4-L7 — Tier policy (the model-matrix optimization, folded in):** the inline evaluator runs
  **strictly BELOW anchor, never at anchor** — it is frequent, scoped work; anchor-tier inline eval is
  the overhead spiral in disguise. *(Amended #2 — gate HIGH-2: the original "anchor −1" precision was
  unimplementable through the D131 resolver as built — economy steps are mode- and family-dependent
  (Anthropic: advanced −1, standard/essential −2; generic default: advanced 0), and absent
  `kata.config.models` the resolver returns `None` everywhere ⇒ inherit-anchor.)* Binding rules: the
  inline-eval skill registers in `kata_models.SKILL_WORK_CLASS` as **`economy`** (the R5 coverage test
  forces registration); its dispatch resolves through `kata_models.resolve()` like every dispatch —
  landing wherever the mode×family economy cell lands, which is strictly below anchor whenever the
  resolver resolves at all. **Degrade rule (the "never anchor" enforcement):** if `resolve()` returns
  `None` for the inline-eval slot (no `models` block, unknown family/anchor, or a zero-step cell), M4
  **degrades to `telemetry` mode for that run — surfaced, never a silent anchor-tier eval** (mirrors the
  M4-L9 platform degrade; the resolver's inherit-on-doubt fail-safe must never collide silently with this
  design's "never" invariant). **R2-fallback carve-out (gate v2 #1):** the R2 dispatch-failure fallback
  terminus (≤2 step-downs then OMIT-inherit) does NOT apply to the inline-eval slot — on chain exhaustion,
  or a `fallback_chain` of `[None]` (the resolved economy model is already the family floor), do NOT
  omit-and-inherit: **skip the eval and degrade M4 to `telemetry` for the run, surfaced** (same route as
  resolution-time `None`). The inline evaluator NEVER dispatches without an explicit below-anchor model id. Anchor is reserved for: the M4-L5 grounding pass, human-required
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
  is a **durable artifact written at checkpoint time** (board line, git commit, ~~per-checkpoint record
  file in the task worktree committed with the checkpoint~~ *[SUPERSEDED by A1-Q2, gate MED-7: `.kata/`
  is gitignored tier-3 so a committed record FILE is unsatisfiable; the record is a `Kata-Checkpoint:`
  commit-message trailer on the checkpoint commit itself]*) — never an in-session observation; the
  scheduler POLLS durable git/board artifacts at checkpoint granularity. Adapter contract (normative for adapters/*): (a) the
  worker context can append to the shared board at the integration root (the S3b shared-root rule);
  (b) the platform provides a session kill + fresh-dispatch primitive (reroll needs nothing else — no
  mid-session injection is required by design, M4-L2); (c) no M4 feature may depend on streaming
  output or shared session memory. If (a) or (b) is unavailable on a platform, M4 degrades to
  `telemetry` mode there — surfaced, never silent.

- **M4-L10 — Telemetry P0 (ships FIRST; pure measurement; no scheduling/gating/recovery behavior change).**
  Per-task records additionally carry the task's **effective `inlineEval` mode** (gate v2 #10 — per-run
  resolver degrade × per-platform capability degrade make mixed-mode runs legal; the ledger must say what
  actually ran). *(Amended #2 — gate HIGH-3: "zero behavior change" was an overclaim — per-checkpoint signal vectors can
  only exist if the worker dispatch brief gains the checkpoint-commit + trailer mandate, so P0/`telemetry`
  DOES change worker dispatch content. The honest claim: `telemetry` changes NO scheduling, gating, or
  recovery behavior — no triggers, no ladder, no kills — and the record mandate's cost is precisely what
  P0's <1% instrument measures.)* Per task:
  {task-id, class, tier, chunk count, per-checkpoint signal vectors, first-trip index (streak),
  ladder events, gate verdict, fix-cycle count, wall-clock, token counts where the platform exposes
  them}. Per run: first-pass acceptance rate per class × tier; streak distributions. Hot storage
  `.kata/telemetry/` (disposable); a compact per-run summary row appended to a **committed ledger**
  (`.planning/telemetry-ledger.md`) so calibration data is git-durable (the durability lesson of M1-L3).
  **Ledger home + commit authority (gate HIGH-4):** the ledger lives in the **HARNESS repo** (calibration
  is cross-run/cross-target by definition — a per-target ledger could never reach the ≥3-runs/≥5-samples
  thresholds); target-repo runs locate it via a `telemetryLedger` path in `.kata-settings.json` (machine
  settings, the `confirmedPlatforms` precedent) — **absent ⇒ the ledger source is absent** (A1-Q3 falls
  through to frontmatter/absent, the documented fail-safe; hot-storage telemetry still accumulates). The
  row-append is **NOT an autonomous commit**: D133's carve-out covers ONLY the board→orphan-ref; the
  ledger row is written at closeout and rides the existing **human-gated closeout commit** (recorded in
  D141 — no new autonomous-git path is created by implication). **Target-repo vehicle (gate v2 #2):**
  when `telemetryLedger` resolves OUTSIDE the run's target repo (the normal case for target-repo runs —
  including the planned live proof), the target repo's closeout commit structurally cannot carry the row;
  closeout therefore requests a **second, explicitly human-gated commit in the ledger's repo** (same
  human, same gate, ledger row only). Declined or failed ⇒ the append is **surfaced as
  pending-uncommitted, never silent** (the M1-L3 durability promise is kept or loudly deferred, never
  quietly broken). A **malformed ledger row** read by the
  class-median computation RAISES (never skip-and-average — gate MED-9b).
  P0 alone validates/refutes the Expected-value estimates above. **Measurement path for the <1% cap and
  the kill-switch (gate MED-11):** the P0 A/B runs in a token-surfacing configuration wherever available;
  where the host surfaces no token counts (`usage_meter` nullable-honesty), the DOCUMENTED proxy is
  wall-clock + tool-call counts with the same <1% threshold on wall-clock, labeled as proxy — the STOP-at-P0
  decision is defined over whichever of (tokens | proxy) the run actually measured, stated explicitly in
  the P0 report, never silently unmeasurable.

## Architecture sketch (the builder's mental model)

```
worker session (per task, per chunk — the commit cadence is NEW, mandated by the dispatch brief, D141):
  build chunk → run class verify (cheap, deterministic)
  → commit (checkpoint) carrying the Kata-Checkpoint: trailer (the record — A1-Q2)
  → append PROGRESS (done/owned; slack is COMPUTED by the scheduler from PROGRESS
    timestamps + done/owned — the board format is untouched)

scheduler (orchestrator loop, on durable checkpoint artifacts only — polls the ACTIVE attempt branch):
  poll new checkpoint → compute risk score (M4-L4)
  score ≤ τ  → do nothing                                  [the happy path: zero added cost]
  score > τ  → ladder (M4-L5): inline eval (economy tier)
               → continue | correct-note | reroll(kill+redispatch from last good commit)
               → 2nd trigger: grounding pass → tightened brief → reroll
               → 3rd trigger: human-required

final gate: unchanged (M4-L8). telemetry (M4-L10) records everything at every step.
```

New/changed surfaces (the PLAN partitions these — list amended per gate HIGH-1/MED-9/LOW-14): a `tools/`
risk-score + telemetry module (pure, fail-closed per D136 where it drives decisions; telemetry itself is
observability and may be fail-soft); `tools/kata_models.py` `SKILL_WORK_CLASS` registration of the
inline-eval skill as `economy` (R5 coverage test forces it — a D131-data addition, gated as such);
kata-orchestrate prose (the **worker checkpoint-commit + `Kata-Checkpoint:` trailer mandate in the
dispatch template — a NEW mandate, not an inherited one**; the scheduler loop; the ladder; the
grounding-pass step; load-guard: a **present-but-malformed `inlineEval` value ⇒ STOP + escalate**, the
D45/GB12 posture — never "unknown ⇒ off"); kata-tdd worker prose (the per-chunk commit cadence +
per-checkpoint verify record); protocol/config.md (`inlineEval` block); protocol/board.md is
**UNTOUCHED** (A1-Q2 — no pointer line, PROGRESS format unchanged); kata-plan freeze validation (a
present-but-malformed per-task `estimate:` fails at freeze — A1-Q3; task-level `class:` frontmatter is
the class-detection source, default `code` — never `runShape`, which is provenance-only);
`.kata-settings.json` `telemetryLedger` path; kata.config bootstrap defaults; adapter contract note
(`adapters/`). kata-evaluate is NOT a surface in P0/P1 (the final gate is unchanged, M4-L8; the
`evidence` digest field is telemetry-only in P0, consumed by the inline evaluator at trigger time in P1,
and gate-time evidence re-validation is **DEFERRED — flagged, not silently claimed**). Exact ownership
map is PLAN work, not DESIGN.

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
   no **scheduling, gating, or recovery** behavior (no triggers, no ladder, no kills) — it DOES add the
   checkpoint-record mandate to the worker brief, whose cost is what the P0 <1% instrument measures
   (amended per gate HIGH-3); a present-but-malformed `inlineEval` value ⇒ load-guard STOP + escalate
   (never a silent "off").
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

## Grill resolutions (Amendment #1 — 2026-07-04, anchor-grilled; supersedes the open questions below)

The five open questions were grilled at anchor per the M4 handoff recipe step 2. Each resolution is a
dated amendment. *(Corrected by Amendment #2: the original claim here that "M4-L1..L10 stand unchanged in
shape" did not survive the freeze-gate — gate v1 (2026-07-04, HOLD) found the substrate account inside
M4-L2/L7/L9/L10 unsound; those decisions now carry loud in-place amendments. The doctrine — event-triggered,
trigger-shy, evidence-only, lossless — is unchanged; the gate confirmed it clean.)*

**A1-Q1 — Corrective-NOTE transport: ONE recovery primitive, parameterized by anchor commit (no second
channel).** The ladder's three verdicts share the single M4-L2 primitive (kill + fresh dispatch); they
differ only in `(anchor_commit, brief_delta)`:
- `continue` → no action (false alarm; logged to the ledger for τ calibration).
- `correct` → kill + fresh dispatch from the **CURRENT checkpoint** (the flagged chunk is kept — it was
  acceptable-with-guidance) with the corrective note folded into the dispatch brief.
- `reroll` → kill + fresh dispatch from the **last good commit** (last below-τ checkpoint, else the task's
  dispatch base) with the corrective brief.
*Why (verifiable, not plausible):* the dispatch brief is a durable, orchestrator-authored artifact — the
transport is verifiable by construction and exists on every platform via adapter primitive (b) alone. The
rejected alternative (an in-worktree `NOTES.md` the live worker "must read each chunk") rests on worker
compliance (M1-L3: soundness never rests on compliance), needs an ack-in-next-checkpoint protocol to be
verifiable at all, and has an unfixable race (a note landing mid-chunk is unseen until N+2). Cost note: a
`correct` restart pays one dispatch-context overhead on an already-triggered task — bounded, rare by
construction (trigger-shy τ), and it buys zero new seams. In-flight partial work past the anchor commit is
discarded on any kill; that loss is bounded by one chunk (polling-lag waste, triggered paths only).

**A1-Q2 — Checkpoint-record transport: a `Kata-Checkpoint:` commit trailer, NOT a file, NOT a board
extension.** `.kata/` is gitignored tier-3 (D132/D133 — the board needed an orphan ref for exactly this
reason), so "a record file committed with the checkpoint" is unsatisfiable as drafted, and extending the
board's PROGRESS line violates its one-line/single-purpose discipline (D135; the escalation-payload
precedent keeps structure OFF the board). The checkpoint commit itself already travels: the worker appends
ONE compact single-line JSON trailer `Kata-Checkpoint: {"i":<n>,"verify":{"exit":0,"passed":N,"failed":N},
"lint":<exit>,"evidence":<digest>,...}` to its checkpoint commit message (M1 trailer
precedent: `Kata-Task:`/`Kata-Supersede:`). *(Gate v2 #3: `slack` is struck from the trailer — slack is
SCHEDULER-computed from PROGRESS timestamps + done/owned (see the sketch); the worker cannot read the
harness-repo ledger and a worker-authored ratio would be a self-report entering the signal vector.)*
**Trailer well-formedness (gate v2 #5):** MORE than one `Kata-Checkpoint:` trailer on a commit, or a
checkpoint trailer on a MERGE commit (multi-parent — "the chunk diff" is undefined), is MALFORMED ⇒
treat-as-triggered + surface (never first/last-wins on ambiguous evidence). **Chunk unit (gate v2 #4):**
chunk ≙ **owned-module completion** — the same unit as the F3 PROGRESS `done/owned` cadence `[TUNABLE]`;
the checkpoint commit and the module-completion PROGRESS line are two artifacts of the same boundary, so
the trailer's `"i"` index, the streak metric, and A1-Q3's `expected_fraction_complete` all align on one
definition (and the <1% overhead recount is priced at module-sized chunks, not per red→green micro-cycle). Durability = git-by-construction; the scheduler polls task-branch
commits (durable artifacts at checkpoint granularity, M4-L9) and parses trailers with the D139-hardened
discipline (parser RAISES on git error; malformed trailers loudly surfaced, never `{}`). The `evidence`
field is a combined digest over the chunk's files *(re-specified by Amendment #2, gate MED-6/LOW-14c: the
digest is computed over the checkpoint commit's own **git blob hashes** — `git ls-tree` at the checkpoint
commit for the chunk's changed paths — NOT filesystem reads, so it is defined over committed content by
construction; a path DELETED by the chunk enters the digest as an explicit `path:ABSENT` entry, so a
deletion is detectable, honoring the F5-4 None-at-stamp contract in spirit; a listed path that cannot be
resolved against the commit tree at stamp time ⇒ RAISE, loud, never hashed-as-missing. Consumer, named:
telemetry-only in P0; read by the inline evaluator at trigger time in P1; gate-time evidence re-validation
is DEFERRED and flagged — the unchanged final gate re-runs everything, M4-L8, which is what makes the
deferral sound.)* Board = untouched (PROGRESS
unchanged; no pointer line — the commit is the event). Fail-closed bindings (D136): the risk-score tool
RAISES on a malformed record; the scheduler's documented response to that raise is **treat-as-triggered +
surface** (a designed fail-safe, D136-exempt as documented). A **mandated-but-missing** record on a
checkpoint commit (task dispatched with `inlineEval: on`) scores as a hard signal (see A1-Q4), never as
green. *D33 boundary (state it before the gate asks):* the record carries worker-reported **mechanical
outputs** (exit codes, counts — re-runnable from the commit, rule-verifiable in principle), never worker
self-ASSESSMENT; the gating judgment stays with the orchestrator-side inline evaluator, and the unchanged
final gate re-runs everything (M4-L8 — a wrong record delays detection, never worsens output).

**A1-Q3 — Slack-estimate source precedence: ledger class-median → plan frontmatter → signal-absent.**
(1) When the telemetry ledger holds ≥5 task samples for the class, the estimate is the ledger's class
median (data over guesses); (2) else an optional per-task `estimate:` in plan frontmatter, when present;
(3) else the slack term is ABSENT — it contributes 0 to the capped-sum score (trigger-shy: a missing
estimate must never manufacture a trigger; documented fail-safe, D136-exempt). A present-but-malformed
`estimate:` fails at plan-freeze validation (freeze-time raise, not a mid-run surprise). The ratio is
progress-normalized where PROGRESS provides `modulesDone/modulesOwned` (F3): `elapsed / (estimate ×
expected_fraction_complete)` — a task 3/5 done at 2× pace signals earlier and more honestly than absolute
task time. **Zero-progress guard (gate v2 #6):** `expected_fraction_complete == 0` (no module yet
complete — the mandated `0/1` early-heartbeat form) ⇒ the slack term is ABSENT (contributes 0); the
formula must never manufacture a trigger against a healthy early worker (division-by-zero is not a signal).

**A1-Q4 — τ defaults + weights (provisional, [TUNABLE], calibrated from the ledger at ≥3 instrumented
runs per M4-L4).** Score = `min(1.0, Σ active-signal weights)`, one τ per class. Weights (v1 defaults,
config-overridable under `inlineEval`, no per-signal thresholds):
- Hard signals, weight **0.60** each: per-checkpoint verify FAIL (exit ≠ 0); lane drift (non-empty
  out-of-footprint set via the F5 commit-scoped diff); mandated-but-missing checkpoint record;
  (research) citation-integrity FAIL; (debug) ≥3 hypothesis cycles without a confirmed repro, or a
  repro-status regression (reproduced→unreproduced).
- Soft signals: slack ratio ≥ 2.0× ⇒ **0.30** (else 0); (research) source-coverage gap **0.25**, scope
  drift vs brief **0.25**; (debug) same-hypothesis re-entry **0.30**.
- τ defaults: **code 0.50 · research 0.45 · debug 0.45.**
Rationale the gate can attack arithmetically: every hard signal alone crosses every τ (0.60 ≥ 0.50) —
deterministic failure evidence always triggers; no soft signal alone crosses any τ (0.30 < 0.45) — slack
alone never false-triggers pre-calibration; soft PAIRS cross only in research/debug (0.25+0.25=0.50 ≥ 0.45;
0.30+0.30=0.60 ≥ 0.45) and not in code (slack is code's only soft signal ⇒ code triggers on hard evidence
only = the long leash), encoding the DSpark context-conditional insight as τ ordering + signal mix rather
than a rule engine.

**A1-Q5 — Ladder arbitration (the ONE paragraph, M4 × liveness × fix-loop × kata-diagnose).** At most one
corrective ladder is active per task, arbitrated by **evidence class**: (1) an open escalation or park on a
task SUSPENDS its M4 ladder (a parked task produces no checkpoints; resolution re-arms the ladder fresh,
trigger count intact). (2) **Absence of signal** (staleness) routes ONLY through the liveness ladder —
nudge → human-required — and staleness alone NEVER authorizes a kill (F3/D139: the dark worker may be
healthy-but-slow; double-writer hazard). (3) **Present-but-bad evidence** (a triggered, committed
checkpoint) routes ONLY through the M4 ladder; an inline-eval `reroll`/`correct` verdict is the one bounded
auto-kill authority (orchestrator-resolvable, board-logged `DECISION`), and it stands even if the worker
has meanwhile gone dark — an evidence-backed kill is not a blind kill. (4) The M4 ladder ENDS at the task
gate: the final-gate fix loop and its thrash budget count only their own cycles; M4 ladder history never
spends the thrash budget and vice versa (M4-L8). (5) Inside a debug-class task, kata-diagnose's
hypothesis loop is the WORKER's discipline — M4 reads only the emitted checkpoint artifacts and never
arbitrates within-session hypothesis cycling; a debug-class trigger #3 routes to the existing
`human-required` kind (no enum change — the L6/D139 precedent). Trigger #2's grounding pass is
orchestrator-authored (board `DECISION`); a plan-defect finding routes through the existing supersede
path, never a silent patch (M4-L5 unchanged).

## Freeze-gate history + Amendment #2 (2026-07-04)

**Gate v1 (fresh-context adversarial, no-write, adjacent seams named per L19): HOLD** — 4 HIGH / 7 MED /
3 LOW. Headline catches, all folded as loud in-place amendments above: **HIGH-1** the "workers already
commit at checkpoints" premise was FALSE (step 5 is the orchestrator's integration commit; kata-tdd never
commits) and making the commit stream load-bearing partially supersedes FROZEN D134 → M4-L2 amended, D141
records the supersede; **HIGH-2** "anchor −1 via D131" was unimplementable (mode/family-dependent economy
steps; BC-default config would run the inline evaluator AT ANCHOR silently) → M4-L7 amended: strictly-below-
anchor + degrade-to-telemetry when `resolve()` returns `None`; **HIGH-3** "telemetry = zero behavior change"
overclaimed (the record mandate changes worker briefs) → M4-L10 + criterion 3 re-scoped honestly; **HIGH-4**
the committed ledger had no commit authority (D133 covers only board→orphan-ref) and no home → M4-L10
amended: harness-repo ledger, `.kata-settings.json` `telemetryLedger` locator, row rides the human-gated
closeout commit. **MED-5** kill confirmed-dead + kill-failure ⇒ `human-required` + per-platform kill
bindings → folded into M4-L2. **MED-6** evidence digest re-specified over git blob hashes with explicit
deletion entries + RAISE on unresolvable + named consumer → folded into A1-Q2. **MED-7** loud supersede
markers added to M4-L9 and the sketch; the Amendment #1 preamble corrected. **MED-8** mutation spot-probe
removed from the signal list (post-trigger tool only). **MED-9** malformed `inlineEval` ⇒ load-guard STOP;
malformed ledger row ⇒ RAISE. **MED-10** reroll topology pinned (new attempt branch, active-branch polling,
worktree remove+prune on kill) → folded into M4-L2. **MED-11** <1%/kill-switch measurement path pinned
(tokens where surfaced, else the wall-clock+tool-calls proxy, stated in the P0 report) → folded into M4-L10.

Remaining folds recorded here (LOW tier):
- **LOW-12 (compliance hole, named):** a worker that never commits checkpoints is invisible to M4 —
  bounded by M4-L8 (detection-only ⇒ today's behavior), but named, not hidden. Cheap tell: a `DONE` whose
  task branch carries **zero checkpoint commits** on a run with `inlineEval ≠ off` ⇒ a telemetry flag
  (ledger-visible), feeding calibration; never a gate.
- **LOW-13 (debug pre-calibration caveat, stated):** with slack ABSENT (no ledger, no estimate — the
  cold-start regime) debug cannot soft-trigger (its only soft pair includes slack); debug pre-calibration
  triggering rests on its hard signals alone. Acceptable and intended (trigger-shy), now explicit.
- **LOW-14a/b:** the plan-freeze `estimate:` validation site and the task-level `class:` frontmatter
  source (never `runShape`) are added to the change-surface list above.
- **LOW-14d (substrate honesty):** the handoff's "PROGRESS heartbeat + slack fields BUILT" shorthand is
  read precisely: `protocol/board.md` PROGRESS carries `done/owned <label>` + self-stamped timestamps —
  the SUBSTRATE for slack computation, not literal slack fields. The scheduler COMPUTES slack from
  PROGRESS timestamps + done/owned (see the sketch); the board format is untouched.
- **MED-10 corollary (lane-check raise route):** a mid-run `changed_in_task` RAISE (multi-merge-base /
  no-ancestor — `tools/footprint.py` fail-closed) reaching the per-checkpoint lane-drift signal is routed
  exactly like a malformed record: **treat-as-triggered + surface** (documented fail-safe, D136-exempt).

**Gate v2 (fresh-context, distinct reviewer, fold-verification + fresh attack): SHIP-WITH-FIXES** —
2 HIGH / 4 MED / 4 LOW, all folded same-day (the SHIP-WITH-FIXES-terminal precedent of the M1 P2 gate):
- **v2-HIGH-1 → M4-L7:** the R2 dispatch-failure fallback terminus (OMIT-inherit) would have silently run
  the inline evaluator AT ANCHOR on chain exhaustion — carve-out added: skip-eval + degrade-to-telemetry,
  never OMIT-inherit for this slot.
- **v2-HIGH-2 → M4-L10 + D141(b):** target-repo runs (incl. the live proof) had NO commit vehicle for the
  harness-repo ledger row — second explicitly human-gated commit in the ledger's repo; declined/failed ⇒
  pending-uncommitted, surfaced.
- **v2-MED-3 → A1-Q2:** worker-authored `slack` struck from the trailer (scheduler-computed only).
- **v2-MED-4 → A1-Q2:** chunk pinned ≙ owned-module completion (the F3 `done/owned` unit) `[TUNABLE]`.
- **v2-MED-5 → A1-Q2:** duplicate trailers / trailer-on-merge-commit = malformed ⇒ treat-as-triggered.
- **v2-MED-6 → A1-Q3:** `expected_fraction_complete == 0` ⇒ slack ABSENT (no manufactured early trigger).
- **v2-LOW-7 → M4-L2:** "task branch" post-reroll = active attempt branch, stated for loop steps 3–5.
- **v2-LOW-8:** supersede banner added to the HANDOFF (three stale shorthands; DESIGN takes precedence —
  the D138 stale-doc class).
- **v2-LOW-9 → M4-L1:** wording precision — "no LLM evaluation of green work" + the <1% cap as the
  operative criterion (the absolutist "no-op" sentence was falsifiable against the design's own polling).
- **v2-LOW-10:** the per-run ledger row records each task's EFFECTIVE inlineEval mode (mixed-platform runs
  are legal: per-run resolver degrade × per-platform capability degrade); every degrade is surfaced as a
  board `NOTE` + a run-start (or discovery-point) conversation line — never silent.
Gate v2 verified all 14 v1 folds RESOLVED (HIGH-4 partially → completed by v2-HIGH-2's vehicle clause).
Clean under fresh attack: A1-Q4 arithmetic, A1-Q5 arbitration, board protocol untouched, escalation kinds
unextended, kata-evaluate not-a-surface claim, attempt-branch × concurrency-snippet composition.

**Post-gate status: DESIGN FROZEN as of 2026-07-04 (v1 HOLD → all folded → v2 SHIP-WITH-FIXES → all
folded). LOCKED set = M4-L1..L10 as amended + A1-Q1..Q5 + the Amendment #2/#3 bindings. Pending the
operator commit gate (branch `m4/inline-eval`, commits on approval only).**

## Amendment #4 (2026-07-04, OPERATOR-DIRECTED scope addition — M4 observability fields; routed
via the supersede/amendment path, deliberate and human-gated)

**Disposition (routing rule applied against VERIFIED phase state):** at receipt, the DESIGN
freeze-gate had passed (`1cd1a60`), PLAN-p0 was frozen (`75ac522`), the ledger schema v1 was built
and merged (T1 `fb0568a`), and ledger rows existed (row 1, `32bd7f2`) ⇒ **routing branch 3: no
mid-phase retrofit; P0.1 schema-bump queued immediately after P0 completion** (P0 completed at
`32bd7f2`; P0.1 executes next, before P1). Recorded as a board `DECISION` + **D142**.

**The addition (extends M4-L10; ADDITIVE-ONLY; ledger row schema v1 → v2; no backfill — v1 rows
read as `failure kinds unclassified / cost null`, never fabricated):**
1. **Ledger cost columns:** per-task `{tokensIn, tokensOut, wallClockS}` in the ledger row —
   populated where the platform exposes them, **explicit nulls** where not (usage_meter honesty).
   *Named consumers:* the M4-L7 acceptance-driven routing break-even; post-July-7 anchor-metering
   budgeting.
2. **Failure-kind enum:** one structured field per gate rejection (and per M4 ladder event, P1+),
   enum `{test-regression, lane-drift, spec-misread, integration-conflict, packaging, security,
   other}` (+ the reader-side `unclassified` for v1/legacy rows) — classified by the ORCHESTRATOR
   at gate time, **never worker self-classified** (D33). An unknown kind at row-BUILD time RAISES
   (producer bug, loud); at READ time unknown/absent maps to `unclassified` (observability,
   fail-soft with explicit sentinel). *Named consumers:* the τ-calibration failure-type-mix
   parameter (§1 named it unmeasured); recurrence/L19 failure-class hardening.
3. **Structured degraded-mode signal (folds BACKLOG #16 into M4):** the stdout-only NOTE fallbacks
   gain a machine-readable leg — `kata_restore`: additive `collect_integrated_tasks_ex(...) ->
   {tasks, degraded, reasons}` (the bare-set `collect_integrated_tasks` delegates, byte-identical
   BC) + additive `restore()` keys `degraded: bool` / `degraded_reasons: [str]`; the ledger row v2
   gains `degraded: [{scope, reason}]` covering every M4 degrade path (resolver-None, missing kill
   binding, tools-dir unresolvable, absent-locator pending row). NOTEs stay (the human leg).
   *Named consumers:* degraded-run exclusion in calibration/A-B analysis; programmatic restore
   callers (kata-orient/kata-readiness).
**Constraints honored:** all fields orchestrator/gate-side or on already-emitted artifacts — zero
new per-checkpoint worker emissions (M4-L1 holds); D136 fail-closed only where a field drives a
decision; every item has a named consumer (none dropped).

**LIVE PROOF + MILESTONE status (dated note, 2026-07-04, D145):** COMPLETE. The ladder fired
live (trigger 0.60>0.50 on an arranged red checkpoint; inline eval at sonnet via D131; verdict
`correct` diff-cited; redispatch-with-NOTE; attempt-2 green with index continuity); the float ran
n=0→1 (builds_against dependent at freeze; pin MATCH; stubs 0; danglers 0; suite 15/15); A/B:
0 gate rejections on-arm vs 1 rejection + 1 fix cycle control. Happy path = zero LLM calls live.
Ledger row #4. v0.2.0 tags this state. Honest limits recorded in D145 (toy-scale economics; <1%
cap AT-RISK with named remediation; class extras await producers).

**P1+P2 status (dated note, 2026-07-04):** P1 BUILT (dogfooded+instrumented, run #2, D143;
L19 cross-seam sweep SHIP-WITH-FIXES 0 HIGH, all folded) — kata_risk, kata-inline-eval (48th
skill), orchestrate 0.7.0 scheduler+ladder, adapter contract. P2 BUILT (D144) — per-class leashes
live; class extras DATA'd with named-deferred producers (gate-caught: the originally-specced
sources did not exist); orchestrate 0.8.0. A1-Q4's research citation-integrity hard signal is
REALIZED as the research-class verify riding verify.exit (P2 gate HIGH-3 fold — arithmetically
identical, recorded here as the DESIGN-text reconciliation). Ledger ≥3 instrumented runs: the
M4-L8 offer-`on` threshold is MET. Remaining: live proof + closeout.

**P0 status (dated note, 2026-07-04):** P0 BUILT + instrumented calibration run #1 COMPLETE.
PLAN-p0-telemetry frozen (own double gate: v1 HOLD incl. a kill-switch-relocation BLOCKER; v2
SHIP-WITH-FIXES; all folded). T1 `fb0568a` (kata_telemetry, +70 tests → 2376/3, 7 mutation proofs,
Snyk 0), T3 `b281a71`, T2 `18ff54a` (orchestrate 0.6.0), T4 `af5d6dc` (committed ledger + locator).
T5: 2-arm calibration A/B (off vs telemetry, same 2-task plan, same model) — all 4 stamped evidence
digests re-derived MATCH from the commit trees, zero lane drift, 4/4 worker mandate compliance,
first ledger row appended (`calibration: true`, median-excluded, verified). Measured mechanical
overhead ≈ +1.9k tokens / ~+5 tool calls per checkpoint (n=1, toy-module scale — see the P0 report
in the session record + `.planning/telemetry-ledger.md` row 1). Kill-switch call: PROCEED to P1 —
break-even clears comfortably (cost ~1–3% extrapolated vs 5–10% payoff); the M4-L1 <1% green-run
cap is flagged AT-RISK at owned-module chunking and is re-measured on the P1 dogfooded build
(instrumented run #2, real module sizes); named remediation if it misses: coarsen the chunk unit
(checkpoint every N modules — the A1-Q2 `[TUNABLE]`), never a silent cap change.

## Open questions for the grill (before freeze)

> **RESOLVED 2026-07-04** — see *Grill resolutions (Amendment #1)* above. Retained verbatim below per
> supersede-never-rewrite.


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
