---
title: "Second-brain learning — the Recall read-CONTRACT (v1) + files-only default adapter"
status: "FROZEN — freeze-gate kata-review HOLD→SHIP (2026-06-29; B1 open-contract-strings + B2 REQUIRED_PROTOCOL registration + N1/N2/N3 fixed; re-gate found 2 ownership-map inconsistencies → reconciled → conditional SHIP satisfied)"
date: 2026-06-28
spec: second-brain-learning
tier: "v1 — Recall read-contract (the interface) + files-only adapter ONLY"
source: >-
  Resolved Recall grill (operator-decided, 4 points + adopted defaults + the read-only invariant +
  the contract-vs-adapter split, LOCKED); BRIEF.md (the Second-brain / Recall(Librarian) / Reason(decider)
  three-part model, D99); protocol/engram.md (the reserved CONSULT backend seam + C1–C6 + engram.backend,
  D30 clean-room); protocol/config.md (engram.{backend,learnFeed,autonomy}); BUILT recall sources
  tools/validation_misses.py + tools/recurrence_detect.py (D114/D101); kata-initiate Phase 1b + Phase-2 mirror.
  Structural template: .planning/specs/recurrence-hardening/PLAN-t2.md.
---

# Second-brain learning — the Recall read-CONTRACT (v1)

v1 defines the **Recall read-CONTRACT** — the agnostic interface a second brain answers — and ships a
**files-only default adapter** that serves it from existing on-disk artifacts. Recall **serves**; it never
decides (that is `kata-reason`, a separate future grill) and never writes/distills (that is the β LEARN feed,
D74, emit-only — already covered). The contract is the **`engram.backend` CONSULT-read seam finally named**
(D30 clean-room): external stores (Obsidian / kiban / kagami) become downstream adapters behind this same
contract later, without re-contracting.

## Locked decisions (from grill) — introduce NOTHING beyond these

1. **Scope = define the Recall read-CONTRACT (the interface) + ship a FILES-ONLY default adapter** that serves
   it from existing on-disk artifacts. **DEFER:** external second-brain stores (Obsidian/kiban/kagami =
   downstream adapters behind the same contract), the `kata-reason` decider (separate future grill), and the
   write/distill half (already covered emit-only by the β LEARN feed, D74 — NOT re-opened here).
2. **Selection = tag/keyword match against the current goal/CONTEXT terms + recency**, and **ALWAYS surface
   open validation-miss recurrences.** **NO embeddings / NO RAG** (corpus is small tagged Markdown; explicit
   BRIEF stance).
3. **Output = a contract-shaped STRUCTURED PAYLOAD (record-level) rendered into a short RECALL BRIEF** that
   `kata-initiate` surfaces in its **Phase-2 mirror/grill** — **NEVER written into the frozen/pinned INTENT**
   (`protocol/intent.md` — INTENT is PINNED once set).
4. **Staleness = surface provenance + date, prefer recency, never silently trust — do NOT hard-enforce/filter**
   (the human/grill judges; mirrors engram C5 supersede-not-rewrite).

**Adopted defaults (LOCKED):**
- **Sources (v1):** `.planning/LESSONS-LEARNED.md` + `.planning/DECISIONS.md` + prior `INTENT.md` + the
  understand-map (`.kata/understand.md`) + `.planning/validation-misses.jsonl` +
  `.planning/recurrence-handled.jsonl`. DEFER: external vault, persona/engram fingerprint.
- **Trigger/slot:** `kata-initiate` **Phase 1b** (cold start + version-up loop-back) — the existing
  context-ingest point; the **grill is the consumer**. NOT per-task.
- **READ-ONLY invariant:** Recall surfaces material; it NEVER changes a gate verdict, auto-acts, mutates a
  skill/protocol/tool, or re-decides a LOCKED decision (engram invariants **C2** fail-to-human / **C4**
  LOCKED-guardrail / **C6** audit). Write/distill OUT; the decider OUT.
- **Agnostic fit:** a **PLUGGABLE backend behind the contract, files-only default**; external stores are
  deferred adapters (the reserved `engram.backend` CONSULT seam, D30 clean-room — finally named).

> **Contract-vs-adapter split (the load-bearing separation, pinned).** The **contract** = the payload schema +
> the selection/staleness/read-only rules (`protocol/recall.md` + `recall.recall_payload_schema()`). The
> **files-only adapter** = the default implementation that reads the six on-disk sources and populates the
> contract. An external store (Obsidian/kiban/kagami) is a *different adapter answering the same contract* —
> it drops in later **without re-contracting**. Keep the two strictly separate so the seam survives.

