---
name: kata-diagnose-light
description: >-
  Fast diagnosis for a shallow or obvious bug where the cause is readily apparent. Pick this when the failure
  is straightforward — a clear regression, an obvious misconfiguration, or a bug with an immediately plausible
  single cause — and you want to fix it quickly without the full hypothesis/instrumentation ceremony.
license: Apache-2.0
version: 0.1.0
category: execute
status: beta
agnostic: true
cost-weight: 2
allowed-tools: [Read, Grep, Glob, Bash, Edit, Write]
source: adapted-from mattpocock/skills engineering/diagnose
tags:
  - kata/execute
  - kata/module/quality
  - kata/tier/light
  - debugging
  - diagnosis
---
# kata-diagnose-light — fast diagnosis for obvious bugs

**Method:** see [`../kata-diagnose/RUBRIC.md`](../kata-diagnose/RUBRIC.md) — the tier-invariant method
(feedback-loop-first principle, the 6-phase method, kata constraints: stay in lane, escalate, don't re-plan).
This file sets ONLY the depth.

## Depth contract (Light)

**Applicable when:** the bug is shallow or its cause is obvious at a glance — a clear regression, a typo, an
off-by-one, a missing guard, or any failure where a single most-likely hypothesis is immediately apparent.

**Run Phases 1 and 2** (build the feedback loop, reproduce the bug) exactly as the RUBRIC describes — the
loop is still required; do not skip it.

**Skip Phase 3 (ranked hypotheses) and Phase 4 (instrumentation):** if the cause is obvious, go directly to
the fix. You do NOT need to enumerate 3–5 hypotheses or set up probes when the answer is already clear.

**Run Phase 5** (fix + regression test) in full: write the regression test before the fix if a correct seam
exists; otherwise document the absent-seam finding.

**Run Phase 6** (cleanup + post-mortem) in full: all debug artifacts removed, repro no longer reproduces,
regression test green.

**If the cause turns out to not be obvious mid-loop,** escalate to `kata-diagnose-full` rather than
continuing with guesswork. The light tier is for quick resolution of straightforward bugs — not for shortcuts
on genuinely complex failures.
