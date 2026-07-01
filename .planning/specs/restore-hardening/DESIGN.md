---
title: "restore-hardening — FROZEN DESIGN (durable board + auto-checkpoint + slash-commands)"
status: FROZEN (2026-06-30) — operator-approved LEAN scope; grill-prep + simplicity-pass folded
spec: restore-hardening
decision: D132 (Option-2 restore-hardening) — this DESIGN REFRAMES D132's scope and introduces D133 (recovery-ref git carve-out) + D134 (restore = task-granular re-dispatch)
builds-on: mid-build-loss/restore assessment + grill-prep report; the simplicity-pass CUTS (C1–C2) SUPERSEDE any richer scope implied by D132
scope: Claude-only adapter (6 pointer commands + PreCompact hook) + core durability (board → orphan ref) + a task-granular restore read
invariant: restore-only (no forward-replay) · the task is the restart unit · the board is the ONLY trail · recovery ref never touches the integration branch · 5 frozen install fns byte-unchanged · STDLIB-only install path · validate 47/0 · Snyk medium+ 0
tags: [design, frozen, restore-hardening, durable-board, orphan-ref, precompact-hook, slash-commands, split-increments]
---

# restore-hardening — FROZEN DESIGN

Today a mid-build session death restores POORLY: the live progression state (`.kata/board.md`, `state.json`) is
tier-3 (GITIGNORED, `.gitignore:9`), self-handoff is manual-and-conscious only, and a fresh conductor cannot
rebuild the active frontier from the durable trail. This DESIGN closes that with the **smallest mechanism that
actually works**, not a new subsystem.

**The reframe that sizes the whole build:** `protocol/board.md` is *already* an append-only, worker-stamped,
stdlib-parsed event log (`CLAIM/DONE/BLOCK/ESCALATE/NOTE/DECISION/PROGRESS`, one line each, folded to a frontier
snapshot by the existing concurrency reduce). Its **only** deficiency for restore is that it lives in gitignored
tier-3. So the feature is **durability of the board**, not a parallel journal. Two simplicity cuts (C1, C2 below)
remove the two pieces of the original Option-2 scope that were building capability we already have, or building
recovery machinery for bytes that are usually already gone.

This freeze folds the grill-prep outcomes and the operator's simplicity-pass; the CUTS supersede any richer reading
of D132.

---

## 0. Locked decisions (operator-approved)

- **L1 — restore-only.** We rebuild the frontier at the point of loss and resume; we do **not** deterministically
  re-execute a run forward (model output is not deterministic — forward-replay is a much larger verification
  problem for no operator benefit). The trail is *structured* so forward-replay could be added later, but it is
  **out of scope** here.
- **L2 — split into two increments.** **Increment A** (discoverability: 6 pointer commands + installer helper) is
  adapter-clean, spine-risk-free, and ships FIRST. **Increment B** (durable restore: durable board + PreCompact
  hook + restore read) is the spine-touching work, its own gated increment, hook LAST.
- **L3 — durable trail = an orphan git ref (`refs/kata/trail`).** It EXTENDS tier-3 (does not replace it): tier-3
  stays the disposable hot cache; the orphan ref is the durable recovery tail. It never lands on the integration
  branch, so it never pollutes the completion-order history the concurrency evidence + `kata-evaluate` consume.
  Squashed/dropped at task integration (its durable value is by then captured by the real integration commit).
  Accepted worst case: a `git gc` or a clone that omits `refs/kata/*` loses the tail and degrades to today's
  per-integration granularity — no worse than status quo.
- **C1 (CUT) — NO new JSONL / event-journal artifact. The board IS the trail.** Building a second append-only log
  alongside the board doubles the write + parse + divergence surface for a capability that already exists. We make
  the existing board durable; we do not invent a journal. This directly reverses D132's "continuous-replay is the
  SPINE, not a bolt-on" scope, so it is recorded as its own numbered decision **D135** (not prose). *(Δ Option-2:
  drops the "continuous-replay journal" subsystem.)*
