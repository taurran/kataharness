---
title: "restore-hardening — BUILD PLAN (wave DAG, disjoint ownership, TDD)"
status: FROZEN PLAN (2026-06-30) — derived from DESIGN.md (SHIP after 3 adversarial gate passes); build order is binding
spec: restore-hardening
design: DESIGN.md (this plan implements A1–A2 + B1–B3, closes Gaps 1–3, records D133/D134/D135)
increments: A (discoverability — ships + proven FIRST, zero spine risk) → B (durable restore — spine-touching; hook LAST)
parallelism: tasks WITHIN a wave have DISJOINT file ownership — no two parallel tasks touch the same file
tags: [plan, frozen, restore-hardening, wave-dag, disjoint-ownership, tdd, split-increments]
---

# restore-hardening — BUILD PLAN

Two increments, gated independently. **Increment A ships and is proven FIRST** (adapter-clean, no dependency on
the spine). **Increment B** is the spine-touching durable-restore work; its **hook is built LAST** (it cannot be
proven before the trail it commits exists). TDD every task: failing test first, default-FAIL, no task done until
its tests are green and the wave gate passes. **Frozen-five MD5-verify** after any `kata_install.py` work.
**bump-on-modify** every edited SKILL.md.

---

## INCREMENT A — discoverability (ship + prove first)

### WAVE A1 — commands + installer (parallel; disjoint ownership)

#### A1-a — six pointer commands  ·  OWNS: `adapters/claude/commands/*.md` (new dir, 6 files)
- Create `adapters/claude/commands/`: `kata.md` (static index — the one new artifact, lists the other five, no
  logic), `kata-start.md`→`kata-initiate`, `kata-onboard.md`→`kata-onboard`, `kata-resume.md`→`kata-orient`
  (then `kata-handoff`), `kata-status.md`→`kata-board`, `kata-validate.md`→`kata-validate`.
- Each file = frontmatter (`description`, optional `argument-hint`) + the FROZEN pointer body (identical shape,
  DESIGN A1): *"Invoke the `<skill>` skill to <purpose>. Pass through: $ARGUMENTS. Do not improvise; if the skill
  is unavailable, say so."* **Zero logic** — a skill bump must never require a command edit.
- **Proof:** each command names its exact registered skill; `/kata` index lists all five; no command carries a
  threshold/decision. (Content check, no code.)
- **Gate:** six files present; bodies match the frozen convention; no logic drift.

#### A1-b — installer helpers  ·  OWNS: `tools/kata_install.py` (ADDITIVE only), `tools/tests/test_install_commands.py`
- Add `_link_or_copy_file` (stdlib file primitive: `os.symlink` file / `shutil.copy2` fallback) with the FROZEN
  file-collision policy (DESIGN A2): (a) replace only a link/file we own; (b) refuse/skip-with-NOTE a real
  pre-existing non-kata file — **never clobber** a user's `~/.claude/commands/<name>.md`; (c) track managed names in
  `~/.claude/.kata-commands.json` for idempotent re-install/uninstall.
- Add `_flat_link_commands` (mirrors `_flat_link_skills` in SHAPE, but per-FILE): globs
  `adapters/claude/commands/*.md`, links each into `~/.claude/commands/<name>.md`. Wire the call from
  **`_install_claude`** (kata_install.py:166 — NOT a frozen fn).
- **HARD:** the 5 frozen engine fns (`_flat_link_skills`, `_link_or_copy`, `install`, `copy_project`,
  `confirm_platform`) stay **byte-identical** — MD5-verify before/after. STDLIB-only (no `yaml`, no
  `validate_skills`).
- **TDD:** (1) `_link_or_copy_file` links/copies a file idempotently; (2) policy (b) SKIPS a pre-existing non-kata
  file with a NOTE and does not overwrite it; (3) manifest round-trips (install → re-install no-op → uninstall
  removes exactly ours); (4) `_flat_link_commands` links all six by fixture.
