# kata-diagnose — shared method (RUBRIC)

The tier-invariant diagnosis method. The `kata-diagnose-<tier>` skills set only depth; they all obey this.

---

## The feedback-loop-first principle (read first)

**Phase 1 is the skill.** A fast, deterministic, agent-runnable pass/fail signal is a prerequisite for
everything that follows — bisection, hypothesis-testing, instrumentation all just consume the signal. Without
it, staring at code won't save you. Spend disproportionate effort here. Be aggressive; refuse to give up. Treat
the loop as a product — make it faster, sharper, more deterministic.

For the catalog of ways to construct one (failing test → curl → CLI diff → headless browser → replay trace →
throwaway harness → fuzz → bisect → differential → HITL last resort) and the non-deterministic-bug tactics,
see `resources/FEEDBACK-LOOPS.md`. **Do not proceed without a loop you believe in** — if you genuinely can't
build one, say so explicitly, list what you tried, and ESCALATE.

## When to use `kata-diagnose` (vs `kata-tdd`)

Boundary with [[kata-tdd]]: tdd builds *new* behavior where RED is *expected* (you write code to green it).
`kata-diagnose` is for *unexpected* RED — a regression, a should-pass test failing, broken/throwing behavior
you can't green in one step. A worker switches tdd→diagnose only on a failure it can't immediately explain.

## Kata constraints

- **Stay in your owned files.** Do not touch files outside your ownership boundary.
- **Don't re-plan.** If the fix reveals a design flaw requiring structural change, that is a finding to
  escalate — not a mandate to rebuild. The diagnosis loop produces a fix within the current plan.
- **Escalate via [[kata-board]]** if the fix needs a file you don't own or the plan looks wrong.
- Ground your mental model in the domain glossary ([[kata-context]] / `CONTEXT.md`) and any ADRs /
  decision-ledger entries for the area **before** hypothesising.

---

## The 6-phase method

### Phase 1 — Build a feedback loop

A fast, deterministic, agent-runnable pass/fail signal for the bug. See the feedback-loop-first principle
above and `resources/FEEDBACK-LOOPS.md` for construction tactics.

### Phase 2 — Reproduce

Run the loop; watch the bug appear. Confirm it's the failure the *spec/user* described (not a nearby one),
that it's reproducible (or high-rate for flaky bugs), and capture the exact symptom for later verification.

### Phase 3 — Hypothesise (3–5 ranked, falsifiable)

Generate 3–5 ranked hypotheses *before* testing any — single-hypothesis anchors on the first idea. Each must
state a prediction ("if X is the cause, changing Y makes it disappear"). No prediction = a vibe; sharpen or
discard. Note the ranked list on the board (cheap checkpoint; the orchestrator/human may re-rank instantly).

### Phase 4 — Instrument (one variable at a time)

Each probe maps to a specific Phase-3 prediction. Prefer debugger/REPL > targeted boundary logs > never "log
everything and grep". **Tag every debug log** with a unique prefix (e.g. `[DBG-a4f2]`) so cleanup is one grep.
For perf regressions, measure first (baseline + profiler/timing), then bisect — logs mislead.

### Phase 5 — Fix + regression test

Write the regression test **before the fix**, but only if a *correct seam* exists (one exercising the real
bug pattern at the call site). If no correct seam exists, **that is the finding** — note it (the architecture
is preventing lock-down) and flag for [[kata-improve]]. Otherwise: failing test → fix → passing → re-run the
Phase-1 loop on the original (un-minimised) scenario.

### Phase 6 — Cleanup + post-mortem (required before "done")

- [ ] Original repro no longer reproduces · [ ] regression test passes (or absent-seam documented)
- [ ] all `[DBG-…]` instrumentation removed (grep the prefix) · [ ] throwaway harnesses deleted
- [ ] the correct hypothesis stated in the commit message (the next debugger learns)

Then ask **"what would have prevented this?"** — if the answer is architectural, hand the specifics to
[[kata-improve]] *after* the fix lands (you know more now than at the start).

### Phase 6 → Verdict: fix-problem vs plan-problem (fix-loop-hardening — NEW capability)

> **When dispatched by the orchestrator's thrash budget** (the fix loop hit N=2 on one area, or the run-level
> ceiling), Phase 6's post-mortem question is the root of a **returnable verdict**. This is a NEW capability
> formalized from the existing Phase-6 seam — `kata-diagnose` did not previously return this verdict.

After the Phase-6 post-mortem, return **one** of:

| Verdict | Meaning | Orchestrator action |
|---|---|---|
| **`fix-problem`** | The failure is a legitimate implementation difficulty — hard, but solvable within the current plan (e.g. wrong approach, missing precondition, transient environment issue). | Resume fixing; use the diagnosis context. No human escalation. |
| **`plan-problem`** | The failure reveals a structural defect in the plan itself — the plan cannot reach a passing state without a plan-level change (e.g. wrong acceptance criteria, unresolvable constraint, architectural mismatch the plan baked in). | Orchestrator escalates a re-plan candidate via `kind: "human-required"` (L3). |

**How to decide:** apply Phase-6's "what would have prevented this?" reasoning:
- *A different implementation* (better algorithm, correct precondition, right tool) → **`fix-problem`**
- *A different plan* (different acceptance criteria, different architecture, a LOCKED decision that is wrong) → **`plan-problem`**
- *Uncertain:* lean `fix-problem` if at least one credible fix path exists; lean `plan-problem` if every
  credible fix path requires changing something the plan treats as fixed.

**Standing constraints (unchanged):** the skill **returns the verdict to the orchestrator and does NOT itself
re-plan** — consistent with the "Don't re-plan — escalate" rule. Both `kata-diagnose-full` and
`kata-diagnose-light` inherit this verdict (shared RUBRIC, tier-invariant).
