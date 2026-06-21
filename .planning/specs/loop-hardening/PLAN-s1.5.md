---
date: 2026-06-21
spec: loop-hardening
sprint: S1.5 — status-surface adapters (agnostic-via-adapters, applied to OUTPUT)
status: FROZEN — partitions S1.5 into disjoint slices for an orchestrated foreground-parallel build
roadmapRef: ./ROADMAP.md · researchRef: ./RESEARCH-s1.5.md · baseline: S1 green (c94dbcf)
closes: G7 (viewer not seamless per-platform)
tags: [plan, loop-hardening, sprint-s1.5, adapters, statusline, claude, web-viewer, frozen]
---

# S1.5 — status-surface adapters · frozen PLAN

Make the live view **seamless into the platform it runs on**. Grounded by `RESEARCH-s1.5.md`: **Claude Code** can
show a live one-line statusline (`statusLine` cmd + `refreshInterval:1`, reads `<cwd>/.kata/`); **Codex** has no
live in-TUI surface (fallback to the viewer); **Kiro** needs a `.vsix` extension (deferred). So this sprint builds
(1) the **Claude statusline adapter** — seeding the `adapters/` layer with its first concrete member — and (2) a
**host-agnostic localhost web viewer** as the universal rich fallback. Two disjoint slices, Sonnet workers in
isolated worktrees → integration gate → fresh-context `kata-evaluate`. **After S1.5: STOP for the operator demo.**

## LOCKED decisions (do NOT re-decide)
- **PULL, not push.** Both surfaces are pull consumers that reuse the existing pure layer
  `kata_dash_model.build_view_model(board_text, state)`. **No push `StatusSink` interface** (research dropped it as
  unnecessary for file-pollable surfaces). **No wiring into `kata-loop`/`kata-orchestrate`** — the run already emits
  telemetry via `kata_board`. Neither slice edits `kata_dash_model.py` (import-only; read-only reuse).
