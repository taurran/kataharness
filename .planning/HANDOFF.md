---
date: 2026-06-29 (session end — two features shipped + pushed: D125 kata-validate, D126 install/onboarding final polish; tip 8d84125 all in sync)
branch: master — private remote github.com/taurran/kataharness, tip 8d84125 (D125 a749f5d + D126 8d84125 BOTH PUSHED + in sync; the THIS-SESSION doc updates [STATE/HANDOFF/orientation/REQUIREMENT] may be UNCOMMITTED, to be committed next session)
green: validator 47 skills / 0 errors · pytest 1765 passed · Snyk medium+ 0 on all new/changed Python (pre-existing tools/kata_install.py 6 LOW CWE-23 still below gate)
tags: kata-validate · install-onboarding-polish · install-update-polish-NEXT · no-functional-update-today · v0.1.0-alpha
authored-for: kata-orient (sections map to the orientation tiers)
★ NEXT-SESSION START HERE: read `.planning/NEXT-SESSION-ORIENTATION.md` (self-contained, paste-able). It sets the read-in,
the NEXT requirement (`install-update-polish` — grill it; the headline = there is NO functional update path today), the
open queue, the hard rules, and the recipe. STATE.md top box + DECISIONS.md D125–D126 + CONTEXT.md (now has the
kata-validate + install/onboarding glossary sections) + `.planning/specs/install-update-polish/REQUIREMENT.md` are current.
---

