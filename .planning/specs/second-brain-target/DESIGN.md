---
tags:
  - kata/spec
  - second-brain
---

# second-brain-target — DESIGN (E3 reframed; frozen 2026-07-13)

**Status:** FROZEN — freeze-gate HOLD(3 HIGH) → all folded → re-gate SHIP-WITH-FIXES (1
residual: HIGH-3 not propagated to PLAN T3 — folded) · 2026-07-13 · grill: `GRILL-LEDGER.md`
(D1–D5 + EV-1, standard tier, operator present) · INTENT: the frozen root `INTENT.md` (6 ACs) ·
instrumented run (`inlineEval: telemetry` — the E1/E2 `verify.owned` unblock).

## Frame (from the grill, binding)

Second brain is a **user-definable, optional TARGET** — never a requirement (D2). MindBridge is
OUT (D1). No vault or install churn (D2/D5): the only vault writes this run makes are the
standard grill-close emits already performed. The NEW build is the **PokeVault recommendation
flow** (D3) with the **remembered-decline** leg (EV-1).

## S1 — engine: the recommendation decision (pure, tested)

`tools/kata_settings.py` gains:

- `vault_recommendation(settings, home=None) -> dict` — pure decision:
  `{"recommend": bool, "reason": str, "link": "https://github.com/taurran/pokevault"}`.
  `recommend=True` IFF `vaultDir` is unset/empty AND no un-lapsed remembered decline exists.
  **Remembered decline + re-arm (EV-1):** the decline lives in `acceptedDefaults`
  (`"vault-recommendation": {value: "declined", v: <gitSha-or-"unknown">, at: <ISO>}` — the
  existing C-1 schema, no new store). Re-arm mirrors `first_run_required`'s version clause:
  a recorded decline whose `v` ≠ the current `.kata-version` `gitSha` has LAPSED ⇒ recommend
  again; stamp absent or `gitSha == "unknown"` ⇒ the version clause is skipped and the decline
  holds (dev in-repo posture — a dev tree must not nag).
- `record_vault_decline(home=None) -> None` — thin wrapper writing that acceptedDefaults entry
  via the existing `record_accepted_defaults` (fail-closed inherits).
- Corrupt/absent settings read as "no decline recorded" (lenient read, consistent with
  `first_run_required`); the WRITE stays fail-closed (C-3 posture).

## S2 — installer surface: a note, never a prompt

`tools/kata_install.py` `main()`: **insertion point pinned (freeze-gate HIGH-2 fold):
immediately BEFORE the plain-install `result = install(...)` call (~line 1824), i.e. after
every verb branch (`--install-hooks`/`--uninstall-hooks`, `--confirm`, `--uninstall`,
`--update`, `--factory-reset`, `--dry-run`) has already returned** — NOT "after settings
handling", which is a shared prelude those verbs also pass through. When the effective
`vault_dir` is unset AND `vault_recommendation(...)` says recommend ⇒ **print a one-line note
to stderr** (and a `vault_recommendation` field riding the plain-install `--json` result
dict): second brain is optional; to add one later,
point `--vault-dir` at any vault, or start with PokeVault → the repo link. **Never a prompt**
(the CLI's `_non_interactive` contract "no interactive prompts today" is preserved — a note
cannot hang a headless run; AC2's never-hang leg). The note does NOT record a decline (only an
explicit interactive decline does, S3 — a note the user never answered is not a choice).

## S3 — skill surface: the per-discretion ask (once)

`kata-bootstrap` (Phase 2.5 bundle) + `kata-initiate` (Phase 2 mirror, vault value) prose: when
composing a run with `vaultDir` unset AND `vault_recommendation` recommends ⇒ ONE structured
question (recommendation-first, free-text escape): link PokeVault (`git clone` + bootstrap, or
install), name their own vault path, or decline. **Decline ⇒ `record_vault_decline`** (EV-1 —
surfaced once, re-armed by install/upgrade only). Accept-own-path ⇒ the existing
`--vault-dir`/settings write path. The question NEVER blocks: headless/no-TTY composition skips
it (the floor: feed no-op). **Same-session once-guard (freeze-gate HIGH-3 fold):** both
insertion points share ONE pull-check (`vault_recommendation`) — and the kata-initiate ask
MUST persist the answer IMMEDIATELY at the moment the human answers (accept-a-path ⇒
`kata_settings.write_settings(..., vault_dir=...)`; decline ⇒ `record_vault_decline()`) —
BEFORE Phase 5 ever invokes kata-bootstrap, so bootstrap's Phase 2.5 check in the same session
sees `recommend=False` and never re-asks (EV-1 "surfaces once" holds within a session, not just
across sessions). T3 acceptance includes a manual trace of the initiate→bootstrap same-session
composition. Skill edits carry **bump-on-modify** version increments + validator `--write`.

## S4 — docs: optional-target truth

`docs/SETUP.md` + `README.md` second-brain mentions state plainly: second brain is an
**optional target** — kata is fully functional without one (feed no-op, BC1); any vault path
works; PokeVault is the recommended starter (repo link). No surface may claim it is required
(AC3).

## S5 — instrumentation (how this run pays for E1/E2)

`kata.config` `inlineEval: "telemetry"` is already written. Every task below carries an
`estimate:` in the PLAN frontmatter and a per-task **owned-scoped verify command** (D4); the
dispatch brief carries the checkpoint-commit + `Kata-Checkpoint:` trailer mandate. The run's
records land in the telemetry stream + the calibration ledger at
`.planning/telemetry-ledger.md` (AC4).

## Out of scope (recorded, not drift)

MindBridge (D1, operator) · any vault install/copy (D2) · vault AGENTS.md instantiation (D5,
convergence-resolved) · interactive prompts inside kata_install CLI (S2 note-only; the ask
lives in the skill surface).

## Acceptance

= the frozen INTENT.md AC1–AC6, verbatim. Gate chain: freeze-gate (fresh-context, no-write) →
dual-control operator confirm → orchestrated build (workers in worktrees, no-git in main tree;
conductor sole git writer) → full gauntlet + Snyk (when-available) → fresh-context adval →
PR → merge → `record_first_run` + closeout.
