---
tags:
  - kata/plan
  - statusline
tasks:
  - id: T1
    title: "Core: kata_crew.py (roster + chip renderer) + layout/degrade goldens"
    owns:
      - tools/kata_crew.py
      - tools/tests/test_kata_crew.py
    wave: 1
    estimate: 25
    verify: "cd tools && uv run pytest tests/test_kata_crew.py -q"
  - id: T2
    title: "Claude binding: chain-wrapper composition + full-segment goldens (incl. the BC golden)"
    owns:
      - adapters/claude/statusline_chain.py
      - tools/tests/test_statusline_chain.py
    wave: 2
    estimate: 20
    verify: "cd tools && uv run pytest tests/test_statusline_chain.py -q"
  - id: T3
    title: "Conductor mandate: kata-orchestrate dispatch-roster prose + bump"
    owns:
      - skills/coordinate/kata-orchestrate/SKILL.md
    wave: 2
    estimate: 10
    verify: "cd tools && uv run python validate_skills.py"
---

# PLAN — subagent-monitor (frozen 2026-07-14; executes the sibling DESIGN.md S1–S5)

Integration branch `feat/subagent-monitor`; conductor = sole main-tree git writer; workers in
isolated worktrees with the checkpoint-commit + `Kata-Checkpoint:` trailer mandate (inlineEval
telemetry). Wave 1: T1. Wave 2: T2 ∥ T3 (zero file overlap; T2 depends on T1's API names —
workers merge the integration branch first).

## T1 (wave 1) — core

DESIGN S1 exactly, TDD (goldens first, red). The golden values are authored BY the builder from
the frozen D5 layout and then byte-pinned — fixed injected `now`, real ANSI bytes, no
environment dependence (Determinism laws 2/3/7/10; atomic writes via `fs_atomic`). Required
tests: the five layout goldens (empty/1/3/many+N/stale) · the four EV-1 degrade goldens
(roster-absent · roster-corrupt · all-stale · model-field-absent ⇒ `""` model chip) · roster
write/close round-trip (atomic; corrupt-existing ⇒ fail-closed write, byte-unchanged file) ·
fail-soft read (absent/corrupt/non-dict ⇒ `{}`) · liveness boundary fresh/stale ±ε · board
corroboration beats `dispatchedAt` · **liveness() never raises on malformed/garbage
`board_text` — unparseable lines are skipped (freeze-gate F3; own lenient parse, never
`parse_progress_events`' raising posture)**. No edits outside the two owned files.

## T2 (wave 2, after T1) — claude binding

DESIGN S2 exactly: `_render_segment` composes model chip + crew via lazy tools-import of
`kata_crew` (mirror `_import_kata_gauge`); empty slot ⇒ no separator; `livenessDeadline`
fail-soft from `<root>/kata.config`, default 10; per-slot degrade (v2-F6 lineage — a failing
crew read never blanks the gauge); **`_kata_leg` + `_render_segment` gain a required
`now: datetime` parameter, `_main()` supplies `datetime.now(timezone.utc)` once (freeze-gate
F2, law 7 — the composition golden calls `_render_segment(..., now=<fixed>)` and byte-pins)**. Tests appended to `test_statusline_chain.py` (existing tests
untouched): composition golden (payload + roster fixture ⇒ the pinned D5 layout, byte-exact) ·
**BC golden: payload without `model` + no roster ⇒ byte-identical to the CURRENT (pre-build)
segment render — capture the reference bytes from the pre-edit code path FIRST** · kata-leg
behavior outside kata scope unchanged (existing drift/leg tests stay green untouched).

## T3 (wave 2, ∥ T2) — conductor mandate (prose)

DESIGN S3: the kata-orchestrate dispatch step gains the roster mandate (write entry at dispatch
with role + D131-resolved model + effort; close at the task gate; single-writer = conductor;
display-only, never gates) **AND the run-start hygiene step extends to rotate/clear
`.kata/dispatch.json` alongside `board.md` before the first dispatch (freeze-gate F1 — the D3
LOCKED edge; phantom chips from a dead run are a D4-class fabricated signal)**. MINOR version bump; validator `--write` for the README index sync
(the T3-of-last-run precedent: index lines are a sanctioned mechanical touch). Prose only.

## Integration + gates (conductor)

T1 → gate → T2 ∥ T3 → gate each → integrate → telemetry materialization (records + calibration
row `subagent-monitor-2026-07-14` with REAL top-level aggregates — the E3 adval HIGH-1 lesson)
→ full gauntlet + Snyk (when-available, tools/ + adapters/) → **AC4 live smoke** (real payload +
roster fixture through the installed chain command on this machine) → fresh-context adval → PR
→ operator merge gate → closeout. Per-task gate: verify green + owned-scope respected + no
re-planning (escalate). Estimates feed `resolve_estimate`; checkpoints carry `verify.owned` =
the task verify exit.
