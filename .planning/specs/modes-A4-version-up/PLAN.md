# Modes Spec A4 — Version-up + kata-graph Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this
> plan task-by-task. Steps use checkbox (`- [ ]`). The FROZEN contract is `./DESIGN.md` — quote its LOCKED
> decisions (L1–L6) verbatim; do not re-decide. Versions stay `0.1.0` (policy A). No `knowledgeGraph` config
> (deferred). No `[[wikilink]]` to unbuilt skills (`kata-understand`, etc.) — plain prose only.

**Goal:** Ship version-up execution + `kata-graph` per the frozen `DESIGN.md`: the `kata.graph.json` +
escalation protocol contracts, the `kata-graph` skill, version-up wiring in grill/plan, and the
`kata-orchestrate` generalization to rolling DAG-frontier dispatch + async escalation.

**Architecture:** Two new `protocol/` schemas (the contracts) + one new skill (`kata-graph`) + prose edits to
four existing skills, all validator/pytest-gated where machine-checkable and adversarial-`kata-review`-gated for
prose. Contract-mediated — no skill calls another's internals.

**Tech Stack:** Markdown skills + `protocol/` schemas; `tools/` Python/uv validator + pytest.

---

## File Structure
| Path | Task | Responsibility |
|---|---|---|
| `protocol/graph.md`, `protocol/escalation.md`, `protocol/config.md`, `tools/validate_skills.py`, `tools/tests/test_validate_skills.py` | T1 | the two new contract schemas + config `graph` block + validator enforcement |
| `skills/plan/kata-graph/SKILL.md` | T2 | the kata-graph skill (L1/L2/L3/L6) |
| `skills/coordinate/kata-orchestrate/SKILL.md` | T3 | rolling DAG-frontier dispatch + async escalation (L5, P1) |
| `skills/plan/kata-grill/RUBRIC.md` | T4 | Phase 0 invokes kata-graph when `target.kind == existing` |
| `skills/plan/kata-plan/RUBRIC.md` | T5 | version-up footprint ownership + blast-radius (L4) |
| `skills/coordinate/kata-readiness/SKILL.md`, `skills/evaluate/kata-evaluate/SKILL.md` | T6 | tree-sitter readiness gate + regression note |
| `README.md`, `.planning/SKILL-COST-RATINGS.md`, `docs/TAXONOMY.md` | T7 | register kata-graph (cost 3) |
| `.planning/DECISIONS.md`, `.planning/STATE.md`, `.planning/ROADMAP.md` | T8 | promote A4-GB → D47+; status |
| `.planning/specs/modes-A4-version-up/REVIEW.md` | T9 | adversarial review (D15) |

---

## Task 1: Contract schemas (`graph.md`, `escalation.md`) + config `graph` block + validator (Sonnet)

**Files:** Create `protocol/graph.md`, `protocol/escalation.md`; Modify `protocol/config.md`,
`tools/validate_skills.py:234`, `tools/tests/test_validate_skills.py`.

- [ ] **Step 1 — failing test.** Add to `tools/tests/test_validate_skills.py`:
```python
def test_a4_protocol_schemas_required():
    from validate_skills import REQUIRED_PROTOCOL, check_protocol_schemas
    assert {"id", "kind", "rank", "edge", "meta", "symKind"} <= set(REQUIRED_PROTOCOL["graph.md"])
    assert {"taskId", "decisionNeeded", "status", "kind"} <= set(REQUIRED_PROTOCOL["escalation.md"])
    assert "graph" in REQUIRED_PROTOCOL["config.md"]
    # the real protocol files must document their required terms (no findings)
    findings = [str(f) for f in check_protocol_schemas([])]
    assert not any("graph.md" in f or "escalation.md" in f for f in findings), findings
```
Run: `cd tools && uv run pytest tests/test_validate_skills.py::test_a4_protocol_schemas_required -v` → FAIL.

