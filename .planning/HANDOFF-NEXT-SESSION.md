# HANDOFF — next session (written 2026-07-20, end of the advisor-executor session)

> **Supersedes the 2026-07-12c handoff** (its return-checklist items were all executed same-day;
> that history is preserved in `.planning/STATE.md` CURRENT blocks — nothing is lost).
> **Ground truth at write time:** master **`0d3abc6`** (PR #39 merged, branch deleted local+remote,
> tree clean, `git stash list` EMPTY). Gauntlet at merge: **pytest 3981 pass / 3 pre-existing skip ·
> integration 2/2 · ruff clean · validator 49/0/0 · Snyk med+ 0 · mutation non-vacuous.**
> ⚠ IGNORE `C:\Dev\CLAUDE.md` (unrelated Mise project).

## 1. WHAT SHIPPED THIS SESSION — D167 advisor-executor (PR #39)

The **Fable-tier Advisor consult** (`kata-advise`, the 49th skill) — the advisor-executor pattern
wired across the loop. Built by running the **full Kata Loop on the harness itself** at a Fable
anchor: initiate → 7-question grill (28 LOCKED entries, **5 fresh-context convergence passes**,
HOLD 8/3/3/2 → SHIP) → ELEVATE EV-1 accepted → freeze-gate SHIP-WITH-FIXES (7 folds) → 6 workers /
2 waves → evaluate **PASS** (8/8 ACs) + adval **SHIP** → operator-ordered pre-merge smoke → merge.

**The contract (all LOCKED, compiled in `.planning/specs/advisor-executor/DESIGN.md`):**
- `advisor.approved` is the **SOLE** legality record — fully decoupled; **`models.premium`,
  `ADAPTIVE_EVENTS`, and `kata_adaptive.py` are BYTE-UNTOUCHED** (diff-proven at the gate).
- **Fable-target rung** (`advisor_rung_of`): opus/sonnet/haiku anchors elevate to **fable**;
  fable/mythos inherit at anchor (arm a); never one-rung arithmetic, never mythos by default.
- **Advise-first, bump-second:** at the D150 fail threshold the conductor consults FIRST at the
  same worker rung (orchestrator-side bump deferral — engine untouched); the bump consumes
  normally on the next failure, advice riding along.
- **Two-moment grants:** advanced consents at **bootstrap** composition (so planning consults are
  legal); standard opts in **once per RUN** at **preflight** (post-freeze, pre-execution);
  **essential excluded**; headless ⇒ OFF + surfaced note, never blocks.
- **Own budget pool** (standard 5/1 reserved · advanced 10/2), FCFS + reserve floor, loud lapses.
- **The gate NEVER consults** (judge independence); closeout never consults.
- **EV-1 advice-effectiveness pairing** (`advised-pass` / `advised-fail-bumped` /
  `advised-fail-ceiling`) in the telemetry ledger + after-action rollup.
- BC: absent `advisor` block ⇒ byte-identical behavior.

**Honesty labels (PD-2 — these travel with every claim):** the **dispatch mechanics** are
live-exercised **n=1** (operator-granted consult: gate → budget → dispatch → structured response →
disposition, full artifact trail at `.kata/advice/live-exercise-1-1.json`). The **four hooks are
test- and smoke-proven prose — live-if-they-occur, UNFIRED** (no real task hit threshold-2 this
run). Arm (b) (sub-fable anchor elevation) and the standard carve-out are test-proven, not
live-proven.

**Pre-merge proof battery (operator-ordered):** 6-seam deterministic smoke, zero LLM calls,
**double-run byte-equal** (digest `ac81085c83748ae1`, artifact `.kata/smoke-advisor.json`) — gate
matrix across mode×anchor×event, all NO-FIRE reasons, 7/7 poison configs raising (D136), rung
table, reserve-floor boundary, render→recount round-trip, telemetry presence-discrimination, and
the composed advise-first loop walked dry end-to-end. A fresh-context Opus auditor attacked the
battery itself for vacuity/coverage/determinism-theater: verdict **SOUND**.

## 2. ★★ START HERE NEXT SESSION — the quota-resilience initiative

**The operator's next build, briefed and ready to grill:**
**`.planning/specs/quota-resilience/REQUIREMENT.md`** — a complete, file:line-cited intake brief
(pre-grill, not frozen). Read it FIRST; it contains the whole research pass so you do not repeat it.

**One-paragraph version.** Detect per-provider rate-limit / token-quota exhaustion
(Anthropic/OpenAI/Cursor/Gemini), tell the operator plainly they are out, **park the run via the
existing handoff machinery so `/kata-resume` resumes exactly where it stopped**, and emit that
provider's upgrade command or URL. Plus the advisor-specific kill-switch: skip remaining consults
for the session and report the reason at closeout.

**The three findings that shape it:**
1. **The save/resume half is BUILT+WIRED** — but every trigger is context-utilization,
   operator-stop, or crash. **Quota is a trigger nowhere.**
