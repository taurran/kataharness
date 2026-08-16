---
spec: dispatch-seam
item: "BL-M33 · the conductor↔host dispatch seam (plain name: the code chokepoint every agent launch must pass through)"
status: draft
opened: 2026-08-16
baseline: master `de8578c` → branch grill/dispatch-seam · gauntlet 4/4 PASS (pytest 4518) · tree clean
tier: kata-grill-advanced (enforcement-critical, architecturally load-bearing — M34/N01/N19/N20 all hang off this seam)
target: CODEBASE (dev source, operator-selected this session)
---

# GRILL LEDGER — BL-M33 · the conductor↔host dispatch seam

**In plain terms:** today, when the harness starts any agent on its own host, a model writes a
prompt. No function runs. So every rule about *how* an agent must be launched — frozen plan only,
fresh-context judge, our-own-agent-definition, inside-the-loop-only — is a sentence the next model
may or may not honor, and nothing can tell the difference. The seam is the code that must run for a
dispatch to happen at all, so the rules become physics instead of requests.

## Phase 0 — grounding (read + swept + spot-verified; full evidence in [[SURFACE-MAP]])

- **`SURFACE-MAP.md`** (this dir) — the complete ground-truth inventory: 12 dispatch surfaces
  (11 sanctioned, 1 bypass), 10 built-but-orphaned enforcement primitives, 6 verified absences,
  10 inherited hard constraints, 4 candidate authority attach points, the blast radius.
- Binding rulings read in full this session: **D172** (seam actions are engine code, deterministic,
  fail-closed — minimal-Python preference relaxed exactly here) · **D169** (non-frozen plan BLOCKS
  dispatch; the chokepoint exists and is dead) · **EDR-7** (any disk-readable token is forgeable;
  a prose comparator is no comparator; the judge never certifies itself) · **BBM-12** (entire loop,
  always; conductor-driven bypass is DRIFT) · `protocol/orchestration.md` (thin conductor).
- Prior grills consumed as input: `specs/evaluator-dispatch-record/` (EDR-1..7),
  `specs/agent-cadre/` AC-1/AC-10/AC-11/AC-13 + roster row 2, `specs/backlog-burn-mode/` BBM-1/9/11/12.
- The operator's framing directive (2026-08-16, this session, verbatim intent): *identify all the
  surfaces it touches and how it plugs in — own agent or skill? prose within existing mechanisms?
  "It needs some aspect of authority over everything the harness does."*

### Answered from the docs before asking (Phase 0.3 — no operator attention spent)

| question | answer from ground truth |
|---|---|
| Is the seam an agent? | No. An agent obeying prose is the failure class being retired (D172, BL-N01 elevation). Agents are *subjects* of the seam (AC-1: loaded via the seam only). |
| Is it a skill? | Not primarily. Skills are prose the seam must bind; the seam is engine code (D172 verbatim: "guaranteeing proper execution rather than requesting it"). Skills get rewritten to route through it. |
| Is it prose within existing mechanisms? | Ruled out by D172 + the live evidence: both burns bypassed prose. Prose changes ride along (blast radius) but are not the mechanism. |
| Does a partial seam already exist? | Yes — `kata_dispatch` is a real, tested dispatch engine for codex/kiro, with the D169 freeze chokepoint built in. It is orphaned, and the Claude/host path is explicitly out of its scope ("handled by the orchestrator, not here"). |
| Where can authority physically live? | Exactly four attach points (SURFACE-MAP §5): the engine-as-only-door, host hook interception, the wrapper door, post-hoc identity verification. They compose. |

## The decision tree (initial derivation — re-derived after every resolution, to exhaustion)

| # | branch | status |
|---|---|---|
| B1 | **The authority architecture** — which composition of the four attach points constitutes "the seam," and what BL-M33 ships vs. defers to M34/N01/N20 | OPEN |
| B2 | **The Claude-host enforcement mechanism** — how code gets authority over in-process `Agent` dispatches (hook interception fail-closed? route the host through a headless CLI builder? engine-mint + post-hoc verify only?) — capability probes required, not assumed | OPEN |
| B3 | **Run identity** — does the seam mint a run-id; where it lives (board grammar? dispatch.json? state.json?); relation to `evidence_is_current`; what "live loop context" (BL-M34's predicate) is made of | OPEN |
| B4 | **Seam scope** — which of the 12 dispatch surfaces MUST pass through it (workers only? judges? authors? advisor? critics? loop-module invocations?) — the operator's "everything the harness does" made precise | OPEN |
| B5 | **What a dispatch record carries** — brief, role, model, plan ref, ticket — and the forgery analysis per EDR-7 (what the dispatched agent can and cannot reach) | OPEN |
| B6 | **Wiring the orphans** — which existing engines the seam routes through (build_brief/assert_frozen · resolve_roles · kata_models.resolve · validate_core_config · kata_board writer · roster) vs. leaves untouched | OPEN |
| B7 | **Cross-host reach** — codex/kiro already pass through code; the seam contract on hosts without interception; loud degraded modes (the kill-binding precedent) | OPEN |
| B8 | **Bypass semantics** — what happens at a dispatch the seam did not bless: fail-closed block vs. escalate; the BBM-11 headless-never-block tension; non-kata sessions must be untouched (kata_scope gating) | OPEN |
| B9 | **Migration** — ~52 launch sites in kata-orchestrate alone; rewrite order; what stays true mid-migration | OPEN |
| B10 | **Failure/degradation** — hook absent, engine unavailable, settings drift; what the honest residual is (what the seam does NOT prove, stated in the contract — the EDR-5 house style) | OPEN |
| B11 | **The M33/M34 boundary** — the seam (chokepoint exists) vs. the guard (bypass fails closed); which ledger owns which decisions | OPEN |

*Branch list is the opening derivation; Advanced-tier rule: re-derive after each resolution until
the re-derived tree is empty. Security surface (forgery, injection via briefs, hook trust) gets its
own dedicated pass per the Advanced depth contract.*

## Resolved branches

*(none yet — grilling begins after the operator confirms the ground-truth map)*

## Blocked-at-close notes (standing)

Grill-close `learn_feed.py` emit is **BLOCKED by 🔴 BL-X12** (the emitter mislabels grill-ledger
OPEN questions as resolved decisions — must not run against any grill ledger until closed). Same
posture as DEF-2 before it. Surface at close; do not run the emit.
