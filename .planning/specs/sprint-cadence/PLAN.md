---
date: 2026-06-19
spec: sprint-cadence
status: FROZEN — human-approved 2026-06-19 (M1 = evaluate). Changes are deliberate re-freezes. → kata-orchestrate
tier: kata-plan-advanced
design-ref: ./DESIGN.md (FROZEN, D78–D85)
green-baseline: validator 29 skills / 0 errors · pytest 27 passed · Snyk 0
ownership:
  T1: [protocol/config.md]
  T2: [protocol/state.md]
  T3: [protocol/handoff.md, protocol/escalation.md]
  T4: [skills/plan/kata-plan/ROADMAP.md, skills/plan/kata-plan/RUBRIC.md, skills/plan/kata-plan-essential/SKILL.md, skills/plan/kata-plan-standard/SKILL.md, skills/plan/kata-plan-advanced/SKILL.md]
  T5: [skills/handoff/kata-selfhandoff/SKILL.md]
  T6: [skills/coordinate/kata-readiness/SKILL.md]
  T7: [skills/coordinate/kata-sprint/SKILL.md]
  T8: [skills/evaluate/kata-report/SKILL.md]
  T9: [skills/handoff/kata-handoff/SKILL.md]
  T10: [tools/validate_skills.py, tools/tests/test_validate_skills.py]
  T11: [docs/TAXONOMY.md, README.md, .planning/ROADMAP.md, .planning/STATE.md, .planning/DECISIONS.md]
waves:
  wave1: [T1, T2, T3, T8]
  wave2: [T4, T5, T6, T9]
  wave3: [T7]
  wave4: [T10]
  wave5: [T11]
depends_on:
  T4: [T1]
  T5: [T1]
  T6: [T2]
  T7: [T3, T4, T8]
  T9: [T3]
  T10: [T1, T2, T3, T4, T5, T6, T7, T8, T9]
  T11: [T10]
tags: [plan, draft, sprint-cadence, dag, file-ownership, waves, advanced]
---

# sprint-cadence — BUILD PLAN (advanced)

> **The plan adds no new decisions** — it only sequences the FROZEN DESIGN (D78–D85). Every `action` quotes a
> LOCKED item verbatim. Net skill delta: **29 → 31** (+`kata-sprint`, +`kata-report`). The roadmap layer is a
> shared **method file** in the `kata-plan` family folder (like its `RUBRIC.md`), not a validator-counted skill.

## Decomposition note (why these slices)
Vertical tracer-slices, each a coherent capability cut through its layers; ownership = the files each slice
touches. Three files are genuinely shared by many slices, so per the RUBRIC they are **sequenced as their own
single task** rather than split horizontally: `tools/validate_skills.py`+tests (**T10**, asserts every new
protocol term + new skill) and the docs/index bundle (**T11**, README `--write` + TAXONOMY + planning). All
other ownership is disjoint by construction.

