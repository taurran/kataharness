---
title: "Debug Mode — Phase 1 PLAN (run-shape wiring + kata-comprehend oracle)"
status: FROZEN — freeze-gate kata-review HOLD→SHIP (2026-06-27)
date: 2026-06-27
spec: debug-mode
phase: P1 (foundation)
source: FROZEN DESIGN .planning/specs/debug-mode/DESIGN.md (LD1, LD2, LD7); recipe per .planning/HANDOFF.md §5
build-gate: blockers cleared (install-portability D104 + kata-preflight D109)
---

# Debug Mode — Phase 1 PLAN (foundation)

Phase 1 of the phased Debug Mode build. Scope = the **substrate** the rest of the feature consumes:
the **`debug` run-shape wiring** (LD1) and the **`kata-comprehend` function-model oracle** (LD2, LD7).
The 7-step deviation pipeline (LD4), characterization-gen + behavioral drift gate (LD6/§5), language
prompt-profiles (LD10), and onboarding (LD13) are **P2/P3 — explicitly out of scope here**.

This PLAN partitions P1 into **disjoint-ownership slices** with a wave DAG. It does not introduce decisions;
every choice traces to a LOCKED decision in the frozen DESIGN. An unresolved point ⇒ return to the DESIGN/grill.

## In scope (P1)
- **LD1** — the `debug` run-shape (peer of version-up, `target.kind==existing`), selectable at bootstrap,
  recognized by `kata-orchestrate` which sequences a **comprehension phase** before any change. (P1 wires the
  run-shape + the comprehension-phase hook; the fix/pipeline/drift wiring is P2.)
- **LD2/LD7** — `kata-comprehend`: builds a per-module **`function_model`** (executable pre/postcondition
  assertions + NL `intent_summary` + behavioral examples + `derivation_sources` + `confidence`), checkable via a
  **spec-wrapper**. Every FM is a hypothesis (the architecture gates on corroboration, not FM accuracy — that
  gating is P2).

## Out of scope (deferred to P2/P3 — do NOT build here)
- The 7-step deviation pipeline + confidence-routing consumption (LD4/LD5) → P2.
- Characterization-suite generation + the behavioral drift gate (LD6, §5) → P2.
- Language prompt-profiles (LD10) → P3. Onboarding/convert-to-loop (LD13) → P3.
- Formal isotonic confidence calibration (LD5 fast-follow) and the surface/AST structural-drift layer (§5 H4)
  remain DESIGN-level fast-follows.

## The `function_model` artifact (the P1 keystone — LD2 full form)
Schema (emitted one per module/function by `kata-comprehend`, validated + executed by the engine):
```json
{
  "module": "<repo-relative path or qualified symbol>",
  "intent_summary": "<natural-language intended function>",
  "preconditions":  ["<python boolean expr over named inputs>", "..."],
  "postconditions": ["<python boolean expr over `result` and inputs>", "..."],
  "behavioral_examples": [{"inputs": {"<name>": <val>}, "expected": <val>}],
  "derivation_sources": ["graph"|"docs"|"types"|"commit-history"|"callers"|"contract-inference", "..."],
  "confidence": 0.0
}
```
- `confidence` is stored in `[0,1]`; the **heuristic computation and routing that consume it are P2** (LD5).
  P1 only validates the field and lets `kata-comprehend` populate it.
