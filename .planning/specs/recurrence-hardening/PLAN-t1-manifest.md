---
title: "Validation-miss manifest — T1 PLAN (universal, all-modes data layer)"
status: FROZEN — freeze-gate kata-review HOLD→SHIP (2026-06-27)
date: 2026-06-27
spec: recurrence-hardening
tier: T1 (manifest + emit hook; observe-only; passive learning)
source: BRIEF-validation-misses.md (D101 data layer); recipe per .planning/HANDOFF.md §5
---

# Validation-miss manifest — T1 PLAN

Build the **universal, observe-only data layer** for recurrence-hardening: a durable manifest that logs every
time the conformance gate (`kata-evaluate`) PASSED something the adversarial lens (`kata-review`/D98), a
re-confirm, or a human later CAUGHT. **Spine-level, all-modes** (the hook lives in the shared `kata-review`
RUBRIC, run by every mode's build); Debug Mode is the richest source, not the owner. T1 **logs + counts only —
it changes no gate behavior** (the β-LEARN-feed posture; C/B invariant: observe, never auto-mutate).

Out of scope (T2/T3, per BRIEF): the recurrence→proposal loop (T2 = D101 grill+build), auto-authoring guards
(T3, C-arc-gated). T1 stops at "logged, counted, surfaced."

## The manifest
- **Location (durable, committed corpus):** `.planning/validation-misses.jsonl` — append-only JSON-lines; it
  accumulates across runs/sessions (a learning corpus, not a `.kata/` run-artifact).
- **Entry schema:**
  ```json
  {
    "ts": "<ISO8601>", "mode": "<run-shape/mode>", "failure_class": "<slug>",
    "responsible_skill": "<skill that should harden>", "severity": "BLOCKER|MAJOR|MINOR",
    "what_conformance_missed": "<description — NO code payloads (private repo, secret hygiene)>",
    "what_caught_it": "d98|re-confirm|human", "guard_ref": "<doc/test that closed it, or null=open>",
    "decision_ref": "<D-number or null>"
  }
  ```

## Slices (disjoint ownership)

### S1 — manifest engine  *(Python)*
**Owns:** `tools/validation_misses.py` (NEW) + `tools/tests/test_validation_misses.py` (NEW).
**Surfaces (cite-able by name):**
- `miss_schema() -> dict` — the entry schema (single source of truth).
- `validate_miss(entry: dict) -> list[str]` — errors (empty = valid); required fields + enums
  (`severity ∈ {BLOCKER,MAJOR,MINOR}`, `what_caught_it ∈ {d98,re-confirm,human}`); rejects extra keys; rejects
  a `what_conformance_missed` that looks like a code payload is out of scope (description-only is a convention,
  not enforced — note it).
- `append_miss(entry: dict, path: str | Path) -> bool` — validate then append one JSON line (append-only; never
  rewrites prior lines); `..`-guarded path (CWE-23, mirror `_safe_abs`); creates the file if absent. **Error
  contract (pins the non-fatal BC guarantee): raises `ValueError` ONLY on a malformed entry or a `..` path (caller
  bugs); on an I/O write failure it returns `False` (logging is a pure side-effect — it must NEVER raise an I/O
  error into a gate/build).** Returns `True` on success.
- `read_misses(path) -> list[dict]` — parse all lines (skip a malformed line, never crash the reader); absent file ⇒ `[]`.
- `count_by_class(misses) -> dict` — aggregate counts keyed by the **string** `f"{responsible_skill}::{failure_class}"`
  (JSON-serializable — not a tuple key).
- `recurrences(misses, threshold=3) -> list[dict]` — the **passive** detector: classes at/over threshold
  (surfaces them; T1 does NOT act — that is T2).
**Acceptance (default-FAIL, runnable):** schema round-trips; `validate_miss` rejects each malformed shape
(missing field, bad `severity`/`what_caught_it` enum, extra key); `append_miss` is append-only (two appends →
two lines, first preserved), raises `ValueError` on a `..` path and on a malformed entry, and **returns `False`
(does NOT raise) on an I/O write failure** (e.g. an unwritable/dir path) — the tested non-fatal guarantee;
`read_misses` tolerates a malformed line + returns `[]` for an absent file; `count_by_class` + `recurrences`
aggregate correctly (a class with 3 entries is surfaced at threshold 3, not at 4). **Mutation non-vacuous** on
the threshold comparison in `recurrences` and the append-only guard.
**No exec surface** — pure data; no subprocess, no eval (nothing for `exec-safety.md`).

### S2 — contract + universal hook  *(docs/skills; depends_on S1)*
**The seam fix (freeze-gate MAJOR):** `kata-review` is **fresh-context, read-only** ("findings, not fixes" — no
Write). So the reviewer does **not** write the manifest. Instead: the reviewer **FLAGS** which confirmed findings
were conformance-escapes (a field/tag in its findings output, read-only); the **orchestrator** — which already
writes gate artifacts at the Final-gate/D98 step — **appends** them via `validation_misses.append_miss`, wrapped
**non-fatally** (a `False`/raised logging error is surfaced, never fails the build).
**Owns:** `protocol/validation-misses.md` (NEW) + an edit to `skills/evaluate/kata-review/RUBRIC.md` (shared rubric,
DRY across all 3 tier files) + the write-hook in `skills/coordinate/kata-orchestrate/SKILL.md` (Final-gate/D98
step) + a one-line pointer in `skills/evaluate/kata-evaluate/SKILL.md`.
- `protocol/validation-misses.md` — the contract: purpose, the entry schema (cite `validation_misses.miss_schema`
  by name), the **when-to-log rule** (*when a `kata-review`/D98 pass, a re-confirm, or a human catches a finding
  the preceding `kata-evaluate` PASSED → a miss*), **who writes it** (reviewer flags read-only → orchestrator
  appends, non-fatal), the durable location, the secret-hygiene convention (description-only, no payloads), and
  the **observe-only / C/B-invariant** note (T1 records; never changes a gate verdict or mutates a skill).
  Reference `BRIEF-validation-misses.md` for T2/T3.
- `kata-review/RUBRIC.md` — add a short **"Flag conformance-escapes" step** (universal, all tiers, **read-only**):
  for any confirmed finding the preceding `kata-evaluate` had PASSED, mark it as a conformance-escape in the
  findings output (with class/responsible-skill/severity), per `protocol/validation-misses.md`. NO write here.
- `kata-orchestrate/SKILL.md` — at the Final-gate/D98 step (where it already emits gate artifacts and receives
  review findings), **append each flagged conformance-escape** via `validation_misses.append_miss` (cite by name),
  **wrapped non-fatally** (logging never fails the build). Universal — every mode's build ends here.
- `kata-evaluate/SKILL.md` — a one-line pointer: the conformance gate's escapes are flagged by the subsequent
  review and recorded to the validation-miss manifest by the orchestrator (observe-only; no change to evaluate's verdict).
**Acceptance:** `validate_skills` green (40/0 — no new skill; RUBRIC is a resource); the RUBRIC flag-step is
present + **read-only** (no Write claim, consistent with the rubric's no-fixes contract); the orchestrate write-hook
cites `validation_misses.append_miss` by name (anchors resolve) and is **non-fatal**; the contract states
observe-only + reviewer-flags/orchestrator-writes + secret-hygiene; **BC: no gate verdict changes** (logging is a
pure side-effect).
**depends_on:** S1.

## Wave DAG
- Wave 1: S1.  Wave 2: S2 (depends_on S1). (Small build; ≤1 worker per wave is fine, or S1 then S2.)

## Integration gate
pytest green · `validate_skills` 40/0 · Snyk on `tools/validation_misses.py` · `gate_emit` artifacts ·
then fresh-context `kata-evaluate` → D98 `kata-review` (which — fittingly — can log its own first miss if it
finds one) → operator merge gate.

## Risks
- **Scope creep into T2/T3:** if a slice starts building the recurrence→proposal or auto-author loop, STOP — T1
  is observe-only (log + count + surface). The detector `recurrences()` SURFACES; it does not propose or mutate.
- **Secret hygiene:** entries are description-level; never log code payloads (private repo). Convention stated in
  the contract; `validate_miss` does not enforce content (noted as a limitation).
- **BC:** logging must be a pure side-effect — it must never alter a gate verdict or fail a build if the manifest
  write fails (a write error is surfaced, not fatal).
