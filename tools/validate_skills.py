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
