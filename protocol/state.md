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
  "sprint": { "index": 2, "gateStatus": "green", "openCorrection": false, "boundary": "gated" },
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

## Sprint progression — three tiers (sprint-cadence D81, GB5; git is the source of truth)
For an incremental run (`delivery.shape == "incremental"`), progression lives in **three tiers** with strictly
separated authority — **git is authoritative; the live cache is disposable**:

| Tier | Holds | Lives in | Lifecycle |
|---|---|---|---|
| 1 frozen provenance | `delivery: {shape, policy}` | `kata.config` (git) | bootstrap-set, append-stable, D45-guarded |
| 2 durable trail | per-sprint reports + boundary handoffs + superseding decisions / roadmap amendments | `.planning` Obsidian docs (git) | **authoritative, resumable record** |
| 3 progression cache | `sprint.index`, `gateStatus`, `openCorrection`, `boundary: dirty\|gated` (the fields above) | `.kata/state.json` (gitignored) | single-writer plan-guardian (L3); **churns; rebuilt from tier-2 on re-entry** |

- The `sprint` block above is **tier-3 only** — *disposable and rebuildable*, never authoritative. The
  authoritative record is the committed tier-2 trail.
- **Resume / rebuild rule (R5):** on a fresh session or clone, `kata-readiness` rebuilds tier-3 from the
  git-committed tier-2 trail — **current sprint = which per-sprint reports exist + are gated**;
  `boundary: dirty` (mid-sprint, uncommitted work) ⇒ resume the sprint; `boundary: gated` (sprint gate green,
  awaiting the boundary) ⇒ course-correct. **If the cache corrupts, throw it away and rebuild** — losing
  `.kata/` loses nothing durable.
- **Single-writer still holds (L3):** only the orchestrator writes `.kata/state.json`; `kata-readiness` computes
  the rebuilt state and hands it back, it does not write (T6).
- **Thrash counts (fix-loop-hardening, L2/L4) are NOT here.** The per-area and run-level fix-cycle counts from
  the final-gate fix loop are **orchestrator-transient in-context control state** — deliberately **NOT** persisted
  in `state.json`, **NOT** a board event TYPE, and **NOT** written via `kata_board.update_task`. They are the
  orchestrator's own loop bookkeeping while it runs eval→fix iterations; they are recountable on resume from the
  `DECISION` board lines the orchestrator **writes per fix-cycle** (`NEEDS_WORK fix: <area> cycle <n>`; the
  `DECISION` TYPE already exists — this is the per-fix-cycle cadence, not a new TYPE). A confirmation-pass
  regression counts against the budget; a later-invalidated PASS does **not** zero the count. *(Do not add a
  `state.json` field or a new board TYPE for these counts — that would contradict L2/L4.)*
