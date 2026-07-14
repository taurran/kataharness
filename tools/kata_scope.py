"""tools/kata_scope.py — the ONE definition of "am I in a kata scope?".

Shared kata-scope helper (D160 / EV-1 accepted at the 2026-07-12c live ELEVATE; home moved
to ``tools/`` core by the statusline-scope-unify item U1). This module is the SINGLE physical
home of the bounded-upward-walk that answers "is this cwd inside a kata run?" — the
behavior-identical extraction of the walk that used to live only inside
``adapters/claude/hooks/kata-gauge-check.py._is_kata_scope`` (freeze-gate F-3). It lives in
``tools/`` because the core renderer is now a consumer and core MUST NOT import adapter code;
the module is pure stdlib, so it is core-legal. THREE consumers import from here — the
UserPromptSubmit gauge hook (``adapters/claude/hooks/kata-gauge-check.py``), the
``adapters/claude/statusline_chain.py`` chain wrapper, and the core renderer
(``tools/kata_statusline.statusline_from_event``) — plus the drift tests
(``tools/tests/test_kata_scope.py`` and ``tools/tests/test_statusline_chain.py``) that pin
every call site to this helper so the definition is never copied (the D2 edge-(a) "ONE
definition, never two" made structural rather than review-enforced).

Pure stdlib, no third-party imports, no subprocess. The walk semantics are identical to the
former gauge-hook helper: an ancestor carrying a ``.kata/`` directory OR a ``kata.config``
file, a bounded number of directory checks, a filesystem-root stop, and an OSError-⇒-None
fail-soft posture (a scope check must never raise into a statusline tick or a hook turn).

Public surface:
    find_kata_root(start, *, max_levels=10) -> Path | None
        The ONE bounded upward walk. Returns the first ancestor (at or above *start*)
        carrying kata-run evidence, or None.
    is_kata_scope(start, *, max_levels=10) -> bool
        ``find_kata_root(...) is not None`` — one signature everywhere (v2-F5, the kwarg is
        forwarded).
    resolve_start(payload) -> Path | None
        The ONE payload→start-path resolution: ``cwd`` first, ``workspace.current_dir``
        fallback (the repo-wide convention, pinned by test_kata_statusline "cwd wins");
        non-string/empty ⇒ None (NO ``os.getcwd()`` fallback here — that posture belongs to
        the hook caller, never to a replace-decision). Normalization lives here too (v2-F2):
        the returned path is ``.resolve()``d; a resolution OSError ⇒ None.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

#: Kata-scope upward-walk bound (F-3): *start* + ancestors, capped at this many directory
#: checks; the walk also stops early at the filesystem root. Moved here from the gauge hook
#: (EV-1) so the single owner of the walk owns the single owner of the cap.
_SCOPE_WALK_CAP = 10


def find_kata_root(start: Path, *, max_levels: int = _SCOPE_WALK_CAP) -> Optional[Path]:
    """Return the first ancestor at/above *start* carrying kata-run evidence, or None.

    Kata-run evidence is a ``.kata/`` directory OR a ``kata.config`` file. The walk checks
    *start* and its ancestors, at most *max_levels* directories, and stops early at the
    filesystem root (a directory whose parent is itself). Any OS error while probing a
    directory ⇒ None (silent fail-soft — a scope check never raises).

    This is the ONE bounded upward walk repo-wide (D160/EV-1). ``is_kata_scope`` and all
    three consumers (the gauge hook, the chain wrapper, the core renderer) route through it.
    """
    current = start
    for _ in range(max_levels):
        try:
            if (current / ".kata").is_dir() or (current / "kata.config").is_file():
                return current
        except OSError:
            return None
        parent = current.parent
        if parent == current:  # filesystem root reached
            return None
        current = parent
    return None


def is_kata_scope(start: Path, *, max_levels: int = _SCOPE_WALK_CAP) -> bool:
    """True iff kata-run evidence exists at/above *start* (``find_kata_root`` is not None).

    One signature everywhere (v2-F5): *max_levels* is forwarded verbatim to
    :func:`find_kata_root`, so callers never see two walk caps.
    """
    return find_kata_root(start, max_levels=max_levels) is not None


def resolve_start(payload: Any) -> Optional[Path]:
    """Resolve the start path from a statusLine/hook payload, or None.

    Precedence (the repo-wide convention, pinned by ``test_kata_statusline`` "cwd wins"):
    ``payload["cwd"]`` first, then ``payload["workspace"]["current_dir"]``. A non-string or
    empty value at both slots ⇒ None — there is deliberately NO ``os.getcwd()`` fallback
    here: an absent cwd must never let a replace-decision (the chain wrapper's kata leg)
    silently adopt the process cwd. The hook caller wraps this helper's None with its own
    getcwd posture (S3); this helper stays posture-free.

    Normalization (v2-F2): the returned path is ``.resolve()``d so the downstream walk sees
    a canonical absolute path. A resolution OSError ⇒ None (fail-soft — never raise).
    """
    if not isinstance(payload, dict):
        return None

    raw = payload.get("cwd")
    if not (isinstance(raw, str) and raw):
        workspace = payload.get("workspace")
        raw = workspace.get("current_dir") if isinstance(workspace, dict) else None
    if not (isinstance(raw, str) and raw):
        return None

    try:
        return Path(raw).resolve()
    except (OSError, ValueError):
        # ValueError: e.g. a null byte in the path on POSIX — the "never raise"
        # contract must hold for future consumers too (sweep finding 4).
        return None
