---
date: 2026-06-20
spec: greater-loop
phase: 0 — FOUNDATIONS
status: FROZEN — partitions Phase 0 (F1 ∥ F2) into disjoint vertical slices for an orchestrated foreground-parallel build
designRef: ./DESIGN.md (FROZEN, D87–D90) · ./ROADMAP.md Phase 0
delivery: build-through (BUILD-THROUGH directive — no test ceremony until Phase 4; per-merge correctness gates apply)
tags: [plan, greater-loop, phase-0, foundations, disjoint-ownership, waves, frozen]
---

# Phase 0 — FOUNDATIONS · frozen PLAN

Two **independent** vertical slices, built **in parallel** (Wave 1, no inter-slice dependency). Each is built by
a worker subagent in an **isolated git worktree** (Sonnet), TDD, then octopus-merged → integration gate →
fresh-context `kata-evaluate` → continue (no stop). File ownership is **disjoint** — verified below.

## LOCKED decisions (quoted from DESIGN §5, verbatim — do NOT re-decide)
- **F1:** *"Make `kata-evaluate`/the gate actually **emit** `RESULT.json` (via the built `run_result`), compute the
  **footprint manifest** vs the plan, and record the **mutation/non-vacuity** result. Closes the dogfood-2
  residual; it is the closeout's data layer."*
- **F2:** *"Install tree-sitter + a generator that produces `kata.graph.json` per the existing `protocol/graph.md`
  contract (**Python first**), enough to back `kata-understand` + version-up footprint. **Defer the full Graphify
  oracle** (neighbors/shortest-path/pr-impact)."*
- **RESULT.json schema is PINNED** to `tools/run_result.py:build_result` (kata-evaluate §"Machine-readable inputs"):
  `gateName, command, exitCode, passed, failed, skipped, stdoutTail, baselineSha, resultSha, utc`. Producer and
  consumer agree on this shape — neither slice may fork it.
- **graph schema is PINNED** to `protocol/graph.md` (file/symbol nodes, def/ref/import edges, `meta.backend`).

## Wave DAG
```
Wave 1 (parallel):  F1 ──┐
                    F2 ──┘   (no edge between them — fully disjoint)
Integration:        octopus-merge F1+F2 → uv sync → full green gate → fresh-context kata-evaluate
```

---

## Task F1 — wire the eval artifacts into the live gate
**Owns (disjoint):**
- `tools/gate_emit.py` (NEW)
- `tools/tests/test_gate_emit.py` (NEW)
- `skills/evaluate/kata-evaluate/SKILL.md` (EDIT — point at the emitter + `.kata/` paths)
- `skills/coordinate/kata-orchestrate/SKILL.md` (EDIT — integration-gate step emits artifacts)
- `skills/execute/kata-tdd/SKILL.md` (EDIT — mutation step records the proof)

**read_first:** `tools/run_result.py`, `tools/footprint.py`, `tools/mutation_check.py`, the three owned SKILL.md
files, `skills/evaluate/kata-evaluate/SKILL.md` §"Machine-readable inputs the gate MUST consume".

**action:** Build `gate_emit.py` — the thin orchestrator that turns the three existing pure libraries into an
actually-produced artifact set during a run. It **composes, never reimplements** them:
1. `emit_gate_artifacts(gate_name, command, footprint, baseline_sha, result_sha, out_dir, *, mutation_records=None,
   runner=run_result.run_gate, utc=None) -> dict` —
   - run the gate (`runner(command) -> (output, exit_code)`),
   - `result = run_result.build_result(...)` → `write_result(result, out_dir/"RESULT.json")`,
   - `changed = footprint.changed_since(baseline_sha)`, `diffstat = footprint.diff_stat(baseline_sha)`,
     `man = footprint.manifest(changed, footprint, diffstat)` → write `out_dir/"footprint.json"`,
   - if `mutation_records` (list of `{testWentRed, nonVacuous}` dicts from `mutation_check.mutation_verdict`):
     write `out_dir/"mutation.json"` = `{"records": [...], "allNonVacuous": all(r["nonVacuous"] for r)}`,
   - return a summary dict `{resultPath, footprintPath, mutationPath|None, withinFootprint, passed, failed,
     skipped, exitCode}`.
   - `runner`/`utc` are injectable so tests stay pure (no real subprocess, deterministic timestamp).
