# Modes Spec A1 — Foundations Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or
> superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Lay the mechanical foundations of the operating-modes system — a skill-conformance validator
(default-FAIL gate), `cost-weight` metadata on every skill, a frontmatter-generated README index, the
`kata.config` + dependency-manifest protocol schemas, and `docs/TAXONOMY.md` — with **no behavior change** to
any existing skill.

**Architecture:** A single Python validator (`tools/validate_skills.py`, maintainer tooling, NOT shipped with
the agnostic suite — D27) parses every `skills/**/SKILL.md` frontmatter, asserts conformance to
`docs/STANDARDS.md`, and regenerates the README skill-index's mechanical columns from frontmatter (frontmatter
= machine truth; README = generated catalog — D28). Each foundational artifact (cost-weight, the two protocol
schemas, TAXONOMY) is added under a check so it is genuinely default-FAIL-gateable (RED before, GREEN after).

**Tech Stack:** Python 3.12 + `uv` (per project standards) + PyYAML; pytest for the validator's own tests.
Markdown for all skill/doc artifacts.

**Scope guards:** A1 is foundations only. It does NOT restructure any skill into tiers (that is A2), build
`kata-bootstrap` or wire `kata-orchestrate` (A3), or build `kata-preflight` (Spec D). It only *declares the
schemas* those later specs consume, and adds the validator rules they will lean on. YAGNI: the validator
checks only what STANDARDS + the modes work require — it is not a general markdown linter.

---

## File Structure

| File | Responsibility |
|---|---|
| `tools/pyproject.toml` (create) | uv project for the maintainer validator; pins PyYAML + pytest |
| `tools/validate_skills.py` (create) | the conformance validator + README regenerator (CLI: `--check` default, `--write`) |
| `tools/tests/test_validate_skills.py` (create) | pytest unit tests over controlled fixtures |
| `tools/tests/fixtures/` (create) | good/bad SKILL.md fixtures for the validator's tests |
| `skills/**/SKILL.md` (modify ×15) | add `cost-weight:` frontmatter key |
| `README.md` (modify) | add `Cost` column + `<!-- SKILL-INDEX -->` markers; table becomes generated |
| `protocol/config.md` (create) | `kata.config` schema (mode/modules/effort/tiers/preflight/bakeoff/skillVersions) |
| `protocol/dependencies.md` (create) | dependency-manifest schema (incl. `scope`, `classification`) |
| `docs/TAXONOMY.md` (create) | categories · `kata-<verb>` · tier-family convention · spine-vs-module · cost-weight |
| `.planning/STATE.md`, `.planning/ROADMAP.md` (modify) | mark A1 done |

**Cost-weight values** (from `.planning/SKILL-COST-RATINGS.md`, the authority): `kata-orchestrate` 5 ·
`kata-grill` 4 · `kata-diagnose` 3 · `kata-tdd` 3 · `kata-plan` 3 · `kata-design-doc` 2 · `kata-evaluate` 2 ·
`kata-review` 2 · `kata-board` 2 · `kata-handoff` 1 · `kata-worktree` 1 · `kata-selfhandoff` 1 ·
`kata-context` 1 · `kata-improve` 1 · `kata-write-skill` 1.

---

## Task 1: tools/ scaffold + validator core (frontmatter + name==dir + enums)

**Files:**
- Create: `tools/pyproject.toml`
- Create: `tools/validate_skills.py`
- Create: `tools/tests/test_validate_skills.py`
- Create: `tools/tests/fixtures/good/kata-good/SKILL.md`
- Create: `tools/tests/fixtures/bad-name/kata-wrongname/SKILL.md`

- [ ] **Step 1: Write the uv project file**

`tools/pyproject.toml`:
```toml
[project]
name = "kata-tools"
version = "0.1.0"
description = "KataHarness maintainer tooling (skill-conformance validator). Not shipped with the skill suite."
requires-python = ">=3.12"
dependencies = ["pyyaml>=6.0"]

[dependency-groups]
dev = ["pytest>=8.0"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

- [ ] **Step 2: Write the fixtures**

`tools/tests/fixtures/good/kata-good/SKILL.md`:
```markdown
---
name: kata-good
description: A conformant fixture skill.
license: Apache-2.0
version: 0.1.0
category: plan
status: experimental
agnostic: true
---
# kata-good
Body.
```

`tools/tests/fixtures/bad-name/kata-wrongname/SKILL.md` (frontmatter `name` deliberately ≠ dir):
```markdown
---
name: kata-mismatch
description: Name does not match its directory.
license: Apache-2.0
version: 0.1.0
category: plan
status: experimental
agnostic: true
---
# kata-wrongname
Body.
```

- [ ] **Step 3: Write the failing test**

`tools/tests/test_validate_skills.py`:
```python
from pathlib import Path

import validate_skills as v

FIXTURES = Path(__file__).parent / "fixtures"


def _skills_in(subdir: str) -> list[v.Skill]:
    return v.load_skills(FIXTURES / subdir)


