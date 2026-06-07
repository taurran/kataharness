# protocol/handoff.md — durable handoff artifact schema

Canonical shape for the two-way, git-committed handoff produced by [[kata-handoff]]. Unlike the board/state
(machine, `.kata/`), the handoff is a **durable, Obsidian-native** doc (YAML frontmatter + wikilinks +
tags) — it is meant to be read by a human or a fresh agent ([[STANDARDS]] §5).

- **Location:** `.planning/HANDOFF.md` (durable, git-committed BEFORE any compaction/session end).
- **Required sections** (see [[kata-handoff]] for the discipline):
  1. **Read-in order** — exact files, in sequence, to rebuild context (re-anchor on the FROZEN plan).
  2. **State** — branch / commit / green numbers (tests, build, security) with expected values for the
     "confirm green" first action.
  3. **What shipped** — concretely, with paths + commits.
  4. **NEXT STEP — in order** — precise next actions so the resumer starts doing, not deciding.
  5. **Suggested next skills** — which kata-* skills the resumer will likely invoke next.
  6. **Open decisions for the human.**
  7. **Redaction** — confirm no secrets/keys/PII.
- **Frontmatter:** `date`, `branch`, `commit`, `green` (the gate numbers), `tags`.
- **Self-handoff** (write→compact→resume at a context threshold) uses this same schema; prefer a
  **task-boundary** trigger. The self-handoff *automation* is [[kata-selfhandoff]]; the artifact
  shape is this file either way.