- **Agnostic core vs adapter split (spine #3):** the **agnostic one-line projection lives in the core**
  (`tools/kata_statusline.py`, no `rich`, no tool deps); the **Claude-specific glue lives in the adapter**
  (`adapters/claude/`). The web viewer is host-agnostic core (`tools/kata_web.py`).
- **FROZEN statusline format** (`render_statusline(view_model) -> str`, plain text, no ANSI — degrade-safe + testable):
  - waiting ⇒ `KATAHARNESS 改善型 │ ⏳ idle — no active run`
  - else ⇒ `KATAHARNESS 改善型 │ <phase> │ <bar> <pct>% │ <done>/<total> tasks │ gate <gate|–> │ drift <d>`
    where `bar` = 8-wide `▰`/`▱` with `filled = clamp(round(pct/100*8))`; `pct = round(mean(task.percent))` over
    tasks (0 if none); `done = count(t.done)`; `total = len(tasks)`; `gate = view_model.gate or "–"`;
    `d = view_model.driftEscalations[0]`. Separator is ` │ ` (U+2502). Reuses the `▰▱` motif from `kata_dash`.
- **Adapter is invisible outside a kata run:** `adapters/claude/statusline.py` reads the Claude stdin JSON, takes
  `cwd` (fallback `workspace.current_dir`); if `<cwd>/.kata/` **does not exist ⇒ print nothing** (blank line, so
  non-kata projects show no bar); if it exists ⇒ print `build_statusline(<cwd>/.kata)`. **Fail-soft: ANY exception ⇒
  print nothing** (never crash or hang Claude's statusline). Fast: plain file reads only, no git/subprocess.
- **Claude config is `refreshInterval: 1`** (research: event triggers go quiet while a coordinator waits on
  subagents; the timer is what makes it tick ~1 s during an orchestrated run). Shipped as a documented snippet, not
  auto-installed.
- **Web viewer is localhost-only + framework-free:** stdlib `http.server` **bound to `127.0.0.1`** (never
  `0.0.0.0`); two routes only — `/` serves an embedded HTML/JS page, `/api/view` serves the ViewModel as JSON; the
  page polls `/api/view` every **1000 ms** via `fetch`. No disk file-serving over HTTP (no HTTP path-traversal
  surface). Renders the same motifs (改善型 title, per-task `▰▱` bars, loop ribbon, board feed, gate/drift).
- **BC preserved:** the existing `kata_dash.py` TUI is unchanged and remains the universal terminal fallback.
  Codex/Kiro get **documented** fallbacks (no fake bars).

## Wave DAG
```
Wave 1 (parallel):  S1.5a statusline (core render + Claude adapter) ──┐
                    S1.5b localhost web viewer ───────────────────────┘  (disjoint files; both import the
Integration:        octopus-merge → uv sync → pytest + validator 35/0 + Snyk    already-merged build_view_model)
                    → gate_emit RESULT.json → fresh-context kata-evaluate → operator demo
```

## Task S1.5a — statusline core + Claude adapter (seeds `adapters/`)
**Owns (disjoint):**
`tools/kata_statusline.py` (NEW), `tools/tests/test_kata_statusline.py` (NEW),
`adapters/claude/statusline.py` (NEW), `adapters/claude/README.md` (NEW),
`adapters/claude/settings.snippet.json` (NEW).
**read_first:** `RESEARCH-s1.5.md` (the Claude stdin contract + refresh finding), `tools/kata_dash_model.py`
(the `ViewModel`/`TaskRow` shape + `build_view_model`), `tools/kata_dash.py` (`render_bar` motif + `_safe_path` +
the fail-soft/lazy-import patterns), this PLAN's LOCKED section.
**action:**
- **`tools/kata_statusline.py`** (pure core, **no `rich`**, stdlib only):
  - `render_statusline(view_model) -> str` — exactly the FROZEN format above (duck-typed `view_model`, like the
    `kata_dash` render helpers). Own tiny 2-line `▰▱` bar helper (do NOT import `kata_dash`/`rich`).
  - `build_statusline(kata_dir) -> str` — read `<kata_dir>/board.md` (text, "" if absent) + `state.json` (dict or
    None if absent/bad JSON) → `kata_dash_model.build_view_model(...)` → `render_statusline(...)`. `_safe_path`
    `..`-guard (mirror `kata_dash`). Lazy-import `kata_dash_model` so import never hard-fails.
  - `statusline_from_event(stdin_text: str) -> str` — parse the Claude stdin JSON; `cwd = data.get("cwd") or
    data.get("workspace",{}).get("current_dir")`; if no cwd OR `Path(cwd)/".kata"` absent ⇒ return `""`; else
    return `build_statusline(Path(cwd)/".kata")`. Wrap the whole body so ANY exception ⇒ return `""`.
- **`adapters/claude/statusline.py`** (thin glue, integration-smoked only, like `kata_dash.main`): add the repo
  `tools/` dir to `sys.path` via `Path(__file__).resolve().parents[2] / "tools"`; read all of `sys.stdin`; print
  `kata_statusline.statusline_from_event(text)`; `try/except` around everything ⇒ print nothing on failure. UTF-8
  reconfigure like `kata_dash` (degrade-safe glyphs).
- **`adapters/claude/settings.snippet.json`**: `{ "statusLine": { "type": "command", "command": "python
  \"<repo>/adapters/claude/statusline.py\"", "padding": 1, "refreshInterval": 1 } }` (with a `<repo>` placeholder
  note).
- **`adapters/claude/README.md`**: what it is, the stdin-`cwd` mechanism, how to install the snippet into
  `.claude/settings.json` (or `settings.local.json`), the `refreshInterval:1` rationale (cite RESEARCH-s1.5), the
  invisible-outside-kata behavior, and the Codex/Kiro fallback note (Codex → web viewer/TUI; Kiro → `.vsix` later).
**verify (default-FAIL):** `cd tools && uv run pytest tests/test_kata_statusline.py -q` (TDD red→green). Cover:
the FROZEN format for a populated VM (phase, 8-wide bar, mean pct, done/total, gate, drift); the waiting/idle line;
`build_statusline` over a temp `.kata` with a board+state; `statusline_from_event` returns `""` when cwd missing,
`""` when `<cwd>/.kata` absent, and the rendered line when present; a malformed stdin JSON ⇒ `""` (fail-soft);
`..`-guard rejects traversal. Full suite + `validate_skills.py` 35/0 stay green.
**acceptance:** piping a Claude-shaped JSON (`{"cwd": "<tmp>"}`, with `<tmp>/.kata/{board.md,state.json}` present)
through `statusline_from_event` yields the one-line `改善型 …` summary; absent `.kata` ⇒ empty; the README+snippet
let an operator wire it into Claude.
**threat model:** reads only under the stdin-supplied `cwd`/`.kata` (`..`-guard); no exec, no network; fail-soft.
New Python ⇒ Snyk at the gate.

## Task S1.5b — localhost web viewer (host-agnostic universal fallback)
**Owns (disjoint):** `tools/kata_web.py` (NEW), `tools/tests/test_kata_web.py` (NEW).
**read_first:** `tools/kata_dash_model.py` (`ViewModel`/`TaskRow` + `build_view_model`), `tools/kata_dash.py`
(the motifs to mirror in HTML + `_safe_path`), this PLAN's LOCKED section.
**action:** Build `tools/kata_web.py` (**stdlib only** — `http.server`, `json`, `argparse`, `pathlib`):
- `view_to_dict(view_model) -> dict` (pure) — JSON-serialize the ViewModel: `spec, wave, phase, gate, waiting,
  updatedUtc, driftEscalations (as [d,e]), events (list[str])`, and `tasks` as a list of
  `{id,label,status,percent,active,blocked,done,progressLabel}`.
- `build_web_view(kata_dir) -> dict` — read board+state from `kata_dir` (same reader shape as S1.5a/kata_dash),
  `build_view_model`, `view_to_dict`. `_safe_path` `..`-guard.
- `PAGE_HTML` constant — a single self-contained HTML page (inline CSS+JS, no CDN/framework): title
  **`KATAHARNESS 改善型`**, a task list with `▰▱` bars + percent + status + progressLabel, the 6-phase loop ribbon
  with the active phase highlighted, a board-events feed, and gate/drift. Plain JS `fetch('/api/view')` every
  **1000 ms**, re-render; show an idle state when `waiting`.
- `Handler(BaseHTTPRequestHandler)` — `GET /` ⇒ `PAGE_HTML` (text/html); `GET /api/view` ⇒
  `json.dumps(build_web_view(self.kata_dir))` (application/json); anything else ⇒ 404. Silence the default logging.
- `main(argv=None)` — `--kata-dir` (default `.kata`, `_safe_path`), `--port` (default `8765`); `ThreadingHTTPServer`
  **bound to `127.0.0.1`**; print the `http://127.0.0.1:<port>` URL; serve forever. (Thin glue — not unit-tested.)
**verify (default-FAIL):** `cd tools && uv run pytest tests/test_kata_web.py -q` (red→green). Cover: `view_to_dict`
shape for a populated VM (incl. tasks list of dicts + driftEscalations as `[d,e]`); `build_web_view` over a temp
`.kata` with a board+state returns the expected phase/tasks; `build_web_view` over an empty/absent dir returns
`waiting: true`; `PAGE_HTML` contains `改善型` and the `1000` poll interval and `/api/view`; `_safe_path` rejects
traversal. (Optionally bind a server to port 0 and do one `/api/view` request — keep it hermetic/skippable.) Full
suite + validator stay green.
**acceptance:** running `uv run python tools/kata_web.py --kata-dir .kata` serves a page at `127.0.0.1:8765` that
live-updates every second from `.kata/` with bars/ribbon/board/gate; over a demo replay it animates.
**threat model:** binds **127.0.0.1 only** (never 0.0.0.0); serves two routes; HTML is embedded (no disk
file-serving over HTTP, no HTTP path-traversal); `--kata-dir` `..`-guarded. New Python ⇒ Snyk at the gate.

## Integration + the demo (the boundary artifact)
1. Octopus-merge `s1.5/statusline` + `s1.5/web` off master → `s1.5/integration`. `cd tools && uv sync` (no new deps).
2. Full gate: `uv run pytest -q` (268 + new) · `uv run python validate_skills.py` (35/0 — no new skills, no change) ·
   `mcp__Snyk__snyk_code_scan` on the new Python (fix real issues; bind-127.0.0.1 + `..`-guards are the controls;
   any residual CWE-23 on operator CLI/stdin args = the documented FP class, see `SECURITY-phase0.md`). Emit
   `.kata/RESULT.json` via `tools/gate_emit.py`.
3. **Fresh-context `kata-evaluate`** — a SEPARATE no-write Sonnet subagent, 8-rubric, default-FAIL, runs the gate
   itself. **No self-certification (L8).** Must return PASS.
4. **Prep the operator demo (two ways to watch):**
   - **Statusline:** show the exact `.claude/settings.json` snippet; drive a `kata_dash_demo` replay against `.kata/`
     and confirm the statusline command, given `{"cwd":"<repo>"}`, prints an advancing `改善型 … <bar> <pct>%` line.
     (Capture 2–3 line snapshots early/mid/done in the REPORT.)
   - **Web viewer:** `uv run python tools/kata_web.py --kata-dir demo.kata` in one terminal + `kata_dash_demo`
     animating `demo.kata` in another ⇒ open `127.0.0.1:8765` and watch bars advance. (Capture a snapshot/notes.)
5. Merge to master only on the operator's S1.5 boundary nod (this sprint **stops for the demo**). Then checkpoint
   STATE/HANDOFF/ROADMAP, push, clean up worktrees+branches. Backout: tag `pre-s1.5` before the build.

## Ownership disjointness
| File | Owner |
|---|---|
| `tools/kata_statusline.py`, `tools/tests/test_kata_statusline.py`, `adapters/claude/statusline.py`, `adapters/claude/README.md`, `adapters/claude/settings.snippet.json` | S1.5a |
| `tools/kata_web.py`, `tools/tests/test_kata_web.py` | S1.5b |
| integration RESULT.json, STATE/HANDOFF/ROADMAP checkpoint | Integrator |
No file in two lanes. Neither lane edits `kata_dash_model.py` (import-only). ✓
