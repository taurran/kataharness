# KataHarness — NEXT-SESSION ORIENTATION

## 0. WHO / WHERE
- Project: KataHarness — tool-agnostic, skills-based agent harness ("the Kata Loop"). Dir `C:\Dev\Projects\KataHarness`.
- Git: private remote github.com/taurran/kataharness. `master`, tip **`8d84125`**, **all PUSHED + in sync** (D125
  `a749f5d` kata-validate → D126 `8d84125` install/onboarding polish are on origin). Only the THIS-SESSION doc updates
  (STATE/HANDOFF/this file/REQUIREMENT) may be uncommitted — commit them after the first read-in (or fold into the
  install-update-polish freeze commit).
- You are the **conductor**: grill/plan → freeze → orchestrate subagents → gate → merge. Do NOT build inline.
- ★ OPERATOR DIRECTIVE: drive every step via subagents to spare main context. Resume a finished subagent with
  `SendMessage(agentId)` ("had no active task; resumed" is normal).
- Multi-model is LIVE: Codex CLI 0.142.3 (ChatGPT-authed) at
  `C:\Users\taurr_nvs748q\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` — NOT on PATH (prepend that bin dir).

## 1. FIRST — confirm green + read-in
```
cd C:/Dev/Projects/KataHarness/tools
uv run pytest -q                  # expect 1765 passed
uv run python validate_skills.py  # expect 47 skills, 0 errors
git -C C:/Dev/Projects/KataHarness log --oneline origin/master..HEAD   # expect empty (in sync)
git -C C:/Dev/Projects/KataHarness status -sb   # expect only uncommitted STATE/HANDOFF/orientation/REQUIREMENT (if any)
```
Read: `AGENTS.md` → `CONTEXT.md` (glossary — now has the **kata-validate** + **install/onboarding** sections) →
`.planning/STATE.md` (top box) → `DECISIONS.md` **D125–D126** → **`.planning/specs/install-update-polish/REQUIREMENT.md`**
(the NEXT requirement — grill it) → `protocol/{exec-safety,validation-misses,intent,reuse-claims}.md` →
`.planning/specs/{install-onboarding,kata-validate}/` (this session's frozen specs).
Note the env-sensitive `test_benchmark.py::TestRunDualGateCwd::test_importing_fixture_gives_q_one` is green canonically
(1765) but flaky in some sandbox venvs — NOT a regression (D124 caveat).

## 2. WHAT SHIPPED THIS SESSION (D125–D126, 2026-06-29) — both committed + PUSHED
- **D125 (`a749f5d`) — `kata-validate`**, the always-available validation mini-loop (`skills/evaluate/kata-validate`).
  A programmatically-callable `validate(payload, target="auto", profile) -> Report{passed, findings[]}` that runs
  **inline on ANY data OR another agent's output** and requires **NO freeze/INTENT/`kata.config`** (its defining
  property). 4 deterministic-first **METHOD-by-reference** legs (grounding = kata-evaluate injected-knowledge +
  grounding_gate · review = kata-review 5-surface RUBRIC · slop = kata-slop-check G1–G6/A1–A3 · score = kata-evaluate
  conformance, conditional/N-A when no plan). Drives its **OWN thin conductor** (`kata-loop`/`kata-onboard` precedent —
  `kata-orchestrate` is byte-for-byte UNTOUCHED); bounded **≤2 passes**; **payload-as-data isolation** (graded, never
  obeyed); **report-only by default**, per-finding human-gated fix via a **single writer** (validators stay no-write);
  **tripwire + cross-family-judge** rails. NEW pure `tools/validation_report.py` + `render_validation_banner`. PART B
  caught **2 fail-opens** the unit tests + PART A missed (severity case-sensitivity + a half-measure band-map — the
  default-FAIL escape class) → fixed.
