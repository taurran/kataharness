---
date: 2026-06-21
spec: loop-hardening
sprint: S1.5 (status-surface adapters)
status: research complete — feasibility verified per platform (cited)
method: 3 parallel fresh-context research agents (web, citation-demanding) — one per host
tags: [research, loop-hardening, s1.5, adapters, statusline, claude, codex, kiro, agnostic-via-adapters]
---

# RESEARCH — S1.5 status-surface adapters: can the live view be seamless per platform?

**Question:** the operator requires the live run-view to be *seamless into the platform it's running on*
(Claude, Codex, Kiro, …). Does each host expose a programmable surface to display live external
(`.kata/`) run-state, and via what mechanism? Verify before building (no pretend bars).

## Verdicts (cited)

### Claude Code — ✅ FEASIBLE NOW (build it)
- **Config:** `statusLine` in `settings.json` (`~/.claude/` global · `.claude/settings.json` project ·
  `.claude/settings.local.json` gitignored). Shape: `{ "type": "command", "command": "<script>",
  "padding"?, "refreshInterval"?, "hideVimModeIndicator"? }`.
- **stdin contract:** the command receives a JSON object on **stdin** that **includes `cwd` AND
  `workspace.current_dir`** (and `workspace.git_worktree`, `workspace.project_dir`, `model`,
  `context_window`, `session_id`, `transcript_path`, `version`, …). ⇒ the command can reliably locate
  `<cwd>/.kata/` (and knows the worktree) to read live state. **This is the load-bearing fact.**
- **Output:** stdout; **multi-line supported**; **ANSI color supported**; **Unicode supported** — `改善型`
  + block bars `▰▱` render fine; can read `$COLUMNS`/`$LINES` (v2.1.153+). Keep it short; wraps if wide.
- **Refresh — THE critical finding:** event-driven (after each assistant message, `/compact`, permission/
  vim change) with a **300 ms debounce**; in-flight runs are cancelled if a new trigger fires. **During
  idle (the main session waiting on background subagents) it does NOT update** — *unless* you set
  **`refreshInterval: N`** (min **1 s**) to also re-run on a fixed timer. The docs call out our *exact*
  case: *"these triggers can go quiet … while a coordinator waits on background subagents … set
  `refreshInterval` to keep externally-sourced segments current."* ⇒ **`refreshInterval: 1` gives ~1 s
  live granularity during an orchestrated run.** Sub-second is not possible; 1 s is plenty for a
  multi-minute build.
- **Constraints:** runs locally (no token cost); needs workspace trust; disabled if `disableAllHooks`;
  slow scripts block updates (keep the read fast — atomic file reads, no git/subprocess); non-zero exit
  or empty stdout ⇒ blank; stderr ignored.
- **Source:** https://code.claude.com/docs/en/statusline.md · https://code.claude.com/docs/en/settings.md

### Codex CLI — ❌ NO live in-TUI surface (fall back to the viewer)
- `tui.status_line` (`~/.codex/config.toml`) is a **fixed built-in enum** (`spinner`, `project`, `model`,
  `current-dir`, `git-branch`, `token-usage`, …) — **no command-backed custom item.** That exact
  capability is an **open, unimplemented** feature request (github.com/openai/codex **#17827**; #20140/#20244
  closed as dups; proposed `[status_line] command=… refresh_interval_secs=…` not built).
- **Hooks** exist (`SessionStart`/`PreToolUse`/`SubagentStart`/`Stop`/…, JSON on stdin) but **explicitly
  cannot render to the UI** ("communicate through `systemMessage` … surface as warnings") and **have no
  recurring/background mode.**
- Closest analog = the **`notify`** config command (egress-only; event `agent-turn-complete`; JSON via
  **argv**, not stdin; must be user/global, ignored in project `.codex/`). Outbound notification, **not** a
  live display.
- **Verdict: none available for live in-TUI status today.** Use the host-agnostic viewer fallback.
- **Source:** developers.openai.com/codex/{config-reference,config-advanced,hooks} · openai/codex#17827

