"""intent_scaffold.py — deterministic INTENT.md builder for KataHarness.

COMPOSES the gathered-answers dict (from the kata-initiate interview) into
a schema-conformant INTENT.md artifact per ``protocol/intent.md``.

Public API
----------
build_intent(answers: dict) -> str
    Pure function — no file I/O. Returns the complete INTENT.md text
    (YAML frontmatter + north-star body).  Validates required keys;
    raises ``ValueError`` (fail-closed) on missing/invalid ``kind``,
    ``target.kind``, or ``grillDepth``.

write_intent(path: str, answers: dict) -> None
    Thin wrapper: ``..``-guard on ``path`` (mirrors gate_emit._safe_path,
    CWE-23), calls ``build_intent``, writes the file (UTF-8).

Security note: ``write_intent`` accepts an operator-supplied ``path``; the
``..``-guard rejects path-traversal so a crafted argument cannot climb out
of the intended tree.  The pure ``build_intent`` function writes no files.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Allowed values (protocol/intent.md schema — PINNED D88)
# ---------------------------------------------------------------------------

_VALID_KIND = frozenset({"project", "research", "version-up"})
_VALID_TARGET_KIND = frozenset({"self", "existing", "greenfield"})
_VALID_GRILL_DEPTH = frozenset({"skip", "light", "standard", "full"})


# ---------------------------------------------------------------------------
# Public: pure builder
# ---------------------------------------------------------------------------


def build_intent(answers: dict) -> str:  # noqa: C901
    """Build the complete ``INTENT.md`` text from an answers dict.

    Parameters
    ----------
    answers:
        Dict with keys expected by the kata-initiate interview:
        ``kind``, ``goal``, ``fixes``, ``features``, ``modulesAdded``,
        ``changeSummary``, ``target`` (sub-dict with ``kind``, ``path``,
        ``vault``, ``platform``), ``grillDepth``, ``readiness``.

        **Optional field (ADDITIVE — BC):**
        ``acceptanceCriteria`` (``list[str]``) — checkable success criteria
        confirmed in the Phase-2 mirror (step 2g, Slice D).  When absent or
        empty the emitted ``INTENT.md`` is byte-identical to the pre-field
        build (the conditional insert is skipped entirely).

    Returns
    -------
    str
        Full INTENT.md text — YAML frontmatter between ``---`` delimiters
        followed by a north-star body section.

    Raises
    ------
    ValueError
        Fail-closed: raised on missing or invalid ``kind``, ``target.kind``,
        or ``grillDepth``.  A clear message names the offending field.
    """
    # ------------------------------------------------------------------
    # Validate required scalar fields
    # ------------------------------------------------------------------
    if "kind" not in answers:
        raise ValueError(
            "build_intent: 'kind' is required but missing from answers"
        )
    kind: str = answers["kind"]
    if kind not in _VALID_KIND:
        raise ValueError(
            f"build_intent: invalid 'kind' value {kind!r}; "
            f"must be one of {sorted(_VALID_KIND)}"
        )

    if "grillDepth" not in answers:
        raise ValueError(
            "build_intent: 'grillDepth' is required but missing from answers"
        )
    grill_depth: str = answers["grillDepth"]
    if grill_depth not in _VALID_GRILL_DEPTH:
        raise ValueError(
            f"build_intent: invalid 'grillDepth' value {grill_depth!r}; "
            f"must be one of {sorted(_VALID_GRILL_DEPTH)}"
        )

    # ------------------------------------------------------------------
    # Validate target sub-schema
    # ------------------------------------------------------------------
    if "target" not in answers:
        raise ValueError(
            "build_intent: 'target' is required but missing from answers"
        )
    target: dict = answers["target"]
    target_kind: str = target.get("kind", "")
    if target_kind not in _VALID_TARGET_KIND:
        raise ValueError(
            f"build_intent: invalid 'target.kind' value {target_kind!r}; "
            f"must be one of {sorted(_VALID_TARGET_KIND)}"
        )

    # ------------------------------------------------------------------
    # Assemble frontmatter dict (exact field order mirrors protocol/intent.md)
    # ------------------------------------------------------------------
    goal: str = str(answers.get("goal", ""))
    fixes: list[Any] = list(answers.get("fixes", []))
    features: list[Any] = list(answers.get("features", []))
    modules_added: list[Any] = list(answers.get("modulesAdded", []))
    change_summary: str = str(answers.get("changeSummary", ""))
    readiness: str = str(answers.get("readiness", ""))
    # OPTIONAL — Slice D additive field; default to empty list (never raises)
    acceptance_criteria: list[Any] = list(answers.get("acceptanceCriteria", []))

    # Target sub-object
    target_obj: dict = {
        "kind": target_kind,
        "path": target.get("path", ""),
        "vault": target.get("vault", ""),
        "platform": target.get("platform", ""),
    }

    # Build an ordered mapping for the frontmatter
    frontmatter: dict = {
        "kind": kind,
        "goal": goal,
        "fixes": fixes,
        "features": features,
        "modulesAdded": modules_added,
        "changeSummary": change_summary,
        "target": target_obj,
        "grillDepth": grill_depth,
        "readiness": readiness,
    }

    # acceptanceCriteria is OPTIONAL — emitted only when non-empty.
    # BC guarantee: absent or empty ⇒ the frontmatter dict is identical to
    # the pre-Slice-D dict, so yaml.dump produces byte-identical output.
    if acceptance_criteria:
        frontmatter["acceptanceCriteria"] = acceptance_criteria

    # ------------------------------------------------------------------
    # Render YAML frontmatter
    # ------------------------------------------------------------------
    # Use pyyaml's safe dumper; allow_unicode keeps non-ASCII readable.
    # default_flow_style=False forces block style for lists.
    fm_text = yaml.dump(
        frontmatter,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=False,
    )

    # ------------------------------------------------------------------
    # Assemble north-star body
    # ------------------------------------------------------------------
    body = _build_body(kind, goal, change_summary)

    # ------------------------------------------------------------------
    # Compose final text
    # ------------------------------------------------------------------
    return f"---\n{fm_text}---\n\n{body}\n"


# ---------------------------------------------------------------------------
# Public: thin file-writing wrapper
# ---------------------------------------------------------------------------


def write_intent(path: str, answers: dict) -> None:
    """Write the INTENT.md artifact to *path* from the given *answers*.

    Performs a ``..``-traversal guard (CWE-23) on ``path`` before touching
    the filesystem, mirroring ``gate_emit._safe_path``.

    Parameters
    ----------
    path:
        Destination file path (operator-supplied).
    answers:
        Same dict accepted by ``build_intent``.

    Raises
    ------
    ValueError
        If ``path`` contains a ``..`` segment (path-traversal guard).
    ValueError
        Propagated from ``build_intent`` on invalid/missing required fields.
    """
    _safe_path(path)  # raises ValueError on traversal
    content = build_intent(answers)
    dest = Path(path)
    dest.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _safe_path(raw: str) -> Path:
    """Reject path-traversal (CWE-23) in an operator-supplied path.

    Blocks any ``..`` segment — the traversal-escape primitive — so a crafted
    argument cannot climb out of the intended tree.  Mirrors
    ``gate_emit._safe_path`` (both raise ``ValueError`` since the repo-wide
    guard unification, v0.1.0 cluster item 3).
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"intent_scaffold: refusing path with '..' traversal: {raw!r}"
        )
    return p.resolve()


def _build_body(kind: str, goal: str, change_summary: str) -> str:
    """Produce the north-star narrative body for INTENT.md.

    This is the human-readable expansion of ``goal`` that a builder reading
    cold can understand without further context.  It is NOT a plan — it is
    the intent the plan must serve.
    """
    lines = [
        "# North-Star Intent",
        "",
        "## Goal",
        "",
        goal or "(no goal recorded)",
        "",
        "## Change Summary",
        "",
        change_summary or "(no change summary recorded)",
        "",
        "## Notes",
        "",
        f"- **Run kind:** `{kind}`",
        "- This file was frozen by `kata-initiate` at the end of the initiation",
        "  session.  It is the authoritative goal record for this run.",
        "- Do **not** modify this file mid-run.  If a discovery invalidates the",
        "  goal, treat it as an escalation event (`protocol/escalation.md`).",
    ]
    return "\n".join(lines)
