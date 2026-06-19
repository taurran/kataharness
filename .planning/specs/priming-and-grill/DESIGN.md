---
date: 2026-06-18
spec: priming-and-grill
status: FROZEN (re-froze 2026-06-18 post fresh-context kata-review HOLD→SHIP: wired assumption-log into the gate; floor is always-on substrate, grill additive). Wiring spec; architecture pre-decided (D71/D72 frozen).
source-decisions: D71, D72 (.planning/DECISIONS.md); L11 (.planning/LESSONS-LEARNED.md)
tags: [design, frozen, priming-and-grill, D71, D72, grill-depth, autonomous-floor, kata-defer]
---

# priming-and-grill — D71/D72 wiring — FROZEN DESIGN

No new architecture here — **D71/D72 are already frozen decisions**. This spec wires them into the skill suite.
The grill is now an **optional human certainty layer over the priming prompt**; declining it drops to an
**autonomous-reliability floor**. Grill ↔ RS are one ambiguity-resolution spectrum (up-front-with-human vs
in-loop-without-human). Approved scope + micro-picks (human, 2026-06-18).

## 1. What this delivers (and the one honest caveat)
- **Full control surface NOW:** the grill-depth dial `skip | light | standard | full` — three positions already
  exist as the `kata-grill` A2 tier-family (light=essential, standard=standard, full=advanced); **`skip` is the
  only new rung.** Bootstrap offers it (D46); `kata-readiness` recommends it from priming-prompt richness.
- **The always-on autonomous floor's available-now safety net:** the floor (default-FAIL + RS + assumption-log)
  is the substrate on **every** rung; the grill adds up-front certainty on top (D71: "both coexist"). `skip`
  leans entirely on the floor; light→full add increasing up-front grill. `kata-defer` (promoted from backlog
  D42/D43) is the floor's **assumption/ambiguity log**, **graded by `kata-evaluate` rubric item 8 at the gate**
  and surfaced at handoff, plus its D42 out-of-scope parking role.
- **CAVEAT (deliberate partial delivery):** D71's floor also names the **RS research subagent**, which is the
  *next* build phase (loop-cognition, ROADMAP). So today the skip-floor = **default-FAIL (exists) + `kata-defer`
  assumption-log**, with the **RS slot documented and wired-for** but lit when RS lands. The grill side
  (light/standard/full) is **fully functional immediately**.

## 2. LOCKED decisions (micro-picks resolved 2026-06-18; each traces to D71/D72)
**M1 — `skip` lives as a value of `tiers["kata-grill"]`** (`skip | essential | standard | advanced`), NOT a
separate `grillDepth` field — one source of truth, no divergence risk. Human-facing dial labels
`skip|light|standard|full` map to config values `skip|essential|standard|advanced`. *(→ D73.)*

**M2 — `kata-defer` is built once with both roles** (D71 assumption/ambiguity log + D42 out-of-scope parking) —
identical capture-to-file mechanic, near-zero marginal cost over a throwaway log.

**M3 — `kata-defer` category = `handoff`** (both its artifacts surface at the gate/handoff boundary). Optional
module `kata/module/defer` (D43 — additive, not spine).

**M4 — `skip` engages the floor, never bypasses the gate.** On `skip`, `kata-orchestrate` dispatches **no grill
skill**; it freezes the priming prompt as the spec input and turns on the floor (default-FAIL stays; RS slot;
`kata-defer` assumption-log active). The default-FAIL `kata-evaluate` gate is **never** skipped (D22/D33).

