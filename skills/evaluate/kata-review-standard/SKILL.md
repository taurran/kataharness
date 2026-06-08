---
name: kata-review-standard
description: >-
  Full 5-surface adversarial review (default). Use after kata-evaluate passes, before trusting a result,
  to red-team the spec's judgment, hunt missing test coverage, and probe the security and failure surface.
license: Apache-2.0
version: 0.1.0
category: evaluate
status: experimental
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Bash]
source: >-
  adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate)
tags:
  - kata/evaluate
  - kata/module/quality
  - kata/tier/standard
  - adversarial
  - red-team
  - no-write
---
# kata-review-standard — full 5-surface adversarial review (default)

**Method:** see [`../kata-review/RUBRIC.md`](../kata-review/RUBRIC.md) — the tier-invariant method (5 attack
surfaces, cite-evidence rule, SHIP/HOLD output, the "attack before you trust" framing). This file sets ONLY
the depth.

## Depth contract (Standard)

Run the **full method** as defined in the RUBRIC — all five attack surfaces, each with cited evidence:

1. **Decision judgment** — challenge every LOCKED decision on merit; argue the rejected alternative back.
2. **Test adequacy** — enumerate behaviors NOT covered; probe boundary/clamping, monotonicity,
   all-one-category, renormalization sign-flips, and interaction effects.
3. **Assumptions & contradictions** — surface spec assumptions; check them against code/docs/data; flag
   anything contradicting a prior decision, the glossary, or reality.
4. **Security & failure surface** — attacker-reachable inputs, escaping, malformed/edge input behavior;
   confirm plan-model threats are actually mitigated.
5. **Second-order effects** — what does this change downstream that no one looked at?

Produce a findings list (severity · attack · cited evidence · specific risk) and an overall SHIP / HOLD.

This is today's `kata-review` at its original depth — the default for any non-trivial adversarial pass.
