# MODES-DESIGN — KataHarness operating modes (design, pre-implementation)

> **Status: DESIGN (brainstormed 2026-06-07), not yet implemented.** Produced via the brainstorming skill;
> next step is a per-spec implementation plan (Spec A first). Read with `DESIGN.md`, `STANDARDS.md`,
> `.planning/REVIEW-v0.1.md`, and `.planning/SKILL-COST-RATINGS.md`. Decisions here are logged in
> `.planning/DECISIONS.md` (D17+). Items marked *(confirm at spec review)* are recommended defaults.

## Vision
Operating modes that trade **effort / thoroughness / completeness against cost**, all producing **one-shot
results**, where Standard and Advanced raise output *quality* (not just spend). A cheap one-shot can be
**escalated** up a tier — and because the cheap tier's frozen artifacts seed the expensive pass, stepping up
is cheaper than starting cold. The harness's non-negotiable north star is **consistency**: the same mode
yields comparable, reproducible output, run to run. "Without consistency it is nothing." (D18.)

## Prior art (researched 2026-06-07 — the pieces exist; the synthesis is the contribution)
- **LLM cascade / FrugalGPT** (arXiv 2305.05176): cheap→escalate-if-not-good-enough, at the *model* level.
- **Best-of-N**: Cursor multi-agent (run prompt 3–5× in worktrees, judge, merge); **AgentHub** (`/hub:*`,
  installed here) dispatches N subagents in worktrees, judges, merges the winner. = the bake-off, shipping.
- **Effort tiers**: Claude `effort` param (medium/high/xhigh/max); "Ares" adaptive per-step effort.
- **Spec-driven dev**: GitHub **Spec Kit** — spec-as-source, "many implementations from one spec for different
  optimization targets," iterative refinement. Closest competing design.
- **Novel here:** (1) **skill-set tiering** (modes change *which skills + at what depth*, not just the model);
  (2) **escalation-with-reuse** (cheap tier seeds the expensive one); (3) **Improvement-Kata framing for
  one-shot version-ups of existing projects**. Do NOT reinvent model-effort (use Claude `effort`) or the
  bake-off plumbing (use AgentHub / our worktree pattern).

## The architecture — two orthogonal dials + à-la-carte

### Dial 1 — Mode = tier + modules (unified axis) *(confirm at spec review)*
A **mode** sets two things at once, so the names `Essential / Standard / Advanced` describe both:
1. **Which modules are active** (breadth), and
2. **The tier of each tiered skill** (depth) — Essential mode runs the `-essential` variants, etc.
Modes (D17 — named **Essential / Standard / Advanced**; "Master" rejected for the master/slave connotation):

| Mode | = spine + … | Quality-floor contract |
|---|---|---|
| **Essential** | spine only (+ `review-essential` smell-test) | One-shot, builds, **conformance-gated**; cheap smell-test of the highest-risk surfaces. PoC-grade, best value. |
| **Standard** | spine + `quality` module | Essential **+ full adversarial review + systematic debugging + deeper grill/plan**. Production-reasonable. |
| **Advanced** | spine + `quality` + `design` + `bakeoff` (+ `improve`) | Best-of-N, design-complete, refined. Max value. |

### Dial 2 — Effort overlay (orthogonal)
Model + reasoning effort (Claude `effort`), set independently of the mode. "High-effort run with the
Essential skill set" is a valid combo — effort multiplies depth-per-step *over* the skill selection. Set at
the bootstrap; **not** a mode axis. (D19.)

### À-la-carte modules
Any preset + added module(s) as an extra pass — e.g. **Essential + `design`**. Forces the constraint:
**modules are independent and additive** (clean interface: declares needs/produces/where-it-slots), so any
module bolts onto any tier without entangling. (D20.)

## Spine vs modules
- **Spine (always runs — the consistency machine):** `kata-grill` · `kata-design-doc` · `kata-plan` ·
  `kata-orchestrate` · `kata-board` · `kata-worktree` · `kata-tdd` · **`kata-evaluate`** · `kata-handoff` ·
  `kata-selfhandoff`. Every mode ends at the **same** `kata-evaluate` default-FAIL gate.