## 3. Where it lives
| Path | Change | What |
|---|---|---|
| `protocol/config.md` | modify | `tiers["kata-grill"]` accepts `"skip"`; document the dial↔value map + the floor it engages |
| `skills/coordinate/kata-readiness/SKILL.md` | modify | **Scope 3 — priming-prompt richness/ambiguity** → recommends a grill depth (read-only; returns to bootstrap) |
| `skills/coordinate/kata-bootstrap/SKILL.md` | modify | **grill-depth question (D46)** pre-filled from readiness; writes `tiers["kata-grill"]` incl. `skip`; on `skip` notes the floor |
| `skills/coordinate/kata-orchestrate/SKILL.md` | modify | branch on `tiers["kata-grill"]=="skip"` → no grill dispatch; freeze priming prompt; engage floor. Promote the `kata-defer` prose ref from "backlog" |
| `skills/handoff/kata-defer/SKILL.md` | **create** | the floor safety net + D42 parking; module `kata/module/defer`; cost-weight 1; no Agent |
| `skills/plan/kata-grill/RUBRIC.md` | modify | short "depth dial incl. skip → floor" note (the grill↔RS spectrum entry point) |
| `docs/DESIGN.md` | modify | new section: the **Priming-and-Grill / grill↔RS ambiguity-resolution spectrum** (D71) |
| `.planning/SKILL-COST-RATINGS.md` · `docs/TAXONOMY.md` | modify | register `kata-defer` (module) |
| `README.md` | regenerate | `validate_skills.py --write` inserts the row (25→**26 skills**); hand-author the Use cell |
| `tools/tests/test_validate_skills.py` | modify | D71 test seam: config.md documents `skip`; `kata-defer` present + category handoff |
| `.planning/{STATE,ROADMAP,DECISIONS}.md` | modify | status; **D73** (config representation ADR) |

**Held at version 0.1.0** (pre-release policy A). `kata-defer` ships `experimental`.

## 4. Backward-compatibility (checkable)
- **BC1** Absent/default config ⇒ today's behavior: `tiers["kata-grill"]` missing ⇒ mode default (Standard);
  `skip` is opt-in only. *Check:* a run with no grill-depth set grills at Standard exactly as before.
- **BC2** The gate is structural: `skip` engages the floor but `kata-evaluate` stays default-FAIL, no Write.
  *Check:* validator reports kata-evaluate cost 2, no Write; orchestrate's final gate unchanged.
- **BC3** All skills `0.1.0` (policy A). *Check:* validator green; no version bumped.
- **BC4** RS not wired pre-loop-cognition: skip-floor names RS in prose only, no CONSULT/dispatch call-site.
  *Check:* grep shows no `kata-research` wikilink/dispatch (it's unbuilt — prose-only, like A4 did for kata-defer).

## 5. Acceptance (default-FAIL, runnable)
- **A1** `cd tools && uv run pytest -q` → all pass (incl. the new D71 config/skip + kata-defer tests).
- **A2** `uv run python validate_skills.py` → `26 skills checked — 0 error(s)`, README in sync, `kata-defer`
  frontmatter conformant (category handoff; `kata/module/defer`; cost-weight 1).
- **A3** `protocol/config.md` documents the `skip` rung + dial map; no `[[kata-research]]` wikilink exists yet.
- **A4** Fresh-context `kata-review` (D15) over the full diff returns SHIP — confirms: (a) `skip` engages the
  floor and never bypasses the default-FAIL gate; (b) `kata-defer` is read/append-only at the boundary, no
  Agent; (c) the dial has one source of truth (`tiers["kata-grill"]`); (d) RS is prose-only (no dangling link).
- **A6** The assumption-log is **actually graded, not asserted:** `kata-evaluate` rubric item 8 reads
  `ASSUMPTIONS.md` and fails prompt-contradicting assumptions; the orchestrate Final gate points the evaluator
  at it. The floor framing is consistent across config/bootstrap/orchestrate/docs/DESIGN (floor always-on; grill
  additive; `skip`≠`light`). *(Both findings from the first review HOLD; fixed and re-froze.)*

## 6. Scope guard
Skill-body + protocol + docs wiring; one new module skill (`kata-defer`). No change to the execution machinery,
no RS build (that is the next phase). Both grill and skip paths end at the same `kata-evaluate` default-FAIL gate.

---
**FROZEN.** Build order: config → readiness → bootstrap → orchestrate → kata-defer → RUBRIC/docs → register/README
→ tests → planning-docs → validator+pytest → fresh-context `kata-review`. Changes are deliberate re-freezes.
