"""validation_misses.py — pure data layer for the validation-miss manifest.

Tracks every time the conformance gate (kata-evaluate) PASSED something that
the adversarial lens (kata-review/D98), a re-confirm, or a human later CAUGHT.
T1 (PLAN-t1-manifest.md §S1): observe-only — log + count + surface. No subprocess,
no eval. Changes no gate behavior.

No exec surface: no subprocess, no eval (exec-safety.md clean).

Limitation (secret hygiene): ``what_conformance_missed`` accepts any string.
The spec states entries must be description-level only — no code payloads from
the private repo. This is a **convention**, not enforced programmatically here
(enforcement would require NLP heuristics). It is stated in
``protocol/validation-misses.md`` and in ``miss_schema()``'s field description.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Enum constants (single source of truth)
# ---------------------------------------------------------------------------

_SEVERITY_VALUES: frozenset[str] = frozenset({"BLOCKER", "MAJOR", "MINOR"})
_CAUGHT_BY_VALUES: frozenset[str] = frozenset({"d98", "re-confirm", "human"})

# All 9 schema fields
_REQUIRED_STR_FIELDS: frozenset[str] = frozenset({
    "ts",
    "mode",
    "failure_class",
    "responsible_skill",
    "severity",
    "what_conformance_missed",
    "what_caught_it",
})
_NULLABLE_STR_FIELDS: frozenset[str] = frozenset({"guard_ref", "decision_ref"})
_ALL_FIELDS: frozenset[str] = _REQUIRED_STR_FIELDS | _NULLABLE_STR_FIELDS


# ---------------------------------------------------------------------------
# Path-traversal guard (CWE-23) — mirrors _safe_abs in kata_settings.py
# ---------------------------------------------------------------------------

def _guard_path(raw: str | Path) -> Path:
    """Reject paths containing ``..`` traversal (CWE-23). Does NOT resolve.

    Resolution is deliberately left to the caller's non-fatal I/O block: a
    pathological path (e.g. an embedded NUL) must surface as a write *failure*
    (return False), not as a raise into a gate/build. Only the ``..`` caller-bug
    raises here.

    Raises:
        ValueError: if ``raw`` contains a ``..`` path component.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"validation_misses: refusing path with '..' traversal: {raw!r}"
        )
    return p


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def miss_schema() -> dict:
    """Return the entry schema — single source of truth for field names and types.

    Returns a dict keyed by field name. Each value describes the field type,
    allowed values (for enum fields), and a description. Callers (S2 orchestrator,
    tests, documentation) import this so the schema stays DRY.

    All 9 fields:
        ts, mode, failure_class, responsible_skill, severity,
        what_conformance_missed, what_caught_it, guard_ref, decision_ref.
    """
    return {
        "ts": {
            "type": "str",
            "description": "ISO8601 timestamp of the miss (e.g. 2026-06-27T12:00:00Z)",
        },
        "mode": {
            "type": "str",
            "description": "Run shape / mode (e.g. debug, build, review)",
        },
        "failure_class": {
            "type": "str",
            "description": "Slug categorising the miss (e.g. rce-unchecked, dos-vector)",
        },
        "responsible_skill": {
            "type": "str",
            "description": "The skill that should harden (e.g. kata-evaluate)",
        },
        "severity": {
            "type": "str",
            "enum": sorted(_SEVERITY_VALUES),
            "description": "Impact severity: BLOCKER | MAJOR | MINOR",
        },
        "what_conformance_missed": {
            "type": "str",
            "description": (
                "Description of the gap. "
                "CONVENTION: description-level only — no code payloads (private repo, "
                "secret hygiene). Not enforced programmatically — see module docstring."
            ),
        },
        "what_caught_it": {
            "type": "str",
            "enum": sorted(_CAUGHT_BY_VALUES),
            "description": "What surfaced the miss: d98 | re-confirm | human",
        },
        "guard_ref": {
            "type": "str|null",
            "description": "Doc/test that closed the miss, or null when still open",
        },
        "decision_ref": {
            "type": "str|null",
            "description": "D-number reference (e.g. D109), or null",
        },
    }


def validate_miss(entry: dict) -> list[str]:
    """Validate a miss entry; return a list of error strings (empty list = valid).

    Checks enforced:
    - ``entry`` is a dict.
    - All required fields are present and are non-None strings.
    - ``severity`` is in {BLOCKER, MAJOR, MINOR}.
    - ``what_caught_it`` is in {d98, re-confirm, human}.
    - ``guard_ref`` and ``decision_ref`` are str or None.
    - No extra keys (additionalProperties: false).

    Not enforced (by design — see module docstring):
    - Content of ``what_conformance_missed`` is not checked for code payloads.
      Description-only is a convention stated in ``protocol/validation-misses.md``.

    Args:
        entry: The candidate miss entry dict.

    Returns:
        A list of human-readable error strings. Empty list means the entry is valid.
    """
    errors: list[str] = []

    if not isinstance(entry, dict):
        return ["entry must be a dict"]

    # Extra keys — additionalProperties: false
    extra = set(entry.keys()) - _ALL_FIELDS
    if extra:
        errors.append(f"extra keys not allowed: {sorted(extra)}")

    # Required string fields — must be present AND be str
    for field in sorted(_REQUIRED_STR_FIELDS):
        if field not in entry:
            errors.append(f"missing required field: {field!r}")
        elif not isinstance(entry[field], str):
            errors.append(
                f"field {field!r} must be str, got {type(entry[field]).__name__!r}"
            )

    # Enum: severity
    if isinstance(entry.get("severity"), str):
        if entry["severity"] not in _SEVERITY_VALUES:
            errors.append(
                f"severity {entry['severity']!r} not in {sorted(_SEVERITY_VALUES)}"
            )

    # Enum: what_caught_it
    if isinstance(entry.get("what_caught_it"), str):
        if entry["what_caught_it"] not in _CAUGHT_BY_VALUES:
            errors.append(
                f"what_caught_it {entry['what_caught_it']!r} not in {sorted(_CAUGHT_BY_VALUES)}"
            )

    # Nullable string fields — must be str OR None (missing key allowed)
    for field in _NULLABLE_STR_FIELDS:
        if field in entry:
            val = entry[field]
            if val is not None and not isinstance(val, str):
                errors.append(
                    f"field {field!r} must be str or None, got {type(val).__name__!r}"
                )

    return errors


