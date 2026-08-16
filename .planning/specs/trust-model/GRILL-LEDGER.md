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

*(none yet — Phase 1 begins at B1, dependency order: B → C → A → D → E → F → G → H, with A1/A2
posed when their sections are reached or sooner at operator preference)*

## Blocked-at-close notes (standing)

Grill-close `learn_feed.py` emit **BLOCKED by 🔴 BL-X12** (the emitter mislabels grill-ledger OPEN
questions as resolved decisions). Surface at close; do not run the emit.
