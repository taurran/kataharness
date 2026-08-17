# kata-plan — shared method (RUBRIC)

The tier-invariant plan method. The `kata-plan-<tier>` skills set only depth; they all obey this.

---

## Purpose

The plan is the contract [[kata-orchestrate]] enforces. Its job is to make execution *mechanical*: each task
is small, owns a disjoint slice of files, has a runnable gate, and slots into a dependency DAG. **The plan
adds no new decisions** — it only sequences the frozen DESIGN. An unresolved decision here means the grill /
design-doc was incomplete; go back, don't decide in the plan.

## Decompose vertically FIRST, then assign ownership

Decompose by **vertical tracer-slices** — each task cuts through the layers it needs end-to-end (mattpocock
to-issues; [[kata-tdd]] "vertical slices, never horizontal"). THEN take each slice's touched files as its
ownership set. **File-ownership is the isolation mechanism, not the decomposition axis** — never carve
horizontal layer-tasks just to make files disjoint. If two vertical slices genuinely share a file, sequence
them in the DAG (one wave after another) rather than splitting into horizontal layers.

## The load-bearing property: DISJOINT file ownership

Partition the work so **no file is owned by two tasks.** This is what lets concurrent workers run in isolated
worktrees and merge with zero conflicts ([[kata-worktree]]) — and what makes "stay in your lane" a checkable
rule rather than a hope. If two tasks genuinely must touch one file, either merge them into one task or split
the file; never let ownership overlap.

## Structure (frontmatter the orchestrator reads)

```yaml
ownership:      { T1: [files...], T2: [files...], ... }   # disjoint across all tasks
waves:          { wave1: [T1], wave2: [T2, T3], ... }     # parallelizable sets
depends_on:     { T2: [T1], T3: [T1], T4: [T1, T2] }      # the DAG
evidence:       { T1: ["artifact:<path>"], T2: [...] }    # REQUIRED — one entry per task (below)
builds_against: { D1: ["C1@<64-hex surfaceHash>"] }       # dependent -> contract pins (OPTIONAL)
```

Derive waves from the DAG: a wave is the set of tasks whose dependencies are all satisfied and whose file
sets are disjoint. Sequential single-task waves are fine; parallel waves are the payoff.

## Completion evidence — the per-task `evidence:` field (REQUIRED)

**No plan item freezes without its completion-evidence declaration.** One entry per task in the PLAN
frontmatter, authored here by the plan-author and checked at the freeze gate — a task with no `evidence:`
entry **fails plan freeze**. This is what lets the close resolve every plan item mechanically instead of
degrading to file-touch heuristics: at close time the declaration is the thing re-run or re-checked, so
"done" is a fact a machine re-derives rather than a claim a report asserts.

```yaml
evidence:
  T1: ["artifact:skills/plan/kata-plan/RUBRIC.md"]
  T2: ["test:tools/tests/test_evidence_grammar.py::test_test_form_compiles_to_the_design_pinned_argv"]
  T3: ["probe:gauntlet"]
```

**The grammar is CLOSED — three forms, no fourth, no escape hatch. Do not restate it in your own words;
CITE it:**

- **Implementation:** `tools/evidence_grammar.py` — `FORMS`, `parse_declaration` (the outer
  `fullmatch` grammar), `compile_declaration`, and `check_evidence_map` (the whole-plan check). That module
  is the one place a declaration is parsed, guarded, and REFUSED.
- **Registered contract:** `protocol/exec-safety.md`'s three `evidence_grammar` rows (`artifact:` /
  `test:` / `probe:` forms) — trust domain, guard, and compiled argv per form. Those rows were written
  before the module and the module is built to them; a divergence is resolved out loud, never by quietly
  rewriting either side.

One-line orientation only — **the two sources above are authoritative**: `artifact:<repo-relative-path>`
(NEVER executed; existence/wiring-checked) · `test:<pytest-node-id>` (compiled to structured argv, no
shell, ever) · `probe:<registered-name>` (a NAME resolved against the committed `tools/probe_registry.json`;
an unregistered name is REFUSED, never executed as a command, never auto-registered).

**A freeform command string is not evidence and is REFUSED at the freeze gate** — `"pytest -q tools/tests"`,
`"run the suite"`, and a bare path with no form prefix all fail `parse_declaration` before any inner guard
runs. If a task's real proof fits none of the three forms, the answer is a new registered probe entry
(repo-committed, reviewed like code), never a looser field.

**Authoring rules:**

- **Declare what proves THIS task**, not the suite. A node-ID that would still pass with the task's work
  reverted is a vacuous declaration — the same defect class as a test that asserts nothing.
- **Name the NEW test node-IDs the task will create**, not only pre-existing ones: the declaration is the
  contract that the test gets written.
- **Verify before you cite** (`protocol/reuse-claims.md`): an `artifact:` path or a `probe:` name asserted
  without checking is a phantom-machinery claim. A `probe:` name must already exist in
  `tools/probe_registry.json` — the grammar refuses an unregistered name at freeze, by design.
