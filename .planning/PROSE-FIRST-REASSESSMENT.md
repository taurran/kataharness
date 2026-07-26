---
date: 2026-07-26
kind: reassessment — corrects my own framing
bearing_on: KH-T04 (the six doctrine laws), KH-T05 (when code is required), the whole prose-first question
---

# IS PROSE-FIRST BROKEN? — a reassessment

## The operator's question

> *"If prose first is actually broken, that's a problem. MindBridge Loop operates under the assumption
> that determinism doctrine will allow a working model. If that's just flat out false, we need to
> reassess the approach at least here."*

## My framing was wrong, and the distinction is the whole answer

I reported: *"every invariant that lived only in a `SKILL.md` sentence came back unverifiable or
quietly broken."* True — but I let it imply **prose-first is broken**. It doesn't show that.

**What it actually shows: UNGOVERNED prose fails.** Every one of our prose failures was written
*without* the discipline that MindBridge's doctrine exists to impose. We have never applied their
rules to our prose. We wrote prose the ordinary way and it rotted the ordinary way.

That is not a test of prose-first. It is a test of prose-with-no-rules — and it failed exactly as
their doctrine predicts.

## The evidence, mapped

Their proposed laws 11–16 are precisely about making prose enforceable. Here is every confirmed break
we found this week, mapped to the law that would have caught it. **I did this mapping to try to
falsify the connection — it got stronger instead.**

| our confirmed break | the law it violates |
|---|---|
| Prime-directive check is 7 substrings; an inverted document passes green | **13** — validating the SHAPE of evidence is an existence check; recompute the value. Also **11** |
| Stale `RESULT.json` credited — 37 commits behind HEAD, no currency check | **12** — a gate's PARAMETERS are part of the gate; derive them in-fence from the live artifact |
| D33 never-tiered invariants have no test across tier variants | **14** — a gate is not verified until RUN against every artifact class it claims to cover |
| My own D4 test could not fail (both rung sets identical today) | **16** — a check with a ZERO denominator reports VACUOUS |
| `l2` flag validated, stored, never read by anything | **16** — structurally vacuous |
| "Fresh-context evaluator" has zero runtime attestation | **11** — a machine-checkable rule ships with its checker |
| `STANDARDS.md` says version-bump is "validator-enforced"; no detector exists | **11** — a documented guarantee whose detector does not exist reads as enforced to every future author |
| Nothing in code reads `mode` / `tiers` | **11** |
| Boundary-supersedes-self handoff: prose, zero code | **11** |
| Handoff staleness comparator: does not exist | **11** |

**Ten independent failures. Every one lands on law 11, 12, 13, 14, or 16.**

That is not a coincidence and it is not me being charitable to their package. Those laws were derived
from *their* audit of *their* harness, on a different architecture, and they predict our failures
with no adaptation.

## What this changes

**1. The answer to the operator's question is: prose-first is not shown broken.** What is shown
broken is prose-first *as we have been practising it* — with no requirement that a promise carry a
detector, that a gate derive its own parameters, or that a check be capable of failing.

**2. `MC-02` just became far more important than I rated it.** I recommended taking **2 of 6** on the
grounds that they were "batch-reviewed, single-corpus, from an architecture unlike ours." That
reasoning is now much weaker: we have **ten independent confirmations, on our own tree, that the
failure modes those laws describe are real here.** The laws describe our disease.

**3. But confirming the DISEASE is not confirming the CURE — and I will not overclaim it.** What we
verified is that the failure modes are real. Whether their specific remedies work is still untested
**on both sides** — neither harness has completed a live end-to-end run. So the honest posture:
- The **problem statements** in laws 11–16 are now evidence-backed here. Treat them as findings.
- The **prescriptions** still get grilled on their merits. Adopting a rule because its diagnosis
  was right is exactly the reasoning error we keep catching.

**4. It reframes `KH-T05`.** The question is not "prose or code." It is: **what makes prose safe
enough to keep?** Their answer is the doctrine. Ours can additionally be "use code where code is
optimal," which they cannot do. **We have a strictly larger option set** — prose-with-doctrine *or*
code — and should stop treating it as a binary.

## The honest residual risk

MindBridge is betting their entire architecture on the doctrine making prose safe, because their host
constraint leaves them no alternative. **They have not proven that bet** — no live end-to-end run,
their own determinism grader has never fired, and only 3 of their 22 checks have a deliberate-break
probe.

We are not exposed to that bet the same way, because **we can drop to code whenever the doctrine
looks insufficient.** That is the material difference between the two harnesses, and it is the thing
the outbound alignment package got wrong by calling us "scripts-first" — it described the *tool* we
reach for instead of the *freedom* we have to reach for it.

## Recommendation

- **Do not abandon prose-first.** The evidence does not support it.
- **Do adopt the discipline** — a promise carries a detector; a gate derives its parameters; a check
  that cannot fail is reported as vacuous. Whether that arrives as their laws 11–16, our own wording,
  or `KH-B39` (grep every promise for its producing code site) is the grill's call.
- **Raise `KH-T04` in priority.** It was "understand before deciding." It is now the item that
  determines whether our default architecture is viable as practised.
