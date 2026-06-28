---
title: "Recurrence-hardening — T2 PLAN (actionable-recurrence detector → auto-DRAFTED gated proposal)"
status: "FROZEN — freeze-gate kata-review HOLD→SHIP (2026-06-27; BC contradiction [run_id vs test_schema_round_trips] fixed via option-b → re-confirm SHIP)"
date: 2026-06-27
spec: recurrence-hardening
tier: T2 (recurrence→proposal loop; act-but-gated; = D101 proper)
source: >-
  Resolved T2 grill (operator-decided + adopted defaults, 7 points + the C/B invariant, LOCKED);
  D101 (recurrence hardening) · D102 + D112 (the two hand-done worked examples = the T2 output shape) ·
  D114 (the T1 manifest this builds ON); BUILT data layer tools/validation_misses.py + PLAN-t1-manifest.md;
  protocol/validation-misses.md (the T1 contract); recipe per PLAN-p2b.md structural template
---

# Recurrence-hardening — T2 PLAN

T2 turns the BUILT, observe-only validation-miss manifest (T1, D114) into an **act-but-gated** loop: a pure
**actionable-recurrence detector** (severity-aware, distinct-run-aware, handled-aware) clusters the manifest,
and when a class crosses threshold it surfaces a NOTE and **auto-DRAFTS a one-page hardening proposal** that is
**human-gated** — drafting is automated; authoring/merging the real guard stays human, routed through a
fresh-context freeze-gate `kata-review` → human merge gate. T2 **reads the manifest and authors a proposal**;
it changes no gate verdict, edits no skill/protocol/tool, and never merges its own proposal. **T3 (auto-author
the guard itself) is OUT OF SCOPE.**

T2 builds ON the frozen T1 surfaces (`validation_misses.recurrences/count_by_class/read_misses/miss_schema/
validate_miss/append_miss/_guard_path`, the 9-field schema, `guard_ref` null=open) — it extends, it does not
re-implement.

## Locked decisions (from grill) — these are LOCKED, introduce nothing beyond them

1. **Recurrence trigger.** Act on the **3rd** recurrence of a class; **2nd** for BLOCKER-severity classes.
   Cluster key = `responsible_skill` × `failure_class` (the existing `recurrences()` / `count_by_class`
   clustering). **Count DISTINCT runs/sessions, not raw rows** (false-recurrence control — two misses from one
   session ≠ a cross-run pattern). **Distinct-run identity = a nullable `run_id`** stamped per run by the
   orchestrator; the detector counts DISTINCT `run_id`, **falling back to `ts`** for legacy entries that have no
   `run_id`. (LOCKED — the robust, faithful implementation of "count distinct runs"; the fragile `ts`-only proxy
   is superseded by `run_id`-with-`ts`-fallback.)
2. **`failure_class` becomes a short CURATED ENUM (extendable)** in the miss schema for reliable clustering.
   **BC-CRITICAL:** the enum MUST include the classes already logged in `.planning/validation-misses.jsonl`
   (`honesty-fail-open`, `over-claim-fail-open`) plus the historically-seen classes (`exec-injection`,
   `phantom-reuse`, `dos-vector`, `stateful-hole`, `fail-open`, `over-claim`). **Existing logged misses must
   stay valid; existing tests must stay green.**
3. **Auto-DRAFT the hardening-proposal doc** when a class crosses threshold — **human-gated** (drafting
   automated; authoring/merging the real guard stays human).
4. **The proposal names the target surface**, defaulting to a **protocol contract + a mechanical test** (the
   D102 `reuse-claims.md`+validator-rule / D112 `exec-safety.md`+`test_exec_safety.py` shape). `responsible_skill`
   is the CLUSTERING key, **NOT necessarily the fix location** — the proposal proposes WHERE.
5. **Output artifact + gate.** A one-page hardening-proposal doc under
   `.planning/specs/recurrence-hardening/` (recurring class + evidence rows from the manifest + proposed target
   surface + guard text/test sketch) → fresh-context **freeze-gate `kata-review`** → **human merge gate**. The
   route is the **repo-hardening path — NOT `kata-promote`** (which governs external candidate skills; do not
   wire it).
6. **Trigger timing.** Run the detector right after the orchestrator's Final-gate validation-miss append hook
   (all modes), AND make it **on-demand-invocable**. Surface a newly-crossed class as a NOTE + auto-draft per #3.
7. **Handled-classes marker.** Once a class crosses threshold and a proposal exists (and/or a guard ships),
   mark the class **handled** so T2 stops re-proposing it AND so "did recurrence drop?" is answerable.

