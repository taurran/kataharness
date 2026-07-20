# REQUIREMENT — quota-resilience (provider rate-limit / token-exhaustion graceful stop + resume)

> **Status: PRE-GRILL INTAKE BRIEF — not frozen, not designed, nothing built.**
> Written 2026-07-20 at operator direction, end of the advisor-executor session (D167, PR #39).
> This file exists so the next session can go straight to `/kata-start` with full grounding and
> zero re-research. Every claim below is cited to file:line and was verified by a fresh-context
> research pass on 2026-07-20 against master `0d3abc6`.

## 1. The operator's ask (verbatim intent)

Two related things, raised after the advisor-executor merge:

1. **Advisor-specific:** what happens if Fable is unavailable when the advisor tries to consult?
   Add a kill-switch so a session can **skip the remaining consults** and report the error +
   reasoning at loop closeout.
2. **General (the bigger ask):** session/plan **rate-limit and token-quota exhaustion handling,
   per provider** (Anthropic, OpenAI, Cursor, Gemini, …). When the operator runs out of tokens
   the harness should: tell them plainly they're out; **use the pause/continue machinery to save
   state** so they can return and pick up exactly where they left off; and **emit the
   provider-specific upgrade path** — the slash command or the account URL to add capacity.

Operator belief at the time: "I think we laid the groundwork already, but I would like to confirm
it's wired and working." **Answer: half true — see §2.**

## 2. GROUND TRUTH (verified 2026-07-20, master `0d3abc6`)

### 2a. WIRED AND WORKING — the save/resume half

| Piece | Status | Trigger TODAY |
|---|---|---|
| `kata-selfhandoff` (`skills/handoff/kata-selfhandoff/SKILL.md:30-44`) | BUILT+WIRED | context utilization only (`contextTrigger` 0.70 × host window, via `kata_gauge`), evaluated at wave/frontier boundaries |
| `tools/kata_gauge.py:96-124`, `:273 trigger_crossed` | BUILT+WIRED | bridge schema = `{session_id, remaining_percentage, used_pct, timestamp, total_tokens}` — **context window ONLY; no plan/quota field exists** |
| `adapters/claude/hooks/kata-gauge-check.py`, `kata-precompact.py` | BUILT+WIRED | per-turn context check / host auto-compaction |
| `tools/kata_steer.py:67-83 stop_requested` | BUILT+WIRED | operator-initiated only (`AGENT_STOP` file / `## AGENT_STOP` sentinel) |
| `tools/kata_restore.py` (`detect_lost_run:55`, `read_board_from_trail:103`, `fold_board:132`, `collect_integrated_tasks:324`, `compute_redispatch_set:629`, `restore:718`) | BUILT+WIRED | crash / lost run (tier-3 `.kata/` wiped ⇒ rebuild from `refs/kata/trail` + `Kata-Task:` trailers) |
| `/kata-resume` → `kata-orient` → `kata-handoff` (`adapters/claude/commands/kata-resume.md`) | BUILT+WIRED | operator-invoked resume |

**The gap in this half:** every trigger is context-utilization, operator-stop, or crash.
**A model-quota-exhaustion event is a trigger NOWHERE.**

**Resume proof honesty:** resume-after-session-limit-kill is live-proven *by manual operator
playbook*, NOT by `kata_restore` (`.planning/STATE.md:115`; `NEXT-SESSION-ORIENTATION.md:160` —
"resume each agent via its agentId with a 're-verify your owned files on disk first' preamble").
`kata_restore`'s own live-proofs cover the installer and PreCompact hook, not an end-to-end
mid-run restore (`specs/restore-hardening/PLAN.md:54,119`).

### 2b. ABSENT — the detection half (treat as GREENFIELD)

- **429 / rate-limit / quota detection: ABSENT.** The string `429` appears nowhere in the repo
  outside `uv.lock` hashes. No retry-after parsing, no rate-limit branch, no quota probe.
- **401/403 handling: PROSE-ONLY, no executable owner.** Two rules exist as conductor prose:
  `kata-orchestrate/SKILL.md:952-956` (baseline R2 carve-out ⇒ `human-required` escalation) and
  `:973-977` (premium rung ⇒ `premium-unavailable`, OMIT-inherit + LOUD + `degraded {scope:
  "premium", reason: "auth-40x"|"unavailable"}`), plus `:970-972` (ANY premium dispatch failure
  lapses `models.premium.approved` for the run). **`kata_models.py` never sees an error;
  `fallback_chain` (`:1067-1110`) is pure ladder arithmetic.** The docs say "auth / quota" but
  the detector is 401/403 only — a 429 or plan-limit message is out of scope entirely.
- **★ THE BLOCKER — `tools/kata_dispatch.py:172-174` DISCARDS `proc.stderr`.** `_subprocess_runner`
  runs with `capture_output=True` but returns **only `proc.stdout`**. A provider CLI's rate-limit
  message is destroyed at that line before anything could classify it. Everything then collapses
  at `:200-204` (`exit_code != 0` ⇒ `"failed"`, `{"error": f"worker exited {exit_code}"}`) with
  no status-code inspection. `_STATUS = frozenset({"completed","failed","timeout","fallback"})`
  (`:38`). **This is a standalone defect degrading ALL error reporting today, independent of this
  feature.**
- **Per-provider registry: ABSENT (confirmed by grep of `tools/`, `protocol/`, `adapters/`).** No
  upgrade URLs, plan/quota metadata, or billing links anywhere. The richest source material is
  `docs/platforms/*.md` (codex-cli, cursor, kiro, copilot, gemini-cli) — **human prose, unparsed,
  loaded by no tool.**
- **Non-Anthropic ladders are empty stubs** (`kata_models.py:72-84`: `_OPENAI_LADDER`,
  `_GEMINI_LADDER`, `_GENERIC_LADDER` all `[]`); `ID_MAP:89` is Anthropic-only; `family_of` (`:268-291`)
  resolves family by ladder membership, so a non-Anthropic anchor resolves to no family
  (`CLAUDE.md:25` confirms: non-Anthropic families run everything at the anchor).

### 2c. THE HARD LEG — the silent hang

`docs/platforms/codex-cli.md:89`: **"Hang-on-402, no exit code. Quota/insufficient-credit (HTTP
402) errors are not surfaced."** `:92-93`: codex shares a 5-hour rolling quota across interactive
and headless `exec` — "a long unattended loop can silently exhaust quota." With no exit code, this
lands at `kata_dispatch.py:197-198` (`TimeoutExpired → "timeout"`), **indistinguishable from a slow
task.** Solving it needs a watchdog heuristic ("no output for N seconds on a task that should be
streaming") and is the leg most likely to produce false positives. `docs/platforms/cursor.md:74,93-94`
flags headless exhaustion behavior as an undocumented, load-bearing open gap.

### 2d. REUSABLE SURFACES (wiring, not new engine)

- **Breakthrough alert** (`protocol/narration.md:68-90`) — the established never-tiered pattern for
  surfacing an unmissable blocked-on-human condition. Needs a trigger, not a mechanism.
- **Escalation** (`protocol/escalation.md:5-19`) — reuse `kind: "human-required"` UNCHANGED,
  carrying the quota distinction in `decisionNeeded`/`rationale`. Precedent for exactly this:
  `escalation.md:42-55` (thrash routing, "no enum change (L6)").
- **Degraded ledger record** — `[{scope, reason}]` (`protocol/observability.md:33`;
  `.planning/telemetry-ledger.md:11-22`; D142). Producer `kata_telemetry.build_ledger_row:1405` is
  an **unvalidated passthrough** (`row["degraded"] = list(run_summary.get("degraded", []))`), unlike
  its fail-closed siblings `_validate_failure_kinds:1087`, `_validate_verdict_by_tier:1134`,
  `_validate_tier_events:1190`. Adding a quota reason costs nothing schema-wise — but nothing
  enforces it either; matching the `_validate_*` pattern is the consistent choice.
- **Preflight BLOCK shape** — `tools/kata_preflight.py:16` (`gate_status`) and especially
  `stranding_verdict(...)` (`:796-812`, CA-L25) is the shaped precedent for a walk-away-run BLOCK;
  a quota-headroom leg fits its signature style.
- **Handoff kinds** — `protocol/handoff.md:19` `kind: manual|self|boundary`. A quota-triggered
  handoff needs a 4th value or a deliberate reuse of `self` (a grill branch).
- ⚠ **Do NOT conflate:** `kata_adaptive.py:113` reason enum already contains `"budget-exhausted"` —
  that is **kata's own internal premium/advisor spend budget**, not provider quota. Same word,
  different thing.

### 2e. PRIOR ART — nothing backlogged, three real incidents

No D-record, no BACKLOG item, no spec directory for this (48 specs, none quota-related). But
session-limit kills hit this project at least three times and were each recovered **manually**:
`.planning/STATE.md:115` (mid-build kill, 5 builders resumed clean); `DECISIONS.md:1489`, `:1527`,
`STATE.md:590` (session-token-limit cut the freeze-gate mid-verdict twice ⇒ re-ran a fresh gate);
`.planning/NEXT-SESSION-ORIENTATION.md:160` (the standing manual playbook). `BACKLOG.md:14` cites a
session-limit kill only as a *hazard amplifier* for the mutation-on-disk class, not as a feature gap.
**The Fable outage** (`CLAUDE.md:25`, `docs/STANDARDS.md:30,64`) is an *availability/model-gating*
lesson (⇒ R2/R7: never hard-bake a model id, OMIT terminus), NOT a quota lesson — but
`specs/context-autonomy/GRILL-LEDGER.md:358` carries the load-bearing anti-retry rule:
*"Retry-per-task would recreate the exact Fable-outage retry pattern R2 exists to prevent."*

## 3. PROPOSED SCOPE (operator-reviewed 2026-07-20; tiers agreed, build NOT authorized yet)

### Tier 1 — provider-unavailable lapse + operator kill-switch (small, < 1 wave)
Generalize the advisor's per-task failure posture into a run-wide safety net for ANY dispatch
consumer:
- **N consecutive failed dispatches (N=2) ⇒ run-wide lapse** with reason `advisor-unavailable` /
  `provider-unavailable`, mirroring the existing budget-exhaustion lapse
  (`kata-orchestrate/SKILL.md:1128-1130`) and the premium CA-L30 discipline (`:970-972`).
- **Operator kill-switch:** a `STEERING`-file verb (the D151 `tools/kata_steer.py` engine already
  exists and is polled at boundaries) — e.g. `ADVISOR_OFF` ⇒ lapse for the run's remainder, reason
  `operator-directed`.
- Both reasons flow into the **existing** after-action rollup + handoff note with zero new
  reporting work (`kata-orchestrate/SKILL.md:1194-1200`, Final-gate step 8 `:1518-1526`).

**Why this matters TODAY:** the advisor's failure lapse is scoped **per-task**, not run-wide
(deliberate — a single flaky consult shouldn't kill the advisor for a whole run). Under global
Fable unavailability (now live — Fable moved to API rates 2026-07-20) EVERY task's first consult
fails, burning one doomed dispatch + latency each. It IS bounded (budget exhaustion lapses run-wide
at 5 calls standard / 10 advanced), so worst case is 5–10 pointless round-trips, then unadvised to
completion with correct reporting. Wasteful, not dangerous.

### Tier 2 — real quota handling (roughly doubles Tier 1)
- **Fix the stderr discard** (`kata_dispatch.py:172-174`) — ~10 lines + tests. **Independently
  worth doing even if nothing else is built.**
- Per-provider **classifier** for the clean-error case (nonzero exit + parseable signal: 429, 402,
  plan-limit text).
- Route to `human-required` escalation (enum unchanged, L6 precedent) + **breakthrough alert** +
  an **automatic handoff write**, so the run parks itself cleanly and `/kata-resume` picks it up.
- `degraded {scope:"provider", reason:"quota-exhausted"|"rate-limited"}` ledger record.

### Tier 3 — registry + watchdog (follow-on, its own grill)
- Machine-readable **per-provider registry**: upgrade slash-command or account URL, surfaced in the
  block message. Source material = `docs/platforms/*.md`. **Open decision:** maintenance burden —
  upgrade URLs drift; who owns freshness?
- **Silent-hang watchdog** for the codex-402 class. **Needs its own grill** for false-positive
  policy (killing a legitimately slow worker is worse than a late quota detection).
- **Preflight quota-headroom check** (shaped like `stranding_verdict`).

**Recommendation on record:** Tier 1 + Tier 2 in ONE version-up; Tier 3 as a follow-on with its own
grill. Tier 3's two legs each carry a policy decision that does not belong in the same freeze.

## 4. OPEN QUESTIONS FOR THE GRILL

1. **Handoff kind:** new 4th `kind: quota` in `protocol/handoff.md:19`, or deliberate reuse of
   `self`? (BC implications either way.)
2. **N for the consecutive-failure lapse** — 2, or provider-signal-dependent (fire on the FIRST
   401/403/429, matching the premium `premium-unavailable` precedent, vs. 2 for generic failures)?
3. **Steering verb vocabulary** — one generic verb with an argument (`KATA_OFF <subsystem>`) or
   per-subsystem verbs (`ADVISOR_OFF`)? Does it belong in `kata_steer.py`'s existing sentinel
   grammar or a new file?
4. **Auto-resume vs. park-and-tell** — on quota exhaustion, does the harness write the handoff and
   STOP (recommended: quota takes wall-clock hours to reset), or poll/retry-after?
5. **Registry freshness/maintenance** (Tier 3) — and whether a wrong/stale upgrade URL is worse
   than no URL (PD-2 posture).
6. **Non-Anthropic ladders** (`kata_models.py:75-77`) — populate them as part of this, or leave
   empty? For THIS feature fallback-to-a-cheaper-model is arguably the WRONG response (the operator
   wants to be told + parked, not silently downgraded) — confirm.
7. Does the quota trigger belong on the **gauge** (extend the bridge schema with a quota field, if
   any host ever reports one) or purely on **dispatch-result classification**? Today no host
   surfaces plan quota — so dispatch classification is the only real signal source.

## 5. HOW TO START THE NEXT SESSION

```
cd C:\Dev\Projects\KataHarness     # start cwd INSIDE the repo (statusline/gauge scope)
/kata-start                         # → kata-initiate; feed it THIS file as the brief
```
Suggested framing for the mirror: `kind: version-up` · `target: self` · mode `standard` ·
grill depth `standard` (the decision tree is enumerated in §4; richness is high). Tier 1+2 is the
proposed scope; Tier 3 deferred by design.

## 6. RELATED / DO FIRST (independent, cheap)

- **`kata_dispatch.py` stderr fix** — Tier 2's first item, but valid as a standalone ~10-line
  commit. Highest value-per-token item in this whole brief.
- Outstanding from the advisor run (D167): relink installed kata-home to master `0d3abc6`
  (`update.ps1`) · optional `v0.4.0` tag (CHANGELOG sits at Unreleased) · fold the advisor's own
  recommended `TestAdvisorDeferralCompat` pinning tests (sketch archived in
  `.kata/advice/live-exercise-1-1.json`).
