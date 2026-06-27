---
title: "Debug Mode — Phase 2b PLAN (the PROTECT half: apply fixes SAFELY)"
status: "FROZEN — freeze-gate kata-review HOLD→SHIP (2026-06-27)"
date: 2026-06-27
spec: debug-mode
phase: P2b (characterization-gen + behavioral drift gate + gated fix-application loop; NO discovery)
source: >-
  FROZEN DESIGN .planning/specs/debug-mode/DESIGN.md (LD6, §5 incl. v1 LIMITATION note, LD9, LD3, §4, §7);
  PLAN-p2a.md (the FIND half — tools/deviation.py findings schema + routes; kata-deviate; the P2b
  comment-seam in kata-orchestrate/SKILL.md); recipe per .planning/HANDOFF.md §5
---

# Debug Mode — Phase 2b PLAN (the PROTECT half)

Phase 2b turns P2a's **`auto-fix-eligible`** findings (in `.kata/deviations/findings.json`) into **applied,
behavior-preserving fixes**. Scope = **LD6** (characterization-suite generation) + **§5** (the behavioral
drift gate, v1) + **LD9** (gated fix application through the loop). P2b **starts at routed findings and ends
at applied fixes (or deferred-with-reason)** — it does **not** discover deviations (that is P2a).

This PLAN introduces no decisions; every choice traces to a LOCKED decision in the frozen DESIGN. An
unresolved point ⇒ return to DESIGN/grill. It partitions P2b into **disjoint-ownership slices** with a wave
DAG, following the same recipe shape P2a used (deterministic Python engine + LLM-judgment skill + orchestrate
wiring).

## In scope (P2b — the PROTECT half)
- **LD6 — characterization-suite generation.** Per fix's **blast-radius** (computed with `tools/footprint.py`
  + the graph), generate tests that **PIN current behavior EXCEPT the deviation being fixed**; capture
  before/after; **the generated suite is LEFT BEHIND** in the target repo (conversion value).
- **§5 — behavioral drift gate (v1).** Every baseline-GREEN test stays GREEN; characterization snapshots
  byte-identical (nondeterminism scrubbed) **EXCEPT an Allowed Exception List** (the nominated buggy test[s]
  that may go RED→GREEN). Any previously-green test → RED = **BLOCK**.
- **LD9 — gated fix application.** Each fix is TDD'd (`kata-tdd`) against its characterization tests, applied
  in worktrees (`kata-worktree`), passes `kata-evaluate` + D98 `kata-review` + Snyk on modified code.
  Objective defects (test/type/Snyk) are fixed **regardless of intent-confidence**;
  **can't-fix-without-drift → DEFER to a deferred-fix list** (preserves the no-drift guarantee).

## Out of scope (P3 / fast-follow — do NOT build here)
- **LD12** the closeout confidence report — *consumes* P2b's outputs (applied fixes + deferred list + drift
  proofs) but is **P3/closeout**.
- **LD13** onboarding / convert-to-loop path; **LD10** language prompt-profiles — P3.
- **LD5 fast-follow** confidence calibration (isotonic); **§5 fast-follow** the surface/structural-invariance
  layer (public-API diff = ∅ + AST-edit-script) — see the honest limitation note below.
- Re-running the P2a discovery funnel; editing `tools/deviation.py` / `kata-deviate` (P2a-owned).

## ⚠ §5 v1 LIMITATION — surfaced honestly (FREEZE note, DESIGN §5 / H4)
P2b enforces **BEHAVIORAL drift strongly** (baseline-green stays green; characterization snapshots stable
except the AEL). It enforces **structural / public-surface drift only loosely** — the surface-invariance
layer (public-API diff = ∅ **+** AST-edit-script = body-updates-only) is a **FAST-FOLLOW, NOT v1**. The
"structure preserved" promise (F3) is **behaviorally** enforced in v1; full structural enforcement arrives
with the fast-follow. Every artifact P2b produces (drift report, skill prose, the handoff to LD12) must state
this so "structure preserved" is **not over-claimed**. `tools/drift_gate.py` leaves a clearly-named,
non-executing seam for the structural layer; it does **not** implement it.

