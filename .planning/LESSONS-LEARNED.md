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