- **C2 (CUT) — the TASK is the restart unit. NO mid-wave re-attach.** If a task held a `CLAIM` with no `DONE` at
  the point of loss, restore **re-dispatches that task from scratch** — every input it needs is already durable
  (frozen DESIGN, PLAN, disjoint file ownership). We do NOT record branch/worktree paths, do NOT build a mid-wave
  commit protocol, and do NOT re-attach a half-finished worktree (which is often unrecoverable after a session
  death anyway). Workers MAY commit to their own task-branch as normal git hygiene, but nothing load-bearing
  depends on it. *(Δ Option-2: drops Gap-2's re-attach machinery; tasks are TDD-sized to make re-run cheap.)*
- **L4 — the PreCompact hook is a mechanical FLOOR, never a reasoned artifact.** A Claude `PreCompact` hook is
  (ASSUMED — **verify at build**, live-proof #2) a deterministic shell command, NOT an agent turn — it cannot run
  `kata-selfhandoff`. It commits the already-durable board to the recovery ref and (optionally) plants a
  `custom_instructions` nudge for the resumed turn. Rich, reasoned handoffs remain with
  `kata-selfhandoff`/`kata-handoff` at task boundaries, **unchanged**. (If the build finds PreCompact is NOT a
  synchronous shell hook with a usable time budget, the integration-checkpoint durability of B1 still closes
  Gap 2/3; only the compaction-window floor of Gap 1 would need a different trigger.)
- **L5 — D-numbers.** This DESIGN introduces **D133** (recovery-ref git carve-out to the no-autonomous-git spine
  rule), **D134** (restore = task-granular re-dispatch, C2), and **D135** (board-is-the-trail; no continuous-replay
  journal — supersedes D132's continuous-replay-SPINE scope, C1). It also records that **D132's "adapter closes
  Gap 1 with no core change" framing is superseded**: Gap 1's fix is an adapter *trigger* on a *core* durability
  mechanism plus the D133 protocol carve-out. D132 is not edited (supersede-never-rewrite); D133/D134/D135 are the
  next free numbers, written to `DECISIONS.md` at freeze.

---

## 1. The three gaps, and how the lean design closes each

| Gap | Today | Closed by |
|-----|-------|-----------|
| **1 — no automatic pre-compaction checkpoint** | self-handoff is manual + conscious; `kata-orchestrate` never fires it in-loop | **PreCompact hook** commits the durable board to `refs/kata/trail` before compaction (L4) |
| **2 — mid-wave progress lost on death** | checkpoint granularity is per-integration only | **C2:** restore recomputes the frontier from the frozen PLAN minus integrated tasks and re-dispatches every non-integrated task; the task is the restart unit (no re-attach machinery) |
| **3 — in-flight ownership not durable** | the `tasks{}` / board CLAIM map is in-memory / gitignored | the **frozen PLAN + integration history** (both always-durable) drive the re-dispatch set; the durable board *corroborates* which task a dead worker held, but never gates the set |

All three close with **one durable board + one dumb hook + one restore read.** No journal subsystem, no re-attach
protocol.

---

## 2. Architecture

### Increment A — discoverability (adapter-clean; ships first)

**A1 — six pointer commands** in `adapters/claude/commands/` (the repo is the single source of truth; the installed
copies land in the user's `~/.claude/commands/`, which the repo does not track — exactly as skills install to
`~/.claude/skills/`). Each file is
`.claude/commands/<name>.md` = YAML frontmatter (`description`, optional `argument-hint`) + a 1–3 line **pointer
body** that names the exact skill and passes `$ARGUMENTS`. **Zero logic, zero thresholds** — a labeled front door,
mirroring the repo's own `CLAUDE.md → AGENTS.md` pointer style, so a skill version bump never touches the command
(DRY holds across the now-active bump-on-modify discipline).

| Command | Routes to | Note |
|---------|-----------|------|
| `/kata` | — (static index) | the ONE new artifact: a short list of the other five, one line each, no logic |
| `/kata-start` | `kata-initiate` | start a run |
| `/kata-onboard` | `kata-onboard` | onboard an existing repo |
| `/kata-resume` | `kata-orient` → `kata-handoff` | resume after a break/loss |
| `/kata-status` | `kata-board` | show the frontier |
| `/kata-validate` | `kata-validate` | run the validator |

Frozen body convention (identical shape across all six): *"Invoke the `<skill>` skill to <purpose>. Pass through:
$ARGUMENTS. Do not improvise; if the skill is unavailable, say so."*

**A2 — installer helper `_flat_link_commands`** in `tools/kata_install.py`. NOTE: the frozen `_link_or_copy`
(kata_install.py:111) is **directory-only** — it uses `shutil.copytree` and `os.symlink(..., target_is_directory=
True)`. Commands are flat **files** (`<name>.md`), so `_link_or_copy` **cannot** be reused for them. So A2 adds
TWO additive functions (neither touches the frozen five): a small stdlib **file** primitive `_link_or_copy_file`
(`os.symlink` for a file / `shutil.copy2` fallback), and `_flat_link_commands`, which globs
`adapters/claude/commands/*.md` and links each file per-file into the user's `~/.claude/commands/<name>.md`
(a shared dir that commonly pre-exists — so per-file, never whole-dir). Wired in from **`_install_claude`**
(kata_install.py:166 — NOT one of the frozen five), so all five frozen engine fns (`_flat_link_skills`,
`_link_or_copy`, `install`, `copy_project`, `confirm_platform`) stay **byte-identical** (MD5-verified post-build).
STDLIB-only: `os`/`shutil`/`pathlib`; command files are plain text; no `yaml`, no `validate_skills` on this path.

**File-collision policy (FROZEN — do NOT leave to builder discretion; this touches the user's own files).** The
directory guard `_link_or_copy` uses (a `.kata-managed` marker *inside* the copied dir) is impossible for a bare
`.md` file in a shared dir. So `_link_or_copy_file` MUST: (a) **replace only a link/file we own** (a symlink
pointing into the repo, or a name in our managed-command manifest); (b) **refuse (skip with a NOTE) a real
pre-existing file we did not write** — never clobber a user's own `~/.claude/commands/<name>.md`; (c) **track
managed command names in a small manifest** (e.g. `~/.claude/.kata-commands.json`) so re-install is idempotent and
uninstall removes exactly what we placed. All six kata command names are namespaced (`kata`, `kata-start`, …),
which makes accidental collision unlikely but not impossible — (b) is the safety backstop.

### Increment B — durable restore (spine-touching; hook last)

**B1 — durable board.** The existing `.kata/board.md` is snapshotted to the orphan ref `refs/kata/trail` (L3) by a
mechanical helper in `tools/` (stdlib + `git` subprocess), authored by plumbing only — **`git hash-object -w` →
`mktree` → `commit-tree -p <prior refs/kata/trail>` → `update-ref refs/kata/trail`** — which **never touches the
index or working tree** and is atomic at `update-ref`. **Read-and-commit only, never a push, never the integration
branch.** Only `board.md` goes in the ref (NOT `state.json` — that is the derived, rebuildable cache). Robustness
invariants (the helper must never fail or hang the host turn): **no-op when `.kata/board.md` is absent** (fired
outside a run) and **retry-once-then-skip on a busy `refs/kata/trail.lock`**.

The helper fires at **two cadences** — this is what closes Gap 2 for the *arbitrary-crash* case, not just the
compaction case:
1. **At each integration checkpoint** (a new call site in `kata-orchestrate` step 5, right after a task integrates)
   — so the orphan-ref board is never staler than the last *integrated* task. This is a scoped core change and is
   why Gap 2/3 do NOT depend on the hook firing. The **same step-5 change** ensures the integration commit records
   its **task-id** (conventional-commit trailer, e.g. `Kata-Task: <id>`) so restore can map commit → task-id for
   the B3 step-3 reconcile. (If step 5 already carries the task-id in its project trailer, this is a no-op; verify
   at build.)
2. **On compaction** via the B2 hook — the additional floor for the compaction window.

**B2 — PreCompact hook** (adapter, `adapters/claude/settings.snippet.json`): a deterministic shell command that
invokes the B1 helper before compaction, then optionally emits `custom_instructions` telling the resumed turn
"first action: run `kata-handoff` from the just-committed trail." Durable safety NEVER depends on that turn
happening — the mechanical commit is the guarantee; the nudge is the enhancement. It inherits B1's no-op /
lock-tolerance robustness, so a hook firing outside a run or during a ref-lock is a clean no-op, never a host
hang. The hook is mid-task-safe *because* it only snapshots and never reasons (it sidesteps `kata-selfhandoff`'s
"never mid-task" rule entirely — it is not a handoff).

**B3 — restore read.** `kata-resume` (via `kata-orient`/`kata-readiness`) learns to:
1. **Detect a lost run** — tier-3 cache absent/stale but `refs/kata/trail` present.
2. **Read `board.md` from the orphan ref** and fold it to the frontier with the **existing** concurrency reduce.
3. **Recompute the dispatchable set from the frozen PLAN minus tier-2 (integration history is AUTHORITATIVE for
   DONE) — the board CORROBORATES, it NEVER gates.** The re-dispatch set = **every task in the frozen PLAN that has
   no integration commit** (C2: the task is the restart unit, so each non-integrated plan task re-runs from
   scratch). The folded orphan-ref board is **corroborating only** — it may confirm which task a dead worker held
   (in-flight ownership) but it **never limits** the re-dispatch set. *(Why: gating on board CLAIMs would silently
   drop early-wave tasks a crash never durably recorded — e.g. a wide first wave that crashes before any
   integration. The PLAN + integration history are the only ALWAYS-durable sources; the board's completeness is
   not load-bearing, consistent with the L4 fallback note.)* This requires mapping **integration commit → task-id**:
   the step-5 integration commit MUST record the task-id (conventional-commit trailer/message convention). If it
   does not today, adding that trailer is a small scoped core change (named in B1 and §6).
4. **Clean up before re-dispatch (C2 safety).** A dead worker's branch (`task/<id>`) and `.git/worktrees/<name>`
   metadata live in `.git/` and SURVIVE the tier-3 wipe, so a naïve `worktree add -b task/<id>` collides. Before
   re-dispatching an incomplete task: `git worktree prune`, then delete/reset the stale `task/<id>` branch (or
   re-dispatch under a fresh branch name keyed on the same task-id — the concurrency reduce keys on task-id, not
   branch, and already tolerates a re-dispatched task's span). Half-written worktree artifacts are **discarded,
   not reused.**
5. **Do NOT rotate on resume.** `kata-orchestrate` rotates a pre-existing `.kata/board.md` at *run start*; a
   *resume* restores the orphan-ref board into place and **skips rotation** (rotating would archive the recovered
   CLAIM/DONE lines and empty the live board).

`kata-readiness`'s existing "rebuild tier-3 from tier-2" rule (R5) is extended to also consult the orphan ref with
the step-3 precedence. These `kata-resume`/`kata-readiness` edits + the B1 helper + the step-5 call site are the
full set of core changes; each edited skill takes a semver bump (bump-on-modify).

---

## 3. D133 — the recovery-ref git carve-out (protocol ruling)

`kata-loop` forbids the conductor from carrying out git actions autonomously (those require explicit human approval
inside `kata-closeout`). The durable board + hook necessarily commit without a turn-by-turn human approval, so this
DESIGN carves out a **narrow, mechanical exception**:

> **D133:** A mechanical helper MAY commit `.kata/board.md` to the dedicated orphan ref `refs/kata/trail` without
> per-event human approval, PROVIDED it (a) writes ONLY to `refs/kata/trail`, never a branch and never the
> integration ref; (b) NEVER pushes; (c) commits ONLY the board (no source, no `state.json`); (d) is
> recovery-only and self-pruning (squashed/dropped at task integration). All *integration* commits remain under
> the existing human-approval gate. This exception exists so a mid-build loss is recoverable; it does not loosen
> the integration-branch approval rule at all.

---

## 4. NOT building (anti-drift guards — read before every build task)

- **NOT** a JSONL / event-journal subsystem. The board is the trail (C1). If a task starts adding a parallel log
  format, it has drifted.
- **NOT** forward-replay / deterministic run re-execution (L1). Restore rebuilds the frontier; it does not replay.
- **NOT** a mid-wave re-attach protocol, branch-name/worktree-path recording, or half-done-work recovery (C2).
  Incomplete tasks are re-dispatched whole.
- **NOT** a new conceptual tier in `protocol/state.md`. The orphan ref is a *recovery mechanism* described in one
  focused section — do NOT restructure the D81 three-tier model or mint a "tier-2.5" concept.
- **NOT** a hook that authors a handoff, writes `state.json`, or touches source (L4) — it is git-plumbing only.
- **NOT** porcelain git anywhere on the durability path — plumbing only (`hash-object`/`mktree`/`commit-tree`/
  `update-ref`); never `git add`/`commit`/`stash`; never touch the index or working tree during a live run.
- **NOT** a durability path that can fail or hang the host turn — it no-ops on absent board and retries-once-then-
  skips on a ref lock (B1).
- **NOT** any edit to the 5 frozen `kata_install.py` engine fns; the command installer is additive.
- **NOT** any `yaml`/`validate_skills` import on the install/materialize path.
- **NOT** commands with logic — pointer bodies only; a skill bump must never require a command edit.

---

## 5. Invariants + integration gates

- restore-only · task = restart unit · board is the only trail · orphan ref never touches the integration branch.
- 5 frozen install fns byte-unchanged (MD5-verified) · STDLIB-only install path.
- **pytest green** (existing suite + new tests for `_link_or_copy_file` + `_flat_link_commands`, the
  board-durability helper, and the fold-plus-reconcile restore read) · **validate_skills 47/0** (any skill edited —
  `kata-resume`/`kata-readiness` + `kata-orchestrate` step-5 call site — gets a semver bump per bump-on-modify) ·
  **Snyk medium+ 0** on all new/changed Python.
- **LIVE PROOF** (mandatory, not asserted — unit tests + kata-evaluate PART A cannot see cross-seam gaps, D124):
  1. **A2/installer:** a real install links all six commands into `~/.claude/commands/`; the 5 frozen fns MD5-match.
  2. **B1/B2 hook:** a simulated compaction fires the hook → `board.md` lands on `refs/kata/trail`; the integration
     branch is untouched; nothing is pushed.
  3. **B3 restore:** kill a run mid-wave (board has a CLAIM without DONE, tier-3 cache deleted) → `kata-resume`
     reads the orphan ref, folds the frontier, and re-dispatches exactly the incomplete task(s), no more, no fewer.
  4. **B3 reconcile ("no more"):** a task that INTEGRATED after the last durability write (present as
     CLAIM-without-DONE in the stale orphan-ref board but represented by an integration commit) is NOT
     re-dispatched — tier-2 wins (step 3).
  5. **B3 early-wave crash ("no fewer"):** dispatch a wide first wave (T1/T2/T3 all CLAIM to the live board),
     integrate NOTHING, delete tier-3, kill → restore re-dispatches ALL of T1/T2/T3 (they are non-integrated PLAN
     tasks), NONE silently dropped — proves the re-dispatch set is PLAN-derived, not board-gated.
  6. **C2 cleanup:** the re-dispatch of an incomplete task succeeds even though the dead worker's `task/<id>` branch
     and worktree metadata survive in `.git/` (prune + stale-branch handling works; no `already exists` collision).
  7. **File-collision safety:** installing commands over a shared `~/.claude/commands/` containing a user's own
     non-kata `<name>.md` never clobbers it (policy (b) skips-with-NOTE); re-install is idempotent (manifest).

---

## 6. Sequencing (safe build order — dependency-ordered)

1. **Increment A** (commands + `_flat_link_commands`): no dependency on the spine; ship + prove first.
2. **Increment B core, in order:** B1 board-durability helper + its `kata-orchestrate` step-5 call site + the
   task-id integration-commit trailer (+ D133/D135 recorded) → B3 restore read (PLAN-derived re-dispatch set,
   reconcile-against-integration, C2 cleanup).
3. **B2 hook LAST:** it is the thin trigger on top of B1; it cannot be proven before the trail it commits exists.
   Building the hook before B1 would be building against a mechanism that isn't there (guaranteed cross-seam gap).
   Because Gap 2/3 close on the step-5 call site (not the hook), Increment B is already useful before B2 lands.
