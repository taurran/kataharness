# LESSONS-LEARNED — KataHarness

The kata's memory. Seeded from the CryptoPortfolioPlanner session that birthed this project
(2026-06-05/06) — every one of these is a harness requirement, not a footnote.

- **L1 — Pin line endings (`.gitattributes eol=lf`) from commit #1.** On Windows, `core.autocrlf=true`
  rewrote the working tree to CRLF mid-merge, making a "deterministic" build size drift 259K→266K→270K.
  Build/handoff sizes must be deterministic to be trustworthy signals. *Baked in:* KataHarness shipped
  `.gitattributes` in its first scaffold.
- **L2 — Git worktrees are the right isolation for concurrent code agents.** Building CPP Phase 2 in an
  isolated worktree on a phase branch let work proceed with zero collision against a live `master` in
  another window. *Baked in:* `kata-worktree` is a coordinate-phase primitive.
- **L3 — Shared single-writer state corrupts under concurrency.** Two sessions both wrote `STATE.md` →
  it went stale/contradictory. *Baked in:* single-writer state owned by the plan-guardian + append-only
  board for lateral comms (no last-writer clobber).
- **L4 — Subagents overstep their mandate without structural limits.** A planner subagent committed to a
  research doc mid-run (outside its job). *Baked in:* least-privilege `allowed-tools` in frontmatter
  (evaluators are read-only) + tight task scope — enforce structurally, not by prose.
- **L5 — Default-FAIL + a fresh-context, no-write evaluator earns trust.** The CPP eval caught a real
  blocker the builder missed. *Baked in:* `kata-evaluate`.
- **L6 — Provenance + adversarial validation before findings drive decisions.** An ungated research pass
  (IPO-vacuum) had to be adversarially validated before acceptance. *Baked in:* `source:` frontmatter +
  an evaluate-phase gate before "done."
- **L7 — Converse, don't pop up.** For substantive design decisions, lay out options + a recommendation
  in prose; the human gives richer direction than constrained pickers. (Process note, applies to grilling.)