- [ ] **Step 2 — create `protocol/graph.md`** documenting the L2 contract verbatim from DESIGN.md (the `file`
  node fields, the `symbol` node fields incl. `symKind` enum, the `edge` fields with `import` file→file and
  `call` oracle-only, the `meta` block WITHOUT `seedSymbols`), plus: backends (tree-sitter floor populates
  def+ref(+import); grep-reduced = unranked, ordered by `path` then import-ref-count desc, exploration-only;
  Graphify-MCP oracle adds `call`/`community`), caching (content-hash incremental, ids line-independent), and a
  Notes section: "seedSymbols + digest + blast-radius are USE-TIME projections, never cached (L3)." Location:
  `kata.graph.json` at the branch root.

- [ ] **Step 3 — create `protocol/escalation.md`** documenting L5: the payload at `.kata/escalations/<task-id>.json`
  with fields `taskId, kind ("orchestrator-resolvable"|"human-required"), decisionNeeded, optionsConsidered[],
  agentRecommendation, rationale, lockedDecisionInTension?, costOfWaiting, costOfProceeding, status
  ("open"|"resolved"), resolution?`. Producer = the escalating worker. The board (`protocol/board.md`) carries
  only the one-line pointer `ESCALATE | <task-id> | <summary>` (append-only, L3 preserved). Lifecycle: worker
  writes (status=open) → orchestrator classifies/routes → resolver writes status=resolved + resolution. Note:
  resolved payloads are the engram learning surface (GB10, future).

- [ ] **Step 4 — config `graph` block.** In `protocol/config.md` schema table add:
  `| `graph` | `{ budget: int, marginDepth: int, backend: "tree-sitter"|"grep-reduced"|"graphify" }` | kata-graph tunables: digest token budget (default 3000), ownership reverse-dependent depth (default 1), backend selection. |`

- [ ] **Step 5 — validator.** In `tools/validate_skills.py`, extend `REQUIRED_PROTOCOL`:
```python
REQUIRED_PROTOCOL = {
    "config.md": ["mode","modules","effort","tiers","preflight","bakeoff","skillVersions","runShape","target","graph"],
    "dependencies.md": ["classification","scope","verify","install"],
    "graph.md": ["id","kind","path","name","symKind","span","rank","weight","edge","meta"],
    "escalation.md": ["taskId","kind","decisionNeeded","optionsConsidered","agentRecommendation","status"],
}
```

- [ ] **Step 6 — verify green + commit.** `cd tools && uv run pytest -q` (all pass) + `uv run python validate_skills.py`
  (`24 skills checked — 0 error(s)` — no new skills yet). Commit:
```
git add protocol/graph.md protocol/escalation.md protocol/config.md tools/validate_skills.py tools/tests/test_validate_skills.py
git commit -m "feat(A4): graph + escalation protocol contracts; config graph block; validator-enforced"
```

---

## Task 2: `kata-graph` skill (Opus)

**Files:** Create `skills/plan/kata-graph/SKILL.md`. **read_first:** `DESIGN.md` L1/L2/L3/L6, `protocol/graph.md`.

- [ ] **Step 1 — write the skill.** Frontmatter EXACTLY:
```yaml
---
name: kata-graph
description: >-
  Build a token-budgeted structural map of an existing codebase — the kata.graph.json contract — so the loop
  ingests a large repo cheaply. tree-sitter symbol/reference graph + personalized PageRank + a token budget;
  pluggable backend (grep-reduced / tree-sitter floor / Graphify-MCP oracle). Invoke at grill Phase 0 for
  version-up or any existing-repo run.
license: Apache-2.0
version: 0.1.0
category: plan
status: experimental
agnostic: true
cost-weight: 3
allowed-tools: [Read, Grep, Glob, Bash]
compatibility: >-
  Requires tree-sitter for the default backend (pre-flight, D29); grep-reduced is exploration-only
source: >-
  adapted-from aider repo-map (MIT — tree-sitter tag-queries + personalized PageRank + token budget) + Graphify
  (safishamsi/graphify, MIT — AST graph + MCP oracle get_neighbors/shortest_path/get_pr_impact)
tags:
  - kata/plan
  - kata/module/graph
  - graph
  - repo-map
  - token-optimization
---
```
  Body (points to `protocol/graph.md` for the schema; do NOT restate it): **Purpose** (token-saving structural
  map; the contract is the anti-chimera glue). **Backends** (tree-sitter floor = def+ref(+import); grep-reduced =
  unranked exploration-only; Graphify-MCP oracle = +call/+community + blast-radius queries). **Output** = the
  cached `kata.graph.json` (`protocol/graph.md`), content-hash incremental, **feature-agnostic** (L3).
  **Ranking** = personalized PageRank, **seeded at use-time** (tokenize the feature description → case-insensitive
  match vs symbol `name` → ×10, + user-named files) — never cached. **Digest** = top-rank signatures selected
  until the `[TUNABLE: graph.budget=3000]`-token estimate (chars/4) is hit (selection not truncation).
  **Slot** = invoked by [[kata-grill]] Phase 0 when `target.kind == existing`. Describe Graphify/kata-understand
  in plain prose — NO `[[kata-graph]]`-style links to unbuilt skills.

