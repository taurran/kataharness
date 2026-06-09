# A3 (bootstrap + wiring) — Grill Decision Ledger

> Running ledger for the A3 design grill (per `kata-grill` RUBRIC — checkpoint after every resolved
> branch). Feeds FREEZE (`kata-design-doc`). Each entry: chosen option · rejected alternatives ·
> rationale · provenance. Status of A3 scope is still being grilled.

## Resolved branches

### GB1 — Run-shapes are presets *on top of* the mode axis, not a new axis
- **Chosen:** the four run-shapes (individual / batch / version-up / advanced) are **named presets** —
  each a bundle `(mode, modules[], config-defaults)` that pre-seeds the D24c composition ladder; the user
  can still drill down from any preset.
- **Rejected:** run-shapes as a second top-level axis competing with Essential/Standard/Advanced.
- **Rationale:** keeps the frozen unified axis (D24a) intact; a preset is data, not a code branch.
- **Provenance:** user framed bootstrap's interview around the four shapes; reconciled against D24a.

### GB2 — "Batch" = bakeoff (best-of-N), NOT a task-queue
- **Chosen:** batch preset = the `bakeoff` module (N variants → judge → pick → refine up), Spec B.
- **Rejected:** a multi-task scheduling queue (new machinery, competes with the single-frozen-plan premise).
- **Provenance:** user — "Bake off is what I meant."

### GB3 — "Review of existing project" = version-up (Spec C), NOT a read-only audit
- **Chosen:** the preset = **one-shot feature-addition to a live project without regressing the rest**
  (the Improvement-Kata on existing repos, Spec C).
- **Rejected:** read-only `kata-review` audit over a repo (my recommendation — user corrected it).
- **Rationale/provenance:** user — "Versioning up a project with [a] feature and being able to one-shot the
  feature addition without breaking other aspects of the project. More challenging." Matches Spec C.

### GB4 — Bakeoff composes with version-up (module × run-shape are orthogonal)
- **Chosen:** yes — a baked-off version-up = spawn N candidate feature-implementations, evaluate each for
  *adds-the-feature AND regresses-nothing*, pick the winner. Bakeoff is a module (how many variants);
  run-shape is the target (greenfield vs existing). Orthogonal → composable.
- **Provenance:** user — "Can we also bake off a version update? I'm not sure." Resolved: yes, by orthogonality.
- **Consequence:** reinforces GB1 (modules compose *under* run-shapes).

### GB5 — A3 / A4 cut: version-up is COMMITTED (A4), bootstrap is version-up-aware now
- **Chosen:** split the work.
  - **A3 = the bootstrap brain + greenfield wiring + version-up *fully configurable*.** Readiness eval,
    run-shape router, walk-through-every-config, the D24c ladder, cost preview, write **+ validate**
    `kata.config`, wire `kata-orchestrate` to read config + resolve family→tier. Bootstrap is version-up-aware
    from day one (asks new-vs-existing, takes the repo, writes a correct version-up config that routes to the
    A4 bundle). Includes the *cheap reused tweaks* (context maintain-mode, evaluate regression contract, plan
    existing-file ownership) since those are deltas to skills that already exist.
  - **A4 = the version-up execution bundle** — `kata-graph` (ingestion, GB6) + proving the context-aware
    plan→build→regression-gate runs end-to-end on a real existing repo. **A4 absorbs the old standalone
    "Spec C — version-ups"** (version-up is a run-shape preset on the modes axis, so it belongs to the arc).
    Committed and next-in-line after A3 — *not* deferred.
- **Delta analysis (why this cut):** greenfield vs version-up differ in only TWO places — (1) a context-ingestion
  front-end (`kata-graph`, the "wholly different" part), (2) existing-file-aware planning + a baseline-green
  regression contract (mostly carried in the PLAN + a small `kata-evaluate` flag). Everything else —
  orchestrate, worktree, board, tdd, evaluate-core, handoff, improve, context-maintain — is **reused as-is.**
  Key reuse: `kata-evaluate`'s default-FAIL gate *already is* the "don't break other aspects" guarantee
  (baseline suite + new tests green).
- **Answers to the structural questions:** same orchestrator (D24d, config-driven — not forked); same
  bootstrap (re-entrant: cold-start writes config, later runs read it and offer same/step-up/change-shape —
  one skill, not a first-run-vs-every-run pair); version-up = a preset bundle (GB1), not a parallel machine.
- **Provenance:** user — "version-up needs to be part of this... maybe it should be its own phase... determine
  the scope of difference." Delta analysis resolved it to a contained 2-point difference → clean A3/A4 cut.

### GB6 — `kata-graph` = pre-processing structural map (Graphify nod); version-up's ingestion engine
- **Chosen:** new skill `kata-graph` — builds a compact symbol/dependency map of an **existing** codebase so
  grill/plan/orchestrate ingest a large repo cheaply (token-saving pre-processing). It is the A4 ingestion
  front-end (supersedes the working name `kata-map`). Default backend = agnostic grep/glob/Read; the
  accelerated AST / MCP graph backend stays an **optional adapter binding** (spine #3 — core never hard-deps on
  Graphify). Also reusable for grill/plan/diagnose Phase-0 exploration on large repos.
- **Reframes** the existing BACKLOG "Optional code-navigation (Graphify/MCP)" entry: promoted from
  deferred-optional → **active A4 component** (the skill), while the accelerated backend stays optional.
- **Attribution:** nods to Graphify via `source:` frontmatter (spine #12); OSS-attributed, not barred (D30
  clean-room is AWS-internal-IP only).
