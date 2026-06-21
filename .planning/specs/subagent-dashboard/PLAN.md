---
date: 2026-06-21
spec: subagent-dashboard
status: FROZEN — v1 design locked + partitioned into disjoint slices for an orchestrated foreground-parallel build
intentRef: ./INTENT.md (frozen) · briefRef: ./BRIEF.md
context: Phase 4 self-dogfood of the complete Greater Loop (kata-initiate -> harness -> kata-closeout)
tags: [plan, subagent-dashboard, tui, rich, disjoint-ownership, dogfood, frozen]
---

# subagent-dashboard v1 — frozen DESIGN + PLAN

Build the BRIEF's "separate-terminal dashboard (the real product)" at **v1**: a `rich` TUI that **tails** the
harness's existing files and renders the design target. Two layers, built as two disjoint slices by Sonnet
workers in isolated worktrees → integration gate → fresh-context `kata-evaluate`.

## LOCKED design decisions (v1 — do NOT re-decide)
- **Two layers.** A **pure model** (`kata_dash_model.py`: parse → ViewModel, no `rich`, fully unit-tested) and a
  **render/app** (`kata_dash.py`: `rich` renderables + a `Live` tail loop + CLI). Separation keeps the logic
  testable and the UI thin.
- **Data sources (read-only observer).** `.kata/board.md` (append-only lines per `protocol/board.md`:
  `<utc> | <agent-id> | <TYPE> | <task-id> | <msg>`), `.kata/state.json` (per `protocol/state.md`: `tasks{}`,
  `gate`, `driftLedger`, `wavesDone`, `integrationBranch`, `forkPoint`, `updatedUtc`). **Never writes** either.
- **Stepped bars from task state (v1 — no protocol change).** Map `state.tasks[id]` →
  `assigned 5% · in-progress 50% · blocked 50%(✗) · done 90% · gated 95% · integrated 100%`. (v2 heartbeats →
  smooth bars is DEFERRED — not in this build.)
- **Aesthetic = the BRIEF design target.** `rich` Panel frame; one row per task: marker `▸`, label, a block-bar
  (`▰`/`▱`), percent, a braille spinner (`⠹⠼⠧⠿`) for active tasks / `✓` done / `✗` blocked, status text. Header:
  `KATAHARNESS ⛩ 道 · <spec> · wave w/W · <gate glyph>`. Footer: recent board events + `drift N · escalations N`
  from the driftLedger. A **loop ribbon** `GRILL ▸ FREEZE ▸ EXECUTE ▸ EVALUATE ▸ HANDOFF ▸ IMPROVE` with the live
  phase highlighted (v1 phase = derive from state: tasks present+not all integrated ⇒ EXECUTE; all integrated +
  gate green ⇒ EVALUATE/HANDOFF; default EXECUTE).
- **Graceful + host-agnostic.** Missing/empty `.kata/` ⇒ a calm "⏳ waiting for an orchestrated run…" panel, never
  a crash. Reads files only — identical under any host. Refresh ~4–8 Hz via `rich.Live`.
- **Dependency:** add `rich` to `tools/pyproject.toml` (de-risked: `rich==15.0.0` installs + renderables import
  clean on this platform). No `textual`/`curses` in v1.

## Frozen contract — the ViewModel (both slices build against this)
`kata_dash_model.build_view_model(board_text: str, state: dict | None) -> ViewModel` where (dataclasses):
```
TaskRow:   id:str · label:str · status:str · percent:int · active:bool · blocked:bool · done:bool
ViewModel: spec:str|None · wave:str|None (e.g. "2/4") · phase:str (one of the 6 ribbon phases)
           gate:str|None · tasks:list[TaskRow] · driftEscalations:tuple[int,int]
           events:list[str] (last N formatted board lines) · waiting:bool (no live run) · updatedUtc:str|None
```
`parse_board(text:str) -> list[BoardEvent]` (BoardEvent: utc·agent·type·task·msg) is the public helper.
The render layer consumes a `ViewModel` **duck-typed** (attribute access) so it can be unit-tested with simple
stand-ins; the real `ViewModel` is imported at integration.

## Wave DAG
```
Wave 1 (parallel):  DASH-model ──┐
                    DASH-render ──┘   (disjoint files; render tests use SimpleNamespace ViewModel stand-ins)
Integration:        octopus-merge → uv sync (rich) → pytest (112 + new) → validator 35/0 → smoke-run the CLI
                    on a synthetic .kata/ fixture → fresh-context kata-evaluate
```

---

## Task DASH-model — pure parser + ViewModel
**Owns (disjoint):** `tools/kata_dash_model.py` (NEW), `tools/tests/test_kata_dash_model.py` (NEW).
**read_first:** `protocol/board.md`, `protocol/state.md`, `.planning/specs/subagent-dashboard/{INTENT,BRIEF}.md`.
**action:** Build the pure model (no `rich`, no I/O beyond accepting strings/dicts):
- `parse_board(text) -> list[BoardEvent]` — tolerant line parse (`utc | agent | TYPE | task | msg`); skip blank/
  malformed lines; keep order.
- `status_to_percent(status) -> int` and `build_view_model(board_text, state) -> ViewModel` per the frozen
  contract: derive `tasks` rows from `state["tasks"]` (label = task id unless a board NOTE names it; v1: id is
  fine), `wave` from `len(wavesDone)`+the plan if present (else `None`), `gate` from `state["gate"]`, drift/
  escalations from `state["driftLedger"]`, `events` = last ~6 formatted board lines, `phase` per the locked
  derivation, `waiting=True` when `state is None` and board is empty. Pure dataclasses; deterministic.