2. A `__main__` CLI: `python -m gate_emit --gate-name N --command C --footprint A B C --baseline SHA --result SHA
   --out .kata` (mutation optional). `out_dir` defaults to `.kata/`; create it if missing.
3. **Wire the skills (additive paragraphs only — do NOT touch frontmatter):**
   - `kata-evaluate`: the gate reads `.kata/RESULT.json` (+ `.kata/footprint.json`, `.kata/mutation.json`)
     emitted by `tools/gate_emit.py`; name the emitter as the canonical producer.
   - `kata-orchestrate`: at the integration gate, the orchestrator runs `tools/gate_emit.py` to emit the artifact
     set before handing to `kata-evaluate`.
   - `kata-tdd`: the mutation/non-vacuity step records each verdict via `mutation_check.mutation_verdict`, passed
     to `gate_emit` as `mutation_records`.

**verify (default-FAIL):** `cd tools && uv run pytest tests/test_gate_emit.py -q` — must START red (write tests
first), END green. Tests cover: RESULT.json written with the pinned schema + correct counts (injected output);
footprint.json reflects in/out partition; mutation.json aggregates `allNonVacuous` correctly (true when all bite,
false when one is vacuous); summary dict shape; `out_dir` auto-created. Use `tmp_path` + an injected `runner`
(no real subprocess).

**acceptance (falsifiable):**
- Running the emitter produces `RESULT.json` byte-identical in shape to `build_result`'s contract (same keys).
- A run that changes a file outside the declared footprint yields `withinFootprint == false` in `footprint.json`.
- A vacuous mutation record flips `allNonVacuous` to `false`.
- The three SKILL.md edits name `tools/gate_emit.py` and the `.kata/` artifact paths; no frontmatter changed.
- `uv run python validate_skills.py` stays green (31/0).

**threat model:** `gate_emit` runs a shell command (`run_gate`, `shell=True`) — attacker-reachable only via the
`command` arg the operator/orchestrator supplies (same trust level as today's gate invocation; no new external
surface). No untrusted input parsed. Mitigation: command is operator-supplied, never derived from repo content.

---

## Task F2 — graph runtime operational (minimal, tree-sitter floor, Python-first)
**Owns (disjoint):**
- `tools/graph_gen.py` (NEW)
- `tools/tests/test_graph_gen.py` (NEW)
- `tools/pyproject.toml` (EDIT — add `tree-sitter`, `tree-sitter-python` deps)
- `tools/uv.lock` (regenerated by `uv add`)
- `skills/plan/kata-graph/SKILL.md` (EDIT — name the generator as the tree-sitter-floor producer)

**read_first:** `protocol/graph.md` (the PINNED schema — single source of truth), `skills/plan/kata-graph/SKILL.md`.
**Verified de-risk:** `tree-sitter==0.25.2` + `tree-sitter-python==0.25.0` install + parse Python cleanly on this
platform (orientation probe). Use `tree_sitter_python.language()` + `tree_sitter.Language/Parser`.

**action:** Build `graph_gen.py` — the **tree-sitter floor** generator that walks a repo's Python files and emits
`kata.graph.json` per `protocol/graph.md`:
1. `build_graph(root, files=None) -> dict` —
   - discover `*.py` files under `root` (or use the passed list); skip `.venv`, `__pycache__`, worktree dirs;
   - per file: a `file` node (`id=path`, `kind="file"`, `path`, `hash`=content hash, `rank` (float), `lang="python"`);
   - parse with tree-sitter → `symbol` nodes for `function_definition`, `class_definition`, and methods
     (`symKind ∈ function|class|method`), `id = path::name[~N]` (def-order ordinal for same-name collisions),
     `span=[startLine,endLine]` 1-indexed inclusive, `hash`, `rank`, optional `signature`;
   - `edge`s: `def` (file→symbol) for every symbol; `import` (file→file, best-effort) from `import`/`import_from`
     statements resolved to in-repo paths; `ref` (symbol→symbol, best-effort) from call/identifier references.
     **`call` is oracle-only — omit it** (defer Graphify).
   - compute a PageRank `rank` over the node/edge graph (personalization is use-time, NOT here — uniform rank at
     build time per the schema: "computed on every floor build");
   - `meta = {"backend": "tree-sitter", "repoHash": <hash of file hashes>, "generatedAt": <iso utc>}`.