- **Modules (additive feature-sets):** `quality` (= `kata-review` + `kata-diagnose` + deeper grill/plan gate) ·
  `design` (own spec) · `bakeoff` (N-variant orchestration; "tier" = N) · `improve` (`kata-improve`, powers
  version-ups). Future: `security`, `docs`.

## Tiering — cost-gated, two mechanisms (D21)
Tier where it pays; don't explode into ~30 files.
- **Separate per-tier skill files** (max determinism — prevents the context-rot/overstep of a single
  branching skill) — reserve for **high cost AND high variance**: `kata-grill`, `kata-review`, `kata-plan`,
  `kata-diagnose` (light/full). Each tier file is thin and **points to one shared rubric in `resources/`**
  (DRY-by-pointer, no duplicated substance).
- **Mode-passed depth hint** (one file) — for **medium** skills where over-doing it is cheap:
  `kata-design-doc`, `kata-tdd`. The active mode tells them how deep; no file fork.
- **NEVER tiered — the consistency floor (D22):** `kata-evaluate`. The conformance gate is the **uniform
  invariant** that makes results comparable across modes and across N variants. Contrast: `review` tiers
  (adversarial depth is discretionary), `evaluate` does not (conformance is constant). This is the spine of
  "consistency is everything."
- **Not tiered:** all weight-1 skills; and `kata-orchestrate` (throttled by plan shape + model pinning, not
  internal tiers — tiering the spawn-hub would fragment the spine).

## Cost-weight metadata
Bake the `.planning/SKILL-COST-RATINGS.md` weights (1–5 + base/amplification/exec-context) into each skill's
frontmatter (`cost-weight`) + the README index. Dominant axis = **amplification** (spawn ≫ loop ≫ none);
fresh-context spend is cheaper-to-the-loop than equivalent inline. Lets the bootstrap **price a mode** and
each à-la-carte add. Heaviest: `kata-orchestrate` (5, spawn hub) > `kata-grill` (4) > diagnose/tdd/plan (3).

## New components
- **`kata-bootstrap`** (new skill *(confirm at spec review)*) — pre-loop GSD-style Q&A selector: picks mode +
  à-la-carte modules + effort, shows the **cost preview** (summed weights), writes `kata.config`, launches the
  loop. Its own skill because it runs *before* the loop and writes config (not an orchestrator param).
- **`kata.config`** — per-branch provenance: `{ mode, modules[], effort, bakeoff: {N, lineage}, skillVersions }`.
  The reproducibility backbone; what makes escalation (C) and bake-off (B) comparable.
- **`docs/TAXONOMY.md`** (to write) — categories, `kata-<verb>` naming, the **tier-family convention**
  (`kata-<verb>-<tier>`), spine-vs-module.
- **`kata-orchestrate`** reads `kata.config` to select which skills/tiers/modules run.

## Scope & sequence
- **Spec A** = the mode/tier/module/config/bootstrap system + cost-weight metadata + tier `kata-grill`,
  `kata-review`, `kata-plan`, `kata-diagnose` + the `kata-evaluate`-stays-single invariant + TAXONOMY.
  Fold the grill **efficiency refactor** in while restructuring it (move L8-narrative + convergence checklist
  to `resources/` → ~30% lighter body, per the ratings).
- **Spec B** = bake-off (N variants → judge → pick → refine up), on AgentHub/worktrees.
- **Spec C** = one-shot version-ups / feature-rollouts of existing projects (the Improvement-Kata track;
  consumes A's `kata.config` so a branch knows how it was made and can step up a tier cheaply).
- **`design` module** = its own parallel spec (UI/UX, 2D/3D assets, slides, mobile, image-FM imagery — Claude's
  design blind spot). Built to *slot into* Advanced; inherently tiered.

## Open / deferred
- `kata-tasklist` **reframed** (D23): from file-locked claim → a **virtual task board** over GSD structure +
  backlog, syncing to Jira/Asana via MCP (env already has `pm-skills`/`atlassian` MCP). Orthogonal to modes; backlog.
- Efficiency refactors (grill prose + orchestrate worker-prompt → `resources/`/`protocol/`) — backlog / fold into Spec A.
- Confirm at spec review: mode=tier unification (vs independent tier+module knobs); `kata-bootstrap` as its own skill.
