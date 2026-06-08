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

---

## Output format

A findings list, each entry: **severity · the attack · cited evidence · the specific risk.**

Then an overall **SHIP / HOLD** recommendation.

HOLD findings route back to [[kata-orchestrate]] as a deliberate decision (re-grill the bad branch, tune a
constant, add coverage) — never an inline silent fix.
