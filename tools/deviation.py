"""deviation.py — Deviation-discovery pipeline engine for KataHarness debug mode.

This module is the deterministic engine for the LD4 deviation-discovery funnel and
LD5 confidence/routing.  It is PURE decision logic over signal dicts — no subprocess,
no eval, no exec.

FM evaluation is the skill's job via the already-safe ``function_model.evaluate_spec``.
This module consumes pre-gathered signal records as plain dicts and returns routed
verdicts.

Public surfaces
---------------
DEFAULT_WEIGHTS           dict — TUNABLE LD5 confidence weights (w1/w2/w3)
DEFAULT_THRESHOLDS        dict — TUNABLE routing thresholds (tau_high/tau_low/low_cap)
tally_self_consistency    LD4 step 4 — vote tally (≥2/3 k_min, TUNABLE)
self_consistency_entropy  normalized binary entropy for the (1 − entropy) confidence term
corroboration_gate        LD4 step 5 — HARD gate (LLM-only → human; IRIS pattern)
compute_confidence        LD5 confidence formula C = w1·MSAS + w2·(1−entropy) + w3·Prior
apply_force_low           LD5 sparse-signal cap
route_finding             LD5 routing bands (auto-fix-eligible / research / defer)
run_funnel                pure composition: SC → gate → refute → confidence → route
findings_schema           JSON schema (single source of truth for findings artifact)
emit_findings             JSON write to .kata/deviations/findings.json
load_findings             JSON read from findings artifact

exec-safety (mandatory per protocol/exec-safety.md)
---------------------------------------------------
No subprocess, no eval, no exec is introduced by this module.  It is pure decision
logic over signal dicts.  FM evaluation reuses function_model.evaluate_spec /
function_model._safe_eval (already registered in exec-safety.md).  This module
registers no new execution sink.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# TUNABLE knobs — LD5 (calibratable without re-freeze; DESIGN §4)
# ---------------------------------------------------------------------------

DEFAULT_WEIGHTS: dict[str, float] = {
    "w1": 0.40,   # MSAS (multi-signal agreement score) weight
    "w2": 0.35,   # (1 − self-consistency-entropy) weight
    "w3": 0.25,   # StructuralPrior weight
}
"""TUNABLE confidence weights for the LD5 formula C = w1·MSAS + w2·(1−entropy) + w3·Prior.

Calibrate these without re-freezing the PLAN.  Weights need not sum to 1 —
the result is clamped to [0, 1] — but a unit-sum partition is the natural choice.
"""

DEFAULT_THRESHOLDS: dict[str, float] = {
    "tau_high": 0.72,   # C ≥ tau_high → auto-fix-eligible
    "tau_low":  0.38,   # C ≤ tau_low  → defer   (tau_low < C < tau_high → research)
    "low_cap":  0.35,   # force-LOW cap: sparse-signal modules capped here
}
"""TUNABLE routing thresholds for the LD5 routing bands.

