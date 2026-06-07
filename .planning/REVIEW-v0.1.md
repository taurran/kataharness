# REVIEW-v0.1 — adversarial validation synthesis (2026-06-06)

Two fresh-context Opus adversarial reviewers (kata-review, read-only, HOLD-biased) audited all 11 skills +
scaffolding. Both returned **HOLD**. This is the synthesized gap ledger + triage. Corroborated = both flagged.

## Verdict
v0.1 skill *bodies* are high quality and the execution half is field-proven (L9/L10), but v0.1 **over-claims**:
it advertises a 7-phase, self-improving, agnostic harness while the IMPROVE phase, adapters, ¾ of the
protocol, and several loop-critical skills don't exist; two `source:` lines are name-drops/inversions; the
fidelity-tracking artifact (`research/NOTES.md`) was never written; and the grill grades its own convergence.

## Gap ledger (severity · corroboration · disposition)

| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1 | HIGH | `protocol/` claims 4 schemas (board/tasklist/state/handoff); only board.md exists | **FIX**: write state.md+handoff.md; tasklist→backlog (scoped) |
| 2 | HIGH | `kata-orchestrate` hard-codes Claude-specific `Agent` tool in an `agnostic:true` skill (grill abstracts AskUserQuestion; orchestrate doesn't); +unjustified Write/Edit | **FIX**: abstract dispatch as adapter-bound; trim allowed-tools |
| 3 | HIGH | `kata-board` bare `>>` not atomic/locked; claims clobber-safety it can't guarantee; recipe is Unix-only (project runs on Windows PS) | **FIX**: cross-platform + honest safety reframe (orchestrator-assigns model) |
| 4 | HIGH | README/DESIGN over-claim: IMPROVE vapor, 0 adapters, partial protocol, 3 loop skills unbuilt; layout lists nonexistent dirs/files | **FIX**: make claims honest (built vs backlog) |
| 5 | HIGH | `research/NOTES.md` (DESIGN's "most important bake-in work") never written | **FIX**: write it (this review seeds it) |
| 6 | HIGH | `kata-grill` grades its OWN convergence — no fresh-context check; ironic given kata-review exists. The harness's core bet, structurally unenforced | **FIX**: insert pre-freeze adversarial gate (kata-review on the ledger) before FREEZE |
| 7 | HIGH | `kata-plan` decomposes by disjoint-file-ownership (horizontal-leaning) — contradicts cited `to-issues` vertical-slice + `kata-tdd` "never horizontal" | **FIX**: reconcile (slice vertically → assign each slice's files as ownership) |
| 8 | HIGH | BMAD `source:` on kata-plan is a name-drop — none of role-agents/trade-offs-over-verdicts present | **FIX**: correct attribution + import trade-offs-over-verdicts into design-doc |
| 9 | MED | `kata-review` cites mattpocock `review` but implements cpp-adversarial-validation; review's Standards axis missing from whole EVALUATE phase | **FIX**: correct attribution + add Standards axis to kata-evaluate |
| 10 | MED | `kata-handoff` inverts mattpocock handoff (temp→durable) without noting it; drops "suggested skills" | **FIX**: note deliberate inversion + add suggested-next pointer |
| 11 | MED | `kata-tdd` orphaned — orchestrate dispatch never tells worker to invoke it | **FIX**: wire `[[kata-tdd]]` into the dispatch step |
| 12 | MED | task-claim ownership contradiction: board has `CLAIM` vs planned tasklist "file-locked claim" | **FIX**: board=messaging/audit; orchestrator assigns (no self-claim) in v0.1; tasklist=backlog self-claim |
| 13 | MED | `kata-context` ~redundant with kata-grill's inline glossary baking | **FIX**: delineate (grill captures during; context owns standalone/multi-context maintenance) |
| 14 | MED | `kata-tdd` dropped mattpocock's supporting depth (deep-modules/interface-design/mocking/tests/refactoring) | **FIX (light)**: add principle pointers; full resource port → backlog |
| 15 | MED | evaluator "read-only" oversold while `Bash` present (write escape hatch) | **FIX**: reword STANDARDS to "no Write/Edit; Bash for gates only" |
| 16 | LOW | `kata-design-doc` dropped to-prd's test-seams + Testing Decisions | **FIX**: add test-seams element |
| 17 | LOW-MED | `kata-grill` dropped GSD checkpointing + user-cited-doc accumulation | **FIX**: ledger-checkpoint-after-each-branch + cited-doc rule |
| 18 | LOW | STATE.md:11 stale ("0 skills built") contradicts later | **FIX**: trivial |
| 19 | LOW | board schema duplicated in skill + protocol/board.md (drift risk) | **FIX**: skill points to protocol for schema |
| 20 | HIGH | **The existential one**: A/B tied; spine differentiators bought 0 correctness edge; the bet (grill) is unproven | **DECISION**: ship-gate = planning-varied A/B before v0.1 is "validated" |
| 21 | HIGH | IMPROVE phase + kata-diagnose/tasklist/selfhandoff + adapters unbuilt (the "build more") | **DEFER → user fork**: build-now vs honestly-downscope-v0.1 |

## Triage
- **FIX NOW** (#1–19, errors/honesty/structural/attribution; all edits to existing files + 3 new schema/doc files).
- **DECISION** (#20): record the ship-gate.
- **USER FORK** (#21): the only "build more" — present down-scope-to-honest vs build the missing loop skills.

## Standing policy (from this exercise)
Run `kata-review` (fresh-context adversarial) on everything built here, at least once, before it's called done.
→ to be locked as a DECISION (D15).
