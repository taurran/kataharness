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
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import yaml

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
#   * CLAUSES apply to ALL 13 REQUIRED_PROTOCOL files. This layer is free on ordinary
#     edits — it is reflow-tolerant and only fires when a load-bearing sentence is
#     deleted or reworded — so there is no reason to withhold it anywhere.
#   * FINGERPRINTS apply to 12 of the 13. `config.md` is deliberately EXCLUDED: it is a
#     key registry that changed 31 times (vs 1-11 for every other protocol file), because
#     essentially every feature adds a config key. Fingerprinting a registry buys nothing
#     — the risk there is a MISSING key, which REQUIRED_PROTOCOL already covers — while
#     imposing ~31 re-approvals, which is precisely how blind re-approval gets trained.
#     Its invariants are still clause-pinned.
#
# NOT covered, and worth naming rather than leaving to be rediscovered: eight protocol
# files are absent from REQUIRED_PROTOCOL entirely and therefore ungated by any layer —
# board.md, exec-safety.md, observability.md, iac-safety.md, narration.md,
# validation-misses.md, advice.md, persona.md. board.md in particular carries a literal
# run-isolation MUST. Registering new files newly gates them, so that is its own change.
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
}

#: Digest of the normalised file. Update ONLY via --update-protocol-fingerprint,
#: after reviewing the diff — the whole point is that the update is a deliberate act.
#: NOTE the deliberate absence of `config.md` — see the SCOPE note above.
PROTOCOL_FINGERPRINTS: dict[str, str] = {
    "dependencies.md": "652df1a8f46b93cd13f1e54ba19ec8725ec9e48c02e4b03ea5a8e27bcafe972c",
    "engram.md": "ad01a873d4aff387c85f3798db7494ed6750aab4c1054b876e9282c9fbf2d879",
    "escalation.md": "b155f7151a6440226c3a841f65b5a6f1fd0d2580fc6af7ae10346892a26ee15b",
    "graph.md": "48fbd4619ac9f6feb761119d5e0569b634ae556e2bc8f38c7fe3ff49f2194778",
    "handoff.md": "2e0e11d17f6b8101d2de705ebb01df065ac4cc6decfad53a63bd0237e0e696c9",
    "intent.md": "aaf4632093ca7310f373f8ea49cd85373aa124f30f1adcf9d9103b640521b747",
    "orchestration.md": "bc0aee0520b48b69f94f3b9242ac427bb587866e7d45dd74d221317de02b2daf",
    "orientation.md": "b926c41b9e61945b1450c96ec8e89044c33668ef5d63414038279787c61c455e",
    "prime-directives.md": "7be2a0d1ab682ed45120fe5d6ca976f38a68df623da2665a19b0374ec7e07959",
    "recall.md": "6edfd018c9c4d62f27f9b94e081e6e15b4002dd13a2277aa7d214ddff4f0d405",
    "reuse-claims.md": "4cc12760aca1c920f72f833b9f7b7a6131e21ed447cc3bcc2ef8b4d52921f732",
    "state.md": "19e0e36c263df02170133de4271f07566fb8e7cc94e0364f843d2c012d27c767",
    "steering.md": "df9bed6779b1e96244d9c0f087bb3a7c450187b44bad8b9857fab62f2086f5b4",
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