low_cap must be ≤ tau_low so that force-LOW lands a sparse finding in the defer band.
Calibrate without re-freezing the PLAN.
"""


# ---------------------------------------------------------------------------
# LD4 step 4 — self-consistency vote tally
# ---------------------------------------------------------------------------

def tally_self_consistency(votes: list[bool], *, k_min: int = 2) -> dict:
    """Tally LD4 step-4 self-consistency votes and decide if the finding passes.

    The skill samples the LLM ×3 (shuffled/rephrased) and collects boolean
    agreement values.  This function counts the agreements and applies the
    k_min gate.

    Args:
        votes:  Ordered list of boolean agreement values (True = this run
                agrees there is a deviation).  Typically 3 elements (×3 runs).
        k_min:  Minimum number of agreeing runs required to pass (default 2,
                i.e. ≥2/3 of 3 runs; TUNABLE via this parameter — LD4 [TUNABLE]).

    Returns:
        ``{"agree": int, "total": int, "passes": bool}``
        Fail-closed: empty → passes=False; tie resolves to passes=False when
        agree < k_min.

    Note: ``k_min`` is a count gate calibrated for the ×3 sampling; if
    sample-N becomes tunable, make this ratio-aware instead.
    """
    agree = sum(1 for v in votes if v)
    total = len(votes)
    passes = agree >= k_min
    return {"agree": agree, "total": total, "passes": passes}


# ---------------------------------------------------------------------------
# LD5 — normalized binary entropy of the agreement distribution
# ---------------------------------------------------------------------------

def self_consistency_entropy(votes: list[bool]) -> float:
    """Return the normalized binary entropy of the self-consistency vote distribution.

    Entropy is in [0, 1].  Maximum disagreement (p = 0.5) → 1.0; perfect
    consensus (p = 0 or p = 1) → 0.0; empty votes → 0.0.

    This feeds the ``(1 − entropy)`` term in the LD5 confidence formula — higher
    entropy (more disagreement) reduces the confidence contribution of SC.

    Args:
        votes:  List of boolean agreement values.

    Returns:
        Normalized binary entropy in [0.0, 1.0].
    """
    total = len(votes)
    if total == 0:
        return 0.0
    p = sum(1 for v in votes if v) / total
    # Degenerate cases: full consensus → entropy = 0
    if p <= 0.0 or p >= 1.0:
        return 0.0
    # Binary entropy H(p) = -p·log2(p) - (1-p)·log2(1-p), already in [0, 1]
    h = -p * math.log2(p) - (1.0 - p) * math.log2(1.0 - p)
    return min(1.0, max(0.0, h))


# ---------------------------------------------------------------------------
# LD4 step 5 — objective-corroboration HARD gate (false-positive control)
# ---------------------------------------------------------------------------

_OBJECTIVE_SOURCES: frozenset[str] = frozenset(
    {"test", "type", "tool", "snyk", "lint", "fm", "sbfl"}
)
"""Allowlist of objective corroborator ``source`` values for the HARD gate.

