# protocol/graph.md — the `kata.graph.json` schema

Per-branch structural map produced by `kata-graph`, read by grill/plan. Machine state — JSON at the branch root `kata.graph.json`. Feature-agnostic + content-hash cached (incremental); ids are line-independent so unrelated edits don't churn the cache.

## Node Types

### `file` node

| Field | Value / Constraint | Notes |
|---|---|---|
| `id` | = `path` | REQUIRED |
| `kind` | `"file"` | REQUIRED |
| `path` | repo-relative | REQUIRED |
| `hash` | content hash | REQUIRED |
| `rank` | float PageRank | REQUIRED — computed on every floor build |
| `lang` | string | OPTIONAL |
| `community` | int | OPTIONAL — oracle-only |

### `symbol` node

| Field | Value / Constraint | Notes |
|---|---|---|
| `id` | = `path::name[~N]` where `~N` is a def-order ordinal for same-name collisions | REQUIRED |
| `kind` | `"symbol"` | REQUIRED |
| `path` | repo-relative | — |
| `name` | string | — |
| `symKind` | enum: `function\|class\|method\|interface\|type\|constant\|other` | REQUIRED |
| `span` | `[startLine, endLine]`, 1-indexed inclusive | REQUIRED |
| `hash` | content hash | — |
| `rank` | float PageRank | REQUIRED |
| `signature` | string | OPTIONAL |
| `community` | int | OPTIONAL |

## `edge`

| Field | Value / Constraint | Notes |
|---|---|---|
| `src` | id | source node |
| `dst` | id | destination node |
| `kind` | `def\|ref\|call\|import` | edge type |
| `weight` | float | REQUIRED, default `1.0` |

Targets: `def` file→symbol; `ref`/`call` symbol→symbol; `import` **file→file**. The tree-sitter floor MUST populate `def`+`ref` (and `import` best-effort); **`call` is oracle-only** (Graphify backend), may be absent.

## `meta`

`{ backend, repoHash, generatedAt }` — `backend ∈ tree-sitter|grep-reduced|graphify`. (Do NOT include `seedSymbols` — it is a use-time projection input, never cached.)

## Backends

| Backend | Description |
|---|---|
| `tree-sitter` floor | Populates `def`, `ref`, `import` edges. Full ranking. Primary build-time backend. |
| `grep-reduced` | Unranked, ordered by `path` then import-reference-count descending, **exploration-only**. Used when tree-sitter is unavailable. |
| `graphify` MCP oracle | Adds `call` edges and `community` assignments. Enables blast-radius queries. |

## Notes

`seedSymbols`, the budgeted digest, and blast-radius are USE-TIME projections computed per-run from the feature description + named files — never stored in the cached artifact. Digest budget + reverse-dependent margin depth + backend are tuned via `kata.config.graph`.