- Multiple declarations per task are normal (the test **and** the artifact it lands).
- **Round-trip the map before freezing.** `check_evidence_map(evidence, task_ids, repo_root=<root>)` raises
  on all four defect shapes: no `evidence:` map at all · a task with no declaration · a declaration that
  fails the grammar or an inner guard · a key naming a task that does not exist (a typo there silently
  leaves a REAL task undeclared).

## Contract edges (`builds_against`) — Freeze/Float M1

**OPTIONAL.** Declares that a dependent task builds against a *frozen interface surface* it does not own, so
it can dispatch at freeze in parallel with its provider instead of waiting on provider integration. Absent
this key, every surface below no-ops (BC). Edge grammar — dependent-task ⇒ list of `contractId@surfaceHash`
pins:

```yaml
builds_against: { D1: ["C1@<64-hex surfaceHash>"] }
```

- **One contract = one `contracts/<id>/` subdir containing an `__init__.py`** — the `__init__.py` makes the
  import namespace and the dangling-import scan's base-module candidates well-defined. It is
  **sentinel-EXEMPT**: it may be empty namespace glue, and requiring a body-less sentinel there would make
  retirement ambiguous.
- **The PROVIDER owns the contract dir.** It appears in the provider task's `ownership:` (one writer). The
  dependent NEVER writes `contracts/<id>/` — it only imports it.
- **Stub materialization is the plan-guardian's ([[kata-orchestrate]]) job, AT FREEZE, before any worker
  exists:** it commits the contract interface + stub bodies (each bearing the `# KATA-CONTRACT-STUB`
  sentinel) to the integration branch, so dependent worktrees fork with the stubs present. It also computes
  the pin `contract_edges.surface_hash(contracts/<id>)` at freeze, records it in the edge, and commits the
  frozen PLAN to the integration branch **in the same freeze step** — the final gate's bounded scan
  hard-fails on an unresolvable plan fork-point, so the freeze commit is its scan bound.
