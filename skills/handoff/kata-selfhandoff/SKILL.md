---
name: kata-selfhandoff
description: >-
  In-session context-reclamation: at the model-resolved prime-frame threshold (task-boundary preferred), write
  a durable handoff, compact/reset, and resume re-anchored on the frozen plan — with zero task loss. Use to
  survive long runs without context rot. It is the TRIGGER POLICY only; it delegates the handoff artifact to
  kata-handoff and never re-implements the format.
license: Apache-2.0
version: 0.2.1
category: handoff
status: beta
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Write, Bash]
source: adapted-from Anthropic compaction guidance + mattpocock caveman compression
tags:
  - kata/handoff
  - kata/spine
  - self-handoff
  - compaction
  - context
---

# kata-selfhandoff — reclaim context without losing the thread

This is the active remedy for context rot (spine #5). It owns only the **trigger policy + the compact/resume
mechanics** — the durable artifact itself is written by [[kata-handoff]] (one format, [[protocol|handoff]]
schema). Do not duplicate the handoff template here.

## When to fire (the trigger is now WIRED — supersedes D8's % clause, B1/D83)
- **The trigger source is now concrete (context-autonomy CA-L7).** This wires the long-standing prime-frame
  policy to a live gauge — SR-1: *a gauge wired to an existing policy; no new threshold concept is invented.*
  Trigger = **0.70 `[TUNABLE]` × host-reported effective window** (CA-L5 — the denominator is the gauge's
  `context_window.total_tokens`, post-cap: a capped session's real frame IS the cap). One key
  (`contextTrigger`, §2), shown in bootstrap's **advanced drawer**, **never interactively asked** (no new
  dial). It is read via the gauge (`kata_gauge`) and evaluated at **wave/frontier boundaries by the conductor**
  ([[kata-orchestrate]]) — this skill states the policy; the conductor fires it. On Claude, a **mechanical
  per-turn check** additionally enforces this once the hook chain is installed via `kata_install.py
  --install-hooks` (the UserPromptSubmit gauge-check hook, CG-L1/D152); without the deployed chain the
  boundary check remains conductor prose. Do **not** hard-code a number
  at the call site — read `contextTrigger` (default `0.70` when absent).
  - **Smart-zone framing (CA-L7).** The operating target is the **smart zone** — *above the context floor*
    (kata-orient 3-tier load complete), *below the rot ceiling*. A note for 1M frames: a lower value is one
    config edit away (`contextTrigger`).
  - **D83 stays intact (CA-L8, supersede-never-rewrite).** The prime-frame **0.40** fraction remains the
    **sprint-sizing** fraction, unchanged (`protocol/config.md` *Prime-frame sizing*); the per-role one-shot
    self-handoff threshold source is now this spec's `contextTrigger`. **Same primitive lineage, two
    policies** — no rewrite of D83.
- **D8's principles survive — generous, not timid (CA-L13).** The default is still **generous, not timid** —
  the failure mode this skill is explicitly tuned *against* is wrapping up sessions early ([[LESSONS-LEARNED]];
  user-flagged). **Early exit is a risk equal to rot.** Err toward continuing; the trigger already reserves
  headroom, so do not pre-empt it. This is graded: the acceptance suite includes a **NO-FIRE case** (CA-A5) —
  a session *under* threshold produces **zero handoff churn**.
- **Prefer a task boundary.** Fire *between* tasks/waves, never mid-task — mid-task compaction loses the
  in-flight state that's hardest to reconstruct. If the threshold trips mid-task, finish (or cleanly
  checkpoint) the task first.
- **Shape policy — when the trigger is even consulted (CA-L32/L33).** In a **one-shot** run rotation is
  **UNCONDITIONAL** — the `contextAutonomy` key **is not consulted**; this includes **pre-v0.2.1 configs** (the
  deliberate BC departure named in D147: the behavior is protective, additive, and was ALWAYS mandated by this
  prose — it was simply never wired). In an **incremental** run, `contextAutonomy: "on"|"off"` governs
  **intra-sprint refresh only**. Degradation is always graceful (CA-L6): no gauge/hooks ⇒ deterministic
  rotation, never "assume infinite context."
- **Intra-sprint refresh (sprint-cadence B1).** In an incremental run, self-handoff also runs **inside** a
  sprint — a pure context refresh with **no human gate and no drift** (it is not a boundary). The sprint is the
  one-shot mechanism + a *planned* stop at prime-frame **sprint** boundaries for gate+report+course-correct
  ([[kata-sprint]]); intra-sprint self-handoff is the *unplanned* refresh that keeps the current sprint going.
  Same primitive (the prime frame), two policies.

## Reset ownership (CA-L14) — kata owns the schedule, the host owns the mechanism
**Host compaction is the SOLE reset mechanism on Claude** (no programmatic `/compact` exists). **Kata owns the
SCHEDULE + DURABILITY** — the threshold, handoff freshness, and recommended backstop placement; **the host owns
the MECHANISM.** The "compact / reset" step below is the host act arriving *on kata's schedule*, not a kata
call. Platforms with a respawn primitive treat rotation as a kata-initiated respawn. **There is no conductor
self-compaction leg.**

## The cycle
1. **Write** the durable handoff via [[kata-handoff]] (read-in order, state + green numbers, NEXT STEP in
   order, suggested next skills). Git-commit it **before** compacting — durable first, always.
2. **Compact / reset** the context.
3. **Resume** from the handoff: confirm green, then **re-anchor on the frozen plan** and re-enter the loop at
   the exact next task boundary. The resumer starts *doing*, not re-deriving.

## Compression
Use caveman-style compression in the handoff (dense, telegraphic) — but **lossless on the NEXT STEP and the
green numbers**. Density is for the narrative; the recovery path must be exact.

## What it must NOT do
- Not wrap up early "to be safe" (the anti-pattern). Continuing is the default; handoff is the exception.
- Not fire mid-task. Not re-implement the handoff format (delegate to [[kata-handoff]]).
