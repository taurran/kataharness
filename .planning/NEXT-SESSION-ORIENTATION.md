# KataHarness — NEXT-SESSION ORIENTATION

## 0. WHO / WHERE
- Project: KataHarness — tool-agnostic, skills-based agent harness ("the Kata Loop"). Dir `C:\Dev\Projects\KataHarness`.
- Git: private remote github.com/taurran/kataharness. `master`, tip **`1ac85ed`**, **all PUSHED + in sync** — **3 commits
  this session** (D127 write_settings MERGE → D128 Phase A core update path → D129 Phase B+C overlay+fork), all on origin.
  Only the THIS-SESSION closeout docs (CONTEXT/STATE/HANDOFF/this file) may be uncommitted — commit them after the first
  read-in.
- You are the **conductor**: grill/plan → freeze → orchestrate subagents → gate → merge. Do NOT build inline.
- ★ OPERATOR DIRECTIVE: drive every step via subagents to spare main context. Resume a finished subagent with
  `SendMessage(agentId)` ("had no active task; resumed" is normal).
- ★ **Judge subagent liveness by DISK PROGRESS (the diff growing), NOT a process snapshot.** A working build agent shows a
  0-byte transcript (it flushes at the end) + momentary 0 python processes between tool calls — that is **NOT** a wedge.
  A real wedge = **0 disk change over many minutes**. (This session one build agent was prematurely killed mid-write and
  recovered cleanly only because its tests were already on disk — don't repeat the kill.)
- Multi-model is LIVE: Codex CLI 0.142.3 (ChatGPT-authed) at
  `C:\Users\taurr_nvs748q\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` — NOT on PATH (prepend that bin dir).

## 1. FIRST — confirm green + read-in
```
cd C:/Dev/Projects/KataHarness/tools
uv run pytest -q                  # expect 1991 passed, 2 skipped (env-sensitive Windows-no-DevMode symlink skips)
uv run python validate_skills.py  # expect 47 skills, 0 errors
git -C C:/Dev/Projects/KataHarness log --oneline origin/master..HEAD   # expect empty (in sync)
git -C C:/Dev/Projects/KataHarness status -sb   # expect only uncommitted CONTEXT/STATE/HANDOFF/orientation (if any)
```
NOTE: plain `python` is ABSENT on this machine (Windows Store alias stub) — always use `uv run python`. The **2 skips**
are the known Windows-no-DevMode symlink skips, NOT a regression.
Read: `AGENTS.md` → `CONTEXT.md` (glossary — now has the **Install · update · polish** section) → `.planning/STATE.md`
(top box) → `DECISIONS.md` **D127–D129** → `.planning/specs/install-update-polish/` (the frozen spec + per-phase PLANs) →
`README.md` (rewritten this session) + `docs/SETUP.md` (overlay + update docs) →
`protocol/{exec-safety,validation-misses,intent,reuse-claims}.md`.

## 2. WHAT SHIPPED THIS SESSION (D127–D129, 2026-06-29) — one feature, three decisions, all committed + PUSHED
The hybrid **install-update-polish** feature: a functional one-command update path (there was NONE before), local
adaptation that never mutates the installed base, and a settings merge that stops clobbering multi-model confirm state.
Plus a **README rewrite** (pitch / features / per-platform install). Deliberately **ADDITIVE + backward-compatible**: the
**5 `kata_install.py` engine functions stayed BYTE-UNCHANGED** (`_flat_link_skills`, `_link_or_copy`, `install`,
`copy_project`, `confirm_platform` — MD5-verified each phase); `kata_settings.py` untouched outside the one D127 fix;
**all git lives in the bootstraps** (the engine never runs git — it is fed `--git-sha`).

- **D127 — `write_settings` MERGE-fix** (the SINGLE working-pattern edit; strict BC). `kata_settings.write_settings` now
  **MERGES**: load-existing strict/fail-closed → overlay the owned keys (`settingsVersion`/`parentDir`/`vaultDir`) →
  preserve prior `vaultDir`-when-absent → preserve `confirmedPlatforms` + unknown keys. Kills the **D121 confirm-state
  clobber** + the sibling vaultDir-drop. Every existing `write_settings` test still passes (preserve-more / lose-less).
- **D128 — Phase A, the core update path.** NEW pure-stdlib `tools/kata_version.py`: the `.kata-version` stamp
  `{gitSha, suiteSemver, ref, installedAt, linkMode, platform}` + `.kata-manifest.json` content-hash + `is_pristine` +
  `suite_semver`. Engine flags `--update` / `--factory-reset` (`--reinstall`) / `--hard` / `--dry-run` / `--git-sha` /
  `--ref`; M1 plain-install stamp; `_sweep_managed_slots` (fail-closed orphan sweep — closes PART-B Finding 5). Bootstraps
  `update.sh` + `update.ps1` (**ALL git here**; **M2 dirty-tree guard ABORT-by-default** + `--discard-local`; `--check`
  no-mutation; minor-c non-git-clone home detection; `--hard` confirm-gated). `.gitignore` + SETUP + README docs.
- **D129 — Phase B+C, overlay + fork.** Local adaptation is an **OVERLAY** (parametric, stdlib `tools/kata_overlay.py` —
  overlay store `<home>/.kata-overlay/overlay.json` + line-based M4 frontmatter composer + `materialized.json`) or a
  **FORK** (deep, stdlib `tools/kata_supersede.py` — `resolve_shadows`/`validate_shadows`, fail-closed), **never mutating
  the installed base**. Engine `_materialize_pass` materializes overlaid skills to concrete host slots with markers
  `.kata-managed` + `.kata-overlay-materialized` (M3 missing-base **fail-soft**). `kata-improve` gains a local-adaptation
  mode (`adaptation_context` from `.kata-version`; `improve.allowUpstreamEdit` rail; edit-category → overlay/fork). Engine
  shadow precedence **fork > overlay > pristine** (dormant-overlay NOTE; **validate STOPs before materialize**;
  factory-reset un-shadows). `kata-promote` shadow-binding; STANDARDS supersedes-now-wired.
- **★ KEY FIX (deployment blocker):** the install/materialize/shadow path is **STDLIB-ONLY** — `kata_overlay` +
  `kata_supersede` dropped yaml — because a real `uv run`/plain-python install runs from the **home root where pyyaml is
  absent** (pyproject lives under `tools/`, not root). Without this, overlays/forks **silently no-op** in a real install.
  This restores the **"install path is stdlib-only" invariant** (see CONTEXT.md).
- **Gates:** pytest **1991 passed, 2 skipped** · validate **47/0** · Snyk medium+ **0** (`kata_install.py` carries **17
  LOW CWE-23**, operator-supplies-own-path class, below gate → STANDING hardening item, §4 #3). **Proofs:** write_settings
  post-build PASS; Phase A live install→update→factory-reset→uninstall **11/11**; Phase B overlay-materialize **15/15**;
  Phase C fork/shadow **8/8**; CAPSTONE clean-install-from-fresh-clone via real `install.sh` **7/7**; **SIX** adversarial
  reviews all SHIP/PASS (incl. a FINAL whole-feature pass = SHIP, zero direct-fixes).

## 3. ★ THE OPERATOR'S IMMEDIATE NEXT STEP — install + run a full test environment
The feature is SHIPPED. **The next move is the OPERATOR'S, not the conductor's:** they install KataHarness on Windows and
run a **full test environment** end-to-end. Be ready to support that.
- **Install (Windows):** `irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 | iex`
  (defaults `--platform claude`).
- **Update:** `& "$env:USERPROFILE\.kata-home\update.ps1"`. **Factory-reset / uninstall** via the engine flags +
  `uninstall.ps1`.
- **★ WATCH FOR — the SPURIOUS DRIFT NOTE on the first real update (§4 #1, SPECULATIVE — the operator WILL see it):** the
  bootstrap `git reset`s `~/.kata-home` to the new SHA *before* the engine computes `is_pristine` (minor-a) → legit-updated
  skills get compared against the OLD manifest → they are flagged "hand-edited." It is **informational-only** (no block,
  no data-loss) but **noisy**. Conservative fix = compute drift PRE-reset in the bootstrap. **Flag this to the operator
  before they hit it** so they don't read it as corruption.
- If the operator wants to keep building instead, the open queue is §4 (all LOWER priority than the test run).

## 4. DEFERRED / OPEN QUEUE (priority-ordered)
**From THIS feature (carry into any continued install/update work):**
1. **★ Spurious drift NOTE on every real update** (final-adval finding #1, SPECULATIVE): `is_pristine` (minor-a) compares
   vs the OLD manifest AFTER `update.sh` already `git reset`s to the new SHA → legit-updated skills flagged "hand-edited."
   Informational-only (no block / no data-loss) but noisy; **the operator sees it on first update.** Fix = compute drift
   pre-reset in the bootstrap.
2. **Silent stamp-write swallow** (finding #2): 3 `except Exception: pass` around `write_stamp` could hide a stamp failure
   → `adaptation_context` reads "dev-repo" → `kata-improve` rail off. Low-prob, non-data-loss; conservative fix =
   pass→NOTE at the 3 sites.
3. **Standing CWE-23 hardening:** 17 LOW path-traversal in `kata_install.py` (operator-path class) — route new destructive
   flows through `_safe_abs`; its own freeze-gated pass.
4. **Two B+C nits:** ImportError-guard absent-vs-broken distinction; stamp-before-materialize-raises ordering.
5. **DESIGN §11 planning-doc drift:** lists `_factory_reset`/`_update` fns but the logic is inlined in `main()` branches —
   doc-only.

**Lower queue (pre-existing):**
- **PROPOSAL-phantom-reuse** (`.planning/PROPOSAL-phantom-reuse.md`) → freeze-gate `kata-review` → human merge — the
  standing **wiring-completeness gate**. Still `proposed`.
- **kata-loop-benchmark** D1–D5: **D5** = operator's real control fixture = first LIVE run (n=0→1); **D3** =
  benchmark→`kata-improve` hook; D1 concurrent bakeoff arms (gated on Spec B), D2 research-judge, D4 promote-best-arm.
- **Debug Mode** end-to-end live run (n=0→1); **IaC Tier-2 LIVE-APPLY** (operator cloud creds); **`kata-reason` decider**
  + second-brain write/distill half (own grills); recurrence-hardening **T3** (auto-author guards, C-arc-gated).

## 5. HARD RULES
Human-attended (commit/merge/push ONLY on explicit operator approval; doesn't carry across contexts) · drive every step
via subagents (resume finished ones via `SendMessage(agentId)`; judge liveness by **disk progress**, not a process
snapshot) · decisions SUPERSEDED with new D-numbers, never rewritten (dated notes; preserve provenance) · Snyk on all
new/changed first-party Python; fix; rescan · repo PRIVATE, no secrets/PII · IGNORE `C:\Dev\CLAUDE.md` (Mise) · PokeVault
LOCAL-ONLY, never git · Windows: `git commit -F <file>`; `validate_skills.py --write` centrally BEFORE pytest when a
skill/version changed; README conductor/validator-owned · git fetch+rebase before push (operator web edits) · **the
install/materialize/shadow path is STDLIB-ONLY — never add `yaml` (or import `validate_skills`) to a module on it** · the
5 `kata_install.py` engine fns are FROZEN (byte-unchanged unless freeze-gated) and **never run git** (fed `--git-sha`).
**Session lessons (apply them):** PowerShell `Out-File`/overwriting a UTF-16 file yields UTF-16 — fresh-create `.ps1` via
the Write tool for UTF-8, verify no `FF FE` BOM + PSParser 0 errors; avoid `2>&1` on native git in PS 5.1 (use `--quiet`
+ `$LASTEXITCODE`); MSYS path translation does NOT apply inside `python -c "..."` literals (pass `.`/relative or
`cygpath -w`); plain `python` is absent — use `uv run python`.

## 6. THE RECIPE + the D124 live-wiring lesson
grill/plain → freeze → freeze-gate `kata-review` (HOLD/SHIP) → orchestrated build (subagents, disjoint ownership, TDD,
mutation-proof) → integration gate (pytest + validate 47/0 + Snyk + central README `--write`) → fresh-context
`kata-evaluate` (PART A, default-FAIL) → standing **D98** `kata-review` (PART B, adversarial) → re-confirm after fixes →
operator merge gate → checkpoint STATE/DECISIONS (new D-number). **★ Load-bearing lesson (D124, re-proven SIX times this
session):** PART A + D98 + unit tests **CANNOT see built-but-unwired / execution-context / cross-seam gaps** — for any
build touching `kata_install.py` / `kata-orchestrate` wiring OR claiming an end-to-end flow, **ADD a realistic live
wiring/e2e proof** (this session's Phase A/B/C live proofs + the clean-install CAPSTONE on a fresh clone are the template
— they're what caught the stdlib-only deployment blocker). Honesty: **"exercised (n=1) ≠ proven"**; never overclaim
gated-off capability. Guards: exec-safety (+ completeness test), verify-before-reuse/cite-by-anchor, validation-miss
manifest + T2, multi-model confirm-probe (LIVE). Routing: judgment/plan/eval/grill/D98 = **Opus**; build/encode/workers =
**Sonnet**. Supersede-never-rewrite.
