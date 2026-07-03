---
name: kata-review-essential
description: >-
  Smell-test review for the highest-risk surfaces only. Pick this for a fast sanity check on a PoC or
  cheap one-shot where exhaustive adversarial coverage is not required — e.g., early drafts, time-boxed
  spikes, or when a full adversarial pass is planned later.
license: Apache-2.0
version: 0.1.1
category: evaluate
status: experimental
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Bash]
source: >-
  adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate)
tags:
  - kata/evaluate
  - kata/module/quality
  - kata/tier/essential
  - adversarial
  - red-team
  - no-write
---
# kata-review-essential — smell-test (top-risk surfaces only)

**Method:** see [`../kata-review/RUBRIC.md`](../kata-review/RUBRIC.md) — the tier-invariant method (the numbered attack
surfaces, cite-evidence rule, SHIP/HOLD output, the "attack before you trust" framing). This file sets ONLY
the depth.

## Depth contract (Essential)

Run a **smell-test** over the **two highest-risk surfaces only**:

- **Decision judgment** — challenge the drift-magnets (classification/boundary calls and magnitude/constants).
  Is each LOCKED decision defensible, or did a borderline case get filed wrong?
- **Test adequacy gaps** — the most obvious missing coverage: untested boundary behavior, all-one-category
  inputs, or the meaningful middle range the builder's suite skips.

Cite evidence for every finding. Produce a SHIP / HOLD.

**What this tier deliberately skips:** assumptions/contradictions audit, security/failure surface deep-dive,
and second-order effects chase. Note in the output that this was an Essential-tier review (partial surface
coverage) so downstream consumers know the scope.

**This tier does NOT replace a Standard review before a production decision.** Use it when a PoC or early
draft is the context and the user has explicitly accepted reduced coverage.