- [ ] **Step 2 — verify + commit.** `cd tools && uv run python validate_skills.py` → 25 skills, zero errors
  attributable to kata-graph (a README-sync error is expected, fixed in T7). Confirm no unresolved wikilinks.
```
git add skills/plan/kata-graph/
git commit -m "feat(A4): kata-graph — token-budgeted structural map skill (L1/L2/L3/L6)"
```

---

## Task 3: `kata-orchestrate` — rolling DAG-frontier dispatch + async escalation (Opus, P1)

**Files:** Modify `skills/coordinate/kata-orchestrate/SKILL.md`. **read_first:** DESIGN L5, `protocol/escalation.md`,
the current `## The loop` and `## Escalation` sections.

**action (LOCKED — quote L5):** This SUPERSEDES the synchronous wave-loop + synchronous escalation prose — the
edit must REMOVE the contradicting text, not just append.

- [ ] **Step 1 — replace `## The loop` opener.** Change "For each **wave** in dependency order:" to rolling
  DAG-frontier: *"Maintain a rolling frontier. A task is dispatchable iff (all its `depends_on` are integrated)
  ∧ (its owned files are disjoint from every in-flight task). Dispatch every dispatchable task (concurrently,
  each in its own [[kata-worktree]]); as each integrates, recompute the frontier. Waves are a derived view of
  this, not a hard gate."* Keep the isolate/dispatch/gate/integrate/checkpoint sub-steps; checkpoints integrate
  **in completion order** (linear history).

- [ ] **Step 2 — replace `## Escalation`** with the async model (L5): an escalation does NOT halt the run.
  Classify (orchestrator-resolvable → re-scope + re-dispatch, never reaches a human; human-required = a LOCKED
  conflict). For any escalation: write the structured payload (`protocol/escalation.md`,
  `.kata/escalations/<task-id>.json`) and append the one-line `ESCALATE | <task-id> | <summary>` to the board.
  **Park** the escalating task + its DAG-dependents (remove from frontier); **keep dispatching the rest of the
  frontier**; checkpoint completions. **Hard-wait for the human IFF the frontier is empty ∧ open human-required
  escalations remain.** (Engram auto-resolve before hard-wait = future, GB10 — do not wire.) A LOCKED-decision
  conflict still escalates to the human; never silently re-decided.

- [ ] **Step 3 — worker prompt:** add the version-up escalation predicate to the worker rule (L5): *"Escalate
  ONLY if completing your task's acceptance test requires writing a file you do not own; otherwise record
  out-of-scope discoveries via [[kata-defer]] and keep going."*

- [ ] **Step 4 — verify + commit.** Validator: zero errors for kata-orchestrate; `version: 0.1.0` unchanged; no
  remaining synchronous-wave / synchronous-escalation prose.
```
git add skills/coordinate/kata-orchestrate/SKILL.md
git commit -m "feat(A4): kata-orchestrate — rolling DAG-frontier dispatch + async structured escalation (L5/P1)"
```

---