- **Provenance:** user — "Graphify is premap to understand and save tokens on executions... call it kata-graph."

### GB7 — `kata-understand` = post-processing comprehension map (desired state)
- **Chosen:** record as a **desired-state** capability — a post-loop comprehension map of a **newly-built**
  codebase that helps the *user* understand/navigate what KataHarness created. ("Understand Anything" nod.)
- **Distinct from `kata-report` (D32):** report synthesizes the *build log* (DESIGN/DAG/diffs/verdicts) and
  lists from-scratch comprehension as a *non-goal*; `kata-understand` *is* that comprehension. Complementary.
- **Scope/sequence:** own later spec or module, post-v0.1 (orthogonal to version-up; about explaining NEW
  builds). Backlog now; not in A3/A4.
- **Provenance:** user — "a version of understand anything that is a post-processing map for new codebases...
  helps the user actually understand what was created."

### GB8 — Mapping skills: research OSS, bake stripped-down minimal steps
- **Chosen:** when planning `kata-graph` (and later `kata-understand`), evaluate against open-source examples
  (repo-mappers: Graphify, aider repo-map / tree-sitter, repomix, gitingest, code2prompt, ctags/Understand;
  comprehension: "Understand Anything"/DeepWiki-class) and bake in **only the necessary, stripped-down steps.**
- **Provenance:** user — "evaluate it against all open source examples; baking in stripped down and necessary steps."

### GB9 — `kata-defer`: in-loop deferral / "nice-to-haves" capture (new optional module)
- **Chosen:** new module `kata-defer` — during a run, any out-of-scope-but-worth-keeping item (nice-to-have,
  post-processing candidate, deferred-for-a-reason) is captured to a run-scoped `DEFERRED.md` instead of being
  silently dropped OR scope-crept into the frozen plan. Artifact compiled at HANDOFF; feeds the project
  backlog / `kata-improve` / post-processing (`kata-understand` may consume it). needs: none; produces: `DEFERRED.md`.
- **Rationale:** the structural complement to the no-drift spine (#1/#2). No-drift forbids acting on tempting
  additions; `kata-defer` gives them a home so the discipline is *sustainable* — parked, not lost, not executed.
  Pressure-release valve for one-shot = no-churn.
- **Name:** `kata-defer` (verb-form; artifact `DEFERRED.md`) — soft; alts `kata-park` / `kata-icebox`.
- **Provenance:** user — "a backlog skill of some sort to track items that weren't necessary to deployment but
  are saved for post-processing... nice to haves... not part of execution."

### GB10 — `kata-graph` / `kata-understand` / `kata-defer` are optional MODULES (not spine)
- **Chosen:** all three are modules — additive, independent, selectable from **any** mode (`kata/module/<m>`);
  each declares needs/produces/slot. The **version-up preset bundles `kata-graph` by default** (ingestion
  engine); otherwise à-la-carte. Advanced-default membership: **TBD** (decide when mode default-bundles are defined).
- **Provenance:** user — "They will be 'optional' or modular skills that the user can select from any mode.
  Unsure if required in advanced — figure out later."

### GB11 — Readiness eval = a separate light skill `kata-readiness`, invoked by bootstrap
- **Chosen:** factor readiness into its own light skill (cost ~1–2) rather than inline it in bootstrap. Two
  scopes: **harness-health** (validator green / skills present / required tools on PATH) + **target-readiness**
  (git repo + clean tree, AGENTS/CONTEXT present, deps installable, existing `kata.config` present → re-entrant
  detection). Bootstrap *calls* it.
- **Rationale:** ≥3 callers — re-entrant bootstrap (every run), orchestrate Standard-fallback (D25), pre-flight
  (D29); a standalone "is my kata env ready?" doctor is independently useful; keeps bootstrap's body lean.
- **Provenance:** user invited the judgment ("part of bootstrap, unless intense enough it needs to be invoked
  by bootstrap"). Reuse + bloat-avoidance → invoked-by-bootstrap.

### GB12 — Config validation = fail-closed load-guard in `kata-orchestrate`, NOT a bootstrap phase
- **Chosen:** no separate post-write validation step in bootstrap (it writes `kata.config` by construction —
  redundant = bloat). Instead `kata-orchestrate` guards on READ: fail-closed if `kata.config` is malformed or
  references a non-existent tier/module/effort (consistent with the default-FAIL spine + validator fail-closed
  philosophy). The real risk is a stale / hand-edited / older-version config on a re-entrant run, which only a
  consumer-side load-guard catches.
- **Maintainer-time (later, backlog):** `tools/validate_skills.py` MAY gain an example-`kata.config` check; not A3.
- **Provenance:** user — "I don't know. Is it necessary? Is it bloat?" → bootstrap-phase = bloat; orchestrate load-guard = lean+necessary.

### GB13 — Bootstrap interview surfaces only run-shape-relevant config fields
- **Chosen:** progressive disclosure — ask only the `kata.config` fields relevant to the chosen run-shape; the
  default→go floor stays fast, advanced fields appear only when the path needs them.
- **Provenance:** user — "Only ones relevant to the run shape."

## A3 design — CLOSED, ready to plan
All grilled branches resolved (GB1–GB13). New skills entering scope: A3 = `kata-bootstrap` + `kata-readiness`
+ `kata-orchestrate` config-read/load-guard. Modules baked as desired-state (backlog): `kata-graph` (A4),
`kata-understand` (post-v0.1), `kata-defer`. Next: branch + `kata-plan` writes the A3 PLAN.
