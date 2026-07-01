---
gsd_state_version: 1.0
milestone: v0.2
milestone_name: restore-hardening (durable board + auto-checkpoint + task-granular restore) + /kata commands
status: shipped
last_updated: "2026-07-01T00:00:00.000Z"
---

# STATE — KataHarness

> **CURRENT (2026-07-01, SESSION END — restore-hardening SHIPPED + MERGED to master · tip `16007f7` in sync ·
> pytest 2170 passed / 3 skip / 2 integration-deselected · validate 47/0 · Snyk medium+ 0):** The D132 Option-2
> restore-hardening initiative was designed (3-pass adversarial freeze-gate), built (Increments A + B), and
> MERGED to master via **PR #1** (`0bc2a0e`). A recurrence-hardening guard (**D136**) and a salesy README refresh
> (**PR #2**, `16007f7`) also merged. Decisions **D133** (recovery-ref git carve-out), **D134** (task-granular
> re-dispatch), **D135** (board-is-the-trail; supersedes D132's continuous-replay-SPINE scope), **D136**
> (silent-permissive-default guard, D33 never-tiered family) all recorded; D132 un-edited. Working tree clean,
> everything pushed. **No next initiative is chosen yet** — see `.planning/HANDOFF.md` §4/§6 for the open options.
> The one real-world unknown is live-proof #2 (does Claude's PreCompact hook fire synchronously? — confirmable
> only in a live session; if not, Gaps 2/3 still close via the integration-cadence checkpoint). *(Prior CURRENT
> block below is superseded history.)*

> **CURRENT (2026-06-30, SESSION END — v0.1.0 TAGGED + PUSHED · tip `365c7f1` in sync; pytest 2141 · validate 47/0
> · Snyk medium+ 0):** Two read-only assessments ran this session after the v0.1.0 tag was pushed. Assessment 1
> (slash-command surface): KataHarness ships 0 true Claude slash commands — the `/kata-*` names in the README are
> skill aliases, not `.claude/commands/` files; gap = discoverability; fix = 6 thin pointer-only adapter commands
> (DRY-by-pointer, adapter-only, never core). Assessment 2 (mid-build loss/restore): planned restore is GOOD-but-
> manual; unplanned mid-task loss is POOR (gitignored tier-3, stale handoff, no automatic checkpoint); three root
> gaps identified (Gap 1 = no auto pre-compaction checkpoint; Gap 2 = per-integration checkpoint too coarse; Gap 3
> = in-flight ownership not durable in tier-2). **Operator decision = D132 Option 2: close ALL gaps + add
> continuous-replay spine.** Scope: Adapter (6 slash-command pointers + installer + auto-handoff PreCompact hook
> for Gap 1) + Core (Gap 2 mid-wave worker progress commits + Gap 3 durable CLAIM map in tier-2 + continuous-
> replay event-log as the unified spine). **Design PENDING** — next session grills + freezes the design BEFORE
> any build. Bump-on-modify is now ACTIVE (STANDARDS §3, flipped at v0.1.0): every skill modification requires a
> semver bump (new capability → minor; fix → patch); new skills enter at 0.1.0. Working tree clean after handoff
> commit. See `.planning/HANDOFF.md` + `.planning/NEXT-SESSION-ORIENTATION.md`. Records: `DECISIONS.md` D132.

> **CURRENT (2026-06-30, v0.1 RELEASED — tag `v0.1.0`):** v0.1 cluster COMPLETE. All five items done,
> committed, and pushed before tagging: **(1)** sprint-cadence D15/A5 fresh-context `kata-review` SHIP —
> clears the last pending gate on the sprint-cadence milestone. **(2)** wiring-completeness interim pin —
> prose pointers in `kata-evaluate` item 9 + `kata-review` 6(b) marking the full sweep as a post-v0.1
> ORCHESTRATOR INTEGRATION-GATE step. **(3)** guard-consistency repo-wide — `_safe_path` guards unified
> to `ValueError` across `mutation_run`/`grounding_gate`/`escalation`/`intent_scaffold`. **(4)** CWE-23
> `.snyk` record — standing policy entry for the 17-LOW operator-supplies-own-path class in
> `kata_install.py`. **(5)** benchmark n=0→n=1 live — first live run on real control fixture (D5).
> **Final full adval: 2141 pytest PASSED / validate 47/0 / Snyk medium+ 0.** Versioning policy flipped:
> bump-on-modify active (STANDARDS §3). Remaining backlog items (#6–#13 + wiring-completeness full build)
> explicitly deferred to v0.1.x — none blocks the v0.1 core contract; see `BACKLOG.md` "Explicitly
> deferred to v0.1.x" section. **NEXT milestone: v0.2** (tasklist + worker self-select; adapters;
> post-v0.1 deferred items). Records: `BACKLOG.md`, `ROADMAP.md` Progress table, `docs/STANDARDS.md` §3,
> `CHANGELOG.md` v0.1.0 entry.

> **CURRENT (2026-06-30, D131 model-tiering COMPLETE — built, gated, ready to commit; builds on D130 `8af2e37`):**
> D131 = **relative, mode-driven model-tiering** — DONE across **3 waves**, all via subagents. **W1:**
> `tools/kata_models.py` (NEW pure-stdlib resolver: `resolve`/`step_down`/`fallback_chain`/`family_of`, family ladders
> DATA registry, `ID_MAP`, `SKILL_WORK_CLASS`); A1 re-introduction guard in `validate_skills.py`
> (`check_model_in_skill_frontmatter`, case-insensitive, SKILL.md-frontmatter-only, adapters/config exempt);
> `update.ps1` bare-`exit`→`throw`/`$global:LASTEXITCODE` fix; `protocol/config.md` `models` schema. **W2:**
> `kata_roles.py` relative tokens (`anchor`/`anchor-1`/`anchor-2`, delegating to `step_down`); `kata-orchestrate`
> dispatch-time model-selection prose + R2 ≤2-then-omit fallback (401/403 raises); `kata-bootstrap`/`kata-initiate`
> anchor-write of the `models` block. **W3:** `kata-write-skill` no-`model:` authoring note; D131 entry in
> `DECISIONS.md`; full **47/47** work-class map (25 critical / 12 coding / 10 economy) + count-agnostic coverage test.
> **Contract:** model resolved at dispatch as a differential off the operator's session model (anchor); zero-step cells
> inherit by omission (`None`/OMIT), explicit id only strictly below anchor (determinant = step-count, not work-class);
> R1 coder-floor (essential-coding ≤ standard-coding ≤ anchor); R2 fallback OMIT-terminus; BC: absent config ⇒ inherit
> byte-for-byte. Folds R1–R8; builds on D130; implements D59. **Quality loop:** adval between W2/W3 (SHIP; 4 fixes incl.
> `family="auto"` activation, shared `step_down` DRY primitive). Deep adval (PASS all 7 DESIGN §4 criteria, independently
> re-run). **Two real defects caught by LIVE PROOF / D98 and fixed** (validating D124): (1) advanced/coding wrongly
> stepped down — coder-floor now gated to `mode=="essential"`; (2) MAJOR full-id anchor silently disabled tiering —
> `_normalize_anchor` now maps full ids → short names. **Gates:** pytest **2126 passed / 2 skipped / 0 failed**;
> `validate_skills` **47/0** WITH A1 guard; Snyk medium+ **0** on all new/changed Python. **UNCOMMITTED** —
> operator-approved commit + push to master is the immediate next step.
> **NEXT:** commit + push to master; then version/closeout per the loop. Records: `.planning/specs/model-tiering/`,
> `DECISIONS.md` D131.

> **CURRENT (2026-06-29, SESSION END — install-update-polish SHIPPED + PUSHED · tip `1ac85ed` in sync; pytest 1991 ·
> 47 skills/0 · Snyk med+ 0):** The hybrid install/update/polish feature is COMPLETE, gated, committed AND pushed —
> `master` tip is **`1ac85ed`, in sync** (`git log origin/master..HEAD` empty; **3 commits this session**). Three
> LOCKED decisions: **D127** `write_settings` MERGE-fix (the single working-pattern edit — strict BC); **D128** Phase A
> (the core update path); **D129** Phase B+C (overlay + fork). Plus a README rewrite (pitch / features / per-platform
> install). **(D127)** `kata_settings.write_settings` now **MERGES** — load-existing strict/fail-closed → overlay owned
> keys (`settingsVersion`/`parentDir`/`vaultDir`) → preserve prior `vaultDir`-when-absent → preserve `confirmedPlatforms`
> + unknown keys. Kills the D121 confirm-state clobber + the sibling vaultDir-drop. **(D128 Phase A)** NEW stdlib
> `tools/kata_version.py` (`.kata-version` stamp + `.kata-manifest.json` content-hash + `is_pristine`/`suite_semver`);
> engine `--update`/`--factory-reset`(`--reinstall`)/`--hard`/`--dry-run`/`--git-sha`/`--ref`; M1 plain-install stamp;
> `_sweep_managed_slots` (fail-closed orphan sweep); `update.sh`+`update.ps1` bootstraps (**ALL git here**; M2 dirty-tree
> guard ABORT-by-default + `--discard-local`; `--check` no-mutation; `--hard` confirm-gated); `.gitignore`+SETUP+README
> docs. **(D129 Phase B+C)** stdlib `tools/kata_overlay.py` (overlay store `<home>/.kata-overlay/overlay.json` + M4
> frontmatter composer); engine `_materialize_pass` (markers `.kata-managed`+`.kata-overlay-materialized`, M3 missing-base
> fail-soft); `kata-improve` local-adaptation mode (overlay vs fork by edit-category; `improve.allowUpstreamEdit` rail;
> `adaptation_context` from `.kata-version`); stdlib `tools/kata_supersede.py` (resolve/validate shadows, fail-closed);
> engine shadow precedence (**fork > overlay > pristine**; dormant-overlay NOTE; validate-STOPs-before-materialize;
> factory-reset un-shadows); `kata-promote` shadow-binding; STANDARDS supersedes-now-wired. **KEY FIX (deployment
> blocker):** the install/materialize/shadow path is **STDLIB-ONLY** — `kata_overlay`/`kata_supersede` dropped yaml — so
> overlays/forks no longer **silently no-op** under a real `uv run`-from-home-root install (pyyaml lives only under
> `tools/`). **Invariants held:** the 5 frozen `kata_install.py` engine fns (`_flat_link_skills`, `_link_or_copy`,
> `install`, `copy_project`, `confirm_platform`) **BYTE-UNCHANGED** (MD5-verified each phase); never-git (all git in the
> bootstraps; engine fed only `--git-sha`); `kata_settings.py` untouched outside D127. **Proofs:** write_settings
> post-build PASS; Phase A live install→update→factory-reset→uninstall **11/11**; Phase B overlay-materialize **15/15**;
> Phase C fork/shadow **8/8**; CAPSTONE clean-install-from-fresh-clone via real `install.sh` **7/7**; **SIX** adversarial
> reviews all SHIP/PASS (incl. a FINAL whole-feature pass = SHIP, zero direct-fixes). **Gates:** pytest **1991 passed,
> 2 skipped** (the 2 = known env-sensitive Windows-no-DevMode symlink skips); validate **47/0**; Snyk medium+ **0**
> (`kata_install.py` carries **17 LOW CWE-23**, operator-supplies-own-path class, below gate → STANDING hardening item).
> **NEXT (operator):** install on Windows (`irm …/install.ps1 | iex`) + run a full test environment; update via
> `& "$env:USERPROFILE\.kata-home\update.ps1"`. **★ Watch for the SPECULATIVE spurious drift NOTE on first real update**
> (orientation §4 #1 — informational-only but noisy). The closeout docs (CONTEXT/STATE/HANDOFF/orientation) are
> **uncommitted**, to be committed next. Records: `DECISIONS.md` D127–D129; `.planning/specs/install-update-polish/`.

> **CURRENT (2026-06-29, D129 SHIPPED — install-update-polish Phase B+C · pytest 1991 · 47 skills/0 · Snyk med+ 0):**
> install-update-polish FEATURE-COMPLETE (Phase A+B+C all live-proven). Hybrid update system fully landed:
> local adaptation is an OVERLAY (parametric, `kata_overlay.py`) or a FORK (deep, `kata_supersede.py`),
> never mutating the installed base. Phase B: B1 stdlib-only overlay store + M4 frontmatter composer;
> B2 `_materialize_pass` (`.kata-overlay-materialized` marker, M3 fail-soft, split out of stamp except);
> B3 `kata-improve` local-adaptation mode; B4 `SETUP.md` overlay docs. Phase C: C1 stdlib-only
> `kata_supersede.py` (resolve/validate shadows, fail-closed); C2 fork > overlay > pristine precedence,
> validate-STOPs-before-materialize, factory-reset un-shadows; C3 `kata-promote` shadow-binding note; C4
> `STANDARDS` supersedes-now-wired; `update.{sh,ps1}` `--ref` passthrough. Deployment blocker fixed:
> overlay/supersede are stdlib-only — no pyyaml — so the install path works under real `uv run`-from-home-root
> bootstrap. Live proofs: overlay 15/15, fork 8/8 (real no-yaml env). The 5 frozen engine fns
> byte-unchanged; `kata_settings.py` untouched. Records: `DECISIONS.md` D129.
> **REMAINING:** cross-phase final gate + clean-install capstone, then operator merge/push gate.

> **CURRENT (2026-06-29, SESSION END — BOTH FEATURES SHIPPED + PUSHED · tip `8d84125` in sync; pytest 1765 ·
> 47 skills/0 · Snyk med+ 0):** Two features built, gated, committed AND pushed this session — `master` tip is
> **`8d84125`, all in sync** (`git log origin/master..HEAD` empty). **(1) D125 (`a749f5d`) — `kata-validate`**, the
> always-available validation mini-loop (`skills/evaluate/kata-validate`): a programmatically-callable
> `validate(payload, target, profile) -> Report{passed, findings[]}` that runs **inline on ANY data or another
> agent's output** with **NO freeze/INTENT/`kata.config`** required; 4 deterministic-first METHOD-by-reference legs
> (grounding / review / slop / conditional score); its **OWN thin conductor** (`kata-loop`/`kata-onboard` precedent —
> `kata-orchestrate` byte-for-byte untouched); bounded ≤2 passes; payload-as-data isolation; report-only default with
> per-finding human-gated fix via a single writer (validators stay no-write); tripwire + cross-family-judge rails; NEW
> pure `tools/validation_report.py` + `render_validation_banner`. **(2) D126 (`8d84125`) — install/onboarding final
> polish** in 4 ADDITIVE+BC slices, the **5 `kata_install.py` engine functions byte-for-byte UNTOUCHED, none of the 18
> working patterns altered**: **G1** NEW `install.sh` (curl|sh) + `install.ps1` (irm|iex) + `uninstall.{sh,ps1}`
> wrapping the EXISTING `kata_install.py` engine (idempotent, no-cruft, `KATA_SRC` offline override, ships an
> uninstaller, honest curl|sh caveat); **G2** ADDITIVE headless flags (`--yes`/`--non-interactive`/`--answers-json`/
> `--json`/`--uninstall`/`--target-dir`) + non-TTY auto-skip + semantic exit codes (0 ok/1 not-confirmed/2 usage/
> 3 not-found/4 permission/5 conflict) + idempotent re-install=0 no-op + machine JSON→stdout/human→stderr
> (autonomous-loop DEFERRED); **G3** optional `acceptanceCriteria` in `intent_scaffold` (byte-identical BC absent) +
> `protocol/intent.md` + `kata-initiate` step 2g + S2 gate value #9 (confirmed-absent PASSES, no deadlock; "blanket
> looks-good FAILS" preserved); **G4** NEW pure `tools/kata_router.py` (`..`-guarded idempotent marked-stanza
> upsert + orphan-marker data-loss guard) + `kata-onboard` v0.2.0 opt-in human-gated router-stanza into the target's
> AGENTS.md; uninstaller removes exactly that block. **Gates this session:** pytest **1765 passed**, `validate_skills`
> **47/0**, Snyk **medium+ 0**, offline install/re-install/uninstall smoke green on **BOTH Git Bash and PowerShell**,
> **live e2e seam proof WIRED** (the D124 lesson applied). **validation-misses now 14** (D125 = `kata-validate`
> severity fail-open + class fail-open; D126 = `kata_router` orphan-marker data-loss, class `stateful-hole`). Each
> feature ran the FULL recipe: grill→freeze→freeze-gate `kata-review`(HOLD→fix→SHIP)→disjoint-slice build
> (TDD/mutation-proof)→integration gate→live wiring/e2e proof→PART A `kata-evaluate`→PART B D98 `kata-review`→
> (fixes)→operator merge gate→checkpoint. **NEXT = `install-update-polish`** — release-readiness for update / uninstall
> / settings, the operator's chosen next step (they install + run a full test environment once it's done). **3 items:**
> (1) the **headline gap — there is NO functional update path today** (re-running curl|sh does NOT pull/update); a
> one-command `--update`; (2) **uninstall polish** (orphaned-link sweep, stanza-registry, dry-run preview); (3)
> **`write_settings` MERGE-fix** (the one item that edits a working pattern — needs its OWN freeze-gate + strict BC).
> The intake brief is written: **`.planning/specs/install-update-polish/REQUIREMENT.md`** (pre-grill, not yet frozen).
> Records: `.planning/specs/{kata-validate,install-onboarding,install-update-polish}/`, `DECISIONS.md` D125 + D126,
> `validation-misses.jsonl` (`d125-kata-validate`, `d126-install-onboarding`).

