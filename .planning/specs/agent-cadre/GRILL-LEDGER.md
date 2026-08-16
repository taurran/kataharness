---
spec: agent-cadre
status: draft
opened: 2026-08-16
tier: pre-design operator rulings (BL-N20 expanded program + BL-N04 extraction; full grill owed)
sources: BL-N20 · BL-N04 · BL-N16 (the living substrate) · BL-N10 (challenger) · BBM-1 (judges) ·
  the 2026-08-16 validation-stack live runs (design data points, logged in
  ../backlog-burn-02/OBSERVATIONS.md)
---

# GRILL LEDGER — the agent cadre (our own agents, for everything we execute)

## Operator rulings (2026-08-16, third sitting)

- **AC-1 · Author ALL agent types; MANDATE their use.** Our own optimized agent definitions for
  EVERYTHING we execute — coding agents especially. Dispatch of a bare host-default agent fails
  closed (BL-N20/M34 enforcement). No role runs undefined.
- **AC-2 · The agents are LIVING.** Two evolution channels: (a) our own optimization updates to
  the definitions; (b) the BL-N16 learning substrate — per-agent learning accrues INTO the
  definition (append-for-audit / distill-for-load), so an agent's execution pattern improves
  across runs without human re-authoring, gated per BL-N16's rules.
- **AC-3 · The roster is the deliverable shape.** Every agent to build, and PER AGENT: the
  existing agents pulled from as inspiration + the required optimizations that ELEVATE the
  execution pattern beyond the examples. Not "inspired by" hand-waving — named sources, named
  deltas.
- **AC-4 · Design constraints (carried from BL-N20's second sitting):** lightweight, never
  general-purpose blobs · derived-from-GP permitted, aligned against Hermes/Quicksilver/Pi, but
  OURS · conductor + orchestrators THIN by definition · coding agents carry GOOD-CODE/BAD-CODE
  exemplar pairs; the exemplar pattern extends per role.
- **AC-5 · Sequencing: around BL-N08 (the run-decoupling redesign) — before or after, whichever
  executes optimally.** Grill decides. (The roles ARE that redesign's cast, so the coupling is
  real in both directions.)
- **AC-6 · Research mandate:** survey other harnesses (Hermes, Quicksilver, Pi, GSD, BMAD) and
  the GitHub agent ecosystems for how to build our agents. Dispatched 2026-08-16; report lands
  as `RESEARCH-AGENTS.md` beside this file, evidence-labeled.
- **AC-7 · The superpowers extraction rides this program (amends BL-N04):** our own pack —
  operator's verbatim term "our own mindbridge superpowers" (⚠ naming to confirm at grill; prior
  filings said "KataHarness Superpowers"; MindBridge is otherwise a hands-off boundary) — is
  PART OF THE CADRE, borrows the current superpowers' frontmatter shapes + execution patterns,
  and is **the ONLY superpowers pack loaded when the loop launches via its own command**
  (BL-N21/UX-28).
- **AC-9 · Research agents get DEEP definition, including research SPECIALISTS (operator,
  2026-08-16, fourth sitting).** The researcher is not one generic agent: define the research
  role deeply AND a specialist sub-family (candidate splits for the grill: doc-grounded/field
  research · codebase/archaeology research · academic-paper/experiment research · triage/scoping
  research — the splits themselves are grill questions, not rulings). Inspiration sources
  operator-named: **Karpathy's auto-research repo** (verbatim term; the research pass identifies
  the exact repo with evidence labels rather than guessing) **and other research-agent repos**.
  Research specialists follow the same cadre rules (AC-1..4: lightweight, living, evidence-label
  discipline in-substrate, use mandated).
- **AC-11 · Advisor + Challenger model routing: ALWAYS A STEP UP; default Fable; prefer the
  OPPOSITE family from the validator (operator, 2026-08-16, fifth sitting).** The advisor and
  challenger default to **Fable**; when a model of the opposite family from the validator is
  available, use it — operator named **"Opus or Sol"** as the step-up set (⚠ "Sol" recorded
  verbatim: presumed a non-Anthropic-family model name; identify precisely at grill, do not
  guess). The invariant: **the advisor/challenger tier is always a STEP UP** from the tier of
  the work it judges — cross-family preferred for the challenger (independence is the point,
  per the BL-N10 correction). In **express mode** (the mode currently named "economy" — the
  operator directs a RENAME, filed as BL-N22) the advisor/challenger "just steps up" — one tier
  above the mode's working tier rather than jumping to the ceiling. This REFINES D59's ladder:
  judgment-over-work roles step UP relative to the judged work; only build/encode work tiers
  down. `kata_models` resolver + the substrate files carry this when built.
