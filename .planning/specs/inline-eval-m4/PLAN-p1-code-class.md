---
spec: inline-eval-m4
phase: M4-P1
title: the code-class mechanism — risk score, inline evaluator, ladder, reroll (detection acts)
status: frozen
created: 2026-07-04
revised: 2026-07-04 (v3 — gate v1 HOLD folded; re-gate v2 SHIP-WITH-FIXES 1 HIGH/3 MED/3 LOW, all folded; FROZEN)
branch: m4/inline-eval
baseline: 9bbf830 (P0+P0.1 complete + eval-closed; pytest 2396/3, validator 47/0/0, Snyk medium+ 0)
tags: [kata/freeze-float, plan, inline-eval, M4-P1]
---

# M4-P1 — the code-class mechanism (`inlineEval: on` becomes real)

## Gate history
- **Re-gate v2 (2026-07-04): SHIP-WITH-FIXES — FROZEN after fold.** 13/13 v1 folds verified
  landed. Fresh catches on the fold text, all folded: **v2-HIGH-1** an object-form `inlineEval`
  with `mode` MISSING silently coerced to `"off"` through `validate_inline_eval(None)`'s BC leg
  (the hand-edit error the load-guard exists for) → `mode` key REQUIRED on object form, STOP on
  absence, at BOTH the W1 function and the W3 call site; **v2-MED-2** the W1/W3 cross-wave
  argument contract was stated two ways (whole-config vs value object — the mismatch would have
  silently ignored every override via the absent-block quiet path) → pinned: the VALUE object;
  **v2-MED-3** the treat-as-triggered raise path could not produce the pinned DECISION line (no
  score/sha) → `@<sha|SCAN-ERR> score ERR` shape, counts ONCE per scan window; **v2-MED-4** the
  slack-only-on-newest rule was recovery-scoped while normal batch scans have the same geometry
  (P2 soft pairs would manufacture triggers) → ONE batch rule, normal + recovery, plus the
  batch-stops-at-first-kill-verdict short-circuit; **v2-LOW-5** `continue` explicitly writes its
  ladder DECISION (else recovery re-triggers cleared work); **v2-LOW-6** task ids must not begin
  `area:`; **v2-LOW-7** degrade decidability wording. Clean under fresh attack: run-start
  pre-resolution decidability, recovery-recount arithmetic, W3 numbering, W1 test list, R5
  forcing, the `never OMIT-inherit` grep pin, ownership/versions.
