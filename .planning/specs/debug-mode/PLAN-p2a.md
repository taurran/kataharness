---
title: "Debug Mode — Phase 2a PLAN (the FIND half: deviation-discovery → routed findings)"
status: FROZEN — freeze-gate kata-review HOLD→SHIP (2026-06-27)
date: 2026-06-27
spec: debug-mode
phase: P2a (deviation pipeline — discovery + corroboration + confidence/routing; NO fix)
source: FROZEN DESIGN .planning/specs/debug-mode/DESIGN.md (LD4, LD5, §4, §7; LD8/LD9 context); PLAN-p1.md (P1 substrate); recipe per .planning/HANDOFF.md §5
---

# Debug Mode — Phase 2a PLAN (the FIND half)

Phase 2a builds the **deviation-discovery pipeline** that turns P1's function-model oracle into
**ROUTED findings**. Scope = **LD4** (the 7-step pipeline) + **LD5** (confidence-tiering + routing) +
the orchestrate wiring that runs them after the comprehension phase. P2a **stops at "findings discovered,
corroborated, confidence-scored, ROUTED"** — it does **not** fix anything.

This PLAN partitions P2a into **disjoint-ownership slices** with a wave DAG. It introduces no decisions;
every choice traces to a LOCKED decision in the frozen DESIGN. An unresolved point ⇒ return to DESIGN/grill.

## In scope (P2a — the FIND half)
- **LD4 — the 7-step deviation pipeline.** Multi-signal candidate gathering (FM-deviation via
  `function_model.evaluate_spec` over `.kata/function_models/` + cross-module contract mismatch + Snyk +
  run-tests/SBFL + static/types/lint + `kata-diagnose`; dynamic stack-gated) → semantic LLM comparison →
  **self-consistency ≥2/3** `[TUNABLE]` → **objective-corroboration HARD gate** (≥1 tool/test/type/Snyk
  co-locates, else LLM-only → human) → **adversarial refute-or-promote** (ties to D98 `kata-review`). The
  fix gate (step 7) is **P2b — out of scope**. **`kata-research` is NOT a discovery source (H5) —
  escalation-only.**
- **LD5 — confidence tiering + routing.** `C = w1·MSAS + w2·(1−self-consistency-entropy) + w3·StructuralPrior`
  with **TUNABLE weights/cutoffs**; **force-LOW** for sparse-signal modules; route `C≥τ_H` →
  auto-fix-eligible · `τ_L<C<τ_H` → research(≤2)→defer · `C≤τ_L` → defer. v1 **heuristic only** — formal
  isotonic calibration is a DESIGN fast-follow, NOT here.
- **Orchestrate wiring** — extend the P2 comment-seam in `kata-orchestrate/SKILL.md` (gated on
  `kata/module/debug`, **after** the comprehension phase) to run the pipeline and PRODUCE the routed findings
  artifact.

## Out of scope (P2b / fast-follow — do NOT build here)
- **LD6** characterization-suite generation → P2b.
- **§5** behavioral drift gate → P2b.
- **LD9** the fix-application loop (TDD-against-characterization + drift gate + apply-in-worktree) → P2b.
- LD4 step 7 (fix gate) and re-run-2–6-on-patch → P2b.
- Formal isotonic confidence calibration (LD5 fast-follow); surface/AST structural-drift layer (§5 H4) —
  DESIGN-level fast-follows.

P2a's terminal artifact is **`.kata/deviations/findings.json`**: each finding carries its locus, the
corroboration verdict, the self-consistency tally, the refute outcome, the confidence score, and the
**route** (`auto-fix-eligible` / `research` / `defer` / `human` for LLM-only). P2b consumes this.

## Architecture split (the recipe — deterministic engine vs LLM-judgment skill)
Per the hard constraints, **deterministic logic lives in a pure Python engine** and the **LLM-judgment parts
drive it**:

- **`tools/deviation.py` (NEW engine, Slice D1)** — pure, injectable, mutation-proof. Owns the funnel's
  *decisions*: self-consistency vote tally (≥2/3), the objective-corroboration HARD-gate decision, the LD5
  confidence formula (TUNABLE weights), the routing thresholds (TUNABLE), and force-LOW. No I/O beyond
  emit/load of the findings artifact; **no subprocess, no eval** — it consumes pre-gathered signal records
  as plain dicts and returns routed verdicts.
