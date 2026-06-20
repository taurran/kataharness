# protocol/state.md — single-writer run state schema

Canonical schema for the live run state owned by the plan-guardian ([[kata-orchestrate]]). Machine state —
kept separate from durable Obsidian docs ([[STANDARDS]] §5).

- **Single writer.** ONLY the orchestrator writes this file. Workers never write it (they append to
  [[kata-board]]). This is the fix for the shared-state corruption in [[LESSONS-LEARNED]] L3.
- **Location:** `.kata/state.json` in the target repo's integration worktree.
- **Shape:**
```json
{
  "plan": ".planning/phases/<id>/<plan>.md",
  "forkPoint": "<commit>",
  "integrationBranch": "<branch>",
  "wavesDone": ["wave1"],
  "tasks": { "T1": "gated", "T2": "in-progress", "T3": "assigned", "T4": "blocked" },
  "gate": { "tests": "244/0/0", "build": "deterministic 322511", "security": "0" },
  "driftLedger": { "unauthorizedDeviations": 0, "escalations": 0, "interventions": 0 },
  "candidates": [ { "name": "kata-foo", "status": "grounded", "groundingVerdict": "GROUND" } ],
  "updatedUtc": "<ISO-8601>"
}
```
- **Task status vocabulary:** `assigned → in-progress → done(worker) → gated(orchestrator) → integrated`;
  plus `blocked` (awaiting a board DECISION).
- **Candidate (managed-learning) lifecycle — loop-cognition L5:** an agent-distilled candidate moves
  `distilled → grounded` (passed the grounding gate, D33) `→ promoted | sandboxed | rejected` (the human gate
  [[kata-promote]] at session end). `candidates[]` tracks them by `name` + lifecycle `status` (+ the grounding
  verdict). The candidate *artifacts* live in `<agentSkills.dir>/candidates/` (outside the repo); this array is
  only the run-state pointer so the orchestrator surfaces open candidates at handoff for `kata-promote`. Absent
  `agentSkills.dir` ⇒ no candidates (no-op).
- The orchestrator rewrites this atomically at each checkpoint; the board is the append-only event log, this
  is the current-truth snapshot.
