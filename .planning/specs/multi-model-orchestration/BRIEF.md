---
date: 2026-06-19
spec: multi-model-orchestration
status: BRIEF — pre-grill, not frozen. A captured gap; the build needs its own grill → DESIGN → PLAN.
order: 2 of 3 (future-gap sequence — the cross-tool/model layer; builds on install-portability)
tags: [brief, future-gap, multi-model, adapters, acp, mindbridge, quick, orchestrator, handoff]
---

# Multi-Model & Cross-Tool Loop Orchestration

> **Quick plan brief.** This is spine #3 (agnostic via adapters) taken to its real conclusion: the loop's
> components can run in **different models / tools on a shared filesystem**, with the orchestrator located
> wherever the host dictates.

## Why (the gap)
Today the loop runs in one host (Claude). The vision: **run and hand off to agents running in other models on
the same file system** — because the durable, file-based handoff (spine #5) already makes the filesystem the
shared substrate. What's missing is the **routing layer** that decides *which model/tool runs which loop
component*, and *where the orchestrator itself lives*.

## Scope / what it must do
- **Host-located orchestrator.** The orchestrator runs **where the host dictates**:
  - **MindBridge** ⇒ orchestrator runs in **Quick** (Quick-based executions via **ACP**).
  - **Kiro / Claude** ⇒ the orchestrator runs **there** — the harness must *know* its host and place the
    orchestrator accordingly (not hard-code one).
- **Per-component model/tool routing.** Each loop component (grill · plan · execute · **evaluate** · **test** ·
  handoff · improve) can be operated by a **different agent/model**, all coordinating through the shared
  filesystem (board/state/handoff/escalation protocols already exist for this).
- **Validation & testing are first-class in the routing.** Explicitly allow assigning the **evaluation and
  testing** steps to their own agent/model (ties to [[testing-model]]) — not just the build steps.
- **Cross-model handoff on one filesystem.** A component finishing in model A hands off (via the durable
  artifact) to a component starting in model B, with no loss — the handoff/orient contract is the interop seam.

## Modularity / key constraints
- **Adapters own host specifics**; the agnostic core only defines the contracts (where the orchestrator binds,
  how a component is dispatched, the handoff/board/state schemas). MindBridge brings its **ACP/Quick** adapter;
  Kiro/Codex bring theirs.
- The orchestrator stays the **plan-guardian** regardless of where it runs (spine #1 — no drift). Sprint-blind
  orchestration (BC2) and the boundary router (D86) must survive cross-host placement.
- Must not break single-host runs (today's Claude-only path is the degenerate case: all components = one model).

## Open questions (for the grill)
- ACP as the cross-tool transport — what's the minimal capability set the core requires of any adapter?
- How does a run *declare* per-component routing (a `routing`/`models` block in the workspace binding or
  `kata.config`)? Default = single-host.
- "Multi-modal" proper (image/audio/vision components, e.g. a design step) — adjacent; in scope or a separate
  brief? (Flag, don't assume.)
- How does the orchestrator supervise an agent it cannot directly spawn (a different tool's process) — poll the
  board, or an ACP control channel?
- Determinism/reproducibility (`kata.config.skillVersions`, effort) across heterogeneous models.

## Dependencies & sequencing
- **Depends on [[install-portability]]** (must know where skills + operable dirs live before routing across
  hosts).
- **Pairs with [[testing-model]]** (a routed test/eval component is a concrete consumer of this layer).
- Realizes spine #3; supersedes/expands the v0.3 "adapters" roadmap milestone (Codex/Kiro + ACP/Quick).

## Out of scope (for now)
Building any specific non-Claude adapter end-to-end; the MindBridge/Quick internals (MindBridge owns those);
true multimodal media pipelines (revisit as its own brief if needed).
