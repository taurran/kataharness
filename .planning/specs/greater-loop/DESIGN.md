---
date: 2026-06-20
spec: greater-loop
status: FROZEN 2026-06-20 — grill converged (rounds 1–3) + testing-model RATIFIED; promoted to D87–D90. Changes are deliberate re-freezes.
source-ledger: ./GRILL-LEDGER.md
roadmap: ./ROADMAP.md
locked-inputs: [modular DESIGN + master roadmap, graph-runtime-first, anchor on self-end-to-end]
tags: [design, greater-loop, initiation, closeout, understand-anything, modular, draft]
---

# Greater Loop — DESIGN

The **wrapper around the harness**. Today KataHarness is the *middle* of a loop (grill→…→evaluate→handoff). The
Greater Loop adds the **front half** (a real initiation that ingests the user's intent and specs it via the
grill) and the **back half** (a closeout that maps what changed, gets the human's decision, and either loops to
the next version-up or starts something new). Three **plug-and-play modules**, each a directory with its own
`AGENTS.md`, sequenced by a thin conductor.

```
   ┌────────────────┐     ┌─────────────────┐     ┌────────────────┐
   │  INITIATION    │ ──▶ │   THE HARNESS   │ ──▶ │   CLOSEOUT     │ ──┐
   │ modules/       │     │  (built loop —  │     │ modules/       │   │
   │  initiation/   │     │   REUSED)       │     │  closeout/     │   │
   └────────────────┘     └─────────────────┘     └────────────────┘   │
   kata-initiate:         grill→freeze→exec→       kata-closeout:        │
   ingest intent;         evaluate (REAL           track artifacts;      │
   route kind; capture    orchestrated run,        kata-understand map;  │
   GOAL (INTENT.md);      RESULT.json emitted)     satisfied? commit/    │
   configure target/                               push/merge?           │
   platform/vault;          ▲                      run-again or new? ────┘
   grill-to-ready OR        │ kata-loop conductor sequences the three
   user says "execute"      └─ and carries context across the loop-back
```

## 1. The conductor — `kata-loop` (NEW, thin)
A **thin** top-level conductor (GL-R2a) that sequences `initiation → harness → closeout` and owns the
**loop-back**. It **composes, never reimplements** — like `kata-sprint`, it calls the modules and the inner
`kata-orchestrate`; it does not re-plan or re-evaluate. The greater loop is **optional**: absent the conductor,
a direct one-shot harness run behaves exactly as today (BC).
- **Loop-back carries context (GL-R2d):** after closeout, "run again (version-up)" re-enters `kata-initiate`
  **with the prior run's context** — new baseline, the understand-map, lessons — so the next cycle starts
  informed, not cold. "Build something else" = a fresh initiation.

## 2. Initiation module — `modules/initiation/` (NEW; own `AGENTS.md`)
**`kata-initiate`** is the front door (GL-R1a). It OWNS the front-half flow and **composes** existing pieces
(`kata-readiness`, `kata-grill`, `kata-bootstrap` as the config-writer, `kata-context`); it reuses the D71
**priming-and-grill** machinery rather than re-inventing it.
- **Ingest** the user's design/brief (from the system prompt and/or a project brief file) → classify **kind:
  `project | research | version-up`**.
- **Capture the GOAL → frozen `INTENT.md` (NEW artifact, GL-R1b)** — the explicit hand-off the harness freezes
  on (the thing missing when version-up goals weren't captured):
  ```
  INTENT.md frontmatter:
    kind: project | research | version-up
    goal: <one-paragraph north star>
    fixes: [ ... ]            # version-up: what's being repaired
    features: [ ... ]         # what's being added
    modulesAdded: [ ... ]     # new modules/skills
    changeSummary: <what changes in this version>
    target: { kind: self | existing | greenfield, path, vault, platform }
    grillDepth: skip|light|standard|full
    readiness: <the agent's "enough-to-execute" verdict + rationale>
  ```
- **Configure WHERE/ON WHAT it runs, interactively (GL-R3c — folds in install-portability).** The initiation
  session leads the user through **target + platform + workspace binding**: self · an existing repo · a vault
  (link/scaffold PokeVault, point at your own, or aim each folder) · platform (Claude · MindBridge/Quick · Kiro).
  This is the **install-portability config layer woven into initiation** — the heavier per-platform *installer
  mechanics* remain a sub-component the initiation session triggers (a platform brings its own installer +
  `AGENTS.md`).
- **Spec-to-ready, dual control (GL-R2b):** drive `kata-grill` at the chosen depth. The user can say **"execute"
  at any point** (hard bail). Independently the grill **self-judges readiness** (enough decision branches
  resolved to one-shot) and, when met, **proposes execute** — the user confirms. Either path **freezes
  `INTENT.md`** and hands the full context to the harness.

## 3. Closeout module — `modules/closeout/` (NEW; own `AGENTS.md`)
**`kata-closeout`** (NEW, GL-R1c) owns the back-half control flow; **composes** `kata-report`, `kata-understand`,
`kata-handoff`, and git. It runs **after** the harness's default-FAIL gate (it never gates — that stays
`kata-evaluate`).
- **Track everything:** consume the machine-readable run artifacts — `RESULT.json` + footprint manifest +
  mutation proof (from **F1**, §5) — so the record is real, not transcribed.