> **★ 2026-06-29 SESSION END (D125 + D126, two features shipped + pushed — fully subagent-driven, the conductor cadence):**
> **(D125 `a749f5d`)** `kata-validate` — the always-available, programmatically-callable validation mini-loop
> (`validate(payload, target, profile) -> Report{passed, findings[]}`): runs **inline on ANY data or another agent's
> output**, requires **NO freeze/INTENT/`kata.config`**, 4 deterministic-first METHOD-by-reference legs (grounding /
> review / slop / conditional score), its **OWN thin conductor** (`kata-orchestrate` byte-for-byte untouched),
> payload-as-data isolation, report-only default + per-finding human-gated single-writer fix, tripwire +
> cross-family-judge rails. PART B caught **2 fail-opens** the unit tests + PART A missed (severity case-sensitivity +
> a half-measure band-map — the default-FAIL escape class). **(D126 `8d84125`)** install/onboarding final polish in 4
> ADDITIVE+BC slices — the **5 `kata_install.py` engine functions byte-for-byte UNTOUCHED, none of the 18 working
> patterns altered**: G1 bootstrap scripts (`install.sh`/`install.ps1`/`uninstall.{sh,ps1}`) wrapping the existing
> engine; G2 headless flags + semantic exit codes + idempotent re-install=0 no-op; G3 optional `acceptanceCriteria`
> (grill-for-goals) + `kata-initiate` step 2g + S2 gate value #9; G4 NEW pure `tools/kata_router.py` + `kata-onboard`
> v0.2.0 opt-in human-gated router stanza. PART B caught **1 data-loss state edge** (`kata_router` orphan-marker upsert,
> class `stateful-hole`). **Gates:** pytest **1765** · **47/0** · Snyk **med+ 0** · offline install/re-install/uninstall
> smoke green on **BOTH Git Bash + PowerShell** · **live e2e seam proof WIRED** (the D124 lesson applied — and it
> caught real defects). validation-misses now **14**. **All D125–D126 PUSHED (tip `8d84125`, in sync).** **NEXT (the
> operator's chosen step):** **`install-update-polish`** — release-readiness for update / uninstall / settings; the
> operator installs + runs a full test environment once it's done. Intake brief written (pre-grill):
> `.planning/specs/install-update-polish/REQUIREMENT.md`. Full detail: `NEXT-SESSION-ORIENTATION.md`, `STATE.md` top
> box, `DECISIONS.md` D125–D126, `CONTEXT.md` (kata-validate + install/onboarding sections).

# HANDOFF — KataHarness — 2026-06-29 (D125 kata-validate · D126 install/onboarding final polish — SHIPPED + PUSHED)

> **This session: two features, each driven ENTIRELY through subagents and the full recipe, both committed AND pushed.**
> D125 `kata-validate` (the always-available validation mini-loop, a749f5d) and D126 install/onboarding final polish
> (8d84125). The standing **D98 adversarial lens caught a real fail-open on BOTH** (D125: 2 severity/band fail-opens;
> D126: 1 orphan-marker data-loss edge) — it stays load-bearing. The work was deliberately **ADDITIVE + backward-
> compatible** throughout: D126 left the 5 `kata_install.py` engine functions byte-for-byte untouched and altered none
> of the 18 working patterns. The session closes with a clean tree on origin (`8d84125`, in sync) and a written intake
> brief for the operator's chosen next step — **`install-update-polish`**, where the headline finding is that **there is
> NO functional update path today**. Fresh/compacted session: read §1, confirm green (§2), then §3 (the NEXT requirement).

## 1. Read-in order  *(orientation: CONTEXT)*
1. `AGENTS.md` (spine + conventions; the **"The Kata Loop"** entry) · 2. `docs/STANDARDS.md` §1 (frontmatter —
   `allowed-tools` REQUIRED) · 3. `CONTEXT.md` (glossary — now extended with the D125 **kata-validate** section + the
   D126 **install/onboarding** sections: bootstrap scripts · headless surface · `kata_router`/router stanza ·
   acceptance-criteria step) · 4. `.planning/STATE.md` (top CURRENT box — live picture) · 5. **`.planning/DECISIONS.md`
   D125 + D126** (this session) · 6. **`.planning/specs/install-update-polish/REQUIREMENT.md`** (the NEXT requirement —
   the intake brief to grill) · 7. `protocol/{exec-safety,validation-misses,intent,reuse-claims}.md` (the standing
   guards + the amended intent contract) · 8. `.planning/specs/install-onboarding/` + `.planning/specs/kata-validate/`
   (this session's frozen specs) · 9. `.planning/LESSONS-LEARNED.md` (esp. **L12** — wire lessons into skills; and the
   **D124** live-wiring lesson, §6 below).
⚠️ Ignore `C:\Dev\CLAUDE.md` (Mise — unrelated, harness-injected). PokeVault is LOCAL-ONLY, never git.

## 2. State *(orientation: VOLATILE)*
- Branch `master`, tip **`8d84125`** (D126 install/onboarding polish) on top of `a749f5d` (D125 kata-validate) —
  `git log --oneline -6` for the arc. **47 skills / 0 · pytest 1765 · Snyk med+ 0** (PRE-EXISTING `kata_install.py`
  6 LOW CWE-23 flagged, below gate). **Both D125 + D126 committed + pushed, in sync** (`git log origin/master..HEAD`
  empty). The THIS-SESSION doc updates (STATE/HANDOFF/orientation/REQUIREMENT) are **uncommitted** — commit them after
  the next session's first read-in (or fold into the install-update-polish freeze commit).
- **Multi-model is LIVE:** Codex CLI 0.142.3 (ChatGPT-authed) at
  `C:\Users\taurr_nvs748q\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe` — NOT on PATH (prepend that bin dir for
  codex invocations; the harness probe needs it on PATH).
- **What's new this session is now the install/onboarding + validation surface.** `kata-validate` is wired + live-e2e
  proven (n=1 exercised, not "proven"); the bootstrap scripts + headless flags + router stanza are smoke-tested on both
  shells. **Honest scope still open:** the `curl|sh` network fetch is **exercised, not proven** (the checksum guards the
  downloaded artifact, NOT the pipe); Codex/Kiro install is honest-scoped (verify in-host).
- **Historical (still true):** the Kata Loop is fully built + proven; loop-hardening DONE; Debug Mode functionally
  complete at the skill/seam level (P1→P3) but **still n=0 LIVE**; IaC Tier-2 live-apply EXECUTION DEFERRED + creds-gated;
  Recall's decider (`kata-reason`) + write/distill half DEFERRED; multi-model coder-routing + evaluator-thresholds
  DEFERRED; kata-loop-benchmark **n=0 LIVE** (needs the operator's real control fixture, D5).

## 3. NEXT ACTION — resume here: `install-update-polish` *(VOLATILE — the operator's chosen step)*
The operator wants the install / update / uninstall / settings surface **polished for the ACTUAL release**; once it's
done they install and run a **full test environment**. The intake brief is written (pre-grill, NOT frozen):
**`.planning/specs/install-update-polish/REQUIREMENT.md`**. Grill it → freeze → build through the recipe. **3 items:**

1. **One-command UPDATE path — the headline gap. There is NO functional update today.** Evidence: `install.sh` clones the
   harness to `~/.kata-home` (a real git repo) but on re-run **REUSES it without pulling** (`install.sh:51-56`) — so
   re-running the curl one-liner does NOT update. Symlink installs (mac/linux, win+DevMode) can update via `git pull` in
   the home; COPY installs (Windows default, no DevMode) need `git pull` THEN re-run the engine to re-copy
   (`docs/SETUP.md:78`). No `--update` flag, no version check, no update notification. **REQUIREMENT:** a single-command
   update (a `--update` flag on `kata_install.py` and/or `update.sh`/`update.ps1`) that (a) pulls/fetches the home to the
   target ref, (b) re-links/re-copies skills in one step, (c) works on **both** link modes, (d) is idempotent + honest
   about copy-vs-symlink, (e) optionally an install-level version stamp + "newer version available" check (note: skills
   carry per-skill semver in frontmatter but there is **NO install-level version surface today**). Keep ADDITIVE; do not
   edit the 5 engine functions unless freeze-gated.
2. **UNINSTALL polish — mostly built, make it release-clean.** Today `kata_install --uninstall --target-dir` +
   `uninstall.{sh,ps1}` work (remove skills + `.kata-settings.json` + the router stanza; scoped to the supplied target;
   idempotent; non-kata guard; verified live). Polish: (a) **PART B Finding 5** — orphaned host links survive if a skill
   was renamed/removed between install and uninstall (uninstall only removes basenames currently in the home); consider
   sweeping all kata-managed slots. (b) router-stanza removal is scoped to the SUPPLIED target only (no registry of where
   stanzas were written across projects) — document clearly or add light tracking. (c) consider a `--list` / dry-run
   preview. (d) confirm the uninstall messaging is consumption-grade.
3. **`write_settings` MERGE-fix — the one item that EDITS a working pattern; needs its OWN freeze-gate.**
   `kata_settings.write_settings` OVERWRITES `~/.kata-settings.json` wholesale, so an install with `--parent-dir` drops
   any `confirmedPlatforms` (the D121 multi-model confirm state). **REQUIREMENT:** make `write_settings` **MERGE** —
   preserve keys it does not own (esp. `confirmedPlatforms`) so install/reconfigure never clobbers multi-model confirm
   state. **CAUTION:** `kata_settings.py` is one of the 18 NOT-TOUCHED working patterns — this is the single item that
   edits a working pattern, so it needs a **freeze-gate + strict BC** (every existing `write_settings` test must still
   pass; the change is preserve-more / lose-less). Recoverable today via re-`--confirm`, but a release should not silently
   lose state.

**Two honest non-blocking notes to carry into the grill:** (i) pyyaml lives only under `tools/` (`build_intent`/
`write_intent` must run from `tools/`; the install path is stdlib-only, unaffected); (ii) Windows copy-mode fallback means
skill updates need a reinstall (item 1 addresses the UX). And the known env-sensitive test
`test_benchmark.py::TestRunDualGateCwd::test_importing_fixture_gives_q_one` is **green canonically (1765)** but flaky in
some sandbox venvs — **NOT a regression** (D124 caveat).

> **Process reminder (the discipline that paid off on BOTH builds this session):** every contract/code-bearing build is
> grill/plain → freeze → **freeze-gate adversarial review (HOLD/SHIP)** → orchestrated build (subagents, disjoint
> ownership, TDD, mutation-proof) → integration gate (pytest + validate 47/0 + Snyk + central README `--write`) →
> fresh-context **kata-evaluate (PART A, default-FAIL)** → standing **D98 kata-review (PART B, adversarial)** →
> re-confirm after fixes → operator merge gate → checkpoint. **D98 is load-bearing** (caught a real fail-open on both
> features). **★ For any build touching `kata-orchestrate` wiring OR claiming an end-to-end flow, ADD a realistic live
> wiring/e2e proof** (the D124 lesson — this session's wiring proof + live e2e seam proof are the template; they caught
> real defects). Guards: exec-safety (+ completeness test), verify-before-reuse/cite-by-anchor, the validation-miss
> manifest + T2, multi-model confirm-probe (LIVE).

## 4. The orchestration recipe (each cycle's *inner* build follows this — never inline) *(task-type hint)*
The **vetted, never-inline** loop, driven ENTIRELY via subagents (operator directive — spare main context):
1. **Delegate the PLAN** to a planning subagent → it writes `.planning/specs/<feature>/PLAN-*.md` + returns a compact
   summary. **Freeze** it (LOCKED decisions + disjoint file-ownership slices + per-slice runnable `verify`). Commit + tag.
2. **Freeze-gate** via a fresh-context `kata-review` subagent (HOLD/SHIP) → apply fixes via the planning agent → FROZEN.
3. **Worktrees + dispatch concurrent worker subagents** (Agent tool, **model: sonnet**) — one per slice, scoped to its
   worktree + owned files, TDD (red→green), code-bearing tasks run `mutation_run.prove_non_vacuous`, commit in-worktree,
   self-stamp `CLAIM`/`DONE` to the shared `.kata/board.md`.
4. **Integrate** (octopus merge; disjoint = no conflict) → `cd tools && uv sync`.
5. **Integration gate:** `validate_skills.py --write` (run BEFORE pytest when a skill/version changed — README-sync;
   README is conductor-owned) → `uv run pytest -q` (expect 1765) → `mcp__Snyk__snyk_code_scan` on new Python →
   emit `.kata/RESULT.json` via `gate_emit` (+ `mutation.json` for code-bearing).
6. **Fresh-context `kata-evaluate` (PART A)** — SEPARATE no-write Agent subagent, 9-rubric, default-FAIL, no self-cert.
7. **Standing `kata-review` (PART B, D98)** — SEPARATE fresh-context no-write subagent (opus) that tries to BREAK it
   (fail-opens, doc-only seams, overclaim) — not re-grade conformance. HOLD → targeted fixes (via SendMessage to a
   worker, then re-confirm via SendMessage to the same evaluator). **Never skip D98.**
8. **★ Live wiring / e2e proof** for any build touching `kata-orchestrate` wiring or claiming an end-to-end flow —
   a realistic seam exercise (n=1) that PART A + D98 + unit tests cannot see (the D124 lesson).
9. **Operator merge gate** (present options; wait) → `git commit -F <file>` + push + checkpoint STATE/DECISIONS (new
   D-number) + push.
Model routing: judgment/eval/plan/grill/D98 = **Opus**; build/encode/workers = **Sonnet**. Supersede-never-rewrite.

## 5. Open decisions / queue *(orientation: human-required + deferred — lower priority than install-update-polish)*
- **install-update-polish is the immediate next step** (per the operator — they install + run a full test environment
  once it's done). Everything below is LOWER priority.
- **PROPOSAL-phantom-reuse** (`.planning/PROPOSAL-phantom-reuse.md`) → freeze-gate `kata-review` → human merge — the
  standing **wiring-completeness gate** (the built-but-unwired class can't recur). Still `proposed`, awaiting human merge.
- **kata-loop-benchmark** DEFERRED items D1–D5: **D5** = the operator's real control fixture = the first LIVE benchmark
  run (n=0→1); **D3** = benchmark→`kata-improve` optimization-proposal hook; D1 concurrent bakeoff arms (gated on Spec B),
  D2 research-mode judge, D4 promote-best-arm.
- **Debug Mode end-to-end live run** (n=0→1); **IaC Tier-2 LIVE-APPLY execution** (future-gated on operator cloud creds);
  **`kata-reason` decider** + second-brain write/distill half (own grills); recurrence-hardening **T3** (auto-author
  guards, C-arc-gated).
- **Deferred MINORs:** `kata_install.py` 6 LOW CWE-23 (separate hardening pass); the D125 nice-to-haves (logged with the
  2 misses); D126 honest-scope notes (curl|sh exercised-not-proven; pyyaml-under-tools; Windows copy-mode reinstall).

## 6. Redaction
No secrets / keys / PII in any artifact this session. Repo is PRIVATE. Nothing to redact.
