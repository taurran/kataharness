---
date: 2026-06-19
spec: dogfood-selfup-1
status: RUNNING — version-up dogfood of KataHarness on itself (manual-operator drive)
target: KataHarness (existing repo, version-up)
baselineGate: "cd tools && uv run pytest -q  &&  uv run python validate_skills.py"
baseline: 38 tests passed · validator 31 skills / 0 errors  (green @ 7888f28… / 8a9f58f)
tags: [dogfood, version-up, self-improvement, loop-live-test, evaluate-depth-test]
---

# Dogfood #1 — self version-up of KataHarness

**Dual purpose:** (1) exercise the version-up machinery on a real target (itself); (2) stress-test whether the
loop's **evaluation + end report** are deep enough to trust a live run (the user's open question). Deliberately
**small feature** to isolate *machinery + evaluation* from feature complexity.

## Feature (the increment)
Turn a **prose-only conformance rule into an enforced structural check**: `allowed-tools` is load-bearing
(least-privilege security + cost surface) and documented in `docs/STANDARDS.md`, but the validator never checks
it. Make it a **validated frontmatter key**: present + a **non-empty list of strings**. (The documented
evaluator "MUST omit Write/Edit" rule is a *separate, thornier* enforcement — recorded as a finding, not in
this footprint.)

## Phase: READINESS (kata-readiness) — verdict + findings
- ✅ Git repo, baseline **green** (38 / 31-0), tooling on PATH (`uv`, pytest).
- ⚠️ **FINDING R1 (real):** `kata-readiness` Scope-2 says *version-up BLOCKs if tree-sitter is unavailable*
  (kata-graph needs AST). **tree-sitter is NOT installed here** → a strict reading **BLOCKs this version-up** —
  even though the change touches only the validator + tests + a doc and needs **no** structural graph. **The
  rule is too coarse:** it blocks graph-irrelevant version-ups. *Deliberate operator override:* footprint needs
  no `kata-graph`; proceeding. → backlog: scope the tree-sitter BLOCK to runs that actually require the graph
  (or make graph optional when footprint ∌ code-structure).
- ⚠️ **FINDING R2 (process):** the loop is being driven **manually** (no automated orchestrate/worktree/subagent
  dispatch, no installed host) — the multi-agent automation + install layer aren't wired. Tractable for a tiny
  footprint; would not scale. (Expected; confirms install/multi-model briefs are real.)

## Phase: GRILL — skip (priming prompt is precise)
Feature is fully specified above; `tiers["kata-grill"] = skip` → lean on the autonomous floor. Assumptions
logged below (the kata-defer ASSUMPTIONS role).
- **A1:** `allowed-tools` becomes **REQUIRED** (was documented OPTIONAL). Safe — all 31 skills already carry it
  (verified). STANDARDS updated to match; recorded as a decision.
- **A2:** "well-formed" = a non-empty YAML list whose entries are all strings. Tool-name *validity* (is `Frobnicate`
  a real tool?) is **out of scope** — unknowable agnostically.

## Phase: PLAN (footprint-scoped, frozen) — single vertical slice
**Footprint (disjoint, version-up = modified ∪ reverse-deps):**
- `tools/validate_skills.py` — add `REQUIRED_KEYS += ("allowed-tools",)` + a new `check_allowed_tools` (non-empty
  list of strings).
- `tools/tests/test_validate_skills.py` — seams: good-fixture still clean; a `bad-tools` fixture errors.
- `tools/tests/fixtures/bad-tools/...` — a SKILL.md with malformed `allowed-tools` (string, not list).
- `tools/tests/fixtures/good/...` — ensure the good fixture carries a valid `allowed-tools` (else the new
  REQUIRED key would break the good-fixture test — caught by the gate).
- `docs/STANDARDS.md` — `allowed-tools` OPTIONAL → **REQUIRED**; note the enforced shape.
**Method:** kata-tdd — write the failing fixture/test first (red) → implement the check (green) → full regression.
**Gate (default-FAIL):** the baselineGate stays green (full suite + validator) **and** the new seams pass.

## Phase: EXECUTE (kata-tdd)
- **RED:** added `bad-tools` fixture (allowed-tools as a string) + 2 seams → failed (`check_allowed_tools`
  missing, key not REQUIRED). ✓ proved the tests bite.
- **GREEN:** `REQUIRED_KEYS += "allowed-tools"`; new `check_allowed_tools` (non-empty list of strings); added
  `allowed-tools` to the good fixture (the REQUIRED key would otherwise break its `== []` test — caught exactly
  as designed); STANDARDS OPTIONAL→REQUIRED.
- **Gate:** full suite **40 passed** (was 38; +2 seams) · validator **31 / 0**. Regression contract held
  (baseline green ∧ new tests green).

## Phase: EVALUATE — fresh-context, no-write, default-FAIL (kata-evaluate) → **GATE: PASS**
A fresh-context Opus evaluator (Fable down) ran the gate **itself** (40 passed · 31/0) and **proved the new
check non-vacuous by deleting it** (the `bad-tools` test then fails — the string-not-list case is caught *only*
by the new shape check, since REQUIRED_KEYS sees the key present). AC1–AC6 all MET; footprint = validator/docs/
tests only, **no `skills/` file touched**, no existing check weakened.
- **Hygiene finding (applied):** making `allowed-tools` REQUIRED added an *unintended secondary* "missing key"
  error to the sibling bad fixtures. Fixed — added `allowed-tools` to bad-name/bad-cost/bad-link/bad-tier +
  good-tier so each fixture isolates exactly one defect. Gate re-run green (40 / 31-0).

## Phase: IMPROVE — the headline finding (answers the user's open question)
**Q: "Is the end-of-run writeup enough to evaluate a live run in depth?" → Empirically: NO, not from a prose
RUN.md alone.** The evaluator could only trust this run because it **re-ran the gate locally**. As a standalone
artifact the writeup lacks the machine-checkable evidence in-depth evaluation needs. Concrete gaps to close
(→ next dogfood / `kata-improve` target — a real upgrade to `kata-report`/`kata-evaluate`):
1. **Self-emitted `RESULT.json`** — gate name + **verbatim** stdout + exit codes + pass/fail counts + timestamp.
2. **Baseline + result commit SHAs pinned** (before/after), so the run is reproducible, not "uncommitted on master".
3. **Footprint manifest + diff-stat**, with an assertion that touched files ⊆ the PLAN's footprint.
4. **Recorded mutation/non-vacuity proof** — bake "would this test fail if the asserted line were removed?" into
   `kata-tdd` and record its result (the single most valuable thing the evaluator did by hand).
5. **Corpus-wide "new findings" delta** — surface side effects (exactly what caught the bad-fixture noise above)
   automatically, not by luck.
6. (minor) provenance of the gate command from `kata.config.baselineGate`.

**This is the dogfood's real product:** the machinery works (version-up regression contract held end-to-end),
but the *evaluation artifact* must become **self-sufficient**. Recorded for the next cycle.

## Phase: REPORT → `REPORT.md` (kata-report v1) — and the meta-test of whether it suffices.

