---
title: "Multi-Model Orchestration — grill decision ledger"
status: GRILL DONE → DESIGN FROZEN (2026-06-26); HOLD#1 (phantom-reuse) resolved · re-confirm SHIP · DESIGN.md compiled (3 minors folded in)
spec: multi-model-orchestration
grounding: RESEARCH.md (5 cited agents) · install-portability D104 · kata-orient/kata-handoff · kata-orchestrate · protocol/config.md
principle: keep it plain + the simplest model that works (memory grill-in-plain-terms); verify-before-reuse (protocol/reuse-claims.md)
---

# Multi-Model Orchestration — GRILL LEDGER

Goal: a frozen DESIGN for routing loop **roles** to different platforms/models (Claude=coder, Codex=validator,
Kiro=researcher…), orchestrator as central source of truth, shared filesystem as the handoff substrate.

> **Convergence HOLD#1 (2026-06-26) — resolved.** The fresh-context gate caught the project's signature failure
> mode: the ledger over-claimed **reuse** of `kata-orient` / `kata-orchestrate` / D104 / `kata.config` where the real
> surfaces don't expose it. Per `protocol/reuse-claims.md`, those are relabeled **NEW** below and scoped. The
> *decisions* did not change; the framing became honest + execution-grade.

## Verify-before-reuse pass (what's REUSE vs NEW) — closes HOLD#1
**Genuinely reused (verified surfaces):**
- git **worktrees** (`kata-worktree`) · the **board/state** files (`tools/kata_board.py`, `.kata/`) · the
  **concurrent rolling-frontier** dispatch *pattern* (`kata-orchestrate/SKILL.md:57-60`) · `kata-orient` as an
  **input** (it assembles an in-memory orientation, read-only) · `kata.config.bakeoff` `{n,lineage}` (`config.md:19`) ·
  the D104 installer's **flat-link routine** (`tools/kata_install.py`).

**NEW capabilities to build (NOT reuse — each scoped):**
- **N1 — the cross-model task-brief artifact** (`.kata/dispatch/<taskId>/BRIEF.json`). kata-orient/kata-handoff are
  *inputs* that feed it; the durable on-disk brief a non-Claude CLI worker reads is NEW (kata-orient is read-only/in-memory, no result-path field — `protocol/orientation.md:73-74`).
- **N2 — per-platform dispatch adapters** (`adapters/<platform>/dispatch`): shell out to `codex exec` / `kiro-cli` /
  `copilot` / `cursor agent`. kata-orchestrate ships only the **Claude** dispatch adapter today (`SKILL.md:14,72-74`); the CLI adapters are NEW.
- **N3 — the result normalizer + per-role result contract** (`.kata/dispatch/<taskId>/RESULT.json`). Maps each
  platform's output into the role's EXISTING result shape; the envelope + mapping are NEW.
- **N4 — the `roles` routing block in `kata.config` + `confirmedPlatforms` in settings.** Neither exists today
  (`config.md` has no `roles`/`routing` block); both NEW + must be validated by the fail-closed load-guard.
- **N5 — install `.agents/skills/` targeting + the sentinel confirm probe.** D104 links into `<host>/skills/` only and
  has no probe; both NEW.

## Resolved branches (LOCKED ledger)

### MM-1 — Five role groups; evaluator is a distinct lightweight inline scorer · LOCKED
- coder = `execute/` (kata-tdd). validator = adversarial cluster (red-team + anti-slop + grounding). researcher =
  `plan/kata-research`. orchestrator = `coordinate/` (plan-guardian). **evaluator** = a **lightweight scorer**,
  injectable at MULTIPLE loop points, scores → **accept · send-back · or "slot-machine" reroll** (rejection-sampling;
  reroll wires to `bakeoff` best-of-N — **the bakeoff key is verified `config.md:19`; the evaluator→bakeoff wiring is
  NEW/deferred**). Light+frequent → fits a fast/cheap model.
- Boundary: evaluator = conformance/scoring; validator = adversarial.
- **Flag (deferred to its own design pass):** evaluator **injection-points + score thresholds**. NOTE the coupling to
  MM-5 — the evaluator's accept/send-back/reroll verdict is one of the result shapes N3 must emit; that shape is
  defined here (below) even though the *threshold/placement mechanism* is deferred.

### MM-2 — Every role routable to any platform; coder stays a single agent · LOCKED
- Any role → any platform/model (incl. coder on non-Claude). Constraint (parallelism, not platform): one build TASK =
  one **sustained coder agent**, never fanned out (Anthropic). Fan-out stays available for validator/researcher.
  Default per-role = single-host (BC).

