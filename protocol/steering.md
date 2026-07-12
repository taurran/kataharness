# protocol/steering.md — the operator→agent steering channel

Mid-run direction **without a restart**. The operator writes to `STEERING.md`; the orchestrator
reads it at every wave/task boundary, surfaces active directives, acts within the frozen plan (or
escalates if a directive would require re-planning), and moves consumed directives to the
`## Consumed / delivered` section. Backed by `tools/kata_steer.py` (the deterministic reader) so
the channel is a real, tested behavior — not a prose promise. (Wired 2026-07-12; before that
`STEERING.md` described a cadence with no implementation — the built-but-claimed facade the Prime
Directives, `protocol/prime-directives.md`, exist to prevent.)

## The two signals

1. **`AGENT_STOP` — graceful kill-switch (never a blind mid-task kill).** Requested by EITHER a
   file at `<kata_dir>/AGENT_STOP` OR a `## AGENT_STOP` heading line in `STEERING.md`. Read by
   `kata_steer.stop_requested(kata_dir)`. On a positive result the orchestrator: finishes nothing
   new, **parks** in-flight tasks (they resume via the normal restore path), writes/refreshes the
   `HANDOFF.md`, and stops cleanly **at the current boundary**. This composes with the board's
   "never a blind kill" rule (`protocol/board.md`) — a stop is a boundary halt, not a `SIGKILL`.
2. **Active directives** — the non-empty, non-placeholder lines under `## Active directives` in
   `STEERING.md`, read by `kata_steer.read_active_directives(path)` (deterministic: source order,
   no dedupe). Each is operator guidance for the run (e.g. "prioritize the auth module",
   "skip the perf pass"). A directive that stays inside the frozen plan is acted on directly; one
   that would **change the plan** is not silently obeyed — it routes through the normal
   escalation/re-plan path (spine #1: the plan does not drift), and the operator's directive is the
   deliberate re-plan trigger.

## Cadence + who writes

- **Read cadence:** every wave boundary and every task-completion boundary (the same points the
  orchestrator already refreshes state/liveness). Deterministic file reads only — no polling thread.
- **Single-writer:** the **operator** authors directives; the **orchestrator** moves them to
  `## Consumed / delivered` after acting (a prose edit it owns, like state). `kata_steer` is
  **read-only** — the engine never rewrites `STEERING.md`.
- **Fail-soft read / halt-biased stop:** an absent or malformed `STEERING.md` yields no directives
  (steering is additive, never run-fatal); the stop check is biased toward halting (an unreadable
  file whose bytes carry the sentinel still stops — halting is the safe direction the operator asked
  for).
- **Honest limit — the stop is prose-gated, not host-enforced.** Like every other boundary behavior
  (liveness, self-handoff), the conductor *invokes* `kata_steer` at the boundary because this skill
  tells it to; there is no host-level hook that fires `AGENT_STOP` independently. A runaway or
  non-compliant conductor that skips the boundary step would not honor a stop. The engine is real and
  tested; the *guarantee* is bounded by conductor adherence, at parity with the rest of the loop. For
  a hard, host-enforced kill, terminate the session directly.

## Producer / consumer

**Producer:** the operator (directives) + the orchestrator (moves-to-consumed). **Consumer:**
`kata-orchestrate` — calls `kata_steer.stop_requested` + `read_active_directives` at each boundary
(see its *Steering channel* step). The reader logic lives here + in `tools/kata_steer.py`, never in
the weight-5 dispatcher prose.
