---
title: "Capability-aware agent assignment — detect the target's stack, route tasks to specialist agents (pre-grill BRIEF)"
status: BRIEF (pre-grill, NOT frozen — captured 2026-06-25 from operator direction)
date: 2026-06-25
spec: capability-aware-assignment
relates-to: multi-model-orchestration (resolves its flagged "multi-modal — separate brief?" open question) · install-portability (detection substrate) · kata-graph (repo structure) · debug-mode (primary consumer) · multi-model-orchestration (model/tool routing — the sibling axis)
tags:
  - kata/coordinate
  - assignment
  - polyglot
  - detection
  - specialist-agents
  - phase-5
---

# Capability-aware agent assignment — "multi-modal" specialist routing by detected stack

> **Pre-grill brief, not frozen.** Captures the operator directive (2026-06-25): *"multi-modal assignments for
> agents, based upon what is detected to be installed"* — a **big** Phase-5 item. Working name; the operator's
> word was "multi-modal" (clarify at grill — here it means **capability/stack-aware specialist routing**, not
> media modalities; the media sense stays parked in `multi-model-orchestration` out-of-scope).

## Why (the gap)
Today every worker is a generic coder running the same `kata-tdd`. A real polyglot repo (Python + TypeScript +
Rust + Terraform + Dockerfiles + SQL + CI YAML…) is built and debugged better by **agents specialized to each
language / file-class** — and which specialists a run needs is **discoverable from the target itself**, not
something the user should hand-configure. The harness already knows *where* things live (install-portability)
and the repo's *structure* (`kata-graph`); the missing layer is **detect the stack → assign the right specialist
to each task.**

## The two halves
1. **Detection.** Determine the target's **capability mix**: languages + frameworks + build/test tooling + config/
   IaC file-classes present in the footprint, plus what is actually **installed/available** in the environment
   (the install-portability seam). Output: a machine **capability manifest** (`.kata/capabilities.json`?) keyed to
   files/footprint regions. Likely composes `kata-graph` (file/symbol nodes already carry language) + a light
   environment probe (install-portability) — *verify these expose what's needed before claiming reuse
   (`protocol/reuse-claims.md`).*
2. **Assignment/routing.** Map each plan task to a **specialist agent** by the capability mix of its owned files:
   per-language coders, plus **config/context-file specialists** (IaC, CI, Dockerfiles, env). Specialists are
   **prompt-specializations layered on the spine** (per `prefer-in-context-over-new-python` — a specialist roster
   of system-prompt profiles, not a parallel code stack), selected by the orchestrator at dispatch.

## Key constraints (operator + spine)
- **Reuse the existing loop maximally** — this is a **routing/assignment layer over `kata-orchestrate`'s existing
  dispatch**, not a new orchestrator. Disjoint file-ownership, frontier dispatch, board/state all unchanged; the
  only addition is *which specialist profile* a task's worker gets.
- **Agnostic.** The specialist roster + detection are capability-driven, not host-driven; degrades to today's
  generic worker when the stack is unknown or single-language (BC).
- **Distinct from `multi-model-orchestration`.** That routes *which model/tool/host* runs a component; this routes
  *which domain specialist* builds a task. Orthogonal axes that compose (a Rust specialist could run on model B on
  host Quick). Resolve the relationship explicitly at grill.

## Open questions (for the grill)
- **Terminology** — "multi-modal" vs. "capability-aware" vs. "polyglot specialist routing." Confirm the operator's
  intent (language/tooling specialists, or literal media modalities too?).
- **Specialist roster** — which specialists at v1 (per-language coders + a config/context specialist), and are they
  pure prompt-profiles, or do any warrant tools (e.g. a language-server probe)? Default lean: prompt-profiles.
- **Detection source of truth** — `kata-graph` language tags vs. a dedicated probe vs. both; where the capability
  manifest lives and when it's (re)built (use-time projection, like the graph digest, not cached-stale).
- **Assignment granularity** — per-task (by owned-file mix) vs. per-file within a mixed task; tie-breaking when a
  task spans languages.
- **Interaction with footprint/ownership** — does specialist assignment ever want to *re-shape* the partition
  (split a mixed-language task so each slice gets one specialist)? Or assign post-partition only?
- **Relationship to multi-model-orchestration** — one combined routing layer, or two composable layers?

## Scope / sequencing
- **Depends on:** install-portability (environment detection) + `kata-graph` (structure/language). Phase-5 work.
- **Potential consumer (NOT a coupling):** `debug-mode` is a **self-contained mode** with its own in-mode
  specialist selection and does **not** depend on this layer (operator anti-bloat call, 2026-06-25). If both ship,
  they MAY converge on a shared specialist-profile mechanism — but neither blocks the other.
- **Pairs with:** multi-model-orchestration (the model/host axis) + testing-model.
- **Path:** grill → DESIGN → PLAN → build through the loop (contract-bearing).

## Out of scope (for now)
- Literal multimodal media pipelines (stays in `multi-model-orchestration` out-of-scope unless the grill pulls it in).
- New per-specialist Python stacks (specialists are prompt-profiles unless the grill proves a tool is load-bearing).
