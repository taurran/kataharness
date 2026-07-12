---
name: kata-deviate
description: >-
  LLM-judgment driver of the LD4 7-step deviation-discovery pipeline for Debug Mode (P2a / DESIGN
  LD4–LD5). Per module, over P1's function models in .kata/function_models/: gathers multi-signal
  candidates (FM-deviation via evaluate_spec, cross-module contract mismatch, Snyk, run-tests/SBFL,
  static/types/lint, kata-diagnose), performs semantic code-vs-intent comparison, self-consistency
  sampling (×3), objective-corroboration gating, and adversarial refute-or-promote; then computes
  confidence and routes each finding via the deviation.py engine (run_funnel). Emits ROUTED findings
  to .kata/deviations/findings.json via emit_findings. Stops at routed findings — no fix loop, no
  characterization suite, no drift gate (all P2b). kata-research is escalation-only (H5), explicitly
  NOT a discovery source. Gated on kata/module/debug; invoked by kata-orchestrate after the
  comprehension phase produces FMs.
license: Apache-2.0
version: 0.1.0
category: execute
status: beta
agnostic: true
cost-weight: 4
allowed-tools: [Read, Grep, Glob, Bash, Write]
source: >-
  new (KataHarness original, Debug Mode P2a — deviation-discovery pipeline, DESIGN LD4–LD5)
tags:
  - kata/execute
  - kata/spine
  - kata/module/debug
  - deviation
---

# kata-deviate — deviation-discovery pipeline driver

The debug run's deviation-discovery pass. After `kata-comprehend` has built a `function_model` (FM) per
module (P1), `kata-deviate` drives the **7-step LD4 funnel** that finds, corroborates, and ROUTES
deviations — per module — and emits the findings artifact consumed by P2b.

A **bug is a deviation of code from its derived intended function** (DESIGN LD2). The FM is a *hypothesis*;
the corroboration gate — not FM accuracy — is what makes a finding actionable. This skill never claims
certainty; it produces ROUTED findings that downstream phases act on.

**Honest scope (P2a):** this skill PRODUCES and ROUTES findings only. It does **not** fix, synthesize
characterization tests, or apply the drift gate — all P2b (DESIGN LD9, LD6, §5). `confidence` is a v1
heuristic (formal isotonic calibration is a DESIGN fast-follow, not implemented here). FM-deviation signals
are hypotheses, not guaranteed bugs. The corroboration gate is the load-bearing false-positive control.

**`[[kata-research]]` is escalation-only (DESIGN H5) — explicitly NOT a discovery source.** Research may
be invoked by the orchestrator for `research`-routed findings (≤2 rounds, grounding gate), but it is never
part of multi-signal candidate gathering. Treating `[[kata-research]]` as a discovery source is a defect
against H5.

## Inputs

- **`.kata/function_models/*.json`** — FM artifacts from the P1 comprehension pass, loaded per module via
  `function_model.load_function_model` from `tools/function_model.py`.
- **Operator test runner** — the test command configured for the project; used (dynamic/stack-gated) to
  capture call records that `evaluate_spec` consumes.
- **Graph / cross-module dependency data** — from `kata.graph.json`; used to detect caller/callee contract
  mismatches across module boundaries.
- **Snyk** (`mcp__Snyk__snyk_code_scan`) — security signal per module/file.
- **Static analysis outputs** — type-checker errors, linter findings, and any existing test reports.

## The 7-step deviation pipeline (LD4 / LD5)

Run the pipeline **per module**, in the PageRank/churn order established by the comprehension sweep (DESIGN
LD8). Every deterministic gate decision is delegated to `tools/deviation.py` — never re-implemented in
prose.

### Step 1 — Multi-signal candidate gathering (LD4 step 2; parallel, cheap-first)

Collect candidate deviation signals from all available channels for the module under analysis.

**a. FM-deviation (objective FM signal)**

For each FM in `.kata/function_models/` (loaded via `function_model.load_function_model`):

