---
spec: trust-model
artifact: assessment (operator-directed 2026-08-16 — "Assess.")
date: 2026-08-16
status: assessment — NOT a design, NOT frozen; the grill decides everything below marked OPEN
provenance: operator directive mid-dispatch-seam-grill (verbatim intent recorded in
  specs/dispatch-seam/GRILL-LEDGER.md, operator-directive block); ground truth from
  specs/dispatch-seam/SURFACE-MAP.md + three conductor spot-verifications this session
  (grounding_gate.py orphan status · no grounding role in the agent-cadre roster · the
  BBM cursor ruling at backlog-burn-mode/GRILL-LEDGER.md:117-124)
---

# THE TRUST MODEL — assessment

**The operator's charge, in plain terms:** the harness is a facade wherever its promises rest on a
model obeying prose. Tie the engine and the prose together; wire in Truth Serum; track everything
at the cursor as a temporal, graph-shaped record so interrupted runs actually resume; put specific
blocks against stubs, deferrals, and omissions; put ground truth inside the grounding/validation/
eval stack (including a grounding AGENT, which the roster lacks); make every completion gate
require a truth-serum check; and end every run by grounding everything against the plan to kill
drift and spiraling. Goal: **TRUST in every mechanism AND trust in the output — backed by fact.**

## 1. The trust ledger — where trust is fact today, and where it is a costume

Verdicts: **FACT** = a machine runs the check · **PARTIAL** = mechanism exists, reach incomplete ·
**PROSE** = rests on model obedience · **FACADE** = machinery exists and is advertised, nothing
runs it · **ABSENT** = no mechanism and no machinery.

| # | Trust claim the harness makes | What backs it today | Verdict |
|---|---|---|---|
| T1 | Protocol contracts cannot be silently inverted (KH-T02 fix) | clause-pins + fingerprints, run by validate_skills in the gauntlet | **FACT** |
| T2 | Skill versions bump on modify; schemas valid; model: forbidden in core | validate_skills, gauntlet | **FACT** |
| T3 | Judges cannot write | `allowed-tools` frontmatter, structural | **FACT** |
| T4 | Context gauge checked every turn | UserPromptSubmit hook (fail-soft) | **FACT** (advisory by design) |
| T5 | Board survives compaction | PreCompact hook commits board to `refs/kata/trail` | **FACT** — the only wired durable run record in the harness |
| T6 | Nothing builds from a draft (D169) | `assert_frozen` inside `build_brief` — zero production callers | **FACADE** |
| T7 | Host-only roles never route off-host; roles fail-closed at preflight | `resolve_roles`/`HOST_ONLY_ROLES` — zero callers; preflight never calls it | **FACADE** |
| T8 | The contract gate ran | `contract-gate.json` producer-only; zero ever written in a real run | **FACADE** |
| T9 | Runs are accounted (telemetry, counters, ledger rows) | 71 KB engine, zero callers; burns produced zero rows | **FACADE** |
| T10 | Runs survive interruption / lost runs are recoverable | `detect_lost_run`/`restore`/`fold_board` — zero callers; no run-id anywhere; `state.json` never written in a live run | **FACADE** — "which we were supposed to have already" is correct |
| T11 | Research claims are grounded before credited | `grounding_gate.py` engine (GROUND/REJECT/ESCALATE) — test-only callers; the gate step is prose | **FACADE** (engine) / **PROSE** (step) |
| T12 | Judges run from a fresh context | dispatch convention — honestly labeled as unverified since EDR-7 | **PROSE** (honestly so) |
| T13 | The plan does not drift; workers never re-plan | prose + gate judgment | **PROSE** |
| T14 | Every run uses the entire loop (BBM-12) | prose; bypassed live twice, operator-caught | **PROSE** — the proven breach |
| T15 | Gate evidence is current, not stale | `evidence_is_current` exists and is real — wired only into benchmark/debug; the evaluator is not pointed at it (BL-X11); a July artifact was read raw at the burn-02 final eval | **PARTIAL** |
| T16 | Done = built + wired + exercised (PD-1/PD-2) | prose contract + judge judgment; `contract_edges.surviving_stubs` exists unwired; no stub/omission detector runs anywhere | **PROSE** / **ABSENT** (the Truth Serum hole) |
| T17 | Learning fed to the vault is faithful | `learn_feed` emits OPEN questions as RESOLVED decisions (BL-X12, challenger-proven) | **BROKEN** — worse than absent: wrong output presented as fact |
| T18 | The prose cites real code | five skills cite stale `kata_dispatch` line anchors; `kata-tdd` references a nonexistent `tools/my_task.py` | **BROKEN** (drift between layers, unchecked) |

