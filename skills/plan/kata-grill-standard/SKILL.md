---
name: kata-grill-standard
description: >-
  Full doc-grounded grill (default). Use this for any non-trivial build, feature, or change where the
  output must be drift-proof — the standard production-quality grill that resolves the entire decision tree.
license: Apache-2.0
version: 0.4.0
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
  Phase 1. On SHIP, run the RUBRIC's **ELEVATE step** (D153 — exactly ONE grounded recommendation, posed as a
  single question; outcome recorded as an `EV-{n} · LOCKED` ledger entry), then the **grill-close emit** (the
  `tools/learn_feed.py` second-brain feed — no-op when `engram.learnFeed.dir` is unset; never blocks the
  close).
- **Interaction (D153/U1):** every grill question — ELEVATE included — goes out ONE at a time (Claude adapter:
  one `AskUserQuestion` call, exactly one question); never a multi-question dump.

## Convergence-pass record — the gate's precondition (trust-model DESIGN §3.3)

The convergence gate is a **dispatch-gated** surface: the fresh-context pass is a launch of *another agent*,
so it is minted through the seam (`kata_dispatch.mint(governs=…, role=…, task_id=…)`) before it runs and its
SHIP/HOLD is read back through `kata_dispatch.capture` from the **persisted** record — never from a
conversational value the griller remembers. That record pair (the dispatch record + its captured VERDICT) IS
the **convergence-pass record**, and the gate's precondition is its presence:

> **Grill convergence** | **convergence-pass record** — incl. proof the Advanced double-pass ran as two
> distinct dispatches, via seam records | **convergence-pass record**

Standard runs ONE pass, so its record is one dispatch + one captured VERDICT. A convergence asserted with no
record does not close the grill (PD-2: done requires proof, not assertion).

**Honest residual (PD-2), stated rather than papered over:** the convergence-reviewer *function* has no role
token of its own, and the tokens a reviewer dispatches under today (`reviewer` / `critic` / `challenger`)
carry **no grill-phase ledger rung** — `tools/kata_dispatch.py:458-468` says so in the code and names the
judge-contract wave as the owner of that assignment. Until it lands, mint the convergence pass under the rung
its actual role token carries and let a refusal park the task; never widen a rung to make a dispatch fit.

## The grill-close status write — `converged`, and only here

On the close, write the ledger's frontmatter `status: converged` (shape:
[`../kata-grill/resources/DECISION-LEDGER.md`](../kata-grill/resources/DECISION-LEDGER.md)). Two binding
properties:

- **`converged` is written ONLY by this grill-close act**, after the final convergence SHIP. Nothing else in
  the harness writes that value.
- **The status write is INDEPENDENT of the grill-close emit above.** A blocked, skipped, or failed
  `learn_feed` emit never blocks it — the emit is best-effort and never blocks the close, so letting it gate
  the status would leave a converged grill recorded as `draft` and silently deny every mint governed by it.

The value is read mechanically by the `ledger` governor rung (`kata_dispatch.ledger_status`): the enum is the
closed four-value `draft | converged | frozen | absorbed`, parsed **first word only** (so
`status: converged — 2026-08-16, pass 1 SHIP …` is legal and reads as `converged`), and **fail-closed** — an
absent or empty `status:` reads `absent` and satisfies nothing, and an unrecognized first word RAISES rather
than being coerced to a default in either direction.

This is today's `kata-grill` at its original depth — the default for any production-quality planning session.
