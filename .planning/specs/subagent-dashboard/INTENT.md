---
kind: version-up
goal: >-
  Give KataHarness a distinctive, host-agnostic LIVE view of an orchestrated run — a separate-terminal TUI that
  tails the harness's own coordination files and renders worker subagents as artistic ASCII with animated
  progress, the kata motif, and a loop-phase ribbon. The outcome is a run you can WATCH and enjoy, identical
  regardless of which host spawned the agents — not a replacement for a host's native panel, but the unified,
  branded KataHarness view.
fixes: []
features:
  - "tools/kata_dash_model.py — pure parser: .kata/board.md + .kata/state.json -> a render-ready ViewModel"
  - "tools/kata_dash.py — rich-based live TUI: artistic ASCII worker rows + stepped progress bars + spinners + loop ribbon + board feed; tails files in a side terminal"
modulesAdded: []
changeSummary: >-
  Add a v1 subagent-dashboard (two layers: a pure model parser + a rich render/tail app) that reads the existing
  board + state artifacts and renders the BRIEF's design target. v1 = stepped bars derived from task state (no
  protocol change); v2 progress-heartbeats and v3 cross-host views are deferred. Adds `rich` to tools deps.
target:
  kind: self
  path: ""
  vault: PokeVault (self — KataHarness repo is its own workspace)
  platform: Claude
grillDepth: light
readiness: >-
  Enough to execute. The subagent-dashboard BRIEF already converged the hard questions (feasibility:
  separate-terminal = fully feasible; in-chat live = not feasible; design-target aesthetic frozen; v1/v2/v3 scope
  split). The remaining decisions are local + low-risk: v1 uses STEPPED bars from the existing task-status
  vocabulary (no board protocol change), `rich` (de-risked: installs + renderables import clean on this Win
  platform), read-only observer (never writes board/state), graceful "waiting for run" when files are absent.
  Two disjoint slices (pure model ∥ render/app) partition cleanly for an orchestrated foreground-parallel build.
  Deferred-with-reason: progress heartbeats (v2 — needs a board addition), textual/curses (rich suffices for v1),
  cross-host unification (v3 — pairs with multi-model). This is a real, self-contained feature workout for the
  full Greater Loop.
---

# INTENT — subagent-dashboard (Phase 4 self-dogfood version-up)

**North star.** When the harness runs concurrent workers, you should be able to open a second terminal and
*watch* it — block-bar progress per worker, braille spinners, the `⛩ 道` kata motif, a `GRILL→…→IMPROVE` ribbon
lighting the live phase, and the board's recent events + drift ledger beneath. It reads the harness's own files
(`.kata/board.md`, `.kata/state.json`, worktree git status), so it looks identical under Claude, Kiro, or
Quick — the host-agnostic, unmistakably-KataHarness run view.

This is the **first end-to-end exercise of the complete Greater Loop on KataHarness itself**: `kata-initiate`
froze this INTENT → the harness builds it (orchestrated, real workers in worktrees) → `kata-closeout` reports,
offers the understand-map, and ends at the operator's **version-select**. It deliberately builds a *real,
visible* feature so the loop gets a genuine workout, not a toy.

**Scope guard (v1 only).** Stepped bars from task state; `rich`; read-only observer; graceful when no run is
live. NOT in v1: progress-heartbeat protocol additions (v2), cross-host unification (v3), textual/curses,
any GUI/web. Frozen — the build executes against this; a new initiation is required to change it.
