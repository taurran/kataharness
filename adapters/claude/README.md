# KataHarness — Claude Code adapter

Claude Code adapter features:

1. **statusLine** — live one-line run-status in Claude Code's status bar, updated
   every ~1 second while an orchestrated kata run is in progress. It also writes the
   context-usage **bridge file** that feeds the context-autonomy gauge (CA-L1/CA-L2).
2. **statusLine chaining wrapper** — when the operator ALREADY has a `statusLine`
   command, kata **never clobbers** it: it offers a wrapper that runs the user's
   command as a child and writes kata's own sibling bridge (CA-L1). **In kata-scoped
   cwds the wrapper renders kata's OWN segment instead and does NOT run the child**
   (D160 replace-in-kata-scopes — kata renders kata state in kata scopes, the operator's
   statusline owns everywhere else).
3. **PreCompact hook** — auto-checkpoint that commits `.kata/board.md` to
   `refs/kata/trail` before context compaction, closing Gap 1 of restore-hardening;
   additively surfaces `.planning/HANDOFF.md` freshness (CA-L17).
4. **SessionStart(compact) hook** — re-anchors a post-compaction / respawned session
   on the newest `.planning/HANDOFF.md` (CA-L18).
5. **UserPromptSubmit gauge-check hook** — mechanizes the conductor's 0.70
   context-gauge check on every user turn (CG-L1/D152); kata-scope-gated, deduped,
   structurally never-exit-2. Deployed (with the other hooks) via
   `kata_install.py --install-hooks`.

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

## SessionStart(compact) hook

`adapters/claude/hooks/kata-sessionstart.py` fires when Claude Code starts a session
from a **compaction** or **resume** boundary (`source` is `compact` or `resume`). It
emits `hookSpecificOutput.additionalContext` (CA-L18) — a re-anchor instruction pointing
the fresh session at the newest `.planning/HANDOFF.md`, telling it to apply the handoff
**staleness rule** (protocol/handoff.md) and rebuild via the kata-orient 3-tier load. When
no `HANDOFF.md` exists, the injected context says so and points at a kata-orient full
rebuild. It is fail-soft (any exception ⇒ silent exit 0) and never blocks.

### Hook installation

The `SessionStart` entry in `settings.snippet.json` wires this script with the
`compact|resume` matcher:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "compact|resume",
        "hooks": [
          {
            "type": "command",
            "command": "\"<repo>/tools/.venv/Scripts/python.exe\" \"<repo>/adapters/claude/hooks/kata-sessionstart.py\""
          }
        ]
      }
    ]
  }
}
```

Same `<repo>` / venv substitution rules as the PreCompact entry above. The hook is
stdlib-only, so any Python 3.12+ interpreter works.

---

## UserPromptSubmit gauge-check hook (CG-L1)

`adapters/claude/hooks/kata-gauge-check.py` fires on **every user prompt** and makes the
conductor's 0.70 context-gauge check machinery instead of prose (D152; fixes audit
C-1/C-2). It reads the kata statusline **bridge** (`tempfile.gettempdir()/kata-ctx-<session_id>.json`
— the writer's exact resolution, never a raw `%TEMP%` env read), evaluates the existing
tested gauge engine (`kata_gauge.resolve_gauge` → `trigger_crossed`), and when the
trigger fraction is crossed injects a one-line `[KATA CONTEXT GAUGE]` directive telling
the conductor its context fraction and to execute `kata-selfhandoff` at the next task
boundary.

Behavioral contract (mirrored from the hook's docstring — DESIGN CG-L1, FROZEN 2026-07-12):

- **Kata-scope gate (F-3, mandatory, first).** Inject ONLY when the stdin `cwd` shows
  kata-run evidence — a `.kata/` dir or `kata.config` file at or above cwd (bounded
  upward walk, 10 levels, stops at the filesystem root). A global hook must not push
  kata directives into non-kata sessions; outside kata scope it prints nothing.
- **Once-per-crossing dedupe (F-3).** A sidecar `kata-gauge-notified-<session_id>.json`
  (same temp dir, atomic temp+`os.replace` writes) records the last-notified fraction;
  it re-notifies only when the fraction has grown ≥ 0.05 since the last notification.
  A corrupt sidecar is treated as absent (notify rather than never-notify).
- **Never exit 2 (F-8, structural).** A UserPromptSubmit exit 2 **blocks and erases the
  user's prompt**, so the entire body runs under one try/except and the process always
  exits 0 — below-threshold, absent/stale/corrupt bridge, unsafe `session_id`, or ANY
  failure ⇒ silent no-op (one stderr breadcrumb on exceptions).

### Grounding — UserPromptSubmit (GROUNDED-BY-PATTERN, pending live smoke)

The SessionStart hook's `hookSpecificOutput.additionalContext` injection is the
**CONFIRMED** mechanism (GROUNDING-CLAUDE.md G2, official hooks docs). This hook reuses
the same output shape with `hookEventName: "UserPromptSubmit"`, and reads the same
documented stdin fields the other hooks receive (`session_id`, `cwd`). Status:
**GROUNDED-BY-PATTERN** — the stdin fields + `additionalContext` mechanism for the
UserPromptSubmit event specifically are inferred from the documented hook-event pattern
and the unit/integration suite (`tools/tests/test_kata_gauge_check.py`), pending the
live smoke scheduled this session (freeze-gate F-9). Not yet marked CONFIRMED.

### Hook installation

The `UserPromptSubmit` entry in `settings.snippet.json` wires this script:

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"<repo>/tools/.venv/Scripts/python.exe\" \"<repo>/adapters/claude/hooks/kata-gauge-check.py\""
          }
        ]
      }
    ]
  }
}
```

