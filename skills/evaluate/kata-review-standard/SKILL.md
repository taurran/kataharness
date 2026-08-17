---
name: kata-review-standard
description: >-
  Full 5-surface adversarial review (default). Use after kata-evaluate passes, before trusting a result,
  to red-team the spec's judgment, hunt missing test coverage, and probe the security and failure surface.
  Burn-02 meta-finding, verbatim: "the judgment+human layers found all of these; the automated mechanical
  gates found none."
license: Apache-2.0
version: 0.2.0
category: evaluate
status: beta
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Bash]
source: >-
  adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate)
tags:
  - kata/evaluate
  - kata/module/quality
  - kata/tier/standard
  - adversarial
  - red-team
  - no-write
---
# kata-review-standard — full 5-surface adversarial review (default)

**Method:** see [`../kata-review/RUBRIC.md`](../kata-review/RUBRIC.md) — the tier-invariant method (the numbered attack
surfaces, cite-evidence rule, SHIP/HOLD output, the "attack before you trust" framing). This file sets ONLY
the depth.

## Depth contract (Standard)

Run **ALL** attack surfaces exactly as defined in `../kata-review/RUBRIC.md` — full coverage, no
surface skipped. The RUBRIC is the single source of truth for what each surface means, the cite-evidence
rule, and the SHIP / HOLD output format. This tier does not narrow the surface set; it runs the complete
adversarial pass at original depth.

This is today's `kata-review` at its original depth — the default for any non-trivial adversarial pass.

## Judge contract (trust-model W5 — TM-E2, R3-M2)

> **Burn-02 meta-finding (standing humility, verbatim):** *"the judgment+human layers found all of these; the
> automated mechanical gates found none."* Detectors ATTEST and NARROW; judges judge (TM-D2).

- **Pinned first line.** The **literal FIRST LINE** of this review's returned envelope MUST be exactly
  `VERDICT: <enum>` with the CLOSED enum — this judge's complete verdict space:

  | Verdict | Meaning |
  |---|---|
  | `SHIP` | Every attack surface run at this tier's depth came back clean or with only non-blocking notes. |
  | `HOLD` | At least one finding blocks trust; the findings list names the fix/re-grill target. |

  The line is parsed by the ONE verdict parser, `kata_dispatch.parse_verdict` — strict `fullmatch` on line 1
  of the envelope; the body is NEVER scanned and there is deliberately **no body-scan fallback** (a no-match
  is `CaptureRefused`, the absent-records refusal path). Dispatchers bind this enum by passing
  `allowed={"SHIP","HOLD"}` at capture; today only [[kata-orchestrate]]'s LS-31 pins its set (the
  evaluator's `PASS|NEEDS_WORK`) — the reviewer dispatch sites (LS-06/27/34/39) pass bare
  `capture(kind="verdict")`, so the enum binding there is DECLARED, not yet wired (the wiring is
  kata-orchestrate's file, W4-owned). The RUBRIC's "overall SHIP / HOLD recommendation" in the body
  restates this line; the two must agree, and line 1 is the copy the machine reads.
- **Attested fact table as REQUIRED input (TM-E2).** The review's brief carries the attested fact table for
  its target (detector outputs + grounding verdicts + evidence identity). **Judge ON the facts: never
  re-derive what an engine attested; never accept a worker claim the table contradicts** — the contradiction
  is itself a finding. The regenerate-and-diff duty is captured in the VERDICT payload's evidence pointers.
  **Producer (scheduled, NOT yet built):** the table's emitter is the `tools/grounding_gate.py` fact-table
  extension, landing with the Loop B `grounding-agent` task. Until it lands this input is declared
  Honor-system — review the raw artifacts and say the table was not available.
- **Residual-judgment surfaces (TM-E2 c), explicit:** this review IS the residual-judgment layer — **quality**
  (decision judgment, drift-magnet calls), **design fidelity** (does the result honor the frozen spec's
  intent), **threat reasoning** (the security/failure surface). Facts are the engines' job; these three are
  this judge's.
- **Tripwire (TM-D3, R-M6): Honor-system — declared, not enforced.** This judge's known-bad corpus and its
  runner (`tools/tripwire_check.py`) land with the Loop B `judge-tripwire-corpora` task — **scheduled, NOT
  yet built**. Until the corpus lands this judge is Honor-system per R-M6 (never blocked); a judge that
  cannot demonstrate failure-capability is **Dormant, not Verified**.
