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
| A3 | *(opened by re-derivation at G1 — operator ruling)* Backlog items carry truth status — designed vs. built must be unmistakable | OPEN → resolved below |

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

### TM-A1 — The Guardian trust scale; fixes route THROUGH the loop · LOCKED

- **Decision (operator, 2026-08-16, three-part — via directive then a three-model comparison):**
  1. **Ubiquitous-language ruling:** the internal audit categories (FACT/PARTIAL/PROSE/FACADE/
     FALSE) stay as the diagnostic layer, but "built"/"wired"-class designations are **archaic
     and confusing to the average user** — every user-facing trust surface uses the **Guardian
     scale** (operator-picked over an Auditor/SOC-2 model and a Kata/craft model): **Verified ·
     Partially verified · Honor-system · Dormant · Broken** — naming what is CHECKING, not the
     code's condition. Baked into `CONTEXT.md`.
  2. **Remediation routes THROUGH the loop (operator, verbatim intent):** the relabel/fix is
     "acted upon within the loop — either a re-execution of code or a fix applied during the
     validation section. **If anything is false or facade it should be another loop pass.**"
     No out-of-band doc edits; FALSE/FACADE findings are loop work items. This seeds section D's
     routing rule: a Broken or Dormant-claimed-as-Verified finding is NEEDS_WORK-class and
     routes to re-loop (F2 consumes this).
  3. The 5 FALSE + ~25 FACADE promise-audit rows therefore become **work items in the
     trust-model build's first loop passes**, relabeled in Guardian terms with the mechanism
     cited when wiring lands.
- **Rejected — wire-then-true:** prose keeps lying to readers for the build's duration.
- **Rejected voices:** Auditor (controls language — precise but insider); Kata (house craft
  voice — distinctive but higher learning curve). Structure identical in all three; voice was
  the choice.
- **Provenance:** promise-audit evidence (the 114 rows + distribution finding); PD-2;
  the three-model comparison presented with previews this session.

### TM-A2 — Split & commit run provenance; drift-checked at branch close, fail ⇒ re-loop · LOCKED

- **Decision (operator, 2026-08-16, accept-with-rider):** machine-specific values (personal
  paths) migrate to `.kata-settings.json` (the existing machine-local home); `kata.config` and
  `INTENT.md` become clean, **committed run provenance** — `protocol/state.md:41`'s tier-1
  "(git)" claim becomes true as written, completing the cursor's machine-change story. A
  redaction check guards the migration (no personal data committed).
- **Rider (operator):** the committed provenance is **enforced via drift checks at the close of
  the branch** — if `kata.config`/`INTENT.md` as committed do not match what the run actually
  executed (per the cursor record), the close FAILS and the run is **sent back through the
  loop**. Lands as a section-F close check; consumes TM-C4's records; routes per TM-A1's
  loop-routed remediation rule.
- **Rejected — committed run manifest:** a second artifact that can drift from the live config.
- **Rejected — re-tier honestly:** the resilience-primary directive (TM-C3) argues against
  accepting the loss.
- **Provenance:** `.gitignore:10,19` vs `protocol/state.md:41` (cursor dossier governing fact);
  TM-C3 resilience directive.

*Section A complete. Next: section D (Truth Serum). D5 and D3 are substantially pre-resolved by
locked branches (TM-C2 run-membership evidence; the anti-vacuity law adopted at TM-C6/D3's
evidence) — conductor resolves them with citations; operator forks remain at D1 (deferral ledger
hardening), D2 (detector set v1), D4 (gate-precondition rollout).*

### TM-D1 — The deferral ledger gets FULL hardening · LOCKED

- **Decision (operator, 2026-08-16):** pinned canonical paths (`.planning/DEFERRED.md` +
  `.planning/ASSUMPTIONS.md`) · a machine schema (formalized heading grammar + required fields:
  what/why/provenance/owed-to, closure discipline) · **an approval record on operator-approved
  deferrals** — `accepted_by`/`accepted_at`, the gsd-override shape, answering BL-N01's open
  question "where does approval get recorded so the gate can check it" · **a `protocol/deferral.md`
  contract registered in `REQUIRED_PROTOCOL` and clause-pinned** so the rules themselves are
  tamper-evident. Silent-deferral detection (matrix class d — the three-way join
  PLAN ⋈ tree ⋈ DEFERRED) becomes fully mechanical; a debt marker without a `DEF-*` reference is
  a BLOCKER (the gsd D3b rule, adopted).
- **Rejected — schema without the protocol contract:** the detector would work while the rules
  stayed unguarded — the exact pre-2026-08-03 protocol-folder class.
- **Rejected — best-effort parsing of prose:** every parse miss is a silent-deferral miss on
  PD-1's own sanctioned path.
- **Provenance:** detectability dossier §5 + matrix class d; gsd-verifier D3b/D8 extractions;
  prime-directives.md PD-1 sanctioned-paths clause.

### TM-D2 — v1: MECH detectors block, SEMI detectors signal; deferred blocks filed as BL-N24 · LOCKED

