---
name: kata-board
description: >-
  Append-only message board for orchestrator↔subagent and lateral peer coordination. Use whenever multiple
  agents work the same plan and must claim tasks, report done, or ESCALATE an unknown without re-planning.
  An agnostic, file-based reimplementation of the Claude Agent Teams mailbox — append-only so no writer
  clobbers another (the failure mode of shared single-writer state).
version: 0.1.0
category: coordinate
status: experimental
agnostic: true
allowed-tools: [Read, Bash]
source: adapted-from Claude Agent Teams protocol (agnostic file reimplementation); CryptoPortfolioPlanner LESSONS-LEARNED L3
tags: [coordinate, protocol, mailbox, escalation]
---

# kata-board — append-only coordination, no clobber

Shared single-writer state corrupts under concurrency ([[LESSONS-LEARNED]] L3). The board is **append-only**:
every agent *appends* a line; no one rewrites existing lines. The orchestrator reads the whole board to
decide. This carries lateral comms AND the **escalation channel** that keeps workers from re-planning.

## File
`.kata/board.md` in the target repo's integration worktree (machine coordination state — kept separate from
durable Obsidian docs, per [[STANDARDS]] §5). One message per line, newest appended at the end.

## Message format
```
<ISO-8601> | <agent-id> | <TYPE> | <task-id> | <one-line message>
```
`TYPE` ∈ `CLAIM` (starting a task) · `DONE` (task verify passed, ready to gate) · `BLOCK` (cannot proceed) ·
`ESCALATE` (the plan is unclear/wrong — needs an orchestrator decision) · `NOTE` (lateral info for peers) ·
`DECISION` (orchestrator-only: a deliberate ruling resolving a BLOCK/ESCALATE).

## Append (never edit)
```bash
printf '%s | %s | %s | %s | %s\n' "$(date -u +%FT%TZ)" "$AGENT" "$TYPE" "$TASK" "$MSG" >> .kata/board.md
```

## Discipline
- **Workers** may append CLAIM / DONE / BLOCK / ESCALATE / NOTE. They MUST NOT append DECISION and MUST NOT
  edit prior lines.
- **Workers never re-plan.** If the frozen plan is unclear or seems wrong, append `ESCALATE` with the exact
  ambiguity and STOP — do not improvise (this is the no-drift spine).
- **Orchestrator** ([[kata-orchestrate]]) reads the board each cycle, and is the only author of `DECISION`.
  Every `BLOCK`/`ESCALATE` must be answered by a `DECISION` before that task resumes.
- The board is the audit trail for the drift ledger: escalations and decisions are countable evidence.
