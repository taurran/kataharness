---
spec: inline-eval-m4
phase: M4-P2
title: research + debug signal adapters (same scheduler, two more signal sets)
status: frozen
revised: 2026-07-04 (v2 — gate v1 HOLD 3 HIGH/4 MED/1 LOW, all folded per the gate's own minimal amendments; re-gate v2 verified the folds; FROZEN)
created: 2026-07-04
branch: m4/inline-eval
baseline: fa21277 (P1 complete + L19-swept; pytest 2470/3, validator 48/0/0, Snyk medium+ 0)
tags: [kata/freeze-float, plan, inline-eval, M4-P2]
---

# M4-P2 — the research + debug adapters (M4-L6: one scheduler, three signal sets)

## Gate history
- **Freeze-gate v1 (2026-07-04): HOLD — 3 HIGH / 4 MED / 1 LOW, all folded (v2 = this text; the
  folds SHRINK the phase, per the anti-overcomplication mandate).** HIGH-1: the class tables had
  DROPPED the three universal hard signals (a missing checkpoint record on a research task would
  have scored GREEN — the exact A1-Q2 "never as green" violation; and the frozen P1
  every-hard-signal-triggers-every-class test would have broken) → every class table = the base
  hard trio ∪ class extras ∪ slack. HIGH-2: the three debug class signals had NO PRODUCER (the
  deviation-funnel schema carries no hypothesis records; the diagnose RUBRIC's hypothesis loop is
  in-session) → ABSENT-by-default in v1, weights DATA'd, the durable hypothesis-record emission a
  NAMED DEFERRAL (it is a new worker emission — it must arrive via its own gated amendment, never
  a silent claim). HIGH-3: the research grounding-REJECT source is gate-time + gitignored tier-3
  (fails M4-L9 durability at trigger time) and coverage_gap named a trailer field that does not
  exist → citation_fail = the research-class per-checkpoint VERIFY (the citation-integrity check
  IS the class verify, already in the trailer's verify.exit); coverage_gap + scope_drift
  ABSENT-by-default v1 (named deferrals; scope_drift additionally lacked a mechanical comparator —
  MED-7). MED-4: X2 explicitly owns the frozen scheduler call-line edit (a declared bounded touch,
  not a silent one). MED-5: the by-class weight/override plumbing contract pinned. MED-6:
  orchestrate 0.8.0 (MINOR — behavior-bearing; the P0/P1 precedent). LOW-8: present-but-MALFORMED
  class artifacts RAISE → treat-as-triggered (only ABSENT is the quiet leg).

ADAPTERS, not new sensors (M4-L6's own assessment): the scheduler, ladder, reroll, kill bindings,
and cursor machinery are P1's and are NOT touched except the ONE declared call-line edit (gate v1
MED-4). P2 adds (a) the per-class weight registry to `kata_risk` (base hard trio in EVERY class +
class extras DATA'd, A1-Q4 as amended by gate v1), (b) the class-adapter prose: per-class τ
leashes live NOW on the base trio + slack; the class EXTRAS are ABSENT-by-default with
NAMED-DEFERRED producers (gate v1 HIGH-2/HIGH-3 — the originally claimed sources did not exist in
the claimed shapes), (c) the class-detection source (`class:` task frontmatter, default `code`,
never `runShape`) + the P1-deferred `area:`-guard line in the kata-plan RUBRIC. The A1-Q5(5)
double-ladder precedence ALREADY shipped in P1's arbitration paragraph — P2 adds nothing to it.

## Ownership (disjoint) + DAG

```yaml
ownership:
  X1: [tools/kata_risk.py, tools/tests/test_kata_risk.py]
  X2: [skills/coordinate/kata-orchestrate/SKILL.md, skills/plan/kata-plan/RUBRIC.md]
waves:
  wave1: [X1]
  wave2: [X2]
depends_on:
  X2: [X1]
tasks:
  X1: { estimate: 25, modules: 2, class: code }
  X2: { estimate: 20, modules: 2, class: code }
```

X3 (conductor closeout): telemetry harvest (instrumented run #3 rows fold into the ledger at the
milestone closeout row), CHANGELOG, DESIGN P2 status note, D144. No new skill; orchestrate
0.8.0 (MINOR, gate v1 MED-6) + kata-plan tier PATCHes (0.1.1 → 0.1.2 — the D140/F7 rule).

## X1 — `kata_risk` class tables (code; TDD + mutation proofs)

1. **`DEFAULT_WEIGHTS_BY_CLASS`** replaces the single `DEFAULT_WEIGHTS` as the registry (the old
   name stays as an alias for the code table — **BY REFERENCE: `DEFAULT_WEIGHTS =
   DEFAULT_WEIGHTS_BY_CLASS["code"]`, the same object, never a copy (re-gate v2 F2 — a copy
   silently diverges under [TUNABLE] calibration edits), pinned by an `is`-identity test**;
   additive BC; the P1 tests keep passing unmodified).
   **Every class table carries the UNIVERSAL base hard trio (gate v1 HIGH-1 — A1-Q2/A1-Q4's
   unscoped hard signals: a missing record or lane drift is never green in ANY class):**
   - `code` (unchanged, P1): verify_fail .60, lane_drift .60, missing_record .60, slack_ge_2x .30
   - `research`: verify_fail .60 (**the research-class per-checkpoint verify IS the
     citation-integrity check — gate v1 HIGH-3; no separate citation_fail key**), lane_drift .60,
     missing_record .60, coverage_gap .25, scope_drift .25, slack_ge_2x .30
   - `debug`: verify_fail .60, lane_drift .60, missing_record .60, hypothesis_cycles_3plus .60,
     repro_regression .60, same_hypothesis_reentry .30, slack_ge_2x .30
   **Producer honesty (gate v1 HIGH-2/HIGH-3/MED-7):** the class EXTRAS (coverage_gap, scope_drift,
   hypothesis_cycles_3plus, repro_regression, same_hypothesis_reentry) are **ABSENT-by-default in
   v1 — weights DATA'd, no producer exists**: the durable per-hypothesis diagnose record and the
   brief-pinned scope/coverage comparators are NAMED DEFERRALS (each is a new worker emission or a
   new mechanical comparator that must arrive via its own gated amendment — never a silent claim,
   never an LLM judgment pre-trigger, M4-L3). What P2 SHIPS live: per-class τ leashes (0.45 vs
   0.50) + the base trio + slack on research/debug tasks + the class-signal plumbing awaiting
   producers.
2. **Signal derivation:** `should_trigger` gains an optional `class_signals: dict | None` kwarg
   (research: `coverage_gap: bool`, `scope_drift: bool`; debug: `hypothesis_cycles: int` — the
   tool derives `hypothesis_cycles_3plus` from `>= 3` internally, the LOW-11 pattern;
   `repro_regression: bool`, `same_hypothesis_reentry: bool`). `None`/missing keys ⇒ absent ⇒ 0
   (trigger-shy fail-safe); an unknown key RAISES (producer bug); a class-signal key supplied for
   the WRONG class RAISES (cross-class contamination is a producer bug, loud).
   **By-class plumbing contract (gate v1 MED-5; re-gate v2 F1/F3):** `should_trigger` treats the
   passed `weights` as an **OVERRIDE MAP overlaid on `DEFAULT_WEIGHTS_BY_CLASS[task_class]`,
   filtered to that class's vocabulary** — NOT a replacement table (the P1 boundary tests pass
   unchanged: they supply full code-vocabulary maps, and overlay-of-a-full-map ≡ replacement for
   them); `resolve_inline_eval_params` keeps its P1-flat return shape (the pinned tests stand) and
   validates weight-override KEYS against the UNION of all class vocabularies; an override applies
   to a class iff that class's table carries the key — **union-valid keys are DELIBERATELY inert
   for classes whose table lacks them (documented in both docstrings + D144, never read as a
   bug).** Integration test (F1): a resolver override of a research extra changes a research
   trigger outcome AND is inert for code.
3. **A1-Q4 arithmetic pins (tests):** research soft PAIR crosses (0.25+0.25 = 0.50 > 0.45 STRICT);
   debug re-entry+slack pair crosses (0.30+0.30 = 0.60 > 0.45); every hard signal alone crosses
   every τ; no lone soft signal crosses any τ; **the LOW-13 debug cold-start caveat PINNED as a
   test**: debug with slack ABSENT cannot soft-trigger (0.30 alone < 0.45 — hard signals only).
4. **Mutation proofs (≥3):** the cross-class-contamination guard; the `>= 3` hypothesis-cycles
   derivation boundary (mutate to `> 3` → the cycles==3 test RED); one research-pair arithmetic pin
   (mutate coverage_gap weight to 0.15 → the pair test RED). Plus the P1 base-trio test
   (`every hard signal alone triggers every class`) must pass UNMODIFIED against the new registry
   (gate v1 HIGH-1 — the six research/debug base cells are the regression canary).
5. Pure module invariants unchanged (no subprocess; structural test already pins it).

## X2 — signal wiring + RUBRIC (prose)

1. **kata-orchestrate 0.7.0 → 0.8.0 (gate v1 MED-6 — behavior-bearing ⇒ MINOR, the P0/P1
   precedent) — an "M4-L6 class adapters" subsection under the scheduler, PLUS one DECLARED
   bounded edit to the frozen scheduler text (gate v1 MED-4):** the per-new-checkpoint
   `should_trigger` call line gains `class_signals=<class-signal dict or None>` and the
   `task_class=<class>` placeholder is defined: **class detection = the task's plan-frontmatter
   `class:` (default `code`; never `runShape` — provenance-only, LOW-14b).** Signal sources:
   - **research:** the class per-checkpoint VERIFY is the citation-integrity check (its exit rides
     the trailer's `verify.exit` — the existing verify_fail signal; gate v1 HIGH-3). Grounding-gate
     REJECT verdicts and coverage remain GATE-TIME inputs (telemetry/calibration), not trigger
     inputs — `.kata/grounding.json` is gate-time, gitignored tier-3, and has no chunk mapping.
     `coverage_gap`/`scope_drift`: ABSENT in v1 (named deferrals — no mechanical comparator/
     producer exists; a future brief-pinned scope-list comparator arrives via its own amendment).
   - **debug:** `hypothesis_cycles`/`repro_regression`/`same_hypothesis_reentry`: ABSENT in v1
     (named deferral — the diagnose discipline emits no durable per-hypothesis records today;
     adding that emission is a gated future amendment). Debug tasks trigger on the base trio +
     slack, at the shorter 0.45 leash.
   Scheduler passes `class_signals` per the X1 contract; **ABSENT artifacts ⇒ absent signals ⇒ 0**
   (trigger-shy, documented); **present-but-MALFORMED class artifacts RAISE → treat-as-triggered +
   surface** (gate v1 LOW-8 — the A1-Q2/D136 posture; only absence is quiet).
2. **kata-plan RUBRIC (+ tier PATCH bumps 0.1.1 → 0.1.2):** the per-task `class:` field
   (`code | research | debug`, default `code`, validated at freeze — unknown value FAILS freeze)
   + the P1-deferred guard line: **plan task ids MUST NOT begin `area:`** (fails freeze).

## Acceptance

1. Full gauntlet: suite grown from 2470; validator 48/0/0 (bumps in sync); Snyk 0 on kata_risk;
   ≥3 mutation proofs listed in D144.
2. A1-Q4 research/debug arithmetic + the LOW-13 caveat test-pinned; P1 code-class tests pass
   UNMODIFIED (the alias BC pin).
3. Prose: signal sources name only EXISTING artifacts (the sweep's no-new-sensors check); class
   detection never reads `runShape`; the RUBRIC guard + class field land with tier PATCHes.
4. X1 built dogfooded with the checkpoint mandate (instrumented); X2 prose likewise.

## Out of scope

Live research/debug-class runs (the live proof is code-class; research/debug adapters ship
protocol-conformant + arithmetic-pinned — their live proof rides future real runs, stated
honestly); slack per-attempt re-scoping (the P1 L19-sweep LOW-8 named caveat — backlog); learned scorers (M4.1).
