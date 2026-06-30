---
name: kata-grill-advanced
description: >-
  Exhaustive, adversarial grill for max-rigor results. Use when the cost of a missed branch is very high —
  e.g., security-critical systems, public APIs with long backward-compat horizons, or architectures that
  are genuinely hard to reverse.
license: Apache-2.0
version: 0.1.0
category: plan
status: experimental
agnostic: true
cost-weight: 5
allowed-tools: [Read, Grep, Glob, Write, Edit]
source: >-
  adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model
tags:
  - kata/plan
  - kata/spine
  - kata/tier/advanced
  - grilling
  - ddd
  - doc-baking
  - ubiquitous-language
---
# kata-grill-advanced — exhaustive adversarial grill

**Method:** see [`../kata-grill/RUBRIC.md`](../kata-grill/RUBRIC.md) — the tier-invariant method (interaction
format, doc-baking, the quality principles, the convergence/output definition). This file sets ONLY the depth.

## Depth contract (Advanced)

Run the **full Standard-depth method (see the RUBRIC)** **plus**:

- **Re-derive the decision tree after each resolution, to exhaustion.** Do not batch or skip re-derivation
  steps: every resolved branch may unlock new branches, and Advanced does not stop until the re-derived tree
  is empty.
- **Exhaustive edge-case scenarios.** Generate scenarios that cover not just the obvious boundaries but
  combinatorial edge cases, degraded-mode behavior, and race/timing conditions where applicable.
- **Second-order effects + security surface.** Probe the security surface deeply: authentication/authorization
  boundaries, data-trust boundaries, injection surfaces, and failure-mode escalation paths. Surface any
  second-order effects (downstream systems, dependent services, data at rest/transit).
- **Two fresh-context convergence passes.** Run [[kata-review]] twice with a fresh context between passes.
  The first pass gates the main decision tree; the second pass gates the security/edge-case layer added by
  Advanced. Both must return SHIP before the grill is complete.

The Advanced tier is strictly a superset of Standard — it produces the same artifact types (ledger + glossary
+ ADRs) but with higher coverage, deeper adversarial probing, and the double convergence gate.
