"""benchmark_def.py — S3 Benchmark Definition + repeat_from + delta + criteria loader.

Durable, content-pinned Benchmark Definition artifact (``benchmark.def.json``)
that fully specifies a benchmark run for **replay-by-definition** (DESIGN §4).

Split (per PLAN S3 + DESIGN §4):
  (A) Schema / build — def_schema, build_def
      Pure: validates fields, records content-hash pin, generates the definition
      dict.  content_hash must be supplied by the caller (computed via
      ``benchmark_control.content_hash`` from S4).
  (B) Durable I/O — write_def, load_def
      NOT in ``.kata/`` (D81 durable/disposable split).  Intended path:
      ``benchmarks/<id>/benchmark.def.json`` beside the run artifacts.
  (C) repeat_from resolution — resolve_repeat_from
      Resolves an existing definition by location (path / registry-id).
      URL locations are explicitly unsupported in v1 (no network call made).
  (D) Delta — compute_delta
      Pure diff of two scorecards; produces the delta-mode headline.
  (E) Embedded-criteria contract — criteria_schema, CRITERIA_FILE, load_criteria
      Pure: reads + validates the embedded criteria file from a control root.
      Bridges ``build_def.criteria_ref`` (producer) to
      ``benchmark.run_dual_gate`` ``f2p_ids`` / ``p2p_ids`` (consumer).
      Conventional path: ``.kata-benchmark/criteria.json`` within the control root
      (``CRITERIA_FILE`` constant).  ``load_criteria`` is the canonical reader.

Security posture
----------------
PURE — no subprocess, no eval, no exec, no network fetch.  CWE-23 ``..``-guard
on all path inputs (mirrors ``_guard_path`` in ``validation_misses.py`` and
``benchmark.py``).  ``protocol/exec-safety.md`` is unchanged — zero new exec
sink is a deliberate invariant.  ``resolve_repeat_from`` accepts a URL field
but raises ``NotImplementedError`` clearly rather than silently fetching
(network fetch is out of v1 scope; accepting the field without fetching keeps
the API honest for future extension without adding an unregistered network sink).
Node-IDs loaded by ``load_criteria`` are validated by ``_guard_node_id`` before
being returned — defense-in-depth ahead of the ``run_dual_gate`` INTERNAL sink.

Content-hash pinning (DESIGN §4, mutation-proven)
-------------------------------------------------
``build_def`` records ``control.content_hash`` (a 64-char SHA-256 hex string
computed by ``benchmark_control.content_hash(ref_dir)`` from S4).  This pins
the control to a byte-identical reference state.  A repeat re-clones the
byte-identical reference (drift detected and flagged via
``benchmark_control.detect_drift`` if the reference was mutated after pinning).
The ``_hash_valid`` validation line is mutation-proven — removing it causes a
NameError at definition time, which the proof test catches.

Public surfaces (cite-able by name per protocol/reuse-claims.md)
---------------------------------------------------------------
def_schema()                                    — JSON schema (single source of truth)
build_def(...)                                  — pure builder, content-hash pinned
write_def(path, definition)                     — durable write (NOT .kata/; CWE-23)
load_def(path)                                  — durable read (CWE-23)
resolve_repeat_from(location, *, registry)      — path / registry-id resolver (no network)
compute_delta(new_scorecard, prior_scorecard)   — pure delta headline
criteria_schema()                               — JSON schema for embedded criteria file
CRITERIA_FILE                                   — conventional path (.kata-benchmark/criteria.json)
load_criteria(control_dir, *, criteria_ref)     — load + validate criteria → {f2p, p2p}
"""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ALLOWED_KINDS: frozenset = frozenset({"code", "research"})
_ALLOWED_PROFILES: frozenset = frozenset({"balanced", "cost-lean", "quality-strict"})
_CONTENT_HASH_LEN: int = 64  # SHA-256 hex output length
_URL_SCHEMES: tuple = ("http://", "https://")


# ---------------------------------------------------------------------------
# CWE-23 path-traversal guard (mirrors _guard_path in validation_misses.py
# and benchmark.py)
# ---------------------------------------------------------------------------


def _guard_path(raw: str | Path) -> Path:
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
        raise ValueError(
            f"benchmark_def: refusing path with '..' traversal: {raw!r}"
        )
    return p


# ---------------------------------------------------------------------------
# (A) Schema
# ---------------------------------------------------------------------------


