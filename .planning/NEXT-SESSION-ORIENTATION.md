# NEXT-SESSION ORIENTATION — written 2026-07-12b session end (master `4692be4`)

> **The in-depth agent orientation for the next session.** Read this AFTER the mandated read order
> (`protocol/prime-directives.md` → `AGENTS.md` → `docs/DESIGN.md` → `docs/STANDARDS.md` +
> `docs/DETERMINISM-DOCTRINE.md` → `.planning/STATE.md`). The paste-companion summary is
> `.planning/HANDOFF-NEXT-SESSION.md`; THIS file carries the full action plan with per-item
> context, pointers, and acceptance. ⚠ IGNORE `C:\Dev\CLAUDE.md` (unrelated Mise project).

## 0. GROUND TRUTH AT WRITE TIME

- **master `4692be4`** (= PR #22 docs sync over PR #21 merge `c81db21`), pushed, tree clean except
  the known untracked `.planning/config.json` (pre-existing operator artifact — leave it).
- **Gate:** pytest 3476/3 skip · integration 2/2 · ruff clean · validator 48/0/0 · Snyk medium+ 0
  new (accepted: statusline_chain MED CWE-78 + python/PT LOW class, see `.snyk`).
- **Hook chain LIVE-INSTALLED in the operator profile** (2026-07-12 20:56 UTC): SessionStart +
  PreCompact + UserPromptSubmit(gauge-check) appended; GSD statusline chain-wrapped (original
  verbatim after `--`); backup `settings.json.kata-backup-20260712T205642739769Z`; rollback =
  `kata_install.py --platform claude --uninstall-hooks`. **The chain activates at SESSION START —
  the next session is the FIRST ever to run under it.**
- **Installed kata-home + skills = current** (`.kata-version` gitSha `c81db21…`, 48 skills linked).
- **The second-brain loop is LIVE**: `learn_feed.py` → vault `decision-patterns/` → recall
  `feed_dir`. The operator's PokeVault second brain holds its first 11 pages (MM ledger, D151
  smoke). Settings: vaultDir `C:\Users\taurr_nvs748q\PokeVault\PokeVault` (`.kata-settings.json`).

## 1. WHAT THE 2026-07-12b SESSION ESTABLISHED (one paragraph each)

**Conductor self-handoff root cause (Review 1):** never fired because (C-1/C-2) the gauge check
was prose living only in kata-orchestrate's wave loop — sessions outside that loop had no
evaluation point; (D-1/D-2) the chain was never deployed (installer wrote no host settings; GSD
owned the statusline; zero bridge files ever); (C-3/C-4) no reset backstop. D152 fixed C-1/C-2
(mechanical UserPromptSubmit gauge hook, kata-scope-gated, deduped w/ drop-re-arm, never-exit-2)
and D-1/D-2 (consent-gated `--install-hooks`, executed live). C-4 and R6 remain OPEN (below).

**Pointer structure (Review 2): SOUND.** Six da9bc92 PD wirings verified; AGENTS.md canonical,
zero drift; A2/A3/A4 fixed. Residual: recall is wired at ONE prose call site (initiate Phase 1b)
— see C3 below.

**Second brain (Review 3 + D151 build):** the learn→store→recall loop now exists and is
live-proven n=1. Grill responses emit at grill close (one decision-pattern page per resolved
ledger entry) and recall reads them back as the config-gated 7th source. Redaction is
redact-and-mark (operator's conscious C3 re-scope — vault security is the operator's
responsibility). The β/kata-improve path cites the same engine.

## 2. THE ACTION PLAN — every open item, sequenced

### PHASE A — passive live confirmations (first ~30 min of the next session; no build)

- **A1. Verify the chain came up.** GSD statusline still renders (chain passthrough) AND a bridge
  file `kata-ctx-<session_id>.json` exists under the temp dir. If the statusline broke: rollback
  via `--uninstall-hooks`, file a finding. *Acceptance: both observed, noted in session log.*
- **A2. F-9 — first gauge-directive observation.** In a kata-scoped cwd, when context crosses
  0.70 the `[KATA CONTEXT GAUGE]` directive appears at a user turn. When observed: flip
  `.planning/specs/context-autonomy/GROUNDING-CLAUDE.md` §G1b and `adapters/claude/README.md`
  GROUNDED-BY-PATTERN → **CONFIRMED** (cite the observation). *Acceptance: both markers flipped
  with evidence.*