**verify (default-FAIL):** `cd tools && uv run pytest tests/test_kata_dash_model.py -q` (TDD: red→green). Cover:
board parse (well-formed + malformed-skipped + order), each status→percent mapping, ViewModel assembly from a
fixture state dict (tasks/gate/drift/phase/wave), the `waiting` path (no state + empty board), events truncation.
**acceptance:** every locked status→percent value is exact; `build_view_model` populates every ViewModel field;
malformed board lines are skipped not crashed; `waiting=True` iff no run data. No `rich` import in this file.
**threat model:** none — pure parsing of the repo's own machine files; no exec, no attacker surface.

## Task DASH-render — rich render + tail app
**Owns (disjoint):** `tools/kata_dash.py` (NEW), `tools/tests/test_kata_dash_render.py` (NEW),
`tools/pyproject.toml` (EDIT — add `rich`), `tools/uv.lock` (regenerated by `uv add`).
**read_first:** `.planning/specs/subagent-dashboard/{INTENT,BRIEF}.md` (the design target ASCII), `protocol/board.md`,
`protocol/state.md`. `rich` usage: `from rich.live import Live; from rich.panel import Panel; from rich.table
import Table; from rich.text import Text; from rich.console import Console`. NOTE: `rich` has no `__version__`.
**action:** `uv add rich` first. Then build:
- **Pure render helpers (unit-tested):** `render_bar(percent:int, width:int=20) -> str` (block chars `▰`/`▱`);
  `spinner_frame(tick:int) -> str` (cycle `⠹⠼⠧⠿`); `render_row_text(task_row, tick) -> str` (marker·label·bar·
  percent·glyph·status — `✓` done / `✗` blocked / spinner active); `render_ribbon(phase) -> str`
  (`GRILL ▸ … ▸ IMPROVE`, live phase highlighted). These take a **duck-typed** ViewModel/TaskRow (attribute
  access) so tests pass `types.SimpleNamespace(...)` — no dependency on DASH-model at unit-test time.
- **rich frame:** `build_frame(view_model, tick) -> rich.console.RenderableType` — the Panel with header
  (`KATAHARNESS ⛩ 道 · spec · wave · gate`), the task Table/rows, the ribbon, and the board-events + drift footer;
  a `waiting` ViewModel ⇒ the calm "⏳ waiting…" panel.
- **tail app + CLI:** `main(argv=None)` — argparse `--kata-dir .kata --refresh 0.15 --once`; read `.kata/board.md`
  + `.kata/state.json` (tolerant of absence), call `kata_dash_model.build_view_model`, render via `rich.Live`
  loop (or a single frame when `--once`). Keep the Live loop THIN (the testable logic is in the helpers/model).
  Reuse the `_safe_path` `..`-guard pattern for `--kata-dir` (consistency with the other CLIs).
**verify (default-FAIL):** `cd tools && uv run pytest tests/test_kata_dash_render.py -q` (TDD red→green). Cover:
`render_bar` (0/50/100% → correct filled/empty counts), `spinner_frame` cycles, `render_row_text` shows `✓` for
done / `✗` for blocked / a spinner for active and contains the label+percent, `render_ribbon` highlights the
given phase, `build_frame` returns a renderable for both a normal and a `waiting` SimpleNamespace ViewModel
without raising. Do NOT unit-test the live loop (glue).
**acceptance:** helpers are pure + tested with SimpleNamespace stand-ins; `--once` renders a single frame from a
real `.kata/` and exits 0; missing `.kata/` ⇒ waiting panel, exit 0 (no crash); `rich` added to pyproject.
**threat model:** reads the repo's own `.kata/` files; `--kata-dir` is operator-supplied → reuse the `..`-guard
(CWE-23 defense-in-depth, consistent with gate_emit/graph_gen). No exec of target code.

## Integration
1. Octopus-merge `dash/model` + `dash/render` → `dash/integration`. `cd tools && uv sync` (pull `rich`).
2. Full gate: `uv run pytest -q` (112 + new) · `uv run python validate_skills.py` (35/0 — no skill changes).
3. **Smoke the real wiring:** write a synthetic `.kata/board.md` + `.kata/state.json` fixture, run
   `uv run python kata_dash.py --kata-dir <fixture> --once` → confirm a rendered frame (a worker row with a bar +
   the ribbon) and exit 0; also run with a missing dir → waiting panel, exit 0.
4. **Snyk** on the two new Python modules → fix→rescan (or document FP per the Phase-0 pattern).
5. **Emit the gate artifacts** via `tools/gate_emit.py` (dogfood F1 again) → `.kata/RESULT.json` + footprint.
6. **Fresh-context `kata-evaluate`** over this PLAN → PASS/NEEDS_WORK. (Then CLOSEOUT: report + understand-map +
   your version-select.) Backout safety: tag `pre-dash` before any merge to master.

## Ownership disjointness
| File | Owner |
|---|---|
| `tools/kata_dash_model.py`, `tools/tests/test_kata_dash_model.py` | DASH-model |
| `tools/kata_dash.py`, `tools/tests/test_kata_dash_render.py`, `tools/pyproject.toml`, `tools/uv.lock` | DASH-render |
| integration RESULT.json, the `.kata/` smoke fixture | Integrator |
No file in two lanes. ✓
