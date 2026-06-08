---
name: kata-grill-essential
description: >-
  Fast, top-risk grill for a PoC/cheap one-shot. Pick this when speed matters more than exhaustiveness and
  the output does not need to be drift-proof — e.g., exploratory spikes, throwaway prototypes, or
  time-boxed pre-reads before a fuller grill.
license: Apache-2.0
version: 0.1.0
category: plan
status: experimental
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Write, Edit]
model: opus
source: >-
  adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model
tags:
  - kata/plan
  - kata/spine
  - kata/tier/essential
  - grilling
  - ddd
  - doc-baking
---
# kata-grill-essential — fast top-risk grill

**Method:** see [`../kata-grill/RUBRIC.md`](../kata-grill/RUBRIC.md) — the tier-invariant method (interaction
format, doc-baking, the quality principles, the convergence/output definition). This file sets ONLY the depth.

## Depth contract (Essential)

Run **ONE focused pass** over only the **highest-risk / drift-magnet branches**: classification boundaries,
magnitude/threshold choices, interface contracts, and failure behavior. Resolve from docs/code aggressively —
do not ask the user what you can discover yourself.

**Doc-baking:** bake the **decision ledger** only (skip ADRs and glossary polish unless a term is actively
ambiguous and causing confusion in this session).

**Stop** when the top-risk branches are resolved with no contradiction. Do NOT enumerate the full decision
tree — that is Standard's job. Explicitly note in the ledger that this was an Essential-tier grill (partial
tree, top-risk only) so downstream consumers know the coverage.

**This tier does NOT replace a Standard grill before a production freeze.** Use it when a PoC or one-shot
outcome is acceptable and the user has explicitly accepted the reduced coverage.