## Build-time grounding (D83 — do FIRST, inside T1)
Before writing any prime-frame number: **WebSearch the real current Fable 5 and Sonnet context windows +
recommended effective-utilization guidance.** Do **not** pin from memory (DESIGN §7: *"the ~1M window +
prime-frame fraction are `[TUNABLE]`, grounded against real model facts at BUILD time"*). The architecture is
number-independent; the grounded numbers are written as `[TUNABLE]`-annotated defaults.

---

## Wave 1 — foundations (parallel; disjoint)

### T1 — `delivery` axis + prime-frame policy in config
- **owns:** `protocol/config.md`
- **read_first:** DESIGN §3 (delivery config), §7 (prime-frame sizing), existing config.md schema table + Grill-depth dial section (the pattern to match).
- **action:**
  1. Ground the prime-frame numbers (see *Build-time grounding* above) — WebSearch first.
  2. Add a `delivery` schema row + sub-block exactly per DESIGN §3 (pinned D3): `delivery: { shape: "one-shot"|"incremental" (default "one-shot", D25 absent ⇒ today's behavior); boundary: "always-stop"|"auto-continue-while-green" (default "always-stop", control-first GB6); backend?: <engram pointer> (optional CONSULT seam E2/E19, no-op if absent) }`. Record the preset pre-fill: *"individual ⇒ one-shot · version-up ⇒ **ask** · batch ⇒ one-shot"*; the D45 load-guard validates `delivery` **fail-closed** (malformed ⇒ stop+escalate, not guess).
  3. Add a **prime-frame** policy subsection (DESIGN §7 / D83): the prime frame = *"a model's recommended effective working band (below the degradation zone, headroom reserved) — an agnostic fraction/policy; the adapter resolves it to real tokens per model."* State the grounded `[TUNABLE]` default fraction + the floor (fits one prime frame ⇒ refuse a sprint, recommend one-shot) and ceiling (exceeds one prime frame ⇒ split) rules. This is the single source both T4 (sizing) and T5 (self-handoff trigger) reference.
- **verify:** `cd tools && uv run python validate_skills.py` (still green); `grep -n "delivery" protocol/config.md` shows the three sub-fields + defaults; `grep -ni "prime frame" protocol/config.md` shows the policy block.
- **acceptance_criteria:**
  - Positive: `delivery.shape` default is `one-shot`; `delivery.boundary` default is `always-stop`; the prime-frame policy is documented as an agnostic fraction with adapter-resolved tokens.
  - Negative: **NO** literal token count is written without a `[TUNABLE]` annotation and a "grounded at build via WebSearch" note; **NO** change to any existing config row (BC1 — absent `delivery` ⇒ today's behavior byte-for-byte).
- **risk:** if `delivery` defaults wrong (e.g. boundary auto-continue), a sprinted run could skip the human gate. Blast radius = every incremental run. Mitigated by defaults-control-first + T10 asserting the default strings.

### T2 — three-tier sprint state schema
- **owns:** `protocol/state.md`
- **read_first:** DESIGN §6 (three-tier state table) + §10 T5/T6, existing state.md (single-writer L3 invariant, candidate lifecycle pattern).
- **action:** Add a **sprint-progression** section per DESIGN §6: tier-1 frozen provenance (`delivery:{shape,policy}` in `kata.config`), tier-2 durable trail (per-sprint reports + boundary handoffs + superseding decisions/roadmap amendments in `.planning` git docs — *"authoritative, resumable record"*), tier-3 progression cache in `.kata/` (sprint index, gate status, open-correction status, **dirty/gated flag**) — *"single-writer plan-guardian (L3), churns; rebuilt from tier-2 on re-entry."* Extend the JSON shape with the tier-3 sprint fields (e.g. `sprint: { index, gateStatus, openCorrection, boundary: "dirty"|"gated" }`). State the resume rule (T5): *"current sprint = which reports exist + are gated; if the cache corrupts, throw it away and rebuild."*
- **verify:** validator green; `grep -nE "sprintIndex|gateStatus|dirty|gated|rebuild" protocol/state.md`.
- **acceptance_criteria:**
  - Positive: tier-3 fields documented as **disposable + rebuildable from the git-committed tier-2 trail**; single-writer (orchestrator only) invariant preserved.
  - Negative: **NO** claim that tier-3 is authoritative; **NO** worker-writable state added (L3 must hold).
- **risk:** a non-rebuildable cache breaks fresh-clone resume (R5). Blast radius = cross-session/clone resume. Mitigated by the explicit "rebuilt from tier-2" semantics + T10/A4 check.

### T3 — boundary artifact + red-sprint escalation (protocol)
- **owns:** `protocol/handoff.md`, `protocol/escalation.md`
- **read_first:** DESIGN §4 (boundary protocol), §5 (boundary-artifact), §10 T1/T4, existing handoff.md + escalation.md schemas.
- **action:**
  - `handoff.md`: add a **boundary-handoff** variant section — the per-sprint boundary artifact = the standard handoff sections + the sprint gate result + the drift-labelling carried forward; note T1 *"a boundary supersedes a coincident self-handoff."*
  - `escalation.md`: add the **red-sprint async path** (T4): *"a red sprint escalates (D51/D52), never a boundary"* — a failed sprint gate routes through the existing escalation lifecycle, it does not open a course-correct boundary.
- **verify:** validator green; `grep -ni "boundary" protocol/handoff.md`; `grep -ni "red sprint\|never a boundary" protocol/escalation.md`.
- **acceptance_criteria:**
  - Positive: the boundary handoff is documented as the same schema + sprint-gate fields; a red sprint routes to escalation.
  - Negative: **NO** new escalation `kind` invented (reuse the three existing kinds); **NO** suggestion that a red gate becomes a boundary stop.
- **risk:** conflating red-gate with boundary would let a broken sprint masquerade as a clean stop. Blast radius = sprint-gate integrity. Mitigated by the explicit T4 routing rule + T10 seam.

### T8 — `kata-report` v1 (NEW skill)
- **owns:** `skills/evaluate/kata-report/SKILL.md`  *(category pick: **evaluate** — synthesis of the sprint gate/build log; see Micro-pick M1)*
- **read_first:** DESIGN §5 (kata-report = D32 v1 minimal core), DESIGN §10 T2, an existing minimal skill's frontmatter (e.g. `kata-readiness`) for the schema-v2 shape + tag rules.
- **action:** Author the minimal one-page per-sprint report skill (D2: *"the per-sprint one-page report **is** `kata-report v1` (not throwaway); D32 expands later"*). Content contract: sprint id + goal, gate result (tests/build/security numbers), what shipped (paths), drift ledger (authorized/unauthorized counts), open items / deferred. Frontmatter: `category: evaluate`, `cost-weight: 1`, `agnostic: true`, `allowed-tools: [Read, Grep, Glob, Write]`, tags `kata/evaluate` + `kata/module/report` (or `kata/spine` — see M1), `status: experimental`, `version: 0.1.0`.
- **verify:** `uv run python validate_skills.py` counts 30 skills, 0 errors after this file lands (or as part of T10's run).
- **acceptance_criteria:**
  - Positive: validator-conformant frontmatter; the report contract names gate numbers + shipped paths + drift ledger.
  - Negative: **NO** evaluation/gating logic (it reports, it does not gate — `kata-evaluate` owns the gate, D22); **NO** dependency on sprint-only state (must be invocable for a one-shot run too, so D32 can reuse it).
- **risk:** scope-creep into a gate. Blast radius = duplicate/competing gate logic. Mitigated by the "reports, never gates" boundary + negative assertion.

---

## Wave 2 — capabilities on the foundations (parallel; disjoint)

### T4 — `kata-plan` roadmap layer (NEW method file + tier wiring)
- **owns:** `skills/plan/kata-plan/ROADMAP.md` (NEW), `skills/plan/kata-plan/RUBRIC.md`, `skills/plan/kata-plan-essential/SKILL.md`, `skills/plan/kata-plan-standard/SKILL.md`, `skills/plan/kata-plan-advanced/SKILL.md`
- **depends_on:** T1 (prime-frame policy)
- **read_first:** DESIGN §5 (roadmap layer + artifact schema), §7 (prime-frame sizing), §8 (version-up reuse), the existing `kata-plan/RUBRIC.md` (the family method to extend, not duplicate).
- **action:**
  - NEW `ROADMAP.md` (shared method, parallels `RUBRIC.md`): the roadmap-partition layer — *"partition the DAG at natural seams into prime-frame-sized sprints; emit the roadmap artifact; per-sprint just-in-time plan freeze; sprint N≥2 = version-up plan (D50)."* Pin the **roadmap-artifact schema** verbatim (DESIGN §5/A1): `{ projectDesignRef, frozenAt, sprints: [ { id, goal, gateCommand, demonstrableArtifactType, dagSeamRationale, dependsOn[] } ] }`. Encode the floor/ceiling sizing (DESIGN §7, reference T1's prime-frame policy — do not re-define it) and `baselineGate = most recent green gate` (D84).
  - In each `kata-plan-{essential,standard,advanced}` SKILL.md and the family `RUBRIC.md`: add a short pointer — *"when `delivery: incremental`, first run the roadmap layer (`ROADMAP.md`) to partition into sprints, then plan the active sprint at the chosen tier."* No other change to the tier depth contracts.
- **verify:** validator green (wikilinks resolve; family folder still valid); `grep -n "projectDesignRef\|dagSeamRationale" skills/plan/kata-plan/ROADMAP.md`.
- **acceptance_criteria:**
  - Positive: the roadmap artifact schema matches §5 exactly; each tier skill points to `ROADMAP.md` for incremental delivery.
  - Negative: **NO** prime-frame number redefined here (must reference T1); **NO** change to a tier's existing depth contract beyond the one pointer; **NO** new SKILL.md added under the family (it is a method file, not a counted skill).
- **risk:** if the roadmap layer re-defines prime-frame, two sources drift. Blast radius = inconsistent sprint sizing vs self-handoff trigger. Mitigated by single-source-in-T1 + negative assertion + T10 grep.

### T5 — `kata-selfhandoff` prime-frame trigger
- **owns:** `skills/handoff/kata-selfhandoff/SKILL.md`
- **depends_on:** T1
- **read_first:** DESIGN §7 / B1 (supersedes D8 threshold clause), existing selfhandoff (the D8 anti-over-conservative principle to preserve).
- **action:** Replace the *"configurable % threshold"* trigger with the **prime-frame-fraction** trigger (B1/D83): *"the one-shot self-handoff/refresh threshold changes from D8's user-set % → the model-resolved prime-frame fraction. D8's principles survive (anti-over-conservative; task-boundary-preferred)."* Add: self-handoff runs **inside sprints** too (intra-sprint refresh — no human gate, no drift); *"sprint = the one-shot mechanism + a planned stop at prime-frame boundaries."* Reference T1's prime-frame policy; do not duplicate the number.
- **verify:** validator green; `grep -ni "prime frame\|intra-sprint" skills/handoff/kata-selfhandoff/SKILL.md`.
- **acceptance_criteria:**
  - Positive: trigger is the prime-frame fraction; the anti-over-conservative + task-boundary principles (D8) explicitly survive; intra-sprint refresh documented as no-gate/no-drift.
  - Negative: **NO** human gate or drift introduced by an intra-sprint refresh; **NO** re-implementation of the handoff format (still delegates to `kata-handoff`).
- **risk:** an over-eager prime-frame trigger reintroduces the "wrap up early" anti-pattern (LESSONS L). Blast radius = long-run productivity. Mitigated by preserving the D8 generous-default principle.

### T6 — `kata-readiness` sprint-state detect + rebuild
- **owns:** `skills/coordinate/kata-readiness/SKILL.md`
- **depends_on:** T2
- **read_first:** DESIGN §5 (readiness EXTEND), §6 (tier-3 rebuild), §10 T5, existing readiness scopes.
- **action:** Add sprint-progression detection to Scope 2: detect an **open roadmap + sprint index + gated-vs-dirty boundary** (T5: *"dirty ⇒ resume / gated ⇒ course-correct"*) and **rebuild the tier-3 cache from the git-committed tier-2 trail** (current sprint = which reports exist + are gated). Keep it read-only (returns the verdict; never writes — consistent with the skill's existing no-write contract; the cache rebuild is reported/handed to the orchestrator, the single writer).
- **verify:** validator green; `grep -ni "sprint\|rebuild\|dirty\|gated" skills/coordinate/kata-readiness/SKILL.md`.
- **acceptance_criteria:**
  - Positive: detects open-roadmap + sprint index + dirty/gated; rebuild-from-git-trail described.
  - Negative: **NO** write to `.kata/` from readiness itself (single-writer L3 — the orchestrator writes); **NO** new BLOCK that fires on a normal one-shot run (delivery absent ⇒ unchanged behavior).
- **risk:** a false dirty/gated read mis-routes resume vs course-correct. Blast radius = wrong boundary behavior on resume. Mitigated by deriving state from committed reports (deterministic) + T10/A4 fresh-clone check.

### T9 — `kata-handoff` boundary tie-in
- **owns:** `skills/handoff/kata-handoff/SKILL.md`
- **depends_on:** T3
- **read_first:** DESIGN §5 (handoff EXTEND — boundary-artifact content), T3's new `protocol/handoff.md` boundary section, the existing Orientation tie-in (the pattern to extend).
- **action:** Add a short **boundary-handoff** subsection: at a sprint boundary, the handoff additionally carries the sprint gate result + drift-labelling + the next-sprint pointer, per `protocol/handoff.md`. Keep it pointing at the protocol schema (do not duplicate). One-shot handoff behavior unchanged.
- **verify:** validator green; `grep -ni "boundary" skills/handoff/kata-handoff/SKILL.md`.
- **acceptance_criteria:**
  - Positive: boundary-handoff content references the T3 protocol section; composes with `kata-orient` and `kata-sprint`.
  - Negative: **NO** change to the existing one-shot/session handoff sections (BC); **NO** duplicated schema (points to protocol).
- **risk:** duplicated boundary schema drifts from protocol. Blast radius = handoff/protocol divergence. Mitigated by point-to-protocol + negative assertion.

---

## Wave 3 — the boundary coordinator

### T7 — `kata-sprint` boundary coordinator (NEW skill — the centerpiece)
- **owns:** `skills/coordinate/kata-sprint/SKILL.md`
- **depends_on:** T3 (boundary/escalation protocol), T4 (roadmap artifact), T8 (kata-report)
- **read_first:** DESIGN §4 (G1–G4 in full), §5 (kata-sprint NEW — *"composes, never reimplements"*), §9 (engram C4-adjacent rule), §10 (T1–T8), existing `kata-orchestrate` (to confirm it stays **sprint-blind** — T7 must not require changing it).
- **action:** Author the thin boundary coordinator. **Stop-side:** verify the sprint gate is green → compose `kata-report` (T8) + `kata-handoff` (boundary variant, T9/T3) → **STOP**. **Resume-side:** run the **Boundary Change-Control Protocol G1–G4** verbatim (DESIGN §4, *structural invariants, never tiered — D33*):
  - **G1** explicit approval gate — boundary hard-stops; no correction applies without explicit user approval *(unless `boundary: auto-continue-while-green` AND all green-conditions hold, GB6)*.
  - **G2** drift labelling — classify each change by reach (next-sprint-plan / roadmap-reshape / DESIGN-amendment); a drift-class change needs a separate explicit *"yes, I am changing frozen X."*
  - **G3** post-approval adversarial sweep — fresh-context `kata-review` (D15) over the approved set; on finds → re-present, **capped at PINNED 2 rounds (A2 — a safety backstop, NOT a tunable)**; still snowballing ⇒ G4.
  - **G4** snowball guard — predicate is **solely** `blast-radius(approved corrections)` vs the **remaining-roadmap footprint** — exceeds ⇒ flag **re-scope, not a tweak** → deliberate re-plan/new run *(the numeric threshold is **removed**; blast-radius-vs-footprint only)*.
  - **Safety spine:** *"when in doubt, stop and make the human decide; never silently expand."*
  - Compose `kata-grill` delta-mode + `kata-review` + blast-radius; freeze the next sprint plan; hand to `kata-orchestrate`. Encode the §9 rule: a boundary CONSULT may **never** flip `stop→continue` while any of {green ∧ no escalations ∧ no pending corrections ∧ no G3 tertiary drift} is false. Plus DESIGN §4 B5: *a DESIGN-layer amendment at a boundary requires the same fresh-context `kata-review` SHIP the initial freeze demands.* Frontmatter: `category: coordinate`, tags `kata/coordinate` + `kata/spine`, `cost-weight: 2`, `allowed-tools: [Read, Grep, Glob, Write, Edit, AskUserQuestion]` (G1 needs human approval), `agnostic: true`.
- **STRIDE threat register** (attacker/agent-reachable surface = the boundary gate, where steering enters):
  - **Spoofing** — a worker/agent self-asserting "approved" → mitigation: G1 requires an explicit human `AskUserQuestion` approval; approval is not inferable from state.
  - **Tampering** — silent edit to a frozen DESIGN/ROADMAP at the boundary → mitigation: G2 drift-class requires a separate explicit "changing frozen X" + B5 fresh-context review for DESIGN amendments; supersede-never-rewrite.
  - **Repudiation** — untraceable course-correction → mitigation: every boundary change recorded as a superseding decision/roadmap amendment in the tier-2 git trail (T2/T3).
  - **Information Disclosure** — n/a (no secrets cross the boundary; T-redaction handled by kata-handoff §7).
  - **Denial of Service** — an infinite re-present loop → mitigation: G3 PINNED 2-round cap, then G4 escalates to re-scope (bounded).
  - **Elevation of Privilege** — `auto-continue-while-green` flipping `stop→continue` without the full green-condition set → mitigation: the §9 AND-gate (green ∧ no escalations ∧ no pending corrections ∧ no G3 drift) + GB6 default `always-stop`.
- **verify:** `uv run python validate_skills.py` → 31 skills, 0 errors; `git diff --stat` shows **`kata-orchestrate` unchanged** (BC2); `grep -nE "G1|G2|G3|G4|blast-radius|2 round|always-stop" skills/coordinate/kata-sprint/SKILL.md`.
- **acceptance_criteria:**
  - Positive: G1–G4 all present + explicitly never-tiered; the 2-round cap and blast-radius-only G4 predicate are encoded; stop-side composes `kata-report`+`kata-handoff`; resume-side composes `kata-grill` delta + `kata-review` + blast-radius.
  - Negative: **NO** edit to `kata-orchestrate` (it stays sprint-blind, BC2 — the diff must prove it); **NO** reimplementation of grill/review/report logic inside kata-sprint (compose only); **NO** numeric threshold in G4; **NO** path where a correction applies without G1 approval (except the explicit GB6 AND-gate).
- **risk:** the single highest-residual risk in the build — a boundary that silently expands scope or skips the human violates the steering tenet (R3) and the spine (plan-doesn't-drift). Blast radius = every incremental run's correctness + the no-drift guarantee. Mitigated by the full STRIDE register above, G1 hard human gate, and T10 asserting orchestrate-unchanged + G1–G4 presence; final D15 review (A5) is the backstop.

---

## Wave 4 — conformance

### T10 — validator + protocol assertions + test seams
- **owns:** `tools/validate_skills.py`, `tools/tests/test_validate_skills.py`
- **depends_on:** T1–T9 (asserts their terms + new skills exist)
- **read_first:** existing `validate_skills.py` `REQUIRED_PROTOCOL` dict + the existing β/RS/AO/ML test seams (the pattern to extend).
- **action:**
  - `REQUIRED_PROTOCOL`: add `"delivery"` to `config.md`'s term list; add a `state.md` entry asserting tier-3 sprint terms (e.g. `["sprint", "gateStatus", "dirty", "gated", "rebuild"]` — match the exact strings T2 used); add a `handoff.md` entry asserting the boundary term(s); add a term to `escalation.md`'s list for the red-sprint path **only if** T3 introduced a stable keyword (else assert via a test grep).
  - Tests: add seams for — delivery default strings (one-shot/always-stop); prime-frame policy present; tier-3 state rebuildable-from-trail; `kata-sprint` frontmatter (coordinate + spine, G1–G4 present, never-tiered, 2-round cap, blast-radius-only); `kata-orchestrate` byte-unchanged guard (BC2 — assert no sprint keyword leaked into orchestrate); `kata-report` frontmatter + "reports-not-gates"; roadmap layer present (`ROADMAP.md` + artifact schema keys); selfhandoff prime-frame trigger; readiness sprint-detect.
- **verify:** `cd tools && uv run pytest -q` (all pass, new seams green) **and** `uv run python validate_skills.py` (31 skills / 0 errors).
- **acceptance_criteria:**
  - Positive: every new protocol term is asserted; every new/changed behavior has a test seam; validator counts 31 skills / 0 errors.
  - Negative: **NO** test that passes vacuously (each new seam must fail if its target line is deleted — default-FAIL discipline); **NO** weakening of an existing check.
- **risk:** a vacuous seam gives false confidence (recall the β `"zero CONSULT"` casing bug). Blast radius = undetected regressions. Mitigated by writing each seam to a specific string T1–T9 actually emit + a quick delete-the-line sanity check.
- **STRIDE:** n/a (maintainer tooling, not shipped — D27; no attacker-reachable surface).

---

## Wave 5 — index + docs + planning

### T11 — TAXONOMY + README + planning docs
- **owns:** `docs/TAXONOMY.md`, `README.md`, `.planning/ROADMAP.md`, `.planning/STATE.md`, `.planning/DECISIONS.md`
- **depends_on:** T10 (validator must be green before `--write`; index reflects the final 31-skill set)
- **read_first:** existing TAXONOMY module/spine sections, the README SKILL-INDEX markers, ROADMAP sprint-cadence row, STATE CURRENT box.
- **action:**
  - `TAXONOMY.md`: add `kata-sprint` (spine, coordinate), `kata-report` (evaluate; module/report or spine — per M1), the `kata-plan` **roadmap layer** (method file), and the `delivery` axis.
  - `README.md`: regenerate the index — `cd tools && uv run python validate_skills.py --write` (mechanical; preserves the hand-authored Use column). Then add a hand-authored Use cell for the two new skills.
  - `.planning/ROADMAP.md`: mark sprint-cadence **BUILT**; update the progress table.
  - `.planning/STATE.md`: update the CURRENT box (31 skills, sprint-cadence built, gate numbers).
  - `.planning/DECISIONS.md`: **verify D78–D85 present (already promoted at freeze, lines 566–603) — no re-add**; append only a build-completion note if warranted.
- **verify:** validator green (README in sync); `uv run pytest -q` green; `git status` shows only intended files.
- **acceptance_criteria:**
  - Positive: README index lists 31 skills in sync; TAXONOMY documents both new skills + the roadmap layer + delivery axis; ROADMAP/STATE reflect built.
  - Negative: **NO** duplicate D78–D85 decision entries; **NO** manual edit to the README mechanical columns (only `--write` + the Use cell).
- **risk:** an out-of-sync README fails the validator (caught) — low residual. Blast radius = doc accuracy. Mitigated by `--write` + the sync check.

---

## Closing gate (NOT a task — the done-discipline, L8 / D15 / A5)
After T11: a **fresh-context, no-write `kata-review`** (advanced tier given the boundary-protocol surface) sweeps
the whole diff for soundness, drift, and second-order issues → must return **SHIP** before "done." Then run
**Snyk** on the changed Python (`tools/validate_skills.py` + tests) per the always-on security rule, fix→rescan
until clean. Commit-as-you-go per wave (conventional prefixes; stage specific files; end messages with the
Co-Authored-By trailer). All work on `master` (local-only).

## Micro-picks (implementation details the frozen DESIGN left open — not new design decisions)
- **M1 — `kata-report` category + tag.** DESIGN §5 wrote *"skills/evaluate|handoff/kata-report"*. Plan defaults
  to **`evaluate`** (a report synthesizes the gate/build log; listed first in the DESIGN) with tag
  `kata/module/report`. Trivially swappable to `handoff`/`kata/spine` if you prefer it sit beside `kata-handoff`.
- **M2 — roadmap layer = method file, not a skill.** Built as `skills/plan/kata-plan/ROADMAP.md` (parallels the
  family's `RUBRIC.md`), so it is a *layer within* `kata-plan` (DESIGN's wording) and does **not** add a
  validator-counted skill. Net skill delta stays +2.

## Acceptance roll-up (DESIGN §13, run at build end)
A1 validator green incl. new frontmatter + REQUIRED_PROTOCOL coverage → **T10**. A2 roadmap artifact + just-in-time
freeze → **T4**. A3 G1–G4 never-tiered + 2-round cap + blast-radius-only + B5 → **T7**. A4 fresh-clone tier-3
rebuild → **T6/T10**. A5 fresh-context adversarial review SHIP → **Closing gate**.
