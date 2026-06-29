"""benchmark.py — S2 deterministic benchmark scorer (kata-loop-benchmark).

Two-axis scorecard: Axis Q (outcome quality, floor-gated) × Axis C (efficiency).

Split (per PLAN S2 + DESIGN §3):
  (A) PURE scoring engine — scorecard_schema, score_arms, emit_scorecard
      Pure: no subprocess, no eval, no exec. Only reads .kata/ JSON artifacts
      and writes the scorecard via plain json.dumps / Path.write_text.
  (B) Thin dual-gate runner — run_dual_gate
      Calls mutation_check.run_named_test (existing INTERNAL sink registered at
      protocol/exec-safety.md:58; fixed shell=False argv). This module never
      introduces a new subprocess sink — the subprocess surface stays in
      mutation_check.py only (zero-new-sink posture).

Security posture
----------------
PURE — no subprocess, no eval, no exec.  run_dual_gate (B) calls
mutation_check.run_named_test (INTERNAL registered sink, exec-safety.md:58).
The node-ID is DATA in the argv list; never shell-interpolated.
emit_scorecard: CWE-23 path-traversal guard (_guard_path) rejects '..' in path.
run_dual_gate: _guard_node_id checks '..' AND containment AND leading '-' per FIX 2.
Zero new exec sink; protocol/exec-safety.md is unchanged.

Public surfaces (cite-able by name per protocol/reuse-claims.md)
---------------------------------------------------------------
scorecard_schema()                                   — JSON schema single source of truth
score_arms(arm_map, *, profile, f2p_p2p_results)    — PURE scorer (A)
emit_scorecard(path, scorecard)                      — write scorecard (CWE-23 guarded)
run_dual_gate(clone_root, f2p_ids, p2p_ids)         — thin runner (B)

Adversarial fixes (D98-series)
-------------------------------
FIX 1: No free dual-score — unevaluated gate → dual_gate_evaluated=False, Q=0.
FIX 2: run_dual_gate traversal guard — _guard_node_id rejects '..' + containment.
FIX 3: Honesty pin + recommendations — engine-pinned 'honesty' dict and
        deterministic 'recommendations' list in every scorecard.
FIX 5: Floor partial-RESULT fail-closed — missing 'failed' key → floor FAIL.
FIX 6b: Absent non-nullable Axis-C field → usage_incomplete=True, not 0.
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Union


# ---------------------------------------------------------------------------
# CWE-23 path-traversal guard (mirrors usage_meter._guard_path)
# ---------------------------------------------------------------------------


def _guard_path(raw: Union[str, Path]) -> Path:
    """Reject paths containing ``..`` traversal (CWE-23).  Does NOT resolve.

    Args:
        raw: The candidate path (str or Path).

    Returns:
        A Path object for the accepted path.

    Raises:
        ValueError: if ``raw`` contains a ``..`` path component.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        msg = f"benchmark: refusing path with '..' traversal: {raw!r}"
        raise ValueError(msg)
    return p


# ---------------------------------------------------------------------------
# FIX 2: Node-ID traversal guard for run_dual_gate
# ---------------------------------------------------------------------------


def _guard_node_id(test_id: str, clone_root: Path) -> None:
    """Guard a pytest node-ID against path-traversal (CWE-23, FIX 2).

    Applies three checks on the path component of *test_id*
    (the part before the final ``::``):

    1. Reject a leading ``-`` path segment (could be interpreted as a pytest flag).
    2. ``_guard_path`` rejects any ``..`` component (CWE-23).
    3. Containment: the resolved ``clone_root / rel_path`` must lie under the
       resolved *clone_root* — blocks symlink-escape and OS-specific corner cases
       that survive the ``..`` check.

    Raises:
        ValueError: on any guard violation (fail-closed — never hand a bad ID
                    to mutation_check.run_named_test).
    """
    sep = test_id.rfind("::")
    if sep < 0:
        return  # malformed — handled by _run_one before this call

    rel_path = test_id[:sep]

    # (1) Reject leading '-' path segment (pytest flag injection)
    parts = Path(rel_path).parts
    if parts and parts[0].startswith("-"):
        raise ValueError(
            f"benchmark: refusing test-ID with leading '-' path segment: {test_id!r}"
        )

    # (2) Reject '..' traversal components
    _guard_path(rel_path)

    # (3) Containment: resolved path must be under resolved clone root
    resolved_root = clone_root.resolve()
    resolved_test = (clone_root / rel_path).resolve()
    try:
        resolved_test.relative_to(resolved_root)
    except ValueError:
        raise ValueError(
            f"benchmark: test-ID path escapes clone root: {test_id!r}"
        )


