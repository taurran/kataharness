# NEXT-SESSION ORIENTATION — written 2026-08-16 (branch `burn/backlog-burn-01`)

> **This file follows the locked agent-orientation format (UX-15): MISSION → GUARDRAILS →
> CONTEXT → REPORT CONTRACT → YOUR BRIEF, with the copy block LAST.** The ✂ block at the bottom
> is what the operator pastes into the fresh session — content lines carry zero decoration (UX-7).
> The authoritative state is `.planning/HANDOFF.md`; this file is the paste companion.

━━ KATAHARNESS · AGENT ORIENTATION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
run: planning-batch-2026-08 · session: next · branch: burn/backlog-burn-01
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## MISSION

Help the operator decide **the next planning items and how far to plan before coding execution
starts** — their explicitly set agenda. Everything from the 2026-08-15/16 marathon is recorded in
depth; your job is to present the decision honestly, take their ruling, and then run whatever
grill/freeze/build path they choose under the normal loop. Do not invent a different agenda.

## GUARDRAILS

- **PD-1/PD-2 bind** (`protocol/prime-directives.md`, loaded first, always). Done requires proof.
- **D169:** nothing dispatches without a FROZEN plan. Every design produced last session is
  DRAFT — grill + convergence gate before any build.
- The session-lifecycle grill remains **HELD** (SL-1..36 must NOT be compiled; CONVERGENCE-HOLD
  files are authoritative). Read `DECISIONS.md`, never measure it.
- Never PowerShell Get-Content/Set-Content round-trips on repo files; never `_run_git` for file
  content; run tests via `uv run` from tools/.
- Plain English always; item codes always paired with what the thing actually is.
- The vault is **KIBAN** (`~/Kiban/Vault`) — never PokeVault; never git-ops against it.
- Internal codenames (Kitchen, engram) never appear in user-facing surfaces (UX-24).
- Worktrees: manual `git worktree add` at a pinned SHA; builders verify base as step 0 (BBM-9).

## CONTEXT — read in this order

| what | where |
|---|---|
| Authoritative state | `.planning/HANDOFF.md` §0–§5 (the 2026-08-16 block) |
| Current block only | `.planning/STATE.md` CURRENT (do NOT read the 1500-line file wholesale) |
| The planning batch (17 features + 7 fixes) | `.planning/BACKLOG.md` top — BL-N01..N17, BL-X01..X07 |
| Burn-mode rulings | `.planning/specs/backlog-burn-mode/GRILL-LEDGER.md` (BBM-1..11) |
| The UX system | `.planning/specs/ux-rework/` — DESIGN.md first, then GRILL-LEDGER (UX-1..27), PLATFORM-MATRIX, **templates/** (generators = pixel-exact spec) |
| Learning graph | BL-N16 in BACKLOG + `.planning/specs/learning-graph/RESEARCH-HERMES-PI.md` |
| Burn evidence | `.planning/specs/backlog-burn-01/OBSERVATIONS.md` (H1–H7) |

The next-step decision inputs (HANDOFF §2, presented, not pre-decided): grill-ready = UX system ·
Burn mode · learning graph; cheap unblockers = the six platform probes + BL-X01/02/03/05/07;
full-grill-needed = the Kitchen (operator has unsaid details — live grill) · Truth Serum (shaped
by BL-M33); candidate execution shape = a small burn over fixes+probes while the first big grill
runs — a CANDIDATE only.

## REPORT CONTRACT — before this next session ends

☐ the planning-depth decision recorded (which items, in what order, and the go/no-go bar for
  starting coding execution) ☐ any grill opened is ledgered under `.planning/specs/<name>/`
☐ push/PR decision surfaced (38+ unpushed commits) ☐ 🔴 PAT rotation surfaced (deferred ≠ dropped)
☐ T-03 scope call surfaced ☐ handoff refreshed at close

━━━━━ end orientation ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## YOUR BRIEF — ✂ copy below · paste into new session ✂

Load all KataHarness context per CLAUDE.md (prime directives first, then AGENTS.md).
Then read .planning/HANDOFF.md's 2026-08-16 block in full, and .planning/STATE.md's
CURRENT block only. Verify ground truth before acting:
git status --porcelain (empty) · git rev-parse --abbrev-ref HEAD (burn/backlog-burn-01) ·
cd tools && uv run python scripts/gauntlet.py (4/4 PASS).
This session's agenda, set by me last session: decide the next planning items and how
far to plan before we start coding execution. Present the decision inputs from HANDOFF
section 2 and decide WITH me — do not pre-decide, do not invent a different agenda.
Everything designed last session is DRAFT: grill and convergence-gate before any build
(D169). The vault is Kiban. Wave, never sprint. Plain English, always.

✂ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ copy ends ━━━━━━━━━━━━━━━━━━━━━━
