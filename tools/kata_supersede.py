"""kata_supersede.py — supersedes / fork precedence resolver for KataHarness.

Provides the fork-shadowing layer defined in install-update-polish DESIGN §7.
This module is PURE and STDLIB-ONLY: NO git, NO network, NO yaml, NO third-party
imports.  The same zero-dependency invariant that forced kata_overlay to drop yaml
applies here — the resolve path runs in the engine install/update path where pyyaml
is NOT guaranteed to be installed.  Importing yaml (directly or transitively via
validate_skills, which imports yaml at module top) would make kata_install's
import-guarded _materialize_pass silently no-op in a real install.

Public API
----------
resolve_shadows(agentskills_dir) -> dict[str, Path]
    Scan the PROMOTED skills under <agentskills_dir>/skills/**/SKILL.md.
    Candidates (under <agentskills_dir>/candidates/**) are NOT scanned — they
    are sandboxed and never shadow upstream skills.
    For each promoted skill whose frontmatter has a non-empty ``supersedes: <name>``,
    map ``{upstream_name: fork_dir}``.  When two different forks both claim the same
    upstream name, the conflicting entry maps to ``_CONFLICT_PATH`` (a sentinel
    that validate_shadows detects and reports as an ambiguous-double-supersede error).
    Absent/None agentskills_dir → {} (no-op, BC).

validate_shadows(shadows, base_names) -> list[str]
    Fail-closed structural check.  Returns ERROR strings (empty list = valid) for:
    (a) a supersedes target not in base_names — unknown upstream skill;
    (b) an ambiguous double-supersede — two promoted forks claimed the same upstream
        (detected via the _CONFLICT_PATH sentinel in the shadows dict).

Security: all operator-supplied paths are ``..``-guarded (CWE-23).
"""

from __future__ import annotations

import re
from pathlib import Path

# ---------------------------------------------------------------------------
# Conflict sentinel
# ---------------------------------------------------------------------------

# Returned by resolve_shadows when two different promoted forks both carry
# ``supersedes: <same-upstream-name>``.  The leading '.' makes it an
# invalid skill directory name on every supported platform; it is always a
# *relative* path so it can never equal an absolute fork dir returned by
# a real scan.  validate_shadows checks for this sentinel and emits an error.
_CONFLICT_PATH = Path(".__kata_conflict__")


# ---------------------------------------------------------------------------
# Path safety — mirror kata_overlay / kata_version ._safe_abs convention
# ---------------------------------------------------------------------------


def _safe_abs(raw: str | Path) -> Path:
    """Reject ``..`` traversal (CWE-23) then resolve to an absolute path."""
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"kata_supersede: refusing path with '..' traversal: {raw!r}"
        )
    return p.resolve()


# ---------------------------------------------------------------------------
# Frontmatter split — stdlib-only (NO yaml).
# Mirrors kata_overlay._split_frontmatter exactly (same shape: "---\n<fm>\n---\n<body>").
# ---------------------------------------------------------------------------


def _split_frontmatter(text: str) -> tuple[str | None, str]:
    """Split a SKILL.md string into (raw_frontmatter_text, body).

    Returns ``(None, text)`` when there is no leading frontmatter block.
    Otherwise returns the raw text BETWEEN the opening and closing ``---``
    delimiters and the body (everything after the closing ``---``).

    Reconstruction is exact: ``"---" + fm + "---" + body == original``.
    """
    if not text.startswith("---"):
        return None, text
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None, text
    return parts[1], parts[2]


# ---------------------------------------------------------------------------
# supersedes extractor — stdlib-only frontmatter reader
# ---------------------------------------------------------------------------