**The pattern is exact, and it is the whole assessment in one sentence: trust is FACT precisely
where a machine runs at check-time (the gauntlet's document checks, the three hooks), and PROSE or
FACADE everywhere execution happens — because nothing mechanical runs inside the loop.** The
harness has a working immune system for its *contracts* and none for its *behavior*. The trust
model program is: make a machine run at every point where trust is currently asserted.

## 2. The operator's six components — how they tie together as one control loop

They are not six features. They are one chain of custody from intent to output, each link
consuming the previous link's facts:

```
frozen PLAN/INTENT
      │
  (1) THE SEAM — every dispatch is a code act (M33) that a bypass cannot imitate (M34);
      the seam MINTS run identity and stamps every launch
      │
  (2) THE CURSOR — the seam's memory: one durable, temporal, graph-shaped run record;
      every seam event (dispatch, gate, ruling, phase move) appends a node;
      interruption resilience = replay the cursor, not branch archaeology
      │
  (3) TRUTH SERUM — the fact extractor (N01): mechanical detectors over returned work —
      stub scan, unwired-symbol scan, exists/imported/used-beyond-imports artifact levels,
      data-flow trace (gsd-verifier prior art; contract_edges.surviving_stubs is a seed) —
      emitting a FACT TABLE stamped to the cursor. This is the specific block against
      stubs, deferrals, and omissions: a deferral is legal ONLY as a recorded kata-defer
      entry the fact table can see; an unrecorded gap is a detected violation
      │
  (4) THE GROUNDING AGENT — new cadre role (confirmed missing from the roster):
      attests CLAIMS against FACTS before any judge credits them. Its engine exists
      (grounding_gate.py, orphaned). Design law: the agent is still a model — only its
      ENGINE-RUN comparisons are facts. The agent orchestrates checks; the engine attests.
      AC-10 ("validators execute the tooling") generalized into a standing role
      │
  (5) GATE PRECONDITIONS — no completion gate (task gate, wave gate, final eval, grill
      convergence, closeout) may return PASS without a seam-minted truth-serum fact
      artifact for the thing it grades. Same shape as D169: the gate REFUSES, never warns.
      Judgment stays judgment — but it must judge on attested facts, not on the worker's
      account of itself
      │
  (6) PLAN-GROUNDING AT CLOSE — the anti-drift/anti-spiral terminus: before a run may
      close, a mechanical prompting step re-derives promised-vs-built from the frozen
      plan — every plan item mapped to fact (built / wired / exercised per Truth Serum),
      every artifact mapped back to a plan item or to a recorded deferral/escalation.
      Additions with no plan anchor = named drift. Spiraling shows up as the diff.
      │
trusted OUTPUT — with its chain of custody attached
```

**"Trust in every mechanism" and "trust in the output" are the same chain proved twice:** mechanism
trust = every step demonstrably ran through the seam and is on the cursor; output trust = every
claim about the output resolves to an attested fact on the same record.

## 3. What already exists to build on (verified seeds — do not reinvent)

| Component | Existing seed | State |
|---|---|---|
| The seam | `kata_dispatch` (+ `assert_frozen` chokepoint) | built, tested, orphaned |
| The cursor | `refs/kata/trail` (PreCompact already commits the board there — WIRED); `Kata-Task:`/`Kata-Checkpoint:` trailers (git-durable, strict regexes); `kata.graph.json`/graph_gen (the graph substrate); the BBM cursor ruling + BL-N16 substrate alignment | fragments exist; one is even wired; no unified record |
| Truth Serum | `contract_edges.surviving_stubs`; gsd-verifier's 7-step protocol (mined per BL-N01's note, not reinvented) | seeds only |
| Grounding agent | `grounding_gate.py` (verdicts, `build_verdict`, `write_grounding`) | engine built, orphaned; role absent from roster |
| Gate preconditions | `evidence_is_current` (extend SHA-freshness → run-membership); the D169 refuse-never-warn shape | partial |
| Plan-grounding | plan frontmatter enum + `parse_plan_tasks`; the closeout's goal-anchored report (prose today) | fragments |
| The trust philosophy itself | validate_skills' clause-pin/fingerprint pattern — the in-repo PROOF that mechanical trust works | fact — extend from documents to execution |

