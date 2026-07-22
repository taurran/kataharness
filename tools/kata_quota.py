"""kata_quota.py — provider quota/rate-limit/auth classification + lapse policy (pure stdlib).

The quota-resilience Tier 1+2 engine (grill: `.planning/specs/quota-resilience/GRILL-LEDGER.md`,
G-1..G-12). Three pure functions the conductor wires at existing boundaries:

- :func:`classify_dispatch_result` — deterministic clean-error classifier over a
  ``kata_dispatch`` RESULT envelope (G-7/G-8: dispatch results are the ONLY signal source;
  the worker stderr it reads exists since the PR #42 stderr fix).
- :func:`lapse_decision` — the G-2 hybrid threshold: a CLASSIFIED provider signal lapses on
  the FIRST occurrence (the premium ``premium-unavailable`` fires-on-first precedent);
  unclassified generic failures lapse at 2 consecutive.
- :func:`parse_kill_switch` — the G-3 operator kill-switch: ``KATA_OFF <subsystem>`` lines
  from the EXISTING steering Active-directives grammar (``kata_steer.read_active_directives``
  output; ``kata_steer.py`` itself is byte-untouched).

Policy boundaries (deliberate, grill-recorded):
- Classification NEVER triggers a model downgrade (G-6 — park or lapse, never silently
  cheaper). This module returns facts; the conductor routes by path criticality (G-9:
  optional subsystems lapse-and-continue; the primary dispatch path parks per G-4 —
  human-required escalation + breakthrough alert + handoff write, NEVER a retry loop).
- No provider registry / upgrade URLs here (G-5, Tier 3): :func:`park_message` emits a
  generic, always-true upgrade line naming the provider when the envelope carries one.

Determinism (DETERMINISM-DOCTRINE): pure functions of their inputs; the pattern table is
ordered most-specific-first and matching is case-insensitive over the envelope's text
fields; ``evidence`` is the first matching line in a fixed field-scan order. Fail-closed
(D136): a malformed envelope RAISES — a signal-free envelope returns ``classified: False``
(a computed result over read input, not an unread input).

⚠ Do NOT conflate with ``kata_adaptive``'s ``"budget-exhausted"`` — that is kata's own
internal premium/advisor spend budget. This module classifies PROVIDER-side exhaustion.
"""

from __future__ import annotations

import re

__all__ = [
    "QuotaError",
    "CLASSIFIED_REASONS",
    "KILL_SWITCH_SUBSYSTEMS",
    "GENERIC_LAPSE_THRESHOLD",
    "classify_dispatch_result",
    "lapse_decision",
    "parse_kill_switch",
    "park_message",
]


class QuotaError(Exception):
    """Malformed input to quota decision-code (D136 — never a silent permissive default)."""


#: The classification vocabulary (G-10 ledger reasons use these exact strings).
CLASSIFIED_REASONS: tuple[str, ...] = ("rate-limited", "quota-exhausted", "auth")

#: Recognized kill-switch subsystems (G-3). ``provider:<name>`` is also accepted.
KILL_SWITCH_SUBSYSTEMS: frozenset[str] = frozenset({"advisor", "provider"})

#: G-2: unclassified generic dispatch failures lapse at this many CONSECUTIVE failures.
GENERIC_LAPSE_THRESHOLD: int = 2

_KILL_VERB = "KATA_OFF"

# Ordered most-specific-first (G-8). Each row: (reason, compiled pattern).
# Sources: HTTP status idioms + provider CLI phrasings recorded in docs/platforms/*.md
# (codex hang-on-402 quota class; plan/credit phrasing) + Anthropic/OpenAI 429 shapes.
_PATTERNS: tuple[tuple[str, re.Pattern], ...] = (
    # -- quota / plan exhaustion (the "you're out" class) ---------------------------
    ("quota-exhausted", re.compile(
        r"(?i)\b402\b|insufficient[ _-]?(credit|quota|funds)|quota[ _-]?(exceeded|exhausted)|"
        r"out of (tokens|credits|quota)|plan limit|(reached|exceeded).{0,20}usage limit|"
        r"usage limit (reached|exceeded)|"
        r"billing (hard )?limit|credit balance is too low")),
    # -- rate limiting (the "slow down / try later" class) --------------------------
    ("rate-limited", re.compile(
        r"(?i)\b429\b|rate[ _-]?limit(ed|s)?\b|too many requests|retry[ _-]?after|"
        r"overloaded_error|server[ _-]?overloaded")),
    # -- auth (the "your key is bad" class) ------------------------------------------
    ("auth", re.compile(
        r"(?i)\b401\b|\b403\b|unauthorized|forbidden|invalid (api[ _-]?key|x-api-key)|"
        r"authentication[ _-]?error|permission[ _-]?denied.*api|api key.*(invalid|expired)")),
)

