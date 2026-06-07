---
name: kata-grill
description: >-
  Relentless, doc-grounded interrogation that resolves EVERY decision branch a spec leaves open, before any
  freeze. Use at the start of any non-trivial build/feature/change to turn a fuzzy ask into a very specific,
  drift-proof design contract. Explores code/docs to answer instead of asking; poses structured
  choice-or-free-text questions with a recommendation each; stress-tests with concrete scenarios; sharpens
  terminology; and bakes resolved decisions into a glossary, ADRs, and a decision ledger as it goes.
version: 0.1.0
category: plan
status: experimental
agnostic: true
allowed-tools: [Read, Grep, Glob, Write, Edit]
model: opus
source: >-
  adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model
tags: [plan, grilling, ddd, doc-baking, ubiquitous-language]
---

# kata-grill — interrogate every branch until the design is specific enough that execution cannot drift

The grill is the harness's highest-leverage phase: a frozen plan is only as good as the interrogation that
produced it. The goal is **a very specific design contract** — specific enough that downstream execution has
no room to re-decide (that is what makes [[kata-orchestrate]]'s no-drift line *possible*).

## The anti-pattern this skill exists to prevent (read first)
**A one-pass list of "here are N decisions, each with my recommendation" is NOT a grill — it is a survey.**
It pre-answers for the user, stops at the first plausible option, and never stress-tests. (This is the exact
failure recorded in [[LESSONS-LEARNED]] L8/L9 from the Wizard-of-Oz run.) A real grill is **iterative,
demanding, and adversarial to ambiguity**: it walks the decision tree branch by branch, re-deriving the tree
after each answer, and does not stop until the convergence criteria below are met.

## Interaction format (the GSD-style binding — L7/L8)
Ask **structured questions the user can either click an option for OR answer in free text.** Every question:
- offers 2–4 concrete options, **recommendation first** and labeled, each with its trade-off in one line;
- **always allows a free-text answer** — never a no-escape constrained picker (that is what [[LESSONS-LEARNED]]
  L7 forbids; offering options *with* an escape is encouraged, not banned);
- states the provenance: what in the spec/code/docs raised this branch.
Group tightly-related questions together, but resolve **dependent** branches in sequence (an answer routinely
opens or closes downstream branches). *(Adapter binding: Claude → `AskUserQuestion`; a plain CLI → numbered
options + a free-text prompt. The pattern is host-agnostic; the rendering is the adapter's job.)*

## Phase 0 — Ground before you ask
1. Read the spec / source docs in full, plus any existing `CONTEXT.md` / `CONTEXT-MAP.md`, ADRs
   (`docs/adr/` or the project's decision log), and the relevant code.
2. **Build the decision tree:** enumerate EVERY branch the spec leaves open or under-specified — data shape,
   classification/boundary calls, algorithm/magnitude choices, interface contracts, failure behavior,
   backward-compat, security surface. Missing branches are how vague specs ship bugs.
3. **Answer from the docs/code whatever you can** — if a question is resolvable by exploration, resolve it
   yourself and record it; do NOT spend the user's attention on what you can discover.

## Phase 1 — Interrogate, dependency-ordered
For each still-open branch, in dependency order, run the loop:
- **Pose** the choice-or-text question (format above) with your recommendation + rationale.
- **Probe — don't accept the first plausible answer.** Push on second-order consequences, the failure mode,
  and "what would break this?" A branch is not resolved until its *edges* are defined.
- **Stress-test with concrete scenarios.** Invent specific cases that force precise boundaries ("what does
  the system do when X and Y at once?"). Vague relationships hide here.
- **Sharpen language.** Any fuzzy/overloaded term → propose the one canonical word; the rest go under
  `_Avoid_` in the glossary. Challenge terms that conflict with the existing `CONTEXT.md`.
- **Cross-reference code/docs.** If the user's statement contradicts the code or a prior decision, surface it
  immediately and resolve which is right.
- **Re-derive the tree.** After each resolution, recompute what is now open/closed before the next question.

## Doc-baking — inline, not batched ([[STANDARDS]] §5; formats from grill-with-docs)
As each branch resolves, capture it *then and there*:
- **Glossary** (`CONTEXT.md`, glossary-only — no implementation): one tight definition per resolved term,
  with `_Avoid_:` synonyms. Create the file lazily on the first resolved term. (See `kata-context`.)
- **ADR** — offer one ONLY when all three hold: hard to reverse · surprising without context · the result of
  a real trade-off. Otherwise skip it. Sequential `docs/adr/NNNN-slug.md`, 1–3 sentences.
- **Decision ledger** — append every resolved branch (chosen option, rejected alternatives, rationale,
  provenance) to the running ledger. This is the raw material the FREEZE phase ([[kata-design-doc]]) compiles
  into the contract. See `resources/DECISION-LEDGER.md`.

## Convergence criteria — the grill is DONE only when ALL hold
- [ ] Every enumerated branch is resolved with a chosen option + rationale (none left "TBD").
- [ ] No fuzzy/overloaded terms remain; the glossary is canonical for this work.
- [ ] Every probed scenario / edge case has a defined behavior.
- [ ] No unresolved contradiction with the code, the glossary, or prior ADRs.
- [ ] The design is specific enough that a competent executor could not *reasonably* drift on it
      (the operational test: could two independent builders read this and diverge? If yes, keep grilling).

If any box is unchecked, you are not done — return to Phase 1. Stopping early is the failure mode.

## Handoff to FREEZE
Output = the **decision ledger** + the updated **glossary** + any **ADRs**. These are consumed by
[[kata-design-doc]] and [[kata-plan]] to produce the frozen DESIGN + PLAN. The grill never freezes the plan
itself — it makes freezing *safe*.