# ---------------------------------------------------------------------------
# Profile table — λ and partial-credit weights (per DESIGN §3.4)
# ---------------------------------------------------------------------------

_PROFILES: Dict[str, dict] = {
    "balanced": {
        "lambda_": 1.0,
        "f2p_weight": 0.6,
        "p2p_weight": 0.4,
        "mut_mult_vacuous": 0.5,
    },
    "cost-lean": {
        "lambda_": 2.0,
        "f2p_weight": 0.6,
        "p2p_weight": 0.4,
        "mut_mult_vacuous": 0.5,
    },
    "quality-strict": {
        "lambda_": 0.5,
        "f2p_weight": 0.7,
        "p2p_weight": 0.3,
        "mut_mult_vacuous": 0.3,
    },
}

_DEFAULT_PROFILE = "balanced"

# Axis C: non-nullable fields (always present in usage.json per S1 schema)
_NON_NULLABLE_C_FIELDS: List[str] = [
    "wallClockS",
    "toolCalls",
    "escalations",
    "thrashIters",
    "subagentDispatches",
]


# ---------------------------------------------------------------------------
# (A) Schema
# ---------------------------------------------------------------------------


def scorecard_schema() -> dict:
    """Return the JSON schema for .kata/benchmark/<run-id>.json (single source of truth).

    Honesty fields (engine-pinned, DESIGN §6b + FIX 3):
      honesty        — dict: {directional, basis, disclosure} — cannot be silently dropped.
      n              — number of arms scored
      directional    — True: result is directional evidence, not statistical proof
                       (n=1 is directional by definition; always present)
      recommendations — list of deterministic, data-derived factual observations.

    Per-arm field added by FIX 1:
      dual_gate_evaluated — False when gate was not evaluated → Q=0, no free credit.

    Returns:
        A JSON Schema (draft 2020-12) dict for the benchmark scorecard.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "BenchmarkScorecard",
        "description": (
            "Deterministic benchmark scorecard produced by tools/benchmark.py (S2). "
            "Two-axis (Q × C) scoring: floor-gated composite (Pareto point + scalar "
            "Q/(1+λ·C_norm)) among floor-passers only. "
            "Honesty (engine-pinned): n=1 is directional, not proven; "
            "floor-fail ⇒ Q=0 absolute; tokens-unavailable labeled, not scored as 0. "
            "dual_gate_evaluated: false ⇒ Q=0 (no free credit for unevaluated gate). "
            "Reports NEVER gate (kata-evaluate owns the gate)."
        ),
        "type": "object",
        "required": [
            "schema", "profile", "n", "directional",
            "honesty", "recommendations", "arms", "utc",
        ],
        "properties": {
            "schema": {
                "type": "string",
                "description": "Schema identifier for this scorecard format.",
            },
            "profile": {
                "type": "string",
                "enum": ["balanced", "cost-lean", "quality-strict"],
                "description": "Scoring profile used (determines λ and partial-credit weights).",
            },
            "n": {
                "type": "integer",
                "description": "Number of arms scored in this run.",
            },
            "directional": {
                "type": "boolean",
                "description": (
                    "Always True: scorecard result is directional evidence, not "
                    "statistical proof. n=1 is directional by definition (DESIGN §6b)."
                ),
            },
            "honesty": {
                "type": "object",
                "description": (
                    "Engine-pinned honesty block (FIX 3). Cannot be silently dropped — "
                    "in schema required list. Fields: directional (bool, always True), "
                    "basis (str, e.g. 'n=1'), disclosure (str carrying the "
                    "n=1-directional + exercised-not-proven statement)."
                ),
                "required": ["directional", "basis", "disclosure"],
                "properties": {
                    "directional": {
                        "type": "boolean",
                        "description": "Always True — result is directional, not proven.",
                    },
                    "basis": {
                        "type": "string",
                        "description": "Honesty basis label, e.g. 'n=1'.",
                    },
                    "disclosure": {
                        "type": "string",
                        "description": (
                            "Short statement carrying the n=1-directional and "
                            "exercised-not-proven honesty note."
                        ),
                    },
                },
            },
            "recommendations": {
                "type": "array",
                "description": (
                    "Deterministic, data-derived factual observations (FIX 3). "
                    "No judgment — purely derived from scored arm data "
                    "(pareto/composite/c_norm/rank). Empty list if nothing notable. "
                    "Kinds: pareto-best | cost-outlier | dominated."
                ),
                "items": {
                    "type": "object",
                    "required": ["kind", "arm"],
                    "properties": {
                        "kind": {
                            "type": "string",
                            "enum": ["pareto-best", "cost-outlier", "dominated"],
                        },
                        "arm": {"type": "string"},
                        "detail": {"type": "string"},
                    },
                },
            },
            "arms": {
                "type": "array",
                "items": {
                    "type": "object",
                    "description": (
                        "Per-arm scorecard row. Key fields: label, floor_passed, "
                        "floor_verdict, q, c_norm, composite, rank, pareto, "
                        "in_efficiency_set, tokens_unavailable, usage_incomplete, "
                        "mutation_available, f2p_pass_rate, p2p_pass_rate, "
                        "dual_gate_both_green, dual_gate_evaluated (FIX 1), detail."
                    ),
                },
                "description": "Per-arm scorecard rows (one entry per arm_map key).",
            },
            "floor_passers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Labels of arms that cleared the floor gate.",
            },
            "floor_failers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Labels of arms that failed the floor gate (Q=0 absolute).",
            },
            "utc": {
                "type": "string",
                "description": "ISO-8601 UTC timestamp when the scorecard was built.",
            },
        },
        "additionalProperties": True,
    }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _load_json(path: Path) -> Optional[dict]:
    """Load JSON from *path*; return None if the file is absent or unreadable."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, OSError, json.JSONDecodeError):
        return None


