---
name: kata-review-essential
description: >-
  Smell-test review for the highest-risk surfaces only. Pick this for a fast sanity check on a PoC or
  cheap one-shot where exhaustive adversarial coverage is not required — e.g., early drafts, time-boxed
  spikes, or when a full adversarial pass is planned later. Burn-02 meta-finding, verbatim: "the
  judgment+human layers found all of these; the automated mechanical gates found none."
license: Apache-2.0
version: 0.2.0
category: evaluate
status: beta
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Bash]
source: >-
  adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate)
tags:
  - kata/evaluate
  - kata/module/quality
  - kata/tier/essential
  - adversarial
  - red-team
  - no-write
---
# kata-review-essential — smell-test (top-risk surfaces only)

**Method:** see [`../kata-review/RUBRIC.md`](../kata-review/RUBRIC.md) — the tier-invariant method (the numbered attack
surfaces, cite-evidence rule, SHIP/HOLD output, the "attack before you trust" framing). This file sets ONLY
the depth.

## Depth contract (Essential)

Run a **smell-test** over the **two highest-risk surfaces only**:

- **Decision judgment** — challenge the drift-magnets (classification/boundary calls and magnitude/constants).
  Is each LOCKED decision defensible, or did a borderline case get filed wrong?
- **Test adequacy gaps** — the most obvious missing coverage: untested boundary behavior, all-one-category
  inputs, or the meaningful middle range the builder's suite skips.

Cite evidence for every finding. Produce a SHIP / HOLD.

**What this tier deliberately skips:** assumptions/contradictions audit, security/failure surface deep-dive,
and second-order effects chase. Note in the output that this was an Essential-tier review (partial surface
coverage) so downstream consumers know the scope.

**This tier does NOT replace a Standard review before a production decision.** Use it when a PoC or early
draft is the context and the user has explicitly accepted reduced coverage.

## Judge contract (trust-model W5 — TM-E2, R3-M2)

> **Burn-02 meta-finding (standing humility, verbatim):** *"the judgment+human layers found all of these; the
> automated mechanical gates found none."* Detectors ATTEST and NARROW; judges judge (TM-D2).

- **Pinned first line.** The **literal FIRST LINE** of this review's returned envelope MUST be exactly
  `VERDICT: <enum>` with the CLOSED enum — this judge's complete verdict space:

  | Verdict | Meaning |
  |---|---|
  | `SHIP` | Both smell-test surfaces came back clean or with only non-blocking notes (Essential scope stated). |
  | `HOLD` | At least one finding blocks trust; the findings list names the fix/re-grill target. |

  The line is parsed by the ONE verdict parser, `kata_dispatch.parse_verdict` — strict `fullmatch` on line 1
  of the envelope; the body is NEVER scanned and there is deliberately **no body-scan fallback** (a no-match
  is `CaptureRefused`, the absent-records refusal path). Dispatchers bind this enum by passing
  `allowed={"SHIP","HOLD"}` at capture; today only [[kata-orchestrate]]'s LS-31 pins its set (the
  evaluator's `PASS|NEEDS_WORK`) — the reviewer dispatch sites (LS-06/27/34/39) pass bare
  `capture(kind="verdict")`, so the enum binding there is DECLARED, not yet wired (the wiring is
  kata-orchestrate's file, W4-owned). The body's SHIP / HOLD restates this line; the two must agree, and
  line 1 is the copy the machine reads.
- **Attested fact table as REQUIRED input (TM-E2).** The review's brief carries the attested fact table for
  its target (detector outputs + grounding verdicts + evidence identity). **Judge ON the facts: never
  re-derive what an engine attested; never accept a worker claim the table contradicts** — the contradiction
  is itself a finding. **Producer (scheduled, NOT yet built):** the table's emitter is the
  `tools/grounding_gate.py` fact-table extension, landing with the Loop B `grounding-agent` task. Until it
  lands this input is declared Honor-system — review the raw artifacts and say the table was not available.
- **Residual-judgment surfaces (TM-E2 c), explicit:** at this tier the residual-judgment set narrows with
  the depth contract but keeps the same names — **quality** (decision judgment on the drift-magnets),
  **design fidelity** and **threat reasoning** only as far as the two smell-test surfaces reach (the skipped
  depth is stated in the output, per this tier's scope note).
- **Tripwire (TM-D3, R-M6): Honor-system — declared, not enforced.** This judge's known-bad corpus and its
  runner (`tools/tripwire_check.py`) land with the Loop B `judge-tripwire-corpora` task — **scheduled, NOT
  yet built**. Until the corpus lands this judge is Honor-system per R-M6 (never blocked); a judge that
  cannot demonstrate failure-capability is **Dormant, not Verified**.
