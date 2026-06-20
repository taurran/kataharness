---
date: 2026-06-20
spec: greater-loop
phase: 2 — CLOSEOUT
status: FROZEN — partitions Phase 2 into disjoint slices for an orchestrated foreground-parallel build
designRef: ./DESIGN.md §3 (FROZEN, D87–D90) · D91 (module structure) · ./ROADMAP.md Phase 2
delivery: build-through (no test ceremony until Phase 4; per-merge correctness gates apply)
tags: [plan, greater-loop, phase-2, closeout, understand-anything, disjoint-ownership, frozen]
---

# Phase 2 — CLOSEOUT · frozen PLAN

Builds the **back half** of the Greater Loop: a self-contained `modules/closeout/` (own `AGENTS.md`, **D91**)
fronted by **`kata-closeout`**, plus the NEW **`kata-understand`** comprehension map. Closeout tracks the run's
machine artifacts (F1), reports, offers the understand-map, and runs the **human decision gate** — it **never
gates correctness** (that stays `kata-evaluate`). Two slices built by Sonnet workers in isolated worktrees →
integration → fresh-context `kata-evaluate`.

## LOCKED decisions (quoted, verbatim — do NOT re-decide)
- **D89 / DESIGN §3:** `kata-closeout` owns the back-half control flow and **composes** `kata-report`,
  `kata-understand`, `kata-handoff`, and git; it runs **after** the default-FAIL gate and **never gates** (it
  reports). It consumes the machine artifacts from F1 — `.kata/{RESULT.json, footprint.json, mutation.json}` — so
  the record is real, not transcribed. Human gate: *satisfied? → commit/push/merge? → run-again (version-up) or
  build something else?*
- **`kata-understand` (GL-R2c, opt-in):** closeout **offers** it (user opts in per run). It produces a structured
  comprehension map of **what changed + what was built**, **backed by the `kata-graph` runtime (F2 — `tools/
  graph_gen.py` → `kata.graph.json`)**; if the graph is unavailable it **degrades** to a lighter git/diff map with
  a note.
- **D91 module structure:** `modules/closeout/AGENTS.md` + `modules/closeout/<skill>/SKILL.md`; validator already
  discovers `modules/*/*/SKILL.md` (Phase 1).
- **BC / spine:** closeout is additive; default-FAIL is never weakened (closeout reports, never gates).

## Wave DAG
```
Wave 1 (parallel):  C1 (kata-understand) ──┐
                    C2 (kata-closeout + module AGENTS.md) ──┘
Integration:        merge C1+C2 → --write regen README (34 skills) → validate 34/0 → pytest 112 → fresh eval
```
C1 and C2 own disjoint subdirs. **One known cross-slice link:** C2's `kata-closeout` wikilinks `[[kata-understand]]`
(built by C1). In C2's worktree the validator will report **exactly one** unresolved wikilink `[[kata-understand]]`
— that is EXPECTED and resolves at integration once C1 merges. (Same integration-time-resolution pattern as
Phase 0/1.)

---

## Task C1 — `kata-understand` (the understand-anything map)
**Owns (disjoint):**
- `modules/closeout/kata-understand/SKILL.md` (NEW)

**read_first:** `.planning/specs/greater-loop/DESIGN.md` §3, `docs/STANDARDS.md` §1, `skills/plan/kata-graph/SKILL.md`
+ `protocol/graph.md` + `tools/graph_gen.py` (the F2 runtime it is backed by), `protocol/orientation.md` (how
structural maps are projected), an existing well-formed SKILL.md for shape.

