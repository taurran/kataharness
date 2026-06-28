"""recurrence_detect.py — T2 actionable-recurrence detector engine (Slice S1).

Turns the BUILT, observe-only validation-miss manifest (T1, validation_misses.py)
into an **act-but-gated** signal: a PURE detector that clusters the manifest by
``responsible_skill`` × ``failure_class``, counts DISTINCT runs (not raw rows),
applies a severity-aware threshold (BLOCKER → 2, else → 3), skips clusters that
already have a handled-sidecar marker, and flags off-vocabulary clusters.

It READS the manifest + handled sidecar and COMPUTES verdict dicts. It changes no
gate verdict, edits no skill/protocol/tool, and never merges anything (the T2 C/B
invariant). The only write surface is the append-only handled sidecar
``append_handled`` (the ``proposed`` marker), a file append mirroring
``validation_misses.append_miss``.

Security posture
----------------
PURE — no subprocess, no eval, no exec, no shell. Plain dict/set/list logic + JSON
read + a ``..``-guarded (CWE-23) file append. Assertable by source scan (see
test_recurrence_detect.py::TestExecSafety). No new execution sink; no new registry
row in protocol/exec-safety.md.

Public surfaces (cite-able by name per protocol/reuse-claims.md)
----------------------------------------------------------------
distinct_run_counts        — per cluster, count of DISTINCT run identities
cluster_severity_tier      — BLOCKER if any entry is BLOCKER, else MAJOR/MINOR
actionable_recurrences     — severity-aware / distinct-run / handled-aware detector
read_handled               — parse the handled sidecar (tolerant; absent ⇒ [])
append_handled             — validate + append one handled record (non-fatal I/O)
handled_schema             — single source of truth for a handled record
detect_from_paths          — thin I/O convenience (reads both files, calls the core)

Reuses the T1 data layer by import: ``validation_misses.read_misses`` (manifest
read) and ``validation_misses.is_known_class`` (off-vocabulary flag).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import validation_misses

log = logging.getLogger(__name__)

# Cluster key shape mirrors validation_misses.count_by_class:
#   f"{responsible_skill}::{failure_class}"
_CLUSTER_SEP = "::"

# Handled-sidecar record vocabulary.
_STATUS_VALUES: frozenset[str] = frozenset({"proposed", "guarded"})
_HANDLED_REQUIRED_STR_FIELDS: frozenset[str] = frozenset({
    "ts",
    "key",
    "responsible_skill",
    "failure_class",
    "status",
    "proposal_ref",
})
_HANDLED_NULLABLE_STR_FIELDS: frozenset[str] = frozenset({"guard_ref"})
_HANDLED_ALL_FIELDS: frozenset[str] = (
    _HANDLED_REQUIRED_STR_FIELDS | _HANDLED_NULLABLE_STR_FIELDS
)


# ---------------------------------------------------------------------------
# Path-traversal guard (CWE-23) — mirrors validation_misses._guard_path
# ---------------------------------------------------------------------------

def _guard_path(raw: str | Path) -> Path:
    """Reject paths containing a ``..`` traversal component (CWE-23). Does NOT resolve.

    Resolution is deliberately left to the caller's non-fatal I/O block so a
    pathological path surfaces as a write *failure* (return False), not a raise
    into a gate/build. Only the ``..`` caller-bug raises here. Mirrors
    ``validation_misses._guard_path``.

    Raises:
        ValueError: if ``raw`` contains a ``..`` path component.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"recurrence_detect: refusing path with '..' traversal: {raw!r}"
        )
    return p


# ---------------------------------------------------------------------------
# Pure clustering / counting
# ---------------------------------------------------------------------------