- **D126 (`8d84125`) — install/onboarding final polish**, 4 ADDITIVE+BC slices. **The 5 `kata_install.py` engine
  functions are byte-for-byte UNTOUCHED; none of the 18 working patterns altered.** **G1** NEW `install.sh` (curl|sh) +
  `install.ps1` (irm|iex) + `uninstall.{sh,ps1}` wrapping the EXISTING engine (idempotent, no-cruft, `KATA_SRC` offline
  override, ships an uninstaller, honest curl|sh caveat). **G2** ADDITIVE headless flags
  (`--yes`/`--non-interactive`/`--answers-json`/`--json`/`--uninstall`/`--target-dir`) + non-TTY auto-skip + semantic
  exit codes (0 ok/1 not-confirmed/2 usage/3 not-found/4 permission/5 conflict) + idempotent re-install=0 no-op + machine
  JSON→stdout/human→stderr (autonomous-loop DEFERRED). **G3** optional `acceptanceCriteria` in `intent_scaffold`
  (byte-identical BC absent) + `protocol/intent.md` + `kata-initiate` step 2g + S2 gate value #9 (confirmed-absent
  PASSES; "blanket looks-good FAILS" preserved). **G4** NEW pure `tools/kata_router.py` (`..`-guarded idempotent
  marked-stanza upsert + orphan-marker data-loss guard) + `kata-onboard` v0.2.0 opt-in human-gated router stanza into the
  target's AGENTS.md; uninstaller removes exactly that block. PART B caught **1 data-loss state edge** (orphan-marker
  upsert, class `stateful-hole`) → fixed.
- **Gates this session:** pytest **1765** · **47/0** · Snyk **med+ 0** · offline install/re-install/uninstall smoke green
  on **BOTH Git Bash + PowerShell** · **live e2e seam proof WIRED**. **validation-misses now 14.** Each feature ran the
  FULL recipe (grill→freeze→freeze-gate→build→integration→live proof→PART A→PART B D98→fixes→merge gate→checkpoint).

## 3. ★ THE NEXT REQUIREMENT — `install-update-polish` (the operator's chosen step)
Release-readiness for **update / uninstall / settings**. The operator wants these **polished for the ACTUAL release**;
**once done they install and run a full test environment.** Intake brief written (pre-grill, NOT frozen):
**`.planning/specs/install-update-polish/REQUIREMENT.md`** — GRILL it → freeze → build through the recipe. **3 items:**
1. **One-command UPDATE — the headline gap: there is NO functional update today.** `install.sh` clones to `~/.kata-home`
   (a real git repo) but on re-run **REUSES it without pulling** (`install.sh:51-56`) → re-running curl|sh does NOT
   update. Symlink installs update via `git pull`; COPY installs (Windows no-DevMode) need `git pull` THEN re-run the
   engine to re-copy (`docs/SETUP.md:78`). No `--update`, no version check, no notification. **WANT:** a single-command
   update (`--update` on `kata_install.py` and/or `update.{sh,ps1}`) that pulls/fetches the home to ref, re-links/copies
   in one step, works on **both** link modes, idempotent + honest about copy-vs-symlink, + optionally an install-level
   version stamp + "newer available" check (per-skill semver exists in frontmatter; **NO install-level version surface
   today**). Keep ADDITIVE; do not edit the 5 engine functions unless freeze-gated.
2. **UNINSTALL polish — mostly built, make it release-clean.** (a) PART-B Finding 5: orphaned host links survive a
   skill rename/remove between install + uninstall (uninstall only removes current basenames) → consider sweeping all
   kata-managed slots. (b) stanza removal is scoped to the SUPPLIED target only (no cross-project registry) → document or
   add light tracking. (c) `--list` / dry-run preview. (d) confirm uninstall messaging is consumption-grade.
