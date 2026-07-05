---
name: kata-readiness
description: >-
  Fast pre-run readiness check: is the kata harness healthy (validator green, skills present, required tools
  on PATH) and is the target ready (git repo + clean tree, AGENTS/CONTEXT present, deps installable, an
  existing kata.config = re-entrant run)? Also rates the priming prompt's richness to recommend a grill depth
  (skip|light|standard|full, D71). Invoke from kata-bootstrap before composing a run, or standalone as
  an "is my kata environment ready?" doctor.
license: Apache-2.0
version: 0.2.2
category: coordinate
status: beta
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Bash]
source: >-
  new (KataHarness original); pattern echoes environment "doctor" checks (e.g. brew/flutter doctor) — abstract,
  no external code adapted
tags:
  - kata/coordinate
  - kata/spine
  - readiness
  - preflight
---
# kata-readiness — is the harness + target ready to run?

A **read-only** check (no Write — it returns a verdict to its caller, it does not author artifacts). Two scopes,
each a checklist; report PASS / WARN / BLOCK per item and an overall verdict.

## Scope 1 — harness health
- Skills tree present and the validator is green (`tools/` → `uv run python validate_skills.py`, exit 0).
- Required host tools on PATH for the chosen run (e.g. `git`, the test runner, `uv`/language toolchain).
- A subagent-capable host is available (orchestrate's dispatch binding).

## Scope 2 — target readiness
- Inside a git repo with a **clean working tree** (uncommitted churn ⇒ WARN — execution wants a clean fork).
- `AGENTS.md` (and `CONTEXT.md` if the run plans against one) present, or flag that grill must create them.
- Declared dependencies are installable from an allowed registry (defers the actual install to pre-flight, D29).
- **Re-entrant detection:** if a `kata.config` already exists at the branch root, report it (its `mode`,
  `runShape`, `modules`) so bootstrap offers "same as last / step up / change shape" rather than cold-start.
- **Pre-v0.2.1 config WARN (context autonomy, CA-L34) — INCREMENTAL shapes only.** This check runs at
  **every bootstrap entry** (including Phase 0b routing), but fires ONLY when the re-entrant config's
  `delivery.shape == "incremental"` AND it **lacks the `contextAutonomy` key** (a pre-v0.2.1 config):
  surface a WARN: "pre-v0.2.1 config lacks contextAutonomy — written at next composition (Phase 3) or
  opt in by config edit." This is **surfaced, never silent, and never a retroactive flip** — readiness
  reports it; the key is only ever written when bootstrap next composes the config (Phase 3's
  write-all-fields-by-construction, matching kata-bootstrap's write-at-next-touch), or when the user
  opts in by editing the config. Honest posture — **not a scare-WARN**: sprint boundaries ALREADY
  rotate by design (the boundary handoff), so such a run is not stranded; only intra-sprint refresh is
  absent. **One-shot shapes are EXEMPT from this WARN** (final-review fold): rotation is UNCONDITIONAL
  there and never consults the key (CA-L33/D147), so "lacks contextAutonomy" describes nothing absent —
  a WARN would misstate the run's posture and invite a pointless config edit.
- **Version-up gate:** for a version-up run (`target.kind == existing`), **BLOCK if tree-sitter is not
  available** — the kata-graph ingestion (seeding + blast-radius) needs AST; there is no inert grep-mode
  fallback for version-up.
- **Sprint-progression detection (sprint-cadence D81, T5).** For an incremental run
  (`delivery.shape == "incremental"`, `protocol/config.md`), detect where the run stands: is there an **open
  roadmap artifact**, what is the **current sprint index**, and is the boundary **dirty** (mid-sprint,
  uncommitted work ⇒ *resume the sprint*) or **gated** (sprint gate green, awaiting the boundary ⇒
  *course-correct*)? **Rebuild the tier-3 progression cache from the git-committed tier-2 trail**
  (`protocol/state.md` §sprint-progression): current sprint = which per-sprint reports exist + are gated. This
  is what makes a fresh session or clone resumable (R5) — the `.kata/` cache is disposable; the committed trail
  is authoritative. Report the rebuilt `{sprintIndex, gateStatus, boundary: dirty|gated}` in the verdict.
  **Read-only:** readiness *computes* the rebuilt state and hands it to the orchestrator (the single writer,
  L3) — it never writes `.kata/` itself. One-shot runs (no `delivery` / `shape: one-shot`) skip this entirely.
- **Lost-run detection (R5 extension — restore-hardening B2, D134).** When the sprint-progression rebuild
  (above) finds `.kata/` absent or stale but `refs/kata/trail` is present, treat this as a *lost-run* condition
  and extend the rebuild to include the durable board:
  1. Read `board.md` from `refs/kata/trail` (`git cat-file -p refs/kata/trail:board.md`) and fold it to the
     frontier using the canonical concurrency reduce (`protocol/board.md` canonical snippet, `fold_board` in
     `tools/kata_restore.py`).  The folded board CORROBORATES in-flight ownership but **never gates** the
     re-dispatch set.
  2. Re-dispatch set = all task-ids in the frozen PLAN **minus** those with an integration commit on the
     integration branch (mapped via the `Kata-Task: <id>` trailer in each commit — `collect_integrated_tasks`
     in `tools/kata_restore.py`).  **Tier-2 (integration history) is AUTHORITATIVE for DONE.**
     A task absent from the board (not even a CLAIM) but non-integrated is re-dispatched; a task with a board
     `DONE` but no integration commit is also re-dispatched.  Gating on board CLAIMs would silently drop
     early-wave tasks a crash never durably recorded — the PLAN + integration history are the only always-durable
     sources.
  3. Report the re-dispatch set + board frontier in the verdict (flagged as `lost_run: true`).  Call
     `kata_restore.restore(repo_root, plan_path, integration_branch)` to materialize the cleanup (C2 stale
     branch + worktree prune) and write the board back to `.kata/board.md` **without rotation** (no archive
     file — see R5-norotate below).

     **Caller contract for `kata_restore.restore()`:**
     - `plan_path` — resolved to the run's frozen PLAN at `.planning/specs/<spec-name>/PLAN.md`.
       Read the active spec name from `kata.config` or discover the most recent frozen PLAN under
       `.planning/specs/`.  Pass the absolute path.
     - `integration_branch` — defaults to `"integration"` for all standard kata runs.  Override
       only when `kata.config` names a different branch.
  **Read-only on the verdict path:** readiness calls `kata_restore.restore` which handles the `.kata/` writes
  only on the confirmed lost-run code path; the readiness verdict itself stays read-only.
- **R5-norotate:** a *resume* MUST NOT rotate `.kata/board.md` to `.kata/board.<utc>.archive.md`.  Rotation
  is a run-start action ([[kata-orchestrate]] loop preamble); a resume restores the orphan-ref board into
  place and skips rotation entirely.  Rotating would archive the recovered CLAIM/DONE lines and empty the
  live board, defeating the restore.

## Scope 3 — priming-prompt richness → recommended grill depth (D71)
Assess the **priming prompt** (the human's original spec for this run) and recommend a starting **grill-depth
dial** position (`skip | light | standard | full` → `tiers["kata-grill"]` per `protocol/config.md`). This is a
**recommendation, not a decision** — bootstrap surfaces it and the human always chooses. Read the prompt (and any
`AGENTS.md`/`CONTEXT.md` it leans on) and rate richness vs ambiguity:
- **Rich + unambiguous** (concrete acceptance criteria, named interfaces, decided edge behavior, few open
  branches) ⇒ recommend **skip** or **light** — little for a grill to interrogate; the autonomous floor suffices.
- **Moderate** (clear goal, several under-specified branches — boundaries/magnitudes/failure behavior) ⇒
  recommend **standard** (the default).
- **Thin / high-ambiguity / hard-to-reverse / production-freeze** ⇒ recommend **full**.
Report the recommendation **with its one-line rationale** (what in the prompt drove it — the open branches you
counted). Never grade the prompt's *quality*; only its decision-completeness for one-shotting. This scope never
writes — the recommendation is returned to bootstrap.

## Verdict
Return a compact structured verdict (overall PASS/WARN/BLOCK + the per-item findings + the re-entrant
`kata.config` summary if any + the **recommended grill depth + rationale**). **BLOCK** = a hard stop bootstrap
must resolve before composing a run; **WARN** = surface to the user but allow proceed. The grill-depth
recommendation is advisory (never BLOCK/WARN). The check never installs, never writes, never mutates the repo.
