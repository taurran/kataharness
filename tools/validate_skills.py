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
# Schema v2 (D31): name-regex + description-length enforced here; `license` + `cost-weight` join
# REQUIRED_KEYS in Task 2 (when all skills gain them in one pass — keeps the real tree green each step).
REQUIRED_KEYS = ("name", "description", "license", "version", "category", "status", "agnostic", "cost-weight")
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
    fm = yaml.safe_load(parts[1])
    if not isinstance(fm, dict):
        fm = {}
    return fm, parts[2]


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


TIER_RE = re.compile(r"^(kata-[a-z0-9]+(?:-[a-z0-9]+)*?)-(essential|standard|advanced|light|full)$")
THREE_TIER = {"essential", "standard", "advanced"}
TWO_TIER = {"light", "full"}
FAMILY_TIERS = {
    "kata-grill": THREE_TIER, "kata-review": THREE_TIER,
    "kata-plan": THREE_TIER, "kata-diagnose": TWO_TIER,
}


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
        allowed = FAMILY_TIERS.get(family)
        if allowed is not None and tier not in allowed:
            out.append(Finding("ERROR", s.dir.name, f"tier '{tier}' not valid for family {family}"))
        tags = s.frontmatter.get("tags") or []
        if f"kata/tier/{tier}" not in tags:
            out.append(Finding("ERROR", s.dir.name, f"tier skill must tag kata/tier/{tier}"))
        rubric = s.dir.parent / family / "RUBRIC.md"
        if not rubric.exists():
            out.append(Finding("ERROR", s.dir.name, f"tier family missing shared rubric: {family}/RUBRIC.md"))
    return out


INDEX_START = "<!-- SKILL-INDEX:START -->"
INDEX_END = "<!-- SKILL-INDEX:END -->"
INDEX_HEADER = "| Skill | Ver | Cost | Category | Status | Source | Use |"
INDEX_SEP = "|---|---|---|---|---|---|---|"


def _first_line(value) -> str:
    if not value:
        return "—"
    return " ".join(str(value).split()).strip()


def _parse_existing_use(readme_text: str) -> dict[str, str]:
    """Preserve the hand-authored 'Use' column, keyed by skill name. Split-based (robust);
    a literal '|' inside a Use cell must be escaped per Markdown."""
    use: dict[str, str] = {}
    for line in readme_text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("| `kata-"):
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(cells) >= 7:
            m = re.match(r"`(kata-[a-z0-9-]+)`", cells[0])
            if m:
                use[m.group(1)] = cells[-1]
    return use


def _build_index(skills: list[Skill], use_by_name: dict[str, str]) -> str:
    rows = [INDEX_START, INDEX_HEADER, INDEX_SEP]
    for s in sorted(skills, key=lambda x: (CATEGORY_ORDER.index(x.frontmatter["category"]), x.name)):
        fm = s.frontmatter
        use = use_by_name.get(s.name, "—")
        cost = fm.get("cost-weight", "—")
        rows.append(
            f"| `{s.name}` | {fm['version']} | {cost} | {fm['category']} | "
            f"{fm['status']} | {_first_line(fm.get('source'))} | {use} |"
        )
    rows.append(INDEX_END)
    return "\n".join(rows)


def _splice_index(readme_text: str, new_block: str) -> str:
    if INDEX_START not in readme_text or INDEX_END not in readme_text:
        raise SystemExit("README is missing SKILL-INDEX markers; cannot regenerate.")
    start, end = readme_text.index(INDEX_START), readme_text.index(INDEX_END) + len(INDEX_END)
    return readme_text[:start] + new_block + readme_text[end:]


def regenerate_readme(skills: list[Skill], readme: Path = README) -> None:
    text = readme.read_text(encoding="utf-8")
    block = _build_index(skills, _parse_existing_use(text))
    readme.write_text(_splice_index(text, block), encoding="utf-8")


@check
def check_readme_sync(skills: list[Skill]) -> list[Finding]:
    # Only meaningful when running against the real skills tree; skip for fixture-based test calls.
    if not skills or not all(SKILLS_DIR in s.dir.parents for s in skills):
        return []
    text = README.read_text(encoding="utf-8")
    if INDEX_START not in text or INDEX_END not in text:
        return [Finding("ERROR", "README.md", "missing SKILL-INDEX markers")]
    current = text[text.index(INDEX_START): text.index(INDEX_END) + len(INDEX_END)]
    expected = _build_index(skills, _parse_existing_use(text))
    if current.strip() != expected.strip():
        return [Finding("ERROR", "README.md", "skill index out of sync with frontmatter — run `--write`")]
    return []


PROTOCOL_DIR = REPO_ROOT / "protocol"
REQUIRED_PROTOCOL = {
    "config.md": ["mode", "modules", "effort", "tiers", "preflight", "bakeoff", "skillVersions"],
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


@check
def check_rubric_wikilinks(_skills: list[Skill]) -> list[Finding]:
    targets = _valid_skill_targets()
    out: list[Finding] = []
    for rubric in sorted(SKILLS_DIR.glob("*/*/RUBRIC.md")):
        body = rubric.read_text(encoding="utf-8")
        for ref in set(WIKILINK.findall(body)):
            if ref not in targets:
                out.append(Finding("ERROR", f"{rubric.parent.name}/RUBRIC.md", f"unresolved skill wikilink [[{ref}]]"))
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
        # README-sync findings are EXPECTED pre-write, so they don't block the write;
        # any OTHER skill error could corrupt the index, so refuse until it's fixed.
        blocking = [f for f in run_checks(skills) if f.level == "ERROR" and f.where != "README.md"]
        if blocking:
            for f in blocking:
                print(f"{f.level}: {f.where}: {f.msg}", file=sys.stderr)
            print("\nRefusing --write: fix the skill errors above first.", file=sys.stderr)
            return 1
        regenerate_readme(skills)
        print(f"README index regenerated from {len(skills)} skills.")

    findings = run_checks(skills)
    for f in findings:
        print(f"{f.level}: {f.where}: {f.msg}", file=sys.stderr)
    errors = [f for f in findings if f.level == "ERROR"]
    print(f"\n{len(skills)} skills checked — {len(errors)} error(s), {len(findings) - len(errors)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
