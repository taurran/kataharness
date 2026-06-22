---
date: 2026-06-20
spec: greater-loop
phase: 1 — INITIATION
status: FROZEN — partitions Phase 1 into disjoint slices for an orchestrated foreground-parallel build
designRef: ./DESIGN.md §1–§4 (FROZEN, D87–D90) · D91 (module structure) · ./ROADMAP.md Phase 1
delivery: build-through (no test ceremony until Phase 4; per-merge correctness gates apply)
tags: [plan, greater-loop, phase-1, initiation, disjoint-ownership, waves, frozen]
---

# Phase 1 — INITIATION · frozen PLAN

Builds the **front half** of the Greater Loop: a self-contained `modules/initiation/` (own `AGENTS.md` + its
skills, per **D91**) fronted by **`kata-initiate`**, which ingests intent, captures a frozen **`INTENT.md`**,
interactively configures target/platform/vault, and drives spec-to-ready under dual control. Two slices built in
parallel by Sonnet worker subagents in isolated worktrees → integration gate → fresh-context `kata-evaluate`.

## LOCKED decisions (quoted, verbatim — do NOT re-decide)
- **D91 module structure:** modules are self-contained dirs — `modules/<name>/AGENTS.md` + `modules/<name>/<skill>/SKILL.md`.
  Validator discovers `modules/*/*/SKILL.md` alongside `skills/*/*/SKILL.md`.
- **D88 / DESIGN §2:** `kata-initiate` is the front door — ingest → classify `kind: project|research|version-up`
  → capture the GOAL to a **frozen `INTENT.md`**; interactive target/platform/vault config (install-portability
  config layer folds in); **dual spec-to-ready control** (user "execute" anytime OR grill self-proposes execute).
  Composes `kata-readiness`/`kata-grill`/`kata-bootstrap`/`kata-context` — composes, never reimplements.
- **INTENT.md schema is PINNED** (DESIGN §2): `kind, goal, fixes[], features[], modulesAdded[], changeSummary,
  target{kind,path,vault,platform}, grillDepth, readiness`. Slices may not fork it.
- **BC (DESIGN §9):** `INTENT.md` absent ⇒ the harness reads the frozen DESIGN as today. Initiation is additive.