- **Decision (operator, 2026-08-16, accept-with-rider):** Truth Serum v1 ships **BLOCKING**
  (gate-refusing): stub-body AST scan (tree-sitter spans) · the silent-deferral three-way join
  (on TM-D1's hardened ledger) · debt-marker-without-`DEF-*` · stale/wrong-run evidence
  (TM-C2's extended `evidence_is_current`) · citation-existence resolver · **mutation proof
  RE-RUN by the gate** — never the worker-reported union (closes the gate-inventory's
  worker-union hole). **SIGNAL-ONLY** (feeds judges, never blocks): unwired-symbol detection,
  calibrated on the T6–T11 orphan corpus. Detectors ATTEST and NARROW; judges judge (burn-02
  meta-finding stated wherever v1 is described).
- **Rider (operator):** every deferred block is a BACKLOG item executed at the end of the current
  backlog and **updated along the way** — filed as **BL-N24 (Truth Serum v2)** with per-item
  promotion criteria and the standing rule: a v1 scope cut lands there or it is a PD-1 silent
  deferral.
- **Rejected — everything blocks:** class-b false positives block healthy work and train bypass
  pressure. **Rejected — minimal v1:** leaves the live BL-X11 stale-evidence class open.
- **Provenance:** detectability matrix; burn-02 OBSERVATIONS:136; gate-inventory (mutation
  union); TM-C2.

### TM-D3 — The anti-vacuity companion law + judge tripwires · LOCKED (conductor-resolved; evidence already adopted the law)

- **Decision:** every detector ships with its anti-vacuous-check companion — it REFUSES to
  certify over zero inputs / absent preconditions (the `check_reuse_claims_producers_exist` /
  `surface_hash`-zero-file / protocol-folder-zero-scan pattern, now a stated design law). The
  kata-validate **tripwire generalizes to the judge stack**: every judge proves it can still
  fail against a known-bad corpus before its verdict is credited (the only existing meta-gate
  becomes standard equipment). A detector or judge that cannot demonstrate failure-capability is
  Dormant, not Verified (Guardian terms).
- **Provenance:** detectability cross-cutting law #1; gate-inventory (tripwire = the only
  meta-gate); TM-A1 Guardian scale.

### TM-D5 — Evidence identity everywhere · LOCKED (conductor-resolved; TM-C2 already ruled the mechanism)

- **Decision:** every evidence consumer (kata-evaluate's machine-input step first — the BL-X11
  fix — then review/debrief/closeout/sprint-stop) routes through the extended
  `evidence_is_current` (SHA fresh AND runId matches, TM-C2). The RESULT parsed-counts
  cross-gate chimera (BL-X13) is fixed in the same build (per-gate counts or the honesty flag,
  per its filing). BL-X11 and BL-X13 fold into the trust-model build.
- **Provenance:** TM-C2; BL-X11/BL-X13 filings; gate-inventory step-5 row.

### TM-D4 — Every completion gate gains its fact-precondition in this program · LOCKED

- **Decision (operator, 2026-08-16):** ALL gates — task, wave, final eval, grill convergence,
  freeze, grounding, sprint, closeout — gain a truth-serum fact-artifact precondition
  (refuse-not-warn, the locked house shape) in the trust-model build. The NEW artifacts the
  inventory identified get created: per-task gate record · convergence-pass record (incl. proof
  the Advanced double-pass ran as two distinct dispatches, via seam records) · green-at-fork
  baseline RESULT. Wave-phasing WITHIN the build is the frozen PLAN's job, not a scope cut;
  any true scope cut lands in BL-N24 per the TM-D2 standing rule.
- **Provenance:** operator directive #6 (verbatim, recorded in the directives block);
  gate-inventory SEAM/NEW markers; TM-C4.

*Section D complete. Next: E (grounding agent + judge inputs), then F (plan-grounding close),
G (presentation), H (cross-cutting + security pass).*

### TM-E1 — Two-tier grounding: engines everywhere; the agent at the stack head + signal-triggered · LOCKED

- **Decision (operator, 2026-08-16, after a requested overhead assessment):** the M4 doctrine
  applied to grounding. (1) **Engines at every gate, always** (near-free, already locked at
  TM-D4). (2) **The grounding AGENT stands FIRST in the validation stack** at the greater-loop
  level (the operator's position) — ~3–5 bounded dispatches per run, economy-tiered under D131
  (fact-orchestration, not judgment). (3) **Signal-triggered at other gates**: the agent fires
  only when an engine flags what it cannot attest alone — a reuse-claim phrase, an unattestable
  DONE claim, a research finding, a resolved-but-unread citation. (4) **Telemetry-informed
  promotion**: per-gate injection expands only where run data shows it cheap — tracked in BL-N24
  per the TM-D2 standing rule.
- **Assessment recorded (modeled, labeled):** per-task agent dispatches ≈ +15–30 serialized
  minutes on a mid-size run (H1: gates serialize) — the overhead class the operator flagged;
  stack-head-only ≈ +2–5 minutes per run. Engines are milliseconds and token-free.
- **Charter (carried from the directive + cross-doc):** the agent RUNS the engines and emits the
  attested fact table judges consume; agent proposes, engine attests; AC-10 execute-the-tooling
  is its standing law; scope boundary — grounding attests FACTS pre-judgment, the challenger
  attacks JUDGMENTS post-hoc.
- **Provenance:** operator overhead directive (verbatim in the E1 exchange); H1 (backlog-burn-01
  OBSERVATIONS); M4 zero-LLM-happy-path doctrine; D131.

### TM-E2 — Judges consume attested fact tables; residual judgment enumerated · LOCKED (conductor-resolved from locked context)

- **Decision:** every judge's brief carries the attested fact table for its target (detector
  outputs + grounding verdicts + evidence identity), and judge contracts are rewritten to
  (a) judge ON the facts (never re-derive what an engine attested, never accept a worker claim
  the table contradicts), (b) state residual-judgment surfaces explicitly (quality, design
  fidelity, threat reasoning — the legitimately-judgment set per the gate inventory), and
  (c) carry the TM-D3 tripwire. The burn-02 meta-finding travels with every description:
  detectors narrow and attest; judges find what detectors cannot.
- **Provenance:** gate-inventory §B; TM-D3; burn-02 OBSERVATIONS:136.

### TM-F1 — Evidence declared at freeze; tracked on the cursor; truth metrics in the final report · LOCKED

- **Decision (operator, 2026-08-16, accept-with-riders):** **no plan item freezes without its
  completion-evidence declaration** (artifact path, test name, or probe command — one line per
  item, authored by the plan-author, gated at the freeze gate). The close join becomes TOTAL:
  every item mechanically resolves to built-and-exercised / recorded-deferral / named drift.
- **Rider 1 (operator):** the declarations and their resolution are **tracked in the cursor
  machinery** — item done-ness is a cursor fact, not a report-time derivation.
- **Rider 2 (operator):** the join **feeds the final report** (the UX-designed closeout):
  **truth metrics presented at the final report** — items resolved, evidence per item, drift
  named, deferrals with approvals. "They should always be resolved, but it should show any
  leftover items" — leftovers are always displayed, **with the option to execute them in another
  run** when the shape was single-wave or an approval-requiring mode (ties closeout Decision 3 /
  BL-N19's re-loop route).
- **Provenance:** detectability class d; gsd observable-truths; the UX closeout report (freeze-
  candidate); operator riders verbatim.

### TM-F2 — The close is fail-closed: NEEDS_WORK routes to re-loop or recorded operator acceptance · LOCKED (conductor-resolved from locked context)

- **Decision:** the plan-grounding close emits its verdict artifact (TM-C4 shape). A failing
  verdict leaves exactly two legal paths: **another loop pass** (BL-N19's mechanical route,
  wave-level per BBM-12) or **recorded operator acceptance** (the TM-D1 approval-record shape).
  The seam refuses run-closure otherwise. TM-A2's provenance drift check and TM-A1's
  false/facade⇒loop-pass rule both land here as close checks.
- **Provenance:** TM-A1/A2 riders; TM-C4; BBM-12; D169's refuse-shape.

### TM-G2 — Rendering law: facts and judgment visually distinct; provenance on every fact · LOCKED (conductor-resolved; follows from locked branches)

- **Decision:** every displayed fact carries its provenance (which check, which artifact, which
  runId/seq — the quote-verbatim-never-recompute discipline generalized); machine facts render
  as data (boxes, per the UX grammar), judgment renders as prose (dividers); Guardian terms
  (TM-A1) are the only user-facing trust vocabulary; **the presentation layer inherits PD-2** —
  an opinion in fact clothing is the facade one layer up, and detector humility ("no unattested
  fact enters a gate," never "no defect escapes") travels to every trust surface.
- **Provenance:** TM-A1; UX-15/18 grammar; kata-report verbatim-badge discipline; DETAILED-PASS
  component-7 law.

### TM-A3 — Backlog items carry TRUTH STATUS; the UX item's status corrected · LOCKED

- **The trigger (PD-2 moment, recorded honestly):** at the G1 posing the operator stated the UX
  backlog item was "already built." Ground truth: the UX system is **DESIGNED to
  freeze-candidate** (DESIGN rev 3, convergence-clean, awaiting the operator's standing freeze
  sign-off per `specs/ux-rework/CONVERGENCE-R1.md`) — **zero UX code is shipped** (no wrapper
  commands on disk; the UX-29 grammar renderer not committed; templates are committed spec
  reference, not shipped code). The conductor corrected the record per PD-2. The operator's
  meta-ruling stands vindicated by the very confusion: the backlog's prose lets
  "33-rulings-deep design" read as "built."
- **Decision (operator, verbatim intent):** "apply truth status to the backlog items… and ensure
  they are marked complete properly in the future." Every backlog item carries a **truth-status
  mark** — lifecycle stage + Guardian verification: `FILED · GRILLED · DESIGNED
  (freeze-candidate) · FROZEN · BUILT—Verified (with cited evidence) · CLOSED`. "BUILT" is legal
  ONLY with the Verified evidence citation (the TM-D2 truth-serum checks are what verify it) —
  an uncited BUILT is the PD-2 violation class itself. Immediate correction: the UX items
  (BL-N06/N07) marked DESIGNED—freeze-candidate; the full retrofit of existing items rides the
  trust-model build's loop passes (TM-A1 routing) and the standing rule feeds BL-N11 (backlog
  management) as a binding input.
- **Provenance:** operator ruling at G1; STATE/HANDOFF freeze-candidate records; UX-29;
  PD-2.

### TM-G1+G3 — All four trust surfaces adopted; fold into the UX freeze-candidate (corrected sequencing) · LOCKED

- **Decision (operator intent "execute this here", applied to corrected ground truth):** all four
  surfaces adopted — (1) run-start box (in/NOT-in + enforcement level + resilience level);
  (2) per-gate receipts (fact tables as data-boxes, **visible refusals with reasons**); (3) the
  final report's **truth metrics** (per-item evidence, drift named, deferrals with approvals,
  leftovers with the run-again option — TM-F1 riders); (4) the per-run trust ledger
  (Guardian-termed). **Sequencing corrected by A3's ground truth:** the UX system is NOT yet
  frozen, so there is no amendment gate to route through — the trust surfaces **join the UX
  freeze-candidate as a pre-freeze addition**, extending the operator's standing sign-off list
  by exactly this section (surfaced, not silent). The UX freeze sign-off then covers both; the
  build executes under this program per BBM-12.
- **Provenance:** operator directive at G1; TM-A3 correction; TM-B2/C3/F1 surface seeds;
  CONVERGENCE-R1 standing gate.

### TM-H1 — Migration order: engine → cursor → skills → hook LAST; Guardian honesty covers the interim · LOCKED (conductor-resolved)

- **Decision:** build lands in dependency order — engine + cursor first, the ~52 launch sites and
  dispatched-skill inbound contracts rewrite to route through the seam in waves (each wave a loop
  pass per BBM-12), and **the fail-closed hook is the LAST switch flipped**, activated only after
  every sanctioned path is migrated — because a hook activated early would deny un-migrated
  legitimate prose sites, and a soft interim mode is the rejected warn-shape. Until activation,
  the run-start declaration honestly reports enforcement **Dormant** (Guardian terms make the
  interim truthful instead of soft). Naming migration (board→cursor heritage) rides the same
  waves; stale `kata_dispatch` line anchors across five skills fix in wave 1 (they are already
  Broken rows).
- **Provenance:** TM-B2/B5; TM-A1 Guardian; promise-audit T18.

### TM-H2 — Degradation honesty completes: every degraded state is declared, scoped, and non-viral · LOCKED (conductor-resolved)

- **Decision:** the TM-B2 loud-degrade law generalizes: hook absent/uninstalled ⇒ detection-only,
  DECLARED at run-start (the hook's presence is live-probed at seam init — an uninstalled hook
  can never be reported Verified); engine unavailable ⇒ the run cannot mint, which is a
  no-legal-path park (TM-B5), never a silent prose fallback; settings drift detected at seam
  init (config-vs-settings consistency check). `kata_scope` guards everything — non-kata
  sessions are untouched by the hook. The honest residual (EDR-5 style) is stated in the
  contract: the seam's guarantees are scoped to runs that enter it; the validator's-own-source
  meta-layer remains undefended and says so.
- **Provenance:** TM-B2/B5; kata_scope (live machinery); KH-T02 residual clause.

### TM-H3 — Backlog mapping: what this DESIGN closes vs. feeds · LOCKED (conductor-resolved)

- **CLOSES when built+Verified:** 🔴 BL-M33 (the seam) · 🔴 BL-M34 (the guard = TM-B5+hook) ·
  🔴 BL-N01 (Truth Serum v1 per TM-D2; v2 = BL-N24) · BL-N19's missing mechanical route (TM-C4/
  F2) · BL-X11 + BL-X13 (TM-D5) · the T6–T11 facade rows as wiring lands (TM-A1 loop-routed).
