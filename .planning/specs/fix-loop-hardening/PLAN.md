---
title: "Fix-loop hardening — PLAN"
status: FROZEN (PLAN) — freeze-gate SHIP (HOLD→resolved, re-confirmed)
date: 2026-06-24
spec: fix-loop-hardening
ownership:
  S1: [protocol/state.md, protocol/escalation.md]
  S2: [skills/coordinate/kata-orchestrate/SKILL.md, skills/execute/kata-diagnose/RUBRIC.md]
waves:
  - [S1]
  - [S2]
depends_on:
  S1: []
  S2: [S1]
tags:
  - kata/plan
  - fix-loop
  - thrash-guard
---

# Fix-loop hardening — implementation PLAN

**Goal.** Wire DESIGN L1–L6: material (footprint-cited) re-verification + a **per-area + run-level** thrash
budget that escalates an oscillating fix-loop to a **deliberate, human-gated re-plan event** via `kata-diagnose`.
Non-code-bearing — `.md` contract edits only; **no new `tools/` Python** (L4).

## Global constraints (every slice)
- **No new committed Python** (L4) — the thrash counts are **transient orchestrator in-context bookkeeping**
  during the final-gate fix loop (the orchestrator counts its own eval→fix iterations); the existing `DECISION`
  board lines are the durable recount trail. **No `state.json` field, no `update_task` change, no new board
  TYPE, no `.py`.** (The board records no "NEEDS_WORK→fix" event — do not assume one.)
- **Additive between the gates** (L6) — do not alter the default-FAIL gate, the no-self-cert rule, or the
  escalation *contract*; bound/scope the loop between them. Quote LOCKED decisions verbatim where referenced.
- Conventional commits + trailer; stage specific files; match each file's existing voice.

## LOCKED (verbatim from DESIGN — workers MUST NOT re-decide)
L1 material re-verification (conservative; **indeterminate ⇒ re-run**; confirmation pass = cheap gate +
`kata-evaluate`, red-team once after) · L2 thrash budget — **per-area N=2** + a **run-level ceiling**, both
**orchestrator-in-context** (transient fix-loop counts; not a `state.json` field, no board TYPE),
confirmation-regressions count · L3 thrash → `kata-diagnose` fix-vs-plan verdict → human valve **only on
plan-problem**, via the existing `human-required` kind (no enum change), async-parked, never silent · L4 **no
new Python; counter orchestrator-in-context** · L5 batch-fix + staged cascade · L6 additive between the gates
(no enum/schema change).

---

## Slice S1 — the contract (`protocol/state.md`, `protocol/escalation.md`) · wave 1
**read_first:** this PLAN + the DESIGN (L1–L6); current `protocol/state.md` (the drift-ledger / state schema)
and `protocol/escalation.md` (the escalation kinds/classification + payload schema).
**action:**
1. `protocol/state.md`: add a one-line clarifying note (in or near the tier-3 derived-cache / R5 section) that
   the fix-loop **thrash counts** (per-area + run-level, fix-loop-hardening) are **orchestrator-transient
   in-context control state during the final-gate fix loop** — **deliberately NOT** persisted in `state.json`,
   **NOT** a board event TYPE, and **NOT** written via `kata_board.update_task`; they are recountable from the
   existing `DECISION` board lines on resume (L2/L4). A confirmation-pass regression counts against them (a
   later-invalidated PASS does not zero them). *(This note exists to stop a future dev from adding a `state.json`
   field or a board TYPE.)*
2. `protocol/escalation.md`: document the **thrash → re-plan-candidate** routing — it **reuses** the existing
   `kind: "human-required"` (**no enum change**, L6); the thrash distinction is carried in `decisionNeeded`/
   `rationale` + a note that the orchestrator ran **`kata-diagnose` first** and only a **plan-problem** verdict
   surfaces to the human (supersede-not-rewrite; async-parked per the existing contract, L3). The `kind` enum,
   payload schema, and async park/drain contract are otherwise **unchanged**.
**acceptance:**
- `state.md` documents the thrash counts as **orchestrator-transient in-context** control state (NOT a
  `state.json` field, NOT a board TYPE, NOT via `update_task`) per L2/L4; the confirmation-regression-counts
  note is present.
- `escalation.md` frames thrash as a `human-required` re-plan-candidate routed **`kata-diagnose`-first**,
  distinction in `decisionNeeded`/`rationale`, **no `kind` enum change**, async/payload contract unchanged (L6).
**verify:** `cd tools && uv run python validate_skills.py` (36/0 — protocol files aren't skills; confirms no
breakage) + a read-back that the two additions are present and consistent with each other.

