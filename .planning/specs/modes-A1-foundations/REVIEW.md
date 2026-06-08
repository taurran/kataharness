---
date: 2026-06-07
reviewer: fresh-context adversarial (kata-review style, Sonnet) + Opus triage
scope: Plan A1 — Foundations (git diff master..modes/A1-foundations)
verdict: SHIP (all FIX-NOW resolved in 4df4baf; blockers re-verified)
tags: [review, adversarial, A1, D15]
---

# REVIEW — Modes A1 (adversarial, D15)

Fresh-context red-team of A1. Conformance gate was all-green; this pass attacked correctness and found
real defects (the L6/L10 lesson: conformance ≠ correctness). **Verdict: HOLD** — 4 blockers + secondary
findings. Opus triage disposition below: **FIX-NOW** (resolve before merge) vs **BACKLOG** (track, address
by A2). Surfaces 1.3/4.2/4.3/5/8.1/8.2 came back clean (regex anchoring, body `---` handling, cost-weight
fidelity 15/15, no scope creep, no TAXONOMY/STANDARDS contradiction beyond 6.2).

## Blockers (HOLD)
| # | Sev | Finding | Disposition |
|---|---|---|---|
| 1.1 | Critical | `parse_frontmatter` returns a truthy non-dict (YAML list/scalar) → every check crashes `AttributeError` before any ERROR → **not fail-closed** | **FIX-NOW** — coerce non-dict → `{}` (then missing-keys ERROR → exit 1) |
| 1.2 | High | `main()` calls `regenerate_readme` *before* `run_checks`; a bad `category`/missing `cost-weight` crashes `_build_index` mid-write | **FIX-NOW** — validate first; `--write` only when no non-README errors (avoid the sync-vs-write deadlock) |
| 7.1 | High | `protocol/dependencies.md` never states the manifest's **file name/location** → Spec-D has no entry point | **FIX-NOW** — document `kata.dependencies.json` at branch root |
| 6.2 | Medium | `kata-context` tagged `kata/spine` but **absent from the spine list** in TAXONOMY.md + MODES-DESIGN.md → A3 would misclassify it | **FIX-NOW** — `kata-context` IS spine; add it to both lists (the docs were incomplete, the tag is right) |

## Secondary — FIX-NOW (cheap + correctness/faithfulness)
| # | Sev | Finding | Disposition |
|---|---|---|---|
| 6.1 | Medium | 9 skills **dropped meaningful domain tags** in the restructure (e.g. `no-write` on evaluate/review, `plan-guardian` on orchestrate, `git` on worktree) — plan said "preserve existing" | **FIX-NOW** — restore the dropped domain tags |
| 2.1 | High(latent) | `_parse_existing_use` greedy regex truncates a `Use` cell containing `|` on round-trip | **FIX-NOW** — split-by-`|`, take last column; note `|` must be escaped |
| 3.2 | Medium | `check_protocol_schemas` omits `tiers`+`bakeoff` (the A2/A3 tier-resolution mechanism) from config.md required terms | **FIX-NOW** — add both |
| 2.2 | Medium | No pytest exercises `check_readme_sync` against the real tree | **FIX-NOW** — add `test_real_tree_readme_in_sync` |
| 2.3 | Medium | `_splice_index` raises bare `ValueError` if markers absent | **FIX-NOW** — guard with a clear `SystemExit` message |
| 7.2 | Medium | manifest mentions "hash-verified" but defines no `hash` field | **FIX-NOW** — add optional `hash` field to the schema |
| 7.3 | Medium | `effort.reasoning` enum `xhigh`/`max` may not match the host API | **FIX-NOW** — note that A3 maps these to the host's effort enum (decouple) |
| 6.3 | Low | README spine bullet #6 still says "this index is the source of truth" (contradicts STANDARDS §3/D28) | **FIX-NOW** — reword to "generated catalog" |
| 6.4 | Low | `bad-cost`/`bad-link` fixtures aren't schema-v2 except their one defect (misleading examples) | **FIX-NOW** — make them conformant-except-the-tested-defect |

## Secondary — BACKLOG (inherent or A2-time)
| # | Sev | Finding | Disposition |
|---|---|---|---|
| 3.1 | Medium | `check_protocol_schemas`/`check_taxonomy_present` substring-match → can't detect substantive erasure | **BACKLOG** — document as a known limitation; deeper structural checks if it bites |
| 3.3 | Low | `check_tags_namespace` allows bogus `kata/...` sub-namespaces (e.g. `kata/tier/typo`) | **BACKLOG (A2)** — add a `kata/...` prefix allowlist when `kata/tier/<tier>` becomes load-bearing |

## Resolution — CLEARED (2026-06-07, commit `4df4baf`)
All 13 FIX-NOW items applied + committed. Re-verified: `9 passed`, validator exit 0, and the two blockers
probed directly — list/non-dict frontmatter now coerces to `{}` (fail-closed, no crash); `--write` refuses on
non-README skill errors; `no-write`/`plan-guardian`/etc. domain tags restored; `kata-context` added to the
spine in TAXONOMY + MODES-DESIGN; manifest location (`kata.dependencies.json`) documented. **HOLD → SHIP.**
BACKLOG items 3.1 (substring-match limitation) + 3.3 (tags sub-namespace allowlist, A2-time) tracked in
`.planning/BACKLOG.md`.