**Invariant (C/B boundary) — LOCKED.** T2 may READ the manifest and AUTHOR a proposal; it may NOT (i) change
any gate verdict, (ii) edit any skill/protocol/tool, or (iii) merge its own proposal. Every hardening stays a
deliberate, frozen, fresh-context-reviewed, human-approved change. **T3 (auto-authoring the guard itself) is
OUT OF SCOPE.**

## In scope (T2)
- A pure **actionable-recurrence detector** (NEW): severity-aware threshold (BLOCKER→2, else→3), distinct-run
  counting (distinct `run_id`, `ts`-fallback), handled-aware skipping, off-enum flagging. On-demand-invocable +
  run from the orchestrate hook.
- A **nullable `run_id` field** added to the miss schema (BC-safe; existing misses have none) — stamped per run
  by the orchestrator; the detector's distinct-run identity.
- A **BC-preserving curated `failure_class` enum** declared in the miss schema (the canonical clustering
  vocabulary; emit-guided + detector-normalized; **not** append-rejected — see §Enum-BC).
- A **handled-classes sidecar** (NEW, append-only) so the detector stops re-proposing and recurrence-drop is
  answerable.
- A **kata-improve extension** that auto-DRAFTS the one-page proposal doc + records the handled marker, and
  states the freeze-gate → human-merge route (NOT kata-promote).
- A **kata-orchestrate Final-gate wiring** that runs the detector right after the T1 append hook (all modes),
  surfaces a NOTE, and triggers the draft — **non-fatal** (never fails a build, never changes a verdict).
- The **`protocol/validation-misses.md` contract** extended for T2's act-but-gated posture (keeping T1's
  observe-only statement accurate).

## Out of scope (T3 / fast-follow — do NOT build here)
- **T3 — auto-authoring/self-applying the guard.** T2 DRAFTS a proposal only; it never writes the guard doc or
  the mechanical test, never edits a skill/protocol/tool (beyond its own proposal doc + the handled sidecar),
  and never merges. If a slice "needs" to write the guard → STOP (T2/T3 boundary).
- Changing any gate verdict, the `kata-evaluate`/`kata-review` verdict logic, or the `kata-promote` path.
- A hard append-time enum rejection in `validate_miss` (would break existing tests + drop real misses at the
  non-fatal append — see §Enum-BC and Risks).

## Enum-BC — how the curated enum preserves backward-compat (the crux, pinned)

