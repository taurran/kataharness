---
title: "Debug Mode — a one-shot delivery mode that systematically debugs an existing codebase in confidence (pre-grill BRIEF)"
status: BRIEF (pre-grill, NOT frozen — captured 2026-06-24, enriched 2026-06-25 from operator direction)
date: 2026-06-25
spec: debug-mode
relates-to: modes-A4-version-up (the sibling mode it parallels) · capability-aware-assignment (its language specialists) · kata-diagnose (root-cause core) · install-portability + second-brain-learning (the onboarding/conversion story) · D98 red-team + Snyk security stack
tags:
  - kata/coordinate
  - delivery-mode
  - debug
  - onboarding
  - security
  - phase-5
---

# Debug Mode — point it at a codebase and debug in confidence

> **Pre-grill brief, not frozen.** Captures the operator direction (2026-06-24 capture; 2026-06-25 enrichment):
> *"a one-shot debug mode that acts like version-up but focuses entirely on debugging the code base in a
> systematic and thorough manner — assess all modules, tie-ins, logic, and promote coding efficiency. Point it at
> a codebase and tell it to debug in confidence: nothing broken, bugs fixed, via our debugging agents and
> security stack. A great first run for devs who install KataHarness and want to convert their code to the loop
> and live in our vault."* **Status: do NOT build yet — grill it first.**

## What it is
A **new delivery mode / run-shape, sibling to Version-Up**, with the **opposite intent**: where version-up
*advances* the code (feature add + version bump), Debug Mode **holds the feature set and structure fixed** and
runs a **deep systematic debugging pass** — find and resolve real defects, tighten logic, and promote coding
efficiency, **without changing behavior** (bugs out, structure preserved). Entry: a `delivery.shape == debug`
preset in `kata-bootstrap`/`kata-orchestrate`, paralleling version-up.

## The "debug in confidence" contract (the hard part)
The value proposition is **trust**: a dev points it at their repo and gets fixes, *not* breakage. That needs a
**fixed-structure / behavior-preserving gate** layered on the version-up regression discipline:
- **Footprint-scoped** (changes ⊆ touched files ∪ depth-1 reverse-deps, like version-up) — no sprawling rewrites.
- **No feature/structure drift** — assert the public surface / behavior is preserved (full baseline suite stays
  green) **except** the specific buggy behavior, which a **new regression test pins** before the fix (`kata-tdd`
  red→green per fix). *Open: how to assert "no structural drift while allowing the fix" — likely behavior-diff +
  surface-invariance checks, possibly graph-shape comparison via `kata-graph`.*
- **Security stack inline** — Snyk MCP scan + `kata-evaluate` (default-FAIL) + standing D98 `kata-review`
  (adversarial), so fixes don't introduce vulns or regressions.

## Reuse maximally (hard operator constraint)
A **new mode/preset over the existing Harness**, NOT a parallel stack. Expected reuse:
- **`kata-diagnose`** (root-cause — the obvious core) · **`kata-graph`** (structural map / blast-radius of the
  existing repo) · the **version-up footprint + no-regression gate** discipline · **`kata-evaluate`/`kata-review`**
  (default-FAIL + adversarial) · **`kata-tdd`** (regression test pinning each fix) · the **closeout/backout**
  surfaces (offered rollback). New = the systematic-sweep planning logic + the behavior-preserving gate.
- **Language-specialist debug agents** come from **`capability-aware-assignment`** (its primary consumer): per
  major language + config/context-file specialists, routed by the footprint's detected stack.

## Borrow from industry agentic debugging (research at grill)
Survey + adopt mechanisms (don't reinvent): the **`superpowers:systematic-debugging`** skill and **`gsd-debug`**
(both already installed locally), SWE-agent / SWE-bench agentic loops, OpenHands, Aider's debug flow, the
engineering-skills systematic-debugging. Distill their proven loop (reproduce → localize → hypothesize → fix →
verify) and graft it onto our gated spine — **keep our gates** (default-FAIL, no-self-cert, fresh-context review),
*verify any "we reuse X" claim before freezing it* (`protocol/reuse-claims.md`).

## The strategic payoff — the onboarding / conversion killer-app
This is the **ideal first run for a new KataHarness user**: install → point it at their existing repo → "debug in
confidence" → they get real value (a cleaner, bug-fixed, security-checked codebase) **before** committing to the
loop. That experience is the on-ramp to **converting the repo to the Kata Loop and moving into the vault**
(install-portability's bring-your-own-vault path + the second-brain story). Debug Mode = the demo that earns trust.

## Open questions (for the grill)
- The **behavior-preserving / no-structural-drift gate** — concrete assertion mechanism (behavior-diff? surface
  invariance? graph-shape compare?). This is the load-bearing design.
- **Systematic sweep planning** — how does it "assess all modules, tie-ins, logic" exhaustively yet stay
  footprint-bounded and one-shot? (loop-until-dry over modules? graph-ordered traversal? risk-ranked?)
- **"Promote coding efficiency"** — is that in-scope for a *debug* mode (behavior-preserving refactors) or does it
  blur into version-up? Where's the line between "fix a bug" and "improve the code"?
- **Specialist roster + routing** — depends on `capability-aware-assignment`; confirm the dependency direction.
- **Onboarding integration** — does Debug Mode get a dedicated `kata-bootstrap` first-run path tied to install?
- **Relation to the planning-approach↔delivery-mode alignment** item (BACKLOG) — Debug Mode is a 4th mode to align.

## Scope / sequencing
- **Depends on:** `capability-aware-assignment` (language specialists) + version-up discipline (built) +
  `kata-diagnose` (built). Naturally **after** capability-aware-assignment.
- **Path:** grill → DESIGN → freeze-gate review → build through the loop (contract-bearing). Not bundled.

## Out of scope (for now)
- Feature addition / version bump (that IS version-up — Debug Mode is the behavior-preserving sibling).
- Structural refactors that change the public surface (drift — explicitly forbidden by the confidence contract).
