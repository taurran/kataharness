# STEERING — KataHarness

Operator → agent steering channel (mid-run direction without a restart). The harness reads this on a
cadence; entries are consumed and cleared. Empty = no active steering.

> Convention (from Anthropic's `STEER.md`): write a directive here; the running loop surfaces it,
> acts, and clears it. `AGENT_STOP` (presence of the file) is the kill-switch.

## Active directives
_(none active — the BUILD-THROUGH directive below was DELIVERED 2026-06-20 and is consumed.)_

## Consumed / delivered
- **BUILD-THROUGH (2026-06-20, operator) — ✅ DELIVERED 2026-06-20.** Built the **full Greater Loop (Phases 0–3:
  F1, F2, initiation, closeout, `kata-loop`)** as a continuous build, no intermediate test ceremony; per-phase
  correctness gates applied each phase (pytest · validator · Snyk · fresh-context `kata-evaluate` PASS 8/8 before
  each merge). All four phases on `master` (`9e1b27c`→`f39f37b`), pushed. **The single next TEST = Phase 4
  self-dogfood of the complete Greater Loop — operator-driven** (see `HANDOFF.md` §4 NEXT ACTION). External reach
  (Phase 5: install/multi-model) follows. *(Durable copy in `greater-loop/ROADMAP.md`.)*
