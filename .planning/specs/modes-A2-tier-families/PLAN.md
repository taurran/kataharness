# Modes Spec A2 — Tier Families Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Split the four high-cost/high-variance skills (`kata-grill`, `kata-review`, `kata-plan`,
`kata-diagnose`) into the **tier-family layout** (D26) — a shared `RUBRIC.md` holding the tier-invariant method
plus thin per-tier `SKILL.md` peers carrying only their depth knob — and give `kata-design-doc`/`kata-tdd` a
mode-passed depth hint. Net: the modes system can dispatch the right depth per `kata.config`.

**Architecture:** For each tiered family `kata-<verb>`: the folder `skills/<cat>/kata-<verb>/` keeps a
`RUBRIC.md` (the invariant method — *not* a skill, no SKILL.md) plus any existing `resources/`; the invocable
units become peer dirs `skills/<cat>/kata-<verb>-<tier>/SKILL.md`, each thin (full schema-v2 frontmatter + a
pointer to `../kata-<verb>/RUBRIC.md` + ONLY its depth contract). Bare `[[kata-<verb>]]` stays a tier-agnostic
alias (validator already resolves family folders). `kata-evaluate`/`kata-orchestrate` stay single (D22/D24d).

**Tech Stack:** Markdown skills; the existing `tools/` Python validator (extended for tier-family rules).

**Consistency guardrail (D18/D22):** every tier still produces a frozen artifact that passes the *constant*
`kata-evaluate` floor. Tiers differ in **depth/breadth/rigor**, never in whether the output is valid. Standard
is the default (D25), so the L8-grade deep grill lives in Standard+Advanced; Essential is a deliberate,
labeled PoC downshift.

**Scope guards:** A2 does NOT build `kata-bootstrap` or wire `kata-orchestrate` to read `kata.config` (that is
A3). A2 produces the tier *files* + the validator rules that govern them. The tier dispatch/resolution is A3.

---

## File Structure

| Path | Responsibility |
|---|---|
| `tools/validate_skills.py` (modify) | tier-family rules: tier-skill → matching `kata/tier/<tier>` tag + sibling `RUBRIC.md` must exist |
| `tools/tests/...` (modify/create) | fixtures + tests for a valid tier skill and a tier skill missing its tier tag |
| `skills/plan/kata-grill/RUBRIC.md` (create) + `kata-grill-{essential,standard,advanced}/SKILL.md` (create); `kata-grill/SKILL.md` (delete) | grill family |
| `skills/evaluate/kata-review/RUBRIC.md` + `kata-review-{essential,standard,advanced}/SKILL.md`; delete old | review family |
| `skills/plan/kata-plan/RUBRIC.md` + `kata-plan-{essential,standard,advanced}/SKILL.md`; delete old | plan family |
| `skills/execute/kata-diagnose/RUBRIC.md` + `kata-diagnose-{light,full}/SKILL.md`; delete old | diagnose family |
| `skills/plan/kata-design-doc/SKILL.md`, `skills/execute/kata-tdd/SKILL.md` (modify) | add a "Depth by mode" section (one file, no split) |
| `.planning/SKILL-COST-RATINGS.md` (modify) | add the per-tier weights |
| `README.md` (regenerate), `docs/TAXONOMY.md` (touch-up) | index now lists the tier skills |

