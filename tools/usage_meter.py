"""usage_meter.py — S1 metering engine → .kata/usage.json (kata-loop-benchmark).

Net-new hook confirmed by DESIGN §3.3 (R-cost RESOLVED): the harness does NOT
persist per-arm token/cost today.  This module writes ``.kata/usage.json`` for
every benchmarked arm so Axis C (efficiency) has inputs.

Pure, deterministic, no subprocess, no eval/exec.  wallClockS is caller-supplied
(injectable elapsed seconds — tests pass a fixed value, never a real wall-clock
call inside the builder).  tokensIn/tokensOut/costUSD are nullable because token
capture is host-dependent; they are honestly labeled null when the host did not
surface them.  wallClockS and toolCalls are always present.

Security posture
----------------
PURE — no subprocess, no eval, no exec, no shell.  Writes JSON via plain
json.dumps and Path.write_text.  CWE-23 path-traversal guard (``_guard_path``)
rejects any path containing ``..`` before any filesystem operation, mirroring
the ``_guard_path`` pattern from validation_misses.py.  Zero new exec sink —
protocol/exec-safety.md is unchanged.

Public surfaces (cite-able by name per protocol/reuse-claims.md)
---------------------------------------------------------------
usage_schema          — JSON schema (single source of truth) for .kata/usage.json
build_usage(...)      — pure builder; validates inputs; nullable token fields allowed
cost_from_rate_table  — per-model $/token pricing; returns None when tokens are null
write_usage           — writes .kata/usage.json (CWE-23 guarded)
load_usage            — reads .kata/usage.json
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional, Union


# ---------------------------------------------------------------------------
# Path-traversal guard (CWE-23) — mirrors _guard_path in validation_misses.py
# ---------------------------------------------------------------------------


def _guard_path(raw: Union[str, Path]) -> Path:
    """Reject paths containing ``..`` traversal (CWE-23).  Does NOT resolve.

    Resolution is deliberately left to the caller's I/O block: a pathological
    path (e.g. embedded NUL) must surface as a write failure, not as a raise
    into a gate.  Only the ``..`` caller-bug raises here.

    Args:
        raw: The candidate path (str or Path).

    Returns:
        A Path object for the accepted path.

    Raises:
        ValueError: if ``raw`` contains a ``..`` path component.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        msg = f"usage_meter: refusing path with '..' traversal: {raw!r}"
        raise ValueError(msg)
    return p


# ---------------------------------------------------------------------------
# JSON schema (single source of truth)
# ---------------------------------------------------------------------------