- **Gate:** tests green; frozen-five MD5 unchanged; Snyk medium+ 0.

### INCREMENT A gate + LIVE PROOF (needs A1-a + A1-b)
- **pytest green · Snyk medium+ 0 · frozen-five MD5 unchanged.**
- **Live-proof #1 (installer):** a REAL install links all six commands into `~/.claude/commands/`; a `/` menu shows
  them; the 5 frozen fns MD5-match.
- **Live-proof #7 (collision safety):** install over a `~/.claude/commands/` holding a user's own non-kata
  `<name>.md` never clobbers it; re-install is idempotent; uninstall removes exactly the six.
- **Adversarial sweep (D98) + fresh-context `kata-evaluate` (PART A, default-FAIL)** → operator merge gate.

---

## INCREMENT B — durable restore (spine-touching; hook LAST)

### WAVE B1 — durability foundation (single cohesive task; blocks B2/B3)

#### B1 — board-durability helper + step-5 call site + task-id trailer + decisions
- OWNS: `tools/kata_trail.py` (NEW), `tools/tests/test_kata_trail.py` (NEW),
  `skills/coordinate/kata-orchestrate/SKILL.md` (step-5 edit — bump), `.planning/DECISIONS.md` (D133/D134/D135).
- **`kata_trail.py`** (stdlib + `git` subprocess, PLUMBING ONLY): snapshot `.kata/board.md` →
  `refs/kata/trail` via `hash-object -w` → `mktree` → `commit-tree -p <prior>` → `update-ref` (NEVER touches index
  or working tree; NEVER pushes; ONLY the board). Robustness: **no-op when `.kata/board.md` absent**;
  **retry-once-then-skip on a busy `refs/kata/trail.lock`**; never fail/hang the caller.
- **`kata-orchestrate` step 5:** add a call site that fires `kata_trail` right after each task integrates (cadence
  i — closes Gap 2/3 independently of the hook), and ensure the integration commit records its task-id
  (`Kata-Task: <id>` trailer; no-op if the existing project trailer already carries it — VERIFY at build).
