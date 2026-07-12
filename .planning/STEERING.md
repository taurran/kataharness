# STEERING — KataHarness

Operator → agent steering channel (mid-run direction without a restart).

> **Honesty note (2026-07-12 health review):** this file is a **manual convention, not an
> automated harness behavior**. No skill, tool, or hook currently reads this file on a cadence,
> and no `AGENT_STOP` kill-switch is implemented anywhere in the harness. An agent acts on this
> file when the operator points it here (or a session-start read order includes it) — nothing
> more. The earlier header claiming "the harness reads this on a cadence" and an `AGENT_STOP`
> kill-switch described an aspiration, not a built feature (the built-but-claimed class this
> project guards against). Wiring a real steering-check into the orchestrator's boundary cadence
> + a real kill-switch is a named backlog item (see BACKLOG "2026-07-12 health-review
> follow-ups"). Until that ships: to steer a running loop, interrupt the session directly.

Convention (from Anthropic's `STEER.md`): write a directive here; when an agent is directed to
this file it surfaces the directive, acts, and moves it to Consumed. Empty = no active steering.

## Active directives
_(none active — the BUILD-THROUGH directive below was DELIVERED 2026-06-20 and is consumed.)_

## Consumed / delivered
- **BUILD-THROUGH (2026-06-20, operator) — ✅ DELIVERED 2026-06-20.** Built the **full Greater Loop (Phases 0–3:
  F1, F2, initiation, closeout, `kata-loop`)** as a continuous build, no intermediate test ceremony; per-phase
  correctness gates applied each phase (pytest · validator · Snyk · fresh-context `kata-evaluate` PASS 8/8 before
  each merge). All four phases on `master` (`9e1b27c`→`f39f37b`), pushed. **The single next TEST = Phase 4
  self-dogfood of the complete Greater Loop — operator-driven** (see `HANDOFF.md` §4 NEXT ACTION). External reach
  (Phase 5: install/multi-model) follows. *(Durable copy in `greater-loop/ROADMAP.md`.)*