def _compute_arm_q(
    result_json: Optional[dict],
    mutation_json: Optional[dict],
    f2p_results: dict,
    p2p_results: dict,
    weights: dict,
) -> tuple:
    """Compute Axis Q for one arm.  Returns (q: float, detail: dict).

    Floor-fail ⇒ Q=0 absolute (DESIGN §3.1.1, PLAN S2).  The assignment
    ``q = 0.0`` in the floor-fail branch is mutation-proven:
    test_floor_fail_exit_code_nonzero goes red when it is removed.

    FIX 5 — Fail-closed floor: requires exitCode==0 AND 'failed' key present
    AND failed==0.  A RESULT.json of just ``{"exitCode":0}`` (missing 'failed')
    is treated as FAIL (partial/truncated artifact).  Mutation-proven:
    test_floor_fail_missing_failed_key goes red if the present-check is removed.

    FIX 1 — No free dual-score: if both f2p_results and p2p_results are empty
    (no criteria declared), dual_gate_evaluated=False and Q=0.0 for any
    floor-passing arm.  Credit requires evaluated booleans.  Mutation-proven:
    test_no_gate_empty_criteria_no_q_credit goes red if the guard is removed.

    Args:
        result_json:   Parsed RESULT.json (or None if absent).
        mutation_json: Parsed mutation.json (or None if absent).
        f2p_results:   {test_id: bool} for FAIL_TO_PASS tests (pre-computed).
        p2p_results:   {test_id: bool} for PASS_TO_PASS tests (pre-computed).
        weights:       Profile weight dict from _PROFILES.

    Returns:
        (q, detail) where q ∈ [0,1] and detail is a diagnostic dict.
    """
    # FIX 5: fail-closed floor — require 'failed' key to be present
    if result_json is None:
        exit_code = 1
        failed = None
        failed_present = False
    else:
        exit_code = result_json.get("exitCode", 1)
        failed_present = "failed" in result_json  # FIX 5: fail-closed on absent 'failed' key (load-bearing)
        failed = result_json.get("failed", None)

    floor_passed = exit_code == 0 and failed_present and failed == 0

    detail: dict = {
        "floor_passed": floor_passed,
        "exit_code": exit_code,
        "failed": failed,
    }

    if not floor_passed:
        detail["floor_verdict"] = "FAIL"
        detail["dual_gate_evaluated"] = False
        q = 0.0  # floor-fail: Q=0 absolute (not modified further)
        return q, detail

    # -- Floor passed: check dual-gate evaluation status (FIX 1) --
    detail["floor_verdict"] = "PASS"

    gate_evaluated = len(f2p_results) > 0 or len(p2p_results) > 0
    detail["dual_gate_evaluated"] = gate_evaluated

    if not gate_evaluated:
        q = 0.0  # FIX 1: no free dual-score — gate not evaluated → no credit (load-bearing)
        return q, detail

    # -- Dual-gate scoring (gate was evaluated) --
    f2p_total = len(f2p_results)
    p2p_total = len(p2p_results)
    f2p_pass = sum(1 for v in f2p_results.values() if v)
    p2p_pass = sum(1 for v in p2p_results.values() if v)

    f2p_rate = f2p_pass / f2p_total if f2p_total > 0 else 1.0
    p2p_rate = p2p_pass / p2p_total if p2p_total > 0 else 1.0

    both_green = f2p_rate == 1.0 and p2p_rate == 1.0
    dual_score = weights["f2p_weight"] * f2p_rate + weights["p2p_weight"] * p2p_rate

    # -- Mutation multiplier (anti-weak-test; DESIGN §3.1.3) --
    mutation_available = mutation_json is not None
    if mutation_json is not None:
        all_non_vacuous = bool(mutation_json.get("allNonVacuous", True))
        mut_multiplier = 1.0 if all_non_vacuous else weights["mut_mult_vacuous"]
    else:
        # Absent mutation.json → no penalization; labeled mutation_available=False
        all_non_vacuous = True
        mut_multiplier = 1.0

    q = dual_score * mut_multiplier

    detail.update(
        {
            "f2p_pass_rate": f2p_rate,
            "p2p_pass_rate": p2p_rate,
            "dual_gate_both_green": both_green,
            "dual_gate_score": dual_score,
            "mutation_available": mutation_available,
            "mutation_all_non_vacuous": all_non_vacuous,
            "mutation_multiplier": mut_multiplier,
            "f2p_results": f2p_results,
            "p2p_results": p2p_results,
        }
    )
    return q, detail


