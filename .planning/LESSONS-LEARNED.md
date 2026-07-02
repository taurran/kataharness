# LESSONS-LEARNED — KataHarness

The kata's memory. Seeded from the CryptoPortfolioPlanner session that birthed this project
(2026-06-05/06) — every one of these is a harness requirement, not a footnote.

- **L1 — Pin line endings (`.gitattributes eol=lf`) from commit #1.** On Windows, `core.autocrlf=true`
  rewrote the working tree to CRLF mid-merge, making a "deterministic" build size drift 259K→266K→270K.
  Build/handoff sizes must be deterministic to be trustworthy signals. *Baked in:* KataHarness shipped
  `.gitattributes` in its first scaffold.
- **L2 — Git worktrees are the right isolation for concurrent code agents.** Building CPP Phase 2 in an
  isolated worktree on a phase branch let work proceed with zero collision against a live `master` in
  another window. *Baked in:* `kata-worktree` is a coordinate-phase primitive.
- **L3 — Shared single-writer state corrupts under concurrency.** Two sessions both wrote `STATE.md` →
  it went stale/contradictory. *Baked in:* single-writer state owned by the plan-guardian + append-only
  board for lateral comms (no last-writer clobber).
- **L4 — Subagents overstep their mandate without structural limits.** A planner subagent committed to a
  research doc mid-run (outside its job). *Baked in:* least-privilege `allowed-tools` in frontmatter
  (evaluators are read-only) + tight task scope — enforce structurally, not by prose.
- **L5 — Default-FAIL + a fresh-context, no-write evaluator earns trust.** The CPP eval caught a real
  blocker the builder missed. *Baked in:* `kata-evaluate`.
- **L6 — Provenance + adversarial validation before findings drive decisions.** An ungated research pass
  (IPO-vacuum) had to be adversarially validated before acceptance. *Baked in:* `source:` frontmatter +
  an evaluate-phase gate before "done."
- **L7 — Converse, don't pop up.** For substantive design decisions, lay out options + a recommendation
  in prose; the human gives richer direction than constrained pickers. (Process note, applies to grilling.)
