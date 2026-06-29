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
changes no gate behavior, never alters a gate verdict, and never mutates a skill. T1's posture is
**unchanged** by T2: the T1 data layer still only logs/counts/surfaces. The recurrence→proposal loop
(**T2 — now BUILT**, see §T2 below) adds an **act-but-gated** layer ON TOP — detect → auto-DRAFT a
human-gated proposal → human-gated hardening — without weakening T1's observe-only guarantee. Auto-authoring
the guards themselves (T3) remains deferred per `BRIEF-validation-misses.md` (§Tiers).

## Entry schema

The schema is the single source of truth exported by `validation_misses.miss_schema`
(`tools/validation_misses.py`). All 10 fields:

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
| `run_id` | str\|null | Per-run identity stamped by the orchestrator at the Final-gate emit (one id shared by every miss from that run). The recurrence detector counts DISTINCT `run_id` per cluster (falling back to `ts` for legacy entries). Nullable + missing-key allowed — existing `run_id`-less misses stay valid. (D118) |

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

T1 **records, counts, and surfaces** — it never changes a gate verdict or mutates a skill. **This T1
statement stays accurate after T2 ships: the T1 data layer below remains observe-only; T2 (§T2) acts
only by authoring an inert, human-gated proposal — it still changes no gate verdict and mutates no
skill.**

- `validation_misses.append_miss` — append only; no gate logic.
- `validation_misses.read_misses` — read only; never modifies the file.
- `validation_misses.count_by_class` — aggregate counts; passive.
- `validation_misses.recurrences` — surfaces classes at/over a threshold; T1 does NOT act on them.

**Any change to a gate verdict or skill based on manifest data is T2 (recurrence→proposal loop) or T3
(auto-author).** T2 is now BUILT (§T2) — but it acts ONLY by drafting a human-gated proposal; it never
changes a gate verdict, edits a surface, or merges. T3 (auto-author the guard itself) remains deferred.
See `BRIEF-validation-misses.md` §Tiers for the T2/T3 scope and the C/B invariant (every hardening is
deliberate, frozen, gated, audited — the B-trap is explicitly out of bounds for T1/T2; T3 only ever
proposes into the existing human+fresh-context gate).

## T2 — recurrence→proposal (act-but-gated)

T2 turns the observe-only manifest into an **act-but-gated** loop: **detect → auto-DRAFT a proposal →
human-gated hardening**. It **reads the manifest and authors a proposal**; it changes no gate verdict,
edits no skill/protocol/tool, and never merges. The detector engine is `tools/recurrence_detect.py`; the
proposal author is the `kata-improve` "Recurrence-hardening proposal (T2)" sub-mode; the wiring is the
`kata-orchestrate` Final-gate hook.

### Detection (the pure engine)

`recurrence_detect.actionable_recurrences(misses, handled, *, default_threshold=3, blocker_threshold=2)`
(or the I/O convenience `recurrence_detect.detect_from_paths(misses_path, handled_path)`) clusters the
manifest by `responsible_skill` × `failure_class` and surfaces **actionable** clusters:

- **Severity-aware threshold** — act on the **3rd** recurrence of a class, **2nd** for BLOCKER-severity
  classes (`recurrence_detect.cluster_severity_tier` drives this).
- **Distinct-run counting** — counts DISTINCT runs, **not raw rows** (`recurrence_detect.distinct_run_counts`):
  identity = the per-run `run_id` the orchestrator stamps, falling back to `ts` for legacy entries. Two
  misses from one run count as ONE.
- **Handled-aware** — a cluster whose key already has a sidecar marker is skipped (no re-proposal).
- **Off-vocabulary flag** — a cluster whose `failure_class` is not in the curated enum is RETURNED with
  `off_vocabulary: True` (flagged "clustering may be unreliable"), **never dropped**.

This is pure read+compute — no subprocess, no eval, no exec; it acts on nothing.

### Drafting (kata-improve, human-gated)

For each actionable cluster, `kata-improve` auto-DRAFTS a one-page proposal at
**`.planning/specs/recurrence-hardening/PROPOSAL-<failure_class>.md`** (one per recurring class) containing:
the recurring cluster (distinct-run count, severity tier, threshold); the **evidence rows** from the
manifest (description-level only, per §Secret-hygiene convention); the **proposed target surface**
(defaulting to a **protocol contract + a mechanical test** — the D102 `protocol/reuse-claims.md`+
`validate_skills` rule / D112 `protocol/exec-safety.md`+`test_exec_safety.py` shape; `responsible_skill` is
the clustering key, **NOT necessarily the fix location**); and a **guard text + test sketch**. It then
records a `proposed` marker via `recurrence_detect.append_handled`. It **DRAFTS only** — it does not write
the guard, edit any surface, or merge.

### Routing

The drafted proposal goes to a fresh-context **freeze-gate `kata-review` → human merge gate** — the
**repo-hardening path, NOT `kata-promote`** (which governs external agent-distilled candidate skills,
outside this repo's `skills/` tree). Drafting is automated; authoring/merging the real guard stays human.

### Handled sidecar — `.planning/recurrence-handled.jsonl`

An append-only sidecar (sibling of the manifest; never mutates manifest rows) with two marker statuses of
**distinct, LOCKED ownership** (`recurrence_detect.handled_schema`):

- **`proposed`** — appended by `kata-improve` when it auto-drafts (T2's only auto write into the sidecar);
  the detector then skips that cluster.
- **`guarded`** — appended by the **human / kata-improve at guard-merge time** (with `guard_ref` + `ts`),
  **OUTSIDE T2's auto-scope. T2 never marks a class `guarded`.** The `guarded` `ts` is the cutoff that
  makes **"did recurrence drop?"** answerable (count cluster misses logged after it).

### Curated `failure_class` enum (soft — emit FROM it; never append-rejected)

`validation_misses.miss_schema()["failure_class"]["enum"]` (backed by `_FAILURE_CLASS_VALUES`) publishes
the canonical clustering vocabulary. The emit path SHOULD pick `failure_class` from this enum so clusters
are reliable — that is where clustering reliability is earned. It is **SOFT**: `validate_miss` still accepts
ANY non-None `str` (never append-rejected), so an off-vocab slug at the non-fatal append is **flagged** by
the detector (`is_known_class`), **never dropped** (signal preservation). Extending the enum = add a member
to `_FAILURE_CLASS_VALUES` + note it here; this only ever WIDENS acceptance → always BC-safe.

### C/B invariant (T2 boundary — LOCKED)

T2 may **READ the manifest and AUTHOR a proposal**; it may NOT (i) change any gate verdict, (ii) edit any
skill/protocol/tool, or (iii) merge its own proposal. The only writes T2 performs are **its own proposal
doc + a `proposed` handled-sidecar record** — both inert until a human acts. Every hardening stays a
deliberate, frozen, fresh-context-reviewed, human-approved change. **T3 (auto-authoring the guard itself)
is OUT OF SCOPE.**
