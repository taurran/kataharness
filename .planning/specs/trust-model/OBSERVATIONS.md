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
- **D-7 · Minor: `statusline_chain.py` docstring's §security block claims its exec-safety
  row "lands at P2/C10 closeout" — stale: the row EXISTS (`protocol/exec-safety.md:68`).
  Docstring correction can ride any future statusline touch. X15's Snyk scan: one
  pre-existing Medium (CWE-78 class) on the registered operator-domain sink, unchanged by
  the fix (verified by revert-and-rescan); no `.snyk` entry added (outside task ownership) —
  surfaced here for the wave gate.