- **FEEDS (binding input, does not close):** BL-N16 (cursor substrate + roll-up + scope
  taxonomy) · BL-N20/cadre (grounding agent, phase-aware definitions, agentDef slot) · BL-N08
  Kitchen (tree-of-runs, close policies) · BL-N14 (projections) · BL-N21 (wrapper = outermost
  layer) · BL-N11 (truth-status rule, TM-A3) · the UX freeze (G surfaces joined pre-freeze).
- **Provenance:** the cross-doc pass (committed d785370) + this ledger's locks.

### TM-H4 — The security register (Advanced security/edge-case layer; gated by convergence pass 2)

- **S1 Forgery.** Dispatch-record fabrication: detected via cursor-lineage mismatch (TM-B4);
  verdict forgery: VERDICT lines are orchestrator-only and seam-appended — but the conductor IS
  the orchestrator, so the **adversarial-conductor residual stands and is stated** (detection at
  post-hoc verification, not prevention). Worker-line forgery: dispatch-lineage stamps mean a
  forged line must name a live parent (TM-C6).
- **S2 Injection.** (a) Brief injection — advice/learning/facts are INLINED VERBATIM into briefs
  by ruling; **all inlined content is delimited as DATA** (the kata-validate payload-as-data
  discipline generalized to every brief assembly). (b) Cursor-line injection — folds and any
  agent reading the cursor treat line content as data, never instructions; renderers escape.
  (c) Hook input parsing — structured, exec-safety-registered, never string-eval; the hook is a
  new sink and joins the exec-safety registry per its keep-in-sync rule. (d) Learning-substrate
  injection-persistence — already a BL-N16 ruling (security scan on self-written learning);
  cross-bound here.
