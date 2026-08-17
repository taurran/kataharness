---
name: kata-review-advanced
description: >-
  Exhaustive adversarial review with threat-model deep-dive and test-case generation. Use when maximum
  rigor is required — high-stakes decisions, security-sensitive surfaces, or any result where a Standard
  review found HOLDs and the re-reviewed surface still warrants deeper scrutiny. Burn-02 meta-finding,
  verbatim: "the judgment+human layers found all of these; the automated mechanical gates found none."
license: Apache-2.0
version: 0.2.0
category: evaluate
status: beta
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Bash]
source: >-
  adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate)
tags:
  - kata/evaluate
  - kata/module/quality
  - kata/tier/advanced
  - adversarial
  - red-team
  - no-write
---
# kata-review-advanced — exhaustive adversarial review

**Method:** see [`../kata-review/RUBRIC.md`](../kata-review/RUBRIC.md) — the tier-invariant method (the numbered attack
surfaces, cite-evidence rule, SHIP/HOLD output, the "attack before you trust" framing). This file sets ONLY
the depth.

## Depth contract (Advanced)

Run the **full Standard method** (ALL surfaces, cited evidence, SHIP/HOLD) **plus**:

- **Threat-model deep-dive.** Go beyond surface-level security checks: enumerate the attacker's goal, build
  an explicit threat register (asset · threat actor · attack vector · mitigation · residual risk), and confirm
  each claimed mitigation is actually enforced in code — not just asserted in the plan.
- **Exhaustive second-order chase.** Trace every downstream consumer of the changed interface/behavior;
  enumerate cascading effects two hops out; flag any implicit coupling that the Standard pass leaves implicit.
- **Adversarial test-case generation.** For each gap found in the test adequacy surface, produce concrete
  failing-case specifications (input · expected behavior · why the current suite misses it) that a builder can
  translate directly into regression tests.

Findings list carries the same format (severity · attack · cited evidence · specific risk). Overall SHIP /
HOLD. HOLD findings are specific enough that the re-grill or fix target is unambiguous.

## Judge contract (trust-model W5 — TM-E2, R3-M2)

> **Burn-02 meta-finding (standing humility, verbatim):** *"the judgment+human layers found all of these; the
> automated mechanical gates found none."* Detectors ATTEST and NARROW; judges judge (TM-D2).

- **Pinned first line.** The **literal FIRST LINE** of this review's returned envelope MUST be exactly
  `VERDICT: <enum>` with the CLOSED enum — this judge's complete verdict space:

  | Verdict | Meaning |
  |---|---|
  | `SHIP` | Every surface — the full Standard set plus this tier's three deep-dives — came back clean or with only non-blocking notes. |
  | `HOLD` | At least one finding blocks trust; the findings list names the fix/re-grill target. |

  The line is parsed by the ONE verdict parser, `kata_dispatch.parse_verdict` — strict `fullmatch` on line 1
  of the envelope; the body is NEVER scanned and there is deliberately **no body-scan fallback** (a no-match
  is `CaptureRefused`, the absent-records refusal path). Dispatchers bind this enum by passing
  `allowed={"SHIP","HOLD"}` at capture; today only [[kata-orchestrate]]'s LS-31 pins its set (the
  evaluator's `PASS|NEEDS_WORK`) — the reviewer dispatch sites (LS-06/27/34/39) pass bare
  `capture(kind="verdict")`, so the enum binding there is DECLARED, not yet wired (the wiring is
  kata-orchestrate's file, W4-owned). This applies to **each** convergence pass this tier runs: the
  Advanced grill double-pass is two distinct dispatches, and each pass returns its own
  `VERDICT: SHIP|HOLD` first line under its own record.
  The body's SHIP / HOLD restates line 1; the two must agree, and line 1 is the copy the machine reads.
- **Attested fact table as REQUIRED input (TM-E2).** The review's brief carries the attested fact table for
  its target (detector outputs + grounding verdicts + evidence identity). **Judge ON the facts: never
  re-derive what an engine attested; never accept a worker claim the table contradicts** — the contradiction
  is itself a finding. The regenerate-and-diff duty is captured in the VERDICT payload's evidence pointers.
  **Producer (scheduled, NOT yet built):** the table's emitter is the `tools/grounding_gate.py` fact-table
  extension, landing with the Loop B `grounding-agent` task. Until it lands this input is declared
  Honor-system — review the raw artifacts and say the table was not available.
- **Residual-judgment surfaces (TM-E2 c), explicit:** this tier is the residual-judgment layer at maximum
  depth — **quality** (decision judgment across all surfaces), **design fidelity** (second-order chase
  against the frozen spec's intent), **threat reasoning** (the explicit threat register: asset · actor ·
  vector · mitigation · residual risk, enforcement confirmed in code). Facts are the engines' job; these
  three are this judge's.
- **Tripwire (TM-D3, R-M6): Honor-system — declared, not enforced.** This judge's known-bad corpus and its
  runner (`tools/tripwire_check.py`) land with the Loop B `judge-tripwire-corpora` task — **scheduled, NOT
  yet built**. Until the corpus lands this judge is Honor-system per R-M6 (never blocked); a judge that
  cannot demonstrate failure-capability is **Dormant, not Verified**.
