# protocol/board.md — append-only coordination board schema

Canonical schema for the machine-coordination board consumed by [[kata-board]] and [[kata-orchestrate]].
Machine state — kept separate from durable Obsidian docs ([[STANDARDS]] §5).

- **Location:** `.kata/board.md` in the target repo's integration worktree.
- **Append-only:** agents append lines; no agent edits or deletes a prior line (no last-writer clobber —
  [[LESSONS-LEARNED]] L3).
- **Line format:** `<ISO-8601-UTC> | <agent-id> | <TYPE> | <task-id> | <one-line message>`
- **TYPE vocabulary:**
  | TYPE | Author | Meaning |
  |---|---|---|
  | `CLAIM` | worker | starting an assigned task |
  | `DONE` | worker | task `<verify>` passed; ready for the orchestrator gate |
  | `BLOCK` | worker | cannot proceed (environment/dependency) |
  | `ESCALATE` | worker | the frozen plan is unclear/wrong — needs an orchestrator decision (never re-plan) |
  | `NOTE` | worker | lateral info for peers |
  | `DECISION` | orchestrator only | a deliberate ruling resolving a BLOCK/ESCALATE |
  | `PROGRESS` | worker | granular progress heartbeat; `msg` carries `<step>/<n> <label>` (e.g. `3/5 writing tests`) |
- **PROGRESS is opt-in, ignored by the coordination logic, and read only by the dashboard** — the DECISION/BLOCK/ESCALATE invariants are unchanged.
- **Invariants:** workers never author `DECISION`; every `BLOCK`/`ESCALATE` is answered by a `DECISION`
  before the task resumes; the board is the countable audit trail for the drift ledger.