def test_good_fixture_has_no_findings():
    findings = v.run_checks(_skills_in("good"))
    assert findings == [], f"expected clean, got {findings}"


def test_name_mismatch_is_an_error():
    findings = v.run_checks(_skills_in("bad-name"))
    assert any(f.level == "ERROR" and "name" in f.msg for f in findings)
```

- [ ] **Step 4: Run the test to verify it fails**

Run: `cd tools && uv run pytest -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'validate_skills'`.

- [ ] **Step 5: Implement the validator core**

`tools/validate_skills.py`:
```python
#!/usr/bin/env python3
"""KataHarness skill-conformance validator (maintainer tooling — NOT shipped with the suite, D27).

Parses every skills/**/SKILL.md, asserts conformance to docs/STANDARDS.md, and (with --write)
regenerates the README skill-index's mechanical columns from frontmatter. Default-FAIL: exits
non-zero when any ERROR finding is present.
"""
from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
README = REPO_ROOT / "README.md"

CATEGORY_ORDER = ["plan", "coordinate", "execute", "evaluate", "handoff", "meta", "cognition"]
CATEGORIES = set(CATEGORY_ORDER)
STATUSES = {"experimental", "beta", "stable", "deprecated"}
# Schema v2 (D31): license is required (public-intended); cost-weight added in Task 2.
REQUIRED_KEYS = ("name", "description", "license", "version", "category", "status", "agnostic")
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
NAME_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")   # agentskills.io spec
DESCRIPTION_MAX = 1024
NAME_MAX = 64


@dataclass
class Skill:
    name: str
    dir: Path
    frontmatter: dict
    body: str


@dataclass
class Finding:
    level: str  # "ERROR" | "WARN"
    where: str
    msg: str


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text
    return (yaml.safe_load(parts[1]) or {}), parts[2]


def load_skills(root: Path = SKILLS_DIR) -> list[Skill]:
    skills: list[Skill] = []
    for path in sorted(root.glob("*/*/SKILL.md")):
        fm, body = parse_frontmatter(path.read_text(encoding="utf-8"))
        skills.append(Skill(name=str(fm.get("name", "")), dir=path.parent, frontmatter=fm, body=body))
    return skills


CHECKS: list[Callable[[list[Skill]], list[Finding]]] = []


def check(fn: Callable[[list[Skill]], list[Finding]]):
    CHECKS.append(fn)
    return fn


@check
def check_frontmatter(skills: list[Skill]) -> list[Finding]:
    out: list[Finding] = []
    for s in skills:
        fm, where = s.frontmatter, s.dir.name
        for key in REQUIRED_KEYS:
            if key not in fm:
                out.append(Finding("ERROR", where, f"missing required frontmatter key: {key}"))
        name = fm.get("name", "")
        if name != s.dir.name:
            out.append(Finding("ERROR", where, f"name '{name}' != dir '{s.dir.name}'"))
        if not NAME_RE.match(str(name)) or len(str(name)) > NAME_MAX:
            out.append(Finding("ERROR", where, f"name '{name}' violates spec regex/length (≤{NAME_MAX})"))
        desc = str(fm.get("description", ""))
        if not desc.strip() or len(desc) > DESCRIPTION_MAX:
            out.append(Finding("ERROR", where, f"description must be non-empty and ≤{DESCRIPTION_MAX} chars"))
        if fm.get("category") not in CATEGORIES:
            out.append(Finding("ERROR", where, f"category '{fm.get('category')}' not in {CATEGORY_ORDER}"))
        if fm.get("status") not in STATUSES:
            out.append(Finding("ERROR", where, f"status '{fm.get('status')}' not in {sorted(STATUSES)}"))
        if not SEMVER.match(str(fm.get("version", ""))):
            out.append(Finding("ERROR", where, f"version '{fm.get('version')}' is not semver"))
        if "adapters" not in s.dir.parts and fm.get("agnostic") is not True:
            out.append(Finding("ERROR", where, "core skill must be agnostic: true"))
    return out


