# HANDOFF — Advisor-Executor feature (transfer record)

> **Purpose:** a detailed, self-contained record of *how* the Fable-tier Advisor feature was
> designed and built through the full Kata Loop, written so the approach can be reproduced in a
> sibling loop project. Maintained LIVE through the run — each phase appends its section as it
> completes. Neutral naming by policy; no external project linkage on this surface.

**Status:** IN PROGRESS — initiation complete, grill starting.
**Run date:** 2026-07-19 · **Anchor:** Fable 5 session · **Mode:** standard · one-shot · target `self`.

---

## 0. The pattern being adopted (source concept)

The **advisor-executor pattern** (public reference: mindstudio.ai blog, "Advisor-Executor Pattern
with Claude Code + Fable 5"): a premium model (Fable 5) does *scoped thinking* — planning,
targeted review, unblocking advice — while a cheaper executor (Opus/Sonnet) does the bulk work.
Key mechanics from the source, adapted here:
- Advisor produces **structured output only** (never executes); executor **flags, never improvises
  strategy** when stuck.
- Phase 3 of the pattern — "re-advise": a *short, targeted* premium session on an exception,
  instead of full re-planning. This maps directly onto our evaluation-failure hook.
- Token economics: 5–15% advisor / 85–95% executor; premium quota preserved.
- Known failure modes: blurred roles (advisor starts executing), vague prose plans, executor
  improvising. Our design must structurally prevent all three.

## 1. Where the harness already was (grounding assessment, 2026-07-19)

A fresh-context research agent assessed current premium-model routing before any design work.
Full detail lives in the DESIGN's assessment section; the load-bearing facts:

- **Model routing is anchor-relative** (D59/D131): work classes critical/coding/economy ×
  mode step-down table; zero-step cells inherit by OMISSION (never re-select the anchor id);
  no `model:` frontmatter anywhere (validator hard-fails it).
- **Fable-anchored session:** critical work (grill/plan/evaluate/review/orchestrate) runs at
  Fable in standard AND advanced; coding at −1 (Opus) on standard; economy −2. A preflight
  cost-confirm exists (decline ⇒ pin anchor to opus).
- **Opus-anchored session:** Fable is reachable ONLY via the D148 premium offer — advanced mode
  only, preflight-approved, critical+coding classes, exact-one-rung-above, budget-capped
  (adaptive events form, default 10 calls, 2 reserved), loud lapse-on-failure (CA-L30).
- **No advisor mechanism existed.** `kata-reason` (the CONSULT decider) = named but deferred.
- **Three engineered attachment points** for a "consult after N failures" hook:
  1. `kata_adaptive.bump_pending` — codified fail counter, fires at `failBumpAt: 2`.
  2. The fix-loop thrash valve — already dispatches `kata-diagnose` at the failure ceiling.
  3. The `ADAPTIVE_EVENTS` registry — events-form premium scope; every event must cite a real
     covering dispatch site (MED-12).
- **Constraints inherited:** D136 fail-closed decision code · D33 never-tiered invariants ·
  PD-1/PD-2 · premium four-conjunct gate shape · R2 OMIT-terminus fallback.

## 2. Process log (how each phase was run)

### 2.1 INITIATION (kata-initiate) — DONE 2026-07-19
- Phase 0: Prime Directives loaded; `kata-readiness` PASS (validator 48/0/0, clean tree,
  tree-sitter OK). 2 WARNs: stale `engram.learnFeed.dir` (old vault path gone — fixed by
  config regen at composition); `confirmedPlatforms` empty (single-host run).
- Phase 1b: recall brief via `recall.recall_from_paths` — 0 open recurrences; 282 records;
  top hits D148/D131/D59/D150/D143/D153 (exactly the contract surface being touched).
- Phase 2: reflective goal mirror presented; all 9 load-bearing values individually named;
  operator confirmed as mirrored (incl. 8 acceptance criteria + standard grill depth).
- Phase 4: draft INTENT.md written via `intent_scaffold.write_intent` (sole writer).
- Grounding ran in PARALLEL with initiation (background research agent) — zero wall-clock cost.

### 2.2 GRILL (kata-grill-standard) — DONE 2026-07-19
- **Shape:** 7 operator questions (one at a time, recommendation-first, free-text escape) + 6
  self-resolved structural entries + 4 fresh-context convergence passes.
- **Operator decisions:** G-1 naming (new feature owns "Advisor"; kata-reason re-titled) · G-2
  narrow D148 carve-out (standard opt-in unlocks advisor-class premium) · G-3 advise-first/
  bump-second ordering · G-4 cross-phase matrix (gate NEVER consults — judge independence) ·
  G-5 once-per-RUN opt-in at preflight · G-6 mode-scaled own budget pool (5/1, 10/2) · G-7
  machine-ingestible payload, agent-consumed, after-action rollup to the human (operator rider
  mid-grill) · G-8 essential excluded · G-9 two-moment grant model (advanced consents at
  bootstrap ⇒ planning consults legal; standard at preflight).
- **Convergence journey (the load-bearing part):** HOLD(8) → HOLD(3) → HOLD(3) → HOLD(2) →
  SHIP. Each pass was a FRESH reviewer with no stake. Headline catches: the grant-timing
  paradox (planning happens pre-freeze but grants lived post-freeze — became G-9); budget
  dual-accounting (resolved by fully DECOUPLING advisor legality from models.premium — S-16,
  which SIMPLIFIED the design); the fable-target-vs-one-rung-above contradiction the code
  proved (S-24: sonnet anchors consult fable, not opus); a stale glossary clause that would
  have rebuilt the dismantled coupling (S-22/S-26a).
- **ELEVATE (D153):** EV-1 accepted — advice-effectiveness telemetry pairing (advised→pass /
  advised→fail→bumped / advised→fail→ceiling), making advisor ROI an evidence question.
- **Emit:** learn_feed wrote 40 pages to the second brain (167 skipped-identical, 0 redactions).
- **Technique note (transferable):** the reviewer sequence converged because each HOLD's
  resolutions were written as LOCKED supersession entries (never edits to prior entries) — the
  next fresh reviewer could audit the chain instead of re-deriving it. Supersede-don't-edit is
  what makes multi-pass fresh-context review converge instead of thrash.

### 2.3 FREEZE / DESIGN — DONE 2026-07-19
- **Authoring:** a dispatched design author compiled the 28 LOCKED ledger entries into DESIGN.md
  (contract by subsystem, supersession chains FLATTENED to final rules, final config schema of
  record, file-touch map with semver bumps, test surface, risks/non-goals) + PLAN.md (6 tasks,
  2 waves, disjoint file ownership, TDD mandates, per-task gates). The author REPORTED five
  tensions/interpolations instead of silently resolving them (PD-2 discipline).
- **Freeze-gate:** fresh-context adversarial reviewer, default-HOLD, grounded every cited
  file:line against the live tree. Verdict: SHIP-WITH-FIXES — all 5 interpolations RATIFIED
  with reasons; 8 findings (2 HIGH: a validator/schema mismatch that would have bricked every
  default composed config at the load-guard; the live-proof grant paradox — this run's config
  predates the feature, so the n=1 exercise needs an explicit operator-DECISION grant; 3 MED,
  3 LOW). Fixes sent back to the SAME author agent (context intact) rather than re-authoring.
- **Transferable techniques:** (a) authors REPORT tensions, gates RULE on them — interpolation
  without ratification is drift; (b) the gate grounds citations against the tree, not the
  design's own claims — that's how the schema-mismatch brick was caught pre-build; (c) reusing
  the author agent for fixes via message-resume preserves its full reading context at zero
  re-read cost.

### 2.3b BUILD DISPATCH — DONE 2026-07-19
- Operator dual-control confirm received → branch `advisor/fable-advisor`; freeze artifacts
  committed first (`0922cf6`).
- **W1 (parallel, disjoint, no-git workers at Opus = anchor−1 standard coding):** T1
  kata_models additions (registry/rung/validator/gate + 218 tests) · T2 NEW kata_advisor.py
  (budget/state/EV-1 pairing, 110 tests) + additive telemetry key (209 tests, BC proven) ·
  T3 three protocol docs. Conductor wave gate: byte-untouched claims DIFF-VERIFIED (not
  trusted from reports), 687 tests, ruff, validator 48/0/0 → commit `1b5936a`.
- **W2 (parallel, disjoint):** T4 kata-advise SKILL.md 0.1.0 (49th skill, A1 clean) · T5
  four-hook prose wiring across 8 skills (orchestrate 0.14.0 w/ FIX-4 Leg-C anchoring;
  bootstrap/preflight/initiate/design-doc/plan tiers bumped) · T6 D167 + README + CHANGELOG.
  Cross-task README-index staleness resolved by the CONDUCTOR's `validate_skills.py --write`
  reconcile (both workers correctly refused to cross ownership — the error was an
  integration-order artifact, not a defect). Validator 49/0/0 → commit `badf63d`.
- **Transferable techniques:** (a) workers report ownership-boundary blockers instead of
  fixing them out-of-lane — the conductor owns cross-task reconciliation; (b) the conductor
  re-verifies byte-untouched claims by git diff itself — worker self-reports are necessary
  but not sufficient (PD-2 + no-self-cert applied to build waves); (c) per-wave commits by
  the sole-git-writer conductor keep worker parallelism free of tree races.

### 2.4 EXECUTE — integration gate + live exercise — DONE 2026-07-19
- **Gauntlet:** pytest-unit PASS · pytest-integration PASS · ruff PASS · validator 49/0/0 PASS
  (honest-exit runner `tools/scripts/gauntlet.py`). Snyk Code med+ = 0 on tools/.
- **Live n=1 exercise (AC #1), operator-granted (FIX-2 path):** operator grant recorded as a
  board DECISION → the REAL gate ran (`advisor_status` ⇒ fires, arm (a) inherit at the fable
  anchor) → budget/spend/outcome through the REAL engine (`resolve_advisor_budget` 5/1,
  `can_spend_advisor` True with reserve intact, `record_advisor_spend`, `record_outcome`
  null-pending — honest: no failing advised attempt exists in an exercise) → request artifact
  `.kata/advice/live-exercise-1-1.json` → fresh-context kata-advise dispatch at the session
  anchor → structured response (schema-shaped, citation-dense) → disposition DECISION.
- **The consult was genuinely useful (not a smoke ritual):** the question was the run's own
  riskiest seam (S-11b bump-deferral vs engine consume semantics). The advisor CONFIRMED the
  deferral legal (observe≠consume, double-bump structurally impossible) and surfaced a real
  new risk — restart-mid-deferral loses the earned bump (accepted under-adapt), plus the rule
  that the failbump DECISION line must be emitted only at consume time. These findings were
  handed to the evaluate/adval judges as evidence; the pinning-test sketch goes to the
  operator rollup (S-2: never auto-applied).
- **Transferable technique:** make the live exercise EARN its keep — aim the n=1 consult at
  the run's own most uncertain seam, so the proof-of-life doubles as real verification input.

### 2.5 EVALUATE / ADVAL — IN PROGRESS
*(fresh-context default-FAIL evaluate + adversarial review dispatched in parallel)*

### 2.4 EXECUTE
*(pending)*

### 2.5 EVALUATE / ADVAL
*(pending)*

### 2.6 CLOSEOUT
*(pending)*

## 3. Transferable technique notes

- **Parallel grounding:** dispatch the codebase-assessment agent *before* entering the loop's
  front door; its report lands mid-initiation and grounds the grill with zero added latency.
- **Recall-before-design:** run the recall engine over prior decisions/lessons with
  feature-derived query terms; the top-matched decision records ARE the constraint set the
  design must compose with — cheaper and more reliable than re-reading everything.
- *(more appended as the run proceeds)*
