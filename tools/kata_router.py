"""kata_router.py — AGENTS.md marker-stanza manager (Feature 2, G4).

Manages a single MARKED, idempotent router block in a target project's AGENTS.md.

Stdlib only.  No exec sink.  No network.  No side-effects at import time.

Public API
----------
render_stanza(summary: str = "") -> str
    Return the full stanza string (begin marker + body + end marker).
    Deterministic and byte-stable for identical inputs.
    Body: ~17 Markdown lines covering what's installed, the two entrypoints
    (kata-bootstrap, kata-validate), the four run-state locations
    (.kata/, .planning/, INTENT.md, kata.config), and the CA-L20 standing line
    (a resumed/compacted session re-anchors via .planning/HANDOFF.md first).
    No HTML in the body.

write_stanza(agents_md_path: str | Path, summary: str = "") -> None
    Idempotent UPSERT.
    - File absent       → create it containing only the stanza.
    - File present, no block  → append the stanza (existing content preserved).
    - File present, block exists → replace the block in place (rest byte-identical).
    Re-running always leaves exactly ONE ``<!-- kata:begin -->…<!-- kata:end -->`` block.

remove_stanza(agents_md_path: str | Path) -> None
    Remove exactly the marked block, leaving all other content byte-identical.
    No-op when the block is absent or the file does not exist.

Security note (CWE-23)
-----------------------
Operator-supplied paths are sanitised by ``_safe_path`` before any filesystem
sink is reached.  Mirrors ``kata_board._safe_path`` and
``grounding_gate._safe_path`` — raises ``ValueError`` on traversal.
"""

from __future__ import annotations

from pathlib import Path

# ---------------------------------------------------------------------------
# Marker constants — the idempotency primitive
# ---------------------------------------------------------------------------

BEGIN_MARKER = "<!-- kata:begin -->"
END_MARKER = "<!-- kata:end -->"


# ---------------------------------------------------------------------------
# Path-traversal guard (CWE-23)
# ---------------------------------------------------------------------------


def _safe_path(raw: str | Path) -> Path:
    """Reject path-traversal (CWE-23) in an operator-supplied path, then resolve.

    Blocks any ``..`` segment — the traversal-escape primitive — so a crafted
    argument cannot climb out of the intended tree, while still allowing the
    absolute and nested-relative paths the operator legitimately targets.

    Raises ``ValueError`` on violation (mirrors ``kata_board._safe_path`` and
    ``grounding_gate._safe_path``).
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"kata_router: refusing path with '..' traversal: {raw!r}"
        )
    return p.resolve()


# ---------------------------------------------------------------------------
# Stanza body (deterministic template; `{home}` = the harness home back-pointer)
# ---------------------------------------------------------------------------

#: Default harness-home back-pointer (CG-L4). The literal `~`-form is the BC
#: pin: rendering with this default is byte-identical to the pre-`home`-param
#: stanza's prime-directives line — existing call sites keep today's bytes.
DEFAULT_HOME = "~/.kata-home"

_STANZA_BODY = """\
## KataHarness

KataHarness is installed in this project.

**Prime Directives** (loaded every run — `{home}/protocol/prime-directives.md`): never silently defer/stub/skip designed work (ask first); absolute truthfulness — a stub reported as built is drift.

**Entrypoints**
- `/kata-start` — begin a kata run (kata-initiate, the canonical front door; `kata-bootstrap` is the pre-loop configurator)
- `kata-validate`  — adversarially validate a payload or an agent's output

**Run state**
- `.kata/`      — live board, task state, grounding
- `.planning/`  — frozen plans and specs
- `INTENT.md`   — the locked run intent
- `kata.config` — harness configuration

a resumed/compacted session re-anchors via `.planning/HANDOFF.md` + the staleness rule before doing anything else. (Universal fallback for platforms with no hook — §5.)

