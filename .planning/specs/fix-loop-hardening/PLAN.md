---
title: "Fix-loop hardening — PLAN"
status: FROZEN (PLAN) — pending freeze-gate adversarial review
date: 2026-06-24
spec: fix-loop-hardening
ownership:
  S1: [protocol/state.md, protocol/escalation.md]
  S2: [skills/coordinate/kata-orchestrate/SKILL.md, skills/execute/kata-diagnose/SKILL.md]
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

**Goal.** Wire DESIGN L1–L6: material (blast-radius-scoped) re-verification + a per-task thrash budget that
escalates an oscillating fix-loop to a **deliberate, human-gated re-plan event** via `kata-diagnose`.
Non-code-bearing — `.md` contract edits + one drift-ledger field; **no new `tools/` Python** (L4).

## Global constraints (every slice)
- **No new committed Python** (L4) — the `fixAttempts` counter is a field in the existing `state.json` drift
  ledger the orchestrator already writes via `kata_board.update_task`. Add no `.py`.
- **Additive between the gates** (L6) — do not alter the default-FAIL gate, the no-self-cert rule, or the
  escalation *contract*; bound/scope the loop between them. Quote LOCKED decisions verbatim where referenced.
- Conventional commits + trailer; stage specific files; match each file's existing voice.

## LOCKED (verbatim from DESIGN — workers MUST NOT re-decide)
L1 material re-verification · L2 thrash budget (per-task `fixAttempts`, **default N=2** → escalate on the 3rd
failure) · L3 thrash → deliberate human-gated re-plan via `kata-diagnose` + the existing escalation valve,
never silent · L4 no new Python (counter in `state.json`) · L5 batch-fix + staged cascade · L6 additive
between the gates.

---

## Slice S1 — the contract (`protocol/state.md`, `protocol/escalation.md`) · wave 1
**read_first:** this PLAN + the DESIGN (L1–L6); current `protocol/state.md` (the drift-ledger / state schema)
and `protocol/escalation.md` (the escalation kinds/classification + payload schema).
**action:**
1. `protocol/state.md`: add a **`fixAttempts`** field to the per-task drift-ledger record (int, default 0,
   orchestrator-incremented on each NEEDS_WORK→fix cycle for that task; reset when the task reaches PASS).
   Document that it is the thrash-budget counter (L2) and that it is written **only** by the orchestrator via
   the existing `kata_board.update_task` path (single-writer L3-state rule unchanged).
2. `protocol/escalation.md`: register a **thrash classification** — a fix-loop that hits the budget (L2) is
   escalated as a **re-plan candidate** (reuse/extend the existing `human-required` kind; do **not** invent a
   parallel valve). Document that the orchestrator routes it through `kata-diagnose` first (root-cause:
   fix-problem vs plan-problem), and only a **plan-problem** becomes a human-gated re-plan event
   (supersede-not-rewrite, L3). The one-line board `ESCALATE` pointer + structured payload contract are unchanged.
**acceptance:**
- `state.md` has `fixAttempts` (semantics + default + reset + single-writer note) per L2/L4.
- `escalation.md` frames thrash as a re-plan-candidate routed via `kata-diagnose`, reusing the existing valve
  (no parallel mechanism), human-gated, never silent (L3). No change to the payload schema or the async
  park/drain contract beyond this classification note.
**verify:** `cd tools && uv run python validate_skills.py` (36/0 — protocol files aren't skills; confirms no
breakage) + a read-back that the two additions are present and consistent with each other.

## Slice S2 — orchestrator wiring (`kata-orchestrate`, `kata-diagnose`) · wave 2 (depends_on: S1)
**read_first:** this PLAN + DESIGN (L1/L3/L5); S1's frozen `protocol/state.md` + `protocol/escalation.md`;
current `kata-orchestrate` "## Escalation" + "## Final gate" (the fix-loop step) + the per-task gate (loop
step 3); current `skills/execute/kata-diagnose/SKILL.md`.
**action:**
1. `kata-orchestrate`:
   - **Fix-loop step (Final gate "NEEDS_WORK → targeted fix" + the per-task gate):** add **material
     re-verification (L1)** — always re-run the cheap gate; re-run a fresh-context judge only if the fix's
     footprint intersects its evidence basis; **one** full-stack confirmation pass after the final fix batch.
     Add **batch-fix (L5)** — collect all of a judge's findings, fix in one batch, then re-verify that judge
     (not fix-one-rerun-one). Reaffirm the cheap→expensive **staged cascade** ordering.
   - **Thrash budget (L2/L3):** increment per-task `fixAttempts` (via `kata_board.update_task`) each
     NEEDS_WORK→fix cycle; at **N=2** (3rd failure on one area) **STOP**, dispatch `kata-diagnose`, and on a
     plan-problem verdict escalate a **re-plan candidate** through the existing escalation valve (human-gated,
     supersede-not-rewrite, async-park per the existing contract). Quote L3 verbatim.
2. `kata-diagnose`: add a **thrash tie-in** — when invoked by the orchestrator on a budget-exhausted area,
   run a systematic root-cause pass that explicitly **classifies fix-problem vs plan-problem** and returns that
   verdict to the orchestrator (it does not itself re-plan; the orchestrator owns the re-plan decision).
**acceptance:**
- Fix-loop carries L1 (material re-verify + one confirmation pass) + L5 (batch-fix) + the staged-cascade note,
  additively (no change to default-FAIL/no-self-cert/escalation-contract — L6).
- Thrash budget present: `fixAttempts` increment, N=2 stop, `kata-diagnose` dispatch, plan-problem →
  human-gated re-plan via the existing valve (L2/L3). No new Python; no parallel escalation mechanism.
- `kata-diagnose` returns a fix-problem-vs-plan-problem verdict; does not re-plan itself.
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
