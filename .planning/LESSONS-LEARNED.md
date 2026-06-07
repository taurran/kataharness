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
- **L8 — `kata-grill` must be FAR deeper + GSD-structured, not a one-shot decision list.** Surfaced live
  during the WoZ on CPP Phase 3 (2026-06-06): the manual grill (4 decisions, each "options + a
  recommendation," resolved in a single pass) did **not** meet the bar for this harness's
  planning/discussion phase. The user's explicit spec for the real `kata-grill`:
  - **GSD-format interaction**: questions presented as **selectable multiple-choice the user can click
    through OR answer in plain text** (the AskUserQuestion pattern — structured options *with* a free-text
    escape, which is *compatible* with [[L7]]: options are offered, but typing is always allowed; it is the
    constrained-picker-with-no-escape that L7 forbids, not structure itself).
  - **Far more in-depth and demanding** — iterative, multi-round interrogation that does not stop at the
    first plausible answer; it pushes until the design is *very specific* and genuinely speaks to the user's
    spec. One pass is not a grill.
  - **Refined and user-friendly like GSD** (the discuss/spec-phase UX) **but with the thoroughness, logic,
    and doc-baking of mattpocock `grill-with-docs`** — ground every branch in the source docs, and bake the
    resolved decisions back into a durable design artifact as it goes.
  - **Output bar**: a *very specific final design contract* derived from relentless, doc-grounded
    questioning — not a checklist the orchestrator pre-answered for the user.
  *Baked in:* this is a hard requirement on `kata-grill` (and `kata-context`/`kata-design-doc`) when built
  in v0.1. The WoZ proved the *method shape*; it also proved the **grill step is the weakest link** and is
  the priority to get right. See `[[kata-grill]]`.
