---
title: "WS-3 user-friendliness v0.1 — frozen PLAN"
status: FROZEN (freeze before dispatch; supersede-not-edit once orchestration starts)
date: 2026-06-24
mode: version-up (target.kind = self; baseline = current green master `1d41924`)
non-code-bearing: true   # contracts + skill prose only; footprint codeBearing:false ⇒ mutation-proof exempt (kata-evaluate rubric item 1 BC fallback)
design-ref: .planning/specs/ws3-user-friendliness/DESIGN.md (FROZEN; freeze-gate kata-review HOLD→SHIP)
ownership:
  A: [protocol/persona.md, protocol/engram.md]
  B: [protocol/narration.md]
  C: [modules/initiation/kata-initiate/SKILL.md]
  D: [skills/coordinate/kata-bootstrap/SKILL.md]
  E: [skills/coordinate/kata-orchestrate/SKILL.md]
  F: [modules/closeout/kata-closeout/SKILL.md, skills/evaluate/kata-report/SKILL.md]
waves:
  wave1: [A, B]
  wave2: [C, D, E, F]
depends_on:
  A: []
  B: []
  C: [A]
  D: [A]
  E: [A, B]
  F: [A]
tags:
  - kata/spec
  - ws3
  - ux
---

# WS-3 user-friendliness v0.1 — frozen PLAN

## Goal
Make the four human-facing surfaces — **intake, the decision tree, in-loop narration, and closeout** — legible,
warm, and goal-anchored, per the frozen DESIGN (L1–L11), **without weakening any spine invariant and without
faking gated capabilities.** Two new agnostic contracts (`persona.md`, `narration.md`) + a re-frame of the four
existing UX surfaces + one default-safe engram seam. **Non-code-bearing:** no new Python, no new config field, no
validator change. The build itself runs as an orchestrated version-up dogfood (per `exercise-harness-for-real`)
and its **own closeout uses the new goal-anchored closeout** (slice F dogfoods itself).

## LOCKED decisions (distilled from DESIGN L1–L11; no worker may re-decide — conflict ⇒ escalate human-required)
- **K1 — Default register = moderate non-expert** (static default, stated in `persona.md`). Adaptive register is
  a **named, gated seam, NOT live** (engram CONSULT off, D9/D56/D74). Never imply adaptivity is live. (DESIGN L1/L8.)
- **K2 — Persona = the calm kata-craftsperson-who-translates**, **nameless** (the harness's own voice). Warm
  through clarity, plain-language-first, never kawaii/unserious, never inflation/overclaim. (DESIGN L2.)
- **K3 — Reference contracts by path, never by `[[wikilink]]`.** `protocol/persona.md` and `protocol/narration.md`
  are protocol contracts; skills reference them as `protocol/<file>.md` (wikilinks resolve to *skills*, so a
  `[[persona]]` link would fail validation). Do NOT add either to the validator's `REQUIRED_PROTOCOL` (that is a
  code change; this run is non-code-bearing).
- **K4 — Intake gate refinement preserves the S2 anti-drift requirement.** Presentation → infer-then-confirm;
  requirement → **every frozen INTENT value traces to an explicit human confirmation.** The rewritten
  gate-checklist MUST require each load-bearing value (kind / target.kind / target.path / vault / platform /
  grillDepth / dual-control execute) be **individually visible in the reflected-back mirror AND survive into the
  frozen `INTENT.md` unchanged-or-corrected**; a blanket "looks good" over un-itemized inferred values FAILS the
  gate. (DESIGN L3/L4.)
- **K5 — Mode dial maps to EXISTING `kata.config` fields only:** `mode` + `tiers["kata-grill"]` +
  `delivery.boundary`. No new config field; the composition ladder becomes the "advanced drawer." `kata.config`
  schema unchanged. (DESIGN L5.)
- **K6 — Narration: milestone + breakthrough; never stage names; honesty guard.** Plain-language at boundaries,
  quiet between; the **breakthrough invariant** (decisions/escalations/critical failures surface immediately) is
  **never tiered**; `narration.md` MUST NOT narrate un-wired autonomy. The `改善型` dashboard/board stay the
  firehose (unchanged). (DESIGN L6.)
- **K7 — Closeout: goal-anchored by-aspect synthesis; leads with plain-language what-changed-why; NEVER gates.**
  `kata-evaluate`'s verdict is read verbatim and surfaced; closeout never confers pass/fail. (DESIGN L7/L10.)
