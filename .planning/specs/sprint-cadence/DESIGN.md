---
date: 2026-06-19
spec: sprint-cadence
status: FROZEN — grill converged (SC-GB1–10 + engram) + freeze-gate audit HOLD→resolved (all 7 must-fixes applied); fresh-context re-audit SHIP. Changes are deliberate re-freezes.
source-ledger: ./GRILL-LEDGER.md (SC-GB1–10 + engram cross-cut + the 2026-06-15 freeze-gate audit)
tags: [design, frozen, sprint-cadence, delivery-axis, incremental, boundary-protocol, prime-frame]
---

# sprint-cadence — incremental delivery — FROZEN DESIGN

Compiled from the converged grill ledger + the freeze-gate audit's 7 must-fixes. No new decisions here — every
LOCKED item traces to a resolved branch. Promoted to **D78–D85**. **Builds next** (the D16-first lock that
GB10 set was dissolved by D70 — sprint-cadence is no longer gated; see §8).

## 1. What it is
A second **delivery cadence**: build a project in **gated, reviewable increments (sprints)** instead of one
continuous run. Each sprint is a one-shot (no-drift holds within it); the **boundary** between sprints is the
scheduled, human-facing re-plan event — gate → report → controlled course-correct → next sprint. The steering
tenet: *each sprint is a one-shot; the boundary is the only place steering happens.*

## 2. Requirements satisfied
- **R1** A new orthogonal `delivery` axis (one-shot | incremental) composing with every existing axis (mode,
  run-shape, effort, modules) — not a new run-shape, not a module (GB1/GB2).
- **R2** Three-layer freeze: project DESIGN (north star) · sprint ROADMAP (boundary-amendable) · active sprint
  PLAN (immutable within the sprint) — the course-correct can steer *remaining* sprints, never the active one (GB3).
- **R3** A controlled boundary: explicit approval, drift-labelling, post-approval adversarial sweep, snowball
  guard — ceremony scales with reach; default light (GB3 G1–G4).
- **R4** Sequencing without bloating the spine: re-entrant `kata-bootstrap` routes; `kata-orchestrate` stays
  **sprint-blind**; a thin NEW `kata-sprint` owns the boundary (GB4 A+C).
- **R5** Resume across sessions/clones: progression state is a **disposable cache rebuilt from the git-committed
  trail** (GB5).
- **R6** Prime-frame context-budget sizing — the *same* primitive sizes sprints AND sets the one-shot
  self-handoff/refresh threshold (GB7, refines D8).
- **R7** Sprint N≥2 protects the prior green baseline via the shipped version-up machinery (GB8).

## 3. The `delivery` axis + config (D3 — pinned)
`protocol/config.md` gains:
```
delivery: {
  shape:    "one-shot" | "incremental"            # default "one-shot" (D25 absent ⇒ today's behavior)
  boundary: "always-stop" | "auto-continue-while-green"   # default "always-stop" (control-first, GB6)
  backend?: <engram pointer>                       # optional CONSULT seam (E2/E19, no-op if absent)
}
```
Preset pre-fill (GB4/D46): individual ⇒ one-shot · version-up ⇒ **ask** · batch ⇒ one-shot. The D45 load-guard
validates `delivery` **fail-closed** (malformed ⇒ stop+escalate, not guess). Absent ⇒ one-shot (BC, D25).

## 4. Three-layer freeze + the Boundary Change-Control Protocol (G1–G4)
| Layer | Freeze status | Change path |
|---|---|---|
| Project **DESIGN** | north star | only an **appended superseding decision** at a boundary (never silent rewrite); **+ B5: a DESIGN-layer amendment requires the same fresh-context `kata-review` SHIP the initial freeze demands** |
| Sprint **ROADMAP** | frozen, boundary-amendable | reshape *remaining* sprints (add/drop/reorder) as a recorded re-plan |
| Active sprint **PLAN** | immutable within the sprint | none — D1 no-drift, full force |

**Boundary protocol (G1–G4) — structural invariants, never tiered (D33):**
- **G1 — explicit approval gate.** Boundary hard-stops; no correction applies without explicit user approval
  (unless `boundary: auto-continue-while-green` AND all green-conditions hold, GB6).
- **G2 — drift labelling.** Each change classified by reach (next-sprint-plan / roadmap-reshape /
  DESIGN-amendment) and flagged when it is drift from a frozen artifact; drift-class needs a separate explicit
  "yes, I am changing frozen X."
- **G3 — post-approval adversarial sweep.** Fresh-context `kata-review` (D15) sweeps the approved set for
  second/third-order drift the user did not ask for. On finds → **re-present for another approval round, capped
  at PINNED 2 rounds (A2 — a safety backstop, NOT a tunable)**; still snowballing ⇒ G4.
- **G4 — snowball guard.** Predicate is **solely** `blast-radius(approved corrections)` vs the **remaining-
  roadmap footprint** — exceeds ⇒ flagged **re-scope, not a tweak** → deliberate roadmap re-plan / new run
  (A2 — the numeric threshold is **removed**; blast-radius-vs-footprint only, for D18 reproducibility).