def def_schema() -> dict:
    """Return the JSON schema for the Benchmark Definition (single source of truth).

    Fields (DESIGN §4):
      benchmark_id         — unique identifier (UUID4)
      created              — ISO-8601 UTC timestamp
      parent_benchmark_id  — lineage pointer (nullable; None for originals)
      control              — {kind: code|research, ref, content_hash}
      criteria_ref         — reference to the embedded criteria
      arms[]               — [{label, mode, modules, effort, model, routing}]
      metric               — {profile, weights, floor_gate}
      k_repeats            — integer >= 1 (default 1 = n=1 directional)
      inputs               — {system, prompt, input_refs}
      naming               — template string '<base>-katabenchmark{N}'
      provenance           — {tool_version, skill_versions}

    Honesty (engine-pinned):
      content_hash pinned at definition time → byte-identical replay;
      parent_benchmark_id nullable → lineage traces repeat_from runs;
      same benchmark_id + newer provenance → honest harness-delta (C-on/C-off).

    Returns:
        A JSON Schema (draft 2020-12) dict for the Benchmark Definition.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "BenchmarkDefinition",
        "description": (
            "Durable, content-pinned Benchmark Definition produced by "
            "tools/benchmark_def.py (S3, kata-loop-benchmark). Fully specifies "
            "a benchmark run for replay-by-definition (DESIGN §4). "
            "control.content_hash (SHA-256, 64 hex chars) pins the reference "
            "to a byte-identical state; a repeat re-clones the byte-identical "
            "reference — drift detected via benchmark_control.detect_drift if "
            "mutated after pinning. parent_benchmark_id is nullable (None for "
            "original benchmarks; set for repeat_from lineage). Same "
            "benchmark_id + newer provenance = honest harness-delta (C-on/C-off). "
            "DURABLE: stored at benchmarks/<id>/benchmark.def.json — NOT in "
            ".kata/ (D81 durable/disposable split)."
        ),
        "type": "object",
        "required": [
            "benchmark_id",
            "created",
            "parent_benchmark_id",
            "control",
            "criteria_ref",
            "arms",
            "metric",
            "k_repeats",
            "inputs",
            "naming",
            "provenance",
        ],
        "properties": {
            "benchmark_id": {
                "type": "string",
                "description": "Unique identifier for this benchmark definition (UUID4).",
            },
            "created": {
                "type": "string",
                "description": "ISO-8601 UTC timestamp when this definition was built.",
            },
            "parent_benchmark_id": {
                "type": ["string", "null"],
                "description": (
                    "Lineage pointer: the benchmark_id this definition was derived "
                    "from (repeat_from run), or null for an original benchmark."
                ),
            },
            "control": {
                "type": "object",
                "required": ["kind", "ref", "content_hash"],
                "properties": {
                    "kind": {
                        "type": "string",
                        "enum": ["code", "research"],
                        "description": "The type of control reference.",
                    },
                    "ref": {
                        "type": "string",
                        "description": (
                            "Path or identifier of the immutable reference "
                            "directory (the control that is never mutated)."
                        ),
                    },
                    "content_hash": {
                        "type": "string",
                        "description": (
                            "SHA-256 hex digest (64 chars) of the control reference "
                            "at definition time, computed by "
                            "benchmark_control.content_hash(ref_dir). "
                            "Pins the control to a byte-identical state: a repeat "
                            "re-clones the byte-identical reference; drift is detected "
                            "and flagged via benchmark_control.detect_drift if the "
                            "reference was mutated after pinning."
                        ),
                    },
                },
                "additionalProperties": True,
                "description": "Immutable control reference (kind, ref, content_hash).",
            },
            "criteria_ref": {
                "type": "string",
                "description": (
                    "Reference to the embedded criteria (path or identifier). "
                    "The criteria contain FAIL_TO_PASS + PASS_TO_PASS test-IDs "
                    "and mutation criteria used by the benchmark scorer (S2)."
                ),
            },
            "arms": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["label", "mode", "modules", "effort", "model", "routing"],
                    "properties": {
                        "label": {
                            "type": "string",
                            "description": "Arm identifier (unique within this benchmark).",
                        },
                        "mode": {
                            "type": "string",
                            "description": "Run mode for this arm.",
                        },
                        "modules": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Module list for this arm.",
                        },
                        "effort": {
                            "type": "string",
                            "description": "Effort level for this arm.",
                        },
                        "model": {
                            "type": "string",
                            "description": "Model identifier for this arm.",
                        },
                        "routing": {
                            "type": "string",
                            "description": "Routing configuration for this arm.",
                        },
                    },
                    "additionalProperties": True,
                },
                "description": "List of benchmark arms to compare (>= 1 required).",
            },
            "metric": {
                "type": "object",
                "required": ["profile", "weights", "floor_gate"],
                "properties": {
                    "profile": {
                        "type": "string",
                        "enum": ["balanced", "cost-lean", "quality-strict"],
                        "description": "Scoring profile (matches benchmark.py _PROFILES).",
                    },
                    "weights": {
                        "type": "object",
                        "description": "Custom weight overrides (profile defaults used if empty).",
                    },
                    "floor_gate": {
                        "type": "boolean",
                        "description": "True = default-FAIL floor is active (always True in v1).",
                    },
                },
                "additionalProperties": True,
                "description": "Metric configuration: profile, weights, floor_gate.",
            },
            "k_repeats": {
                "type": "integer",
                "minimum": 1,
                "description": (
                    "Number of repeats per arm. Default 1 = n=1 directional "
                    "(DESIGN §6b R6 RESOLVED). Configurable to k for k-repeat "
                    "mean ± spread reporting."
                ),
            },
            "inputs": {
                "type": "object",
                "required": ["system", "prompt", "input_refs"],
                "properties": {
                    "system": {
                        "type": "string",
                        "description": "System prompt shared by all arms.",
                    },
                    "prompt": {
                        "type": "string",
                        "description": "User prompt shared by all arms.",
                    },
                    "input_refs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Additional input file references.",
                    },
                },
                "additionalProperties": True,
                "description": "Input specification (system, prompt, input_refs).",
            },
            "naming": {
                "type": "string",
                "description": (
                    "Naming template for benchmark copies: '<base>-katabenchmark{N}' "
                    "where N is the run index — consistent with "
                    "benchmark_control.sibling_name(base, n)."
                ),
            },
            "provenance": {
                "type": "object",
                "required": ["tool_version", "skill_versions"],
                "properties": {
                    "tool_version": {
                        "type": "string",
                        "description": "KataHarness tool version at definition time.",
                    },
                    "skill_versions": {
                        "type": "object",
                        "description": "Map of skill_name → version at definition time.",
                    },
                },
                "additionalProperties": True,
                "description": (
                    "Provenance stamp. Same benchmark_id + newer provenance = "
                    "honest harness-delta (C-on/C-off) measurement (DESIGN §4)."
                ),
            },
        },
        "additionalProperties": True,
    }


# ---------------------------------------------------------------------------
# (A) Content-addressed id derivation (DET-13, opt-in)
# ---------------------------------------------------------------------------


def content_addressed_id(content_hash: str, criteria: dict) -> str:
    """Derive a deterministic content-addressed ``benchmark_id`` (DET-13, opt-in).

    DETERMINISM-DOCTRINE law 9 ("content-addressed ids are strictly stronger and
    preferred where the content hash already exists"): a ``uuid.uuid4()`` id is
    minted-random, so the SAME benchmark definition (byte-identical control +
    criteria) yields a DIFFERENT id every build — the id is only comparable
    (``compute_delta.sameDefinition``) after the caller persists and re-reads it.
    This helper derives the id from the pinned ``control.content_hash`` plus the
    sorted criteria id-lists, so identical inputs ⇒ identical id on any machine,
    with no persist-and-reuse round-trip required.

    The digest is netstring length-prefixed (the ``benchmark_control.content_hash``
    / ``contract_edges._netstring_hash`` in-repo pattern, DETERMINISM-DOCTRINE law
    4) so different ``(content_hash, f2p, p2p)`` partitions cannot collide. Criteria
    ids are sorted before framing so caller order never changes the id.

    OPT-IN: pass the result as ``build_def(benchmark_id=...)``. The default
    ``build_def`` behavior (``uuid.uuid4()`` when ``benchmark_id is None``) is
    UNCHANGED, so existing ``repeat_from`` flows that persist+reuse a uuid are
    unaffected.

    Args:
        content_hash: The 64-char SHA-256 hex from ``benchmark_control.content_hash``.
        criteria: A ``{"f2p": [...], "p2p": [...]}`` dict (the ``load_criteria`` shape);
                  missing keys are treated as empty lists.

    Returns:
        A ``"benchmark_ca_<hex>"``-prefixed content-addressed id (deterministic).
    """
    h = hashlib.sha256()
    for label, value in (
        ("content_hash", content_hash),
        ("f2p", "\n".join(sorted(criteria.get("f2p", []) or []))),
        ("p2p", "\n".join(sorted(criteria.get("p2p", []) or []))),
    ):
        for part in (label, value):
            b = part.encode("utf-8")
            h.update(f"{len(b)}:".encode("ascii"))
            h.update(b)
    return f"benchmark_ca_{h.hexdigest()}"


# ---------------------------------------------------------------------------
# (A) Build
# ---------------------------------------------------------------------------


def build_def(
    *,
    benchmark_id: str | None = None,
    parent_benchmark_id: str | None = None,
    control: dict,
    criteria_ref: str,
    arms: list[dict],
    metric: dict,
    k_repeats: int = 1,
    inputs: dict,
    naming: str,
    provenance: dict,
    created: str | None = None,
) -> dict:
    """Build a validated Benchmark Definition dict (pure).

    Content-hash pinning (DESIGN §4, mutation-proven):
        ``control.content_hash`` must be a 64-character hex string (SHA-256)
        produced by ``benchmark_control.content_hash(ref_dir)`` from S4.
        This pins the control reference to a byte-identical state.  A repeat
        re-clones the byte-identical reference; drift is detected and flagged
        via ``benchmark_control.detect_drift`` if the reference was mutated
        after pinning.  The ``_hash_valid`` line below is mutation-proven:
        removing it causes a NameError that the proof test catches.

    ``parent_benchmark_id`` is **nullable**: None for an original benchmark;
    set to the parent's benchmark_id for a ``repeat_from`` derived run.

    Args:
        benchmark_id:        Optional UUID string.  Auto-generated (UUID4) if None.
        parent_benchmark_id: Lineage pointer.  None for an original benchmark;
                             str UUID for a repeat_from derivation.
        control:             Dict with {kind, ref, content_hash}.
                             kind must be 'code' or 'research'.
                             content_hash must be a 64-char lowercase hex string
                             (compute via benchmark_control.content_hash).
        criteria_ref:        Reference to the embedded criteria file.  Points at
                             ``CRITERIA_FILE`` (``.kata-benchmark/criteria.json``)
                             within the control root.  ``load_criteria`` is the
                             canonical reader that resolves this field and returns
                             the ``{f2p, p2p}`` id-lists consumed by
                             ``benchmark.run_dual_gate``.
        arms:                Non-empty list of arm dicts, each with
                             {label, mode, modules, effort, model, routing}.
        metric:              Dict with {profile, weights, floor_gate}.
                             profile: 'balanced' | 'cost-lean' | 'quality-strict'.
        k_repeats:           Integer >= 1 (default 1 = n=1 directional).
        inputs:              Dict with {system, prompt, input_refs}.
        naming:              Naming template, e.g. '<base>-katabenchmark{N}'.
        provenance:          Dict with {tool_version, skill_versions}.
        created:             ISO-8601 UTC timestamp.  Auto-generated if None.

    Returns:
        A definition dict conforming to def_schema().

    Raises:
        ValueError: on any validation failure (invalid kind, bad content_hash,
                    invalid profile, k_repeats < 1, empty arms list).
    """
    # -- Validate control.kind --
    kind = control.get("kind")
    if kind not in _ALLOWED_KINDS:
        raise ValueError(
            f"benchmark_def: control.kind must be one of {sorted(_ALLOWED_KINDS)}, "
            f"got {kind!r}"
        )

    # -- Content-hash pin (DESIGN §4, mutation-proven) --
    # The caller computes this via benchmark_control.content_hash(ref_dir) (S4).
    # 64-char SHA-256 hex — required for byte-identical replay on repeat_from.
    # A repeat re-clones the byte-identical reference; drift is flagged by detect_drift.
    _content_hash = control.get("content_hash")
    _hash_valid = isinstance(_content_hash, str) and len(_content_hash) == _CONTENT_HASH_LEN
    if not _hash_valid:
        raise ValueError(
            f"benchmark_def: control.content_hash must be a {_CONTENT_HASH_LEN}-character "
            "hex string (compute via benchmark_control.content_hash); required for "
            "byte-identical replay (DESIGN §4, mutation-proven)"
        )

    # -- Validate metric.profile --
    profile = metric.get("profile")
    if profile not in _ALLOWED_PROFILES:
        raise ValueError(
            f"benchmark_def: metric.profile must be one of {sorted(_ALLOWED_PROFILES)}, "
            f"got {profile!r}"
        )

    # -- Validate k_repeats --
    if not isinstance(k_repeats, int) or isinstance(k_repeats, bool) or k_repeats < 1:
        raise ValueError(
            f"benchmark_def: k_repeats must be an integer >= 1, got {k_repeats!r}"
        )

    # -- Validate arms --
    if not isinstance(arms, list) or len(arms) == 0:
        raise ValueError("benchmark_def: arms must be a non-empty list")

    # -- Generate IDs / timestamps --
    bid = benchmark_id if benchmark_id is not None else str(uuid.uuid4())
    ts = created if created is not None else datetime.now(tz=UTC).isoformat()

    return {
        "schema": "benchmark_def/v1",
        "benchmark_id": bid,
        "created": ts,
        "parent_benchmark_id": parent_benchmark_id,
        "control": {
            "kind": kind,
            "ref": control.get("ref", ""),
            "content_hash": _content_hash,
        },
        "criteria_ref": criteria_ref,
        "arms": list(arms),
        "metric": dict(metric),
        "k_repeats": k_repeats,
        "inputs": dict(inputs),
        "naming": naming,
        "provenance": dict(provenance),
    }


# ---------------------------------------------------------------------------
# (B) Durable I/O — NOT .kata/ (D81 durable/disposable split)
# ---------------------------------------------------------------------------


def write_def(path: str | Path, definition: dict) -> None:
    """Write *definition* as durable JSON to *path* (CWE-23 guarded).

    Durable storage (D81): the definition is the pointable, replayable artifact.
    Intended path: ``benchmarks/<id>/benchmark.def.json`` — NOT in ``.kata/``.
    The disposable run artifacts (scorecard JSON, spawned copies) live in
    ``.kata/`` and sibling copy directories; this durable artifact is kept
    separate so it can be pointed to by other systems and registries.

    ``benchmark_id`` persist-and-reuse contract (DET-13, DETERMINISM-DOCTRINE law
    9): ``build_def`` mints a RANDOM ``uuid.uuid4()`` ``benchmark_id`` when the
    caller passes none, and ``created`` defaults to the wall clock — so the id is
    NOT reproducible across builds. ``compute_delta.sameDefinition`` compares two
    scorecards' ``benchmark_id`` values, so a ``repeat_from`` run MUST reuse the
    STORED id from this durable artifact (load it via :func:`load_def` /
    :func:`resolve_repeat_from`, then pass it back as
    ``build_def(benchmark_id=...)``) — NOT mint a fresh one, which would read as a
    different definition. Callers wanting a reproducible id WITHOUT the
    persist-and-reuse round-trip should derive it via :func:`content_addressed_id`
    and pass it to ``build_def``.

    Args:
        path:       Destination path.  Must not contain ``..`` (CWE-23).
        definition: Dict produced by :func:`build_def`.

    Raises:
        ValueError: if *path* contains ``..`` traversal (CWE-23).
        OSError:    on I/O failure.
    """
    dest = _guard_path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(definition, indent=2, ensure_ascii=False), encoding="utf-8")


def load_def(path: str | Path) -> dict:
    """Load a Benchmark Definition dict from *path* (CWE-23 guarded).

    Args:
        path: Path to a JSON file previously written by :func:`write_def`.

    Returns:
        The parsed definition dict.

    Raises:
        ValueError:          if *path* contains ``..`` traversal (CWE-23).
        FileNotFoundError:   if the file does not exist.
        json.JSONDecodeError: if the file is not valid JSON.
    """
    src = _guard_path(path)
    return json.loads(src.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# (C) repeat_from resolution (path / registry-id; URL → NotImplemented)
# ---------------------------------------------------------------------------


def resolve_repeat_from(
    location: str,
    *,
    registry: dict[str, str] | None = None,
) -> dict:
    """Resolve an existing Benchmark Definition by location.

    Resolution order (v1):
      1. **URL detection** — if *location* starts with ``http://`` or
         ``https://``: raises ``NotImplementedError`` immediately.
         URL fetch is explicitly out of v1 scope.  The field is accepted (so
         a definition file can carry a URL for future use) but no network call
         is ever made — that would be an unregistered network sink against the
         exec-safety invariant.  Callers must supply a local path or registry-id
         in v1.
      2. **Registry lookup** — if *registry* is provided and *location* is a key:
         the mapped path is resolved via CWE-23 guard → :func:`load_def`.
      3. **Path fallback** — *location* is treated as a file path, CWE-23
         guarded, and loaded via :func:`load_def`.

    Args:
        location: A file path string, registry id, or URL.
                  URLs are detected by ``http://`` or ``https://`` prefix
                  (case-insensitive).
        registry: Optional ``{registry_id: path_str}`` lookup table.
                  Injectable for tests and future registry backends.
                  None = empty registry (path-only resolution).

    Returns:
        The loaded definition dict.

    Raises:
        NotImplementedError: if *location* is a URL (``http://`` / ``https://``).
                             No network call is made (out of v1 scope).
        ValueError:          if the resolved path contains ``..`` (CWE-23).
        FileNotFoundError:   if the definition file does not exist.
        json.JSONDecodeError: if the file is not valid JSON.
    """
    # 1. URL detection — reject, never fetch (network is out of v1 scope)
    loc_lower = location.lower()
    for scheme in _URL_SCHEMES:
        if loc_lower.startswith(scheme):
            raise NotImplementedError(
                f"benchmark_def.resolve_repeat_from: URL locations are not "
                f"supported in v1 (no network fetch — register a local path or "
                f"registry id instead): {location!r}"
            )

    # 2. Registry lookup (injectable for tests / future backends)
    _registry = registry or {}
    if location in _registry:
        return load_def(_registry[location])

    # 3. Path fallback — CWE-23 guard is applied inside load_def
    return load_def(location)


# ---------------------------------------------------------------------------
# (D) Delta — compute_delta (pure)
# ---------------------------------------------------------------------------


def _top_arm(scorecard: dict) -> dict | None:
    """Return the rank-1 arm (best among floor-passers), or None if absent."""
    for arm in scorecard.get("arms", []):
        if arm.get("rank") == 1:
            return arm
    return None


def compute_delta(new_scorecard: dict, prior_scorecard: dict) -> dict:
    """Compute the delta-mode headline between a new scorecard and a prior one.

    Produces the four-field delta report (DESIGN §4):
      dQuality        — Q improvement of the new run's best arm vs the prior
      dCost           — C_norm improvement of the new run's best arm vs the prior
      dParetoPosition — Pareto points (new, prior) for the rank-1 arms
      sameDefinition  — True iff both scorecards carry the same non-null
                        benchmark_id (mutation-proven: removing the assignment
                        causes NameError that the proof test catches)
      provenanceDiff  — key-level diff between provenance fields; empty dict if
                        identical; non-empty + sameDefinition = honest
                        harness-delta (C-on/C-off measurement, DESIGN §4)

    sameDefinition = True + non-empty provenanceDiff = the C-on/C-off number:
    the same benchmark run, with a newer harness version — an honest measure of
    harness improvement (D99).

    Args:
        new_scorecard:   New run's scorecard dict.  May carry optional
                         ``benchmark_id`` and ``provenance`` keys (injected by
                         S6 wiring; scorecard_schema() allows additionalProperties).
        prior_scorecard: Prior run's scorecard (same shape).

    Returns:
        ``{dQuality, dCost, dParetoPosition, sameDefinition, provenanceDiff}``

    Pure: no subprocess, no eval, no exec, no network, no side effects.
    """
    # -- Scalar deltas from the rank-1 (best) arm in each scorecard --
    new_top = _top_arm(new_scorecard)
    prior_top = _top_arm(prior_scorecard)

    dq_new = new_top.get("q") if new_top else None
    dq_prior = prior_top.get("q") if prior_top else None
    dQuality = (
        (dq_new - dq_prior)
        if (dq_new is not None and dq_prior is not None)
        else None
    )

    dc_new = new_top.get("c_norm") if new_top else None
    dc_prior = prior_top.get("c_norm") if prior_top else None
    dCost = (
        (dc_new - dc_prior)
        if (dc_new is not None and dc_prior is not None)
        else None
    )

    dParetoPosition = {
        "new": new_top.get("pareto") if new_top else None,
        "prior": prior_top.get("pareto") if prior_top else None,
    }

    # -- sameDefinition: both scorecards trace to the same benchmark_id --
    # MUTATION-PROVEN: removing this exact line causes NameError at return time.
    new_bid = new_scorecard.get("benchmark_id")
    prior_bid = prior_scorecard.get("benchmark_id")
    same_definition = new_bid is not None and prior_bid is not None and (new_bid == prior_bid)

    # -- provenanceDiff: key-level diff of provenance fields --
    # same_definition=True + non-empty provenanceDiff → honest harness-delta.
    new_prov = new_scorecard.get("provenance") or {}
    prior_prov = prior_scorecard.get("provenance") or {}
    provenance_diff: dict = {}
    for key in sorted(set(new_prov) | set(prior_prov)):
        nv = new_prov.get(key)
        pv = prior_prov.get(key)
        if nv != pv:
            provenance_diff[key] = {"new": nv, "prior": pv}

    return {
        "dQuality": dQuality,
        "dCost": dCost,
        "dParetoPosition": dParetoPosition,
        "sameDefinition": same_definition,
        "provenanceDiff": provenance_diff,
    }


# ---------------------------------------------------------------------------
# (E) Embedded-criteria contract — criteria_schema, CRITERIA_FILE, load_criteria
# ---------------------------------------------------------------------------

#: Conventional path for the embedded criteria file within a control root.
#:
#: ``build_def``'s ``criteria_ref`` field resolves to this path (relative to
#: the control root).  ``load_criteria`` is the canonical reader that produces
#: the ``{f2p, p2p}`` id-lists consumed by ``benchmark.run_dual_gate``.
#:
#: The file lives in a hidden ``.kata-benchmark/`` directory at the control
#: root — separate from ``.kata/`` (run-time disposable artifacts) and from
#: the project's own test tree.  It is committed with the control and never
#: auto-generated at run time.
CRITERIA_FILE: str = ".kata-benchmark/criteria.json"


def criteria_schema() -> dict:
    """Return the JSON schema for the embedded criteria file (single source of truth).

    The criteria file lives at ``CRITERIA_FILE`` (``.kata-benchmark/criteria.json``)
    within the control root.  It declares two test-ID lists consumed by the
    dual-gate scorer (DESIGN §3.1, SWE-bench F2P/P2P model):

    - ``fail_to_pass``: tests expected to FAIL on the unmodified control and
      PASS after the agent's changes.  Non-empty list = the primary gate.
    - ``pass_to_pass``: tests expected to PASS both before and after the
      agent's changes.  Regression guard.

    Both lists may be empty.  Node-IDs are relative to the control root, e.g.
    ``tests/test_x.py::test_name`` (``path::name`` shape, ``shell=False``-safe).

    Producer ↔ consumer bridge:
        ``build_def``'s ``criteria_ref`` field points at this file.
        ``load_criteria`` is the reader that resolves ``criteria_ref`` and
        returns the ``{f2p, p2p}`` dict fed to ``benchmark.run_dual_gate``.

    Returns:
        A JSON Schema (draft 2020-12) dict for the criteria file.
    """
    return {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "BenchmarkCriteria",
        "description": (
            "Embedded benchmark criteria file for a KataHarness control "
            "(DESIGN §2.4, §3.1). Declares FAIL_TO_PASS and PASS_TO_PASS "
            "test-ID lists (SWE-bench F2P/P2P model). Node-IDs are relative "
            "to the control root (e.g. 'tests/test_x.py::test_name'). "
            "Stored at .kata-benchmark/criteria.json within the control root "
            "(CRITERIA_FILE). "
            "criteria_ref in build_def points at this file; "
            "load_criteria is the reader that produces {f2p, p2p} for run_dual_gate."
        ),
        "type": "object",
        "required": ["fail_to_pass", "pass_to_pass"],
        "properties": {
            "fail_to_pass": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Tests expected to FAIL on the unmodified control and PASS "
                    "after the agent's changes (SWE-bench F2P model). "
                    "Node-IDs relative to the control root. May be empty."
                ),
            },
            "pass_to_pass": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Tests expected to PASS both before and after the agent's "
                    "changes (regression guard). Node-IDs relative to the "
                    "control root. May be empty."
                ),
            },
        },
        "additionalProperties": True,
    }


def _guard_node_id(node_id: str) -> str:
    """Validate a pytest node-ID before feeding it to run_dual_gate (defense-in-depth).

    Node-IDs must satisfy all of:
      - Non-empty string.
      - Not start with ``-`` (no CLI flag injection — argv list, not shell string).
      - Not contain ``..`` (no path traversal).
      - Contain ``::`` (``path::name`` shape, as in ``run_named_test``).

    ``run_dual_gate``'s own ``_guard_node_id`` re-checks at the INTERNAL sink
    boundary.  This call is the earlier defense layer in the criteria loader.

    Args:
        node_id: The candidate node-ID string.

    Returns:
        The node_id string if it passes all checks.

    Raises:
        ValueError: if the node_id fails any validation check.
    """
    if not isinstance(node_id, str) or not node_id:
        raise ValueError(
            f"benchmark_def: node-ID must be a non-empty string, got {node_id!r}"
        )
    if node_id.startswith("-"):
        raise ValueError(
            f"benchmark_def: node-ID must not start with '-' (CLI flag injection "
            f"risk in argv list): {node_id!r}"
        )
    if ".." in node_id:
        raise ValueError(
            f"benchmark_def: node-ID must not contain '..' (path traversal "
            f"risk; CWE-23): {node_id!r}"
        )
    if "::" not in node_id:
        raise ValueError(
            f"benchmark_def: node-ID must be 'path::name' shape (must contain "
            f"'::', e.g. 'tests/test_x.py::test_name'): {node_id!r}"
        )
    return node_id


def load_criteria(
    control_dir: str | Path,
    *,
    criteria_ref: str | None = None,
) -> dict:
    """Load and validate the embedded benchmark criteria from a control directory.

    Reads the criteria file at ``CRITERIA_FILE`` (``.kata-benchmark/criteria.json``)
    within *control_dir*, or from an explicit *criteria_ref* path if supplied.
    Returns ``{"f2p": [...], "p2p": [...]}`` — the test-ID lists consumed by
    ``benchmark.run_dual_gate(clone_root, f2p_ids, p2p_ids)``.

    This is the producer ↔ consumer bridge::

        # build_def records criteria_ref (producer)
        defn = build_def(..., criteria_ref=CRITERIA_FILE, ...)

        # load_criteria reads it (consumer → run_dual_gate)
        ids = load_criteria(clone_root)
        run_dual_gate(clone_root, ids["f2p"], ids["p2p"])

    Missing file (honest empty):
        Returns ``{"f2p": [], "p2p": []}`` — the scorer then flags
        ``dual_gate_evaluated: false``.  A missing file is NOT free credit.

    Malformed file (fail-closed):
        Raises ``ValueError`` — invalid JSON, missing required keys, wrong
        structure, or any node-ID that fails ``_guard_node_id``.

    CWE-23 guard:
        Both *control_dir* and *criteria_ref* are ``..``-guarded at the
        boundary.  Node-IDs in the file are also validated by ``_guard_node_id``
        (defense-in-depth; ``run_dual_gate`` re-checks at the INTERNAL sink).

    Args:
        control_dir:  Root of the control directory (the immutable reference;
                      never mutated).  Must not contain ``..`` (CWE-23).
        criteria_ref: Optional explicit path to the criteria file.  When
                      supplied, overrides the conventional ``CRITERIA_FILE``
                      path.  Must not contain ``..`` (CWE-23).  When None,
                      defaults to ``control_dir / CRITERIA_FILE``.

    Returns:
        ``{"f2p": [<node-id>, ...], "p2p": [<node-id>, ...]}``

    Raises:
        ValueError: if *control_dir* or *criteria_ref* contain ``..`` (CWE-23),
                    if the file is malformed JSON, if required keys are missing
                    or have wrong types, or if a node-ID fails ``_guard_node_id``.

    Pure: no subprocess, no eval, no exec, no network fetch.
    """
    # CWE-23 guard on control_dir — use returned Path object
    guarded_dir = _guard_path(control_dir)

    # Resolve criteria file path (explicit override takes precedence)
    if criteria_ref is not None:
        criteria_path = _guard_path(criteria_ref)
    else:
        criteria_path = guarded_dir / CRITERIA_FILE

    # Missing file → honest empty (not an error; scorer flags dual_gate_evaluated:false)
    if not criteria_path.exists():
        return {"f2p": [], "p2p": []}

    # Read and parse JSON — fail-closed on any parse error
    raw = criteria_path.read_text(encoding="utf-8")
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"benchmark_def.load_criteria: criteria file is not valid JSON "
            f"({criteria_path!r}): {exc}"
        ) from exc

    # Root must be a JSON object
    if not isinstance(data, dict):
        raise ValueError(
            f"benchmark_def.load_criteria: criteria file root must be a JSON "
            f"object, got {type(data).__name__!r} ({criteria_path!r})"
        )

    # Required keys + list types (fail-closed)
    for key in ("fail_to_pass", "pass_to_pass"):
        if key not in data:
            raise ValueError(
                f"benchmark_def.load_criteria: criteria file missing required "
                f"key {key!r} ({criteria_path!r})"
            )
        if not isinstance(data[key], list):
            raise ValueError(
                f"benchmark_def.load_criteria: criteria key {key!r} must be a "
                f"list, got {type(data[key]).__name__!r} ({criteria_path!r})"
            )

    # Node-ID validation (defense-in-depth; run_dual_gate._guard_node_id re-checks)
    # MUTATION-PROVEN: removing the _guard_node_id(nid) call in the f2p loop
    # causes test_load_criteria_node_id_dotdot_in_f2p_raises to go red.
    f2p: list[str] = []
    for nid in data["fail_to_pass"]:
        _guard_node_id(nid)
        f2p.append(nid)
    p2p: list[str] = []
    for nid in data["pass_to_pass"]:
        _guard_node_id(nid)
        p2p.append(nid)

    return {"f2p": f2p, "p2p": p2p}