Only corroborators whose ``source`` field is a member of this set are counted
toward corroboration.  A corroborator with a missing or unknown ``source`` is
IGNORED — fail-closed, so an absent/unrecognised source can never make a
finding ``auto-fix-eligible``.
"""


def _co_locates(corroborator: dict, llm_finding: dict) -> bool:
    """Return True iff the corroborator is objective AND co-locates with the LLM finding.

    Both conditions must hold (fail-closed):

    1. **Objective source (M-2):** ``corroborator["source"]`` must be in
       ``_OBJECTIVE_SOURCES``.  A missing or unknown source → ``False``.
    2. **Co-location (M-1 / L-3):** both ``module`` values are truthy and equal,
       AND both ``locus`` values are truthy and equal.  ``None == None`` and
       ``"" == ""`` both degenerate to ``True`` under plain equality — this
       predicate uses a truthiness guard so any falsy value (None, "", etc.)
       on either side fails closed.
    """
    # M-2: reject non-objective or missing sources (fail-closed)
    if corroborator.get("source") not in _OBJECTIVE_SOURCES:
        return False
    # M-1 / L-3: require truthy module AND locus on both sides (fail-closed)
    cm, cl = corroborator.get("module"), corroborator.get("locus")
    fm_, fl = llm_finding.get("module"), llm_finding.get("locus")
    return bool(cm) and bool(cl) and cm == fm_ and cl == fl


def corroboration_gate(llm_finding: dict, corroborators: list[dict]) -> dict:
    """Apply the objective-corroboration HARD gate (LD4 step 5, DESIGN §4 IRIS pattern).

    A finding is corroborated iff ≥1 objective corroborator (tool / test / type /
    Snyk) co-locates with the LLM finding (same module AND locus).  An
    uncorroborated finding is LLM-only and is **NEVER** auto-fix-eligible — it is
    routed ``"human"`` here.  This is the load-bearing false-positive control.

    Args:
        llm_finding:   The LLM-produced deviation dict.  Must contain ``"module"``
                       and ``"locus"`` keys for co-location matching.
        corroborators: List of objective-signal dicts from tools / tests / types /
                       Snyk.  Each must contain ``"module"`` and ``"locus"``.

    Returns:
        ``{"corroborated": bool, "route": str | None, "co_located": list[dict]}``
        ``route`` is ``None`` when corroborated (downstream routing decides);
        ``"human"`` when uncorroborated (LLM-only, never auto-fix-eligible).
    """
    co_located: list[dict] = []
    for c in corroborators:
        if _co_locates(c, llm_finding):
            co_located.append(c)
    corroborated = len(co_located) > 0
    route = None if corroborated else "human"
    return {"corroborated": corroborated, "route": route, "co_located": co_located}


# ---------------------------------------------------------------------------
# LD5 — confidence formula
# ---------------------------------------------------------------------------

def compute_confidence(
    msas: float,
    sc_entropy: float,
    structural_prior: float,
    *,
    weights: dict = DEFAULT_WEIGHTS,
) -> float:
    """Compute the LD5 heuristic confidence score (v1 — heuristic only).

    Formula: ``C = w1·MSAS + w2·(1 − sc_entropy) + w3·StructuralPrior``

    All weights are TUNABLE via the ``weights`` argument (default DEFAULT_WEIGHTS).
    Result is clamped to [0, 1].  Formal isotonic calibration is a DESIGN fast-follow
    NOT implemented here.

    Args:
        msas:             Multi-signal agreement score (MSAS) in [0, 1].
                          Higher MSAS = more objective signals agree.
        sc_entropy:       Self-consistency entropy from ``self_consistency_entropy``.
                          ``(1 − sc_entropy)`` → higher entropy lowers confidence.
        structural_prior: Structural-prior signal in [0, 1] (LD5; e.g. call-site
                          density, type-coverage fraction).
        weights:          Weight dict with keys ``w1``, ``w2``, ``w3``.
                          Defaults to DEFAULT_WEIGHTS (TUNABLE).

    Returns:
        Confidence score in [0.0, 1.0].
    """
    w1 = weights["w1"]
    w2 = weights["w2"]
    w3 = weights["w3"]
    c = w1 * msas + w2 * (1.0 - sc_entropy) + w3 * structural_prior
    return min(1.0, max(0.0, c))


# ---------------------------------------------------------------------------
# LD5 — force-LOW for sparse-signal modules
# ---------------------------------------------------------------------------

def apply_force_low(
    confidence: float,
    *,
    sparse_signal: bool,
    low_cap: float = DEFAULT_THRESHOLDS["low_cap"],
) -> float:
    """Cap confidence to the LOW band for sparse-signal modules (LD5 force-LOW).

    When a module has sparse signal coverage (few tests, few callers, no type
    annotations), the formula score is unreliable.  Force-LOW prevents a
    numerically high formula score from promoting a weakly-supported finding to
    ``auto-fix-eligible`` or ``research``.

    Args:
        confidence:    Raw confidence from ``compute_confidence``.
        sparse_signal: True iff the module is sparse-signal (force-LOW applies).
        low_cap:       Maximum confidence allowed when sparse_signal is True.
                       Defaults to DEFAULT_THRESHOLDS["low_cap"] (TUNABLE).
                       Should be ≤ tau_low so the finding lands in the defer band.

    Returns:
        ``min(confidence, low_cap)`` when sparse_signal else ``confidence``.
    """
    if sparse_signal:
        return min(confidence, low_cap)
    return confidence


# ---------------------------------------------------------------------------
# LD5 — routing bands
# ---------------------------------------------------------------------------

def route_finding(confidence: float, *, thresholds: dict = DEFAULT_THRESHOLDS) -> str:
    """Map a confidence score to an LD5 routing band.

    Bands (all thresholds TUNABLE via DEFAULT_THRESHOLDS):
        C ≥ tau_high             → ``"auto-fix-eligible"``
        tau_low < C < tau_high   → ``"research"``
        C ≤ tau_low              → ``"defer"``

    ``"human"`` is never returned by this function — that verdict comes from the
    corroboration gate (``corroboration_gate``) and the refute path in ``run_funnel``.

    Args:
        confidence:  Score in [0, 1] from ``compute_confidence`` (post force-LOW).
        thresholds:  Dict with keys ``tau_high``, ``tau_low`` (and ``low_cap`` —
                     unused here, only by ``apply_force_low``).
                     Defaults to DEFAULT_THRESHOLDS.

    Returns:
        One of ``"auto-fix-eligible"``, ``"research"``, ``"defer"``.
    """
    tau_high = thresholds["tau_high"]
    tau_low = thresholds["tau_low"]
    if confidence >= tau_high:
        return "auto-fix-eligible"
    if confidence > tau_low:
        return "research"
    return "defer"


# ---------------------------------------------------------------------------
# Pure composition — run_funnel
# ---------------------------------------------------------------------------

def run_funnel(finding: dict) -> dict:
    """Pure composition: apply the full LD4/LD5 funnel to a gathered finding.

    Funnel order (invariant — a finding stopped at any gate is NEVER routed
    ``auto-fix-eligible``):

    1. Self-consistency gate  (``tally_self_consistency``)
    2. Objective-corroboration HARD gate  (``corroboration_gate``)
    3. Adversarial-refute resolution  (``refuted`` bool, already resolved by skill)
    4. Confidence formula  (``compute_confidence``)
    5. Force-LOW  (``apply_force_low``)
    6. Routing  (``route_finding``)

    The adversarial-refute step is resolved by the ``kata-deviate`` skill and passed
    in as ``refuted: bool`` so this engine remains deterministic.  If ``refuted=True``
    the finding is contested and routed ``"human"``.

    This function **does not fix anything** — it produces ROUTED findings only.

    Args:
        finding: Dict produced by the ``kata-deviate`` skill.  Expected keys:
            ``module``           str   — module path (for co-location)
            ``locus``            str   — locus within the module (function/block)
            ``votes``            list  — list[bool] from ×3 self-consistency samples
            ``corroborators``    list  — list[dict] of objective-signal dicts
            ``refuted``          bool  — True iff adversarial refute succeeded
            ``msas``             float — multi-signal agreement score
            ``structural_prior`` float — structural-prior signal
            ``sparse_signal``    bool  — True iff the module is sparse-signal

    Returns:
        Routed verdict dict with keys: ``module``, ``locus``, ``sc_tally``,
        ``corroboration``, ``refuted``, ``confidence``, ``sparse_signal``,
        ``route``, ``funnel_stop``.
        ``funnel_stop`` is ``None`` when the funnel ran to completion; otherwise
        the stage name where it stopped early.
    """
    # L-1: coerce present-but-null values to [] so None never causes a TypeError
    votes: list[bool] = finding.get("votes") or []
    corroborators: list[dict] = finding.get("corroborators") or []
    refuted: bool = finding.get("refuted", False)
    msas: float = finding.get("msas", 0.0)
    structural_prior: float = finding.get("structural_prior", 0.0)
    sparse_signal: bool = finding.get("sparse_signal", False)

    # Step 1 — self-consistency gate
    sc_tally = tally_self_consistency(votes)
    if not sc_tally["passes"]:
        return {
            "module": finding.get("module"),
            "locus": finding.get("locus"),
            "sc_tally": sc_tally,
            "corroboration": None,
            "refuted": refuted,
            "confidence": None,
            "sparse_signal": sparse_signal,
            "route": "defer",
            "funnel_stop": "self_consistency",
        }

    # Step 2 — objective-corroboration HARD gate
    corroboration = corroboration_gate(finding, corroborators)
    if not corroboration["corroborated"]:
        return {
            "module": finding.get("module"),
            "locus": finding.get("locus"),
            "sc_tally": sc_tally,
            "corroboration": corroboration,
            "refuted": refuted,
            "confidence": None,
            "sparse_signal": sparse_signal,
            "route": "human",
            "funnel_stop": "corroboration_gate",
        }

    # Step 3 — adversarial-refute resolution (passed in as refuted bool from skill)
    if refuted:
        return {
            "module": finding.get("module"),
            "locus": finding.get("locus"),
            "sc_tally": sc_tally,
            "corroboration": corroboration,
            "refuted": True,
            "confidence": None,
            "sparse_signal": sparse_signal,
            "route": "human",
            "funnel_stop": "refuted",
        }

    # Step 4 — LD5 confidence formula
    sc_entropy = self_consistency_entropy(votes)
    raw_confidence = compute_confidence(msas, sc_entropy, structural_prior)

    # Step 5 — force-LOW for sparse-signal modules
    confidence = apply_force_low(raw_confidence, sparse_signal=sparse_signal)

    # Step 6 — routing
    route = route_finding(confidence)

    return {
        "module": finding.get("module"),
        "locus": finding.get("locus"),
        "sc_tally": sc_tally,
        "corroboration": corroboration,
        "refuted": False,
        "confidence": confidence,
        "sparse_signal": sparse_signal,
        "route": route,
        "funnel_stop": None,
    }


# ---------------------------------------------------------------------------
# JSON schema — single source of truth for the findings artifact
# ---------------------------------------------------------------------------

def findings_schema() -> dict:
    """Return the JSON schema for a routed finding (single source of truth).

    The terminal P2a artifact is ``.kata/deviations/findings.json`` — a JSON array
    of dicts conforming to this schema.  P2b (fix loop) consumes this artifact.

    Returns:
        JSON schema dict (JSON Schema Draft-07 compatible).
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "RoutedFinding",
        "description": (
            "A routed deviation finding produced by the LD4/LD5 pipeline "
            "(run_funnel).  The terminal P2a artifact."
        ),
        "type": "object",
        "required": ["module", "locus", "sc_tally", "route"],
        "properties": {
            "module": {
                "type": ["string", "null"],
                "description": "Module path (relative to repo root).",
            },
            "locus": {
                "type": ["string", "null"],
                "description": "Locus within the module (function/line/block).",
            },
            "sc_tally": {
                "oneOf": [
                    {
                        "type": "object",
                        "required": ["agree", "total", "passes"],
                        "properties": {
                            "agree": {"type": "integer"},
                            "total": {"type": "integer"},
                            "passes": {"type": "boolean"},
                        },
                        "additionalProperties": False,
                    },
                    {"type": "null"},
                ],
                "description": "Self-consistency tally from tally_self_consistency.",
            },
            "corroboration": {
                "oneOf": [
                    {
                        "type": "object",
                        "required": ["corroborated", "route", "co_located"],
                        "properties": {
                            "corroborated": {"type": "boolean"},
                            "route": {"type": ["string", "null"]},
                            "co_located": {"type": "array"},
                        },
                    },
                    {"type": "null"},
                ],
                "description": "Corroboration HARD gate result (corroboration_gate).",
            },
            "refuted": {
                "type": ["boolean", "null"],
                "description": "True iff adversarial refute succeeded (contested → human).",
            },
            "confidence": {
                "type": ["number", "null"],
                "description": "LD5 heuristic confidence score in [0,1] (null if funnel stopped early).",
            },
            "sparse_signal": {
                "type": ["boolean", "null"],
                "description": "True iff force-LOW was applied to this finding.",
            },
            "route": {
                "type": "string",
                "enum": ["auto-fix-eligible", "research", "defer", "human"],
                "description": "Routing verdict (LD5 band or HARD-gate override).",
            },
            "funnel_stop": {
                "type": ["string", "null"],
                "description": (
                    "Stage at which the funnel stopped early "
                    "(self_consistency / corroboration_gate / refuted / null)."
                ),
            },
        },
        "additionalProperties": True,
    }


# ---------------------------------------------------------------------------
# I/O — emit / load the findings artifact
# ---------------------------------------------------------------------------

def emit_findings(findings: list[dict], path: Any) -> None:
    """Write routed findings to the findings JSON artifact.

    Creates parent directories as needed (idempotent).

    Args:
        findings:  List of routed finding dicts (produced by run_funnel).
                   Normally written to ``.kata/deviations/findings.json``.
        path:      Destination path (str or pathlib.Path).
    """
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(findings, indent=2), encoding="utf-8")


def load_findings(path: Any) -> list[dict]:
    """Load routed findings from the findings JSON artifact.

    Args:
        path:  Source path (str or pathlib.Path).

    Returns:
        List of routed finding dicts.
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))