1. Obtain a call record `{"inputs": {...}, "result": <value>}` — this is **instrumentation/observation of
   an operator-authored test run**, not harness-synthesized direct invocation. The call record is captured
   by running the target through the operator test runner (existing sink; `protocol/exec-safety.md` operator
   domain). **No new execution sink is introduced.**
2. Call `function_model.evaluate_spec(fm, call)` — the AST-safe spec-wrapper. A non-empty `violations`
   list is an objective FM signal: the running code violated the FM's derived pre/postconditions.

Exec-safety: `evaluate_spec` routes all assertion evaluation through `function_model._safe_eval`
(registered in `protocol/exec-safety.md`; in-process evaluation, AST allowlist). This reuses P1's safe
spec-wrapper with no new evaluator. `eval`/`exec` are prohibited throughout `tools/function_model.py`.

**b. Cross-module contract mismatch**

From the graph (`kata.graph.json`), identify caller/callee pairs where the calling module's expectations
(input shapes, return types) conflict with the called module's FM contract. Each mismatch at a shared
interface is a candidate with `{module, locus}` anchored at the callee boundary.

**c. Snyk** (`mcp__Snyk__snyk_code_scan`)

Run a Snyk code scan on the module's source file. Security-class findings are collected as objective
corroborators, keyed by `{module, locus}` for co-location matching in Step 4.

**d. Run-tests / SBFL** (dynamic; stack-gated)

Run the operator test suite. Collect failing-test loci and, where available, SBFL (Spectrum-Based Fault
Localization) suspicion scores for the module. Dynamic signals are **stack-gated**: if no runnable
environment exists, degrade gracefully — log the untested/non-runnable status, record the module under
DESIGN §4 non-runnable edge handling, and continue with the remaining static signals.

**e. Static / types / lint**

Collect type-checker errors, linter warnings, and static-analysis findings for the module. Map each to a
`{module, locus}` pair for co-location matching.

**f. `[[kata-diagnose]]`** (resolved tier; root-cause signal)

When diagnostic context is available or the module shows multi-signal agreement, invoke `[[kata-diagnose]]`
(tier resolved by the orchestrator per the normal tier-resolution rules) to surface root-cause hypotheses
as additional objective signal.

Assemble all signals into a list of candidate records keyed by `{module, locus}`.

### Step 2 — Semantic LLM comparison (LD4 step 3; code vs derived intent)

For each candidate locus, reason over:
- The actual implementation (source text, read via Read/Grep).
- The FM's `intent_summary`, `preconditions`, and `postconditions`.
- The gathered signals from Step 1.

Emit a structured deviation record for each candidate where the comparison identifies a potential
deviation:

```json
{
  "module":   "<repo-relative module path>",
  "locus":    "<function/block/line reference>",
  "type":     "<deviation type: logic | contract | security | type | lint | ...>",
  "evidence": "<concise NL justification citing both code behavior and FM intent>"
}
```

Discard candidates where the code-vs-intent comparison finds no meaningful deviation. This is not a
corroboration gate — it is preliminary LLM-judgment screening before the three-run self-consistency
sample.

### Step 3 — Self-consistency sampling (LD4 step 4; ×3 runs)

For each surviving deviation candidate, sample the LLM judgment **three times** with shuffled evidence
ordering or rephrased prompts. Collect boolean agreement values: `True` = this run agrees there is a
deviation; `False` = this run does not.

Call **`deviation.tally_self_consistency(votes)`** from `tools/deviation.py`:
- Returns `{"agree": int, "total": int, "passes": bool}`.
- Advances only if `tally["passes"]` is `True` (≥2/3 agreement; `k_min=2` by default — TUNABLE).
- Fail-closed: empty votes → `passes=False`; fewer than `k_min` agreements → candidate is dropped and
  never promoted further.

Retain `votes` — they feed the `self_consistency_entropy` term in `deviation.compute_confidence`.

### Step 4 — Objective-corroboration HARD gate (LD4 step 5; false-positive control)

Assemble the list of **objective corroborators** (tool / test / type / Snyk signals from Step 1) that
co-locate with the LLM deviation candidate (same `module` + same `locus`).

