# protocol/recall.md — the Recall read-CONTRACT (recall/v1)

The **Recall read-CONTRACT** is the agnostic interface a second brain answers when the harness asks
"what did we already know that is relevant here?" It defines the payload shape + the
selection/staleness/read-only rules, so that **any** backend adapter (the files-only default today;
Obsidian / kiban / kagami later) can implement it **without re-contracting**. This file is the canonical
source of truth; responsible skills reference it by path (`protocol/recall.md`), never by `[[wikilink]]`.

Recall is the **read-side** of the reserved `engram.backend` CONSULT seam (D30 clean-room, finally
named — see `protocol/engram.md` › "Recall — the read-side of `engram.backend`"). Recall **serves**; it
never decides (that is `kata-reason`, a deferred future grill) and never writes/distills (that is the β
LEARN feed, D74 — emit-only, out of scope here).

## The contract vs the adapter (the load-bearing separation)

- **The CONTRACT** = the payload schema (`recall.recall_payload_schema()`, `tools/recall.py`) + the
  selection / staleness / read-only rules in this doc. It validates **SHAPE — required keys + types —
  ONLY**; it **never** closes a `source` / `backend` / `produced_by` vocabulary.
- **The files-only default adapter** = `recall.recall_from_paths(...)` + the per-source parsers
  (`recall.parse_lessons` / `parse_decisions` / `parse_intent` / `parse_understand`): the default backend
  that serves the contract from six on-disk artifacts. It is **one implementation** of the contract.
- An external store (Obsidian / kiban / kagami) is a *different adapter answering the same contract* — it
  drops in later **without re-contracting**. Keep the two strictly separate so the seam survives.

## 1. The payload schema (the read-side interface)

`recall.recall_payload_schema()` (`tools/recall.py`) is the **single source of truth** — the published
contract surface external adapters cite by name (per `protocol/reuse-claims.md`). It mirrors the
single-source-of-truth *schema-function* pattern of `validation_misses.miss_schema()` /
`recurrence_detect.handled_schema()`. `recall.validate_payload(payload)` shape-validates against it
(returns a list of errors; `[]` = valid). `recall.build_payload(...)` assembles a conforming payload.

The pinned top-level `schema_version` is the literal string `recall/v1`.

```
RecallPayload (schema_version "recall/v1"):
  schema_version : str            # "recall/v1"
  query          : { terms: list[str], kind: "project"|"research"|"version-up" }
  records        : list[RecallRecord]        # tag/keyword + recency-selected source items
  recurrences    : list[RecurrenceRecord]    # ALWAYS-surfaced open validation-miss recurrences
  provenance     : { backend: str, sources_read: list[str], generated_ts: str }

RecallRecord (9 fields):
  id            : str    # stable id = source_path + anchor/slug (NOT line numbers — anchors survive edits)
  source        : str    # OPEN adapter-supplied label (see §7)
  source_path   : str    # the on-disk artifact path
  title         : str    # the surfaced item's anchor/name (e.g. "L7 — Converse, don't pop up")
  excerpt       : str    # short, description-level snippet (no code payloads)
  tags          : list[str]                  # matched tags/keywords
  match_score   : float                      # token-overlap count + recency component
  provenance    : { produced_by: str (OPEN, §7), date: str|null, recency_rank: int }
  stale         : bool   # date-based HINT only — NEVER a filter (the grill judges)

RecurrenceRecord (EXACTLY 7 fields — raw `evidence` projected OUT, see §8):
  key, responsible_skill, failure_class, distinct_runs, severity_tier, off_vocabulary, open: true
```

## 2. The selection contract (tag/keyword overlap + recency — NO embeddings)

Selection is **case-insensitive token overlap** between the query terms (the current goal/CONTEXT terms;
for a version-up, also the prior INTENT goal) and a record's `tags` + `title` + `excerpt` tokens, **plus a
recency component**. The rule (`recall.select_records`, `recall.match_score`, `recall.token_overlap`):

- **Overlap > 0 is a hard PREDICATE (gate).** A record with **zero** token overlap is **excluded** — no
  matter how recent. Recency never promotes a zero-overlap record in.
- **Recency only RANKS among the passers** (sets `provenance.recency_rank`, breaks ties in `match_score`).
  It **never filters a passer out**: an old-but-overlapping record stays in `records`.
- **Recurrences bypass selection entirely** — always surfaced (see §3) regardless of overlap.

**NO embeddings / NO RAG / no vector retrieval.** The corpus is a small tagged-Markdown set; selection is
plain token-set intersection only. This is a hard stance (assertable by source scan — no
numpy/embedding/vector import in `tools/recall.py`). A slice that reaches for vector search "to improve
matching" must STOP and return to grill.

## 3. The always-surface-open-recurrences rule

Open validation-miss recurrences are **ALWAYS surfaced**, bypassing the selection gate. The files-only
adapter obtains them by reusing the BUILT detector `recurrence_detect.detect_from_paths(misses_path,
handled_path)` by name (no re-clustering, no recall-specific threshold invented). "Open" = the detector's
own actionable, handled-aware, severity-aware over-threshold subset. Because this is the over-threshold
subset, a consumer (the RECALL BRIEF) must note that sub-threshold misses may exist but were not surfaced
(honest scoping; the recurrence list is not the full miss log).

