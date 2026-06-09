---
date: 2026-06-08
spec: modes-A4-version-up
topic: kata-graph design research (D41 / GB8 — evaluate OSS, bake stripped-down minimal steps)
status: research complete — feeds the kata-graph grill
tags: [research, A4, kata-graph, graphify, repo-map, token-optimization]
---

# kata-graph — OSS research brief (Graphify + aider repo-map)

Grounding for the `kata-graph` grill (per the RUBRIC Phase 0 + D41). Two reference systems studied:
**Graphify** (`safishamsi/graphify`, the user's nod) and **aider's repo-map** (the proven in-loop token
optimizer). Conclusion up front: they are **two different archetypes**, and our backlog already split along
exactly that seam — `kata-graph` (cheap, in-loop, token-saving) wants the *aider* model; `kata-understand`
(rich comprehension) wants the *Graphify* model. Graphify the tool plugs into **both** as an optional backend —
we should **bind/ingest it, not reimplement it**.

## 1. Graphify — QRD (what it actually is)
A **knowledge-graph builder** shipped as an agent skill (`/graphify .`) for Claude Code/Cursor/Gemini/etc. MIT.
- **Pipeline:** detect (free) → extract (**tree-sitter AST for code = local, free, 31 langs**; PDFs/images/docs
  → **LLM semantic extraction = costs tokens**; audio/video → local whisper) → assemble NetworkX graph →
  Leiden community detection → analyze (centrality/anomaly) → render.
- **Output:** `graphify-out/` with `graph.json` (full queryable graph), `graph.html` (interactive viz), and
  `GRAPH_REPORT.md` ("god nodes", surprising cross-module connections, the *why* from docstrings/comments).
- **Consumption:** terminal (`query`/`path`/`explain`), an **MCP server** (`query_graph`, `get_node`,
  `get_neighbors`, `shortest_path`, `get_pr_impact`, `triage_prs`), or HTTP for teams.
- **Execution model:** **out-of-loop, cached.** SHA256 incremental cache (only changed files re-extract);
  ~90s first build on a 50K-line monorepo; a file-watcher / git-hook can auto-rebuild.
- **Strengths:** multimodal, semantic "why", **`get_pr_impact` = change blast-radius** (directly useful to
  version-up's regression surface), visualization, the oracle MCP.

### The token-savings reality (the part to get right)
Graphify markets **71.5× fewer tokens/query** — but that figure is a *large mixed corpus* (code + papers +
images) vs reading every raw file. An **independent real-world test** (a browser-use coding session, 10
questions) measured **113k tokens with Graphify vs 120k without ≈ 7–8% savings, not 71×**. So for
**pure-code, in-loop** use (our version-up case), Graphify's value-add *over plain tree-sitter+PageRank* is
**modest** — its real differentiation is semantic comprehension + blast-radius + multimodal, not raw code
token-compression. This is the single most important finding for scoping `kata-graph`.

## 2. aider repo-map — the in-loop token optimizer (the better anchor for kata-graph's stated goal)
The gold standard for *token-budgeted* repo maps inside an agent loop — "the feature that makes aider work on
large codebases without burning a fortune; the feature most users never see."
- **Tree-sitter** parses each file; language `.scm` tag-queries extract **def** (functions/classes/methods) and
  **ref** (usages) tags.
- Build a graph (file = node, edges = ref→def dependencies); run **personalized PageRank** to rank what matters.
  Edge-weight heuristics: **×10** for identifiers in the current task/message, **×10** for "real-looking" names
  (snake/camel/kebab, 8+ chars), **×50** for refs from files already in scope, **×0.1** for private (`_`) or
  ubiquitous (defined in >5 files) names.
- **Select top-ranked defs until a token budget is filled** (`--map-tokens`, default ~1k; expands ×8 when no
  files are in scope). Render as **scope-aware elided code** (signatures + key lines, bodies elided).
- **Deterministic, no API calls, regenerated cheaply, never an always-on context dump.**

## 3. The key insight — two archetypes, and Graphify plugs into both
| | **kata-graph** (A4) | **kata-understand** (backlog) |
|---|---|---|
| Goal | cheap, in-loop, **token-saving** ingestion for version-up | rich **comprehension** of a built codebase for the human |
| Best model | **aider repo-map** (tree-sitter tags + PageRank + budget) | **Graphify** (semantic graph, god-nodes, the *why*, viz) |
| Cost profile | deterministic, ~free, in-loop | heavier, out-of-loop, cached; some LLM extraction |
| Graphify's role | **optional accelerated backend / oracle** (its MCP `get_neighbors`/`shortest_path`/`get_pr_impact`) when present + repo large | **the inspiration / backend itself** |

**Graphify is a better fit for `kata-understand` than for `kata-graph`.** For `kata-graph`'s token-optimization
job, adopt the aider model as the agnostic default; bind Graphify as the heavy/semantic oracle.

## 4. Decisions for the grill (recommendations)

### D-A4-1 — Output artifact (the menu to pick from)
- **Option A — aider-style budgeted text digest.** Top-PageRank symbols rendered as elided signatures, capped
  at N tokens. *Pro:* exactly the in-context token-saver; what grill/plan read directly. *Con:* ephemeral, not
  separately queryable.
- **Option B — Graphify-style `graph.json` + report.** Rich persistent graph + GRAPH_REPORT. *Pro:* queryable,
  multimodal, comprehension-grade. *Con:* heavier, build costs tokens, overkill for in-loop token-saving.
- **Option C (RECOMMENDED) — hybrid: a compact `kata.graph.json` (durable, cacheable machine substrate) +
  a budgeted text digest rendered from it on demand.** The JSON is the queryable artifact (and the hand-off
  point to an optional Graphify/MCP oracle); the digest is what enters context. Union of A's budgeting and B's
  persistence, scaled to our need. Incremental via content-hash cache (Graphify's SHA256 model).

### D-A4-2 — Ranking + token budget (the real goal: optimize tokens)
Adopt **aider's model**: tree-sitter def/ref → reference graph → **personalized PageRank** → fill to a token
budget. **Version-up personalization:** seed/boost the PageRank around the **feature's blast radius** (the
files/symbols the requested change touches) so the map is *task-relevant*, not whole-repo — this is where
Graphify's `get_pr_impact` notion is borrowed as the regression-surface signal.

### D-A4-3 — Slot + lifecycle
`kata-graph` runs as a **pre-processing step invoked by grill Phase 0 when `target.kind == existing`** (and
optionally any large-repo run). Produces `kata.graph.json` (cached, content-hash incremental) + injects the
budgeted digest into grill/plan context. The accelerated path (Graphify MCP) is an **out-of-context oracle**
queried with a bounded budget — **never an always-on hook** (matches the backlog usage discipline).

### D-A4-4 — One skill or many? (the user's "this looks bigger" instinct)
**Determination: `kata-graph` stays ONE skill** — but the "bigness" is real and absorbed three ways:
(1) the already-decided **kata-graph (ingest/token-save) vs kata-understand (comprehend)** split;
(2) a **pluggable backend** inside kata-graph (agnostic grep default → tree-sitter → Graphify-MCP oracle),
adapter-bound per spine #3, not forked skills; (3) **build vs query** kept simple — kata-graph *builds* the
map; consumption is a plain read of the artifact (or an MCP oracle query in accelerated mode), not a second
kata-skill. So: **kata-graph (1) + kata-understand (1, later) + Graphify-as-backend (0 new skills — bound).**

### D-A4-5 — Build vs bind vs ingest Graphify
**Do NOT reimplement Graphify.** It's MIT and *ships as an agent skill with an MCP server.* Two clean hooks we
already built: (a) bind it as kata-graph's **optional accelerated backend / oracle** (adapter, pre-staged via
D29); (b) **ingest it via `kata-bootstrap`'s external-skill rung (D24c #4)** — declare its slot
(needs/produces/slot). "Custom version based on their repo" = **adopt their tree-sitter tag-query technique**
(shared with aider) for our agnostic default + **bind their MCP** for the heavy/semantic path. Attribute both
Graphify (MIT) and aider in `source:` (spine #12).

## 5. Open for the grill (when the user is back)
- Confirm **Option C** (hybrid artifact) vs A or B.
- The **agnostic default floor**: do we ship a *grep-only* heuristic map when tree-sitter isn't present, or make
  tree-sitter the hard floor (it's `uv`-installable, no API)? (Pins the D29 dependency manifest.)
- Token-budget default (aider uses ~1k; version-up ingestion may want more) + how the feature description seeds
  the PageRank personalization.
- Where `kata.graph.json` lives + its schema (nodes: file/symbol; edges: def/ref/import; props: path, sig, hash).
- Whether `get_pr_impact`-style blast-radius is a kata-graph output or a separate version-up planning step.

## 5b. kata-understand base — Understand-Anything vs Graphify (bake-off)
`kata-understand` (backlog) job = explain a **freshly-built, kata-created** codebase to its **owner**.
- **Understand-Anything** (`Lum1104/Understand-Anything`, MIT, ~46k★): tree-sitter + LLM → interactive KG,
  shipped as a Claude Code/Cursor/etc. plugin. Philosophy *"graphs that teach > graphs that impress."*
  Comprehension/onboarding-first: `/understand-onboard`, `/understand-chat`, `/understand-explain`,
  `/understand-domain` (code→business processes/flows). Lighter, education-shaped.
- **Graphify**: heavier, query/oracle-first; multimodal + infra/SQL/Terraform + `get_pr_impact` + Leiden.
- **Determination:** `kata-understand` → **base on Understand-Anything** (purpose-built for teach-the-human
  comprehension); Graphify is a *secondary* source (multimodal/infra) and the **oracle backend for `kata-graph`**
  (blast-radius via `get_pr_impact`). UA and Graphify are near-twins (same primitives), so "merge" = **compose
  pluggable skills** (pick base by job-fit, bind the other's standout capability via its skill/MCP), **never
  fork-and-splice internals.** Attribute all bases in `source:` (spine #12).

## 5c. Naming principle (settled) — name by JOB, not by vendor
A skill's name describes its job; the OSS we borrow from lives in `source:` frontmatter, never the name.
`kata-graph` = "build a structural graph" (true whether powered by aider's PageRank or Graphify's AST);
`kata-understand` = "comprehend" (true whether based on Understand-Anything or Graphify). No `kata-pagerank`.
Distinct one-liner if needed: **kata-graph optimizes tokens for the agent; kata-understand teaches the codebase
to the human.** (Candidate for `docs/TAXONOMY.md` if we want it formalized.)

## 6. Sources
- Graphify repo — https://github.com/safishamsi/graphify
- Graphify site — https://graphify.net/
- Graphify architecture (DeepWiki) — https://deepwiki.com/safishamsi/graphify
- Independent token-savings critique — https://medium.com/@manavghosh/graphify-claude-code-how-i-cut-token-usage-by-71x-on-a-50k-line-codebase-74868ac67fd1
- aider repo-map (how it works) — https://aider.chat/2023/10/22/repomap.html
- aider repo-map docs — https://aider.chat/docs/repomap.html
- aider repository-understanding (DeepWiki) — https://deepwiki.com/Aider-AI/aider/4.1-repository-mapping-system
- Understand-Anything repo — https://github.com/Lum1104/Understand-Anything
- Understand-Anything overview — https://dev.to/arshtechpro/understand-anything-turn-any-codebase-into-an-interactive-knowledge-graph-37ed
