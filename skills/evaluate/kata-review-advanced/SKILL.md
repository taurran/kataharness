---
name: kata-review-advanced
description: >-
  Exhaustive adversarial review with threat-model deep-dive and test-case generation. Use when maximum
  rigor is required — high-stakes decisions, security-sensitive surfaces, or any result where a Standard
  review found HOLDs and the re-reviewed surface still warrants deeper scrutiny.
license: Apache-2.0
version: 0.1.2
category: evaluate
status: beta
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Bash]
source: >-
  adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate)
tags:
  - kata/evaluate
  - kata/module/quality
  - kata/tier/advanced
  - adversarial
  - red-team
  - no-write
---
# kata-review-advanced — exhaustive adversarial review

**Method:** see [`../kata-review/RUBRIC.md`](../kata-review/RUBRIC.md) — the tier-invariant method (the numbered attack
surfaces, cite-evidence rule, SHIP/HOLD output, the "attack before you trust" framing). This file sets ONLY
the depth.

## Depth contract (Advanced)

Run the **full Standard method** (ALL surfaces, cited evidence, SHIP/HOLD) **plus**:

- **Threat-model deep-dive.** Go beyond surface-level security checks: enumerate the attacker's goal, build
  an explicit threat register (asset · threat actor · attack vector · mitigation · residual risk), and confirm
  each claimed mitigation is actually enforced in code — not just asserted in the plan.
- **Exhaustive second-order chase.** Trace every downstream consumer of the changed interface/behavior;
  enumerate cascading effects two hops out; flag any implicit coupling that the Standard pass leaves implicit.
- **Adversarial test-case generation.** For each gap found in the test adequacy surface, produce concrete
  failing-case specifications (input · expected behavior · why the current suite misses it) that a builder can
  translate directly into regression tests.

Findings list carries the same format (severity · attack · cited evidence · specific risk). Overall SHIP /
HOLD. HOLD findings are specific enough that the re-grill or fix target is unambiguous.
