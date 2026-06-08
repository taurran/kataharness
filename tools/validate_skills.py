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
        cost = fm.get("cost-weight", "—")
        rows.append(
            f"| `{s.name}` | {fm['version']} | {cost} | {fm['category']} | "
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