def _validate_numeric(v: object) -> Optional[float]:
    """Return a validated non-negative finite float, or None.

    FIX C1 READ-PATH GUARD: any raw usage metric value that is negative, NaN,
    or Infinity is treated as *missing* (returns None) rather than being accepted
    and potentially poisoning the normalization or ranking.  The validated value
    feeds FIX C2 imputation (missing → worst-case 1.0).

    Args:
        v: Raw value from usage.json (any type; may be None, str, float, int, etc.).

    Returns:
        float if v is numeric, finite, and >= 0; None otherwise.
    """
    if v is None:
        return None
    try:
        fv = float(v)
    except (TypeError, ValueError):
        return None
    _c1_valid = math.isfinite(fv) and fv >= 0  # FIX C1: reject negative/NaN/Inf (load-bearing)
    if not _c1_valid:
        return None
    return fv


def _compute_c_norm_for_arms(usage_list: List[Optional[dict]]) -> List[dict]:
    """Normalize Axis C across all arms.

    Returns a list of ``{"c_norm": float, "tokens_unavailable": bool,
    "usage_incomplete": bool}`` dicts, one per arm in the same order as
    *usage_list*.

    FIX C1 (READ-PATH GUARD): every raw numeric value is validated via
    ``_validate_numeric`` before use.  Negative, NaN, or Infinity values are
    treated as *missing* (None) and feed FIX C2 imputation.  This closes the
    attack where ``costUSD: -540`` would produce the smallest c_norm and win
    rank-1.  The arm is flagged ``usage_incomplete=True``.

    FIX C2 (IMPUTATION — replaces old FIX 6b exclusion): a missing, null, or
    C1-invalid field is **imputed as the worst-case normalized value (1.0)**
    and *included* in the mean.  Omission never helps; an arm with missing data
    looks expensive (the honest-conservative direction).
    Exception: if **no** arm reports a given field at all (field_max is None),
    that field is dropped for everyone (neutral — not imputed for any arm).

    Honesty labels:
      ``tokens_unavailable=True``  — costUSD was null/absent from the host
                                      (host could not surface token data).
      ``usage_incomplete=True``    — any non-nullable field is absent OR any
                                      field (including costUSD) failed C1 validation.

    Normalization: each present field is divided by its per-arm-set maximum
    (0.0 when the max is 0 — no relative disadvantage).  ``c_norm`` is the mean
    of all dimension contributions (imputed or real) for the available fields of
    that arm.
    """
    n = len(usage_list)
    if n == 0:
        return []

    # --- Collect and validate raw values (FIX C1) ---
    # field_vals[f][i] = validated float or None (missing/invalid)
    field_vals: Dict[str, List[Optional[float]]] = {f: [] for f in _NON_NULLABLE_C_FIELDS}
    cost_vals: List[Optional[float]] = []   # validated costUSD (None = missing or C1-rejected)
    cost_raw_null: List[bool] = []          # True when original costUSD was null/absent

    for u in usage_list:
        uj = u or {}
        for field in _NON_NULLABLE_C_FIELDS:
            field_vals[field].append(_validate_numeric(uj.get(field)))  # FIX C1
        cost_raw = uj.get("costUSD")
        cost_raw_null.append(cost_raw is None)          # honest null vs invalid
        cost_vals.append(_validate_numeric(cost_raw))   # FIX C1

    # --- Per-field max for normalization ---
    # None means "no arm reported this field" → drop that field for everyone (FIX C2 edge).
    field_maxes: Dict[str, Optional[float]] = {
        f: max((v for v in vs if v is not None), default=None)
        for f, vs in field_vals.items()
    }
    cost_max: Optional[float] = max(
        (v for v in cost_vals if v is not None), default=None
    )

    results: List[dict] = []
    for i in range(n):
        cost_val = cost_vals[i]

        # tokens_unavailable: costUSD was null/absent from the original JSON (honesty label)
        tokens_unavailable = cost_raw_null[i]

        # usage_incomplete: any non-nullable field missing/invalid (FIX 6b + FIX C1)
        usage_incomplete = any(field_vals[f][i] is None for f in _NON_NULLABLE_C_FIELDS)
        # Also flag when costUSD was present but C1-rejected (invalid value)
        if not cost_raw_null[i] and cost_val is None:
            usage_incomplete = True

        # --- Normalize non-nullable fields (FIX C2: impute 1.0 for missing) ---
        norms: List[float] = []
        for field in _NON_NULLABLE_C_FIELDS:
            v = field_vals[field][i]
            mx = field_maxes[field]

            if mx is None:
                # No arm reports this field → neutral, drop for everyone (FIX C2 edge)
                continue

            if v is None:
                norms.append(1.0)  # FIX C2: missing/invalid field → impute worst-case
                continue

            norms.append(v / mx if mx > 0.0 else 0.0)

        # --- costUSD dimension (FIX C2: impute 1.0 for missing/invalid) ---
        if cost_max is not None:
            if cost_val is not None:
                norms.append(cost_val / cost_max if cost_max > 0.0 else 0.0)
            else:
                norms.append(1.0)  # FIX C2: missing/invalid costUSD → impute worst-case

        c_norm = sum(norms) / len(norms) if norms else 0.0
        results.append({
            "c_norm": c_norm,
            "tokens_unavailable": tokens_unavailable,
            "usage_incomplete": usage_incomplete,
        })

    return results