- **The provider fills real behavior** behind the same import paths in its own worktree, **deleting the
  sentinel lines** (sentinel retirement — the ONLY M1 retirement; whole-dir contract deletion is OUT of
  scope, DESIGN Amendment #2).
- **Edge honesty:** a dependent's test files import ONLY `contracts/<id>/`, never provider impl paths. A
  violation means the edge is really a `depends_on` in disguise — reclassify before freeze.
- **M1-L1 residual:** module constants, `TypeAlias` declarations, and `__all__` are NOT machine-pinned (only
  signatures + return annotations + decorators + defined `def`/`class` names are; re-exports/aliases are NOT pinned) — a contract relying on them is flagged
  for the [[kata-review]] backstop until a later milestone lands the export visitor.

## Version-up ownership (existing-repo runs)

When `target.kind == existing`, the ownership partition's universe is the **footprint**, defined as:
**footprint = modified-files (the files the frozen DESIGN says the feature changes/adds) ∪ the
`marginDepth`-hop reverse-dependents of those files** (over `ref ∪ call` edges; default `marginDepth = 1`,
from `kata.config.graph.marginDepth`). The planner computes the reverse-dependents by inverting the forward
edge list in `kata.graph.json` (built by [[kata-graph]]).

- Files **outside the footprint are off-limits — owned by no task.** This is the structural form of "don't
  break other aspects": a worker physically cannot edit beyond the footprint.
- Pre-owning the depth-1 reverse-dependents puts the common "update a caller of what I changed" case
  in-lane, so it does not trigger an escalation.
- Disjoint-ownership, waves, and the DAG rules are otherwise unchanged.
- The regression contract is enforced at evaluation: the **full baseline suite still green + new feature
  tests green** (gated by [[kata-evaluate]] — no new evaluator).

## Per task

- **owns** — its exact file set (a subset of the partition).
- **read_first** — the DESIGN sections, closest code analogs, and conventions to load before editing.
- **action** — what to build, specifically, tied to the LOCKED decisions (quote them; never paraphrase a
  classification or magnitude — restate verbatim so a worker can't drift).
- **verify** — the runnable, default-FAIL command(s) that prove the task done.
- **acceptance_criteria** — falsifiable checks a fresh-context evaluator can confirm.
- **evidence** *(REQUIRED — see the completion-evidence section above)* — the task's completion-evidence
  declaration(s) in the closed three-form grammar, carried in the PLAN's frontmatter `evidence:` map. A task
  with no declaration **fails plan freeze**; a declaration that does not parse fails it too.
- **estimate** *(OPTIONAL, minutes)* — a per-task time estimate feeding the M4 slack signal (A1-Q3, the
  ledger-median → frontmatter → absent precedence). Omit it freely; a task with no `estimate:` simply falls
  through to the next source. When present it MUST be numeric (minutes) — a present-but-non-numeric
  `estimate:` **fails plan freeze** (freeze-time raise, not a mid-run surprise); the runtime
  `kata_telemetry.resolve_estimate` raise is the second-line backstop.
- **class** *(OPTIONAL, one of `code | research | debug`; default `code`)* — the task's work-class, read by
  [[kata-orchestrate]]'s M4 inline-eval scheduler to select the per-class risk leash + weight table
  (`kata_risk.DEFAULT_TAU` / `kata_risk.DEFAULT_WEIGHTS_BY_CLASS`). Omit it ⇒ `code`. An **unknown value**
  (anything other than the three) **fails plan freeze** (freeze-time raise, not a mid-run surprise — the same
  freeze-gate posture as `estimate:`). `class:` is **never** derived from `runShape` (provenance-only, LOW-14b).
- **complexity** *(OPTIONAL, one of `low | standard | high`; D150/AT-L10a)* — the plan-time low-value
  rating for adaptive tiering: `low` ⇒ the task's build worker STARTS one rung below its L0 resolution
  (floor-clamped; `coding`-class dispatches only; inert unless the run's `models.adaptive` block is
  present with `planComplexityDownshift: true`). This rating is **assessed at plan/grill time and FROZEN
  with the plan** — it is the initiative's one new plan-frozen judgment surface, deliberately attackable
  by the plan freeze-gate (never a runtime LLM value judgment). Omit it ⇒ no effect (BC). An **unknown
  value fails plan freeze** (the `estimate:`/`class:` posture). `high` and `standard` are recorded-only
  in v1 (no upward modulation from this field — bumps come from evidence, AT-L8, never from a rating).

## Dispatch sizing (context autonomy)

Plan/freeze time carries two fail-soft sizing checks over the per-task `estimate:` and the
conductor-authored dispatch brief, both computed off the same arithmetic — `kata_gauge.dispatch_budget`
(the CA-L9 rotation-point + over-briefing engine): rotation point = startup load + the **40pp** work
quantum, clamped by the 0.80 hard cap of the worker window.

- **Freeze WARN (CA-L11).** A **WARN** (never hard-fail) when estimated task burn > the 40pp quantum,
  estimator `[TUNABLE]` tokens-per-chunk seeded from ledger `perTask` medians; the budget line is
  mandatory prose in every dispatch brief (D136 posture: the estimate drives a WARN + split suggestion,
  fail-soft; splitting stays planner judgment). Worker-side observance is **compliance**, not soundness
  (M1-L3); TRUE enforcement is conductor-side ([[kata-orchestrate]] liveness machinery + the M4 kill
  primitive).
- **Freeze mandate (CA-L9).** When **startup load > 0.40** the 40pp quantum is unsatisfiable below the
  0.80 cap (`dispatch_budget` returns `over_briefed`), so the dispatch is **OVER-BRIEFED** and is caught
  at plan/freeze time — split the task or slim the brief, a **mandate, not a WARN**. Startup load = the
  conductor-authored dispatch payload only (brief + packed orientation attachments); worker read-ins
  count toward the worker's own budget, never startup. (Over-briefing also WARNs earlier, at startup
  > 0.30 — the early smell.)

## Quality bar (the invariant — all tiers must meet this)

- Ownership is provably disjoint (no file in two tasks).
- Every LOCKED decision the task implements is quoted verbatim from the DESIGN.
- Every task has a runnable verify and falsifiable acceptance criteria.
- The DAG is acyclic and every task is reachable.
- Any "reuses / composes / already exists" claim in `read_first` or `action` obeys `protocol/reuse-claims.md` —
  the surface is cited with a concrete `file:line`, or the capability is labeled NEW.
- The Dependency Manifest (`kata.dependencies.json`) is present at freeze per `protocol/dependencies.md` (D29);
  the PRE-FLIGHT phase provisions the approved set before `kata-orchestrate` dispatches.
- Any per-task `estimate:` present is numeric (minutes); a present-but-non-numeric `estimate:` **fails the
  freeze** (A1-Q3 freeze-time validation — bootstrap does not validate plans, so the freeze is the gate).
- Any per-task `class:` present is one of `code | research | debug`; an unknown value **fails the freeze**
  (same freeze-time validation gate as `estimate:`).
- **Every task has a grammar-valid `evidence:` declaration** — the whole map round-trips through
  `evidence_grammar.check_evidence_map` without raising. Unlike `estimate:`/`class:` this field is not
  optional: an absent declaration, an unparseable one, or a key naming a non-existent task each **fail the
  freeze** (TM-F1/R-M9 — no plan item freezes without its completion-evidence declaration).
- **No plan task id begins `area:`** — that prefix is reserved for [[kata-orchestrate]]'s M4 per-area
  `failureKinds` attribution convention, so a colliding task id would corrupt closeout attribution; a task id
  starting `area:` **fails the freeze** (re-gate v2 LOW-6).

When these hold, **freeze the plan** and hand to [[kata-orchestrate]].

## Incremental delivery — run the roadmap layer first
When `delivery.shape == "incremental"` (`protocol/config.md`), **before** applying this tier method, run the
**roadmap layer** ([`ROADMAP.md`](./ROADMAP.md), sprint-cadence D85): partition the frozen DESIGN into
prime-frame-sized sprints, emit the roadmap artifact, then apply *this* method at the configured tier to **only
the active sprint's** slice, just-in-time. One-shot delivery (the default) ignores the roadmap layer entirely.
