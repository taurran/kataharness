---
date: 2026-06-08
spec: modes-A4-version-up
reviewer: fresh-context adversarial (kata-review advanced, D15) — Opus, read-only
verdict: SHIP
gate: pytest 13 passed · validator 25 skills / 0 errors
tags: [review, A4, version-up, kata-graph, ship]
---

# A4 (version-up + kata-graph) — Adversarial Review (D15)

**VERDICT: SHIP.** Fresh-context, read-only adversarial pass over `git diff master...phase-2/modes-A4-version-up`
(8 build commits), judged against the frozen `DESIGN.md` (L1–L6, BC1–BC5, A1–A5). No blockers.

## Gate (run by the reviewer)
- `uv run pytest -q` → **13 passed**
- `uv run python validate_skills.py` → **25 skills checked — 0 error(s), 0 warning(s)**

## Drift-magnet checks (DESIGN §6 A4) — all confirmed
1. **(a)** `protocol/graph.md` `meta = {backend, repoHash, generatedAt}` — **no `seedSymbols`** (use-time only). ✔
2. **(b)** `import` edges file→file; `call` documented oracle-only; `symKind` exact closed enum. ✔
3. **(c)** `kata-orchestrate` supersession is REAL (deleted, not additive): no "for each wave in dependency
   order", no synchronous "make a deliberate decision yourself / re-dispatch". Dispatchable predicate +
   hard-wait predicate (frontier empty ∧ open human-required escalations) present and decidable. ✔
4. **(d)** Board stays one-line `ESCALATE | <task-id> | <summary>`; structured payload separate
   (`.kata/escalations/<task-id>.json`, `protocol/escalation.md`). ✔
5. **(e)** `kata-readiness` BLOCKs version-up without tree-sitter (no inert grep path). ✔
6. **(f)** No `knowledgeGraph` config (Obsidian deferred, BC5) — config.md adds only the `graph` block. ✔
7. **(g)** All 25 skills `version: 0.1.0` (BC4); none bumped. ✔
8. `kata-graph` frontmatter conforms (STANDARDS §1): `kata/plan`+`kata/module/graph`, cost-weight 3,
   `source:` names BOTH aider (MIT) + Graphify (MIT, spine #12); body points to `protocol/graph.md`, doesn't restate. ✔
9. No dangling wikilinks — `kata-defer`/`kata-understand` appear as prose only, never `[[links]]`. ✔
10. Contract coherence: `kata-plan` footprint = modified ∪ `marginDepth`-hop reverse-deps (L4 exact);
    `kata-grill` Phase 0 invokes kata-graph for existing targets (L4); `kata-evaluate` note = baseline+new
    green, no new evaluator (L4/BC3); D47–D56 + STATE + ROADMAP consistent. No contradictions. ✔

## Secondary (cosmetic) — FIXED post-review
- `kata-orchestrate` Final-gate read "After the last wave" (stale once waves became a derived view). Tidied to
  "After the frontier drains (all tasks integrated)" so the wave-gate supersession is fully clean. Non-blocking;
  did not affect any predicate.

## Outcome
SHIP. A4 merges to `master`. The supersession is genuine, schemas are validator-enforced, deferred work (Obsidian
KG, engram) is clean with no inert hooks.
