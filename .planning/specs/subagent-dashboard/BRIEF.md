---
date: 2026-06-20
spec: subagent-dashboard
status: BRIEF — pre-grill. Captured 2026-06-20 (user wants a cool, unique-to-KataHarness live agent view).
order: pairs with multi-model (Phase 5) or sooner if desired — host-agnostic, orthogonal to the loop
tags: [brief, observability, dashboard, tui, ascii, subagents, host-agnostic]
---

# Subagent Dashboard — a cool, host-agnostic live view of the orchestrated run

> **Quick plan brief.** A standalone TUI that renders the harness's worker subagents as **live, artistic ASCII
> progress** — unique to KataHarness. Orthogonal to the loop; does not block the greater-loop freeze.

## Why
When the harness runs concurrent worker subagents, the only live view today is the *host's* native one (Claude
Code's agent panel; Kiro's; Quick/ACP's). The user wants a **distinctive, fun KataHarness view** — and a
**host-agnostic** one that looks the same regardless of who spawned the agents.

## Feasibility (assessed 2026-06-20)
- **In-chat live animated TUI: NOT feasible** — the chat transcript is append-only, no canvas/redraw. During
  foreground-parallel dispatch the *host* shows its native panel.
- **In-chat static ASCII snapshot frames: partial** — printable at milestones (best with *background* agents,
  where the orchestrator takes turns between reports). Branding flavor, not animation.
- **Separate-terminal dashboard: FULLY feasible (the real product)** — a `rich`/`textual` (or `blessed`/curses)
  app in its own pane **tails the harness's existing files** (`kata-board` `protocol/board.md` · `.kata/state.json`
  `protocol/state.md` · worktree git status) and renders a live, animated, artistic view. Host-agnostic because
  it reads the board, not the host UI. `rich`/`textual` natively do block-bar progress, spinners, panels, ASCII.

## Design target (aesthetic)
```
╔══════════════════════════════════════════════════════════════════════════════╗
║  KATAHARNESS  ⛩  道   orchestrated run · <spec>            wave w/W   ◐ gate   ║
╟──────────────────────────────────────────────────────────────────────────────╢
║  ▸ A  <task>              ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▱▱▱▱▱▱  72%  ⠹ <status>                 ║
║  ▸ B  <task>              ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▱  93%  ⠼ committing…             ║
║  ▸ D  <task>              ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰ 100%  ✓ done · <sha>            ║
╟──────────────────────────────────────────────────────────────────────────────╢
║  board ▸ <recent events>          drift 0   escalations 0                      ║
║  worktrees ▸ _kata/{…}                                    ⠿ orchestrator live  ║
╚══════════════════════════════════════════════════════════════════════════════╝
   GRILL ──▶ FREEZE ──▶ ◉ EXECUTE ──▶ EVALUATE ──▶ HANDOFF ──▶ IMPROVE
```
Block-char bars (`▰▱`), braille spinners (`⠹⠼⠧⠿`), kata motif (`⛩ 道`), a **loop ribbon** tracking the live
phase. One row per worker; orchestrator + board + drift ledger below.

## Data dependency (the one real build cost)
Smooth bars need **granular progress** on the board. Today: discrete task states (`assigned → in-progress →
done → gated`) ⇒ **stepped** bars (works v1). Smooth %: workers post lightweight **progress heartbeats** to the
board (e.g. `PROGRESS | <task> | <step>/<n> | <label>`) — a tiny `protocol/board.md` addition; opt-in, ignored
by everything else.

## Scope (when built)
- v1: a `tools/kata_dash.py` (`rich`/`textual`) that tails board+state+worktrees and renders the design above;
  run in a side terminal (`! python tools/kata_dash.py` or a separate window). Stepped bars from task state.
- v2: worker progress heartbeats → smooth bars; the loop-ribbon driven by the run phase.
- v3 (host views): the per-host native panels stay available; this is the *unified* cross-host view (pairs with
  `multi-model-orchestration` — when agents run across Claude/Kiro/Quick, one dashboard shows them all).

## Sequencing
**Not now.** Foreground-parallel dispatch (Claude Code's native live panel) is the immediate answer. This
dashboard is a **build-later** component — natural alongside `multi-model-orchestration` (Phase 5), or pulled
earlier as a fun standalone if desired. Host-agnostic + orthogonal ⇒ never blocks the loop.

## Out of scope
Replacing/recreating a host's built-in panel (can't restyle Claude Code's); a GUI/web app (a terminal TUI first).
