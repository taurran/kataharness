---
date: 2026-06-08
branch: master (local only — no remote yet)
commit: de4b0ee (Merge modes Spec A4 — version-up + kata-graph) + docs/handoff on top
green: validator 25 skills / 0 errors (exit 0) · pytest 13 passed · Snyk 0
tags: [handoff, modes, spec-A-complete, A1-A4-merged, checkpoint]
---

# HANDOFF — KataHarness — 2026-06-08 (Modes Spec A COMPLETE: A1+A2+A3+A4 merged)

> **Fresh session: read in order, confirm green, then resume at NEXT STEP. Re-anchor on the FROZEN specs, not a summary.**

## 1. Read-in order
1. `AGENTS.md` (canonical) · 2. `docs/DESIGN.md` (charter) · 3. `docs/STANDARDS.md` (frontmatter v2 §1 + the
**versioning hold policy A** in §3) · 4. `docs/MODES-DESIGN.md` (modes architecture) · 5. `docs/TAXONOMY.md`
(tier-family + module conventions) · 6. `CONTEXT.md` (glossary — now incl. the A4 graph/version-up terms) ·
7. `.planning/STATE.md` · 8. `.planning/DECISIONS.md` (**D1–D56**) · 9. `.planning/LESSONS-LEARNED.md`
(**L1–L10**) · 10. `.planning/SKILL-COST-RATINGS.md` · 11. the four spec folders under `.planning/specs/`
(`modes-A1-foundations`, `-A2-tier-families`, `-A3-bootstrap-wiring`, `-A4-version-up`) —
each has `{PLAN, REVIEW}` (+ A3/A4 also `GRILL-LEDGER`, A4 also `RESEARCH`, `DESIGN`).

## 2. State (confirm green first)
- Branch **master**, tip ≈ **de4b0ee** + this handoff commit. **Local-only — no git remote yet.**
- Gate: `cd tools && uv run pytest -q` → **13 passed**; `cd tools && uv run python validate_skills.py` →
  **`25 skills checked — 0 error(s)`**, exit 0. (`uv` on PATH.)

## 3. What shipped — Modes Spec A (A1→A4), all merged + adversarially reviewed (D15)
- **A1 (foundations):** `tools/validate_skills.py` (skill-conformance + README-regen validator, Python/uv);
  schema-v2 frontmatter (`cost-weight`+`license`+namespaced `tags`); generated README index;
  `protocol/{config,dependencies}.md`; `docs/TAXONOMY.md`; Apache-2.0 LICENSE.
- **A2 (tier families):** grill/review/plan → essential/standard/advanced; diagnose → light/full; shared
  `RUBRIC.md` per family (DRY-by-pointer); validator tier rules. **D33: structural invariants never tiered.**
- **A3 (bootstrap + wiring):** `kata-bootstrap` (run-shape router — individual/batch/version-up/advanced as
  PRESETS over the mode axis; D24c ladder) + `kata-readiness` + `kata-orchestrate` reads `kata.config` with a
  **fail-closed load-guard**. `kata.config` gained `runShape`+`target`. D34–D46.
- **A4 (version-up + kata-graph):** `kata-graph` — token-budgeted structural map of an existing repo (the
  version-up ingestion engine) — **based on aider's repo-map** (tree-sitter tags + personalized PageRank +
  token budget), **Graphify = optional MCP oracle backend**; tree-sitter hard floor; the **`kata.graph.json`**
  contract (`protocol/graph.md`), feature-agnostic + cached; seeding/digest/blast-radius are use-time
  projections. Version-up wiring (grill Phase 0 ingest, footprint = modified ∪ depth-1 reverse-deps ownership,
  full-suite-green regression via existing `kata-evaluate`). **`kata-orchestrate` generalized to rolling
  DAG-frontier dispatch + ASYNC escalation** (park/drain/hard-wait-iff-frontier-blocked; structured payload =
  its own contract `protocol/escalation.md`). D47–D56. **25 skills.**
- **Method that worked (keep doing it):** subagent-driven, **Opus on judgment tasks / Sonnet on mechanical**,
  Opus reviews every diff + gates on validator. **Fresh-context adversarial gates (D15) are load-bearing** —
  A4 took **3 convergence gates + a coherence audit** to freeze; each caught real defects (the seedSymbols
  cache contradiction, the async/wave-model collision, the board/payload fusion). The no-drift discipline even
  held at the worker level (a worker BLOCKED on a bad `[[kata-defer]]` link rather than improvising).

## 4. NEXT STEP — Spec A is COMPLETE; a user choice gates the next phase
1. **Obsidian-KG / kata-understand spec** — the deferred emit+ingest (folder-based, pluggable frontmatter
   profiles; bootstrap "emit a KG?" question + `knowledgeGraph` config; `kata-understand` base =
   Understand-Anything) projecting from the `kata.graph.json` contract A4 built. **Wants PortaVault to exist
   first** — the user is scaffolding that Obsidian vault; this is the natural next build once it's stood up. (D54/D55.)
2. **Spec B — bake-off** (N variants → judge → pick → refine up; composes with version-up, D37).
3. **D16 planning-varied A/B — the real v0.1 validation gate.** Prove the grill differentiates (Arm A plans via
   `kata-grill`→`kata-design-doc`→`kata-plan` vs a baseline). Still unproven (L10 = TIE on frozen-plan execution).
- **Opus recommendation:** if PortaVault is ready → **1** (it ties the user's second brain to the harness and is
  high personal value); otherwise **3** (D16) is the honest v0.1 ship-gate; **2** anytime.

## 5. Suggested next skills
- Any new spec: `kata-grill` (grill it first — the gates pay off) → `kata-design-doc` (freeze) → `kata-plan` →
  subagent-driven build → `kata-review` (D15). `kata-write-skill` to author new skills to STANDARDS.
- D16: run `kata-grill`/`kata-design-doc`/`kata-plan` for real on a CPP-style target vs a baseline; measure.

## 6. Open decisions for the human
- **Which of 1/2/3 above** (gated partly on PortaVault readiness). · **Set a git remote** before public release
  (Apache-2.0, public-intended, still local-only). · Suite/plugin packaging shape.

## 7. Redaction
No secrets / keys / PII. Nothing to redact.
