---
name: kata-improve
description: >-
  The Improvement Kata applied to the harness itself — fold accumulated LESSONS-LEARNED, review findings, and
  run surprises back into the SKILLS. Use after a run/milestone to deepen skills, close recurring gaps, and
  bump versions. Targets the skills/ tree (not product code); decides WHAT to change and delegates new-skill
  authoring to kata-write-skill.
license: Apache-2.0
version: 0.2.0
category: meta
status: experimental
agnostic: true
cost-weight: 1
allowed-tools: [Read, Grep, Glob, Edit, Write, Bash]
source: adapted-from the Improvement Kata (Toyota Kata) + mattpocock/skills engineering/improve-codebase-architecture
tags:
  - kata/meta
  - kata/module/meta
  - improvement-kata
  - retrospective
  - continuous-improvement
---

# kata-improve — every run improves the harness

This is the phase that makes the project's name true. It is **cross-run and retrospective**, and it edits the
**skills**, not the product. Boundaries that keep it from competing:
- vs [[kata-review]]: review *finds* defects in **one** run (a gate); improve folds **accumulated** lessons
  back over many runs (the kata). Review's HOLD findings are *inputs* here.
- vs the worker's fix loop: workers fix **product code**; improve changes **`skills/**`, docs, protocol**.
- when a gap needs a **new** skill, improve doesn't free-hand it — it calls [[kata-write-skill]].

## Inputs (read on demand — don't embed)
`.planning/LESSONS-LEARNED.md`, `DECISIONS.md`, any `REVIEW-*.md`, and the latest run's surprises/handoff.
These are durable files; load them when improving, not into the loop.

