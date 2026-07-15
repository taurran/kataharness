---
tags:
  - kata/spec
  - statusline
---

# subagent-monitor — DESIGN (frozen 2026-07-14)

**Status:** FROZEN — freeze-gate SHIP-WITH-FIXES (3 findings: roster rotation · injectable now ·
liveness never-raise — all folded into DESIGN **and** PLAN) · 2026-07-14 · grill:
`GRILL-LEDGER.md` (D1–D5 + EV-1, standard tier, operator present) · INTENT: the frozen root
`INTENT.md` (6 ACs) · instrumented (`inlineEval: telemetry` — calibration row 2 of 3).

## Frame (binding, from the grill)

Claude-only this run (D1: codex parked pending the operator's MindBridge-side alignment import;
kiro later — not installed here). No fabricated signals (D4): live "thinking" state is
unobservable and never rendered; dispatch-time reasoning-effort tier + heartbeat liveness are
the truthful substitutes. The pinned layout (D5, operator-picked):

```
kata │ KataHarness ▰▱▱▱▱▱▱▱▱▱ 9% │ fable │ ⚒ C·opus·H▰ C·opus·H▰ V·son·M▱ │ run
idle: kata │ KataHarness ▰▱▱… 9% │ fable │ run          (crew slot ABSENT)
many: … ⚒ C·opus·H▰ C·opus·H▰ V·son·M▰ +2 │ run          (truncate at 3 chips + "+N")
```

## S1 — core: `tools/kata_crew.py` (pure, agnostic — the portable guarantee)

New module, stdlib-only, Determinism-Doctrine-conformant (injectable `now`, law 7; sorted
iteration, law 2/3; atomic writes via the existing `fs_atomic.atomic_write_text`):

- **Roster schema** — `.kata/dispatch.json`:
  `{"v": 1, "workers": {"<taskId>": {"role": str, "model": str, "effort": "L"|"M"|"H",
  "dispatchedAt": iso, "closedAt": iso|null}}}`. **Single-writer = the conductor.**
- `write_roster_entry(kata_dir, task_id, *, role, model, effort, now=None)` /
  `close_roster_entry(kata_dir, task_id, *, now=None)` — atomic read-modify-write; fail-closed
  on a corrupt existing file (the `record_accepted_defaults` posture — never clobber).
- `read_roster(kata_dir) -> dict` — **fail-soft**: absent/corrupt/non-dict ⇒ `{}` (the
  lenient-read side; a statusline tick never raises).
- `liveness(entry, board_text, task_id, *, now, deadline_minutes) -> bool` — fresh IFF the max
  of `dispatchedAt` and the task's latest board `CLAIM`/`PROGRESS` self-stamp is within
  `deadline_minutes` (reads the board line grammar `<ts> | <agent> | <TYPE> | <task> | <msg>`
  with its OWN lenient parse — **never raises on malformed board content: an unparseable line
  is SKIPPED** (freeze-gate F3 fold; do NOT copy `parse_progress_events`' raise-on-malformed
  posture — that is a gate parser, this is a statusline tick); the board is corroboration —
  absent board ⇒ `dispatchedAt` alone). Display-only; never gates (D3).
- `render_crew(roster, board_text, *, now, deadline_minutes=10) -> str` — the chip run:
  open entries only (`closedAt` null), sorted by `dispatchedAt` then taskId (law 10),
  `<RoleLetter>·<model>·<effort>` + `▰`/`▱`, dim-themed, truncate 3 + `+N`, `""` when empty.
  Role letter = first letter of the role, uppercased (C/V/R/O/E per the `roles` vocabulary).
- `render_model_chip(payload) -> str` — dim shortname from `payload.model.display_name`
  (lowercased first token, e.g. "Fable 5" → `fable`); `""` when absent/malformed (EV-1).

## S2 — claude binding: `adapters/claude/statusline_chain.py`

`_render_segment` composes: `marker │ dirname meter │ <model-chip> │ <crew> │ run` — the model
chip and crew slots each rendered by S1 (lazy tools-import, the existing `_import_kata_gauge`
pattern) and each ABSENT (no separator) when empty. **Injectable clock (freeze-gate F2 fold,
Determinism law 7):** `_kata_leg` and `_render_segment` gain a `now: datetime` parameter (no
default — the `kata_gauge.read_bridge(now_utc=...)` idiom); `_main()` supplies
`datetime.now(timezone.utc)` ONCE at the top; tests call `_render_segment(..., now=<fixed>)`
directly so the composition golden byte-pins. `livenessDeadline` read fail-soft from
`<root>/kata.config` when present, default 10. In-scope render errors keep the D162 contract:
degrade the failing slot only, never blank the segment (v2-F6 lineage).

## S3 — conductor mandate: `kata-orchestrate` prose

The dispatch step gains the roster mandate: write a roster entry at every worker dispatch
(role, resolved model, effort), close it at the task gate. **Run-start rotation (freeze-gate
F1 fold — the D3 LOCKED edge):** the existing "Run-start board hygiene" step extends to
`.kata/dispatch.json` — rotate/clear it alongside `board.md` before the first dispatch, so a
crashed prior run's never-closed entries can never render phantom crew chips (a phantom chip is
a fabricated signal, D4-class). MINOR version bump + validator `--write`. Prose only.

## S4 — tests (the operator's named requirement: layout validation)

- `tools/tests/test_kata_crew.py` — **layout goldens byte-pinning** (fixed injected `now`,
  ANSI included): idle/empty (`""`) · 1 worker · 3 workers · many (+N) · stale chip — plus the
  **EV-1 degrade-golden family**: roster absent · roster corrupt · all-stale · model-chip
  absent-field. Roster API tests: atomic write/close round-trip · corrupt-file fail-closed
  write · fail-soft read · liveness boundary (fresh at deadline−ε, stale at deadline+ε, board
  corroboration wins over dispatchedAt).
- `tools/tests/test_statusline_chain.py` extension — full-segment composition goldens:
  payload+roster fixture ⇒ the pinned D5 layout · **BC golden: no model field + no roster ⇒
  byte-identical to today's D162 segment** (the pre-build render is the frozen reference).

## S5 — instrumentation + live smoke (conductor)

`inlineEval: telemetry` rides from the E3 run's kata.config (same branch-root config, target
self). Workers carry the checkpoint mandate; the conductor materializes records + appends
calibration row 2 (`subagent-monitor-2026-07-14`). **AC4 live smoke:** after integration, pipe
a real payload + a roster fixture through the installed chain command and observe the pinned
layout on this machine.

## Out of scope (recorded, not drift)

Codex binding/research (D1 — parked for the MindBridge alignment import) · kiro anything (not
installed; smoke impossible here — named deferral) · any live-thinking signal (D4) · roster
writes by workers (single-writer stays the conductor) · gauge-hook changes.

## Acceptance

= frozen INTENT.md AC1–AC6. Gate chain: freeze-gate → dual-control → build (workers in
worktrees, checkpoint mandate) → per-task gates → gauntlet + Snyk (when-available) →
fresh-context adval → live smoke → PR → merge → closeout.
