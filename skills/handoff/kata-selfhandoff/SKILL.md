---
name: kata-selfhandoff
description: >-
  In-session context-reclamation: at a configurable threshold (task-boundary preferred), write a durable
  handoff, compact/reset, and resume re-anchored on the frozen plan — with zero task loss. Use to survive
  long runs without context rot. It is the TRIGGER POLICY only; it delegates the handoff artifact to
  kata-handoff and never re-implements the format.
license: Apache-2.0
version: 0.1.0
category: handoff
status: experimental
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

## When to fire (prime-frame trigger — supersedes D8's % clause, B1/D83)
- **Trigger at the model-resolved prime-frame fraction**, not a user-set naive % (sprint-cadence D83/B1: the
  threshold moves from D8's user-set percentage → the **prime frame** = the model's recommended effective
  working band, adapter-resolved to real tokens; see `protocol/config.md` *Prime-frame sizing*). Do **not**
  hard-code a number here — read the policy.
- **D8's principles survive.** The default is still **generous, not timid** — the failure mode this skill is
  explicitly tuned *against* is wrapping up sessions early ([[LESSONS-LEARNED]]; user-flagged). Err toward
  continuing; the prime frame already reserves headroom, so do not pre-empt it.
- **Prefer a task boundary.** Fire *between* tasks/waves, never mid-task — mid-task compaction loses the
  in-flight state that's hardest to reconstruct. If the threshold trips mid-task, finish (or cleanly
  checkpoint) the task first.
- **Intra-sprint refresh (sprint-cadence B1).** In an incremental run, self-handoff also runs **inside** a
  sprint — a pure context refresh with **no human gate and no drift** (it is not a boundary). The sprint is the
  one-shot mechanism + a *planned* stop at prime-frame **sprint** boundaries for gate+report+course-correct
  ([[kata-sprint]]); intra-sprint self-handoff is the *unplanned* refresh that keeps the current sprint going.
  Same primitive (the prime frame), two policies.

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
