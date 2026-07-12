---
spec: second-brain-loop
status: FROZEN 2026-07-12 (operator-directed G1-G4, this session)
builds_on: .planning/specs/second-brain-learning/{BRIEF.md,PLAN-recall.md}
supersedes: nothing (additive; v1 Recall contract invariants all preserved)
date: 2026-07-12
---

# DESIGN — second-brain loop: grill responses as deep input + read-back

## Problem (from the 2026-07-12 second-brain audit)

The learn→store→recall loop does not exist. Recall (read) is built+tested but reads only six
repo-local sources. The β LEARN feed (write) is prose-only — no emitter engine, no invocation,
`engram.learnFeed.dir` never seeded. The live vault second brain has ZERO entries. Grill
responses — the highest-density operator-decision signal in the harness — flow only into frozen
plan artifacts and never reach the second brain. `kata-grill/RUBRIC.md:11` claims otherwise
(doc-drift F2).

## Operator decisions (2026-07-12, verbatim scope — recorded as D151)

- **G1 — emit at grill close.** Every kata execution's grill enriches the second brain the moment
  the decision ledger checkpoints (convergence-gate SHIP-to-close). `kata-improve` β retains its
  broader re-synthesis role over the same engine.
- **G2 — one synthesis page per resolved decision** (Karpathy one-page-one-pattern, engram.md
  wiki-synthesis schema) + one `wiki/log.md` append per emit session. **Plus a dedicated
  second-brain section primarily for coding/research WORKFLOW DECISION PATTERNS** — pages land
  under `<learnFeed.dir>/decision-patterns/`.
- **G3 — recall reads it back.** The feed dir becomes a config-gated 7th recall source
  (files-only, read-only, all v1 invariants preserved). Cross-project: future grills see prior
  grill resolutions.
- **G4 — light-touch redaction (operator re-scope of C3).** The operator owns vault security.
  The emitter runs a deterministic best-effort secret-pattern scrub (redact-and-mark, never
  block). This consciously re-scopes engram.md C3 "fail-closed pre-write gate" for the loop
  feed — recorded here + D151, operator-directed, PD-1-compliant.

## LOCKED decisions

- **SB-L1 — Engine `tools/learn_feed.py` (NEW, stdlib-only).** Pure parse/render core with an
  injected clock; writes ONLY under the `..`-guarded feed dir + `wiki/log.md`. API:
  `parse_grill_ledger(text) -> entries` (DECISION-LEDGER per-entry shape:
  `### D{n} — title · LOCKED|open` + bold-field bullets; tolerant, LOCKED-only emitted),
  `parse_decisions_bullets(text)` (reuse recall's `- **anchor — title.** body` shape),
  `render_page(entry, *, source_path, scope, kind, now) -> (relpath, content)`,
  `emit(feed_dir, pages, *, log_path, now) -> report{written, skipped_identical, redactions}`,
  CLI `python learn_feed.py --ledger <p>... --decisions <p> --feed-dir <d> --kind <k> [--scope project|universal] [--json]`.
- **SB-L2 — Page contract = engram.md wiki-synthesis schema, verbatim.** Frontmatter
  `produced-by: loop`, `source:` (raw artifact paths), `date:`, `scope:`,
  `tags:` sorted, namespaced: `kata/synthesis/decision-pattern` +
  `kata/decision-pattern/<coding|research|workflow>` (from run kind: project→coding,
  research→research, version-up/debug→workflow). Body: Question / Options considered /
  Decision / Rationale / Edges with `[[wikilinks]]` to raw artifacts. One page = one pattern.
- **SB-L3 — Determinism (Doctrine laws 2/3/5/6/7).** Deterministic filename
  `<project-slug>--<Dn-anchor-slug>.md`; sorted tags; sorted dir walks; injectable `now`
  (log-stamp only — pages carry the ledger's own date when present, else `now` date);
  idempotent emit — identical content ⇒ skip (no rewrite), changed content ⇒ overwrite.
  **Conscious deviation from engram C5 supersede-not-rewrite:** loop-emitted pages are
  REGENERABLE DERIVED VIEWS of the durable raw ledger (which stays as-is per the raw↔synthesis
  split); rewriting a derived view loses nothing. C5 continues to protect hand-curated pages
  (`produced-by: wiki|agent` are never touched — the emitter refuses to overwrite a page whose
  frontmatter `produced-by` ≠ `loop`, fail-closed).
- **SB-L4 — Redaction (G4).** Deterministic pattern scrub (AWS `AKIA…`, `github_pat_…`,
  `-----BEGIN…PRIVATE KEY`, `password/token/secret[:=]<nonspace>` classes) → replace match with
  `[REDACTED:<class>]`, count in report + page frontmatter `redactions: N`. Never blocks emit.
- **SB-L5 — Recall 7th source, BC-safe.** `recall_from_paths(..., feed_dir=None)`; absent ⇒
  byte-identical behavior (BC1). Present ⇒ `parse_synthesis_pages(feed_dir)` (sorted rglob of
  `*.md`, frontmatter+body → records `source="second-brain"`, `produced_by`=frontmatter value,
  date from frontmatter, tags from frontmatter+title tokens). Read-only, tolerant, CWE-23
  `..`-guard. Selection unchanged (N1 overlap gate + recency rank). Payload schema unchanged
  (`recall/v1`; `second-brain` is a new `source` label — the schema's source field is open).
- **SB-L6 — Wiring (prose).** (a) `kata-grill` RUBRIC close: after convergence-gate SHIP,
  run the SB-L1 CLI over the run's GRILL-LEDGER.md (+ `.planning/DECISIONS.md` when present);
  no-op when `engram.learnFeed.dir` unset (BC1). RUBRIC:11's "feeds the cognitive fingerprint
  (D72)" claim becomes TRUE and is reworded to cite the engine. (b) `kata-improve` β sub-mode
  cites `tools/learn_feed.py` as its engine (wider inputs: + LESSONS, REVIEW-*). (c)
  `kata-initiate` Phase 1b recall table gains the `feed_dir` row (config-gated). Version bumps
  per STANDARDS §3 on all three + validator `--write` regen.
- **SB-L7 — Config seeding (fixes F3).** `kata_settings.default_learn_feed_dir(settings) ->
  str|None` = `<vaultDir>/second-brain/wiki/pages/synthesis` when `vaultDir` set, else None.
  `kata-bootstrap` prose: seed `engram.learnFeed.dir` from it at config-write (operator may
  override). Docstring claim in kata_settings becomes true.
- **SB-L8 — Smoke (this session, live).** Emit from a real harness grill ledger into the live
  vault (`C:\Users\taurr_nvs748q\PokeVault\PokeVault\second-brain\wiki\pages\synthesis\
  decision-patterns\`), verify pages + log line; then `recall_from_paths(feed_dir=…)` with a
  matching query surfaces them. n=1 live proof of the closed loop, labeled honestly.

## Invariants preserved (pinned)

Recall stays pure/read-only/no-write-to-INTENT (v1 PINNED); emit is additive + no-op-when-
unconfigured (BC1); zero CONSULT (the read-back is recall-display only — no decider); the
grounding gate/freeze discipline untouched; INTENT.md writer unchanged.

## Out of scope (named, not silent)

kata-reason/CONSULT decider; readiness exam/triage/benchmark (BRIEF C-arc); vault llm-wiki
pipeline; embeddings/RAG (forbidden by recall contract); automated §7 structural redaction
beyond SB-L4 (BACKLOG, unchanged).
