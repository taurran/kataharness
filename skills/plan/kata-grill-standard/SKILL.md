---
name: kata-grill-standard
description: >-
  Full doc-grounded grill (default). Use this for any non-trivial build, feature, or change where the
  output must be drift-proof — the standard production-quality grill that resolves the entire decision tree.
license: Apache-2.0
version: 0.2.0
category: plan
status: beta
agnostic: true
cost-weight: 4
allowed-tools: [Read, Grep, Glob, Write, Edit]
source: >-
  adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model
tags:
  - kata/plan
  - kata/spine
  - kata/tier/standard
  - grilling
  - ddd
  - doc-baking
  - ubiquitous-language
---
# kata-grill-standard — full doc-grounded grill (default)

**Method:** see [`../kata-grill/RUBRIC.md`](../kata-grill/RUBRIC.md) — the tier-invariant method (interaction
format, doc-baking, the quality principles, the convergence/output definition). This file sets ONLY the depth.

## Depth contract (Standard)

Run the **full method** as defined in the RUBRIC:

- Enumerate the **whole decision tree** in Phase 0 — every branch the spec leaves open, dependency-ordered.
- Multi-round interrogation through Phase 1: probe each branch, stress-test with concrete scenarios, sharpen
  all fuzzy terms, cross-reference code/docs, and re-derive the tree after each resolution.
- **Full doc-baking:** glossary updates (`CONTEXT.md`), ADRs where warranted (hard-to-reverse + surprising +
  real trade-off), and the decision ledger updated at every checkpoint.
- Run the **fresh-context convergence gate** ([[kata-review]], "could two independent builders still diverge?"
  mode) before declaring the grill done. Only a SHIP from that pass closes the grill; a HOLD sends it back to
  Phase 1. On SHIP, run the RUBRIC's **grill-close emit** (the `tools/learn_feed.py` second-brain feed —
  no-op when `engram.learnFeed.dir` is unset; never blocks the close).

This is today's `kata-grill` at its original depth — the default for any production-quality planning session.
