# HANDOFF — next session (written 2026-07-12, end of the Fable 5 health-review session)

> Paste-companion for the next fresh session. **Supersedes the 2026-07-05 v0.2.1 handoff.**
> Ground truth: **`master` @ `da9bc92`**, pushed, tree clean (only untracked `.planning/config.json`,
> a pre-existing operator artifact). ⚠ IGNORE `C:\Dev\CLAUDE.md` (unrelated Mise project).

## 1. WHAT HAPPENED THIS SESSION (2026-07-12, Fable 5)

A full-project **health review** of KataHarness, run OUTSIDE the kata loop (the loop was the subject
under audit — D33 no-self-cert), in three rounds + a pre-merge adversarial validation. **Merged via
PR #20 (`6c5dbc1`)**, then a follow-up wiring commit (`da9bc92`) direct to master.

**Verdict: KataHarness is NOT a facade.** 0 FALSE / 0 UNSUBSTANTIATED of ~19 load-bearing public
claims; 259/259 prose-cited engine surfaces real; zero dead modules; the learning loop was validated
hop-by-hop live on committed data (real machinery). Full ledger: `.planning/REVIEW-FABLE5-2026-07-12.md`.
Reusable procedure: `.planning/REVIEW-PROCEDURE.md`.

**Shipped:**
- **`protocol/prime-directives.md`** — PD-1 (never silently defer/stub/skip designed work; operator
  permission before any bypass) + PD-2 (absolute truthfulness; stub-reported-as-built IS DRIFT).
- **`docs/DETERMINISM-DOCTRINE.md`** — ten laws.
- **`protocol/steering.md` + `tools/kata_steer.py`** — the F-3 facade FIXED: STEERING/AGENT_STOP is a
  real, tested, wired engine (was prose claiming a cadence with zero implementation).
- **`.planning/REVIEW-PROCEDURE.md`**, gauntlet infra (ruff/coverage/SCA/`.github/workflows/ci.yml`/
  `docs/RELEASE-CHECKLIST.md`), and ALL health-review backlog fixes (gate-input, benchmark integrity,
  determinism residuals, git timeouts, ~20 robustness LOWs) — each mutation-proven.
- Biggest catch: the **PreCompact hook snapshotted the harness home, not the session repo** — the
  flagship crash-durability guarantee silently no-op'd in every installed deployment. Fixed.
- Adval caught **1 HIGH in my own F1 fix** (seq-repetition cap bounded the count operand not the
  result length; chained `[0]*1000*1000` bypassed it) + 1 MED (blanket plugin-autoload-disable
  deflates 3rd-party benchmark numbers). Both folded.

**Final gate at merge:** pytest **3274 pass / 3 skip** · integration **2/2** · ruff **clean** ·
validator **48/0/0** · Snyk medium+ **0**.

## 1b. FOLLOW-UP COMMIT `da9bc92` — Prime Directives on EVERY execution + Determinism Doctrine wired

