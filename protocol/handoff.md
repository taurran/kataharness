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
- **Frontmatter:** `date`, `branch`, `commit`, `green` (the gate numbers), `tags`, and additive
  `kind: manual|self|boundary` (provenance, CA-L21). A **pre-existing HANDOFF.md without `kind:`**
  reads as **unknown kind; never gates** (§4 row 11) — the field is purely additive.
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

## Handoff taxonomy & provenance (CA-L21)
- **(1) TERMINOLOGY (normative — glossary "handoff"):** a handoff = the session-boundary durable artifact
  (`.planning/HANDOFF.md` family) ONLY; dispatch briefs, worker final reports, and escalation payloads are
  agent-exchange artifacts, never "handoffs".
- **(2) PROVENANCE:** HANDOFF.md frontmatter gains additive `kind: manual|self|boundary` — who wrote it:
  a human-directed [[kata-handoff]] write is `manual`, a [[kata-selfhandoff]] cycle writes `self`, a
  [[kata-sprint]] boundary writes `boundary`.
- **(4) REFRESH:** an over-threshold refresh **overwrites** HANDOFF.md + commits (history lives in git);
  **T1 extended** — any coincident boundary handoff supersedes a same-boundary self-refresh (base rule
  above, this section's Tier-1 rule).
- **(6) NO new artifact formats** — everything is additive to this file + [[kata-handoff]]; there is no
  second schema.

## Staleness rule (CA-L19)
STRICT: any board `DONE`/`DECISION` line **newer** than the HANDOFF.md git commit demotes the handoff from
sole-anchor to context-input; the [[kata-orient]] 3-tier rebuild becomes authoritative. Comparator = newest
board DONE/DECISION ISO-8601-UTC line timestamp ([[protocol|board]] line grammar, `board.md:9`, verified) vs
HANDOFF.md's git commit timestamp, strict `>`; same-second ties favor the handoff. N=1 semantics; **no
tunable**. Trail-ref independent; no reliance on `@sha` presence.

**Clock-skew note (freeze-gate fold #10):** the comparator crosses clock domains — board lines carry writer
PROCESS clocks ([[protocol|board]]'s stated single-host assumption), the handoff carries the git COMMITTER
clock. Acceptable on a single host at this rule's granularity; the strict `>` + ties-favor-the-handoff
convention is also the skew posture (a same-second ambiguity never demotes). Multi-machine runs re-visit this
with the board's own documented revisit item.
