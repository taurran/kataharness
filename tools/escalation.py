"""escalation.py — machine-readable escalation + research-finding emitters.

stdlib only.  Fail-closed: every builder validates its inputs and raises
ValueError (or SystemExit for the path-traversal guard) on any violation.

Public API
----------
build_escalation(...)    -> dict   — validates + builds the protocol/escalation.md payload.
write_escalation(...)    -> str    — ..‑guard kata_dir; writes .kata/escalations/<taskId>.json.
build_finding(...)       -> dict   — validates + builds {claim, source, confidence, groundsToPlan}.

Security
--------
write_escalation rejects any kata_dir containing a '..' segment (CWE-23, mirroring
gate_emit._safe_path).  Only the path-traversal guard raises SystemExit; all other
validation raises ValueError so callers can catch it specifically.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

# ---------------------------------------------------------------------------
# Constants — enum-equivalent sets (keep in sync with protocol/escalation.md)
# ---------------------------------------------------------------------------

_VALID_KINDS = frozenset({
    "orchestrator-resolvable",
    "research-needed",
    "human-required",
})

_VALID_STATUSES = frozenset({"open", "resolved"})

_VALID_CONFIDENCES = frozenset({"HIGH", "MED", "LOW"})

_VALID_GROUNDS_TO_PLAN = frozenset({"YES", "NO", "PARTIAL"})


# ---------------------------------------------------------------------------
# build_escalation
# ---------------------------------------------------------------------------


def build_escalation(
    taskId: Optional[str] = None,
    kind: Optional[str] = None,
    decisionNeeded: Optional[str] = None,
    optionsConsidered: Optional[List[str]] = None,
    agentRecommendation: Optional[str] = None,
    rationale: Optional[str] = None,
    *,
    lockedDecisionInTension: Optional[str] = None,
    costOfWaiting: Optional[str] = None,
    costOfProceeding: Optional[str] = None,
    status: str = "open",
    resolution: Optional[str] = None,
) -> dict:
    """Validate inputs and build the protocol/escalation.md payload dict.

    Parameters
    ----------
    taskId:
        REQUIRED — the task identifier this escalation belongs to.
    kind:
        REQUIRED — one of ``"orchestrator-resolvable"``, ``"research-needed"``,
        ``"human-required"``.
    decisionNeeded:
        REQUIRED — clear statement of the decision that must be made.
    optionsConsidered:
        REQUIRED — non-empty list of options the worker evaluated.
    agentRecommendation:
        REQUIRED — the worker's recommended option with reasoning.
    rationale:
        REQUIRED — why the worker cannot proceed without resolution.
    lockedDecisionInTension:
        OPTIONAL — any locked decision that conflicts with the current situation.
    costOfWaiting:
        OPTIONAL — cost/impact of blocking on resolution.
    costOfProceeding:
        OPTIONAL — cost/impact of proceeding without resolution.
    status:
        REQUIRED — ``"open"`` (default) or ``"resolved"``.
    resolution:
        OPTIONAL — written by the resolver when status becomes ``"resolved"``.

    Returns
    -------
    dict matching the protocol/escalation.md schema.

    Raises
    ------
    ValueError
        On any missing/empty required field, invalid enum value, or empty list.
    """
    # --- Required string fields (non-empty) ---
    _require_non_empty_str("taskId", taskId)
    _require_non_empty_str("decisionNeeded", decisionNeeded)
    _require_non_empty_str("agentRecommendation", agentRecommendation)
    _require_non_empty_str("rationale", rationale)

    # --- kind enum ---
    if not isinstance(kind, str) or not kind:
        raise ValueError(f"build_escalation: 'kind' is required and must be a non-empty string; got {kind!r}")
    if kind not in _VALID_KINDS:
        raise ValueError(
            f"build_escalation: invalid kind {kind!r}; must be one of {sorted(_VALID_KINDS)}"
        )

    # --- status enum ---
    if not isinstance(status, str) or not status:
        raise ValueError(f"build_escalation: 'status' is required; got {status!r}")
    if status not in _VALID_STATUSES:
        raise ValueError(
            f"build_escalation: invalid status {status!r}; must be one of {sorted(_VALID_STATUSES)}"
        )

    # --- optionsConsidered: must be a non-empty list ---
    if not isinstance(optionsConsidered, list):
        raise ValueError(
            f"build_escalation: 'optionsConsidered' must be a list; got {type(optionsConsidered).__name__}"
        )
    if len(optionsConsidered) == 0:
        raise ValueError("build_escalation: 'optionsConsidered' must be a non-empty list")

    # --- Build the payload (all fields per schema) ---
    payload: dict = {
        "taskId": taskId,
        "kind": kind,
        "decisionNeeded": decisionNeeded,
        "optionsConsidered": optionsConsidered,
        "agentRecommendation": agentRecommendation,
        "rationale": rationale,
        "status": status,
    }

    # Optional fields — include when provided (even if None, include so round-trip is lossless)
    payload["lockedDecisionInTension"] = lockedDecisionInTension
    payload["costOfWaiting"] = costOfWaiting
    payload["costOfProceeding"] = costOfProceeding
    payload["resolution"] = resolution

    return payload


# ---------------------------------------------------------------------------
# write_escalation
# ---------------------------------------------------------------------------


def write_escalation(kata_dir: str, payload: dict) -> str:
    """Write the escalation payload to ``<kata_dir>/escalations/<taskId>.json``.

    Mirrors gate_emit._safe_path: rejects any ``kata_dir`` containing a ``..``
    segment (CWE-23) by raising SystemExit.  All other errors raise ValueError.

    Parameters
    ----------
    kata_dir:
        Operator-supplied root directory (e.g. ``.kata``).  Must not contain
        ``..`` path segments.
    payload:
        A dict produced by :func:`build_escalation`.

    Returns
    -------
    str — the absolute path of the written file.

    Raises
    ------
    SystemExit
        If ``kata_dir`` contains a ``..`` segment.
    """
    _safe_kata_dir(kata_dir)

    root = Path(kata_dir)
    escalations_dir = root / "escalations"
    escalations_dir.mkdir(parents=True, exist_ok=True)

    task_id = payload["taskId"]
    out_path = escalations_dir / f"{task_id}.json"
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(out_path)


# ---------------------------------------------------------------------------
# build_finding
# ---------------------------------------------------------------------------


def build_finding(
    claim: str,
    source: str,
    confidence: str,
    grounds_to_plan: str,
) -> dict:
    """Validate inputs and build a research finding dict.

    An ungrounded claim is not a finding — ``source`` is mandatory and must be
    non-empty.  All enum values are case-sensitive.

    Parameters
    ----------
    claim:
        The specific, actionable answer to the research gap.  Must be non-empty.
    source:
        Citation grounding the claim (file+line, URL, doc).  Mandatory and
        non-empty — an ungrounded claim is not a finding.
    confidence:
        One of ``"HIGH"``, ``"MED"``, ``"LOW"`` (case-sensitive).
    grounds_to_plan:
        One of ``"YES"``, ``"NO"``, ``"PARTIAL"`` (case-sensitive).

    Returns
    -------
    dict with keys ``claim``, ``source``, ``confidence``, ``groundsToPlan``.

    Raises
    ------
    ValueError
        On empty/missing claim or source, or invalid enum value.
    """
    _require_non_empty_str("claim", claim)

    # source is mandatory — ungrounded claim is not a finding
    if source is None:
        raise ValueError("build_finding: 'source' is required; an ungrounded claim is not a finding")
    if not isinstance(source, str) or not source.strip():
        raise ValueError(
            "build_finding: 'source' must be a non-empty string; an ungrounded claim is not a finding"
        )

    if confidence not in _VALID_CONFIDENCES:
        raise ValueError(
            f"build_finding: invalid confidence {confidence!r}; must be one of {sorted(_VALID_CONFIDENCES)}"
        )

    if grounds_to_plan not in _VALID_GROUNDS_TO_PLAN:
        raise ValueError(
            f"build_finding: invalid grounds_to_plan {grounds_to_plan!r}; "
            f"must be one of {sorted(_VALID_GROUNDS_TO_PLAN)}"
        )

    return {
        "claim": claim,
        "source": source,
        "confidence": confidence,
        "groundsToPlan": grounds_to_plan,
    }


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _require_non_empty_str(field: str, value: object) -> None:
    """Raise ValueError if value is not a non-empty string."""
    if not isinstance(value, str) or not value:
        raise ValueError(
            f"build_escalation: '{field}' is required and must be a non-empty string; got {value!r}"
        )


def _safe_kata_dir(raw: str) -> Path:
    """Reject path-traversal (CWE-23) in operator-supplied kata_dir.

    Blocks any ``..`` segment — the traversal-escape primitive — so a crafted
    argument cannot climb out of the intended tree.  Mirrors gate_emit._safe_path.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise SystemExit(
            f"escalation: refusing kata_dir with '..' traversal: {raw!r}"
        )
    return p.resolve()