- **A3. R6 — live host-fired compaction e2e** (the LAST unproven context-autonomy leg). A long
  session that auto-compacts: PreCompact snapshots the SESSION repo board → SessionStart(compact)
  re-anchors on `.planning/HANDOFF.md` → next task zero-loss + kata-orient context-quality grade.
  R1-R5/R7 attended checks (BACKLOG v0.2.1 queue item 2) ride the same observation window.
  *Acceptance: R6 recorded proven (or the precise broken link named) in STATE + BACKLOG.*

### PHASE B — the two operator-priority builds (full discipline: grill → freeze → build → adval → smoke)

- **B1. THE "ELEVATE" STEP** (operator-directed 2026-07-12; BACKLOG 2026-07-12b #1). At the END of
  every grill session — on EACH KataHarness execution — the harness uses its deep context + task
  understanding to make **ONE brainstormed recommendation** (more only if the user asks) that
  elevates the design and function of the output. Design anchors: home = grill close, immediately
  BEFORE the D151 learn-feed emit (so the elevate recommendation + the operator's accept/decline
  become ledger entries → second-brain signal); always-on (a grill behavior, not a config-gated
  module); single by default; the recommendation must be grounded in the run's actual grill
  context (never generic advice); the operator's decision on it is recorded in the ledger (LOCKED
  or declined-with-reason). Grill forks to resolve at freeze: tier behavior (essential/standard/
  advanced same or scaled?); interaction shape (present via the B2 single-question UI?); whether
  declines feed the second brain too (recommend: yes — a decline is preference signal). Files in
  play: `skills/plan/kata-grill/RUBRIC.md` + 3 tier SKILL.md (bump), possibly `kata-initiate`
  (mirror). *Acceptance: freeze-gated design; built; adval SHIP; live-smoked on a real grill;
  validator 48/0/0.*
- **B2. GRILL SINGLE-QUESTION UX** (operator-directed 2026-07-12; BACKLOG #2). The doc-grounded
  grill must ask via Claude's single-question output (AskUserQuestion) **ONE question at a time**
  — never a multi-question dump ("throwing five out there isn't a good UX"). Scope: the grill
  tier skills' interactive flow on the Claude adapter (adapter-behavior note in RUBRIC or tier
  prose; non-Claude platforms keep prose questioning); `kata-initiate` Phase 2b already uses
  AskUserQuestion — align wording. NOTE the operator's general preference stands OUTSIDE the
  grill: conversational prose for design discussion. Combine with B1's interaction shape so the
  elevate recommendation lands in the same UX. *Acceptance: tier skills bumped; a live grill
  demonstrably asks one-at-a-time.*

### PHASE C — decisions + small builds from this session's review residuals

- **C1. C-4 backstop decision.** The `autoCompactWindow` recommendation is still recommend-only —
  nothing writes it. Decide: add an OPT-IN write to `--install-hooks` (same consent flow) or keep
  recommend-only permanently (record the decision either way). Pointers:
  `kata_gauge.backstop_recommendation`; GROUNDING-CLAUDE §G1 (ceiling semantics, floor 100k).
- **C2. 7th-source first-run fallback** (prose-adval observation; BACKLOG 2026-07-12b #4). On a
  FRESH project, recall's feed_dir row can never fire in run 1 (Phase 1b precedes kata.config).
  Decide + small build: fall back to `kata_settings.default_learn_feed_dir()` when no kata.config
  exists. Pointer: `modules/initiation/kata-initiate/SKILL.md` Phase 1b table.
- **C3. Recall-beyond-initiation decision** (audit finding B1): should kata-orient fold a recall
  brief into WORKER orientation (workers currently never see prior lessons)? Decide scope
  deliberately; if built, it is a kata-orient + orchestrate prose change.
- **C4. PostToolUse gauge cadence** — ONLY if A2/A3 show UserPromptSubmit under-samples
  turn-internal growth (one giant turn can blow past 0.70 unseen between prompts).
  Evidence-gated; do not build speculatively.
- **C5. LOW acceptances to keep or close:** G-3 (hand-duplicated kata hook entries leave one
  stale slot until uninstall — optional sweep); A5 (platform docs carry no pointer-structure
  reinforcement — cosmetic); memory-doesn't-reassert-pointer-discipline (orthogonal-by-design;
  revisit only with engram CONSULT).

### PHASE D — environment/process hardening (parallel-track, any session)

