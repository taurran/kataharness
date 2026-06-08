---
name: kata-diagnose
description: >-
  Disciplined diagnosis loop for an UNEXPECTED failure a worker can't green in one TDD step — reproduce →
  feedback-loop → ranked hypotheses → instrument → fix + regression → cleanup. Use when a test that should
  pass fails, a regression appears, or behavior is broken/throwing and the cause is unknown. Stays in the
  worker's owned files; escalates rather than re-planning.
license: Apache-2.0
version: 0.1.0
category: execute
status: experimental
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Bash, Edit, Write]
source: adapted-from mattpocock/skills engineering/diagnose
tags:
  - kata/execute
  - kata/module/quality
  - debugging
  - diagnosis
---

# kata-diagnose — find the cause before you touch the fix

Boundary with [[kata-tdd]]: tdd builds *new* behavior where RED is *expected* (you write code to green it).
`kata-diagnose` is for *unexpected* RED — a regression, a should-pass test failing, broken/throwing behavior
you can't green in one step. A worker switches tdd→diagnose only on a failure it can't immediately explain.
Kata constraints still apply: **stay in your owned files; don't re-plan; escalate via [[kata-board]] if the
fix needs a file you don't own or the plan looks wrong.** Ground your mental model in the domain glossary
([[kata-context]] / `CONTEXT.md`) and any ADRs / decision-ledger entries for the area before hypothesising.

## Phase 1 — Build a feedback loop (this IS the skill)
A fast, deterministic, agent-runnable pass/fail signal for the bug. With it, bisection / hypothesis-testing /
instrumentation all just consume the signal; without it, staring at code won't save you. Spend
disproportionate effort here. Be aggressive; refuse to give up. Treat the loop as a product — make it
faster, sharper, more deterministic. For the catalog of ways to construct one (failing test → curl → CLI
diff → headless browser → replay trace → throwaway harness → fuzz → bisect → differential → HITL last
resort) and the non-deterministic-bug tactics, see `resources/FEEDBACK-LOOPS.md`. **Do not proceed without a
loop you believe in** — if you genuinely can't build one, say so explicitly, list what you tried, and ESCALATE.

## Phase 2 — Reproduce
Run the loop; watch the bug appear. Confirm it's the failure the *spec/user* described (not a nearby one),
that it's reproducible (or high-rate for flaky bugs), and capture the exact symptom for later verification.

## Phase 3 — Hypothesise (3–5 ranked, falsifiable)
Generate 3–5 ranked hypotheses *before* testing any — single-hypothesis anchors on the first idea. Each must
state a prediction ("if X is the cause, changing Y makes it disappear"). No prediction = a vibe; sharpen or
discard. Note the ranked list on the board (cheap checkpoint; the orchestrator/human may re-rank instantly).

## Phase 4 — Instrument (one variable at a time)
Each probe maps to a specific Phase-3 prediction. Prefer debugger/REPL > targeted boundary logs > never
"log everything and grep". **Tag every debug log** with a unique prefix (e.g. `[DBG-a4f2]`) so cleanup is
one grep. For perf regressions, measure first (baseline + profiler/timing), then bisect — logs mislead.

## Phase 5 — Fix + regression test
Write the regression test **before the fix**, but only if a *correct seam* exists (one exercising the real
bug pattern at the call site). If no correct seam exists, **that is the finding** — note it (the architecture
is preventing lock-down) and flag for [[kata-improve]]. Otherwise: failing test → fix → passing → re-run the
Phase-1 loop on the original (un-minimised) scenario.

## Phase 6 — Cleanup + post-mortem (required before "done")
- [ ] Original repro no longer reproduces · [ ] regression test passes (or absent-seam documented)
- [ ] all `[DBG-…]` instrumentation removed (grep the prefix) · [ ] throwaway harnesses deleted
- [ ] the correct hypothesis stated in the commit message (the next debugger learns)
Then ask **"what would have prevented this?"** — if the answer is architectural, hand the specifics to
[[kata-improve]] *after* the fix lands (you know more now than at the start).