**action:** Author `kata-understand` — an **opt-in, read-leaning** skill that produces a structured comprehension
map of *what changed + what was built* in a completed run. Conformant frontmatter: `name: kata-understand`,
`category: handoff` (it is a comprehension/handoff aid), `status: experimental`, `version: 0.1.0`,
`agnostic: true`, `license: Apache-2.0`, `cost-weight: 2`, `allowed-tools: [Read, Grep, Glob, Bash]`,
`model: fable`, `source:` short provenance, `tags: [kata/handoff, kata/module/closeout, understand, graph-backed,
opt-in]` (MUST include `kata/handoff` + `kata/module/closeout`). Body specifies:
- **Graph-backed primary path:** run/refresh the F2 runtime (`tools/graph_gen.py --root . --out kata.graph.json`)
  → read `kata.graph.json` (per `protocol/graph.md`) → project a **comprehension map**: the files/symbols that
  changed this run (intersect the run footprint / git diff with graph nodes), their structural role (rank), and
  what was *added* (new modules/skills/symbols). Keep it a **map**, not a re-evaluation.
- **Light fallback (graph unavailable / greenfield / no tree-sitter):** degrade to a `git diff`-based change map
  (files changed, additions, a short structural summary) **with an explicit note** that the graph backend was
  unavailable. Never hard-fail.
- **Opt-in contract:** this skill is *offered* by `kata-closeout`; it is not part of the default-FAIL gate and
  never blocks. Output is a human-readable understand-map artifact (define its shape inline — sections: Changed,
  Added, Structural-role/Blast-context, Open-questions).
- Compose/reference `[[kata-graph]]` (exists). **Do NOT** wikilink `[[kata-closeout]]` (built in C2, parallel) —
  reference it in prose only, to avoid a cross-slice wikilink error in THIS worktree.

**verify (default-FAIL, limited in worktree):** manually check frontmatter against `docs/STANDARDS.md` §1 (parse
it with the yaml one-liner pattern from the Phase-1 I2 brief: all REQUIRED keys, name==dir, tags include
kata/handoff + kata/module/closeout, agnostic:true). Sanity-run the graph backend it depends on:
`cd tools && uv run python graph_gen.py --root . --out C:/Dev/projects/kataharness/.kata/understand-probe.graph.json`
and confirm it writes a graph (proves the primary path is real). `uv run pytest -q` stays green (112; no code).

**acceptance (falsifiable):**
- Frontmatter passes every STANDARDS §1 rule (verified at integration: 34/0).
- The body specifies BOTH the graph-backed primary path (reading `kata.graph.json`) AND the git/diff light
  fallback with a degradation note.
- The opt-in/never-gates contract is explicit.
- No `[[kata-closeout]]` wikilink (prose reference only).

**threat model:** none new — markdown skill; `allowed-tools` Read/Grep/Glob/Bash (Bash only to run the existing
graph generator, which AST-parses, never executes target code).

---

## Task C2 — `kata-closeout` + the closeout module
**Owns (disjoint):**
- `modules/closeout/AGENTS.md` (NEW)
- `modules/closeout/kata-closeout/SKILL.md` (NEW)

**read_first:** `.planning/specs/greater-loop/DESIGN.md` §3, `docs/STANDARDS.md` §1, the root `AGENTS.md`,
`modules/initiation/AGENTS.md` (the Phase-1 sibling module doc — match its shape), `protocol/orientation.md`,
`skills/evaluate/kata-report/SKILL.md`, `skills/handoff/kata-handoff/SKILL.md`, `skills/evaluate/kata-evaluate/SKILL.md`
(to be clear closeout runs AFTER it and never gates), and `tools/gate_emit.py` / `skills/evaluate/kata-evaluate/SKILL.md`
§"Machine-readable inputs" (the `.kata/` artifacts closeout consumes).

