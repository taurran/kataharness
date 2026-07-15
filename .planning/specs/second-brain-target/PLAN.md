---
tags:
  - kata/plan
  - second-brain
tasks:
  - id: T1
    title: "Engine: vault_recommendation + record_vault_decline (+ AC1 seeding test)"
    owns:
      - tools/kata_settings.py
      - tools/tests/test_kata_settings_vault_rec.py
    wave: 1
    estimate: 20
    verify: "cd tools && uv run pytest tests/test_kata_settings_vault_rec.py -q"
  - id: T2
    title: "Installer note (S2) + docs optional-target truth (S4)"
    owns:
      - tools/kata_install.py
      - tools/tests/test_kata_install_vault_note.py
      - docs/SETUP.md
      - README.md
    wave: 2
    estimate: 20
    verify: "cd tools && uv run pytest tests/test_kata_install_vault_note.py -q"
  - id: T3
    title: "Skill surface (S3): bootstrap + initiate recommendation step, version bumps"
    owns:
      - skills/coordinate/kata-bootstrap/SKILL.md
      - modules/initiation/kata-initiate/SKILL.md
    wave: 2
    estimate: 15
    verify: "cd tools && uv run python validate_skills.py"
---

# PLAN — second-brain-target (frozen 2026-07-13; executes the sibling DESIGN.md S1–S5)

One integration branch (`feat/second-brain-target`), conductor = sole main-tree git writer;
workers build in **isolated worktrees** (T2 ∥ T3 concurrent in wave 2), no-git beyond their own
worktree checkpoint commits (`Kata-Checkpoint:` trailer mandate — inlineEval telemetry).

## T1 (wave 1) — engine

Implement DESIGN S1 exactly: `vault_recommendation(settings, home=None)` (pure decision;
recommend IFF vaultDir unset AND no un-lapsed decline; re-arm mirrors `first_run_required`'s
version clause incl. the `gitSha=="unknown"` skip) + `record_vault_decline(home=None)` (thin
`record_accepted_defaults` wrapper, fail-closed inherited). TDD. Tests MUST cover: recommend on
empty settings · no-recommend when vaultDir set · no-recommend under a live decline ·
LAPSED decline re-arms on gitSha mismatch · `unknown`-sha skip holds the decline · corrupt
settings ⇒ lenient read (recommend) · **AC1: `default_learn_feed_dir` seeds correctly from a
CUSTOM vaultDir path (any user vault, not just PokeVault)**. Acceptance: verify green; no other
kata_settings behavior changes (existing tests untouched and green).

## T2 (wave 2, after T1) — installer note + docs

DESIGN S2: the stderr note (+ `--json` field) on the plain-install path when
`vault_recommendation` recommends; NEVER a prompt; the note records nothing. DESIGN S4: SETUP.md
+ README second-brain sections say optional-target (kata fully functional without; any vault
path; PokeVault recommended starter with the repo link). Tests: note emitted on vaultless
install (subprocess or main()-level, matching the file's existing test style) · note absent when
vaultDir set · note absent under a live decline · `--json` carries the field · exit codes
unchanged · **verb-exclusion regressions (freeze-gate HIGH-2 fold): note AND `--json` field
absent under `--update`, `--uninstall`, `--confirm`, and `--factory-reset` even with vaultDir
unset and `KATA_PARENT_DIR` set**. Acceptance: verify green; no existing kata_install test
modified.

## T3 (wave 2, ∥ T2) — skill prose

DESIGN S3 into the two skills: the ONE structured recommendation question (recommendation-first,
free-text escape, decline ⇒ `record_vault_decline`, never blocks, headless skips), placed in
kata-bootstrap Phase 2.5 (bundle slot) + kata-initiate Phase 2 (mirror vault value). **Once-guard
(freeze-gate HIGH-3, BINDING here in the executable contract, not only in DESIGN prose):** both
insertion points read the SAME live pull-check (`vault_recommendation`); the kata-initiate prose
MUST mandate IMMEDIATE persistence at the moment the human answers — accept-a-path ⇒
`kata_settings.write_settings(..., vault_dir=...)` right then; decline ⇒ `record_vault_decline()`
right then — never deferred to the Phase-6 INTENT freeze, so a Phase-5 bootstrap invocation in
the SAME session sees `recommend=False` and never re-asks. MINOR version bumps on both skills
(bump-on-modify) — then validator green. Prose only; no engine edits (T1 owns the engine).
**T3 acceptance (named, conductor-checked):** in addition to the validator verify, the conductor
performs the same-session initiate→bootstrap trace (read both edited SKILL.md files end-to-end
and confirm the ask-once chain: initiate asks → persists immediately → bootstrap's Phase-2.5
check pulls the persisted state → no second ask) BEFORE the fresh-context adval.

## Integration + gates (conductor)

Sequence: T1 → gate → dispatch T2 ∥ T3 → gate each → integrate → full gauntlet + Snyk
(when-available, tools/) → fresh-context adval → PR → merge → `record_first_run` + closeout
(understand-map offer, EV/decision emit, BACKLOG E3 text corrected per D1).

Per-task gate (default-FAIL): the task's `verify` command green + owned-file scope respected +
no re-planning (escalate on discovery). **T3 additionally gates on the conductor-performed
same-session initiate→bootstrap once-guard trace (HIGH-3 fold — not automatable as a command;
performed and recorded before the adval).** Estimates above feed
`kata_telemetry.resolve_estimate`; checkpoint records carry `verify.owned` = the task verify
exit (D4).
