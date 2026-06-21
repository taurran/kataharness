"""grounding_gate.py — deterministic GROUND/REJECT/ESCALATE verdict emitter (S3a-2).

Maps a kata-research finding to a verdict per the kata-evaluate injected-knowledge
grounding rules and writes ``.kata/grounding.json``.

Stdlib only.  Called by the orchestrator post-evaluation to persist the artifact;
the kata-evaluate skill itself remains no-write (it never imports this module).

Public API
----------
grounding_verdict(finding, source_supports, locked_conflict) -> str
    Return "GROUND", "REJECT", or "ESCALATE".

build_verdict(finding, source_supports, locked_conflict, evidence) -> dict
    Return {finding, verdict, evidence}.

write_grounding(kata_dir, verdicts) -> str
    Write <kata_dir>/grounding.json and return the path.

Security note (CWE-23): ``kata_dir`` is operator-supplied.  ``_safe_path`` blocks
any ``..`` segment before reaching the filesystem sink — mirrors gate_emit._safe_path.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List


# ---------------------------------------------------------------------------
# Path-traversal guard (mirrors gate_emit._safe_path)
# ---------------------------------------------------------------------------


def _safe_path(raw: str) -> Path:
    """Reject path-traversal (CWE-23) in an operator-supplied path, then resolve.

    Blocks any ``..`` segment — the traversal-escape primitive — so a crafted
    argument cannot climb out of the intended tree, while still allowing the
    absolute and nested-relative paths the operator legitimately targets.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise SystemExit(
            f"grounding_gate: refusing path with '..' traversal: {raw!r}"
        )
    return p.resolve()


# ---------------------------------------------------------------------------
# Core verdict logic
# ---------------------------------------------------------------------------


def grounding_verdict(
    finding: dict,
    source_supports: bool,
    locked_conflict: bool,
) -> str:
    """Derive the deterministic grounding verdict for a single finding.

    Rules (per kata-evaluate injected-knowledge grounding mode):

    1. ``locked_conflict`` OR ``finding["groundsToPlan"] == "NO"``  ⇒ ``"ESCALATE"``
       (LOCKED tension or the finding itself flags a plan conflict — never fold silently).
    2. ``not source_supports``                                       ⇒ ``"REJECT"``
       (source does not actually support the claim — default-FAIL).
    3. Otherwise                                                     ⇒ ``"GROUND"``
       (cited, source-supported, no LOCKED conflict — orchestrator may fold).

    Parameters
    ----------
    finding:
        The kata-research output dict ``{claim, source, confidence, groundsToPlan}``.
    source_supports:
        True if the caller has read the cited source and confirmed it supports the
        claim.  **Never assumed True** — default-FAIL: the caller must assert this.
    locked_conflict:
        True if folding this finding would contradict a LOCKED decision.
    """
    if locked_conflict or finding.get("groundsToPlan") == "NO":
        return "ESCALATE"
    if not source_supports:
        return "REJECT"
    return "GROUND"


# ---------------------------------------------------------------------------
# Verdict builder
# ---------------------------------------------------------------------------


def build_verdict(
    finding: dict,
    source_supports: bool,
    locked_conflict: bool,
    evidence: str,
) -> dict:
    """Build a complete verdict dict for a single finding.

    Parameters
    ----------
    finding:
        The kata-research output dict ``{claim, source, confidence, groundsToPlan}``.
    source_supports:
        Whether the caller confirmed the source supports the claim.
    locked_conflict:
        Whether folding this finding conflicts with a LOCKED decision.
    evidence:
        Quoted or paraphrased excerpt from the source (or explanation for
        REJECT/ESCALATE) — the auditable trail.

    Returns
    -------
    dict with keys ``finding``, ``verdict``, ``evidence``.
    """
    return {
        "finding": finding,
        "verdict": grounding_verdict(finding, source_supports, locked_conflict),
        "evidence": evidence,
    }


# ---------------------------------------------------------------------------
# Artifact writer
# ---------------------------------------------------------------------------


def write_grounding(kata_dir: str, verdicts: List[dict]) -> str:
    """Write ``<kata_dir>/grounding.json`` and return the absolute path.

    Parameters
    ----------
    kata_dir:
        Operator-supplied path to the ``.kata/`` output directory (or any
        equivalent directory).  Traversal (``..``) is rejected (CWE-23).
    verdicts:
        List of verdict dicts produced by :func:`build_verdict`.

    Returns
    -------
    Absolute path string to the written ``grounding.json``.
    """
    out = _safe_path(kata_dir)
    out.mkdir(parents=True, exist_ok=True)

    payload = {
        "verdicts": verdicts,
        "allGrounded": all(v["verdict"] == "GROUND" for v in verdicts),
    }

    grounding_path = out / "grounding.json"
    grounding_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(grounding_path)