def distinct_run_counts(
    misses: list[dict],
    *,
    run_id_key: str = "run_id",
    fallback_key: str = "ts",
) -> dict:
    """Per cluster, the count of DISTINCT run identities (NOT raw rows).

    Cluster key = ``f"{responsible_skill}::{failure_class}"`` (the T1
    ``count_by_class`` key shape). An entry's run identity is ``entry[run_id_key]``
    ONLY when it is a non-empty, non-whitespace string; **otherwise (None, missing,
    or blank/whitespace) it falls back to ``entry[fallback_key]``** (the ``ts``
    legacy fallback for entries logged before run_id stamping, AND the fail-honest
    path for a buggy emitter that stamps ``""`` / ``"  "``). Two misses sharing a
    run_id count as ONE run; two with distinct run_id count as TWO.

    Args:
        misses:       List of miss entry dicts (e.g. from ``read_misses``).
        run_id_key:   Field holding the per-run identity (default ``"run_id"``).
        fallback_key: Field used when run_id is absent/None/blank (default ``"ts"``).

    Returns:
        Dict mapping cluster key to the count of distinct run identities.
    """
    clusters: dict[str, set] = {}
    for m in misses:
        if not isinstance(m, dict):
            continue  # defense-in-depth: tolerate a non-dict element, never crash
        skill = m.get("responsible_skill")
        cls = m.get("failure_class")
        if not isinstance(skill, str) or not isinstance(cls, str):
            continue
        key = f"{skill}{_CLUSTER_SEP}{cls}"
        # Run identity = run_id ONLY when it is a non-empty, non-whitespace str.
        # A blank/whitespace run_id is treated as ABSENT and falls back to ts
        # (fail HONEST): a buggy emitter stamping "" / "  " must NOT silently
        # collapse a whole cluster to one run and suppress all recurrence detection.
        rid = m.get(run_id_key)
        if isinstance(rid, str) and rid.strip():
            identity = rid
        else:
            identity = m.get(fallback_key)
        clusters.setdefault(key, set()).add(identity)
    return {key: len(identities) for key, identities in clusters.items()}


def cluster_severity_tier(misses_for_cluster: list[dict]) -> str:
    """Return the cluster's severity tier driving the threshold.

    ``"BLOCKER"`` if ANY entry has ``severity == "BLOCKER"``, else the highest of
    ``"MAJOR"`` / ``"MINOR"`` present (``"MINOR"`` when neither is present).

    Args:
        misses_for_cluster: The entries belonging to one cluster.

    Returns:
        One of ``"BLOCKER"`` | ``"MAJOR"`` | ``"MINOR"``.
    """
    severities = {
        m.get("severity") for m in misses_for_cluster if isinstance(m, dict)
    }
    if "BLOCKER" in severities:
        return "BLOCKER"
    if "MAJOR" in severities:
        return "MAJOR"
    return "MINOR"


def actionable_recurrences(
    misses: list[dict],
    handled: list[dict],
    *,
    default_threshold: int = 3,
    blocker_threshold: int = 2,
    run_id_key: str = "run_id",
    fallback_key: str = "ts",
) -> list[dict]:
    """The severity-aware / distinct-run / handled-aware actionable detector.

    For each cluster (``f"{responsible_skill}::{failure_class}"``):
      - threshold = ``blocker_threshold`` if the cluster's severity tier is
        ``"BLOCKER"``, else ``default_threshold``;
      - distinct-run count comes from ``distinct_run_counts`` (distinct run_id,
        ts-fallback — NOT raw rows);
      - the cluster is **actionable** iff ``distinct_runs >= threshold`` AND its
        key is NOT already in ``handled`` (no re-proposal).

    Off-vocabulary clusters (``failure_class`` not in the curated enum) are still
    RETURNED — flagged via ``off_vocabulary: True``, never dropped.

    Args:
        misses:            List of miss entry dicts (e.g. from ``read_misses``).
        handled:           List of handled-sidecar records (from ``read_handled``).
        default_threshold: Distinct-run threshold for non-BLOCKER tiers (default 3).
        blocker_threshold: Distinct-run threshold for the BLOCKER tier (default 2).
        run_id_key:        Field holding per-run identity (default ``"run_id"``).
        fallback_key:      Field used when run_id is absent/None (default ``"ts"``).

    Returns:
        List of dicts, one per actionable cluster, each with keys: ``key``,
        ``responsible_skill``, ``failure_class``, ``distinct_runs``, ``raw_count``,
        ``severity_tier``, ``threshold``, ``off_vocabulary``, ``evidence``.
    """
    # Group entries per cluster (reuse the T1 clustering convention).
    clusters: dict[str, list[dict]] = {}
    for m in misses:
        if not isinstance(m, dict):
            continue
        skill = m.get("responsible_skill")
        cls = m.get("failure_class")
        if not isinstance(skill, str) or not isinstance(cls, str):
            continue
        key = f"{skill}{_CLUSTER_SEP}{cls}"
        clusters.setdefault(key, []).append(m)

    run_counts = distinct_run_counts(
        misses, run_id_key=run_id_key, fallback_key=fallback_key
    )
    handled_keys = {
        h.get("key") for h in handled if isinstance(h, dict)
    }

    results: list[dict] = []
    for key, entries in clusters.items():
        skill, cls = key.split(_CLUSTER_SEP, 1)
        tier = cluster_severity_tier(entries)
        threshold = blocker_threshold if tier == "BLOCKER" else default_threshold
        distinct_runs = run_counts.get(key, 0)
        if key in handled_keys:
            continue  # handled-aware skip: already proposed/guarded → no re-proposal
        if distinct_runs >= threshold:
            results.append({
                "key": key,
                "responsible_skill": skill,
                "failure_class": cls,
                "distinct_runs": distinct_runs,
                "raw_count": len(entries),
                "severity_tier": tier,
                "threshold": threshold,
                "off_vocabulary": not validation_misses.is_known_class(cls),
                "evidence": entries,
            })
    return results