Same `<repo>` / venv substitution rules as above; the hook itself is stdlib-only (it
imports `tools/kata_gauge.py` by path), so any Python 3.12+ interpreter works. The
consent-gated deployer for the whole chain — statusline + all three hooks, resolved
paths, append-never-replace merge, backup, uninstall round-trip — is
`kata_install.py --install-hooks` (merge engine: `tools/kata_host_settings.py`, CG-L2).

---

## statusLine chaining wrapper (CA-L1 — never clobber)

`adapters/claude/statusline_chain.py` is kata's **chain-never-clobber** wrapper. It exists
for the case where the operator ALREADY has a `statusLine` command (e.g. the operator's
`gsd-statusline.js`). Kata **never** replaces or edits that command. Instead it offers to
**chain**: run the user's command as a child, pass its stdin through unmodified, print the
child's stdout **byte-identical**, and then write kata's OWN sibling bridge file. Two
bridge files, zero contention (R-32) — the user's file is never touched.

### Kata scopes — replace, not chain (D160, deliberate re-scope of CA-L1)

The never-clobber guarantee above is **deliberately re-scoped by D160**: it holds
**everywhere except a kata-scoped cwd**. When the payload cwd is inside a kata run — a
`.kata/` directory or a `kata.config` file at or above cwd, the shared
`adapters/claude/kata_scope.py` walk (the SAME definition the gauge hook uses, EV-1) — the
wrapper renders kata's **own** one-line segment and **does NOT run the child**. kata renders
kata state in kata scopes; the operator's statusline owns everywhere else. Outside kata
scope (and on unparseable / cwd-less / non-kata stdin) the CHAIN and SKIP legs stay
byte-identical, and `kata_statusline.write_bridge` still writes kata's sibling bridge on
every leg — kata scope or not.

The kata segment format is `kata │ <dirname> <meter> <run>`: a dim `kata` marker, the cwd
basename (control-chars stripped), a 10-segment context meter (red band derived from the
kata trigger fraction `kata_gauge.DEFAULT_TRIGGER_FRACTION`, yellow pre-warning band, colour
and printed % keyed off the same rounded value), and a ` │ run` hint when the scope root's
`.kata/board.md` is non-empty. Rendering is fail-soft: any error inside the kata leg emits
nothing and exits 0 (the bridge still writes).

### The offer (fresh-profile vs existing-statusline)

- **No user `statusLine` exists (fresh profile):** kata installs its own unchained
  `statusLine` command (`statusline.py`), which writes the superset bridge directly
  (`kata_statusline.write_bridge`, the fresh-profile owner). This is the default snippet.
- **A user `statusLine` exists:** kata offers to **chain** (wrap the user's command) OR to
  **skip** to the fallback legs. **The operator's own statusline stays untouched (R-4: no
  operator action).** When chained, the wrapper writes `%TEMP%/kata-ctx-<session_id>.json`
  (atomic temp+rename); the user's own `%TEMP%/claude-ctx-<session_id>.json` is untouched.

### Chained install

The chained `statusLine` command passes the user's original command after `--`:

```json
{
  "statusLine": {
    "type": "command",
    "command": "python \"<repo>/adapters/claude/statusline_chain.py\" -- <user's original statusLine command>"
  }
}
```

The wrapper shlex-parses the user command and runs it as a **list-argv** child. It chains
**only** when that command shlex-parses to plain argv with **no shell metacharacters**;
otherwise it takes the SKIP leg (see Security below). On Windows, keep the chained command
using **forward slashes** so it stays chain-eligible (a backslash is treated as a shell
metacharacter and forces the SKIP leg — safe, but kata then falls back to its own bridge
instead of chaining).

