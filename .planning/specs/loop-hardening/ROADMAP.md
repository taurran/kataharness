---
date: 2026-06-21
spec: loop-hardening
status: FROZEN roadmap (boundary-amendable) — incremental delivery; closes the verified gaps from the Phase-4 dogfood accounting
delivery: incremental (sprint-cadence) · baseline: most-recent-green (v0.1.0-alpha.2, 3ed18d3)
tags: [roadmap, loop-hardening, sprint-cadence, vetted, dogfood, gap-closure]
---

# loop-hardening — close the verified gaps toward "fully functioning, vetted"

**Goal (north star):** move the Greater Loop from "first happy-path run" to *demonstrably exercises every load-
bearing mechanism* — and prove **the loop actually loops** (≥1 version-up re-entry with the handoff evaluated as
it cycles back). Each gap below is **grounded in evidence** from the Phase-4 dogfood accounting, not speculation.

## Grounding — the gaps are real (verified, not assumed)
| Gap | How it was VERIFIED broken/unfired |
|---|---|
| G1 No live coordination board | `ls .kata/board.md .kata/state.json` → **No such file** after the real run. The orchestration used the host Agent tool, never the file-coordination protocol. The dashboard has only ever tailed a synthetic fixture. |
| G2 Dashboard never tailed reality / real-time unproven | Consequence of G1. |
| G3 Mutation/non-vacuity proof never ran | Evaluator noted `mutation.json` absent; `gate_emit` was called with no `mutation_records`. |
| G4 Interactive initiation never prompted | The run made initiation decisions inline; the human got one prompt (version-select), not the `kata-initiate` interview. |
| G5 Grounding gate / `kata-research` never fired | No research-need escalation occurred; the gate was never invoked in injected-knowledge mode. |
| G6 Loop-back never exercised | The version-select chose "ship," so the version-up re-entry (Phase 1b) never ran; the handoff-on-re-entry is unproven. |

## Sprints (one-shot each; boundary = a gated, demonstrable artifact you can SEE)
- **S1 — Live telemetry → the dashboard tails reality (real-time, accurate). ✅ DONE (`fedbb87`, fresh-eval PASS).**
  Built `tools/kata_board.py` (emits `.kata/board.md` incl. **PROGRESS heartbeats** + single-writer `state.json`,
  self-creates `.kata/`) + dashboard heartbeat bars + `tools/kata_dash_demo.py` replay driver; title **`KATAHARNESS
  改善型`** (kaizen-gata; torii+hiragana removed per operator). Closes **G1, G2**. pytest 244→268. ⏸ **STOPPED at the
  boundary for the operator demo.** Plan: `PLAN-s1.md`.
- **S2 — Vet the gate + bring the human into initiation. Closes G3, G4.** Baseline = S1 green.
  - *S2a — mutation/non-vacuity proof in the gate:* wire the `kata-tdd` mutation step (use `tools/mutation_check.py`)
    → emit `.kata/mutation.json` `{records, allNonVacuous}` via `gate_emit`; `kata-evaluate` reads it (NEEDS_WORK if a
    claimed-covered test is vacuous). *Demonstrable:* a `mutation.json` proving tests bite.
  - *S2b — `kata-initiate` actually prompts:* the skill must STOP and use `AskUserQuestion` for kind/target/grill-depth
    + the dual-control execute decision (not decide inline). *Demonstrable:* an initiation that asks the operator
    questions and freezes `INTENT.md` from the answers. (Disjoint from S2a by file.)
- **S3 — Exercise the cognition + PROVE THE LOOP LOOPS. Closes G5, G6.** Baseline = S2 green. **Operator's hard
  requirement: ≥1 real loop-back iteration with the re-entry handoff evaluated.**
  - *S3a — grounding + research:* introduce a `research-needed` task → `kata-research` (no-write, fresh-context) →
    the **grounding gate** (`kata-evaluate` injected-knowledge mode: GROUND/REJECT/ESCALATE, source must support the
    claim). *Demonstrable:* real GROUND/REJECT verdicts on cited findings.
  - *S3b — the loop-back:* a real version-up cycle — `kata-closeout` "run again" → `kata-loop` loop-back →
    `kata-initiate` **Phase 1b** re-entry consuming carried context (`.kata/understand.md`, prior `INTENT.md`,
    lessons, baseline SHA) → second small build → closeout. **Grade the re-entry handoff** (did Phase 1b ingest the
    prior context, avoid re-grilling mapped ground?). *Demonstrable:* a second cycle that provably started informed.

## Cadence & rules (sprint-cadence)
- Baseline = most-recent-green (S1 baselines on `v0.1.0-alpha.2`; each later sprint baselines on the prior green).
- Each sprint is **one-shot**, ends at a runnable default-FAIL gate + a fresh-context `kata-evaluate`. The
  **boundary** (between sprints) is the only place steering happens (`kata-sprint` G1–G4) — you course-correct there.
- This roadmap is **boundary-amendable**: after S1 you may reshape S2/S3. The active sprint plan is immutable.
- Every sprint is itself **dogfooded** through the Greater Loop and built as a real orchestrated run (worktrees +
  concurrent workers + fresh-context eval), never inline.