Call **`deviation.corroboration_gate(llm_finding, corroborators)`** from `tools/deviation.py`:
- Returns `{"corroborated": bool, "route": str | None, "co_located": list}`.
- **Corroborated** (≥1 co-located objective signal): `corroborated=True`, `route=None`; proceed to Step 5.
- **Uncorroborated** (zero objective co-locators — LLM-only finding): `corroborated=False`,
  `route="human"`. **This finding is NEVER `auto-fix-eligible`.** Record it with `route="human"` and
  `funnel_stop="corroboration_gate"`. This is the IRIS pattern — the load-bearing false-positive control
  (DESIGN §4). No LLM-only finding ever reaches `auto-fix-eligible` or `research`.

### Step 5 — Adversarial refute-or-promote (LD4 step 6; ties to D98)

For each corroborated candidate, invoke a **fresh-context adversarial instance** that argues the code is
**CORRECT** — applying the same adversarial lens that the standing D98 `[[kata-review]]` embodies (cite
by family; tier resolved at runtime by the orchestrator). The adversary receives the full evidence bundle
(FM, code, signals, corroborators) and must attempt to rebut the deviation claim.

Resolve a single `refuted: bool`:
- **`refuted = False`** — the adversary cannot mount a plausible rebuttal; the deviation is promoted.
  Proceed to Step 6.
- **`refuted = True`** — the adversary surfaces a plausible explanation that the code is correct as
  written; the finding is contested. Record with `route="human"` and `funnel_stop="refuted"`. Skip Step 6
  for this candidate.

Pass the resolved `refuted` value into `deviation.run_funnel` (Step 6); the engine enforces the routing
consequence deterministically. Do not re-implement refute routing in prose.

### Step 6 — Confidence, routing, and emission (LD5)

For each surviving candidate (corroborated + `refuted=False`):

**1. Gather LD5 inputs:**
- `msas` (multi-signal agreement score in `[0, 1]`): fraction of Step 1 signal channels that produced a
  co-located signal for this locus.
- `structural_prior` (in `[0, 1]`): structural signal for this module/locus (e.g. call-site density,
  type-coverage fraction).
- `sparse_signal` (`bool`): `True` iff the module was flagged sparse-signal by the comprehension pass.
- `votes`: boolean list from Step 3.
- `corroborators`: co-located objective signals list from Step 4.
- `refuted`: `False` (only surviving candidates reach this step).

**2. Compose the finding dict and call `deviation.run_funnel(finding)` from `tools/deviation.py`.**

`run_funnel` applies the complete funnel in invariant order — do not call the sub-functions individually
for surviving candidates; `run_funnel` is the single composition point:

| Sub-function invoked internally by `run_funnel` | Purpose |
|---|---|
| `deviation.tally_self_consistency(votes)` | Re-verified SC gate |
| `deviation.corroboration_gate(finding, corroborators)` | Re-verified HARD gate |
| `refuted` check | Contested → `"human"` |
| `deviation.compute_confidence(msas, sc_entropy, structural_prior, weights=DEFAULT_WEIGHTS)` | LD5 formula: `C = w1·MSAS + w2·(1−entropy) + w3·Prior`; clamped `[0, 1]`; weights TUNABLE |
| `deviation.apply_force_low(confidence, sparse_signal=sparse_signal, low_cap=DEFAULT_THRESHOLDS["low_cap"])` | Caps confidence for sparse-signal modules; TUNABLE `low_cap` |
| `deviation.route_finding(confidence, thresholds=DEFAULT_THRESHOLDS)` | `C≥τ_H` → `"auto-fix-eligible"` · `τ_L<C<τ_H` → `"research"` · `C≤τ_L` → `"defer"`; TUNABLE |

`run_funnel` returns the **routed verdict dict** with `module`, `locus`, `sc_tally`, `corroboration`,
`refuted`, `confidence`, `sparse_signal`, `route`, and `funnel_stop` fields.