# ---------------------------------------------------------------------------
# FIX 3: Deterministic recommendations builder
# ---------------------------------------------------------------------------


def _build_recommendations(
    floor_passer_labels: List[str],
    arm_records: Dict[str, dict],
) -> List[dict]:
    """Build deterministic, data-derived factual observations (FIX 3).

    No judgment — purely derived from scored arm data (pareto/composite/c_norm/rank).
    Empty list if nothing notable or no floor-passers.

    Kinds emitted:
        pareto-best   — arm with highest composite (always emitted when ≥1 passer).
        cost-outlier  — arm whose c_norm exceeds 2× floor-passer mean (≥2 passers).
        dominated     — arm A where arm B has Q_B ≥ Q_A AND C_B ≤ C_A (≥1 strict).

    Args:
        floor_passer_labels: Labels of arms that cleared the floor gate.
        arm_records:         Per-arm record dicts (post-scoring).

    Returns:
        List of recommendation dicts with at least ``kind`` and ``arm`` keys.
    """
    recs: List[dict] = []
    if not floor_passer_labels:
        return recs

    # pareto-best: arm with highest composite (ties broken by label order)
    best = max(
        floor_passer_labels,
        key=lambda lb: arm_records[lb].get("composite") or 0.0,
    )
    recs.append({"kind": "pareto-best", "arm": best})

    # cost-outlier: c_norm > 2× mean among floor-passers (only with ≥2 arms)
    if len(floor_passer_labels) >= 2:
        c_entries = [
            (lb, arm_records[lb]["c_norm"])
            for lb in floor_passer_labels
            if arm_records[lb]["c_norm"] is not None
        ]
        if c_entries:
            mean_c = sum(c for _, c in c_entries) / len(c_entries)
            for lb, c in c_entries:
                if c > mean_c * 2.0:
                    recs.append({
                        "kind": "cost-outlier",
                        "arm": lb,
                        "detail": f"c_norm={c:.3f} vs mean={mean_c:.3f}",
                    })

    # dominated: arm A is dominated by arm B when Q_B ≥ Q_A AND C_B ≤ C_A (≥1 strict)
    for lb in floor_passer_labels:
        q_a = arm_records[lb]["q"]
        c_a = arm_records[lb]["c_norm"] or 0.0
        dominated = False
        for other in floor_passer_labels:
            if other == lb:
                continue
            q_b = arm_records[other]["q"]
            c_b = arm_records[other]["c_norm"] or 0.0
            if (q_b >= q_a and c_b <= c_a) and (q_b > q_a or c_b < c_a):
                dominated = True
                break
        if dominated:
            recs.append({"kind": "dominated", "arm": lb})

    return recs