def run_checks(skills: list[Skill]) -> list[Finding]:
    findings: list[Finding] = []
    for fn in CHECKS:
        findings.extend(fn(skills))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KataHarness skill-conformance validator")
    parser.add_argument("--write", action="store_true", help="regenerate the README skill index from frontmatter")
    args = parser.parse_args(argv)

    skills = load_skills()
    if args.write:
        regenerate_readme(skills)  # defined in Task 3
        print(f"README index regenerated from {len(skills)} skills.")

    findings = run_checks(skills)
    for f in findings:
        print(f"{f.level}: {f.where}: {f.msg}", file=sys.stderr)
    errors = [f for f in findings if f.level == "ERROR"]
    print(f"\n{len(skills)} skills checked — {len(errors)} error(s), {len(findings) - len(errors)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

> Note: `main()` references `regenerate_readme` (added in Task 3). Until then, only invoke the validator via
> `run_checks` in tests (Task 1–2 tests never call `--write`). Do not run `python validate_skills.py --write`
> before Task 3.

- [ ] **Step 6: Run the test to verify it passes**

Run: `cd tools && uv run pytest -q`
Expected: PASS (2 passed).

- [ ] **Step 7: Run the validator against the real tree (sanity)**

Run: `cd tools && uv run python validate_skills.py`
Expected: exit 0 — `15 skills checked — 0 error(s)`. (Confirms all current skills satisfy the *existing* schema;
`cost-weight` is added as a requirement in Task 2.)

- [ ] **Step 8: Commit**

```bash
git add tools/
git commit -m "chore: add skill-conformance validator (maintainer tooling, D27)"
```

---

## Task 2: schema-v2 frontmatter on all 15 skills (cost-weight + license + namespaced tags)

> Schema v2 = D31 + STANDARDS §1. This single pass over all 15 skills adds `cost-weight` (1–5),
> `license: Apache-2.0`, and restructures `tags` into the `kata/...` automation namespace (§1.1). It also
> adds the validator's `cost-weight` range check and a `tags`-namespace lint.

**Files:**
- Modify: `tools/validate_skills.py` (add `cost-weight` to required keys + range check; add tags-namespace check)
- Modify: `tools/tests/test_validate_skills.py` (add range-check test)
- Modify: `tools/tests/fixtures/good/kata-good/SKILL.md` (add `cost-weight: 2`)
- Create: `tools/tests/fixtures/bad-cost/kata-badcost/SKILL.md`
- Modify: all 15 `skills/**/SKILL.md`

- [ ] **Step 1: Add the cost-weight check to the validator**

In `tools/validate_skills.py`, change the `REQUIRED_KEYS` tuple to include cost-weight:
```python
REQUIRED_KEYS = ("name", "description", "version", "category", "status", "agnostic", "cost-weight")
```
Then append these check functions (after `check_frontmatter`):
```python
@check
def check_cost_weight(skills: list[Skill]) -> list[Finding]:
    out: list[Finding] = []
    for s in skills:
        cw = s.frontmatter.get("cost-weight")
        if not isinstance(cw, int) or isinstance(cw, bool) or not (1 <= cw <= 5):
            out.append(Finding("ERROR", s.dir.name, f"cost-weight '{cw}' must be an int 1-5"))
    return out


@check
def check_tags_namespace(skills: list[Skill]) -> list[Finding]:
    """STANDARDS §1.1: every namespaced tag is under kata/...; kata/<category> + spine|module present."""
    out: list[Finding] = []
    for s in skills:
        tags = s.frontmatter.get("tags") or []
        if not isinstance(tags, list):
            out.append(Finding("ERROR", s.dir.name, "tags must be a list (Obsidian)"))
            continue
        kata_tags = [t for t in tags if str(t).startswith("kata/")]
        if f"kata/{s.frontmatter.get('category')}" not in kata_tags:
            out.append(Finding("ERROR", s.dir.name, f"tags must include kata/{s.frontmatter.get('category')}"))
        if not any(t == "kata/spine" or str(t).startswith("kata/module/") for t in kata_tags):
            out.append(Finding("ERROR", s.dir.name, "tags must include kata/spine or kata/module/<module>"))
    return out
```

- [ ] **Step 2: Update fixtures + add the bad-cost fixture + test**

Update `tools/tests/fixtures/good/kata-good/SKILL.md` to full schema v2 (add `cost-weight: 2` and a
namespaced `tags` block so it passes `check_tags_namespace`):
```markdown
---
name: kata-good
description: A conformant fixture skill.
license: Apache-2.0
version: 0.1.0
category: plan
status: experimental
agnostic: true
cost-weight: 2
tags:
  - kata/plan
  - kata/spine
---
# kata-good
Body.
```

Create `tools/tests/fixtures/bad-cost/kata-badcost/SKILL.md`:
```markdown
---
name: kata-badcost
description: cost-weight out of range.
license: Apache-2.0
version: 0.1.0
category: plan
status: experimental
agnostic: true
cost-weight: 9
---
# kata-badcost
Body.
```

Append to `tools/tests/test_validate_skills.py`:
```python
def test_cost_weight_out_of_range_is_an_error():
    findings = v.run_checks(_skills_in("bad-cost"))
    assert any(f.level == "ERROR" and "cost-weight" in f.msg for f in findings)
```

- [ ] **Step 3: Run the validator against the real tree to verify it FAILS**

Run: `cd tools && uv run python validate_skills.py`
Expected: exit 1 — 15 ERRORs, each `missing required frontmatter key: cost-weight`.

- [ ] **Step 4: Add schema-v2 fields to every skill**

For each skill add three things: `license: Apache-2.0` (after `description`), `cost-weight: <N>` (after
`agnostic`), and a restructured `tags:` block (STANDARDS §1.1). Per-skill values — cost-weight, the
spine/module tag, and a suggested domain tag (preserve any existing domain tags):

| Skill | cost | spine/module tag | domain tags (suggested; keep existing) |
|---|---|---|---|
| `skills/plan/kata-grill` | 4 | `kata/spine` | grilling, ddd, doc-baking |
| `skills/plan/kata-context` | 1 | `kata/spine` | ddd, ubiquitous-language |
| `skills/plan/kata-design-doc` | 2 | `kata/spine` | freeze, design-contract |
| `skills/plan/kata-plan` | 3 | `kata/spine` | freeze, dag, file-ownership |
| `skills/coordinate/kata-orchestrate` | 5 | `kata/spine` | orchestration, no-drift |
| `skills/coordinate/kata-board` | 2 | `kata/spine` | board, mailbox |
| `skills/coordinate/kata-worktree` | 1 | `kata/spine` | worktree, isolation |
| `skills/execute/kata-tdd` | 3 | `kata/spine` | tdd, red-green-refactor |
| `skills/execute/kata-diagnose` | 3 | `kata/module/quality` | debugging, diagnosis |
| `skills/evaluate/kata-evaluate` | 2 | `kata/spine` | conformance, default-fail |
| `skills/evaluate/kata-review` | 2 | `kata/module/quality` | adversarial, red-team |
| `skills/handoff/kata-handoff` | 1 | `kata/spine` | handoff |
| `skills/handoff/kata-selfhandoff` | 1 | `kata/spine` | self-handoff |
| `skills/meta/kata-improve` | 1 | `kata/module/meta` | improvement-kata |
| `skills/meta/kata-write-skill` | 1 | `kata/module/meta` | authoring |

Each `tags:` block = `[kata/<category>, <spine-or-module-tag>, <domain tags…>]`. Example
(`skills/coordinate/kata-orchestrate/SKILL.md`):
```yaml
description: >-
  ...
license: Apache-2.0
version: 0.1.0
category: coordinate
status: experimental
agnostic: true
cost-weight: 5
allowed-tools: [Read, Grep, Glob, Bash, Write, Agent]   # Agent = the Claude-adapter binding ...
...
tags:
  - kata/coordinate
  - kata/spine
  - orchestration
  - no-drift
```
(`kata/<category>` mirrors each skill's `category`; `kata-orchestrate` is spine, so `kata/spine`.) The
validator's `check_tags_namespace` enforces that `kata/<category>` + a spine/module tag are present.

- [ ] **Step 5: Run the unit tests + the real-tree validator to verify GREEN**

Run: `cd tools && uv run pytest -q`
Expected: PASS (3 passed).
Run: `cd tools && uv run python validate_skills.py`
Expected: exit 0 — `15 skills checked — 0 error(s)`.

- [ ] **Step 6: Add the repo LICENSE + update README**

The frontmatter now declares `license: Apache-2.0` on every skill (D31c), so the repo must carry it:
- Create root `LICENSE` with the **standard Apache-2.0 license text** (verbatim from
  https://www.apache.org/licenses/LICENSE-2.0.txt), copyright holder = the project owner, year 2026.
- In `README.md`, change the License section from `TBD before public release ...` to:
  `Apache-2.0 — see [LICENSE](./LICENSE).`

- [ ] **Step 7: Commit**

```bash
git add tools/ skills/ LICENSE README.md
git commit -m "feat: schema-v2 frontmatter (cost-weight + license + namespaced tags) + Apache-2.0 LICENSE"
```

---

## Task 3: README index — Cost column + frontmatter regeneration

**Files:**
- Modify: `README.md` (insert markers around the index table; add `Cost` column header)
- Modify: `tools/validate_skills.py` (add `regenerate_readme` + `check_readme_sync`)
- Modify: `tools/tests/test_validate_skills.py` (test regeneration round-trips)

- [ ] **Step 1: Add index markers to README.md**

Wrap the existing skill-index table (the `| Skill | Ver | ... |` block) with HTML-comment markers so
regeneration is surgical and the hand-authored prose around it is untouched. Immediately *above* the table
header line insert:
```html
<!-- SKILL-INDEX:START -->
```
and immediately *below* the last table row insert:
```html
<!-- SKILL-INDEX:END -->
```

- [ ] **Step 2: Implement regeneration + the sync check**

Append to `tools/validate_skills.py`:
```python
INDEX_START = "<!-- SKILL-INDEX:START -->"
INDEX_END = "<!-- SKILL-INDEX:END -->"
INDEX_HEADER = "| Skill | Ver | Cost | Category | Status | Source | Use |"
INDEX_SEP = "|---|---|---|---|---|---|---|"


def _first_line(value) -> str:
    if not value:
        return "—"
    return " ".join(str(value).split()).strip()


def _parse_existing_use(readme_text: str) -> dict[str, str]:
    """Preserve the hand-authored 'Use' column, keyed by skill name."""
    use: dict[str, str] = {}
    for line in readme_text.splitlines():
        m = re.match(r"\|\s*`(kata-[a-z0-9-]+)`\s*\|.*\|([^|]*)\|\s*$", line)
        if m:
            use[m.group(1)] = m.group(2).strip()
    return use


def _build_index(skills: list[Skill], use_by_name: dict[str, str]) -> str:
    rows = [INDEX_START, INDEX_HEADER, INDEX_SEP]
    for s in sorted(skills, key=lambda x: (CATEGORY_ORDER.index(x.frontmatter["category"]), x.name)):
        fm = s.frontmatter
        use = use_by_name.get(s.name, "—")
        rows.append(
            f"| `{s.name}` | {fm['version']} | {fm['cost-weight']} | {fm['category']} | "
            f"{fm['status']} | {_first_line(fm.get('source'))} | {use} |"
        )
    rows.append(INDEX_END)
    return "\n".join(rows)


def _splice_index(readme_text: str, new_block: str) -> str:
    start, end = readme_text.index(INDEX_START), readme_text.index(INDEX_END) + len(INDEX_END)
    return readme_text[:start] + new_block + readme_text[end:]


def regenerate_readme(skills: list[Skill], readme: Path = README) -> None:
    text = readme.read_text(encoding="utf-8")
    block = _build_index(skills, _parse_existing_use(text))
    readme.write_text(_splice_index(text, block), encoding="utf-8")


@check
def check_readme_sync(skills: list[Skill]) -> list[Finding]:
    text = README.read_text(encoding="utf-8")
    if INDEX_START not in text or INDEX_END not in text:
        return [Finding("ERROR", "README.md", "missing SKILL-INDEX markers")]
    current = text[text.index(INDEX_START): text.index(INDEX_END) + len(INDEX_END)]
    expected = _build_index(skills, _parse_existing_use(text))
    if current.strip() != expected.strip():
        return [Finding("ERROR", "README.md", "skill index out of sync with frontmatter — run `--write`")]
    return []
```

- [ ] **Step 3: Add a regeneration round-trip test**

Append to `tools/tests/test_validate_skills.py`:
```python
def test_index_is_idempotent_under_regeneration():
    skills = _skills_in("good")
    use = {"kata-good": "does a good thing"}
    block = v._build_index(skills, use)
    # the generated block parses back to the same Use text
    assert v._parse_existing_use(block).get("kata-good") == "does a good thing"
    assert "| Cost |" in block
```

- [ ] **Step 4: Run check to verify it FAILS (out of sync — no Cost column yet)**

Run: `cd tools && uv run python validate_skills.py`
Expected: exit 1 — `README.md: skill index out of sync with frontmatter — run --write`.

- [ ] **Step 5: Regenerate, then verify GREEN**

Run: `cd tools && uv run python validate_skills.py --write`
Then: `cd tools && uv run python validate_skills.py`
Expected: regeneration prints `README index regenerated from 15 skills.`; the second run exits 0.
Run: `cd tools && uv run pytest -q`
Expected: PASS (4 passed).

- [ ] **Step 6: Eyeball the README**

Open `README.md`; confirm the table now has a `Cost` column with the right weights and the hand-authored
`Use` prose is preserved. Fix any `Use` cell the regex didn't carry (it keys on the trailing column).

- [ ] **Step 7: Commit**

```bash
git add tools/ README.md
git commit -m "feat: README skill index is frontmatter-generated with a Cost column (D28)"
```

---

## Task 4: protocol schemas — kata.config + dependency manifest

**Files:**
- Create: `protocol/config.md`
- Create: `protocol/dependencies.md`
- Modify: `tools/validate_skills.py` (add `check_protocol_schemas`)
- Modify: `tools/tests/test_validate_skills.py`

- [ ] **Step 1: Write `protocol/config.md`**

```markdown
# protocol/config.md — the `kata.config` schema

> Per-branch provenance written by `kata-bootstrap` (Spec A3) and read by `kata-orchestrate` (D24d). It is
> machine-coordination state — JSON, not vault-managed (STANDARDS §5). It is the reproducibility backbone:
> what makes escalation (Spec C) and bake-off (Spec B) comparable.

## Location
`kata.config` (JSON) at the working-branch root. Absent ⇒ orchestrator assumes **Standard** (D25).

## Schema
| Field | Type | Meaning |
|---|---|---|
| `mode` | `"essential" \| "standard" \| "advanced"` | The unified tier+module axis (D24a). Default `"standard"` (D25). |
| `modules` | `string[]` | Active à-la-carte modules beyond the mode's bundle (D20): e.g. `["quality","design","bakeoff","improve"]`. |
| `effort` | `{ model: string, reasoning: "medium"\|"high"\|"xhigh"\|"max" }` | Orthogonal effort overlay (D19); set independently of `mode`. |
| `tiers` | `{ "<family>": "<tier>" }` | Resolved tier per tiered family (`kata-grill`/`kata-review`/`kata-plan` → essential\|standard\|advanced; `kata-diagnose` → light\|full). Lets bootstrap override a single family (D24c cross-tier picking) without changing `mode`. Missing family ⇒ the mode's default tier. |
| `ingested` | `[{ name, slot, source }]` | External/custom skills folded in (D24c): each declares where it slots in the loop. |
| `preflight` | `object` | Dependency pre-flight policy (D29) — see below. |
| `bakeoff` | `{ n: int, lineage: string[] }` | N-variant best-of-N (Spec B). `n: 1` ⇒ no bake-off. `lineage` records parent configs for escalation-with-reuse. |
| `skillVersions` | `{ "<skill>": "<semver>" }` | The exact skill versions this branch was built with (reproducibility). |

### `preflight` block (D29)
| Field | Type | Meaning |
|---|---|---|
| `allowed_registries` | `string[]` | Trusted install sources (e.g. `["npm","pypi","uv","cargo"]`). Anything outside requires an explicit approved override. |
| `pin_policy` | `"exact" \| "compatible"` | Version-pinning strictness; `"exact"` for determinism (L1). |
| `scan_required` | `bool` | Gate installs on a Snyk SCA scan (default `true`). |
| `approval_mode` | `"approve-at-freeze" \| "ask-each"` | When the human approves the dependency set. Default `"approve-at-freeze"` (the manifest is approved as part of the freeze; pre-flight then provisions unattended). |
| `sandbox_required` | `bool` | Require the loop to run in an isolated/disposable environment (container/devcontainer). |

## Notes
- Tier resolution: `kata-orchestrate` maps a bare family reference (`[[kata-grill]]`) → `tiers["kata-grill"]`
  → e.g. `kata-grill-standard` (D26). Absent config ⇒ Standard (D25).
- `kata.config` is never tiered or mode-specific in *format* — one schema, all modes (consistency, D18).
```

- [ ] **Step 2: Write `protocol/dependencies.md`**

```markdown
# protocol/dependencies.md — the Dependency Manifest schema

> Enumerated during GRILL, frozen into the DESIGN/PLAN, approved as part of the freeze, and provisioned by
> `kata-preflight` (Spec D) in the PRE-FLIGHT phase BEFORE the loop launches (D29). A long-running closed
> loop must never stall mid-flight on a missing dependency. Machine state (JSON/table), not vault-managed.

## Why it is a *frozen decision*, not a pre-flight decision
The manifest is part of the frozen contract: the human approves the dependency *set + sources* when approving
the design (`approval_mode: approve-at-freeze`). PRE-FLIGHT only **provisions** the approved set and verifies
it — it makes no new decisions. A dependency discovered later that is NOT in the approved manifest is a drift
signal ⇒ escalate ⇒ deliberate re-freeze (never a silent install). Workers **cannot install** at all
(least-privilege); discovery mid-loop escalates to the orchestrator.

## Per-entry fields
| Field | Type | Meaning |
|---|---|---|
| `name` | string | The dependency identifier (package/tool/MCP/repo/template name). |
| `type` | `"library" \| "tool" \| "mcp" \| "repo" \| "template" \| "runtime" \| "capability"` | What kind of thing it is. |
| `version` | string | Pinned version / constraint (honor `preflight.pin_policy`). |
| `purpose` | string | Why the build needs it (traceable to a DESIGN requirement). |
| `install` | string | The exact install command (recognized package manager — **never `curl \| bash` from an arbitrary domain**). |
| `verify` | string | A runnable command proving presence (e.g. `expo --version`, `python -c "import docx"`). PRE-FLIGHT is default-FAIL on this. |
| `source` | string | Registry/URL + a short trust note; reviewed by the human at freeze. |
| `scope` | `"global" \| "project-local"` | Install scope. Prefer `project-local` + pinned for determinism + easy cleanup (D-registry). |
| `classification` | `"build-time" \| "runtime"` | `runtime` ⇒ must be bundled into the artifact (a packaging task) → its global base copy becomes a cleanup candidate; `build-time` ⇒ removable after the run (D-registry). |

## Pre-flight gate (summary — full procedure in `kata-preflight`, Spec D)
enumerate → freeze+approve (set + sources) → check presence (`verify`) → Snyk SCA scan if `scan_required` →
install (recognized registry, pinned, hash-verified) → re-`verify` (default-FAIL) → append to the
machine-global installed-library registry (`~/.kata/installed-registry.json`, D-registry) → signal loop-ready.
Never auto-uninstall; the cleanup report (reference-counted across projects) recommends, the human executes.
```

- [ ] **Step 3: Add the schema-presence check**

Append to `tools/validate_skills.py`:
```python
PROTOCOL_DIR = REPO_ROOT / "protocol"
REQUIRED_PROTOCOL = {
    "config.md": ["mode", "modules", "effort", "preflight", "skillVersions"],
    "dependencies.md": ["classification", "scope", "verify", "install"],
}


@check
def check_protocol_schemas(_skills: list[Skill]) -> list[Finding]:
    out: list[Finding] = []
    for fname, required_terms in REQUIRED_PROTOCOL.items():
        path = PROTOCOL_DIR / fname
        if not path.exists():
            out.append(Finding("ERROR", f"protocol/{fname}", "required protocol schema missing"))
            continue
        text = path.read_text(encoding="utf-8")
        for term in required_terms:
            if term not in text:
                out.append(Finding("ERROR", f"protocol/{fname}", f"schema must document '{term}'"))
    return out
```

- [ ] **Step 4: Add a test guarding the schema files exist on the real tree**

Append to `tools/tests/test_validate_skills.py`:
```python
def test_protocol_schemas_present_on_real_tree():
    # check_protocol_schemas reads the real protocol/ dir, not fixtures
    findings = v.check_protocol_schemas([])
    assert findings == [], f"protocol schemas incomplete: {findings}"
```

- [ ] **Step 5: Run to verify (write the docs first if RED)**

Run: `cd tools && uv run pytest -q tests/test_validate_skills.py::test_protocol_schemas_present_on_real_tree`
Expected: PASS once both `protocol/config.md` and `protocol/dependencies.md` exist with the required terms.
(If you wrote the check before the docs, it goes RED first, then GREEN after Steps 1–2 — confirm that ordering.)
Run the full validator: `cd tools && uv run python validate_skills.py` → exit 0.

- [ ] **Step 6: Commit**

```bash
git add protocol/config.md protocol/dependencies.md tools/
git commit -m "feat: kata.config + dependency-manifest protocol schemas (D29, D-registry)"
```

---

## Task 5: docs/TAXONOMY.md

**Files:**
- Create: `docs/TAXONOMY.md`
- Modify: `tools/validate_skills.py` (add `check_taxonomy_present`)
- Modify: `tools/tests/test_validate_skills.py`
- Modify: `README.md` (the Layout block notes `TAXONOMY` is no longer "planned")

- [ ] **Step 1: Write `docs/TAXONOMY.md`**

```markdown
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
- **Spine** (always runs — the consistency machine): `kata-grill` · `kata-design-doc` · `kata-plan` ·
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
```

- [ ] **Step 2: Add the taxonomy-presence check**

Append to `tools/validate_skills.py`:
```python
TAXONOMY = REPO_ROOT / "docs" / "TAXONOMY.md"


@check
def check_taxonomy_present(_skills: list[Skill]) -> list[Finding]:
    if not TAXONOMY.exists():
        return [Finding("ERROR", "docs/TAXONOMY.md", "missing")]
    text = TAXONOMY.read_text(encoding="utf-8")
    out: list[Finding] = []
    for term in ("kata-<verb>-<tier>", "RUBRIC.md", "Family alias", "Spine vs module"):
        if term not in text:
            out.append(Finding("ERROR", "docs/TAXONOMY.md", f"must document '{term}'"))
    return out
```

- [ ] **Step 3: Add the real-tree test**

Append to `tools/tests/test_validate_skills.py`:
```python
def test_taxonomy_present_on_real_tree():
    assert v.check_taxonomy_present([]) == []
```

- [ ] **Step 4: Verify GREEN + update README Layout note**

Run: `cd tools && uv run pytest -q` → all pass.
Run: `cd tools && uv run python validate_skills.py` → exit 0.
In `README.md`, the Layout block: change `(ARCHITECTURE · TAXONOMY: planned)` to `(ARCHITECTURE: planned)`
(TAXONOMY now exists).

- [ ] **Step 5: Commit**

```bash
git add docs/TAXONOMY.md tools/ README.md
git commit -m "docs: TAXONOMY.md — categories, tier-family convention, spine-vs-module (D26)"
```

---

## Task 6: wikilink / rubric-pointer resolution check (family-alias aware)

**Files:**
- Modify: `tools/validate_skills.py` (add `check_wikilinks`)
- Modify: `tools/tests/test_validate_skills.py`

**Why now:** every `[[kata-...]]` reference should resolve to a real skill or family — this catches typos
today and pre-builds the resolver A2 needs when families appear (a family is a `kata-<verb>/` folder with a
`RUBRIC.md` and no `SKILL.md`). On the current tree all references resolve to skill dirs; the check must pass.

- [ ] **Step 1: Implement the resolver + check**

Append to `tools/validate_skills.py`:
```python
WIKILINK = re.compile(r"\[\[(kata-[a-z0-9-]+)\]\]")
# Bare family names that are valid tier-agnostic aliases even before A2 splits them into folders.
KNOWN_FAMILIES = {"kata-grill", "kata-review", "kata-plan", "kata-diagnose"}


def _valid_skill_targets() -> set[str]:
    names = {p.parent.name for p in SKILLS_DIR.glob("*/*/SKILL.md")}
    # a family folder = kata-<verb>/ containing RUBRIC.md but no SKILL.md (post-A2)
    for rubric in SKILLS_DIR.glob("*/*/RUBRIC.md"):
        names.add(rubric.parent.name)
    return names | KNOWN_FAMILIES


@check
def check_wikilinks(skills: list[Skill]) -> list[Finding]:
    targets = _valid_skill_targets()
    out: list[Finding] = []
    for s in skills:
        for ref in set(WIKILINK.findall(s.body)):
            if ref not in targets:
                out.append(Finding("ERROR", s.dir.name, f"unresolved skill wikilink [[{ref}]]"))
    return out
```
> `KNOWN_FAMILIES` lets bare family aliases resolve before A2 creates their folders; after A2 the
> `RUBRIC.md` glob covers them and the set is belt-and-suspenders. Non-skill `[[wikilinks]]` (e.g.
> `[[LESSONS-LEARNED]]`, `[[STANDARDS]]`) are intentionally ignored — the regex only matches `kata-*`.

- [ ] **Step 2: Add a test (good fixture references resolve; a bogus one fails)**

Create `tools/tests/fixtures/bad-link/kata-badlink/SKILL.md`:
```markdown
---
name: kata-badlink
description: references a non-existent skill.
version: 0.1.0
category: plan
status: experimental
agnostic: true
cost-weight: 1
---
# kata-badlink
See [[kata-does-not-exist]].
```
Append to `tools/tests/test_validate_skills.py`:
```python
def test_unresolved_wikilink_is_an_error():
    findings = v.check_wikilinks(_skills_in("bad-link"))
    assert any("unresolved skill wikilink" in f.msg for f in findings)


def test_real_tree_wikilinks_all_resolve():
    assert v.check_wikilinks(v.load_skills()) == []
```

- [ ] **Step 3: Run to verify**

Run: `cd tools && uv run pytest -q`
Expected: PASS. If `test_real_tree_wikilinks_all_resolve` fails, a real skill body has a typo'd `[[kata-…]]`
— fix the typo in the offending SKILL.md (do NOT weaken the check).
Run: `cd tools && uv run python validate_skills.py` → exit 0.

- [ ] **Step 4: Commit**

```bash
git add tools/
git commit -m "feat: validator resolves kata-* wikilinks (family-alias aware, pre-builds A2)"
```

---

## Task 7: adversarial review + status update (D15)

**Files:**
- Modify: `.planning/STATE.md`, `.planning/ROADMAP.md`
- Modify: `README.md` (Status line)
- Create: `.planning/specs/modes-A1-foundations/REVIEW.md` (the kata-review output)

- [ ] **Step 1: Run the adversarial review**

Dispatch `kata-review` as a **fresh-context, read-only** subagent (per D15 — everything built here gets an
adversarial pass before "done"). Scope it at the A1 diff: the validator (does `--check` actually fail closed?
can the README round-trip silently drop a hand-authored `Use` cell? are the regexes anchored?), the schema
docs (do `config.md` / `dependencies.md` fully specify what A3/Spec-D consume, or leave a branch open?), and
TAXONOMY (does the family-alias rule contradict anything in STANDARDS/MODES-DESIGN?). Capture findings +
SHIP/HOLD to `.planning/specs/modes-A1-foundations/REVIEW.md`.

- [ ] **Step 2: Resolve any HOLD findings**

For each HOLD: fix it, re-run `cd tools && uv run pytest -q` + `uv run python validate_skills.py` (both green),
commit the fix. Re-review only the changed surface. Do not proceed to A2 on a HOLD.

- [ ] **Step 3: Update status docs**

- `README.md` Status: note "modes Spec A1 (foundations) landed — validator + cost-weight + generated index +
  `kata.config`/dependency schemas + TAXONOMY."
- `.planning/STATE.md`: move A1 from "next action" to done; set next = **A2 (tier families)**.
- `.planning/ROADMAP.md`: check the Spec A line's A1 portion; A2 next.

- [ ] **Step 4: Commit**

```bash
git add .planning/ README.md
git commit -m "docs: A1 foundations reviewed (D15) + status; next = A2 tier families"
```

---

## Self-Review (completed during planning)

**1. Spec coverage** — every A1 scope item maps to a task: validator (T1) · cost-weight on all skills (T2) ·
README generated + Cost column (T3) · `kata.config` schema (T4) · dependency-manifest schema incl.
`scope`/`classification` (T4) · TAXONOMY incl. tier-family convention (T5) · wikilink/rubric resolution
pre-build (T6) · adversarial review per D15 (T7). The grill efficiency refactor and the actual tier *split*
are deferred to A2 (they restructure grill itself) — A1 only lays the convention + the resolver hook.

**2. Placeholder scan** — no TBD/TODO; every code step shows complete code; every doc step shows full content.

**3. Type consistency** — `Skill`/`Finding` dataclasses, `load_skills`/`run_checks`/`check`/`regenerate_readme`
names are used identically across T1–T7; `REQUIRED_KEYS` is defined in T1 and extended (not renamed) in T2;
`CHECKS` registry is append-only; `_build_index`/`_parse_existing_use` introduced in T3 and reused by the
sync check. The `--write` path in `main()` (T1) is satisfied by `regenerate_readme` (T3) — flagged inline in
T1 so it isn't invoked before it exists.

**4. Ambiguity** — README regeneration explicitly preserves the hand-authored `Use` column (T3 Step 2/6);
"required" frontmatter is the closed `REQUIRED_KEYS` tuple; agnostic-core enforcement excludes `adapters/`.
```