def _read_supersedes(text: str) -> list[str]:
    """Extract the list of upstream names from a SKILL.md's ``supersedes:`` field.

    Handles all forms that appear in real skill files:

    ``supersedes: kata-review``     → ["kata-review"]   (simple scalar)
    ``supersedes: [kata-review]``   → ["kata-review"]   (inline list, one element)
    ``supersedes: [a, b]``          → ["a", "b"]        (inline list, multiple)
    ``supersedes: []``              → []                 (empty inline list)
    ``supersedes:`` (blank)        → []                 (empty value)
    multi-line::

        supersedes:
        - kata-review

    → ["kata-review"]

    absent key                      → []

    Stdlib-only: no yaml.  Parses the raw frontmatter text from _split_frontmatter.
    Only top-level (non-indented) ``supersedes:`` keys are recognised; indented
    continuations are collected only as list items (leading ``-``).
    """
    fm_text, _ = _split_frontmatter(text)
    if fm_text is None:
        return []

    lines = fm_text.split("\n")
    for i, line in enumerate(lines):
        m = re.match(r"^supersedes\s*:(.*)", line)
        if m is None:
            continue

        inline = m.group(1).strip()

        if not inline:
            # Multi-line YAML list: gather "- item" continuation lines until a
            # line that is blank or starts a new top-level key.
            names: list[str] = []
            for cont in lines[i + 1 :]:
                stripped = cont.strip()
                if not stripped:
                    # Blank line ends the list block.
                    break
                if not stripped.startswith("-"):
                    # Next top-level key or non-list content ends the block.
                    break
                item = stripped[1:].strip().strip('"').strip("'")
                if item:
                    names.append(item)
            return names

        # Inline list form: ``[a, b, c]`` or ``[]``.
        if inline.startswith("["):
            inner = inline[1:].rstrip("]").strip()
            if not inner:
                return []
            return [
                part.strip().strip('"').strip("'")
                for part in inner.split(",")
                if part.strip()
            ]

        # Simple scalar: ``kata-review``.  Strip any quoting.
        return [inline.strip('"').strip("'")]

    return []


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_shadows(agentskills_dir) -> dict[str, Path]:
    """Scan promoted toolkit skills and return the supersedes shadow map.

    Scans ``<agentskills_dir>/skills/**/SKILL.md`` only — NOT ``candidates/``.
    Candidates are sandboxed; they never shadow upstream skills until promoted
    through the ``kata-promote`` human gate.

    For each promoted SKILL.md carrying a non-empty ``supersedes: <name>``, adds
    ``{upstream_name: fork_dir}`` to the result.  When **two different** promoted
    forks both claim the same upstream name, the conflicting entry maps to
    ``_CONFLICT_PATH`` (a sentinel that ``validate_shadows`` detects as an error).

    Parameters
    ----------
    agentskills_dir:
        Path-like or ``None``.  The user's toolkit directory (``agentSkills.dir``
        config value).  ``None`` → ``{}`` (BC — the engine calls this
        unconditionally; an absent toolkit is the common case for a fresh install
        that has not yet configured a toolkit).

    Returns
    -------
    dict[str, Path]
        Mapping of upstream skill name → promoted fork directory.
        A conflict entry (two forks for the same upstream) maps to
        ``_CONFLICT_PATH``; call ``validate_shadows`` to surface the error.
    """
    if agentskills_dir is None:
        return {}

    try:
        base = _safe_abs(agentskills_dir)
    except ValueError:
        # Path with '..' traversal — refuse silently (fail-closed).
        return {}

    if not base.is_dir():
        return {}

    skills_root = base / "skills"
    if not skills_root.is_dir():
        return {}

    # Accumulate: upstream_name → list of all fork dirs claiming it.
    # Using a list (not a set) to preserve scan order for determinism.
    accumulator: dict[str, list[Path]] = {}

    for skill_md in sorted(skills_root.rglob("SKILL.md")):
        fork_dir = skill_md.parent
        try:
            text = skill_md.read_text(encoding="utf-8", errors="replace")
        except OSError:
            # Unreadable SKILL.md — skip (fail-closed, never crash).
            continue

        for upstream_name in _read_supersedes(text):
            if not upstream_name:
                continue
            if upstream_name not in accumulator:
                accumulator[upstream_name] = []
            accumulator[upstream_name].append(fork_dir)

    # Collapse accumulator: single-fork entries use the real fork dir;
    # multi-fork entries use _CONFLICT_PATH so validate_shadows can report them.
    result: dict[str, Path] = {}
    for upstream_name, fork_dirs in accumulator.items():
        if len(fork_dirs) == 1:
            result[upstream_name] = fork_dirs[0]
        else:
            # Two or more forks claim this upstream → ambiguous precedence.
            result[upstream_name] = _CONFLICT_PATH

    return result


def validate_shadows(
    shadows: dict[str, Path],
    base_names,
) -> list[str]:
    """Fail-closed structural check for the shadow map.

    Intended to be called after ``resolve_shadows`` before the materialize pass
    installs any fork bodies.  The C2 engine wiring uses this return value to
    STOP and escalate rather than apply a partial shadow (no partial shadow —
    PLAN C1 gate).

    Parameters
    ----------
    shadows:
        The dict returned by ``resolve_shadows``.
    base_names:
        An iterable of the canonical upstream skill names present in the repo
        (e.g. the keys from ``kata_version.read_manifest`` or the set returned
        by ``iter_skill_dirs``).  Used to verify that every ``supersedes:``
        target names a real base skill.

    Returns
    -------
    list[str]
        ERROR strings (empty list = all shadows valid and unambiguous).
        One error string per problem found:
        (a) Unknown upstream — ``supersedes`` target not in ``base_names``.
        (b) Ambiguous double-supersede — two promoted forks claimed the same
            upstream name (detected via the ``_CONFLICT_PATH`` sentinel).
    """
    base_set = set(base_names)
    errors: list[str] = []

    for upstream_name, fork_path in shadows.items():
        # (b) Conflict sentinel: two or more forks claimed this upstream.
        # Report the conflict first and skip the unknown-upstream check so
        # the error message focuses on the real problem (the duplicate fork),
        # not the side-effect of the sentinel not being in base_names.
        if fork_path == _CONFLICT_PATH:
            errors.append(
                f"supersedes conflict: multiple promoted forks claim the same "
                f"upstream '{upstream_name}' — promote only one fork with "
                f"'supersedes: {upstream_name}' to resolve the ambiguity"
            )
            continue

        # (a) Unknown upstream: the target is not a known base skill.
        if upstream_name not in base_set:
            errors.append(
                f"supersedes error: '{upstream_name}' is not a known base skill "
                f"(fork at '{fork_path}' carries 'supersedes: {upstream_name}' "
                f"but no such skill exists in the repo — check the spelling)"
            )

    return errors