- **Safety spine:** when in doubt, **stop and make the human decide; never silently expand.**

## 5. Tie-in / wiring map (D1 — honest NEW / EXTEND / REUSE labels)
| Path | Label | What |
|---|---|---|
| `skills/plan/kata-plan` **roadmap layer** | **NEW** (the feature's largest build surface — *not* latent; A1) | partition the DAG at natural seams into prime-frame-sized sprints; emit the **roadmap artifact** (schema below); per-sprint just-in-time plan freeze; sprint N≥2 = version-up plan (D50) |
| `skills/coordinate/kata-sprint` | **NEW** (thin boundary coordinator, GB4-C) | stop-side: verify gate green → compose `kata-report` + `kata-handoff` → STOP. resume-side: run G1–G4 course-correct (composes `kata-grill` delta-mode + `kata-review` + blast-radius) → freeze next sprint plan → hand to orchestrate. **Composes, never reimplements.** |
| `skills/evaluate|handoff/kata-report` | **NEW (minimal core = D32 v1; D2)** | the per-sprint one-page report **is** `kata-report v1` (not throwaway); D32 expands later |
| `skills/coordinate/kata-readiness` | **EXTEND** | detect sprint-progression state (open roadmap, sprint index, **gated-vs-dirty** boundary T5); **rebuild the tier-3 cache from the git trail** |
| `skills/handoff/kata-selfhandoff` | **EXTEND** | prime-frame trigger (GB7) replacing D8's % threshold; runs intra-sprint too |
| `skills/handoff/kata-handoff` | **EXTEND** | boundary-artifact content (the boundary handoff) |
| `protocol/config.md` | **EXTEND** | the `delivery` field (§3) + D45 guard |
| `protocol/state.md` | **EXTEND** | tier-3 sprint fields + disposable/rebuildable semantics |
| `protocol/handoff.md` · `protocol/escalation.md` | **EXTEND** | boundary-artifact shape; red-sprint async path (T4) |
| `kata-orchestrate` · `kata-evaluate` · `kata-review` · `kata-grill` (delta) · blast-radius · D50 version-up | **REUSE (verbatim)** | orchestrate stays **sprint-blind**; delivery-awareness lives only in HANDOFF-phase routing (one-shot → `kata-handoff`/`kata-selfhandoff`; incremental → `kata-sprint`) |

**Roadmap artifact schema (A1 — pin):**
`{ projectDesignRef, frozenAt, sprints: [ { id, goal, gateCommand, demonstrableArtifactType, dagSeamRationale, dependsOn[] } ] }`

## 6. State (GB5 — three tiers, git is the source of truth)
| Tier | Holds | Lives in | Lifecycle |
|---|---|---|---|
| 1 frozen provenance | `delivery: {shape, policy}` | `kata.config` (git) | bootstrap-set, append-stable, D45-guarded |
| 2 durable trail | per-sprint reports + boundary handoffs + superseding decisions/roadmap amendments | `.planning`-style Obsidian docs (git) | **authoritative, resumable record** |
| 3 progression cache | sprint index, gate status, open-correction status, dirty/gated flag | `.kata/` (gitignored) | single-writer plan-guardian (L3), **churns; rebuilt from tier-2 on re-entry** |
Resume works in a new session/clone because `kata-readiness` rebuilds tier-3 from the git-committed tier-2 trail
(current sprint = which reports exist + are gated). If the cache corrupts, throw it away and rebuild.

## 7. Prime-frame sizing (GB7 — the cross-cutting primitive; B1 — supersedes D8's threshold clause)
The **prime frame** = a model's recommended effective working band (below the degradation zone, headroom
reserved) — an **agnostic fraction/policy; the adapter resolves it to real tokens per model** (Fable 5 deep /
Sonnet workers, D59). **Floor:** fits one prime frame ⇒ refuse sprint, recommend one-shot. **Ceiling:** a sprint
exceeding one prime frame ⇒ split. Max sprint count = `⌈project context demand ÷ prime frame⌉`, no arbitrary cap.
- **B1 (D-number, supersedes D8's threshold half):** the one-shot self-handoff/refresh threshold changes from
  D8's user-set % → the **model-resolved prime-frame fraction**. D8's *principles survive* (anti-over-
  conservative; task-boundary-preferred). `kata-selfhandoff` = **EXTEND**. Self-handoff runs **inside sprints**
  too (intra-sprint refresh, no human gate, no drift); **sprint = the one-shot mechanism + a planned stop at
  prime-frame boundaries** for gate+report+course-correct. Same primitive, two policies.
- The ~1M window + prime-frame fraction are **`[TUNABLE]`, grounded against real model facts at BUILD time**
  (verify Fable 5 / Sonnet windows + recommended utilization — do not pin from memory). Architecture is
  number-independent.

## 8. Version-up reuse + sequencing
- **GB8:** a sprint is version-up-shaped whenever a prior green baseline exists. Unifying rule: **`baselineGate`
  = the most recent green gate** (existing repo's, else the prior sprint's). Greenfield ⇒ sprint 1 greenfield,
  2+ version-ups; existing-repo ⇒ every sprint a version-up. Reuses D50 footprint+regression + D51/D52
  escalation verbatim; `kata-graph` activates à-la-carte on prime-frame pressure.
- **GB9:** sprinted version-up is **first-class**; `delivery` × mode/effort/modules works today; **sprinted
  bake-off TRIMMED** (no config path/offer/seam — not forbidden, just not built; revisit only on a concrete
  request once Spec B exists).
- **Sequencing (supersedes GB10):** GB10 locked "build after D16," but **D16 was retired (D70)** — the D16-first
  lock is dissolved. Sprint-cadence **builds next** (after loop-cognition, per the current ROADMAP). Freeze is
  docs-only/cheap and done here; build is a separate planned+approved effort (its own PLAN).

## 9. Engram cross-cut
The engram seam registry + contract already shipped (`protocol/engram.md`, E1–E21 + C1–C6 + backend binding).
Sprint-cadence seams: **E19** (sprint re-entry routing, CONSULT), **E20** (G4 snowball re-scope), **E2/E3**
(boundary auto-continue / delta-grill). **Should-fix A3 applied:** a boundary CONSULT may never flip
`stop→continue` while any of {green ∧ no escalations ∧ no pending corrections ∧ no G3 tertiary drift} is false
(C4-adjacent — subordinate to the GB6 AND-gate). **Lens-C trim is MOOT — keep the registry:** the load-bearing
host skills are now built (**E17** `kata-readiness` D44, **E18** `kata-defer` D73-M2, **E21** `kata-handoff`
spine #5), so the registry is no longer purely speculative and the maintenance rule justifies keeping it.
**E19/E20** are this spec's own NEW `kata-sprint` seams — concrete-by-construction once `kata-sprint` is built. **Should-fix D4 applied:** T3 mid-project cadence change (incremental↔one-shot)
routes through the G1/G2 approval gate (it changes the roadmap layer = drift-class).

## 10. Tertiary-drift register (T1–T8 — LOCKED, from the grill)
T1 boundary supersedes a coincident selfhandoff · T2 `kata-report` v1 built here (no debt) · T3 cadence-change
is a bootstrap re-entry path (drift-class, D4) · T4 red sprint escalates (D51/D52), never a boundary · T5
dirty⇒resume / gated⇒course-correct (readiness) · T6 sprint state single-writer (L3) · T7 deterministic
sprint-scoped worktree naming · T8 STEERING/kill-switch survives session spans at the boundary.

## 11. Decisions to promote at freeze (D78–D85)
- **D78** — `delivery` orthogonal axis (one-shot|incremental); unit = sprint (GB1/GB2).
- **D79** — three-layer freeze + Boundary Change-Control Protocol G1–G4 (+E1 cap=2, +B5 DESIGN-amend SHIP gate) (GB3).
- **D80** — sequencing A+C: re-entrant bootstrap routes, orchestrate sprint-blind, NEW thin `kata-sprint` (GB4).
- **D81** — three-tier state; tier-3 `.kata/` cache rebuilt from the git trail (GB5).
- **D82** — course-correct = scoped delta-grill; `delivery.boundary` default always-stop (GB6).
- **D83** — prime-frame context-budget primitive; **supersedes D8's threshold clause** (D8 principles survive) (GB7/B1).
- **D84** — sprint baseline = most recent green gate (GB8); sprinted version-up first-class, bake-off trimmed (GB9).
- **D85** — `kata-plan` roadmap layer is **NET-NEW** (A1); roadmap-artifact + `delivery` config schemas pinned.

## 12. Backward-compatibility (checkable)
- **BC1** `delivery` absent ⇒ one-shot = today's behavior exactly (D25). *Check:* a run with no `delivery` field
  behaves as the current loop; `kata-orchestrate` is byte-unchanged.
- **BC2** orchestrate stays sprint-blind. *Check:* the diff shows no sprint logic in `kata-orchestrate`.
- **BC3** all skills `0.1.0` (policy A). **BC4** every sprint gate = the same `kata-evaluate` default-FAIL (D22).

## 13. Acceptance (of the eventual build — recorded now, run at build)
- **A1** validator green incl. NEW `kata-sprint` + `kata-report` frontmatter; `REQUIRED_PROTOCOL` covers the
  `delivery` config field + the boundary-artifact + tier-3 state terms.
- **A2** `kata-plan` emits a roadmap artifact matching the §5 schema; per-sprint plans freeze just-in-time.
- **A3** boundary protocol G1–G4 present + never-tiered; the PINNED 2-round cap + blast-radius-only G4 predicate
  encoded; a DESIGN-amendment at a boundary triggers a fresh-context `kata-review` (B5).
- **A4** resume rebuilds tier-3 from the git trail in a fresh clone (the GB5 robustness claim).
- **A5** fresh-context adversarial `kata-review` (D15) over the build returns SHIP.

---
**FROZEN.** Next: a fresh-context freeze-gate re-audit confirms the 7 must-fixes are applied (no self-certification),
then promote D78–D85; the BUILD is a separate planned+approved effort. Changes are deliberate re-freezes.
