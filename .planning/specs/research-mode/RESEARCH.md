---
name: research-mode-research
date: 2026-06-09
status: PRE-GRILL EXPLORATORY (path-forward brief, not a frozen design — no DESIGN/PLAN yet)
spec: research-mode (a major post-v0.1 capability; design + plan later in the dev cycle)
tags: [research, modes, run-shape, pre-grill, exploratory, prior-art, "kata/module/research"]
related: ["[[kata-orchestrate]]", "[[kata-graph]]", "[[kata-review]]", "[[kata-evaluate]]", "[[kata-bootstrap]]"]
---

# RESEARCH — A Research-Loop Mode for KataHarness

> **Status: pre-grill exploratory brief.** Produced in a focused deep-research window (2026-06-09) to
> *find a path forward*, per the user's ask, NOT to freeze a design. The point is to prove the approach is
> coherent (reuses the spine, no chimera), name the new components, and sequence it in the dev cycle. The
> real GRILL → FREEZE → PLAN comes later. Read with `docs/MODES-DESIGN.md`, `protocol/graph.md`,
> `skills/coordinate/kata-orchestrate/SKILL.md`, and the Obsidian-KG / `kata-understand` spec (next build).

---

## 1. The ask (distilled)

A **research mode** for KataHarness that reuses the harness's guts — the same loop model as
dev / version-up / bake-off — but swaps the *work unit* and the *agent roster*:

- A `projects/Research/` root; under it, **one folder per research project** you start.
- The loop spins up **multiple kinds of research agents in a recursive loop**: **research** agents,
  **adversarial-validation** agents, **evaluation** agents.
- Research agents **represent different disciplines**, and each is set to **targeted** or **open-ended
  exploratory** research within a defined discipline / skill / target.
- **Lean on existing research libraries** where it pays.
- Reference **Karpathy's AutoResearch** and the surrounding ecosystem to shore up the design.
- This is a **large, later-cycle feature** — the deliverable now is a *solid approach*, not a build.

---

## 2. Prior art surveyed (and what to borrow from each)

| System | What it is | The transferable idea | What to borrow → kata primitive |
|---|---|---|---|
| **Karpathy AutoResearch** (Mar 2026; `program.md` + `train.py`) | English methodology doc drives an indefinite generate→experiment→measure→commit/rollback loop on one file against one metric, fixed time budget, "never stop / don't ask the human." | The **English methodology = the program**; a **git ratchet** (commit-if-better / reset-if-worse) as the integrity gate; **scope boundaries + protected files**; a **fixed per-experiment budget**. | `program.md` → our **frozen DESIGN+PLAN**; ratchet → **version-up no-regression gate**; protected files → **file-ownership + LOCKED decisions**; time budget → **experiment/recursion budget guard**. |
| **Sakana AI Scientist** (Nature, 2026) | Full pipeline: hypothesis → literature-dedup check → design+run experiments (parallel agentic tree search) → analyze → write manuscript → **multi-round structured self-peer-review** (ratings on novelty/soundness/significance + accept/reject). | The **staged research pipeline** and a **structured reviewer rubric** with numeric dimensions + a binary gate. | pipeline → our **grill→freeze→execute→evaluate** specialized for research; reviewer rubric → **`kata-review` specialized to claims**; tree search → **bake-off (best-of-N)**. |
| **Google Co-Scientist** (DeepMind, Nature 2026) | Coalition of specialized agents: **Generation** (hypotheses grounded in lit) · **Reflection** (virtual peer reviewer: correctness/novelty/rigor) · **Ranking** (**Elo tournament** of ideas) · **Evolution** (refine/recombine top-ranked). | The **agent roster = exactly the user's triad** (research / adversarial / evaluation) + an **Elo tournament** to rank where there is no single metric + an **Evolution** step that escapes the Karpathy ratchet's monotonicity trap. | roster → the **research skill family**; Elo → the **evaluation leg / generalized bake-off judge**; Evolution → **non-monotonic refine (the kata advantage over Karpathy)**. |
| **GPT Researcher** | Mature OSS deep-research agent; **planner → parallel executors (one per sub-question) → publisher** producing a cited report. | A clean **decompose → parallel-investigate → synthesize-with-citations** backbone. | planner → **kata-plan**; parallel executors → **kata-orchestrate frontier dispatch**; publisher+citations → **synthesis + the citation-integrity floor**. Candidate **optional synthesis backend**. |
| **Stanford STORM** | Discovers **perspectives** by surveying related work, then simulates multi-perspective expert↔writer conversations to build an outline before prose. | **Perspective/discipline discovery** — how you populate "different disciplines" automatically rather than hand-listing them. | perspectives → the **discipline-lens registry** (auto-seeded + user-pinned). Candidate **optional discovery backend**. |
| **LangChain Open Deep Research / Static-DRA / DeepResearch^Eco** | Recursive decomposition with **user-controllable depth + breadth** parameters; recurse until a depth limit then research the leaf directly; three task axes — **conceptual breadth, logical nesting depth, exploration level**. | A principled **recursion + budget model** for open-ended vs targeted runs. | the three axes → our **targeted↔exploratory dial + recursion/budget guard**. |
| **Deep-research hallucination work** (PING taxonomy; DREAM, ReportBench, ResearchRubrics benchmarks) | **All evaluated OSS deep-research agents score critically low on citation integrity.** Failure taxonomy: **G**rounding (fabricated/misattributed claims), **N**oise (ignoring best evidence), **I**ntent (planning misreads the query), **P**ropagation (later steps build on earlier hallucinations). | The single most important finding: **citation integrity is the universal failure mode** → it MUST be the never-tiered floor, and PING is the exact surface to gate against. | PING → the **research conformance floor** (the D22 analog); benchmarks → **the evaluator's rubric source**. |

