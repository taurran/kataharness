# STEERING — KataHarness

Operator → agent steering channel (mid-run direction without a restart).

> **Wired 2026-07-12 (health review F-3).** This is now a **real harness behavior**, not a manual
> convention: `kata-orchestrate` (≥ 0.12.0) reads this file at every wave/task boundary via
> `tools/kata_steer.py`, backed by the contract in `protocol/steering.md`. Write a directive under
> `## Active directives`; the running loop surfaces it at the next boundary, acts on it (or escalates
> if it would change the frozen plan), and moves it to `## Consumed / delivered`. **Graceful stop:**
> create an `AGENT_STOP` file in the run's `.kata/` dir OR add a `## AGENT_STOP` line here — the loop
> halts cleanly at the next boundary (parks in-flight work, refreshes the handoff), never a blind
> mid-task kill. Empty `## Active directives` = no active steering.

## Active directives
_(none active — the BUILD-THROUGH directive below was DELIVERED 2026-06-20 and is consumed.)_

## Consumed / delivered
- **BUILD-THROUGH (2026-06-20, operator) — ✅ DELIVERED 2026-06-20.** Built the **full Greater Loop (Phases 0–3:
  F1, F2, initiation, closeout, `kata-loop`)** as a continuous build, no intermediate test ceremony; per-phase
  correctness gates applied each phase (pytest · validator · Snyk · fresh-context `kata-evaluate` PASS 8/8 before
  each merge). All four phases on `master` (`9e1b27c`→`f39f37b`), pushed. **The single next TEST = Phase 4
  self-dogfood of the complete Greater Loop — operator-driven** (see `HANDOFF.md` §4 NEXT ACTION). External reach
  (Phase 5: install/multi-model) follows. *(Durable copy in `greater-loop/ROADMAP.md`.)*
