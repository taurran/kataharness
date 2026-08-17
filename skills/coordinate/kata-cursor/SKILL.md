---
name: kata-board
description: >-
  Append-only message board for orchestrator↔subagent and lateral peer coordination. Use whenever multiple
  agents work the same plan and must claim tasks, report done, or ESCALATE an unknown without re-planning.
  An agnostic, file-based reimplementation of the Claude Agent Teams mailbox — append-only so no writer
  clobbers another (the failure mode of shared single-writer state).
license: Apache-2.0
version: 0.1.0
category: coordinate
status: beta
agnostic: true
cost-weight: 2
allowed-tools: [Read, Bash]
source: adapted-from Claude Agent Teams protocol (agnostic file reimplementation); CryptoPortfolioPlanner LESSONS-LEARNED L3
tags:
  - kata/coordinate
  - kata/spine
  - board
  - mailbox
  - escalation
  - protocol
---

# kata-board — append-only coordination, no clobber

Shared single-writer state corrupts under concurrency ([[LESSONS-LEARNED]] L3). The board is **append-only**:
every agent *appends* a line; no one rewrites existing lines. The orchestrator reads the whole board to
decide. This carries lateral comms AND the **escalation channel** that keeps workers from re-planning.

## Schema (canonical: `protocol/board.md` — don't restate it elsewhere)
`.kata/board.md` in the target repo's integration worktree (machine state — separate from durable Obsidian
docs, [[STANDARDS]] §5). One message per line, append-only, newest last:
```
<ISO-8601-UTC> | <agent-id> | <TYPE> | <task-id> | <one-line message>
```
`TYPE` ∈ `CLAIM · DONE · BLOCK · ESCALATE · NOTE` (workers) and `DECISION` (orchestrator only). Full
definitions are in `protocol/board.md`, which is the source of truth.

## Append — one whole line, atomic, never edit a prior line
The append must be **atomic** so concurrent writers don't interleave; the mechanism is the adapter's, the
invariant (one whole line, append-only) is the contract.
```
# POSIX (illustrative — a single short write to an O_APPEND fd is atomic):
printf '%s | %s | %s | %s | %s\n' "$(date -u +%FT%TZ)" "$AGENT" "$TYPE" "$TASK" "$MSG" >> .kata/board.md
# Windows PowerShell:
Add-Content .kata/board.md "$([DateTime]::UtcNow.ToString('o')) | $AGENT | $TYPE | $TASK | $MSG"
```
If a host cannot guarantee atomic multi-writer append, use the v0.1 default: **orchestrator-as-sole-writer**
— workers return their line in their result and [[kata-orchestrate]] appends it.

## Discipline
- **Workers** may append CLAIM / DONE / BLOCK / ESCALATE / NOTE. They MUST NOT append DECISION and MUST NOT
  edit prior lines.
- **Workers never re-plan.** If the frozen plan is unclear or seems wrong, append `ESCALATE` with the exact
  ambiguity and STOP — do not improvise (this is the no-drift spine).
- **Orchestrator** ([[kata-orchestrate]]) reads the board each cycle, and is the only author of `DECISION`.
  Every `BLOCK`/`ESCALATE` must be answered by a `DECISION` before that task resumes.
- **v0.1 claim model:** the orchestrator *assigns* tasks; workers do NOT self-select, so there is no claim
  race. `CLAIM` is a worker *announcing* it has started its assigned task — not a lock. A file-locked
  self-claim ledger (`kata-tasklist`) is backlog, needed only if workers ever self-select tasks.
- The board is the audit trail for the drift ledger: escalations and decisions are countable evidence.