# ---------------------------------------------------------------------------
# Handled sidecar (.planning/recurrence-handled.jsonl)
# ---------------------------------------------------------------------------

def handled_schema() -> dict:
    """Return the handled-sidecar record schema — single source of truth.

    Returns a dict keyed by field name. The sidecar is append-only (durable,
    committed; sibling of the manifest). Two marker statuses with LOCKED ownership:
    ``proposed`` (appended by kata-improve when it auto-drafts — T2's only auto
    write) and ``guarded`` (appended by the human/kata-improve at guard-merge time
    — OUTSIDE T2's auto-scope; T2 never marks ``guarded``).

    Fields:
        ts, key, responsible_skill, failure_class, status, proposal_ref, guard_ref.
    """
    return {
        "ts": {
            "type": "str",
            "description": "ISO8601 timestamp when the marker was recorded",
        },
        "key": {
            "type": "str",
            "description": "Cluster key f'{responsible_skill}::{failure_class}'",
        },
        "responsible_skill": {
            "type": "str",
            "description": "Clustering key (NOT necessarily the fix location)",
        },
        "failure_class": {
            "type": "str",
            "description": "The recurring class this marker handles",
        },
        "status": {
            "type": "str",
            "enum": sorted(_STATUS_VALUES),
            "description": (
                "proposed (auto, by kata-improve at draft) | guarded "
                "(human/merge-time, outside T2 auto-scope)"
            ),
        },
        "proposal_ref": {
            "type": "str",
            "description": (
                "Path to the drafted proposal, e.g. "
                ".planning/specs/recurrence-hardening/PROPOSAL-<failure_class>.md"
            ),
        },
        "guard_ref": {
            "type": "str|null",
            "description": "Doc/test that shipped the guard, or null until guarded",
        },
    }


def validate_handled(record: dict) -> list[str]:
    """Validate a handled-sidecar record; return a list of error strings ([] = valid).

    Checks: ``record`` is a dict; required str fields present and non-None str;
    ``status`` in {proposed, guarded}; ``guard_ref`` is str or None (missing-key
    allowed); no extra keys.

    Args:
        record: The candidate handled record dict.

    Returns:
        A list of human-readable error strings. Empty list means valid.
    """
    errors: list[str] = []

    if not isinstance(record, dict):
        return ["record must be a dict"]

    extra = set(record.keys()) - _HANDLED_ALL_FIELDS
    if extra:
        errors.append(f"extra keys not allowed: {sorted(extra)}")

    for field in sorted(_HANDLED_REQUIRED_STR_FIELDS):
        if field not in record:
            errors.append(f"missing required field: {field!r}")
        elif not isinstance(record[field], str):
            errors.append(
                f"field {field!r} must be str, got {type(record[field]).__name__!r}"
            )

    if isinstance(record.get("status"), str):
        if record["status"] not in _STATUS_VALUES:
            errors.append(
                f"status {record['status']!r} not in {sorted(_STATUS_VALUES)}"
            )

    for field in _HANDLED_NULLABLE_STR_FIELDS:
        if field in record:
            val = record[field]
            if val is not None and not isinstance(val, str):
                errors.append(
                    f"field {field!r} must be str or None, got {type(val).__name__!r}"
                )

    return errors