## In scope (v1)
- A pure **Recall engine + files-only adapter** (NEW `tools/recall.py`): read the six sources → tag/keyword +
  recency selection → ALWAYS-surface open validation-miss recurrences → provenance/recency/staleness tagging →
  assemble the **contract-shaped record-level payload**. Pure, injectable, mutation-proof; on-demand-invocable.
- The **Recall read-CONTRACT** as a published payload schema (`recall.recall_payload_schema()`) + a protocol
  contract doc (`protocol/recall.md`) so external adapters can implement it later.
- Naming **Recall as the read-side of the reserved `engram.backend` CONSULT seam** (a pointer section in
  `protocol/engram.md`; the D30 clean-room binding finally named) — keeping C1–C6 accurate.
- `kata-initiate` **Phase 1b + Phase-2-mirror** wiring: build the payload, render the **RECALL BRIEF**, surface
  it as read-only recall context the human/grill considers — **never** written into the frozen INTENT.

## Out of scope (DEFER — do NOT build here; STOP if a slice "needs" one)
- **External second-brain stores** (Obsidian / kiban / kagami) — downstream adapters behind this contract.
- **The `kata-reason` decider** (the Advisor) — a separate future grill. Recall **serves**, never decides.
- **The write/distill half** — the β LEARN feed (D74) emits synthesis pages, emit-only; v1 does NOT read-back,
  re-open, or extend it. Recall is **read-only**.
- **Embeddings / RAG / vector retrieval** — explicitly forbidden (small tagged-Markdown corpus, BRIEF stance).
- **Any write to `INTENT.md`** — PINNED (`protocol/intent.md`); the only INTENT writer stays
  `intent_scaffold.write_intent`. Recall feeds the mirror deliberation, never the `answers` dict.
- **Changing any gate verdict, autonomy dial, or LOCKED decision** — Recall is inert/advisory.

## Architecture split (the recipe — pure engine vs contract doc vs skill wiring)
- **`tools/recall.py` (NEW engine + files-only adapter, R1)** — pure functions: per-source parsers (markdown
  bullets / YAML frontmatter / JSONL) → candidate records; `match_score` (token overlap + recency component);
  `select_records` (tag/keyword + recency, no embeddings); `build_payload` (assemble the contract); the
  always-surface-recurrences branch **reuses `recurrence_detect.detect_from_paths` by name** (no re-clustering).
  **No subprocess, no eval, no exec.** Consumes file paths, returns the payload dict.
- **`protocol/recall.md` (NEW contract doc, R2)** + an `engram.md` pointer section — the **read-side interface**:
  the payload schema (cites `recall.recall_payload_schema()` by name), the selection contract (tag/keyword +
  recency, NO embeddings/RAG), the staleness rule (surface, never filter), the read-only invariant, the
  INTENT-never-written rule, and the contract-vs-files-only-adapter separation (so external adapters implement
  it later). Names Recall as the read-side of the reserved `engram.backend` CONSULT seam (D30).
- **`kata-initiate` Phase-1b / Phase-2-mirror wiring (R3)** — calls the engine, renders the RECALL BRIEF,
  surfaces it as read-only recall context in the mirror; pins the read-only + INTENT-never-written invariants;
  non-fatal/degrades when sources are absent.

## The Recall CONTRACT (the payload schema — record-level, pinned)
`recall.recall_payload_schema()` is the single source of truth (mirrors `validation_misses.miss_schema()` /
`recurrence_detect.handled_schema()`). The payload shape:

```
RecallPayload (schema_version "recall/v1"):
  schema_version : str            # "recall/v1"
  query          : { terms: list[str], kind: "project"|"research"|"version-up" }
  records        : list[RecallRecord]        # tag/keyword+recency-selected source items
  recurrences    : list[RecurrenceRecord]    # ALWAYS-surfaced open validation-miss recurrences
  provenance     : { backend: "files-only", sources_read: list[str], generated_ts: str }

RecallRecord:
  id            : str    # stable id = source_path + anchor/slug (NOT line numbers — anchors survive edits)
  source        : str    # OPEN adapter-supplied label (files-only uses "lessons"|"decisions"|"prior-intent"|"understand-map")
  source_path   : str    # the on-disk artifact path
  title         : str    # the surfaced item's anchor/name (e.g. "L7 — Converse, don't pop up")
  excerpt       : str    # short, description-level snippet (no code payloads)
  tags          : list[str]                 # matched tags/keywords
  match_score   : float                      # token-overlap + recency component
  provenance    : { produced_by: str, date: str|null, recency_rank: int }   # produced_by = OPEN adapter-supplied label
  stale         : bool   # date-based HINT only — NEVER a filter (the grill judges)

RecurrenceRecord (PROJECTED from recurrence_detect.actionable_recurrences — raw `evidence` dropped, see N3 below):
  key, responsible_skill, failure_class, distinct_runs, severity_tier, off_vocabulary, open: true
```