## Slice S2 — orchestrator wiring (`kata-orchestrate`, `kata-diagnose/RUBRIC.md`) · wave 2 (depends_on: S1)
**read_first:** this PLAN + DESIGN (L1/L3/L5); S1's frozen `protocol/state.md` + `protocol/escalation.md`;
current `kata-orchestrate` "## Escalation" + "## Final gate" (the fix-loop step 5 + the D98 red-team step 6) +
the per-task gate (loop step 3); the **shared** `skills/execute/kata-diagnose/RUBRIC.md` (tier-invariant
method — the `-full`/`-light` SKILLs both obey it) incl. its Phase-6 "if architectural → kata-improve" seam.
**action:**
1. `kata-orchestrate`:
   - **Fix-loop step (Final gate "NEEDS_WORK → targeted fix" + the per-task gate):** add **material
     re-verification (L1)** — always re-run the cheap gate; re-run a fresh-context judge **iff** the fix
     footprint intersects a file that judge's findings cited, **indeterminate ⇒ re-run**; **one** confirmation
     pass after the final fix batch = the cheap gate **+ `kata-evaluate`**, with the D98 `kata-review` (step 6)
     running **once after the confirmation pass settles, never inside the loop.** Add **batch-fix (L5)** —
     collect all of a judge's findings, fix in one batch, then re-verify that judge. Reaffirm the
     cheap→expensive **staged cascade** ordering.
   - **Thrash budget (L2/L3):** count fix-cycles **per-area** (keyed on task) **and run-level**, both as
     **transient in-context counts** the orchestrator keeps while running the fix loop (it counts its own
     eval→fix iterations; its existing `DECISION` board lines are the recount trail) — **NOT** a board event,
     **NOT** `update_task`, **NOT** a `state.json` field. At **N=2** (3rd failure of one area) **or** the
     run-level ceiling, **STOP**, dispatch **`kata-diagnose`** (resolved tier), and **only on a plan-problem
     verdict** escalate a **re-plan candidate** via the existing `human-required` kind (async-parked,
     supersede-not-rewrite). Quote L3 verbatim.
2. `skills/execute/kata-diagnose/RUBRIC.md` (the **shared, tier-invariant** method): formalize a
   **fix-problem vs plan-problem verdict** as a returnable output, built from the RUBRIC's **existing Phase-6
   "what would have prevented this? — if architectural, hand to kata-improve"** seam. The skill **returns the
   verdict to the orchestrator and does NOT itself re-plan** (consistent with its standing "Don't re-plan —
   escalate" rule). Both `-full`/`-light` inherit it (shared RUBRIC).
**acceptance:**
- Fix-loop carries L1 (conservative footprint-cited + **indeterminate⇒re-run** + confirmation pass = cheap +
  `kata-evaluate`, red-team **once after**, never in-loop) + L5 (batch-fix) + staged-cascade, **additively** (no
  change to default-FAIL / no-self-cert / escalation contract — L6).
- Thrash budget: **orchestrator-transient in-context** per-area + run-level counts (**no board TYPE, no
  `update_task`/state field, no new Python**), N=2/ceiling STOP, `kata-diagnose` dispatch, **plan-problem only**
  → `human-required` escalation (no enum change, no parallel mechanism).
- `kata-diagnose/RUBRIC.md` returns a fix-vs-plan verdict (tier-invariant; both tiers inherit), formalized from
  Phase-6, does **not** re-plan itself. **The acceptance test must prove the verdict is actually returned**
  (D98/L12 reproduce-don't-trust), not merely documented.
- `model: fable`, frontmatter, the WS-3 narration section, and the D98 red-team step (step 6) untouched.
**verify:** `cd tools && uv run python validate_skills.py` (36/0).

---

## Integration & gate (orchestrator)
1. Octopus-merge S1 → S2 (disjoint files); `cd tools && uv sync`.
2. Gate: `uv run pytest -q` (**447**, unchanged — non-code-bearing) + `validate_skills.py` (**36/0**). Emit
   `.kata/RESULT.json` via `gate_emit` (expect `codeBearing:false`). No Snyk (no new/changed Python).
3. Fresh-context **Opus `kata-evaluate`** (no-write, default-FAIL) on the diff + artifacts. Must PASS.
4. **Standing adversarial `kata-review` (D98 — this is a contract-bearing build):** fresh-context, ≥ standard,
   attack the thrash threshold / "material" definition / async-escalation interaction / C-arc safety claim.
   SHIP-WITH-FIXES/HOLD → targeted fixes → re-confirm.
5. Operator gate → merge, push, checkpoint, push.