## Architecture split (the recipe — deterministic engine vs LLM-judgment skill vs wiring)
- **`tools/drift_gate.py` (NEW engine, Slice F1)** — pure, injectable, **mutation-proof** deterministic
  decision logic: parse before/after per-test outcomes, enforce **green→RED = BLOCK** against the **trusted
  Allowed Exception List**, byte-compare characterization snapshots with nondeterminism scrubbed, and the
  AEL **integrity** check. **No subprocess, no eval, no exec** — it consumes test-RESULT data as plain
  dicts/strings and returns verdicts. Operator test runs go through the **existing** registered operator
  runner (`run_result.run_gate`); the engine never spawns one.
- **`kata-characterize` (NEW skill, Slice F2; category `execute`, never-tiered debug-spine)** — the
  LLM-judgment author of the pinning tests: scope the blast-radius (via `footprint`), author
  characterization tests that pin current behavior **except** the deviation, establish the finding-bound AEL,
  and capture before-snapshots. It **calls the engine for every deterministic decision** — it never
  re-implements a transition rule or a snapshot compare in prose.
- **The fix-loop wiring in `kata-orchestrate` (Slice F3)** — replace the P2b comment-seam: consume
  `findings.json` (`route=="auto-fix-eligible"`) → per finding: **characterize → kata-tdd fix in worktree →
  drift gate → kata-evaluate + D98 kata-review + Snyk → apply / defer**.

### exec-safety posture (mandatory — `protocol/exec-safety.md`)
**No new execution sink is introduced by P2b.** Confirmed against the contract:
- **`tools/drift_gate.py` is pure decision logic.** It parses captured test output text into per-test
  outcome maps (pure string parsing — `parse_test_outcomes`), compares result dicts, and byte-compares
  scrubbed snapshot strings. It **spawns no subprocess and calls no `eval`/`exec`** — assertable by source
  scan in its test (re-asserting the P2a posture for the new module).
- **Operator test runs** (before/after baseline + characterization runs) go through the **existing**
  operator-domain sink **`run_result.run_gate`** (`protocol/exec-safety.md` → registry row
  *"`run_result.run_gate` … operator … `shell=True` registered exception"*). No new row.
