# protocol/validation-misses.md — the validation-miss manifest contract

A cross-skill contract defining the **universal, observe-only validation-miss data layer** (T1 of
recurrence-hardening D101; the Hermes-borrowed learning loop's harness-facing sibling). This is the
canonical source of truth; responsible skills reference it by path (`protocol/validation-misses.md`),
never by `[[wikilink]]`.

## Purpose

Every time the conformance gate (`kata-evaluate`) PASSES something that the adversarial lens
(`kata-review`/D98), a re-confirm, or a human later CATCHES, the harness has a **validation miss** — a
gap in the gate that let a defect through. Recording these misses durably and systematically is the first
step of the recurrence-hardening loop (D101): make the signal first-class, queryable, and feedable to
the loop so the harness, not the human, spots the pattern.

The manifest is **universal — spine-level, all-modes.** The emit hook lives at the standing adversarial
step (D98) that every code/contract-bearing build runs; it is not owned by any single mode. Debug Mode
is the richest source (it red-teams whole codebases), but the mechanism fires for every mode's build.

**T1 is observe-only (passive learning, β-LEARN-feed posture):** it logs, counts, and surfaces — it
changes no gate behavior, never alters a gate verdict, and never mutates a skill. The
recurrence→proposal loop (T2) and auto-authoring guards (T3) are both deferred per
`BRIEF-validation-misses.md` (§Tiers).

## Entry schema

The schema is the single source of truth exported by `validation_misses.miss_schema`
(`tools/validation_misses.py`). All 9 fields:

| Field | Type | Description |
|---|---|---|
| `ts` | str | ISO8601 timestamp of the miss (e.g. `2026-06-27T12:00:00Z`) |
| `mode` | str | Run shape / mode (e.g. `debug`, `build`, `review`) |
| `failure_class` | str | Slug categorising the miss (e.g. `rce-unchecked`, `dos-vector`) |
| `responsible_skill` | str | The skill that should harden (e.g. `kata-evaluate`) |
| `severity` | str | `BLOCKER` \| `MAJOR` \| `MINOR` |
| `what_conformance_missed` | str | Description of the gap — see **Secret-hygiene convention** below |
| `what_caught_it` | str | `d98` \| `re-confirm` \| `human` |
| `guard_ref` | str\|null | Doc/test that closed the miss, or `null` when still open |
| `decision_ref` | str\|null | D-number reference (e.g. `D109`), or `null` |

Callers import `validation_misses.miss_schema` to stay DRY — do not duplicate this table in code.
Validate entries with `validation_misses.validate_miss` before appending.

## When to log

A miss entry is warranted when **ALL** of the following hold:

1. The preceding `kata-evaluate` run **PASSED** the build without flagging a finding.
2. A subsequent `kata-review`/D98 adversarial pass, a re-confirm, or a human review **confirms** a
   real defect (not a style preference or speculative concern).
3. The confirmed finding is one that a properly-calibrated conformance gate **should** have caught.

If `kata-evaluate` flagged the finding itself (NEEDS_WORK) and the builder fixed it, that is the gate
working correctly — no miss entry. Only a **conformance escape** (passed by the gate, caught later)
qualifies.

## Who writes it — the read-only seam

`kata-review` is fresh-context, **read-only** ("findings, not fixes" — no Write/Edit; structural per
`STANDARDS §1`). The reviewer does **NOT** write the manifest.

Instead:
- **Reviewer (flags, read-only):** for each confirmed finding that the preceding `kata-evaluate` had
  PASSED, mark it in the findings output as a conformance-escape with its `failure_class`,
  `responsible_skill`, and `severity`, per the entry schema above.
- **Orchestrator (appends, non-fatal):** at the Final-gate/D98 step, reads the review findings and
  calls `validation_misses.append_miss(entry, ".planning/validation-misses.jsonl")` for each flagged
  conformance-escape, wrapped non-fatally — a `False` return or any I/O error is surfaced as a NOTE
  and never fails the build (logging is a pure side-effect; BC: no gate verdict changes).

This respects the fresh-context read-only contract and keeps the write responsibility with the
orchestrator, which already writes gate artifacts at that step.

## Durable location

`.planning/validation-misses.jsonl` — append-only JSON-lines. The file accumulates across runs and
sessions (a **learning corpus**, not a per-run `.kata/` artifact) and is committed to the repo so the
signal persists across context resets.

## Secret-hygiene convention

The `what_conformance_missed` field **MUST** be description-level only — a human-readable sentence or
two explaining the gap class and why the gate missed it. **Never log code payloads, key material,
secrets, or verbatim code fragments** (the repo is private, but defence-in-depth applies: a
description that names the pattern is as useful as a snippet and carries far less risk if the corpus
is ever referenced outside).

This is a **convention**, not enforced programmatically by `validation_misses.validate_miss` (enforcing
it would require NLP heuristics). It is stated here and in the `miss_schema()` field description;
auditors must verify entries comply.

## Observe-only / C/B-invariant (T1 boundary)

T1 **records, counts, and surfaces** — it never changes a gate verdict or mutates a skill.

- `validation_misses.append_miss` — append only; no gate logic.
- `validation_misses.read_misses` — read only; never modifies the file.
- `validation_misses.count_by_class` — aggregate counts; passive.
- `validation_misses.recurrences` — surfaces classes at/over a threshold; T1 does NOT act on them.

**Any change to a gate verdict or skill based on manifest data is T2 (recurrence→proposal loop) or T3
(auto-author), both deferred.** See `BRIEF-validation-misses.md` §Tiers for the T2/T3 scope and the
C/B invariant (every hardening is deliberate, frozen, gated, audited — the B-trap is explicitly out of
bounds for T1/T2; T3 only ever proposes into the existing human+fresh-context gate).