2. Content-hash **incremental** cache: if an existing `kata.graph.json` is passed/loaded, reuse nodes whose file
   `hash` is unchanged; only re-parse changed files. Minimal is acceptable (full rebuild ok if cache absent).
3. A `__main__` CLI: `python -m graph_gen --root . --out kata.graph.json`.
4. `uv add tree-sitter tree-sitter-python` (updates pyproject + uv.lock).
5. Wire `kata-graph` SKILL.md (additive only — do NOT touch frontmatter): name `tools/graph_gen.py` as the
   tree-sitter-floor producer of `kata.graph.json`.

**verify (default-FAIL):** `cd tools && uv run pytest tests/test_graph_gen.py -q` — START red, END green. Tests run
against a **fixture** (write 2–3 tiny `.py` files into `tmp_path`): assert file nodes exist with hashes; assert a
known function + class + method become symbol nodes with correct `symKind` and 1-indexed inclusive spans; assert
same-name collisions get `~N` ordinals; assert `def` edges connect file→symbol; assert an `import` between two
fixture files yields a file→file `import` edge; assert `meta.backend == "tree-sitter"`; assert the output
**validates against `protocol/graph.md`** (required fields present on every node/edge).

**acceptance (falsifiable):**
- `build_graph` on the `tools/` directory itself produces a graph whose `meta.backend == "tree-sitter"` and whose
  symbol nodes include `tools/run_result.py::build_result` with a plausible span.
- Every node has the schema-required fields (`id/kind/path/hash/rank` for file; `+name/symKind/span` for symbol).
- Two fixture files with an `import` between them produce a file→file `import` edge.
- A same-name function defined twice in one file yields ids `…::name` and `…::name~1` (ordinal).
- `uv run python validate_skills.py` stays green (kata-graph already declares `Bash`; no frontmatter change).

**threat model:** parses repo Python with tree-sitter (AST only — never executes the code, unlike `import`).
No attacker-reachable surface beyond reading files the operator already trusts. Mitigation: AST parse only, no
`exec`/`eval`/import of target code; skip dirs that could contain vendored/untrusted trees.

---

## Integration (after both slices green in their worktrees)
1. Octopus-merge `phase0/f1-gate-emit` + `phase0/f2-graph-runtime` into an integration branch.
2. `cd tools && uv sync` (pulls F2's tree-sitter deps), then the **full green gate**:
   `uv run pytest -q` (expect 72 + new F1 + new F2 tests, 0 fail/skip) · `uv run python validate_skills.py` (31/0).
3. Snyk scan on the two new Python modules (`gate_emit.py`, `graph_gen.py`) — fix→rescan until clean.
4. Regenerate the README skill index if any description changed (integrator-owned, avoids worker contention).
5. **Fresh-context `kata-evaluate`** (no-write subagent) over this PLAN → PASS/NEEDS_WORK.
6. On PASS: merge to `master` (per-phase correctness gate satisfied) → **continue straight into Phase 1**
   (no dogfood/version-select ceremony — BUILD-THROUGH). Backout safety: tag `pre-phase0` before merge.

## Ownership disjointness check
| File | Owner |
|---|---|
| `tools/gate_emit.py`, `tools/tests/test_gate_emit.py` | F1 |
| `skills/evaluate/kata-evaluate/SKILL.md`, `skills/coordinate/kata-orchestrate/SKILL.md`, `skills/execute/kata-tdd/SKILL.md` | F1 |
| `tools/graph_gen.py`, `tools/tests/test_graph_gen.py`, `tools/pyproject.toml`, `tools/uv.lock` | F2 |
| `skills/plan/kata-graph/SKILL.md` | F2 |
| `README.md` (index regen), integration RESULT.json | Integrator (post-merge) |
No file appears in two lanes. `tools/tests/` is shared as a directory but the two test files are distinct. ✓