- **Freeze-gate v1 (2026-07-04): HOLD — 4 HIGH / 4 MED / 5 LOW, all folded (v2 = this text).**
  HIGH-1 the boundary-comparator test spec contradicted its own strict-`>` pin (a builder would
  have shipped `>=` — drift on the function that fires kills); HIGH-2 the resolver-`None` leg of
  the never-anchor invariant was missing from the IMPLEMENTING text (the OMIT path would have run
  the inline eval AT ANCHOR on the BC-default config — the third resurfacing of this defect class,
  caught again) → both never-anchor failure points now carved out at trigger #1 incl. run-start
  pre-resolution; HIGH-3 the scheduler cursor was unrecoverable after compaction (no sha in the
  ladder DECISION; happy path writes none) → sha in the line + the recovery rule (adjudicated shas
  never re-trigger; slack live only on the newest unadjudicated checkpoint); HIGH-4 the
  `{taskId|area}` widening silently null-attributed per-area entries through the as-built producer
  → the `area:<name>`-in-taskId convention (zero code). MED: per-PLATFORM kill-binding degrade
  (was per-run — contradicted M4-L9c and W4's own text); active-attempt-branch redefinition landed
  at the consuming loop steps 3/4/5; the precondition-0 object-form edit named (it would have
  fail-closed EVERY object config at load); the D140 frozen-pre-P1-text pin for the instrumented
  build. LOW: exec-safety.md dropped from W1 (no specified edit); W2 validator-required frontmatter
  keys named incl. the spine-tag choice; the slack_ge_2x/slack_ratio key mapping pinned; the L19
  re-sweep bounded (≤2 then operator valve); the general-vs-contract supersede route ordering.
  Clean surfaces verified by the gate: ladder anchor semantics, grounding-before-reroll#2,
  escalation kinds unextended, kill discipline, A1-Q5 arbitration, R5 registration forcing,
  ownership/DAG, versions, no overcomplication found.

Implements the FROZEN DESIGN's action half for the CODE class: M4-L4 (one-dial risk score),
M4-L5 (the ladder incl. the grounding-pass rung), M4-L2 as amended (reroll = kill + fresh dispatch
from an anchor commit on a NEW attempt branch; kill confirmed-dead; kill-failure ⇒
`human-required`), M4-L7 as amended (inline evaluator strictly below anchor via the D131 resolver;
degrade-to-telemetry on resolver-`None` AND on R2-chain exhaustion), A1-Q1/A1-Q4/A1-Q5 verbatim.
BC unchanged: `inlineEval` absent ⇒ `off`; `telemetry` mode gains NO new behavior from P1 (records
only — the P0 posture); ONLY `on` activates the scheduler/ladder. The final gate, kata-evaluate,
and the adversarial sweep are untouched as gates (M4-L8).

**Build mode: dogfooded + INSTRUMENTED (instrumented run #2).** Workers build in worktrees on task
branches forked from `m4/inline-eval` with the P0 checkpoint mandate active (`telemetry`-mode
mechanics — P1's own scheduler is not yet built while P1 builds); the conductor runs the per-task
telemetry steps and appends **ledger row #2 (real, `calibration: false`)** at closeout — this is
the real-module-size re-measurement of the AT-RISK <1% cap (P0 report flag). **The P1 build run
executes the FROZEN PRE-P1 orchestrate 0.6.1 text at `inlineEval: telemetry` END-TO-END,
including W5 closeout (the D140 "run executes the frozen PRE-P2 skill text" precedent — gate v1
MED-8); orchestrate 0.7.0 first executes in a post-merge run.** Build workers tier
down per D131; gates at anchor.

## Ownership (disjoint) + DAG

```yaml
ownership:
  W1: [tools/kata_risk.py, tools/tests/test_kata_risk.py]
  W2: [skills/evaluate/kata-inline-eval/SKILL.md, tools/kata_models.py, tools/tests/test_kata_models.py]
  W3: [skills/coordinate/kata-orchestrate/SKILL.md, protocol/config.md]
  W4: [adapters/ADAPTER-CONTRACT-M4.md, skills/execute/kata-tdd/SKILL.md]
waves:
  wave1: [W1, W2]
  wave2: [W3, W4]
depends_on:
  W3: [W1, W2]
  W4: [W1]
tasks:
  W1: { estimate: 45, modules: 3, class: code }
  W2: { estimate: 30, modules: 2, class: code }
  W3: { estimate: 40, modules: 3, class: code }
  W4: { estimate: 20, modules: 2, class: code }
```

W5 (conductor closeout): per-task telemetry + gate + integration per task; ledger row #2
(`calibration: false`, real run) with the D141(b) board-`DECISION` approval; CHANGELOG; README
regen; D143; DESIGN P1 status note; the <1% re-measurement verdict in the P1 report.

## W1 — `tools/kata_risk.py` (code; TDD + mutation proofs; stdlib-only; imports kata_telemetry only)

The one-dial score (M4-L4) + trigger decision as pure, fail-closed decision code (D136 — this
DRIVES decisions, unlike telemetry):
1. **Defaults as DATA:** `DEFAULT_WEIGHTS` (code class per A1-Q4: verify_fail 0.60, lane_drift
   0.60, missing_record 0.60, slack_ge_2x 0.30) and `DEFAULT_TAU = {"code": 0.50, "research":
   0.45, "debug": 0.45}` — module constants, `[TUNABLE]`-commented, research/debug weights DATA'd
   now (A1-Q4) but only `code` is consumed in P1 (P2 wires the adapters; no dead code paths — the
   score function is class-parametric already).
2. **`risk_score(signals: dict, weights: dict) -> float`** — capped sum `min(1.0, Σ active)`;
   `signals` = `{verify_fail: bool, lane_drift: bool, missing_record: bool, slack_ratio:
   float|None}` (the score derives the weighted `slack_ge_2x` term INTERNALLY from `slack_ratio ≥ 2.0` —
   `slack_ratio` is an input field, never an "unknown key", gate v1 LOW-11; `None` ⇒ absent ⇒ 0). An
   unknown signal key in `signals` RAISES (a signal the weights don't know is a producer bug —
   loud, never silently ignored); a MISSING key ⇒ that signal absent (0) — the documented
   trigger-shy fail-safe for absent signals, D136-exempt as designed.
3. **`should_trigger(record_or_none, lane_drift, slack_ratio, *, task_class, weights=None,
   tau=None) -> dict`** — the decision function: builds the signal vector from a parsed
   `Kata-Checkpoint` record (`None` record on a checkpoint commit under mode `on` ⇒
   `missing_record: True` — the A1-Q2 hard signal), computes the score, returns
   `{triggered: bool, score: float, signals: {...}, tau: float}` (the full vector — feeds
   telemetry + the ladder DECISION line). Unknown `task_class` RAISES (never a default leash).
4. **Config overrides:** `resolve_inline_eval_params(value) -> {weights, tau}` — **the argument
   is the `inlineEval` VALUE itself (string or dict), NEVER the whole kata.config** (re-gate v2
   MED-2 — the W1/W3 cross-wave contract pinned: passing the whole config would hit the
   absent-block quiet path and silently ignore every override). String value ⇒ defaults; `None`
   (field absent) ⇒ defaults; dict value: **the `mode` key is REQUIRED — a mode-less object
   RAISES** (re-gate v2 HIGH-1: `validate_inline_eval(None)`'s BC leg exists for an ABSENT FIELD,
   not a present-but-mode-less object — the classic hand-edit error must STOP, never silently
   run `off`); optional sub-fields `tau: {class: float}` / `weights: {signal: float}`; a
   present-but-malformed value (non-numeric, unknown class key, unknown signal key, τ outside
   (0,1]) RAISES — load-guard STOP material (GB12/D45; same posture as `validate_inline_eval`).
   Named tests: mode-less-object raise; whole-config-passed-by-mistake raise (a dict with an
   `inlineEval` key is not a valid value object — unknown-key raise covers it).
5. **Exec-safety:** kata_risk spawns NO subprocess (pure) — state it in the module docstring and
   pin it structurally (test: no `subprocess` import). NO exec-safety registry row and NO edit to
   `protocol/exec-safety.md` (gate v1 LOW-9 — the file left W1's ownership; owning a file with no
   specified edit invites an invented one).
**Tests/proofs:** the A1-Q4 arithmetic PINNED as tests (every hard signal alone ≥ every τ; no lone
soft signal ≥ any τ; code-class slack-alone never triggers; boundary: **`score == τ` does NOT trigger** — pins the strict `>` comparator per M4-L4 verbatim
"score > τ_class ⇒ trigger"; mutating `>` to `>=` turns this named boundary test RED);
unknown-key/class raises; None-slack absent; capped sum at 1.0. Mutation proofs (≥4): the
unknown-signal guard, unknown-class guard, malformed-override guard, and the `> tau` comparator
(mutate to `>=` → the boundary test goes RED).

## W2 — `skills/evaluate/kata-inline-eval/SKILL.md` (NEW skill) + D131 registration (code+prose)

1. **The skill** (frontmatter mirrors kata-evaluate — validator-REQUIRED keys named, gate v1
   LOW-10: `license: Apache-2.0`, `status: experimental`, `cost-weight: 1`, category `evaluate`,
   version 0.1.0, tags `[kata/evaluate, kata/spine, inline-eval, no-write, M4]` (spine: it is the
   M4 detection leg of the quality loop), `allowed-tools: [Read, Grep, Glob, Bash]`,
   no Write/Edit — fresh-context, NO-WRITE, like kata-evaluate; `agnostic: true`): input = the
   chunk diff (`git show <sha>`), the task brief, the signal record + score vector; verdict =
   exactly one of `continue` (false alarm — say why, feeds calibration) | `correct` (the chunk
   stands; emit a corrective NOTE ≤ 10 lines for the redispatch brief) | `reroll` (the chunk is
   defective; name the defect + the last good checkpoint index). Verdict rules mirror
   kata-evaluate's evidence discipline: cite the diff, never trust the worker's message; the
   OUTPUT is machine-parseable (`VERDICT: <continue|correct|reroll>` first line). It never edits,
   never re-plans, never sees other tasks (scoped context = economy cost).
2. **D131 registration:** `kata_models.SKILL_WORK_CLASS["kata-inline-eval"] = "economy"` (M4-L7
   as amended; the R5 coverage test derives the skill set dynamically and will FAIL until
   registered — registration is forced). Add the M4-L7 pin test: for every (mode, family) cell,
   `resolve("kata-inline-eval", ...)` returns either an id strictly below the anchor rung or
   `None` — NEVER the anchor id (the zero-step contract already guarantees this structurally;
   pin it against regression anyway — one test, parametrized).
**Proofs:** validator 48 skills / 0 / 0 (count grows); the pin test mutation-proven (flip the
step table's advanced-economy to 0 for anthropic → the pin test still passes via `None`… choose a
mutation that matters: hardcode `resolve` to return the anchor id for the skill → RED).

## W3 — kata-orchestrate 0.6.1 → 0.7.0 + config.md (the scheduler + the ladder; prose)

1. **config.md:** `inlineEval` row v2 — the field becomes an OBJECT-or-string: the P0 string form
   stays valid (`"off"|"telemetry"|"on"`); the object form `{mode, tau?, weights?}` adds the
   A1-Q4 overrides (validated by `kata_risk.resolve_inline_eval_params` + `validate_inline_eval`
   on `mode`; malformed ⇒ load-guard STOP). Flip the `on` row cell from "not-yet-consumed" to
   live, pointing at the orchestrate scheduler section.
2. **Precondition-0 load-guard edit (gate v1 MED-7 — the call site that actually runs):** string
   form ⇒ `validate_inline_eval` exactly as today; OBJECT form ⇒ **`'mode' in value` REQUIRED —
   missing ⇒ STOP + escalate (re-gate v2 HIGH-1; never `validate_inline_eval(None)`'s silent
   `"off"`)** — then `validate_inline_eval(value['mode'])` + `kata_risk.resolve_inline_eval_params
   (value)` (the VALUE object, MED-2) — any raise ⇒ STOP + escalate (GB12/D45).
3. **The scheduler (new subsection under the loop, ADDITIVE; fires IFF effective mode == `on`):**
   at every liveness-monitor pass AND at each worker `DONE`, scan the task's ACTIVE attempt
   branch for NEW checkpoint commits (`kata_telemetry.scan_checkpoints`, cursor = last seen sha
   per task, in-context bookkeeping like the thrash counters — DECISION lines are the recount
   trail); per new checkpoint compute drift + slack (the P0 steps) then
   `kata_risk.should_trigger(...)`. `triggered: false` ⇒ record to telemetry, done (the happy
   path costs zero LLM calls — M4-L1). A `should_trigger`/`scan` RAISE under mode `on` ⇒
   **treat-as-triggered + surface** (the A1-Q2 documented fail-safe — P1 flips the P0
   record-only response for mode `on`; `telemetry` mode keeps the P0 never-blocks posture).
   **Raise-path DECISION shape (re-gate v2 MED-3):** a raise has no score and possibly no sha —
   its ladder line is `ladder: <task> trigger <n> @<sha|SCAN-ERR> score ERR verdict <v>`; a
   `SCAN-ERR` adjudication covers THAT SCAN WINDOW and counts ONCE on the ladder (a persistent
   git error must not re-fire per conductor restart into an unbounded loop — the ≤3 ladder bound
   applies to raise-triggers exactly as to scored ones).
4. **The ladder (M4-L5/A1-Q1/A1-Q5 verbatim — reuse, don't invent):** per-task trigger count is
   in-context bookkeeping + a board `DECISION` line per ladder event — **the line CARRIES the
   checkpoint sha** (`ladder: <task> trigger <n> @<sha> score <s> verdict <v>` — the L2/L3 pattern;
   no new board TYPE, no new escalation kind). **Cursor recovery rule (gate v1 HIGH-3):** the
   happy-path cursor (last-seen sha per task) is in-context only; on conductor
   compaction/restart, adjudicated checkpoint shas recount from the ladder `DECISION` lines and
   are NEVER re-triggered. **Batch rule (re-gate v2 MED-4 — normal AND recovery scans, one rule):**
   in ANY scan batch, the slack term is live ONLY on the NEWEST unadjudicated checkpoint
   (elapsed-vs-now grows monotonically — scoring history against `now` manufactures triggers on
   accepted work; at P2's soft-pair classes this would walk the ladder on a healthy-but-slow
   worker), and **a batch STOPS at the first `reroll`/`correct` verdict** (the remaining
   checkpoints belong to the killed attempt's abandoned suffix).
   - **Trigger #1 ⇒ inline eval:** dispatch [[kata-inline-eval]] fresh-context no-write at the
     D131-resolved tier. **BOTH "never anchor" failure points are carved out (gate v1 HIGH-2 —
     the OMIT path must be unreachable for this slot):** (i) **pre-resolve at run start under
     mode `on`** — `resolve("kata-inline-eval", ...)` returning `None` (absent `models` block,
     unknown family/anchor, zero-step/floor-clamped cell) ⇒ SKIP every eval + degrade the RUN to
     `telemetry`, surfaced AT RUN START; (ii) at dispatch failure — R2 chain exhaustion or a
     `fallback_chain` of `[None]` ⇒ same skip + degrade route. In both cases: board NOTE + a
     `degraded` ledger entry; **the inline evaluator NEVER dispatches via the OMIT/inherit path
     and never at the anchor** (never OMIT-inherit). Context: chunk diff + task
     brief + signal vector ONLY. Verdicts: `continue` ⇒ **ladder `DECISION` line (verdict continue — its sha must adjudicate
     or recovery re-triggers cleared work, re-gate v2 LOW-5)** + calibration log; `correct` ⇒ kill
     (confirmed-dead; failure ⇒ `human-required`) + fresh dispatch from the CURRENT checkpoint on
     attempt branch `<task>-attempt<n>` with the corrective NOTE in the brief; `reroll` ⇒ same
     primitive anchored at the LAST GOOD checkpoint (last below-τ, else dispatch base).
     Worktree remove+prune before the fresh worktree (the abort route); the reroll DECISION line
     names the new attempt branch (the scheduler polls ONLY the active one).
   - **Trigger #2 (same task) ⇒ GROUNDING PASS before any second reroll:** YOU (plan-guardian)
     re-anchor the task against the FROZEN plan — is the SPEC the defect? Output = a tightened
     task brief (within plan bounds, board `DECISION`), then reroll #2. Plan-defect finding ⇒ the EXISTING general supersede path (deliberate,
     audited re-plan via `human-required` where LOCKED text is touched — gate v1 LOW-13); the
     contract-surface supersede route applies ONLY when the plan declares `builds_against` and a
     contract surface changes. Never a silent plan patch.
   - **Trigger #3 ⇒ `human-required`** (existing kind, no enum change; async-parked per the
     existing contract). Ladder arbitration = A1-Q5 verbatim (absence-of-signal → liveness only;
     present-bad-evidence → M4 only; an open escalation/park suspends the ladder; ladder history
     never spends the thrash budget and vice versa — restate the ONE paragraph, cite A1-Q5).
   - **failureKinds widening (P0.1 deferral discharged; gate v1 HIGH-4 — zero-code convention):**
     ladder events + final-gate fix-loop areas enter `failureKinds` with the **`taskId` field
     carrying `area:<name>` for per-area entries** (the as-built `_validate_failure_kinds` passes
     `taskId` through verbatim — no producer change, no attribution loss to `null`);
     orchestrator-classified (D33). Document the `area:` prefix convention in the ledger header
     (W5) and the closeout block text — **and the guard: plan task ids MUST NOT begin `area:`**
     (re-gate v2 LOW-6; one line in the kata-plan RUBRIC authoring rules is P2-deferred — for P1
     the convention doc carries it; no task id in this plan or any existing plan collides).
   - **Active-attempt-branch redefinition landed at the CONSUMING steps (gate v1 MED-6, v2-LOW-7):**
     W3 explicitly edits loop step 3 (the lane check's `changed_in_task(integration_ref,
     task_ref)`), step 4 (integrate), and step 5 (checkpoint commit) so "the task branch" reads
     **"the ACTIVE attempt branch after any reroll"** at each site — not only in the telemetry
     substep.
5. **Kill bindings (M4-L2 as amended):** name them where the ladder uses them — Claude host =
   background-task stop on the dispatched worker; LD6 off-host = OS process kill; **no binding ⇒
   THAT PLATFORM degrades to `telemetry` (per-platform, M4-L9c — gate v1 MED-5; a mixed run keeps
   `on` where the primitive exists), recorded as each task's effective mode (the M4-L10
   taxonomy), surfaced at run start** (decidable at run start — the platform set is known at
   precondition 0; a kill FAILURE at reroll time ⇒ `human-required`, never
   proceed-and-redispatch).
6. Version 0.7.0 (behavior addition); renumber/re-anchor discipline on any step cross-refs.

## W4 — `adapters/ADAPTER-CONTRACT-M4.md` (NEW) + kata-tdd 0.2.0 → 0.2.1 (prose)

1. **The adapter contract (M4-L9 normative, one page):** an adapter supporting `inlineEval: on`
   MUST provide (a) worker append access to the shared board at the integration root (S3b);
   (b) session kill + fresh-dispatch (confirmed-dead semantics); absent either ⇒ the platform
   runs M4 at `telemetry` — surfaced, never silent, recorded as a `degraded` ledger entry. Every
   M4 signal is a durable artifact (trailer, board line, DECISION); the scheduler POLLS at
   checkpoint granularity; no feature may require streaming, mid-session injection, or shared
   session memory. Cross-model: LD6 workers are identical (subprocess kill = the primitive);
   tier resolution ONLY via the D131 resolver + the R2 carve-out. Reference: DESIGN M4-L2/L7/L9.
2. **kata-tdd 0.2.1:** one paragraph under the checkpoint-cadence section: under mode `on`, a
   session may be killed+re-dispatched at a checkpoint boundary (reroll/correct); the fresh brief
   carries a corrective NOTE when verdict was `correct` — treat it as task context, not a
   re-plan; the cadence mechanics are UNCHANGED from telemetry mode (workers never see the
   scheduler).

## Acceptance (falsifiable)

1. Full gauntlet: suite grown from 2396 (W1+W2 tests), validator **48**/0/0 (new skill), Snyk
   medium+ 0 on new/changed tools; every decision guard mutation-proven (≥5 listed in D143).
2. A1-Q4 arithmetic test-pinned incl. the `> tau` boundary comparator.
3. M4-L7 pin: `kata-inline-eval` never resolves to the anchor id (test); R2 carve-out prose
   present in the ladder text (grep-able: "never OMIT-inherit").
4. BC: string-form `inlineEval` configs (incl. absent) parse unchanged (test); `telemetry` mode
   behavior byte-identical to P0 (no scheduler text fires below `on` — prose + the config test).
5. Instrumented run #2: ledger row #2 appended (`calibration: false`, board-`DECISION` approval),
   with per-checkpoint records from the P1 build's own workers; the P1 report states the measured
   real-module overhead vs the <1% cap and the remediation decision if it misses (coarsen chunk
   unit — named in the P0 report; never a silent cap change).
6. L19 integrated cross-seam adversarial sweep over the WHOLE M4 body (P0+P0.1+P1) before the
   merge gate — reviewer prompt names the adjacent seams (board, fix loop, liveness, escalation
   kinds, D131 resolver, LD6/LD7, the M1 contract final-gate step). SHIP required (HOLD ⇒ fold ⇒
   re-sweep, **≤2 re-sweeps then the operator valve** — gate v1 LOW-12; every loop carries a bound).

## Out of scope (P2+)

Research/debug signal adapters (P2 — the score function is already class-parametric; P2 adds
signal WIRING, not scoring changes); automatic tier mutation (M4-L7 report-and-recommend only);
gate-time evidence re-validation (deferred, flagged in A1-Q2); ACP live proof (protocol
conformance only — the Quick adapter milestone owns the live leg).
