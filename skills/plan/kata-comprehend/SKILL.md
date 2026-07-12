---
name: kata-comprehend
description: >-
  Pre-change, whole-repo comprehension pass for Debug Mode (LD2/LD7, P1). Builds a per-module/function
  function_model (executable pre/postcondition assertions + NL intent_summary + behavioral examples
  + derivation_sources + confidence) from graph/PageRank, docs, types, commit-history, caller usage,
  and cross-module contract inference. Every FM is a hypothesis; P1 validates the oracle only — no
  deviation detection or fix loop (P2). Emits schema-valid FMs to .kata/function_models/. Invoked
  by kata-orchestrate comprehension phase, gated on kata/module/debug.
license: Apache-2.0
version: 0.1.0
category: plan
status: beta
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Bash, Write]
source: >-
  new (KataHarness original, Debug Mode P1 — function-model oracle, DESIGN LD2/LD7)
tags:
  - kata/plan
  - kata/spine
  - kata/module/debug
  - comprehension
---

# kata-comprehend — pre-change function-model oracle

The debug run's comprehension pass. Before any change is made, `kata-comprehend` derives the
**intended function** of every module and emits an executable oracle — a `function_model` (FM) — so
that the downstream deviation pipeline can compare *what the code does* against *what it was meant
to do*. A bug is a deviation of code from its derived intended function (DESIGN LD2).

**Honest scope (P1 vs P2):** This skill PRODUCES and VALIDATES the oracle only. It does NOT act on
it — no deviation detection, no fix loop, no drift gate (all P2). `confidence` is stored in each FM
and not yet routed; confidence-tiering and its consumption are P2 (DESIGN LD5). Every FM is a
hypothesis; the architecture gates on corroboration, not FM accuracy.

**Not reused from `kata-understand`:** `kata-understand` is post-run and map-only; it derives no
intent (DESIGN §2, verified at `modules/closeout/kata-understand/SKILL.md`). `kata-comprehend` is
pre-change and intent-deriving; they are distinct and must not be conflated.

## Inputs (LD7)

For each module, gather evidence across all available channels before authoring the FM:

1. **Graph / PageRank digest** — from the `kata-graph` output (`kata.graph.json`). Symbols, their
   PageRank scores, and reference/call edges. Visit modules in dependency/PageRank order (DESIGN
   LD8 sweep ordering — highest-rank / churn-risk-weighted first).
2. **Docs, comments, types, config** — module-level docstrings, inline comments, type annotations,
   and any configuration that governs the module's contract or expected behavior.
3. **Commit history / blame** — recent commits and blame context for the module; change frequency
   and hotspot signal inform both FM derivation and confidence assessment.
4. **Caller usage** — how other modules call this module's public symbols; resolves ambiguous
   contracts from observed call sites.
5. **Cross-module contract inference** — what callers expect from return shapes/types; what callees
   require from passed arguments. Synthesized across the reference graph.

When evidence is thin across all five channels (**sparse-signal module**), force `confidence` to
**LOW** (a value ≤ 0.3 is a reasonable P1 default `[TUNABLE in P2]`). Flag sparse-signal modules
in the per-module confidence note. Routing that consumes this low-confidence flag is P2 (DESIGN
LD5) — not wired here.

## Method — per-module loop

For each module/function (visited in PageRank/churn order):

1. **Derive intent** — synthesize an `intent_summary` (NL) from the gathered inputs. The summary
   must be specific enough to be falsifiable: it should imply what correct vs. incorrect behavior
   looks like.

2. **Author assertions** — write `preconditions` and `postconditions` as plain boolean expressions
   over named inputs and `result`. Every assertion must conform to the §Assertion grammar. Keep
   assertions minimal and directly traceable to the derived intent. When no reliable assertion can
   be authored (insufficient signal), emit an empty list rather than a speculative expression.

3. **Compose behavioral examples** — two to four concrete `{"inputs": {...}, "expected": <val>}`
   pairs that cover the happy path and at least one edge case. These serve as FM-level test
   fixtures for the spec-wrapper.

4. **Record derivation sources** — list which of `"graph"`, `"docs"`, `"types"`,
   `"commit-history"`, `"callers"`, `"contract-inference"` contributed evidence. Only list sources
   that actually informed this FM.

5. **Set confidence** — a `[0.0, 1.0]` heuristic estimate of FM fidelity. Sparse-signal modules:
   force LOW. Multi-source modules with consistent signals: higher. Exact weight formula is P2
   (DESIGN LD5); P1 populates the field honestly based on available evidence.

6. **Validate** — call `validate_function_model` from `tools/function_model.py`. A non-empty error
   list means the FM is malformed; fix it before emitting. Surface persistent errors (log + flag
   the module as sparse-signal / unresolvable) rather than emitting a false-confident FM. An FM
   with a non-empty `validate_function_model` result is **never emitted**.