## Task 4: `kata-grill` RUBRIC — Phase 0 invokes kata-graph (Sonnet)

**Files:** Modify `skills/plan/kata-grill/RUBRIC.md` (Phase 0 section). **depends:** T2.

- [ ] **Step 1 — add to Phase 0 "Ground before you ask":** *"When `target.kind == existing` (version-up),
  invoke [[kata-graph]] first to build/load the cached `kata.graph.json` and ingest its feature-seeded digest —
  interrogate the feature's design AGAINST the existing architecture, not greenfield. (kata-graph requires
  tree-sitter; readiness BLOCKs version-up without it, L1.)"*
- [ ] **Step 2 — verify + commit.** Validator green (wikilink `[[kata-graph]]` now resolves).
```
git add skills/plan/kata-grill/RUBRIC.md
git commit -m "feat(A4): kata-grill Phase 0 ingests kata-graph for existing-repo runs (L4)"
```

---

## Task 5: `kata-plan` RUBRIC — version-up footprint ownership (Opus)

**Files:** Modify `skills/plan/kata-plan/RUBRIC.md`. **depends:** T1, T2. **action (quote L4):**

- [ ] **Step 1 — add a "Version-up ownership" section:** *"For `target.kind == existing`: the ownership
  partition's universe is the **footprint = modified-files (from the frozen DESIGN) ∪ `[TUNABLE: graph.marginDepth=1]`-hop
  reverse-dependents** over `ref ∪ call` edges (the planner inverts `kata.graph.json`'s forward edge list).
  Files outside the footprint are **off-limits — owned by no task** (structural "don't break other aspects").
  Disjoint-ownership and the wave/DAG rules are unchanged. The regression contract is the full baseline suite +
  new tests green (gated by [[kata-evaluate]], no new evaluator)."*
- [ ] **Step 2 — verify + commit.** Validator green.
```
git add skills/plan/kata-plan/RUBRIC.md
git commit -m "feat(A4): kata-plan version-up footprint ownership = modified ∪ depth-1 reverse-deps (L4)"
```

---

## Task 6: `kata-readiness` tree-sitter gate + `kata-evaluate` regression note (Sonnet)

**Files:** Modify `skills/coordinate/kata-readiness/SKILL.md`, `skills/evaluate/kata-evaluate/SKILL.md`.

- [ ] **Step 1 — kata-readiness:** in Scope 2 add: *"For a version-up run (`target.kind == existing`),
  **BLOCK if tree-sitter is not available** — kata-graph's seeding + blast-radius need AST; there is no inert
  grep-mode fallback for version-up (L1.1)."*
- [ ] **Step 2 — kata-evaluate:** add a one-line version-up note: *"Version-up regression contract: the gate is
  the **baseline suite still green + new feature tests green** (rubric items #2/#6 applied to an existing repo's
  full suite). No new evaluator — the conformance floor is unchanged (D22)."*
- [ ] **Step 3 — verify + commit.** Validator green; both still `0.1.0`.
```
git add skills/coordinate/kata-readiness/SKILL.md skills/evaluate/kata-evaluate/SKILL.md
git commit -m "feat(A4): readiness tree-sitter gate for version-up + evaluate regression note (L1.1/L4)"
```

---

## Task 7: Register kata-graph — README + cost-ratings + TAXONOMY (Sonnet)

**Files:** Modify `.planning/SKILL-COST-RATINGS.md`, `README.md`, `docs/TAXONOMY.md`. **depends:** T2.

- [ ] **Step 1 — cost-ratings row:** add `| kata-graph | plan | M-L | none (single pass, no spawn/loop) | inline | med | 3 | tree-sitter parse + PageRank over a repo; the version-up ingestion engine. |`
- [ ] **Step 2 — regenerate README:** `cd tools && uv run python validate_skills.py --write`; then hand-author
  the kata-graph `Use` cell: `Token-budgeted structural map of an existing repo (version-up ingestion); kata.graph.json`.
- [ ] **Step 3 — TAXONOMY:** note `kata-graph` as an optional module (`kata/module/graph`), the version-up
  preset bundles it. Keep the validator's required terms intact.
- [ ] **Step 4 — verify + commit.** `uv run python validate_skills.py` → `25 skills checked — 0 error(s)`; pytest pass.
```
git add .planning/SKILL-COST-RATINGS.md README.md docs/TAXONOMY.md
git commit -m "chore(A4): register kata-graph (cost 3) — README + cost-ratings + TAXONOMY"
```

---

## Task 8: Promote decisions + status (Sonnet)

**Files:** Modify `.planning/DECISIONS.md` (append D47+ for A4-GB1…GB10 incl. HOLD resolutions, sourced from
`GRILL-LEDGER.md`), `.planning/STATE.md`, `.planning/ROADMAP.md` (mark A4 in progress → done at merge). **depends:** T2, T3.

- [ ] **Step 1** — append the A4 decisions to DECISIONS.md matching the existing format (find the last D-number;
  it should be D46; append D47+). **Step 2** — update STATE.md active-workstream + ROADMAP A4 line.
- [ ] **Step 3 — verify + commit.** Validator green.
```
git add .planning/DECISIONS.md .planning/STATE.md .planning/ROADMAP.md
git commit -m "docs(A4): promote A4 grill decisions -> D47+; STATE + ROADMAP"
```

---

## Task 9: Adversarial review (D15) (Opus)

**Files:** Create `.planning/specs/modes-A4-version-up/REVIEW.md`. **depends:** T1–T8.

- [ ] **Step 1 — fresh-context `kata-review`** over `git diff master...phase-2/modes-A4-version-up`, judged
  against `DESIGN.md` acceptance A1–A5. Specifically verify the A4 drift-magnets: (a) no `seedSymbols` in graph
  `meta`; (b) `import` edges file→file; (c) orchestrate has NO remaining synchronous wave-gate/escalation prose
  (P1 applied); (d) board one-line + payload separate; (e) version-up readiness BLOCKs without tree-sitter;
  (f) no `knowledgeGraph` config leaked; (g) versions all `0.1.0`.
- [ ] **Step 2 — record REVIEW.md (HOLD/SHIP) + fix loop** until SHIP. **Step 3 — final gate**
  (`pytest -q` + `validate_skills.py` → 25 skills 0 errors) + commit; then merge `--no-ff` to master, update STATE/ROADMAP.

---

## Plan frontmatter (for kata-orchestrate)
```yaml
ownership:
  T1: [protocol/graph.md, protocol/escalation.md, protocol/config.md, tools/validate_skills.py, tools/tests/test_validate_skills.py]
  T2: [skills/plan/kata-graph/SKILL.md]
  T3: [skills/coordinate/kata-orchestrate/SKILL.md]
  T4: [skills/plan/kata-grill/RUBRIC.md]
  T5: [skills/plan/kata-plan/RUBRIC.md]
  T6: [skills/coordinate/kata-readiness/SKILL.md, skills/evaluate/kata-evaluate/SKILL.md]
  T7: [README.md, .planning/SKILL-COST-RATINGS.md, docs/TAXONOMY.md]
  T8: [.planning/DECISIONS.md, .planning/STATE.md, .planning/ROADMAP.md]
  T9: [.planning/specs/modes-A4-version-up/REVIEW.md]
waves:
  wave1: [T1]
  wave2: [T2, T3, T6]      # disjoint; serialize commits (no worktrees)
  wave3: [T4, T5]          # depend on T2
  wave4: [T7, T8]          # depend on T2/T3
  wave5: [T9]
depends_on:
  T2: [T1]; T3: [T1]; T4: [T2]; T5: [T1, T2]; T6: [T1]
  T7: [T2]; T8: [T2, T3]; T9: [T1, T2, T3, T4, T5, T6, T7, T8]
models: { T1: sonnet, T2: opus, T3: opus, T4: sonnet, T5: opus, T6: sonnet, T7: sonnet, T8: sonnet, T9: opus }
```
**Disjoint-ownership check:** no file in two tasks ✔. **DAG:** acyclic, all reachable from T1 ✔.