## Wave DAG
```
Wave 1 (parallel):  I1 (validator plumbing + INTENT contract) ──┐
                    I2 (the initiation module) ─────────────────┘   (disjoint files; I2 authored to pass I1's
Integration:        merge I1+I2 → extended validator now SEES kata-initiate → --write regen README (32 skills)
                    → full green gate → fresh-context kata-evaluate                  extended validator at integ.)
```
I1 and I2 own disjoint files, so they build in parallel. I2's new module skill is only *discovered* by the
extended validator (I1's change), so combined conformance is proven at the **integration gate** (Phase-0 pattern).

---

## Task I1 — module discovery plumbing + the INTENT.md contract
**Owns (disjoint):**
- `tools/validate_skills.py` (EDIT)
- `tools/tests/test_validate_skills.py` (EDIT)
- `protocol/intent.md` (NEW)

**read_first:** `tools/validate_skills.py` (esp. `load_skills`, `_valid_skill_targets`, `check_readme_sync`,
`REQUIRED_PROTOCOL`), `tools/tests/test_validate_skills.py`, `.planning/specs/greater-loop/DESIGN.md` §2 (INTENT
schema), an existing protocol doc (e.g. `protocol/orientation.md`) for house style.

**action:**
1. **`protocol/intent.md` (NEW)** — document the PINNED `INTENT.md` artifact schema exactly per DESIGN §2:
   frontmatter fields `kind` (`project|research|version-up`), `goal`, `fixes[]`, `features[]`, `modulesAdded[]`,
   `changeSummary`, `target` (`{kind: self|existing|greenfield, path, vault, platform}`), `grillDepth`
   (`skip|light|standard|full`), `readiness`. Note it is **frozen at the end of initiation** and is the harness's
   hand-off (BC: absent ⇒ harness reads the frozen DESIGN). Match the terse table+notes style of existing
   `protocol/*.md`.
2. **Extend the validator to discover module skills (D91):**
   - `load_skills`: discover **both** `skills/*/*/SKILL.md` **and** `modules/*/*/SKILL.md` (add a `MODULES_DIR =
     REPO_ROOT / "modules"`; glob both roots; sort stably). All existing checks (frontmatter, tags, cost-weight,
     allowed-tools, agnostic, category) then apply uniformly to module skills.
   - `_valid_skill_targets`: include module skill names so `[[kata-initiate]]` wikilinks resolve.
   - `check_readme_sync` guard: currently `all(SKILLS_DIR in s.dir.parents …)` — fix so it treats a skill as a
     "real repo skill" when its dir is under **SKILLS_DIR OR MODULES_DIR** (otherwise discovering a module skill
     silently DISABLES README-sync enforcement — a real bug). README index includes module skills (grouped by
     their functional `category`).
   - Add `"intent.md"` to `REQUIRED_PROTOCOL` with a few required terms it must document, e.g.
     `["kind", "goal", "fixes", "features", "changeSummary", "target", "grillDepth", "readiness"]`.
3. **Tests (`test_validate_skills.py`, EDIT):** add cases proving — (a) a fixture module skill at
   `modules/<m>/<skill>/SKILL.md` is **discovered** by `load_skills` and validated like a normal skill;
   (b) a module skill name is a valid wikilink target; (c) the `intent.md` protocol requirement fires when the
   file is missing a required term (use the existing protocol-test pattern). Keep tests hermetic (tmp dirs /
   fixtures); do NOT depend on the real `modules/initiation/` (that's I2, may not exist in this worktree).

**verify (default-FAIL):** `cd tools && uv run pytest tests/test_validate_skills.py -q` (START red on the new
cases, END green) → full `uv run pytest -q` (stays green) → `uv run python validate_skills.py` (still **31 skills
/ 0 errors** in THIS worktree — no real module skill exists here yet; the count rises to 32 only at integration
once I2's skill is present).

**acceptance (falsifiable):**
- `load_skills()` returns a fixture module skill placed under `modules/*/*/SKILL.md`.
- Removing a required term from a fixture `intent.md` makes `check_protocol_schemas` emit an ERROR.
- The README-sync guard still enforces sync when a module skill is present (does not silently skip).
- `protocol/intent.md` documents every PINNED INTENT field.

**threat model:** none new — validator + a markdown contract; no attacker-reachable surface.

---

## Task I2 — the initiation module (`modules/initiation/`)
**Owns (disjoint):**
- `modules/initiation/AGENTS.md` (NEW)
- `modules/initiation/kata-initiate/SKILL.md` (NEW)

**read_first:** `.planning/specs/greater-loop/DESIGN.md` §1–§4, `docs/STANDARDS.md` §1 (frontmatter — REQUIRED
keys incl. `allowed-tools`), the root `AGENTS.md` (spine + conventions), `protocol/orientation.md` (the
nested-AGENTS rollup that this module's AGENTS.md plugs into), and the skills it composes:
`skills/coordinate/kata-bootstrap/SKILL.md`, `skills/coordinate/kata-readiness/SKILL.md`,
`skills/plan/kata-grill-standard/SKILL.md`, `skills/plan/kata-context/SKILL.md`.

**action:**
1. **`modules/initiation/AGENTS.md` (NEW)** — the module's own driving doc (nested-rollup target). State: the
   module's single responsibility (front-half: intent → frozen `INTENT.md` → ready-to-execute); its **contract**
   (input: the user's design/brief + system prompt; output: a frozen `INTENT.md` + full context handed to the
   harness); that it **composes** existing skills and never reimplements the spine; that a platform may swap this
   whole dir (bring its own `AGENTS.md`/installer). Keep it focused — it rolls up *under* the root AGENTS.md, so
   only state what differs/specializes, not the whole spine.
2. **`modules/initiation/kata-initiate/SKILL.md` (NEW)** — the front-door skill. Conformant frontmatter:
   `name: kata-initiate`, `category: coordinate`, `status: experimental`, `version: 0.1.0`, `agnostic: true`,
   `license: Apache-2.0`, `cost-weight: 3`, `allowed-tools: [Read, Grep, Glob, Write, Edit]`, `model: fable`,
   `tags: [kata/coordinate, kata/module/initiation, freeze, intent, front-door]` (MUST include `kata/coordinate`
   AND `kata/module/initiation`). Body specifies the flow per DESIGN §2:
   - **Ingest** the user's design/brief (system prompt and/or a project-brief file) → classify
     **kind: project | research | version-up**.
   - **Capture the GOAL → write + freeze `INTENT.md`** per the `protocol/intent.md` schema (esp. for version-up,
     evaluate what the *actual goal* of the version-up is — the gap D88 names).
   - **Interactive target/platform/vault configuration** (GL-R3c): lead the user through target
     (`self | existing | greenfield`) · vault (link/scaffold PokeVault, point at own, or aim-each-folder) ·
     platform (Claude | the work host/Quick | Kiro). Note: installer *mechanics* are deferred to Phase 5; this is the
     config layer only.
   - **Dual spec-to-ready control** (GL-R2b): drive `kata-grill` at the chosen depth; the user may say **"execute"
     at any time** (hard bail) OR the grill **self-judges readiness and proposes execute** (user confirms). Either
     path **freezes `INTENT.md`** and hands full context to the harness.
   - Composes `[[kata-readiness]]`, `[[kata-grill]]`, `[[kata-bootstrap]]`, `[[kata-context]]` (these resolve).
     **Do NOT wikilink `kata-closeout` / `kata-understand` / `kata-loop`** (not built yet — unresolved-wikilink
     ERROR). Reference them in prose without `[[ ]]` if needed.
   - Honor BC (DESIGN §9): `INTENT.md` absent ⇒ harness behaves as today.

**verify (default-FAIL):** In THIS worktree the old validator can't see `modules/`, so self-check the SKILL.md
frontmatter manually against `docs/STANDARDS.md` §1 (all REQUIRED keys present; tags include `kata/coordinate` +
`kata/module/initiation`; `agnostic: true`; valid semver; name == dir). Run `cd tools && uv run pytest -q`
(must stay green — I2 touches no code/tests). Combined validator conformance (32 skills / 0 errors) is proven at
**integration** once merged with I1.

**acceptance (falsifiable):**
- `modules/initiation/AGENTS.md` states the module contract (INTENT.md in→out) and that it composes, never gates.
- `kata-initiate` SKILL.md frontmatter passes every `docs/STANDARDS.md` §1 rule (verified at integration: 32/0).
- The body covers all four flow elements (ingest/classify · capture+freeze INTENT.md · interactive config · dual
  control) and writes `INTENT.md` per `protocol/intent.md`.
- No unresolved wikilinks (only composes already-built skills).

**threat model:** none new — markdown skill + module doc; `allowed-tools` scopes it to Read/Grep/Glob/Write/Edit.

---

## Integration (after both slices green in their worktrees)
1. Octopus-merge `phase1/i1-plumbing` + `phase1/i2-module` into `phase1/integration`.
2. `cd tools && uv run python validate_skills.py --write` — the extended validator now discovers `kata-initiate`
   (32 skills), regenerates the README index. Then `uv run python validate_skills.py` must be **32 skills / 0 errors**.
3. `uv run pytest -q` — full green (109 + I1's new validator tests).
4. Snyk scan on any changed Python (`validate_skills.py`) — fix→rescan→clean (or document FP per Phase-0 pattern).
5. **Fresh-context `kata-evaluate`** (no-write subagent) over this PLAN → PASS/NEEDS_WORK. Then merge to `master`
   → **continue straight into Phase 2** (BUILD-THROUGH). Backout safety: tag `pre-phase1` before merge.

## Ownership disjointness check
| File | Owner |
|---|---|
| `tools/validate_skills.py`, `tools/tests/test_validate_skills.py`, `protocol/intent.md` | I1 |
| `modules/initiation/AGENTS.md`, `modules/initiation/kata-initiate/SKILL.md` | I2 |
| `README.md` (index regen via --write), integration RESULT.json | Integrator (post-merge) |
No file appears in two lanes. ✓