### Kiro — ⚠️ FEASIBLE ONLY via a VS Code status-bar extension (defer — heavyweight)
- Kiro **is a Code-OSS (VS Code) fork**; supports **OpenVSX** extensions and the **full `vscode` API**,
  including **`window.createStatusBarItem()`** — a sideloaded `.vsix` *can* paint a live status-bar item.
- Kiro **agent hooks** route shell-command **stdout into the agent's context, not the UI**; steering/
  AGENTS.md are static. No native/hook display surface for external state.
- **Verdict: live in-window status is possible but ONLY by shipping+maintaining a VS Code extension**
  (`.vsix`, `createStatusBarItem`) — a much bigger artifact than a statusline script (+ a known
  version-gate bug, kirodotdev/Kiro#1339). **Defer**; use the viewer fallback meanwhile.
- **Source:** kiro.dev/docs/{guides/migrating-from-vscode,hooks/types,hooks/actions,steering} · Kiro#1339

## Honest scorecard — "seamless into the platform it's running on"
| Host | In-window live status? | Mechanism | Effort | S1.5 disposition |
|---|---|---|---|---|
| **Claude Code** | ✅ yes (~1 s) | `statusLine` cmd + `refreshInterval:1`, reads `<cwd>/.kata/` | thin script | **BUILD now** |
| **Codex CLI** | ❌ no | none (req #17827 unbuilt); `notify` is egress-only | n/a | **viewer fallback** (documented) |
| **Kiro** | ⚠️ only via `.vsix` ext | VS Code `createStatusBarItem` | heavy (separate ext) | **defer** (documented) |
| **any host** | ✅ (separate window) | the existing `kata_dash.py` TUI (reads `.kata/`) | done | **universal fallback** |

So "seamless in-window" is **fully achievable for Claude now**, **deferred for Kiro** (needs an extension),
and **not achievable for Codex** (their limitation, tracked upstream). The universal honest answer where no
native bar exists is the host-agnostic viewer.

## Architecture implications (confirmed)
1. **S1.5 seeds the `adapters/` layer with its first concrete member** (`adapters/` does not exist yet).
   The status surface is the textbook adapter concern (Claude statusline is already on CLAUDE.md's
   "native features the Claude adapter MAY use" list). Core stays agnostic.
2. **It's a PULL consumer, not push.** The statusline command polls `<cwd>/.kata/` each refresh and reuses
   the existing pure layer: `kata_dash_model.build_view_model(board, state)` → a NEW agnostic
   `render_statusline(view_model) -> str` (one-line projection). **No "wiring into kata-loop" needed** —
   the run already emits telemetry via `kata_board`. The push `StatusSink` abstraction is unnecessary for
   v1 (only file-unpollable surfaces would need it); drop it from scope.
3. `kata.config` has **no host field**; runtime host-sniffing is unnecessary — the **installed adapter is
   the host knowledge** (the KataHarness way). `kata-bootstrap`/initiation MAY offer to write the Claude
   `settings.json` snippet on install.

## Revised S1.5 scope (grounded by this research)
- **S1.5a — agnostic core:** `render_statusline(view_model) -> str` in the pure layer (reuses ViewModel:
  phase · n active/total tasks · smooth percent · gate · drift). Unit-tested. (No push interface.)
- **S1.5b — Claude adapter (first member of `adapters/`):** `adapters/claude/statusline.*` command (read
  `cwd` from stdin JSON → load `<cwd>/.kata/{board.md,state.json}` → `build_view_model` → `render_statusline`
  → print; fast, fail-soft to a quiet default) + a `settings.json` snippet with **`refreshInterval: 1`** +
  README. Demonstrable: a real orchestrated run whose state ticks (~1 s) in Claude's own statusline.
- **Fallbacks (documented, not built as fake bars):** Codex → viewer; Kiro → viewer now, `.vsix` ext later.
  The existing TUI is the universal fallback. (Optional web viewer = separate future sprint.)
