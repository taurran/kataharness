---
spec: trust-model
artifact: the detailed pass (operator-directed follow-up to ASSESSMENT.md — "Assess further first")
date: 2026-08-16
status: assessment synthesis — NOT a design, NOT frozen; every OPEN item below is grill-decided
evidence: evidence/promise-audit.md (114 promises) · evidence/cursor-dossier.md (events, fragments,
  resume gaps) · evidence/detectability.md (8-class matrix + gsd-verifier extraction) ·
  evidence/gate-inventory.md (~40 gates + judge stack + plan-grounding)
baseline: grill/dispatch-seam @ fea7ccb (master de8578c) · gauntlet 4/4
---

# THE TRUST MODEL — detailed pass

## 1. The diagnosis, now quantified

The first assessment said "trust is fact where a machine runs, asserted everywhere else." The
detailed pass proves it and bounds it:

- **114 promises audited**: the FACT rows are almost exclusively CI document-integrity checks +
  three fail-soft hooks. ~25 FACADE rows (correct, tested, zero-caller engines described as
  running). **5 FALSE rows** — including `contextTrigger` (the walk-away dial, connected to
  nothing), "workers structurally cannot drift," and a promotion gate "built and
  validator-enforced" that the validator has never heard of.
- **The distribution finding:** the deep protocol layer already tells the truth about itself,
  precisely ("NOT mechanically provable," "prose-gated," "NOT verified and NOT recorded
  anywhere"). The config schema, orchestrate preconditions, and README use machinery vocabulary
  ("wired," "engine-enforced," "LIVE," "structurally," "automatically") for the same dead code.
  **The repo has an honesty register; it is applied in the wrong layer.**
- **~40 completion gates inventoried**: most already have a SEAM artifact to hang a truth-serum
  precondition on. The redesign is dominantly *wiring*, not invention.
- **~106 state-bearing events inventoried**: the durable set (PLAN status enum, `Kata-Task:` /
  `Kata-Checkpoint:` / supersede trailers, `.planning/` docs) is exactly the set restore's
  re-dispatch computation uses — which is why re-dispatch survives a machine change while **every
  counter, every verdict, and every phase fact does not**.

## 2. The eight discoveries that shape the design

1. **The board is already the cursor — for four subsystems.** Fix-loop thrash, M4 ladder,
   adaptive tier spend, and advisor spend all recount from board `DECISION` lines by explicit
   design (each refused a state field). Its deficiencies are exactly three: **no run identity, no
   phase awareness, no push durability.** D135 (board-is-the-trail, no second journal) and D81
   (tier-3 disposable) then *dictate* the cursor's shape: **upgrade the board and fold over it +
   the trailers + tier-2 — never build a parallel journal.** "Modernized graph manner" =
   the graph is a *projection* built from this one log (aligned with kata.graph/BL-N16), not a
   second source of truth.
2. **Every judgment verdict is undurable by construction — and that decides who writes verdicts.**
   Judges are no-write precisely so they cannot rubber-stamp; therefore no PASS/NEEDS_WORK/SHIP/
   HOLD exists as an artifact anywhere (mid-gate resume must re-run the whole gate; kata-debrief
   must print "verdict pending"; BL-N19's mechanical re-loop has nothing to route on). The
   resolution is EDR-1 arriving from the durability direction: **the dispatcher is the witness —
   the seam that dispatches a judge persists its verdict.** Seam and cursor are therefore one
   design, not two: the seam mints what the cursor records.
3. **The plan-grounding close is one set-difference over data that already exists.**
   `parse_plan_tasks` yields the authoritative plan task set; `Kata-Task:` trailers map every
   integration commit to its task; DEFERRED.md holds the legality records. Nothing joins the
   three. The registry-vs-tree pattern is proven twice in-repo (protocol-folder registration;
   gsd's ORPHANED requirements). Anti-drift/anti-spiral at close = this join + "every artifact
   maps to a plan anchor or a recorded deferral, else named drift."
4. **Truth Serum's mechanical floor is real but bounded — and the burn-02 record proves the
   bound.** MECH today-or-cheaply: stub-body syntax (AST predicate over tree-sitter spans we
   already generate), silent deferral (the three-way join), stale evidence (`evidence_is_current`,
   wired nowhere that matters — BL-X11), citation existence, debt-marker-without-`DEF-*`.
   SEMI: unwired detection (the graph's ref edges are call-only, bare-name, fabricated-src — the
   orphan layer T6–T11 is a ready calibration corpus), test vacuity (whole-test mutation proof
   cannot see dead parametrization legs — the exact shipped defect). JUDG: label-follows-claim,
   stub legitimacy. **And the meta-finding: in burn-02 the automated gates found zero of the live
   defects; judgment found all.** Truth Serum narrows and attests; it does not replace the judge
   stack — it feeds it facts and refuses gates that lack them.
5. **Every detector needs the anti-vacuous-check companion** (the producer-existence-guard
   pattern: a check that refuses to certify over zero inputs / absent preconditions), or Truth
   Serum's green becomes the newest facade. Three in-repo precedents exist; kata-validate's
   tripwire (prove-you-can-still-fail over a known-bad corpus) is the only meta-gate in the
   harness and should become standard equipment for every judge.
6. **The deferral ledger — PD-1's own sanctioned path — is the least machine-checkable artifact
   in the harness.** No pinned path, no schema, no approval field, not protocol-guarded;
   ASSUMPTIONS.md has zero instances ever. gsd's override record (`{must_have, reason,
   accepted_by, accepted_at}`, counted separately) is the shape that answers BL-N01's open
   question "where does approval get recorded so the gate can check it."
7. **Two standing contradictions need operator rulings, not grills:** (a) `kata.config` and
   `INTENT.md` are gitignored while `protocol/state.md:41` calls them tier-1 "(git)" — under a
   machine change the resumer loses the run's goal and entire configuration; (b) the honesty
   register: the FALSE/FACADE labels in config.md/README ("wired," "engine-enforced," "LIVE")
   violate PD-2 *today* and can be fixed by relabeling immediately, independent of any build —
   or left until wiring makes them true. Which rows get wired vs. relabeled is a scope ruling.
8. **gsd-verifier's reusable assets are five, and none is its code** (the binary isn't here; it
   lives at `~/.claude/agents/disabled/`, not the path BL-N01 cites): the check taxonomy
   (exists/substantive/wired + data-flow), the probe-execution rule ("narration is not evidence —
   run it in your own process"), the debt-marker/`DEF-*` legality gate, the signed override
   record, and the ORPHANED set-difference.

## 3. The program, restated with the evidence attached (seven components)

```
(1) SEAM (M33/M34)      — every dispatch is a code act; mints run-id; persists judge verdicts
                          (discovery 2); the freeze chokepoint finally gets a caller
(2) CURSOR              — the board, upgraded: run-id + phase events + verdict records +
                          push-durable trail; graph views are projections (discovery 1);
                          resolves the resume blindness (mid-grill/mid-gate/mid-closeout) and
                          BBM-12's wave accounting; D81/D135-compliant by construction
(3) TRUTH SERUM (N01)   — the detector bank per the 8-class matrix (discovery 4), every
                          detector with its anti-vacuity companion (discovery 5); deferral
                          legality needs the schema'd ledger + approval record first
                          (discovery 6)
(4) GROUNDING AGENT     — new cadre role; orchestrates engine-run comparisons (grounding_gate
                          finally wired); the challenger's execute-the-tooling duty (AC-10)
                          generalized; agent proposes, engine attests
(5) GATE PRECONDITIONS  — per the gate inventory: most gates get a fact-artifact requirement on
                          an EXISTING seam; the named holes get artifacts (persisted verdicts,
                          per-task gate record, convergence-pass record); evidence_is_current
                          wired into every evidence consumer (BL-X11 class closed)
(6) PLAN-GROUNDING CLOSE — the three-way join (discovery 3): plan ⋈ trailers ⋈ DEFERRED;
                          additions without an anchor = named drift; a failed grounding is what
                          BL-N19's re-loop routes on
(7) PRESENTATION LAYER  — operator-directed 2026-08-16 (second sitting): Truth Serum's effects
                          are SHOWN to the user — the hard truthfulness line demonstrated at
                          work, so output and results are trustable for projects and research
```

### Component 7 — the Truth Serum presentation layer (new, operator-directed)

The directive: it is not enough that the line exists — the user must **see** it working, so trust
in the harness's validation and in the output itself is earned by demonstration, not asserted.

Evidence-grounded seeds (all already ruled or built, none yet composed into this):
- **The run-start truth-serum box is already a ruled UX element** (UX-16/19/20: run-start states
  what is in AND explicitly NOT in this run). Component 7 extends it from a run-start moment to a
  run-long surface.
- **The UX grammar already separates data from prose** (boxes = data, dividers = prose, UX-15/18):
  fact tables are boxes — a mechanical check's output renders as data the user can see was
  *computed*, visually distinct from narrative.
- **The quote-verbatim-never-recompute discipline** (kata-report's verdict badge, kata-debrief's
  gate counts) is the presentation-side twin of evidence identity — extend it: every displayed
  fact carries its provenance (which check, which artifact, which SHA).
- **Honesty labels already have house style** (n=1, modeled, "exercised-not-proven") — the
  presentation layer is where they *travel to the user* mechanically instead of by author
  discipline (detectability class h).
- Natural surfaces, per the existing loop UX: gate moments (the fact table + what was REFUSED and
  why — a visible refusal is the strongest trust demonstration), the closeout chain of custody
  (every plan item → built/wired/exercised with its evidence pointer; drift named; deferrals with
  their approval records), and the trust ledger itself as a per-run user-facing artifact (what was
  mechanically verified vs. judged vs. taken on faith — the run's own T1–T18 table).
- **Honest-limit rule for this layer:** the presentation must show judgment as judgment and fact
  as fact — a UI that paints judge opinions in fact clothing would recreate the facade one layer
  up (the same failure the promise audit found in prose). The presentation layer inherits PD-2.

OPEN (grill decides): which surfaces (run-start / per-gate / closeout / report), what the fact
table's canonical render is, how refusals are shown, whether the per-run trust ledger is a
standing report section — and its dependency edge on the UX freeze (the UX system is at
freeze-candidate, waiting ONLY on the operator's sign-off; component 7 lands as a UX-system
citizen, not a parallel grammar).

## 4. What this changes about sequencing (assessment, not a ruling)

The evidence collapses two items into one and adds two cheap immediates:

- **The seam grill and the cursor are one grill.** Discovery 2 makes them inseparable (the seam
  writes what the cursor holds; the cursor is the seam's memory). The in-flight dispatch-seam
  grill should absorb the cursor as its B3, expanded.
- **Truth Serum (N01) grills second**, consuming the matrix + the deferral-schema decision; gate
  preconditions (5) and the plan-grounding close (6) are its enforcement and terminus rather than
  separate items; N19's re-loop routes on (6)'s verdict artifact.
- **The grounding agent joins the cadre grill (N20)** with AC-10 as its charter; the presentation
  layer (7) grills with-or-after the UX freeze (operator gate already standing).
- **Cheap immediates needing only rulings, no build:** (a) the honesty relabel — fix the FALSE
  rows and the machinery-vocabulary FACADE labels now (PD-2 on ourselves; restores prose trust
  before any wiring lands) or explicitly defer them to be made-true-by-wiring; (b) the
  tier-1/gitignore contradiction ruling; (c) BL-X11 (`evidence_is_current` into kata-evaluate's
  machine-input step) is a doc-seam fix already filed — it becomes urgent under this program.

## 5. Honest limits (carried forward, plus one new)

All four ASSESSMENT.md limits stand (entry residual; grounding agent is a model — engine attests;
judgment stays judgment; anti-cathedral: the cursor consolidates the never-written artifacts, it
does not add beside them). New, from the evidence: **detector humility** — the burn-02 record
proves the mechanical layer missed everything the judges caught; Truth Serum's claim is "no
unattested fact enters a gate," never "no defect escapes." Present it that way too (component 7
inherits this label).
