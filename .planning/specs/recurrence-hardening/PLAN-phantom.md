---
title: "Phantom-machinery first hardening — verify-before-reuse guard (FROZEN PLAN)"
status: FROZEN (freeze step done; pending freeze-gate kata-review → build)
date: 2026-06-25
spec: recurrence-hardening
decision: D101 (worked example) · D98/L12 (fold lessons into skills) · D33 (structural invariants never tiered)
relates-to: memory `verify-primitives-before-claiming-reuse` (promoted to a skill guard)
tags:
  - kata/meta
  - improve
  - self-hardening
  - recurrence-hardening
---

# Phantom-machinery first hardening — the worked example of D101

> The first concrete instance of recurrence-hardening (D101): the adversarial lens caught the **same
> failure-class four times this session** — spec/planning agents **over-claiming that machinery exists**
> ("composes existing primitives / reuses X / the orchestrator already writes Y") when the primitive does
> not expose the surface the design assumes (the project's signature documentation-only-seam). Rather than
> rely on the red-team to catch it every time, **harden the responsible skills** with a permanent, gated guard.

## Why this skill, this placement
A "reuses X" claim is an **architectural assertion about existing code**. It enters a contract at the
**design-doc freeze** (DESIGN §2 "where it lives, grounded in code" + §5 backward-compat) and is re-asserted
at **plan** time (`read_first`/`action`) and by the **worker** (`kata-tdd`). `kata-grill` is *not* a site —
it resolves decisions with the human, it does not author code-grounded reuse claims. A `grep` confirms the
pattern is pervasive across `kata-loop`, `kata-orchestrate`, `kata-sprint`, `kata-evaluate`, `kata-report`,
`kata-graph` — so the guard polices the project's most common sentence shape.

## LOCKED decisions

**LD1 — The guard is a STRUCTURAL INVARIANT (never tiered, D33-class).** Verify-before-reuse is integrity,
not depth — like no-self-certification. It applies identically at Essential / Standard / Advanced. Tiers vary
depth only; this guard never relaxes.

**LD2 — Canonical home: `protocol/reuse-claims.md`** (a cross-skill contract, precedent: `escalation.md`,
`orientation.md`). One source of truth; the responsible skills reference it **by path** (not `[[wikilink]]`,
which resolves to skills). DRY-by-pointer.

**LD3 — The guard text (verbatim, the contract):**
> Before writing **"reuses / composes / via the existing X"** (or "the orchestrator already writes Y", "this
> already exists/has Z"), **grep/read X and confirm it exposes the exact field / event / output / path the
> design assumes — cite the concrete `file:line`.** Treat "this already exists" as a **claim to verify, not an
> assumption**. If the surface is not there, label it a **NEW capability** and scope it. A reuse claim with no
> cited surface is a documentation-only seam (the project's signature failure mode) — do not freeze it.

**LD4 — Pointer scope: `kata-design-doc` + `kata-plan/RUBRIC.md` + `kata-tdd`.** The freeze site (design-doc,
primary), the re-assert site (plan RUBRIC — inherited by all three tier files), and the worker (tdd). Each
gains a short pre-flight/quality-bar line pointing at `protocol/reuse-claims.md`.

**LD5 — Two tests, both required (D98/L12 "reproduce, don't trust"):**
- **T-regression (wired, not remembered):** a `validate_skills.py` rule asserts each of the three responsible
  skills references `protocol/reuse-claims.md`. Catches silent removal/drift forever (the L12c lesson —
  unwired lessons recur).
- **T-fire (proof-of-fire, n=1, operator's explicit ask):** a one-shot live adversarial probe — a
  fresh-context planning agent is given a deliberate *"reuses `X.foo()`"* claim against a surface that does
  not exist; the hardened skill's pre-flight must **flag it / label it NEW** instead of freezing the claim.
  Recorded in `REPORT-phantom.md`.

**LD6 — This run is code-bearing** (it adds a `validate_skills.py` rule). `kata-evaluate` rubric item 1
requires `.kata/mutation.json` `allNonVacuous:true` for the validator-rule task (T3).

## Task partition (disjoint file ownership)

```yaml
ownership:
  T1: [protocol/reuse-claims.md]
  T2: [skills/plan/kata-design-doc/SKILL.md, skills/plan/kata-plan/RUBRIC.md, skills/execute/kata-tdd/SKILL.md]
  T3: [tools/validate_skills.py, tools/tests/test_reuse_claims_guard.py]
waves:
  wave1: [T1]
  wave2: [T2]
  wave3: [T3]
depends_on:
  T2: [T1]   # pointers must reference the path T1 creates
  T3: [T1, T2]   # the rule asserts T2's pointers exist and T1's file is present
```

Sequential by necessity (each task references the prior's artifact); ownership is provably disjoint.

### T1 — author the canonical contract  *(owns `protocol/reuse-claims.md`)*
- **action:** create `protocol/reuse-claims.md` containing LD3 verbatim as the contract, framed like the other
  `protocol/` cross-skill contracts (purpose · the guard · what counts as a verified vs phantom claim · the
  NEW-capability fallback). Name the producer skills (design-doc/plan/tdd) and that the guard is never tiered (LD1).
- **verify:** file exists; `validate_skills.py` still green (no skill broken).
- **acceptance:** the LD3 text is present verbatim; the file is a contract (no skill frontmatter).

### T2 — wire the pointers  *(owns the three skill files)*
- **read_first:** `protocol/reuse-claims.md` (T1), each target's current structure.
- **action:** add a short **pre-flight line** to `kata-design-doc/SKILL.md` (a precondition near "grounded in
  the code", §2/§5), a **quality-bar item** to `kata-plan/RUBRIC.md` (the invariant list), and a **worker
  note** to `kata-tdd/SKILL.md` (alongside "read the closest existing code analogs first") — each pointing to
  `protocol/reuse-claims.md` by path. No tier file changes (RUBRIC is inherited; LD1 never-tiered).
- **verify:** `validate_skills.py` green (36/0); each of the three files contains the path string.
- **acceptance:** all three pointers present and resolve to the real file; no `[[wikilink]]` used for the
  contract; no other skill content changed.

### T3 — the regression rule + test  *(owns `validate_skills.py` + a new test)*
- **read_first:** `tools/validate_skills.py` structure; `protocol/reuse-claims.md`.
- **action:** add a validator rule: the three LD4 skills MUST reference `protocol/reuse-claims.md`; missing →
  error (default-FAIL). Add `tools/tests/test_reuse_claims_guard.py` covering present-passes / removed-fails.
  Run `prove_non_vacuous` on the rule (code-bearing, LD6).
- **verify:** `cd tools && uv run pytest -q` (new tests pass) + `uv run python validate_skills.py` (36/0) +
  `.kata/mutation.json allNonVacuous:true`.
- **acceptance:** removing any one pointer makes the validator error (the test proves it); mutation proof present.

### Integration / proof-of-fire (orchestrator + human, not a worker task)
- Run **T-fire** (LD5): dispatch a fresh-context planning agent with a deliberate phantom-reuse claim; confirm
  the hardened design-doc pre-flight flags it / labels it NEW. Record the transcript verdict in
  `REPORT-phantom.md`. (Per L12 — prove the guard fires; don't just document it.)

## Acceptance criteria (phase-level, default-FAIL)
- `validate_skills.py` → **36 skills / 0 errors** (the new rule passes with pointers present).
- `pytest -q` → all pass incl. `test_reuse_claims_guard.py`; `.kata/mutation.json allNonVacuous:true`.
- Removing any LD4 pointer → validator **errors** (T-regression bites — demonstrated by the test).
- The T-fire probe: the hardened skill **flags a phantom reuse claim** (proof-of-fire, n=1).
- No unrelated skill/contract content changed; no `[[wikilink]]` used for the path reference.

## Sequencing (the recipe — HANDOFF §5)
freeze (this doc) → **freeze-gate `kata-review`** (fresh-context, HOLD/SHIP) → orchestrated build (T1→T2→T3,
Sonnet workers, worktrees) → integration gate (`gate_emit` + mutation) → **fresh-context `kata-evaluate`**
(default-FAIL, item 9 reproduce-don't-trust) → **standing D98 `kata-review`** (adversarial) → operator merge
gate → merge + push + checkpoint. Backout tag `pre-phantom-hardening`.

## Out of scope
- The full `recurrence-hardening` machinery (detector / `kata-improve` proposal loop / `kata-promote` gate) —
  this is the **manual first instance**; the spec's BRIEF drives the general build later.
- Rewriting the existing pervasive "composes/reuses" lines across the codebase — the guard applies to *future*
  claims; an audit-and-cite sweep of existing claims is a separate backlog item if wanted.
