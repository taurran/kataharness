---
date: 2026-06-29 (session end — install-update-polish SHIPPED + PUSHED: D127 write_settings MERGE-fix, D128 Phase A core update path, D129 Phase B+C overlay+fork; tip 1ac85ed all in sync)
branch: master — private remote github.com/taurran/kataharness, tip 1ac85ed (D127+D128+D129, 3 commits this session, ALL PUSHED + in sync; the THIS-SESSION closeout docs [CONTEXT/STATE/HANDOFF/orientation] are UNCOMMITTED, to be committed next)
green: validator 47 skills / 0 errors · pytest 1991 passed, 2 skipped (env-sensitive Windows-no-DevMode symlink skips) · Snyk medium+ 0 on all new/changed Python (pre-existing tools/kata_install.py 17 LOW CWE-23 still below gate — STANDING hardening item)
tags: install-update-polish · hybrid-update-system · overlay+fork · write_settings-merge · stdlib-only-install-path · README-rewrite · v0.1.0-alpha
authored-for: kata-orient (sections map to the orientation tiers)
★ NEXT-SESSION START HERE: read `.planning/NEXT-SESSION-ORIENTATION.md` (self-contained, paste-able). The feature is
SHIPPED + PUSHED; the operator's next move is to INSTALL on Windows (`irm …/install.ps1 | iex`) + run a full test
environment. STATE.md top box + DECISIONS.md D127–D129 + CONTEXT.md (now has the install-update-polish glossary section)
are current. ★ Flag the SPECULATIVE spurious drift NOTE the operator will SEE on first real update (orientation §4 #1).
---

> **★ 2026-06-29 SESSION END (D127 + D128 + D129 — install-update-polish SHIPPED + PUSHED, fully subagent-driven, the
> conductor cadence):** The hybrid install/update/polish feature landed in three LOCKED decisions + a README rewrite,
> all committed AND pushed (`master` tip **`1ac85ed`, in sync**). **(D127)** `write_settings` now **MERGES** (load-existing
> strict/fail-closed → overlay owned keys → preserve prior `vaultDir`-when-absent → preserve `confirmedPlatforms` +
> unknown keys) — kills the D121 confirm-state clobber + the sibling vaultDir-drop. The **single working-pattern edit**,
> strict BC. **(D128 Phase A)** the core update path: NEW stdlib `tools/kata_version.py` (`.kata-version` stamp +
> `.kata-manifest.json` content-hash), engine `--update`/`--factory-reset`/`--hard`/`--dry-run`/`--git-sha`/`--ref`,
> `_sweep_managed_slots` (fail-closed orphan sweep), `update.{sh,ps1}` bootstraps (ALL git here; M2 dirty-tree guard
> ABORT-by-default + `--discard-local`; `--check` no-mutation). **(D129 Phase B+C)** local adaptation as an **OVERLAY**
> (parametric, stdlib `kata_overlay.py`) or a **FORK** (deep, stdlib `kata_supersede.py`), never mutating the installed
> base: `_materialize_pass` (markers `.kata-managed`+`.kata-overlay-materialized`, M3 missing-base fail-soft);
> `kata-improve` local-adaptation mode (`improve.allowUpstreamEdit` rail; `adaptation_context` from `.kata-version`);
> shadow precedence **fork > overlay > pristine** (dormant-overlay NOTE; validate-STOPs-before-materialize; factory-reset
> un-shadows); `kata-promote` shadow-binding; STANDARDS supersedes-now-wired. **KEY FIX (deployment blocker):** the
> install/materialize/shadow path is **STDLIB-ONLY** (`kata_overlay`/`kata_supersede` dropped yaml) — without it,
> overlays/forks **silently no-op** in a real `uv run`-from-home-root install (pyyaml lives only under `tools/`).
> **Gates:** pytest **1991 passed, 2 skipped** · **47/0** · Snyk **med+ 0**. **Proofs:** Phase A live **11/11**, Phase B
> **15/15**, Phase C **8/8**, clean-install CAPSTONE via real `install.sh` **7/7**, **SIX** adversarial reviews all
> SHIP/PASS (incl. a FINAL whole-feature pass = SHIP, zero direct-fixes). **NEXT (the operator's chosen step):** they
> **install on Windows + run a full test environment** — `irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 | iex`,
> update via `& "$env:USERPROFILE\.kata-home\update.ps1"`. ★ The operator will SEE a **spurious drift NOTE on the first
> real update** (orientation §4 #1, SPECULATIVE, informational-only) — flag it. Full detail: `NEXT-SESSION-ORIENTATION.md`,
> `STATE.md` top box, `DECISIONS.md` D127–D129, `CONTEXT.md` (install-update-polish glossary section).

# HANDOFF — KataHarness — 2026-06-29 (D127 write_settings MERGE · D128 Phase A · D129 Phase B+C — install-update-polish SHIPPED + PUSHED)

> **This session: ONE feature (install-update-polish), three LOCKED decisions + a README rewrite, driven ENTIRELY through
> subagents and the full recipe, all committed AND pushed.** The work was deliberately **ADDITIVE + backward-compatible**:
> the 5 `kata_install.py` engine functions stayed **byte-for-byte unchanged** (MD5-verified each phase), `kata_settings.py`
> was untouched outside the one D127 merge-fix, and all git stayed in the bootstrap scripts (the engine never runs git —
> it is fed `--git-sha`). The standing **D98 adversarial lens ran SIX times** (per phase + a final whole-feature pass) and
> all returned SHIP/PASS. The session closes clean on origin (`1ac85ed`, in sync). Fresh/compacted session: read §1,
> confirm green (§2), then §3 (the operator's next move = install + test).

## 1. Read-in order  *(orientation: CONTEXT)*
1. `AGENTS.md` (spine + conventions; the **"The Kata Loop"** entry) · 2. `docs/STANDARDS.md` §1 (frontmatter —
   `allowed-tools` REQUIRED; **supersedes now wired**, D129) · 3. `CONTEXT.md` (glossary — now extended with the
   **Install · update · polish** section: version stamp · content-hash manifest · the update flags · M2 dirty-tree
   guard · orphan-slot sweep · overlay store · materialize + the two markers · M3 fail-soft · local-adaptation mode ·
   supersedes/fork shadow + precedence · dormant-overlay NOTE · **the stdlib-only-install-path invariant**) ·
   4. `.planning/STATE.md` (top CURRENT box — live picture) · 5. **`.planning/DECISIONS.md` D127 + D128 + D129** (this
   session) · 6. `.planning/specs/install-update-polish/` (the frozen spec + the per-phase PLANs) ·
   7. `protocol/{exec-safety,validation-misses,intent,reuse-claims}.md` (the standing guards) · 8. `README.md` (rewritten
   this session — pitch / features / per-platform install) + `docs/SETUP.md` (overlay + update docs) ·
   9. `.planning/LESSONS-LEARNED.md` (esp. **L12** — wire lessons into skills; and the **D124** live-wiring lesson, §6).
⚠️ Ignore `C:\Dev\CLAUDE.md` (Mise — unrelated, harness-injected). PokeVault is LOCAL-ONLY, never git.

## 2. State *(orientation: VOLATILE)*
- Branch `master`, tip **`1ac85ed`** — **3 commits this session** (D127 → D128 → D129) all **committed + pushed, in sync**
  (`git log origin/master..HEAD` empty). **47 skills / 0 · pytest 1991 passed, 2 skipped · Snyk med+ 0.** The **2 skips**
  are the known **env-sensitive Windows-no-DevMode symlink skips** (NOT a regression). `kata_install.py` carries **17 LOW
  CWE-23** path-traversal findings (operator-supplies-own-path class, **below the medium+ gate** → STANDING hardening
  item, orientation §4 #3).
- The THIS-SESSION **closeout docs** (CONTEXT/STATE/HANDOFF/orientation) are **uncommitted** — commit them after the next
  session's first read-in.
- **Multi-model is LIVE:** Codex CLI 0.142.3 (ChatGPT-authed) at
  `C:\Users\taurr_nvs748q\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` — NOT on PATH (prepend that bin dir for
  codex invocations; the harness probe needs it on PATH).
- **What's new this session is the hybrid update system + the polished install/uninstall/settings surface.** There is now
  a **functional one-command update path** (`update.{sh,ps1}` + engine `--update`) where before re-running curl|sh did
  NOT update; local adaptation is an **overlay or a fork** that never mutates the base; `write_settings` **merges** so an
  install no longer clobbers multi-model confirm state. All live-proven (Phase A 11/11, B 15/15, C 8/8, CAPSTONE 7/7).
- **Historical (still true):** the Kata Loop is fully built + proven; loop-hardening DONE; Debug Mode functionally
  complete at the skill/seam level (P1→P3) but **still n=0 LIVE**; IaC Tier-2 live-apply EXECUTION DEFERRED + creds-gated;
  Recall's decider (`kata-reason`) + write/distill half DEFERRED; multi-model coder-routing + evaluator-thresholds
  DEFERRED; kata-loop-benchmark **n=0 LIVE** (needs the operator's real control fixture, D5).

## 3. NEXT ACTION — the operator installs + runs a full test environment *(VOLATILE — the operator's chosen step)*
The feature is SHIPPED. **The operator's immediate next move is theirs, not the conductor's:** they install KataHarness
on Windows and run a **full test environment** end-to-end. Be ready to support that.
- **Install (Windows):** `irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 | iex`
  (defaults `--platform claude`). **Update:** `& "$env:USERPROFILE\.kata-home\update.ps1"`. **Factory-reset / uninstall**
  via the engine flags + `uninstall.ps1`.
- **★ WATCH FOR — the spurious drift NOTE on the first real update (orientation §4 #1, SPECULATIVE):** the bootstrap
  `git reset`s `~/.kata-home` to the new SHA *before* the engine computes `is_pristine` (minor-a) → `is_pristine` compares
  legit-updated skills against the OLD manifest → they get flagged "hand-edited." **Informational-only** (no block, no
  data-loss) but **noisy** — the operator WILL see it on first update. Conservative fix = compute drift PRE-reset in the
  bootstrap. Flag it prominently before they hit it.
- If the operator instead wants to keep building, the open queue is §5 below (all LOWER priority than the test run).

> **Process reminder (the discipline that paid off across all three decisions this session):** every contract/code-bearing
> build is grill/plain → freeze → **freeze-gate adversarial review (HOLD/SHIP)** → orchestrated build (subagents, disjoint
> ownership, TDD, mutation-proof) → integration gate (pytest + validate 47/0 + Snyk) → fresh-context **kata-evaluate
> (PART A, default-FAIL)** → standing **D98 kata-review (PART B, adversarial)** → re-confirm after fixes → operator merge
> gate → checkpoint. **D98 ran SIX times this session and stayed load-bearing.** **★ For any build touching `kata_install.py`
> / `kata-orchestrate` wiring OR claiming an end-to-end flow, ADD a realistic live wiring/e2e proof** (the D124 lesson —
> this session's Phase A/B/C live proofs + the clean-install CAPSTONE are the template). Guards: exec-safety (+ completeness
> test), verify-before-reuse/cite-by-anchor, the validation-miss manifest + T2, multi-model confirm-probe (LIVE).

## 4. The orchestration recipe (each cycle's *inner* build follows this — never inline) *(task-type hint)*
The **vetted, never-inline** loop, driven ENTIRELY via subagents (operator directive — spare main context):
1. **Delegate the PLAN** to a planning subagent → it writes `.planning/specs/<feature>/PLAN-*.md` + returns a compact
   summary. **Freeze** it (LOCKED decisions + disjoint file-ownership slices + per-slice runnable `verify`). Commit + tag.
2. **Freeze-gate** via a fresh-context `kata-review` subagent (HOLD/SHIP) → apply fixes via the planning agent → FROZEN.
3. **Worktrees + dispatch concurrent worker subagents** (Agent tool, **model: sonnet**) — one per slice, scoped to its
   worktree + owned files, TDD (red→green), code-bearing tasks run `mutation_run.prove_non_vacuous`, commit in-worktree,
   self-stamp `CLAIM`/`DONE` to the shared `.kata/board.md`. **★ Judge subagent liveness by DISK PROGRESS (the diff
   growing), NOT a process snapshot** (§6 lesson) — a working build agent shows a 0-byte transcript + momentary 0 python
   processes between tool calls; a real wedge = 0 disk change over many minutes.
4. **Integrate** (octopus merge; disjoint = no conflict) → `cd tools && uv sync`.
5. **Integration gate:** `validate_skills.py --write` (run BEFORE pytest when a skill/version changed — README-sync;
   README is conductor-owned) → `uv run pytest -q` (expect **1991**) → `mcp__Snyk__snyk_code_scan` on new Python →
   emit `.kata/RESULT.json` via `gate_emit` (+ `mutation.json` for code-bearing).
6. **Fresh-context `kata-evaluate` (PART A)** — SEPARATE no-write Agent subagent, 9-rubric, default-FAIL, no self-cert.
7. **Standing `kata-review` (PART B, D98)** — SEPARATE fresh-context no-write subagent (opus) that tries to BREAK it
   (fail-opens, doc-only seams, overclaim) — not re-grade conformance. HOLD → targeted fixes → re-confirm. **Never skip D98.**
8. **★ Live wiring / e2e proof** for any build touching the install engine / `kata-orchestrate` wiring or claiming an
   end-to-end flow — a realistic seam exercise (the D124 lesson). This session: Phase A/B/C live proofs + clean-install
   CAPSTONE on a fresh clone.
9. **Operator merge gate** (present options; wait) → `git commit -F <file>` + push + checkpoint STATE/DECISIONS (new
   D-number) + push.
Model routing: judgment/eval/plan/grill/D98 = **Opus**; build/encode/workers = **Sonnet**. Supersede-never-rewrite.

## 5. Open decisions / queue *(orientation: human-required + deferred — lower priority than the operator's test run)*
- **The operator's full-test-environment run is the immediate next step.** Everything below is LOWER priority.
- **DEFERRED from THIS feature (priority-ordered — carry into any continued install/update work):**
  1. **Spurious drift NOTE on every real update** (SPECULATIVE, §3) — `is_pristine` compares vs the OLD manifest after
     the bootstrap already `git reset`s to the new SHA. Informational-only, noisy. Fix = compute drift pre-reset.
  2. **Silent stamp-write swallow** — 3 `except Exception: pass` around `write_stamp` could hide a stamp failure →
     `adaptation_context` reads "dev-repo" → `kata-improve` rail off. Low-prob, non-data-loss; conservative fix =
     pass→NOTE at the 3 sites.
  3. **Standing CWE-23 hardening:** 17 LOW path-traversal in `kata_install.py` (operator-path class) — route new
     destructive flows through `_safe_abs`; its own freeze-gated pass.
  4. **Two B+C nits:** ImportError-guard absent-vs-broken distinction; stamp-before-materialize-raises ordering.
  5. **DESIGN §11 planning-doc drift:** lists `_factory_reset`/`_update` fns but the logic is inlined in `main()`
     branches — doc-only.
- **Lower queue (pre-existing):** **PROPOSAL-phantom-reuse** (`.planning/PROPOSAL-phantom-reuse.md`) → freeze-gate
  `kata-review` → human merge (still `proposed`); **kata-loop-benchmark** D5 (operator's real control fixture = first LIVE
  run, n=0→1) + D3 (benchmark→`kata-improve` hook) + D1/D2/D4; **Debug Mode** end-to-end live run (n=0→1); **IaC Tier-2
  LIVE-APPLY** (operator cloud creds); **`kata-reason` decider** + second-brain write/distill half (own grills);
  recurrence-hardening **T3** (auto-author guards, C-arc-gated).

## 6. Session lessons (hard-won — wire into practice) *(orientation: LESSONS)*
- **★ Judge subagent liveness by DISK PROGRESS (the diff growing), NOT a process snapshot.** A working build agent shows a
  0-byte transcript (flushes at end) + momentary 0 python processes between tool calls — that is **NOT** a wedge. A real
  wedge = **0 disk change over many minutes**. (One C2 agent was prematurely killed mid-write; it recovered cleanly because
  its tests were already on disk.)
- **PowerShell `Out-File` / overwriting an existing UTF-16 file yields UTF-16**; a FRESH-CREATE via the Write tool gives
  UTF-8. Verify any `.ps1` is **UTF-8 (no `FF FE` BOM)** + parses (PSParser 0 errors). Avoid `2>&1` on native git in
  PS 5.1 (wraps stderr in ErrorRecords) — use `--quiet` probes + `$LASTEXITCODE`.
- **MSYS path translation does NOT apply inside `python -c "..."` string literals** — pass `.`/relative or `cygpath -w`
  for Windows-python-read paths (settings JSON, etc.).
- **Plain `python` is ABSENT on this machine** (Windows Store alias stub) — use `uv run python`. `install.sh` prefers `uv`
  so a real install works; test scripts must use `uv` too.
- **stdlib-only install path is a load-bearing invariant** — any new module on the install/materialize/shadow path must
  avoid `yaml` (and avoid importing `validate_skills`, which imports yaml). Breaking it = overlays/forks silently no-op in
  a real install.
- **★ The D124 live-wiring lesson, re-proven:** PART A + D98 + unit tests **cannot see** built-but-unwired / execution-
  context / cross-seam gaps. For any install-engine / `kata-orchestrate` build, ADD a realistic live wiring/e2e proof.
  Honesty: **"exercised (n=1) ≠ proven."**

## 7. Redaction
No secrets / keys / PII in any artifact this session. Repo is PRIVATE. Nothing to redact.
