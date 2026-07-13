# DESIGN — kata-native statusline segment (D160 build; anchors LOCKED in GRILL-LEDGER.md)

**Status:** DRAFT → freeze-gate pending. Executes the D160 decision + the operator-ACCEPTED EV-1
anchor. Model routing this session (operator-directed): build worker = Opus (anchor−1, standard
mode); gates/adval = anchor.

## Locked inputs (not re-decidable — GRILL-LEDGER D1/D2/D3 + EV-1)

- Kata-native segment lives in the EXISTING chain wrapper; **replace-in-kata-scopes**: kata-scoped
  cwd ⇒ kata segment ONLY, child NOT executed; elsewhere ⇒ passthrough byte-identical (CA-L1
  deliberately re-scoped by D160). Kata bridge written on BOTH legs (unchanged).
- **"kata-scoped" = ONE definition** (EV-1): NEW `adapters/claude/kata_scope.py` exporting
  `is_kata_scope(start, *, max_levels=10) -> bool` — behavior-identical extraction of
  `kata-gauge-check.py._is_kata_scope` (`.kata/` dir or `kata.config` file at/above start, bounded
  upward walk, root-stop, OSError ⇒ False). BOTH call sites (the gauge hook + the chain wrapper)
  consume it; a **drift test** pins both call sites to the shared helper (source-scan: no local
  reimplementation of the walk in either consumer).
- No host settings change: the installed statusLine command (the chain invocation) is UNCHANGED —
  the new behavior ships entirely inside `statusline_chain.py`. No reinstall, no consent flow.

## S1 — kata_scope.py (NEW, adapters/claude/)

Pure stdlib module, one public function `is_kata_scope`, docstring citing D160/EV-1 + the F-3
freeze-gate provenance. Import pattern: `statusline_chain.py` (same dir) imports it via a
sibling-path `sys.path` insert mirroring its existing `_write_kata_bridge` tools-path pattern;
`hooks/kata-gauge-check.py` inserts `parents[1]`. Constants (`_SCOPE_WALK_CAP=10`) move here.

## S2 — statusline_chain.py kata leg

In `_main`, after reading stdin: resolve cwd from the payload (`workspace.current_dir`, falling
back to `cwd` key, falling back to `os.getcwd()` — the same precedence the gauge hook family
uses). `is_kata_scope(cwd)` ⇒ render the KATA SEGMENT to stdout and DO NOT run the child; else
existing chain/SKIP legs byte-identical. `_write_kata_bridge` runs on every leg (unchanged).

**Segment format (pinned; deterministic given the same stdin + filesystem state):**
`kata │ {dirname}{meter}{run}` where:
- `kata` literal marker, dim ANSI (`\x1b[2m`), so the operator can tell at a glance which renderer
  owns the line;
- `{dirname}` = basename of the payload cwd, dim;
- `{meter}` = ` {bar} {used}%` — 10-segment bar from the payload's
  `context_window.remaining_percentage` exactly as the kata gauge computes used_pct (raw
  `100 − remaining`, NO GSD-style buffer normalization — kata's own semantics), colored by the
  kata trigger bands: green < 55, yellow < 70, red ≥ 70 (0.70 = the D152 trigger; the meter and
  the gauge directive must agree on the number). `remaining_percentage` absent ⇒ omit the meter.
- `{run}` = ` │ run` (dim) when `.kata/board.md` exists non-empty at/above cwd (the active-run
  hint) else omitted. Cheap check only — never parse the board.
- Fail-soft everywhere: any error in segment rendering ⇒ emit NOTHING (never break the host
  statusline; bridge still written) — same posture as the existing SKIP leg.

## S3 — gauge hook consumes the shared helper

`kata-gauge-check.py` drops its local `_is_kata_scope` + `_SCOPE_WALK_CAP` and imports from
`kata_scope` (path insert `parents[1]`). Behavior byte-identical; its existing tests keep passing
(they may monkeypatch the name — builder adapts imports in tests, not semantics).

## S4 — tests (TDD)

- `test_kata_scope.py` (NEW): the walk semantics (found at cwd / N levels up / cap stops / root
  stop / OSError False) — port the gauge hook's existing scope tests as the base.
- Chain tests (extend the existing statusline_chain test module): kata-scoped stdin ⇒ segment
  rendered, child NOT invoked, bridge written; non-kata ⇒ byte-identical passthrough (pin against
  a golden run of the CURRENT behavior); meter bands; absent remaining_percentage; run-hint
  present/absent; fail-soft (corrupt payload ⇒ empty stdout, exit 0).
- **Drift test**: source-scan asserts both consumers import `kata_scope.is_kata_scope` and neither
  contains a local upward-walk reimplementation.

## S5 — docs

`adapters/claude/README.md`: the statusline section gains the replace-in-kata-scopes behavior +
the D160 pointer; the CA-L1 never-clobber description gains the deliberate re-scope note.
`protocol/exec-safety.md`: NO new row needed (the child-exec sink is unchanged — it just gains a
leg that runs no child); note this in the PR body, not the registry.

## Acceptance

Freeze-gate SHIP → build → tests green (full suite + new) → ruff → validator 48/0/0 → Snyk med+ 0
→ fresh-context adval → PR → merge. **Live smoke** (the segment actually rendering in a kata-cwd
session) rides the SAME next session as F-9/R6 — one repo-cwd session collects all three.
Honesty label until then: built + gated, live-render-unproven.
