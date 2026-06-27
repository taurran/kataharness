---
title: "Validation-miss manifest — the data layer for recurrence-hardening (pre-grill BRIEF addendum)"
status: BRIEF (pre-grill, NOT frozen) — addendum to BRIEF.md
date: 2026-06-27
spec: recurrence-hardening
decision: D101 (parent) — this is its data layer
relates-to: D99 (C-arc / Reason — sibling) · D74 (β LEARN feed) · D98 (the adversarial lens that produces the signal) · D112 (exec-safety) / D102 (reuse-claims) = hand-authored examples of the OUTPUT
tags:
  - kata/meta
  - learning
  - self-hardening
  - validation
---

# Validation-miss manifest — instrument the validation stack's blind spots

> **Operator directive (2026-06-27):** *"Create a manifest for ongoing issues that logs critical misses by our
> validation stack, and [eventually] addresses its own code to close gaps written by the writer. Part of the
> learning-loop mechanism borrowed from Hermes. Implement it alongside Debug Mode P2 — debug surfaces issues
> most often — and make it a **universal mechanism for all modes**."**

## What it is
A durable, append-only **manifest of validation-stack misses**: every time the **conformance gate**
(`kata-evaluate`) PASSES something that the **adversarial lens** (`kata-review`/D98), a **re-confirm**, or a
**human** later CATCHES, we log a structured entry. The manifest is the concrete **data layer** the
recurrence-hardening loop (D101) consumes — today that loop has a corpus in the abstract (the β LEARN feed over
DECISIONS/LESSONS/REVIEW); this gives it a **purpose-built, high-signal dataset about gate quality specifically**.

It is **universal — spine-level, all-modes.** The emit hook lives at the standing adversarial step that every
code/contract-bearing build runs (D98), not inside any one mode. Debug Mode is merely the **richest source**
(it red-teams whole codebases), so it is the natural first heavy exerciser — but the mechanism fires for every
mode's build.

## Why (the evidence is already overwhelming)
This session alone, the conformance gate PASSED and the adversarial/human lens CAUGHT, **5+ times**: D109 RCE,
D110 stateful-set hole, D111 holistic seams, the Debug-P1 DoS, and the chained-Pow on the *re-confirm*. Each was
recorded ad-hoc in DECISIONS as "D98 caught what conformance missed — Nth instance." **A human (the operator)
noticing "is this the first?" is the recurrence detector running in a person's head.** The manifest makes that
signal first-class, queryable, and feedable to the loop — so the harness, not the human, spots the pattern.

## The shape (composes existing pieces; verify-before-reuse per `protocol/reuse-claims.md`)
- **Data layer (NEW — this brief):** the miss-manifest + its schema + a tiny append/read/count tool.
- **Signal source (exists):** D98 `kata-review` findings + human catches + re-confirm findings.
- **Recurrence detector (NEW, T2 = D101 proper):** cluster manifest entries by (responsible-skill × class); ≥N ⇒ flag.
- **Proposal + gate (exists):** `kata-improve` proposes a permanent guard; `kata-promote` + D98 gate it (never auto-mutate — the B-trap; C/B invariant holds).
- **Output template (exists, hand-authored):** `protocol/reuse-claims.md`+validator-rule and `protocol/exec-safety.md`+`test_exec_safety.py` are exactly what an auto-proposed guard looks like.

## Tiers (lift)
- **T1 — manifest + emit hook (THIS build; small; universal).** A schema + `tools/validation_misses.py`
  (append/read/count) + a durable log + a spine hook: when D98/re-confirm/human catches a conformance escape,
  append `{run, mode, failure_class, responsible_skill, severity, what_conformance_missed, what_caught_it,
  guard_ref|open}`. **Doubles as a regression checklist** — each closed miss should already have a permanent test
  (as the 3 RCE misses do in `test_exec_safety.py`); the manifest records the linkage. T1 is **passive learning**:
  it logs + counts, it does not yet act.
- **T2 — recurrence detector → gated proposal (medium; = D101; needs the grill: threshold, class taxonomy,
  skill-attribution — the open questions in `BRIEF.md`).** Reuses `kata-improve`/`kata-promote`.
- **T3 — auto-author + self-apply the guard ("addresses its own code"; large; FUTURE, C-arc-gated).** The loop
  writes the guard doc+test itself and applies it — **gated, never autonomous** (the B-trap). Highest risk, lowest
  marginal value over a human writing a one-paragraph guard; deferred until C-arc maturity (the readiness exam, D99).

## Honest scope / guardrails
- **C/B invariant (LOCKED-class):** every hardening stays a deliberate, frozen, gated, audited change. A loop
  that silently rewrites its own skills is the B-trap — explicitly out of bounds for T1/T2; T3 only ever proposes
  into the existing human+fresh-context gate.
- **T1 is observe-only** (like the β LEARN feed) — no behavior change to any gate; it just records.
- Most of the value is **T1 + T2 (detect + propose)**; the auto-write (T3) is a convenience, not the point.

## Open questions (defer to the T2 grill; not needed for T1)
- Manifest location/lifecycle: durable committed corpus (accumulates across runs) vs per-run `.kata/`. (T1 leans
  **durable + committed** — it is a learning corpus, not a run artifact.)
- Failure-class taxonomy + recurrence threshold N + responsible-skill attribution (the parent BRIEF's questions).
- Privacy/secret-hygiene of logged snippets (repo is private; keep entries description-level, no payloads).