- **AC-10 · Validators EXECUTE the tooling against the artifacts; challengers attack coverage.
  (Process lesson from the 2026-08-16 stack, elevated to a design rule.)** Two independent
  Opus-5 validators plus two convergence rounds all audited artifacts AS PROSE — and the stack's
  only live wrong-output defect (BL-X12: open questions emitted as resolved decisions) surfaced
  only when the challenger EXECUTED the session's own tooling against the session's own
  artifacts. Substrate consequences: the VALIDATOR definition carries "run the consumers of what
  you audit" as a standing duty; the CHALLENGER definition carries the coverage attack
  (including confessed-thin-points and held-list softness probes) as a standing duty. Second
  lesson from the same run: the challenger REFUTED two of AV-1's three HIGH framings at source
  while confirming every underlying fact — validators over-grade; a challenger that re-derives
  from source is not optional accuracy garnish, it is the severity calibrator.
- **AC-8 · Live data points are design input.** The 2026-08-16 validation stack's ad-hoc agents
  — five per-item judges, two final evaluators, two Opus advals, one anchor-tier challenger —
  each ran with a recorded brief, posture, tier, token cost, and outcome. The real definitions
  start from what those runs proved works (refute-posture, verify-primitives, report contracts,
  push-back clauses) and what they proved missing (no persistent identity, no exemplars, no
  learning carry-over, re-briefed from scratch every time).

## THE ROSTER — draft v0 (pre-research; the grill + RESEARCH-AGENTS.md harden it)

> Per AC-3: agent · what it is · inspiration sources (named) · required elevations beyond them.
> All inspirations are REFERENCE material under the independence doctrine (UX-32/BL-N04) — we
> write our own.

