---
name: kata-grill-advanced
description: >-
  Exhaustive, adversarial grill for max-rigor results. Use when the cost of a missed branch is very high —
  e.g., security-critical systems, public APIs with long backward-compat horizons, or architectures that
  are genuinely hard to reverse.
license: Apache-2.0
version: 0.4.0
category: plan
status: beta
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
  Advanced. Both must return SHIP before the grill is complete. On the final SHIP, run the RUBRIC's
  **ELEVATE step** (D153 — exactly ONE grounded recommendation, posed as a single question; outcome recorded
  as an `EV-{n} · LOCKED` ledger entry; an acceptance that opens new branches gets a SCOPED one-pass-per-
  attempt re-check, not a repeat of the double gate), then the **grill-close emit** (the `tools/learn_feed.py`
  second-brain feed — no-op when `engram.learnFeed.dir` is unset; never blocks the close).
- **Interaction (D153/U1):** every grill question — ELEVATE included — goes out ONE at a time (Claude adapter:
  one `AskUserQuestion` call, exactly one question); never a multi-question dump.

## Convergence-pass record — TWO DISTINCT DISPATCHES, proved (trust-model DESIGN §3.3)

The convergence gate is a **dispatch-gated** surface: each fresh-context pass is a launch of *another agent*,
so each is minted through the seam (`kata_dispatch.mint(governs=…, role=…, task_id=…)`) before it runs and
each verdict is read back through `kata_dispatch.capture` from the **persisted** record — never from a
conversational value the griller remembers. The gate's precondition, verbatim:

> **Grill convergence** | **convergence-pass record** — incl. proof the Advanced double-pass ran as two
> distinct dispatches, via seam records | **convergence-pass record**

For this tier that is the whole point of the record: **"fresh context between passes" is a claim a machine
must be able to check, and the check is TWO DISTINCT DISPATCH RECORDS with two distinct `recordId`s and two
separately captured VERDICTs** — one for the main decision-tree pass, one for the security/edge-case pass.
One dispatch that returns two verdicts is **not** a double pass; re-reading the same context twice is **not**
a double pass; a second verdict with no second record is unproven and does not close the grill (PD-2: done
requires proof, not assertion). The scoped re-check an ELEVATE acceptance triggers is its own dispatch and
its own record, one pass per attempt.

**Honest residual (PD-2), stated rather than papered over:** the convergence-reviewer *function* has no role
token of its own, and the tokens a reviewer dispatches under today (`reviewer` / `critic` / `challenger`)
carry **no grill-phase ledger rung** — `tools/kata_dispatch.py:458-468` says so in the code and names the
judge-contract wave as the owner of that assignment. Until it lands, mint each pass under the rung its actual
role token carries and let a refusal park the task; never widen a rung to make a dispatch fit.

## The grill-close status write — `converged`, and only here

On the final SHIP, write the ledger's frontmatter `status: converged` (shape:
[`../kata-grill/resources/DECISION-LEDGER.md`](../kata-grill/resources/DECISION-LEDGER.md)). Two binding
properties:

- **`converged` is written ONLY by this grill-close act**, after the final convergence SHIP — for Advanced,
  after the SECOND pass ships, never after the first. Nothing else in the harness writes that value.
- **The status write is INDEPENDENT of the grill-close emit above.** A blocked, skipped, or failed
  `learn_feed` emit never blocks it — the emit is best-effort and never blocks the close, so letting it gate
  the status would leave a converged grill recorded as `draft` and silently deny every mint governed by it.

The value is read mechanically by the `ledger` governor rung (`kata_dispatch.ledger_status`): the enum is the
closed four-value `draft | converged | frozen | absorbed`, parsed **first word only** (so
`status: converged — 2026-08-16, pass 1 SHIP … · pass 2 SHIP …` is legal and reads as `converged`), and
**fail-closed** — an absent or empty `status:` reads `absent` and satisfies nothing, and an unrecognized
first word RAISES rather than being coerced to a default in either direction.

The Advanced tier is strictly a superset of Standard — it produces the same artifact types (ledger + glossary
+ ADRs) but with higher coverage, deeper adversarial probing, and the double convergence gate.