- **`kata-deviate` (NEW skill, Slice D2)** — the LLM-judgment driver: multi-signal candidate gathering,
  semantic FM-vs-code comparison, the ×3 self-consistency sampling, and the adversarial refute argument. It
  **gathers signals and calls the engine for every gate decision** — it never re-implements a threshold or a
  tally in prose.

### exec-safety posture (mandatory — `protocol/exec-safety.md`)
**No new execution sink is introduced by P2a.** Confirmed against the contract:
- FM-deviation reuses **`function_model.evaluate_spec`** → **`_safe_eval`** (AST allowlist), already
  registered in `protocol/exec-safety.md` → *"In-process evaluation of external expressions"* → in-process
  sink registry row `function_model._safe_eval`. The pipeline reuses **P1's safe spec-wrapper**, NOT a new
  evaluator.
- Capturing the dynamic **call record** (`{"inputs":…, "result":…}`) that `evaluate_spec` consumes is
  **dynamic/stack-gated** and runs the target through the **operator-domain test runner** (existing sink;
  `protocol/exec-safety.md` *operator* domain) — not a new sink. This capture is **instrumentation/observation
  of operator-authored test runs** — NOT harness-synthesized direct invocation of the target with
  harness-chosen inputs — so it introduces **no new execution surface**.
- Snyk = the existing `mcp__Snyk__snyk_code_scan` MCP surface; run-tests/SBFL = the operator test command;
  static/types/lint and `kata-diagnose` = existing surfaces. **`tools/deviation.py` itself spawns no
  subprocess and calls no `eval`/`exec`** — it is pure decision logic over signal dicts. Therefore P2a
  **registers no new row** and the `test_exec_safety.py` regression guard is unaffected. (Slice D1 acceptance
  re-asserts "no `eval`/`exec`/subprocess in `tools/deviation.py`".)

## Slices (disjoint file ownership)

### Slice D1 — `tools/deviation.py` deviation engine  *(Python; pure, mutation-proof)*
**Owns:**
- `tools/deviation.py`
- `tools/tests/test_deviation.py`
- `tools/tests/fixtures/deviation/` (the seeded-deviation fixture: an FM + a true-positive signal bundle and
  a false-positive LLM-only bundle)

**Surfaces (public, cite-able by name per `protocol/reuse-claims.md` + cite-by-anchor):**
- `tally_self_consistency(votes: list[bool], *, k_min: int = 2) -> dict` — returns
  `{"agree": int, "total": int, "passes": bool}`; **passes iff agree ≥ `k_min`** over the sampled runs
  (default ≥2/3, LD4 `[TUNABLE]` via `k_min`). Tie/empty handling fail-closed (`passes=False`).
- `self_consistency_entropy(votes: list[bool]) -> float` — normalized binary entropy of the agreement
  distribution, in `[0,1]`; feeds the `(1 − entropy)` confidence term (LD5).
- `corroboration_gate(llm_finding: dict, corroborators: list[dict]) -> dict` — the **HARD gate** (LD4 step 5,
  DESIGN §4 false-positive control). Returns `{"corroborated": bool, "route": str|None, "co_located": [...]}`.
  Corroborated iff **≥1 objective corroborator co-locates** with the LLM finding (same `module`+locus; the
  co-location predicate is the load-bearing check). **Uncorroborated ⇒ `route:"human"`** (LLM-only never
  auto-fix-eligible — the IRIS pattern).
- `compute_confidence(msas: float, sc_entropy: float, structural_prior: float, *, weights: dict = DEFAULT_WEIGHTS) -> float`
  — `C = w1·MSAS + w2·(1−sc_entropy) + w3·StructuralPrior`, clamped to `[0,1]` (LD5; **TUNABLE** `weights`).
- `apply_force_low(confidence: float, *, sparse_signal: bool, low_cap: float = DEFAULT_THRESHOLDS["low_cap"]) -> float`
  — caps confidence into the LOW band when the module is sparse-signal (LD5 force-LOW; DESIGN §4).
- `route_finding(confidence: float, *, thresholds: dict = DEFAULT_THRESHOLDS) -> str` — returns
  `"auto-fix-eligible"` (C≥τ_H) · `"research"` (τ_L<C<τ_H) · `"defer"` (C≤τ_L) (LD5; **TUNABLE** `thresholds`).
