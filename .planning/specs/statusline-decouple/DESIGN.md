# DESIGN — kata-native statusline segment (D160 build; anchors LOCKED in GRILL-LEDGER.md)

**Status:** **FROZEN (D162)** — freeze-gate v1 HOLD (3 HIGH / 1 MED / 3 LOW, folded) → re-gate v2
SHIP-WITH-FIXES (1 MED / 5 LOW, folded).
Executes the D160 decision + the operator-ACCEPTED EV-1 anchor. Model routing this session
(operator-directed): build worker = Opus (anchor−1, standard mode); gates/adval = anchor.
No SKILL.md is touched ⇒ no bump-on-modify / validator-content impact (G7e).

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

## S1 — kata_scope.py (NEW, adapters/claude/) — THE one walk, start-to-root (G1/G2 folds)

Pure stdlib module, docstring citing D160/EV-1 + F-3 provenance. Public surface:
- `find_kata_root(start: Path, *, max_levels=10) -> Path | None` — the ONE bounded upward walk
  (first ancestor carrying `.kata/` dir or `kata.config` file; root-stop; OSError ⇒ None).
- `is_kata_scope(start: Path, *, max_levels=10) -> bool` = `find_kata_root(...) is not None`
  (kwarg forwarded — one signature everywhere, v2-F5).
- `resolve_start(payload: dict) -> Path | None` — the ONE payload→start-path resolution:
  `cwd` first, `workspace.current_dir` fallback (the repo-wide convention, pinned by
  test_kata_statusline "cwd wins"); non-string/empty ⇒ **None — NO `os.getcwd()` fallback here**
  (that posture belongs to the hook caller, never to a replace-decision). **Normalization lives
  here too (v2-F2): the returned path is `.resolve()`d; a resolution OSError ⇒ None.**
Constants (`_SCOPE_WALK_CAP=10`) move here. Import pattern: `statusline_chain.py` (same dir)
sibling-path insert mirroring its `_write_kata_bridge` pattern; `hooks/kata-gauge-check.py`
inserts `parents[1]` (verified: hooks run from repo paths per settings.snippet.json).

## S2 — statusline_chain.py kata leg

In `_main`, after reading stdin: `start = kata_scope.resolve_start(payload)`. **The kata leg fires
ONLY when `start` is a well-formed path AND `find_kata_root(start)` returns a root** (G3 fold):
render the KATA SEGMENT to stdout and DO NOT run the child. Unparseable stdin, absent/malformed
cwd, or no kata root ⇒ the EXISTING chain/SKIP legs byte-identical (today an eligible child runs
even on garbage stdin — that stays true; the pinned garbage-stdin test keeps passing).
`_write_kata_bridge` runs on every leg (unchanged). The gauge hook keeps ITS `os.getcwd()`
fallback (hook-appropriate posture) — only the start-string resolution + walk are shared.

**Segment format (pinned; deterministic given the same stdin + filesystem state):**
`kata │ {dirname}{meter}{run}` where:
- `kata` literal marker, dim ANSI (`\x1b[2m`), so the operator can tell at a glance which renderer
  owns the line;
- `{dirname}` = basename of the payload cwd, dim, **with C0/C1 control characters stripped**
  (terminal-escape injection via a hostile directory name — G7d fold);