> **OPEN adapter-supplied labels (B1 — the contract-vs-adapter separation, pinned IN the schema).**
> `RecallRecord.source`, `provenance.backend`, and `provenance.produced_by` are **OPEN, adapter-supplied
> strings — SOFT, NOT value-enforced.** The files-only values (`"lessons"` / `"files-only"` / `"repo"`) are
> *that adapter's* labels, **not the contract's closed set.** `recall_payload_schema()` validates **SHAPE:
> required keys + types** (string-typed, present), **never a closed source/backend vocabulary.** An external
> Obsidian/kiban/kagami adapter MUST be able to build a payload with `source="obsidian-note"` /
> `backend="obsidian"` / `produced_by="kiban"` and have it validate — otherwise it would have to re-contract,
> breaking the "drops in later without re-contracting" pin. This is the deliberate *opposite* of
> `miss_schema()`'s `severity`/`what_caught_it` (which `validate_miss` HARD-enforces as closed enums): the
> Recall contract is **shape-validated, vocabulary-open.** Mirror only `miss_schema()`'s single-source-of-truth
> *schema-function* pattern, NOT its closed-enum enforcement, for these three fields.

> **RecurrenceRecord PROJECTS OUT raw evidence (N3).** `recurrence_detect.actionable_recurrences` returns each
> cluster with `evidence` = the **full raw miss dicts** (including `what_conformance_missed`, description-text
> by convention). The files-only adapter **projects these out** — a RecurrenceRecord keeps ONLY
> `key, responsible_skill, failure_class, distinct_runs, severity_tier, off_vocabulary, open`. Raw miss text is
> **never** carried into the payload or the brief (secret-hygiene + altitude — surface the recurring class, not
> the raw description).