> **CURRENT (2026-06-29, FEATURE 2 BUILT — install/onboarding final polish — D126; pytest 1764 · 47 skills/0 ·
> Snyk med+ 0):** The install/onboarding surface is finished off in four gated slices, **ADDITIVE + backward-compatible
> throughout** — the **5 `tools/kata_install.py` install-engine functions are byte-for-byte UNTOUCHED**; **no working
> pattern altered**. **(G1) One-command + GitHub install:** NEW repo-root `install.sh` (`curl|sh`) + `install.ps1`
> (`irm|iex`) + `uninstall.sh`/`uninstall.ps1` — they clone/seed then **invoke the EXISTING `kata_install.py` engine**;
> idempotent, no-cruft, **`KATA_SRC` offline override**; documents the clone path + "Use this template"; an **honest
> `curl|sh` caveat** (checksum protects the download-then-run, NOT the pipe); the uninstaller ships. README + `docs/SETUP`
> updated. **(G2) Headless install+setup:** ADDITIVE flags on `kata_install.py` (`--yes`/`--non-interactive`,
> `--answers-json`, `--json`, `--uninstall`, `--target-dir`) + non-TTY auto-skip; **SEMANTIC EXIT CODES** (0 ok / 1
> not-confirmed / 2 usage / 3 not-found / 4 permission / 5 conflict=non-kata-only); **idempotent re-install = 0 no-op**
> (no `changed` field); machine JSON→stdout, human→stderr. **Autonomous-loop mode DEFERRED** (commit/merge/fix gates stay
> human). **(G3) Grill-for-goals:** ADDITIVE optional `acceptanceCriteria` in `intent_scaffold` (byte-identical BC when
> absent; NOT required) + `protocol/intent.md` amendment; `kata-initiate` **step 2g** (enumerate+confirm success criteria,
> start-with-the-end-in-mind) + **S2 gate value #9** like conditional value #8 — explicit "no criteria" **PASSES** (no
> deadlock; the verbatim "blanket looks-good FAILS" rule preserved; gate **STRENGTHENED not loosened**). **(G4) Router
> stanza:** NEW pure `tools/kata_router.py` (`render`/`write`/`remove_stanza` — `..`-guarded idempotent marked-block upsert
> between `<!-- kata:begin -->`/`<!-- kata:end -->`); `kata-onboard` (**v0.2.0**) gains an **opt-in human-gated Step-3 item**
> that writes the ~15-line stanza into the target project's AGENTS.md; the uninstaller removes exactly that block. Canonical
> AGENTS.md; CLAUDE.md stays a pointer. **Locked:** the persona-SOUL + AGENTS.md-router + CLAUDE.md-pointer "system prompt"
> concept is **already sound** — no change beyond G4. **Build:** 7 disjoint slices / 3 waves (W1 router+intent/initiate ·
> W2 install headless+uninstall · W3 onboard stanza + bootstrap scripts + README/SETUP). **Gate journey:** freeze-gate
> `kata-review` **HOLD** (the `changed:false`-would-force-an-engine-edit contradiction; the optional-field-as-gate-value
> deadlock) → fixed in frozen docs → **SHIP**; live offline install/re-install/uninstall smoke on **BOTH Git Bash and
> PowerShell**; **PART A `kata-evaluate` PASS**; **PART B `kata-review` SHIP** (6 minor findings); hardening folded in
> Finding 1 (marker-corruption data-loss guard), Finding 2 (headless `OSError`→exit 4), Finding 4 (`render_stanza` summary
> test). **★ 1 validation-miss the unit tests missed, PART B caught (`stateful-hole`):** the `kata_router` marked-stanza
> upsert had a **data-loss edge** — an unmatched/orphan `<!-- kata:begin -->` (no end) would, on the 2nd write, pair the
> stray begin with the new block's end and delete the lines between → fixed with a **fail-loud guard + byte-identical-after-
> raise test** (`d126-install-onboarding`). **Gates:** pytest **1764 passed** (new `kata_router` + `install_cli_headless` +
> `intent_scaffold` tests), validate **47/0**, Snyk **med+ 0**, both-shells offline smoke green. **Honest scope:** the known
> D124 env-sensitive benchmark test (`test_benchmark.py::TestRunDualGateCwd::test_importing_fixture_gives_q_one`) is green
> canonically but flaky in some subagent venvs — **NOT a Feature-2 regression, NOT a miss**; the `curl|sh` network fetch is
> **exercised, not proven**; Codex/Kiro install is **honest-scoped** (verify in-host). Records: `specs/install-onboarding/`,
> `DECISIONS.md` D126, `validation-misses.jsonl` (`d126-install-onboarding`).

> **CURRENT (2026-06-29, kata-validate BUILT — the always-available validation mini-loop — D125; pytest 1680 ·
> 47 skills/0 · Snyk med+ 0):** A NEW EVALUATE-family skill `skills/evaluate/kata-validate/SKILL.md` (v0.1.0,
> cost-weight 3, `kata/spine`) — a **programmatically-callable validation mini-loop**:
> `validate(payload, target="auto", profile) -> Report{passed, findings[]}`. **Always-available (NOT a module),
> callable inline on ANY data, requires NO runtime freeze/INTENT/`kata.config`** (a defining property);
> **dual-target** (arbitrary content OR another agent's output) with **payload-as-data isolation** (injection
> containment — the payload is graded, never obeyed). **4 deterministic-first legs by METHOD-by-reference:**
> grounding (`kata-evaluate` injected-knowledge + grounding_gate) · review (`kata-review` 5-surface RUBRIC) · slop
> (`kata-slop-check` G1–G6/A1–A3) · score (`kata-evaluate` conformance — conditional, N/A when no plan). **Own thin
> conductor** (the `kata-loop`/`kata-onboard` composition-wrapper precedent) — `kata-orchestrate` is **byte-for-byte
> untouched**; bounded **≤2 passes**; optional RS research; branded "Running KataHarness validation loop…" banner;
> **tripwire + cross-family-judge** safety rails. **Report-only by default; per-finding human-gated fix via a single
> writer** (validators stay no-write). **Built:** PURE `tools/validation_report.py` (findings schema · SARIF severity
> · `render_table` N/A-guard · `..`-guarded emit/load · **default-FAIL** `compute_passed` ·
> `tripwire_corpus`/`assert_tripwire_flagged`; no exec sink) + tests + tripwire fixtures; ADDITIVE
> `tools/kata_banner.py` (`render_validation_banner` + `--validation` flag); README regen. **Gate journey:**
> freeze-gate `kata-review` HOLD (reuse-as-module-dispatch self-no-op / built-but-unwired) → SHIP; **live end-to-end
> WIRED** (clean payload byte-identical · known-bad flagged 6 errors across 3 surfaces · injection flagged-not-obeyed;
> n=1 exercised); `kata-evaluate` PART A PASS; **PART B HOLD twice → SHIP**. **★ 2 fail-opens the unit tests + PART A
> missed, PART B caught (default-FAIL escape class):** **(F1)** `severity_of` was case-sensitive
> (`ERROR`/`Error`/`REJECT`/`ESCALATE` → `info`) so `compute_passed` returned True on a real error finding →
> case-normalize + synonym map + mutation test. **(F1b)** the band-map fix was a half-measure — slop-detected/
> needs_work/hold tokens + slop major/minor still slipped to passed=True (violating `kata-slop-check` LOCKED L2) →
> full §10-2 verdict-token coverage + conductor `hold:true` stamp + major-slop fixture. 2 misses logged
> (`d125-kata-validate`). **Gates:** pytest **1680** (+84: 78 engine + 6 banner), validate **47/0**, Snyk med+ 0.
> Records: `specs/kata-validate/`, `DECISIONS.md` D125, `validation-misses.jsonl` (F1/F1b).

