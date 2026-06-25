# kata-review — shared method (RUBRIC)

The tier-invariant review method. The `kata-review-<tier>` skills set only depth; they all obey this.

---

## Purpose

`kata-review` asks the harder question: *"is what we specified actually right, and where will it break?"*
(adversarial). It complements [[kata-evaluate]] (which asks *"did we build what we specified?"* — conformance).
The two are distinct legs of the EVALUATE phase — conformance can pass while the design is wrong. This skill
exists because a run can be 0-drift, all-green, and still ship a bad decision ([[LESSONS-LEARNED]] L6, L10:
**neither A/B arm got adversarial validation — that gap is what this fills**).

Run from a **fresh context, read-only** (no Write/Edit — structural, per [[STANDARDS]] §1). You produce
findings, not fixes; findings seed a deliberate orchestrator decision.

---

## Attack surfaces (hunt each; cite evidence)

1. **Decision judgment.** Challenge the LOCKED decisions on merit, not conformance. Especially the
   drift-magnets: **classification/boundary calls** (is each bucket *defensible*, or did a borderline case get
   filed wrong?) and **magnitude/constants** (is the value sane, or violent / double-counted with an existing
   factor?). Argue the rejected alternative back.
2. **Test adequacy.** What behavior is NOT covered? Endpoints tested but the meaningful middle range ignored?
   Monotonicity, boundary/clamping, all-one-category, renormalization sign-flips, interaction with existing
   factors. A passing suite written by the builder has the builder's blind spots.
3. **Assumptions & contradictions.** Surface assumptions the spec rests on; check them against code/docs/data.
   Flag anything that contradicts a prior decision, the glossary, or reality.
4. **Security & failure surface.** Attacker-reachable inputs, escaping, and what happens on malformed/edge
   input. Confirm threats in the plan's model are actually mitigated, not just claimed.
5. **Second-order effects.** What does this change *downstream* that no one looked at?
6. **Reproduction & seam-liveness (L12 — the signature failure mode).** Do not trust that a thing *exists*
   because a doc says so. (a) **Derived artifacts:** for anything the run *computed or rendered* (a board-derived
   `concurrency.json`, a token-filled report, a generated manifest), **regenerate it from its stated source and
   diff** — a presented copy that disagrees with the freshly-reproduced one was hand-massaged (a real defect this
   surface caught on WS-2). (b) **Claimed seams (documentation-only-seam hunt):** for any wiring the build asserts
   ("the orchestrator runs X", "the gate emits Y"), **execute the seam once** against real inputs — confirm it
   actually fires in a real run, not just that the prose describes it. This is the conformance gate's structural
   blind spot ([[kata-evaluate]] grades the artifact *as presented*); this surface attacks the gap.

## Injected-knowledge soundness mode (the grounding gate's adversarial leg — RS findings / ML candidates; D33)
When invoked on **injected knowledge** rather than a built phase, run this surface as the adversarial half of the
**grounding gate** (the conformance/drift half is [[kata-evaluate]]'s injected-knowledge mode). **This surface is
NOT tiered** — when grading injected knowledge it runs at full depth regardless of the review tier (D33: the
gate is never tiered, never bypassed). Attack each [[kata-research]] finding (or ML candidate):
- **Source authority & hallucination.** Is the cited `source` real, authoritative, and current — or a
  low-quality / stale / fabricated citation? Open it; a source that does not say what the claim asserts is the
  primary kill.
- **Confidence calibration.** Is `confidence: HIGH` actually warranted, or optimism? Argue the finding is wrong.
- **Plan-fit honesty.** Does `grounds-to-plan?: YES` hide a LOCKED-decision tension the researcher glossed?
A finding that fails here is **HOLD** (→ REJECT or ESCALATE at the gate), never folded into the build.

---

## Output format

A findings list, each entry: **severity · the attack · cited evidence · the specific risk.**

Then an overall **SHIP / HOLD** recommendation.

HOLD findings route back to [[kata-orchestrate]] as a deliberate decision (re-grill the bad branch, tune a
constant, add coverage) — never an inline silent fix.