- **K8 — Backout (WS-4) anchors on `.kata/RESULT.json.baselineSha`** (already read by `kata-closeout`), offered in
  plain language at the human gate, **human-gated & never autonomous** (`git reset --hard` to the baseline, diff
  shown first, explicit approval), exactly like commit/push/merge. A `pre-<run>` tag is optional convenience, not
  the guaranteed anchor. (DESIGN L9.)
- **K9 — Spine untouched** (default-FAIL, no-drift, no-self-cert, two-way handoff, everything-versioned). WS-3
  changes presentation + voice only. (DESIGN L10.)
- **K10 — Disjoint ownership** (each worker edits ONLY its `ownership:` files). **Roster:** workers = **Sonnet**;
  orchestrator + `kata-evaluate` + the build grader = **Opus** (Fable 5 unavailable, D59). (DESIGN §6.)
- **K11 — Policy A:** skills stay `version: 0.1.0`; modifications do NOT bump (pre-v0.1 hold). New protocol
  contracts carry no semver (they are not skills). (STANDARDS §3.)

---

## Slices

### A — persona/SOUL contract + register seam · wave 1 · not code-bearing
- **read_first:** `protocol/engram.md` (seam-table format + the maintenance rule; note the highest existing E-id
  — slop-check added E22), `CONTEXT.md` (the `exercised vs proven` + persona-adjacent terms), `docs/STANDARDS.md`
  §5 (Obsidian-native durable artifacts), DESIGN §3 (L2/L8) + §4.1 + §4.3.
