---
date: 2026-06-07
branch: master (local only — no remote yet)
commit: see `git log -1` (modes-design checkpoint)
green: n/a (KataHarness ships skills/docs, no test suite of its own)
tags: [handoff, modes, checkpoint]
---

# HANDOFF — KataHarness — 2026-06-07 (operating-modes design done; ready to compact)

> **Fresh session: read in order, then resume.**
> 1. `AGENTS.md` · 2. `docs/DESIGN.md` · 3. `docs/STANDARDS.md` · 4. **`docs/MODES-DESIGN.md`** (the new work) ·
> 5. `CONTEXT.md` (vocabulary) · 6. `.planning/STATE.md` + `DECISIONS.md` (D1–D23) + `LESSONS-LEARNED.md`
> (L1–L10) + `REVIEW-v0.1.md` + `SKILL-COST-RATINGS.md`.

## Where we are
- **15 of 18 skills built**, all `0.1.0/experimental`, adversarially reviewed + fixed (REVIEW-v0.1; HOLD→closed).
  Deferred: `kata-tasklist` (reframed, D23), `kata-zoom-out`, `kata-engram`.
- **Execution half field-proven**: built CPP Phase 3 (G_macro) green via subagents in worktrees; A/B vs GSD
  **tied** (L10) — execution on-par, not better; the grill (differentiator) is untested. CPP Phase 3 lives on
  CPP branch `test/phase3-kata` (worktree `C:/Dev/_kata_armA/integration`); user shipped GSD's Arm B to CPP main.
- **NEW this session — operating-modes design (brainstormed, NOT implemented):** `docs/MODES-DESIGN.md` +
  `CONTEXT.md` + `.planning/SKILL-COST-RATINGS.md`; decisions D17–D23. Cost-rating analyzer run on all 15 skills.

## The modes design in one breath
Modes (Essential/Standard/Advanced) = **spine + module bundle + tier of each tiered skill** (one unified axis),
× an orthogonal **effort overlay**, + à-la-carte modules. **Consistency is the north star** (D18); the
`kata-evaluate` conformance gate is the uniform floor and is **never tiered** (D22). Tiering is **cost-gated**
(D21): separate files for high-cost/variance skills (`grill`, `review`, `plan`, `diagnose`); mode-hint depth for
medium (`design-doc`, `tdd`). A `kata-bootstrap` selector writes a per-branch `kata.config` (provenance →
reproducibility → cheap step-up). Don't reinvent: model-effort = Claude `effort`; bake-off = AgentHub/worktrees.

## NEXT STEP (in order)
1. **User reviews `docs/MODES-DESIGN.md`.** Confirm the 2 pending items: **mode=tier unification** (vs
   independent knobs) and **`kata-bootstrap` as its own skill** (recommended defaults: unified; own skill).
2. **`kata-plan` / writing-plans → Spec A** (the mode/tier/module/config/bootstrap system + bake cost-weights
   into frontmatter + tier grill/review/plan/diagnose + `TAXONOMY.md` + fold grill efficiency refactor). Then
   Spec B (bake-off), Spec C (version-ups), `design` module (own spec).
3. **Parallel: the D16 planning-varied A/B** (prove the grill differentiates) before calling v0.1 "validated."

## Suggested next skills
`kata-plan` (Spec A plan) · `kata-write-skill` (for `kata-bootstrap` + the tier-family files) · `kata-review`
(adversarial-review every new skill, D15) · `kata-improve` (fold the efficiency refactors).

## Open decisions for the human
- The 2 pending confirmations above. · Set a **git remote** (still local-only) before public release. ·
  License selection. · Whether to do Spec A before or after the D16 A/B.

## Redaction
No secrets/keys/PII. Nothing to redact.
