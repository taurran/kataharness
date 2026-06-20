---
date: 2026-06-20
spec: greater-loop
status: converged (rounds 1–3) — feeds DESIGN.md; one item (testing-model §7) awaits human ratification
tags: [grill-ledger, greater-loop, decisions]
---

# Greater Loop — GRILL LEDGER

Interactive kata-grill, 2026-06-20. Pre-grill locked inputs (from the scoping pass): **modular DESIGN + one
master roadmap · understand-anything graph-runtime-first · anchor ordering on self-end-to-end · plan-mode =
interactive grill.**

## Round 1 — structural spine (module boundaries)
- **GL-R1a — Initiation = NEW `kata-initiate` module** (vs extend bootstrap). Owns the front-half flow; composes
  readiness/grill/bootstrap(config-writer)/context. Bootstrap stays a sub-step. → modularity + own AGENTS.md.
- **GL-R1b — Captured GOAL = NEW durable `INTENT.md`** (vs fold into DESIGN). Frozen hand-off into the harness;
  machine-trackable for closeout. Schema in DESIGN §2.
- **GL-R1c — Closeout = NEW `kata-closeout` module** (vs extend report). Owns satisfied?→commit/push/merge?→
  run-again/new control flow; composes report/understand/handoff/git. `kata-report` stays "reports, never gates."
- **GL-R1d — Modules = `modules/<name>/` dirs each with own `AGENTS.md`** (vs skills+tags). Composed via the
  nested-AGENTS.md rollup kata-orient already supports. Plug-and-play / swappable per platform.

## Round 2 — dynamics (control flow + loop-back)
- **GL-R2a — Driver = thin NEW `kata-loop` conductor** (vs artifact-chained). Sequences the 3 modules + owns the
  loop-back; composes-not-reimplements (kin to kata-sprint). Greater loop is optional (BC).
- **GL-R2b — Spec-to-execute = user bails anytime + agent PROPOSES execute when ready (user confirms)** (vs
  auto-proceed). Matches "user can get tired and say execute, OR grill to fullest until the agent is satisfied."
  Both paths freeze INTENT.md.
- **GL-R2c — understand-anything = offered per run, opt-in, graph-backed** (vs always). Light git/diff fallback
  if the graph runtime is unavailable.
- **GL-R2d — Loop-back = return to initiation WITH context carried** (vs cold restart). New baseline + understand
  map + lessons carried so the next version-up starts informed. "Build something else" = fresh initiation.

## Round 3 — ordering & alignment
- **GL-R3a — First increment = FOUNDATIONS first: F1 wire-eval + F2 graph runtime** (vs initiation-first vs thin
  slice). Closeout + understand need real data + a real graph; build them before the modules.
- **GL-R3b — testing-model = ASSESS necessity (Hermes).** User challenged: *"is this even necessary? what does
  Hermes do?"* **Finding (grounded in `loop-cognition/RESEARCH.md` §2–3):** Hermes has **no grounding gate** —
  weaker than us; it teaches *learning loops*, not a testing model. Our rigor is process-based (fresh-context +
  default-FAIL + mutation/non-vacuity + RESULT.json), built or in F1. **Recommendation: do NOT build a dedicated
  testing-model; fold the rigor into F1; keep "route eval to another model" latent in multi-model.** *If* the user
  decides it IS necessary → align with F1 (their stated fallback). **→ awaiting ratification (DESIGN §7, §12).**
- **GL-R3c — install-portability = configured INTERACTIVELY during initiation.** User: *"this should be
  configured interactively during the initiation via a session that leads users through initiate."* So the
  install-portability **config layer folds into `kata-initiate`** (target/platform/vault selection); per-platform
  installer mechanics remain a sub-component initiation triggers. (Supersedes the brief's "build after" framing
  for the config layer; the installer mechanics + multi-model stay later.)
- **GL-R3d — graph runtime = minimal operational, deepen later** (vs full Graphify parity). tree-sitter +
  generator → `kata.graph.json` per `protocol/graph.md` (Python first); defer the Graphify oracle.

## Convergence
All structural + dynamic + ordering branches resolved. **One open item:** GL-R3b testing-model recommendation
needs human ratification before the DESIGN freezes. Promote GL1–GL? → D87+ at freeze.
