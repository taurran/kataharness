---
name: kata-grill-essential
description: >-
  Fast, top-risk grill for a PoC/cheap one-shot. Pick this when speed matters more than exhaustiveness and
  the output does not need to be drift-proof — e.g., exploratory spikes, throwaway prototypes, or
  time-boxed pre-reads before a fuller grill.
license: Apache-2.0
version: 0.4.0
category: plan
status: beta
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Write, Edit]
source: >-
  adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model
tags:
  - kata/plan
  - kata/spine
  - kata/tier/essential
  - grilling
  - ddd
  - doc-baking
  - ubiquitous-language
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

**Convergence gate (non-waivable, D33).** After the top-risk branches are resolved, hand the decision
ledger to a **fresh-context [[kata-review]] (essential tier) scoped to the branches that were grilled**.
A SHIP from that pass closes the Essential grill; a HOLD names an under-specified branch to resolve before
closing. No tier self-certifies — Essential narrows the *tree* it grills, not the *backstop* that gates
it. The convergence gate is a structural invariant; a tier may reduce depth but may NOT drop it. On SHIP,
run the RUBRIC's **ELEVATE step** (D153 — exactly ONE grounded recommendation, posed as a single question;
outcome recorded as an `EV-{n} · LOCKED` ledger entry; same behavior at every tier — Essential narrows the
tree, never the close-out), then the **grill-close emit** (the `tools/learn_feed.py` second-brain feed —
no-op when `engram.learnFeed.dir` is unset; never blocks the close).

**Interaction (D153/U1):** every grill question — ELEVATE included — goes out ONE at a time (Claude adapter:
one `AskUserQuestion` call, exactly one question); never a multi-question dump.

## Convergence-pass record — the gate's precondition (trust-model DESIGN §3.3)

The convergence gate above is a **dispatch-gated** surface: the scoped fresh-context pass is a launch of
*another agent*, so it is minted through the seam (`kata_dispatch.mint(governs=…, role=…, task_id=…)`) before
it runs and its SHIP/HOLD is read back through `kata_dispatch.capture` from the **persisted** record — never
from a conversational value the griller remembers. That record pair (the dispatch record + its captured
VERDICT) IS the **convergence-pass record**, and the gate's precondition is its presence:

> **Grill convergence** | **convergence-pass record** — incl. proof the Advanced double-pass ran as two
> distinct dispatches, via seam records | **convergence-pass record**

Essential runs ONE scoped pass, so its record is one dispatch + one captured VERDICT (the two-distinct-
dispatches clause binds the Advanced double-pass; it is quoted whole here because the record requirement it
sits inside is the same one, non-waivable at every tier). **Essential narrows the tree it grills, never the
record that proves the backstop ran** — a convergence asserted with no record does not close the grill (PD-2:
done requires proof, not assertion).

**Honest residual (PD-2), stated rather than papered over:** the convergence-reviewer *function* has no role
token of its own, and the tokens a reviewer dispatches under today (`reviewer` / `critic` / `challenger`)
carry **no grill-phase ledger rung** — `tools/kata_dispatch.py:458-468` says so in the code and names the
judge-contract wave as the owner of that assignment. Until it lands, mint the convergence pass under the rung
its actual role token carries and let a refusal park the task; never widen a rung to make a dispatch fit.

## The grill-close status write — `converged`, and only here

On the close, write the ledger's frontmatter `status: converged` (shape:
[`../kata-grill/resources/DECISION-LEDGER.md`](../kata-grill/resources/DECISION-LEDGER.md)) — an Essential
grill that reached SHIP is `converged`, with the partial-tree coverage noted in the ledger body as this tier
already requires. Two binding properties:

- **`converged` is written ONLY by this grill-close act**, after the convergence SHIP. Nothing else in the
  harness writes that value.
- **The status write is INDEPENDENT of the grill-close emit above.** A blocked, skipped, or failed
  `learn_feed` emit never blocks it — the emit is best-effort and never blocks the close, so letting it gate
  the status would leave a converged grill recorded as `draft` and silently deny every mint governed by it.

The value is read mechanically by the `ledger` governor rung (`kata_dispatch.ledger_status`): the enum is the
closed four-value `draft | converged | frozen | absorbed`, parsed **first word only** (so
`status: converged — 2026-08-16, essential tier …` is legal and reads as `converged`), and **fail-closed** —
an absent or empty `status:` reads `absent` and satisfies nothing, and an unrecognized first word RAISES
rather than being coerced to a default in either direction.

**This tier does NOT replace a Standard grill before a production freeze.** Use it when a PoC or one-shot
outcome is acceptable and the user has explicitly accepted the reduced coverage.
