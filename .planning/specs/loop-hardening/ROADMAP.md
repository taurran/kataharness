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
| G7 Viewer not seamless per-platform | S1's viewer is a separate-window TUI only; no host-native status surface (e.g. Claude statusline) is used, so the live view isn't "seamless into the platform it's running on" (operator requirement). |

## Sprints (one-shot each; boundary = a gated, demonstrable artifact you can SEE)
- **S1 — Live telemetry → the dashboard tails reality (real-time, accurate). ✅ DONE (`fedbb87`, fresh-eval PASS).**
  Built `tools/kata_board.py` (emits `.kata/board.md` incl. **PROGRESS heartbeats** + single-writer `state.json`,
  self-creates `.kata/`) + dashboard heartbeat bars + `tools/kata_dash_demo.py` replay driver; title **`KATAHARNESS
  改善型`** (kaizen-gata; torii+hiragana removed per operator). Closes **G1, G2**. pytest 244→268. ⏸ **STOPPED at the
  boundary for the operator demo.** Plan: `PLAN-s1.md`.
- **S1.5 — Status-surface adapters (agnostic-via-adapters, applied to OUTPUT). ✅ DONE (`e753504`, fresh-eval PASS).** Closes G7. Baseline was S1 green.
  Built `adapters/claude/` (statusline command + snippet + README — seeds the adapter layer), `tools/kata_statusline.py`
  (agnostic `render_statusline` + Claude adapter entry, fail-soft), `tools/kata_web.py` (localhost web viewer, stdlib
  `http.server` bound 127.0.0.1, polls `/api/view` 1s). Pull-consumers; no push StatusSink. Research: `RESEARCH-s1.5.md`
  (Claude=feasible/refreshInterval:1, Codex=none→fallback, Kiro=`.vsix` deferred). pytest 333→334, validator 35/0, Snyk 0.
  Demo-caught two render bugs (statusline SystemExit fail-soft; web numeric-child) fixed. Plan: `PLAN-s1.5.md`.
  Operator requirement: the live view must be **seamless into the platform it's running on** — publish to each host's
  *native* status surface, falling back to the rich viewer where a host exposes none. The `.kata/` telemetry core
  (S1) stays canonical; this adds a thin viewer-adapter layer over it (same pattern as the input tool-adapters).
  - *S1.5a — `StatusSink` interface + capability detection + Claude statusline adapter:* define `StatusSink.publish(view_model)`;
    detect the host from env signals; ship `ClaudeStatuslineSink` (one live line — `改善型 ▰▰▰▱▱ 3/5 EXECUTE · 2 workers
    · gate:pending`) wired into `kata-loop`/`kata-orchestrate` so a real run shows live state **in Claude's own window**.
    *Demonstrable:* an orchestrated run whose state updates in the Claude statusline. (Owns: `tools/status_sink.py` + tests
    + the statusline command + SKILL wiring.)
  - *S1.5b — host fallback + documented Codex/Kiro stubs:* `NullSink`/`TuiSink` fallback selection so a host with no
    native bar auto-points to the rich TUI; **stub** `CodexSink`/`KiroSink` behind capability flags **only after their
    real surfaces are verified** (no pretend bars). *Demonstrable:* on a no-native-bar host the run selects the rich
    viewer; the adapter table documents each host's verified surface. (Disjoint from S1.5a by file.)
  - ⚠️ **Honesty caveat:** Claude statusline = verified-feasible, build now. Codex/Kiro surfaces are **unverified** — they
    may have none, in which case those hosts get the rich-viewer fallback, not a native bar. Verify before promising.