- **action:**
  1. **Create `protocol/persona.md`** — the agnostic SOUL contract, four sections (Hermes `SOUL.md` structure):
     - **Identity** — the calm kata-craftsperson (改善型) who one-shots complex work and **always translates**:
       "what I did and why it matters to you." Nameless (the harness's own voice, not a mascot).
     - **Style** — plain-language-first; warm through clarity, not chatter; lead with outcomes, not machinery;
       milestone not stream; concise; honest (name uncertainty + *exercised-not-proven*; never hedge once done).
     - **Avoid** — internal stage names (GRILL/FREEZE/…); jargon dumps; kawaii/unserious affect; inflation /
       overclaim; narrating capabilities that are gated off.
     - **Defaults** — **register = moderate non-expert** (static v0.1 default); the agnostic voice is rendered
       per-platform by the adapter (Claude→CLAUDE.md/AGENTS.md; others per adapter).
     - A short **"Register adaptation (seam, gated — not live)"** note: today register is the static moderate
       default; adaptation is the engram seam below, lit only when CONSULT matures (D9/D56). State plainly that
       claiming adaptive register is live is a forbidden overclaim (K1).
  2. **Modify `protocol/engram.md`** — add ONE seam row (next E-id after E22, i.e. **E23**) for
     register-adaptation: LEARN surface = the user's observed comprehension/correction signals + grill-ledger
     choices (D72); latent CONSULT = set the persona register from the matured fingerprint; **gated off** (D9/D56),
     emit/observe-only, zero CONSULT — same posture as every other engram seam. Match the existing row format and
     honor the "register a seam in the same change" maintenance rule.
- **acceptance:** `persona.md` exists with the four named sections + nameless note + moderate-register default +
  the gated register-seam note (K1/K2); `engram.md` carries a well-formed E23 row with substrate/seam distinction
  + gated-off CONSULT; **not** added to `REQUIRED_PROTOCOL` (K3); `validate_skills.py` green (engram.md is already
  validator-enforced, so its schema must stay valid).
- **verify:** `cd tools && uv run python validate_skills.py` ; `grep -n "register" protocol/persona.md` returns
  the default + seam; `grep -n "E23" protocol/engram.md` returns the new row.

### B — narration contract (phase→plain-language map) · wave 1 · not code-bearing
- **read_first:** `protocol/board.md` (the existing PROGRESS/board event model the dashboard tails — narration is
  the *conversation* channel, distinct from the board firehose), `CONTEXT.md` (loop vocabulary — the Kata Loop /
  the Harness / phases), DESIGN §3 (L6) + §4.1.
- **action:** **Create `protocol/narration.md`** with:
  1. **The phase→plain-language map** — a table: internal activity → the human-action phrasing the narrator uses
     in the conversation. Cover at least: grill ("working out and pressure-testing the plan against your goal"),
     freeze ("locking the plan so it can't drift"), pre-flight ("getting the tools it needs ready"), execute /
     parallel workers ("building the pieces — N in parallel"), evaluate ("checking the work honestly against a
     fresh pair of eyes"), handoff, escalation ("I hit a fork I want your call on"), loop-back ("starting the next
     improvement pass, carrying what we learned"). **Internal stage names are never surfaced** (K6).
  2. **The milestone-cadence rule** — narrate at meaningful boundaries, quiet between (trust, not spam; the
     dashboard/statusline carry the granular live view).
  3. **The breakthrough-alert rule** — decisions/escalations/critical failures surface in the conversation
     immediately and unmissably, regardless of routine quiet; **this invariant is never tiered** (K6 / D33-class).
  4. **The honesty guard** — narration describes only what is actually happening; it MUST NOT narrate un-wired
     autonomy (e.g. "researching this myself" implying a standing RS call-site, or "learning from this" implying
     live CONSULT). (K1/K6.)
- **acceptance:** `narration.md` exists with the map table + cadence rule + breakthrough rule + honesty guard;
  no stage names presented as user-facing; not added to `REQUIRED_PROTOCOL` (K3); `validate_skills.py` green.
- **verify:** `cd tools && uv run python validate_skills.py` ; `grep -niE "breakthrough|never tiered" protocol/narration.md` returns the invariant.

### C — intake reflective goal mirror (`kata-initiate`) · wave 2 · not code-bearing · depends_on A
- **read_first:** `modules/initiation/kata-initiate/SKILL.md` (current Phases 0–6 + the "STOP — ask, do not infer"
  gate + the evaluator gate-checklist), `protocol/persona.md` (slice A — voice), `protocol/intent.md` (the frozen
  INTENT contract + `write_intent` authority), DESIGN §3 (L3/L4) + §4.2.
- **action:** Re-frame the front of `kata-initiate` into the **reflective goal mirror** while preserving the
  freeze machinery:
  - Synthesize the inputs (system prompt + any brief + light research + the grill) into a **plain-language
    mirror**: *"here's what you want / what success looks like / here's how I'd set it up"* — including the
    **proposed config in human terms** (kind / target / vault / platform / grill-depth), not a naked form.
  - The human **edits the mirror conversationally** until confirmed; *then* freeze `INTENT.md` (via
    `write_intent` — still the ONLY authorized writer; INTENT.md authority unchanged).
  - **Rewrite the "STOP — ask, do not infer" gate to infer-then-confirm** AND **give the evaluator gate-checklist
    teeth (K4):** the evaluator confirms each load-bearing value (kind / target.kind / target.path / vault /
    platform / grillDepth / dual-control execute) was **individually visible in the reflected-back mirror AND
    survived into the frozen `INTENT.md` unchanged-or-corrected**; a blanket "looks good" over un-itemized
    inferred values **FAILS** the gate. Keep the rule that every frozen value traces to a human confirmation.
  - Voice per `protocol/persona.md` (reference by path, K3). Do not touch other skills' files.
- **acceptance:** the front reads as the mirror (synthesize → reflect incl. proposed config → confirm/edit →
  freeze); the gate is infer-then-confirm with the per-value teeth (visible-in-mirror + survived-to-INTENT;
  blanket-approval fails); `write_intent` remains the sole writer; persona referenced by path; no `[[persona]]`
  wikilink; `validate_skills.py` green.
- **verify:** `cd tools && uv run python validate_skills.py` ; `grep -niE "individually visible|FAILS the gate|mirror" modules/initiation/kata-initiate/SKILL.md` returns the gate teeth.

### D — mode surface re-frame (`kata-bootstrap`) · wave 2 · not code-bearing · depends_on A
- **read_first:** `skills/coordinate/kata-bootstrap/SKILL.md` (Phases 0–4 + the D24c composition ladder +
  Phase 1.5 grill-depth dial), `protocol/config.md` (the `mode` / `tiers` / `delivery` fields the dial maps to),
  `protocol/persona.md` (voice), DESIGN §3 (L5) + §4.2.
- **action:** Re-frame the surface (presentation only — `kata.config` writing unchanged, load-guard unchanged):
  - **Infer** run-shape + mode + grill-depth + delivery from the goal and **state it in plain outcome language**
    ("I'll do a thorough build and check with you at the end").
  - Surface **exactly one** plain dial — *"how careful / how often should I check with you"* — that maps to
    **existing** fields: `mode` + `tiers["kata-grill"]` + `delivery.boundary` (K5). Document the mapping (more
    careful ⇒ higher mode + deeper grill + `always-stop`; lighter ⇒ lower mode + lighter/skip grill).
  - Move the full composition ladder (D24c rungs 2–4 + cost preview) behind an **"advanced settings" drawer** —
    available, not default. The default→go floor stays one keystroke.
  - Voice per `protocol/persona.md` (by path, K3).
- **acceptance:** the surface infers + states in plain language + offers the one dial with the documented
  field-mapping; the ladder is preserved as the advanced drawer; **no new config field**; `kata.config` schema +
  load-guard unchanged; `validate_skills.py` green.
- **verify:** `cd tools && uv run python validate_skills.py` ; `grep -niE "how careful|advanced settings|delivery.boundary" skills/coordinate/kata-bootstrap/SKILL.md` returns the dial + drawer + mapping.

### E — milestone narration (`kata-orchestrate`) · wave 2 · not code-bearing · depends_on A, B
- **read_first:** `skills/coordinate/kata-orchestrate/SKILL.md` (the dispatch/frontier sections — DO NOT change
  dispatch logic), `protocol/narration.md` (slice B), `protocol/persona.md` (slice A), `protocol/board.md` (the
  firehose channel, unchanged), DESIGN §3 (L6) + §4.2.
- **action:** Add an **additive narration section** to `kata-orchestrate` (no change to frontier/dispatch/gate
  logic — orchestrate stays the dispatcher, D24d):
  - At meaningful boundaries, **narrate to the conversation in plain language per `protocol/narration.md`** (never
    stage names); stay quiet between; the `改善型` dashboard/statusline/board remain the granular firehose
    (unchanged).
  - State the **breakthrough-alert invariant** (decisions/escalations/critical failures surface immediately;
    never tiered) and the **honesty guard** (no un-wired-autonomy narration). Reference `narration.md` +
    `persona.md` by path (K3/K6).
- **acceptance:** orchestrate has the milestone-narration + breakthrough + honesty-guard section referencing
  `narration.md`/`persona.md`; **frontier/dispatch/gate prose unchanged** (diff is additive); `validate_skills.py`
  green.
- **verify:** `cd tools && uv run python validate_skills.py` ; `grep -niE "narration.md|breakthrough" skills/coordinate/kata-orchestrate/SKILL.md` returns the section; confirm by diff that the dispatch logic is untouched.

### F — goal-anchored closeout + offered backout (`kata-closeout` + `kata-report`) · wave 2 · not code-bearing · depends_on A
- **read_first:** `modules/closeout/kata-closeout/SKILL.md` (Steps 1–5 + the never-gates boundary + the
  human-gated git note lines 119–122), `skills/evaluate/kata-report/SKILL.md` (current report shape),
  `protocol/persona.md` (voice), DESIGN §3 (L7/L9/L10) + §5 (the fixed skeleton).
- **action:**
  - Re-frame `kata-closeout`'s report + human-gate into the **§5 skeleton**, in order: **(1)** restate the goal
    (plain, from `INTENT.md`) → **(2)** **lead with what-changed-and-why in plain language, organized by
    goal-aspect** (before any path/gate number — the WS-5 requirement; each parallel worker's result folds into
    the goal-aspect it served) → **(3)** did-it-hit-the-goal assessment → **(4)** risks + uncertainties (incl.
    *exercised-not-proven* honesty) → **(5)** evidence linked not dumped (`.kata/RESULT.json`, the report, the
    understand-map **if generated**, findings files) → **(6)** offered options.
  - **Add the WS-4 backout (K8):** in the human-decision gate, offer in plain language "I can cleanly roll this
    entire run back, as if it never happened," anchored to **`.kata/RESULT.json.baselineSha`** (already read in
    Step 1); execution = `git reset --hard <baselineSha>`, **human-gated & never autonomous** (diff shown first,
    explicit approval), under the same guard as commit/push/merge. Foreground it when the human is not satisfied.
  - **Preserve never-gates (K7):** `kata-evaluate`'s verdict is read verbatim and surfaced; a NEEDS_WORK is
    reported plainly, never overridden.
  - **Modify `kata-report`** to produce the **by-goal-aspect synthesis** (group changes by the goal-aspect each
    served), in the persona voice (`protocol/persona.md`, by path).
- **acceptance:** closeout follows the §5 order and **leads with plain-language what-changed-why**; backout is
  offered, baselineSha-anchored, human-gated/never-autonomous; report does by-aspect synthesis; never-gates
  preserved; persona referenced by path; `validate_skills.py` green.
- **verify:** `cd tools && uv run python validate_skills.py` ; `grep -niE "baselineSha|roll this entire run back|goal-aspect" modules/closeout/kata-closeout/SKILL.md skills/evaluate/kata-report/SKILL.md` returns the backout + synthesis.

---

## Orchestration sequence (operator-gated; per HANDOFF §5, never inline)
1. **FREEZE** (this doc) + `git tag pre-ws3` on baseline `1d41924` (backout point). ◆ operator go.
2. **Wave 1:** `git worktree add` per slice; dispatch **A, B concurrently** (Sonnet), scoped to owned files, voice
   authored against the DESIGN. Board records CLAIM with timestamps; **workers self-stamp start/end** (the WS-2
   follow-up — provable concurrency from artifacts, cheap to do here).
3. **Integrate wave 1:** branch off master, `git merge --no-ff` A + B (disjoint ⇒ no conflict).
4. **Wave 2:** as A integrates → C, D, F dispatchable; as A + B integrate → E dispatchable. Dispatch concurrently
   (Sonnet), each in its own worktree.
5. **Integrate wave 2:** octopus/linear merge (disjoint ownership), `cd tools && uv sync` (no dep change expected).
6. **Final gate (default-FAIL):** `uv run pytest -q` (expect **447**, unchanged — non-code) + `validate_skills.py`
   (expect **36/0**, unchanged — no new skill) + **Snyk N/A** (no new/changed Python). Emit `.kata/RESULT.json`
   via `gate_emit`; **`footprint.json.codeBearing` must be `false`** (markdown-only) ⇒ mutation-proof exempt
   (kata-evaluate rubric item 1 BC fallback). No `research-needed` escalation is expected (facts are in-repo).
7. **Fresh-context `kata-evaluate`** — SEPARATE no-write Opus subagent, 8-rubric, default-FAIL. **No self-cert.**
   Must PASS. Plus a **build-acceptance check** (below).
8. **Closeout — dogfood slice F:** run the NEW goal-anchored closeout on this very build (restate goal → lead with
   plain-language what-changed-why → progress → risks → linked evidence → offered backout). ◆ operator reviews.
9. **At the operator boundary:** STOP and ask via `AskUserQuestion` (satisfied? / commit·push·merge? / run-again?).

## Build-acceptance check (graded after the run, fresh-context, in-context — maps to DESIGN L1–L11)
1. **persona.md** has the four SOUL sections + nameless + moderate default + gated register-seam note (K1/K2). ✅/❌
2. **narration.md** has the phase→plain map + milestone cadence + never-tiered breakthrough + honesty guard (K6). ✅/❌
3. **No stage names** (GRILL/FREEZE/…) surfaced as user-facing in any re-framed surface (K6). ✅/❌
4. **Intake gate teeth** present (each value visible-in-mirror + survived-to-INTENT; blanket approval fails) (K4). ✅/❌
5. **Mode dial** maps only to existing `mode`/`tiers["kata-grill"]`/`delivery.boundary`; **no new config field** (K5). ✅/❌
6. **Closeout** leads with plain-language what-changed-why, by goal-aspect; **never gates** (K7). ✅/❌
7. **Backout** offered, anchored on `.kata/RESULT.json.baselineSha`, human-gated/never-autonomous (K8). ✅/❌
8. **No overclaim:** nothing implies adaptive register or un-wired autonomy is live (K1) — and the writeup itself
   is free of inflation (the `kata-slop-check` standard applied to our own closeout). ✅/❌
9. **Disjoint drift:** every file touched ⊆ its slice ownership; spine invariants intact (K9/K10). ✅/❌
10. **Green:** pytest 447 · validator 36/0 · Snyk N/A; `footprint.codeBearing == false`. ✅/❌

## Gate & backout
- **Gate:** `cd tools && uv run pytest -q && uv run python validate_skills.py`. (Snyk N/A — no Python touched. If
  any `.py` is unexpectedly modified, the run is no longer non-code-bearing → run `snyk_code_scan` and add a
  mutation proof — but the PLAN forbids touching Python, so this should not happen; if it does, **escalate**.)
- **Backout (offered at closeout):** `git reset --hard pre-ws3` (tag set in step 1) — surfaced as a first-class
  plain-language option (this build dogfoods K8's own pattern).

## Carry-outs (NOT in this run)
- Promote K1–K11 / DESIGN L1–L11 to `DECISIONS.md` D-numbers (D95+) at build-merge, with STATE/HANDOFF/BACKLOG
  updates (WS-3 ✅, WS-4/WS-5 folded) — same cadence as WS-2 got D94 at build.
- Lighting up adaptive register (gated — needs mature engram CONSULT, D9/D56). The E23 seam is the future site.
- Adapter-specific persona rendering for non-Claude hosts (v0.3 adapter work; the contract is agnostic now).
- WS-1 pre-launch public-sanitization re-grep (independent pre-public tail).
