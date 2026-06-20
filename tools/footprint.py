"""Footprint manifest and diff-stat helpers for KataHarness runs.

Pure core functions (partition, is_within_footprint, manifest) do NOT call git.
Thin git wrappers (changed_since, diff_stat) are provided separately and are
not covered by the unit tests.
"""

from __future__ import annotations

import subprocess


def _normalize(path: str) -> str:
    """Normalize path separators to forward slashes."""
    return path.replace("\\", "/")


def _in_footprint(file: str, footprint: list[str]) -> bool:
    """Return True if *file* equals or is under any entry in *footprint*."""
    f = _normalize(file)
    for entry in footprint:
        e = _normalize(entry)
        if f == e:
            return True
        # treat entry as a directory prefix (ensure it ends with '/')
        prefix = e if e.endswith("/") else e + "/"
        if f.startswith(prefix):
            return True
    return False


def partition(changed_files: list[str], footprint: list[str]) -> dict:
    """Split *changed_files* into in-footprint and out-of-footprint buckets.

    Args:
        changed_files: Paths that changed in the current run (any separator).
        footprint: Declared allowed paths / directory prefixes.

    Returns:
        ``{"in_footprint": [...], "out_of_footprint": [...]}`` — both lists are
        normalized to forward slashes and sorted deterministically.
    """
    inside: list[str] = []
    outside: list[str] = []

    for raw in changed_files:
        normalized = _normalize(raw)
        if _in_footprint(raw, footprint):
            inside.append(normalized)
        else:
            outside.append(normalized)

    return {
        "in_footprint": sorted(inside),
        "out_of_footprint": sorted(outside),
    }


def is_within_footprint(changed_files: list[str], footprint: list[str]) -> bool:
    """Return True iff every changed file is within the declared footprint.

    Args:
        changed_files: Paths that changed in the current run.
        footprint: Declared allowed paths / directory prefixes.

    Returns:
        ``True`` when ``out_of_footprint`` is empty.
    """
    return len(partition(changed_files, footprint)["out_of_footprint"]) == 0


def manifest(
    changed_files: list[str],
    footprint: list[str],
    diffstat: str = "",
) -> dict:
    """Build a full footprint manifest for a KataHarness run.

    Args:
        changed_files: Paths that changed in the current run.
        footprint: Declared allowed paths / directory prefixes.
        diffstat: Optional ``git diff --stat`` output string.

    Returns:
        Dictionary with keys ``footprint``, ``changed``, ``inFootprint``,
        ``outOfFootprint``, ``withinFootprint``, and ``diffstat``.
    """
    parts = partition(changed_files, footprint)
    return {
        "footprint": footprint,
        "changed": changed_files,
        "inFootprint": parts["in_footprint"],
        "outOfFootprint": parts["out_of_footprint"],
        "withinFootprint": is_within_footprint(changed_files, footprint),
        "diffstat": diffstat,
    }


# ---------------------------------------------------------------------------
# Thin git wrappers — NOT required by tests; pure core above must not call git
# ---------------------------------------------------------------------------


def changed_since(ref: str) -> list[str]:
    """Return a list of files changed since *ref* using ``git diff --name-only``.

    Args:
        ref: Git ref (commit hash, branch, tag, etc.) to diff against HEAD.

    Returns:
        Sorted list of changed file paths (forward-slash normalized).
    """
    result = subprocess.run(
        ["git", "diff", "--name-only", ref],
        capture_output=True,
        text=True,
        check=True,
    )
    lines = [_normalize(line) for line in result.stdout.splitlines() if line.strip()]
    return sorted(lines)


def diff_stat(ref: str) -> str:
    """Return the ``git diff --stat`` output since *ref*.

    Args:
        ref: Git ref (commit hash, branch, tag, etc.) to diff against HEAD.

    Returns:
        Raw stat string from git.
    """
    result = subprocess.run(
        ["git", "diff", "--stat", ref],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip()