## The kata (target-condition → current → experiment)
1. **Target condition** — what should the harness do better? (e.g. "the grill converges to a more specific
   contract"; "no recurring class of drift"). State it concretely.
2. **Grasp the current condition** — what do the lessons/reviews show is actually happening? Cluster
   recurring signals; a lesson that recurs is a skill defect, not a footnote.
3. **Next experiment** — the smallest change to a skill/doc that moves toward the target. One step, not a
   rewrite. Apply it; record the expected effect so the *next* run can tell if it worked.

## Applying a change (with discipline)
- Edit the skill body; **bump its semver** (PATCH wording/fix, MINOR new capability, MAJOR contract change)
  and update the **README index** (the source of truth — keep it honest; the v0.1 review caught drift here).
- If the change is a new skill → [[kata-write-skill]]. If it retires one → `deprecated/` + `supersedes`, never
  silent deletion.
- **Managed-learning path (loop-cognition L5):** if a recurring lesson is reusable as a skill but the loop
  (not a human) is distilling it mid-stream, author it as an **agent-distilled candidate** via
  [[kata-write-skill]] (sandboxed: `scope: agent`, in `<agentSkills.dir>/candidates/`, NOT loaded universally) →
  grounding gate → the human persistence gate [[kata-promote]] at session end. Repo-skill edits go the normal
  route above; only *agent-distilled* skills route through the two-stage candidate→promote gate.
- Record the improvement back into `LESSONS-LEARNED.md`/`DECISIONS.md` so the kata compounds.
- Keep changes evidence-driven: cite the lesson/finding that motivated each. No speculative gold-plating.

## Output
A small, cited set of skill/doc edits + version bumps + an index update, and a one-line "expected effect to
verify next run." The harness is now incrementally better; the loop continues.

## Local-adaptation mode (install context)

A **separate operating mode** from the authoring-upstream path above. When `kata-improve` runs against a
**user install** (rather than the maintainer's dev checkout), it must never edit the installed base — that base
is immutable from the user's side and any in-place edit is clobbered by the next `--update`. This mode emits
local adaptations without touching `skills/**`, `protocol/`, or `docs/`.

**Context detection.** Before entering kata mode, determine the context via
`kata_overlay.adaptation_context(home)`:
- **`"install"`** — a `.kata-version` stamp is present in the home (written by every successful install or
  `--update`, git-ignored). Every real user install self-identifies; the safety rail below is on by default.
- **`"dev-repo"`** — no stamp; a canonical maintainer checkout that has never been installed into a host.
  Use the authoring-upstream path (edit `skills/**` in place, bump semver, update the README index).

**Install-context safety rail.** When the context is `"install"`, the kata mode above **refuses to run**
unless the operator has explicitly passed `improve.allowUpstreamEdit`. The default in an install is *never*
to mutate the installed base. The edge case of a maintainer who installed from their own dev checkout (so
the dev tree carries a stamp) is handled by that conscious override — failing toward not-mutating.

**What local-adapt writes and where (by change shape):**

| Change shape | Emission target | Mechanism |
|---|---|---|
| Frontmatter knob · appended guard/lesson/rubric (the ~60–70% bulk) | **Overlay entry** in `<home>/.kata-overlay/overlay.json` | `kata_overlay.write_overlay_entry(home, name, entry)` — read-merge-write one skill; all others preserved |
| Mid-body wording/threshold — expressible as a frontmatter override or append block | **Overlay** — state the choice and record why | same as above |
| Mid-body wording/threshold — NOT expressible as overlay | **Fork** (route as below) | [[kata-write-skill]] → toolkit candidate |
| Deep prose/contract rewrite (~10–15% of changes) | **Fork** authored to the user's toolkit, never the base | [[kata-write-skill]] → `<agentSkills.dir>/candidates/<name>/` (carrying `supersedes: <upstream>`) → [[kata-promote]] human gate before it can shadow |
| Whole new skill | Toolkit candidate (orthogonal) | Existing [[kata-write-skill]] path — no collision |

**Pinned writable footprint (install context).** Local-adapt mode's writable footprint is pinned to exactly:
1. `<home>/.kata-overlay/overlay.json` — via `kata_overlay.write_overlay_entry` (overlay entries).
2. `<agentSkills.dir>/candidates/<name>/` — via [[kata-write-skill]] (fork candidates, pre-promote-gate).

It writes **nothing** under `<home>/skills/`, `protocol/`, or `docs/`. A fork candidate does not shadow the
upstream until it passes the [[kata-promote]] human gate and lands in `<agentSkills.dir>/skills/<category>/`.
No new `allowed-tools` — `Write`/`Edit` (already in the frontmatter) cover both emission targets.

## LEARN-feed emit sub-mode (β — emit-only, the primary fingerprint feed; D66/D72)
A **separate sub-mode** from the kata above (which edits skills). This one **only emits**: it mines the run's
durable decision artifacts into **synthesis pages** for the second-brain LEARN feed, so a future cognitive
fingerprint has raw material. It changes **no skill and no product code** — output goes solely to the feed dir.
Run it at IMPROVE / handoff time (engram seam E6), never as a per-task hook (keep it out of the one-shot budget).

- **Observe → synthesize → emit.** Read `DECISIONS.md`, `LESSONS-LEARNED.md`, the run's `GRILL-LEDGER.md`(s),
  and any `REVIEW-*.md`. Emit compact, cross-linked **synthesis pages** per the **wiki-synthesis output schema
  in `protocol/engram.md`** (Karpathy LLM-Wiki raw↔synthesis split;
  frontmatter `produced-by: loop`, `source:`, `scope:`; `[[wikilinks]]`; one page = one pattern). **Grill
  ledgers are a primary feed (D72)** — each resolved decision + the human's choice + rationale is fingerprint
  signal.
- **Zero CONSULT (structural).** This sub-mode **never reads a fingerprint back into planning or execution** —
  there is no CONSULT call-site. It is purely additive; emitting cannot influence any build (BC2).
- **Redaction is a HARD pre-write gate (C3).** Every page passes the **`kata-handoff` §7 redaction filter**
  (no secrets / keys / PII) and is **project-scoped** (`scope:`) **before any write**. Redaction failure ⇒ do
  not emit that page (fail-closed). This is the data-exfiltration / IP-leak surface — never bypass it. *(Maturity:
  §7 is a prose contract today; a structural redaction filter + test seam land with β-runtime — see `protocol/engram.md`.)*
- **No-op if unconfigured (BC1).** Emit only when `engram.learnFeed.dir` is set (`protocol/config.md`); absent
  ⇒ write nothing. Distinct from `engram.backend` (the CONSULT backend, still gated/off).
- **Output:** N synthesis pages written to `engram.learnFeed.dir` (provenance `produced-by: loop`), plus a
  one-line emit summary. No skill edits, no version bumps in this sub-mode.

## Recurrence-hardening proposal (T2 — auto-DRAFT, human-gated; D101/D102/D112)

A **separate sub-mode** from the kata above (which edits skills). This one **only DRAFTS a proposal**: given an
**actionable recurrence** surfaced by the T2 detector, it authors a one-page hardening-proposal doc and records a
sidecar marker so the detector stops re-proposing. It is the LLM-judgment author half of the recurrence→proposal
loop (the pure detector engine lives in `tools/recurrence_detect.py`). It **DRAFTS only** — it does not write the
guard, edit any surface, or merge. This makes the D102 (`protocol/reuse-claims.md`+`validate_skills` rule) and
D112 (`protocol/exec-safety.md`+`test_exec_safety.py`) hand-done hardenings repeatable: a recurring class →
an auto-drafted proposal of *exactly that shape* → the human gate.

**Trigger.** Run when the detector flags a newly-actionable cluster — either from the `kata-orchestrate`
Final-gate hook (all modes, non-fatal) or **on-demand** by an operator. The deterministic decision (cluster →
distinct-run count → severity-aware threshold → handled-aware skip → off-vocabulary flag) is owned by the engine;
this sub-mode never re-clusters or re-thresholds in prose. Get the actionable clusters from the engine, by name:
- `recurrence_detect.actionable_recurrences(misses, handled, *, default_threshold=3, blocker_threshold=2)`
  (`tools/recurrence_detect.py`) — or its I/O convenience
  `recurrence_detect.detect_from_paths(".planning/validation-misses.jsonl", ".planning/recurrence-handled.jsonl")`.
  Each result dict carries `key, responsible_skill, failure_class, distinct_runs, raw_count, severity_tier,
  threshold, off_vocabulary, evidence` — author the proposal straight from these, computing nothing yourself.

**For each actionable cluster, DRAFT** a one-page proposal at
**`.planning/specs/recurrence-hardening/PROPOSAL-<failure_class>.md`** (LOCKED convention — one per recurring
class; the `proposed` sidecar marker references this path via `proposal_ref`) containing:
1. **The recurring cluster** — `responsible_skill` × `failure_class`, the `distinct_runs` count, `severity_tier`,
   and the `threshold` it crossed (and the `off_vocabulary` flag if set — note "clustering may be unreliable;
   pick `failure_class` from the curated enum next time"). Take all of these from the engine result, not by
   re-counting.
2. **Evidence rows** — the cluster's manifest entries (from the result's `evidence`): `ts`, `mode`,
   `what_conformance_missed`, `what_caught_it`, `decision_ref`, and the distinct runs they span.
   **Description-level only** — inherit the manifest's secret-hygiene convention (`protocol/validation-misses.md`
   §Secret-hygiene convention): never copy code payloads, key material, or verbatim fragments into the proposal.
3. **Proposed target surface** — defaulting to a **protocol contract + a mechanical test** (the D102
   `protocol/reuse-claims.md`+`validate_skills` rule / D112 `protocol/exec-safety.md`+`test_exec_safety.py`
   shape). **NAME the surface.** State explicitly that `responsible_skill` is the **clustering key, NOT
   necessarily the fix location** — the proposal proposes *where* the guard should land.
4. **Guard text + test sketch** — the would-be contract clause (the standing rule the next occurrence must
   satisfy) and the mechanical test idea (what a regression check would assert). A sketch, not the guard itself.
5. **Routing note** — this proposal goes to a fresh-context **freeze-gate [[kata-review]] → human merge gate**.
   This is the **repo-hardening path — NOT [[kata-promote]]** (which governs external agent-distilled candidate
   skills outside this repo's `skills/` tree; do not route here through it). **NOT auto-applied:** drafting is
   automated; authoring/merging the real guard stays human.

**After drafting, record the `proposed` marker** so the detector stops re-proposing the cluster — by name:
- `recurrence_detect.append_handled({ts, key, responsible_skill, failure_class, status: "proposed",
  proposal_ref: "<the PROPOSAL path>", guard_ref: null}, ".planning/recurrence-handled.jsonl")`
  (`tools/recurrence_detect.py`; schema = `recurrence_detect.handled_schema()`). Append-only; non-fatal — a
  `False` return (I/O failure) is surfaced as a NOTE, never an error. **Only `status: "proposed"`** is written
  here.

**Writable footprint — EXACTLY two paths (invariant-critical; verifiable by reading this body).** Because the
`kata-orchestrate` Final gate auto-invokes this Write-capable sub-mode in all modes, its writable footprint is
**pinned to exactly two paths and nothing else**:
1. `.planning/specs/recurrence-hardening/PROPOSAL-<failure_class>.md` — the drafted proposal, and
2. `.planning/recurrence-handled.jsonl` — the `proposed` marker (via `recurrence_detect.append_handled`).

It writes/edits **NOTHING else**: no skill, no protocol, no tool, no manifest row, no other doc; it does **NOT**
append a `guarded` marker; it does **NOT** merge. A drafting run that touches any third path has drifted and must
STOP. This reuses kata-improve's existing `Write`; no new allowed-tool.

**Boundary (the C/B invariant + the T2→T3 line).** This sub-mode may **READ the manifest and AUTHOR a
proposal**; it may NOT (i) change any gate verdict, (ii) edit any skill/protocol/tool, or (iii) merge its own
proposal. The `guarded` marker (with `guard_ref`) is appended by the **human / kata-improve at guard-merge time**,
**OUTSIDE T2's auto-scope** — T2 never marks a class `guarded` (that would assert a guard shipped, which only a
human merge establishes). **Auto-authoring the guard doc/test itself is T3 — OUT OF SCOPE.** If a run "needs" to
write the guard, edit a surface, or merge to be useful, **STOP and escalate** (the T2/T3 boundary).

**Output:** one `PROPOSAL-<failure_class>.md` per actionable cluster + the `proposed` sidecar marker + a one-line
summary naming the cluster and the routing (freeze-gate `kata-review` → human merge). No skill edits, no version
bumps in this sub-mode.
