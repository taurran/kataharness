---
spec: trust-model
item: "The Trust Model — one unified grill (operator-ruled 2026-08-16): the seam (BL-M33/M34) + the cursor + Truth Serum (BL-N01) + the grounding agent + gate preconditions + the plan-grounding close (feeds BL-N19) + the presentation layer"
status: draft
opened: 2026-08-16 (absorbs specs/dispatch-seam/GRILL-LEDGER.md, opened same day — its Phase-0 grounding and B1–B11 tree carry over as input; supersede-never-rewrite)
baseline: master `de8578c` → branch grill/dispatch-seam @ dcdd1b2 · gauntlet 4/4 (pytest 4518)
tier: kata-grill-advanced (enforcement-critical, architecturally load-bearing; double convergence pass + dedicated security/edge-case pass)
target: CODEBASE (dev source, operator-selected this session)
---

# GRILL LEDGER — the Trust Model

**In plain terms:** the harness makes ~114 promises and machines keep only the document-layer
ones; execution runs on model obedience to prose, and both Backlog Burns proved obedience fails.
This grill designs the one program that moves trust from obedience to code: every agent launch
becomes a code act (the seam), every run event lands on one durable temporal record (the cursor),
every completion gate refuses work without attested facts (Truth Serum + preconditions), claims
are attested against ground truth before judges credit them (the grounding agent), every run
closes by grounding the output against the frozen plan (the close), and the user **sees** the
hard line working (the presentation layer). Goal, operator-verbatim: *"TRUST in every mechanism
within the harness/loop, but also trust in the output itself… actually back trust with
fact/truth."*

## Phase 0 — grounding (complete; four dossiers + two assessments + the absorbed seam ledger)

| artifact | what it grounds |
|---|---|
| `../dispatch-seam/SURFACE-MAP.md` | 12 dispatch surfaces · 10 orphaned enforcement primitives · 6 verified absences · 4 authority attach points · blast radius |
| `../dispatch-seam/GRILL-LEDGER.md` | the absorbed seam grill: its Phase-0 answers (not-an-agent / not-a-skill / engine-code per D172) + operator directives recorded verbatim |
| `ASSESSMENT.md` | the trust ledger T1–T18 · the control-loop chain · seeds · limits |
| `DETAILED-PASS.md` | the 8 design-shaping discoveries · the 7-component program · sequencing |
| `evidence/promise-audit.md` | 114 promises: FACT/PARTIAL/PROSE/FACADE/FALSE, the honesty-register distribution finding |
| `evidence/cursor-dossier.md` | ~106 events · fragment inventory · D81/D135 verbatim · per-interruption-point resume gaps |
| `evidence/detectability.md` | the 8-class MECH/SEMI/JUDG matrix · gsd-verifier extraction · anti-vacuity law · deferral-ledger audit |
| `evidence/gate-inventory.md` | ~40 gates with SEAM/NEW markers · judge-stack independence audit · plan-grounding current state |

