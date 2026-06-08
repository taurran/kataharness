---
name: kata-diagnose-full
description: >-
  Full 6-phase diagnosis loop for an unexpected failure a worker can't green in one TDD step. Use when the
  cause is unknown, the bug is intermittent/complex, or a shallow attempt has already failed. Runs the complete
  ranked-hypotheses + instrumentation ceremony before touching the fix.
license: Apache-2.0
version: 0.1.0
category: execute
status: experimental
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Bash, Edit, Write]
source: adapted-from mattpocock/skills engineering/diagnose
tags:
  - kata/execute
  - kata/module/quality
  - kata/tier/full
  - debugging
  - diagnosis
---
# kata-diagnose-full — complete diagnosis loop

**Method:** see [`../kata-diagnose/RUBRIC.md`](../kata-diagnose/RUBRIC.md) — the tier-invariant method
(feedback-loop-first principle, the 6-phase method, kata constraints: stay in lane, escalate, don't re-plan).
This file sets ONLY the depth.

## Depth contract (Full)

**Applicable when:** the cause is unknown, the bug is intermittent or complex, a quick attempt did not reveal
the answer, or the failure warrants rigorous investigation (production regression, data-corruption risk,
security-adjacent behavior).

**Run all 6 phases in full** as specified in the RUBRIC:

- **Phase 1** — build a robust, deterministic feedback loop; consult `resources/FEEDBACK-LOOPS.md` for
  construction tactics; do not proceed without a loop you believe in.
- **Phase 2** — reproduce: confirm the exact symptom matches the spec/user description.
- **Phase 3** — generate **3–5 ranked, falsifiable hypotheses** before testing any; each must state a
  prediction; note the ranked list as a checkpoint before moving on.
- **Phase 4** — instrument one variable at a time mapped to Phase-3 predictions; tag every debug log with a
  unique prefix (e.g. `[DBG-a4f2]`); measure first for perf regressions.
- **Phase 5** — write the regression test before the fix (or document the absent-seam finding); fix; re-run
  the original Phase-1 loop to confirm the bug is gone.
- **Phase 6** — cleanup + post-mortem: all instrumentation removed, repro silent, commit message names the
  correct hypothesis, post-mortem finding handed to [[kata-improve]] if architectural.

This tier is today's `kata-diagnose` — the complete method with no phases skipped.