7. **Smoke-test via spec-wrapper** — call `evaluate_spec` from `tools/function_model.py` with
   each behavioral example as a call record. If an example produces a violation, revise the FM
   (assertion or example) to be internally consistent before emitting.

8. **Emit** — call `emit_function_model` from `tools/function_model.py` to write the validated FM
   to `.kata/function_models/<module-slug>.json`.

## Engine — `tools/function_model.py`

Drive the following surfaces by exact function name (verify-before-reuse per
`protocol/reuse-claims.md`; all surfaces confirmed present in `tools/function_model.py`):

- **`function_model_schema()`** — returns the JSON Schema (single source of truth for required
  fields and their types). Consult it to confirm the FM shape before authoring.

- **`validate_function_model(fm)`** — validates an FM dict; returns a list of error strings (empty
  = valid). Checks required fields, `confidence ∈ [0,1]`, sources ⊆ the allowed set, assertion
  fields are lists of strings, and every assertion passes the AST allowlist. A non-empty return is
  a hard stop — fix the FM before emitting.

- **`_safe_eval(expr, names)`** — the AST-allowlist evaluator. Security-critical: this is the only
  sanctioned path for evaluating LLM-authored assertions. `eval`/`exec` are PROHIBITED throughout
  (registered in `protocol/exec-safety.md`). Available for ad-hoc pre-emit smoke-testing of
  authored assertion strings.

- **`evaluate_spec(fm, call)`** — the spec-wrapper: given an FM and a call record
  `{"inputs": {...}, "result": <val>}`, evaluates pre/postconditions via `_safe_eval` and returns
  `{"ok": bool, "violations": [...]}`. Use to verify behavioral examples are consistent with
  authored assertions before emitting.

- **`emit_function_model(fm, path)`** — writes a validated FM as pretty-printed JSON to
  `.kata/function_models/`. Creates parent directories as needed. Call only after
  `validate_function_model` returns an empty list.

- **`load_function_model(path)`** — JSON round-trip load. Use when resuming a partial comprehension
  pass (incremental sweep over a large repo).

## Assertion grammar

Assertions are evaluated by `_safe_eval`'s AST allowlist (`protocol/exec-safety.md`,
in-process evaluation section). Authored assertions **must** stay within this grammar — a
non-conforming assertion is a validation error caught by `validate_function_model`, never executed:

**Allowed node types:** `Compare`, `BoolOp` (`and`/`or`), `UnaryOp` (`not`, unary `+`/`-`/`~`),
`BinOp` (arithmetic and bitwise operators), `Constant`, `Name` (load-mode only — must resolve to a
bound input name or `result`), `List`/`Tuple`/`Dict`/`Set` literals, `Subscript` over the above.

**Calls:** only names in the fixed safe-symbol table: `len`, `abs`, `min`, `max`, `sum`, `sorted`,
`isinstance`, `type`, `int`, `float`, `str`, `bool`, `list`, `dict`, `tuple`, `set`, `round`,
`range`, `all`, `any`. No keyword arguments. No starred arguments.

**PROHIBITED (raise ValueError in `_safe_eval` / fail `validate_function_model`):** `Attribute`
access (`x.attr`), calls outside the safe-symbol table, comprehensions, lambdas, walrus (`:=`),
ternary expressions (`a if c else b`), f-strings, `Starred` expressions.

Valid examples: `isinstance(result, list)`, `len(result) > 0`,
`result >= 0 and result <= 1`, `all(x >= 0 for x in result)` — **wait: generator expression is
PROHIBITED**. Use `min(result) >= 0` instead. When in doubt, author the simplest expression that
covers the assertion intent.

## Output

- **`.kata/function_models/<module-slug>.json`** — one JSON file per module/function, written by
  `emit_function_model`. Derive the slug from the module path (forward-slash separated, file
  extension stripped, directory separators converted to dashes, e.g., `tools-graph-gen` for
  `tools/graph_gen.py`).

- **Per-module confidence note** — a brief human-readable summary (stdout or appended to a run
  log) of each module's confidence level and any sparse-signal flags. Consumed by the debug-run
  closeout report (DESIGN LD12 confidence map). Format: one line per module, e.g.
  `[HIGH 0.82] tools/graph_gen.py — 5 sources` or `[LOW* 0.15] tools/old_util.py — sparse signal`.

## Invariants

- **Never-tiered / debug-spine:** this skill is invoked only when `kata/module/debug` is present in
  the run's modules. Absent that module, the orchestrate comprehension-phase hook is a silent no-op;
  no existing-run path is affected (BC: additive only).

- **Default-FAIL posture:** a module that cannot be comprehended (insufficient signal or persistent
  FM validation errors) is recorded as force-LOW confidence + flagged — never emitted with
  false-confident assertions. Persistent `validate_function_model` errors surface to the operator.

- **No phantom reuse:** every engine surface cited above resolves to a real function in
  `tools/function_model.py`. `kata-understand` is explicitly NOT a basis for this skill (DESIGN §2).
