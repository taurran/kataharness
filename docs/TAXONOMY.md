# TAXONOMY — categories, naming, tier-families, spine-vs-module

> The organizing scheme that keeps the suite discoverable and consistent (D18). Pairs with `docs/STANDARDS.md`
> (frontmatter/versioning) and `docs/MODES-DESIGN.md` (the modes system).

## Categories (= loop phases)
`plan` · `coordinate` · `execute` · `evaluate` · `handoff` · `meta` · `cognition`. A skill's `category`
frontmatter MUST be one of these; its directory lives under `skills/<category>/`.

## Naming — `kata-<verb>`
Verb-first, action-oriented, collision-safe: `kata-grill`, `kata-plan`, `kata-orchestrate`. The frontmatter
`name` equals the directory name (STANDARDS §2; enforced by `tools/validate_skills.py`).

## Tier-families (D26) — `kata-<verb>-<tier>`
A **tiered family** is a skill that exists at multiple depths for cost/quality trade-offs. Layout:
```
skills/<cat>/kata-<verb>/RUBRIC.md          # the tier-INVARIANT method (shared). No SKILL.md ⇒ not invocable.
skills/<cat>/kata-<verb>-<tier>/SKILL.md    # a thin PEER carrying ONLY its depth/breadth/stopping knob + a pointer to ../kata-<verb>/RUBRIC.md
```
- **Tiers:** `kata-grill` · `kata-review` · `kata-plan` → `essential` / `standard` / `advanced`;
  `kata-diagnose` → `light` / `full`.
- **Family alias:** a bare `[[kata-<verb>]]` reference (in skills/docs/prose) means **the family,
  tier-agnostic**. `kata-orchestrate` resolves it to a concrete tier via `kata.config.tiers` (fallback:
  **Standard**, D25). So cross-skill references stay tier-agnostic by design.
- **Why peers + shared rubric:** DRY-by-pointer with zero cross-tier bleed of the depth instructions (D21);
  the rubric move is also the grill efficiency refactor.
- **Never tiered:** `kata-evaluate` (the conformance floor / consistency invariant, D22), `kata-orchestrate`
  (single config-driven dispatcher, D24d), all weight-1 skills, and the pre-flight gate (a spine floor, D29).

## Spine vs module
- **Spine** (always runs — the consistency machine): `kata-grill` · `kata-context` · `kata-design-doc` · `kata-plan` ·
  `kata-orchestrate` · `kata-board` · `kata-worktree` · `kata-tdd` · `kata-evaluate` · `kata-handoff` ·
  `kata-selfhandoff` · (pre-flight, Spec D). Every mode ends at the same `kata-evaluate` default-FAIL gate.
- **Modules** (additive, independent, declare needs/produces/slot — D20): `quality` (`kata-review` +
  `kata-diagnose` + deeper grill/plan) · `design` (own spec) · `bakeoff` (Spec B) · `improve` (`kata-improve`).

## cost-weight (1–5)
Each skill's `cost-weight` frontmatter (authority: `.planning/SKILL-COST-RATINGS.md`) lets `kata-bootstrap`
price a mode + each à-la-carte add. Dominant axis = amplification (spawn ≫ loop ≫ none). Heaviest:
`kata-orchestrate` (5) > `kata-grill` (4) > `kata-diagnose`/`kata-tdd`/`kata-plan` (3).

## Protocol files
`protocol/config.md` (`kata.config`) · `protocol/dependencies.md` (manifest) · `protocol/board.md` ·
`protocol/state.md` · `protocol/handoff.md`. Tracking surfaces (the installed-library registry, a future
`kata-tasklist` board) expose documented pointers here so an *optional* external PM overlay can attach
without the core depending on it (D30).
