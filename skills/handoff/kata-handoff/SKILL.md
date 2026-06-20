---
name: kata-handoff
description: >-
  Write a durable, two-way, git-committed handoff so work survives session/agent/tool boundaries and
  compaction with zero loss. Use at the end of a session, when handing between agents/tools, or before a
  context reset — anchored on the frozen plan so the resumer re-enters mid-stream without re-deriving.
license: Apache-2.0
version: 0.1.0
category: handoff
status: experimental
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Write, Bash]
source: adapted-from mattpocock/skills {handoff} + Anthropic reset-with-handoff / compaction guidance
tags:
  - kata/handoff
  - kata/spine
  - handoff
  - context
  - durability
---

# kata-handoff — durable, two-way, plan-anchored

Handoffs flow every direction — session↔session, agent↔agent, tool↔tool. They are **durable artifacts**
(git-committed, Obsidian-readable), not chat scrollback, so compaction or a fresh session can't lose them
([[LESSONS-LEARNED]]: durable-to-git before any compaction).

## A handoff MUST contain
1. **Read-in order** — the exact files to load, in sequence, to rebuild context (canonical instructions →
   DESIGN → STANDARDS → STATE → this file). Re-anchor on the **frozen plan**, not a vague summary.
2. **State** — branch / commit / green numbers (tests, build, security). The first action on resume is
   usually "confirm green," so give the expected numbers.
3. **What shipped** — concretely, with paths; what is committed where.
4. **NEXT STEP — in order** — the precise next actions, so the resumer starts *doing*, not deciding.
5. **Suggested next skills** — which kata-* the resumer will likely invoke next (orients them fast).
6. **Open decisions for the human** — anything genuinely blocked on a person.
7. **Redaction** — confirm no secrets/keys/PII (and redact if any).

## Discipline
- **Durable first, compact second.** Write + git-commit the handoff BEFORE any `/compact` or session end.
  *(Deliberate inversion of mattpocock handoff, which saves to OS temp — this harness goes durable / in-workspace
  / git so handoffs survive as audit artifacts and cross sessions, agents, and tools.)*
- **Point to paths; don't re-derive.** List artifacts by path so the resumer reads, not re-discovers.
- **Anchor on the plan.** A resumer must be able to re-enter the loop at the exact task boundary.
- Keep it dense (caveman-style compression is fine) but lossless on the NEXT STEP and the green numbers.

## Orientation tie-in — author for the read side ([[kata-orient]], `protocol/orientation.md`)
A handoff is the **write** half; [[kata-orient]] is the **read** half that loads it into a fresh subagent. Author
the handoff so it maps **directly** into the orientation tiers — no re-derivation at load time:
- **Read-in order** → orientation **context** pointers (the files to roll up).
- **State** (branch/commit/green numbers) + **NEXT STEP** → orientation **volatile** (assignment + current state).
- **Suggested next skills** → the **task-type** hint kata-orient classifies on.
- **Open decisions for the human** → kata-orient's **human-required** questions (surfaced, not auto-resolved).
Keep these sections present and labelled so the mapping is mechanical. A handoff that follows this shape is
**directly loadable** by kata-orient; the two compose without loss (the two-way handoff, spine #5).

Self-handoff at a context threshold (write → compact → resume) is a related capability; prefer a
**task-boundary** trigger over an arbitrary % so no mid-task state is lost. (Automated by [[kata-selfhandoff]].)

## Boundary handoff — the sprint-cadence variant ([[kata-sprint]], `protocol/handoff.md`)
At a **sprint boundary**, [[kata-sprint]] composes a handoff that is **this same artifact plus** the sprint
fields defined in the [[protocol|handoff]] schema's *Boundary handoff* section — do not re-derive the shape,
point to it:
- **State** also carries the **sprint gate result** (the green numbers that closed the sprint) + the **sprint
  index** (what just gated, what is next on the roadmap).
- **Open decisions** also carries the boundary **drift-labelling** (G2 — each pending course-correction
  classified by reach), surfaced for the human, never auto-applied.
- A boundary handoff **supersedes** a coincident self-handoff (T1): at a boundary, write **one** artifact.
The one-shot/session handoff above is unchanged; this is purely additive for incremental runs.