def append_miss(entry: dict, path: str | Path) -> bool:
    """Validate and append one JSON line to the manifest file.

    Error contract (pins the non-fatal BC guarantee):
    1. ``..`` in path  → raise ``ValueError`` (CWE-23; caller bug).
    2. Malformed entry → raise ``ValueError`` (caller bug).
    3. I/O write failure → return ``False`` (NEVER raise — logging is a pure
       side-effect that must NEVER break a gate or build).
    4. Success → append exactly one JSON line (append-only; never rewrites prior
       lines; creates the file and parent dirs if absent) → return ``True``.

    Args:
        entry: The miss entry dict to validate then append.
        path:  Destination file path. Must not contain ``..``.

    Returns:
        True on success; False on any I/O write failure.

    Raises:
        ValueError: if ``path`` contains ``..`` or if ``entry`` fails validation.
    """
    # (1) Path-traversal guard — raises ValueError (CWE-23, caller bug)
    guarded = _guard_path(path)

    # (2) Validate entry — raises ValueError with details on failure (caller bug)
    errors = validate_miss(entry)
    if errors:
        raise ValueError(f"validation_misses: invalid entry: {errors}")

    # (3/4) Resolve + I/O — fully non-fatal. ANY failure here (an OSError, or a
    # pathological path such as an embedded NUL that makes .resolve() raise
    # ValueError) returns False — logging must NEVER raise into a gate/build.
    try:
        resolved = guarded.resolve()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        with resolved.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")
        return True
    except (OSError, ValueError) as exc:
        log.warning("validation_misses: could not write to %s: %s", path, exc)
        return False


def read_misses(path: str | Path) -> list[dict]:
    """Parse all JSON lines from the manifest; skip malformed lines (never crash).

    Args:
        path: The manifest file path.

    Returns:
        List of valid entry dicts in file order. An absent file returns ``[]``.
        Malformed lines (non-JSON, non-dict) are silently skipped so a corrupt
        line never crashes a gate/build.
    """
    p = Path(path)
    if not p.exists():
        return []
    try:
        text = p.read_text(encoding="utf-8")
    except OSError:
        return []
    results: list[dict] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        try:
            obj = json.loads(stripped)
            if isinstance(obj, dict):
                results.append(obj)
        except (json.JSONDecodeError, ValueError):
            pass  # skip malformed line — reader must never crash
    return results


def count_by_class(misses: list[dict]) -> dict:
    """Aggregate miss counts keyed by ``"{responsible_skill}::{failure_class}"``.

    Keys are strings (JSON-serializable — not tuples). Entries missing either
    field are skipped silently.

    Args:
        misses: List of miss entry dicts (e.g. as returned by ``read_misses``).

    Returns:
        Dict mapping ``f"{responsible_skill}::{failure_class}"`` to int count.
    """
    counts: dict[str, int] = {}
    for m in misses:
        if not isinstance(m, dict):
            continue  # defense-in-depth: tolerate a non-dict element, never crash
        skill = m.get("responsible_skill")
        cls = m.get("failure_class")
        if not isinstance(skill, str) or not isinstance(cls, str):
            continue
        key = f"{skill}::{cls}"
        counts[key] = counts.get(key, 0) + 1
    return counts


def recurrences(misses: list[dict], threshold: int = 3) -> list[dict]:
    """Surface failure classes whose count is >= threshold.

    Passive detector only — T1 surfaces; it does NOT propose or act (that is T2).
    The output is a list of dicts so callers can log, display, or forward it
    without any further action (observe-only / C/B-invariant).

    Args:
        misses:    List of miss entry dicts (e.g. as returned by ``read_misses``).
        threshold: Minimum count to surface (inclusive, default 3).

    Returns:
        List of ``{"key", "responsible_skill", "failure_class", "count"}`` dicts,
        one per class at or over ``threshold``. Empty list if none qualify.
    """
    counts = count_by_class(misses)
    result: list[dict] = []
    for key, count in counts.items():
        if count >= threshold:
            skill, cls = key.split("::", 1)
            result.append({
                "key": key,
                "responsible_skill": skill,
                "failure_class": cls,
                "count": count,
            })
    return result
