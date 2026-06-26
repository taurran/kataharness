---
title: "Multi-Model & Cross-Tool Orchestration — FROZEN DESIGN"
status: FROZEN (2026-06-26) — grill converged (HOLD#1 phantom-reuse resolved), re-confirm SHIP. Build PARKED (after install-portability extend).
spec: multi-model-orchestration
compiled-by: kata-design-doc (from GRILL-LEDGER.md + RESEARCH.md)
supersedes-scope: the BRIEF's "host-located orchestrator everywhere" → v1 = init-host orchestrator, workers cross-platform
---

# Multi-Model & Cross-Tool Orchestration — FROZEN DESIGN

> Route the loop's **roles** to different platforms/models (Claude=coder, Codex=validator, Kiro=researcher…), with the
> orchestrator as the central plan-guardian and the **shared filesystem as the handoff substrate**. Default is
> single-host (today's behavior); multi-modal is an opt-in. Every LOCKED decision traces to `GRILL-LEDGER.md`
> (MM-n) + `RESEARCH.md`; this DESIGN introduces no new decisions, only the schemas the freeze owes.

## 1. Requirements
- **R1** Assign each loop **role** to a platform/model; default = all-on-host (BC1).
- **R2** Run a worker on a non-Claude platform headlessly and collect a structured result — over the shared filesystem.
- **R3** Orchestrator stays the plan-guardian + central source of truth (spine #1, no drift), on the init host (v1).
- **R4** Install + **confirm** the harness on each platform before routing a role to it.
- **R5** Backward-compatible: config absent / no multi-modal ⇒ today's single-host Claude loop, byte-for-byte.
- **R6** Honest about churn: per-platform CLI surfaces are point-in-time; the confirm probe is the standing guard.

## 2. Components — REUSE vs NEW (verify-before-reuse, `protocol/reuse-claims.md`)
**Reused (verified surfaces):** git worktrees (`kata-worktree`) · board/state (`tools/kata_board.py`, `.kata/`) · the
concurrent rolling-frontier dispatch *pattern* (`kata-orchestrate/SKILL.md:57-60`) · `kata-orient` as an **input**
(read-only in-memory orientation, `protocol/orientation.md:73-74`) · `kata.config.bakeoff` `{n,lineage}` (`config.md:19`) ·
top-level `kata.config.skillVersions` (`config.md:20`) · the D104 installer flat-link routine (`tools/kata_install.py`).

**NEW capabilities (each scoped + schema'd below):**
- **N1 — cross-model task-brief artifact** `.kata/dispatch/<taskId>/BRIEF.json` (kata-orient/handoff are inputs to it).
- **N2 — per-platform dispatch adapters** `adapters/<platform>/dispatch` (kata-orchestrate ships only the Claude adapter, `SKILL.md:14,72-74`).
- **N3 — result normalizer + per-role result contract** `.kata/dispatch/<taskId>/RESULT.json`.
- **N4 — `roles` routing block in `kata.config` + `confirmedPlatforms` in `.kata-settings.json`** (neither exists today).
- **N5 — install `.agents/skills/` targeting + the sentinel confirm probe** (D104 links into `<host>/skills/`, no probe).

## 3. LOCKED decisions (from the ledger; structure locked, `[TUNABLE]` calibratable)
- **LD1 — Five role groups (MM-1):** coder (`execute/`), validator (red-team + anti-slop + grounding), researcher
  (`plan/kata-research`), orchestrator (`coordinate/`), **evaluator** = a lightweight inline scorer
  (accept · send-back · **reroll**→`bakeoff`), injectable at multiple loop points; light+frequent → fits a cheap model.
- **LD2 — Any role routable; coder stays a single sustained agent (MM-2).** Platform-binding ⊥ parallelism.
- **LD3 — Default all-on-host; multi-modal opt-in at preflight, per-role overrides (MM-3).** `kata-initiate` asks
  "Make this run multi-modal?" → assign each role from `confirmedPlatforms`. Absent ⇒ all-on-host (BC1).
- **LD4 — Dispatch = N1 task-brief + N2 per-platform CLI adapters (MM-4).** Files + headless CLI; mutation role =
  write sandbox, read-only roles = read-only sandbox.
- **LD5 — Result = per-role contract + N3 normalizer envelope (MM-5).** No single magic shape.
- **LD6 — Concurrent background dispatch + join (MM-6).** Synchronous-per-task, concurrent-across-tasks; reconciled
  with the rolling frontier + `.kata/concurrency.json`; timeout + nonzero-exit → LD7.
- **LD7 — Routed-platform failure → host fallback + log + surface (MM-7).** Preflight-unconfirmed = hard block (LD3 boundary).
- **LD8 — Install + confirm all platforms (MM-8/N5).** Flat-link (reuse) + `.agents/skills/` targeting + sentinel probe (NEW).
- **LD9 — Two orthogonal layers (MM-9):** platform/model routing × `capability-aware-assignment` specialist routing; they multiply.
- **LD10 — Determinism + cost (MM-10):** record per-role routing for reproducibility; effort-scaling heuristics; payoff via `kata-loop-benchmark`.
- **LD11 — Orchestrator on the init host in v1 (MM-11);** configurable later (Quick→Kiro/Codex).

## 4. NEW capability schemas (the freeze's contract — resolves the 3 compile minors)

### N1 — `.kata/dispatch/<taskId>/BRIEF.json` (the orchestrator writes; the worker reads)
```jsonc
{ "taskId": "t-007", "role": "validator", "platform": "codex", "model": "<id>",
  "objective": "…", "inputs": ["<paths/context>"],
  "boundaries": { "ownedFiles": ["…"], "sandbox": "read-only" | "write" },
  "outputContract": "<role result-shape name, see N3>",
  "resultPath": ".kata/dispatch/t-007/RESULT.json",
  "acceptanceCriteria": "…" }
```
Assembled FROM the `kata-orient` orientation + the plan's task assignment. The brief is the cross-model interop seam.

### N3 — `.kata/dispatch/<taskId>/RESULT.json` (the worker/normalizer writes; the orchestrator reads)
```jsonc
{ "taskId": "t-007", "role": "validator", "platform": "codex", "model": "<id>",
  "status": "completed" | "failed" | "timeout" | "fallback",   // ← DISPATCH OUTCOME (minor #1 resolved)
  "payload": { /* the role's EXISTING shape */ },
  "raw": "<platform output, for audit>" }
```
**Minor #1 resolved:** `status` carries the **dispatch outcome** (how the subprocess ended — drives LD6/LD7),
**distinct** from the role verdict which lives in `payload`. Per-role `payload`:
- **coder** → the gate `.kata/RESULT.json` shape (`gate_emit`) + a pointer to the worktree diff.
- **validator** → `{ verdict: "ship"|"hold", findings: [...] }` (kata-review shape).
- **evaluator** → `{ score: 0.0–1.0, decision: "accept"|"send-back"|"reroll", reason }`. **Minor #2 resolved:** score
  scale is **0.0–1.0** (RESEARCH §2 LLM-as-judge); the accept/send-back/reroll **threshold cutoffs are DEFERRED to
  the evaluator-mechanism pass** (MM-1 flag) — DESIGN depends on that pass for thresholds, not for the shape.
- **researcher** → `{ claim, source, confidence, groundsToPlan }` (the existing escalation/finding shape).

### N4 — config + settings surfaces
- `kata.config` (NEW block): `roles?: { "<role>": { "platform": string, "model": string, "effort"?: string } }`.
  Absent ⇒ all roles on host (BC1). **To-build:** a `roles` validation case is to be ADDED to the fail-closed
  load-guard (`kata-orchestrate/SKILL.md:34-39` currently validates mode/effort/tiers/modules only, NOT roles) so
  that an unknown role/platform or a platform ∉ `confirmedPlatforms` → STOP + escalate at preflight. The pure
  resolver `tools/kata_roles.py` already enforces this; wiring it into the orchestrator preflight is PARKED.
- `.kata-settings.json` (NEW key, D104): `confirmedPlatforms: ["claude", "codex", …]` (written by the N5 probe).
- **Minor #3 resolved:** per-run reproducibility = the **top-level `config.md:20` `skillVersions`** (skill versions,
  unchanged) **+** the per-role `roles` record `{platform, model, effort}`. The `roles` block does NOT duplicate
  `skillVersions`; together they pin a heterogeneous run.

### N2 — `adapters/<platform>/dispatch` (per-platform CLI launch + result capture)
Given (BRIEF.json, worktree): launch the headless CLI, capture the structured result into `resultPath`, normalize → N3.
- **codex** `codex exec --cd <wt> --sandbox <ro|ww> --model M -o <resultPath> "<brief prompt>"` — `-o` captures
  the worker's final JSON message to the result file; the prompt instructs JSON output. (A real per-role JSON-Schema
  file may later be passed to `--output-schema` for hard constraint — **not** the result path itself.)
- **kiro** `kiro-cli chat --no-interactive --agent <role>` (brief instructs "write result JSON to resultPath"); ACP later.
- **copilot** `copilot -p <brief> --allow-all-tools --model M`  ·  **cursor** `cursor agent -p --output-format json --model M`
- **claude** = the existing Agent-tool path. ⚠ Each flag set is a **June-2026 snapshot** (RESEARCH §0/§6) — **pin/verify at build**, not from this doc; the N5 probe is the standing guard.

### N5 — install + confirm
Extend `tools/kata_install.py` per-platform: flat-link skills into `.agents/skills/` (cross-tool standard) + per-platform
fallbacks. **Confirm probe:** install a sentinel skill → run the platform's headless CLI → assert it (a) discovered the
skill and (b) returned a parseable result → append the platform to `confirmedPlatforms`.

> **Implementation status (proof-slice, 2026-06-26):** the codex command builder + dispatch live in
> `tools/kata_dispatch.py` (not yet split into `adapters/<platform>/`); install flat-links into `<host>/skills/`
> (not yet `.agents/skills/`); the confirm probe verifies a generated token (not yet a sentinel-skill round-trip)
> and is restricted to **codex** (the only platform with a dispatch adapter). These are the DESIGN's target end-state;
> the slice proves the chain. The full-layer build closes the gaps (see §8).

## 5. Edges / integrity (resolved)
- **Preflight vs runtime (LD3/LD7):** role on an unconfirmed platform → **hard block** at preflight; a confirmed
  platform failing at dispatch → **host fallback + log + surface**. Repeated fallbacks → flag the platform unconfirmed for the run.
- **Missing/invalid RESULT.json** → task fails (default-FAIL preserved). **CLI timeout/nonzero** → `status:"failed"|"timeout"` → LD7.
- **Concurrency:** background subprocess per task in its worktree; orchestrator joins on exit; disjoint file-ownership = no races.
- **BC1:** `roles` absent ⇒ single-host Claude loop unchanged. The resolver (`kata_roles.resolve_roles`) defaults
  every role to host on absent; the orchestrator load-guard's `roles` validation is to-build (PARKED).

## 6. Acceptance criteria (default-FAIL, runnable) — for the eventual build
- `roles` absent ⇒ a run is byte-for-byte today's single-host loop (BC1 test).
- A `roles` block routing validator→codex: the orchestrator writes a schema-valid BRIEF.json, the codex adapter runs
  `codex exec` in the worktree, and a schema-valid RESULT.json (envelope + validator payload) comes back and is consumed.
- An unconfirmed platform in `roles` → load-guard STOP at preflight; a confirmed platform made to fail at dispatch →
  host fallback + a surfaced note (verifiable by forcing a nonzero exit).
- The N5 probe: the **host (Claude) is confirmed-by-construction** (it's where the run executes — no live probe);
  a **non-host** platform is confirmed by the sentinel probe (headless CLI returns the token) → appended to
  `confirmedPlatforms`. Testable via the injectable runner; codex/kiro best-effort pending the live CLI.
- Concurrent cross-model dispatch: two routed tasks run as concurrent background subprocesses (≠ serialized), evidenced in `.kata/concurrency.json`.

## 7. Test seams
- BRIEF/RESULT schemas → JSON-schema-validated on fixtures (pure). N2 adapters → injectable worktree + a stub CLI
  (assert the command line + that RESULT.json is captured) without a live host. N3 normalizer → unit-test each role
  payload mapping. Load-guard → fixture configs (valid/unknown-platform/absent). N5 probe → sentinel skill on Claude (real).

## 8. Build sequencing (PARKED — a decent lift)
1. **Extend install + confirm (N5)** — smallest, builds on D104; gives "installed + confirmed on all models".
2. **`roles` config + load-guard (N4)** + the **N1 BRIEF / N3 RESULT schemas** (pure, testable first).
3. **First dispatch adapter = Codex-as-validator (N2)** — highest value, safest role (read-only, structured verdict). Prove the cross-model loop end-to-end.
4. **Generalize** to researcher (Kiro, via write-to-file or ACP) + the rest; wire LD6 concurrency + LD7 fallback into `kata-orchestrate`.
5. **Deferred / fast-follow:** the **evaluator injection-points + thresholds** mechanism (MM-1 flag; supplies the evaluator score cutoffs) · a live ACP control channel · the **orchestrator-location** config (LD11, Quick→Kiro/Codex) · true cross-host async.
Build through the recipe (contract-bearing): freeze-gate → orchestrated build → kata-evaluate → D98 review → merge.