2. **The detection half is effectively GREENFIELD.** `429` appears nowhere in the repo; the
   401/403 rules are SKILL prose with **no executable owner** (`kata_models.py` never sees an
   error).
3. **★ BLOCKER + standalone defect: `tools/kata_dispatch.py:172-174` discards `proc.stderr`.**
   The provider's rate-limit message is destroyed before any classifier could see it. This
   degrades ALL error reporting today. **~10 lines + tests. Highest value-per-token item in the
   entire backlog — worth doing even if nothing else gets built.**

**Agreed scope:** Tier 1 (consecutive-failure run-wide lapse + a `kata_steer` kill-switch verb) +
Tier 2 (stderr fix · classifier · `human-required` escalation + breakthrough alert + auto-handoff ·
`degraded {scope:"provider"}`) in **ONE version-up**; Tier 3 (per-provider upgrade registry ·
silent-hang watchdog · preflight quota-headroom) is a **follow-on needing its own grill** — its two
legs each carry a policy decision that does not belong in the same freeze. Seven open grill
questions are enumerated in the brief §4.

**To start:**
```
cd C:\Dev\Projects\KataHarness      # start cwd INSIDE the repo (statusline/gauge scope)
/kata-start                          # → kata-initiate; hand it the REQUIREMENT.md as the brief
```
Framing for the mirror: `kind: version-up` · `target: self` · mode `standard` · grill `standard`.

## 3. SMALLER OUTSTANDING ITEMS (cheap, independent)

1. **Relink the installed kata-home to `0d3abc6`** — it is still on the pre-advisor SHA, so the
   49th skill is NOT installed yet. `& "$env:USERPROFILE\.kata-home\update.ps1"` from PowerShell
   with all other Claude sessions closed (see the Windows-update memory: `claude update` silently
   rolls back if any `claude.exe` holds the exe).
2. **Optional `v0.4.0` tag** — CHANGELOG sits at `[Unreleased] — Advisor consult (kata-advise)`.
   Operator's call; the advisor is a minor-version feature by semver.
3. **Fold the advisor's own recommended pinning tests** — `TestAdvisorDeferralCompat` (three pins:
   observe≠consume, exactly-one +1 after the advised failure, mid-deferral recount carries no
   mark). The sketch is archived verbatim in `.kata/advice/live-exercise-1-1.json` — it was the
   live consult's own output, deliberately NOT auto-applied (S-2).
4. **E-queue (unchanged):** E1 calibration proper · E2 adaptive live A/B (both now have real rows
   from D165/D167) · E6 health-review LOW/INFO residuals.
5. **F-9 / R6 remain honestly UNOBSERVED** — context never crossed 0.70 and no auto-compaction
   fired. Not broken; still queued. No false fire across two long sessions is itself
   correct-behavior evidence.

## 4. STANDING ORDERS (all prior orders hold)

cite-before-claim · done = gates + record + SHA · fresh-context adval before merge · D136
fail-closed · bump-on-modify + validator `--write` · branch → PR → merge · PD-1/PD-2 ·
**the conductor is the SOLE main-tree git writer** (subagents build no-git or in their own
worktrees) · closeout tripwire: `git stash list` empty + `git status` reviewed · gate runs go
through `tools/scripts/gauntlet.py`, never `pytest | tail && commit`.

**New this session (proven techniques, recorded in `.planning/LESSONS-LEARNED.md` and the transfer
doc):** supersede-don't-edit for grill findings (it is what made 5 convergence passes converge
instead of thrash) · the conductor re-verifies byte-untouched claims by `git diff` itself rather
than trusting worker reports · workers report ownership-boundary blockers instead of crossing lanes
(the conductor owns cross-task reconciliation) · aim the live n=1 exercise at the run's OWN riskiest
seam so proof-of-life doubles as verification input · under token pressure, verify with a
deterministic in-process battery (free) plus ONE cheap-model adversarial auditor **of the battery
itself**.

## 5. TRANSFER DOC (for the sibling loop project)

**`.planning/HANDOFF-ADVISOR-EXECUTOR.md`** — the complete, neutral-named, reproduction-grade
record of how this feature was designed and built end-to-end through the Kata Loop: the pattern
source, the grounding assessment, a phase-by-phase process log, the convergence journey with its
headline catches, and a running "transferable technique notes" section. Written for hand-off to
another loop project; carries **no work-linkage** on any surface. Complete as of merge.

## 6. GATE REPRODUCTION

From `tools/`: `uv run python scripts/gauntlet.py` (all four gates, honest exit).
Advisor smoke: `uv run python <scratchpad>/smoke_advisor.py` — the battery is session-scratchpad
only and was NOT committed (it asserts against `.kata/` run artifacts). **If you want it as a
permanent regression, promote it into `tools/tests/` with the fixture dependency replaced by a
constructed artifact** — a good small next-session task, and it is the natural home for the
`TestAdvisorDeferralCompat` pins from item 3 above.
