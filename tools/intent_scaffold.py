"""intent_scaffold.py — deterministic INTENT.md builder for KataHarness.

COMPOSES the gathered-answers dict (from the kata-initiate interview) into
a schema-conformant INTENT.md artifact per ``protocol/intent.md``.

Public API
----------
build_intent(answers: dict, *, freeze: bool = False) -> str
    Pure function — no file I/O. Returns the complete INTENT.md text
    (YAML frontmatter + north-star body).  Validates required keys;
    raises ``ValueError`` (fail-closed) on missing/invalid ``kind``,
    ``target.kind``, or ``grillDepth``.  ``freeze`` is keyword-only and
    NEVER inferred — omitted ⇒ ``status: draft``.

write_intent(path: str, answers: dict, *, freeze: bool = False) -> None
    Thin wrapper: ``..``-guard on ``path`` (mirrors gate_emit._safe_path,
    CWE-23), calls ``build_intent``, writes the file (UTF-8).  Writes
    ``status: frozen`` ONLY when the caller passes ``freeze=True`` by name.

intent_status(intent_path) -> str
    Fail-closed READER of an ``INTENT.md``'s frontmatter ``status:`` field.
    Returns ``"draft"`` / ``"frozen"`` / ``"absent"``; raises on anything
    else.  Mirrors ``kata_restore.plan_status`` (kata_restore.py:347-377)
    verbatim in posture — same first-word parse rule (BL-F01), same
    no-silent-permissive-default law (D45/GB12 + D136).

Security note: ``write_intent`` accepts an operator-supplied ``path``; the
``..``-guard rejects path-traversal so a crafted argument cannot climb out
of the intended tree.  The pure ``build_intent`` function writes no files.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from fs_atomic import atomic_write_text

# ---------------------------------------------------------------------------
# Allowed values (protocol/intent.md schema — PINNED D88)
# ---------------------------------------------------------------------------

_VALID_KIND = frozenset({"project", "research", "version-up"})
_VALID_TARGET_KIND = frozenset({"self", "existing", "greenfield"})
_VALID_GRILL_DEPTH = frozenset({"skip", "light", "standard", "full"})

#: The closed freeze-status enum (additive amendment, R2-H1/R3-L2).  Identical
#: in shape to ``kata_restore._KNOWN_PLAN_STATUSES`` — deliberately, because the
#: seam's ``intent`` governor rung must read the same two-value vocabulary the
#: ``plan`` rung already reads.
_KNOWN_INTENT_STATUSES = frozenset({"draft", "frozen"})

#: YAML frontmatter matcher — same pattern as ``kata_restore._FM_RE``.  Kept
#: local rather than imported: ``kata_restore`` is the restore/dispatch module
#: and pulls in ``subprocess``/git machinery, so importing it here would couple
#: the initiation-side writer to the restore side for one regex.
_FM_RE = re.compile(r"^---[ \t]*\n(.*?)\n---", re.DOTALL)


# ---------------------------------------------------------------------------
# Public: pure builder
# ---------------------------------------------------------------------------


def build_intent(answers: dict, *, freeze: bool = False) -> str:  # noqa: C901
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
        empty the emitted ``INTENT.md`` is identical to a build that omits
        the field entirely (the conditional insert is skipped).
    freeze:
        **Keyword-only, never inferred** (R2-H1/R3-L2).  ``True`` emits
        ``status: frozen``; omitted or ``False`` emits ``status: draft``.
        The argument is deliberately explicit and named: the freeze status is
        the seam's ``intent`` governor rung, and a rung that could be reached
        by inference (a heuristic on the answers dict, a call-site default, a
        "looks complete" guess) would be a silent-permissive default of
        exactly the D136 class the ladder exists to eliminate.  There is no
        code path in this module that writes ``frozen`` without the caller
        naming ``freeze=True``.

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

    # status is ALWAYS emitted (additive amendment, R2-H1/R3-L2) and is
    # appended LAST so every pre-existing key keeps its exact position — the
    # amendment adds a row, it does not reorder the schema.  `frozen` only
    # ever comes from the caller's explicit `freeze=True`.
    frontmatter["status"] = "frozen" if freeze else "draft"

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


def write_intent(path: str, answers: dict, *, freeze: bool = False) -> None:
    """Write the INTENT.md artifact to *path* from the given *answers*.

    Performs a ``..``-traversal guard (CWE-23) on ``path`` before touching
    the filesystem, mirroring ``gate_emit._safe_path``.

    Parameters
    ----------
    path:
        Destination file path (operator-supplied).
    answers:
        Same dict accepted by ``build_intent``.
    freeze:
        **Keyword-only, never inferred.**  Passed straight through to
        :func:`build_intent`.  ``kata-initiate`` names ``freeze=True`` at its
        Phase-6 freeze act and nowhere else; every other write — every
        interview-in-progress save — omits the argument and therefore writes
        ``status: draft``.

    Raises
    ------
    ValueError
        If ``path`` contains a ``..`` segment (path-traversal guard).
    ValueError
        Propagated from ``build_intent`` on invalid/missing required fields.
    """
    _safe_path(path)  # raises ValueError on traversal
    content = build_intent(answers, freeze=freeze)
    dest = Path(path)
    # D159: atomic tmp+os.replace — a concurrent reader never sees a partial file.
    atomic_write_text(dest, content)


# ---------------------------------------------------------------------------
# Public: fail-closed status reader
# ---------------------------------------------------------------------------
#
# The READER half of the freeze field. It lives here — beside the writer that
# produces the field — rather than in the seam, so the two halves of one schema
# row cannot drift apart. The seam's `intent` governor rung (DESIGN §1.4) is a
# CONSUMER of this function, built in W3; this module owns the parse, the seam
# owns the ladder comparison.
#
# Posture is copied from `kata_restore.plan_status` (kata_restore.py:347-377)
# deliberately and verbatim in substance: same first-word parse rule (BL-F01),
# same three-way return, same refusal to coerce an unrecognized value in either
# direction. Two governor rungs that read a `status:` field must not disagree
# about what that field means.


def intent_status(intent_path: str | Path) -> str:
    """Return an ``INTENT.md``'s normalized freeze status from its frontmatter.

    Fail-closed semantics, mirroring :func:`kata_restore.plan_status`
    (``kata_restore.py:347-377``) — D45/GB12 + D136, no silent-permissive
    default:

    - ``status:`` key absent, or present but empty/whitespace-only ⇒ returns
      ``"absent"``.  This is NOT frozen.  An ``INTENT.md`` written before this
      additive amendment carries no ``status:`` field at all and lands here —
      it reads as ``"absent"``, never as a defaulted ``"frozen"`` and never as
      a hard error.  That is the backward-compatibility path: legacy artifacts
      stay readable, and a governor rung requiring ``frozen`` simply is not
      satisfied by one.
    - Otherwise the value is split on whitespace and the FIRST WORD is taken,
      case-folded; trailing prose after that word is ignored.  Same rule and
      same reason as ``plan_status``: an authored value like
      ``status: FROZEN — sealed 2026-08-16 at the Phase-6 gate`` must parse as
      ``"frozen"`` rather than hard-fail, because a status carrying a trailing
      note is a real authoring shape, not garbage.
    - First word ``"draft"`` or ``"frozen"`` ⇒ that lowercase token is returned.
    - Any other first word ⇒ RAISES.  Never coerced to a default in either
      direction — an unrecognized status must not silently pass as frozen NOR
      silently pass as draft; it is a data problem to resolve by hand.

    Returns
    -------
    str
        One of ``"draft"``, ``"frozen"``, or ``"absent"``.

    Raises
    ------
    ValueError
        Unreadable file, missing/invalid YAML frontmatter, or a ``status:``
        first word that is neither "draft" nor "frozen".
    """
    path = Path(intent_path)
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ValueError(
            f"intent_scaffold: cannot read INTENT at {path!s} ({exc}) — refusing to "
            "assume a status. Resolve manually."
        ) from exc

    fm_match = _FM_RE.match(content)
    if not fm_match:
        raise ValueError(
            f"intent_scaffold: INTENT at {path!s} has no YAML frontmatter — cannot "
            "determine its status. Resolve manually."
        )

    try:
        fm = yaml.safe_load(fm_match.group(1)) or {}
    except yaml.YAMLError as exc:
        raise ValueError(
            f"intent_scaffold: INTENT frontmatter at {path!s} is not valid YAML — "
            f"{exc}. Resolve manually."
        ) from exc

    if not isinstance(fm, dict):
        raise ValueError(
            f"intent_scaffold: INTENT frontmatter at {path!s} is not a mapping — "
            "cannot determine its status. Resolve manually."
        )

    raw = fm.get("status")
    if raw is None:
        return "absent"
    raw_str = str(raw).strip()
    if not raw_str:
        return "absent"

    first_word = raw_str.split()[0].casefold()
    if first_word in _KNOWN_INTENT_STATUSES:
        return first_word

    raise ValueError(
        f"intent_scaffold: INTENT at {path!s} has an unrecognized status {raw_str!r} "
        f"(first word {first_word!r} is neither 'draft' nor 'frozen') — refusing to "
        "coerce to a default. Resolve manually."
    )


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
