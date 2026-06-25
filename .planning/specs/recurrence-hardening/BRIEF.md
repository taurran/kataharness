---
title: "Recurrence hardening — the harness hardens its own agents from repeated failure-classes (pre-grill BRIEF)"
status: BRIEF (pre-grill, NOT frozen)
date: 2026-06-24
spec: recurrence-hardening
decision: D101
relates-to: D99 (the C-arc / Reason — this is its harness-facing sibling) · D98/L12 (fold lessons into skills) · D74 (β LEARN feed)
tags:
  - kata/meta
  - improve
  - self-hardening
  - learning
---

# Recurrence hardening — when a failure-class recurs, harden the responsible agent

> **Pre-grill brief, not frozen.** Captures the operator directive (2026-06-24): *"We need to fix these
> repeated issues in our execution / coding / planning agents. When it happens over and over we need to harden
> the tool. That's how learning should work — I feel like it should be doing this."* Working name; rename later.

## Why
The harness's own agents (planner, coder, evaluator) hit **recurring failure-classes**. This session alone, the
adversarial lens caught the **same class three times** — planning/spec agents **over-claiming that machinery
exists** ("composes existing primitives / reuses X" when the primitive doesn't expose the needed surface; the
project's signature documentation-only-seam). Today the fix is **human-driven and per-instance**: a human
notices the pattern and (maybe) writes a lesson or a memory. **That is not learning — it is repeated manual
patching.** The Improvement-Kata thesis ("every run improves the harness") demands the *loop* recognize a
recurring class and **fold a permanent guard into the responsible agent** — automatically detected,
deliberately gated.

This is the **harness-facing sibling of Reason/C (D99)**: Reason learns the *user's* decisions from a second
brain; recurrence-hardening learns the *harness's* failure patterns from its own run history. **Same gates,
same C/B invariant.**

## The shape (composes existing pieces — verified before claiming, per the standing memory)
1. **Corpus (exists).** The β LEARN feed (D74) already mines `DECISIONS`/`LESSONS`/`REVIEW` findings → emit-only
   synthesis. The `kata-evaluate` / `kata-review` findings per run are the raw signal.
2. **Recurrence detector (NEW).** A pass that **clusters findings by (responsible-skill × failure-class)** across
   runs and flags a class that crosses a threshold (e.g. ≥3 occurrences) — "the planner over-claimed reuse 3×."
3. **Hardening proposal (extends `kata-improve`).** For a flagged class, `kata-improve` proposes a **permanent
   guard in the responsible skill** — a pre-flight check / checklist item / rubric item (e.g. *"before writing
   'reuses X', grep/read to confirm X exposes the needed surface"* → a `kata-plan`/`kata-design-doc` pre-flight).
4. **Gate (reuses `kata-promote` pattern + D98).** The proposed skill-hardening is **fresh-context reviewed
   (no-self-cert) AND human-approved** before it modifies the skill. **Never an auto-mutation** (that is the
   B-trap — a loop rewriting its own skills ungated). The C/B invariant holds: a hardening is a **deliberate,
   frozen, gated, audited skill change.**

## The first concrete instance (already in hand)
The recurring class caught 3× this session — *spec/planning agents over-claim that machinery exists* — should
become the **first hardening**: a `kata-plan`/`kata-design-doc` pre-flight that requires verifying a primitive
exposes the needed surface before claiming reuse (now also the memory `verify-primitives-before-claiming-reuse`).
This is the worked example the spec should drive to.

## Open questions for the grill
- **The recurrence threshold + the "failure-class" taxonomy** — how is a class defined/clustered (by reviewer
  finding-type? by responsible skill? both)? what N triggers? (provisional, calibrate via dogfood — like the
  fix-loop N=2).
- **"Responsible agent" attribution** — how does a finding map to the skill that should be hardened (planner vs
  coder vs evaluator)? Is it in the finding metadata, or inferred?
- **Where the guard lands** — a skill's pre-flight section, its RUBRIC, the worker-dispatch prompt, or `AGENTS.md`?
  (Probably skill-specific; the proposal names the target.)
- **Corpus availability** — this needs run-history (the β feed). Like the C-arc, it is **weak until the corpus
  matures**; early on it should no-op gracefully (too few occurrences to cluster).
- **Relation to the C-arc** — is this a *mode* of the same machinery (shares the readiness/gating with Reason),
  or its own track? (Lean: shares the gates + the corpus; distinct trigger + target.)

## Scope / sequencing
- **Extends:** `kata-improve` (IMPROVE phase) + the β feed (D74) + the `kata-promote` gate pattern.
- **Gated exactly like the C-arc:** detect → propose → fresh-context review + human-approve → apply. Never auto.
- **Sequencing:** its own grill → freeze → freeze-gate review → build (the discipline that paid off 3× this
  session). **Not** bundled into any other frozen build. Naturally pairs with the C-arc (D99) and the
  `kata-loop-benchmark` keystone (a hardening's value is measurable: did it reduce that class's recurrence?).

## Out of scope
- Auto-mutating skills without the human gate (the B-trap — explicitly forbidden).
- Hardening from a single occurrence (that is just the normal per-run targeted fix; recurrence = ≥ threshold).
