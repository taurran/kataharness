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

## Boundary handoff (sprint-cadence D79/D81 — the per-sprint variant)
At a **sprint boundary** ([[kata-sprint]]), the handoff is **this same schema plus** the sprint-specific fields,
so the next sprint (or a fresh session) re-enters at the boundary with no loss:
- **State** additionally carries the **sprint gate result** (the green numbers that closed the sprint) and the
  **sprint index** (which sprint just gated, what is next in the roadmap).
- **Open decisions** additionally carries any **drift-labelling** raised at the boundary (G2 — each pending
  course-correction classified by reach: next-sprint-plan / roadmap-reshape / DESIGN-amendment), surfaced for the
  human, never auto-applied.
- **Tier-1 rule (T1):** a sprint boundary **supersedes** a coincident self-handoff — if the prime-frame refresh
  threshold trips exactly at a boundary, write **one** boundary handoff (not two artifacts).
- The boundary handoff is committed to the **tier-2 durable trail** ([[protocol|state]] §sprint-progression);
  it is what `kata-readiness` reads to rebuild progression on resume. Same durable-first discipline as above.