- `run_funnel(finding: dict) -> dict` — the **pure composition**: given a gathered finding
  (LLM deviation + `votes` + `corroborators` + `refuted` + `msas`/`structural_prior`/`sparse_signal`),
  apply self-consistency → corroboration gate → (refute already resolved by the skill, passed as `refuted: bool`)
  → confidence → force-LOW → route, and return the routed verdict dict. **Funnel order is invariant:** a
  finding failing self-consistency OR the corroboration gate OR surviving-refute is **never** routed
  `auto-fix-eligible` (it is filtered / routed `human`).
- `DEFAULT_WEIGHTS`, `DEFAULT_THRESHOLDS` — the **TUNABLE knobs** (`w1/w2/w3`; `tau_high`/`tau_low`/`low_cap`),
  documented as calibratable-without-re-freeze (LD5 `[TUNABLE]`).
- `findings_schema() -> dict` — JSON schema for a routed finding (single source of truth).
- `emit_findings(findings: list[dict], path) -> None` / `load_findings(path) -> list[dict]` — JSON round-trip
  to `.kata/deviations/findings.json`.

**Reuse (verified):** consumes FM evaluation results produced via **`function_model.evaluate_spec`** /
**`function_model.load_function_model`** (confirmed present in `tools/function_model.py`); the engine itself
does not import a new evaluator. No new exec sink (see exec-safety posture above).

**Acceptance (default-FAIL, runnable — on the seeded fixture):**
- `tally_self_consistency`: 2/3 → `passes:True`; 1/3 → `passes:False`; empty → `passes:False`.
- `corroboration_gate`: a finding with ≥1 co-located corroborator → `corroborated:True, route:None`; an
  **LLM-only finding (zero corroborators) → `corroborated:False, route:"human"`** (the §7 false-positive is
  FILTERED here).
- `compute_confidence`: exact numeric check on synthetic `MSAS/entropy/prior` inputs with `DEFAULT_WEIGHTS`;
  output clamped `[0,1]`; weight override changes the score deterministically.
- `apply_force_low`: a sparse-signal module is capped to the LOW band regardless of the formula output.
- `route_finding`: synthetic confidences map across `auto-fix-eligible` / `research` / `defer` at the default
  thresholds; a threshold override re-routes deterministically.
- **End-to-end funnel:** the fixture's **true-positive** (≥1 corroborator + ≥2/3 self-consistency +
  `refuted:False`/survived) routes `auto-fix-eligible`; the **false-positive** (LLM-only, no corroborator) is
  routed `human` at the corroboration gate (never `auto-fix-eligible`) — DESIGN §6/§7.
- `emit_findings`/`load_findings` round-trip a schema-valid findings list.
- **No `eval`/`exec`/`subprocess` in `tools/deviation.py`** (assertable by source scan in the test).
- **Mutation non-vacuous** on (a) the corroboration-gate co-location branch, (b) a routing-threshold
  boundary branch, and (c) the `k_min` self-consistency ≥2/3 boundary.

**Test seam (DESIGN §7):** each gate (self-consistency, objective-corroboration, route) independently testable
on seeded signal inputs; true-positive fires, false-positive filtered at the corroboration gate.

### Slice D2 — `kata-deviate` skill  *(the LLM-judgment driver; depends_on D1)*
**Skill name + category:** **`kata-deviate`**, category **`execute`** (it runs during the debug **execution**
phase — it drives runners/Snyk/`kata-diagnose` and the engine, peer to `kata-diagnose`; mirrors the
verb-single-word convention `kata-comprehend`/`kata-diagnose`/`kata-evaluate`). **Tiering: never-tiered
debug-spine** (like `kata-comprehend`) — debug-only, invoked by the orchestrate pipeline phase; tags include
`kata/spine` + `kata/module/debug`. **One `SKILL.md` (no tier variants, no RUBRIC).**

**Owns:** `skills/execute/kata-deviate/SKILL.md` (+ `skills/execute/kata-deviate/resources/` only if the
7-step procedure needs a split-out — author inline first).