**Tier cost-weights** (nest around each family's current weight = its Standard/full tier):
grill **3/4/5** · review **1/2/3** · plan **2/3/4** · diagnose light **2** / full **3**.

### The thin tier-file template (every tier `SKILL.md` follows this)
```markdown
---
name: kata-<verb>-<tier>
description: >-
  <tier-specific trigger — what depth this is and WHEN to pick it>
license: Apache-2.0
version: 0.1.0
category: <cat>
status: experimental
agnostic: true
cost-weight: <tier weight>
allowed-tools: [<same as the family's old SKILL.md>]
model: opus                       # only families that had it (grill, plan)
source: >-                         # same provenance as the family's old SKILL.md
  <...>
tags:
  - kata/<cat>
  - kata/spine                     # or kata/module/quality for review/diagnose
  - kata/tier/<tier>
  - <domain tags from the family>
---
# kata-<verb>-<tier> — <one-line>

**Method:** see [`../kata-<verb>/RUBRIC.md`](../kata-<verb>/RUBRIC.md) — the tier-invariant method (interaction
format, doc-baking, the quality principles, the convergence/output definition). This file sets ONLY the depth.

## Depth contract (<Tier>)
<the depth knob: how many rounds, how much breadth, what to skip, the stopping rule — see per-family below>
```
`RUBRIC.md` is a shared resource (NOT a skill): a short top title + the invariant method moved out of the
old single `SKILL.md`. It carries no skill frontmatter (it has no `SKILL.md`, so the validator never treats it
as a skill). Spine/module tagging: grill + plan tiers are `kata/spine`; review + diagnose tiers are
`kata/module/quality`.

---

## Task 1: Validator — tier-family rules

**Files:**
- Modify: `tools/validate_skills.py`
- Create: `tools/tests/fixtures/good-tier/plan/kata-foo-standard/SKILL.md`, `tools/tests/fixtures/good-tier/plan/kata-foo/RUBRIC.md`
- Create: `tools/tests/fixtures/bad-tier/plan/kata-foo-standard/SKILL.md` (missing the `kata/tier/standard` tag)
- Modify: `tools/tests/test_validate_skills.py`

- [ ] **Step 1: Add the tier-family check**

Append to `tools/validate_skills.py` (after `check_tags_namespace`):
```python
TIER_RE = re.compile(r"^(kata-[a-z0-9]+(?:-[a-z0-9]+)*?)-(essential|standard|advanced|light|full)$")


@check
def check_tier_family(skills: list[Skill]) -> list[Finding]:
    """A tier skill (kata-<verb>-<tier>) must carry the matching kata/tier/<tier> tag and have a
    sibling RUBRIC.md (the family's shared method). Closes A1 REVIEW backlog 3.3."""
    out: list[Finding] = []
    for s in skills:
        m = TIER_RE.match(s.name)
        if not m:
            continue
        family, tier = m.group(1), m.group(2)
        tags = s.frontmatter.get("tags") or []
        if f"kata/tier/{tier}" not in tags:
            out.append(Finding("ERROR", s.dir.name, f"tier skill must tag kata/tier/{tier}"))
        rubric = s.dir.parent / family / "RUBRIC.md"
        if not rubric.exists():
            out.append(Finding("ERROR", s.dir.name, f"tier family missing shared rubric: {family}/RUBRIC.md"))
    return out
```

- [ ] **Step 2: Fixtures**

`tools/tests/fixtures/good-tier/plan/kata-foo/RUBRIC.md`:
```markdown
# kata-foo — shared method (rubric)
The tier-invariant method for the foo family.
```
`tools/tests/fixtures/good-tier/plan/kata-foo-standard/SKILL.md`:
```markdown
---
name: kata-foo-standard
description: A conformant tier-skill fixture.
license: Apache-2.0
version: 0.1.0
category: plan
status: experimental
agnostic: true
cost-weight: 3
tags:
  - kata/plan
  - kata/spine
  - kata/tier/standard
---
# kata-foo-standard
See ../kata-foo/RUBRIC.md.
```
`tools/tests/fixtures/bad-tier/plan/kata-foo-standard/SKILL.md` — identical but **omit** the
`- kata/tier/standard` tag line, and do NOT create a `kata-foo/RUBRIC.md` under `bad-tier/`.

- [ ] **Step 3: Tests**

Append to `tools/tests/test_validate_skills.py`:
```python
def test_good_tier_skill_passes_tier_check():
    assert v.check_tier_family(_skills_in("good-tier")) == []


def test_tier_skill_missing_tag_and_rubric_errors():
    findings = v.check_tier_family(_skills_in("bad-tier"))
    assert any("kata/tier/standard" in f.msg for f in findings)
    assert any("RUBRIC.md" in f.msg for f in findings)
```

- [ ] **Step 4: Verify (no-op on real tree — no tier skills yet)**

Run: `cd tools && uv run pytest -q` → all pass. `uv run python validate_skills.py` → exit 0 (the real tree has
no `kata-*-<tier>` skills yet, so `check_tier_family` finds nothing). Commit:
```bash
git add tools/
git commit -m "feat: validator tier-family rules (tier tag + sibling RUBRIC; closes 3.3)"
```

---

## Task 2: Split `kata-grill` (template + folds the efficiency refactor)

**Files:** Create `skills/plan/kata-grill/RUBRIC.md`; create `skills/plan/kata-grill-essential/SKILL.md`,
`kata-grill-standard/SKILL.md`, `kata-grill-advanced/SKILL.md`; delete `skills/plan/kata-grill/SKILL.md`
(keep `skills/plan/kata-grill/resources/DECISION-LEDGER.md`). Then regenerate the README.

- [ ] **Step 1: Extract the RUBRIC (the invariant method + the efficiency refactor)**

Read the current `skills/plan/kata-grill/SKILL.md`. Move into `skills/plan/kata-grill/RUBRIC.md` the
**tier-invariant** parts (this IS the ~30%-lighter refactor — the heavy narrative leaves the per-tier files):
the anti-pattern/anti-shallow principle, the **Interaction format** (GSD choice-or-text, L7/L8), the
**Doc-baking** formats (glossary/ADR/decision-ledger + checkpoint discipline), the **convergence *definition***
("could two independent builders diverge?"), and the **"don't grade your own convergence"** fresh-context
backstop. Header: `# kata-grill — shared method (RUBRIC)` + a line: "The tier-invariant grill method. The
`kata-grill-<tier>` skills set only depth; they all obey this." No skill frontmatter (this is a resource).

- [ ] **Step 2: Write the three tier files** (template above; `model: opus`, `allowed-tools: [Read, Grep, Glob, Write, Edit]`, `source` from the old file, tags `kata/plan` + `kata/spine` + `kata/tier/<tier>` + `grilling`,`ddd`,`doc-baking`)

Depth contracts (the ONLY substantive difference between the three):
- **essential** (cost 3) — `description`: "Fast, top-risk grill for a PoC/cheap one-shot." Depth: ONE focused
  pass over only the **highest-risk / drift-magnet branches** (classification, magnitude, interface contracts,
  failure behavior); resolve-from-docs aggressively; bake the **decision ledger** only (skip ADRs + glossary
  polish). **Stop** when the top-risk branches are resolved with no contradiction. Explicitly does NOT
  enumerate the full decision tree.
- **standard** (cost 4) — `description`: "Full doc-grounded grill (default)." Depth: the full method —
  enumerate the **whole** decision tree, dependency-ordered multi-round interrogation, stress-test with
  scenarios, full doc-baking (glossary + ADRs + ledger), and the fresh-context convergence gate
  ([[kata-review]]) before declaring done. (This is today's `kata-grill`.)
- **advanced** (cost 5) — `description`: "Exhaustive, adversarial grill for max-rigor results." Depth:
  Standard **+** re-derive the decision tree after each resolution **to exhaustion**, generate exhaustive
  edge-case scenarios, probe **second-order effects + the security surface** deeply, and run a **second**
  fresh-context convergence pass.

- [ ] **Step 3: Delete the old single file + regenerate + verify**

`git rm skills/plan/kata-grill/SKILL.md`. Run `cd tools && uv run python validate_skills.py --write` then
`uv run python validate_skills.py` (exit 0) and `uv run pytest -q` (green). Confirm `[[kata-grill]]` still
resolves (the `kata-grill/` folder now has `RUBRIC.md` → `_valid_skill_targets` picks it up). Commit:
```bash
git add skills/plan/ README.md
git commit -m "feat: tier kata-grill (essential/standard/advanced) + extract RUBRIC (efficiency refactor)"
```

---

## Task 3: Split `kata-review`

Same shape. RUBRIC = the **5 attack surfaces**, the cite-evidence rule, the **SHIP/HOLD** output, and the
"attack the result before you trust it" framing (the invariant). Tags `kata/evaluate` + `kata/module/quality`
+ `kata/tier/<tier>` + `adversarial`,`red-team`,`no-write`. `allowed-tools: [Read, Grep, Glob, Bash]` (no
Write/Edit — evaluator). Depth contracts:
- **essential** (1) — smell-test only the **highest-risk surfaces**: decision judgment on the drift-magnets
  (classification/magnitude) + the most obvious missing-coverage gaps. SHIP/HOLD.
- **standard** (2) — the full 5-surface attack (today's `kata-review`).
- **advanced** (3) — Standard **+** a threat-model deep-dive, exhaustive second-order chase, and adversarial
  test-case generation for the gaps it finds.

Delete old `skills/evaluate/kata-review/SKILL.md`, regenerate README, verify green, commit
(`feat: tier kata-review (essential/standard/advanced) + RUBRIC`).

---

## Task 4: Split `kata-plan`

RUBRIC = vertical-slice-first decomposition, the **disjoint file-ownership** load-bearing property, the
wave/dependency **DAG** + `ownership/waves/depends_on` frontmatter shape, the per-task structure
(owns/read_first/action/verify/acceptance_criteria), and the quality bar (the invariant). Tags `kata/plan` +
`kata/spine` + `kata/tier/<tier>` + `freeze`,`dag`,`file-ownership`. `model: opus`,
`allowed-tools: [Read, Grep, Glob, Write, Edit]`. Depth contracts:
- **essential** (2) — coarse vertical slices, disjoint ownership, the DAG, runnable `verify` + acceptance
  criteria per task. Skip the threat model unless attacker-reachable surface is obvious.
- **standard** (3) — today's `kata-plan` (full DAG + ownership + threat model + phase verification + SUMMARY).
- **advanced** (4) — Standard **+** finer-grained slicing, an explicit STRIDE threat register, richer
  falsifiable acceptance criteria, and a per-task risk note.

Delete old, regenerate, verify, commit (`feat: tier kata-plan (essential/standard/advanced) + RUBRIC`).

---

## Task 5: Split `kata-diagnose` (light / full)

RUBRIC = the **feedback-loop-first** principle + the 6-phase method (reproduce → loop → ranked hypotheses →
instrument → fix+regression → cleanup/post-mortem) + the kata constraints (stay in lane, escalate, don't
re-plan). Keep `skills/execute/kata-diagnose/resources/FEEDBACK-LOOPS.md`. Tags `kata/execute` +
`kata/module/quality` + `kata/tier/<tier>` + `debugging`,`diagnosis`. `allowed-tools: [Read, Grep, Glob, Bash, Edit, Write]`.
Depth contracts:
- **light** (2) — for a shallow/obvious bug: build ONE feedback loop, reproduce, single most-likely fix,
  regression test, cleanup. Skip the ranked-hypotheses + instrumentation ceremony.
- **full** (3) — today's `kata-diagnose`: the full 6-phase loop with 3–5 ranked falsifiable hypotheses,
  one-variable instrumentation, and the post-mortem.

Delete old, regenerate, verify, commit (`feat: tier kata-diagnose (light/full) + RUBRIC`).

---

## Task 6: Depth-hint for `kata-design-doc` + `kata-tdd` (no split, D21)

**Files:** modify `skills/plan/kata-design-doc/SKILL.md`, `skills/execute/kata-tdd/SKILL.md`.

Add to each a short `## Depth by mode` section: the active mode (from `kata.config`, read by the orchestrator
and passed in the task) sets depth — **Essential** = the minimum viable artifact (design-doc: requirements +
LOCKED decisions + acceptance; tdd: cover the acceptance-criteria behaviors only); **Standard** = the full
skill as written; **Advanced** = + extra rigor (design-doc: fuller backward-compat + threat notes + test
seams; tdd: deeper refactor pass + edge-case behaviors). One file each — no fork. (These stay weight 2/3.)
Verify green, commit (`feat: mode depth-hint for kata-design-doc + kata-tdd (D21)`).

---

## Task 7: Finalize — ratings, taxonomy, cross-refs, README

**Files:** `.planning/SKILL-COST-RATINGS.md`, `docs/TAXONOMY.md`, `README.md`.

- [ ] Add the per-tier rows to `.planning/SKILL-COST-RATINGS.md` (grill 3/4/5, review 1/2/3, plan 2/3/4,
  diagnose 2/3) under a "Tier weights (A2)" note; the family base weight = its Standard/full tier.
- [ ] `docs/TAXONOMY.md`: confirm the tier-family section names the real tier set per family (it already
  documents the convention; add the concrete family→tiers list).
- [ ] Confirm every `[[kata-grill]]`/`[[kata-review]]`/`[[kata-plan]]`/`[[kata-diagnose]]` reference across all
  skills still resolves as a **family alias** (they should — leave them tier-agnostic; the orchestrator binds
  the tier in A3). Run `uv run python validate_skills.py` (exit 0, wikilinks resolve) + `--write` to sync the
  README, confirm the index now lists all tier skills. Commit (`docs: A2 tier weights + taxonomy + README index`).

---

## Task 8: Adversarial review (D15) + status + merge

- [ ] Dispatch a **fresh-context adversarial reviewer** (kata-review style, read-only) scoped at the A2 diff.
  Attack surfaces: does any tier file **duplicate** substance that belongs in the RUBRIC (DRY-by-pointer
  violation)? Is any tier's depth contract **ambiguous** or does Essential drop so much it can't produce a
  conformance-passing artifact (D18/D22 violation)? Do the tier `description`s give a host model a clear
  "when to pick this" trigger? Did any cross-skill `[[family]]` reference get accidentally pinned to a tier?
  Is the validator's `TIER_RE` correct (e.g., a skill legitimately named `kata-something-full`)? Capture
  findings + SHIP/HOLD to `.planning/specs/modes-A2-tier-families/REVIEW.md`.
- [ ] Resolve HOLDs; re-verify (validator + pytest green) + re-review the changed surface.
- [ ] Update `.planning/STATE.md` + `.planning/ROADMAP.md` (A2 done; next = A3 bootstrap+wiring) + README Status.
- [ ] On a clean SHIP: merge `modes/A2-tier-families` → `master` (`--no-ff`), verify validator green on master,
  delete the branch.

---

## Self-Review (completed during planning)

**1. Spec coverage:** all four families tiered (T2–T5) with concrete depth contracts; depth-hint for the two
medium skills (T6); validator tier rules (T1); cost-weights + taxonomy + README (T7); adversarial review +
merge (T8). `kata-evaluate`/`kata-orchestrate` correctly left single. Bootstrap/orchestrate-wiring correctly
deferred to A3.

**2. Placeholder scan:** no TBD; each family's RUBRIC content and each tier's depth contract are specified.
RUBRIC extraction references the existing SKILL.md as the source (no re-transcription needed) — that is a
restructure instruction, not a placeholder.

**3. Type/name consistency:** tier dirs are `kata-<verb>-<tier>`; `TIER_RE` matches them and the validator
requires the matching `kata/tier/<tier>` tag + sibling `RUBRIC.md`; cost-weights match the table in the file
structure section and Task 7; spine vs module tagging is consistent (grill/plan = spine; review/diagnose =
module/quality), matching MODES-DESIGN.

**4. Ambiguity:** the consistency guardrail (every tier passes the constant `kata-evaluate` floor; tiers vary
depth not validity) is stated up front and is the review's explicit check in T8.