- **S3 Hook trust.** The hook lives in user settings and can be absent/removed: seam init
  live-probes it and the declaration downgrades honestly (TM-H2) — absence can never
  impersonate enforcement. The hook's own source is validator-guarded like protocol contracts
  (clause-pin its deny rule); the meta-residual (guards guarding guards) is stated, not hidden.
- **S4 Redaction.** Committed run provenance (TM-A2) and cursor payloads pass a redaction check
  at mint — no secrets/keys/PII in committed artifacts (the PAT lesson is the standing example);
  fail-closed on detection.
- **S5 Consent.** Outward-facing acts stay human-gated: trail push opt-in only (TM-C3); the hook
  never blocks non-kata work (kata_scope); no auto-push anywhere.
- **S6 Availability.** Fail-closed must not become deny-everything: engine failure parks with a
  loud reason (TM-B5); degraded modes are per-capability, never viral; a wedged hook is
  detectable at seam init and reported.
- **Edge cases:** crash mid-mint ⇒ orphan record without dispatch, detected and cleaned at
  resume (registry enumeration, TM-C7 element 4) · rotation during live children ⇒
  abandon-with-rendezvous (TM-C7) · same-second ordering ⇒ seq (TM-C6) · parallel-dispatch hook
  races ⇒ per-record validation is order-independent · fold purity ⇒ side effects only after
  fold completes (TM-C6).

*Tree fully resolved (A1–A3, B1–B5, C1–C7, D1–D5, E1–E2, F1–F2, G1–G3, H1–H4). Re-derivation
after the final resolutions opened no new branches. Advanced close-out: convergence pass 1 (main
tree) → pass 2 (security layer) → ELEVATE → close. Grill-close emit remains BLOCKED by BL-X12.*

## Convergence pass 1 — HOLD (4H/10M/4L), and the findings were right. Remediations below AMEND the named branches.

The fresh-context reviewer verified 20+ citations (one materially wrong — mine, H4) and found a
hard three-branch contradiction plus unowned formats. Every remediation below specifies within
the operator's locked intent; none reverses an operator ruling. Each amendment is binding on the
DESIGN compile as if written in its branch.

**R-H1 (amends TM-B3/B4/B5) — phase-scoped minting.** The record's freeze check binds exactly the
roles whose work EXECUTES a plan (coder; task-scoped judges; anything dispatched against a plan
task). Pre-freeze roles (design-author, plan-author, grill convergence reviewers, researchers,
grill-time advisor) mint against **the governing artifact of their phase** — frozen `INTENT.md`
(initiation), the converged grill ledger (authoring) — recorded in a new `governs` field.
`assert_frozen` runs for plan-governed mints exactly as D169 rules; a per-role required-field
table lands in the DESIGN. D169's scope is restored, not widened.