- **L8 — `kata-grill` must be FAR deeper + GSD-structured, not a one-shot decision list.** Surfaced live
  during the WoZ on CPP Phase 3 (2026-06-06): the manual grill (4 decisions, each "options + a
  recommendation," resolved in a single pass) did **not** meet the bar for this harness's
  planning/discussion phase. The user's explicit spec for the real `kata-grill`:
  - **GSD-format interaction**: questions presented as **selectable multiple-choice the user can click
    through OR answer in plain text** (the AskUserQuestion pattern — structured options *with* a free-text
    escape, which is *compatible* with [[L7]]: options are offered, but typing is always allowed; it is the
    constrained-picker-with-no-escape that L7 forbids, not structure itself).
  - **Far more in-depth and demanding** — iterative, multi-round interrogation that does not stop at the
    first plausible answer; it pushes until the design is *very specific* and genuinely speaks to the user's
    spec. One pass is not a grill.
  - **Refined and user-friendly like GSD** (the discuss/spec-phase UX) **but with the thoroughness, logic,
    and doc-baking of mattpocock `grill-with-docs`** — ground every branch in the source docs, and bake the
    resolved decisions back into a durable design artifact as it goes.
  - **Output bar**: a *very specific final design contract* derived from relentless, doc-grounded
    questioning — not a checklist the orchestrator pre-answered for the user.
  *Baked in:* this is a hard requirement on `kata-grill` (and `kata-context`/`kata-design-doc`) when built
  in v0.1. The WoZ proved the *method shape*; it also proved the **grill step is the weakest link** and is
  the priority to get right. See `[[kata-grill]]`.
- **L9 — Arm A (execution half) ran clean via real subagents; the EXECUTE/COORDINATE skills work.**
  2026-06-06: built the 5 v0.1 execution skills (`kata-orchestrate`/`kata-worktree`/`kata-board`/`kata-tdd`/
  `kata-evaluate`) on Opus, then executed CPP Phase 3 (G_macro) as **Arm A** — orchestrator = Opus (me),
  4 implementer workers + the evaluator = **Sonnet**, in isolated CPP git worktrees off the frozen-spec
  commit, gated default-FAIL. **Result on the frozen `03-DESIGN`/`03-01-PLAN`:**
  - **One-shot to green:** YES — 244 tests (220 baseline + 24), 0 fail/skip; deterministic build (322,511 B);
    Snyk 0. **Zero re-plans.**
  - **Plan drift: 0.** All 4 LOCKED decisions honored verbatim — esp. the sleeve-classification drift-magnet
    (all 11 `macroBucket` exact). Independently re-verified by a fresh-context `kata-evaluate` (9/9 PASS).
  - **Human interventions during execution: 0.** **Escalations: 0** (plan was clear enough that no worker
    needed to escalate). Changes confined to the 11 planned files — no scope creep.
  - **Hygiene held:** disjoint file-ownership → concurrent T2‖T3 worktrees merged conflict-free;
    append-only board, no state clobber ([[LESSONS-LEARNED]] L3 confirmed designed-out).
  - **Notable (good signal):** the T4 worker discovered a real integration gap — `macroBucket` wasn't in the
    `ui.js` `inputs` projection, so the gate would have *silently no-op'd* — and fixed it **in-lane** without
    escalating or drifting, *because the end-to-end test it wrote actually exercised the gate*. Worker scoping
    + behavior-focused tests caught what a shape-only test would have missed.
  - **Caveats:** orchestrator was Opus / workers Sonnet (D13-allowed asymmetry — note in the verdict); the
    grill/plan half was hand-done (the [[L8]] weak link), not skill-driven. **This validates the execution
    half only.** The headline A/B verdict still needs **Arm B** (the user's concurrent GSD run on
    `phase-3/gsd-baseline`) for the one-shot/drift/intervention comparison.
  *Baked in:* the 5 execution skills are `0.1.0/experimental` and proven on a real complex task. Next: get
  Arm B's numbers, then either tie/win → keep; or fold gaps back via `kata-improve`.
- **L10 — A/B VERDICT: TIE. The execution half is on-par with GSD, not better — by the TEST-PLAN's own bar
  the harness did not earn its complexity on this task.** Arm B (GSD baseline) landed green independently:
  246 tests, det build 319,734 B, Snyk 0, gsd-verifier 5/5, **0 drift, 1 in-lane auto-fix, 0 escalations,
  0 interventions** — i.e. **identical objective outcome to Arm A** (244 tests / det build / Snyk 0 /
  kata-evaluate 9/9 / 0 drift / **the SAME 1 auto-fix** / 0 escalations / 0 interventions). TEST-PLAN bar:
  "passes if Arm A reaches green with 0 drift AND *fewer* interventions; a mere tie means it isn't earning
  its complexity." Interventions/drift were EQUAL → **tie, not a win.** *Why, and the lesson:*
  1. **The test froze the spec+plan for both arms, so only EXECUTION was measured** — and both arms' execution
     is the same shape ("dispatch workers per a frozen 4-task plan, gate, verify"). A tie there was near-baked-in.
  2. **Both arms independently hit the identical hidden bug** (`macroBucket` stripped from the call-site inputs
     projection → gate silently no-ops) and **both auto-fixed it in-lane in T4.** That convergence is strong
     evidence the **frozen plan did the heavy lifting**, not the worktree/board/concurrency machinery.
  3. KataHarness's differentiators (true T2‖T3 concurrency, worktree isolation, append-only board) bought **no
     correctness edge** here; the objective metrics don't capture the one axis they'd help (wall-clock/throughput),
     which is also confounded by the orchestrator running on Opus while workers ran Sonnet.
  4. **The harness's real hypothesized value-add is the GRILL/PLAN half** (deep doc-grounded interrogation →
     a better frozen spec) — and that was **hand-done identically for both arms**, so this A/B was structurally
     blind to it. Ties back to [[L8]]: the grill is both the weak link AND the untested differentiator.
  *Baked in:* (a) the **next A/B must VARY the planning step**, not freeze it — that's where differentiation
  lives; (b) building `kata-grill` to the [[L8]] standard is now the load-bearing work, not optional polish;
  (c) we also surfaced a loop gap — only `kata-evaluate` (conformance) ran, not `kata-review` (adversarial);
  **neither arm got adversarial validation at all.** `kata-review` should join v0.1's evaluate phase. See `[[kata-review]]`.

