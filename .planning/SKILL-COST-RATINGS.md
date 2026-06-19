# SKILL-COST-RATINGS — token-cost weights per skill (2026-06-07)

Produced by a fresh-context read-only analyzer to inform `docs/MODES-DESIGN.md`. Axes: **base footprint**
(body+resident resources when invoked), **amplification** (spawn ≫ loop ≫ none — the real driver),
**exec-context** (fresh-context spend protects the loop budget → cheaper-to-loop than inline), **variance**
(the tiering trigger), → **weight 1–5**. To be baked into skill frontmatter (`cost-weight`) + README index in Spec A.

| skill | cat | base | amplification | exec | variance | weight | note |
|---|---|---|---|---|---|---|---|
| kata-orchestrate | coordinate | M | **spawn** (N workers + evaluate + review) | inline | high | **5** | the cost multiplier of the whole run; ≈ loop + Σ(worker windows) + evaluators. Throttle via plan shape + model pinning, NOT tiers. |
| kata-bootstrap | coordinate | M | none (guided single pass; invokes readiness) | inline | low | 2 | pre-loop configurator; writes kata.config. |
| kata-readiness | coordinate | S | none | inline | low | 1 | read-only health/target check; bootstrap-invoked. |
| kata-grill | plan | **L (largest)** | loop (multi-round) + review spawn | inline | **high** | **4** | biggest body + highest in-loop variance; THE tiering candidate; also the differentiator (L8/L10). |
| kata-diagnose | execute | M | loop (6-phase) | worker | high | 3 | often zero (only on unexpected failure); hard bug spins cycles. light/full tier candidate (secondary). |
| kata-tdd | execute | M | loop (red→green/behavior) | worker | med | 3 | per-worker, multiplied across N workers; good fresh-context spend. depth via mode-hint, not file-tier. |
| kata-plan | plan | M | none (single pass) | inline | med | 3 | one pass but heavy resident output; thoroughness discretionary → **separate-file tier candidate**. |
| kata-design-doc | plan | M | none | inline | med | 2 | bounded compile; depth via mode-hint (not file-tier). |
| kata-evaluate | evaluate | S | none | fresh-context | med | 2 | **NEVER tier — the conformance floor / consistency invariant.** |
| kata-review | evaluate | S | none (open-ended hunt) | fresh-context | **high** | 2 | depth is discretionary → **tier essential/standard/advanced** (confirmed). |
| kata-board | coordinate | S | none | inline | low | 2 | cumulative reads per cycle; per-invoke trivial; points to protocol (efficient). |
| kata-handoff | handoff | S | none | inline | low | 1 | one durable write. |
| kata-defer | handoff | S | none (append-as-you-go) | inline | low | 1 | DEFERRED.md parking (D42) + ASSUMPTIONS.md grill-skip floor log (D71); optional module `kata/module/defer`. |
| kata-worktree | coordinate | S | none | inline | low | 1 | mostly a git recipe. |
| kata-selfhandoff | handoff | S | none (delegates) | inline | low | 1 | trigger policy only. |
| kata-context | plan | S | none | inline | low | 1 | incremental glossary. |
| kata-improve | meta | S | none | inline (out-of-loop) | med | 1 | cross-run, doesn't tax a one-shot run. |
| kata-write-skill | meta | S | none | inline (out-of-loop) | low | 1 | authoring; points to STANDARDS. |
| kata-graph | plan | M-L | none (single pass, no spawn/loop) | inline | med | 3 | tree-sitter parse + PageRank over a repo; the version-up ingestion engine. |

**Tier (separate files):** kata-grill, kata-review, kata-plan, kata-diagnose(light/full). **Mode-hint depth:**
kata-design-doc, kata-tdd. **Never tier:** kata-evaluate (floor) + all weight-1 + kata-orchestrate.

**Efficiency flags (cheap fixes, backlog/Spec-A):** (1) kata-grill body heaviest — move L8-narrative +
convergence checklist to `resources/` (~30% lighter, pairs with tiering it). (2) kata-orchestrate worker-prompt
template → `protocol/`/`resources/` pointer. (3) kata-tdd "Supporting depth" para → one-line pointer.
Suite is otherwise disciplined (progressive disclosure + pointers; no restated-canon violations).

---

## Tier weights (A2)

The four tiered families each carry per-tier `cost-weight` values. The **family base weight** equals the
**Standard** (or full, for diagnose) tier — i.e., the default dispatch tier (D25).

| family | essential | standard | advanced | full |
|---|---|---|---|---|
| kata-grill | 3 | **4** | 5 | — |
| kata-review | 1 | **2** | 3 | — |
| kata-plan | 2 | **3** | 4 | — |
| kata-diagnose (light/full) | — | — | — | light **2** / full **3** |

For `kata-diagnose`, the family base weight = its **full** tier (3), matching the prior single-skill weight.
These weights are baked into each tier's `cost-weight` frontmatter field (authority: this file).
