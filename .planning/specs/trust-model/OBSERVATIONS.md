---
spec: trust-model
artifact: "burn observations — the execution window's discovery + evidence channel (two-window fence: discoveries land HERE + kata-defer, never in the planning window's files)"
---

# OBSERVATIONS — the Trust Model burn (execution window)

## Green-at-fork baseline (recorded as INPUT per DESIGN §2.4/R2-M6 — prose-era record; the machinery that formalizes this is this burn's own W2/W3 work)

- Burn branch `burn/trust-model-01` forked from `grill/dispatch-seam` tip `0bebb6c`.
- Frozen PLAN committed `08ce3da`; F1f amendment `0e54351`.
- **Local gauntlet at the fork (conductor worktree, Windows): 4/4 PASS** — pytest-unit 4518
  passed / 3 skipped · pytest-integration 2/2 · ruff clean · validate-skills 49 skills, 0
  errors, 0 warnings. (Run 2026-08-16, `uv run python scripts/gauntlet.py`.)
- **CI is RED** (BL-X14, Guardian: Broken) — the X14 acceptance is CI green by burn close.

## Wave-1 dispatch record (Guardian: Honor-system — pre-seam prose dispatches, stated)

Seven builders dispatched 2026-08-16 off base `08ce3da`, Opus tier (D131, Fable anchor −1),
manual pinned worktrees under `C:\dev\projects\_kata_wt\trust-model\` (BBM-9, outside repo
root), disjoint ownership per the frozen PLAN wave-1 map:
`fix-mutation-prover` (E2 reproduce-first; task-branch CI push authorized) ·
`fix-statusline-crash` · `fix-learn-feed-truth` (**phase A triage ONLY** — E1 fork proposal
owed to the conductor before any fix) · `deferral-contract` · `exec-safety-registration` ·
`stale-anchor-fixes` (economy class) · `hook-capability-probe` (research class).

Enforcement this wave: **Dormant** (hook lands LAST, W8). Capture: Honor-system
(engine-by-conductor does not exist yet — prose collection). Resilience: Honor-system (no
cursor machinery yet — trail snapshots are the pre-existing board-only shape).

## Wave-1 integration record (2026-08-16)

- Seven task branches merged no-ff with `Kata-Task:` trailers into `burn/trust-model-01`
  (e484ce3 · 75e215a · 1657f50 · 10e169d · 36907d4 · 806aa79 · bd21107) + the exec-safety
  row-retirement follow-up merge + G2 README regeneration (`be2e006`) + DEF-3 (`3f29947`).
- **Local integration gauntlet 4/4** on the merged tree (pytest-unit, pytest-integration,
  ruff, validate-skills — all exit 0; validator 49/0/0 with README in sync).
- **CI GREEN — the 12-day red streak is OVER (the X14 acceptance):** run 31979757460
  (workflow_dispatch, SHA `3f29947` = the integrated tip), gauntlet (ubuntu-latest) SUCCESS +
  gauntlet (windows-latest) SUCCESS.
  https://github.com/taurran/kataharness/actions/runs/31979757460
  **Guardian: the CI gauntlet moves Broken → Verified with exactly this citation** (§6.6).
- Judge verdicts: 5× PASS first-round (X15, exec-safety, stale-anchors, hook-probe, X14);
  2× NEEDS_WORK cured and conductor-verified (deferral B1 → `e4c4e66`; X12 closure residue
  → phase B `cd8723b`). Spot-audit (conductor): deferral clause-pin + fingerprint mutation
  probe — both fired, restored byte-clean.

## Discoveries (append-only)

- **D-1 · The BL-X12 writeback gap (FOR THE PLANNING WINDOW to fold — fence-respecting
  handoff):** BL-X12 was fixed and conductor-gated CLOSED at `2a1b1cf` (2026-08-16 12:40,
  `specs/backlog-burn-02/OBSERVATIONS.md:84`), but `.planning/BACKLOG.md:562` still carries
  the 🔴 open marker — the closure was never written back. Consequence: the trust-model
  ASSESSMENT (T17 BROKEN), BURN-CHARTER item 4, both window orientations, and the frozen
  PLAN's `fix-learn-feed-truth` task were all authored off a ledger that lied about its
  state, and a wave-1 builder was dispatched against work already done (caught by the
  builder's H7 pushback, verified by conductor re-run: 105/105). **Planning window: mark
  BL-X12 closed at `2a1b1cf` in BACKLOG.md.** Stale references elsewhere (both orientations,
  BURN-CHARTER:22, ASSESSMENT:47/134, DESIGN.md:102's parenthetical, dispatch-seam
  ledger:112) are recorded here rather than edited — the gated/ruled artifacts stay as
  authored; this note is the correction of record. **Trust-model finding in its own right:**
  a closed defect whose ledger entry stays red re-schedules done work through an entire
  grill→design→plan→freeze pipeline; §6.6 truth-status marks + EV-1 cover the label side,
  but the WRITEBACK ACT at defect-closure has no owner — candidate binding input for BL-N11
  (backlog management).
- **D-2 · Retroactive trust-model grill emit RUN (2026-08-16):** written=29,
  parsed_open_skipped=2 (correct — the two genuinely open entries), redactions=0, to the
  Kiban vault feed (`.../wiki/pages/synthesis/decision-patterns/`, project slug
  `kataharness`, kind version-up). Ledger `converged:` line corrected (commit `0e9ada9`).
- **D-3 · `evidence:` `test:` argv-form reconciliation owed at W2:** DESIGN §3.5 pins
  compile-to `[python, -m, pytest, <id>]`, but every live sink uses `uv run pytest`
  (`mutation_check.run_named_test`, `scripts/gauntlet.py`); a bare `python -m pytest` misses
  the uv-managed venv. Conductor intent for the W2 `evidence-grammar` brief: grammar compiles
  per DESIGN; the EXECUTION environment may wrap the compiled argv in the uv runner as an
  environment detail, recorded in the module contract — divergence resolved visibly at build,
  not silently. (Exec-safety builder's finding 2.)
- **D-4 · Mutation-sink activation is now contractually BLOCKED on the argv conversion**
  (exec-safety builder's finding 1): the per-task verify command must never reach the
  still-`shell=True` mutation sink; `fix-mutation-prover` (in flight, W1) performs the
  conversion. W2/W6/W7 owners inherit the ordering constraint via the exec-safety watch-list.
- **D-5 · Citation-provenance data point (stale-anchor task):** `kata-validate/SKILL.md:276`'s
  `:13,151` anchor was BORN wrong (line 13 never contained the quoted sentence in any of the
  file's 9 revisions) — not drift but authoring-time fabrication; and line 369's reuse-table
  row had a symbol/range mismatch (anchor widened, label flagged for the W4/W5 rewrite).
  Feeds the B5/S2 detector rationale.
- **D-6 · Validator-evidence discrepancy (accuracy record, BBM-6 class):** the
  `stale-anchor-fixes` builder reported validate_skills green; the conductor re-run returned
  5 errors (STANDARDS §3 version bumps owed on all five changed skills). Fix-loop dispatched;
  builder's explanation pending — recorded whichever way it resolves.
- **D-6a · D-6 resolved:** the builder's accounting — its single validator run happened
  after editing but BEFORE committing, and the version-bump check reads committed blobs
  (`footprint.py:206` documents the ordering), so the green was real-but-invalid evidence
  for the claimed state; the stale claim is also baked into cc589e8's commit message
  (corrected on the record in a7e142b's). Ruled an accuracy finding, not fabrication.
  Corrected practice for all future briefs: **commit first, validate second, paste the raw
  exit code (no pipes — `$?` captures the pipe tail's status)**.
- **D-6b · Amendment G2:** README.md's generated skill index is owned by NO task; every
  SKILL.md version bump desyncs it. Ruled: regeneration is a per-wave integration-time
  conductor act (`validate_skills.py --write`, once, on the integration branch, before the
  wave-gate validator). Task gates for skill-touching tasks are green-except-README.
  Without this, W4's three concurrent skill tasks would have raced on the same generated
  block.
- **D-8 · deferral-contract landed with conductor-verified initial fingerprint pin:**
  the builder self-pasted the initial `deferral.md` pin (the updater cannot print a pin for
  a NEWLY registered file — it iterates the existing pin table, `validate_skills.py:1159`;
  no on-ramp exists). Conductor independently re-derived the digest via
  `--update-protocol-fingerprint`: exact match (`8f2cb080…`). Precedent `9af7c5e`.
  **Surfaced to the operator at the wave report** (an initial pin is a weaker act than a
  re-approval; the on-ramp gap is a small fix candidate for a later wave — recorded, not
  silently absorbed).
- **D-9 · Stale pin-count prose owed a human two-step:** `protocol/prime-directives.md:95-96`
  says 23 clause-pinned / 21 fingerprinted; with deferral.md the real numbers are 24 / 22
  (also echoed in `tools/tests/test_validate_prime_directives.py`). Correcting
  prime-directives.md requires its own fingerprint re-approval — **operator human moment,
  queued for the wave report**; leaving the numbers stale is recorded here so it is a known
  falsehood-in-waiting, not a silent one.
- **D-10 · `.planning/ASSUMPTIONS.md` never existed** despite four surfaces naming it
  canonical — created by deferral-contract with that provenance stated in-file; seeded with
  ASM-1 (the fingerprint-pin reasoning, ungrilled).
- **D-11 · kata-defer/kata-evaluate SKILL wiring to protocol/deferral.md deliberately NOT
  done in W1** (outside ownership) — owed to W4 `authoring-skills-migration` (kata-defer
  alignment is already in its task text) and W5 (kata-evaluate). Flagged so it is never
  assumed done.
- **D-12 · Hook probe (evidence/hook-probe.md, commit 95dae4c) — three findings wave 8 MUST
  absorb, all OBSERVED not assumed:** (1) **fail-open is the governing limit** — a PreToolUse
  hook that times out or crashes lets the call through; only a clean exit-2/deny-JSON blocks.
  The W8 hook must deny on internal error, and post-hoc verification is MANDATORY, not
  belt-and-braces (a broken hook is indistinguishable from an absent one in-session; the
  degrade table's no-result⇒Dormant clause is load-bearing in practice). (2) **Matcher
  naming trap:** the hook payload always carries tool_name "Agent" while result envelopes
  report "Task" — a hook asserting "Task" silently no-ops on every call. (3) **Capture needs
  BOTH edges:** PostToolUse sees the full return envelope on the sync path ONLY (background
  dispatch gets a handle ~4ms after launch); SubagentStop carries the verdict text on both
  paths but lacks the tool_use_id binding — R-H3 as written captures nothing on background
  dispatches without the second edge. Deny survives permission-skip flags (good for BBM-11);
  Bash leg sees the full pre-expansion command literal (Partially-verified residual confirmed
  as observed fact). Interactive sessions, Kiro/Codex, nested Agent-denies-Agent: UNPROBED,
  stated in the note.
- **D-15 · FOR THE PLANNING WINDOW (with D-1): BL-X14's BACKLOG diagnosis text (~line 486)
  records the FALSIFIED hypothesis** (sandbox import-path resolution). The observed mechanism
  is the cmd.exe `cd /d` prefix dying under `/bin/sh` with `shell=True` — both runs failed
  identically, mimicking vacuity (evidence: `evidence/x14-ci-green.md` + CI runs 31978174967
  red / 31979757460 green). When closing BL-X14 in the backlog, replace the diagnosis with
  the observed mechanism; also note stale `shell=True` prose at `.planning/DECISIONS.md:1211,
  1214` + `.planning/BACKLOG.md:840` (the latter is now done work).
- **D-13 · `tools/recall.py:607` carries the identical wrapped-bold-anchor blindness**
  (its own single-line `_BULLET_RE` copy): recall over DECISIONS.md still cannot see
  D168/D172/D173 and still returns D167/D171 with the swallowed text — the READ side of the
  loop phase B's fix only half-closes. Out of every wave-1 ownership; **for the planning
  window: file as a new backlog item** (pairs with the BL-X12 closure writeback, D-1).
- **D-14 · The wave-1 judge layer earned its cost (accuracy record):** of seven items, the
  fresh-context judges caught two real defects that builder self-gates AND conductor
  re-runs both missed — the deferral contract's self-staled citation inside its own
  fingerprinted commit (cured `e4c4e66`, pin re-derived and matched), and the overbroad
  X12 closure hiding a half-fixed sub-defect with neighbor-body corruption (cured
  `cd8723b`). Also: X14's judge found one unreproducible count in the evidence note (46 vs
  91 `testWentRed` occurrences in run 1 — understates pre-fix badness, correction owed at
  the note's zero-failure amend) and confirmed the E2 falsification escalation reached the
  conductor (it did — recorded).
- **D-7 · Minor: `statusline_chain.py` docstring's §security block claims its exec-safety
  row "lands at P2/C10 closeout" — stale: the row EXISTS (`protocol/exec-safety.md:68`).
  Docstring correction can ride any future statusline touch. X15's Snyk scan: one
  pre-existing Medium (CWE-78 class) on the registered operator-domain sink, unchanged by
  the fix (verified by revert-and-rescan); no `.snyk` entry added (outside task ownership) —
  surfaced here for the wave gate.