---

## 3. Core thesis — research-mode is the SAME spine, with three substitutions

The harness already *is* a generic, plan-guardian, default-FAIL, recursive-dispatch loop with an adversarial
leg and a no-regression ratchet. **Research mode is not a fork; it is the spine with three swaps:**

1. **The work unit** changes from *a code file-set* → **a research question / hypothesis** (a claim to be
   established, refuted, or quantified).
2. **The conformance floor** changes from *"builds / tests / scan green"* → **a research-integrity floor**:
   every claim is grounded in ≥1 verifiable source (citation integrity, anti-PING), survives adversarial
   validation, and — for empirical work — is **ratcheted** against a declared metric (commit-if-better).
3. **The agent roster** changes from *implementers + reviewers* → **disciplinary researchers + adversarial
   validators + evaluators** (the Co-Scientist roster = the user's exact triad).

Everything else — the frozen-plan-doesn't-drift discipline, the rolling frontier, async escalation, worktree
isolation, two-way handoff, the bake-off, version-up's ratchet, `kata.config` provenance, the
Improvement-Kata — **carries over unchanged in shape**. That is the whole point and the reason this is
*tractable* rather than a second product.

---

## 4. The mapping (the coherence web — every research concept ties to one existing primitive)

| Research concept (prior art) | Existing kata primitive it reuses | Substitution / specialization |
|---|---|---|
| Methodology document (`program.md`) | **Frozen DESIGN + PLAN** | The research question + scope + metric + stop-rules ARE the frozen plan. |
| Decompose a question into sub-questions | **`kata-plan`** | Plan emits a question-DAG (sub-questions as tasks) instead of a file-DAG. |
| Parallel sub-question investigation | **`kata-orchestrate`** rolling frontier | A "task" = investigate one sub-question; disjoint *evidence-claims* instead of disjoint files. |
| Recursive open-ended exploration | **frontier + recursion-budget guard** | A sub-question may spawn children until a depth/breadth/exploration bound; orchestrate already drains a DAG. |
| Generation agent (hypotheses) | a new **research skill** (`kata-hypothesize`) | Generation, grounded in retrieved evidence + a discipline lens. |
| Disciplinary research agent (targeted/exploratory) | a new **research skill** (`kata-investigate`) | One worker, one sub-question, parameterized by `{discipline, mode: targeted\|exploratory}`. |
| Reflection / peer-review / red-team | **`kata-review`** (already exists, D15, fresh-context adversarial) | Specialized to *claims*: attack grounding, novelty, confounds — the adversarial-validation leg. |
| Elo tournament / ranking | **bake-off judge** (Spec B) generalized | Rank competing hypotheses where no single metric exists; the evaluation leg. |
| Evolution agent (refine/recombine) | **`kata-improve`** / version-up refine | Escapes Karpathy's monotonic-ratchet trap; non-monotonic recombination of top-ranked ideas. |
| Manuscript / report synthesis | a new **synthesis skill** (`kata-synthesize`) | Publisher: assemble surviving, ranked, cited claims into the output artifact. |
| Literature-dedup / novelty check | a grill-phase / evaluator check | "Has this been established already?" — the research analog of "don't reinvent." |
| Citation integrity (anti-PING) | **`kata-evaluate`** floor, specialized | The never-tiered research conformance floor (see §6). |
| Empirical metric + commit/rollback | **version-up regression ratchet** | Karpathy's exact loop = our version-up no-regression gate with a research metric. |
| Code graph (`kata.graph.json`) | **`kata-graph`** generalized | → an **evidence/claim graph** (claims↔evidence↔sources, confidence-ranked). See §5. |
| Output knowledge graph | **the Obsidian-KG / `kata-understand` spec** | **Research-mode's output IS the KG that `kata-understand` ingests and PortaVault hosts.** Keystone tie. |
| Provenance of how a finding was made | **`kata.config`** | mode/disciplines/budgets/lineage recorded per research project. |
| Persistent cross-run learning | **`kata-engram`** (future, D9/D56) | The accumulation Karpathy's loop explicitly *lacks*; our long-game advantage. |

**No orphans.** Every new idea lands on an existing column. The only genuinely *new* substrate is the
**evidence graph** (a generalization of `kata-graph`) and the **research conformance floor** (a specialization
of `kata-evaluate`). Everything else is the spine, re-pointed.

---

## 5. New components (what actually has to be built)

1. **Run-shape `research` + a `research` module** (the existing extension points — D34 run-shape, D20 module).
   `kata-bootstrap` gains a research preset: pick `{disciplines[], target, depth/breadth budget, empirical?,
   emit-KG?}`, write `kata.config`, launch. No new axis — this is exactly how `version-up` and `batch` were added.
2. **The research skill family** (name-by-job, per the A4 naming principle — no `kata-elo`, no `kata-storm`):
   - `kata-hypothesize` — generation (grounded, discipline-lensed).
   - `kata-investigate` — the disciplinary research worker (`{discipline, targeted|exploratory}`).
   - `kata-corroborate` / adversarial validation — **reuses `kata-review`** specialized to claims (likely a
     review *tier/lens*, not a brand-new skill — TBD at grill; avoid duplicating the adversarial engine).
   - `kata-adjudicate` — evaluation/ranking (Elo tournament; generalizes the bake-off judge).
   - `kata-synthesize` — publisher (cited report / manuscript / KG emission).
3. **Discipline-lens registry** — pluggable persona/method profiles (e.g. `security`, `ml`, `economics`,
   `domain-X`) injected into hypothesize/investigate. Auto-seedable via a STORM-style perspective-discovery
   pass; user-pinnable. Same "pluggable profile" pattern as the Obsidian frontmatter profiles (D-series).
4. **Evidence graph** — generalize `protocol/graph.md` → `protocol/evidence.md`. Nodes = **claims** and
   **sources**; edges = `supports | refutes | cites | derives-from` with **confidence** weights; PageRank →
   claim centrality; communities → thematic clusters. Same content-hash-cached, use-time-projection model as
   the code graph (seeding = the research question's neighborhood; digest = the budgeted evidence brief).
   **This is the artifact `kata-understand` ingests** — research-mode and the KG spec share one contract.
5. **The research conformance floor** (the never-tiered D22 analog — call it the **evidence floor**): a claim
   is "green" iff **(a) citation integrity** — every assertion grounds to ≥1 retrievable source, no fabricated
   or misattributed references (anti-PING-Grounding); **(b) adversarial survival** — it withstands the
   `kata-review` red-team pass (anti-Propagation); **(c) empirical ratchet** (empirical runs only) — the
   declared metric improved or the change is rolled back (Karpathy). Default-FAIL, never tiered — this is what
   makes research runs *comparable and trustworthy*, exactly as the code conformance floor does for builds.
6. **The recursion / budget guard** — the targeted↔exploratory dial expressed as the three literature axes:
   **breadth** (how many sub-questions), **depth** (recursion limit; at the limit, investigate the leaf
   directly — no further split), **exploration** (open-endedness). Targeted = low breadth, bounded depth, low
   exploration, deep per-leaf. Exploratory = high breadth/exploration, depth-bounded by budget. A token/time
   budget (Karpathy's fixed limit) bounds the recursion so "long-running" never means "unbounded."

---

## 6. The two architectural forks, resolved (defaults — confirm at grill)

- **Empirical vs synthesis** → **both, layered.** *Synthesis* (retrieve → ground → adversarially validate →
  rank → synthesize, with the citation-integrity floor) is the **always-on core** and needs no sandbox.
  *Empirical* (the Karpathy ratchet: run code/benchmark, measure a metric, commit/rollback) is an **optional
  capability** gated behind the existing **dependency pre-flight (D29)** + a sandbox, lit up only when the
  research project declares a runnable metric. The empirical loop is *literally* version-up's regression
  ratchet with a research metric — near-zero new machinery.
- **What "green" means** → the **evidence floor** of §5.5. Synthesis runs gate on citation-integrity +
  adversarial-survival; empirical runs add the metric ratchet. This is the never-tiered invariant; tiers vary
  *depth of search/critique*, never whether grounding is required (mirrors D22/D33 exactly).

---

## 7. How the loop generalizes (orchestrate, re-pointed)

`kata-orchestrate` already maintains a rolling DAG-frontier with async escalation and a default-FAIL gate.
Re-point it:

- **Frontier unit** = an open sub-question (not a file-task). **Disjointness** is over *claim-space* /
  evidence ownership rather than file-ownership (two investigators shouldn't be establishing the same claim).
- **Recursion** = an investigator may, instead of answering, **split** its sub-question into children
  (subject to the depth/breadth/exploration budget) — the orchestrator simply enqueues them onto the frontier.
  The DAG grows during the run; orchestrate already drains a growing frontier.
- **Gate per node** = the evidence floor (cite-integrity + adversarial survival [+ metric ratchet]).
- **Ranking pass** = when sibling hypotheses compete, `kata-adjudicate` runs the Elo tournament; the
  **Evolution** step recombines top-ranked survivors (the non-monotonic move Karpathy can't make).
- **Async escalation** = a genuinely contested/under-determined claim parks and drains like any escalation;
  human-required only when no further evidence can resolve it within budget.
- **Final gate** = fresh-context `kata-evaluate` (no-write) over the whole evidence graph: integrity + the
  synthesized report's faithfulness to its own citations. Then `kata-synthesize` emits the report + KG.

---

## 8. Layout

```
projects/Research/
  <research-project>/
    kata.config            # runShape: research; disciplines[]; budgets; empirical?; emit-KG target
    DESIGN.md / PLAN.md    # the frozen question, scope, metric, stop-rules (the "program.md")
    kata.evidence.json     # the evidence/claim graph (protocol/evidence.md)
    .kata/board, state     # machine coordination (same as any run)
    findings/              # synthesized, cited outputs
    → emits into PortaVault / Obsidian KG (the kata-understand ingest folder)
```

`projects/Research/<project>/` is just a project root with `runShape: research` — the existing project
machinery (board, state, worktrees, config, handoff) applies verbatim.

---

## 9. Lean-on libraries (optional backends behind a protocol — the aider/Graphify pattern)

`kata-graph` already established the pattern: a **floor** (tree-sitter) + **optional oracle backends**
(Graphify MCP) behind one contract. Research mode reuses it:

- **Retrieval floor** (the tree-sitter analog) = a baseline web/literature search + fetch (already have
  `WebSearch`/`WebFetch`; academic APIs as a step up). No grounding without retrieval = the hard floor.
- **Optional synthesis backend**: **GPT Researcher** (planner-executor-publisher) as a drop-in deep-research
  engine behind the synthesis contract.
- **Optional perspective-discovery backend**: **STORM** for auto-seeding the discipline-lens registry.
- **Optional ranking backend**: a **Co-Scientist OSS reimplementation** (Kaimen-Inc) for the Elo tournament.
- **Evaluator rubric source**: **DREAM / ReportBench / ResearchRubrics / the PING taxonomy** define the
  citation-integrity and faithfulness metrics the evidence floor scores against.

None are *depended on by the core* (D20 module contract): the floor works tool-only; backends are upgrades.

---

## 10. The contribution-delta — what kata adds over the Karpathy loop

Karpathy's loop is brilliant and minimal but has three stated limits we already have answers for:

1. **No multi-step / non-monotonic reasoning** (the ratchet forbids a short-term loss that enables a larger
   later gain) → kata's **Evolution/`kata-improve` step + Elo tournament** reason over a population, not a
   single ratcheted file.
2. **No persistent memory** (no cross-experiment learning beyond git history) → kata's **evidence graph**
   (persistent, queryable) + eventual **engram-mediated learning** (D56) accumulate across runs.
3. **No structured escalation** (blanket "never ask the human") → kata's **async escalation valve** keeps the
   long-running property *without* the brittleness: it drains the frontier and only hard-waits a human when
   genuinely blocked, then *learns* from the resolution (engram, future). Strictly better than "never stop."

This is the synthesis-is-the-contribution framing again: every individual piece exists in the wild; **wiring
the disciplinary roster + adversarial leg + Elo evaluation + evidence-graph memory onto a no-drift,
default-FAIL, escalation-safe spine is the novel part.**

---

## 11. Dependencies & sequencing (where this lands in the dev cycle)

Research mode is **downstream** of work already queued — it *composes with* rather than blocks them:

- **Reuses `kata-review`** (built) for the adversarial leg.
- **Generalizes `kata-graph`** (built, A4) → the evidence graph. Easier after the code-graph contract is proven.
- **Generalizes the bake-off judge** → needs **Spec B (bake-off)** for the Elo/ranking evaluation leg.
- **Shares the KG output contract** with the **Obsidian-KG / `kata-understand` spec** (the next build) — in
  fact research-mode is the *upstream producer* that fills PortaVault. Build the ingest side first; research
  mode emits into it.
- **Wants `kata-engram`** (future) for cross-run learning — but degrades gracefully without it.

**Proposed slot:** a **major post-v0.1 spec**, after (a) v0.1 is validated (D16 planning A/B), (b) Spec B
bake-off lands the judge, and (c) the Obsidian-KG / `kata-understand` spec lands the ingest contract. At that
point research-mode is mostly *re-pointing proven machinery* + the evidence floor + the discipline registry —
a far smaller lift than it looks today, *because* we refused to build a chimera and instead reused the spine.

---

## 12. Coherence audit (no-chimera / no-slop check — the A4 discipline applied)

- **One spine, not two products?** ✅ Three substitutions on the existing loop; orchestrate/worktree/board/
  handoff/config carry over unchanged.
- **Every new concept ties to a named contract with one producer?** ✅ §4 table — no orphan concepts; the only
  new substrates (evidence graph, evidence floor) are generalizations of existing contracts (`graph.md`,
  `kata-evaluate`).
- **No duplicated engines?** ✅ Adversarial validation reuses `kata-review`; ranking reuses the bake-off judge;
  empirical reuses the version-up ratchet; output reuses the KG ingest contract. Net-new skills are only the
  generation/investigate/synthesize roles + the discipline registry.
- **Long-running property preserved?** ✅ Recursion-budget guard + async escalation; "never unbounded," "never
  brittly-blocked."
- **Stays tool-agnostic?** ✅ Floor is tool-only (WebSearch/Fetch); research libraries are optional backends
  behind module contracts (D20), never core dependencies.

Verdict: **coherent path forward.** No half-baked merge; the research libraries are oracle-backends, not a
fused chimera — exactly the kata-graph/Graphify relationship.

---

## 13. Open questions for the future grill

1. Is the adversarial leg a **new skill** or a **`kata-review` lens/tier**? (Lean: a lens — don't fork the
   adversarial engine.)
2. Disjointness for the frontier: is "claim-space ownership" tractable, or do we partition by **sub-question
   subtree** instead? (Files were a clean partition; claims overlap — needs design.)
3. Evidence-graph schema specifics: claim node fields, confidence model, how `supports/refutes` edges
   accumulate and decay; reuse vs fork of `protocol/graph.md`.
4. The Elo tournament's judge: deterministic rubric vs LLM-judge vs both; how it stays *consistent* run-to-run
   (the north star) when ranking is inherently comparative.
5. Empirical sandbox: how the metric is declared/validated at freeze; reuse of D29 pre-flight; isolation model.
6. Stop-rules for open-ended exploration beyond budget: convergence criteria (diminishing new-claim rate?),
   and how "done" is judged when the question is genuinely open.
7. Citation-integrity scoring: which benchmark rubric (DREAM/ReportBench/ResearchRubrics) becomes the
   evaluator's basis; retrieval-source allow-listing.
8. Relationship to `kata-understand`: does research-mode *call* the KG-emit, or share a library with it?

---

## Sources

- Karpathy AutoResearch — [The New Stack](https://thenewstack.io/karpathy-autonomous-experiment-loop/) ·
  [Verdent guide](https://www.verdent.ai/guides/what-is-autoresearch-karpathy) ·
  [Fortune](https://fortune.com/2026/03/17/andrej-karpathy-loop-autonomous-ai-agents-future/) ·
  [MindStudio](https://www.mindstudio.ai/blog/andrej-karpathy-autoresearch-recursive-ai-self-improvement)
- Sakana AI Scientist — [Sakana RSI Lab](https://sakana.ai/rsi-lab/) ·
  [arXiv evaluation 2502.14297](https://arxiv.org/html/2502.14297v2)
- Google Co-Scientist — [DeepMind blog](https://deepmind.google/blog/co-scientist-a-multi-agent-ai-partner-to-accelerate-research/) ·
  [Google Research](https://research.google/blog/accelerating-scientific-breakthroughs-with-an-ai-co-scientist/) ·
  [OSS reimpl](https://github.com/Kaimen-Inc/Co-Scientist)
- GPT Researcher — [GitHub](https://github.com/assafelovic/gpt-researcher) · [gptr.dev](https://gptr.dev/)
- STORM — [Towards Data Science](https://towardsdatascience.com/running-the-storm-ai-research-system-with-your-local-documents-e413ea2ae064/)
- Recursion / depth-breadth — [LangChain Open Deep Research](https://www.langchain.com/blog/open-deep-research) ·
  [Static-DRA arXiv 2512.03887](https://arxiv.org/pdf/2512.03887) ·
  [DeepResearch^Eco](https://www.biorxiv.org/content/10.1101/2025.07.14.664755.full.pdf)
- Hallucination / citation integrity — [PING / Hallucination in Full Research Trajectory (arXiv 2601.22984)](https://arxiv.org/abs/2601.22984) ·
  [Reference-hallucination detection (arXiv 2604.03173)](https://arxiv.org/pdf/2604.03173) ·
  [DREAM (arXiv 2602.18940)](https://arxiv.org/pdf/2602.18940) ·
  [ReportBench (arXiv 2508.15804)](https://arxiv.org/pdf/2508.15804) ·
  [ResearchRubrics (arXiv 2511.07685)](https://arxiv.org/html/2511.07685v1)
- Automated-research systems — [AutoSOTA (arXiv 2604.05550)](https://arxiv.org/pdf/2604.05550) ·
  [Multi-Agent Collaboration for Automated Research (arXiv 2603.29632)](https://arxiv.org/pdf/2603.29632)
