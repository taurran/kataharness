---
title: PROPOSAL — harden against recurring `kata-orchestrate × phantom-reuse` (built-but-unwired)
status: PROPOSED (T2 auto-draft, D118) — routes to freeze-gate kata-review → human merge. NOT applied.
drafted: 2026-06-29
cluster: kata-orchestrate::phantom-reuse
distinct_runs: 2 (BLOCKER-tier threshold = 2) — ACTIONABLE
detector: recurrence_detect.detect_from_paths
---

> **INTERIM (2026-06-30):** prose-pin applied to `kata-evaluate` item 9 + `kata-review` 6(b); full
> wiring-completeness-gate build SCHEDULED (see BACKLOG). NOT yet marked guarded in
> `recurrence-handled.jsonl` — per T2, the guarded marker waits for the build to land.

# Actionable recurrence: orchestrate wiring describes a flow a slice isn't actually wired into

## The cluster (evidence)
| Run | Decision | The miss (PART A + D98 passed; deeper lens caught it) |
|---|---|---|
| `d123-benchmark` | D123 | The dual-gate runner (`run_dual_gate`) was **never wired** into `kata-orchestrate` → `score_arms` ran with no gate data → **Q=1.0 for any floor-passing arm** (quality axis non-functional). D98 caught the dead wiring. |
| `d124-deepadval` | D124 | The Benchmark **definition + criteria + delta chain** was built+tested but **never wired** (def_out required-but-never-written; `criteria_ref` produced-never-consumed; delta `sameDefinition` structurally always False). Plus the dual-gate ran control tests with **no cwd/import-context** → Q=0 for every real importing control. The **deep end-to-end ad-val** caught both. |

## The pattern
A slice's engine surface is unit-built, unit-tested, and mutation-proven — and the orchestrate prose **claims** it is driven — but the producer→consumer handoff is never actually connected (a built-but-unwired / phantom-reuse seam). The conformance gate (`kata-evaluate` PART A) and the standing adversarial review (`kata-review` D98) both **pass it**, because they test units + injected data; they do not trace the live end-to-end flow.

## Why the existing guards miss it
- PART A tests `score_arms` etc. **in isolation with injected booleans/artifacts** → the engine works, so it passes.
- D98 attacks the **engine** (fail-opens, injection, honesty) on synthetic data → finds engine bugs, not unwired seams.
- Neither **runs the whole flow on a realistic fixture** and asserts every produced surface is consumed and every consumed surface is produced.

## Proposed guard (PROSE-pinned, like exec-safety's standing rule — D112-class)
**Add an end-to-end WIRING-COMPLETENESS check to the integration gate for any build that edits `kata-orchestrate` (or any skill claiming an end-to-end flow):**
1. Build a **minimal realistic fixture** (not injected data) and trace the full orchestrated path, asserting **every handoff connects** (output shape of step N == input shape of step N+1).
2. A static **produced-vs-consumed** sweep: every public engine surface the flow introduces must have a caller in the wiring; every input the wiring's calls require must have a producer. Flag any produced-but-unconsumed or consumed-but-unproduced surface.
3. Wire it as a **`kata-evaluate` rubric item** (the "reproduce, don't trust" item 9 extended to "trace, don't assume — run the whole flow once on a realistic fixture") and/or a recipe integration-gate checklist line.

## Test sketch (mechanical, optional companion to the prose rule)
A reusable `tools/` helper (or a CI check) that, given a skill's cited engine surfaces, greps the wiring for callers and the engines for the cited fields, and fails if a cited-but-uncalled surface or an uncalled-required-input exists. (Same spirit as `test_exec_safety.py`'s registry-completeness check — make the wiring-completeness invariant structural, not human-enforced.)

## T2 invariant (load-bearing)
This proposal **proposes** — it does not change a gate verdict, edit a skill/tool, write the `guarded` marker, or merge itself. The guard authoring + merge stay **human** (freeze-gate `kata-review` → operator). Marked `proposed` in `.planning/recurrence-handled.jsonl`.