3. **`write_settings` MERGE-fix — the ONE item that edits a working pattern; needs its OWN freeze-gate.**
   `kata_settings.write_settings` OVERWRITES `~/.kata-settings.json` wholesale → an install with `--parent-dir` drops
   `confirmedPlatforms` (D121 multi-model confirm state). **WANT:** make it **MERGE** (preserve keys it does not own,
   esp. `confirmedPlatforms`). **CAUTION:** `kata_settings.py` is one of the 18 NOT-TOUCHED working patterns → strict BC
   (every existing test must still pass; preserve-more/lose-less). Recoverable via re-`--confirm`, but a release should
   not silently lose state.
**Carry into the grill:** pyyaml lives only under `tools/` (`build_intent`/`write_intent` run from `tools/`; install path
is stdlib-only, unaffected); Windows copy-mode means updates need reinstall (item 1 addresses the UX).

## 4. OTHER OPEN QUEUE (LOWER priority than install-update-polish)
- **PROPOSAL-phantom-reuse** (`.planning/PROPOSAL-phantom-reuse.md`) → freeze-gate `kata-review` → human merge — the
  standing **wiring-completeness gate** (so built-but-unwired can't recur). Still `proposed`.
- **kata-loop-benchmark** DEFERRED D1–D5: **D5** = operator's real control fixture = first LIVE benchmark run (n=0→1);
  **D3** = benchmark→`kata-improve` hook; D1 concurrent bakeoff arms (gated on Spec B), D2 research-judge, D4 promote-arm.
- **Debug Mode end-to-end live run** (n=0→1); **IaC Tier-2 LIVE-APPLY** (operator cloud creds); **`kata-reason` decider**
  + second-brain write/distill half (own grills); recurrence-hardening **T3** (auto-author guards, C-arc-gated).
- **Deferred MINORs:** `kata_install.py` 6 LOW CWE-23 (separate hardening); D125 nice-to-haves; D126 honest-scope notes
  (curl|sh exercised-not-proven; pyyaml-under-tools; Windows copy-mode reinstall).

## 5. HARD RULES
Human-attended (commit/merge/push ONLY on explicit operator approval; doesn't carry across contexts) · drive every step
via subagents (resume finished ones via `SendMessage(agentId)`) · decisions SUPERSEDED with new D-numbers, never rewritten
(dated notes; preserve provenance) · Snyk on all new/changed first-party Python; fix; rescan · repo PRIVATE, no
secrets/PII · IGNORE `C:\Dev\CLAUDE.md` (Mise) · PokeVault LOCAL-ONLY, never git · Windows: `git commit -F <file>`;
`validate_skills.py --write` centrally BEFORE pytest when a skill/version changed; README conductor/validator-owned · git
fetch+rebase before push (operator web edits).

## 6. THE RECIPE + the D124 live-wiring lesson
grill/plain → freeze → freeze-gate `kata-review` (HOLD/SHIP) → orchestrated build (subagents, disjoint ownership, TDD,
mutation-proof) → integration gate (pytest + validate 47/0 + Snyk + central README `--write`) → fresh-context
`kata-evaluate` (PART A, default-FAIL) → standing **D98** `kata-review` (PART B, adversarial) → re-confirm after fixes →
operator merge gate → checkpoint STATE/DECISIONS (new D-number). **★ Load-bearing lesson (D124, re-proven this session):**
PART A + D98 + unit tests **CANNOT see built-but-unwired / execution-context / cross-seam-description gaps** — for any
build touching `kata-orchestrate` wiring OR claiming an end-to-end flow, **ADD a realistic live wiring/e2e proof** (this
session's F1 wiring proof + F2 live e2e seam proof are the template — they caught real defects). Honesty: **"exercised
(n=1) ≠ proven"**; never overclaim gated-off capability. Guards: exec-safety (+ completeness test),
verify-before-reuse/cite-by-anchor, validation-miss manifest + T2, multi-model confirm-probe (LIVE). Routing:
judgment/plan/eval/grill/D98 = **Opus**; build/encode/workers = **Sonnet**.