> **CURRENT (2026-06-29, benchmark build DEEP-AD-VAL'd + integration-completed + metric-hardened — D124; pytest 1597 ·
> 46 skills/0 · Snyk med+ 0):** Operator-requested deep adversarial validation of the D123 benchmark build BEFORE push
> ("end-to-end applied properly, no loose ends, no overcomplication, no drift"). 5 fresh-context opus reviewers →
> operator-gated fixes → 7 fix workers → re-confirm (3 reviewers) → **all CLEAN/SHIP**. **The engine slices were
> unit-solid; the INTEGRATION + RENDER + METRIC layers had ship-blocking gaps the unit gates (PART A + D98) couldn't
> see.** As built, D123 would have scored every REAL control **Q=0** (dual-gate ran tests with no cwd/import-context),
> never produced its replay-definition (build_def/criteria/delta unwired), failed to render its report ({{BENCHMARK_*}}
> tokens absent from the template), let an arm WIN via negative/NaN cost or omitting its worst dimension, and mis-fired
> delta-mode (fresh benchmark_id → false "drifted"). **All fixed (TDD/mutation):** dual-gate cwd (Q=0→Q=1 proven);
> definition+criteria+delta WIRED; metric read-path sanity + worst-case imputation (gaming vectors DEAD, over-fix sweep
> clean); new BRAND-consistent benchmark-report.template.html; k-repeats honest-simplified (mean±spread deferred, R6
> no-drift confirmed); costUSD wired; delta-identity (repeat=same benchmark_id→sameDefinition:true→honest harness-delta).
> **★ The recurrence system caught itself:** kata-orchestrate×phantom-reuse hit the BLOCKER threshold (D123+D124
> built-but-unwired) → T2 auto-drafted PROPOSAL-phantom-reuse.md (proposed standing guard: an end-to-end
> WIRING-COMPLETENESS dry-run on a realistic fixture — unit+injected gates can't see unwired seams) → marked proposed →
> human-merge-gated. **Meta-lesson:** built-but-unwired/exec-context/metric-read gaps need a realistic end-to-end dry-run,
> now a proposed standing gate. 3 fail-opens logged (d124-deepadval). **Gates:** pytest 1597 (1536→1597), 46/0, Snyk
> med+ 0. **Honest scope: n=0 LIVE** (real control fixture = D5, operator-supplied). **COMMITTED-LOCAL; PUSH HELD**
> (b90a8a2 freeze + 72c1b8f D123 + D124) for the operator commit/push gate. **NEXT (operator):** commit/push gate → then
> the D5 real control fixture for the first LIVE run; PROPOSAL-phantom-reuse freeze-gate+merge; D3 benchmark→improve hook.
> Records: DECISIONS.md D124; specs/kata-loop-benchmark/ (DESIGN amended); PROPOSAL-phantom-reuse.md.

> **CURRENT (2026-06-29, kata-loop-benchmark v1 BUILT [the D99 C-arc keystone] — D123; pytest 1536 · 46 skills/0 ·
> Snyk med+ 0):** Queue item (e) step 2 DONE. The deterministic outcome+efficiency benchmark — the keystone that measures
> C-on/C-off learning lift (D99 tumbler #4). Built **entirely via subagents**, **AUTONOMOUSLY at operator request**,
> through the FULL recipe: SWE-bench review + deep web research → grill-RESOLVED RESEARCH.md → DESIGN/PLAN → freeze-gate
> HOLD→SHIP (caught a dual-gate RCE seam: F2P/P2P run as test-IDs-as-DATA via mutation_check.run_named_test, not run_gate)
> → 6-slice/5-wave build → kata-evaluate PART A PASS → **D98 PART B HOLD (1 BLOCKER + 2 MAJOR + 3 MINOR, all proven by
> running the code) → fixed → re-confirm D98 SHIP**. **Design:** an EXPERIMENTAL CONTROL — immutable reference cloned per
> run into `<base>-katabenchmark<N>` (rigidity = the control, not the metric); 2-axis scorecard (Axis Q floor-gated +
> dual-gate F2P/P2P + mutation; Axis C tokens/$/wall-clock/etc, host-dependent fields nullable); floor-gated composite
> (Pareto + scalar, efficiency only among floor-passers); content-pinned Benchmark Definition + repeat_from + delta mode;
> hidden off-by-default `benchmark` module (not in bootstrap); two-tier report (never gates; n=1 directional). **Built:**
> S1 usage_meter.py (net-new metering), S2 benchmark.py (scorer), S3 benchmark_def.py (definition+delta), S4
> benchmark_control.py (immutable clone), S5 kata-benchmark-report skill, S6 config.md + kata-orchestrate wiring. **D98
> caught the load-bearing fail-open:** the dual-gate runner was ORPHANED (never wired) → every floor-passing arm scored
> Q=1.0, quality axis non-functional → wired + engine flags dual_gate_evaluated:false; + a run_dual_gate traversal hole
> (external test-IDs → pytest exec) → _guard_node_id + exec-safety row; + phantom skill citations / fake honesty-pin →
> real engine honesty+recommendations. 3 integrity MINORs fixed (hash collision, floor partial-RESULT, negative usage).
> 3 D98 fail-opens logged to validation-misses.jsonl (d123-benchmark). **DEFERRED:** D1 concurrent bakeoff arms (Spec B
> not executable; v1 = sequential/single-arm + k-repeat + arm-ranking scorer), D2 research-judge, D3 benchmark→improve T2
> optimization proposals, D4 promotion, D5 the real control FIXTURE (operator-supplied; design fixture-agnostic). **Honest
> scope: n=0 LIVE** (synthetic fixtures + unit tests; never run on a real control repo = D5). **Gates:** pytest 1536
> (1324→1536), validate 46/0 (new skill; README regen), Snyk med+ 0. **COMMITTED-LOCAL; PUSH HELD** for the operator
> commit/push gate (built autonomously while operator away). **NEXT (operator):** push gate → then provide the real
> control fixture (D5, orientation §5) for the first LIVE benchmark run, and/or (a) Debug Mode live run, (e D3)
> benchmark→optimization-proposal hook. Records: `specs/kata-loop-benchmark/{RESEARCH,DESIGN,PLAN}.md`, DECISIONS.md D123.

> **CURRENT (2026-06-28, D117–D121 ARC ADVERSARIALLY VALIDATED [ad-val] + TARGETED FIXES — D122; pytest 1324 · 45
> skills/0 · Snyk med+ 0):** The cross-cutting holistic red-team of the 5-build arc (between-build seams the per-build
> D98s couldn't see), D111-pattern, fully subagent-driven: 5 parallel fresh-context opus reviewers → synthesis →
> operator-gated fix scope → workers (TDD/mutation) → integration gate → **fresh-context D98 re-confirm (all 4 fixes
> SOLID)**. **NO BLOCKER, NO invariant-defeating MAJOR** — every D117–D121 invariant survives cross-build composition.
> **Fixed (operator-gated):** (1) MAJOR Tier-2-park-clobbers-Tier-1-escalate-artifact on the stateful-destroy path
> (fixed at both layers: kata-orchestrate parks-and-returns + escalation.py fail-closed non-clobber guard); (2)
> debug_report `_snyk_rollup` negative floor (honesty engine); (3+4) doc-truth drift (validation-misses.md 9→10;
> exec-safety.md kata_install row → the real `_real_probe_runner` sink); (5) exec-safety registry COMPLETENESS now
> structural (new test). 3 fail-opens (#1/#2/#5) logged to validation-misses.jsonl (`d122-adval`). **Deferred per D111
> anti-over-fix:** the latent/prose findings + 2 re-confirm nice-to-haves (corrupt-escalation-file parse error;
> completeness-test substring/prefix limits). **NOTE:** kata-debrief×honesty-fail-open now at 2 distinct runs (1 short
> of T2 auto-proposal). **Gates:** pytest 1324 (1314→1324), 45/0 (README regen), Snyk med+ 0. **UNCOMMITTED** pending
> operator commit gate: the D122 fixes + this session's doc updates (CONTEXT/HANDOFF/orientation from last session) +
> the new `specs/kata-loop-benchmark/RESEARCH.md` (benchmark grill RESOLVED, ready to freeze). **NEXT:** operator commit
> gate → then freeze the kata-loop-benchmark (planning subagent authors DESIGN/PLAN from RESEARCH.md). Records:
> `DECISIONS.md` D122; `specs/kata-loop-benchmark/RESEARCH.md`.

> **CURRENT (2026-06-29, CODEX ADAPTER LIVE-HARDENED + MULTI-MODEL LAYER CONFIRMED LIVE n=0→1 — D121; pytest 1314 ·
> 45 skills/0 · Snyk 0 on changed lines):** Queue item (e), step 1. The operator installed **Codex CLI 0.142.3**
> (ChatGPT-authed) locally — lifting the 2nd-platform install gate. The **first live exercise of the D108 multi-model
> dispatch/probe/confirm chain** (previously stub-only, n=0) immediately surfaced a real adapter defect codex-cli
> 0.142.3 requires: (1) `codex exec` refuses to run outside a trusted git dir without **`--skip-git-repo-check`**;
> (2) it **blocks reading stdin** when the runner leaves stdin open (the harness probe hit its 120s timeout this way).
> **Fixed (4 surgical edits, TDD):** added `--skip-git-repo-check` to `kata_dispatch.codex_command` + the
> `kata_install._PROBE_COMMANDS["codex"]` probe; added `stdin=subprocess.DEVNULL` to both `_subprocess_runner` and
> `_real_probe_runner`. (kiro builder/probe untouched; `--sandbox` policy unchanged; no new exec sink / no `shell=True`
> — `test_exec_safety` green.) **Live confirm now PASSES:** `kata_install.py --platform codex --confirm` → `confirmed:
> true, "probe ok", confirmedPlatforms:["codex"]` in ~6s (real `codex exec` returns the `SSENRAHATAK` token). The
> multi-model layer (read-only validator/researcher routing; coder-routing still DEFERRED per D108) is now LIVE-proven
> on a real 2nd platform. **Gates:** pytest **1314** (1310→1314), `kata_dispatch.py` Snyk **0**; `kata_install.py` has
> 6 PRE-EXISTING Low CWE-23 path-traversal findings (in `..`-guarded path code, NOT touched by this fix, below the
> medium+ gate) — flagged as a separate pre-existing hardening item, not fixed here. **NEXT (e), step 2:** build the
> **`kata-loop-benchmark` keystone** (operator chose this) — grill→freeze→build the benchmark module + a reference-task
> fixture + a single-vs-multi-model metric set; with Codex now confirmed live, it can include a REAL multi-model arm
> (not just a single-model baseline). Then (a, last) Debug Mode live run. Records: `DECISIONS.md` D121; benchmark spec
> TBD `specs/kata-loop-benchmark/`.

> **CURRENT (2026-06-29, SECOND-BRAIN RECALL [read-contract + files-only adapter] BUILT — D120; pytest 1310 · 45
> skills/0 · Snyk 0):** Queue item (d). The READ side of the loop's cross-run learning — names the long-reserved
> `engram.backend` CONSULT seam (D9/D30/D99). Per operator decision, scoped to the **Recall read-CONTRACT + a
> files-only default adapter** (defer external stores, the `kata-reason` decider, and the write/distill half [β LEARN
> feed D74]). Resumed cleanly after a session-limit cut the freeze-gate mid-verdict: re-ran a fresh freeze-gate
> (HOLD→SHIP; B1 open-vocabulary contract + B2 REQUIRED_PROTOCOL registration + N1/N2/N3 + 2 ownership-map fixes) →
> 3-slice 2-wave build → `kata-evaluate` **PART A PASS** → **D98 PART B SHIP — NO must-fix** (every probe defended).
> Built **entirely through subagents**. **Built:** **(R1)** `tools/recall.py` — the PURE engine: `recall_payload_schema`
> (THE contract — **shape-validated, NOT a closed vocabulary**: `source`/`backend`/`produced_by` are OPEN
> adapter-supplied strings so external Librarians drop in without re-contracting), `validate_payload`, the files-only
> `recall_from_paths` adapter (reads LESSONS/DECISIONS/prior-INTENT/understand-map/validation-misses[+handled]),
> `select_records` (**hard token-overlap>0 predicate**; recency only RANKS; **NO embeddings/RAG**), always-surface open
> recurrences (`recurrence_detect.detect_from_paths`), `RecurrenceRecord` **projects out raw `evidence`** (no miss-text
> leak), staleness surfaced-not-filtered; **no exec sink, NO WRITE PATH** (returns a dict), `..`-guarded reads; 7
> mutation proofs. **(R2)** `protocol/recall.md` (NEW contract doc) + `protocol/engram.md` pointer (names the read-side
> binding; the gated CONSULT decider stays OFF; 6 engram terms preserved) + `tools/validate_skills.py`
> `REQUIRED_PROTOCOL["recall.md"]` registration (the engram/D74-BP2 precedent). **(R3)** `kata-initiate` v0.1.0→0.2.0 —
> Phase-1b recall-brief (open recurrences first, then matched records w/ provenance/stale; N2 sub-threshold note) +
> Phase-2 "2a-recall" read-only mirror surface. **The INTENT-never-written invariant is STRUCTURAL:** recall.py has no
> write path at all; `intent_scaffold.write_intent` (fed only by the operator-confirmed `answers`) stays the sole INTENT
> writer; the brief is display-only. **Read-only:** changes no gate verdict, auto-acts on nothing, mutates no surface.
> **Honest scope:** the decider + write-half are NOT activated (deferred); external stores are deferred adapters behind
> the same contract; the files-only adapter degrades gracefully on absent sources. **Deferred MINORs (D98
> nice-to-haves):** a min-token-length(2) doc note in recall.md §2; a `query.kind` schema `open:True` comment. **NEXT
> (operator order b→c→d→e):** **(e) install + confirm a 2nd platform (codex/kiro) → run the single-vs-multi-model
> `kata-loop-benchmark` (D108)** — the benchmark harness is runnable; the run is **gated on the operator installing the
> 2nd CLI** (operator action). Then (a, last) Debug Mode live run (n=0→1). Records:
> `specs/second-brain-learning/PLAN-recall.md`, `DECISIONS.md` D120.

> **CURRENT (2026-06-28, IaC TIER-2 [preview/approve half] BUILT — D119; pytest 1261 · 45 skills/0 · Snyk 0):** Queue
> item (c). The live-apply half of the IaC specialists (Tier-1 = author/review/gate, D110), scoped by operator decision
> to the **preview/approve/plan-capture HALF** — the actual cloud EXECUTION is a **DEFERRED, n=0-live, creds-gated seam**
> (`run_apply` → NotImplementedError; nothing in this build can mutate infra). Operator chose: build-the-preview-half-now
> (stop at the creds wall), **both TF + CFN**, stateful-destroy = a **typed self-binding capability-gate** (not Tier-1's
> hard-block). Built **entirely through subagents**. Grill (subagent-framed → 3 operator calls + adopted defaults) →
> PLAN (planning subagent) → **freeze-gate kata-review HOLD→SHIP** (caught: F2 a README/version-bump ownership
> contradiction → README regen centralized to the conductor integration-gate; F1 the capability grant wasn't
> self-binding to the plan hash → now is; F3 CFN must hash the FULL describe-change-set + a dedicated ARN grammar) →
> 4-slice 3-wave build → `kata-evaluate` **PART A PASS** → **D98 PART B SHIP — NO must-fix** (first zero-fail-open build
> this session; every bypass attack failed CLOSED). **Built:** **(A)** `tools/iac_apply.py` — the PURE engine: 4 argv
> builders (shell=False, structured, no `-target`/`-auto-approve`, dedicated CFN ARN grammar), `plan_hash` (TF binary
> `tfplan` / CFN full `describe-change-set` via `canonical_cfn_plan_bytes`), `approval_verdict` (plan-hash-bound; re-plan
> invalidates), `capability_gate_verdict` (3 self-binding conditions: grant.hash==plan hash AND authorized⊇stateful-set
> AND typed token — fail-closed on every miss), `apply_state`, sibling-artifact `.kata/iac-apply.json`
> (`iac_apply_schema`/`emit`), audit-record builder, and `run_apply` (the deferred NotImplementedError seam); pure (no
> sink — AST-scanned), 6 mutation proofs incl. the self-binding (c) + the seam (f). **(B)** `protocol/exec-safety.md` (4
> DEFERRED operator-domain sink rows; `_SHELL_TRUE_ALLOWLIST` untouched) + `protocol/iac-safety.md` §9 Tier-2 contract.
> **(D)** `kata-orchestrate` IaC region (v0.2.0) — the Tier-2 apply state-machine slotted AFTER Tier-1's escalate
> verdict; park-never-auto-apply; STOPS at READY_DEFERRED; sibling artifact (Tier-1 `.kata/iac.json` + D111
> re-classification untouched). **(C)** both specialists `kata-iac-terraform`/`kata-iac-cloudformation` (v0.2.0) —
> Tier-2 preview/capture sections at the Tier-1 boundary markers, DRY-pointing to §9. **The catastrophic invariant
> holds by construction:** no `subprocess` anywhere in the engine; `run_apply` raises always; the typed self-binding
> capability-gate fail-closed on no-grant/empty-set/partial-cover/stale-hash/missing-token. **Honest scope:** the entire
> apply path is **n=0-live / creds-gated / DEFERRED** — loudly labeled; nothing claims apply "works." **Deferred MINORs
> (D98 nice-to-haves, NOT built):** `approval_verdict` returns PENDING_PLAN (vs BLOCKED) on a non-dict approval
> (fail-safe); a redundant CFN argv flag; N1 inherited stateful-set completeness (fix belongs in `iac_detect`). **NEXT
> (operator order b→c→d→e):** **(d) second-brain Recall** (own grill); then (e) 2nd-platform benchmark; (a, last) Debug
> Mode live run. **Tier-2 live-apply EXECUTION** itself remains future-gated on operator cloud creds. Records:
> `specs/iac-live-apply/PLAN-tier2-preview.md`, `DECISIONS.md` D119.

> **CURRENT (2026-06-27, RECURRENCE-HARDENING T2 BUILT — D118; pytest 1175 · 45 skills/0 · Snyk 0):** Queue item
> (b). Closes the recurrence loop the T1 manifest (D114) opened: when a failure-CLASS recurs (**3× distinct runs, or
> 2× for BLOCKERs**, clustered by `responsible_skill`×`failure_class`) the loop **auto-drafts a human-gated hardening
> proposal** — automating the "operator noticed the RCE recurred 3×" move that hand-triggered D112. Built **entirely
> through subagents** (operator directive). Grill (subagent-framed → operator-decided 3 calls + adopted defaults) →
> PLAN-t2 (planning subagent) → **freeze-gate kata-review HOLD→SHIP** (caught a real BC contradiction: adding `run_id`
> to `miss_schema()` breaks `test_schema_round_trips` while the plan forbade editing it → resolved via option-b: keep
> `run_id` documented + own the 9→10 test edit) → 3-slice 2-wave build → `kata-evaluate` **PART A PASS** → **D98 PART B
> SHIP** (every fail-open/invariant/BC attack held; 1 nice-to-have hardened: blank/whitespace `run_id` now falls back to
> `ts`). **Built:** **(S1)** `tools/recurrence_detect.py` — the PURE detector: `actionable_recurrences` (severity-aware
> threshold; distinct-run via `run_id` with `ts`-fallback incl. blank-coerce; handled-skip; off-vocab flagging),
> `distinct_run_counts`, `cluster_severity_tier`, `detect_from_paths`, the `.planning/recurrence-handled.jsonl` sidecar
> (`read_handled`/`append_handled`/`handled_schema`); + the **BC-safe schema extension** to `validation_misses.py` (soft
> 8-member `failure_class` enum + non-blocking `is_known_class`; nullable **`run_id`** → 10-field schema; `validate_miss`
> unchanged for failure_class so a non-fatal append never DROPS a miss); pure, no sink, mutation-proven (7 targets).
> **(S2)** `skills/meta/kata-improve` v0.1.0→**0.2.0** — the auto-DRAFT proposal sub-mode (drafts `PROPOSAL-<class>.md`
> + the `proposed` marker; **footprint pinned to exactly those 2 paths**; routes to freeze-gate kata-review → **human
> merge**; NOT kata-promote) + `protocol/validation-misses.md` T2 contract (act-but-gated; T1 observe-only preserved).
> **(S3)** `kata-orchestrate` Final-gate — one **`run_id` per run** stamping + the **non-fatal** detector hook (all
> modes; NOTE + auto-invoke the draft; silent no-op absent any actionable recurrence). **Invariant:** T2 READs + AUTHORs
> a proposal — never changes a gate verdict, edits a skill/protocol/tool, writes `guarded`, or merges (the guarded marker
> + the actual guard stay human). **Honest scope:** T2 PROPOSES; the human authors+merges the guard. **T3** (auto-author
> the guard itself) = OUT OF SCOPE / C-arc-gated, future. The footprint/`guarded` invariant is **prose-pinned** (LLM-skill
> architecture — no code gate possible; same risk class as every Write-capable skill). **NEXT (operator order b→c→d→e):**
> **(c) IaC Tier-2 live-apply** (own grill + non-git safety contract; live-apply path gated on operator cloud creds);
> then (d) second-brain Recall; (e) 2nd-platform benchmark; (a, last) Debug Mode live run. Records:
> `specs/recurrence-hardening/PLAN-t2.md`, `DECISIONS.md` D118.

> **CURRENT (2026-06-27, DEBUG MODE PHASE 3 [the FINAL phase] BUILT — D117; pytest 1108 · 45 skills/0 · Snyk 0):**
> Completes Debug Mode end-to-end at the skill/seam level — the **core loop is now functionally complete** (comprehend
> P1 → find/route P2a → characterize/drift-gate/apply-or-defer P2b → **report/onboard P3**). Built **entirely through
> subagents** (operator directive). PLAN-p3 (planning subagent) → **freeze-gate kata-review HOLD→SHIP** (caught a real
> BLOCKER: LD12's mandated "Snyk before/after" cited a `RESULT.json` field that NO P1/P2 surface emits → resolved by a
> real persisted `.kata/snyk/<id>.json` artifact piggybacking the fix-loop's existing before/after states + Snyk MCP;
> +2 MINORs) → 6-slice 2-wave build (A engine; D/E wave-1; B/C/W wave-2) → `kata-evaluate` **PART A PASS** → **D98 PART
> B HOLD→fix→re-confirm SHIP** (caught 2 MAJOR fail-opens in the LD12 honesty machinery the conformance gate passed).
> **Built:** **(A)** `tools/debug_report.py` — the pure LD12 report-assembly engine (confidence map · deviation→fix→
> pinning-test · regression+security proof incl. real Snyk before/after · honesty pinned at the engine: behavioral-only
> + heuristic-confidence + n=0-live; **finding_id** join = `drift_gate.defer_record` derivation; 5 mutation proofs;
> no exec sink). **(B)** `skills/evaluate/kata-debrief` — the LD12 author/renderer (two-tier `kata-report` shape; reports
> never gates). **(C)** `kata-closeout` `Step 3b` — debug-gated; offers kata-debrief; reuses Decision 2/3 (no new git
> path). **(D)** `skills/execute/kata-lang-profile` + 6 lang profiles + config specialist — LD10, prose-only, selected by
> footprint file extensions, injected at dispatch (IaC precedent), no fork/no new Python. **(E)** `skills/coordinate/
> kata-onboard` — LD13 first-run/convert-to-loop, composes built install-portability surfaces; convert-to-loop +
> `.planning/` scaffold honestly labeled NEW. **(W)** `kata-orchestrate` — P3-seam resolved + LD10 injection + the
> `.kata/snyk/<id>.json` before/after persistence (no new sink — Snyk MCP already existed; persistence is a Write).
> **Security (load-bearing):** D98 caught (1) Snyk **regression-masking** (engine trusted prose `newFindings` → now
> recomputes `max(stored, max(0,after−before))`, missing-count ⇒ not-clean) and (2) `applied:true` **not route-gated**
> (research finding could inherit another's proof under a finding_id collision → now gated on `route=="auto-fix-eligible"`
> + ambiguous-id refuses to cross-join); both fixed at the **engine**, mutation-covered; re-confirm SHIP. **Honest scope:**
> behavioral drift only (structural = §5 fast-follow); confidence = LD5 v1 heuristic; **Debug Mode still n=0 live** (proven
> on seeded fixtures, never run end-to-end on a real repo — the natural next step, newly possible). 2 validation-misses
> logged (D114 manifest). **Deferred MINORs:** clamp the cosmetic `newFindings` display on malformed input; a pre-existing
> `kata-report`/`kata-closeout` "verdict from RESULT.json" wording inconsistency (RESULT.json has no `verdict` field).
> **kata-onboard** tagged `kata/spine` (validator requires spine-or-module; least-wrong for an on-ramp) — a recorded
> divergence from PLAN-p3's `kata/coordinate+onboarding`. **NEXT (operator picks):** exercise Debug Mode end-to-end on a
> seeded fixture repo (first live run); or recurrence-hardening T2; or IaC Tier-2; or second-brain Recall; or 2nd-platform
> benchmark. Records: `specs/debug-mode/{DESIGN,PLAN-p3}.md`, `DECISIONS.md` D117.

> **CURRENT (2026-06-27, DEBUG MODE PHASE 2b [the PROTECT half] BUILT — D116; pytest 1062 · 42 skills/0 · Snyk 0):**
> Completes the **core Debug Mode loop** (comprehend P1 → find/route P2a → characterize + drift-gate + apply-or-defer
> P2b). Built entirely through subagents. Freeze-gate SHIP → 3 slices (F1 engine; F2+F3 parallel) → evaluate PART A
> PASS → D98 PART B SHIP (found 2 MEDIUM fail-opens in the drift machinery → fixed → re-confirm SHIP). **Built:** (F1)
> `tools/drift_gate.py` — behavioral drift-gate engine (§5 v1): AEL integrity (rejects green-in-before exceptions;
> trusted finding-bound input), green→RED=BLOCK, **vanished-baseline-green=BLOCK** (D98 fix), narrowed nondeterminism
> scrub (D98 fix — no longer masks real value changes); 5 mutation proofs; no exec sink; structural layer = honest
> non-enforcing seam (FAST-FOLLOW). (F2) `skills/execute/kata-characterize/SKILL.md` — blast-radius characterization
> suite, pins-except-deviation, left-behind, establishes AEL. (F3) `kata-orchestrate` `## Fix-application phase` —
> per auto-fix-eligible finding: characterize → kata-tdd in worktree → drift gate → evaluate+D98+Snyk → apply or
> DEFER (can't-fix-without-drift); AEL orchestrator-owned (worker can't enlarge it). Gated on `kata/module/debug`.
> **Honest scope:** behavioral drift enforced; structural/public-API invariance = §5 v1 fast-follow. **NEXT: Debug
> Mode P3** (language prompt-profiles LD10 + onboarding/convert-to-loop LD13 + LD12 closeout confidence report) — the
> final phase; then Debug Mode is functionally complete. Records: `specs/debug-mode/{DESIGN,PLAN-p2b}.md`, `DECISIONS.md` D116.

> **CURRENT (2026-06-27, DEBUG MODE PHASE 2a [the FIND half] BUILT — D115; pytest 990 · 41 skills/0 · Snyk 0):**
> Built **entirely through the loop/subagents** (operator directive — every step delegated to spare main context):
> planning subagent → freeze-gate **HOLD→SHIP** → 3-slice build (D1 engine; D2+D3 parallel) → evaluate **PART A PASS**
> → D98 **PART B HOLD→fix→re-confirm SHIP** → merge. **Built:** (D1) `tools/deviation.py` — the pure LD4-funnel +
> LD5-confidence engine (self-consistency ≥2/3, **corroboration HARD gate**, confidence+routing, force-LOW;
> mutation-proven; no exec sink); (D2) `skills/execute/kata-deviate/SKILL.md` — the LLM driver (FM-deviation via the
> AST-safe `evaluate_spec`; `kata-research` escalation-only); (D3) `kata-orchestrate` `## Deviation-discovery phase`
> gated on `kata/module/debug`, emits `.kata/deviations/findings.json`, P2b seam left. **D98 caught a real fail-open**
> in the corroboration gate (`None==None` co-location → LLM-only finding could reach auto-fix-eligible) → fixed
> fail-closed + **corroborator objectivity now code-enforced** (`_OBJECTIVE_SOURCES`, no longer trusts prose) + null/
> empty hardening; re-confirm SHIP (every attack fails closed). **Honest scope:** P2a STOPS at routed findings — fixes
> NOTHING (characterization LD6 / drift gate §5 / fix loop LD9 = P2b). The first real "conformance-passed,
> adversarial-caught" event since the D114 manifest exists to record it. **NEXT: Debug Mode P2b** (the PROTECT half),
> then P3. Records: `specs/debug-mode/{DESIGN,PLAN-p2a}.md`, `DECISIONS.md` D115.

> **CURRENT (2026-06-27, VALIDATION-MISS MANIFEST T1 BUILT — D114; pytest 907 · 40 skills/0 · Snyk 0):**
> Operator-directed feature (their idea): a durable, **universal, observe-only** manifest logging when the conformance
> gate (`kata-evaluate`) PASSED something the adversarial lens (`kata-review`/D98)/re-confirm/human later CAUGHT — the
> **data layer for recurrence-hardening (D101)** / the Hermes C-arc's harness-facing sibling. Makes "operator notices a
> recurrence" (the D112 RCE catch) a first-class signal. Built alongside Debug Mode but universal (hook in the shared
> `kata-review` RUBRIC → every mode). Freeze-gate **HOLD→SHIP** (caught: emit hook contradicted kata-review's read-only
> contract → relocated write to orchestrator; non-fatal guarantee prose-only → pinned/tested) → evaluate **PART A PASS**
> → D98 **PART B SHIP** (2 LOW hardening fixes moved the BC guarantee fully in-code). **Built:** `tools/validation_misses.py`
> (schema/validate/append[append-only,CWE-23,non-fatal]/read/count_by_class/passive `recurrences`; mutation-proven) +
> `protocol/validation-misses.md` + the universal flag(read-only)→write(non-fatal) hook. **Tiers:** T1 done (log/count/
> surface, observe-only); **T2** = recurrence→gated-proposal (= D101, needs grill); **T3** = auto-author guards
> (C-arc-gated, future). **NEXT: Debug Mode P2** (7-step deviation pipeline LD4 + confidence routing LD5 +
> characterization-gen LD6 + behavioral drift gate §5) — the manifest's first live exerciser; then P3. Records:
> `specs/recurrence-hardening/{BRIEF-validation-misses,PLAN-t1-manifest}.md`, `DECISIONS.md` D114.

> **CURRENT (2026-06-27, DEBUG MODE PHASE 1 BUILT — D113; pytest 867 · 40 skills/0 · Snyk 0):** First phase of the
> phased Debug Mode build (queue item a; DESIGN frozen). 3 disjoint slices → freeze-gate **HOLD→SHIP** (caught the
> `eval`-RCE class in the PLAN — D112 paying off) → orchestrated build → `kata-evaluate` PART A **PASS** → D98 PART B
> **HOLD→fix→re-confirm HOLD→fix→SHIP**. **Built:** (S1) the `debug` run-shape, gated on a distinct `kata/module/debug`
> module marker (mirrors kata-slop-check; version-up provably unaffected, BC); (S2) `tools/function_model.py` — the
> `function_model` oracle with `_safe_eval` (**AST-allowlist, no eval/exec**) spec-wrapper, registered in exec-safety.md;
> (S3) `skills/plan/kata-comprehend/SKILL.md`. **The evaluator is escape-safe AND DoS-safe** after two HOLD rounds —
> the re-confirm caught a chained-Pow explosion the first fix missed → fixed categorically (`**` removed entirely).
> **Honest scope:** P1 produces+validates the oracle only — no deviation pipeline / fix loop / drift gate (all P2);
> confidence stored not routed. **NEXT: Debug Mode P2** (7-step deviation pipeline + confidence routing +
> characterization-gen + behavioral drift gate), then P3 (language profiles + onboarding). **Operator-raised future
> feature (assessing lift, not yet built): a validation-miss manifest** — log critical misses by the validation stack,
> feed the recurrence-hardening/learning loop (D101 + the Hermes-borrowed C-arc), eventually auto-propose+author its own
> guards (gated). Maps onto existing recurrence-hardening + second-brain-learning. Records: `specs/debug-mode/{DESIGN,PLAN-p1}.md`, `DECISIONS.md` D113.

> **CURRENT (2026-06-27, EXEC-SAFETY STANDING GUARD BUILT — D112; pytest 786 · 39 skills/0 · Snyk 0):** Operator
> noticed RCEs recurring and asked "is this the first?" — it was the **3rd instance of one class in one component**
> (`kata-preflight`: freeform `install` [freeze-gate] → `package` source-injection [D98] → freeform `verify` [D111]),
> each fixed in isolation (whack-a-mole). Fired the **recurrence-hardening** loop (D101): built
> `protocol/exec-safety.md` (structured-argv-only contract + a **sink registry** of every `subprocess` in `tools/`
> with trust domain external/operator/internal) + `tools/tests/test_exec_safety.py` (**AST-based** regression — fails
> CI on a new `shell=True` outside the operator-domain allowlist, on `kata_preflight` regaining `shell=True` or reading
> the freeform `verify`/`install` fields, etc. — the guard that would have caught #3). Audit: shipped code clean (only
> `mutation_run`/`run_result` use `shell=True`, both operator-authored). **NEXT: starting the Debug Mode build (queue
> item (a)) — DESIGN frozen `specs/debug-mode/DESIGN.md`, both blockers long cleared.** Record: `DECISIONS.md` D112.

> **CURRENT (2026-06-27, HOLISTIC RED-TEAM of D108/D109/D110 + FIXES — D111; pytest 776 · 39 skills/0 · Snyk 0;
> D98 re-review CLEAN):** Session first-task per `NEXT-SESSION-ORIENTATION.md` — a fresh-context *cross-cutting*
> adversarial pass over the day's 3 back-to-back builds (the seams *between* them were unreviewed). 5 parallel
> reviewers → synthesis → operator-gated trimmed scope (fix confirmed findings; drop LOW cosmetic). **Real defects
> the per-build passes missed, all fixed + test-proven:** a **preflight RCE** (freeform `dep["verify"]` was executed
> before the SCA gate → structured `verifyImport` builder; freeform `verify` demoted docs-only), **IaC gate-skips**
> (case-sensitive ext match; `forceClassify` documented-but-never-wired; stateful-set gaps incl. KMS/Secrets/MSK/
> FSx/Backup/Logs/Timestream/QLDB/MemoryDB/Keyspaces/CFN-EC2::Volume), **Snyk truthiness** (→ strict `is True` +
> fail-closed), the **iac.json cross-seam fail-open** (kata-evaluate now independently re-classifies the footprint),
> **`resolve_roles` host-only** silently-dropped (→ `HOST_ONLY_ROLES` fail-closed), TF **`action_reason`** wrong
> nesting, manifest **TOCTOU**, regex `fullmatch`, and the **4th doc-drift recurrence** (worst `file:line` cites →
> function/section anchors, killing the class). **Operator caught one spiral** (a sandbox-default flip over-fixing a
> cosmetic finding) → reverted — the spiral-check was load-bearing. Deferred LOW/architectural (snake→camel rename,
> severity-floor enforcement, CDK-source, deterministic `iac_gate.py`). Applied **inline** (operator directive), not
> orchestrated. **Not a planned feature** — a hardening pass. Record: `DECISIONS.md` D111. **NEXT (the open queue,
> operator picks):** (a) **Debug Mode** build (DESIGN frozen, both blockers cleared — the onboarding killer-app);
> (b) IaC Tier-2 live-apply; (c) recurrence-hardening; (d) second-brain-learning; (e) install+confirm a 2nd platform
> → multi-model benchmark.

> **CURRENT (2026-06-26, IaC-SAFETY SPECIALISTS (Tier 1) BUILT — merge `396baa3`, D110; pytest 739 · 39 skills/0 ·
> Snyk 0; PUSHED, in sync):** capability-aware-assignment, narrowed to **IaC specialists** for v1 (the specialist
> value for frontier models is **safety/security/gate discipline, not language expertise**). 4-agent grounded research
> spike → grill → freeze → recipe build (4 slices). **Two specialists** `kata-iac-terraform` + `kata-iac-cloudformation`
> (`execute`, never-tiered, DRY-by-pointer to `protocol/iac-safety.md`); **Tier 1 = author/review/gate, NO live apply**
> (no cloud creds; cloud apply breaks git-reversibility — **Tier 2 deferred**, `specs/iac-live-apply/BRIEF.md`).
> Auto-activated by `tools/iac_detect.py` (classifier + plan/change-set destructive-parsers, fail-closed); gate =
> validate/cfn-lint → `snyk_iac_scan` (default-FAIL high/critical; **fail-closed if unwired**) → 8-smell lens →
> destructive analysis (static + parse-if-provided; no live plan gen) → `.kata/iac.json` → pass/fail/**escalate**
> (destroy/replace on a stateful resource → human-required). `kata-evaluate` reads the artifact; BC: no IaC ⇒ no-op.
> freeze-gate **HOLD→SHIP** · `kata-evaluate` **PASS 9/9** · **D98 HOLD→SHIP — caught a real safety BLOCKER** (stateful
> set too narrow: EFS/SQS/SNS/Kinesis/OpenSearch/Neptune/DocDB weren't escalating on destroy) + fail-open + overclaim,
> all fixed. Backout `pre-iac-specialist`. **NEXT (choose):** (a) **Debug Mode** build (both blockers cleared long ago;
> DESIGN frozen — the onboarding killer-app); (b) **Tier-2 IaC live-apply** (its own grill, gated on authenticated
> cloud access); (c) **recurrence-hardening** general build; (d) **second-brain-learning** (Recall contract); (e)
> install+confirm a 2nd platform → multi-model benchmark. Records: `specs/iac-safety-specialist/*`, `specs/iac-live-apply/BRIEF.md`.

> **CURRENT (2026-06-26, kata-preflight BUILT — the PRE-FLIGHT spine phase — merge `710347a`, D109; pytest 633 ·
> validate 37/0 · Snyk 0 med+; PUSHED, in sync):** D29 realized. Grilled in plain terms → 4 operator decisions
> (auto-run pre-approved installs · full v1 incl. cleanup report · one mechanism for build-deps + target runnable-env ·
> sandbox-when-available-else-host+warn), built through the recipe. **freeze-gate HOLD→SHIP** (command-injection
> BLOCKER + 3 MAJORs fixed) → 3-slice orchestrated build → **kata-evaluate PASS 9/9** → **D98 red-team HOLD→SHIP —
> caught a real untrusted-source RCE path** (`package=https://evil…` bypassing the forced registry) the evaluator
> missed; fixed via **per-manager package-NAME grammar** (no URL/VCS/source expressible) + approval-artifact path/claims
> + Snyk fail-closed. **Exists:** `tools/kata_preflight.py` (guarded auto-installer — structured argv never shell,
> freeform install string never executed, forced trusted registry, Snyk SCA pre-install, manifest-hash drift gate,
> machine-global registry + reference-counted cleanup [never auto-uninstall], target runnable-env probe,
> `preflight_required`/`gate_status`) · the spine skill `kata-preflight` (never tiered) · `kata-orchestrate`
> conditional fail-closed PRE-FLIGHT precondition (BC: no manifest ⇒ today's loop) · structured `dependencies.md` ·
> grill/design-doc/plan manifest pointers (36→**37 skills**). **Honest scope:** auto-install stub-tested (injectable
> runner); real install only behind freeze-approved-hash + Snyk + sandbox; workers never install. **Clears the 2nd of
> Debug Mode's two blockers (install-portability was 1st) → Debug Mode UNBLOCKED.** Backout `pre-kata-preflight`.
> **NEXT (choose):** (a) **Debug Mode** build (both blockers now cleared — DESIGN frozen `specs/debug-mode/DESIGN.md`;
> the onboarding killer-app); (b) grill **capability-aware-assignment**; (c) strategy BRIEFs (second-brain-learning ·
> recurrence-hardening); (d) install+confirm a 2nd platform → multi-model benchmark. Records:
> `specs/kata-preflight/{GRILL-LEDGER,DESIGN,PLAN}.md`.

> **CURRENT (2026-06-26, MULTI-MODAL LAYER BUILT — full routing wiring over the proof-slice — merge `1f58415`,
> D108; pytest 552 · validate 36/0 · Snyk 0 med+; PUSHED, in sync):** The D105 PARKED full layer is now wired,
> built through the full recipe. Frozen PLAN (4 disjoint slices) → **freeze-gate `kata-review` HOLD→SHIP**
> (caught a kiro write-vs-emit seam + a `config.md` false-contract + a self-introduced phantom `target.platform`
> citation) → **orchestrated build** (4 concurrent Sonnet workers in worktrees, TDD, mutation-proven, self-stamped
> — `concurrency.json maxInFlight:3`) → fresh-context **`kata-evaluate` PASS 9/9** (reproduced artifacts + executed
> seams live) → standing **D98 `kata-review` SHIP** (caught 5 stale role-map citations + 1 overclaim → fixed via
> stable section-name anchors). **Wired:** (A) `kata-orchestrate` `roles` load-guard (resolve via `kata_roles`,
> host=runtime adapter identity `"claude"` v1, fail-closed) + "Cross-model dispatch" section (build_brief→dispatch→fold
> per role-group site, LD6 concurrency, LD7 host-fallback); `config.md:27` flipped DESIGN-STAGED→**wired**. (B)
> `kata-initiate` Phase 2e "Make this run multi-modal?" + value #8; `kata-bootstrap` writes `roles`. (C)
> `kata_dispatch` `_brief_prompt` capture-model branch (codex emit / **kiro writes resultPath**) + `kiro_command`.
> (D) `kata_install` `.agents/skills/` targeting + kiro probe + `_PROBE_COMMANDS ⊆ _COMMAND_BUILDERS` invariant.
> **Honest scope:** read-only roles (validator→codex, researcher→kiro) **wired + stub-test-proven**; real run gated
> on install+confirm; coder-routing + copilot/cursor + evaluator-thresholds DEFERRED. **This makes a real
> single-vs-multi-model `kata-loop-benchmark` runnable** once a 2nd platform is installed+confirmed. Backout
> `pre-multimodel-layer`. **NEXT (choose):** (a) `kata-preflight` (the other Debug Mode blocker, D29/D103) → Debug
> Mode; (b) grill **capability-aware-assignment** (the specialist axis that multiplies with multi-model); (c) the
> strategy BRIEFs (second-brain-learning Recall contract; recurrence-hardening general build); (d) install+confirm a
> 2nd platform live + run the benchmark. Records: `specs/multi-model-orchestration/{DESIGN,PLAN}.md`.

> **CURRENT (2026-06-26, install-portability BUILT · multi-model GRILLED+FROZEN+proof-slice BUILT · red-team
> hardened · loop-init banner — tip `fe8d015`, D104–D107; pytest 542 · validator 36/0 · Snyk 0 med+):** A big
> build+research day. **(D104) install-portability BUILT** (the *simple* model after an operator course-correction
> from a config-resolution cathedral → memory [[grill-in-plain-terms]]): one central install + a 2-setting
> `.kata-settings.json` (default parent project folder + vault/second-brain location) + per-run **project search**
> (name + rough location → search → confirm; copy mode) + per-platform installer (Claude verified end-to-end via
> flat-link into `~/.claude/skills/`; Codex/Kiro best-effort; Quick own) + `docs/SETUP.md` + `.claude-plugin/plugin.json`.
> **(D105) multi-model-orchestration GRILLED → FROZEN DESIGN → Codex-validator PROOF-SLICE BUILT** (the operator's
> real "multi-modal" vision: route loop ROLES to platforms — Claude=coder, Codex=validator, Kiro=researcher).
> Grounded in **5 cited research agents** (`RESEARCH.md`): the `SKILL.md` Agent-Skills format is a **shared standard**
> across Claude/Codex/Kiro/Copilot/Cursor, and **all are headless-automatable**. **5 role groups** (coder · validator
> [red-team+anti-slop+grounding] · researcher · orchestrator · **evaluator** = a lightweight inline scorer that
> accepts/sends-back/**rerolls** via `bakeoff`); **default all-on-host, multi-modal opt-in at preflight**; **any role
> routable** (coder stays one sustained agent); **files+CLI dispatch** (concurrent background subprocesses); **failure
> → host fallback**; two orthogonal layers (platform/model × specialist). **Convergence HOLD#1: the D102 guard caught
> over-claimed reuse → relabeled NEW (N1–N5 with schemas) → re-confirm SHIP.** Proof-slice = `tools/{kata_roles,
> kata_dispatch}.py` + confirm-probe + `roles` config; **end-to-end proof** (validator→codex→normalized verdict)
> against a stub-CLI seam (codex not installed → real run gated on install+confirm). **(D106) 3-pass red-team
> hardening** of D104/D105 — fixed copy_project source-destruction, default-FAIL gaps, a spoofable confirm probe, a
> confirm→crash trap, corrupt-JSON/dup-skill robustness, + doc-vs-code lies (the `roles` load-guard is design-staged,
> not wired). **(D107) loop-init banner** — every run opens with a deterministic boxed `KATAHARNESS 改善型 · executing`
> readout (`tools/kata_banner.py`), painted in the closeout-report palette (`--color`); wired into `kata-loop`,
> documented in `protocol/narration.md` §5. **NEXT (choose):** finish the multi-model layer (wire `kata_dispatch`
> into `kata-orchestrate` + the `roles` load-guard + the "make this multi-modal?" preflight + more adapters) — makes
> a real single-vs-multi-model benchmark runnable; OR `kata-preflight` (the other Debug Mode blocker) → Debug Mode
> build; OR grill capability-aware-assignment. Records: `specs/{install-portability,multi-model-orchestration}/*`.

> **CURRENT (2026-06-25, Debug Mode GRILLED + DESIGN FROZEN + PARKED — `d010434`):** Roadmap session. Captured two
> big Phase-5 items as pre-grill BRIEFs — **capability-aware (multi-modal) assignment** (loop-wide stack-detection →
> specialist routing; resolves multi-model-orchestration's flagged "multi-modal?" question) and **Debug Mode** — then
> **fully grilled Debug Mode** to a frozen DESIGN. **Debug Mode** = a self-contained **run-shape `debug`** (peer of
> version-up), pointed at a whole codebase, **debug-in-confidence** (bugs out, behavior preserved); the
> onboarding/conversion killer-app. Design (7 grill rounds + a 4-thread research pass + 3 repo assessments, two
> convergence-gate HOLDs → SHIP): a NEW **`kata-comprehend`** builds an executable **`function_model`** oracle of
> intent; a **7-step deviation pipeline** (self-consistency → objective-corroboration HARD gate → adversarial
> refute-or-promote) gates on corroboration, not oracle accuracy; **behavioral drift gate** v1 (surface/AST +
> confidence-calibration = honest fast-follows, H4 caveat in backward-compat). LOCKED LD1–LD13; reuse claims
> verified (the D102 guard caught a phantom `kata-understand` reuse mid-grill — recurrence-hardening working). **Build
> PARKED** behind **`install-portability` (built first, DG-10b) + `kata-preflight`**. Artifacts:
> `specs/debug-mode/{BRIEF,GRILL-LEDGER,RESEARCH,DESIGN}.md`; the 3 assessed repos (debug-skill/claude-devtools/
> pointbreak-claude) = all BORROW-PATTERN, takeaways parked. **NEXT:** Phase 5 — **`install-portability`** (now the
> critical-path predecessor for Debug Mode) → multi-model → grill the strategy BRIEFs + capability-aware-assignment +
> v0.1 release-checklist.

> **CURRENT (2026-06-25, phantom-machinery first hardening BUILT + MERGED — `47648bf`, D102):** D101's worked
> example shipped — the **verify-before-reuse guard**. `protocol/reuse-claims.md` (cross-skill contract: *before
> claiming "reuses/composes X", grep/read X + cite `file:line`, else label NEW*) + by-path pointers in
> `kata-design-doc` / `kata-plan` RUBRIC / `kata-tdd` + a `validate_skills.py` regression rule (dual mechanism +
> body-integrity full-phrase guard + producer-existence FAIL-loud check). Built through the **full recipe**
> (subagent-driven Sonnet T1/T2/T3, Opus judgment): freeze-gate **HOLD→SHIP** · `kata-evaluate` **PASS 9/9** ·
> **T-fire proof-of-fire** (a fresh `kata-design-doc` agent refused to freeze a phantom `orient.emit_pointers()`
> claim → labeled NEW) · standing D98 `kata-review` **SHIP-WITH-FIXES→SHIP** (caught a default-FAIL gap where a
> renamed producer would silently disable the guard — fixed). pytest **456**, validator **36/0**, Snyk **0**,
> mutation non-vacuous. **Honest:** the rule enforces **presence, not behavior**; T-fire is **n=1, contaminated,
> no guard-off control** — corroborating, not causal proof (the mutation-bitten regression rule is the durable
> proof). Backout `pre-phantom-hardening`. Record: `specs/recurrence-hardening/{PLAN-phantom,REPORT-phantom}.md`.
> **NEXT:** Phase 5 EXTERNAL (install-portability → multi-model → testing-model) + **grill → freeze** the two
> strategy BRIEFs (`second-brain-learning` Recall-contract is load-bearing; `recurrence-hardening` general build)
> + v0.1 release-checklist (flip Policy A). Far-future: `kata-loop-benchmark` → DAG-in-DAG.

> **CURRENT (2026-06-24, loop-learning strategy locked + fix-loop hardening BUILT — `fc7f4f7`, D98–D101):** A long
> strategy + hardening session. **(1) The standing adversarial red-team is now wired (D98/L12):** `kata-review`
> runs after `kata-evaluate` PASS, before merge, on every code/contract-bearing build; `kata-evaluate` gained
> rubric **item 9 "reproduce, don't trust"** (regenerate derived artifacts; execute claimed seams). This wired a
> lesson the project had recorded (L10c) but never baked in — so it kept recurring. **(2) Loop-learning strategy
> locked (D99):** ship **Controlled (A)** now, **Gated-learning (C)** is the destination, **Hermes-fluid (B)** is a
> trap; the learning subsystem is re-modeled as **Second brain (data, BYO) + Recall (per-vault Librarian/adapter,
> downstream) + Reason (`kata-reason`, the Advisor/decider, core)** — *"Recall what you know · Reason what you'd
> do"*; "engram" retired (rename pending). C unlocks via a **four-tumbler** gate (BYO backend · a **readiness exam**
> = the measurable maturity def · **inline triage** red-team · **outcome benchmark** — `kata-loop-benchmark`
> promoted to keystone), bounded by the **C/B invariant** (*every Reason decision stays a frozen, gated,
> thrash-bounded, audited event toward a human-frozen goal — protect the process, not the decider*). Spec:
> `specs/second-brain-learning/BRIEF.md`. **(3) Recurrence hardening captured (D101):** when a failure-class recurs,
> the loop hardens the responsible agent (auto-detect → propose → gated human-approve, never auto-mutate) — the
> harness-facing sibling of Reason. Spec: `specs/recurrence-hardening/BRIEF.md`. **(4) Fix-loop hardening BUILT
> through the main loop (D100, `fc7f4f7`):** the Approach-A thrash guard — material (footprint-scoped)
> re-verification + a per-area (N=2) + run-level (`2×tasks+2` `[TUNABLE]`) thrash budget → `kata-diagnose`
> fix-vs-plan verdict → human only on a plan-problem. Freeze-gate **HOLD→resolved**, re-confirm **HOLD→resolved**,
> build `kata-evaluate` **PASS 7/7** + standing D98 red-team **SHIP-WITH-FIXES** (2 degrade-safe, fixed). pytest
> **447**, validator **36/0**, `codeBearing:false`. **Honest:** wired, exercised by **zero real thrash events**;
> N=2+ceiling provisional. **The adversarial lens caught the phantom-machinery / over-claimed-reuse class FOUR
> times** this session → memory `verify-primitives-before-claiming-reuse` + the live case for D101. **NEXT:** the
> **phantom-machinery first hardening** (document the fix-guide + place the guard in the responsible planning skill,
> then test it — D101's worked example) · then Phase 5 EXTERNAL (install-portability → multi-model → testing-model)
> + grill/freeze the second-brain-learning + recurrence-hardening BRIEFs + v0.1 release-checklist.

> **CURRENT (2026-06-24, WS-2 polish DONE — worker concurrency now artifact-provable — `4d8f01b`, D97):** Closed
> the last WS-2 honest gap (AUDIT §7): durable board timestamps were orchestrator-written (couldn't distinguish
> live concurrency from replay). Now **workers self-stamp `CLAIM`/`DONE` with their own clock** to the shared
> board, and the gate derives **`.kata/concurrency.json`** (maxInFlight · per-task wall-clock · overlap windows).
> Per operator direction, the evidence is produced by an **embedded in-context snippet in `protocol/board.md`** —
> **NO new committed Python** ([[prefer-in-context-over-new-python]]) — keeping the run **non-code-bearing**
> (`codeBearing:false`). 3-slice/2-wave orchestrated dogfood; **self-proving** — the build's own wave-2 workers
> (B+C) overlapped and this run's `concurrency.json` shows **`maxInFlight:2`** (~75s overlap). Fresh-context Opus
> `kata-evaluate` **PASS 7/7**; pytest **447**, validator **36/0**. Backout `pre-ws2-polish`. Record:
> `specs/ws2-polish/PLAN.md`. **NEXT:** Phase 5 EXTERNAL (install-portability → multi-model → testing-model) +
> v0.1 release-checklist (flip Policy A); M8 native-in-tool closeout rendering = adapter work; far-future = loop
> benchmark → DAG-in-DAG.

> **CURRENT (2026-06-24, WS-1 pre-launch re-grep CLEAN):** Ran the final pre-public sanitization pass — the
> work-internal proper noun + variants return **0 matches** across all tracked files, frozen specs, and the
> working tree (incl. untracked artifacts); the `Quick`/ACP plumbing seam is intact (20 files) and the scrub is
> consistent indirection, not bare deletion; light secret/key sweep clean. Hardened `.gitignore` (`/INTENT.md`
> root run-artifact + `.claude/`). **WS-1 is DONE** — the last pre-public sanitization gate. validator **36/0**,
> pytest **447**. **NEXT:** WS-2 worker-self-timestamp polish (code-bearing orchestrated build) → Phase 5 EXTERNAL
> + v0.1 release-checklist.

> **CURRENT (2026-06-24, WS-3 field-exercised + two-tier closeout shipped — `c265c42`, D96):** Ran the **first
> live use** of the WS-3 friendly closeout (n=0→1) by building a real feature through it: the closeout is now
> **two-tier** — a concise CLI/GUI summary that **links to a durable, on-brand, self-contained HTML report**
> (`.kata/closeout.html`) with a Markdown source (`.kata/CLOSEOUT.md`). 3-slice non-code-bearing dogfood
> (concurrent Sonnet workers, self-stamped): template+`BRAND.md` (S1), `kata-report` two-tier content (S2),
> `kata-closeout` emit+render-in-context+link (S3). Fresh-context Opus `kata-evaluate` **caught a cross-slice
> badge-class defect → fixed → PASS**. **Operator refined the brand live at the gate** (M4): dropped a wave
> motif + tab-like loop ribbon; landed the **first KataHarness logo** (kaizen ascending-bars + rising ochre
> arrow), readable **serif** section titles, and **error/warning/ok callout tiles**, on a **Hokusai-derived**
> palette. Non-code-bearing (`codeBearing:false`, 0 drift); pytest **447**, validator **36/0**. **Carry-out:**
> native in-tool rendering (hooks/statusline) deferred to adapters (M8). Backout `pre-ws3-report`. Record:
> `specs/ws3-closeout-report/PLAN.md`. **NEXT:** WS-1 pre-launch re-grep · WS-2 worker-self-timestamp polish ·
> then Phase 5 EXTERNAL + v0.1 release-checklist (far-future: loop benchmark → DAG-in-DAG).

> **CURRENT (2026-06-24, WS-3 user-friendliness BUILT — `d08908d`, D95):** The last pre-public workstream shipped.
> Brainstorm (Hermes/Devin/Claude-Code UX research) → frozen DESIGN (L1–L11) → freeze-gate `kata-review`
> **HOLD→SHIP** (caught a real backout seam — re-anchored to `.kata/RESULT.json.baselineSha`) → frozen PLAN
> (6-slice DAG) → **orchestrated version-up dogfood** (2 waves, concurrent Sonnet workers in worktrees,
> self-stamped overlapping wall-clock) → fresh-context Opus `kata-evaluate` **PASS 10/10**. **Shipped (8 files,
> non-code-bearing, `codeBearing:false`, 0 drift):** `protocol/persona.md` (nameless calm kata-craftsperson SOUL,
> moderate-non-expert default), `protocol/narration.md` (phase→plain map + never-tiered breakthrough + honesty
> guard), `engram.md` E23 register seam (gated), `kata-initiate` reflective **goal-mirror** (S2 gate refined-not-
> reversed, with teeth), `kata-bootstrap` one **"how careful"** dial (existing fields, advanced drawer),
> `kata-orchestrate` additive milestone narration, `kata-closeout`+`kata-report` **goal-anchored by-aspect
> closeout** + offered backout. **WS-4 + WS-5 folded in.** The build's own closeout dogfooded slice F. pytest
> **447**, validator **36/0**. **Honesty:** built + gate-PASS + fresh-eval PASS, **NOT yet field-exercised (n=0
> live UX runs)** — the next real Kata Loop run is the first UX test; adaptive register is a gated seam, not live.
> Backout `pre-ws3`. **NEXT:** field-exercise WS-3 on a real friendly run · WS-1 pre-launch re-grep · then Phase 5
> EXTERNAL (install-portability · multi-model) + v0.1 release-checklist; far-future = loop benchmark → DAG-in-DAG.

> **CURRENT (2026-06-22, WS-2 EXERCISED + `kata-slop-check` shipped — `ece872e`):** Built **`kata-slop-check`** (optional
> EVALUATE module `kata/module/slop`: fresh-context no-write, default-FAIL slop verdict, **in-context heuristics** —
> general G1–G6 + 3 MIT-attributed checks adopted from `ai-slop-detector`, no code copied) via a **real version-up
> dogfood** that doubled as the **WS-2 validation**. A fresh-context auditor graded the run **7/7**: 3-worker
> concurrency → a **live `research-needed` escalation** → orchestrator **parked the sub-tree** (S1+S4+S5) while S2/S3
> integrated → **`kata-research`** grounded the gap → **grounding gate GROUND×6** → **superseding re-plan** fold →
> frontier recompute → **mutation-proven** slice. The feature **caught a defect in
> its own build** (dangling seam pointer → NEEDS_WORK → fixed → CLEAN). **Parallelism + the in-loop RS path
> (audit-flagged "unexercised") are now exercised end-to-end (n=1).** Feature gate `kata-evaluate` **PASS**; pytest **447**,
> validator **36/0**. **Caveat:** board timestamps are orchestrator-written (live-vs-replay not artifact-distinguishable)
> → follow-up = **worker self-timestamping** (BACKLOG). Record: `specs/kata-slop-check/PLAN.md` +
> `specs/ws2-loop-autonomy/AUDIT.md`; audit trail `.kata/board.md`. Backout `pre-ws2-slopcheck`. **NEXT:** **WS-3**
> (user-friendliness — the big pre-public workstream) or remaining WS-2 polish (worker self-stamp).

> **CURRENT (2026-06-21, S3b DONE — G6 PROVEN; loop-hardening COMPLETE — `222cc7e`):** The live loop-back ran:
> KataHarness ran its own **Kata Loop twice**, operator-driven, and a fresh-context grade returned **G6 PROVEN**
> (7/7, corroborated against independent evidence — the Cycle-2 goal is a near-literal instantiation of the
> Cycle-1 understand-map's named adjacent gap, baseline SHA matched `RESULT.json`). **Cycle 1** = NIT-2 (validator
> asserts evaluators `kata-evaluate`/`kata-research` omit Write/Edit; `f72a3bb`); **Cycle 2** (loop-back, Phase 1b
> consumed the carried context) = MAJOR-3 (machine `codeBearing` flag in `footprint.py`; `kata-evaluate` rubric
> item 1 keys off it; `222cc7e`). Both cycles: real `kata-initiate` interview (G4 live), orchestrated Sonnet-worker
> build in a worktree, `prove_non_vacuous` → `mutation.json allNonVacuous:true` (**MAJOR-2 live-proven**),
> fresh-context `kata-evaluate` PASS, operator git/version-select gates. **MAJOR-1 (grounding) correctly did not
> fire** (no research-needed escalation — as PLAN-s3b predicted; stays unit-proven). **ALL 7 GAPS CLOSED
> (G1–G7).** pytest **445**, validator **35/0**, Snyk 0. Tag `pre-s3b`; closes BACKLOG NIT-2 + MAJOR-3. Record:
> `specs/loop-hardening/{PLAN-s3b,REPORT-s3b}.md`. **loop-hardening is DONE — "vetted, and demonstrably loops."**
> **NEXT:** remaining BACKLOG hardening (`_safe_path` guard consistency; planning-approach↔delivery-mode alignment)
> → **Phase 5 EXTERNAL** (install-portability · multi-model-orchestration) → v0.1 release-checklist.

> **CURRENT (2026-06-21, red-team seam-fixes + Kata Loop rename — `94539dd`; AT THE S3b BOUNDARY):** An adversarial
> red-team of S2+S3a confirmed the project's known **documentation-only seam** failure mode had partially recurred and
> we **fixed it inline (D92):** `kata-orchestrate` now explicitly **persists the grounding verdict** via
> `tools/grounding_gate.py` → `.kata/grounding.json` (MAJOR-1 — it was named only in the no-write `kata-evaluate`, so a
> real cycle would have silently skipped it) and **collects per-task `prove_non_vacuous` records** into the integration
> `gate_emit` mutation set (MAJOR-2). `kata-closeout` mutation row aligned to the strengthened S2 rule (MINOR-1).
> **Branding (D92, user):** "Greater Loop" → **"the Kata Loop"** across active/canonical surfaces; inner one-shot
> stays **"the Harness"**; **loop-back** unchanged; frozen `specs/greater-loop/` + history keep the old term as
> provenance; `CONTEXT.md` glossary added. **Deferred to BACKLOG:** machine `codeBearing` flag (MAJOR-3), validator
> no-write assertion (NIT-2), `_safe_path` guard consistency; plus the planning-approach↔delivery-mode alignment
> assessment. **validator 35/0, pytest 420, Snyk 0.** **6 of 7 gaps closed (G1–G5, G7).** **NEXT = S3b, the live
> loop-back (G6)** — operator-driven; the MAJOR-1/MAJOR-2 prose fixes get **live-proven** by it. Full S3b plan in
> `.planning/HANDOFF.md` §4.

> **CURRENT (2026-06-21, loop-hardening S3a DONE — `4391deb`):** **Grounding + research now have a concrete,
> testable substrate** (closes G5). `tools/escalation.py` = `research-needed` escalation payload + research-finding
> builders/writer (`.kata/escalations/<id>.json`); `tools/grounding_gate.py` = deterministic GROUND/REJECT/ESCALATE
> verdict + `.kata/grounding.json` (`allGrounded`); wired into `kata-research` (finding schema) + `kata-evaluate`
> injected-knowledge mode (both stay no-write). **G5 demonstrated end-to-end**: a real escalation + three findings
> graded GROUND·REJECT·ESCALATE (`allGrounded:false` correctly). Grounding is **conditional** (fires only on a
> `research-needed` escalation, not per-run). **pytest 420, validator 35/0, Snyk 0.** Fresh-context `kata-evaluate`
> **PASS 8/8**. Backout tag `pre-s3a`. **6 of 7 verified gaps closed (G1–G5, G7).** **ONLY G6 REMAINS = S3b, the
> live loop-back** — a real version-up re-entry that proves the loop loops (operator-driven: the human "run again"
> decision can't be simulated, `exercise-harness-for-real`). That is the next session, done WITH the operator.

> **CURRENT (2026-06-21, loop-hardening S2 DONE — `cddf9ff`):** **The gate now proves tests bite + initiation is a
> hard human stop** (closes G3+G4). `tools/mutation_run.py` = deterministic restoring mutate→run→restore loop (reuses
> `mutation_check`); `kata-tdd` PROVE points at it; `kata-evaluate` rubric item 1 now **requires** `.kata/mutation.json`
> `allNonVacuous:true` for code-bearing runs (closes the silent-skip hole). `tools/intent_scaffold.py` = schema-conformant
> `INTENT.md` writer; `kata-initiate` now a **hard structural interview STOP** (must `AskUserQuestion` for kind/target/
> vault/platform/grillDepth + execute, no inline inference). **G3 demonstrated end-to-end**: the runner mutated a live
> line → test flipped green→red → file restored byte-for-byte → `mutation.json` (`allNonVacuous:true`) emitted; fresh
> RESULT.json (`s2-integration`, 367) + footprint (`withinFootprint:true`). **pytest 367, validator 35/0, Snyk 0.**
> Fresh-context `kata-evaluate` **PASS 8/8** (it caught a missing RESULT.json regen — fixed — then re-confirmed).
> Backout tag `pre-s2`. **NEXT = S3** — grounding/research (G5) + the **loop-back** (G6): a real version-up re-entry that
> proves the loop loops, evaluating the handoff as it cycles back through `kata-initiate` Phase 1b (operator's hard
> requirement). See `.planning/HANDOFF.md` §4.

> **CURRENT (2026-06-21, loop-hardening S1.5 DONE — `e753504`):** **Status-surface adapters shipped** (closes G7) —
> the live view is now seamless per-platform via the *adapter* pattern applied to OUTPUT. **Seeded `adapters/`** with
> its first concrete member `adapters/claude/` (statusline command + `settings.snippet.json` w/ `refreshInterval:1` +
> README); `tools/kata_statusline.py` (agnostic `render_statusline` + fail-soft Claude entry); `tools/kata_web.py`
> (localhost web viewer, stdlib `http.server` bound 127.0.0.1, polls `/api/view` every 1s, renders 改善型 bars/ribbon/
> feed). Both **pull-consume** `build_view_model` — no push StatusSink, no `kata-loop` wiring. Grounded by
> `specs/loop-hardening/RESEARCH-s1.5.md`: **Claude** statusline feasible now; **Codex** has no live in-TUI surface
> (→ web/TUI fallback); **Kiro** only via a VS Code `.vsix` (deferred) — all documented, no fake bars. Fresh-context
> `kata-evaluate` **PASS**; operator-demo caught two render bugs (statusline SystemExit fail-soft + web numeric-child),
> both fixed w/ regression tests. **pytest 334, validator 35/0, Snyk 0.** Backout tag `pre-s1.5`. **NEXT = S2**
> (mutation proof G3 + interactive initiate G4), then **S3** (grounding/research G5 + the **loop-back** G6 — proves the
> loop loops). See `.planning/HANDOFF.md` §4.

**Phase:** **✅ `v0.1.0-alpha.2` SHIPPED — Greater Loop proven end-to-end (Phase 4 self-dogfood done)** · Phases 0–3 built + adversarial-reviewed + seam-fixed · **35 skills / 0 errors · pytest 205 · Snyk: residual CWE-23 documented FP** · private remote (taurran/kataharness), tip `3ed18d3` · **Updated:** 2026-06-21

> **CURRENT (2026-06-21, alpha.2 shipped):** **The complete Greater Loop ran end-to-end on KataHarness itself for
> the first time and shipped a real feature** — the **subagent-dashboard** (`tools/kata_dash.py` + `kata_dash_model.py`):
> a `rich` live TUI that tails `.kata/board.md`+`state.json` and renders worker subagents as artistic ASCII
> (`⛩ 道`, block bars, braille spinners, `GRILL▸…▸IMPROVE` ribbon). The run: `kata-initiate` (froze INTENT/PLAN) →
> orchestrated harness (DASH-model ∥ DASH-render, 2 workers/worktrees, octopus-merge, `gate_emit` RESULT.json,
> fresh-context `kata-evaluate` **PASS 8/8**) → `kata-closeout` (graph-backed `.kata/understand.md` via F2 — 107
> dashboard symbols mapped; human **version-select** → ship+tag). **The dogfood caught + fixed a real Windows
> UTF-8 render crash via the integration smoke test** (the gate doing its job). pytest 112→205. Record:
> `specs/subagent-dashboard/{INTENT,PLAN,SECURITY,REPORT}.md`. Backout tags `pre-dash` + `pre-phase0..3`.
> **loop-hardening sprint-cadence IN PROGRESS (closes the verified Phase-4 gaps).** Roadmap+grounding:
> `specs/loop-hardening/{ROADMAP,PLAN-s1}.md`. **✅ S1 DONE (`fedbb87`, fresh-eval PASS 8/8):** `tools/kata_board.py`
> emits the live coordination board (`.kata/board.md` incl. **PROGRESS heartbeats**) + single-writer `state.json`
> (self-creates `.kata/`); dashboard renders smooth heartbeat bars + progressLabel; title **`KATAHARNESS 改善型`**
> (kaizen-gata; torii+hiragana removed per operator, see [[ui-text-japanese-concise]]); `tools/kata_dash_demo.py`
> replay driver (delegates to kata_board). Closes **G1+G2**. pytest 244→268, validator 35/0, Snyk med+ 0.
> **⏸ STOPPED at the S1 boundary for the operator to WATCH the live dashboard + give feedback before S2/S3.**
> **S2** (mutation proof + interactive initiation; G3+G4) and **S3** (grounding/research + **loop-back iteration**
> proving the loop loops; G5+G6) are queued, not started. Backout tag `pre-s1`.
> **Then Phase 5 EXTERNAL reach** (install-portability · multi-model) remains after loop-hardening.

> **CURRENT (2026-06-20, BUILD-THROUGH COMPLETE):** **The entire Greater Loop is BUILT + merged + pushed
> (Phases 0–3, `f39f37b`).** Each phase = a real orchestrated foreground-parallel run (Sonnet workers in isolated
> worktrees → octopus-merge → integration gate → **fresh-context `kata-evaluate` PASS 8/8** → merge → push), per
> the no-inline rule. **What now exists end-to-end:**
> - **Phase 0 FOUNDATIONS** (`9e1b27c`): **F1** `tools/gate_emit.py` wires the eval artifacts into the live gate
>   (emits `.kata/{RESULT,footprint,mutation}.json`; dogfooded on the integration gate — closes the dogfood-2
>   residual). **F2** `tools/graph_gen.py` tree-sitter graph runtime → `kata.graph.json` per protocol/graph.md
>   (def/ref/import + PageRank, `call` deferred). Security: sha1→sha256 fixed; CWE-23 path-guard + documented FP.
> - **Phase 1 INITIATION** (`157804f`): **D91** self-contained modules (validator discovers `modules/*/*/SKILL.md`);
>   `modules/initiation/` + **`kata-initiate`** + **`protocol/intent.md`** (PINNED INTENT.md contract). Ingest →
>   classify kind → capture+freeze INTENT.md → interactive target/platform/vault config → dual spec-to-ready control.
> - **Phase 2 CLOSEOUT** (`20dac30`): `modules/closeout/` + **`kata-closeout`** (composes report/understand/handoff/
>   git; consumes F1 `.kata/` artifacts; NEVER gates; human gate satisfied?/commit·push·merge?/run-again·new?) +
>   **`kata-understand`** (opt-in graph-backed comprehension map, git/diff fallback).
> - **Phase 3 CONDUCTOR** (`f39f37b`): **`kata-loop`** thin conductor sequences initiation→harness→closeout, owns
>   the context-carrying loop-back (baseline · understand-map · lessons · prior INTENT); optional (absent ⇒ today's
>   direct run). Root `AGENTS.md` gains a "The Greater Loop" entry.
> Plans: `specs/greater-loop/PLAN-phase{0,1,2,3}.md` + `SECURITY-phase0.md`. Decisions **D87–D91**. Backout tags
> `pre-phase0..pre-phase3` on remote.
> **Adversarial review (2026-06-20, post-build):** a fresh-context red-team found the loop was "skills authored,
> wired by docs, with broken seams" — the sprint-cadence *wired-but-not-connected* anti-pattern partially
> repeating at the Phase-2/3 seam. **All findings fixed (`2d71f2e`):** kata-understand now WRITES `.kata/understand.md`
> (loop-back was reading a never-written file); kata-initiate gained a loop-back-context Phase 1b + `AskUserQuestion`;
> kata-closeout dropped stale "kata-loop not yet built" drift and wikilinks it; kata-orchestrate gained an explicit
> RESULT.json precondition; kata-bootstrap points to kata-loop; D40 marked superseded; INTENT.md/kata.config
> authority pinned. Validator 35/0, pytest 112. **Loop seams now consistent end-to-end (still documentation-wired
> — the Phase 4 dogfood is what proves the live run).**
> **★ NEXT = Phase 4 — the SELF-DOGFOOD TEST of the complete Greater Loop (operator-driven).** Per BUILD-THROUGH
> this is the single next TEST: run a full greater-loop cycle on KataHarness itself — `kata-initiate` (capture a
> real version-up INTENT) → harness (orchestrated) → `kata-closeout` (report + understand-map + **human
> version-select**). Real orchestrated run, never inline (`exercise-harness-for-real`). Likely tags
> `v0.1.0-alpha.2`. **THEN Phase 5** — external reach (install installers / multi-model / optional dashboard).

> **CURRENT (2026-06-20, Phase 0 closed):** **Phase 0 of the Greater Loop is BUILT + merged.** Real orchestrated
> foreground-parallel run: 2 worker subagents (Sonnet) in isolated worktrees → octopus-merge (0 conflict) →
> integration gate → fresh-context `kata-evaluate` **PASS (8/8)** → merged to master `9e1b27c`, pushed.
> **F1 — eval artifacts wired into the live gate** (closes the dogfood-2 residual): `tools/gate_emit.py` composes
> run_result/footprint/mutation_check → emits `.kata/{RESULT,footprint,mutation}.json`; dogfooded on the
> integration gate itself (109 passed, withinFootprint True). Skills wired: kata-evaluate (consumer),
> kata-orchestrate (emits at integration gate), kata-tdd (records mutation proof). **F2 — graph runtime
> operational**: `tools/graph_gen.py` tree-sitter floor produces `kata.graph.json` per protocol/graph.md
> (file/symbol nodes, def/ref/import edges, PageRank, content-hash incremental; `call` omitted = oracle-deferred);
> kata-graph SKILL names it the floor producer. Security: sha1→sha256 (CWE-916, real, fixed); CWE-23 path-guard
> added, residual = documented Snyk FP (operator CLI args, non-shipped tool; see `specs/greater-loop/SECURITY-phase0.md`).
> Plan: `specs/greater-loop/PLAN-phase0.md`. Safety tag `pre-phase0`.
> **★ NEXT (BUILD-THROUGH, no test until Phase 4) = Phase 1 INITIATION:** `modules/initiation/` (own AGENTS.md) +
> `kata-initiate` + frozen `INTENT.md` artifact + interactive target/platform/vault config (install-portability
> config layer folds in) + dual spec-to-ready control (user-says-execute OR grill self-proposes). Then Phase 2
> CLOSEOUT (`kata-closeout` + `kata-understand`, graph-backed by F2), Phase 3 `kata-loop` conductor — straight
> through. Then Phase 4 self-dogfood (the next test).

> **CURRENT (2026-06-20):** **Greater Loop DESIGN is FROZEN** (D87–D90; `.planning/specs/greater-loop/`). The
> wrapper around the harness: **INITIATION** (`kata-initiate` + frozen `INTENT.md` + interactive
> target/platform/vault config) → **HARNESS** (reused) → **CLOSEOUT** (`kata-closeout` + `kata-understand` map),
> sequenced by a thin **`kata-loop`** conductor with a context-carrying loop-back. Modules = `modules/<name>/`
> dirs w/ own AGENTS.md. testing-model folded into F1 (Hermes-grounded); install-portability config layer folds
> into initiation; execution UX = **foreground-parallel** + `subagent-dashboard` brief (build-later).
> **★ BUILD-THROUGH directive (operator):** build the WHOLE Greater Loop (Phases 0–3) continuously, **NO
> intermediate dogfood/test ceremony** — per-phase correctness gates (green/review) still apply; the next TEST is
> the **Phase 4 self-dogfood of the complete loop.** **NEXT ACTION = `kata-plan` partitions Phase 0 (F1 wire the
> dogfood-2 eval artifacts into the live gate · F2 make `kata-graph` actually run via tree-sitter) into disjoint
> slices → orchestrated foreground-parallel build → green+review → CONTINUE straight into Phase 1 (initiation),
> Phase 2 (closeout), Phase 3 (`kata-loop`) without stopping to test.** Then Phase 4 self-dogfood, then Phase 5
> external (install/multi-model). dogfood #2's eval libraries (run_result/footprint/mutation) exist but are
> **unwired** — F1 wires them. Safety tags `pre-dogfood-2` + `v0.1.0-alpha.1` on remote.

> **Dogfood #1 (2026-06-19):** self version-up enforcing `allowed-tools` ran through the full loop (readiness →
> skip-grill → footprint plan → TDD → fresh-context default-FAIL eval **PASS** → report). **Machinery held**
> (regression contract green end-to-end). **Headline finding:** the end-of-run writeup is **not self-sufficient**
> for in-depth evaluation — needs self-emitted `RESULT.json` + footprint manifest + recorded mutation proof
> (→ BACKLOG ★, strong dogfood-#2 candidate). Also: tree-sitter BLOCK too coarse (R1); manual-drive friction
> (R2). See `.planning/specs/dogfood-selfup-1/`.

> **CURRENT (2026-06-19, top of file — older history below is preserved, not current):** **sprint-cadence is
> BUILT + reviewed SHIP** (D78–D85; 11 tasks / 5 waves; commits `43e7c2c`→`e0d0610`). NEW `kata-plan` roadmap
> layer (`ROADMAP.md`), `kata-sprint` (G1–G4 boundary change-control), `kata-report` v1; the
> `delivery: one-shot|incremental` axis + prime-frame sizing (build-grounded: Fable5/Opus4.8/Sonnet4.6 = 1M
> window, ~0.40 effective band). `kata-orchestrate` stays **sprint-blind** (BC2). A fresh-context `kata-review`
> (D15/A5) returned **SHIP**; its one should-fix — `kata-sprint` was wired-but-not-connected — is **fixed**:
> **`kata-bootstrap` is now the boundary router (D86)**, routing a gated boundary → `kata-sprint`. **31 skills ·
> validator 0 · pytest 38 · Snyk 0.** Loop-cognition (β/RS/AO/ML, D74–D77) + D71 Priming-and-Grill shipped
> earlier this session. **Next = the endgame: dogfood version-up on KataHarness itself** (first real
> `delivery: incremental` exercise — will light up the deferred-runtime BACKLOG). See `.planning/HANDOFF.md`.

## Where we are

- Project scaffolded at `C:\Dev\Projects\KataHarness` (git, `.gitattributes eol=lf`). Foundation committed.
- Canonical docs: `AGENTS.md`, `CLAUDE.md` (pointer), `docs/{DESIGN,STANDARDS,TEST-PLAN}.md`, `README.md`
  (versioned skill index). `.planning/{PROJECT,ROADMAP,DECISIONS(16),LESSONS-LEARNED(10),BACKLOG,STATE,STEERING,REVIEW-v0.1}.md`.

- Reference skills vendored (gitignored): `research/reference/{mattpocock-skills,bmad-method}`; GSD local
  at `~/.claude/get-shit-done`.

- **15 `kata-*` skills built**, all `0.1.0/experimental`: the v0.1 ten + `kata-review` + the four
  v0.2-pulled-forward (`kata-diagnose`, `kata-selfhandoff`, `kata-improve`, `kata-write-skill`). 3 remain
  unbuilt: `kata-tasklist` (deferred — redundant with state.json + the plan DAG until workers self-select),
  `kata-zoom-out` (deferred — too thin), `kata-engram` (backlog, gated on a mature engram, D9). The README
  index is the source of truth. (Adversarial-reviewed → `.planning/REVIEW-v0.1.md`; new batch review pending.)

- **2026-06-10 — CPP decoupled (D57) + PortaVault→PokeVault (D58).** CPP is no longer the test medium or
  consumer (history stands; provenance kept). The D16 A/B target is reshaped to **small one-shottable test
  projects**. PokeVault vault is READY (`C:\Users\taurr_nvs748q\PokeVault\PokeVault`, incl.
  `toolkit/agent-sops/`) — KataHarness's install/test home (under `toolkit/`).

## Done so far (this session, 2026-06-06)

- Froze the shared control: CPP `03-DESIGN.md` + `03-01-PLAN.md` (4 locked decisions, 4-task disjoint partition).
- Built the **5 v0.1 execution skills** (`kata-orchestrate/worktree/board/tdd/evaluate`) → `0.1.0/experimental`.
- Ran **Arm A** (KataHarness via Sonnet subagents in CPP worktrees) → GREEN: 244 tests, det build, Snyk 0,
  fresh-context `kata-evaluate` 9/9 PASS, **0 drift / 0 escalations / 0 human interventions** ([[LESSONS-LEARNED]] L9).

- Arm A lives on CPP branch `test/phase3-kata` (worktree `C:/Dev/_kata_armA/integration`).

## Also done (2026-06-06, cont.)

- **A/B verdict recorded: TIE** ([[LESSONS-LEARNED]] L10). Arm B (GSD) matched Arm A on every objective
  metric incl. the identical in-lane auto-fix → execution half on-par, not better; differentiation lives in
  the (frozen-for-both) planning half. User shipping Arm B to CPP `main`.

- **Built the remaining v0.1 planning skills + the adversarial leg** → all `0.1.0/experimental`:
  `kata-grill` (deep, to the L8 standard: GSD-format choice-or-text questions, relentless + doc-grounded,
  doc-baking, convergence criteria, anti-shallow guard + a `resources/DECISION-LEDGER.md`),
  `kata-context`, `kata-design-doc`, `kata-plan` (disjoint file-ownership + wave DAG), `kata-handoff`,
  and **`kata-review`** (adversarial/red-team — the EVALUATE leg the A/B exposed as missing, L10).

- **v0.1 is now skill-complete: 11 skills built** (the 10 + kata-review). README index promoted.

## Active workstream — OPERATING MODES (Spec A1 + A2 + A3 MERGED to master; A4 in progress)

**Spec A1 (foundations) DONE + merged**: skill-conformance validator (`tools/validate_skills.py`), schema-v2
frontmatter (`cost-weight`+`license`+namespaced `tags`), frontmatter-generated README index,
`protocol/config.md`+`protocol/dependencies.md`, `docs/TAXONOMY.md`, Apache-2.0 `LICENSE`. Reviewed HOLD→SHIP.
**Spec A2 (tier families) DONE**: `kata-grill`/`kata-review`/`kata-plan` → 3 tiers each, `kata-diagnose` →
light/full; shared `RUBRIC.md` per family (DRY-by-pointer); `kata-design-doc`/`kata-tdd` got a mode depth-hint;
validator gained tier-family rules. Adversarially reviewed (HOLD→SHIP; surfaced **D33: structural invariants
are never tiered**).
**Spec A3 (bootstrap + wiring) DONE + merged 2026-06-08** (merge `27ca76c`): **`kata-bootstrap`** (run-shape
router — individual/batch/version-up/advanced as PRESETS over the mode axis; D24c ladder; run-shape-relevant
interview) + new light **`kata-readiness`** (harness-health + target-readiness + re-entrant config detection) +
**`kata-orchestrate`** reads `kata.config`, resolves family→tier (fallback Standard/D25) with a **fail-closed
load-guard** (GB12). `kata.config` schema gained `runShape`+`target` (version-up). Grilled GB1–GB13 → promoted
to **D34–D46**; adversarially reviewed **SHIP** (`.../modes-A3-bootstrap-wiring/REVIEW.md`). **24 skills**,
validator green, 12 tests. Versioning **policy A** (hold all skills at 0.1.0 till v0.1 ships, then bump-on-modify).
**A4 (version-up + kata-graph) — DONE + MERGED to master 2026-06-08 (merge `de4b0ee`, reviewed SHIP; 25 skills,
validator green, 13 tests)**: DESIGN frozen (`.planning/specs/modes-A4-version-up/DESIGN.md`);
grill ledger fully converged (GB1…GB10 + HOLD#1/#2/#3 resolutions; coherence audit PASSED;
`.planning/specs/modes-A4-version-up/GRILL-LEDGER.md`); A4-GB decisions promoted to **D47–D56** (this
session). Scope: **`kata-graph`** (tree-sitter-floor, feature-agnostic cached `kata.graph.json` contract,
feature-seeded ~3k-token digest, pluggable grep/tree-sitter/Graphify-MCP backend) + **version-up wiring**
(grill Phase 0 ingest, footprint-scoped disjoint ownership with defer-first + escalate-rare protections,
full-suite-green regression contract) + **`kata-orchestrate` frontier/async-escalation supersession** (rolling
DAG-frontier dispatch, async park/drain/hard-wait, structured escalation payload in its own contract
`protocol/escalation.md`). Deferred clean: Obsidian KG story (own spec under kata-understand, D54);
engram-mediated escalation (D56). Then Spec B (bake-off), `design` module. Parallel outstanding: D16
planning-varied A/B.

Brainstormed a major new capability: cost/effort/thoroughness **operating modes** (Essential/Standard/Advanced),
all one-shot, consistency-first. Full design in `docs/MODES-DESIGN.md`; vocabulary in `CONTEXT.md`; skill
token-weights in `.planning/SKILL-COST-RATINGS.md`; decisions D17–D23. Prior art researched (FrugalGPT cascade,
Cursor/AgentHub best-of-N, Claude `effort`, GitHub Spec Kit) — pieces exist; our synthesis (skill-set tiering +
escalation-with-reuse + Improvement-Kata version-ups) is the contribution.

## 2026-06-11 (evening session) — D59 + sprint-cadence spec opened

- **D59 — model routing Opus → Fable 5** for deep/judgment work (`claude-fable-5`); Sonnet stays the
  lightweight workhorse; 8 skill `model:` pins flipped to `fable`; test arms remain Sonnet (D14/D57).

- **NEW capability spec opened: sprint-cadence** (`.planning/specs/sprint-cadence/`) — user-requested
  bootstrap toggle between **one-shot** (current loop) and **sprint** execution (plan partitions the project
  into GSD-style sprints; run one sprint → gate → output → user course-corrects via grill → re-enter, same
  or new session). RESEARCH.md maps the plumbing (config `cadence` field, bootstrap question + re-entrancy,
  kata-plan roadmap layer, boundary handoff/report, delta-grill; orchestrate ideally sprint-blind; sprint
  N≥2 reuses the A4 version-up regression contract). GRILL-LEDGER.md holds **10 OPEN branches (SC-GB1–10)**
  with recommendations — **user answers them next session.** Framing rule: each sprint is a one-shot; the
  boundary is the scheduled re-plan event (spine #2 compatible).

## 2026-06-15 — sprint-cadence grill CONVERGED + engram registry created (uncommitted until 2026-06-18)

- **Sprint-cadence ledger fully resolved (SC-GB1–10 + engram cross-cut).** Knob = **`delivery: one-shot |
  incremental`** (unit = sprint); three-layer freeze (DESIGN north-star / ROADMAP boundary-amendable / sprint
  PLAN immutable) + Boundary Change-Control Protocol G1–G4; sequencing A+C (re-entrant `kata-bootstrap` routes,
  `kata-orchestrate` stays sprint-blind, NEW thin `kata-sprint`); three-tier state w/ derived `.kata/` cache
  rebuilt from git; scoped delta-grill course-correct (default always-stop); prime-frame sizing primitive
  (refines D8); sprint N≥2 = version-up vs most-recent-green baseline; bake-off trimmed; **D16-first LOCKED**.

- **`protocol/engram.md` CREATED** — engram plugin contract + seam registry (E1–E21, C1–C6, backend binding
  incl. external-backend clean-room). Adversarially reviewed (HOLD→hardened). Freeze-gate audit on sprint-cadence
  returned HOLD with must-fixes (roadmap-layer is NET-NEW in kata-plan; pin tunables; D8 supersession; etc.).

## 2026-06-18 — loop-cognition spec OPENED + CONVERGED (this session)

- **NEW umbrella spec `loop-cognition`** (`.planning/specs/loop-cognition/{RESEARCH,GRILL-LEDGER}.md`): three
  entangled loop enhancements — **RS** in-loop research subagent (escalation-routed, grounding-gated,
  fresh-context no-write `kata-research`), **AO** agent orientation (orchestrator-assembled stable→context→
  volatile tiers; vertical rollup + `kata-graph` lazy adjacency pointers; `protocol/orientation.md` +
  `kata-orient`), **ML** managed learning (candidate-skill distillation → 2-stage gate → human promotion
  `kata-promote`; second-brain LEARN feed as Karpathy-LLM-Wiki-pattern synthesis; progressive autonomy
  `engram.autonomy` maturity∧config AND-gate, grounding never bypassed).

- **Hermes Agent (Nous) baked off** — verdict: borrow mechanisms (autonomous distillation, protected
  head+tail compaction, tiered prompt assembly, `.usage.json` telemetry), keep OUR gates (default-FAIL +
  human promotion). Their no-gate skills + emergent-plan compaction = the failure modes our spine prevents.

- **LC-GB1–9 + RS-GB1–3 + AO-GB1–3 all RESOLVED + user-confirmed.** Sequencing = **Path 2**: D16 first, build
  the LEARN-only feed pipeline (β) in parallel (it's an engram *prerequisite*, low-drift, observe-and-emit,
  zero CONSULT). Artifact map recorded (NEW: kata-research/kata-orient/kata-promote + protocol/orientation +
  protocol/wiki-synthesis; EXTEND: evaluate/review/selfhandoff/orchestrate/handoff/improve/graph).

- **Freeze-gate audited HOLD→SHIP** (fresh-context Opus; MF1–MF3 + SF1–SF4 resolved; re-confirm SHIP).
  **DESIGN FROZEN** (`loop-cognition/DESIGN.md`); decisions promoted **D60–D69**; β ingested into ROADMAP
  (∥ D16), rest post-D16.

- **D16 RETIRED as an RCT + Priming-and-Grill resolved (D70/D71/D72, L11).** Two A/B attempts (easy + hardened
  `wordfreq`) proved the autonomous deterministic-gate A/B can't isolate the grill (4/4→10/10 gate passes; grill's
  human-engine is off without a human). **Grill is now an OPTIONAL human certainty layer over the priming prompt,
  with an autonomous-reliability floor** (default-FAIL + RS + assumption-log); grill ledgers are a PRIMARY
  cognitive-fingerprint feed. **Autonomous reliability is demonstrated; v0.1 no longer gated on an RCT → the
  D16-first lock is dissolved → the full build is UNBLOCKED.**

- **D71 Priming-and-Grill wiring ✅ DONE 2026-06-18** (spec `priming-and-grill`, DESIGN FROZEN; D73 + M1–M3):
  grill **skip** rung (`tiers["kata-grill"]="skip"`) + bootstrap grill-depth dial (Phase 1.5) + readiness Scope-3
  prompt-richness recommendation + orchestrate skip-floor branch + **`kata-defer` built** (DEFERRED.md parking +
  ASSUMPTIONS.md grill-skip log; **25→26 skills**) + grill↔RS spectrum doc'd. Validator 26/0, pytest 15.
  **Caveat:** RS slot doc'd/wired-for, lit in the loop-cognition phase. **Pending: fresh-context `kata-review`.**

- **β LEARN feed ✅ DONE 2026-06-18** (D74 + BP1/BP2): `kata-improve` emit-only sub-mode (E6) → Karpathy-LLM-Wiki
  synthesis pages per the schema in `protocol/engram.md` (`produced-by: loop`); **zero CONSULT** (BC2),
  **redaction-gated** (C3), no-op without `engram.learnFeed.dir` (BP1/BC1); `engram.md` now validator-enforced
  (BP2). Validator 26/0, pytest 18. **Pending: fresh-context `kata-review`.**

- **RS ✅ DONE 2026-06-19** (D75; RS-GB1/2/3): `kata-research` escalation-routed fresh-context **no-write**
  researcher (`research-needed` kind); **L2 grounding gate** = injected-knowledge mode of `kata-evaluate` +
  `kata-review` RUBRIC (never bypassed, D33); orchestrator folds GROUND findings via deliberate superseding
  re-plan, else REJECT/escalate-to-human. `kata/module/research`; **27 skills**. Validator 27/0, pytest 21.
  **Pending: fresh-context `kata-review`.**

- **AO ✅ DONE 2026-06-19** (D76; AO-GB1/2/3 + user extensions): `kata-orient` (spine, read-only) three-tier
  launch orientation + `protocol/orientation.md`; **task-type-aware**, contextually-derived **pointers+callouts**
  from standard markdown, **smart questioning routed** (answer-inline / research-needed→RS / human→grill),
  `kata-handoff` Orientation tie-in (aligned both sides). **28 skills.** Validator 28/0, pytest 24.

- **ML ✅ DONE 2026-06-19** (D77; L5/L6): `kata-promote` stage-2 human promotion gate (AskUserQuestion);
  agent-distilled candidates (STANDARDS §1.3, `<agentSkills.dir>/candidates/`, not universal) → grounding gate →
  human gate; `engram.autonomy` AND-gate default **always-human**; candidate lifecycle in `state.md`. **29 skills.**
  Validator 29/0, pytest 27. **⇒ loop-cognition COMPLETE (RS + AO + ML).**

- **NEXT (see HANDOFF §4 THE PLAN):** (1)–(4) ✅ D71/β/RS/AO; (5) ✅ RS+AO validation; (6) ✅ ML →
  **loop-cognition done.** **(7) ✅ sprint-cadence DESIGN FROZEN 2026-06-19** (D78–D85; freeze-gate HOLD→SHIP) →
  **BUILD it next** (NEW: `kata-plan` roadmap layer + `kata-sprint` + `kata-report` v1; needs PLAN + approval);
  **(8) dogfood version-up on KataHarness itself** (the endgame: build fully → full tests → self-improve). CONSULT/full-autonomy
  stay gated on a mature engram.

## Next action — RS → AO → ML (D16 lock dissolved by D70; D71 + β DONE 2026-06-18)

> ⚠️ The numbered list below predates D70 and is **superseded** — it described the D16-first sequencing that no
> longer applies. Authoritative next step: **RS (research subagent), then AO, then ML.** Kept for provenance.

0. **Answer the sprint-cadence grill ledger** (`.planning/specs/sprint-cadence/GRILL-LEDGER.md`, SC-GB1–10)
   — note SC-GB10 proposes: freeze the sprint DESIGN now, build after D16.

1. **D16 planning-varied A/B (the v0.1 validation gate; ROADMAP-sequenced FIRST):** prove the grill
   differentiates — Arm A plans via `kata-grill`→`kata-design-doc`→`kata-plan` vs a GSD baseline. **Target
   reshaped (D57): small one-shottable greenfield projects in a dedicated test directory** (repeated paired
   measurements, not one big task). Needs its own spec grill (`.planning/specs/`) — TEST-PLAN v1 is superseded.

2. **Obsidian-KG / kata-understand spec** — emit+ingest over the `kata.graph.json` contract (D54/D55).
   **PokeVault gate SATISFIED (D58)** — vault is git-versioned/durable, so no freshness pressure; sequenced
   AFTER D16 per ROADMAP + the 2026-06-10 adversarial review of the "grill-KG-first" option (REJECTED:
   premise decay — durable vault; post-v0.1 inversion; rework exposure from an unvalidated grill).

3. **Spec B — bake-off** (anytime; composes with version-up, D37).
- **Backlog:** A3-review carry-overs (`kata-readiness` harness-vs-target wording for the KG spec; `tools/`
  example-`kata.config` check) · `kata-defer`/`kata-understand`/`kata-tasklist`/`kata-engram` · adapters ·
  **set a git remote before public release** (still local-only).

## Model per stage

Build KataHarness → **Claude Fable 5** (`claude-fable-5`, D59 — supersedes the Opus routing). D16 test
arms → **Sonnet** (constant across arms — D14 principle, survives D57/D59). I pin subagent models on
spawn; operator sets main-session model via `/model`.

## Open decisions for the user

- Confirm D16-first sequencing (adversarial review recommends it; Option D "grill-KG-first" was reviewed
  and REJECTED 2026-06-10). Suite/plugin packaging shape. Git remote before public release.

## Session Continuity

Last session: 2026-06-30T15:02:58.583Z
RS-GB1–3, AO-GB1–3); STATE/HANDOFF refreshed; checkpoint commit of 2026-06-15 (sprint-cadence converged +
engram.md) + 2026-06-18 (loop-cognition spec) work. Resume file: `.planning/HANDOFF.md` (read it first).
**Immediate next:** the session resolved the **Priming-and-Grill architecture (D70/D71/D72, L11)** and
**retired D16 as an RCT** — autonomous reliability is demonstrated, so the full build is UNBLOCKED. Read
`.planning/HANDOFF.md` (rewritten for this hand-off) — §4 THE PLAN: wire D71 → build β → RS/AO/ML → freeze
sprint-cadence → dogfood version-up. loop-cognition DESIGN is FROZEN (D60–D69). The user will compact + orient
a fresh session from the handoff.
