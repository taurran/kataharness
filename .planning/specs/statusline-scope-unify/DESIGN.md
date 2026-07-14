---
tags:
  - kata/spec
  - statusline
---

# statusline-scope-unify — BACKLOG 7 (G5 follow-up of [[statusline-decouple]])

**Status:** FROZEN — freeze-gate SHIP-WITH-FIXES (1 HIGH, folded into U2) · 2026-07-13 ·
conductor session f165e776
**Operator scope decision (2026-07-13, single-question grill):** scope-check unification ONLY.
The full visual reconcile (restyling the fresh-profile line into the D162 segment family) was
offered and **DECLINED** — the PLAN-s1.5 LOCKED long format stays frozen. The decline is
preference signal (rides the second-brain feed at closeout). Renderer restyle is NOT re-queued;
if wanted later it re-enters as its own grilled item.

## Problem (BACKLOG item 7, verbatim gap)

`tools/kata_statusline.statusline_from_event` — the fresh-profile renderer — still carries its
OWN kata-scope check: local payload-cwd parsing (`cwd` → `workspace.current_dir`) + a
single-level `<cwd>/.kata` existence test. Consequences today: (1) a THIRD scope definition
next to `kata_scope.find_kata_root`'s ONE walk; (2) the fresh profile does NOT render from
subdirectories of a kata repo and does NOT recognize `kata.config`-only repos — the chain
wrapper's kata leg does both, so the two profiles disagree about what "in a kata scope" means.

## Locked decisions

- **U1 — the ONE home moves to core: `tools/kata_scope.py`.** `git mv` of
  `adapters/claude/kata_scope.py`, public surface byte-identical (`find_kata_root`,
  `is_kata_scope`, `resolve_start`, `_SCOPE_WALK_CAP`); docstring home/consumer text updated.
  Rationale (supersedes the D160/EV-1 "adapter home" wording, deliberately): the core renderer
  is now a consumer, and core MUST NOT import adapter code; the module is pure stdlib, so it is
  core-legal. A re-export shim at the old path is REJECTED — a module named `kata_scope`
  importing `kata_scope` self-shadows under the adapter-dir-first sys.path insert the chain
  wrapper uses (deterministic import trap); a by-path shim is avoidable complexity. NO shim,
  consumers re-point.
- **U2 — both adapter consumers re-point to tools/.** Each file mirrors its OWN existing
  `kata_gauge` import offset *(freeze-gate HIGH fold: the two consumers sit at different
  depths — one shared numeral would silently no-op the gauge hook)*:
  `statusline_chain._import_kata_scope` → `parents[2]/tools` (as its `_import_kata_gauge`,
  line ~223); the gauge hook `adapters/claude/hooks/kata-gauge-check.py` → `parents[3]/tools`
  (as its existing kata_gauge import, line ~154). Import statements (`import kata_scope`)
  stay textually identical (the gauge-hook pin
  `kata_scope.resolve_start(payload) or Path(os.getcwd())` is untouched).
- **U3 — `statusline_from_event` adopts the ONE walk + ONE resolution.** Local cwd extraction
  and the `<cwd>/.kata` check are DELETED, replaced by `kata_scope.resolve_start(data)` +
  `kata_scope.find_kata_root(start)`; scope found ⇒ `build_statusline(root / ".kata")` (a path
  join, not a scope check — the spec-blessed literal class). Bridge-write-before-render order
  and the fail-soft contract are unchanged. Behavior deltas (the POINT of the item, not drift):
  subdir-of-kata-repo now renders; `kata.config`-only repo now renders (absent
  `.kata/board.md`+`state.json` ⇒ the existing waiting/idle line — coherent "configured, no
  active run"). Frozen long-format BYTES unchanged for every existing in-`.kata`-cwd fixture.
- **U4 — drift tests re-pin, conjunctively.** The parent-walk-only-in-`kata_scope` test now
  points at `tools/kata_scope.py`; consumer pins assert the chain wrapper, the gauge hook, AND
  `kata_statusline` all route through `kata_scope` with no local walk / no local payload-cwd
  parsing in `statusline_from_event`. `test_kata_scope.py` KATA_SCOPE path moves to tools/.
- **U5 — no new renderer work.** `_bar8` (task-progress, fresh profile) and `_bar10`
  (context-meter, chain segment) encode DIFFERENT semantics; merging them is cosmetic-only and
  stays out (operator decline, header). Sharing is limited to what U3 already forces.

## Tasks (one builder, sequential, no-git — conductor commits)

- **T1** `git mv` (conductor pre-stages the move; builder edits content only): module docstring
  home/consumers text.
- **T2** chain wrapper `_import_kata_scope` → tools path (docstring line).
- **T3** gauge hook kata_scope import path → tools (comment line).
- **T4** `statusline_from_event` U3 rewrite (docstring: walk semantics + deltas).
- **T5** tests: `test_kata_scope.py` path; `test_statusline_chain.py` drift-test re-pins +
  kata_statusline consumer pin; `test_kata_gauge_check.py` path-pin if it hardcodes the adapter
  file; `test_kata_statusline.py` — event tests updated to walk semantics + NEW: subdir render ·
  `kata.config`-only idle render · no-local-parsing drift pin · frozen-format byte test kept
  green untouched.
- **T6** docs: `adapters/claude/README.md` statusline section (scope-unify + new home);
  BACKLOG item 7 closed; this spec's Acceptance filled; DECISIONS.md D164 (operator scope
  decision + U1 home-move rationale).

## Acceptance (default-FAIL) — MET 2026-07-13

Freeze-gate SHIP → build → full gauntlet green (`tools/scripts/gauntlet.py`) → ONE parent-walk
definition repo-wide (drift test RED if copied back) → `statusline_from_event` carries zero
local payload-cwd parsing (test-pinned) → chain/gauge behavior byte-identical (their existing
tests pass with only path-pin edits) → frozen s1.5 format bytes unchanged → Snyk med+ 0 on
modified files → fresh-context adval → PR → merge.

**Evidence (all same-day):** freeze-gate fresh-context no-write — SHIP-WITH-FIXES, 1 HIGH
(consumer-depth offsets) folded into U2 pre-dispatch · build — one Opus worker (anchor−1,
D131 standard), no-git, no escalations; targeted suites 214 passed · gauntlet —
**pytest 3643 passed / 3 skipped (+4 net new tests) · integration 2/2 · ruff clean ·
validator 48/0/0** · Snyk Code med+ — tools/ **0** · adapters/ **1** = the pre-existing
`.snyk`-accepted statusline_chain CommandInjection false positive (expiry 2027-01-04), nothing
new · fresh-context adval — **SHIP-WITH-FIXES**, 0 code findings, 1 MED process finding (this
very Acceptance block unfilled) folded here; adval independently re-verified the U2 depths
against the filesystem, the drift-test conjunction's RED-on-copy-back, the hermetic walk-cap
math, and the untouched CWE-23 guards.

## Determinism note

Pure relocation + call-site substitution; no gate/score/hash/order code added. The walk itself
is already deterministic (bounded, sorted-independent, OSError⇒None).
