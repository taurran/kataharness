---
title: "kata-slop-check v0.1 — frozen PLAN (WS-2 version-up dogfood)"
status: FROZEN (freeze before dispatch; supersede-not-edit once orchestration starts)
date: 2026-06-22
mode: version-up (target.kind = existing; baseline = current green master)
dual-purpose: >-
  Builds a real selected feature (kata-slop-check, an optional EVALUATE-phase quality module) AND serves as
  the WS-2 validation vehicle — its DAG + injected research-needed escalation exercise the rolling-frontier
  concurrency branches and the in-loop RS research path that the audit found unexercised.
ownership:
  S1: [skills/evaluate/kata-slop-check/SKILL.md]
  S2: [protocol/engram.md]
  S3: [protocol/config.md]
  S4: [tools/validate_skills.py, tools/tests/test_validate_skills.py]
  S5: [skills/coordinate/kata-orchestrate/SKILL.md]
waves:
  wave1: [S1, S2, S3]
  wave2: [S4, S5]
depends_on:
  S1: []
  S2: []
  S3: []
  S4: [S1]
  S5: [S1, S3]
tags:
  - kata/spec
  - kata-slop-check
  - ws2
---

# kata-slop-check v0.1 — frozen PLAN

## Goal
Ship **`kata-slop-check`** as a standalone **optional module** (`kata/module/slop`): a fresh-context,
**no-write** EVALUATE-phase check that grades a run for **AI-slop / spiraling-session** signals and returns a
**default-FAIL gate finding** (`SLOP-DETECTED ⇒ NEEDS_WORK`), never advisory-only. Detection is **in-context
heuristics** (no new detection Python). The feature catches degraded long-running loops — a risk the operator
flagged — and its build doubles as the WS-2 proof of parallelism + the in-loop RS research path.

## LOCKED decisions (no worker may re-decide; conflict ⇒ escalate human-required)
- **L1 — Form.** Standalone optional module `kata/module/slop`, skill `kata-slop-check`, **fresh-context
  no-write**, dispatched in EVALUATE **alongside** `kata-evaluate` (NOT an axis inside `kata-review`).
- **L2 — Verdict.** A slop verdict is a **default-FAIL gate finding** (`SLOP-DETECTED ⇒ NEEDS_WORK`), never
  advisory-only.
- **L3 — No detection Python.** Checks are **in-context heuristics** in the SKILL. The only code change in
  this run is S4's validator wiring (+ its test). No new `tools/` detection module.
