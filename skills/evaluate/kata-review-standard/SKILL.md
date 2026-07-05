---
name: kata-review-standard
description: >-
  Full 5-surface adversarial review (default). Use after kata-evaluate passes, before trusting a result,
  to red-team the spec's judgment, hunt missing test coverage, and probe the security and failure surface.
license: Apache-2.0
version: 0.1.2
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

**Method:** see [`../kata-review/RUBRIC.md`](../kata-review/RUBRIC.md) — the tier-invariant method (the numbered attack
surfaces, cite-evidence rule, SHIP/HOLD output, the "attack before you trust" framing). This file sets ONLY
the depth.

## Depth contract (Standard)

Run **ALL** attack surfaces exactly as defined in `../kata-review/RUBRIC.md` — full coverage, no
surface skipped. The RUBRIC is the single source of truth for what each surface means, the cite-evidence
rule, and the SHIP / HOLD output format. This tier does not narrow the surface set; it runs the complete
adversarial pass at original depth.

This is today's `kata-review` at its original depth — the default for any non-trivial adversarial pass.
