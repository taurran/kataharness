---
name: kata-grill-essential
description: >-
  Fast, top-risk grill for a PoC/cheap one-shot. Pick this when speed matters more than exhaustiveness and
  the output does not need to be drift-proof — e.g., exploratory spikes, throwaway prototypes, or
  time-boxed pre-reads before a fuller grill.
license: Apache-2.0
version: 0.3.0
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

**This tier does NOT replace a Standard grill before a production freeze.** Use it when a PoC or one-shot
outcome is acceptable and the user has explicitly accepted the reduced coverage.