- **DECISIONS.md:** write **D133** (recovery-ref git carve-out — narrow, orphan-ref only, never push, never
  integration branch, self-pruning), **D134** (restore = task-granular re-dispatch), **D135** (board-is-the-trail;
  supersedes D132's continuous-replay-SPINE scope). D132 left UN-edited (supersede-never-rewrite).
- **TDD:** (1) helper writes a single-file commit to `refs/kata/trail`, working tree + index untouched
  (`git status` clean); (2) no-op on absent board; (3) ref-lock → retry-once-then-skip, no raise; (4) never writes
  a branch/pushes; (5) the step-5 integration commit carries `Kata-Task: <id>` and maps 1:1 to a task.
- **Gate:** tests green; Snyk medium+ 0; validate 47/0 (kata-orchestrate bumped); frozen-five untouched (no
  install change here).

### WAVE B2 — restore read (needs B1)  ·  can run parallel with B3 (disjoint), B3 proof still gated on B1

#### B2 — restore read (PLAN-derived set + reconcile + C2 cleanup)
- OWNS: `skills/handoff/kata-orient/SKILL.md` (bump), `skills/coordinate/kata-readiness/SKILL.md` (bump),
  `tools/kata_restore.py` (NEW), `tools/tests/test_kata_restore.py` (NEW).
- **Restore logic** (`kata-orient`/`kata-readiness` prose + `kata_restore.py` mechanics): (1) detect lost run
  (tier-3 absent/stale, `refs/kata/trail` present); (2) read board from the orphan ref, fold with the EXISTING
  concurrency reduce; (3) **re-dispatch set = frozen PLAN tasks MINUS those with an integration commit** (tier-2
  AUTHORITATIVE for DONE; board CORROBORATES in-flight ownership, NEVER gates the set); (4) C2 cleanup before
  re-dispatch — `git worktree prune` + delete/reset the stale `task/<id>` branch (or fresh branch keyed on
  task-id); half-written artifacts DISCARDED; (5) resume does NOT rotate the board.
- **Depends on:** B1 (task-id trailer + trail helper). **TDD:** (a) re-dispatch set is PLAN-minus-integration, not
  board-derived; (b) **early-wave crash** (wave CLAIMed, nothing integrated, tier-3 wiped) → ALL wave tasks
  re-dispatched, none dropped; (c) integrated-but-stale-board task NOT re-dispatched; (d) finished-but-not-
  integrated task IS re-dispatched (tier-2 authoritative); (e) C2 cleanup clears the `.git/`-surviving
  branch/worktree collision; (f) resume does not rotate.
- **Gate:** tests green; Snyk medium+ 0; validate 47/0 (kata-orient + kata-readiness bumped).

### WAVE B3 — PreCompact hook (needs B1; LAST)

#### B3 — auto-checkpoint hook
- OWNS: `adapters/claude/settings.snippet.json` (hook wiring), `adapters/claude/hooks/` (NEW hook script if a
  wrapper is needed), `adapters/claude/README.md` (document the hook + the PreCompact ASSUMPTION).
- **Hook:** a deterministic shell command invoking `kata_trail` before compaction; optionally emit
  `custom_instructions` nudging the resumed turn to run `kata-handoff` from the just-committed trail (safety NEVER
  depends on that turn). Inherits B1's no-op/lock-tolerance.
- **ASSUMPTION (VERIFY at build, live-proof #2):** PreCompact is a synchronous shell hook with a usable time
  budget. If NOT, Gap 2/3 still close on B1's step-5 cadence; only the compaction-window floor of Gap 1 needs a
  different trigger — surface the finding, do not fake it.
- **Depends on:** B1. **Gate:** wiring valid; hook is git-plumbing only (no handoff authored, no `state.json`
  write, no source touched).

### INCREMENT B gate + LIVE PROOF (all B waves)
- **pytest green · validate 47/0 (all bumped skills) · Snyk medium+ 0 · frozen-five MD5 unchanged.**
- **Live-proof #2 (hook):** a simulated compaction fires the hook → `board.md` lands on `refs/kata/trail`; the
  integration branch is untouched; nothing is pushed. (Also resolves the PreCompact assumption.)
- **Live-proof #3 (restore):** kill a run mid-wave (board CLAIM without DONE, tier-3 deleted) → restore re-dispatches
  exactly the incomplete task(s), no more, no fewer.
- **Live-proof #4 (reconcile — "no more"):** a task integrated after the last durability write is NOT re-dispatched.
- **Live-proof #5 (early-wave crash — "no fewer"):** wide first wave CLAIMed, nothing integrated, tier-3 wiped,
  killed → ALL wave tasks re-dispatched, none silently dropped.
- **Live-proof #6 (C2 cleanup):** re-dispatch succeeds despite the dead worker's `task/<id>` branch + worktree
  metadata surviving in `.git/` (no `already exists` collision).
- **Adversarial sweep (D98) + fresh-context `kata-evaluate` (PART A, default-FAIL)** → operator merge gate.

---

## Integration gate (both increments)
- **pytest green** (existing suite + all new tests) · **validate_skills 47/0** WITH every edited skill bumped ·
  **Snyk medium+ 0** on all new/changed Python (`kata_install.py` additions, `kata_trail.py`, `kata_restore.py`) ·
  **5 frozen `kata_install.py` engine fns byte-identical (MD5-verified).**

## Live-proof obligations (must be demonstrated, not asserted — D124)
Unit tests + `kata-evaluate` PART A CANNOT see built-but-unwired / cross-seam gaps. Live-proofs #1–#7 above are
LOAD-BEARING gates, not ceremony — every seam the freeze-gate flagged is covered by a numbered live-proof.

## Build order (binding)
A1-a ∥ A1-b → **Increment A gate (ship first)** → B1 → (B2 ∥ B3, B3 proof after B1) → **Increment B gate.**