Today `validate_miss` treats `failure_class` as "must be `str`" (no value check), and the existing tests use
throwaway slugs (`rce-unchecked`, `rce`, `dos`, `class-1`, `c`, `c1` …). A **strict** append-time enum check
would (a) break ~10 existing test fixtures and (b) — worse — **drop real misses** at the orchestrator's
non-fatal append whenever an LLM emitter picks a slightly-off slug (a `ValueError` from `append_miss` is caught
and NOTE'd, the miss silently lost). Losing signal is the opposite of the observe-only logging goal.

**Soft enum is therefore the RIGHT design, not a BC compromise** (conductor-CONFIRMED): the load-bearing reason
is signal preservation — a hard reject at the non-fatal append would silently discard a genuine miss over a
vocabulary typo. BC (existing data + behaviour) is satisfied as a bonus, but the primary rationale is "never
drop a real miss." Concretely:
- `validation_misses.py` gains a published, extendable constant
  `_FAILURE_CLASS_VALUES = frozenset({honesty-fail-open, over-claim-fail-open, exec-injection, phantom-reuse,
  dos-vector, stateful-hole, fail-open, over-claim})` and `miss_schema()["failure_class"]` gains an `"enum"`
  key listing it (exactly as `severity`/`what_caught_it` already publish `enum`).
- `validate_miss` is **UNCHANGED for `failure_class`** (still "must be `str`") → the enum adds **no** value
  rejection: existing free-string misses (`rce-unchecked` etc.) and both logged misses stay valid. (Adding the
  `"enum"` key UNDER `failure_class` changes no top-level schema key, so it alone touches no test.)
- A NEW non-blocking helper `validation_misses.is_known_class(failure_class) -> bool` exposes membership; the
  **detector** uses it to flag off-vocabulary clusters ("clustering may be unreliable") instead of dropping
  them, and the **emit path** (kata-review RUBRIC + `protocol/validation-misses.md`) directs reviewers to pick
  `failure_class` FROM the enum — that is where clustering reliability is actually earned.
- **Extending the enum** = add a member to `_FAILURE_CLASS_VALUES` + note it in `protocol/validation-misses.md`.
  This only ever WIDENS acceptance → always BC-safe.

**BC framing (honest, freeze-gate-corrected).** The published `miss_schema()` must not lie about its field set,
so adding `run_id` makes it a **10-field** schema — and `test_schema_round_trips` asserts the schema's KEYS
against a hardcoded field set. Therefore the BC claim is **NOT** "existing tests untouched." The honest claim is:
**existing DATA stays valid** (every `run_id`-less + free-string miss still validates) **and existing BEHAVIOUR
is unchanged** (no verdict logic changes; `validate_miss` still accepts any-str `failure_class` and treats
`run_id` like `guard_ref`); **the ONLY test edit is updating `test_schema_round_trips`'s expected field set
9→10 to include `run_id`** — an intentional, documented schema extension, not a regression. The `enum`-key
addition under `failure_class` is independently BC-safe (it changes no top-level key). `test_validate_extra_key_
rejected` uses a genuinely-unknown field name (e.g. `extra_field`/`sneaky`), so adding `run_id` to the known set
does **not** weaken it — it still rejects truly-unknown keys.

## Distinct-run counting — `run_id` with `ts`-fallback (LOCKED implementation)

Grill #1 LOCKS "count distinct runs/sessions, not raw rows." The frozen 9-field schema carried no explicit
run/session id, and a `ts`-only proxy is too fragile (it depends on per-emit-batch stamping discipline).
**Resolution (conductor, encoded LOCKED):** add a **nullable `run_id`** to the miss schema and count distinct
`run_id`:

- **Schema (S1):** `run_id` joins `_NULLABLE_STR_FIELDS` (alongside `guard_ref`/`decision_ref`) — `str | None`,
  missing-key allowed, AND a `miss_schema()` entry (the published field set, now 10 fields). **Data-BC-safe:**
  existing `run_id`-less misses still validate; the single test consequence is the `test_schema_round_trips`
  field-set edit (9→10) — see §Enum-BC BC framing.
- **Stamping (S3):** the **orchestrator stamps one `run_id` per run** when it appends misses at the Final gate
  (one id shared by every miss flagged in that run/batch). This is the *robust* version of "one ts per batch."
- **Counting (S1 detector):** distinct-run identity for a cluster = the number of **distinct `run_id`** among its
  entries; an entry **with no `run_id` falls back to its `ts`** (legacy entries keep working). So: two misses
  sharing a `run_id` count as ONE run; two with distinct `run_id` count as TWO; `run_id`-less entries fall back
  to `ts`. **NOTE — the two real logged misses do NOT exercise this within-cluster fallback:** they sit in
  DIFFERENT clusters (`kata-debrief::honesty-fail-open` vs `kata-debrief::over-claim-fail-open`), so each cluster
  trivially has one entry and the detector correctly never trips. The within-cluster distinct-run / `ts`-fallback
  behaviour is proven with **synthetic fixtures** (a 3-rows-but-1-distinct-`run_id` cluster and a
  3-rows-but-1-distinct-`ts` cluster), per S1 acceptance — not with the two real rows.

This is the faithful implementation of the locked decision (a robust run identity), **not** a new decision.

## Architecture split (the recipe — pure engine vs LLM-judgment skill vs wiring)
- **`tools/recurrence_detect.py` (NEW engine, S1)** + the BC-safe enum addition to `tools/validation_misses.py`
  + the handled sidecar I/O. Pure, injectable, mutation-proof decision logic: cluster → distinct-run count →
  severity-aware threshold → handled-aware skip → off-enum flag. **No subprocess, no eval, no exec.** It
  consumes manifest + handled records as plain dicts and returns verdict dicts.
- **`kata-improve` extension (NEW sub-mode, S2)** — the LLM-judgment author of the one-page proposal: takes an
  actionable recurrence, drafts the proposal doc (cluster + evidence rows + proposed target surface + guard
  text/test sketch + the freeze-gate→human-merge route), and appends the `proposed` handled marker. It calls
  the engine for every deterministic decision; it never re-clusters or re-thresholds in prose.
- **`kata-orchestrate` Final-gate wiring (S3)** — right after the T1 append step, run the detector over the
  manifest + sidecar; per newly-actionable cluster, surface a NOTE and trigger the S2 draft. **Non-fatal**,
  all modes; also documented as on-demand-invocable.

### exec-safety posture (mandatory — `protocol/exec-safety.md`)
**No new execution sink is introduced by T2.** Confirmed against the contract:
- `tools/recurrence_detect.py` is **pure decision logic** — clustering, integer counting/compare, set
  membership. It **spawns no subprocess and calls no `eval`/`exec`** (assertable by source scan in its test,
  re-asserting the T1 posture for the new module). **No new registry row.**
- The handled-sidecar writer `append_handled` is a **file append only** (same shape as the existing
  `validation_misses.append_miss`): a `..`-guarded path (CWE-23, mirror `_guard_path`) compiled to a normal
  file write — **no subprocess/eval**. No new sink.
- The S2 proposal draft is a skill **Write** (kata-improve already holds `Write`) — authoring a `.md` doc +
  appending a JSON line. No execution surface.
- `test_exec_safety.py` is unaffected (AST scan finds no new `shell=True`, no new sink). Any new Python is
  pure + mutation-proof + **Snyk-scanned** per CLAUDE.md.

## Slices (disjoint file ownership)

### Slice S1 — recurrence detector engine + BC-safe enum + handled sidecar  *(Python; pure, mutation-proof)*
**Owns:**
- `tools/recurrence_detect.py` (NEW)
- `tools/tests/test_recurrence_detect.py` (NEW)
- the schema additions to `tools/validation_misses.py` — the enum (constant + `miss_schema()` enum
  key + `is_known_class`) AND the **nullable `run_id` field** (added to `_NULLABLE_STR_FIELDS` + a `miss_schema()`
  entry, making the published field set 10 fields) — and the matching additions in
  `tools/tests/test_validation_misses.py` (mostly NEW tests; **plus ONE required edit** — bump
  `test_schema_round_trips`'s expected field set 9→10 to include `run_id`. This is the single existing-test edit,
  an intentional schema extension; all other existing tests stay green untouched. See §Enum-BC BC framing.)

**Surfaces (public, cite-able by name per `protocol/reuse-claims.md`):**
- `validation_misses._FAILURE_CLASS_VALUES` — extendable `frozenset` of the 8 LOCKED enum members.
- `validation_misses.is_known_class(failure_class: str) -> bool` — membership; NON-blocking (BC: `validate_miss`
  still accepts any `str` for `failure_class`).
- `validation_misses.miss_schema()["failure_class"]["enum"]` — the published curated vocabulary.
- `validation_misses` schema gains a **nullable `run_id`** (`str | None`, in `_NULLABLE_STR_FIELDS` +
  `miss_schema()` → 10-field published set): the per-run identity the orchestrator stamps; `validate_miss` treats
  it like `guard_ref` (str or None, missing-key allowed) → **existing `run_id`-less misses stay valid**; the
  published schema honestly lists it (the one test consequence is the `test_schema_round_trips` 9→10 edit).
- `recurrence_detect.distinct_run_counts(misses, *, run_id_key="run_id", fallback_key="ts") -> dict` — per
  cluster (`f"{responsible_skill}::{failure_class}"`), the count of **distinct run identities**: an entry's
  identity is `entry["run_id"]` when present/non-null, **else `entry["ts"]`** (legacy fallback). NOT raw rows.
  Reuses the T1 clustering convention (`count_by_class` key shape).
- `recurrence_detect.cluster_severity_tier(misses_for_cluster) -> str` — `"BLOCKER"` if any entry's
  `severity == "BLOCKER"`, else the highest of `MAJOR`/`MINOR`. Drives the threshold.
- `recurrence_detect.actionable_recurrences(misses, handled, *, default_threshold=3, blocker_threshold=2,
  run_id_key="run_id", fallback_key="ts") -> list[dict]` — the **severity-aware / distinct-run / handled-aware**
  detector (distinct-run identity via `distinct_run_counts`, run_id-with-ts-fallback). Per cluster:
  threshold = `blocker_threshold` if BLOCKER-tier else `default_threshold`; **actionable** iff
  `distinct_runs >= threshold` AND the cluster key is NOT in `handled`. Each result:
  `{key, responsible_skill, failure_class, distinct_runs, raw_count, severity_tier, threshold,
  off_vocabulary: bool, evidence: [rows]}` (`off_vocabulary` = `not is_known_class(...)`).
- `recurrence_detect.read_handled(path) -> list[dict]` — parse the handled sidecar (skip malformed lines;
  absent ⇒ `[]`; mirrors `read_misses`).
- `recurrence_detect.append_handled(record, path) -> bool` — validate + append one JSON line to the sidecar;
  `..`-guarded (CWE-23, mirror `_guard_path`); **raises `ValueError` only on `..`/malformed; returns `False`
  (never raises) on I/O failure** (mirrors the `append_miss` non-fatal BC contract). Record schema:
  `{ts, key, responsible_skill, failure_class, status: "proposed"|"guarded", proposal_ref, guard_ref|null}`.
- `recurrence_detect.handled_schema() -> dict` — single source of truth for the sidecar record.
- `recurrence_detect.detect_from_paths(misses_path, handled_path, **kw) -> list[dict]` — thin I/O convenience
  for the **on-demand** + orchestrate-hook callers (reads both files, calls the pure core). No exec.

**Handled-classes mechanism (chosen — grill #7):** a **dedicated append-only sidecar**
`.planning/recurrence-handled.jsonl` (durable, committed; sibling of the manifest), NOT mutation of the
manifest. Rationale: the manifest is **append-only** (no update surface; setting `guard_ref` on prior rows
would rewrite committed lines, violating the T1 contract). Two marker statuses, with **distinct, LOCKED
ownership:**
- **`proposed` — appended by S2 (kata-improve) when it auto-drafts** the proposal (detector then skips that
  cluster → stops re-proposing). This is T2's only auto write into the sidecar.
- **`guarded` — appended by the human / kata-improve at guard-merge time** (with `guard_ref` + ts), **OUTSIDE
  T2's auto-scope. T2 NEVER marks a class `guarded` on its own** — that would be claiming a guard shipped, which
  only a human merge establishes. The `guarded` ts is the cutoff that makes **"did recurrence drop?"** answerable
  (count cluster misses after it).

The T1 per-entry `guard_ref` (null=open) is complementary — future misses of a guarded class reference the
guard — but the handled-GATING is driven by the sidecar (clean, append-only, no manifest mutation).

**Acceptance (default-FAIL, runnable):**
- **Data + behaviour BC:** `validate_miss(_valid_entry())` (default `failure_class="rce-unchecked"`, off-enum)
  still returns `[]`; both logged misses (`honesty-fail-open`, `over-claim-fail-open`) validate and are
  `is_known_class(...) is True`; **every existing `test_validation_misses.py` test stays green EXCEPT the
  single required `test_schema_round_trips` field-set edit (9→10, adding `run_id`)** — no behaviour/verdict logic
  changes.
- **Schema honesty (the round-trip edit):** the updated `test_schema_round_trips` passes against the **10-field**
  set including `run_id`; `set(miss_schema().keys())` == the 10 documented fields.
- **`test_validate_extra_key_rejected` still bites:** it uses a genuinely-unknown field name (`extra_field`/
  `sneaky`), so adding `run_id` to the known set does not weaken extra-key rejection.
- **Enum present:** `_FAILURE_CLASS_VALUES` ⊇ the 8 LOCKED members; `miss_schema()["failure_class"]["enum"]`
  lists them; `is_known_class("rce-unchecked") is False`.
- **`run_id` BC:** `run_id` is in `_NULLABLE_STR_FIELDS` + `miss_schema()`; a miss WITHOUT `run_id` validates
  (missing-key allowed); `run_id=None` validates; `run_id=42` (non-str) is rejected (mirrors `guard_ref`); the
  two existing logged misses (no `run_id`) stay valid.
- **Distinct-run control (run_id):** two misses sharing a `run_id` count as **ONE** run; two with distinct
  `run_id` count as **TWO**; a `run_id`-less (legacy) cluster of **3 rows but 1 distinct `ts`** is **NOT**
  actionable at default=3 while **3 distinct `ts`** IS (fallback path). (Mutation-load-bearing: distinct-run
  identity vs raw row count; and the run_id→ts fallback.)
- **Severity-aware:** a BLOCKER cluster with **2 distinct runs** IS actionable (threshold 2); a MAJOR/MINOR
  cluster with 2 distinct runs is NOT (threshold 3).
- **Handled-aware:** a cluster over threshold whose key has a `proposed` (or `guarded`) sidecar record is **NOT**
  returned (no re-proposal).
- **Off-vocabulary flag:** an over-threshold cluster with an off-enum `failure_class` is returned with
  `off_vocabulary: True` (flagged, never dropped).
- **Sidecar I/O:** `append_handled` is append-only (two appends → two lines, first preserved), raises
  `ValueError` on a `..` path and on a malformed record, and **returns `False` (does NOT raise) on an I/O write
  failure** (dir path); `read_handled` tolerates a malformed line + returns `[]` for an absent file.
- **No `eval`/`exec`/`subprocess` in `tools/recurrence_detect.py`** (assertable by source scan in the test).
- **Mutation non-vacuous** on: (a) the distinct-run count (distinct run identity vs raw row count) **and the
  `run_id`→`ts` fallback**, (b) the severity-aware threshold selection (BLOCKER→2 vs default→3), (c) the
  handled-aware skip, (d) the `>= threshold` comparison, and (e) the `..` guard in `append_handled`.

**depends_on:** none (reuses T1 surfaces by import; touches `validation_misses.py` additively).

### Slice S2 — kata-improve proposal-author sub-mode + contract extension  *(skill/docs; depends_on S1)*
**Owns:**
- `skills/meta/kata-improve/SKILL.md` (NEW sub-mode section + version bump + README index update)
- `protocol/validation-misses.md` (extend for the T2 act-but-gated posture; keep T1's observe-only statement
  accurate)

**Content — kata-improve "Recurrence-hardening proposal (T2)" sub-mode:** given an actionable recurrence (from
`recurrence_detect.actionable_recurrences`, cited by name), **DRAFT** a one-page proposal at
**`.planning/specs/recurrence-hardening/PROPOSAL-<failure_class>.md`** (LOCKED convention — one per recurring
class; the `proposed` sidecar marker references this path via `proposal_ref`) containing:
1. The recurring **cluster** (`responsible_skill × failure_class`, distinct-run count, severity tier, threshold).
2. **Evidence rows** from the manifest (the cluster's entries — `ts`, `mode`, `what_conformance_missed`,
   `what_caught_it`, `decision_ref`; description-level only per the secret-hygiene convention).
3. **Proposed target surface** (grill #4) — **defaulting to a protocol contract + a mechanical test** (the
   D102 `protocol/reuse-claims.md`+`validate_skills` rule / D112 `protocol/exec-safety.md`+`test_exec_safety.py`
   shape). State explicitly that `responsible_skill` is the clustering key, **not necessarily the fix location** —
   the proposal NAMES where the guard should land.
4. A **guard text + test sketch** (the would-be contract clause + the mechanical test idea).
5. The **routing note**: fresh-context **freeze-gate `kata-review` → human merge gate**; **NOT `kata-promote`**;
   **NOT auto-applied** — drafting is automated, authoring/merging the real guard stays human (grill #3/#5).
- After drafting, **append a `proposed` handled marker** via `recurrence_detect.append_handled(...)` (cited by
  name) so the detector stops re-proposing the cluster.
- **Boundary (pinned in the sub-mode):** this sub-mode DRAFTS a proposal + records the marker ONLY. It does
  **not** write the guard doc/test, edit any skill/protocol/tool, or merge — that is the human path (and T3 is
  out of scope). It reuses kata-improve's existing `Write`; no new allowed-tool.
- **Footprint guard (invariant hardening — the highest-leverage drift point).** Because S3 auto-invokes this
  Write-capable sub-mode from the all-modes Final gate, the sub-mode's contract **pins its writable footprint to
  EXACTLY two paths**: `.planning/specs/recurrence-hardening/PROPOSAL-<failure_class>.md` (the draft) and
  `.planning/recurrence-handled.jsonl` (the `proposed` marker). It writes/edits **nothing else** — no skill, no
  protocol, no tool, no manifest row. Stated explicitly in the sub-mode body so a drafting run cannot drift into
  authoring the guard (the T2→T3 line).

**Content — `protocol/validation-misses.md` extension:** add a **"T2 — recurrence→proposal (act-but-gated)"**
section: the detector (`recurrence_detect.*`, cited by name) surfaces actionable clusters (severity-aware
3rd/2nd, distinct-run, handled-aware); kata-improve auto-DRAFTS a human-gated proposal under
`.planning/specs/recurrence-hardening/`; route = freeze-gate `kata-review` → human merge (NOT kata-promote);
the handled sidecar + its role in "did recurrence drop?"; the curated `failure_class` enum (emit FROM it for
reliable clustering; soft — never append-rejected). **Keep the T1 §Observe-only statement accurate** by scoping
it: T1 logging stays observe-only; T2 ACTS only by authoring an inert, human-gated proposal — it still changes
no gate verdict and mutates no skill. Pin the **C/B invariant** verbatim-in-spirit.

**Acceptance:**
- `validate_skills` green (no new skill — kata-improve edited; expect the same skill count, version bumped,
  README index updated).
- The sub-mode **cites `recurrence_detect.actionable_recurrences` and `recurrence_detect.append_handled` by
  name** (anchors resolve to S1 — no phantom reuse, per `protocol/reuse-claims.md`).
- The sub-mode + contract state **drafting-only / human-gated / freeze-gate→human-merge / NOT kata-promote /
  NOT T3** explicitly.
- **Footprint guard present:** the sub-mode explicitly declares its writable footprint = ONLY
  `PROPOSAL-<failure_class>.md` + `.planning/recurrence-handled.jsonl` (the `proposed` marker) — nothing else;
  verifiable by reading the sub-mode body.
- The contract's T1 §Observe-only statement remains accurate (scoped, not contradicted).

**depends_on:** S1 (cites the engine's real surfaces).

### Slice S3 — kata-orchestrate Final-gate detector wiring + `run_id` stamping  *(skill; depends_on S1)*
**Owns:** `skills/coordinate/kata-orchestrate/SKILL.md` — only the Final-gate region **at and immediately after
the existing T1 validation-miss append step** (the `Validation-miss emit` sub-bullet, item 6).

**Content — `run_id` stamping (LOCKED, grill #1):** at the Final-gate emit, the orchestrator **generates one
`run_id` for the run** (a per-run/batch identifier — e.g. a uuid or the run's identifier already in hand) and
includes it on **every** miss entry it appends for that run via `validation_misses.append_miss`. All misses from
one run/review thus share a `run_id` → the detector counts them as one run. (BC: the field is nullable; legacy
entries without it fall back to `ts`.)

**Content — recurrence detection:** after the T1 append step, add a **"Recurrence detection (T2 — non-fatal,
all modes)"** step:
1. Run `recurrence_detect.detect_from_paths(".planning/validation-misses.jsonl",
   ".planning/recurrence-handled.jsonl")` (cited by name).
2. For each **newly-actionable** cluster, surface a **NOTE** in the conversation (the cluster, distinct-run
   count, severity tier, threshold, `off_vocabulary` flag) AND trigger the **S2 kata-improve auto-draft** of the
   proposal (per grill #3/#6).
3. **Non-fatal — pure side-effect / proposal-only:** a detector error, a draft failure, or an `append_handled`
   `False` is surfaced as a NOTE; it **NEVER fails the build, changes any gate verdict, or applies a guard.**
4. Document that the detector is also **on-demand-invocable** (`recurrence_detect.detect_from_paths` / the
   kata-improve sub-mode can be run by an operator outside the Final gate).

**Acceptance:**
- `validate_skills` green.
- The wiring **stamps one `run_id` per run** onto every appended miss (verifiable by reading the emit step);
  misses from one run share it.
- The T2 step sits **right after** the T1 append sub-bullet and **cites `recurrence_detect.detect_from_paths`
  by name** (anchor resolves to S1).
- The step is **non-fatal** and **proposal-only** (NOTE + draft trigger; no verdict change, no guard
  application) — verifiable by reading the wiring.
- **BC:** absent any actionable recurrence ⇒ silent no-op; the step alters **no** gate verdict and is additive
  to the existing Final-gate flow (all modes).

**depends_on:** S1 (cites engine surfaces); forward-refs the S2 kata-improve sub-mode (name fixed by this plan).

## Wave DAG
```
ownership:
  S1: [tools/recurrence_detect.py, tools/tests/test_recurrence_detect.py,
       tools/validation_misses.py (enum + nullable run_id additions only),
       tools/tests/test_validation_misses.py (new tests + the one test_schema_round_trips 9->10 edit)]
  S2: [skills/meta/kata-improve/SKILL.md, protocol/validation-misses.md]
  S3: [skills/coordinate/kata-orchestrate/SKILL.md]   # only the Final-gate post-append region
waves:
  - wave: 1
    slices: [S1]
  - wave: 2
    slices: [S2, S3]
depends_on:
  S1: []
  S2: [S1]
  S3: [S1]
```
- **Wave 1:** S1 (the pure engine + BC-safe enum + handled sidecar — no deps; everything cites its surfaces).
- **Wave 2 (parallel):** S2 (skill + contract, cites engine by name) + S3 (orchestrate wiring, cites engine by
  name; forward-refs the S2 sub-mode). Disjoint files → no interdependency. Concurrency ≤2 workers; git
  worktrees; disjoint ownership verified before dispatch.

## Invariant (pinned — read before every slice)
T2 may **READ the manifest and AUTHOR a proposal**; it may NOT (i) change any gate verdict, (ii) edit any
skill/protocol/tool, or (iii) merge its own proposal. The detector is pure read+compute; the only writes T2
performs are **its own proposal doc + a `proposed` handled-sidecar record** — both inert until a human acts. **T2
NEVER appends a `guarded` marker** (that asserts a guard shipped — a human-merge-time act, outside T2's
auto-scope). Every hardening stays a deliberate, frozen, fresh-context-reviewed, human-approved change. **T3
(auto-authoring the guard itself) is OUT OF SCOPE** — if a slice "needs" to write the guard/test or edit a
skill/protocol/tool to be testable, STOP and escalate.

## Integration gate (after the frontier drains)
pytest green — incl. `test_recurrence_detect.py` **and `test_validation_misses.py` with its single intentional
edit** (the `test_schema_round_trips` field set 9→10 for `run_id`; every other existing test untouched and green —
the honest data/behaviour-BC proof, §Enum-BC) · `validate_skills` green (no new skill; kata-improve + kata-orchestrate edited, version bumps,
README regen `--write`) · **Snyk code scan on `tools/recurrence_detect.py` + `tools/validation_misses.py`**
(new/modified first-party Python — CLAUDE.md security rule; rescan-to-clean) · `test_exec_safety.py` still
green (**no new sink** — detector is pure; sidecar write is a file append like `append_miss`) · `gate_emit`
RESULT/footprint/mutation artifacts. Then fresh-context **`kata-evaluate`** (default-FAIL; exercises the
detector on seeded fixtures: distinct-run control, severity-aware 2nd/3rd, handled-aware skip; and the
draft→handled-marker seam) → **freeze-gate `kata-review`** → **operator merge gate.**

> **Note — two distinct gates.** The above is the GATE on building T2 itself. **The gate ON T2's runtime output
> (each auto-drafted proposal)** is grill #5: fresh-context **freeze-gate `kata-review` → human merge** — the
> repo-hardening path, **NOT `kata-promote`**.

## Risks / escalation triggers
- **T3 bleed (highest-risk scope creep).** If a slice starts writing the guard doc/test, editing a
  skill/protocol/tool (beyond the proposal doc + sidecar), or applying/merging a proposal — **STOP.** T2 DRAFTS
  a proposal and records a marker; nothing else.
- **Strict-enum BC trap.** Do **not** add a hard `failure_class` enum check to `validate_miss` — it breaks ~10
  existing test fixtures AND drops real misses at the non-fatal append (a `ValueError` is caught + NOTE'd, the
  miss lost). The enum is schema-declared + emit-guided + detector-flagged (soft). STOP if a slice "needs"
  hard rejection.
- **Distinct-run identity (resolved — keep it intact).** The detector counts distinct `run_id` (orchestrator-
  stamped, S3) with **`ts`-fallback** for legacy entries. Do **not** regress to a `ts`-only count, and do **not**
  make `run_id` non-nullable (that would break existing run_id-less misses + tests).
- **Append-only integrity.** The handled marker goes to the **sidecar**, never by rewriting manifest rows
  (setting `guard_ref` on prior lines would violate the T1 append-only contract). T2 writes only `proposed`;
  `guarded` is a human/merge-time act.
- **Non-fatal posture.** The Final-gate detector+draft step must never fail a build or change a verdict — a
  detector/draft error is a NOTE. (Mirrors the T1 append's non-fatal guarantee.)
- **Secret hygiene.** Evidence rows copied into a proposal stay description-level (no code payloads) — the
  proposal inherits the manifest's secret-hygiene convention.

## Judgment calls / resolved points (conductor resolutions folded; LOCKED)
All four points I flagged at draft are now RESOLVED and encoded above:
- **Distinct-run identity — RESOLVED:** add a **nullable `run_id`** to the miss schema (S1; `_NULLABLE_STR_FIELDS`,
  BC-safe); orchestrator **stamps one `run_id` per run** (S3); detector counts **distinct `run_id` with `ts`
  fallback** for legacy entries (S1). Encoded LOCKED (Locked decision #1 + §Distinct-run counting).
- **Soft enum — CONFIRMED:** schema-declared + emit-guided + detector-flagged; `validate_miss` unchanged for
  `failure_class`; never append-rejected. The load-bearing reason is **signal preservation** (a hard reject at
  the non-fatal append would drop a real miss), with BC as a bonus — stated in §Enum-BC.
- **`guarded`-marker ownership — CONFIRMED:** `proposed` appended by S2 (auto); `guarded` appended by the
  human/kata-improve at guard-merge time, **outside T2's auto-scope — T2 never marks guarded** (handled-sidecar
  section + Invariant).
- **Proposal filename — RESOLVED:** `.planning/specs/recurrence-hardening/PROPOSAL-<failure_class>.md` (one per
  recurring class; referenced by the `proposed` marker's `proposal_ref`) — encoded in S2.

No open return-to-grill items remain. (The freeze-gate `kata-review` still adversarially audits the plan as
usual.)
