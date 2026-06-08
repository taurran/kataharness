---
date: 2026-06-08
branch: master (local only — no remote yet)
commit: f4d7cb0 (Merge modes Spec A2 — tier families)
green: validator 22 skills / 0 errors (exit 0) · pytest 11 passed · Snyk 0
tags: [handoff, modes, A2-merged, checkpoint]
---

# HANDOFF — KataHarness — 2026-06-08 (Spec A1+A2 merged; A3 / D16-A/B decision pending)

> **Fresh session: read in order, confirm green, then resume at NEXT STEP.**

## 1. Read-in order
1. `AGENTS.md` (canonical) · 2. `docs/DESIGN.md` (charter) · 3. `docs/STANDARDS.md` (frontmatter v2 §1) ·
4. **`docs/MODES-DESIGN.md`** (the modes architecture) · 5. `docs/TAXONOMY.md` (tier-family convention) ·
6. `CONTEXT.md` (glossary) · 7. `.planning/STATE.md` · 8. `.planning/DECISIONS.md` (**D1–D33**) ·
9. `.planning/LESSONS-LEARNED.md` (**L1–L10**) · 10. `.planning/SKILL-COST-RATINGS.md` ·
11. the two spec folders: `.planning/specs/modes-A1-foundations/{PLAN,REVIEW}.md` +
`.planning/specs/modes-A2-tier-families/{PLAN,REVIEW}.md`. Re-anchor on the FROZEN plans, not a summary.

## 2. State (confirm green first)
- Branch **master**, commit **f4d7cb0**. Local-only (no git remote yet).
- Gate: `cd tools && uv run pytest -q` → **11 passed**; `cd tools && uv run python validate_skills.py` →
  **`22 skills checked — 0 error(s)`**, exit 0. (`uv` is on PATH.)

## 3. What shipped (Spec A1 + A2, both merged + adversarially reviewed HOLD→SHIP)
- **A1 (foundations):** `tools/validate_skills.py` — the skill-conformance + README-regen validator
  (Python/uv, maintainer-only, D27); schema-v2 frontmatter on every skill (`cost-weight` + `license` +
  namespaced `tags`); frontmatter-generated README index; `protocol/config.md` (`kata.config`) +
  `protocol/dependencies.md` schemas; `docs/TAXONOMY.md`; Apache-2.0 `LICENSE`.
- **A2 (tier families):** `kata-grill`/`kata-review`/`kata-plan` → `-essential`/`-standard`/`-advanced`;
  `kata-diagnose` → `-light`/`-full`; each a thin tier `SKILL.md` over a shared `kata-<verb>/RUBRIC.md`
  (DRY-by-pointer). `kata-design-doc`/`kata-tdd` got a mode depth-hint. `kata-evaluate`/`kata-orchestrate`
  stay single. **22 skills.** Validator gained tier-family rules (`check_tier_family`, `FAMILY_TIERS`,
  `check_rubric_wikilinks`). New principle: **D33 — structural invariants are never tiered.**
- Execution method that worked: subagent-driven (Sonnet implementers, Opus reviews each diff + gates on the
  validator; fresh-context adversarial `kata-review` per spec, D15). The adversarial leg caught real blockers
  the green gate missed in BOTH specs — keep doing it.

## 4. NEXT STEP — in order
**A user decision gates the next phase** (asked at end of last session, not yet answered):
1. **A3 — bootstrap + wiring** (finish the Spec A trilogy): build `kata-bootstrap` (the D24c composition
   ladder — picks mode+modules+effort, cost-preview from `cost-weight`, writes `kata.config`) and teach
   `kata-orchestrate` to **read `kata.config` + resolve family→tier** (fallback Standard, D25). This is what
   makes the A2 tiers actually *dispatch* — today the tier files exist but nothing selects them.
2. **D16 planning-varied A/B** — prove the grill actually differentiates (Arm A plans via
   `kata-grill`→`kata-design-doc`→`kata-plan` for real vs a GSD-planned baseline). **The whole modes edifice
   rests on the planning half being worth it, and that is still unproven** (L10 was a TIE on frozen-plan
   execution). This is the real ship-gate for calling v0.1 "validated."
3. **Pause** — A1+A2 are a clean merged milestone.
- **Opus recommendation: 2 (the D16 A/B) or 3 over 1** — A3 wires machinery whose value hinges on the
  unproven D16. If the user picks A3 anyway: `kata-plan`/writing-plans → A3 plan → subagent-driven
  (Sonnet-execute/Opus-review) → `kata-review` (D15) → merge.

## 5. Suggested next skills
A3 path: `kata-plan` (write the A3 plan) · `kata-write-skill` (author `kata-bootstrap`) · `kata-orchestrate`
(the config-read wiring) · `kata-review` (D15 adversarial pass on everything new).
D16 path: `kata-grill`/`kata-design-doc`/`kata-plan` run for real on a CPP-style target vs a baseline.

## 6. Open decisions for the human
- **The 1/2/3 call above** (A3 vs D16 A/B vs pause). · Set a **git remote** before public release. ·
  Public-release prep (the project is Apache-2.0, public-intended, still local-only).

## 7. Redaction
No secrets / keys / PII. Nothing to redact.