- **L11 — The autonomous grill-vs-baseline A/B tests the wrong axis; the grill is a human-intent alignment aid,
  not a benchmarkable execution edge. (2026-06-18)** We re-ran the A/B with the planning step *varied* (the
  [[L10]] fix): Arm A = `kata-grill`→`design-doc`→`plan`, Arm B = GSD, both autonomous on Sonnet, on small
  Python projects with held-out gates. A pilot (easy `wordfreq`) **tied**; a *hardened* `wordfreq` (interacting
  pipeline, casefold, apostrophe edges, stopword ordering, top-N tie-group) **also near-tied** — both arms
  **4/4 → 10/10 held-out gate passes**, every discriminating metric ~0, the only delta a noise-level
  fix-iteration (A:1, B:2). Arm A's own note: *"no spec ambiguities required human resolution."*
  1. **A fully-specified task — at any difficulty — is built correctly by a capable agent under either method.**
     "Harder" added complexity, not ambiguity; complexity is just more to implement, which both nail.
  2. **The grill's engine is interrogating the *human*. Autonomous mode turns it off** → it degrades to
     "document assumptions," which GSD does too. The A/B was structurally blind to the grill's actual mechanism —
     the same blindness [[L10]] flagged, now confirmed from the other side.
  3. **A deterministic gate cannot hold genuine ambiguity** (one scoreable answer ⇒ subtly-specified, not
     ambiguous). The Nous/Hermes empirical model (execute→judge outcome→distill, no grill) fits *this*
     autonomous/specified terrain better — exactly where our own data keeps saying "tie."
  *Baked in (→ D70/D71/D72):*
  (a) **Retire the autonomous grill-vs-baseline RCT (D70).** What it DID prove — **autonomous reliability** — is
     kept (both methods one-shot correct, gated, lint-clean builds). v0.1 is no longer gated on an RCT.
  (b) **Re-frame grill as an *optional human certainty layer* over the priming prompt (D71)** — depth
     `skip|light|standard|full`; opt-out → the autonomous-reliability floor (default-FAIL + RS + an
     assumption-log surfaced at the gate). Grill adds alignment certainty **by construction**, not by benchmark.
     Grill (up-front, with-human) and **RS** (in-loop, without-human) are the two ends of one ambiguity-resolution
     spectrum. **Stop benchmarking it — the logic carries it.**
  (c) **Grill ledgers are a PRIMARY cognitive-fingerprint feed (D72)** — each grill trains the engram; a matured
     fingerprint pre-answers future grills (D56). Grill earns its keep twice: this project + the learning path.
  (d) **Don't over-engineer the validation.** The instinct to build a "human/oracle-in-the-loop RCT" (D16 v3)
     was *more* apparatus to prove something architectural — dropped. One light in-setting check beats eighteen
     runs. (Anti-pattern: we hardened a corpus + re-registered before realizing the *axis* was wrong — fix the
     question before scaling the measurement.)

