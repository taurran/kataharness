# A4 (version-up + kata-graph) — Grill Decision Ledger

> Running ledger for the A4 design grill (per `kata-grill` RUBRIC — checkpoint after every resolved branch).
> Grounded in `RESEARCH.md` (Graphify · aider repo-map · Understand-Anything). Feeds FREEZE (`kata-design-doc`).

## Design tenets (steering — apply to every branch)
- **No chimera (user, 2026-06-08).** The mashup of aider-model + Graphify + Understand-Anything must be tied
  together *well* — one coherent capability, never a half-baked Frankenstein of bolted-on features. **The
  mechanism:** ONE job per skill + ONE stable output **contract**; each backend (grep / tree-sitter /
  Graphify-MCP / UA) is a **swappable implementation behind that contract** — it either fully produces the
  contract or it is **not bound**. No backend leaks its own format upward. Degrade **explicitly and labeled**,
  never half-way. The contract is the glue; this is what prevents the chimera.

## Resolved branches

### A4-GB1 — tree-sitter is the hard floor; grep-only is a labeled "reduced" fallback
- **Chosen:** `kata-graph`'s default backend **requires tree-sitter** (symbol def/ref extraction). grep-only is a
  graceful-degradation path that emits a map explicitly labeled "reduced — no AST", not the default.
- **Rejected:** grep-default with tree-sitter as a pure optional accelerator (default would be too weak —
  can't rank by reference-importance, undercutting the token-optimization premise).
- **Key clarification:** spine #3 "agnostic" = **tool-agnostic** (Claude/Codex/Kiro), **not dependency-free.**
  tree-sitter is a universal parser, local, no API, `uv`-installable → a benign build-time dep in the D29
  pre-flight manifest. Requiring it does NOT violate the agnostic core.
- **Provenance:** aider, Graphify, AND Understand-Anything all stand on tree-sitter; it is the proven primitive.

### A4-GB2 — `kata.graph.json` output contract (the anti-chimera glue)
- **Chosen:** Nodes (`file` `{id,path,lang,hash}`, `symbol` `{id,path,name,symKind,signature,span,hash}`) ·
  Edges (`{src,dst,kind}`, kind ∈ def|ref|call|import, optional weight) · per-node `rank` (PageRank) + optional
  `community` · Meta `{backend, repoHash, generatedAt, seedSymbols}`. Serves all THREE consumers by
  construction: (a) digest ← top-`rank` symbols' signatures; (b) Graphify/MCP oracle ← nodes/edges/community map
  onto Graphify's own graph shape; (c) blast-radius ← reverse-reachability over ref/call edges from changed symbols.
- **Rejected:** test-coverage edges (test→covers→symbol). GB5-A3? no — **GB5 (A4 delta) set the regression floor
  at FULL-suite-green**, so coverage edges aren't needed for correctness; blast-radius is for planning/ownership
  scoping only. Keeping them out = anti-bloat.
- **Provenance:** user confirmed the contract + "keep test edges out."

### A4-GB3 — Obsidian KG interop = BOTH emit + ingest, over the shared contract
- **Chosen:** both directions, **emit-first**. Emit (contract → vault: node→note, edge→`[[wikilink]]`,
  community/kind→`#tag`) + Ingest (vault → contract: note→node, wikilink→edge, folds PortaVault in). Both are
  mappings over the same contract → no chimera; no heavy dep (markdown I/O).
- **Owner:** the Obsidian projection is **human-facing → kata-understand's** audience; `kata-graph` produces the
  contract, kata-understand owns the emit/ingest projection (respects the user's PortaVault scaffolding).
- **Provenance:** user — "both."

### A4-GB4 — Obsidian-compatible frontmatter for all ingest + pluggable profile (expansion room)
- **Chosen:** the emitter REUSES the harness's existing Obsidian-compatible frontmatter taxonomy (STANDARDS
  §1/§5 — YAML, list `tags`, no singular reserved props) — "this is where the frontmatter discipline pays off."
  Plus a **pluggable `frontmatterProfile`**: base (standard + body wikilinks) + optional
  `dataview`/`breadcrumbs`/`juggl`/`custom` that add the typed relation fields those plugins consume.
  **Leaves room** to extend the taxonomy/ingest per-plugin later (a reserved extension point, §1.2-style).
- **Critical detail (research §5d):** native graph view reads **body** `[[wikilinks]]`, NOT frontmatter links →
  edges MUST be emitted as body wikilinks (native graph works out of the box); frontmatter typed links are the
  plugin layer on top.
- **Provenance:** user — "Obsidian compatible frontmatter for all ingest … leave room for expansion for specific plugins."

### A4-GB5 — Ingest mechanism = folder emit to a configurable target (researched)
- **Chosen:** Obsidian "ingest" is **folder-based, no API.** Emit a folder of Obsidian-compatible markdown to a
  **configurable target**: `vault-direct` (a vault ingest subfolder the user provides) OR `project-folder`
  (`<project>/.kata/kg/`, user points Obsidian at it via open-as-vault / symlink). One mechanism, two target modes.
- **Provenance:** user — "write it to our vault by providing the obsidian kg ingest folder, or output to a project
  folder we point obsidian at. Figure out how through research, make that the mechanism." Research = §5d.

### A4-GB6 — Bootstrap asks "emit a knowledge graph?" + config/manifest plumbing
- **Chosen:** `kata-bootstrap` (A3, re-entrant) gains a KG question; writes
  `kata.config.knowledgeGraph = { emit: bool, ingest: bool, target: { mode: "vault-direct"|"project-folder",
  path }, frontmatterProfile }`. Plumb into kata.config schema (+ any manifest). No new dependency.
- **Provenance:** user — "bootstrap should ask if you want to output a knowledge graph … plumb this in configs/manifests."

## Open branches (next)
- **Sequencing (next):** does the Obsidian **emit** ship in A4 (thin projection over the contract — complete, not
  half-baked) with richer ingest + plugin profiles deferred to the kata-understand spec? Or all in kata-understand
  with A4 only plumbing the bootstrap question + config fields?
- Token-budget default + feature-seeded PageRank personalization (the token-optimization goal).
- Blast-radius: a `kata-graph` output, or a separate version-up planning step?
- Version-up wiring: how grill Phase 0 invokes kata-graph; the regression contract (baseline-green); file
  ownership over *existing* files.

## Working defaults (confirmed unless overruled)
- Output artifact = **Option C** (hybrid `kata.graph.json` + budgeted text digest). RESEARCH §4 D-A4-1.
- kata-graph stays ONE skill; pluggable backend; compose external skills, never reimplement/fork-splice.
