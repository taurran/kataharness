#!/usr/bin/env python3
"""KataHarness skill-conformance validator (maintainer tooling — NOT shipped with the suite, D27).

Parses every skills/**/SKILL.md, asserts conformance to docs/STANDARDS.md, and (with --write)
regenerates the README skill-index's mechanical columns from frontmatter. Default-FAIL: exits
non-zero when any ERROR finding is present.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml

import footprint

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
MODULES_DIR = REPO_ROOT / "modules"
README = REPO_ROOT / "README.md"

CATEGORY_ORDER = ["plan", "coordinate", "execute", "evaluate", "handoff", "meta", "cognition"]
CATEGORIES = set(CATEGORY_ORDER)
STATUSES = {"experimental", "beta", "stable", "deprecated"}
# Schema v2 (D31): name-regex + description-length enforced here; `license` + `cost-weight` join
# REQUIRED_KEYS in Task 2 (when all skills gain them in one pass — keeps the real tree green each step).
REQUIRED_KEYS = ("name", "description", "license", "version", "category", "status", "agnostic",
                 "cost-weight", "allowed-tools")
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


def load_skills(root: Path = None, roots: list[Path] | None = None) -> list[Skill]:
    """Discover SKILL.md files across one or more root directories.

    Accepts either:
    - ``root`` (single Path, legacy) — existing tests pass a fixture root this way.
    - ``roots`` (list of Paths) — used when discovering both skills/ and modules/.
    - Neither — defaults to [SKILLS_DIR, MODULES_DIR] (the real repo roots).

    Results are sorted stably (by path) so the order is deterministic.
    """
    if roots is not None:
        search_roots = roots
    elif root is not None:
        search_roots = [root]
    else:
        search_roots = [SKILLS_DIR, MODULES_DIR]

    paths: list[Path] = []
    for r in search_roots:
        if r.exists():
            paths.extend(r.glob("*/*/SKILL.md"))
    paths.sort()

    skills: list[Skill] = []
    for path in paths:
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


# ---------------------------------------------------------------------------
# bump-on-modify (BOM-1 … BOM-12)
#
# docs/STANDARDS.md §3 says every modification to an existing skill MUST increment
# its version before merge and that the `version` field is "validator-enforced".
# Until this check landed, the enforcement was presence + FORMAT only (the SEMVER
# match in check_frontmatter): a skill could be rewritten end-to-end while
# `version: 0.1.0` stayed perfectly valid. That is the KH-T02 shape — a documented
# invariant with nothing behind it — so the code is made true rather than the
# sentence deleted (BOM-6).
# ---------------------------------------------------------------------------

BUMP_CHECK = "bump-on-modify"
# BOM-7: `origin/master` FIRST — a contributor's local `master` can be months
# stale, while `origin/master` is what the work actually merges into.
BASE_REF_CANDIDATES = ("origin/master", "master")


def _semver_tuple(version: str) -> tuple[int, int, int]:
    """Parse a SEMVER-matched version string into a comparable integer tuple.

    String comparison is wrong here, and quietly so: `"0.10.0" > "0.9.0"` is
    **False** in Python, so a correct `0.9.0 → 0.10.0` MINOR bump would be
    rejected as a decrease (BOM-8). Skills already sit at `0.2.x`/`0.4.x`, so
    double-digit components are reachable, not hypothetical.

    Args:
        version: A version string already matched by ``SEMVER``.

    Returns:
        ``(major, minor, patch)`` as ints.

    Raises:
        ValueError: *version* is not three dot-separated integers.
    """
    parts = version.split(".")
    if len(parts) != 3:
        raise ValueError(f"not a three-part version: {version!r}")
    major, minor, patch = (int(p) for p in parts)
    return (major, minor, patch)


def resolve_base_ref() -> str | None:
    """Resolve the ref this branch will merge into, or ``None`` if there is none.

    Order (BOM-7): ``origin/master`` → ``master`` → the remote default branch via
    ``refs/remotes/origin/HEAD``.

    ``None`` means no baseline is resolvable — the two real conditions being a
    source zip/tarball with no ``.git`` at all, and a shallow CI checkout with no
    base ref. The caller turns that into the announced WARN skip (BOM-5/BOM-10),
    never a silent pass. ``OSError`` (git not installed) lands in the same bucket
    for the same reason: there is no baseline to compare against.

    Returns:
        A ref name usable with ``git show <ref>:<path>``, or ``None``.
    """
    try:
        for ref in BASE_REF_CANDIDATES:
            if footprint.ref_exists(ref):
                return ref
        default = footprint.origin_head_ref()
        if default and footprint.ref_exists(default):
            return default
    except OSError:
        return None  # git absent from PATH ⇒ no baseline (BOM-5), not a crash
    return None


@check
def check_bump_on_modify(skills: list[Skill]) -> list[Finding]:
    """STANDARDS §3: a modified ``SKILL.md`` must ship a GREATER version (BOM-1…12).

    Scope, stated exactly so it is not over-read:

    * **SKILL.md only** (BOM-1). A shared ``RUBRIC.md``, a ``ROADMAP.md``, a
      ledger, or a language note never obliges anyone to bump — the ``version``
      field lives in ``SKILL.md`` and describes ``SKILL.md``. The known residual:
      a RUBRIC edit really does change how its consumers behave and still needs
      no bump.
    * **COMMITTED work only** (BOM-7), because the comparison is a git diff —
      identical to ``footprint.py``'s sibling lane check. An uncommitted
      un-bumped edit passes; this is a pre-merge gate, not a save-time linter.
      The *version* is read from the working tree (the value about to be
      committed), so bumping fixes the finding immediately; in CI, where the
      tree equals HEAD, the two coincide.
    * **Against the fork point** from the base branch (BOM-2) — the three-dot
      diff in ``footprint.changed_in_task``, so commits the base branch made
      after this branch forked are not attributed to it. Comparing against the
      previous commit instead would demand a bump on *every* commit, which
      contradicts the repo's own commit-as-you-go convention.
    * **Any textual difference counts** (BOM-12) — no "meaningful change"
      heuristic. A whitespace-only edit does require a bump. Newline handling is
      git's (``.gitattributes`` pins LF).
    * **Any increase satisfies it** (BOM-3). Whether an edit deserved MAJOR vs
      MINOR vs PATCH is a semantic judgment; a checker that guessed would emit
      false HOLDs and train people to work around it. Review enforces that.

    Returns:
        One ``WARN`` when no baseline resolves; otherwise an ``ERROR`` per skill
        whose ``SKILL.md`` changed without a strictly greater version.
    """
    base_ref = resolve_base_ref()
    if base_ref is None:
        # BOM-5/BOM-10: announced, never silent, never fatal. WARN prints to
        # stderr with every other finding and does not affect the exit code
        # (`1 if errors else 0`), so a tarball/shallow checkout stays usable
        # while the operator can still SEE that the guard did not run.
        return [Finding(
            "WARN", BUMP_CHECK,
            "no git baseline (no .git, no origin/master|master|origin/HEAD, or a shallow "
            "checkout with no base ref) — check skipped: a modified SKILL.md will NOT be "
            "caught in this run",
        )]

    try:
        changed = set(footprint.changed_in_task(base_ref))
        renamed_from = footprint.renames_in_task(base_ref)
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        # Fail-closed (D136). `changed_in_task` RAISES on >1 merge-base
        # (criss-cross topology) because the three-dot base would be ambiguous;
        # ambiguous evidence must not drive a verdict, and must not crash the
        # validator either — it becomes a visible ERROR.
        return [Finding(
            "ERROR", BUMP_CHECK,
            f"could not read the baseline diff against {base_ref!r}: "
            f"{exc.__class__.__name__}: {exc}",
        )]

    if not changed:
        # Undiverged HEAD (merge-base == HEAD, e.g. sitting on master): the
        # three-dot diff is empty, so there is nothing under review — no-op.
        return []

    out: list[Finding] = []
    for s in skills:
        try:
            rel = Path(s.dir).resolve().relative_to(REPO_ROOT)
        except ValueError:
            # Skill root outside the repo — the fixture trees the tests
            # monkeypatch to `tmp_path`. `relative_to` raises there; there is no
            # baseline for a path git has never heard of, so skip it rather than
            # crash every fixture test (BOM-11).
            continue
        path = (rel / "SKILL.md").as_posix()
        if path not in changed:
            continue

        where = s.dir.name
        renamed = renamed_from.get(path)
        # BOM-9: `changed_in_task` pins `--no-renames`, so a `git mv` arrives as
        # delete+add and a path-keyed lookup finds nothing at the new path —
        # which BOM-4 would call NEW, and new is exempt. Since STANDARDS §2
        # encodes the category in the path and §3's lifecycle mandates *moving*
        # deprecated skills, a rename is a normal operation, so that bypass is a
        # normal-operations-shaped hole. Two predecessor sources close it:
        #   1. git's own rename detection (`-M`, explicit — never inherited from
        #      the operator's `diff.renames`);
        #   2. a same-skill-name fallback over the changed set, because `-M`'s
        #      similarity threshold is exactly what a move-AND-rewrite defeats.
        #      The skill's directory name is the identity the version describes
        #      (check_frontmatter pins `name == dir`), so `.../<name>/SKILL.md`
        #      at a different category IS the predecessor, with no similarity
        #      judgment involved. Sorted for determinism (Doctrine law 2).
        suffix = f"/{s.dir.name}/SKILL.md"
        candidates = [path]
        if renamed:
            candidates.append(renamed)
        candidates.extend(sorted(c for c in changed if c != path and c.endswith(suffix)))

        baseline = None
        for candidate in candidates:
            baseline = footprint.blob_at_ref(base_ref, candidate)
            if baseline is not None:
                break
        if baseline is None:
            if renamed:
                out.append(Finding(
                    "ERROR", where,
                    f"SKILL.md was renamed from '{renamed}' since {base_ref}, but that path "
                    "could not be read at the baseline — the bump cannot be verified (D136)",
                ))
            # BOM-4: no predecessor anywhere ⇒ genuinely new ⇒ nothing to bump from.
            continue

        try:
            base_fm, _ = parse_frontmatter(baseline.decode("utf-8"))
        except (UnicodeDecodeError, yaml.YAMLError) as exc:
            out.append(Finding(
                "ERROR", where,
                f"SKILL.md changed since {base_ref} but its baseline frontmatter could not be "
                f"parsed ({exc.__class__.__name__}) — the bump cannot be verified (D136)",
            ))
            continue

        base_version = str(base_fm.get("version", ""))
        if not SEMVER.match(base_version):
            shown = base_version or "(absent)"
            out.append(Finding(
                "ERROR", where,
                f"SKILL.md changed since {base_ref} but the baseline version '{shown}' is not "
                "semver — the bump cannot be verified, and an unreadable decision input is "
                "never a permissive pass (D136)",
            ))
            continue

        new_version = str(s.frontmatter.get("version", ""))
        if not SEMVER.match(new_version):
            # check_frontmatter already emits an ERROR for this skill, so the run
            # is red either way; a second finding would only duplicate it.
            continue

        if _semver_tuple(new_version) <= _semver_tuple(base_version):
            out.append(Finding(
                "ERROR", where,
                f"SKILL.md changed since {base_ref} but version did not increase "
                f"({base_version} → {new_version}) — bump it before merge (docs/STANDARDS.md §3)",
            ))
    return out


# The two no-write graders (L4 / STANDARDS §1): fresh-context evaluators that must never author artifacts.
NO_WRITE_EVALUATORS: frozenset[str] = frozenset({"kata-evaluate", "kata-research", "kata-slop-check"})


@check
def check_evaluator_no_write(skills: list[Skill]) -> list[Finding]:
    """STANDARDS §1: evaluator skills MUST omit Write/Edit (no-write contract, L4).
    Asserted structurally for the locked no-write grader set so the rule cannot regress silently."""
    out: list[Finding] = []
    for s in skills:
        if s.name not in NO_WRITE_EVALUATORS:
            continue
        at = s.frontmatter.get("allowed-tools") or []
        forbidden = {t for t in at if t in ("Write", "Edit")}
        if forbidden:
            out.append(Finding(
                "ERROR", s.dir.name,
                f"evaluator skill must omit Write/Edit (no-write contract); found: {forbidden}",
            ))
    return out


@check
def check_allowed_tools(skills: list[Skill]) -> list[Finding]:
    """STANDARDS §1: allowed-tools is load-bearing (least-privilege security + cost surface). It must be
    present (REQUIRED_KEYS handles absence) and, when present, a NON-EMPTY list of strings. (dogfood-selfup-1)"""
    out: list[Finding] = []
    for s in skills:
        at = s.frontmatter.get("allowed-tools")
        if at is None:
            continue  # absence is reported by check_frontmatter via REQUIRED_KEYS
        if not isinstance(at, list) or not at or not all(isinstance(t, str) for t in at):
            out.append(Finding("ERROR", s.dir.name, "allowed-tools must be a non-empty list of strings"))
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


def _is_real_repo_skill(s: Skill) -> bool:
    """A skill counts as a real repo skill when it lives under SKILLS_DIR or MODULES_DIR (D91).
    Previously the guard was SKILLS_DIR-only, which silently disabled README-sync enforcement
    when any module skill was present — a real bug fixed here."""
    return SKILLS_DIR in s.dir.parents or MODULES_DIR in s.dir.parents


@check
def check_readme_sync(skills: list[Skill]) -> list[Finding]:
    # Only meaningful when running against the real skills tree; skip for fixture-based test calls.
    if not skills or not all(_is_real_repo_skill(s) for s in skills):
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
    "config.md": ["mode", "modules", "effort", "tiers", "preflight", "bakeoff", "skillVersions",
                  "runShape", "target", "graph", "delivery"],
    "dependencies.md": ["classification", "scope", "verify", "install"],
    "graph.md": ["id", "kind", "path", "name", "symKind", "span", "rank", "weight", "edge", "meta"],
    "escalation.md": ["taskId", "kind", "decisionNeeded", "optionsConsidered", "agentRecommendation", "status"],
    "engram.md": ["CONSULT", "LEARN", "wiki-synthesis", "produced-by", "redaction", "learnFeed"],
    "orientation.md": ["stable", "context", "volatile", "adjacency", "task-type", "callout"],
    # sprint-cadence (D81/D79): tier-3 sprint state + the boundary-handoff artifact.
    "state.md": ["sprint", "gateStatus", "dirty", "gated", "rebuild"],
    "handoff.md": ["Boundary handoff", "sprint index"],
    # initiation (D88/DESIGN §2): the PINNED INTENT.md artifact schema.
    "intent.md": ["kind", "goal", "fixes", "features", "changeSummary", "target", "grillDepth", "readiness"],
    # recurrence-hardening (LD3/LD5b): the three load-bearing guard terms must remain in the contract body.
    # The full LD3 phrase is guarded verbatim (the contract is reflowed so it stays on one line, m5).
    "reuse-claims.md": ["claim to verify, not an assumption", "NEW capability", "documentation-only seam"],
    # second-brain-learning (R2/B2): the Recall read-CONTRACT load-bearing clauses.
    "recall.md": ["schema_version", "recall/v1", "NO embeddings", "never written", "read-only invariant"],
    # prime-directives (2026-07-12 health review): the standing behavioral contract injected into
    # every run — never-tiered; erasing or hollowing it must fail the validator.
    "prime-directives.md": ["PD-1", "PD-2", "DRIFT", "kata-defer", "escalation", "truthful",
                            "stable tier"],
    # steering (2026-07-12 health review F-3): the operator->agent mid-run channel + AGENT_STOP
    # graceful kill-switch — now a real engine (tools/kata_steer.py), no longer a prose facade.
    "steering.md": ["AGENT_STOP", "Active directives", "kata_steer", "boundary", "graceful"],
    # thin-orchestrator doctrine (KH-T12): the conductor's own contract — binding home for a
    # principle that previously lived only in .planning/ (a described rule, not an enforced one).
    "orchestration.md": ["well-behaved orchestrator does not do the work itself", "plan-guardian",
                          "honest residual", "NOT mechanically provable", "clause-pinned"],
    # dispatch-authoring (KH-B42): the conductor-gates-what-it-did-not-author rubric — the six
    # named rows every returned DESIGN.md/PLAN.md is checked against before entering the main tree.
    "authored-artifact-gate.md": ["SCOPE", "CLAIM vs ARTIFACT", "CITATIONS RESOLVE",
                                   "NO UNCITED REUSE CLAIM", "DEVIATIONS CONFIRMED",
                                   "NO FROZEN INVARIANT RETIRED"],
    # ungated-protocol-files (UPF-2/UPF-10, 2026-08-03): the eight contracts that were on disk
    # but in no guard structure at all. Each term below is a word whose deletion would remove a
    # capability the file defines — the UPF-10 bar.
    # cursor.md (heritage key: board.md) — the cursor register: the TYPE vocabulary IS the
    # protocol, and the concurrency-evidence artifact is derived from it.
    "cursor.md": ["CLAIM", "DONE", "BLOCK", "ESCALATE", "NOTE", "DECISION", "PROGRESS",
                  "Append-only", "concurrency.json", "maxInFlight"],
    # exec-safety.md — the RCE guard: the execution rule, the trust-domain table, the auditable
    # sink registry, and the in-process AST allowlist.
    "exec-safety.md": ["structured-argv-only", "shell=False", "Trust domains", "Sink registry",
                       "AST allowlist", "claim to verify, not an assumption",
                       "NEW execution capability"],
    # observability.md — log-reader orientation: the artifact schemas a review/eval dispatch must
    # read correctly, plus the gotchas that produce a silently-wrong read.
    "observability.md": ["Kata-Checkpoint", "failureKinds", "parentTokens", "class_median",
                         "scan_checkpoints", "refs/kata/trail", "gotchas"],
    # iac-safety.md — the normative IaC contract: the tier boundary, the fail-closed scanner gate,
    # the deletion-protection vocabulary, and the stateful/escalate discrimination.
    "iac-safety.md": ["Tier 1", "snyk_iac_scan", "prevent_destroy", "DeletionPolicy",
                      "auto-approve", "stateful", "escalate", "fail-closed"],
    # narration.md — the conversation-channel contract: the cadence rule, the never-tiered
    # breakthrough alert, the honesty guard, and the deterministic loop-init banner.
    "narration.md": ["Milestone-cadence", "Breakthrough", "Honesty guard", "banner",
                     "PROGRESS", "loop-back", "never tiered"],
    # validation-misses.md — the miss-manifest schema (all of these are entry fields or engine
    # entry points) plus the observe-only posture the whole T1 layer rests on.
    "validation-misses.md": ["failure_class", "responsible_skill", "severity", "guard_ref",
                             "run_id", "observe-only", "append_miss", "recurrence"],
    # advice.md — the advisor consult payload: a machine schema of the same kind as escalation.md
    # and graph.md, guarded field-for-field the same way.
    "advice.md": ["taskId", "scopedContext", "diagnosis", "citations", "nonAuthoritative",
                  "rungUsed", "disposition"],
    # persona.md — the agnostic SOUL contract: the identity, the static default register, and the
    # gated (NOT live) adaptation seam whose overclaim kata-slop-check catches.
    "persona.md": ["calm kata-craftsperson", "改善型", "nameless", "moderate non-expert",
                   "static default", "Register adaptation", "overclaim"],
    # deferral.md (trust-model TM-D1) — the sanctioned-deferral ledger contract: the entry ids,
    # the closed STATUS enum, the approval-record field names a gate is allowed to read, the
    # closure field, and the two required-field labels that are unique to this schema. Deleting
    # any one of these removes a capability the ledger grammar depends on.
    "deferral.md": ["DEF-<n>", "ASM-<n>", "OPEN", "ACCEPTED", "CLOSED",
                    "accepted_by", "accepted_at", "closing_commit",
                    "Provenance", "Owed-to", "BLOCKER", "append-only"],
}

#: Protocol files that are deliberately NOT guarded contracts — reference material, each with a
#: WRITTEN reason. Ships EMPTY on purpose (UPF-2): it exists as the declared path for a genuine
#: future non-contract file (a `README.md` dropped into `protocol/`), never as a place to park
#: work. Its exact contents are pinned by a test (UPF-8), so adding an entry can never be a quiet
#: one-line edit — it fails by name and must be justified in the same change.
#:
#: Honest residual, stated rather than designed away: this list IS an escape hatch, and
#: `validate_skills.py` is not itself fingerprinted. A future agent facing a failing clause check
#: could add the file here instead of fixing the contract. The test raises the cost and the
#: visibility of that move; it does not make it impossible.
PROTOCOL_EXEMPT: dict[str, str] = {}


@check
def check_protocol_folder_is_fully_registered(_skills: list[Skill]) -> list[Finding]:
    """Every `protocol/*.md` must be a registered contract or a declared exemption — never neither.

    THE ROOT DEFECT THIS CLOSES: every other use of `PROTOCOL_DIR` in the tree is
    `PROTOCOL_DIR / fname` — a lookup of a name the code was already handed. Nothing ever LISTED
    the directory, so a new protocol file was invisible to every guard, silently and permanently,
    from the moment it was created. Eight files escaped that way; `orchestration.md` and
    `authored-artifact-gate.md` escaped for a while and were caught only because someone
    remembered to register them by hand. A rule that depends on remembering is the disease.

    `sorted()` is mandatory, not cosmetic: DETERMINISM-DOCTRINE law 2 — no unsorted
    `glob`/`iterdir`/`rglob` result may drive artifact content. Non-recursive, `*.md` only.
    """
    out: list[Finding] = []
    found = sorted(p.name for p in PROTOCOL_DIR.glob("*.md"))
    if not found:
        # D136/D33, the same refusal main() makes for "0 skills discovered": an empty scan means
        # the tree is missing or mis-rooted. Certifying over it would be a silent-permissive
        # default — a vacuous pass is the one outcome this check must never produce.
        return [Finding("ERROR", "protocol/",
                        "0 protocol *.md files discovered — refusing to certify an empty protocol "
                        "directory (check the PROTOCOL_DIR root).")]
    for name in found:
        registered = name in REQUIRED_PROTOCOL
        exempt = name in PROTOCOL_EXEMPT
        if registered and exempt:
            out.append(Finding(
                "ERROR", f"protocol/{name}",
                "listed in BOTH REQUIRED_PROTOCOL and PROTOCOL_EXEMPT — a protocol file is a "
                "guarded contract or a declared exemption, never both",
            ))
        elif not registered and not exempt:
            out.append(Finding(
                "ERROR", f"protocol/{name}",
                "unregistered protocol file — add it to REQUIRED_PROTOCOL (a guarded contract: "
                "terms + pinned clauses, and a fingerprint unless it is a registry) or to "
                "PROTOCOL_EXEMPT with a written reason. A protocol file guarded by nothing is "
                "the defect this check exists to prevent.",
            ))
    return out


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


# --------------------------------------------------------------------------- #
# Prime-directive integrity (KH-T02)
#
# REQUIRED_PROTOCOL above is TERM presence: it catches deletion, never rewording.
# A reviewer demonstrated the gap by rewriting both Prime Directives to say the
# OPPOSITE ("stub it and move on, present-but-dead counts as built") while keeping
# all seven guarded tokens — and the validator passed green. Operator ruling: "It is
# prime directive. It shouldn't have a workaround."
#
# Two layers close it, and they catch different attacks:
#   1. PINNED CLAUSES — whole load-bearing sentences, matched after whitespace and
#      markdown-emphasis normalisation so ordinary reflow is fine. An inversion must
#      DELETE a clause, which fails. This is a semantic floor, not a token count.
#   2. FINGERPRINT — a digest of the normalised file, so any OTHER edit fails until
#      deliberately re-approved. Without it, a weakening change to the surrounding
#      context could ride in unnoticed alongside intact pinned clauses.
#
# SCOPE (operator-directed 2026-07-29, "fix it properly in the other files"):
#   * CLAUSES apply to ALL 24 REQUIRED_PROTOCOL files. This layer is free on ordinary
#     edits — it is reflow-tolerant and only fires when a load-bearing sentence is
#     deleted or reworded — so there is no reason to withhold it anywhere.
#   * FINGERPRINTS apply to 22 of the 24, with TWO declared exemptions, both earned on the
#     same structural criterion — a REGISTRY that grows with the codebase, where the risk
#     is a MISSING entry (which REQUIRED_PROTOCOL already covers) and fingerprinting would
#     buy nothing while imposing a re-approval per routine addition, which is precisely how
#     blind re-approval gets trained. Both keep their invariants clause-pinned.
#       - `config.md`: a key registry that changed 32 times (vs 1-12 for every other
#         protocol file), because essentially every feature adds a config key.
#       - `exec-safety.md` (UPF-9): its "Sink registry (verify-before-add — keep in sync
#         with the code)" requires every new execution site to be added, so fingerprinting
#         it would make every new subprocess call site in tools/ cost a manual re-approval.
#         Its rules — structured-argv-only, never-eval/exec — stay clause-pinned, so the
#         safety guarantee is NOT weakened; only the whole-file digest is skipped.
#
# COVERAGE OF THE FOLDER ITSELF (ungated-protocol-files, UPF-1/UPF-11, 2026-08-03): until
# this change nothing ever ENUMERATED protocol/ — every PROTOCOL_DIR use was a lookup of a
# name the code was already handed — so a new protocol file was ungated by every layer from
# the moment it was created, silently and permanently. Eight files (board.md, exec-safety.md,
# observability.md, iac-safety.md, narration.md, validation-misses.md, advice.md, persona.md)
# had escaped that way and are now registered. `check_protocol_folder_is_fully_registered`
# closes the mechanism, not just the instance: every protocol/*.md must appear in exactly one
# of REQUIRED_PROTOCOL or PROTOCOL_EXEMPT, and a file in neither fails the validator BY NAME.
# --------------------------------------------------------------------------- #

def _normalize_protocol_text(text: str) -> str:
    """Normalise a protocol doc for phrase-matching and fingerprinting.

    Line endings, markdown emphasis, and whitespace runs carry no meaning here, so
    they are flattened: a reflowed paragraph or a bolded word must not trip the gate,
    while a deleted or reworded clause must. Pure and deterministic — no clock, no
    environment, no filesystem beyond the caller's read (Determinism Doctrine law 7).
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[*`_]", "", text)          # emphasis/code markers are not meaning
    return re.sub(r"\s+", " ", text).strip()


def protocol_fingerprint(path: Path) -> str:
    """SHA-256 of the normalised protocol text. Same bytes on any machine."""
    return hashlib.sha256(
        _normalize_protocol_text(path.read_text(encoding="utf-8")).encode("utf-8")
    ).hexdigest()


#: Load-bearing sentences that must survive verbatim. Chosen so that stating the
#: OPPOSITE of the directive is impossible while the clause is still present.
PROTOCOL_PINNED_CLAUSES: dict[str, list[str]] = {
    # A key registry, not a contract of prose invariants — but it still carries a few
    # real ones, and those are pinnable even though the file is fingerprint-exempt.
    "config.md": [
        "the grounding gate (D33) is never bypassed at any level",
        "the gate never names a scanner",
        "the validator never scans it",
    ],
    "dependencies.md": [
        "the PRE-FLIGHT engine NEVER reads or executes this string",
        "build the install argv from structured data",
    ],
    "graph.md": [
        "The tree-sitter floor MUST populate",
        "exploration-only",
    ],
    "escalation.md": [
        "the orchestrator makes the final routing call",
        "no in-plan solution",
    ],
    "engram.md": [
        "the agnostic core never depends on the engram",
        "consult-if-present, no-op if absent",
    ],
    "orientation.md": [
        "what it must escalate rather than improvise",
        "budget-capped to the prime frame",
    ],
    "state.md": [
        "git is authoritative; the live cache is disposable",
        "churns; rebuilt from tier-2 on re-entry",
    ],
    "handoff.md": [
        "unknown kind; never gates",
        "demotes the handoff from sole-anchor to context-input",
        "durable, Obsidian-native",
    ],
    "intent.md": [
        "frozen by kata-initiate",
        "Absent or empty is valid",
    ],
    "reuse-claims.md": [
        "claim to verify, not an assumption",
        "A reuse claim with no cited surface",
        "verify-before-reuse",
    ],
    "recall.md": [
        "NO embeddings / NO RAG / no vector retrieval",
        "it never hard-filters or silently trusts",
        "Recall surfaces material; it never decides, never writes, never gates",
    ],
    "steering.md": [
        "graceful kill-switch (never a blind mid-task kill)",
        "Active directives",
    ],
    "orchestration.md": [
        # The doctrine sentence itself — the centrepiece this whole file exists to pin.
        "A well-behaved orchestrator does not do the work itself.",
        # What "not doing the work" means, concretely — the line an inversion would have to erase.
        "Writing the code, the tests, the design doc, or the plan IS doing the work",
        # The honest residual (d) — required, must not be softened away.
        "The conductor cannot reach zero judgment.",
        # The not-mechanically-provable admission (f) — required, must not be softened away.
        "it is NOT mechanically provable",
    ],
    "prime-directives.md": [
        # PD-1 — the prohibition itself, and what "complete" means.
        "never defers, refuses, stubs, scaffolds, simplifies away, leaves unwired, or passes over",
        "Complete means wired end-to-end",
        "is NOT built, and claiming otherwise is a PD-2 violation",
        # PD-2 — truthfulness, and the stub-is-drift equivalence.
        "never misleads, and never lies",
        "Never claim built what is not built",
        "A stub, scaffold, facade, or mock reported as a completed feature IS DRIFT",
        # PD-2 — the operator's 2026-07-28 done-requires-proof bar (KH-T02).
        "Done requires proof, not assertion",
        "or explicitly approved by the operator",
    ],
    "authored-artifact-gate.md": [
        # Row 2 — the conductor must read the file, never substitute the payload's self-report.
        "never the dispatch payload's self-reported verdict as a substitute for reading it",
        # Row 5 — a self-flagged deviation is checked, never trusted outright.
        "never accepted at face value",
        # Row 6 — the no-frozen-invariant-retired prohibition itself.
        "does not silently weaken, retire, or leave ambiguous a Prime Directive",
        # Honesty note — the same non-mechanical admission orchestration.md already makes.
        "explicitly not mechanically provable",
        # §PLAN application — a future reader must not invent a second rubric.
        "No new rows are needed for PLAN.md",
    ],
    # ------------------------------------------------------------------ #
    # ungated-protocol-files (UPF-4/UPF-5, 2026-08-03) — the eight that
    # were guarded by nothing. Same bar as everything above: stating the
    # OPPOSITE of the directive must be impossible while the clause stands.
    # ------------------------------------------------------------------ #
    "cursor.md": [
        # EXACTLY two clauses, and NEITHER may span the "(or truncate it)" parenthetical at
        # the run-isolation section (UPF-4). Clause matching is a substring test after
        # normalisation and
        # does NOT strip parentheticals, so the run-isolation MUST and the rotation duty are
        # pinned as two short spans that sit on either side of it. Pinning the truncation
        # permission would make the LOOPHOLE load-bearing — a tamper-evident contract must
        # protect the invariant, never the escape from it. Whether "(or truncate it)" should
        # be removed at all is a separate, still-open question (2026-07-28 handoff §5).
        "MUST contain only the current run's events",
        "rotates any pre-existing board at run start",
    ],
    "exec-safety.md": [
        # The external-domain execution rule — the RCE guard itself.
        "Structured argv + shell=False + validated. Never a freeform string. Never shell=True.",
        # The registry-growth duty: a new sink cannot be added silently.
        "must be added here with its trust domain and guard, and must satisfy the guard above",
        # The "when the surface is not safe" ruling — the anti-soft-label line.
        "it is a NEW execution capability, not a reuse of an existing safe sink",
        # The in-process sibling of the same class (sandbox-escape via eval/exec).
        "MUST NEVER be passed to eval or exec",
    ],
    "observability.md": [
        # A wrong read of this file corrupts evaluation, which is the gate. Each clause below
        # is a fail-closed reading rule whose inversion produces a silently-wrong read.
        "A malformed row RAISES — never skip-and-average",
        "Never treat null as 0 in an average; never fabricate a value to fill the gap.",
        "Malformed trailer / scan failure ⇒ treat-as-triggered, never a silent pass.",
        "Calibration rows never enter medians.",
        "never bare at a .kata/* path",
    ],
    "iac-safety.md": [
        # The tier boundary — the harness holds no creds and never applies.
        "The harness writes and analyzes IaC. It never runs a live terraform apply or execute-change-set.",
        "must never emit --auto-approve or its equivalent",
        # The fail-closed scanner posture (scanner-absent is its own always-FAIL condition).
        "The gate never passes with zero scanner coverage.",
        # The MAJOR-3 honesty contract on static analysis.
        "A clean static result is NOT a verified no-destroy.",
        # The three-valued verdict must never be collapsed in either direction.
        "escalate must not become fail (losing the human signal) and fail must not become pass (defeating the scanner)",
    ],
    "narration.md": [
        "internal activity labels are never surfaced to the user",
        # The cadence rule — trust, not spam.
        "Narrate at meaningful boundaries; stay quiet between.",
        # The never-tiered breakthrough alert; no mode or cadence setting may suppress it.
        "Decisions, escalations, and critical failures surface in the conversation immediately and unmissably, regardless of routine quiet.",
        # The honesty guard against narrating gated-off capabilities.
        "The narrator MUST NOT imply capabilities that are not wired in the running harness.",
    ],
    "validation-misses.md": [
        # The T1 observe-only boundary — the whole layer's C/B invariant.
        "it logs, counts, and surfaces — it changes no gate behavior, never alters a gate verdict, and never mutates a skill",
        # The read-only seam: the reviewer flags, the orchestrator appends.
        "The reviewer does NOT write the manifest.",
        # Secret hygiene on a durable, committed learning corpus.
        "Never log code payloads, key material, secrets, or verbatim code fragments",
        # The T2 boundary — draft only, never act.
        "it may NOT (i) change any gate verdict, (ii) edit any skill/protocol/tool, or (iii) merge its own proposal",
    ],
    "advice.md": [
        # S-2 — the advisory-never-authoritative posture the whole schema rests on.
        "Advice is advisory, never authoritative",
        "Advice serves; the executor decides.",
        # Only the conductor dispatches; a worker requests via an escalation.
        "Only the conductor dispatches kata-advise — a worker never does",
        # G-4 — builder and judge never share an advisor (a D33-class no-self-cert extension).
        "The gate and closeout NEVER consult",
        "response.sketch is never applied verbatim",
    ],
    "persona.md": [
        # The defining instinct — the translation duty that makes the voice what it is.
        "one-shot complex work, then always translate",
        "Never hedge a completed fact.",
        # Internal loop vocabulary is never the user-facing account.
        "Do not surface GRILL / FREEZE / EXECUTE / EVALUATE / HANDOFF / IMPROVE / PREFLIGHT to the user",
        # The gated-not-live register seam, and the forbidden overclaim about it.
        "There is no live register-setting path in v0.1.",
        "Claiming adaptive register is live is a forbidden overclaim",
    ],
    # ------------------------------------------------------------------ #
    # deferral.md (trust-model TM-D1, 2026-08-16) — the ledger contract.
    # Same bar as everything above: stating the OPPOSITE of the rule must
    # be impossible while the clause stands. Each clause below is one an
    # inversion would have to DELETE — "the gate may also credit approval
    # from the commit message", "captured counts as closed", "an unparsed
    # ledger is skipped" all require the sentence to go.
    # ------------------------------------------------------------------ #
    "deferral.md": [
        # The approval record — the ONLY place a gate may read an approval from.
        # NB: pinned against the body sentence, not the verbatim-contract blockquote. The
        # normaliser strips emphasis but NOT the `>` blockquote marker, so a wrapped quote
        # normalises to "... ONLY from > these fields" and can never be matched as a clause.
        "A gate may credit an approval ONLY from these fields.",
        # No self-approval: the D33 no-self-certification rule applied to the park.
        "accepted_by names a human, not an agent",
        # Closure — the captured/closed distinction the whole ledger rests on.
        "Closure requires the closing commit reference — captured is not closed",
        # The D3b same-line debt-marker rule.
        "without a `DEF-*` reference on the same line is a BLOCKER",
        # Append-only as a rule about MEANING, not bytes.
        "an existing entry is never rewritten to say something else",
        # The anti-vacuity posture: unreadable is a refusal, never a silent zero.
        "a parse failure is a refusal, never a skip",
    ],
}

#: Digest of the normalised file. Update ONLY via --update-protocol-fingerprint,
#: after reviewing the diff — the whole point is that the update is a deliberate act.
#: NOTE the deliberate absence of `config.md` and `exec-safety.md` — the two declared
#: registry-shaped fingerprint exemptions; see the SCOPE note above.
PROTOCOL_FINGERPRINTS: dict[str, str] = {
    "advice.md": "c811801ef8701f0873a8e2dc9edd093da891d17a1c1eb250e1fd8fdca69f500a",
    "authored-artifact-gate.md": "b90eb9ded18eb324382d23772cabc7740112da964983317ed196858c486ae535",
    # Heritage key `board.md` renamed to `cursor.md` with the file (W4). The digest below is
    # the PRE-rename value and is EXPECTED to mismatch until the conductor's G3 re-approval
    # paste — the two-step working, not a regression. Never paste it from a builder.
    "cursor.md": "9faea138d52b639649874cc9c7a00791a017de6ecc7db410f7b79cfd61849f60",
    "deferral.md": "249b9eb666be0988c1f2529175dd98fdff0707baff8c866cbe01b41d8c0829e8",
    "dependencies.md": "652df1a8f46b93cd13f1e54ba19ec8725ec9e48c02e4b03ea5a8e27bcafe972c",
    "engram.md": "ad01a873d4aff387c85f3798db7494ed6750aab4c1054b876e9282c9fbf2d879",
    "escalation.md": "ac9724a093c7f4890fbe567efec8849465517b36cb4f048f1842b9348e116a76",
    "graph.md": "48fbd4619ac9f6feb761119d5e0569b634ae556e2bc8f38c7fe3ff49f2194778",
    "handoff.md": "2e0e11d17f6b8101d2de705ebb01df065ac4cc6decfad53a63bd0237e0e696c9",
    "iac-safety.md": "ae8971eaf8ec94b123129663148a4453a72f2b7fdc4c00abde15d5bca36f62d0",
    "intent.md": "3a45250790721964fc3140420cedf5e2054551e438a90190568760b573245722",
    "narration.md": "b91d64b7491df18691ccec4869c30f95504570e66dd75a5e8a8e825628378d94",
    "observability.md": "d9d71aa9f8c596ff1f391158038ee5fe08954031a3f287672b544154e66ef439",
    "orchestration.md": "bc0aee0520b48b69f94f3b9242ac427bb587866e7d45dd74d221317de02b2daf",
    "orientation.md": "b926c41b9e61945b1450c96ec8e89044c33668ef5d63414038279787c61c455e",
    "persona.md": "987ab6fd61e6688508b638e6a05118371aa061f319167f944ab16a45cf1c23ab",
    "prime-directives.md": "3d5787e3bab577bd0ae3111bcfcad8712fd69dde43b9f61af2c54d4fd378b829",
    "recall.md": "6edfd018c9c4d62f27f9b94e081e6e15b4002dd13a2277aa7d214ddff4f0d405",
    "reuse-claims.md": "4cc12760aca1c920f72f833b9f7b7a6131e21ed447cc3bcc2ef8b4d52921f732",
    "state.md": "19e0e36c263df02170133de4271f07566fb8e7cc94e0364f843d2c012d27c767",
    "steering.md": "df9bed6779b1e96244d9c0f087bb3a7c450187b44bad8b9857fab62f2086f5b4",
    "validation-misses.md": "e91ebdad99de2e7d38f49fbc00ab8c5a1c1a45a2d34bd544ed3fca4fd8ede461",
}


@check
def check_protocol_integrity(_skills: list[Skill]) -> list[Finding]:
    out: list[Finding] = []
    for fname, clauses in PROTOCOL_PINNED_CLAUSES.items():
        path = PROTOCOL_DIR / fname
        if not path.exists():
            out.append(Finding("ERROR", f"protocol/{fname}", "pinned protocol file missing"))
            continue
        normalized = _normalize_protocol_text(path.read_text(encoding="utf-8"))
        for clause in clauses:
            if _normalize_protocol_text(clause) not in normalized:
                out.append(Finding(
                    "ERROR", f"protocol/{fname}",
                    f"load-bearing clause deleted or reworded: {clause!r}",
                ))
    for fname, golden in PROTOCOL_FINGERPRINTS.items():
        path = PROTOCOL_DIR / fname
        if not path.exists():
            continue  # already reported above
        actual = protocol_fingerprint(path)
        if actual != golden:
            out.append(Finding(
                "ERROR", f"protocol/{fname}",
                f"fingerprint mismatch (expected {golden[:12]}…, got {actual[:12]}…). "
                "If this edit is intended: review the diff, then run "
                "`python validate_skills.py --update-protocol-fingerprint` and paste the new value "
                "into PROTOCOL_FINGERPRINTS.",
            ))
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
    # D91: also include module skill names so [[kata-initiate]] wikilinks resolve.
    if MODULES_DIR.exists():
        for p in MODULES_DIR.glob("*/*/SKILL.md"):
            names.add(p.parent.name)
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


@check
def check_reuse_claims_pointers(skills: list[Skill]) -> list[Finding]:
    """LD5(a): assert protocol/reuse-claims.md is referenced in all three concrete paths.

    Dual mechanism (mirrors check_rubric_wikilinks pattern):
    - kata-design-doc, kata-tdd: checked via loaded-skill bodies (skills arg).
    - kata-plan/RUBRIC.md:       checked via separate file read (not a loaded skill).
    Any missing reference is an ERROR (default-FAIL, LD5 / D33 never-tiered).
    """
    errors: list[Finding] = []
    pointer = "protocol/reuse-claims.md"

    # Part 1 — skill bodies: kata-design-doc and kata-tdd are loaded skills; check their bodies.
    skill_map = {s.name: s for s in skills}
    for name in ("kata-design-doc", "kata-tdd"):
        s = skill_map.get(name)
        if s is None:
            # Not in this skill set → nothing to check here. Producer EXISTENCE against the real
            # tree is enforced separately by check_reuse_claims_producers_exist (m4), so this
            # content check stays safe over arbitrary/fixture skill lists.
            continue
        if pointer not in s.body:
            errors.append(Finding("ERROR", s.dir.name, f"skill body must reference '{pointer}' (LD4 pointer, never-tiered)"))

    # Part 2 — kata-plan/RUBRIC.md: NOT a loaded skill; read separately (mirrors check_rubric_wikilinks).
    rubric = SKILLS_DIR / "plan" / "kata-plan" / "RUBRIC.md"
    if rubric.exists():
        if pointer not in rubric.read_text(encoding="utf-8"):
            errors.append(Finding("ERROR", "kata-plan/RUBRIC.md", f"RUBRIC must reference '{pointer}' (LD4 pointer, never-tiered)"))

    return errors


@check
def check_reuse_claims_producers_exist(skills: list[Skill]) -> list[Finding]:
    """m4 (default-FAIL): the reuse-claims producer skills MUST exist in the real tree.

    The pointer content-check (check_reuse_claims_pointers) silently skips a producer that
    isn't present, so a future rename/removal would quietly stop enforcing the guard — the
    exact "unwired lessons recur" risk (L12c) this whole change exists to prevent. This check
    asserts existence against SKILLS_DIR directly (independent of the passed skill list, so it
    is stable over fixtures), and fails loudly if a producer skill is gone.
    """
    errors: list[Finding] = []
    for name in ("kata-design-doc", "kata-tdd"):
        if not list(SKILLS_DIR.glob(f"*/{name}/SKILL.md")):
            errors.append(Finding("ERROR", name, f"reuse-claims producer skill '{name}' is missing from the tree (LD4 guard cannot be enforced; m4/L12c)"))
    return errors


@check
def check_model_in_skill_frontmatter(skills: list[Skill]) -> list[Finding]:
    """A1 re-introduction guard (DESIGN §3 A1, R8 / model-tiering D131).

    ERRORs on any absolute 'model:' key in SKILL.md frontmatter for core skills
    (skills/**) and modules/**. This prevents re-introducing a hard-baked model ID
    that breaks when that model is gated or unavailable (the Fable outage pattern).

    Scope predicate (R8): 'adapters' not in s.dir.parts.
    Adapters/config MAY still pin a model — that is explicitly out of scope for this guard.
    """
    out: list[Finding] = []
    for s in skills:
        if "adapters" in s.dir.parts:
            continue  # adapters/** may pin models — R8 carve-out
        if any(k.lower() == "model" for k in s.frontmatter):
            out.append(Finding(
                "ERROR",
                s.dir.name,
                "frontmatter 'model:' is FORBIDDEN in core SKILL.md — model is dispatch-resolved "
                "(relative to the operator's anchor at runtime), never pinned in a skill body. "
                "Remove this field and rely on dispatch-time relative resolution instead. "
                "See STANDARDS.md §1 and AGENTS.md (model-tiering D131, A1 guard).",
            ))
    return out


def run_checks(skills: list[Skill]) -> list[Finding]:
    findings: list[Finding] = []
    for fn in CHECKS:
        findings.extend(fn(skills))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KataHarness skill-conformance validator")
    parser.add_argument("--write", action="store_true", help="regenerate the README skill index from frontmatter")
    parser.add_argument(
        "--only", metavar="SKILL",
        help="scope the per-skill checks to one skill by name (W-7; the whole-tree checks "
             "— README sync, protocol schemas — still run over the full set)",
    )
    parser.add_argument(
        "--update-protocol-fingerprint", action="store_true",
        help="print the current fingerprint of each pinned protocol file so it can be pasted into "
             "PROTOCOL_FINGERPRINTS after reviewing the diff (KH-T02). Prints only — it never "
             "rewrites the pin, because a self-updating tamper-check protects nothing.",
    )
    args = parser.parse_args(argv)

    if args.update_protocol_fingerprint:
        # Deliberately print-only. Auto-writing the golden would let any edit re-bless
        # itself, which is exactly the workaround this check exists to remove.
        for fname in sorted(PROTOCOL_FINGERPRINTS):
            path = PROTOCOL_DIR / fname
            if not path.exists():
                print(f"ERROR: protocol/{fname}: missing", file=sys.stderr)
                return 1
            print(f'    "{fname}": "{protocol_fingerprint(path)}",')
        print("\nReview the diff, then paste the line(s) above into PROTOCOL_FINGERPRINTS "
              "in validate_skills.py.", file=sys.stderr)
        return 0

    skills = load_skills()
    if args.only and not any(s.name == args.only for s in skills):
        print(f"ERROR: --only: no skill named {args.only!r} found.", file=sys.stderr)
        return 1
    if not skills:
        # D136/D33: zero skills discovered is NOT a green validator — an empty
        # discovery set means the tree is missing or mis-rooted, and certifying
        # over it would be a silent-permissive default (self-certification).
        print("ERROR: skills-tree: 0 skills discovered — refusing to certify an empty tree "
              "(check SKILLS_DIR/MODULES_DIR roots).", file=sys.stderr)
        print("\n0 skills checked — 1 error(s), 0 warning(s).")
        return 1
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

    # Checks always run over the FULL set (so README-sync / protocol-schema
    # checks are correct); --only then filters the REPORT to the named skill's
    # per-skill findings — a focusing aid, never a narrower gate (W-7).
    findings = run_checks(skills)
    if args.only:
        findings = [f for f in findings if f.where == args.only]
    for f in findings:
        print(f"{f.level}: {f.where}: {f.msg}", file=sys.stderr)
    errors = [f for f in findings if f.level == "ERROR"]
    scope = f"1 skill ({args.only})" if args.only else f"{len(skills)} skills"
    print(f"\n{scope} checked — {len(errors)} error(s), {len(findings) - len(errors)} warning(s).")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