**R-H2 (amends TM-C2) — run-membership defined in one sentence.** Gate evidence must carry the
EXACT runId of the run being gated; ancestor/prior-run artifacts are legal as *inputs* but never
as gate evidence; the sanctioned cross-run path is the parent consuming a child's recorded
DOWN/VERDICT summary (which carries the child's runId) at fan-in/close. Each wave-loop's gate
uses its own evidence; a re-loop pass re-emits its gates. Fail-closed preserved; BBM-12 unblocked.

**R-H3 (amends TM-C4) — the capture mechanism is named.** The adapter hook layer binds BOTH
edges: PreToolUse-class (deny, TM-B2) and **PostToolUse-class (capture)** — the post-hook appends
the VERDICT/DOWN record mechanically when a seam-dispatched judge/arm returns, correlated via the
dispatch record (R-L4). The capability probe covers both edges in the same early task. Where the
post-edge is unavailable: loud degrade, and the **close backstop is already mechanical** — TM-F2/
TM-D4 refuse closure without verdict records, so prose-era capture cannot silently satisfy the
gate. Dependents (N19 route, wave gates, convergence-pass records) inherit the mechanism, not
prose.

**R-H4 (amends TM-A3/TM-G1+G3) — my mis-statement corrected, per PD-2.** The UX system's true
state: `DESIGN.md` rev 3, `status: DRAFT — freeze-candidate, awaiting convergence gate`; rounds
R1 and R2 both returned CONVERGE-HOLD; rev 3 was **conductor-verified line-by-line, NOT
independently convergence-reviewed**; the operator's sign-off list is open. "Convergence-clean"
is retracted (the reviewer caught the conductor inheriting a handoff claim instead of reading the
source — recorded as this grill's own validation-miss). Sequencing amended: the combined artifact
(UX DESIGN + the four trust surfaces) receives a **full fresh-context round-3 convergence pass**
before the operator's freeze sign-off; the trust-model program's non-UX build does NOT block on
the UX freeze — only the presentation-layer build wave does.

**R-M1 (amends TM-B4):** dispatch records are **single-use** — consumed at hook validation
(a consumed record fails re-validation) — and carry a short `mintedUtc` expiry. Replay closed.
**R-M2 (amends TM-C1/C5):** PHASE/VERDICT/SPAWN/DOWN/DENY lines are **seam-authored** (engine
mint/capture paths + the hook), never worker-authored; "orchestrator-only" is corrected — the
conductor's pre-orchestrator phase events are written by the seam functions it calls.
**R-M3 (amends TM-C1/C6/C7):** ONE grammar migration, ONE pin re-approval: appended-field form
(`seq` after the timestamp; optional `parent-seq` lineage field), the full new TYPE enumeration
(PHASE, VERDICT, SPAWN, DOWN, DENY), the run-header block (`RUN <runId>` + `prev-run:` +
`parent-run:` + `prev-segment:`), and the fold/parser updates land in the same build wave. Exact
BNF in the DESIGN.
**R-M4 (amends TM-C3/G1):** resilience levels are DEFINED and DERIVED, never asserted: **full**
(trail push on + snapshots verified) · **local** (snapshots verified, no push) · **degraded**
(skips detected). The snapshot skip sentinel becomes a recorded cursor event at the seam call
site, so the declared level is a fold over recorded fact.
**R-M5 (amends TM-B3/B4):** `ROLE_GROUPS` extends in the build (reviewer · slop · inline-eval ·
advisor · critic · challenger · grounding); `HOST_ONLY_ROLES` unchanged pending the cadre grill;
tier mapping stays `SKILL_WORK_CLASS`.
**R-M6 (amends TM-D3):** tripwire corpora activate PER JUDGE as they land (the TM-H1
activation-order pattern): a judge without a corpus is declared **Honor-system**, never blocked;
corpus ownership = the build wave wiring that judge's precondition; home = per-judge fixtures on
the kata-validate precedent; proof cadence = per-build (CI) with the corpus hash on the cursor.
Deny-everything dissolved.
**R-M7 (amends TM-B2):** the Bash CLI-shape leg carries its honest residual — best-effort,
evadable by indirection; its run-start declaration is **Partially verified**, never
"intercepting". The Agent-tool leg alone may claim interception.
**R-M8 (amends TM-A2/C7):** child runs NEVER rewrite the committed `kata.config`; per-arm
variation lives ONLY in the freeze-minted arm registry (committed with the plan). The close
drift-check for a tree = committed config + registry vs. each cursor's recorded execution;
fan-in cannot conflict on config by construction.
**R-M9 (amends TM-F1/H1):** the evidence declaration is a PLAN frontmatter per-task `evidence:`
field; `parse_plan_tasks`, the plan-author skills, and the freeze gate extend to carry/check it —
**added to TM-H1's migration scope explicitly.**
**R-M10 (amends TM-D2/E1):** the mutation re-run's actor is the **grounding agent at the
validation-stack head** (engine-run, orchestrator-triggered before the evaluator dispatch); its
record is the evaluator's precondition — the evaluator refuses without a grounding-run mutation
record. The worker-union hole closes at a named seam.

**R-L1 (amends TM-A2):** corrected — `state.md:41`'s tier-1 claim covers `kata.config` (via the
delivery row) and never claimed `INTENT.md`; committing INTENT.md is a NEW ruling under the
resilience directive, not a restoration. **R-L2:** the fanout-survey's "K3" anchor is the
**K5** schema (`protocol/board.md:57`) — corrected here; the evidence file stands with this
erratum. **R-L3 (amends TM-H3):** BL-N01 closes **at v1 scope** (TM-D2); v2 = BL-N24 — stated
per TM-A3's own uncited-claim rule. **R-L4 (amends TM-B4):** records live under `.kata/dispatch/`
(tier-3 is correct: the CURSOR chain entry is the durable half, D81-consistent); the engine
writes a pending-record pointer at mint; the hook correlates the `Agent` call to the pending
record and consumes it (R-M1).

## Convergence pass 1 re-run — HOLD (3H/6M/4L). Round-2 remediations; each AMENDS the named branch/amendment.

The re-run confirmed the round-1 remediations (16 further citations verified; both errata
confirmed; the UX correction verified at source) and found residual mechanism gaps. All specify
within locked operator intent.

**R2-H1 (amends R-H1) — governors get D169-class recorded states.** The `governs` vocabulary is a
CLOSED enum with a mechanical predicate per entry, extending the `plan_status` pattern:
`plan` (predicate: `assert_frozen` — unchanged, D169) · `ledger` (grill-ledger frontmatter
`status:` becomes a closed enum `draft | converged | absorbed`; `converged` is written ONLY by
the grill-close act after the final convergence SHIP; read by a new `ledger_status` engine
predicate) · `intent` (INTENT.md frontmatter gains `status: draft | frozen`; `intent_scaffold.
write_intent` writes `frozen` at Phase 6; read by a new `intent_status` predicate) ·
`initiation` (pre-INTENT mints; record carries the priming-prompt hash). **Per-role minimum
states:** plan-executing roles ⇒ `plan:frozen` · design/plan-authors ⇒ `ledger:converged` ·
grill-phase researchers/advisor/convergence-reviewers ⇒ `ledger:present(draft)` · bootstrap/
harness-entry ⇒ `intent:frozen`. Unknown governor or unmet state ⇒ the engine refuses to mint
(TM-B5 applies). No convention-only freeze anywhere in the ladder.

**R2-H2 (amends R-M10/TM-D2) — the mutation re-run is a per-task ENGINE act; the ambiguity was a
category error.** `prove_non_vacuous` is deterministic engine code — milliseconds, zero tokens —
so TM-E1's overhead ruling (which governs AGENT dispatches) does not apply. Resolution: the
**orchestrator triggers the engine re-run at each task gate** (closing the worker-union hole at
its source, per task); the **grounding agent at the stack head attests the record set**
(present + current + per-task complete) as the evaluator's precondition. Actor named, cadence
named, overhead nil, TM-E1 untouched.

**R2-H3 (amends R-H3) — hookless capture degrades to conductor-invoked ENGINE capture, declared
Honor-system; deny-the-bypass, never deny-everything.** On hosts without a post-edge, the legal
capture path is the seam's capture FUNCTION invoked by the conductor at verdict collection — the
run closes by doing the legal act, so TM-F2/TM-D4's refusal binds only when records are ABSENT,
not when a hook is (S6 satisfied; same deny-forces-legal-path shape as TM-B5). Guardian grading
of the capture edge, declared at run-start: post-hook = **Verified**; conductor-invoked engine
capture = **Honor-system** (its in-flight half rests on conductor obedience and says so; the
close backstop remains mechanical either way).

**R2-M1 (amends TM-H1/G1):** a MINIMAL run-start declaration (plain-text enforcement + resilience
+ capture-edge Guardian line, seam-derived) ships **in the seam wave** — TM-H1's interim honesty
has its surface from day one; the full UX-grammar box lands in the presentation wave.
**R2-M2 (amends TM-C5/C7/F2):** a re-loop of a wave is a **sibling child**: `parent-run:` = the
same parent (tree structure — roll-up folds walk this), `prev-run:` = the failed sibling
(iteration chain — history walks this). Both pointers, distinct semantics, one ruling.
**R2-M3 (amends TM-C7/R-H3):** at abandon-with-rendezvous, **the parent's seam writes the DOWN
record** by reading the child cursor's terminal state at the next parent seam act — children
still never write the parent's log; unrendezvoused orphans reap at seam init (H4 edge case,
now with a named actor).
**R2-M4 (amends TM-G2/B2/C3/R-M4/R-M7):** ONE trust vocabulary: every user-facing trust claim is
a **Guardian term**; mode words (`intercepting`, `detection-only`, `full`, `local`, `degraded`)
are technical qualifiers in parentheses after the Guardian term, never standalone claims —
e.g. `enforcement: Verified (intercepting)` · `capture: Honor-system (no post-edge)` ·
`resilience: Partially verified (local)`.
**R2-M5 (amends TM-H4 S1):** premise wording corrected — VERDICT lines are **seam-authored**
(per R-M2); the adversarial-conductor residual stands on the conductor-calls-the-seam fact.
**R2-M6 (amends R-H2/TM-D4):** the green-at-fork baseline RESULT is an **input, never gate
evidence**: recorded in the consuming run's cursor as an input reference carrying its origin
runId; the arm/re-loop's regression gate compares against it and emits ITS OWN result under its
own runId.