- **L12 — The default-FAIL gate trusts derived artifacts; an adversarial second lens that *reproduces* them is
  required, and it must be WIRED, not remembered. (2026-06-24)** WS-2 polish passed `kata-evaluate` 7/7, but a
  separate adversarial `kata-review` (run only because the operator asked) found a real correctness defect: the
  concurrency snippet computed over an un-cleared board, so the committed `concurrency.json` (3 workers) silently
  disagreed with what the snippet actually produces from the on-disk board (8 workers — a prior run folded in).
  The evaluator had **graded the artifact as-presented** — confirmed it was well-formed and matched the plan — but
  never **regenerated it from source and reconciled.** This is the project's **signature failure mode** ("recorded/
  documented but not independently reproduced/executed"), the same class as the D92 documentation-only seams.
  **Sharpest part:** [[L10]](c) had *already recorded this exact lesson* — "only `kata-evaluate` ran, not
  `kata-review`; adversarial validation should join the evaluate phase" — but it was never wired into the loop, so
  it **recurred**. A lesson that lives only in a doc is not baked in. *Baked in (→ D98):*
  (a) **`kata-evaluate` rubric item 9 — "reproduce, don't trust"**: for any *derived* artifact, regenerate it from
     its stated source and reconcile (mismatch ⇒ NEEDS_WORK); for any *claimed seam*, execute it once, don't accept
     the prose. (Primary captured test output stays item 2; this targets second-order artifacts + wiring claims.)
  (b) **The adversarial red-team is now a STANDING loop step** (`kata-orchestrate` Final gate step 6 + recipe
     HANDOFF §5 step 7): on a **code/contract-bearing** build, a fresh-context no-write `kata-review` runs after
     `kata-evaluate` PASS and **before merge** (operator-chosen cadence, 2026-06-24). Two lenses: one grades against
     the plan, one attacks the result. (c) **Meta-lesson: fold lessons into the SKILLS, not just the ledger** — an
     unwired lesson (L10c) is latent debt that resurfaces; `kata-improve` must close the loop to a skill edit.

- **L13 — The D124 thesis held live (D131): a green 2126-test matrix BLESSed two defects that only the live proof +
  D98 adversarial sweep caught. (2026-06-30)** (a) `advanced/coding` applied the coder-floor because the guard wasn't
  gated to `mode=="essential"` — wrong tier for a specific anchor×mode cell. (b) A full-model-id anchor silently
  disabled ALL tiering because the resolver compared an id string against ladder short-name indices. Both defects were
  invisible in the unit matrix, which exercised the **contract** (input→output mapping) but not the **integration seam**
  (resolver output → SDK dispatch call). *Reinforces:* live-proof + adversarial gates are load-bearing, not ceremony.
  *Baked in:* see [[L15]] (seam coverage) and [[L16]] (run-order).

- **L14 — Freeze the DETERMINANT, not just the outcome table. (2026-06-30)** The freeze-gate HOLD on D131 caught that
  the spec described the `step==0`/`step<0` logic by work-class rather than by step-count. The fix was to state the
  deciding variable explicitly ("step-count, not work-class") — not to expand the table. When a resolver has multiple
  plausible interpretations, ambiguity lives in which input *drives* the branch, not in what the branches do; freeze the
  determinant first, the outcomes follow. *Baked in:* spec freeze checklist must confirm the determinant is named, not
  only the outcome rows.

- **L15 — A full matrix test is necessary but not sufficient — treat the resolver→dispatch seam as untrusted until
  exercised live. (2026-06-30)** Unit tests validating a resolver's contract (input→output) will not catch errors in how
  that output is *consumed* by the downstream call-site (wrong field, un-indexed value, type mismatch against an SDK
  enum). For any resolver whose output feeds an SDK or dispatch call, require: (1) unit tests on the contract, AND (2) a
  live dispatch that exercises the full resolver→call path. Treat the seam as untrusted until (2) passes. *Ties to:*
  [[L12]] "execute the seam, don't accept the prose." *Baked in:* integration gate must include at least one live
  dispatch per resolver under test; "green matrix" alone is not a gate pass.

- **L16 — Adversarial sweep (D98) runs AFTER the live proof, not before; the run-order is load-bearing. (2026-06-30)**
  Running D98 before live-proof produces a pure spec audit — it can miss the same integration seams the unit tests
  missed, because it has no concrete failures to anchor the investigation. The live proof surfaces specific, observable
  failures; D98 investigates those failures with full context. Correct gate sequence: integration gate → live proof →
  D98 adversarial sweep. *Baked in:* `kata-orchestrate` Final-gate ordering must list live-proof before adversarial
  sweep on any code/contract-bearing build.