def usage_schema() -> dict:
    """Return the JSON schema for a per-arm usage entry (single source of truth).

    Schema fields
    -------------
    label             — arm label (str, required)
    model             — model identifier (str, required)
    tokensIn          — prompt token count (nullable; host-dependent capture)
    tokensOut         — completion token count (nullable; host-dependent capture)
    costUSD           — USD cost (nullable; derived from rate table when tokens available)
    wallClockS        — wall-clock elapsed seconds (float, always present)
    toolCalls         — number of tool calls made (int, always present)
    escalations       — number of escalations (int)
    thrashIters       — number of fix-loop thrash iterations (int)
    subagentDispatches — number of subagent dispatches (int)

    tokensIn/tokensOut/costUSD are nullable (type includes "null") because token
    capture is host-dependent.  wallClockS and toolCalls are always present.

    Returns:
        A JSON Schema (draft 2020-12) dict for .kata/usage.json.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "UsageEntry",
        "description": (
            "Per-arm usage entry for kata-loop-benchmark Axis C (efficiency). "
            "tokensIn/tokensOut/costUSD are nullable (host-dependent capture — "
            "honestly null when the host did not surface them). "
            "wallClockS and toolCalls are always present."
        ),
        "type": "object",
        "required": [
            "label",
            "model",
            "wallClockS",
            "toolCalls",
            "escalations",
            "thrashIters",
            "subagentDispatches",
        ],
        "properties": {
            "label": {
                "type": "string",
                "description": "Arm label (e.g. 'baseline' or 'myproject-katabenchmark1').",
            },
            "model": {
                "type": "string",
                "description": "Model identifier used by this arm.",
            },
            "tokensIn": {
                "type": ["integer", "null"],
                "description": "Prompt token count.  Null when the host did not surface it.",
            },
            "tokensOut": {
                "type": ["integer", "null"],
                "description": "Completion token count.  Null when the host did not surface it.",
            },
            "costUSD": {
                "type": ["number", "null"],
                "description": "USD cost.  Null when tokens were not available for pricing.",
            },
            "wallClockS": {
                "type": "number",
                "description": "Wall-clock elapsed seconds (always present; caller-supplied).",
            },
            "toolCalls": {
                "type": "integer",
                "description": "Number of tool calls made during this arm (always present).",
            },
            "escalations": {
                "type": "integer",
                "description": "Number of escalations during this arm.",
            },
            "thrashIters": {
                "type": "integer",
                "description": "Number of fix-loop thrash iterations during this arm.",
            },
            "subagentDispatches": {
                "type": "integer",
                "description": "Number of subagent dispatches during this arm.",
            },
        },
        "additionalProperties": False,
    }


# ---------------------------------------------------------------------------
# Pure builder
# ---------------------------------------------------------------------------


def build_usage(
    *,
    label: str,
    model: str,
    wall_clock_s: float,
    tool_calls: int,
    tokens_in: Optional[int] = None,
    tokens_out: Optional[int] = None,
    cost_usd: Optional[float] = None,
    escalations: int = 0,
    thrash_iters: int = 0,
    subagent_dispatches: int = 0,
) -> dict:
    """Build a per-arm usage entry conforming to usage_schema().

    tokensIn/tokensOut/costUSD are nullable — None means the host did not
    surface the value (honestly labeled, never fabricated).  wallClockS is
    caller-supplied elapsed seconds (injectable for deterministic tests — the
    caller times the run and passes the result; this function never calls a
    real wall-clock).

    Args:
        label:               Arm label (required).
        model:               Model identifier (required).
        wall_clock_s:        Wall-clock elapsed seconds (always present).
        tool_calls:          Number of tool calls made (always present).
        tokens_in:           Prompt token count (None if not surfaced by host).
        tokens_out:          Completion token count (None if not surfaced by host).
        cost_usd:            USD cost (None if tokens unavailable for pricing).
        escalations:         Number of escalations (default 0).
        thrash_iters:        Number of fix-loop thrash iterations (default 0).
        subagent_dispatches: Number of subagent dispatches (default 0).

    Returns:
        A dict conforming to usage_schema().

    Raises:
        TypeError: if required non-nullable fields have wrong types, or if
                   nullable fields receive a value of the wrong type.
    """
    if not isinstance(label, str):
        raise TypeError(
            f"usage_meter: label must be str, got {type(label).__name__!r}"
        )
    if not isinstance(model, str):
        raise TypeError(
            f"usage_meter: model must be str, got {type(model).__name__!r}"
        )
    if isinstance(wall_clock_s, bool) or not isinstance(wall_clock_s, (int, float)):
        raise TypeError(
            f"usage_meter: wall_clock_s must be numeric, "
            f"got {type(wall_clock_s).__name__!r}"
        )
    if isinstance(tool_calls, bool) or not isinstance(tool_calls, int):
        raise TypeError(
            f"usage_meter: tool_calls must be int, got {type(tool_calls).__name__!r}"
        )
    for _name, _val in (("tokens_in", tokens_in), ("tokens_out", tokens_out)):
        if _val is not None and (isinstance(_val, bool) or not isinstance(_val, int)):
            raise TypeError(
                f"usage_meter: {_name} must be int or None, "
                f"got {type(_val).__name__!r}"
            )
    if cost_usd is not None and (
        isinstance(cost_usd, bool) or not isinstance(cost_usd, (int, float))
    ):
        raise TypeError(
            f"usage_meter: cost_usd must be numeric or None, "
            f"got {type(cost_usd).__name__!r}"
        )

    # Non-negativity guards (D98) — usage magnitudes are ≥ 0 by definition;
    # negatives are nonsensical and are a cheap Axis-C gaming vector (a crafted
    # negative cost_usd drives 1+λ·c_norm toward zero and inflates composite).
    # Null/None remains allowed for nullable fields — only NEGATIVE is rejected.
    if wall_clock_s < 0:
        raise ValueError(
            f"usage_meter: wall_clock_s must be >= 0, got {wall_clock_s!r}"
        )
    if tool_calls < 0:
        raise ValueError(
            f"usage_meter: tool_calls must be >= 0, got {tool_calls!r}"
        )
    for _name, _val in (("tokens_in", tokens_in), ("tokens_out", tokens_out)):
        if _val is not None and _val < 0:
            raise ValueError(
                f"usage_meter: {_name} must be >= 0, got {_val!r}"
            )
    if cost_usd is not None and cost_usd < 0:
        raise ValueError(
            f"usage_meter: cost_usd must be >= 0, got {cost_usd!r}"
        )
    for _name, _val in (
        ("escalations", escalations),
        ("thrash_iters", thrash_iters),
        ("subagent_dispatches", subagent_dispatches),
    ):
        if _val < 0:
            raise ValueError(
                f"usage_meter: {_name} must be >= 0, got {_val!r}"
            )

    return {
        "label": label,
        "model": model,
        "tokensIn": tokens_in,
        "tokensOut": tokens_out,
        "costUSD": cost_usd,
        "wallClockS": float(wall_clock_s),
        "toolCalls": tool_calls,
        "escalations": escalations,
        "thrashIters": thrash_iters,
        "subagentDispatches": subagent_dispatches,
    }


# ---------------------------------------------------------------------------
# Rate-table pricing
# ---------------------------------------------------------------------------


def cost_from_rate_table(
    tokens_in: Optional[int],
    tokens_out: Optional[int],
    model: str,
    rate_table: dict,
) -> Optional[float]:
    """Compute USD cost from a per-model rate table.

    Multi-model arms are each priced from their own entry in rate_table.
    Returns None if tokens are null or the model is absent from the table —
    never fabricates a cost.

    Args:
        tokens_in:  Prompt token count (None = host did not surface).
        tokens_out: Completion token count (None = host did not surface).
        model:      Model identifier.
        rate_table: Dict mapping model name → {"input": cost_per_token,
                    "output": cost_per_token} where cost_per_token is in USD.

    Returns:
        USD cost as float, or None if tokens are null or model not in table.
    """
    if tokens_in is None or tokens_out is None:
        _absent = True  # host did not surface token count — honestly null
        return None
    rates = rate_table.get(model)
    if rates is None:
        _missing = True  # model not in rate table — return None, not zero
        return None
    return tokens_in * rates["input"] + tokens_out * rates["output"]


# ---------------------------------------------------------------------------
# I/O — write / load the usage entry (.kata/usage.json)
# ---------------------------------------------------------------------------


def write_usage(path: Union[str, Path], entry: dict) -> None:
    """Write a usage entry as JSON to *path* (e.g. ``.kata/usage.json``).

    CWE-23 guarded: rejects any path containing ``..`` before touching the
    filesystem, mirroring ``_guard_path`` in validation_misses.py.
    Creates parent directories if absent.  Overwrites any existing file.

    Args:
        path:  Destination path.  Must not contain ``..``.
        entry: Dict produced by ``build_usage()``.

    Raises:
        ValueError: if ``path`` contains ``..`` traversal (CWE-23).
        OSError:    on I/O failure.
    """
    dest = _guard_path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")


def load_usage(path: Union[str, Path]) -> dict:
    """Load a usage entry dict from *path*.

    Args:
        path: Path to a JSON file previously written by ``write_usage()``.

    Returns:
        The parsed usage entry dict.
    """
    return json.loads(Path(path).read_text(encoding="utf-8"))