**3. Collect all routed verdicts** (including `"human"`-routed findings from Steps 4 and 5) into a list
and call **`deviation.emit_findings(findings, ".kata/deviations/findings.json")`** to write the terminal
P2a artifact. `emit_findings` creates parent directories as needed.

The schema for each finding is defined by `deviation.findings_schema()` (single source of truth).

### Step 7 — Fix gate (P2b — OUT OF SCOPE)

The fix gate, characterization-suite generation (DESIGN LD6), behavioral drift gate (§5), and the
fix-application loop (DESIGN LD9) are **P2b**. `kata-deviate` stops at ROUTED findings.
`.kata/deviations/findings.json` is the handoff to P2b.

## Engine surfaces — `tools/deviation.py`

All surfaces confirmed present in `tools/deviation.py` (verify-before-reuse per
`protocol/reuse-claims.md`):

- **`tally_self_consistency(votes, *, k_min=2)`** — LD4 step 4 tally; returns
  `{"agree": int, "total": int, "passes": bool}`; passes iff `agree ≥ k_min`. Fail-closed: empty →
  `passes=False`. [TUNABLE `k_min`]
- **`self_consistency_entropy(votes)`** — normalized binary entropy of the agreement distribution in
  `[0, 1]`; feeds the `(1 − entropy)` confidence term.
- **`corroboration_gate(llm_finding, corroborators)`** — HARD gate (LD4 step 5, IRIS pattern); returns
  `{"corroborated": bool, "route": str | None, "co_located": list}`. Uncorroborated (LLM-only) →
  `route="human"` — never auto-fix-eligible.
- **`compute_confidence(msas, sc_entropy, structural_prior, *, weights=DEFAULT_WEIGHTS)`** — LD5 heuristic
  formula `C = w1·MSAS + w2·(1−entropy) + w3·Prior`; clamped `[0, 1]`. [TUNABLE `DEFAULT_WEIGHTS`]
- **`apply_force_low(confidence, *, sparse_signal, low_cap=DEFAULT_THRESHOLDS["low_cap"])`** — caps
  confidence into the LOW/defer band for sparse-signal modules. [TUNABLE `low_cap`]
- **`route_finding(confidence, *, thresholds=DEFAULT_THRESHOLDS)`** — returns `"auto-fix-eligible"` /
  `"research"` / `"defer"`. (`"human"` comes from `corroboration_gate` / the refute path in `run_funnel`,
  not from this function.) [TUNABLE `DEFAULT_THRESHOLDS`]
- **`run_funnel(finding)`** — pure composition: SC gate → corroboration gate → refute → confidence →
  force-LOW → route. Invariant funnel order. The primary composition point for this skill.
- **`findings_schema()`** — JSON Schema dict for a routed finding (single source of truth for the
  `.kata/deviations/findings.json` artifact).
- **`emit_findings(findings, path)`** — writes the routed findings list as JSON; creates parent dirs.
- **`load_findings(path)`** — JSON round-trip load (for incremental / resume use).
- **`DEFAULT_WEIGHTS`** — TUNABLE LD5 confidence weights (`w1/w2/w3`); calibratable without re-freezing
  the PLAN.
- **`DEFAULT_THRESHOLDS`** — TUNABLE routing thresholds (`tau_high/tau_low/low_cap`); calibratable without
  re-freezing the PLAN.

## FM engine surfaces — `tools/function_model.py`

Confirmed present in `tools/function_model.py`:

- **`function_model.load_function_model(path)`** — loads a P1 FM artifact from
  `.kata/function_models/<slug>.json`.
- **`function_model.evaluate_spec(fm, call)`** — the AST-safe spec-wrapper; evaluates FM
  pre/postconditions against a call record `{"inputs": {...}, "result": <value>}` via
  `function_model._safe_eval`; returns `{"ok": bool, "violations": [...]}`. The only sanctioned path for
  FM assertion evaluation; `eval`/`exec` are prohibited throughout (registered in
  `protocol/exec-safety.md`; in-process evaluation section).

## Output artifact

