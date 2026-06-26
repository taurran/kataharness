"""project_find.py — per-run project-folder search for KataHarness install/preflight.

Given a project NAME and a parent project directory (the remembered default,
overridable per run), search for matching project folders and return ranked
candidates. The skill (kata-initiate preflight) drives the confirm step:

- 1 candidate  -> confirm it.
- N candidates -> list them, the user picks.
- 0 candidates -> the user types the full path.

Public API
----------
find_projects(name, parent_dir, rough_location=None, max_depth=3) -> list[dict]
    PURE search (filesystem read only, no prompts). Walks ``parent_dir`` up to
    ``max_depth`` levels, scores each directory name against ``name``
    (case-insensitive: exact > prefix > substring), boosts candidates whose path
    contains ``rough_location``, and returns a ranked list of
    ``{"path": str, "name": str, "score": int, "isRepo": bool}``.
    Returns ``[]`` when ``parent_dir`` does not exist or nothing matches.

Design notes
------------
No prompting, no mutation — this is a pure read so it is trivially unit-testable
on a ``tmp_path`` fixture. Ranking is deterministic (score desc, then shallower
path, then alphabetical) so two runs over the same tree agree (consistency, D18).
"""

from __future__ import annotations

from pathlib import Path

# Score tiers for a name match (higher = better).
_EXACT = 3
_PREFIX = 2
_SUBSTR = 1
_LOCATION_BOOST = 4  # a rough-location hit outweighs a weaker name match


def _name_score(candidate: str, query: str) -> int:
    """Case-insensitive match score of a directory name against the query."""
    c = candidate.casefold()
    q = query.casefold()
    if c == q:
        return _EXACT
    if c.startswith(q):
        return _PREFIX
    if q in c:
        return _SUBSTR
    return 0


def find_projects(
    name: str,
    parent_dir: str | Path,
    rough_location: str | None = None,
    max_depth: int = 3,
) -> list[dict]:
    """Return ranked candidate project folders for ``name`` under ``parent_dir``.

    Parameters
    ----------
    name:
        The project name the user gave (case-insensitive match).
    parent_dir:
        The parent project directory to search under (default-parent setting,
        overridable per run).
    rough_location:
        Optional path fragment / substring the user offered ("it's somewhere in
        my work folder"); candidates whose absolute path contains it are boosted.
    max_depth:
        How many directory levels below ``parent_dir`` to descend (default 3).

    Returns
    -------
    list[dict]
        ``{"path", "name", "score", "isRepo"}`` sorted best-first. Empty when the
        parent does not exist or nothing matches.
    """
    if not name or not str(name).strip():
        return []
    parent = Path(parent_dir)
    if not parent.is_dir():
        return []

    loc = rough_location.casefold() if rough_location else None
    out: list[dict] = []

    # Walk breadth-limited by depth. parent itself is depth 0; its children depth 1.
    stack: list[tuple[Path, int]] = [(parent, 0)]
    while stack:
        cur, depth = stack.pop()
        if depth >= max_depth:
            continue
        try:
            children = [c for c in cur.iterdir() if c.is_dir()]
        except (PermissionError, OSError):
            continue
        for child in children:
            # Skip noise dirs that are never a user's project root.
            if child.name in {".git", "node_modules", "__pycache__", ".venv"}:
                continue
            score = _name_score(child.name, name)
            if score > 0:
                if loc and loc in str(child).casefold():
                    score += _LOCATION_BOOST
                out.append(
                    {
                        "path": str(child),
                        "name": child.name,
                        "score": score,
                        "isRepo": (child / ".git").exists(),
                    }
                )
            stack.append((child, depth + 1))

    # Deterministic ranking: score desc, shallower path first, then alphabetical.
    out.sort(key=lambda d: (-d["score"], d["path"].count("/") + d["path"].count("\\"), d["path"].casefold()))
    return out
