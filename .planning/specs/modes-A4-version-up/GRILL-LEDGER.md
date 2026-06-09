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

### A4-GB7 — Sequencing: A4 = version-up + kata-graph contract; Obsidian KG = its own next spec
- **Chosen:** clean split. **A4** ships version-up execution + `kata-graph` (the `kata.graph.json` contract is the
  durable substrate). The **whole Obsidian KG story** (emit + ingest + the bootstrap "emit a KG?" question +
  `knowledgeGraph` config + frontmatter profiles + the comprehension/onboarding layer) ships as **its own next
  spec under kata-understand** — shipped *whole*, no "configured-but-inert" seam.
- **Rejected:** a partial emit bolted into A4 (creates an ownership seam — "owned by kata-understand" but built
  before kata-understand exists = a chimera at the spec level). Anti-chimera honored at the spec boundary.
- **Provenance:** user — "go with your gut recommendation." Also: PortaVault must exist before emit can target it.

### A4-GB8 — Task-relevance: agnostic cached graph; seeding + blast-radius are use-time projections
- **Chosen:** `kata.graph.json` is **feature-agnostic and content-hash cached** (rebuilt incrementally on file
  change) — never invalidated per-feature. **Seeding** (the budgeted digest) and **blast-radius** are **use-time
  projections** over that stable graph:
  - **Digest** = feature-seeded PageRank (aider ×10-boost for symbols matching the feature description + named
    files) → the feature's neighborhood, not the whole repo. **Default budget ~3k tokens, configurable** (aider
    uses ~1k for interactive; a one-shot version-up plan wants more grounding).
  - **Blast-radius** = a reverse-reachability query over `ref`/`call` edges from the seed symbols, **computed in
    `kata-plan` (version-up), NOT emitted by kata-graph.** kata-graph stays a pure map-builder (provides graph +
    traversal); the *planner* decides scope. Anti-chimera (planning decisions stay in the planner).
- **Provenance:** user — "go with your rec" (agnostic cached graph · ~3k default · blast-radius in the planner).

### A4-GB9 — version-up wiring (reuses the spine with version-up-aware inputs)
- **Chosen:**
  - **Grill Phase 0** invokes `kata-graph` when `target.kind == existing` → injects the feature-seeded digest
    into grill + plan, so the design is resolved *against* the existing architecture.
  - **File-ownership scoped to the feature's footprint** (disjoint, as always); files outside scope are
    **off-limits — owned by no task** → "don't break other aspects" is structural, not a hope.
  - **Out-of-scope handling = escalate-not-silent-expand** — but with **overuse protections** (below).
  - **Regression contract (reuse, GB5):** orchestrate precond #2 records baseline via `target.baselineGate`
    (full existing suite green at fork); version-up `kata-evaluate` = baseline suite STILL green + new tests
    green, default-FAIL. No new evaluator.
- **Overuse protections (designed into A4 — answers the "this kills long-running" risk):**
  1. **Defer-vs-escalate split** (the main lever): non-blocking discoveries → `kata-defer` (loop keeps running);
     ONLY hard blockers ("can't complete my task without an unowned file") → escalate. Most cases defer.
  2. **Generous plan-time scoping:** with the graph digest in view, grill/plan over-include the blast-radius
     (forward footprint + reverse regression surface + margin) so "I need this file" is mostly pre-owned.
     Escalation frequency is a *plan-quality* metric, fixed at plan-time not runtime.
  3. **Escalation telemetry:** orchestrate's drift ledger counts escalations; crossing a threshold = "plan was
     under-scoped" → signal to re-grill, not normal operation.
- **Provenance:** user confirmed escalate-not-silent-expand "as long as there are protections against overuse."

### A4-GB10 — Engram-mediated escalation (FUTURE phase, harness-wide — captured, not wired)
- **Chosen (as future direction, NOT A4):** *every* human-in-the-loop escalation, anywhere in the harness,
  should eventually route through the engram / cognitive fingerprint: (a) **consult the engram first** — if the
  user's known patterns resolve it, auto-resolve + log; only novel decisions reach the human; (b) **feed every
  human resolution back into the engram** so the next identical escalation auto-resolves. Net: as the engram
  matures, human interrupts **asymptotically decrease** → the long-running promise strengthens over time.
- **Gated on:** PortaVault installed + cognitive-fingerprint synthesis built → grown from the `kata-engram`
  cognition skill (backlog/D9). Ties to [[cognitive-twin-architecture]], [[project-framework]] (kiban),
  [[project-kagami]] (engram sources).
- **Provenance:** user — "these escalations no matter where they are should take the engram into consideration
  … if the user has to enter a human-in-the-loop escalation it should feed into our engram … add it as a future
  phase after PortaVault + cognitive fingerprint synthesis."

## Grill COMPLETE (A4-GB1 … A4-GB10)
All branches resolved. A4 scope frozen for FREEZE (`kata-design-doc`): **kata-graph** (tree-sitter floor,
feature-agnostic cached `kata.graph.json` contract, feature-seeded ~3k-token digest, pluggable
grep/tree-sitter/Graphify-MCP backend) + **version-up wiring** (grill Phase 0 ingest, footprint-scoped ownership
with defer-first + escalate-rare protections, full-suite-green regression contract). Deferred to later specs:
the Obsidian KG story (own spec under kata-understand, GB7) and engram-mediated escalation (GB10).

## Working defaults (confirmed unless overruled)
- Output artifact = **Option C** (hybrid `kata.graph.json` + budgeted text digest). RESEARCH §4 D-A4-1.
- kata-graph stays ONE skill; pluggable backend; compose external skills, never reimplement/fork-splice.