**How the files-only adapter populates it:**
- `LESSONS-LEARNED.md` / `DECISIONS.md` → parse the `- **L<n>/D<n> — title.** body` bullets into RecallRecords
  (title = the anchor, tags = the bullet's terms, date from nearby/frontmatter, `produced_by="repo"`).
- prior `INTENT.md` → parse frontmatter (`goal`/`fixes`/`features`/`tags`) into RecallRecords (`source="prior-intent"`).
- `.kata/understand.md` → parse the understand-map sections (Changed/Added/Open questions) into RecallRecords
  (`source="understand-map"`, written by `kata-understand`).
- `.planning/validation-misses.jsonl` + `.planning/recurrence-handled.jsonl` →
  **`recurrence_detect.detect_from_paths(...)`** (REUSE) → `recurrences[]` (the always-surfaced open recurrences;
  threshold/handled-aware logic stays the detector's own — no new decision here).
- `provenance.sources_read` records exactly which of the six were present (tolerant; absent ⇒ skipped, no crash).

**The selection mechanism (no embeddings; N1 — overlap is a hard PREDICATE, recency only RANKS):**
`match_score(record, query_terms)` = case-insensitive **token overlap** between the query terms (current
goal/CONTEXT terms; for version-up, also the prior INTENT goal) and the record's tags + title + excerpt tokens,
**plus a recency component** (more-recent records boosted). `select_records` **GATES on token-overlap > 0 as a
predicate** — a record with zero overlap is **excluded**, no matter how recent; **recency only RANKS *among* the
records that already pass the overlap gate** (it never promotes a zero-overlap record in). **Recurrences bypass
selection entirely** (always included regardless of overlap). Recency **boosts/ranks, it never filters out**; a
stale but overlapping record stays in the payload with `stale=True`. No vector/embedding/RAG path exists
(assertable by source scan — no numpy/embedding import).

## How the RECALL BRIEF reaches the Phase-2 mirror WITHOUT writing the frozen INTENT
- `kata-initiate` **Phase 1b** (the existing context-ingest point — cold start + the version-up loop-back that
  already consumes the four loop-back inputs) calls `recall.recall_from_paths(...)` over the six sources to get
  the payload, then **renders a short RECALL BRIEF** (Markdown) from it.
- The brief is surfaced in the **Phase-2 mirror** as **read-only recall context** the human/grill weighs while
  editing the goal/setup. It is displayed, not stored.
- **INTENT.md is untouched:** the only INTENT writer remains `tools/intent_scaffold.py :: write_intent(path,
  answers)`, fed from the operator-confirmed `answers` dict (Phase 4/6). The recall brief feeds the human's
  **deliberation in the mirror**, never the `answers` dict and never the frozen file. INTENT stays PINNED
  (`protocol/intent.md`). This is the structural guarantee — Recall has no write path to INTENT.

## exec-safety posture (mandatory — `protocol/exec-safety.md`)
**Zero new execution sink introduced by v1.** Per slice:
- **R1 (`tools/recall.py`)** — pure file reads + token matching + payload assembly. **Spawns no subprocess,
  calls no `eval`/`exec`/shell** (assertable by source scan in its test, mirroring
  `recurrence_detect`/`drift_gate` `TestExecSafety`). Path reads are **`..`-guarded (CWE-23)** via a local
  `_guard_path` mirroring `validation_misses._guard_path` / `kata_settings._safe_*`; I/O failure is tolerant
  (returns `[]`/partial, never raises into the caller — mirrors `read_misses`). **No new registry row.** It
  reuses `recurrence_detect.detect_from_paths` (itself pure, no sink). New Python = pure + mutation-proof +
  **Snyk-scanned** per CLAUDE.md.
- **R2 (docs)** — `protocol/recall.md` + `engram.md` pointer; no code, no sink.
- **R3 (skill prose)** — `kata-initiate` keeps its read-leaning `allowed-tools`; it invokes the pure
  `recall.py`. No execution surface added.
- `test_exec_safety.py` stays green (AST scan finds no new `shell=True`, no new sink).

## Slices (disjoint file ownership)

### Slice R1 — Recall engine + files-only adapter  *(Python; pure, mutation-proof; NEW)*
**Owns:**
- `tools/recall.py` (NEW)
- `tools/tests/test_recall.py` (NEW)

**Surfaces (public, cite-able by name per `protocol/reuse-claims.md`):**
- `recall.recall_payload_schema() -> dict` — **THE CONTRACT**: single source of truth for `schema_version`
  (`"recall/v1"`), the RecallRecord field set, and the RecurrenceRecord field set. **Shape-validates** (required
  keys + types); `source`/`provenance.backend`/`provenance.produced_by` are **string-typed but OPEN** (no closed
  vocabulary — B1).
- `recall.match_score(record: dict, query_terms: list[str]) -> float` — token-overlap + recency component
  (pure; no embeddings).
- `recall.select_records(candidates: list[dict], query_terms: list[str], *, recency_key="date") -> list[dict]`
  — tag/keyword selection: **GATES on token-overlap > 0** (predicate), then recency only **RANKS among** the
  passers (recency never promotes a zero-overlap record in, never filters a passer out — N1).
- `recall.parse_lessons / parse_decisions / parse_intent / parse_understand(text|path) -> list[dict]` — the
  files-only adapter source parsers → candidate RecallRecords with provenance + date + tags.
- `recall.build_payload(query, records, recurrences, sources_read) -> dict` — assemble the contract-shaped
  payload (validates against `recall_payload_schema()`).
- `recall.recall_from_paths(*, lessons_path, decisions_path, intent_path, understand_path, misses_path,
  handled_path, query_terms, kind) -> dict` — the **files-only default adapter entry point**: tolerant reads
  of the six sources, **`recurrence_detect.detect_from_paths(misses_path, handled_path)` for recurrences**
  (cited by name), select, build payload. No exec; no write.
- `recall._guard_path(raw) -> Path` — `..` traversal guard (CWE-23; mirror `validation_misses._guard_path`).

**Reuses (verified real):** `recurrence_detect.detect_from_paths` (always-surface recurrences; it imports
`validation_misses.read_misses`/`is_known_class` internally — no re-clustering in `recall.py`). Degrades when
`recurrence-handled.jsonl` is absent (`read_handled` → `[]`, verified tolerant) — so R1 does NOT depend on the
recurrence-hardening T2 build shipping its sidecar.

**Acceptance (default-FAIL, runnable):**
- **Contract pinned:** `recall_payload_schema()["schema_version"] == "recall/v1"`; its RecallRecord/
  RecurrenceRecord field sets match the documented fields; `build_payload` output validates against it.
- **Contract is vocabulary-OPEN (B1 — mutation-load-bearing on the contract-vs-adapter separation):** a payload
  built with an **arbitrary external-adapter `source`/`backend`/`produced_by`** (e.g. `source="obsidian-note"`,
  `backend="obsidian"`, `produced_by="kiban"`) **validates** against `recall_payload_schema()` — the schema
  enforces shape/keys/types, NOT a closed source/backend vocabulary. (A builder who closes the set to the
  files-only labels FAILS this test — it is the guard that keeps "drops in later without re-contracting" real.)
- **Tag/keyword selection is a hard gate (N1):** a candidate whose tags/title overlap the query terms IS
  selected; a candidate with **zero** overlap is **NOT** — **including a zero-overlap-but-RECENT candidate, which
  is EXCLUDED** (recency ranks passers, it does not promote a non-match in) — unless it is a recurrence.
  (Mutation-load-bearing: the overlap>0 predicate gate vs recency.)
- **ALWAYS-surface recurrences:** a seeded open validation-miss recurrence appears in `payload["recurrences"]`
  **even with zero query-term overlap** (bypasses selection). (Mutation-load-bearing: the always-surface branch.)
- **RecurrenceRecord projects out raw evidence (N3):** a recurrence carries ONLY
  `key/responsible_skill/failure_class/distinct_runs/severity_tier/off_vocabulary/open`; the raw `evidence`
  miss dicts (and `what_conformance_missed` text) from `actionable_recurrences` are **absent** from the payload.
  (Mutation-load-bearing: the projection — no raw miss text leaks into the brief.)
- **Recency boosts, never filters:** of two equally tag-matched records, the more-recent ranks higher; an
  **old but matched** record is STILL in `records` (recency never drops it). (Mutation-load-bearing.)
- **Staleness is a hint, not a filter:** an old record gets `stale=True` and REMAINS in `records`.
  (Mutation-load-bearing: `stale` must not gate inclusion.)
- **Provenance:** every record carries `source_path` + `provenance.{produced_by,date,recency_rank}`;
  `payload["provenance"].sources_read` lists exactly the present sources.
- **No embeddings:** `tools/recall.py` imports no vector/embedding library; selection is token-overlap only
  (assertable by source scan).
- **Tolerant I/O:** an absent source ⇒ that source contributes `[]` candidates, no crash (mirror `read_misses`);
  a malformed line/section is skipped, never raises.
- **`..` guard:** a path containing `..` raises `ValueError` (CWE-23); a non-`..` I/O failure returns `[]`/
  partial (never raises into the caller).
- **No `eval`/`exec`/`subprocess` in `tools/recall.py`** (assertable by source scan — `TestExecSafety`).
- **Recurrence reuse by name:** `recall_from_paths` calls `recurrence_detect.detect_from_paths` (anchor
  resolves; no phantom reuse, no re-clustering in `recall.py`).
- **Mutation non-vacuous** on: (a) the `match_score` overlap predicate (overlap>0 gate, N1), (b) the recency
  component (ranks passers only), (c) the always-surface recurrence branch, (d) the `stale`-does-not-filter rule,
  (e) the `..` guard, (f) the vocabulary-OPEN schema (B1 — closing the source/backend set fails the external-
  adapter test), (g) the RecurrenceRecord evidence-projection (N3).

**depends_on:** none (reuses `recurrence_detect`/`validation_misses` by import only).

### Slice R2 — the Recall read-CONTRACT doc + `engram.backend` naming + validator registration  *(docs; depends_on R1)*
**Owns:**
- `protocol/recall.md` (NEW)
- `protocol/engram.md` (a pointer section only — name Recall as the read-side of the `engram.backend` seam)
- `tools/validate_skills.py` (add the `recall.md` entry to `REQUIRED_PROTOCOL` — the `engram.md` precedent, D74 BP2)

**Content — `protocol/recall.md`:**
1. **The payload schema** — the read-side interface (cites `recall.recall_payload_schema()` by name); the
   RecallRecord/RecurrenceRecord fields; `schema_version "recall/v1"`.
2. **The selection contract** — tag/keyword match against the current goal/CONTEXT terms + recency; **NO
   embeddings / NO RAG** (stated as a hard stance).
3. **The staleness rule** — surface provenance + date, prefer recency, **never hard-filter** (the grill judges;
   maps to engram **C5** supersede-not-rewrite).
4. **The read-only invariant** — Recall surfaces; never changes a gate verdict, auto-acts, mutates a
   skill/protocol/tool, or re-decides a LOCKED decision (engram **C2 / C4 / C6**). Write/distill OUT (β, D74);
   the decider OUT (`kata-reason`).
5. **The INTENT-never-written rule** — the brief feeds the Phase-2 mirror; `INTENT.md` stays PINNED
   (`protocol/intent.md`); `intent_scaffold.write_intent` remains the only INTENT writer.
6. **The contract-vs-files-only-adapter separation** — the contract is backend-agnostic; the files-only adapter
   is the default; an external adapter (Obsidian/kiban/kagami) answers the **same** contract and drops in later
   **without re-contracting**. Documents the implementation contract an external adapter must satisfy, **including
   the OPEN adapter-supplied-labels rule (B1):** `source`/`provenance.backend`/`provenance.produced_by` are
   adapter-chosen strings (the contract shape-validates, never closes the vocabulary) — so external Librarians
   know they may use their own `source`/`backend` labels (e.g. `"obsidian-note"`/`"obsidian"`).

**Content — `protocol/engram.md` pointer:** a short section / registry note naming **Recall** as the
**read-side (CONSULT-read) binding of the reserved `engram.backend` seam** — the D30 clean-room backend binding
finally named; **files-only default**; external stores = deferred adapters. **PRESERVE the 6 existing engram
required terms verbatim** (`CONSULT`, `LEARN`, `wiki-synthesis`, `produced-by`, `redaction`, `learnFeed` —
`tools/validate_skills.py` `REQUIRED_PROTOCOL["engram.md"]`; dropping any fails `check_protocol_schemas`). Keep
C1–C6 accurate (no invariant weakened; C2 fail-to-human + C4 LOCKED-guardrail + C6 audit explicitly preserved).
**No overclaim:** the pointer names only the **read-side (CONSULT-read) binding** — it must NOT imply the gated
CONSULT *decider* is now active (the decider is `kata-reason`, deferred; CONSULT/LEARN stay gated off, D9/D56).
The LEARN/write half (β-feed, D74) and the decider stay out; do not re-open the β-feed section.

**Content — `tools/validate_skills.py` registration (B2 — the `engram.md` precedent, D74 BP2):** add a
`REQUIRED_PROTOCOL` entry `"recall.md": [...]` so the new contract doc gets the default-FAIL floor. Required
terms (the load-bearing contract clauses): **`schema_version`, `recall/v1`, the no-embeddings stance** (e.g.
`"NO embeddings"` / `"no RAG"`), **the INTENT-never-written rule** (e.g. `"INTENT"` + `"never written"`), and
the read-only invariant. (Correction: `protocol/validation-misses.md` is **NOT** in `REQUIRED_PROTOCOL`
(`tools/validate_skills.py` ~301–317); the real precedent is **`engram.md`**, added by D74 BP2 — match its
shape: a filename key → list of must-appear-verbatim terms checked by `check_protocol_schemas`.)

**Acceptance:**
- `check_protocol_schemas` green — `protocol/recall.md` present **and a `REQUIRED_PROTOCOL["recall.md"]` entry
  exists** (the engram.md precedent, D74 BP2); every listed required term appears verbatim in `recall.md`.
- `protocol/recall.md` states all six elements above; explicitly forbids embeddings/RAG, INTENT writes, the
  write/distill half, and the decider; and states the **OPEN adapter-supplied `source`/`backend`/`produced_by`**
  rule (B1) so external Librarians know they may use their own labels.
- `engram.md` names Recall as the read-side of `engram.backend` (cites the config key `engram.backend`,
  `protocol/config.md`); **the 6 existing engram required terms are still present** (`check_protocol_schemas`
  green for `engram.md`); C1–C6 kept accurate; **no overclaim** (the gated CONSULT decider is NOT implied active);
  the β-feed (D74) section is untouched.
- The doc cites `recall.recall_payload_schema()` by name (anchor resolves to R1 — no phantom reuse).

**depends_on:** R1 (cites the engine's real contract surface).

### Slice R3 — kata-initiate Phase-1b / Phase-2-mirror recall wiring  *(skill; depends_on R1)*
**Owns:** `modules/initiation/kata-initiate/SKILL.md` — only the **Phase 1b** region + a **Phase-2 mirror**
addition (the recall-brief surface) + version bump. (The repo-root `README.md` skill index is **NOT owned by any
slice** — it is regenerated centrally by the conductor at the Integration gate via `validate_skills.py --write`,
per the F2 convention; R3's per-slice `validate_skills` check is read-only and tolerates the expected
"README index out of sync" error.)

**Content:**
1. **Phase 1b (and cold-start ingest):** call `recall.recall_from_paths(...)` (cited by name) over the six
   sources to build the payload; render a short **RECALL BRIEF** (Markdown) from it — recurring open
   validation-misses first (always-surfaced), then the tag/keyword+recency-matched records with their
   provenance/date/stale markers. **(N2 — surface-don't-silently-drop):** because "always surface open
   recurrences" = the detector's **actionable** (≥threshold) output, the brief **notes that sub-threshold
   validation-misses may exist but were not surfaced** (one honest line), so the human knows the recurrence list
   is the over-threshold subset, not the full miss log.
2. **Phase-2 mirror:** surface the brief as **read-only recall context** the human/grill considers while
   editing the goal/setup. State it is *recall* (what you knew before), not a decision and not a default.
3. **Read-only invariant pinned (verbatim-in-spirit):** the brief NEVER changes a gate verdict, auto-acts,
   mutates a skill/protocol/tool, re-decides a LOCKED decision, or is written into `INTENT.md`. The only INTENT
   writer remains `intent_scaffold.write_intent`, fed from the operator-confirmed `answers` dict — the recall
   brief feeds **deliberation**, never the `answers` dict.
4. **Staleness shown, never enforced:** display provenance + date + `stale` flags; the grill judges.
5. **Non-fatal / degradation:** absent sources ⇒ a partial/empty brief; recall **never blocks** initiation or
   the freeze (mirrors the understand-map's "never gates" posture).

**Acceptance:**
- `validate_skills` green (kata-initiate version bumped; README index regenerated `--write`; no new skill).
- The wiring **cites `recall.recall_from_paths` by name** (anchor resolves to R1 — no phantom reuse per
  `protocol/reuse-claims.md`).
- The wiring states explicitly: brief = read-only recall context in the mirror; **NEVER** written to
  `INTENT.md`; `intent_scaffold.write_intent` stays the only INTENT writer; recall does not touch the `answers`
  dict.
- The read-only + no-embeddings + INTENT-never-written invariants are pinned in the skill body (verifiable by
  reading it).
- **N2:** the brief-render content states it notes that sub-threshold validation-misses may exist but were not
  surfaced (the recurrence list is the over-threshold subset).
- Non-fatal: the wiring degrades on absent sources and never blocks freeze (verifiable by reading it).

**depends_on:** R1 (cites engine surfaces); forward-refs R2's `protocol/recall.md` (name fixed by this plan).

## Wave DAG
```
ownership:
  R1: [tools/recall.py, tools/tests/test_recall.py]
  R2: [protocol/recall.md, protocol/engram.md (pointer section only), tools/validate_skills.py (REQUIRED_PROTOCOL["recall.md"] entry only)]
  R3: [modules/initiation/kata-initiate/SKILL.md]
  # repo-root README.md skill index: NOT slice-owned — conductor regenerates centrally at the Integration gate (validate_skills.py --write), F2 convention
waves:
  - wave: 1
    slices: [R1]
  - wave: 2
    slices: [R2, R3]
depends_on:
  R1: []
  R2: [R1]
  R3: [R1]
```
- **Wave 1:** R1 (the pure engine + files-only adapter — no deps; reuses `recurrence_detect`/`validation_misses`
  by import; everything else cites R1's surfaces).
- **Wave 2 (parallel):** R2 (contract doc + engram pointer) + R3 (kata-initiate wiring). Disjoint files → no
  interdependency. Concurrency ≤2 workers; git worktrees; disjoint ownership verified before dispatch.

## Invariant (pinned — read before every slice)
Recall **surfaces material; it never decides, never writes, never gates.** It NEVER (i) changes a gate verdict,
(ii) auto-acts, (iii) mutates a skill/protocol/tool, (iv) re-decides a LOCKED decision (engram **C2** fail-to-
human / **C4** LOCKED-guardrail / **C6** audit), or (v) writes `INTENT.md` (PINNED, `protocol/intent.md`).
**No embeddings / no RAG.** The **write/distill half is the β LEARN feed (D74), out of scope**; **the decider
(`kata-reason`) is a separate future grill, out of scope.** The **contract** (schema + rules) and the
**files-only adapter** (default implementation) stay strictly separate so an external adapter drops in later
without re-contracting. If a slice "needs" to write INTENT, add an embedding/RAG path, read-back the β feed,
make a decision, or change a verdict to be testable — **STOP and escalate (return to grill).**

## Integration gate (after the frontier drains)
`pytest` green incl. `tools/tests/test_recall.py` · `validate_skills` green (kata-initiate version bump, README
regen `--write`; no new skill) · `check_protocol_schemas` green (`protocol/recall.md` registered via the new
`REQUIRED_PROTOCOL["recall.md"]` entry — the engram.md precedent, D74 BP2; `engram.md`'s 6 existing required
terms still present) · **Snyk code
scan on `tools/recall.py`** (new first-party Python — CLAUDE.md security rule; rescan-to-clean) ·
`test_exec_safety.py` still green (**no new sink** — `recall.py` is pure; reuses the pure
`recurrence_detect.detect_from_paths`) · `gate_emit` RESULT/footprint/mutation artifacts. Then fresh-context
**`kata-evaluate`** (default-FAIL; exercises the engine on seeded fixtures: tag/keyword selection, always-
surface-recurrence, recency-boost-not-filter, staleness-not-filter, and the no-INTENT-write rule in the R3
wiring) → **freeze-gate `kata-review`** → **operator merge gate.**

## Risks / escalation triggers (scope-creep watch)
- **Embeddings / RAG bleed (forbidden).** If a slice reaches for vector search "to improve matching" — STOP.
  Selection is tag/keyword + recency over a small tagged-Markdown corpus (BRIEF stance). Assert no embedding
  import in R1's exec-safety test.
- **Write-half bleed (D74).** Recall is read-only. If a slice tries to emit synthesis pages, read-back the β
  feed, or distill — STOP; that is the β LEARN feed (D74), a different, emit-only surface.
- **Decider bleed (`kata-reason`).** If a slice tries to fuse/recommend/decide from the surfaced material — STOP;
  Recall **serves**, the Advisor decides, and that is a separate future grill.
- **External-store dependency.** v1 ships the files-only adapter only. If a slice adds an Obsidian/kiban/kagami
  read path — STOP; external stores are deferred adapters behind the contract.
- **INTENT mutation (hardest).** Recall must have **no** write path to `INTENT.md` (PINNED). If the brief is
  ever fed into the `answers` dict or `write_intent` — STOP; that re-freezes with the human.
- **Staleness over-reach.** Recall surfaces provenance + date; it must **never hard-filter or silently trust**.
  A slice that drops records by age regresses the locked decision #4 — STOP.
- **Re-clustering recurrences.** R1 must surface recurrences via `recurrence_detect.detect_from_paths`, not by
  re-implementing clustering/threshold logic in `recall.py` (phantom-reuse / drift).

## Judgment calls / open points for the freeze gate
**Adjudicated at the freeze-gate HOLD (encoded as resolved):**
- **"Always surface open recurrences" = `recurrence_detect.detect_from_paths` output** (actionable, i.e.
  ≥ the detector's own severity-aware threshold, handled-aware = "open") — **ACCEPTED faithful.** Reuses the BUILT
  detector's threshold, no recall-specific one invented. The all-open-misses alternative remains a **return-to-
  grill** (a new selection decision), and N2 makes the over-threshold scoping honest in the brief. *Kept flagged
  for the operator, not silently re-decided.*
- **Record `id` scheme = `source_path + anchor/slug` (NOT line numbers)** — RESOLVED in R1. Anchors survive
  edits and match the cite-by-anchor practice; the same item recalls identically across runs.
- **`protocol/recall.md` validator registration = the `engram.md` precedent (D74 BP2)** — RESOLVED. R2 owns the
  `tools/validate_skills.py` edit adding `REQUIRED_PROTOCOL["recall.md"]` (B2). (The earlier `validation-misses.md`
  precedent was false — it is NOT in `REQUIRED_PROTOCOL`.)
**Remaining (non-blocking):**
- **Sequencing note (not a blocker):** `.planning/recurrence-handled.jsonl` does not exist yet (recurrence-
  hardening T2 not yet built). R1 degrades cleanly (`read_handled` → `[]`); v1 does **not** depend on T2 shipping.
- **No other open return-to-grill items.** The freeze-gate `kata-review` still adversarially audits this plan.