# ---------------------------------------------------------------------------
# (A) Pure scoring engine
# ---------------------------------------------------------------------------


def score_arms(
    arm_map: Dict[str, Union[str, Path]],
    *,
    profile: str = _DEFAULT_PROFILE,
    f2p_p2p_results: Optional[Dict[str, dict]] = None,
    benchmark_id: Optional[str] = None,
    provenance: Optional[dict] = None,
) -> dict:
    """Score every arm in *arm_map* and return a benchmark scorecard.

    Pure (A): no subprocess, no eval, no exec.  Reads ``.kata/`` JSON artifacts
    from each arm's clone root.  F2P/P2P boolean results are injected via
    *f2p_p2p_results* (pre-computed by run_dual_gate or test fixtures) — the
    pure engine never runs pytest itself.

    FIX 1: An arm with no ``f2p_p2p_results`` entry, or whose entry has both
    ``f2p`` and ``p2p`` empty, gets ``dual_gate_evaluated=False`` and Q=0.0.
    No credit is given for an unevaluated gate.

    FIX 3: Scorecard always contains an engine-pinned ``honesty`` dict and a
    ``recommendations`` list (both in schema required).

    FIX A2: When *benchmark_id* and/or *provenance* are provided (non-None),
    they are stamped as TOP-LEVEL scorecard fields so that
    ``benchmark_def.compute_delta``'s ``sameDefinition`` can be True across
    runs of the same benchmark definition.  Without this stamp, both scorecards
    carried ``benchmark_id=None`` and ``sameDefinition`` was structurally always
    False.  Supply these from the wiring layer (the benchmark runner that owns
    the definition).

    Args:
        arm_map:           {arm_label → clone_artifact_root}.  Each root must
                           contain ``.kata/{RESULT,mutation,usage}.json``.
        profile:           Scoring profile — ``'balanced'`` | ``'cost-lean'`` |
                           ``'quality-strict'``.  Default: ``'balanced'``.
        f2p_p2p_results:   {arm_label → {"f2p": {test_id: bool},
                           "p2p": {test_id: bool}}}.  Defaults to empty dicts
                           (no declared test-IDs) when None or key absent.
        benchmark_id:      Optional benchmark definition UUID.  When provided,
                           stamped top-level → enables ``sameDefinition=True``
                           in delta mode (FIX A2).
        provenance:        Optional provenance dict (e.g. tool_version,
                           skill_versions).  When provided, stamped top-level →
                           same benchmark_id + differing provenance = honest
                           harness-delta (C-on/C-off, DESIGN §4).

    Returns:
        Scorecard dict conforming to scorecard_schema().

    Raises:
        ValueError: if *profile* is not a known profile name.
    """
    if profile not in _PROFILES:
        raise ValueError(
            f"benchmark: unknown profile {profile!r}; "
            f"choose from {list(_PROFILES)}"
        )

    weights = _PROFILES[profile]
    gate = f2p_p2p_results or {}
    ordered_labels = list(arm_map.keys())

    # -- Load artifacts per arm and compute Axis Q --
    arm_records: Dict[str, dict] = {}
    usage_list: List[Optional[dict]] = []

    for label in ordered_labels:
        root = Path(arm_map[label])
        kata = root / ".kata"

        result_json = _load_json(kata / "RESULT.json")
        mutation_json = _load_json(kata / "mutation.json")
        usage_json = _load_json(kata / "usage.json")

        arm_gate = gate.get(label)
        f2p = arm_gate.get("f2p", {}) if arm_gate is not None else {}
        p2p = arm_gate.get("p2p", {}) if arm_gate is not None else {}

        q, q_detail = _compute_arm_q(result_json, mutation_json, f2p, p2p, weights)

        arm_records[label] = {
            "label": label,
            "floor_passed": q_detail["floor_passed"],
            "floor_verdict": q_detail.get("floor_verdict", "FAIL"),
            "q": q,
            "c_norm": None,
            "composite": None,
            "rank": None,
            "pareto": None,
            "in_efficiency_set": False,
            "tokens_unavailable": False,
            "usage_incomplete": False,  # FIX 6b — updated below
            "mutation_available": q_detail.get("mutation_available", False),
            "f2p_pass_rate": q_detail.get("f2p_pass_rate", 0.0),
            "p2p_pass_rate": q_detail.get("p2p_pass_rate", 0.0),
            "dual_gate_both_green": q_detail.get("dual_gate_both_green", False),
            "dual_gate_evaluated": q_detail.get("dual_gate_evaluated", False),  # FIX 1
            "detail": q_detail,
        }
        usage_list.append(usage_json)

    # -- Collect floor-passers (efficiency gate — mutation-proven line below) --
    floor_passer_labels: List[str] = []
    for label in ordered_labels:
        if arm_records[label]["floor_passed"]:
            arm_records[label]["in_efficiency_set"] = True
            floor_passer_labels.append(label)  # floor-gate: efficiency only among passers

    floor_failer_labels = [lb for lb in ordered_labels if lb not in floor_passer_labels]

    # -- Compute Axis C (normalize across ALL arms; C_norm assigned to passers only) --
    c_info_list = _compute_c_norm_for_arms(usage_list)
    for label, c_info in zip(ordered_labels, c_info_list):
        arm_records[label]["tokens_unavailable"] = c_info["tokens_unavailable"]
        arm_records[label]["usage_incomplete"] = c_info.get("usage_incomplete", False)  # FIX 6b
        if arm_records[label]["floor_passed"]:
            arm_records[label]["c_norm"] = c_info["c_norm"]

    # -- Composite + rank for floor-passers only (DESIGN §3.4 R-A RESOLVED) --
    lambda_ = weights["lambda_"]
    passer_composites: List[tuple] = []  # (composite_value, label)
    for label in floor_passer_labels:
        c = arm_records[label]["c_norm"]
        q = arm_records[label]["q"]
        c_for_scalar = c if c is not None else 0.0
        composite = q / (1.0 + lambda_ * c_for_scalar)
        arm_records[label]["composite"] = composite
        arm_records[label]["pareto"] = {"q": q, "c": c_for_scalar}
        passer_composites.append((composite, label))

    # Sort descending by composite → assign rank (1 = best among passers)
    passer_composites.sort(key=lambda t: t[0], reverse=True)
    for rank_pos, (_, label) in enumerate(passer_composites, start=1):
        arm_records[label]["rank"] = rank_pos

    # -- FIX 3: Engine-pinned honesty block (cannot be silently dropped) --
    honesty = {
        "directional": True,
        "basis": "n=1",
        "disclosure": (
            "n=1 directional evidence only — exercised is not proven. "
            "Floor-fail is absolute (Q=0). Efficiency scored only among floor-passers."
        ),
    }

    # -- FIX 3: Deterministic, data-derived recommendations --
    recommendations = _build_recommendations(floor_passer_labels, arm_records)

    # -- Assemble scorecard --
    n = len(ordered_labels)
    arms_list = [arm_records[lb] for lb in ordered_labels]

    return {
        "schema": "benchmark/scorecard/v1",
        "profile": profile,
        "n": n,
        "directional": True,  # n=1 is directional, not proven; always noted (DESIGN §6b)
        "honesty": honesty,  # FIX 3: engine-pinned
        "recommendations": recommendations,  # FIX 3: engine-pinned
        "arms": arms_list,
        "floor_passers": floor_passer_labels,
        "floor_failers": floor_failer_labels,
        "utc": datetime.now(tz=timezone.utc).isoformat(),
        # FIX A2: stamp identity fields when provided so compute_delta.sameDefinition can be True.
        # When benchmark_id/provenance are None (not provided), they are omitted (not stamped as null).
        **({"benchmark_id": benchmark_id} if benchmark_id is not None else {}),
        **({"provenance": provenance} if provenance is not None else {}),
    }