### MM-3 — Default all-on-host; multi-modal opt-in at preflight with per-role overrides · LOCKED
- **Default = all roles on the execution/host platform** (single-model, today's behavior).
- Preflight (`kata-initiate`) asks **"Make this run multi-modal?"** → if yes, user picks from the machine's
  `confirmedPlatforms` (N4/N5) then **assigns each role** → overrides on the all-same default; unset roles stay on host.
- **Config (N4, NEW):** a `roles` block in `kata.config`: `roles?: { "<role>": { platform, model, effort? } }`. The
  **fail-closed load-guard** (`kata-orchestrate/SKILL.md:34-39`) validates it: unknown role/platform → STOP+escalate;
  **absent ⇒ all-on-host (BC1 holds, single-host path unchanged).** `confirmedPlatforms: [...]` lives in `.kata-settings.json`.
- **MM-3↔MM-7 boundary (closes m2):** **preflight** — a role assigned to a platform NOT in `confirmedPlatforms` ⇒
  **hard block** (re-pick or run on host) before the run starts. **Mid-run** — a confirmed platform that *fails at
  dispatch* ⇒ **MM-7 fallback** (host + log + surface). Preflight = block; runtime failure = fallback.

### MM-4 — Dispatch = a NEW task-brief artifact + NEW per-platform CLI adapters · LOCKED
- **N1 task-brief artifact** (NEW) — the orchestrator writes `.kata/dispatch/<taskId>/BRIEF.json` into the task's
  worktree, fed BY kata-orient's orientation + the plan's task assignment. Schema (frozen):
  `{ taskId, role, platform, model, objective, inputs[], boundaries{ownedFiles[], sandbox: "read-only"|"write"},
  outputContract (→ MM-5 role result shape), resultPath, acceptanceCriteria }`.
- **N2 dispatch adapters** (NEW, `adapters/<platform>/`) — given the brief + worktree, shell out to the platform's
  headless CLI: `codex exec --cd <wt> --sandbox <ro|ww> --model M --output-schema <resultPath> -o <resultPath>` ·
  `kiro-cli chat --no-interactive --agent <role>` (brief instructs "write result JSON to resultPath") · `copilot -p …
  --allow-all-tools` · `cursor agent -p --output-format json`. Claude adapter = the existing Agent-tool path. Mutation
  role (coder) → write sandbox; read-only roles → read-only sandbox.
- kata-orient/kata-handoff are **inputs** to the brief, not the brief itself (honest per HOLD#1).

### MM-5 — Result = per-role result contract + a NEW normalizer (no single magic shape) · LOCKED
- Each role maps to its **existing** loop result shape; the worker's platform output is normalized INTO it:
  - **coder** → the gate `.kata/RESULT.json` (`gate_emit`) + the worktree diff.
  - **validator** → a SHIP/HOLD + findings verdict (kata-review shape).
  - **evaluator** → `{ score, decision: "accept"|"send-back"|"reroll", reason }` (the MM-1 verdict; reroll → bakeoff).
  - **researcher** → the escalation/finding shape `{claim, source, confidence, groundsToPlan}`.
- **N3 normalizer** (NEW) writes `.kata/dispatch/<taskId>/RESULT.json` = a thin envelope
  `{ taskId, role, platform, model, status, payload (the role shape above), raw (platform output, for audit) }`. The
  orchestrator + existing gates consume `payload` as the role's native shape. **"One shape the loop understands" was
  the hand-wave (B2) — replaced by this explicit per-role contract + envelope.**

### MM-6 — Concurrent background dispatch + join (reconciled with the frontier) · LOCKED
- **Corrects the HOLD#1/M1 contradiction:** cross-model workers are dispatched as **background subprocesses** (one per
  task, in its worktree) — **synchronous per task, concurrent across tasks**, consistent with the existing rolling
  frontier (`kata-orchestrate/SKILL.md:57-60`) and `.kata/concurrency.json`. The orchestrator launches, continues the
  frontier, and **collects each RESULT.json as its subprocess exits** (join/poll), with per-task **timeout +
  nonzero-exit** handling → MM-7. (A live ACP control channel + true cross-host async = deferred.)

### MM-7 — Routed-platform failure → fall back to host + log + surface · LOCKED
- A confirmed platform that fails/unavailable **at dispatch/mid-run** → run that role on the **host (Claude)**, record
  it, surface at the next gate/boundary. Repeated fallbacks for one platform → flag it unconfirmed for the run.
  (Preflight-unconfirmed is a *block*, not this fallback — see MM-3 boundary.)

### MM-8 — Install + confirm on all platforms (flat-link REUSE + `.agents/skills` & probe NEW) · LOCKED
- **Reuse:** the D104 flat-link routine. **NEW (N5):** (a) per-platform discovery-dir targeting — `.agents/skills/`
  (cross-tool standard) with per-platform fallbacks (RESEARCH §1), since D104 links into `<host>/skills/` only; (b)
  the **confirm probe** — install a **sentinel skill**, run the platform's headless CLI, verify it (i) discovered the
  skill and (ii) returned a parseable result; record success in `confirmedPlatforms`. No probe exists in D104 today.

### MM-9 — Platform/model routing × specialist routing = two layers that multiply · LOCKED
- This spec (platform/model per role) and `capability-aware-assignment` (language specialist per task) are separate,
  composable layers stacking at dispatch (Rust specialist as coder on Codex). Neither blocks the other.

### MM-10 — Determinism + cost governance · LOCKED
- Record per-role `{platform, model, effort, skillVersions}` in the **NEW** `roles`/run record (N4) for reproducibility;
  orchestrator keeps effort-scaling heuristics; payoff measured by `kata-loop-benchmark`. The ~15× token caveat is
  about fan-out, not single-agent routing — routing a role to a cheaper model can *reduce* cost; human approves routing at preflight.

### MM-11 — Orchestrator location: v1 = init/host platform; later configurable · LOCKED
- v1 orchestrator on the **init host** (Claude); it is a role whose platform is configurable later (enables Quick→Kiro/Codex
  delegation). v1 routes only **workers** cross-platform.

## Convergence
All branches resolved; HOLD#1 (phantom-reuse) closed by the verify-before-reuse pass (N1–N5 relabeled NEW + schemas
defined: task-brief, per-role result contract + envelope, roles config, concurrency model). **Re-confirm gate next**,
then FREEZE (kata-design-doc → DESIGN.md). Explicitly deferred to its own pass: the **evaluator injection-points +
score-threshold mechanism** (MM-1; its result *shape* is defined here, its *placement/thresholds* are not).