- **L17 — A built feature that isn't signposted at the front door is an unbuilt feature to the user. (2026-07-01)**
  Surfaced live during the first Debug Mode dogfood: a fresh agent driving the harness struggled to
  find and understand Debug Mode because (a) the `/kata` command index, `/kata-start`, and `kata-initiate` never
  named run-shapes at all, (b) the INTENT `kind` enum (`project/research/version-up`) has no `debug`, so the
  "debug run = `kind: version-up` + `target.kind: existing` + `runShape: debug` + module `kata/module/debug`"
  mapping had to be reverse-engineered from `protocol/config.md`, and (c) the bootstrap on-ramp *actively* told
  the agent debug was "execution-pending — describe in prose only, do not wikilink" when it had shipped P1–P3.
  Stale build-status prose in the on-ramp (`kata-bootstrap` SKILL + `run-shapes.md` + the frozen
  `debug-mode/DESIGN.md` header) outlived the build; `README` was refreshed but the config-time surface the user
  actually hits was not. *Ties to:* [[L7]] "converse, don't pop up" (discoverability is a UX property, not just
  a code property). *Baked in:* the front-door command index + `kata-initiate` now name the run-shapes and the
  `kind`↔run-shape mapping; **bump-on-build must refresh status prose across the on-ramp** (`run-shapes.md`,
  `kata-bootstrap` SKILL, spec DESIGN headers), not only `README` — a feature is "done" only when its entry
  point is discoverable, not merely when its code is wired.
- **L18 — A field-run's proposed fix is a hypothesis; verify it against the code before you freeze it. (2026-07-02)**
  Milestone 1 (D137) ingested six fixes (F1–F6) proposed by the agent that ran the Kenjiri one-shot. Fresh-context
  investigators checking each against the actual code found **three of the six proposals were wrong as written**:
  F1's "block on an empty `dependencies` list" would have regressed a first-class, heavily-tested legit state
  (empty-deps ⇒ `ready`) — the real hole was a *malformed* key, not an empty list; F2's "0 ref edges" symptom
  conflated the import-edge bug with a separate name-match heuristic (fix targets import edges only); F4's checklist
  belonged in the language overlay, not the agnostic core. A run that PASSES its own gates still misdiagnoses its
  own fixes — the run's prose is a lead, not a spec. *Ties to:* [[L15]] (treat seams as untrusted), the
  reproduce-don't-trust evaluator rubric. *Baked in:* the plan-freeze step for ingested field-lessons requires a
  code-grounded verification pass **before** the DESIGN LOCKs the fix shape; the LOCKED decision records the
  *reshaped* fix, not the reported one. **Corollary (also this milestone):** the fixes repaired the harness's own
  safety instruments (a vacuous-pass gate, a wrong-scope drift check, the security gate), so they were built
  **directly, not dogfooded** — self-certifying a gate's repair with that same gate is the anti-pattern the
  fresh-context discipline exists to prevent; and indeed both the harness's own sprint-blind test and the WS-A
  adversarial pass each caught a real defect the author's green tests missed.

- **L19 — Unit-reviewed ≠ integration-reviewed: run one fresh-context adversarial sweep over the WHOLE
  merged body of work before wiring anything on top of it. (2026-07-02)** Every Milestone-1 fix and both
  Freeze/Float phases had passed their own build-time adversarial review — and the integrated 9-reviewer
  sweep still surfaced 5 HIGHs, all at SEAMS no unit review owned: a gate consuming a parser's error
  default (`parse_supersede_trailers` `{}` on git error), a shared resolver's blind spot inherited by a
  new gate (`edge_honesty` × relative imports), a scan whose extension filter contradicted the DESIGN's
  language-agnostic claim (`surviving_stubs` × `*.py`), an escalation KIND that self-approved what the
  spine said was human-gated (liveness × `orchestrator-resolvable`), and a git config-dependent diff
  (`--no-renames`). The unit reviews were all honest and all passed honestly — the holes lived between
  the units. Corollary: reviewer prompts must name the ADJACENT seams (what consumes this? what does this
  reuse?), not just the module's own spec.