# ---------------------------------------------------------------------------
# (A) I/O — emit scorecard
# ---------------------------------------------------------------------------


def emit_scorecard(path: Union[str, Path], scorecard: dict) -> None:
    """Write *scorecard* as JSON to *path* (CWE-23 path-traversal guarded).

    Intended destination: ``.kata/benchmark/<run-id>.json``.
    Rejects any path containing ``..`` traversal (CWE-23).
    Creates parent directories if absent.  Overwrites any existing file.

    Args:
        path:      Destination path.  Must not contain ``..``.
        scorecard: Dict produced by :func:`score_arms`.

    Raises:
        ValueError: if *path* contains ``..`` traversal (CWE-23).
        OSError:    on I/O failure.
    """
    dest = _guard_path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(scorecard, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# (B) Thin dual-gate runner — the ONLY non-pure part
# ---------------------------------------------------------------------------


def run_dual_gate(
    clone_root: Union[str, Path],
    f2p_ids: List[str],
    p2p_ids: List[str],
) -> dict:
    """Run F2P and P2P test-IDs via mutation_check.run_named_test (INTERNAL sink).

    No new subprocess sink: this module does NOT reference subprocess at all.
    Delegates entirely to mutation_check.run_named_test (registered INTERNAL sink
    at protocol/exec-safety.md:58; fixed argv list; shell=False).  The test
    node-ID is DATA in the argv list — never shell-interpolated — which also
    preserves ``::``/``[param]`` metacharacters correctly (DESIGN §3.1.2).

    FIX 2: _guard_node_id is called for each test-ID before any delegation to
    run_named_test.  It rejects ``..`` traversal (CWE-23), paths that escape
    the clone root (containment check), and leading ``-`` path segments.  On a
    bad ID, raises ValueError (fail-closed) — never hands it to run_named_test.

    The pure engine (score_arms) consumes the returned booleans; it never calls
    this runner.

    Args:
        clone_root: Root of the arm's clone directory.
        f2p_ids:    FAIL_TO_PASS test-IDs in ``'path/to/test.py::test_name'`` format.
        p2p_ids:    PASS_TO_PASS test-IDs in ``'path/to/test.py::test_name'`` format.

    Returns:
        ``{"f2p": {test_id: bool}, "p2p": {test_id: bool}}``

    Raises:
        ValueError: if any test-ID fails the traversal guard (_guard_node_id).
    """
    import mutation_check  # lazy import — benchmark.py never imports subprocess itself

    root = Path(clone_root)

    def _run_one(test_id: str) -> bool:
        """Split ``'path::name'`` and call mutation_check.run_named_test.

        FIX A1: passes ``cwd=str(root)`` so pytest runs from the clone root and
        PYTHONPATH includes the clone root → ``from src import X`` resolves.
        Uses *rel_path* (relative to clone root) rather than an absolute path, so
        pytest resolves the file under cwd.  The _guard_node_id containment check
        still applies (verifies rel_path stays inside the clone root).
        """
        if "::" not in test_id:
            return False  # malformed test-ID: fail safe
        _guard_node_id(test_id, root)  # FIX 2: traversal guard (load-bearing)
        sep = test_id.rfind("::")
        rel_path = test_id[:sep]
        test_name = test_id[sep + 2:]
        # FIX A1: cwd=clone_root so pytest runs there; rel_path resolves under cwd.
        return mutation_check.run_named_test(rel_path, test_name, cwd=str(root))

    return {
        "f2p": {tid: _run_one(tid) for tid in f2p_ids},
        "p2p": {tid: _run_one(tid) for tid in p2p_ids},
    }
