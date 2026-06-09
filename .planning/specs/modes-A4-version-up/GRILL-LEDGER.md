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

## Convergence HOLD #1 — resolutions (fresh-context gate, 2026-06-08)
The fresh-context convergence check (D15) returned **HOLD**: direction converged, but the `kata.graph.json`
contract + use-time projections were specified at intent-level, not byte/predicate-level (and `seedSymbols`
placement contradicted the cache). Resolutions (grounded in aider's actual implementation):

### A4-GB2.1 — node/edge id grammar + span
- **file id = `path`** (repo-relative). **symbol id = `path::name`**, with `~N` ordinal suffix (def order) for
  same-name collisions within a file. **Line/span are node PROPERTIES, never in the id** → ids stay stable
  across unrelated edits (incremental-cache-safe; cross-file edges don't break when a callee moves lines).
- **span = `[startLine, endLine]`, 1-indexed, inclusive.** (No columns — sufficient for digest elision + blast-radius.)

### A4-GB2.2 — edge-kind obligations per backend tier
- **tree-sitter floor MUST populate `def` + `ref`** (+ `import` best-effort) — all tag-queries natively yield.
  **`call` is oracle-only** (Graphify-MCP backend), MAY be absent in floor/grep maps.
- **Blast-radius traverses `ref ∪ call`** → well-defined on the floor regardless of backend.
- **`weight` always present, default `1.0`** (deterministic; not backend-conditional → reproducible, D18).

### A4-GB2.3 — `seedSymbols` is NOT cached (fixes the GB2↔GB8 contradiction)
- The cached `kata.graph.json` is **feature-agnostic** (GB8). `seedSymbols` is a **per-run projection input**
  computed from the feature description + user-named files, passed to the digest/blast-radius step — **never
  stored in the cached artifact.** Remove it from `meta`.

### A4-GB8.1 — PageRank seed match rule (aider's, literal)
- Tokenize the feature description into identifier-like tokens; match **case-insensitively against symbol
  `name`**; matches (and symbols in user-named files) get the **×10** personalization boost. Reproducible.

### A4-GB8.2 — budget units + enforcement
- Agnostic token estimate = **chars/4 heuristic** (no host-specific tokenizer). Enforced by **selection** (add
  top-ranked signatures until the estimate reaches budget) — NOT post-truncation. **Default 3k, configurable.**
  No ×8 no-scope expansion (version-up always has a feature in scope).
- **Planner derives reverse-reachability by inverting the forward edge list** — no reverse-index in the contract.

### A4-GB9.1 — "footprint" defined; ownership margin
- **footprint = modified-files (from the frozen DESIGN) ∪ depth-1 reverse-dependents** (over `ref ∪ call`).
  Depth-1 default, **configurable**; NOT transitive closure (would own half the repo, break disjoint partition).
  Pre-owning depth-1 reverse-dependents puts the common "update a caller of what I changed" case **in-lane** →
  fewer escalations (serves the GB9 overuse-protection goal directly).

### A4-GB9.2 — decidable escalate predicate
- **Escalate IFF completing the owned task's acceptance test requires a write to an unowned file. Everything
  else defers.** Baseline regressions from unowned files are caught by the **full-suite gate** and handled as a
  **deliberate re-scope at gate-time** (orchestrate), never a worker's silent expansion.

### A4-GB1.1 — version-up hard-requires tree-sitter (no inert grep seam)
- **version-up BLOCKs at readiness if tree-sitter is absent.** grep-reduced maps (unranked / path-frequency
  ordered) are for **lightweight greenfield/exploration only** — version-up's seeding + blast-radius need AST,
  so they are never "configured but inert." Closes the chimera seam the gate flagged.

### A4-GB9.3 — Escalation is ASYNC / non-blocking (drain the DAG; hard-wait only when the frontier is blocked)
- **Ratified:** GB1.1 (version-up requires tree-sitter), GB9.1 (depth-1 reverse-dependent ownership margin),
  GB9.2 (escalate-iff-acceptance-test-needs-unowned-write) all confirmed by the user.
- **Context:** most version-up escalations resolve at the **orchestrator** (re-scope/re-partition + re-dispatch)
  and never reach a human; only a **LOCKED-decision conflict** reaches a human (existing spine). The async model
  governs that human-facing subset.
- **Chosen (harness-wide; built into `kata-orchestrate`'s escalation protocol in A4):** an escalation does NOT
  halt the run. The orchestrator (1) **raises/queues** it (board + notify), (2) **parks only** the escalating
  task + its DAG-dependents, (3) **keeps dispatching every independent ready task** (drains the wave/DAG), (4)
  **checkpoints** completed work as it goes (parked run loses nothing), (5) **classifies criticality** (frontier
  vs single branch), (6) **hard-waits for the human ONLY when the whole DAG frontier is blocked** on open
  escalations. Maximize work-before-wait; never idle while independent work remains.
- **Engram layer (GB10, future):** before any hard-wait, consult the engram to auto-resolve → human interrupts
  asymptotically vanish as the fingerprint matures.
- **Touches:** a prose enhancement to `kata-orchestrate`'s Escalation section (A4; held at 0.1.0). Buildable now
  without the engram; engram-assist is the deferred layer on top.
- **Provenance:** user — "when we escalate make sure we aren't interrupting unfinished processes … pop up the
  escalation, and if the user isn't there, determine if it's truly critical, continue to execute until necessary
  … or pull in the engram."

## Convergence HOLD #2 — resolutions (2026-06-08)
Re-check closed 4/5 prior blockers; 2 remained. Resolved:

### A4-GB2.4 — authoritative node/edge field tables (closes Blocker A)
- **`file` node:** `id`(=path, REQ) · `kind:"file"`(REQ) · `path`(REQ) · `lang`(OPT) · `hash`(REQ) ·
  `rank`(float, REQ — floor computes PageRank every build) · `community`(int, OPT — oracle-only).
- **`symbol` node:** `id`(=`path::name[~N]`, REQ) · `kind:"symbol"`(REQ) · `path`(REQ) · `name`(REQ) ·
  `symKind`(REQ, enum **{function, class, method, interface, type, constant, other}**) · `signature`(OPT) ·
  `span`(`[startLine,endLine]` 1-indexed incl., REQ) · `hash`(REQ) · `rank`(REQ) · `community`(OPT).
- **edge:** `src`(REQ) · `dst`(REQ) · `kind`(REQ, {def,ref,call,import}) · `weight`(REQ, default 1.0). Targets:
  `def` file→symbol · `ref`/`call` symbol→symbol (`call` oracle-only) · **`import` file→file** (symbol-level
  import = oracle-only).
- **`meta`:** `{backend, repoHash, generatedAt}` — **NO `seedSymbols`** (GB2.3; the original GB2 `meta` line is
  superseded — design-doc must restate without it).

### A4-GB9.3-rev — rolling DAG-frontier dispatch + structured escalation (closes Blocker B)
- **Generalize `kata-orchestrate` dispatch from wave-gated → rolling DAG-frontier:** a task is dispatchable iff
  (all `depends_on` integrated) ∧ (owned files disjoint from all in-flight tasks), regardless of original wave.
  **Waves become a derived view, not a hard gate.** This SUPERSEDES the current synchronous per-wave loop +
  the synchronous escalation paragraph in `kata-orchestrate/SKILL.md` (design-doc states the supersession).
- **Async escalation falls out:** park the escalating task + its DAG-dependents (remove from frontier); keep
  dispatching the frontier; checkpoint each completion **in integration order** (linear history); **hard-wait
  for the human IFF the frontier is empty ∧ open escalations remain.** "Criticality" knob DROPPED — frontier-
  blocked IS the criticality test (decidable; the user's "truly critical" operationalized).
- **High-quality escalation payload (structured, not freeform):** a human-facing escalation is a board entry
  `{ blockedTask, decisionNeeded, optionsConsidered[], agentRecommendation+rationale, lockedDecisionInTension?,
  costOfWaiting vs costOfProceeding }`. **Classified** orchestrator-resolvable (re-scope, auto — never reaches
  human) vs human-required (LOCKED conflict — surfaces). Structured = fast human decision + the forward-compatible
  **engram seam** (GB10 learns from it) + resumable.
- **Scope guard:** the orchestrate changes (frontier-dispatch + async escalation + payload) are real surface —
  the PLAN scopes them as their own bounded task so A4 doesn't balloon.

### Minor polish — design-doc nails inline (non-blocking)
1. Restate `meta` without `seedSymbols`. 2. grep-reduced map ordering = deterministic (by `path`, then
   import-reference-count desc). 3. `kata-graph` `source:` names aider (MIT) + Graphify (MIT) per spine #12.
4. Cross-frontier checkpoints integrate in completion order (linear integration-branch history).

## Coherence tenet — contract-mediated web (no skill calls another's internals)
Every cross-skill tie crosses a **named artifact with a schema**, one producer each: `kata.graph.json`
(kata-graph→grill/kata-plan), `kata.config` (bootstrap→orchestrate), frozen DESIGN+PLAN (design-doc/plan→
orchestrate), board+escalation-payload (workers/orchestrator→async coord; later→engram), `DEFERRED.md`
(kata-defer), `target.baselineGate` (bootstrap→evaluate). Deferred items (Obsidian, engram, kata-understand)
are clean projections over already-existing contracts, never load-bearing holes. This is the anti-chimera
principle (GB2) scaled system-wide — what keeps the interdependency a web, not slop.

## Convergence HOLD #3 — resolution (final; coherence audit PASSED)
The final gate PASSED coherence (no drift/orphans/contradictions/slop; A4 stays ONE spec, no split) but found
ONE true blocker:

### A4-GB9.4 — escalation payload is its OWN contract (closes B1; un-fuses board↔payload)
- **Problem:** `protocol/board.md` locks the board to a single one-line message (append-only, L3); the 6-field
  structured escalation payload can't live there. "board+escalation-payload" was wrongly fused into one contract.
- **Chosen:** TWO contracts. **Board stays one-line** — the worker appends `ESCALATE | <task-id> | <summary>`
  (a pointer). **Structured payload = separate artifact** `.kata/escalations/<task-id>.json` (machine state →
  JSON, STANDARDS §5), schema in a NEW **`protocol/escalation.md`**:
  `{ taskId, kind: "orchestrator-resolvable"|"human-required", decisionNeeded, optionsConsidered[],
  agentRecommendation, rationale, lockedDecisionInTension?, costOfWaiting, costOfProceeding, status:
  "open"|"resolved", resolution? }`. **Producer = the escalating worker;** orchestrator reads/classifies/routes;
  resolver writes `status→resolved`; engram (GB10) learns from resolved payloads.
- **Coherence tenet updated:** board (one-line coord, `protocol/board.md`) and escalation-payload
  (`.kata/escalations/*.json`, `protocol/escalation.md`) are TWO contracts, one producer each — improves the web.

### Execution obligations (gate P1/P2 — honored in design-doc/PLAN, not design ambiguities)
- **P1:** the A4 PLAN includes the concrete edit to `skills/coordinate/kata-orchestrate/SKILL.md` (wave-loop →
  rolling DAG-frontier; synchronous escalation → async park/drain/hard-wait) — a bounded task, held at 0.1.0.
- **P2:** the design-doc restates `meta {backend, repoHash, generatedAt}` authoritatively (no `seedSymbols`);
  the stale GB2 `meta` line is not a citable source.

## Coherence audit — PASSED (the user's "no slop / tie features together" check)
Fresh-context gate confirmed: contract-mediated web holds (every cross-skill tie = a named artifact, one
producer); no orphans; no contradictions with A3 (D34–D46)/config/STANDARDS; the three scrutinized additions
(depth-1 margin, frontier-dispatch, structured payload) are load-bearing not gold-plating; A4 stays ONE spec.

## Grill CONVERGED + COHERENT — FREEZE-READY (A4-GB1…GB10 + HOLD#1/#2/#3 resolutions)
All branches resolved. A4 scope frozen for FREEZE (`kata-design-doc`): **kata-graph** (tree-sitter floor,
feature-agnostic cached `kata.graph.json` contract, feature-seeded ~3k-token digest, pluggable
grep/tree-sitter/Graphify-MCP backend) + **version-up wiring** (grill Phase 0 ingest, footprint-scoped ownership
with defer-first + escalate-rare protections, full-suite-green regression contract). Deferred to later specs:
the Obsidian KG story (own spec under kata-understand, GB7) and engram-mediated escalation (GB10).

## Working defaults (confirmed unless overruled)
- Output artifact = **Option C** (hybrid `kata.graph.json` + budgeted text digest). RESEARCH §4 D-A4-1.
- kata-graph stays ONE skill; pluggable backend; compose external skills, never reimplement/fork-splice.