- **L4 — License-gated adoption (spine #12 / D12).** Any check adopted from the external `ai-slop-detector`
  repo MUST be **license-verified** and **`source:`-attributed** before adoption. These facts are NOT in this
  plan (external repo, possibly past the Jan-2026 cutoff) — **S1 must escalate `research-needed`**; the RS path
  resolves it. Do **not** pre-bake or guess them.
- **L5 — Disjoint ownership.** Each worker edits ONLY its `ownership:` files (drift check enforces).
- **L6 — Roster.** Workers = **Sonnet**; orchestrator + `kata-research` (RS) + `kata-evaluate` + the WS-2
  grader = **Opus** (Fable 5 unavailable, D59). RS = `kata-research`, fresh-context **no-write**.
- **L7 — In-context grading (no Python).** The WS-2 invariants are graded by a **fresh-context no-write
  evaluator** reading `.kata/board.md` timestamps + git worktree history — not a Python model.

## Slices

### S1 — the skill (carries the research-needed escalation) · wave 1 · not code-bearing
- **read_first:** `skills/evaluate/kata-evaluate/SKILL.md` + `skills/evaluate/kata-review-standard/SKILL.md`
  (house style), `protocol/engram.md` (seam pattern), `docs/STANDARDS.md` §1, `AGENTS.md`.
- **action:** Author `skills/evaluate/kata-slop-check/SKILL.md`:
  - Frontmatter: `name: kata-slop-check`, `category: evaluate`, `agnostic: true`,
    **`allowed-tools: [Read, Grep, Glob, Bash]`** (NO Write/Edit — no-write contract), `model: fable`,
    `version: 0.1.0`, `status: experimental`, `cost-weight`, tags `kata/evaluate` + `kata/module/slop`,
    and **`source:`** crediting `ai-slop-detector` with its verified license (filled from the RS finding).
  - Body: the fresh-context no-write contract; the **in-context check set** — general signals
    (looping/repetition, self-contradiction, no-progress churn, unrequested scope expansion,
    ungrounded/fabricated claims, degraded coherence) **plus the grounded minimal subset adopted from
    `ai-slop-detector`** (D41/GB8 minimal-step bake-in — adopt only the stripped-down necessary checks); the
    **verdict schema** (`SLOP-DETECTED | CLEAN`, severity, evidence list, **default-FAIL ⇒ NEEDS_WORK**); how
    it is dispatched (EVALUATE, alongside `kata-evaluate`); seam pointers to `kata-review` / `kata-diagnose` /
    `kata-selfhandoff`.
- **RESEARCH-NEEDED (by design):** the worker cannot complete the adopted-subset + `source:`/license without
  the external repo's facts → it MUST write a `research-needed` escalation
  (`decisionNeeded`: "which ai-slop-detector checks to adopt + does its license permit adoption + required
  attribution"; `optionsConsidered`: the general check set alone vs general+adopted) and STOP. Do not guess.
- **acceptance:** `validate_skills.py` passes with the new skill; `allowed-tools` omits Write/Edit; verdict
  schema + default-FAIL semantics present; the adopted subset is grounded with a **cited source** + a license
  note folded in via the orchestrator's superseding re-plan.
- **verify:** `cd tools && uv run python validate_skills.py`

### S2 — engram seam registration · wave 1 · not code-bearing
- **read_first:** `protocol/engram.md` (seam table E1–E21 + the maintenance rule).
- **action:** add seam **E22** for `kata-slop-check`: a `SLOP-DETECTED` verdict is a default-FAIL EVALUATE
  gate finding; LEARN surface = which slop classes the user accepts vs forces-fix; latent CONSULT = pre-weight
  by the user's tolerance. Match the table format; honor the "register a seam in the same change" rule.
- **acceptance:** new row present + well-formed; substrate/seam distinction respected.
- **verify:** `grep -n "kata-slop-check" protocol/engram.md` returns the seam row.

### S3 — config module registration · wave 1 · not code-bearing
- **read_first:** `protocol/config.md` (module-provider + module list).
- **action:** register `kata/module/slop` as an **optional** module (provider `kata-slop-check`), **off by
  default**; document the slop boundary (default-FAIL). Keep the config schema valid.
- **acceptance:** module entry present; default-off; schema coherent.
- **verify:** `grep -n "kata/module/slop" protocol/config.md` returns the entry.

### S4 — validator no-write wiring + test · wave 2 · **code-bearing (mutation-proof required)** · depends_on S1
- **read_first:** `tools/validate_skills.py` (`NO_WRITE_EVALUATORS` frozenset + `check_evaluator_no_write`),
  `tools/tests/test_validate_skills.py`.
- **action:** add `"kata-slop-check"` to `NO_WRITE_EVALUATORS`; add a test asserting kata-slop-check is in the
  no-write set **and** that `check_evaluator_no_write` flags it if Write/Edit were present. Run
  `mutation_run.prove_non_vacuous` on the new assertion and report the verdict with DONE.
- **acceptance:** `pytest` green; new test **non-vacuous** (mutation-proven); `validate_skills.py` green.
- **verify:** `cd tools && uv run pytest -q && uv run python validate_skills.py`

### S5 — EVALUATE-phase dispatch pointer · wave 2 · not code-bearing · depends_on S1, S3
- **read_first:** `skills/coordinate/kata-orchestrate/SKILL.md` (Final gate, step 3).
- **action:** in the Final gate, add a **conditional** pointer: *if `kata/module/slop` is configured, also
  dispatch `kata-slop-check` as a fresh-context no-write check alongside `kata-evaluate`; a `SLOP-DETECTED`
  verdict is default-FAIL (NEEDS_WORK).* 2–4 lines; no change to any LOCKED decision; degrade to no-op when
  the module is absent.
- **acceptance:** conditional pointer present; default-FAIL semantics stated; no-op without the module;
  `validate_skills.py` green.
- **verify:** `cd tools && uv run python validate_skills.py`

## Orchestration sequence (operator-gated)
1. **FREEZE** (this doc) + `git tag pre-ws2-slopcheck` on the baseline (backout point). ◆ operator go.
2. **Wave 1:** worktrees + dispatch **S1, S2, S3 concurrently** (Sonnet). Board records CLAIM with timestamps.
3. **S1 escalates `research-needed`** → park S1 + dependents S4, S5; **keep S2, S3 flowing**. Persist the
   payload (`tools/escalation.py` `build_escalation`/`write_escalation` → `.kata/escalations/S1.json`).
4. **RS:** dispatch `kata-research` (fresh-context no-write) scoped to the payload → returns
   `{claim, source, confidence, groundsToPlan}` findings (license + adopted-check subset, cited). ◆ operator
   may review.
5. **Grounding gate:** `kata-evaluate` injected-knowledge mode + `kata-review` soundness → orchestrator
   persists verdicts (`grounding_gate.py` `build_verdict`/`write_grounding` → `.kata/grounding.json`).
   GROUND ⇒ **fold via a superseding re-plan** (audited in the drift ledger) → re-dispatch S1. REJECT/can't-ground
   ⇒ re-classify human-required ◆.
6. **Wave 2:** as S1 integrates → S4 dispatchable; as S1+S3 integrate → S5 dispatchable. Dispatch concurrently.
7. **Final gate:** full default-FAIL gate green (`pytest` + `validate_skills.py` + Snyk on S4's Python);
   emit `.kata/{RESULT,footprint,mutation}.json` (`gate_emit.emit_gate_artifacts(..., mutation_records=<union>)`).
8. **Fresh-context `kata-evaluate`** → PASS/NEEDS_WORK (feature gate). NEEDS_WORK ⇒ targeted fix, same plan.
9. **WS-2 grade** (separate fresh-context no-write evaluator, in-context): grade the rubric below. ◆ operator
   reviews the closeout (plain-language what-changed-and-why; backout offered).

## WS-2 grading rubric (graded after the run, from `board.md` + git history — in-context)
1. **Concurrency real:** ≥3 workers' CLAIM/DONE intervals genuinely overlap in wave 1 (not serial dispatch).
2. **Park-a-sub-tree:** S1's escalation parked S1 + S4 + S5; **no S4/S5 CLAIM appears during the park**, while
   S2/S3 progressed.
3. **Frontier recompute:** S4 CLAIM only after S1 integrated; S5 CLAIM only after both S1 and S3 integrated.
4. **RS path end-to-end:** `kata-research` dispatched on the escalation; findings **grounded** (cited source +
   verified license); grounding-gate verdict recorded; folded via a **superseding re-plan** in the drift ledger.
5. **Completion-ordered integration:** linear integration history, merge order = completion order.
6. **Mutation proof:** `.kata/mutation.json` carries a non-vacuous proof for S4 (the code-bearing slice).
7. **No drift:** 0 unauthorized LOCKED deviations; every file touched ⊆ its slice ownership.

## Gate & backout
- **Gate:** `cd tools && uv run pytest -q && uv run python validate_skills.py`; **Snyk** on S4's changed Python
  (medium+ = 0).
- **Backout (offered at closeout):** `git reset --hard pre-ws2-slopcheck` (tag set in step 1) — surfaced as a
  first-class option, not a buried command (WS-4 spirit).

## Carry-outs (NOT in this run)
- The grill-skip **proactive**-RS note in `kata-orchestrate` ("named, not yet wired") — a WS-2 tail; tighten
  separately.
- `codeBearing` doc-fix caveat — separate tiny doc commit.
