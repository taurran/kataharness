"""benchmark_control.py — S4 control-clone + naming for kata-loop-benchmark.

Implements the control mechanism from DESIGN §2: an immutable reference directory
is NEVER written; each benchmark run clones the reference into a tagged sibling
working copy named ``<base>-katabenchmark<N>``.  A content-hash pins the control
at benchmark-definition time so ``detect_drift`` can flag any subsequent mutation
of the reference.

Security posture
----------------
PURE except the copytree / prune FS ops (injectable for tests).
No subprocess, no eval, no exec, no shell.  CWE-23 ``..``-guard on all path
inputs (mirrors ``_safe_abs`` in ``kata_install.py`` and ``_guard_path`` in
``validation_misses.py``).  ``protocol/exec-safety.md`` is unchanged — zero new
exec sink is a deliberate invariant of this module.

Public API (S4 contract — cite-able by name per protocol/reuse-claims.md)
--------------------------------------------------------------------------
sibling_name(base, n)              → "<base>-katabenchmark<N>"
next_index(parent_dir, base)       → next free N given existing siblings
content_hash(ref_dir)              → stable SHA-256 digest over sorted file set
detect_drift(ref_dir, pinned_hash) → typed result dict; drifted=True if ref changed
clone_control(ref_dir, dest, *, copy_fn=None) → shutil.copytree copy into dest
prune(copy_dir, *, rm_fn=None)     → remove a spawned *-katabenchmark<N> copy
"""

from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from typing import Callable, Union


# ---------------------------------------------------------------------------
# Sentinel suffix — single source of truth for the naming convention
# ---------------------------------------------------------------------------

_SUFFIX: str = "-katabenchmark"


# ---------------------------------------------------------------------------
# Path-traversal guard (CWE-23) — mirrors _guard_path in validation_misses.py
# and _safe_abs in kata_install.py
# ---------------------------------------------------------------------------


