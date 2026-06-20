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

# kata-graph — token-budgeted structural map of an existing codebase

The cheap, in-loop map that lets the loop work a large repo without burning tokens. The cached
`kata.graph.json` contract is the anti-chimera glue: one shared structural ground-truth that the grill, the
plan, and every downstream agent read instead of re-deriving (and disagreeing on) the architecture.

## Backends
Selected via `kata.config.graph.backend`.

- **`tree-sitter` floor** — the default; populates `def` + `ref` (and `import` best-effort) edges with full
  ranking. **Required for version-up** — the only backend trusted to ground a frozen plan against real
  structure.
- **`grep-reduced`** — unranked, **exploration-only**. Used when tree-sitter is unavailable. **Never
  version-up** — no ranking means no trustworthy digest.
- **`graphify`** — optional MCP oracle backend (the Graphify project). Adds `call` edges plus `community`
  assignments, enabling blast-radius queries the floor cannot answer.

## Output
The cached `kata.graph.json` (schema: `protocol/graph.md` — read it there, it is the single source of truth).
The artifact is **feature-agnostic**, content-hash **incremental**, and its ids are **line-independent** so
unrelated edits don't churn the cache.

## Ranking & digest
Nodes carry a personalized-PageRank `rank`. The personalization vector is **seeded at use-time, never cached**:
tokenize the feature description → case-insensitive match against each symbol `name` → ×10 boost on hits, plus
any user-named files. The digest then walks top-rank signatures, accumulating until the
`kata.config.graph.budget` (default 3000) token estimate (chars ÷ 4) is reached. This is **selection, not
truncation** — the highest-signal symbols for *this* feature, not the first N bytes of the map.

## Slot
Invoked by [[kata-grill]] at Phase 0 when `target.kind == existing`. The budgeted digest grounds the grill and
the resulting plan against the codebase as it actually is, not as imagined. **Blast-radius**
(reverse-reachability over `ref` ∪ `call`) is computed by the **planner**, not here — kata-graph stays a pure
map-builder; consumers project from the map.

**Consumers project, kata-graph stays pure.** [[kata-orient]] (AO) projects **lateral adjacency pointers** — the
modules a task's owned files collaborate with — from the `ref` ∪ `call` edges, the same way the planner projects
blast-radius. kata-graph emits no orientation-specific output: it remains the single feature-agnostic map; each
consumer derives its own view. No `kata.graph.json` (greenfield / no tree-sitter) ⇒ consumers degrade (AO uses
vertical rollup only).

## Caching
Content-hash per file: only files whose hash changed are re-parsed and rebuilt; everything else is reused. The
graph persists across runs, so a version-up loop pays the full build cost once and incremental cost thereafter.