def read_handled(path: str | Path) -> list[dict]:
    """Parse all JSON lines from the handled sidecar; skip malformed lines.

    Mirrors ``validation_misses.read_misses``: an absent file returns ``[]``;
    malformed (non-JSON, non-dict) lines are silently skipped so a corrupt line
    never crashes a gate/build.

    Args:
        path: The handled-sidecar file path.

    Returns:
        List of valid record dicts in file order; ``[]`` for an absent file.
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


def append_handled(record: dict, path: str | Path) -> bool:
    """Validate and append one JSON line to the handled sidecar.

    Error contract (mirrors ``validation_misses.append_miss`` — the non-fatal BC
    guarantee):
    1. ``..`` in path  → raise ``ValueError`` (CWE-23; caller bug).
    2. Malformed record → raise ``ValueError`` (caller bug).
    3. I/O write failure → return ``False`` (NEVER raise — a handled marker is a
       pure side-effect that must NEVER break a gate or build).
    4. Success → append exactly one JSON line (append-only; never rewrites prior
       lines; creates the file and parent dirs if absent) → return ``True``.

    Args:
        record: The handled record dict to validate then append.
        path:   Destination sidecar path. Must not contain ``..``.

    Returns:
        True on success; False on any I/O write failure.

    Raises:
        ValueError: if ``path`` contains ``..`` or if ``record`` fails validation.
    """
    # (1) Path-traversal guard — raises ValueError (CWE-23, caller bug)
    guarded = _guard_path(path)

    # (2) Validate record — raises ValueError with details on failure (caller bug)
    errors = validate_handled(record)
    if errors:
        raise ValueError(f"recurrence_detect: invalid handled record: {errors}")

    # (3/4) Resolve + I/O — fully non-fatal. ANY failure here (an OSError, or a
    # pathological path such as an embedded NUL that makes .resolve() raise
    # ValueError) returns False — a handled marker must NEVER raise into a gate.
    try:
        resolved = guarded.resolve()
        resolved.parent.mkdir(parents=True, exist_ok=True)
        with resolved.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")
        return True
    except (OSError, ValueError) as exc:
        log.warning("recurrence_detect: could not write to %s: %s", path, exc)
        return False


# ---------------------------------------------------------------------------
# Thin I/O convenience (on-demand + orchestrate-hook callers)
# ---------------------------------------------------------------------------

def detect_from_paths(
    misses_path: str | Path,
    handled_path: str | Path,
    *,
    default_threshold: int = 3,
    blocker_threshold: int = 2,
    run_id_key: str = "run_id",
    fallback_key: str = "ts",
) -> list[dict]:
    """Read the manifest + handled sidecar and return the actionable recurrences.

    Thin convenience for the on-demand operator call and the kata-orchestrate
    Final-gate hook. Reads both files via the tolerant readers, then calls the
    pure core ``actionable_recurrences``. No exec; no write.

    Args:
        misses_path:       Path to the validation-miss manifest (.jsonl).
        handled_path:      Path to the handled sidecar (.jsonl).
        default_threshold: Distinct-run threshold for non-BLOCKER tiers (default 3).
        blocker_threshold: Distinct-run threshold for the BLOCKER tier (default 2).
        run_id_key:        Field holding per-run identity (default ``"run_id"``).
        fallback_key:      Field used when run_id is absent/None (default ``"ts"``).

    Returns:
        The ``actionable_recurrences`` result list.
    """
    misses = validation_misses.read_misses(misses_path)
    handled = read_handled(handled_path)
    return actionable_recurrences(
        misses,
        handled,
        default_threshold=default_threshold,
        blocker_threshold=blocker_threshold,
        run_id_key=run_id_key,
        fallback_key=fallback_key,
    )