The operator flagged that PD was wired only for worker *dispatch*. Now guaranteed at every entry:
kata-initiate 0.3.0 Phase 0 (conductor front door, loads PD first) · AGENTS.md Read-first (mandatory
first read) · CLAUDE.md pointer · kata_router stanza (installed targets carry it) · orientation stable
tier (dispatch, already) · validator REQUIRED_PROTOCOL (can't be erased). Determinism Doctrine, an
orphaned doc, is now referenced in AGENTS.md conventions/read-first, CLAUDE.md, and STANDARDS.md §4a.

## 2. ★★ NEXT SESSION — START HERE: two deep-review items (same depth as this session's audits)

The operator wants these two validated IN DEPTH first, before anything else:

1. **The coordinator/parent-session context-handoff — does it actually work?** In THIS session the
   parent (conductor) context ran very long and **never self-managed / self-handed-off** — the
   context-autonomy self-handoff (v0.2.1: conductor watches its own gauge, self-hands-off at 0.70)
   did NOT fire. Validate the whole `kata-selfhandoff` + `kata_gauge` + statusline-bridge + PreCompact/
   SessionStart re-anchor chain end-to-end for the PARENT/conductor (not just workers). Is the gauge
   readable by the conductor? Does the trigger fire? Does re-anchor restore full context? This is the
   R6 "live host-fired compaction" leg that was already the top of the backlog — now with the concrete
   observation that it didn't engage this session. Deep-validate like the facade audit: prove it, don't
   assume it.
2. **The universal pointer/context structure — is AGENTS.md truly the single standard, and is memory
   wired in?** Validate that ALL instruction/pointer files (`CLAUDE.md`, `STEERING.md`, per-platform
   `docs/platforms/*`, the kata_router stanza, nested-module AGENTS.md) consistently point to
   `AGENTS.md` as the canonical standard (STANDARDS §4 dual-standard) with no drift or contradiction.
   THEN validate the **memory-management component**: how does KataHarness persist/recall cross-run
   memory (recall.py + the learning loop + `.claude` memory), and are memories wired to reinforce the
   pointer structure? The operator wants memories that "wire in the memory management component" — i.e.
   confirm the recall/second-brain read-path actually surfaces the right context at run start and that
   the pointer discipline is memory-reinforced.

## 3. REMAINING BACKLOG (after the two deep reviews)

- `.planning/BACKLOG.md` "2026-07-12 health-review follow-ups" — the LOW/INFO residuals NOT fixed:
  skill-level Determinism-Doctrine enforcement in `kata-review`/`kata-evaluate` (named this session);
  the physical `_safe_path` shared-helper extraction (a drift-guard test covers the invariant — the
  one consciously-deferred item, see §4); R3 param-node-id backslash collision (niche); a handful of
  cosmetic LOWs.
- Then the pre-existing queue: R1–R5/R7 attended-host residuals, calibration-proper (τ/weights),
  adaptive live A/B, PokeVault install / MindBridge ingest.

## 4. THE STORY WITH THE ONE CONSCIOUSLY-DEFERRED ITEM (`_safe_path` consolidation, Q-12)

The engine has ~30 hand-copied `..`-rejection path guards (`_safe_path`/`_guard_path`/`_safe_abs`/…).
The review found drift starting at the edges (kata_supersede was swallowing the error — fixed).
Q-12's options were: extract one shared `kata_paths.safe_path` helper and migrate all 30 files, OR add
a check that the guards stay consistent. **I chose the drift-guard test** (`tests/test_path_guard_family.py`
— pins all 29 guards reject `..` + a completeness tripwire so a new unenumerated guard fails CI) over
the 30-file refactor, **because a mass mechanical refactor right before merge was the wrong risk given
the worktree-revert instability observed all session** (see §5). The behavioral invariant that actually
protects correctness is now enforced; the physical DRY extraction is a safe future refactor, not a
functional gap. This is the ONE item deferred with rationale (PD-1-compliant: named, reasoned,
operator-visible).

## 5. ⚠ ENVIRONMENT HAZARD — worktree/git revert instability

Multiple times this session a transient git/worktree operation **silently reverted uncommitted
edits**: one fix-group's changes wiped entirely, `function_model.py` corrupted mid-edit, and
STEERING.md / orchestrate SKILL / validate_skills reverted 2×. Each was caught via re-grep / failing
tests and re-applied, then committed promptly. **Mitigation for next session: commit early and often;
after any batch of edits, `git status` + re-grep key signatures before trusting they landed.** Worth
investigating what in the parallel-agent-in-worktree setup causes it.

## 6. STANDING ORDERS (unchanged, load-bearing)

Cite the artifact before claiming it exists; "done" = gate numbers + record + SHA in the same message;
fresh-context adversarial review before merge (D33 no-self-cert); D136 fail-closed decision-code;
bump-on-modify + `validate_skills --write`; branch→PR→merge (this session's `da9bc92` wiring went
direct to master under time pressure — prefer a branch next time); **the Prime Directives now bind
every run — PD-1/PD-2 are non-negotiable.**

## 7. GATE REPRODUCTION (from `tools/`)

`uv run pytest -m "not integration"` → 3277 pass · `uv run pytest -m integration` → 2 pass ·
`uvx ruff check .` → clean · `uv run python validate_skills.py` → 48/0/0 · Snyk Code medium+ → 0.
Installed skills at `~/.claude/skills` are still v0.2.0-era — run the updater before any
INSTALLED-target kata run so future runs carry the Prime Directives.
