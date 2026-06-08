---
date: 2026-06-07
reviewer: fresh-context adversarial (kata-review style, Sonnet) + Opus triage
scope: Plan A2 — Tier Families (git diff master..modes/A2-tier-families)
verdict: SHIP (all fixes in 01bbc78; D33 logged; blockers re-verified)
tags: [review, adversarial, A2, D15]
---

# REVIEW — Modes A2 (adversarial, D15)

Fresh-context red-team of the four tier-family splits. Validator was green; this pass attacked the *design*
of the split and found the subtle failure mode of tiering: **structural invariants accidentally tiered.**
Surfaces 3 (no-bleed), 4 (discovery triggers), 5 (family-alias integrity), 8 (scope) came back clean.

## The principle the review surfaced → D33
The three blockers share a root cause: **the cheap tiers dropped spine invariants, not just depth.**
no-self-certification (L8), no-drift (verbatim LOCKED decisions), and DRY-by-pointer are *structural* — they
must hold at **every** tier. Tiers may vary depth/breadth/rigor; they may NOT relax a spine invariant. This
generalizes D22 (kata-evaluate never tiered) into a rule: **structural invariants are never tiered.** Logged
as **D33**.

## Blockers (HOLD) — all FIX-NOW
| # | Sev | Finding | Fix |
|---|---|---|---|
| H1 | High | `kata-review-standard` re-itemizes all 5 attack surfaces (DRY break — the default tier duplicates its RUBRIC) | collapse to "run all five surfaces as defined in `../kata-review/RUBRIC.md`"; keep only the depth framing |
| H2 | High | `kata-grill-essential` silent on the RUBRIC's "don't grade your own convergence" backstop (the L8 anti-bias) — ambiguous whether essential self-certifies | essential MUST invoke the convergence gate **scoped to its top-risk branches** (cheapest review tier); a SHIP closes it. No tier self-certifies (D33) |
| H3 | High | `kata-plan-essential` drops `read_first`+`action` from per-task requirements — `action` carries the verbatim LOCKED decisions (the no-drift line) | essential MUST require `owns`+`action`(verbatim LOCKED decisions)+`verify`+`acceptance_criteria`; `read_first` present but may be coarse. The verbatim-decision quote is non-waivable at any tier (D33) |

## Secondary — FIX-NOW (cheap)
| # | Sev | Finding | Fix |
|---|---|---|---|
| F4 | Low | `kata-grill-advanced`/`kata-plan-advanced` use `(see \`kata-<verb>-standard\`)` sibling prose refs → couples tiers | point to the RUBRIC's full-method section instead |
| F5 | Low | grill tiers dropped `ubiquitous-language`; plan tiers dropped `waves` (domain tags) | restore both across the tiers (faithfulness, cf. A1 F6.1) |
| F6 | Low | `TIER_RE` has no per-family allowed-tier map → `kata-plan-light` would pass | add `FAMILY_TIERS` map; tier must be valid for the family |
| F7 | Low | RUBRIC wikilinks unvalidated (load_skills globs only SKILL.md) | add `check_rubric_wikilinks` over `*/*/RUBRIC.md` |
| F8 | Low | `docs/TAXONOMY.md` cost-weight prose still names pre-split single weights | reword to reflect tier ranges |

## Resolution — CLEARED (2026-06-07, commit `01bbc78`)
All 8 FIX-NOW items applied + committed. Re-verified: `11 passed`, validator exit 0, and the structural
blockers probed directly — `kata-grill-essential` now runs the convergence gate scoped to its branches
(non-waivable, D33); `kata-plan-essential` keeps `action`+verbatim LOCKED-decision quoting; `kata-review-standard`
points to the RUBRIC instead of re-itemizing; validator gained `FAMILY_TIERS` (per-family tier validation) +
`check_rubric_wikilinks`. **HOLD → SHIP.** Principle locked as **D33** (structural invariants are never tiered).