#: Envelope text fields scanned, in FIXED order (payload first — stderr is the richest
#: signal since PR #42; then the error string; then raw stdout).
_SCAN_FIELDS: tuple[tuple[str, ...], ...] = (
    ("payload", "stderr"),
    ("payload", "error"),
    ("raw",),
)


def _field_text(result: dict, path: tuple[str, ...]) -> str:
    node = result
    for key in path:
        if not isinstance(node, dict):
            return ""
        node = node.get(key)
    return node if isinstance(node, str) else ""


def classify_dispatch_result(result: dict) -> dict:
    """Classify a ``kata_dispatch`` RESULT envelope for a clean provider error signal.

    Args:
        result: The N3 envelope (``build_result`` shape): must be a dict carrying a
            ``status`` string. Only ``failed``/``timeout`` envelopes are classifiable;
            a ``completed``/``fallback`` envelope returns unclassified by definition
            (success needs no quota routing).

    Returns:
        ``{"classified": bool, "reason": str | None, "evidence": str, "platform": str}``
        — ``reason`` ∈ :data:`CLASSIFIED_REASONS` when classified; ``evidence`` is the
        first matching LINE from the first matching field (fixed scan order, so the
        result is a pure function of the envelope); ``platform`` echoes the envelope's
        platform for the park message (empty string when absent).

    Raises:
        QuotaError: On a malformed envelope (not a dict, or ``status`` missing/non-str)
            — decision-code never silently defaults on unreadable input (D136).
    """
    if not isinstance(result, dict):
        raise QuotaError(f"classify_dispatch_result: envelope must be a dict, got {type(result).__name__}")
    status = result.get("status")
    if not isinstance(status, str) or not status:
        raise QuotaError("classify_dispatch_result: envelope missing 'status' (malformed RESULT — D136)")

    platform = result.get("platform") if isinstance(result.get("platform"), str) else ""
    if status not in {"failed", "timeout"}:
        return {"classified": False, "reason": None, "evidence": "", "platform": platform}

    for path in _SCAN_FIELDS:
        text = _field_text(result, path)
        if not text:
            continue
        for reason, pattern in _PATTERNS:
            m = pattern.search(text)
            if m:
                # evidence = the full line containing the first match (bounded input:
                # stderr is already tail-capped by kata_dispatch)
                start = text.rfind("\n", 0, m.start()) + 1
                end = text.find("\n", m.end())
                line = text[start: end if end != -1 else len(text)].strip()
                return {"classified": True, "reason": reason, "evidence": line, "platform": platform}
    return {"classified": False, "reason": None, "evidence": "", "platform": platform}


def lapse_decision(consecutive_generic_failures: int, classified_reason: str | None) -> dict:
    """The G-2 hybrid lapse threshold, as one pure decision point.

    Args:
        consecutive_generic_failures: The conductor's run-scoped count of consecutive
            UNCLASSIFIED dispatch failures on this lane (reset to 0 on any success).
        classified_reason: A reason from :func:`classify_dispatch_result`, or None.

    Returns:
        ``{"lapse": bool, "reason": str | None}`` — reason is the classified reason
        (fires on FIRST), or ``"provider-unavailable"`` at the generic threshold.

    Raises:
        QuotaError: On a negative/non-int count or an unknown classified reason
            (producer bug — D136).
    """
    if isinstance(consecutive_generic_failures, bool) or not isinstance(consecutive_generic_failures, int):
        raise QuotaError(f"lapse_decision: count must be an int, got {consecutive_generic_failures!r}")
    if consecutive_generic_failures < 0:
        raise QuotaError(f"lapse_decision: count must be >= 0, got {consecutive_generic_failures}")
    if classified_reason is not None and classified_reason not in CLASSIFIED_REASONS:
        raise QuotaError(
            f"lapse_decision: unknown classified reason {classified_reason!r} — "
            f"known: {list(CLASSIFIED_REASONS)}. Producer bug (D136)."
        )
    if classified_reason is not None:
        return {"lapse": True, "reason": classified_reason}
    if consecutive_generic_failures >= GENERIC_LAPSE_THRESHOLD:
        return {"lapse": True, "reason": "provider-unavailable"}
    return {"lapse": False, "reason": None}


