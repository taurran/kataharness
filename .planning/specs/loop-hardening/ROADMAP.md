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
- **S1 — Live telemetry → the dashboard tails reality (real-time, accurate).** Build the board+state emitter so a
  real run writes `.kata/board.md` (incl. **PROGRESS heartbeats**) + `.kata/state.json`; the dashboard renders it
  smoothly & accurately; new title **改善の型**; a **replay/demo driver** so you can watch it animate live.
  Closes **G1, G2**. ⛔ **STOP after S1 — hand to the operator to watch + give feedback before S2/S3.**
- **S2 — Vet the gate + bring the human into initiation.** Make the gate run the **mutation/non-vacuity proof**
  (emit `mutation.json`); make `kata-initiate` actually **prompt** (the stop-and-ask interview + dual control).
  Closes **G3, G4**. Demonstrable: a `mutation.json` proving tests bite + an initiation that asks you questions.
- **S3 — Exercise the cognition + PROVE THE LOOP LOOPS.** Deliberately trigger a research-need → `kata-research`
  (no-write) → **grounding gate** (GROUND/REJECT/ESCALATE); then run a real **version-up loop-back** re-entry and
  **evaluate the handoff as it cycles back through** (the must-have). Closes **G5, G6**. Demonstrable: grounding
  verdicts + a second loop cycle that starts informed from the carried context.

## Cadence & rules (sprint-cadence)
- Baseline = most-recent-green (S1 baselines on `v0.1.0-alpha.2`; each later sprint baselines on the prior green).
- Each sprint is **one-shot**, ends at a runnable default-FAIL gate + a fresh-context `kata-evaluate`. The
  **boundary** (between sprints) is the only place steering happens (`kata-sprint` G1–G4) — you course-correct there.
- This roadmap is **boundary-amendable**: after S1 you may reshape S2/S3. The active sprint plan is immutable.
- Every sprint is itself **dogfooded** through the Greater Loop and built as a real orchestrated run (worktrees +
  concurrent workers + fresh-context eval), never inline.