| # | Agent | What it does | Pulling from (inspiration) | Required elevations (the deltas that make it OURS) |
|---|---|---|---|---|
| 1 | **Conductor** | the primary human-facing session: research, brainstorm, rulings intake, gating | the live sessions themselves; Claude Code main-loop conventions | THIN by definition (spine #8 baked in, not graded after); records rulings verbatim-with-provenance; never authors gated artifacts; carries the truth-serum report register |
| 2 | **Orchestrator** (chef/sous-chef under BL-N08) | runs the loop: dispatch, board, wave/bake management | today's kata-orchestrate prose; GSD's execute-phase orchestrators; Agent-Teams lead protocol (mined, D4) | thin + code-seam-backed (BL-M33): the definition assumes the seam, never re-implements it in prose; branch-parallel ("bake") management; zero authoring rights |
| 3 | **Coder** | builds one owned slice against a frozen plan | host general-purpose coding agents; GSD gsd-executor; feature-dev patterns; our burn briefs (step-0 verify, push-back) | GOOD/BAD-code exemplar pairs in-substrate (AC-4); owner-set discipline structural; mechanical self-gates authored by default; PD-2 report contract native, not briefed |
| 4 | **Validator** (adversarial) | attacks finished work to find real defects | feature-dev code-reviewer; GSD code-reviewer; our AV-1/AV-2 briefs (multi-lens, reproduce-don't-trust, held-list discipline) | lens assignment (interaction/behavior/security/records) as substrate config; mandatory "what held" section; confessed-thin-points section (proved valuable — the challenger used it) |
| 5 | **Evaluator** (the gate) | fresh-context, no-write, default-FAIL final evaluation | kata-evaluate contract; GSD verifier; our two final-eval runs | machine-evidence-first (BL-X11's identity-check routing native); run-level lens (between-items residuals); scope-of-re-run output mandatory on NEEDS_WORK |
| 6 | **Judge** (per-item gate, burn/wave) | diff-vs-brief + independent claim reproduction per item | BBM-1's judge briefs (5 live runs, 4/5 first-pass catches) | scoped-cheap (one item, minutes); verdict schema pinned; feeds the wave eval |
| 7 | **Advisor** | fresh-context consult at trigger points | D167 advisor-executor (live n=1 July run) | tunable hooks surfaced (BL-N18); reach extended through the seam so it fires wherever the loop runs (the burn-02 gap) |
| 8 | **ARBITER** (new) | advisor + second-brain decision-making: consults the vault's decision history when arbitrating | the advisor pattern + Kiban vault consult (D9 seam); no external equivalent known yet (research to confirm) | vault-grounded verdicts with citation obligation; D74 redaction native; needs its own definition at grill (operator, BL-N08) |
| 9 | **Challenger** (new) | cross-examines the ADVERSARIAL VALIDATOR's findings — refute/downgrade/upgrade; separate subagent, ideally different model | BL-N10 ruling; the 2026-08-16 live challenger run (AC-8 data point) | different-model execution as substrate default; per-finding verdict schema (CONFIRMED/REFUTED/RESCOPED); coverage attack (the held-lists) as a standing duty |
| 10 | **Researcher + research SPECIALISTS (AC-9, deep)** | doc-grounded external research, evidence-labeled — plus a specialist sub-family (doc/field · codebase · academic/experiment · triage-scoping; splits grilled) | GSD researcher family; our RESEARCH-HERMES-PI dispatch (labels held up under three later audits); **Karpathy's auto-research repo + other research-agent repos (operator-named, research pass identifies precisely)** | evidence-labeling (RV/DS/UA/LP) mandatory in-substrate; scope fences (never rules, only reports); specialist depth per split; auto-research pipeline patterns (hypothesis→probe→record) mined from the named repos |
| 11 | **Design-author / Plan-author** | dispatched authoring of DESIGN/PLAN artifacts (KH-T13) | our three-revision UX design-author run (labels discipline, change-summaries) | label discipline in-substrate ([author-proposed] native); ledger-fidelity self-check before returning; erratum-pass capability |
| 12 | **Learning agent** (new) | applies gated learning to agent substrates (BL-N16) | Hermes skills pipeline (staged writes/diff/approve); kata-promote's two-stage gate | confidence-thresholded application; recency conflict resolution; security scan on self-written learning; per-agent (never harness-wide blanket) |
| 13 | **Context-scanner** (new, assess first) | initial intake on existing code: full-context scan before any run acts | GSD codebase-mapper; Explore; our graph runtime (kata-graph/graph_gen) | large-codebase strategy (budget exhaustion honesty, partial-map labeling); feeds the BL-N21 intake; assessment at grill decides agent-vs-function |
| 14 | **Cadre specialists** (BL-N04) | installable domain specialists (GitHub specialist named; coding-optimization; domain packs) + the extracted superpowers pack (AC-7) | current third-party superpowers (frontmatter shapes + execution patterns, as REFERENCE); BL-N16 spin-off seam (kata-promote stage 2) | vault-resident (Kiban, official folders, persist across reinstalls); spin-off-from-learning path; the pack is the only superpowers loaded by the loop command |

**Cross-cutting elevations (every agent):** substrate file per BL-N16 (frontmatter + markdown,
temporal learning log, capped active section) · model-tier declaration RELATIVE per D59 (never a
hard model id) · report contract + PD-1/PD-2 injection standing · lightweight (AC-4) · loaded
via the dispatch seam ONLY (BL-M33/M34).

## Research landed (2026-08-16 — `RESEARCH-AGENTS.md` beside this file; evidence-labeled)

Factual corrections it delivers (accepted as facts, not rulings): **Quicksilver = Hermes v0.19's
codename** — the AC-4 triad is TWO harnesses · **Hermes has NO agent-definition files** (dispatch
contract only) — **Pi is the format anchor** (`pi-subagents`: acceptance/completionGuard/
turnBudget/fallbackModels/defaultContext/memory — the richest schema surveyed) · **superpowers
ships no agents/ dir; its frontmatter is minimal name+description** (AC-7 borrows a deliberately
minimal shape; its role prompt-TEMPLATES are the transferable gold) · **AC-9(a) RESOLVED:
`github.com/karpathy/autoresearch`** (separation-of-powers + structural anti-gaming) · Claude
Code ships native per-agent memory with a 200-line injection cap (independently corroborates
BL-N16's distill-for-load) but fails on hardened tools-allowlists (#57507) — **BL-N16 must own
its own memory path** · **gsd-verifier's 7-step artifact-level protocol is a mechanized PD-1
detector** — direct prior art for 🔴 BL-N01's truth-serum machinery (cross-noted there).

Challenges the GRILL must answer (research-raised, NOT adopted silently): (1) the roster has no
FALSE-POSITIVE control in validator/challenger/judge — every elevation sharpens refute-posture,
nothing bounds it (candidate: anchored confidence rubric with a floor); (2) row 10's four-way
specialist split is one seat too many — research recommends 3 (doc/field · codebase ·
experiment) with triage folded into a mandatory brief section (field evidence: deep-research
systems RETREATED from supervisor splits); (3) researcher stays report-only, externally gated —
AI-Scientist's self-reviewing cast produced a 42% experimental failure rate with misleading
claims (arxiv 2502.14297); (4) compiled-vs-authored-portable definition format (BMAD compiles,
superpowers ships portable prose) — a PREREQUISITE decision for AC-1; (5) a length/budget policy
for definitions (field spans 47→1,452 lines, no consensus); (6) ecosystem-alignment claims must
cite files we read — high-star collections proved self-inconsistent (a published read-only
reviewer convention shipping a reviewer with Write/Edit).

## Open for the full grill

Naming (the AC-7 ⚠) · BL-N08 before/after sequencing (AC-5) · agent-vs-function call on the
context-scanner · does the Judge fold into the Evaluator as a tier or stand alone · triage/intake
role: own agent or conductor duty · the per-role exemplar sets (AC-4) · substrate schema final
form (BL-N16 grill owns it; this spec consumes it).