**action:**
1. **`modules/closeout/AGENTS.md`** — the module's driving doc (nested-rollup target), shaped like
   `modules/initiation/AGENTS.md`: single responsibility (back half: track → report → understand → human decision
   → hand to loop-back); contract (input: the completed run + its `.kata/` artifacts + the post-gate verdict;
   output: a report + the human's decision {satisfied, git-actions, run-again|build-new}); states it **composes**
   and **never gates** (default-FAIL stays in `kata-evaluate`); a platform may swap the whole dir.
2. **`modules/closeout/kata-closeout/SKILL.md`** — the back-door skill. Conformant frontmatter: `name:
   kata-closeout`, `category: handoff`, `status: experimental`, `version: 0.1.0`, `agnostic: true`, `license:
   Apache-2.0`, `cost-weight: 2`, `allowed-tools: [Read, Grep, Glob, Bash]`, `model: fable`, `source:`,
   `tags: [kata/handoff, kata/module/closeout, closeout, human-gate, never-gates]` (MUST include kata/handoff +
   kata/module/closeout). Body per DESIGN §3:
   - **Track everything:** consume `.kata/{RESULT.json, footprint.json, mutation.json}` (the F1 artifacts) — the
     record is real, not transcribed. Runs **after** the `kata-evaluate` default-FAIL gate; it **never gates**.
   - **Report:** compose `[[kata-report]]` over those artifacts.
   - **Offer the understand-map:** **offer** `[[kata-understand]]` (opt-in, per run; graph-backed, light fallback).
   - **Human decision gate:** *Are you satisfied?* → *commit / push / merge?* (carry the chosen git actions out)
     → *run again (version-up) or build something else?* — and hand that decision to the conductor's loop-back
     (the conductor is Phase 3; reference `kata-loop` in **prose only**, not as a wikilink — not built yet).
   - Compose `[[kata-handoff]]` for the two-way handoff. Honor BC (additive; never weakens default-FAIL).
   - **Wikilinks allowed:** `[[kata-report]]`, `[[kata-understand]]`, `[[kata-handoff]]`, `[[kata-evaluate]]`
     (all will resolve at integration; `[[kata-understand]]` is C1's — see the cross-slice note below).
     **Do NOT** wikilink `[[kata-loop]]` (Phase 3, unbuilt) — prose only.

**verify (default-FAIL, limited in worktree):** manually check both files' frontmatter against STANDARDS §1
(yaml parse-check). Run `uv run python validate_skills.py` in the worktree: **expect EXACTLY ONE error** — an
unresolved wikilink `[[kata-understand]]` (C1's skill, not present in this worktree; resolves at integration). If
you see ANY OTHER error, fix it. `uv run pytest -q` stays green (112).

**acceptance (falsifiable):**
- `modules/closeout/AGENTS.md` states the module contract and the never-gates property.
- `kata-closeout` frontmatter passes STANDARDS §1 (verified at integration: 34/0).
- The body covers: consume `.kata/` artifacts · compose kata-report · offer kata-understand · human decision gate
  (satisfied/commit·push·merge/run-again·build-new) · compose kata-handoff · never gates.
- Only the single expected `[[kata-understand]]` wikilink is unresolved in-worktree; no `[[kata-loop]]` wikilink.

**threat model:** none new — markdown; `allowed-tools` Read/Grep/Glob/Bash (Bash to read artifacts + carry the
human-approved git actions). The git actions are **human-gated** (push/merge only on explicit approval).

---

## Integration (after both slices green in their worktrees)
1. Octopus-merge `phase2/c1-understand` + `phase2/c2-closeout` into `phase2/integration`.
2. `cd tools && uv run python validate_skills.py --write` — discovers the two new module skills (34 skills),
   regenerates the README index. Then `uv run python validate_skills.py` must be **34 skills / 0 errors** (the
   `[[kata-understand]]` link now resolves).
3. `uv run pytest -q` — full green (112; no new code in this phase).
4. Snyk: no new first-party Python (markdown only) → no scan required; note the pre-existing documented CWE-23 FPs
   are unchanged.
5. **Fresh-context `kata-evaluate`** over this PLAN → PASS/NEEDS_WORK. Then merge to `master` → **continue into
   Phase 3** (`kata-loop` conductor). Backout safety: tag `pre-phase2` before merge.

## Ownership disjointness check
| File | Owner |
|---|---|
| `modules/closeout/kata-understand/SKILL.md` | C1 |
| `modules/closeout/AGENTS.md`, `modules/closeout/kata-closeout/SKILL.md` | C2 |
| `README.md` (index regen via --write), integration RESULT.json | Integrator (post-merge) |
No file appears in two lanes. ✓