- The **spec-wrapper** is the testable seam (DESIGN §7): given an FM + a call record, evaluate pre/postconditions
  and return a structured pass/violation result. **FM assertions are authored by `kata-comprehend` (an LLM) →
  they are EXTERNAL-trust-domain input** (`protocol/exec-safety.md`), so evaluating them is a NEW execution
  surface that must be registered and guarded:
  - **`eval`/`exec` of an FM assertion string is PROHIBITED — including `eval(expr, {"__builtins__": {}}, ns)`.**
    Empty-builtins `eval` is a known-escapable sandbox (`().__class__.__bases__[0].__subclasses__()…` reaches
    `os`/`subprocess`). This is exactly the class `exec-safety.md` exists to stop.
  - The evaluator is an **AST allowlist**: `ast.parse(expr, mode="eval")`, then walk and **reject** any node
    outside a whitelist of {`Compare`, `BoolOp`, `UnaryOp`, `BinOp`, comparison/bool/arith operators, `Constant`,
    `Name` (load only), `List`/`Tuple`/`Dict`/`Set` literals, `Subscript`/`Index` over those}. **No `Attribute`
    access, no `Call`** (except an explicit vetted allowlist — e.g. `len`, `abs`, `min`, `max` — resolved from a
    fixed safe-symbol table, never from builtins). Names resolve only to the FM's bound inputs + `result`.
    A non-conforming assertion ⇒ validation/violation error, never execution.
  - S2 **registers this surface** in `protocol/exec-safety.md` (a new "in-process evaluation of external
    expressions → AST allowlist, never eval/exec" rule + registry row).

## Slices (disjoint file ownership)

### Slice S1 — `debug` run-shape wiring  *(no Python; doc/skill)*
**The discriminator (resolves the debug-vs-version-up ambiguity — both are `target.kind=="existing"`):**
orchestrate dispatches off `mode`/`modules`, **not** `runShape` (`config.md` design rules). So the `debug`
run-shape preset pre-fills a **distinct module marker `kata/module/debug`**, and orchestrate's comprehension-phase
hook fires **iff that module is present** — exactly mirroring how `kata-slop-check` is gated on `kata/module/slop`
(precedent: `CONTEXT.md` "dispatched … only when `kata/module/slop` is in the run's modules"). `version-up`
(no debug module) ⇒ no comprehension phase. `runShape:"debug"` stays provenance-only, consistent with
`config.md`.
**Owns:**
- `protocol/config.md` — add `debug` to the `runShape` enum + a one-row note (peer of version-up;
  `target.kind==existing`; **gated by the `kata/module/debug` module, not by runShape**).
- `skills/coordinate/kata-bootstrap/SKILL.md` + `skills/coordinate/kata-bootstrap/resources/run-shapes.md`
  — add the `debug` run-shape preset (pre-fills `mode` + `modules:[…,"kata/module/debug"]` + `target.kind:existing`);
  selectable in the run-shape question; readiness may flag execution-pending like version-up.
- `skills/coordinate/kata-orchestrate/SKILL.md` — when `kata/module/debug` is in the run's modules, **sequence a
  comprehension phase that invokes `[[kata-comprehend]]` before any change** (ADDITIVE, mirrors the slop-check
  gating). Pipeline/drift/fix wiring is explicitly **deferred to P2** (leave a named, commented seam, not a stub
  that executes). Absent the module ⇒ this hook is a silent no-op.
**Acceptance:** `validate_skills` green; `config.md` runShape enum + `run-shapes.md` preset both list `debug` and
the preset includes the `kata/module/debug` module; the orchestrate comprehension hook is **unambiguously gated on
the module's presence**; **BC: a `version-up`/greenfield config (no `kata/module/debug`) triggers NO comprehension
phase — every existing run is byte-for-byte unchanged.** (The discriminator/BC check is verifiable by reading the
gating condition; an end-to-end config example is confirmed at the integration gate, not as a unit test — S1 owns
no Python.)

### Slice S2 — `function_model` engine  *(Python)*
**Owns:** `tools/function_model.py` + `tools/tests/test_function_model.py` + `tools/tests/test_exec_safety.py`
(extend its coupling to cover the new surface) + a registry addition to `protocol/exec-safety.md`. That contract
is currently scoped to *subprocess* sinks; S2 **widens it** with a short "in-process evaluation of external
expressions" subsection (rule: AST-allowlist, never `eval`/`exec`) and adds `_safe_eval` as a registry row there
— do not file an in-process surface under the subprocess-only heading.
**Surfaces (public, cite-able by name per `protocol/exec-safety.md` + cite-by-anchor):**
- `function_model_schema() -> dict` — the JSON schema (single source of truth).
- `validate_function_model(fm: dict) -> list[str]` — returns errors (empty = valid); checks required fields,
  `confidence ∈ [0,1]`, sources ⊆ the allowed set, assertion fields are lists of strings, **and that every
  assertion parses + passes the AST allowlist** (a non-conforming assertion is a validation error, surfaced by
  `kata-comprehend` before any evaluation).
- `_safe_eval(expr: str, names: dict) -> bool` — the AST-allowlist evaluator (PROHIBITS `eval`/`exec`; node
  whitelist per §function_model; `Attribute`/`Call`-outside-allowlist ⇒ `ValueError`).
- `evaluate_spec(fm: dict, call: dict) -> dict` — the **spec-wrapper**: given an FM and a call record
  (`{"inputs": {...}, "result": ...}`), evaluate each pre/postcondition via `_safe_eval` over a namespace of the
  bound inputs + `result` and return `{"ok": bool, "violations": [<which assertions failed>]}`.
- `emit_function_model(fm, path)` / `load_function_model(path)` — JSON round-trip to `.kata/function_models/`.
**Acceptance (default-FAIL, runnable):** schema-valid FM round-trips; `validate_function_model` rejects each
malformed shape (missing field, bad confidence, bad source, non-list assertions, **assertion failing the AST
allowlist**); `evaluate_spec` returns `ok:true` for behavior matching the FM and `ok:false` + the violated
assertion for an injected deviation on a seeded fixture; **`_safe_eval` raises on an escape attempt** (e.g.
`().__class__.__bases__`, `__import__('os')`, attribute access, an out-of-allowlist call); the new
`test_exec_safety.py` registry coupling still passes. **Mutation non-vacuous** on the violation-detection guard
AND on an AST-allowlist reject branch.
**Test seam:** the spec-wrapper on fixtures (true behavior passes; injected deviation fails; escape attempt
raises) — DESIGN §7.

### Slice S3 — `kata-comprehend` skill  *(depends_on S2)*
**Owns:** `skills/plan/kata-comprehend/SKILL.md` (category `plan`, alongside `kata-graph`; never-tiered spine of
the debug run — it is debug-only, invoked by the orchestrate comprehension phase).
**Content:** drives `function_model.py` (cite surfaces by **function name**, not line); derives each module's FM
from the LD7 inputs (graph/`kata-graph` digest + docs/comments/types/config + commit-history/blame + caller usage
+ cross-module contract inference), flags sparse-signal modules **force-LOW** confidence (LD5 stored, not yet
routed), emits schema-valid FMs to `.kata/function_models/`. Honest-scope note: FM is a **hypothesis**; P1
produces + validates the oracle but does **not** act on it (no fix loop until P2). Reuse claims verified per
`protocol/reuse-claims.md`; `kata-understand` is **NOT** reused (it is post-run/map-only — DESIGN §2).
**Acceptance (slice-level, runnable):** `validate_skills` passes (frontmatter/schema/anchors); no phantom reuse
(every cited engine surface resolves to a real symbol in `function_model.py`). **The FM-emission check** (that a
`kata-comprehend` run produces an FM `validate_function_model` accepts) is **non-deterministic (a model run) →
verified at the integration/`kata-evaluate` gate on a fixture, NOT as a slice unit test.**
**depends_on:** S2 (cites the engine's real surfaces).

## Wave DAG
- **Wave 1 (parallel):** S1, S2 — disjoint files, no interdependency.
- **Wave 2:** S3 — depends_on S2.
Concurrency: ≤2 workers wave 1. All slices in git worktrees; disjoint ownership verified before dispatch.

## Integration gate (after the frontier drains)
pytest green · `validate_skills` (expect 40 skills/0 — `kata-comprehend` is new) · Snyk code scan on
`tools/function_model.py` (new first-party Python) · `gate_emit` RESULT/footprint/mutation · README regen
(`validate_skills.py --write`). Then fresh-context `kata-evaluate` (9-rubric, default-FAIL) → standing D98
`kata-review` → operator merge gate.

## Risks / escalation triggers
- **Safe assertion evaluation (S2) — HARD exec-safety line:** the spec-wrapper evaluates EXTERNAL (LLM-authored)
  assertions, so `eval`/`exec` is **prohibited outright**, including empty-builtins `eval` (a known-escapable
  sandbox). The evaluator is an **AST allowlist** (parse → reject non-whitelisted nodes; no attribute access, no
  out-of-allowlist calls). If the AST allowlist cannot safely express a needed assertion form, the worker
  **escalates** — it never falls back to `eval`. S2 registers the surface in `protocol/exec-safety.md`.
- **Scope creep into P2:** if a slice finds itself needing the deviation pipeline or drift gate to be testable,
  STOP — that is the P1/P2 boundary; the FM oracle is validated in isolation (DESIGN §7), not via the pipeline.
- **BC:** any change that alters a non-debug run is a defect — the run-shape is purely additive.