## 4. The staleness rule (surface, never hard-filter)

Staleness is a **date-based HINT only** (`RecallRecord.stale`). Recall surfaces provenance + date and
prefers recency, but it **never hard-filters or silently trusts** by age — the human/grill judges. A
stale-but-overlapping record stays in the payload with `stale=True`. This mirrors engram **C5**
(supersede-not-rewrite / decay): surface the staleness, do not pin or drop on it.

## 5. The read-only invariant

Recall **surfaces material; it never decides, never writes, never gates.** This is the **read-only
invariant**. Recall NEVER (i) changes a gate verdict, (ii) auto-acts, (iii) mutates a
skill/protocol/tool, or (iv) re-decides a LOCKED decision — preserving engram **C2** (fail-to-human),
**C4** (LOCKED-decision guardrail), and **C6** (audit every auto-resolution). The **write/distill half is
the β LEARN feed (D74)** — out of scope, emit-only; Recall does not read it back, re-open, or extend it.
The **decider (`kata-reason`)** is a separate future grill — out of scope; Recall serves, the Advisor
decides. The engine is pure (no subprocess / eval / exec / shell; returns a dict), with `..`-guarded path
reads (CWE-23, `recall._guard_path`) and tolerant I/O (absent source ⇒ `[]`, never raises).

## 6. The INTENT-never-written rule

The RECALL BRIEF feeds the **`kata-initiate` Phase-2 mirror** as read-only recall context the human/grill
weighs while editing the goal/setup — it is displayed, not stored. The brief is **never written** into
`INTENT.md` (PINNED, `protocol/intent.md`). The only INTENT writer remains
`intent_scaffold.write_intent(path, answers)`, fed from the operator-confirmed `answers` dict. Recall has
**no write path to INTENT** and never touches the `answers` dict — this is the structural guarantee, not a
procedural one.

## 7. OPEN adapter-supplied labels (B1 — the contract is vocabulary-OPEN)

`RecallRecord.source`, `provenance.backend`, and `provenance.produced_by` are **OPEN, adapter-supplied
strings — SOFT, shape-validated (type-checked `str`, present), NEVER value-enforced.** The files-only
values (`source="lessons"|"decisions"|"prior-intent"|"understand-map"`, `backend="files-only"`,
`produced_by="repo"|"kata-understand"`) are *that adapter's* labels, **not the contract's closed set.**

`recall_payload_schema()` marks these three fields `"open": True` and carries no `values`/`enum` set;
`validate_payload` checks they are present strings and nothing more. An external **Obsidian / kiban /
kagami** adapter MUST be able to build a payload with `source="obsidian-note"` / `backend="obsidian"` /
`produced_by="kiban"` and have it **validate** — otherwise it would have to re-contract, breaking the
"drops in later without re-contracting" pin. External Librarians may therefore use **their own**
`source` / `backend` / `produced_by` labels.

This is the deliberate **opposite** of `validation_misses.miss_schema()`'s `severity` / `what_caught_it`
(which `validate_miss` HARD-enforces as closed enums): the Recall contract is **shape-validated,
vocabulary-open.** Mirror only `miss_schema()`'s single-source-of-truth *schema-function* pattern, NOT its
closed-enum enforcement, for these three fields.

## 8. RecurrenceRecord projects out raw evidence (N3)

`recurrence_detect.actionable_recurrences` returns each cluster WITH `evidence` = the full raw miss dicts
(including `what_conformance_missed`, description-text by convention). The files-only adapter **projects
these out** — a RecurrenceRecord keeps ONLY `key, responsible_skill, failure_class, distinct_runs,
severity_tier, off_vocabulary, open`. Raw miss text is **never** carried into the payload or the brief
(secret-hygiene + altitude — surface the recurring *class*, not the raw description).

## What an external adapter must satisfy

To bind a second brain behind this contract, an adapter implements one entry point that returns a payload
which `recall.validate_payload(...)` accepts:

- Produce a `RecallPayload` with `schema_version == "recall/v1"`, a `{terms, kind}` query, the
  shape-correct `records` / `recurrences` / `provenance` (use `recall.build_payload(...)` or match its
  output shape).
- Use **your own** `source` / `backend` / `produced_by` labels (§7) — the contract shape-validates, never
  closes the vocabulary.
- Honour the selection contract (overlap predicate + recency rank; **NO embeddings**, §2), the
  always-surface-recurrences rule (§3), the staleness-is-a-hint rule (§4), and the **read-only
  invariant** (§5) + the INTENT-never-written rule (§6). The adapter surfaces; it never decides, writes,
  or gates.

## Cross-references

- `tools/recall.py` — the engine + files-only default adapter (Slice R1).
- `protocol/engram.md` — Recall is the read-side binding of the `engram.backend` CONSULT seam (D30).
- `protocol/intent.md` — the PINNED INTENT artifact Recall never writes.
- `protocol/validation-misses.md` / `tools/recurrence_detect.py` — the recurrence source Recall surfaces.
- `.planning/specs/second-brain-learning/PLAN-recall.md` — the frozen plan.