**R2-L1:** the UX round-2 record lives INSIDE `CONVERGENCE-R1.md` (its "Round 2" section) — no
separate R2 file exists; stated so the citation is locatable. **R2-L2:** the combined-artifact
pass is named **round C1**, reviewing DESIGN **revision 4** (= rev 3 + the trust surfaces) —
no collision with the UX rounds numbering. **R2-L3 (amends TM-H4 S3):** the hook's clause-pin
and exec-safety registration cover BOTH edges (deny + capture). **R2-L4:** the fail-soft
precedent anchor is `kata-gauge-check.py:34-36` (was cited :35-37).

## Convergence pass 1, third run — HOLD (3H/6M/4L). Round-3 remediations; each AMENDS the named branch/amendment.

The third fresh reviewer verified all prior errata at source and reported closure on two of five
tracked classes. Its H3 caught a **false premise of the conductor's** (R2-H2's "milliseconds"),
corrected below per PD-2 — the reviewer recomputed where the conductor shape-checked, which is
doctrine law 13 exercising itself on this grill.

**R3-H1 (amends TM-C2/C1) — crash-resume ADOPTS the runId; rotation happens only at run START.**
Run identity lives in the cursor header. Seam init distinguishes two cases mechanically:
**new run** (no live cursor, or the live cursor's run is closed) ⇒ rotate + mint; **resume**
(live cursor with an unclosed run) ⇒ ADOPT the header's runId, reap orphan records (R2-M3), and
continue — pre-crash gate artifacts remain evidence (exact-runId rule satisfied), which is what
makes TM-C3's mid-gate-resume claim true. A resumed session never re-mints; a re-loop (R2-M2)
and a loop-back (TM-C5) always do.

**R3-H2 (amends R2-H1) — the governor ladder honors BC; the entry rung is shape-dependent; the
initiation predicate is the open-phase check.** The `governs` enum selects WHICH artifact governs
a dispatch — it is not a mandatory pipeline: a **direct one-shot harness run** (no initiation —
the BC case `protocol/intent.md:11` PINS) governs under `plan` exactly as today; `intent:frozen`
binds only runs that ENTERED via initiation/kata-loop. The `initiation` governor's predicate is
**an open INITIATION phase event on the live cursor** (checkable; the record additionally carries
the priming-prompt hash as provenance) — and initiation-phase mints are graded **Honor-system**
in Guardian terms (the weakest rung, declared as such, never dressed as Verified). Deny-legal-
runs eliminated; no convention-only rung remains unlabeled.

**R3-H3 (amends R2-H2/TM-D2) — the cost premise corrected; scope + ordering ruled.** CORRECTION
(PD-2): `prove_non_vacuous` is NOT milliseconds — it copies the project tree to a sandbox and
runs the test command twice per asserted line (`mutation_run.py:218-315`). Resolution within the
operator's overhead ruling: (1) **per-task re-runs use the TASK'S OWN verify command** (narrow by
construction), re-running the worker's claimed mutation set with a declared cap (all lines ≤ N,
default N=5; beyond that the orchestrator samples N and records the sampling on the cursor —
no silent truncation); (2) **the final gate's stack-head grounding pass re-runs a sampled subset
against the gate command** and attests the whole set's records; (3) **ordering rule:** the
blocking mutation precondition ACTIVATES per platform only after 🔴 BL-X14 closes (the prover
proven able to fail on that platform — the TM-D3 law applied to the prover itself); until then
the precondition is declared **Honor-system** on that platform (the TM-H1 activation-order
pattern). No Linux task gate fail-closes on a Broken prover.

**R3-M1 (amends R-M1/R-H3):** consumption = **mark-consumed-and-retain** (records persist for
lineage; a consumed record fails PRE-hook re-validation only). The `mintedUtc` expiry bounds the
MINT→LAUNCH window only; return correlation is by the host's native tool-call pairing plus the
record id stored at validation — a judge may legally return hours later.
**R3-M2 (amends TM-E2):** every judge contract gains a **pinned machine-parseable first line**
(the kata-inline-eval pattern generalized): `VERDICT: <enum>` per judge type — the thing the
post-hook parses. Part of the judge-contract rewrite wave.
**R3-M3 (amends R2-H1/TM-H1):** `ledger_status` enum = `draft | converged | frozen | absorbed`
(`frozen` is a legitimate terminal state in live use); normalizing the live free-prose statuses
(`GRILL COMPLETE…`, `GRILL DONE…`) is added to TM-H1's migration scope EXPLICITLY.
**R3-M4 (amends R-H1):** the governor argument inherits BL-F01's rule verbatim: **required,
keyword-only, no default** — an omittable governor is the D136 silent-permissive class.
**R3-M5 (amends R2-M4):** the complete Guardian↔mode table (no builder invention):
enforcement — Verified (intercepting) · Partially verified (bash-leg) · Dormant
(pre-activation) · Honor-system (detection-only host); capture — Verified (post-edge) ·
Honor-system (engine-by-conductor); resilience — Verified (full: **push receipt recorded on the
cursor**, never the config flag — this also resolves L3) · Partially verified (local) ·
Honor-system (degraded/skips detected).
**R3-M6 (amends TM-D4/F2/C1):** D134 reconciliation, stated: tier-2 integration trailers remain
**AUTHORITATIVE for DONE**; the cursor gates ONLY fact classes for which it is the system of
record (verdicts, phases, denials, spawns) — for DONE it corroborates, exactly as D134 rules.
The close's refusals bind per fact class to that class's system of record.

