# KataHarness — Claude Code statusLine adapter

Live one-line run-status in Claude Code's own status bar, updated every ~1 second
while an orchestrated kata run is in progress.

## What it is

`adapters/claude/statusline.py` is the **Claude-specific glue layer** for the
agnostic statusline core (`tools/kata_statusline.py`). It reads the Claude
`statusLine` stdin JSON, locates `<cwd>/.kata/`, and prints the frozen one-line
summary:

```
KATAHARNESS 改善型 │ EXECUTE │ ▰▰▰▰▰▱▱▱ 62% │ 3/5 tasks │ gate – │ drift 0
```

When no kata run is active (`.kata/` absent or empty), it prints nothing —
invisible to non-kata projects.

## stdin mechanism

Claude Code invokes the `statusLine` command and writes a JSON object to its stdin.
The relevant fields (per RESEARCH-s1.5.md § Claude stdin contract):

```json
{
  "cwd": "/absolute/path/to/the/project",
  "workspace": { "current_dir": "/absolute/path/to/the/project", "..." : "..." },
  "model": "...",
  "session_id": "...",
  "..."
}
```

The adapter reads `cwd` (falling back to `workspace.current_dir`) and checks whether
`<cwd>/.kata/` exists. If it does, it reads `board.md` + `state.json` and calls
`build_view_model` + `render_statusline` (pure, stdlib-only, < 10 ms).

## Installation

1. Copy the snippet from `settings.snippet.json` into your Claude settings file.
   Claude Code merges three tiers of settings (last writer wins):
   - `~/.claude/settings.json` — user global
   - `.claude/settings.json` — project-level (checked in)
   - `.claude/settings.local.json` — project-local (gitignored)

   For a per-project install (recommended), add to `.claude/settings.local.json`:

   ```json
   {
     "statusLine": {
       "type": "command",
       "command": "python \"/absolute/path/to/kataharness/adapters/claude/statusline.py\"",
       "padding": 1,
       "refreshInterval": 1
     }
   }
   ```

   Replace `/absolute/path/to/kataharness` with the actual absolute path to the
   KataHarness repo on your machine (e.g. `C:/Dev/projects/kataharness` on Windows,
   `/home/user/projects/kataharness` on Linux/macOS).

2. Reload Claude Code (restart or reload window). The status bar will update within
   1 second once a kata run starts writing to `.kata/`.

## Why `refreshInterval: 1`

Claude Code's statusLine is **event-driven** by default (refreshes after each
assistant message, `/compact`, permission changes, etc.). During an orchestrated
kata run, the main Claude session is mostly **idle, waiting on background subagents** —
those events go quiet for minutes at a time.

Setting `refreshInterval: 1` tells Claude to also re-run the command on a 1-second
timer. This gives ~1 s live granularity while subagents are executing.

Source: RESEARCH-s1.5.md § Claude Code — critical finding on `refreshInterval`.

## Invisible-outside-kata behavior

If `<cwd>/.kata/` does not exist, the adapter prints an empty string (Claude renders
nothing). No status bar item appears. This means:

- Non-kata projects see no artifact.
- The adapter is safe to install globally in `~/.claude/settings.json`.

## Fail-soft guarantee

Any exception (missing Python, import error, bad JSON, file permission) causes the
adapter to print nothing and exit 0. Claude never crashes or hangs due to this script.

## Fallbacks for other hosts

| Host | Status | Guidance |
|------|--------|----------|
| **Claude Code** | Live statusLine | This adapter |
| **Codex CLI** | No live surface | Use `kata_dash.py` TUI in a side terminal, or the web viewer (`kata_web.py`) |
| **Kiro** | Deferred | Would need a VS Code `.vsix` extension using `createStatusBarItem()` — not built yet; use `kata_dash.py` TUI or `kata_web.py` meanwhile |
| **Any host** | Universal fallback | `uv run python tools/kata_dash.py --kata-dir .kata` (rich TUI in a side terminal) |

The `kata_dash.py` TUI is the universal terminal fallback that works in any
environment. The `kata_web.py` localhost web viewer (S1.5b) is the host-agnostic
rich fallback for environments where a side terminal is impractical.