**`.kata/deviations/findings.json`** — a JSON array of routed finding dicts conforming to
`deviation.findings_schema()`. Each finding carries:

| Field | Type | Description |
|---|---|---|
| `module` | string / null | Repo-relative module path |
| `locus` | string / null | Function/block/line reference |
| `sc_tally` | object / null | `{"agree", "total", "passes"}` from `tally_self_consistency` |
| `corroboration` | object / null | Gate result from `corroboration_gate` |
| `refuted` | bool / null | `True` iff adversarial refute succeeded (contested) |
| `confidence` | number / null | LD5 heuristic confidence in `[0, 1]`; null if funnel stopped early |
| `sparse_signal` | bool / null | Whether force-LOW was applied |
| `route` | string | `"auto-fix-eligible"` / `"research"` / `"defer"` / `"human"` |
| `funnel_stop` | string / null | Stage where funnel stopped early; null if ran to completion |

P2b (fix loop) consumes this artifact. `kata-deviate` writes it and stops.

## Escalation policy — `[[kata-research]]`

**`[[kata-research]]` is escalation-only (DESIGN H5) — it is NOT a discovery source.** It must not appear
in Steps 1–5 of the pipeline. Research is invoked only by the orchestrator for `research`-routed findings
(≤2 rounds via the grounding gate), not by this skill during candidate gathering or corroboration.
Treating `[[kata-research]]` as a signal source in the discovery pipeline is a defect against H5.

## Invariants

- **Never-tiered / debug-spine:** this skill is invoked only when `kata/module/debug` is present in the
  run's modules, after the comprehension phase has produced FMs to `.kata/function_models/`. Absent
  `kata/module/debug`, the skill is a silent no-op. Version-up / greenfield runs are byte-for-byte
  unchanged (BC: additive only).

- **Engine delegation — no re-implementation in prose:** every deterministic gate decision (vote tally,
  corroboration check, confidence formula, force-LOW, routing) is delegated to `tools/deviation.py`. This
  skill gathers signals and calls the engine; it never re-implements a threshold or tally in prose.

- **Default-FAIL / fail-closed posture:** self-consistency ties resolve to `passes=False`; zero
  corroborators route `"human"` (never `auto-fix-eligible`); adversarial rebuttal routes `"human"`. A
  finding reaches `auto-fix-eligible` only by surviving all three gates (≥2/3 SC + ≥1 corroborator +
  `refuted=False`) plus a confidence score above `tau_high`.

- **Corroborator objectivity (engine-enforced):** every corroborator dict MUST carry a `source` field whose value is in `_OBJECTIVE_SOURCES` (`test`, `type`, `tool`, `snyk`, `lint`, `fm`, `sbfl`); the engine silently ignores any corroborator with a missing or non-allowlisted `source`.

- **No new execution sink:** FM-deviation reuses `function_model.evaluate_spec` /
  `function_model._safe_eval` (already registered in `protocol/exec-safety.md`). Dynamic call-record
  capture is instrumentation of operator-authored test runs (existing sink). Snyk = existing
  `mcp__Snyk__snyk_code_scan` MCP surface. Static/lint/type tools are read-only analysis. `kata-diagnose`
  is an existing skill. `tools/deviation.py` is pure decision logic (no subprocess, no eval, no exec).
  P2a registers no new exec sink row.

- **Confidence is heuristic v1:** no isotonic calibration (fast-follow per DESIGN LD5). Weights and
  thresholds (`DEFAULT_WEIGHTS`, `DEFAULT_THRESHOLDS`) are `[TUNABLE]` knobs — calibratable without
  re-freezing the PLAN. Do not claim calibrated precision in outputs or logs.

- **No phantom reuse:** every engine surface cited in this skill resolves to a real symbol in
  `tools/deviation.py` or `tools/function_model.py`. `[[kata-research]]` is cited escalation-only.
  `[[kata-diagnose]]` resolves to `skills/execute/kata-diagnose/`. `[[kata-review]]` resolves to
  `skills/evaluate/kata-review/`.