**R3-L1:** a root-level re-loop has no parent by definition: `prev-run:` chain only (the new
root points at the failed root) — TM-C5's existing shape, stated. **R3-L2:** the INTENT `status`
field addition is an explicit **additive amendment to the pinned intent schema with its own
two-step** (the acceptanceCriteria precedent); the draft/frozen discriminator is a new explicit
`freeze=True` argument to `write_intent` at Phase 6 — named, not inferred. **R3-L3:** resolved
inside R3-M5 (push receipt, not config flag). **R3-L4:** subsumed by R3-H2/R3-H3.

## Convergence pass 1, fourth run — HOLD on ONE finding (all six tracked classes verified closed; 12 further citations sound). Round-4 remediation.

**R4-H1 (amends R2-H1/R3-H2) — the `ledger` rung gets its BC case; D71 grill-skip runs mint
authoring dispatches under `initiation`.** A run with NO grill ledger (D71 `skip`/`light` — a
FROZEN-legal shape kata-readiness actively recommends for lean prompts — or any
bootstrap-entered authoring run) mints its `design-author`/`plan-author` dispatches under the
**`initiation` governor**: predicate = the run's open INITIATION/authoring phase event on the
live cursor, record carrying the priming-prompt hash, graded **Honor-system** (declared, never
dressed as Verified). **`ledger:converged` binds only runs that actually ran a grill.** The
grill remains exactly what D71 froze it as — an optional enrichment dial, never a de-facto
mandate at the seam.

**Residuals accepted into the DESIGN compile (recorded, not re-decided):** (1) R3-H3's sampling
uses a stated deterministic sort key (doctrine laws 9/10 — no randomness, explicit total
order); (2) the re-run's honest residual stated in-contract: it proves the worker's CLAIMED
mutation set bites — claimed-set completeness stays worker-asserted; (3) "run is closed" is a
RECORDED terminal phase state, never convention (the D169 class one layer down); (4) one
VERDICT-line parser, two callers (post-hook + conductor-invoked engine capture), per-judge enum
table enumerated at the contract-rewrite wave; (5) `ledger_status` carries R3-M3's four-value
form + BL-F01's first-word parse rule; the live free-prose corpus normalizes in TM-H1's
migration. **TM-H4 compile notes:** the register absorbs R2-M5 (seam-authored) and R2-M3 (the
DOWN actor); its "element 4" anchor for the arm registry corrects to element 2.

### Mid-close evidence event — CI red 12 days; the vacuity-prover vacuous on Linux (2026-08-16)

Operator surfaced inbox spam of gauntlet failures mid-convergence. Conductor diagnosis (run
31966366450): **every CI run since ≥2026-08-04 is FAILED including all master merges** — 62
failures, ~61 of them mutation-proof meta-tests where `prove_non_vacuous` returns
`testWentRed: False` on ubuntu for mutations that bite on Windows — the anti-vacuity engine
cannot prove it can fail on Linux (the TM-D3 violation class, live, in our own machinery), plus
one statusline empty-argv crash. Filed 🔴 BL-X14 + BL-X15; fixes route through the loop (TM-A1).
**Trust-ledger sharpening recorded:** the promise audit's FACT grade for the gauntlet rested on
"CI runs it" — CI ran, failed, and the signal landed only in a spammed inbox: direct evidence
for TM-G1 (receipts must land where the operator looks) and for TM-D3's tripwire law applying to
the provers themselves, cross-platform. Guardian status of CI-gauntlet today: **Broken.**

## Convergence pass 1 — SHIP (fifth run, 2026-08-16). Six compile residuals recorded.

The fifth fresh-context reviewer returned SHIP: governor ladder verified rung-by-rung against
live skill text (every legal run shape lands on a checkable rung; no de-facto grill mandate);
12 citations verified at source; sections A–H walked with all four amendment rounds; no
builder-divergence remains. **DESIGN-compile residuals (contract, carried into the brief):**
(1) the phase vocabulary MUST name the open INITIATION/authoring phase (the weakest rung's
predicate reads it) and the recorded terminal `closed` state (R3-H1's branch reads it);
(2) the per-role "minimum state" ordering over the four-value `ledger_status` enum is stated,
and `absorbed` ROUTES the mint to the absorbing ledger rather than satisfying it; (3) R4-H1
compiles as **ledger-presence-predicated, never tier-predicated** (a `light` grill DOES produce
a ledger — the parenthetical must not become the test); (4) the never-a-de-facto-mandate law
carries into TM-D4's per-gate fact-sets (no gate requires a grill artifact of a run that
legally has none); (5) the grill-close `converged` status write is INDEPENDENT of the
BL-X12-blocked learn_feed emit; (6) the healthy default run declares
`resilience: Partially verified (local)` — the run-start wording must read as honest state,
not a defect report.

## Convergence pass 2 (security layer) — HOLD (4H/9M/6L). RS-\* remediations; each AMENDS TM-H4 (and named branches). The register also absorbs the R4 compile notes here (R2-M5 seam-authored wording · R2-M3 DOWN actor · arm-registry anchor = TM-C7 element 2).

**RS-H1 (amends TM-F1/R-M9/R3-H3 + TM-H4 S2) — the `evidence:` field is a NEW execution
capability and gets the exec-safety treatment, not a freeform string.** Closed grammar, three
forms only: `artifact:<repo-relative-path>` (NEVER executed — existence/wiring checked) ·
`test:<pytest-node-id>` (fullmatch grammar on the node id, compiled to structured argv
`[python, -m, pytest, <id>]`, no shell) · `probe:<registered-name>` (names an argv template
from a committed probe registry — never a freeform command). A freeform command string is
REFUSED at the freeze gate. The per-task verify command the mutation re-run uses gets the same
treatment (trust domain: LLM-authored ⇒ compiles through the grammar or is refused). The field
+ grammar + argv + trust domain are registered in `protocol/exec-safety.md` BEFORE build, per
its own new-capability law.
**RS-H2 (amends R-M1/R3-M1 + the H4 edge list) — consumption is an ATOMIC CLAIM.** Consuming a
record = `os.rename` of the record file into `consumed/` (atomic within the volume): two racing
pre-hooks ⇒ one rename wins, the loser's validation fails ⇒ deny. The edge-case sentence is
rewritten: parallel-dispatch order-independence is ACHIEVED BY the atomic claim, never assumed.
`fs_atomic`'s replace-only primitive is explicitly NOT the consume mechanism.
**RS-H3 (amends R3-H2/R4-H1 + TM-H4 S1) — the initiation rung gets exclusivity + its honest
residual.** Initiation-governed minting is REFUSED once the live run records a stronger governor
(`plan:frozen` or `ledger:converged`) or once its INITIATION phase has closed; re-opening
INITIATION on a run with a frozen plan is a recorded DENY-class event. Stated residual: pre-
freeze, the rung is self-serviceable by the conductor (it opens the phase it needs) — that is
WHY it is graded Honor-system, and cursor lineage is its detection channel, not a prevention.
**RS-H4 (amends TM-H4 S3, subsumes M9) — hook integrity is probed, never presumed.** The hook
source carries a pinned FINGERPRINT (digest; updater prints, never rewrites — the
protocol_fingerprint pattern, which clause-pins cannot substitute for on code). Seam init runs a
**live deny-tripwire**: a self-test dispatch that MUST be denied; the Guardian enforcement
declaration derives from that probe's result — file presence proves nothing (a mid-session
install reads present-but-inactive; a neutered hook reads present-and-green). TM-D3's
failure-capability law now explicitly covers the deny hook itself.