def _guard_path(raw: str | Path) -> Path:
    """Reject paths containing ``..`` traversal (CWE-23).  Does NOT resolve.

    Resolution is left to the caller; only the ``..`` caller-bug raises here
    so that a pathological path surfaces as a loud ValueError, not a silent
    directory escape.

    Args:
        raw: The raw path string or Path to guard.

    Returns:
        A ``Path`` built from *raw* (unresolved).

    Raises:
        ValueError: if *raw* contains a ``..`` path component.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"benchmark_control: refusing path with '..' traversal: {raw!r}"
        )
    return p


# ---------------------------------------------------------------------------
# §2.1 Naming — sibling_name / next_index
# ---------------------------------------------------------------------------


def sibling_name(base: str, n: int) -> str:
    """Return the canonical benchmark copy name ``<base>-katabenchmark<N>``.

    Args:
        base: The base project name (the immutable reference directory's name).
        n:    The run index (>= 0).

    Returns:
        The string ``f"{base}-katabenchmark{n}"``.
    """
    return f"{base}{_SUFFIX}{n}"


def next_index(parent_dir: str | Path, base: str) -> int:
    """Return the next free N for ``<base>-katabenchmark<N>`` siblings.

    Scans *parent_dir* for entries whose name starts with ``<base>-katabenchmark``
    and ends in a non-negative integer, finds the maximum existing N, and returns
    ``max_N + 1`` (or ``1`` if no siblings exist yet).

    Args:
        parent_dir: The directory that contains (or will contain) the siblings.
        base:       The base project name (matches the reference directory's name).

    Returns:
        The smallest integer > every existing ``<base>-katabenchmark<N>`` index,
        starting at 1 when no siblings are present.
    """
    parent = _guard_path(parent_dir).resolve()
    prefix = f"{base}{_SUFFIX}"
    max_n = 0
    if parent.is_dir():
        for entry in parent.iterdir():
            name = entry.name
            if name.startswith(prefix):
                tail = name[len(prefix):]
                if tail.isdigit():
                    max_n = max(max_n, int(tail))
    return max_n + 1


# ---------------------------------------------------------------------------
# §2.2 Content-hash pin — content_hash / detect_drift
# ---------------------------------------------------------------------------


def content_hash(ref_dir: str | Path) -> str:
    """Return a stable SHA-256 hex digest over the sorted file set of *ref_dir*.

    Determinism guarantee: files are sorted by their relative POSIX path string
    before hashing.  For each file, the UTF-8-encoded relative path is fed into
    the digest before the raw file bytes, so a rename (same bytes, different path)
    produces a different hash.

    Collision-safety (D98 fix): each path and each file body is length-prefixed
    using netstring style (``<len>:<data>``) so that different (path, bytes)
    partitions producing the same naive concatenation cannot collide.  Without
    this prefix, a file named ``ab`` containing ``b'c'`` and a file named ``a``
    containing ``b'bc'`` both stream ``abc`` → identical digest, defeating the
    detect_drift integrity anchor (DESIGN §4 / repeat_from guarantee).

    Args:
        ref_dir: The directory to fingerprint (must exist and be a directory).

    Returns:
        A 64-character lowercase hex string (SHA-256 digest).
    """
    root = _guard_path(ref_dir).resolve()
    h = hashlib.sha256()
    files = sorted(
        (p for p in root.rglob("*") if p.is_file()),
        key=lambda p: p.relative_to(root).as_posix(),
    )
    for f in files:
        rel = f.relative_to(root).as_posix()
        rel_bytes = rel.encode("utf-8")
        data = f.read_bytes()
        h.update(f"{len(rel_bytes)}:".encode())
        h.update(rel_bytes)
        h.update(f"{len(data)}:".encode())
        h.update(data)
    return h.hexdigest()


def detect_drift(ref_dir: str | Path, pinned_hash: str) -> dict:
    """Detect whether *ref_dir* has changed since *pinned_hash* was recorded.

    Computes the current ``content_hash`` of *ref_dir* and compares it to the
    hash that was pinned at benchmark-definition time.  A mismatch means the
    immutable reference was mutated — a protocol violation that must be surfaced
    to the operator (DESIGN §2.1).

    Args:
        ref_dir:     The immutable reference directory to check.
        pinned_hash: The SHA-256 hex digest recorded when the benchmark was defined.

    Returns:
        ``{"drifted": bool, "current_hash": str, "pinned_hash": str}`` where
        ``drifted`` is ``True`` iff the current hash differs from *pinned_hash*.
    """
    current = content_hash(ref_dir)
    drifted = current != pinned_hash
    return {"drifted": drifted, "current_hash": current, "pinned_hash": pinned_hash}


# ---------------------------------------------------------------------------
# §2.2 Clone primitive — clone_control (shutil.copytree; no subprocess)
# ---------------------------------------------------------------------------


def clone_control(
    ref_dir: str | Path,
    dest: str | Path,
    *,
    copy_fn: Union[Callable[[Path, Path], None], None] = None,
) -> Path:
    """Clone the immutable reference into *dest* using ``shutil.copytree``.

    The reference directory is **never written or mutated** by this function
    (DESIGN §2.1: "The original is never mutated.  It is the control.").

    Guards applied (mirrors ``copy_project`` in ``kata_install.py``):
    - CWE-23: ``..`` components in either path are rejected before resolution.
    - Overlap: *dest* equal to *ref_dir*, *dest* inside *ref_dir* (an rmtree
      would destroy the source!), or *ref_dir* inside *dest* — all refused.
      The overlap check uses ``Path.parents`` on resolved absolute paths.

    Args:
        ref_dir: The immutable reference directory (source; never written).
        dest:    The destination path.  Must not overlap *ref_dir*.
        copy_fn: Injectable copy function (default: ``shutil.copytree``).
                 Called as ``copy_fn(src: Path, dst: Path)``.  Exists so
                 tests can inject a spy without touching the real FS.

    Returns:
        The resolved *dest* ``Path``.

    Raises:
        ValueError: on ``..`` traversal in either path, or source/dest overlap.
    """
    s = _guard_path(ref_dir).resolve()
    d = _guard_path(dest).resolve()
    # Overlap guard: equal, dest-is-ancestor-of-source, or source-is-ancestor-of-dest.
    # Mirrors kata_install.copy_project's resolved-overlap check.
    if s == d or d in s.parents or s in d.parents:
        raise ValueError(
            f"benchmark_control.clone_control: source and destination overlap "
            f"(equal or ancestor/descendant): {s} <-> {d}"
        )
    if copy_fn is None:
        shutil.copytree(s, d)
    else:
        copy_fn(s, d)
    return d


# ---------------------------------------------------------------------------
# §2.1 / R4 Prune convenience — prune (shutil.rmtree; no subprocess)
# ---------------------------------------------------------------------------


def prune(
    copy_dir: str | Path,
    *,
    rm_fn: Union[Callable[[Path], None], None] = None,
) -> None:
    """Remove a spawned ``*-katabenchmark<N>`` benchmark copy (R4 convenience).

    Guards (defense-in-depth so this can never delete arbitrary directories):
    - CWE-23: ``..`` in path is rejected before resolution.
    - Naming: the basename must contain ``-katabenchmark`` AND the suffix after
      it must be a non-empty decimal integer string.
    - Existence: the resolved path must be an existing directory.

    Args:
        copy_dir: Path to a benchmark copy directory to remove.  Must match
                  the ``*-katabenchmark<N>`` naming convention.
        rm_fn:    Injectable remove function (default: ``shutil.rmtree``).
                  Called as ``rm_fn(path: Path)``.

    Raises:
        ValueError: on ``..`` traversal, non-benchmark name, non-digit suffix,
                    or non-existent directory.
    """
    p = _guard_path(copy_dir).resolve()
    name = p.name
    # Naming guard — must contain the sentinel suffix
    if _SUFFIX not in name:
        raise ValueError(
            f"benchmark_control.prune: refusing to prune '{name}' — "
            f"not a benchmark copy (name does not contain '{_SUFFIX}')"
        )
    # The part after the last -katabenchmark must be a non-empty digit string
    tail = name.rsplit(_SUFFIX, 1)[-1]
    if not tail or not tail.isdigit():
        raise ValueError(
            f"benchmark_control.prune: refusing to prune '{name}' — "
            f"suffix after '{_SUFFIX}' is not a decimal integer: {tail!r}"
        )
    # Resolved-path existence check
    if not p.is_dir():
        raise ValueError(
            f"benchmark_control.prune: path is not an existing directory: {p}"
        )
    if rm_fn is None:
        shutil.rmtree(p)
    else:
        rm_fn(p)