**Content (drives the engine; cite engine + reuse surfaces by NAME, not line):**
1. **Candidate gathering (LD4 step 2, multi-signal, parallel/cheap):**
   - **FM-deviation** — for each FM in `.kata/function_models/` (loaded via
     `function_model.load_function_model`), capture a call record (dynamic, **stack-gated** via the operator
     test runner) and call **`function_model.evaluate_spec`**; a violation is an objective FM signal.
   - **Cross-module contract mismatch** — caller/callee expectation conflicts from the graph (the LD7
     contract-inference channel surfaced by P1's FMs).
   - **Snyk** (`mcp__Snyk__snyk_code_scan`), **run-tests/SBFL** (operator test command suspicion scores),
     **static/types/lint**, and **`kata-diagnose`** (resolved tier; root-cause signal).
   - **Dynamic** signals are **stack-gated** (only when a runnable env exists; otherwise degrade — DESIGN §4
     untested/non-runnable edge).
2. **Semantic comparison (step 3)** — reason code-vs-FM, emit a structured deviation `{module, locus, type, evidence}`.
3. **Self-consistency (step 4)** — sample ×3 (shuffled/rephrased), collect agreement `votes`, call
   **`deviation.tally_self_consistency`**; advance only if `passes`.
4. **Objective-corroboration HARD gate (step 5)** — assemble objective corroborators co-located with the LLM
   finding, call **`deviation.corroboration_gate`**; **uncorroborated ⇒ route `human` (never auto-fix)**.
5. **Adversarial refute-or-promote (step 6, ties to D98)** — a fresh-context instance argues the code is
   CORRECT; can't-rebut ⇒ promote (`refuted:False`); plausible rebuttal ⇒ contested ⇒ route `human`. This is
   the **same adversarial lens** the standing D98 `[[kata-review]]` embodies (cite by family; tier-resolved).
6. **Confidence + routing (LD5)** — gather `MSAS`/`structural_prior`/`sparse_signal`, call
   **`deviation.compute_confidence`** → **`apply_force_low`** → **`route_finding`**; compose via
   **`deviation.run_funnel`**; emit the routed findings via **`deviation.emit_findings`** to
   `.kata/deviations/findings.json`.
- **Honest scope:** stops at ROUTED findings — **no fix loop, no characterization suite, no drift gate**
  (P2b). **`kata-research` is escalation-only (H5), explicitly NOT a discovery source** — name it as such.
- **Reuse claims** verified per `protocol/reuse-claims.md`: every cited engine surface resolves in
  `tools/deviation.py`; FM surfaces in `tools/function_model.py`; `kata-diagnose`/`kata-review`/`kata-research`
  are real skills (`skills/execute/kata-diagnose/`, `skills/evaluate/kata-review/`, `skills/plan/kata-research/`).

**Acceptance (slice-level, runnable):**
- `validate_skills` passes (frontmatter/schema/anchors); new-skill count increments.
- **No phantom reuse** — every cited engine surface resolves to a real symbol in `tools/deviation.py` /
  `tools/function_model.py`; `kata-research` is cited escalation-only.
- The skill **delegates every deterministic decision** (tally, gate, confidence, route) to the engine (no
  threshold/tally re-implemented in prose).
- **The end-to-end pipeline run is non-deterministic (a model run) → verified at the integration/`kata-evaluate`
  gate on the seeded fixture, NOT as a slice unit test** (mirrors P1 S3): on the fixture a true-positive
  reaches `auto-fix-eligible` only via ≥1 corroborator + ≥2/3 + surviving refute; the LLM-only false-positive
  is routed `human` at the corroboration gate.

**depends_on:** D1 (cites the engine's real surfaces).

### Slice D3 — orchestrate pipeline wiring  *(extend the P2 seam; depends_on D1)*
**Owns:** `skills/coordinate/kata-orchestrate/SKILL.md` (only the P2 comment-seam region, lines around the
`<!-- P2: deviation pipeline … -->` marker after the **Comprehension phase** section).

**Content:** replace the P2 comment-seam with the **P2a discovery wiring**, gated on `kata/module/debug`,
**after** the comprehension phase produces FMs:
- When `kata/module/debug ∈ modules` AND comprehension emitted FMs to `.kata/function_models/`, invoke
  **`[[kata-deviate]]`** (forward reference, resolved at integration — mirrors how P1 S1 forward-referenced
  `[[kata-comprehend]]`) to run the 7-step funnel and **PRODUCE `.kata/deviations/findings.json`** (routed:
  `auto-fix-eligible` / `research` / `defer` / `human`).
- **Routing consequences at the orchestrator (FIND-half only):** `research`-routed findings → the existing
  research path (≤2 rounds, `[[kata-research]]` via the grounding gate — escalation-only, NOT discovery);
  `defer`/`human` → recorded for the closeout/recommendations (LD12, produced in a later phase) and surfaced.
  **`auto-fix-eligible` findings are produced and recorded — they are NOT fixed here** (the fix loop is LD9 /
  P2b).
- Note that P2a's findings **flow through the normal gates** that feed the validation-miss manifest
  (`tools/validation_misses.py` + the universal hook) — P2a does **not** build that manifest.
- Leave a **new, named, commented P2b seam** (characterization-suite LD6 + behavioral drift gate §5 + the
  LD9 fix-application loop) — a comment, not an executing stub — exactly as P1 left the P2 seam.

**Acceptance:**
- `validate_skills` green.
- The seam is **unambiguously gated on `kata/module/debug` presence** (not on `runShape`, not on
  `target.kind=="existing"` alone — keying on that field would break version-up BC).
- The wiring **produces** the routed findings artifact and **does not fix** (no LD9/drift/char-suite wiring;
  a P2b comment seam is present).
- **BC line:** absent `kata/module/debug` ⇒ no pipeline (silent no-op); **version-up/greenfield runs are
  byte-for-byte unchanged.** (Verifiable by reading the gating condition; end-to-end confirmed at the
  integration gate, not a unit test — D3 owns no Python.)

**depends_on:** D1 (cites engine surfaces / artifact contract); forward-refs `[[kata-deviate]]` (D2).

## Wave DAG
```
ownership:
  D1: [tools/deviation.py, tools/tests/test_deviation.py, tools/tests/fixtures/deviation/]
  D2: [skills/execute/kata-deviate/]
  D3: [skills/coordinate/kata-orchestrate/SKILL.md]   # only the P2-seam region
waves:
  - wave: 1
    slices: [D1]
  - wave: 2
    slices: [D2, D3]
depends_on:
  D1: []
  D2: [D1]
  D3: [D1]
```
- **Wave 1:** D1 (the pure engine — no deps; everything cites its surfaces).
- **Wave 2 (parallel):** D2 (skill, cites engine by name) + D3 (orchestrate, cites engine + artifact;
  forward-refs `[[kata-deviate]]` whose name is fixed by this plan). Disjoint files → no interdependency.
- Concurrency: ≤2 workers in wave 2. All slices in git worktrees; disjoint ownership verified before dispatch.

## Integration gate (after the frontier drains)
pytest green (incl. `test_deviation.py`) · `validate_skills` (expect new count — `kata-deviate` is new) ·
**Snyk code scan on `tools/deviation.py`** (new first-party Python — per CLAUDE.md security rule; rescan-to-clean) ·
`test_exec_safety.py` regression still green (no new sink) · `gate_emit` RESULT/footprint/mutation ·
README regen (`validate_skills.py --write`). Then fresh-context `kata-evaluate` (9-rubric, default-FAIL) — which
**exercises the seeded-fixture end-to-end pipeline** (true-positive promoted, false-positive filtered) → standing
D98 `kata-review` → operator merge gate.

## Risks / escalation triggers
- **Corroboration-gate co-location is the load-bearing correctness surface (D1).** If the co-location
  predicate is too loose, an LLM-only finding could slip the HARD gate → auto-fix-eligible (a §4 false-positive
  leak). Mutation must cover this branch; the fixture's false-positive must route `human`.
- **No new exec sink (D1).** If a worker finds it "needs" a subprocess/`eval` in `tools/deviation.py`, STOP and
  escalate — the engine is pure; dynamic capture goes through the existing operator runner and FM eval through
  the already-registered `function_model._safe_eval`. Never add an evaluator.
- **Scope creep into P2b.** If a slice finds it needs the characterization suite, the drift gate, or the fix
  loop to be testable, STOP — that is the P2a/P2b boundary. P2a ends at ROUTED findings.
- **`kata-research` as a discovery source (H5 violation).** Research is escalation-only; if the skill drafts
  research into candidate gathering, that is a defect against LD4/H5.
- **Confidence is heuristic v1 (LD5).** No isotonic calibration here; weights/thresholds are `[TUNABLE]`
  defaults, documented as calibratable-without-re-freeze. Do not claim calibrated precision.
- **BC:** any change that alters a non-debug run is a defect — the pipeline is purely additive, gated on
  `kata/module/debug`.