- **S2 — Vet the gate + bring the human into initiation. ✅ DONE (`cddf9ff`, fresh-eval PASS 8/8).** Closes G3, G4. Baseline was S1.5 green.
  Built `tools/mutation_run.py` (deterministic restoring mutate→run→restore loop, reuses `mutation_check`); `kata-tdd`
  PROVE now points at it; `kata-evaluate` rubric item 1 **requires** `.kata/mutation.json` `allNonVacuous:true` for
  code-bearing work (closes the silent-skip). `tools/intent_scaffold.py` (schema-conformant INTENT.md writer);
  `kata-initiate` now a **hard structural interview STOP** (AskUserQuestion). **G3 demonstrated end-to-end** (real
  mutation flipped a test green→red, file restored, `mutation.json` emitted). pytest 334→367, validator 35/0, Snyk 0.
  Plan: `PLAN-s2.md`.
  - *S2a — mutation/non-vacuity proof in the gate:* wire the `kata-tdd` mutation step (use `tools/mutation_check.py`)
    → emit `.kata/mutation.json` `{records, allNonVacuous}` via `gate_emit`; `kata-evaluate` reads it (NEEDS_WORK if a
    claimed-covered test is vacuous). *Demonstrable:* a `mutation.json` proving tests bite.
  - *S2b — `kata-initiate` actually prompts:* the skill must STOP and use `AskUserQuestion` for kind/target/grill-depth
    + the dual-control execute decision (not decide inline). *Demonstrable:* an initiation that asks the operator
    questions and freezes `INTENT.md` from the answers. (Disjoint from S2a by file.)
- **S3 — Exercise the cognition + PROVE THE LOOP LOOPS. Closes G5, G6.** Baseline = S2 green. **Operator's hard
  requirement: ≥1 real loop-back iteration with the re-entry handoff evaluated.**
  - *S3a — grounding + research:* **✅ DONE (`4391deb`, fresh-eval PASS 8/8).** Built `tools/escalation.py`
    (`research-needed` payload + research-finding builders/writer → `.kata/escalations/<id>.json`) +
    `tools/grounding_gate.py` (deterministic GROUND/REJECT/ESCALATE verdict + `.kata/grounding.json`), wired into
    `kata-research` (finding schema) + `kata-evaluate` injected-knowledge mode. **G5 demonstrated end-to-end** (real
    escalation + all three verdicts; `allGrounded:false` correctly). pytest 367→420, validator 35/0, Snyk 0. Plan:
    `PLAN-s3a.md`. *(Grounding is conditional — fires only on a `research-needed` escalation, not per-run.)*
  - *S3b — the loop-back:* **✅ DONE (`222cc7e`, G6 PROVEN).** Two operator-driven cycles through the live Kata
    Loop — Cycle 1 NIT-2 (`f72a3bb`) → `kata-closeout` "run again" → `kata-loop` loop-back → `kata-initiate`
    **Phase 1b** consumed the carried context (baseline SHA · `.kata/understand.md` · prior `INTENT.md` · lessons)
    → Cycle 2 MAJOR-3 (`222cc7e`). A fresh-context re-entry grade scored 7/7, corroborated (Cycle-2 goal = a
    near-literal instantiation of the Cycle-1 understand-map's named adjacent gap). G4 + MAJOR-2 live-proven;
    MAJOR-1 correctly did not fire. pytest 445, validator 35/0, Snyk 0. Plan/record: `PLAN-s3b.md` / `REPORT-s3b.md`.

> **✅ loop-hardening COMPLETE — all 7 gaps (G1–G7) closed. The Kata Loop is "vetted, and demonstrably loops."**

## Cadence & rules (sprint-cadence)
- Baseline = most-recent-green (S1 baselines on `v0.1.0-alpha.2`; each later sprint baselines on the prior green).
- Each sprint is **one-shot**, ends at a runnable default-FAIL gate + a fresh-context `kata-evaluate`. The
  **boundary** (between sprints) is the only place steering happens (`kata-sprint` G1–G4) — you course-correct there.
- This roadmap is **boundary-amendable**: after S1 you may reshape S2/S3. The active sprint plan is immutable.
- Every sprint is itself **dogfooded** through the Greater Loop and built as a real orchestrated run (worktrees +
  concurrent workers + fresh-context eval), never inline.