- **Characterization tests are LLM-GENERATED code that gets RUN via pytest.** This is the **normal
  worker-output-through-the-gate trust model** — the generated suite is gated by `kata-tdd` (it is the
  worker's owned output), by `kata-evaluate`, and by the drift gate itself — **NOT a freeform-eval sink**.
  No harness code evaluates a worker-supplied *string*; pytest collects and runs *files* exactly as it runs
  every other test in the repo. This introduces **no new execution surface** and registers **no new row**;
  `tools/tests/test_exec_safety.py` is unaffected.
- FM intent consulted during characterization reuses the already-safe **`function_model.evaluate_spec`** /
  **`function_model._safe_eval`** (AST allowlist; already registered). No new evaluator.

## Slices (disjoint file ownership)

### Slice F1 — `tools/drift_gate.py` behavioral drift-gate engine  *(Python; pure, mutation-proof)*
**Owns:**
- `tools/drift_gate.py`
- `tools/tests/test_drift_gate.py`
- `tools/tests/fixtures/drift_gate/` (seeded fixtures: a baseline-GREEN suite + before/after outcome sets for
  (a) an **injected unrelated regression** — a previously-green test goes RED, and (b) the **nominated fix** —
  the AEL test goes RED→GREEN with all others GREEN; plus nondeterministic-but-equal snapshot pairs and a
  genuinely-divergent snapshot pair)

**Surfaces (public, cite-able by name per `protocol/reuse-claims.md` + cite-by-anchor):**
- `parse_test_outcomes(output_text: str) -> dict[str, str]` — **pure** parse of captured (verbose) test-runner
  output into a per-test map `{test_id: "green"|"red"}`. No subprocess; string parsing only. (Keeps the
  engine pure while the *running* stays on the existing operator sink.)
- `classify_transitions(before: dict[str, str], after: dict[str, str]) -> dict` — per-test transition
  classification: `green->green` / `green->red` / `red->green` / `red->red` / `added` / `removed`.
- `validate_allowed_exceptions(allowed: list[str], before: dict[str, str]) -> dict` — **AEL integrity gate**
  (the load-bearing decision). Returns `{"valid": bool, "rejected": [...]}`. An AEL entry is valid **only if
  the test is present AND RED in `before`** (a buggy/failing test nominated to flip to GREEN). An entry that
  is **GREEN in `before`** (or unknown) is **REJECTED** — a green test can never be authorized to regress.
- `drift_verdict(before: dict, after: dict, *, allowed_exceptions: list[str]) -> dict` — the §5 behavioral
  gate. Composes: (1) `validate_allowed_exceptions` first — **invalid AEL ⇒ `BLOCK`**; (2) **any `green->red`
  outside the AEL ⇒ `BLOCK`**; (3) **every AEL test must be `red->green`** — a nominated test still RED ⇒
  the fix did not land ⇒ `BLOCK`; (4) `PASS` only when all baseline-green stay green **and** every AEL test
  flipped red→green. Returns `{"verdict": "PASS"|"BLOCK", "blocking": [...], "flipped": [...], "reason": str}`.
- `scrub_nondeterminism(text: str, *, patterns: list = DEFAULT_SCRUB_PATTERNS) -> str` — scrub timestamps /
  hex addresses / tmp paths / uuids before comparison (TUNABLE pattern list).
- `snapshots_match(before_snap: str, after_snap: str, *, scrub: bool = True) -> bool` — byte-compare after
  scrubbing.
- `characterization_snapshot_verdict(before_snaps: dict, after_snaps: dict, allowed_exceptions: list[str]) -> dict`
  — snapshots must be **byte-identical (scrubbed) EXCEPT** the AEL; returns `{"verdict": "PASS"|"BLOCK",
  "changed_outside_ael": [...]}`.
- `defer_record(finding: dict, reason: str) -> dict` / `emit_deferrals(records: list[dict], path) -> None`
  — the **can't-fix-without-drift → DEFER** record + JSON write to `.kata/deviations/deferred.json`
  (LD9/DG-12; consumed by LD12 in P3 — kept distinct from the P3 recommendations report).
- `build_drift_report(finding, behavioral, snapshot) -> dict` / `emit_drift_report(report, path) -> None`
  — per-finding drift proof to `.kata/drift/<finding_id>.json` (feeds the LD12 regression proof).
- `drift_schema() -> dict` — JSON schema for a drift report (single source of truth).
- `DEFAULT_SCRUB_PATTERNS` — TUNABLE nondeterminism-scrub list, documented as calibratable-without-re-freeze.
- **`structural_drift_verdict` is NOT implemented (§5 v1 LIMITATION).** A clearly-named module-level comment
  marks the fast-follow seam (public-API diff = ∅ + AST-edit-script); the engine raises/returns nothing for
  it in v1. Behavioral verdict only.

**Reuse (verified):** consumes test-result data parsed from the **existing** operator runner
`run_result.run_gate` and the canonical `run_result.build_result` (both in `tools/run_result.py`);
blast-radius is computed by the caller via `footprint.partition` / `footprint.manifest` /
`footprint.changed_since` (in `tools/footprint.py`). The engine imports **no new evaluator** and adds
**no exec sink** (see exec-safety posture above).

**Acceptance (default-FAIL, runnable — on the seeded fixtures):**
- `parse_test_outcomes`: a captured verbose run parses to the expected per-test green/red map.
- `classify_transitions`: each transition class is produced correctly on the fixture pair.
- **Injected unrelated regression → BLOCK:** `drift_verdict` on the (a)-fixture (a previously-green test goes
  RED, empty/irrelevant AEL) returns `verdict:"BLOCK"` with that test in `blocking` (DESIGN §6/§7).
- **Nominated fix → PASS:** `drift_verdict` on the (b)-fixture (AEL test red→green, all others green) returns
  `verdict:"PASS"` with the AEL test in `flipped`.
- **AEL integrity:** `validate_allowed_exceptions` REJECTS an entry that is GREEN-in-before (and an unknown
  entry) ⇒ `valid:False`; `drift_verdict` with such an AEL ⇒ `BLOCK` (a fix worker cannot authorize a green
  test to regress). A nominated AEL test that stays RED after ⇒ `BLOCK`.
- `scrub_nondeterminism` / `snapshots_match`: nondeterministic-but-equal snapshots match after scrub; a real
  divergence does not. `characterization_snapshot_verdict`: byte-identical-except-AEL → PASS; an unexpected
  change outside the AEL → BLOCK.
- `defer_record`/`emit_deferrals` and `build_drift_report`/`emit_drift_report` round-trip schema-valid JSON.
- **No `eval`/`exec`/`subprocess` in `tools/drift_gate.py`** (assertable by source scan in the test).
- **Mutation non-vacuous** on (a) the **green→RED BLOCK** branch, (b) the **AEL handling** (the
  green-in-before rejection **and** the AEL-must-flip red→green requirement), and (c) the snapshot
  changed-outside-AEL BLOCK branch.

**Test seam (DESIGN §7):** the drift gate is testable by injecting an unrelated regression (must BLOCK) vs.
the nominated fix (must PASS); each gate (behavioral transitions, AEL integrity, snapshot compare) is
independently testable on seeded result/snapshot inputs.

### Slice F2 — `kata-characterize` skill  *(the LLM-judgment author; depends_on F1)*
**Skill name + category:** **`kata-characterize`**, category **`execute`** (runs during the debug execution
phase, peer to `kata-deviate`/`kata-tdd`; verb-single-word convention `kata-comprehend`/`kata-deviate`).
**Tiering: never-tiered debug-spine** (like `kata-comprehend`/`kata-deviate`) — debug-only, invoked by the
orchestrate fix-loop phase; tags `kata/execute` + `kata/spine` + `kata/module/debug`. **One `SKILL.md`
(no tier variants, no RUBRIC).**

**Owns:** `skills/execute/kata-characterize/SKILL.md` (+ `resources/` only if the procedure needs a split-out
— author inline first).

**Content (authors the pinning suite; drives the engine; cite engine + reuse surfaces by NAME, not line):**
1. **Blast-radius scoping (LD6/LD8).** For an `auto-fix-eligible` finding, compute the candidate fix's
   blast-radius using **`footprint.manifest`/`footprint.partition`** (+ the graph's caller/callee edges) —
   the set of modules whose behavior must stay pinned.
2. **Author characterization tests** that **PIN current behavior across the blast-radius EXCEPT at the
   deviation locus**, where the test pins the **derived-correct** behavior (consult the FM's
   `intent_summary`/postconditions via **`function_model.evaluate_spec`** — the AST-safe spec-wrapper, no new
   evaluator). The deviation-pinning test is therefore **RED before the fix, GREEN after**; every other
   characterization test pins unchanged behavior (GREEN before and after).
3. **Establish the finding-bound Allowed Exception List.** The AEL = the deviation-pinning test id(s),
   **bound 1:1 to this finding** and recorded in the orchestrator-owned trusted fix manifest. The skill
   **nominates from the finding only** — it does not author an open-ended AEL. (Integrity decision below.)
4. **Capture before-snapshots** of the characterization outputs (for the §5 snapshot layer); the skill calls
   **`drift_gate.scrub_nondeterminism`** / **`drift_gate.snapshots_match`** semantics — it never re-implements
   the compare.
5. **Leave the suite behind.** Write the characterization suite into the **target repo's** test tree
   (conversion value, LD6) — these files are part of the fix's owned footprint and ship with the merge.
- **Honest scope:** authors + pins; it does **not** apply the fix (that is `kata-tdd`), does not run the drift
  verdict (the orchestrator does, via the engine), and **states the §5 v1 structural-drift limitation**.
- **Reuse claims** verified per `protocol/reuse-claims.md`: `drift_gate.*` resolve in `tools/drift_gate.py`
  (F1); `footprint.*` in `tools/footprint.py`; `function_model.evaluate_spec` in `tools/function_model.py`.

**Acceptance (slice-level, runnable):**
- `validate_skills` passes (frontmatter/schema/anchors); new-skill count increments.
- **No phantom reuse** — every cited engine surface resolves to a real symbol in `tools/drift_gate.py` /
  `tools/footprint.py` / `tools/function_model.py`.
- The skill **delegates every deterministic decision** (transition/snapshot/AEL-validity) to the engine; the
  AEL is **finding-bound** (not worker-authored open-ended).
- **The characterization-authoring run is a model run → verified at the integration/`kata-evaluate` gate on
  the seeded fixture, NOT as a slice unit test** (mirrors P2a S2): the deviation-pinning test is RED→GREEN
  and the blast-radius pins hold.

**depends_on:** F1 (cites the engine's real surfaces).

### Slice F3 — orchestrate fix-loop wiring  *(extend the P2b seam; depends_on F1)*
**Owns:** `skills/coordinate/kata-orchestrate/SKILL.md` (only the P2b comment-seam region — the
`<!-- P2b: characterization-suite gen (LD6) + behavioral drift gate (§5) + gated fix-application loop (LD9) … -->`
marker after the Deviation-discovery phase section).

**Content:** replace the P2b comment-seam with the **fix-application loop**, gated on `kata/module/debug`,
consuming `.kata/deviations/findings.json` (only `route=="auto-fix-eligible"`). Per such finding:
1. **`[[kata-characterize]]`** (forward reference, resolved at integration — mirrors how P2a forward-referenced
   `[[kata-deviate]]`) → blast-radius characterization suite + **before-snapshots** + the **finding-bound AEL**
   written to the trusted fix manifest.
2. **`[[kata-worktree]]`** → an isolated worktree on the integration branch for this fix (disjoint per finding).
3. **`[[kata-tdd]]`** → implement the fix against the characterization tests (red→green on the
   deviation-pinning test), staying in the fix's owned footprint. **Objective defects (test/type/Snyk
   corroborated) are fixed regardless of intent-confidence** (LD9).
4. **Drift gate** → run the operator suite + characterization suite **before** (pre-fix state) and **after**
   (fixed worktree) via the existing operator runner; call **`drift_gate.drift_verdict`** +
   **`drift_gate.characterization_snapshot_verdict`** with the trusted AEL. **Any `green->red` outside the
   AEL ⇒ BLOCK.**
5. **`[[kata-evaluate]]`** (PASS) + **D98 `[[kata-review]]`** (SHIP) + **Snyk** (`mcp__Snyk__snyk_code_scan`)
   on the modified code.
6. **Apply or defer.** All gates green ⇒ merge the worktree (disjoint files → clean). **Can't-fix-without-drift
   (drift BLOCK that cannot be resolved without behavioral change) ⇒ `drift_gate.defer_record` →
   `.kata/deviations/deferred.json`** (preserves the no-drift guarantee; LD9/DG-12). Drift proof per applied
   fix → `.kata/drift/<id>.json`.
- **`research`/`defer`/`human`-routed findings are NOT fixed here** (already handled/recorded in P2a).
  **Findings with no `auto-fix-eligible` entries ⇒ no fixes applied** (clean no-op).
- Leave a **new, named, commented P3 seam** (LD12 closeout confidence report — *consumes* the applied fixes +
  `.kata/deviations/deferred.json` + `.kata/drift/*`; LD13 onboarding; LD10 language profiles) — a comment,
  not an executing stub — exactly as P2a left the P2b seam.

**Acceptance:**
- `validate_skills` green.
- The seam is **unambiguously gated on `kata/module/debug` presence** (not on `runShape`, not on
  `target.kind=="existing"` — keying on those would break version-up BC).
- The wiring **applies** auto-fix-eligible fixes through the gates **or defers them**; it does not re-run
  discovery; a P3 comment seam is present.
- **AEL is consumed as a trusted input** (from the finding-bound fix manifest), never re-derived from the
  fixed worktree's results — verifiable by reading the wiring.
- **BC line:** absent `kata/module/debug` ⇒ no fix loop (silent no-op); **version-up/greenfield runs are
  byte-for-byte unchanged.** Findings file with zero `auto-fix-eligible` ⇒ no fixes. (Verifiable by reading
  the gating condition; end-to-end confirmed at the integration gate — F3 owns no Python.)

**depends_on:** F1 (cites engine surfaces / artifact contracts); forward-refs `[[kata-characterize]]` (F2),
and reuses `[[kata-tdd]]` / `[[kata-worktree]]` / `[[kata-evaluate]]` / `[[kata-review]]` (all verified real).

## Wave DAG
```
ownership:
  F1: [tools/drift_gate.py, tools/tests/test_drift_gate.py, tools/tests/fixtures/drift_gate/]
  F2: [skills/execute/kata-characterize/]
  F3: [skills/coordinate/kata-orchestrate/SKILL.md]   # only the P2b-seam region
waves:
  - wave: 1
    slices: [F1]
  - wave: 2
    slices: [F2, F3]
depends_on:
  F1: []
  F2: [F1]
  F3: [F1]
```
- **Wave 1:** F1 (the pure engine — no deps; everything cites its surfaces).
- **Wave 2 (parallel):** F2 (skill, cites engine by name) + F3 (orchestrate, cites engine + artifact;
  forward-refs `[[kata-characterize]]` whose name is fixed by this plan). Disjoint files → no interdependency.
- Concurrency: ≤2 workers in wave 2. All slices in git worktrees; disjoint ownership verified before dispatch.

## Allowed-Exception-List integrity decision (pinned)
The AEL is a **TRUSTED input**, not something a fix worker can expand to make its own breakage pass:
1. **Provenance.** The AEL is established at the **characterize** step (F2), **bound 1:1 to the routed
   finding** (the deviation-pinning test id[s]) + any **operator nomination**, and recorded in an
   **orchestrator-owned trusted fix manifest**. It is **never** authored open-endedly by the fix worker.
2. **Lane isolation.** The fix worker (`kata-tdd` in its worktree) owns only the fix source + the finding's
   characterization file; the fix manifest / `findings.json` are **out of its lane** — it **cannot enlarge
   the AEL**.
3. **Engine enforcement (the hard guard).** `drift_gate.validate_allowed_exceptions` **rejects any AEL entry
   that is GREEN in the before-run** (or unknown) — a green test can never be authorized to regress — and
   `drift_verdict` requires every AEL test to actually flip **red→green** (a still-RED nominee ⇒ BLOCK). The
   engine **never infers the AEL from the after-results**. This branch is **mutation-covered** (F1
   acceptance).

## §5 v1-limitation handling (pinned)
- v1 = **behavioral drift gate only** (baseline-green stays green; snapshots stable except the AEL). This is
  the BC guarantee P2b enforces.
- The **structural / public-surface invariance layer** (public-API diff = ∅ + AST-edit-script) is a
  **FAST-FOLLOW, NOT v1** — `tools/drift_gate.py` carries a named non-executing seam for it and does not
  implement it.
- Every P2b artifact (skill prose, drift report, the LD12 handoff) **states this limitation** so the
  "structure preserved" promise (F3) is honestly scoped to **behavioral** enforcement in v1.

## Integration gate (after the frontier drains)
pytest green (incl. `test_drift_gate.py`) · `validate_skills` (expect new count — `kata-characterize` is new) ·
**Snyk code scan on `tools/drift_gate.py`** (new first-party Python — per CLAUDE.md security rule;
rescan-to-clean) · `test_exec_safety.py` regression still green (**no new sink** — drift_gate is pure; test
runs go through the registered `run_result.run_gate` operator sink; characterization tests run via pytest as
normal worker output) · `gate_emit` RESULT/footprint/mutation (`emit_gate_artifacts`, `prove_non_vacuous`) ·
README regen (`validate_skills.py --write`). Then fresh-context **`kata-evaluate`** (9-rubric, default-FAIL) —
which **exercises the seeded-fixture end-to-end drift decision** (injected unrelated regression → **BLOCK**;
nominated fix → **PASS**) and the characterize→fix→gate seam (item 9 reproduce-the-seam) → standing **D98
`kata-review`** → operator merge gate.

## Risks / escalation triggers
- **AEL integrity is the load-bearing correctness surface (F1).** If a worker could expand the AEL or the
  engine inferred it from after-results, a regression could be whitewashed. Pinned via trusted-input
  provenance + lane isolation + the green-in-before rejection (mutation-covered). If a slice finds it "needs"
  the worker to nominate exceptions, **STOP and escalate** — that breaks the §5 guarantee.
- **§5 v1 structural-drift limitation (honesty).** Do **not** claim full structural preservation in v1; the
  AST/public-API layer is a fast-follow. Over-claiming "structure preserved" is a defect against the FREEZE
  note (DESIGN §5/H4).
- **No new exec sink (F1).** If a worker finds it "needs" a subprocess/`eval` in `tools/drift_gate.py`, STOP
  and escalate — the engine is pure; test runs go through the existing `run_result.run_gate` operator sink;
  characterization tests run via pytest as normal worker output. Never add an evaluator.
- **Can't-fix-without-drift must DEFER, never force (LD9/DG-12).** A fix that can only pass by changing
  behavior is **deferred to `.kata/deviations/deferred.json`**, not forced through — this preserves the
  no-drift guarantee.
- **Scope creep into P3.** If a slice finds it needs the closeout confidence report (LD12), the onboarding
  path (LD13), or language prompt-profiles (LD10) to be testable, STOP — that is the P2b/P3 boundary. P2b
  ends at **applied-or-deferred fixes + drift proofs**.
- **BC.** Any change that alters a non-debug run is a defect — the fix loop is purely additive, gated on
  `kata/module/debug`; zero `auto-fix-eligible` findings ⇒ no fixes applied.

## Judgment calls (flagged for the freeze gate)
- **No new `kata-fix` skill.** LD9 specifies the fix is **`kata-tdd` against the characterization tests** —
  P2b reuses `kata-tdd` + `kata-worktree` rather than inventing a fix skill. The only NEW skill is
  `kata-characterize` (the pinning-test author). Engine = `tools/drift_gate.py`.
- **Per-test outcome parsing lives in the pure engine** (`drift_gate.parse_test_outcomes`) as string parsing
  over captured output — keeping the engine mutation-proof while the *running* stays on the existing operator
  sink (no new subprocess).
- **Deferred-fix list (`.kata/deviations/deferred.json`) is P2b-owned and distinct from the P3 LD12
  recommendations report** — P2b writes the deferred records; P3 closeout renders them. Drift proofs go to
  `.kata/drift/<id>.json` (feeds LD12's regression proof).
- **AEL provenance binding** is recorded in an orchestrator-owned trusted fix manifest (per-finding), not in
  worker-writable space — see the integrity decision above.