- **`kata-understand` (NEW) — the understand-anything map (GL-R2c, opt-in).** Closeout **offers** it; the user
  opts in per run. It produces a structured comprehension map of **what changed + what was built**, **backed by
  the `kata-graph` runtime (F2)**; if the graph is unavailable it degrades to a lighter git/diff map with a note.
- **The human decision gate:** *Are you satisfied?* → *commit / push / merge?* (carries the chosen git actions
  out) → *run again (version-up) or build something else?* → hand to the conductor's loop-back.

## 4. Modularity / `AGENTS.md` (GL-R1d)
Each module is `modules/<name>/` with its **own `AGENTS.md`** + its skills, composed via the **nested-AGENTS.md
rollup** `kata-orient` already supports — no new plumbing. The conductor depends only on the module **contracts**
(`INTENT.md` in; report + decision out), so a platform (MindBridge) can **swap a module** and bring its own
`AGENTS.md`/installer. Spine #3 (agnostic-via-adapters) applied to whole stages, not just tools.

## 5. Foundations (prerequisites — build FIRST, GL-R3a)
- **F1 — wire the eval artifacts into the live gate.** Make `kata-evaluate`/the gate actually **emit**
  `RESULT.json` (via the built `run_result`), compute the **footprint manifest** vs the plan, and record the
  **mutation/non-vacuity** result. Closes the dogfood-2 residual; it is the closeout's data layer. **Folds in the
  testing rigor (§7).**
- **F2 — graph runtime operational (minimal, GL-R3d).** Install tree-sitter + a generator that produces
  `kata.graph.json` per the existing `protocol/graph.md` contract (**Python first**), enough to back
  `kata-understand` + version-up footprint. **Defer the full Graphify oracle** (neighbors/shortest-path/
  pr-impact) to a later upgrade. This makes the long-specced-but-inert `kata-graph` actually run.

## 6. The harness (middle) — REUSED verbatim
The built loop (grill/plan/orchestrate/worktree/tdd/evaluate/handoff + sprint-cadence + loop-cognition). The
conductor calls it; no change to its spine.

## 7. Testing-model — ASSESSMENT (answer to "is it necessary?", GL-R3b) — **needs ratification**
**Grounded in our own Hermes research (`loop-cognition/RESEARCH.md` §2–3):** Hermes has **no default-FAIL
grounding gate** — its quality control is a garbage-collecting curator, not a gate; we are already *more*
rigorous. Hermes teaches *learning loops*, **not** a dedicated testing model. The rigor that matters lives in the
**process** — fresh-context, no-write, **default-FAIL** evaluation + **mutation/non-vacuity proofs** +
machine-readable **RESULT** — which is built or lands in **F1**. A separate testing *model* adds complexity for
marginal gain.
- **Recommendation:** **do NOT build a dedicated testing-model.** Deliver the rigor via **F1**. Keep "route the
  eval/test step to a different model" as a **latent option in the multi-model layer** (not built now). Retire the
  `testing-model` brief to *"assessed → folded into F1; revisit only if multi-model lands and a real need shows."*
- **✅ RATIFIED 2026-06-20** — fold into F1; no separate testing-model. (latent option stays in multi-model.)

## 8. Alignment with the prior briefs
- **`install-portability`** → its **config layer folds into `kata-initiate`** (§2, interactive target/platform/
  vault). The modular per-platform installers remain a sub-component initiation triggers. (Brief updated to point
  here.)
- **`multi-model-orchestration`** → AFTER the self greater loop; it is also where the §7 testing-model option
  lives latent.
- **`testing-model`** → folded into F1 per §7 (pending ratification).

## 9. Backward-compatibility & spine
- **BC:** conductor absent ⇒ today's direct harness run, unchanged. `INTENT.md` absent ⇒ harness reads the
  frozen DESIGN as today. Modules are additive.
- **Spine preserved:** plan-doesn't-drift · default-FAIL (never weakened by closeout — it reports, never gates) ·
  two-way handoff · everything-versioned · agnostic-via-adapters (now at module granularity).
- **Discipline:** no module self-certifies; each is built via a **real orchestrated run** (worktrees + concurrent
  workers + fresh-context review + human version-select — see memory), Snyk on new Python.

## 10. Build order → see `ROADMAP.md`
Foundations (F1, F2) → Initiation → Closeout (incl. understand) → `kata-loop` conductor → **dogfood the whole
greater loop on SELF** → then install-portability (external) / multi-model.

## 11. Decisions to promote at freeze (GL1–GL?? → D87+)
See `GRILL-LEDGER.md` for the full rationale; promoted to D-numbers at freeze.

## 12. Status & open items (before freeze)
- **✅ §7 testing-model — RATIFIED** (2026-06-20): fold into F1; no separate model.
- **Execution UX (decided 2026-06-20):** orchestrated runs dispatch workers **foreground-parallel** (Claude
  Code's native live agent panel). A **cool, host-agnostic KataHarness live dashboard** (artistic ASCII +
  animated bars, `rich`/`textual`, tails board+state) is captured as `[[subagent-dashboard]]` — **build-later**,
  orthogonal, does not block the loop.
- **Per-phase clarification:** the user will ask/clarify details on each item as we walk the ROADMAP (the
  high-level design freezes; phase specifics are refined just-in-time per phase).
- **REMAINING TO FREEZE:** just the human "freeze" go — then promote GL1–? → D87+ and start Phase 0 (F1+F2)
  as a real orchestrated run, foreground-parallel.