- **D1. Transient file corruption/revert root-cause hunt.** Two sessions running: 2026-07-12
  (multiple uncommitted-edit reverts; function_model corruption) and 2026-07-12b
  (recurrence_detect phantom IndentationError during a concurrent read, self-healed byte-clean).
  Suspects: parallel-agent worktree ops under `.claude/worktrees/`, AV/indexer interference,
  concurrent pytest + read. Deliverable: a reproduction attempt + a mitigation (or a documented
  monitoring discipline). Until then the standing mitigation HOLDS: commit early/often; re-grep
  signatures after every edit batch; trust the disk.
- **D2. Updater stale-lock robustness.** This session `update.ps1` failed to advance past a stale
  `refs/remotes/origin/master.lock` (left by an interrupted fetch) and RE-STAMPED THE OLD SHA
  while still relinking — a silent-stale-install failure mode. ADD: detect+surface (or clear with
  consent) stale ref locks, and make "advanced to <sha>" compare against origin (fail loud if
  still behind after update). Small, test-backed.
- **D3. Piped-exit-code discipline** (this session's own miss): never `pytest -q | tail && git
  commit` — the pipe eats the failure. Check the tail TEXT or run unpiped before committing.
  Consider a `tools/scripts/` gauntlet helper that exits honestly.

### PHASE E — standing queue (unchanged order, after A–C)

- **E1.** Calibration proper (τ/weights) — needs fresh instrumented runs that EMIT `verify.owned`
  (the C-1/D149 fix landed; such runs don't exist yet). Wire the C-3 `verdict×tier` ledger
  columns in the same pass.
- **E2.** Adaptive-vs-static LIVE A/B (D150 follow-on) — rides the same instrumented runs as E1.
- **E3.** PokeVault install / MindBridge ingest — first external deploys (now MORE compelling:
  the second-brain loop gives the vault install real content from day one).
- **E4.** Kenjiri resume (PAUSED mid-run since 2026-07-01) — doubles as the restore-path live
  test.
- **E5.** OPTIONAL operator choice: full DECISIONS backfill (`learn_feed --decisions` over the
  harness's ~150 ADR bullets → second brain). Accepted-by-design volume; one idempotent command,
  run whenever the operator wants the corpus fleshed out.
- **E6.** Health-review LOW/INFO residuals not yet closed (BACKLOG "2026-07-12 HEALTH-REVIEW
  FOLLOW-UPS"): skill-level Determinism-Doctrine enforcement in kata-review/kata-evaluate;
  `_safe_path` physical consolidation (the drift-test covers the invariant); R3 param-node-id
  backslash collision; misc cosmetics.

## 3. SEQUENCING RECOMMENDATION

Session N+1: **A1/A2 passively → B1+B2 as ONE grilled initiative** (they share the grill-close
surface and the interaction UX) **→ C1/C2 decisions inline** (both small) **→ close with the
learn-feed emit proving B1's ledger entries land in the vault.** A3/R6 confirms itself whenever
the session runs long. D1/D2 are good parallel dispatch targets while builders run. E-queue after.

## 4. HAZARDS + STANDING ORDERS (binding)

- **PD-1/PD-2 bind every run** (never silently defer/stub; absolute truthfulness). Determinism
  Doctrine on anything that gates/scores/orders/hashes/writes durable artifacts.
- Cite the artifact before claiming it exists; "done" = gate numbers + record + SHA in the same
  message; fresh-context adval before merge (D33); D136 fail-closed; bump-on-modify + validator
  `--write`; branch→PR→merge (no direct-to-master).
- **Worktree/corruption hazard is LIVE** (D1 above): commit early/often, re-grep after batches.
- **Session-limit kills mid-fan-out are recoverable**: resume each agent via its agentId with a
  "re-verify your owned files on disk first" preamble — proven this session (all 5 builders
  resumed clean).
- Piped-exit-code rule (D3 above).
- Kata target toggle: harness work is CODEBASE-target; the INSTALLED set is current with master
  post-`c81db21`, so INSTALLED-target runs are also safe.

## 5. GATE REPRODUCTION (from `tools/`)

`uv run pytest -m "not integration"` → 3476 pass / 3 skip · `uv run pytest -m integration` → 2
pass · `uvx ruff check .` → clean · `uv run python validate_skills.py` → 48/0/0 · Snyk Code
medium+ → 0 new. Second-brain loop re-verify (read-only): `recall_from_paths(feed_dir=<vault
synthesis dir>, query_terms=['model','tiering'], kind='version-up')` surfaces
`source="second-brain"` records.