### Reader priority (context-autonomy gauge)

The gauge (`tools/kata_gauge.py`) reads bridge files in this fixed priority:

1. **kata bridge** (`kata-ctx-<session_id>.json`, 5-field superset) — full token-aware
   triggering.
2. **user bridge** (`claude-ctx-<session_id>.json`, gsd 4-field) — percentage-only
   triggering (no `total_tokens`).
3. **deterministic N-wave fallback** — no usable/fresh bridge ⇒ graceful rotation
   (CA-L3/L4). Never "assume infinite context."

**Bridge selection (which file is the kata bridge).** The running conductor has **no session-id source** on
the Claude adapter — the SessionStart hook (`hooks/kata-sessionstart.py`) receives `session_id` on stdin but
neither persists nor exports it, the statusline writes `kata-ctx-<session_id>.json` from its own separate
stdin, and there is no `CLAUDE_SESSION_ID` env. So the conductor **selects the newest
`%TEMP%/kata-ctx-*.json` by mtime**. **Known limitation — concurrent same-host kata sessions:** if more than
one *fresh* (younger than the 300 s `[TUNABLE]` staleness window) `kata-ctx-*.json` exists, none can be
attributed to *this* conductor without a session-id, so the gauge is treated as **AMBIGUOUS** and the
conductor **falls to deterministic N-wave rotation — it never guesses**. Pinned in `kata-orchestrate`
(§ boundary-eval); mirrored here.

### Security (subprocess sink)

The chaining wrapper is the highest-scrutiny surface in this adapter: it runs a command
every statusline tick. The posture:

- **list-argv only, `shell` left False.** The child is executed as a validated
  `list[str]` with `shell=False`. The user's command string is **never** string-
  interpolated into a shell; `os.system` / `os.popen` are not used.
- **Chain-eligibility gate.** Kata chains ONLY when the command shlex-parses to plain
  argv with NO shell metacharacters (`| & ; < > ( ) $ `` ` `` \ * ? [ ] { } ~ ! # % ^`,
  newline/tab — `%` and `^` are cmd.exe-only). Any metacharacter, an unbalanced quote, or
  an empty command ⇒ the **SKIP leg**: no child runs, nothing is emitted, kata still
  writes its own bridge. Kata never re-introduces shell evaluation, and the never-clobber
  guarantee is preserved at install time (kata does not wrap an ineligible command — it
  leaves the user's statusline as-is).
- **Windows batch targets are skip-not-chain.** A `.bat`/`.cmd`/`.com` argv[0]
  (case-insensitive) is never chained, because Windows executes batch files via an
  implicit cmd.exe even under `shell=False` — the argument line is re-parsed with cmd.exe
  shell semantics, defeating the list-argv guarantee.
- **Bounded child.** The child runs under a hard timeout (5 s `[TUNABLE]`). Child failure,
  nonzero exit, or timeout ⇒ kata still emits whatever stdout the child produced, never
  hangs, and exits 0 — the host-statusline fail-soft contract (kata must never break the
  operator's statusline under any failure).
- **No new privilege.** The chained command is the operator's OWN pre-existing statusline
  command — the same trust domain as a test runner; chaining grants it no new capability.

The canonical `protocol/exec-safety.md` sink-registry row for this subprocess now exists
(authored at the P2/C10 closeout); this adapter documents the same sink here as the adapter-local view.

---

## Merge discipline & approval (CA-L24 — append-never-replace)

Applying `settings.snippet.json` is a **write to `~/.claude/settings.json`** and is
therefore an explicit item in the approved bundle collected pre-run — **never an implied
side effect**. When kata's install/bootstrap applies the snippet, the following merge
discipline holds verbatim:

> **hooks arrays are APPEND-NEVER-REPLACE; `statusLine` is only ever chained-or-skipped**
> — the CA-L1 never-clobber guarantee generalizes to EVERY settings key kata touches.

Concretely: a new `SessionStart` / `PreCompact` hook entry is **appended** to any existing
hooks array (never replacing the operator's hooks), and an existing `statusLine` command is
**chained or skipped**, never overwritten.

The operator's chosen mode (`bridgeMode`: `chained` | `user-only` | `none`) is recorded to
`<harness_home>/.kata-settings.json` under `hostPosture` (R-36/CA-L35 — the home corrected from the earlier
`~/.kata/settings.json`; this is where `kata_settings.record_host_posture` actually writes) by the bootstrap
flow (P2/C1). This
README states that contract; the adapter files here **write nothing** to host settings on
their own — the snippet is applied only via the approved bundle's host-settings write slot.

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
