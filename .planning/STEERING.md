# STEERING — KataHarness

Operator → agent steering channel (mid-run direction without a restart). The harness reads this on a
cadence; entries are consumed and cleared. Empty = no active steering.

> Convention (from Anthropic's `STEER.md`): write a directive here; the running loop surfaces it,
> acts, and clears it. `AGENT_STOP` (presence of the file) is the kill-switch.

## Active directives
- **BUILD-THROUGH (2026-06-20, operator):** deliver the **full Greater Loop (Phases 0–3: F1, F2, initiation,
  closeout, `kata-loop`)** as a continuous build. **Do NOT run another dogfood/test ceremony until the whole
  loop is built** — "no reason to test until we've built what we know we need." Per-build *correctness* gates
  still apply every phase (validator green · pytest · Snyk · fresh-context `kata-review` before merge) — those
  are build discipline, not the "test." **The single next TEST = Phase 4 self-dogfood of the complete Greater
  Loop.** External reach (Phase 5: install/multi-model) follows after. *(Durable copy in `greater-loop/ROADMAP.md`.)*
