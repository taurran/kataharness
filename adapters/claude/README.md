# KataHarness — Claude Code adapter

Two Claude Code adapter features:

1. **statusLine** — live one-line run-status in Claude Code's status bar, updated
   every ~1 second while an orchestrated kata run is in progress.
2. **PreCompact hook** — auto-checkpoint that commits `.kata/board.md` to
   `refs/kata/trail` before context compaction, closing Gap 1 of restore-hardening.

---

## PreCompact Hook

`adapters/claude/hooks/kata-precompact.py` is a **thin trigger** that fires before
Claude auto-compacts the context window.  It calls `kata_trail.snapshot_board()`
(from `tools/kata_trail.py`) to commit `.kata/board.md` to the orphan ref
`refs/kata/trail` via git plumbing only.

### What the hook does

1. Resolves the repo root from `__file__` (three levels up from `adapters/claude/hooks/`).
2. Imports and calls `kata_trail.snapshot_board(repo_root)`.
3. `snapshot_board` writes a git-plumbing-only snapshot of `.kata/board.md` to
   `refs/kata/trail` — no index touch, no push, no working-tree change.
4. If the snapshot succeeded, prints a JSON line:
   ```json
   {"custom_instructions": "KataHarness trail checkpoint saved ... First action after resuming: invoke the kata-handoff skill ..."}
   ```
   This `custom_instructions` key is intended to nudge the post-compaction resumed
   turn to run `kata-handoff`.  **Durable safety NEVER depends on this nudge** — the
   mechanical commit to `refs/kata/trail` is the guarantee; the nudge is the
   enhancement.
5. If the snapshot is skipped (no board, busy lock, git error, etc.) the hook exits
   silently with exit code 0.  Compaction is never blocked or delayed.

The hook is mid-task-safe because it only snapshots and never reasons — it sidesteps
`kata-selfhandoff`'s "never mid-task" rule entirely (it is not a handoff, it is a
mechanical archive).

### Hook installation

The `hooks` entry in `settings.snippet.json` wires this script:

```json
{
  "hooks": {
    "PreCompact": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"<repo>/tools/.venv/Scripts/python.exe\" \"<repo>/adapters/claude/hooks/kata-precompact.py\""
          }
        ]
      }
    ]
  }
}
```

Replace `<repo>` with the absolute path to the KataHarness repo.  On Windows use
forward slashes or escaped backslashes; on Unix/macOS replace
`tools/.venv/Scripts/python.exe` with `tools/.venv/bin/python`.

**No venv?** The hook only calls `kata_trail.snapshot_board`, which is
**stdlib + `git` subprocess only** (no third-party imports) — so any Python 3.12+
interpreter works.  If the repo venv is absent, point the command at a system
`python3` (or `python`); nothing in the hook path needs the venv's packages.

Merge this into the same settings file as the `statusLine` entry.  All three
settings tiers work (user global, project, project-local).

### Assumptions (flagged for live-proof #2)

**ASSUMPTION — Claude `PreCompact` is a synchronous shell hook with a usable time
budget.**

This assumption must be verified empirically (live-proof #2: fire the hook in a real
session and confirm the board lands on `refs/kata/trail` before compaction
completes).  At build time it cannot be triggered programmatically; the command has
been verified by running the wrapper directly against a temp git repo (see build
report).

The assumption covers two sub-claims:
- **Synchronous:** Claude waits for the hook command to exit before proceeding with
  compaction.  If the hook is fire-and-forget, the git-plumbing commit might race
  with the compaction window.
- **Usable time budget:** `snapshot_board` is fast (< 1 s on a warm git repo for a
  small board.md), but if the PreCompact window is very short (e.g. < 100 ms) the
  hook might be killed before the ref is updated.

**Fallback if the assumption is false:**

If `PreCompact` is NOT a synchronous shell hook with a usable time budget, the hook
still cannot harm anything (it exits 0 unconditionally and never blocks the turn).
However, Gap 1's compaction-window floor would not be closed by this hook.

Gap 2 and Gap 3 still close independently via B1's integration-cadence call site in
`kata-orchestrate` step 5, which fires `snapshot_board` right after each task
integrates.  Only the specific scenario — "board updated mid-wave, compaction fires
before the next integration" — would still be exposed.  For that scenario the
operator would need a different trigger (e.g. a `PostToolUse` hook on a writing
tool, or a timed external cron).  Surface the finding and add a note to
`.planning/DECISIONS.md`; do NOT attempt to fake the guarantee.

---

## statusLine

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
