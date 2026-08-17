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
    find_run_marker(start, *, max_levels=10) -> Path | None
        The W8 RUN-MARKER scope check (DESIGN §8 RS-L5). Returns the path of the
        seam-init-written ``<root>/.kata/run-marker.json`` at or above *start*, or None.

RS-L5 extension (wave 8, ``hook-activation``) — why a SECOND question exists here.
``is_kata_scope`` answers *"is this cwd inside a kata project?"* (a ``.kata/`` dir or a
``kata.config`` is enough — a checkout with no run in flight still answers yes). The
fail-closed deny hook needs the strictly narrower question *"is a kata RUN live here?"*,
whose only honest evidence is the marker ``kata_dispatch.run_start`` writes at seam init.
Widening ``is_kata_scope`` to mean that would silently change the gauge hook and the
statusline; adding the narrower predicate beside it keeps each consumer's posture intact.
**There is still exactly ONE walk.** ``find_run_marker`` does not re-implement it and does
not add a second loop anywhere in the tree: it CALLS ``find_kata_root`` and then performs a
single direct existence check on that root's marker. The D2 "ONE definition, never two"
property that motivated this module is therefore not re-broken by the second predicate, and
``test_statusline_chain.TestScopeDrift`` (the AST canary that pins the parent-loop to
``find_kata_root`` and to nothing else) stays green unchanged.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Optional

#: Kata-scope upward-walk bound (F-3): *start* + ancestors, capped at this many directory
#: checks; the walk also stops early at the filesystem root. Moved here from the gauge hook
#: (EV-1) so the single owner of the walk owns the single owner of the cap.
_SCOPE_WALK_CAP = 10

#: The run-state directory name. A LOCAL literal, deliberately: this module is pure stdlib
#: and core-legal precisely because it imports nothing (three consumers, one of them a
#: host-triggered hook), so it must not pull in the seam engine for two strings.
#: ``tools/tests/test_seam_guard.py::test_kata_scope_marker_constants_match_the_engine``
#: pins both against ``kata_dispatch`` — drift is a RED test, not a review duty.
_KATA_DIRNAME = ".kata"
#: Mirror of ``kata_dispatch.RUN_MARKER_FILENAME`` (pinned by the test named above).
RUN_MARKER_FILENAME = "run-marker.json"


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


def find_run_marker(start: Path, *, max_levels: int = _SCOPE_WALK_CAP) -> Optional[Path]:
    """Return the seam-init RUN MARKER at/above *start*, or None (DESIGN §8 RS-L5).

    The marker is ``<root>/.kata/run-marker.json``, written by
    ``kata_dispatch.run_start`` when a run opens. It is the deny hook's ENTIRE scope
    decision: **present ⇒ a kata run is live here ⇒ the hook fails CLOSED; absent ⇒ the
    session is not ours ⇒ the hook allows the call untouched and emits nothing.**

    Deliberately narrower than :func:`find_kata_root`: a checkout carrying ``kata.config``
    but no live run answers None here, so installing the guard globally cannot deny an
    Agent call in a repo that merely *looks* like a kata project.

    **No second walk.** This delegates to :func:`find_kata_root` — the ONE bounded upward
    walk, with its cap, its root-stop and its fail-soft posture — and then does a single
    direct existence check. Nothing here loops.

    STATED EDGE (shadowing): because the delegated walk stops at the FIRST ancestor
    carrying kata evidence, a nested inner directory that has a bare ``.kata/`` or a
    ``kata.config`` but no marker SHADOWS a live run further up, and this returns None.
    That resolves to "allow, untouched" — the same direction as every other scope miss, and
    the same class as the marker-loss edge below. It is not silently permissive: the run's
    own cursor still shows the SPAWN line with no matching DENY/VERDICT at the next
    lineage audit. Naming it here so it is a known residual rather than a surprise.

    **The OSError posture is the hook's ONE fail-open window and is a STATED residual**
    (RS-L5): a marker that cannot be read reads as "not a kata run" and the call proceeds.
    That direction is chosen deliberately — the alternative is denying every tool call in
    every non-kata session on a transient filesystem error. The residual channel is
    post-hoc: a run whose marker vanished mid-flight shows up as missing DENY/lineage at
    the next cursor-lineage audit.
    """
    root = find_kata_root(start, max_levels=max_levels)
    if root is None:
        return None
    marker = root / _KATA_DIRNAME / RUN_MARKER_FILENAME
    try:
        return marker if marker.is_file() else None
    except OSError:
        return None