def parse_kill_switch(directives: list) -> dict:
    """Parse ``KATA_OFF <subsystem>`` lines from steering Active-directives output (G-3).

    Consumes the output of ``kata_steer.read_active_directives`` — this module never
    reads STEERING.md itself, and ``kata_steer.py`` is byte-untouched.

    Grammar: a directive whose first token is ``KATA_OFF`` (exact case — steering verbs
    are shouted, like ``AGENT_STOP``) followed by ONE subsystem token: ``advisor``,
    ``provider``, or ``provider:<name>``. Leading list-bullet markers (``- ``/``* ``)
    are tolerated (directives are normally bullets).

    Returns:
        ``{"off": list[str], "unknown": list[str]}`` — ``off`` = recognized subsystem
        tokens in source order (deduped, first occurrence wins); ``unknown`` = the full
        original directive line for every malformed/unrecognized ``KATA_OFF`` use, for
        the conductor to surface LOUDLY (never silently ignored, never run-fatal —
        steering is additive; a typo must not kill a run and must not vanish).

    Raises:
        QuotaError: If *directives* is not a list of strings (producer bug — the
            kata_steer reader always returns exactly that).
    """
    if not isinstance(directives, list) or any(not isinstance(d, str) for d in directives):
        raise QuotaError("parse_kill_switch: directives must be list[str] (kata_steer reader output)")

    off: list[str] = []
    unknown: list[str] = []
    for raw in directives:
        stripped = raw.strip()
        if stripped[:2] in ("- ", "* "):
            stripped = stripped[2:].strip()
        tokens = stripped.split()
        if not tokens or tokens[0] != _KILL_VERB:
            continue  # not a kill-switch directive — other directives are none of our business
        if len(tokens) != 2:
            unknown.append(raw)
            continue
        subsystem = tokens[1]
        base = subsystem.split(":", 1)[0]
        if base not in KILL_SWITCH_SUBSYSTEMS or (":" in subsystem and base != "provider") \
                or subsystem.endswith(":"):
            unknown.append(raw)
            continue
        if subsystem not in off:
            off.append(subsystem)
    return {"off": off, "unknown": unknown}


def park_message(reason: str, evidence: str, platform: str = "") -> str:
    """The plain operator message for a park (G-4/G-5). Deterministic; NO URLs (Tier 3).

    Generic and always-true: names the provider when known, quotes the evidence line,
    states the park + resume path. A wrong/stale upgrade URL is worse than none (PD-2).

    Raises:
        QuotaError: On an unknown reason (producer bug).
    """
    if reason not in CLASSIFIED_REASONS and reason != "provider-unavailable":
        raise QuotaError(f"park_message: unknown reason {reason!r}")
    who = f"{platform} " if platform else ""
    headline = {
        "quota-exhausted": f"You're out of {who}tokens/credits.",
        "rate-limited": f"The {who}provider is rate-limiting this run.",
        "auth": f"The {who}provider rejected authentication.",
        "provider-unavailable": f"The {who}provider is failing repeatedly.",
    }[reason]
    lines = [
        headline,
        f"Evidence: {evidence}" if evidence else "Evidence: repeated dispatch failures (no clean provider signal).",
        "The run has been PARKED: state saved via handoff; nothing was lost.",
        "To add capacity: check your plan/billing with the provider, or wait for the quota window to reset.",
        "When ready, resume with /kata-resume — it picks up exactly where this stopped.",
    ]
    return "\n".join(lines)