- `{meter}` = ` {bar} {used}%` — 10-segment bar from the payload's
  `context_window.remaining_percentage`, used_pct = raw `100 − remaining` (verified: exactly what
  `write_bridge` records — kata's own semantics, NO GSD-style buffer normalization). Colors:
  **red boundary DERIVED by import from `kata_gauge.DEFAULT_TRIGGER_FRACTION * 100`** (structural
  agreement with the D152 directive — never a literal 70); yellow from 55, a NEW display-only
  `[TUNABLE]` pre-warning band (G4 fold: 55 is NOT a kata semantic, it is introduced here); green
  below. **Bands evaluate the ROUNDED displayed value** so color and printed % always agree.
  `remaining_percentage` **absent OR non-numeric (mirror `write_bridge`'s `_is_number`) ⇒ omit
  the meter only** — never blank the whole segment for a malformed meter field (v2-F6).
- `{run}` = ` │ run` (dim) when `(root / ".kata" / "board.md")` exists non-empty — `root` being
  the value the ONE `find_kata_root` call in this leg already returned (v2-F6 wording: one call,
  reuse its result; no second walk, no second invocation); else omitted. Cheap existence+size
  check only — never parse the board.
- Fail-soft: an error INSIDE kata-leg rendering ⇒ emit NOTHING, exit 0 (bridge still written).
  Corrupt/absent payload never reaches the kata leg — it takes the existing legs (S2, G3 fold).

## S3 — gauge hook consumes the shared helper

`kata-gauge-check.py` drops its local `_is_kata_scope` + `_SCOPE_WALK_CAP` **and its local
payload-cwd parsing**: start resolution becomes
`kata_scope.resolve_start(payload) or Path(os.getcwd())` — the hook's getcwd posture WRAPS the
shared helper's None; the hook contains NO local payload-cwd parsing (v2-F1, drift-test-pinned).
Near-identical behavior, THREE named deltas stated honestly (sweep finding 5 added b/c): (a) the
hook gains the `workspace.current_dir` fallback it lacked (practically inert — hook events don't
carry `workspace`); (b) the getcwd fallback branch is no longer `.resolve()`d (the old code
resolved both branches); (c) a payload cwd whose resolution errors now falls through to the
getcwd posture instead of raising into the top-level fail-soft. All three match the frozen
wording (`resolve_start(payload) or Path(os.getcwd())`) and none changes a gate outcome.
Existing tests keep passing (builder adapts imports in tests, not semantics).

## S4 — tests (TDD)

- `test_kata_scope.py` (NEW): find_kata_root/is_kata_scope walk semantics (found at cwd / N levels
  up / cap stops / root stop / OSError None) — port the gauge hook's existing scope tests as the
  base — plus resolve_start precedence (cwd wins over workspace.current_dir; non-string/empty ⇒
  None; NO getcwd fallback).
- Chain tests (extend the existing statusline_chain test module): kata-scoped stdin ⇒ segment
  rendered, child NOT invoked, bridge written; non-kata ⇒ byte-identical passthrough via a
  **golden fixture** (G6 fold: fixed stub child + fixed stdin ⇒ COMMITTED expected stdout bytes,
  asserted for BOTH the CHAIN and SKIP legs); garbage-stdin ⇒ existing-leg behavior unchanged
  (the pinned test stays green); meter bands incl. the rounded-value boundary; absent
  remaining_percentage; run-hint present/absent at the scope root; control-char-stripped dirname;
  kata-leg-internal error ⇒ empty stdout exit 0.
- **Drift test (G2-sharpened, v2-F4 conjunctive)**: source-scan asserts the upward-walk logic —
  defined as a parent-loop AND evidence literals (`.kata`/`kata.config`) **in the same function**
  — exists ONLY in `kata_scope.py` (a bare `.kata` literal elsewhere, e.g. the run-hint's path
  join, is fine); both consumers import from it; **and neither consumer carries local payload-cwd
  parsing** (v2-F1 — the hook's start line must be the `resolve_start(...) or getcwd` wrap).
- **Fixture hermeticity (v2-F3):** the golden fixture's stdin cwd is a guaranteed-non-kata pytest
  `tmp_path` injected into the payload (golden stdout stays byte-fixed — the stub ignores stdin);
  the two EXISTING chain-leg tests using the literal `/tmp/whatever` cwd get the same treatment
  (a stray `.kata` on any machine's `/tmp` must not flip them onto the kata leg).

## S5 — docs

`adapters/claude/README.md`: the statusline section gains the replace-in-kata-scopes behavior +
the D160 pointer; the CA-L1 never-clobber description gains the deliberate re-scope note.
`statusline_chain.py` module docstring: the unconditional "print the child's stdout
byte-identical" claim gains the kata-leg carve-out (G7c). `protocol/exec-safety.md`: no NEW row,
but the existing statusline_chain row's leg narration gains ONE line for the
eligible-but-not-executed kata leg (G7b — cheaper than a stale registry).
**Out of scope (G5, recorded):** the fresh-profile renderer `adapters/claude/statusline.py`
(`statusline_from_event`) is a THIRD scope check + second kata renderer — NOT touched by this
build (D1/D2 lock only the chain wrapper); unifying it onto `kata_scope` is a named BACKLOG
follow-up added in this PR.

## Acceptance

Freeze-gate SHIP → build → tests green (full suite + new) → ruff → validator 48/0/0 → Snyk med+ 0
→ fresh-context adval → **BACKLOG queue item 3 build-item closed + G5 follow-up item added**
(G7a) → PR → merge. **Live smoke** (the segment actually rendering in a kata-cwd session) rides
the SAME next session as F-9/R6 — one repo-cwd session collects all three. Honesty label:
**LIVE (n=1, 2026-07-13)** — first repo-cwd session after the merge, three citations:
(1) operator visually confirmed the segment (`kata │ KataHarness ▰▱▱▱▱▱▱▱▱▱ 10% │ run`) in the
live statusline, GSD child replaced in-kata-scope as designed; (2) the session's live bridge
`%TEMP%/kata-ctx-f165e776-0d92-450e-af52-e6725e2d400e.json` written by the host-invoked chain
from the repo cwd during the same session; (3) deterministic repro — the exact `settings.json`
chain command fed a repo-cwd payload rendered the kata segment byte-stable with the child not
run. *(Label history: built + gated, live-render-unproven from merge 2026-07-12c until this
observation.)*