_Managed by KataHarness._"""
# Body: the ~15-line instruction budget + the CA-L20 resume/compact re-anchor line
# (universal fallback for platforms with no SessionStart hook — DESIGN CA-L20 / §4 row 8)
# + the standing Prime Directives reminder (loaded on every execution, 2026-07-12).
# CG-L4 (2026-07-12): the prime-directives back-pointer is templated via `{home}`
# (custom KATA_HOME installs render their real home); the start verb is
# `/kata-start` (kata-initiate, the canonical front door) with kata-bootstrap
# named as the pre-loop configurator.


def _render_home(home: str | Path) -> str:
    """Render *home* for embedding in the stanza: forward slashes only.

    The default ``~/.kata-home`` passes through unchanged (the `~`-form is
    preserved — BC pin); a Windows path like ``C:\\kata\\home`` renders as
    ``C:/kata/home``. Pure text templating — no filesystem sink, no resolve.
    """
    return str(home).replace("\\", "/")


# ---------------------------------------------------------------------------
# Stanza renderer
# ---------------------------------------------------------------------------


def render_stanza(summary: str = "", home: str | Path = DEFAULT_HOME) -> str:
    """Return the full router stanza string including begin/end markers.

    Deterministic and byte-stable for identical inputs.  The body (between the
    markers) contains ~17 Markdown lines: a project pointer, the entrypoints
    (``/kata-start`` — kata-initiate, the canonical front door, with
    ``kata-bootstrap`` as the pre-loop configurator — and ``kata-validate``),
    the four run-state locations (``.kata/``, ``.planning/``, ``INTENT.md``,
    ``kata.config``), and the CA-L20 standing line (resume/compact sessions
    re-anchor via ``.planning/HANDOFF.md`` before doing anything else — the
    universal fallback for hook-less platforms).  No HTML tags appear in the body.

    Parameters
    ----------
    summary:
        Optional one-line install summary appended below the project pointer.
        An empty string (the default) omits the line — output is byte-identical
        to previous calls with no summary (BC guarantee).
    home:
        The harness-home back-pointer templated into the Prime Directives line
        (CG-L4). Rendered with forward slashes. The default ``~/.kata-home``
        preserves the pre-param bytes (BC guarantee) — pass the real
        ``KATA_HOME`` for custom-home installs.
    """
    body = _STANZA_BODY.format(home=_render_home(home))
    if summary:
        # Insert the summary line after the blank line that follows the header,
        # keeping the body within the ~15-line budget for short summaries.
        body_lines = body.splitlines()
        # "## KataHarness" is index 0, blank is index 1 — insert after blank
        body_lines.insert(2, summary)
        body = "\n".join(body_lines)
    return f"{BEGIN_MARKER}\n{body}\n{END_MARKER}"


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _has_orphan_begin(lines: list[str]) -> bool:
    """Return True when a BEGIN_MARKER exists with no subsequent END_MARKER.

    Distinguishes a well-formed ``BEGIN…END`` pair (returns False) from a
    lone, hand-typed ``BEGIN`` that was never closed (returns True).  Only
    the first ``BEGIN`` occurrence is considered — callers should resolve any
    data-loss risk before proceeding.
    """
    found_begin = False
    for line in lines:
        stripped = line.rstrip("\n\r")
        if stripped == BEGIN_MARKER and not found_begin:
            found_begin = True
        elif stripped == END_MARKER and found_begin:
            return False  # complete begin…end pair
    return found_begin


def _find_block(lines: list[str]) -> tuple[int | None, int | None]:
    """Scan *lines* (from ``splitlines(keepends=True)``) for the kata block.

    Returns ``(begin_idx, end_idx)`` — both inclusive — or ``(None, None)``
    when no complete block is found.  A ``BEGIN_MARKER`` line without a
    subsequent ``END_MARKER`` line is treated as incomplete (no match).
    """
    begin_idx: int | None = None
    end_idx: int | None = None
    for i, line in enumerate(lines):
        stripped = line.rstrip("\n\r")
        if stripped == BEGIN_MARKER and begin_idx is None:
            begin_idx = i
        elif stripped == END_MARKER and begin_idx is not None and end_idx is None:
            end_idx = i
            break
    if begin_idx is None or end_idx is None:
        return None, None
    return begin_idx, end_idx


def _upsert_stanza(original: str, stanza: str) -> str:
    """Return *original* with the kata block replaced or appended.

    If a complete ``BEGIN_MARKER…END_MARKER`` span exists it is replaced
    in-place (surrounding lines are byte-identical).  If no span exists the
    stanza is appended with at most one leading newline separator.
    """
    lines = original.splitlines(keepends=True)
    begin_idx, end_idx = _find_block(lines)

    if begin_idx is None:
        # Append — ensure exactly one newline separator before the stanza.
        sep = "\n" if original and not original.endswith("\n") else ""
        return original + sep + stanza + "\n"

    # Replace begin_idx..end_idx (inclusive) with the new stanza.
    new_lines = lines[:begin_idx] + [stanza + "\n"] + lines[end_idx + 1 :]
    return "".join(new_lines)


def _strip_stanza(content: str) -> str:
    """Return *content* with the kata block removed.

    Finds the first complete ``BEGIN_MARKER…END_MARKER`` span and removes the
    entire span (inclusive).  All surrounding content is preserved byte-for-byte.
    No-op if no complete block is found.
    """
    lines = content.splitlines(keepends=True)
    begin_idx, end_idx = _find_block(lines)

    if begin_idx is None:
        return content  # no complete block — no-op

    new_lines = lines[:begin_idx] + lines[end_idx + 1 :]
    return "".join(new_lines)


# ---------------------------------------------------------------------------
# Public writers
# ---------------------------------------------------------------------------


def write_stanza(
    agents_md_path: str | Path,
    summary: str = "",
    home: str | Path = DEFAULT_HOME,
) -> None:
    """Idempotent UPSERT of the KataHarness router stanza into the target AGENTS.md.

    Behaviour:
    - File absent             → create it containing only the stanza.
    - File present, no block  → append the stanza; existing content preserved.
    - File present, block     → replace the block in place; rest byte-identical.

    Re-running always leaves exactly ONE ``<!-- kata:begin -->…<!-- kata:end -->`` block.

    Parameters
    ----------
    agents_md_path:
        Path to the target project's AGENTS.md.  Must not contain ``..``.
    summary:
        Optional one-line install summary forwarded to :func:`render_stanza`.
    home:
        Harness-home back-pointer forwarded to :func:`render_stanza` (CG-L4).
        Default ``~/.kata-home`` preserves existing call sites' bytes (BC).
    """
    path = _safe_path(agents_md_path)
    stanza = render_stanza(summary, home=home)

    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(stanza + "\n", encoding="utf-8")
        return

    original = path.read_text(encoding="utf-8")
    lines = original.splitlines(keepends=True)
    if _has_orphan_begin(lines):
        raise ValueError(
            f"malformed KataHarness marker block in {path}; fix manually"
        )
    updated = _upsert_stanza(original, stanza)
    path.write_text(updated, encoding="utf-8")


def remove_stanza(agents_md_path: str | Path) -> None:
    """Remove exactly the KataHarness marker block from AGENTS.md.

    Preserves all content outside the ``<!-- kata:begin -->…<!-- kata:end -->``
    span byte-for-byte.  No-op when the block is absent or the file does not
    exist — never raises, never creates a file.

    Parameters
    ----------
    agents_md_path:
        Path to the target project's AGENTS.md.  Must not contain ``..``.
    """
    path = _safe_path(agents_md_path)
    if not path.exists():
        return
    content = path.read_text(encoding="utf-8")
    updated = _strip_stanza(content)
    if updated != content:
        path.write_text(updated, encoding="utf-8")
