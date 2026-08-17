---
spec: trust-model
artifact: "ledger-status normalization table — tm-w2-ledger-status-normalization output (builder-produced, conductor-filed 2026-08-16); the fence-blocked remainder is the planning window's fold input"
---

# Grill-ledger `status:` normalization table (all 29, exhaustive)

Search: four converging patterns (tracked + untracked, separator-agnostic, whole worktree);
exactly 29 `GRILL-LEDGER.md` files, all under `.planning/specs/`; 37 spec dirs have none;
the two other `*LEDGER*` hits (telemetry-ledger.md, DECISION-LEDGER.md format doc) are not
grill ledgers. Enum: `draft | converged | frozen | absorbed`, first-word parse (BL-F01).

## A · CONFORMANT (11 — no action)

agent-cadre `draft` · backlog-burn-01 `draft` · backlog-burn-mode `draft` ·
bump-on-modify `frozen` · dispatch-seam `absorbed —…` (first word parses; see R2) ·
evaluator-dispatch-record `draft` · greater-loop `converged (…)` (advisory: content
arguably supports `frozen`; both satisfy the same mints) · learn-feed-body-loss `frozen` ·
**trust-model `converged` (G4 ownership — verified, no edit)** · ungated-protocol-files
`frozen` · ux-rework `draft`.

## B · NON-CONFORMANT, free-prose first word (3 — FENCE-BLOCKED, planning window)

| File | First word | Required | Basis |
|---|---|---|---|
| debug-mode | `GRILL` (…COMPLETE…) | `frozen` | DESIGN FROZEN + BUILT; all four PLAN-p* FROZEN |
| install-portability | `GRILL` (…DONE…) | `frozen` | its own status names the freeze; DESIGN FROZEN 2026-06-26 |
| multi-model-orchestration | `GRILL` (…DONE…) | `frozen` | DESIGN + PLAN FROZEN 2026-06-26 |

## C · NON-CONFORMANT, `status:` key ABSENT (15 — FENCE-BLOCKED, planning window)

| File | Required | Basis |
|---|---|---|
| advisor-executor | `converged` | convergence SHIP pass 5; PLAN "awaiting freeze-gate" |
| context-autonomy | `frozen` | DESIGN FROZEN 2026-07-04 |
| d16-planning-varied-ab | `frozen` | DESIGN FROZEN v2 |
| dispatch-stderr-fix | AMBIGUOUS `converged\|frozen` → **R3: `converged`** | ledger-as-contract, no recorded freeze act |
| kata-preflight | `frozen` | DESIGN + PLAN FROZEN 2026-06-26 |
| loop-cognition | `frozen` | DESIGN FROZEN |
| modes-A3-bootstrap-wiring | `converged` (low confidence) | no frozen marker anywhere |
| modes-A4-version-up | `frozen` | DESIGN FROZEN |
| mutation-sandbox | AMBIGUOUS → **R3: `converged`** | as dispatch-stderr-fix |
| quota-resilience | AMBIGUOUS → **R3: `converged`** | as dispatch-stderr-fix |
| second-brain-target | `frozen` | DESIGN FROZEN (re-gate SHIP-WITH-FIXES) |
| session-lifecycle | `draft` | NEVER converged — three consecutive HOLDs; the held state is authoritative (STATE.md: "must stay held") |
| sprint-cadence | `frozen` | DESIGN + PLAN FROZEN, human-approved (ledger's "IN PROGRESS" prose is stale — resolve by the act) |
| statusline-decouple | `frozen` | DESIGN FROZEN (D162) |
| subagent-monitor | `frozen` | DESIGN FROZEN |

## Conductor rulings (2026-08-16)

- **R1 (acceptance amendment, D-a):** the frozen acceptance ("grep for non-enum first-words
  returns zero") passes VACUOUSLY on the 15 key-absent ledgers — every one as fatal to the
  W3 fail-closed `ledger_status` predicate as free prose. The acceptance is amended to:
  **every grill ledger's `status:` is PRESENT and its first word is in the enum.** The task
  itself completes at its G4 scope (trust-model verified); corpus completion is the planning
  window's fold plus D-d's authoring-side fix.
- **R2 (D-b):** dispatch-seam already parses `absorbed` — off the fence-blocked list. Its
  routing target (`../trust-model/GRILL-LEDGER.md`) is PROSE-ONLY — **W3 input:** the
  `absorbed`-ROUTES-the-mint semantics need either a parseable `absorbed-into:` frontmatter
  field or a documented prose-resolution rule; ambiguous target ⇒ refuse-to-mint ⇒ park (E6).
- **R3 (D-c):** the three ambiguous ledger-as-contract specs take `converged` — the
  conservative value that never over-claims (`frozen` satisfies everything `converged`
  satisfies, so no mint is lost). Planning window may upgrade any of them to `frozen` by
  recording the freeze act it finds.
- **R4 (D-d):** the root cause is the authoring format doc —
  `skills/plan/kata-grill/resources/DECISION-LEDGER.md` prescribes no document frontmatter
  at all, so the drift regrows on every new grill. The frontmatter block (`spec:` ·
  `status:` enum · `opened:`) is added to that resource in **W4 authoring-skills-migration**
  (ownership amendment G5, recorded — the grill-close status-write duty is already that
  task's; the resource is its companion surface).
- **R5 (D-e):** stale ledger-body prose vs a later recorded act resolves BY THE ACT; the
  frontmatter is the single source of truth the enum establishes.