Binding rulings carried: D172 (engine code, deterministic, fail-closed) · D169 (freeze blocks) ·
D81/D135 (cursor = board upgrade + fold, never a new journal; authority never lives in `.kata/`) ·
EDR-7 (disk-readable tokens are forgeable; the dispatcher is the witness) · BBM-12 (entire loop,
wave-per-loop) · BBM-11 (headless never blocks) · AC-1/AC-10/AC-11 (cadre loads via the seam;
validators execute the tooling; challenger steps up) · thin-orchestrator (spine #8) ·
UX-15/16/18/19/20 (the grammar + the ruled run-start truth-serum box) · PD-1/PD-2 (the contract
this program mechanizes).

## Operator directives of record (this session, verbatim intent — see the absorbed ledger for full text)

1. Tie the engine and the prose together — the facade ends.
2. Truth Serum wired in as part of it (BL-N01).
3. Everything tracked at the CURSOR — temporal, interruption-resilient, "modernized graph manner."
4. Specific blocks against stubs, deferrals, omissions.
5. Ground truth inside the grounding/validation/eval stack — including a **grounding agent** (roster gap confirmed).
6. No completion gate passes without a truth-serum check.
7. An end-of-run mechanism grounding everything against the plan (anti-drift, anti-spiraling).
8. **The presentation layer** (second sitting): demonstrate the hard truthfulness line AT WORK to the user — trust in output and results, shown not asserted.
9. **One unified grill** (this ledger): one tree, one double convergence gate, one DESIGN.

## The decision tree (initial derivation — Advanced: re-derived after every resolution, to exhaustion)

### A — standing rulings (operator calls, posed in-grill)
| # | branch | status |
|---|---|---|
| A1 | The honesty relabel — the 5 FALSE + ~25 FACADE promise rows: relabel now (PD-2 immediately true) vs. wire-then-true vs. split | OPEN |
| A2 | The tier-1 contradiction — `kata.config`/`INTENT.md` gitignored vs. `state.md:41` "(git)": commit them, or re-tier and fix the doc | OPEN |

### B — the authority spine (the seam; absorbs dispatch-seam B1/B2/B4/B5/B8)
| # | branch | status |
|---|---|---|
| B1 | The authority architecture — which composition of the four attach points (engine-door · host-hook interception · wrapper door · post-hoc verification) IS the seam; phasing | OPEN |
| B2 | The Claude-host enforcement mechanism — hook-intercept fail-closed vs. headless-CLI routing vs. mint+verify only; capability probes (never assumed) | OPEN |
| B3 | Seam scope — which of the 12 dispatch surfaces MUST route through it ("everything the harness does," made precise) | OPEN |
| B4 | The dispatch record — contents (brief, role, model, plan ref, run-id, ticket) + the EDR-7 forgery analysis per field | OPEN |
| B5 | Bypass semantics — unblessed dispatch: block vs. escalate; BBM-11 unattended shapes; non-kata sessions untouched (kata_scope) | OPEN |

### C — the cursor (absorbs dispatch-seam B3; discovery 1+2 constraints locked)
| # | branch | status |
|---|---|---|
| C1 | Cursor shape — the board upgrade concretely: run-id + phase into the grammar? new TYPEs? (board.md is clause-pinned — deliberate two-step re-approval) vs. sidecar structured log folded with the board | OPEN |
| C2 | Run identity — minting (seam, at run start), format, where it stamps (board lines, artifacts, reports path), `evidence_is_current` extended to run membership | OPEN |
| C3 | Push durability — `refs/kata/trail` never pushes today; survive machine-change (iv) or accept local-git durability; what else the trail snapshots (board-only today) | OPEN |
| C4 | Verdict persistence — the dispatcher-as-witness records for evaluate/review/slop/inline/convergence verdicts (judges stay no-write); schema; where they live | OPEN |
| C5 | The phase model — which loop phases become recorded states (mid-grill/mid-freeze/mid-closeout are blind today); closeout Decisions 1–4 as structured records (backout-approved-unexecuted is the highest-stakes gap) | OPEN |
| C6 | The graph manner — the cursor's graph projection: alignment with kata.graph/BL-N16 substrate; views (rail, statistics BL-N14) as folds, never second sources | OPEN |
| C7 | *(opened by the operator's C3 directive — re-derivation)* Parallel/branched fan-out + Kitchen async: how the cursor models concurrent arms and async processes — one cursor per run in a linked tree vs. shared multi-writer | OPEN |

### D — Truth Serum (BL-N01)
| # | branch | status |
|---|---|---|
| D1 | The deferral ledger hardening — pinned path, schema, `accepted_by/accepted_at` approval record (the gsd override shape), protocol-guard status; ASSUMPTIONS.md same | OPEN |
| D2 | Detector set v1 — which of the 8 classes ship first; the Python stub-body AST predicate over tree-sitter spans; the T6–T11 orphan corpus as calibration; unwired-detector honesty (SEMI, not MECH) | OPEN |
| D3 | Anti-vacuity companions + the meta-gate — every detector refuses zero-input certification; tripwire (prove-you-can-still-fail) generalized to the judge stack | OPEN |
| D4 | Gate preconditions map — per the inventory: which gates gain which fact requirements; refuse-not-warn semantics; the named NEW artifacts (per-task gate record, convergence-pass record) | OPEN |
| D5 | Evidence identity everywhere — `evidence_is_current` into every evidence consumer (BL-X11 class); the RESULT parsed-counts fix interplay (BL-X13) | OPEN |

### E — the grounding agent + judge stack
| # | branch | status |
|---|---|---|
| E1 | The grounding agent charter — engine-attested comparisons only (agent proposes, engine attests); wiring `grounding_gate`; its place in the cadre roster + AC-10 duty; scope vs. the challenger | OPEN |
| E2 | Judge-input contract — judges consume attested fact tables; what remains legitimately judgment (detector humility stated) | OPEN |

### F — the plan-grounding close (feeds BL-N19)
| # | branch | status |
|---|---|---|
| F1 | The three-way join — plan ⋈ trailers ⋈ DEFERRED mechanics; "every artifact maps to a plan anchor or a recorded deferral, else named drift"; behavioral-deliverable handling | OPEN |
| F2 | Re-loop routing — the close's verdict artifact as what BL-N19's mechanical NEEDS_WORK→re-loop routes on; wave-level (BBM-12) vs. run-level | OPEN |

### G — the presentation layer (component 7)
| # | branch | status |
|---|---|---|
| G1 | Surfaces — run-start truth-serum box extension · per-gate receipts (incl. visible REFUSALS) · closeout chain of custody · the per-run trust ledger as a user-facing artifact | OPEN |
| G2 | Rendering law — fact-vs-judgment visually distinct (boxes=data grammar); provenance on every displayed fact (quote-verbatim discipline); PD-2 inherited (no fact-clothing on opinions) | OPEN |
| G3 | UX-freeze dependency — lands as a UX-system citizen; sequencing against the standing operator sign-off gate | OPEN |

### H — cross-cutting
| # | branch | status |
|---|---|---|
| H1 | Migration — ~52 launch sites in kata-orchestrate + the dispatched-skill inbound contracts; rewrite order; what stays true mid-migration | OPEN |
| H2 | Degradation honesty — hosts without interception; engine unavailable; loud degraded modes (the kill-binding precedent); the honest residual stated in the contract (EDR-5 style) | OPEN |
| H3 | Backlog mapping — what this DESIGN closes (M33, M34, N01, N19-route, X11; N14-as-views) vs. feeds (N16, N20, N21, UX) | OPEN |
| H4 | Security pass (Advanced mandate) — forgery, brief injection, hook trust, the validator's-own-source residual, redaction | OPEN |

## Resolved branches

### TM-B1 — The seam is all four attach points, layered · LOCKED

- **Decision (operator, 2026-08-16):** the seam's authority architecture composes ALL four attach
  points, layered: (1) **the engine is the only door** — every dispatch is a function call that
  mints/validates run context, wiring the orphan layer (freeze chokepoint, roles, models, board,
  roster) in one move; (2) a **fail-closed Claude-adapter hook** intercepts bare `Agent`-tool
  dispatches at the host boundary; (3) **post-hoc identity verification at every gate** audits
  the chain; (4) **the wrapper door defers to BL-N21** as the outermost layer, later.
- **Rejected — engine + post-hoc only:** host-independent and simplest, but the bypass class
  survives as detectable-not-preventable; both burns showed in-the-moment prose bypass is the live
  failure, and detection-after was exactly what the operator had to do by hand.
- **Rejected — hook-first with a minimal engine:** blocks at the boundary but leaves the orphan
  enforcement layer (roles/models/freeze) unwired — the facade would persist behind a guarded
  door.
- **Rationale:** defense in depth; each layer covers the others' blind spot (engine = authority +
  wiring; hook = in-the-moment blocking on the host; verification = host-independent audit;
  wrapper = launch invariant). EDR-7 satisfied: all four sit on the dispatcher's side.
- **Provenance:** SURFACE-MAP §5; DETAILED-PASS discovery 2; the two live bypasses (BL-M34);
  EDR-7.

### TM-B2 — Hook-guarded Agent path on Claude; interception is an abstract per-host capability · LOCKED

- **Decision (operator, 2026-08-16, accept-with-modification: "fine with option 1, but we need to
  consider codex, kiro, and other harnesses"):**
  1. **Claude host:** workers stay on the in-process `Agent` path (host-native statusline, kill
     binding, background management). The engine mints the dispatch record FIRST; a new
     **PreToolUse-class hook fail-closes any `Agent` call lacking a valid record**. The hook
     capability probe is an explicit early task (UX-28 discipline: assess, never assume). This
     deliberately breaks the all-hooks-fail-soft precedent — scope-gated to kata runs via
     `kata_scope` so non-kata sessions are untouched.
  2. **CLI platforms (codex/kiro) — the operator's modification:** their workers already launch
     through engine code (`_COMMAND_BUILDERS` → subprocess) when sanctioned — but a conductor
     with Bash can shell `codex exec` / `kiro-cli chat` raw. **The same hook layer therefore also
     guards raw CLI worker launches through Bash on a Claude conductor** (match the dispatch
     command shapes, require the record). One interception surface, two guarded doors.
  3. **Other harnesses as HOST (conductor runs on kiro/codex/etc.):** "dispatch interception" is
     an **abstract adapter capability**; each adapter binds it natively (Kiro: its PreToolUse
     equivalent, risk-flagged per PLATFORM-MATRIX issue #5527 — assess; Codex: assess). A host
     with NO interception primitive runs engine + post-hoc-verify only and **degrades LOUDLY**
     (the kill-binding precedent: surfaced, never silent) — its runs are
     detectable-not-preventable and say so.
  4. **The enforcement level is declared in the run-start truth-serum box** ("enforcement:
     intercepting / detection-only") — the first concrete G1 presentation-layer element, born
     from this branch.
- **Rejected — route Claude through a CLI builder:** abandons the proven in-process model; `-p`
  verifiably degrades the statusline; loses the host kill binding the M4 ladder depends on.
- **Rejected — both paths (hook + CLI fallback):** two Claude dispatch paths to keep honest;
  fallback semantics already covered better by the loud-degrade rule.
- **Tree effect:** H2's dispatch-half is substantially narrowed (the loud-degrade + abstract
  capability law lands here); H2 remains open for engine-unavailable/settings-drift cases. G1
  gains a concrete element.
- **Provenance:** kata-orchestrate:1247 (in-process default branch); README:189 (headless
  statusline degradation, verified); gauge hook :35-37 (fail-soft precedent, deliberately
  broken); ADAPTER-CONTRACT-M4 kill-binding degrade precedent; PLATFORM-MATRIX per-host hook
  rows.

### TM-B3 — The seam gates ALL agent launches; skill invocation is cursor-tracked, not gated · LOCKED

- **Decision (operator, 2026-08-16):** every launch of another agent — workers, judges
  (evaluate/review/slop/inline), design/plan authors, the advisor, researchers, kata-validate
  critics, debug fix-workers, reroll/correct re-dispatches, grill convergence reviewers — MUST
  carry a seam record; the hook blocks a record-less launch. **In-session skill invocations**
  (kata-loop → initiate → bootstrap → orchestrate sequencing) are the conductor reading its own
  instructions, not creating an agent: they emit **cursor phase events** but are not
  dispatch-gated.
- **Rejected — gate absolutely everything:** ceremony + a new failure surface on every ordinary
  skill load, for no trust gain the phase record doesn't already give.
- **Rejected — workers+judges only:** the advisor-reach gap (zero consults against a standing
  grant, burn-02) was one of the three recorded bypass symptoms; leaving advisor/research/critics
  prose-dispatched preserves a proven hole.
- **Sharpens:** judges' seam records are also where their verdicts persist (C4); the advisor's
  seam record closes the reach gap mechanically (the hook can also positively confirm the consult
  happened).
- **Provenance:** SURFACE-MAP §1 (D1–D12); backlog-burn-mode:146-161 (the reach gap, third
  bypass symptom); BBM-12.

### TM-B4 — Full engine-minted record, hook validates semantically, mint chains to the cursor · LOCKED

- **Decision (operator, 2026-08-16):** the dispatch record is **engine-minted** with:
  `runId · taskId · role · platform · resolved model+effort · planPath (freeze VERIFIED at mint
  via assert_frozen) · briefHash · mintedUtc · seq · agentDef (slot reserved for BL-N20)`. The
  hook **re-runs the engine validations against the record** (semantic check, not existence
  check), and the mint **appends a chained entry to the cursor** — so a fabricated record
  without matching cursor lineage is post-hoc detectable at the next gate.
- **The launched agent never echoes anything** — validation is wholly dispatcher-side, which
  eliminates the EDR-7 echo-forgery class rather than mitigating it.
- **Rejected — existence/shape check only:** a stale or hand-copied record from an earlier
  dispatch would pass the hook — the T-04 staleness class reborn at the seam.
- **Rejected — minimal record:** no run identity travels with the launch; C2 stamping and C4
  verdict persistence would need a second mechanism.
- **Honest residual (EDR-5 style, stated in the contract):** a deliberately adversarial conductor
  holds the session and can fabricate files; the seam DETECTS fabrication (cursor-lineage
  mismatch at post-hoc verification), it does not prevent it. The seam's prevention claim is
  scoped to drift, laziness, and prompt-obedience failure — the classes actually observed.
- **Provenance:** EDR-7; `kata_dispatch.build_brief` validations (the seed); T-04
  identity-not-ancestry; DETAILED-PASS discovery 2.

### TM-B5 — Deny-and-route; park when no legal path; every denial is a visible cursor event · LOCKED

- **Decision (operator, 2026-08-16):** a record-less launch is **DENIED by the hook** with a
  message naming the legal path (mint via the engine). Denial forces the legal path and needs no
  human, so it is BBM-11-compatible in unattended shapes. When the **engine itself refuses to
  mint** (plan not frozen, unknown role, unconfirmed platform) there is no legal path: ESCALATE
  `human-required`; unattended runs **park the task** (existing async-park pattern), never die
  silently and never proceed. **Every denial is a cursor event and a G1 visible refusal** — the
  presentation layer shows the line being held.
- **Rejected — warn-first rollout:** the exact "warn as a soft status" posture the operator
  rejected for D169; burns proved warnings scroll past.
- **Rejected — hard-fail the run:** one prose slip mid-migration would destroy healthy runs;
  deny-with-legal-path achieves the guarantee without the blast radius.
- **Provenance:** D169 verbatim ruling; BBM-11; the escalation async-park pattern
  (kata-orchestrate:884-885).

*Section B complete. Re-derivation: B1–B5 opened no new B-branches; C1 (cursor shape) is next in
dependency order — C2's run-id format is consumed by B4's record, so C1/C2 resolve before D.*

### TM-C1 — The CURSOR is the upgraded run log (board-shape heritage); named cursor; alignment study commissioned · LOCKED

- **Decision (operator, 2026-08-16, accept-with-modification):**
  1. **Shape accepted:** the run's one log IS the cursor — the existing append-only log upgraded:
     a **run-header line** (runId minted by the seam; rotation + header makes cross-run detection
     mechanical), new **orchestrator-only PHASE and VERDICT line types**, structured payloads as
     pointed-to JSON files (the existing escalation line+payload idiom). One log — D135's letter
     and spirit; the grammar change rides the pinned-clause deliberate two-step.
  2. **Named CURSOR (operator's modification):** "cursor is a better name than board because it
     marks where in the process we are sitting and where it is currently executing." Consistent
     with the operator's prior BBM ruling ("the CURSOR is the interruption token"). Glossary
     entry added to `CONTEXT.md` (concept renamed; file/skill heritage names migrate under H1 —
     the rename's blast radius is a migration item, not a design fork).
  3. **Alignment study commissioned (operator's rider):** evaluate the design against other
     learning-loop / graph-learning / run-record models (LangGraph checkpointing, Temporal-style
     event-sourcing replay, OTel trace chains, Hermes/Pi substrates per the existing
     `specs/learning-graph/RESEARCH-HERMES-PI.md`, GSD state) to ensure we align with or improve
     on them — dispatched as an in-grill research task; **its findings gate section C's close**
     (C5/C6 stay open until it reports).
- **Rejected — sidecar structured log:** it IS the second append-only journal D135 forbids.
- **Rejected — git-only cursor:** phase/verdict events aren't commits; in-flight visibility loses
  its source.
- **Provenance:** D135/D81 verbatim (cursor dossier); escalation idiom `protocol/escalation.md:3`;
  BBM cursor ruling `backlog-burn-mode/GRILL-LEDGER.md:117-124`.

### TM-C2 — Run identity penetrates fully, down to git trailers and evidence checks · LOCKED

- **Decision (operator, 2026-08-16):** the seam mints `runId` at run start (one seam act =
  cursor rotation + header write). Format: composite `run-<utc>-<hex>` — sortable, humane;
  randomness-mints-identity-only per the Determinism Doctrine. It stamps: the cursor header ·
  every dispatch record (TM-B4) · every gate artifact (`RESULT.json` gains `runId`) · report
  filenames (making `observability.md:18`'s promise TRUE — it was a FALSE row) · **a new
  `Kata-Run: <runId>` trailer on integration commits** (run membership survives machine change
  via git, the only (iv)-durable tier) · and **`evidence_is_current` is extended to run
  membership**: evidence is credited ONLY if the SHA is fresh AND the runId matches the live
  run — fail-closed on every old artifact (closes the July-artifact-read-raw class completely).
- **Rejected — runtime-only identity:** run membership would die with `.kata/`; old artifacts
  would still pass on freshness alone.
- **Rejected — soft evidence check:** the D169 "warn as a soft status" rejected shape.
- **Provenance:** cursor dossier (trailers = the only (iv) record); promise-audit FALSE row 4;
  BL-X11; T-04.

### TM-C3 — Resilience is a PRIMARY cursor benefit: snapshot-on-verdict cadence + offered trail push · LOCKED

- **Operator directive (2026-08-16, verbatim intent):** "We need to offer resilience as a primary
  benefit of the upgraded cursor… this all flows into the graph/learning graph function — align
  everything so we can build the learning graph around this. This is the truth component, but it
  all plays together into a single properly organized and woven spine. With the ability to handle
  parallelization in branched fan-out runs. With async processes that the Kitchen brings. All
  orchestrated properly, by a smart orchestrator and/or conductor which are phase aware."
- **Decision:** (1) **trail snapshot cadence upgrades** to fire on every PHASE and VERDICT append
  (alignment-study candidate #1) — mid-gate resume without re-running the gate, on existing
  fail-soft machinery; (2) **trail push is OFFERED at the human push gate** (closeout Decision 2,
  alongside commit/push/merge; config-rememberable `cursor.pushTrail`) — presented AS the
  resilience option per the directive; default stays never-push (BC, house guard, consent is the
  operator's); (3) resilience is a named, user-facing benefit — the presentation layer states the
  run's resilience level (feeds G1, same pattern as the enforcement-level declaration of TM-B2).
- **Provenance:** operator directive above; alignment study candidates #1/#6; kata_trail
  never-push deliberate rule; closeout never-auto-push house law.

### TM-C4 — Verdict persistence: dispatcher-witnessed VERDICT line + payload; durable by C3 cadence · LOCKED (conductor-resolved from locked context; no operator question spent)

- **Decision:** every judge verdict (evaluate PASS/NEEDS_WORK, review SHIP/HOLD, slop, inline
  chunk verdicts, grill convergence SHIP/HOLD — including proof the Advanced double-pass ran as
  two distinct dispatches) is persisted by the SEAM at collection: an orchestrator-only
  **VERDICT cursor line + pointed-to JSON payload** (verdict, evidence pointers, judge dispatch
  seq, runId). Judges stay no-write (their independence is untouched — the dispatcher is the
  witness, EDR-1/TM-B4). The C3 snapshot cadence makes verdicts durable at the moment they exist.
  This closes the cursor dossier's largest hole (undurable verdicts), gives BL-N19's mechanical
  re-loop its routing artifact, and gives BBM-12 wave gates a record.
- **Provenance:** TM-B3 sharpening; TM-C1 VERDICT type; cursor dossier cross-cutting #2;
  alignment study (LangGraph pending-writes analogy).

### TM-C5 — The phase model covers the WHOLE loop; closeout decisions become structured records · LOCKED (conductor-resolved under the operator's phase-aware directive)

- **Decision:** PHASE cursor events span the full Kata Loop — initiation · grill · freeze ·
  execution (per wave) · final gate · closeout · loop-back — closing the blind zones (mid-grill /
  mid-freeze / mid-closeout are invisible to restore today). The conductor and orchestrator are
  **phase-aware by contract**: they read position from the cursor, never re-derive it from
  context memory (feeds the BL-N20 agent definitions). **Closeout Decisions 1–4 land as
  structured cursor records** — including backout-approved (the highest-stakes unrecorded
  event) — and the loop-back event is recorded with the `prev-run:` chain pointer (study
  candidate #2). Exact phase vocabulary = design-doc detail, not a grill fork.
- **Provenance:** operator "phase aware" directive (TM-C3 block); cursor dossier §C blind spots;
  study candidates #2.

### TM-C6 — The cursor is the learning graph's substrate; projections carry provenance; hardening set adopted · LOCKED (conductor-resolved under the operator's alignment directive)

- **Decision:** (1) the learning graph (BL-N16) **builds around the cursor** — the cursor is the
  truth component; graph projections are folds over it and **every derived graph fact carries the
  (runId, line/seq) that produced it**, so a superseding DECISION invalidates downstream facts
  mechanically (Graphiti-derived, projection-layer only); (2) fold outputs are named
  **projections** (glossary term to add at design compile); (3) Hermes' distill-for-load binds:
  folds/context injections consume bounded distillations, never the raw log; (4) **adopted from
  the study**: `prev-run:` run-chain header (#2) · monotonic per-run `seq` (#3) ·
  dispatch-lineage stamps on worker lines (#4, bundled with #3 in the ONE grammar two-step) ·
  fold-cache snapshots in `.kata/` as pure cache (ES discipline; D81 licenses) · the stated
  invariant "fold is pure; side effects only after fold completes" · archives get the
  `prev-segment` chained-segmenting header field reserved NOW, built when a real cursor gets big
  (#5).
- **Provenance:** operator alignment directive (TM-C3 block); alignment study §3/§5/§6 +
  candidates #2-#5; RESEARCH-HERMES-PI.md:77-79; D81.

### TM-C7 — IN FLIGHT: operator-directed comparative assessment before resolution

- **Operator directive (2026-08-16, verbatim intent):** do not pick from the offered options yet —
  "do an assessment with known working patterns" from other harnesses on fan-out handling, and
  design to these requirements: **(1)** orchestrator FULL VISIBILITY into everything processing
  and how it aligns with dependencies flowing between individual tasks in the fan-out; **(2)**
  fans that MERGE into aligned results at the end; **(3)** the run structure is BUILT BEFORE
  EXECUTION — alignment with the planning agent; **(4)** protect runs from clobbering data and
  overrunning results; **(5)** gain efficiencies in multi-threaded tracking. Conductor to "map
  this out" at full depth after the survey returns.
- **Standing commitment (operator, same directive): HEAVY cross-documentation** — the trust-model
  seams and behaviors get written INTO the other backlog items (BL-N08 Kitchen · BL-N16 learning
  graph · BL-N19 re-loop · BL-N20 cadre · BL-N14 statistics · BL-N21 always-loop · the BBM
  ledger) so their future planning sessions execute with this work in mind. Scheduled to land
  once C7 resolves, so the concurrency rulings ride along. **This commitment is owed — surface
  at handoff if unmet.**
- Survey dispatched (LangGraph Send/map-reduce · Temporal child workflows · Airflow/Dagster DAG
  mapping · OTP supervision trees · CI matrix fan-in · git-native merge · in-repo ground truth);
  resolution question returns to the operator with the assessment.
- **RESOLVED below (same day) — survey delivered (`evidence/fanout-survey.md`), mapping presented,
  operator accepted with riders.**

### TM-C7 — Two-tier tree-of-runs fan-out; learning rolls up the tree; overruns pre-assessed · LOCKED

- **Decision (operator, 2026-08-16, accept-with-riders):** the cursor's fan-out model is the
  **two-tier tree-of-runs**: in-wave tasks stay lines on the parent's cursor; bakeoff arms,
  Backlog Burn wave-loops, and Kitchen bakes mint **child runs** (own runId + cursor + worktree,
  `parent-run:` header — D135 holds via **arm = run**, ruled explicitly). All eight design
  elements adopted: two-tier law · freeze-minted arm registry (the tree exists in the frozen
  PLAN before dispatch — planning-agent alignment) · dispatcher-witnessed SPAWN/DOWN-with-reason
  on the parent cursor (children never write the parent's log) · per-arm parent-close policy
  (cancel | park | **abandon-with-rendezvous** — mandatory across BBM-12 wave rollovers) ·
  declared fold reducers, undeclared concurrent merge = fail-loud refusal · ordering =
  (runId, seq) + parent fold-order, wall-clock never load-bearing · fan-in as merge-parents +
  `Kata-Arm:` trailer, fail-closed on conflict, mechanical-only fan-in commits (no evil merges —
  PD-2 in git history) · bakeoff selection as recorded supersede (winner + losing runIds; `-s
  ours`-shaped, never content blending; human version-select per standing rule). All seven named
  hazards carry their answering patterns (`evidence/fanout-survey.md`).
- **Rider 1 — learning rolls UP the tree (operator):** session/run closeouts produce learning
  items that propagate up the run tree — child-run learnings fold to the parent for either
  **in-loop learning** (applied within the current loop) or **total-loop learning** (the BL-N16
  run-end learning session). **There may be TEMPORARY, job-scoped learnings** specific to the
  current work that never promote to the durable agent substrate — a learning-scope taxonomy
  (job-scoped/ephemeral vs. substrate/durable) **needs assessment at the BL-N16 grill**; seeded
  into BL-N16's cross-doc note.
- **Rider 2 — overruns pre-assessed (operator):** small result overruns relative to other tasks
  are acceptable **only when pre-assessed and optimized by the orchestrator** — planned, declared
  overlap tolerance at partition/dispatch time; the fail-closed clobber protection stays for any
  UN-assessed overlap. Lands in the partition/plan rules (BBM-2 seam).
- **Provenance:** operator directive + riders (verbatim intent above); `evidence/fanout-survey.md`
  (six external lenses + collision analysis); the five requirements mapped in-session.

## Blocked-at-close notes (standing)

Grill-close `learn_feed.py` emit **BLOCKED by 🔴 BL-X12** (the emitter mislabels grill-ledger OPEN
questions as resolved decisions). Surface at close; do not run the emit.
