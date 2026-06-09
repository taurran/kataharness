---
name: kata-readiness
description: >-
  Fast pre-run readiness check: is the kata harness healthy (validator green, skills present, required tools
  on PATH) and is the target ready (git repo + clean tree, AGENTS/CONTEXT present, deps installable, an
  existing kata.config = re-entrant run)? Invoke from kata-bootstrap before composing a run, or standalone as
  an "is my kata environment ready?" doctor.
license: Apache-2.0
version: 0.1.0
category: coordinate
status: experimental
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Bash]
source: >-
  new (KataHarness original); pattern echoes environment "doctor" checks (e.g. brew/flutter doctor) — abstract,
  no external code adapted
tags:
  - kata/coordinate
  - kata/spine
  - readiness
  - preflight
---
# kata-readiness — is the harness + target ready to run?

A **read-only** check (no Write — it returns a verdict to its caller, it does not author artifacts). Two scopes,
each a checklist; report PASS / WARN / BLOCK per item and an overall verdict.

## Scope 1 — harness health
- Skills tree present and the validator is green (`tools/` → `uv run python validate_skills.py`, exit 0).
- Required host tools on PATH for the chosen run (e.g. `git`, the test runner, `uv`/language toolchain).
- A subagent-capable host is available (orchestrate's dispatch binding).

## Scope 2 — target readiness
- Inside a git repo with a **clean working tree** (uncommitted churn ⇒ WARN — execution wants a clean fork).
- `AGENTS.md` (and `CONTEXT.md` if the run plans against one) present, or flag that grill must create them.
- Declared dependencies are installable from an allowed registry (defers the actual install to pre-flight, D29).
- **Re-entrant detection:** if a `kata.config` already exists at the branch root, report it (its `mode`,
  `runShape`, `modules`) so bootstrap offers "same as last / step up / change shape" rather than cold-start.

## Verdict
Return a compact structured verdict (overall PASS/WARN/BLOCK + the per-item findings + the re-entrant
`kata.config` summary if any). **BLOCK** = a hard stop bootstrap must resolve before composing a run; **WARN**
= surface to the user but allow proceed. The check never installs, never writes, never mutates the repo.
