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
   input. Confirm threats in the plan's model are actually mitigated, not just claimed. **Hunt the
   silent-permissive-default class (D136):** any decision-bearing function that reads/parses an external
   artifact to drive a dispatch set / resolver output / gate verdict and, on ABSENT or UNPARSEABLE input, falls
   through to a permissive default (empty set, `None`-inherit, vacuous-pass) instead of hard-failing — the
   lenient-direction failure that passes happy-path tests. Confirm such functions RAISE and that the required
   absent/malformed-input test exists (kata-tdd D136). A legitimately empty COMPUTED result and a designed,
   documented fail-safe fallback are NOT findings — the target is accidental silent-permissive defaults.
5. **Second-order effects.** What does this change *downstream* that no one looked at?
6. **Reproduction & seam-liveness (L12 — the signature failure mode).** Do not trust that a thing *exists*
   because a doc says so. (a) **Derived artifacts:** for anything the run *computed or rendered* (a board-derived
   `concurrency.json`, a token-filled report, a generated manifest), **regenerate it from its stated source and
   diff** — a presented copy that disagrees with the freshly-reproduced one was hand-massaged (a real defect this
   surface caught on WS-2). (b) **Claimed seams (documentation-only-seam hunt):** for any wiring the build asserts
   ("the orchestrator runs X", "the gate emits Y"), trace the **WHOLE orchestrated flow** once on a realistic
   fixture (not a single isolated seam) — assert every PRODUCED surface is CONSUMED and every CONSUMED surface
   is PRODUCED. A produced-but-unconsumed or consumed-but-unproduced seam is **HOLD**. (Scope: code-bearing
   wiring — greppable producer→consumer handoffs; prose-orchestrated LLM seams are out of scope here.) This is
   the conformance gate's structural blind spot ([[kata-evaluate]] grades the artifact *as presented*); this
   surface attacks the gap. Mirrors `kata-evaluate` item 9; pointer to the scheduled wiring-completeness-gate
   build (see BACKLOG).

   > **Caveat (no-write fresh-context grade limit):** a no-write grader CAN grep produced-vs-consumed handoffs
   > in the wiring files and assert handoff shapes match; it CANNOT build or run the fixture itself. The
   > build-and-run leg is enforced by the orchestrator integration gate (the scheduled wiring-completeness build
   > — see BACKLOG), not by this no-write item.
7. **Contract-edge honesty (any plan/run declaring `builds_against`).** The freeze-time machine check proves
   *import-surface* honesty only; the deeper judgment is yours. Hunt: (a) **Semantic honesty** — a dependent that
   imports ONLY the `contracts/<id>/` surface can still lean at runtime on provider INTERNALS the contract
   under-specifies (ordering, mutation, error taxonomy, side-effects the signature doesn't pin). The machine check
   is blind to this by construction (M1-L5 residual — the reviewer owns this judgment); read the dependent's actual
   use of the imported surface, not just its import lines. (b) **Pinned-constant reliance** — does any contract's
   consumer depend on a constant, `TypeAlias`, or `__all__` entry? These are NOT machine-pinned (M1-L1 residual —
   the surface hash covers signatures + defined `def`/`class` names — re-exports/aliases and constant VALUES are invisible to it); a value flip ships silently green.
   (c) **`depends_on` in disguise** — is a `builds_against` edge really a hard `depends_on`? Probe for mock-shielded
   dependent tests: green against a stub or mock but would FAIL against the provider's real integrated body. Such an
   edge dispatched early at freeze is a false float — reclassify before trusting the run.

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

## Flag conformance-escapes (universal, all tiers — READ-ONLY)

For every confirmed finding in your findings list, check whether the preceding `kata-evaluate` run **PASSED**
that same issue without flagging it. If it did, the finding is a **conformance-escape** — the gate let it
through and you caught it.

Mark each conformance-escape in your findings output with these three fields (inline, no separate doc):
- `failure_class` — a short slug naming the gap class (e.g. `rce-unchecked`, `dos-vector`, `seam-dead`).
- `responsible_skill` — the skill that should harden to catch this class next time (e.g. `kata-evaluate`).
- `severity` — `BLOCKER` | `MAJOR` | `MINOR` (per the finding's severity).

Per `protocol/validation-misses.md` (the full entry schema and when-to-log rule).

**You do NOT write the manifest.** You are fresh-context, read-only — no Write/Edit (structural, per
`STANDARDS §1`). The orchestrator reads your flagged findings and appends each conformance-escape to
`.planning/validation-misses.jsonl` via `validation_misses.append_miss` (non-fatally). Your job is to
flag; the orchestrator's job is to record.

---

## Output format

A findings list, each entry: **severity · the attack · cited evidence · the specific risk** (and, when
applicable, `failure_class` / `responsible_skill` / `severity` tags for any conformance-escape per the
section above).

Then an overall **SHIP / HOLD** recommendation.

> **Verdict-tier variance (CA-L44 F1, GROUNDING SMOKE-1):** the SHIP/HOLD call, like the gate's PASS/NEEDS_WORK,
> is not tier-portable — the same evidence can draw a different verdict at a different review tier. State the
> review tier and the rationale alongside the recommendation. See the calibration note in [[kata-evaluate]]
> (Output) — it is the shared home for this guidance.

HOLD findings route back to [[kata-orchestrate]] as a deliberate decision (re-grill the bad branch, tune a
constant, add coverage) — never an inline silent fix.