**RS-M5 (register row added):** ONE verdict parser, strict fullmatch on line 1 of the
tool-result ENVELOPE (never scanning the body — repo content/advice payloads/diff hunks cannot
forge a verdict), per-judge enum table; the conductor-invoked capture leg's input is
conductor-supplied and says so (Honor-system).
**RS-M6 (amends TM-A2 + S5):** committing `INTENT.md`/`kata.config` into a TARGET repo is an
outward act with a **first-run consent moment** (per-target, remembered); the harness's own repo
consents by standing config. Redaction is not consent; both apply.
**RS-M7 (amends S4, folds L6):** redaction is detection, stated as such — DETECTED classes fail
closed **at the commit act** (branch close, not mint — closing the TOCTOU window); undetected
content is a stated residual; the scrub extends `learn_feed.redact`'s class table (one scrub,
not two).
**RS-M8 (register row added):** trust-boundary table for the record store + cursor: writers
enumerated per artifact; a worker CAN mint-and-launch and is caught post-hoc (stated); and the
register now CLAIMS the strength it owns — `refs/kata/trail` snapshots give git-object
tamper-evidence for retro-edits of the cursor: the post-hoc integrity anchor.
**RS-M10 (amends S3):** the settings entry records the full expected command string + script
digest at install; seam init compares (the `/adapters/claude/` substring is identification,
never verification). `~/.claude/settings.json` itself is unguardable by kata — stated residual.
**RS-M11 (amends S6):** the deny hook **fails CLOSED in-run** (explicitly the opposite of the
gauge hook's never-block precedent — that difference is stated in both files); bounded runtime
+ payload cap (oversized/timeout ⇒ deny with reason, recorded).
**RS-M12 (amends R-M1):** `mintedUtc` expiry is defense-in-depth ONLY; the atomic single-use
claim (RS-H2) is THE replay control; wall-clock is never load-bearing (TM-C7 reaffirmed).
**RS-M13 (amends S2 + TM-G2):** ALL cursor-derived text rendered to any surface is
control-character/ANSI-stripped (the UX-30 glyph-first ruling applied as a security control) —
a cursor line cannot repaint a fake receipt.

**RS-L1:** crash windows completed — rotation is an atomic sequence (archive rename, then
header write; a torn rotation is detected at seam init); mid-capture loss is backstopped by the
close's absent-records refusal (stated).
**RS-L2:** abandoned-arm PROCESS disposition: at parent close, arms are killed unless their
close policy names a successor rendezvous; a closed run's arm commits are quarantined (never
merged into graded results); write-after-close residual stated.
**RS-L3:** per-run trail refs (`refs/kata/trail/<runId>`) eliminate fan-out snapshot contention
(per-arm cursors get per-arm durability; the legacy ref unchanged for BC); expected skip rate
becomes a measured cursor metric at build.
**RS-L4:** the exec-safety mechanical scan extends to `adapters/**/hooks/*.py` (or the hook's
row is manual WITH that limitation stated — the scan-scope fact is recorded either way).
**RS-L5:** the deny hook's scope check reads a seam-init-written run marker (no live FS walk
per call); marker present ⇒ kata scope ⇒ fail closed on errors; absent ⇒ allow (non-kata
sessions untouched). The transient-error window collapses to the marker read, and the posture
per edge is now explicit.

## Convergence pass 2 — SHIP (re-run, 2026-08-16). THE ADVANCED DOUBLE GATE IS SATISFIED.

The security reviewer verified all four RS HIGH closures at source (11 claims checked; the
atomic rename-to-claim row graded "the strongest") and confirmed the register's honest-residual
discipline throughout. **Fifteen compile residuals recorded into the DESIGN brief** — the two
high-priority ones: (1) the redaction scrub compiles as TWO named points (provenance at branch
close; cursor/trail content at the snapshot-or-push edge); (2) the deny-tripwire's no-result
posture is fail-closed to Dormant (never inheriting a prior declaration), with the script
tripwire + registration digest named jointly necessary. Mediums include: the mutation sink's
shell=True conversion/re-domaining rides RS-H1; the `test:` grammar REUSES `_guard_node_id` and
`artifact:` gets `_guard_path` CWE-23 treatment; replay-prevention scoped to intercepting hosts;
the marker-loss edge stated with post-hoc detection as its residual; the hook's internal timeout
pinned strictly below the host's; glyph-mimicry answered by provenance-fields rendering, not
stripping alone. Lows: consent lives machine-local (`.kata-settings.json`); trail
tamper-evidence is evidential-until-pushed; retry-reads-as-replay deny message names the re-mint
path; expiry wording; RS-H3 reads against the INITIATION/authoring phase; VERDICT no-match ⇒
absent-records refusal, never body-scan fallback; prefer extending the exec-safety scan to
adapters hooks. All fifteen are binding compile notes.

**Grill convergence status: pass 1 SHIP (fifth run) + pass 2 SHIP (second run). Remaining
close-out per the Advanced contract: ELEVATE (posed to the operator) → record EV → close (emit
BLOCKED by BL-X12, surfaced not run).**

## Operator sequencing mandate (2026-08-16, recorded verbatim-intent — binding on the close)

**"As soon as this gets frozen we will need to do a FULL DOCUMENTED handoff with agent
orientation. That will have to happen before we execute."** Sequence therefore: grill close →
design-author → plan-author → FREEZE (D169) → **full kata-handoff (STATE current-block rewrite +
HANDOFF turnover block + the locked UX-15 agent-orientation format with its paste block, per the
NEXT-SESSION-ORIENTATION precedent) → THEN execution dispatches.** No build dispatch before the
handoff package is committed. Surface at close; a freeze without the handoff is an incomplete
close.

## Blocked-at-close notes (standing)

Grill-close `learn_feed.py` emit **BLOCKED by 🔴 BL-X12** (the emitter mislabels grill-ledger OPEN
questions as resolved decisions). Surface at close; do not run the emit.