## 4. Honest limits — what cannot be mechanized (stated, per the EDR-5 house style)

1. **Entry is the outermost residual.** The seam governs every run that enters it; a session that
   never invokes the harness at all is host-config territory (BL-N21's wrapper/always-loop is that
   layer's answer). State it in the contract; do not pretend the seam closes it.
2. **A grounding agent is a model.** Its trust derives entirely from engine-run comparisons. Any
   design where the agent's *opinion* is the artifact recreates the facade one level up.
3. **Judgment gates stay judgment.** "Is this good work?" is not mechanizable; "is this claim
   about the work true?" largely is. The trust model constrains judges to attested inputs — it
   does not replace judging.
4. **The validator's own source remains undefended** (the recorded KH-T02 residual). The trust
   model raises the cost and visibility of switching protections off; it does not make it
   impossible. Same honest clause travels here.
5. **Anti-cathedral check:** D172 relaxed minimal-Python for exactly this domain, but the cursor
   must CONSOLIDATE the scattered `.kata/` artifacts nobody writes (state.json, contract-gate.json,
   telemetry rows) into one record — not add a parallel bureaucracy beside them.

## 5. Trust surfaces the directive did not name (completeness — all in scope of "trust in output")

- **BL-X12** — the learning emitter's wrong-output defect (OPEN → "resolved"): a trust breach in
  the learning path; MUST be inside the trust model's fence, not beside it.
- **BL-X11 / T-04 class** — evaluators not routed through the identity check: stale-evidence trust.
- **Prose↔code citation drift** (stale line anchors, phantom files): trust in the prose itself; a
  citation-resolver is a cheap Truth Serum leg with outsized honesty yield.
- **Honesty labels** (n=1, modeled, unproven legs) — PD-2's traveling labels are gate-graded prose
  today; the fact table can carry them mechanically.

## 6. Program shape (assessment + recommendation; the decision is the operator's)

This is **one program, not six items**: the backlog already contains its spine in dependency order
(🔴 M33 seam → 🔴 M34 guard → 🔴 N01 Truth Serum → N19 re-loop → N20/cadre), and the directive adds
the connective tissue those items were each missing a piece of: the **cursor** (M33's run-identity
branch B3, generalized to the temporal graph record; subsumes BL-N14 run-statistics as views over
it), the **grounding agent** (a roster addition inside N20's cadre program + the wiring of
grounding_gate), **gate preconditions** (the enforcement half of N01, landing at every gate), and
**plan-grounding at close** (composes with N19's re-loop: a failed grounding is what a re-loop is
FOR). BL-X11 and BL-X12 fold in as trust-breach fixes.

**Recommendation:** record the Trust Model as the program-level DESIGN target (this spec dir), and
keep the dispatch-seam grill in flight as its phase-1 spine — re-framing its tree under the trust
model: B3 becomes the cursor branch; B4/B5 gain the gate-precondition scope; the grounding agent
and plan-grounding get their own branches here or in the N01/cadre grills, whichever the operator
prefers. The execution-core order survives intact; the trust model is its unifying contract, not a
re-order.
