"""test_benchmark_def.py — TDD suite for tools/benchmark_def.py (S3, kata-loop-benchmark).

Strategy: default-FAIL (tests written before implementation; green only after
benchmark_def.py is present and correct).  All engine tests are pure (tmp_path
fixtures; no real benchmark_control calls needed — content_hash is a 64-char hex
string, so a "a"*64 stand-in is correct for validation tests).
Mutation-proof tests spawn a real subprocess via mutation_run.prove_non_vacuous.

Coverage map
------------
def_schema:
    TestDefSchema::test_required_fields_present
    TestDefSchema::test_schema_has_all_required_field_names
    TestDefSchema::test_schema_has_control_with_content_hash
    TestDefSchema::test_schema_parent_benchmark_id_nullable
    TestDefSchema::test_schema_has_provenance_with_versions
    TestDefSchema::test_schema_has_arms_array
    TestDefSchema::test_schema_description_mentions_content_hash_pin
    TestDefSchema::test_schema_description_mentions_durable_not_kata

build_def:
    TestBuildDef::test_build_def_valid_returns_dict          ← mutation-proof target (a)
    TestBuildDef::test_build_def_auto_generates_benchmark_id
    TestBuildDef::test_build_def_explicit_benchmark_id_preserved
    TestBuildDef::test_build_def_parent_benchmark_id_nullable_none
    TestBuildDef::test_build_def_parent_benchmark_id_string_preserved
    TestBuildDef::test_build_def_content_hash_pinned_in_output
    TestBuildDef::test_build_def_invalid_content_hash_short_rejects
    TestBuildDef::test_build_def_invalid_content_hash_none_rejects
    TestBuildDef::test_build_def_invalid_control_kind_rejects
    TestBuildDef::test_build_def_invalid_profile_rejects
    TestBuildDef::test_build_def_k_repeats_below_one_rejects
    TestBuildDef::test_build_def_empty_arms_rejects
    TestBuildDef::test_build_def_k_repeats_defaults_to_one
    TestBuildDef::test_build_def_schema_field_is_present

write_def / load_def:
    TestWriteLoadDef::test_write_def_creates_file
    TestWriteLoadDef::test_write_def_not_in_kata_path
    TestWriteLoadDef::test_write_load_round_trip
    TestWriteLoadDef::test_write_def_creates_parent_dirs
    TestWriteLoadDef::test_write_def_guard_rejects_traversal
    TestWriteLoadDef::test_load_def_guard_rejects_traversal
    TestWriteLoadDef::test_load_def_raises_on_missing_file

resolve_repeat_from:
    TestResolveRepeatFrom::test_resolve_path_existing_file
    TestResolveRepeatFrom::test_resolve_registry_id_maps_to_path
    TestResolveRepeatFrom::test_resolve_url_http_raises_not_implemented
    TestResolveRepeatFrom::test_resolve_url_https_raises_not_implemented
    TestResolveRepeatFrom::test_resolve_url_mixed_case_raises_not_implemented
    TestResolveRepeatFrom::test_resolve_nonexistent_path_raises
    TestResolveRepeatFrom::test_resolve_url_no_network_call

compute_delta:
    TestComputeDelta::test_compute_delta_same_definition_true        ← mutation-proof target (b)
    TestComputeDelta::test_compute_delta_same_definition_false_different_ids
    TestComputeDelta::test_compute_delta_same_definition_false_missing_ids
    TestComputeDelta::test_compute_delta_dQuality_positive
    TestComputeDelta::test_compute_delta_dQuality_negative
    TestComputeDelta::test_compute_delta_dQuality_none_when_no_rank_one
    TestComputeDelta::test_compute_delta_dCost_computed
    TestComputeDelta::test_compute_delta_dParetoPosition_has_new_and_prior
    TestComputeDelta::test_compute_delta_provenance_diff_when_different
    TestComputeDelta::test_compute_delta_provenance_diff_empty_when_same
    TestComputeDelta::test_compute_delta_pure_does_not_mutate_inputs
    TestComputeDelta::test_compute_delta_all_five_fields_in_output

exec-safety:
    TestExecSafety::test_no_subprocess_import
    TestExecSafety::test_no_eval
    TestExecSafety::test_no_exec
    TestExecSafety::test_no_shell_true
    TestExecSafety::test_no_network_fetch

Mutation proofs (spawn real subprocess via prove_non_vacuous):
    TestMutationProof::test_mutation_proof_content_hash_validation_line
    TestMutationProof::test_mutation_proof_same_definition_assignment
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Optional

import pytest

# ---------------------------------------------------------------------------
# Path setup — mirrors pattern in test_benchmark_control.py
# ---------------------------------------------------------------------------

_TESTS = Path(__file__).resolve().parent
_TOOLS = _TESTS.parent

if str(_TOOLS) not in sys.path:
    sys.path.insert(0, str(_TOOLS))

import benchmark_def  # noqa: E402


# ---------------------------------------------------------------------------
# Shared fixtures / helpers
# ---------------------------------------------------------------------------

_VALID_HASH: str = "a" * 64  # 64 lowercase hex chars — passes validation


def _make_control(
    kind: str = "code",
    ref: str = "/control/ref",
    content_hash: Optional[str] = None,
) -> dict:
    """Build a valid control dict for build_def tests."""
    return {
        "kind": kind,
        "ref": ref,
        "content_hash": content_hash if content_hash is not None else _VALID_HASH,
    }


def _make_metric(profile: str = "balanced") -> dict:
    return {"profile": profile, "weights": {}, "floor_gate": True}


def _make_arm(label: str = "baseline") -> dict:
    return {
        "label": label,
        "mode": "build",
        "modules": ["kata/module/benchmark"],
        "effort": "medium",
        "model": "sonnet",
        "routing": "default",
    }


def _make_provenance(
    tool_version: str = "0.1.0",
    skill_versions: Optional[dict] = None,
) -> dict:
    return {
        "tool_version": tool_version,
        "skill_versions": skill_versions if skill_versions is not None else {"kata-benchmark-report": "0.1.0"},
    }


def _make_valid_build_args(**overrides) -> dict:
    """Return a full set of valid keyword args for build_def."""
    base = dict(
        control=_make_control(),
        criteria_ref="criteria/embedded.json",
        arms=[_make_arm()],
        metric=_make_metric(),
        k_repeats=1,
        inputs={"system": "sys", "prompt": "do the thing", "input_refs": []},
        naming="<base>-katabenchmark{N}",
        provenance=_make_provenance(),
    )
    base.update(overrides)
    return base


def _make_scorecard(
    benchmark_id: Optional[str] = None,
    q: float = 0.8,
    c_norm: float = 0.3,
    provenance: Optional[dict] = None,
) -> dict:
    """Build a minimal scorecard dict (mirrors scorecard_schema shape from S2)."""
    arm = {
        "label": "arm1",
        "q": q,
        "c_norm": c_norm,
        "pareto": {"q": q, "c": c_norm},
        "rank": 1,
        "floor_passed": True,
    }
    sc: dict = {
        "schema": "benchmark/scorecard/v1",
        "profile": "balanced",
        "n": 1,
        "directional": True,
        "arms": [arm],
        "floor_passers": ["arm1"],
        "floor_failers": [],
        "utc": "2026-06-28T00:00:00+00:00",
    }
    if benchmark_id is not None:
        sc["benchmark_id"] = benchmark_id
    if provenance is not None:
        sc["provenance"] = provenance
    return sc


# ---------------------------------------------------------------------------
# def_schema
# ---------------------------------------------------------------------------


class TestDefSchema:
    """Unit tests for def_schema() — JSON schema (single source of truth)."""

    def _schema(self) -> dict:
        return benchmark_def.def_schema()

    def test_required_fields_present(self):
        """Schema must have a 'required' list."""
        s = self._schema()
        assert "required" in s
        assert isinstance(s["required"], list)
        assert len(s["required"]) > 0

    def test_schema_has_all_required_field_names(self):
        """All key S3 field names appear in schema required list."""
        required = self._schema()["required"]
        for field in (
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
        ):
            assert field in required, f"Schema missing required field: {field!r}"

    def test_schema_has_control_with_content_hash(self):
        """control property must declare content_hash as a required sub-field."""
        control_prop = self._schema()["properties"]["control"]
        assert "content_hash" in control_prop.get("required", [])
        assert "content_hash" in control_prop["properties"]

    def test_schema_parent_benchmark_id_nullable(self):
        """parent_benchmark_id must accept null (type includes 'null')."""
        prop = self._schema()["properties"]["parent_benchmark_id"]
        t = prop["type"]
        # Either "type": ["string", "null"] or "type": "string" + nullable flag
        assert "null" in t or t == "null", (
            "parent_benchmark_id must be nullable in the schema"
        )

    def test_schema_has_provenance_with_versions(self):
        """provenance property must require tool_version and skill_versions."""
        prov = self._schema()["properties"]["provenance"]
        assert "tool_version" in prov.get("required", [])
        assert "skill_versions" in prov.get("required", [])

    def test_schema_has_arms_array(self):
        """arms must be declared as an array type."""
        arms_prop = self._schema()["properties"]["arms"]
        assert arms_prop["type"] == "array"

    def test_schema_description_mentions_content_hash_pin(self):
        """Top-level description must mention content_hash and byte-identical replay."""
        desc = self._schema()["description"]
        assert "content_hash" in desc
        assert "byte-identical" in desc or "byte_identical" in desc.replace("-", "_")

    def test_schema_description_mentions_durable_not_kata(self):
        """Top-level description must note NOT in .kata/ (D81 durable/disposable)."""
        desc = self._schema()["description"]
        assert ".kata/" in desc or "not in .kata" in desc.lower()


# ---------------------------------------------------------------------------
# build_def
# ---------------------------------------------------------------------------


class TestBuildDef:
    """Tests for build_def(...) — pure builder, validates, pins content_hash."""

    def test_build_def_valid_returns_dict(self):
        """A fully valid call returns a dict (not an exception).

        This is also mutation-proof target (a): removing the _hash_valid line
        causes a NameError at runtime — this test then fails because build_def
        raises instead of returning a dict.
        """
        result = benchmark_def.build_def(**_make_valid_build_args())
        assert isinstance(result, dict)

    def test_build_def_auto_generates_benchmark_id(self):
        """benchmark_id is auto-generated (UUID string) when not provided."""
        result = benchmark_def.build_def(**_make_valid_build_args())
        assert "benchmark_id" in result
        bid = result["benchmark_id"]
        assert isinstance(bid, str)
        assert len(bid) > 0

    def test_build_def_explicit_benchmark_id_preserved(self):
        """An explicitly provided benchmark_id is preserved in the output."""
        result = benchmark_def.build_def(
            **_make_valid_build_args(benchmark_id="my-bench-001")
        )
        assert result["benchmark_id"] == "my-bench-001"

    def test_build_def_parent_benchmark_id_nullable_none(self):
        """parent_benchmark_id=None is accepted and stored as None (nullable)."""
        result = benchmark_def.build_def(
            **_make_valid_build_args(parent_benchmark_id=None)
        )
        assert result["parent_benchmark_id"] is None

    def test_build_def_parent_benchmark_id_string_preserved(self):
        """A string parent_benchmark_id is stored in the output."""
        result = benchmark_def.build_def(
            **_make_valid_build_args(parent_benchmark_id="parent-bench-xyz")
        )
        assert result["parent_benchmark_id"] == "parent-bench-xyz"

    def test_build_def_content_hash_pinned_in_output(self):
        """The content_hash from control is preserved in the output definition."""
        expected_hash = "b" * 64
        args = _make_valid_build_args(control=_make_control(content_hash=expected_hash))
        result = benchmark_def.build_def(**args)
        assert result["control"]["content_hash"] == expected_hash

    def test_build_def_invalid_content_hash_short_rejects(self):
        """A content_hash shorter than 64 chars raises ValueError."""
        bad_hash = "abc123"  # only 6 chars — not 64
        args = _make_valid_build_args(control=_make_control(content_hash=bad_hash))
        with pytest.raises(ValueError, match="content_hash"):
            benchmark_def.build_def(**args)

    def test_build_def_invalid_content_hash_none_rejects(self):
        """A missing (None) content_hash raises ValueError."""
        control_no_hash = {"kind": "code", "ref": "/ref"}  # no content_hash key
        args = _make_valid_build_args(control=control_no_hash)
        with pytest.raises(ValueError, match="content_hash"):
            benchmark_def.build_def(**args)

    def test_build_def_invalid_control_kind_rejects(self):
        """An invalid control.kind raises ValueError."""
        args = _make_valid_build_args(control=_make_control(kind="binary"))
        with pytest.raises(ValueError, match="kind"):
            benchmark_def.build_def(**args)

    def test_build_def_invalid_profile_rejects(self):
        """An invalid metric.profile raises ValueError."""
        args = _make_valid_build_args(metric={"profile": "unknown-mode", "weights": {}, "floor_gate": True})
        with pytest.raises(ValueError, match="profile"):
            benchmark_def.build_def(**args)

    def test_build_def_k_repeats_below_one_rejects(self):
        """k_repeats=0 raises ValueError."""
        args = _make_valid_build_args(k_repeats=0)
        with pytest.raises(ValueError, match="k_repeats"):
            benchmark_def.build_def(**args)

    def test_build_def_empty_arms_rejects(self):
        """An empty arms list raises ValueError."""
        args = _make_valid_build_args(arms=[])
        with pytest.raises(ValueError, match="arms"):
            benchmark_def.build_def(**args)

    def test_build_def_k_repeats_defaults_to_one(self):
        """k_repeats defaults to 1 when not provided (n=1 directional, DESIGN §6b)."""
        args = {k: v for k, v in _make_valid_build_args().items() if k != "k_repeats"}
        result = benchmark_def.build_def(**args)
        assert result["k_repeats"] == 1

    def test_build_def_schema_field_is_present(self):
        """Output dict carries a 'schema' version field."""
        result = benchmark_def.build_def(**_make_valid_build_args())
        assert "schema" in result
        assert "benchmark_def" in result["schema"]

    def test_build_def_research_kind_accepted(self):
        """control.kind='research' is accepted (code|research are both valid)."""
        args = _make_valid_build_args(control=_make_control(kind="research"))
        result = benchmark_def.build_def(**args)
        assert result["control"]["kind"] == "research"

    def test_build_def_cost_lean_profile_accepted(self):
        """metric.profile='cost-lean' is accepted."""
        args = _make_valid_build_args(metric=_make_metric(profile="cost-lean"))
        result = benchmark_def.build_def(**args)
        assert result["metric"]["profile"] == "cost-lean"

    def test_build_def_quality_strict_profile_accepted(self):
        """metric.profile='quality-strict' is accepted."""
        args = _make_valid_build_args(metric=_make_metric(profile="quality-strict"))
        result = benchmark_def.build_def(**args)
        assert result["metric"]["profile"] == "quality-strict"


# ---------------------------------------------------------------------------
# write_def / load_def — durable I/O, NOT .kata/
# ---------------------------------------------------------------------------


class TestWriteLoadDef:
    """Tests for write_def(path, definition) / load_def(path)."""

    def _build_sample(self) -> dict:
        return benchmark_def.build_def(**_make_valid_build_args(benchmark_id="test-id-001"))

    def test_write_def_creates_file(self, tmp_path):
        """write_def creates the file at the given path."""
        dest = tmp_path / "benchmarks" / "test-id-001" / "benchmark.def.json"
        defn = self._build_sample()
        benchmark_def.write_def(dest, defn)
        assert dest.exists()

    def test_write_def_not_in_kata_path(self, tmp_path):
        """Durable path must NOT be in .kata/ (D81 split: durable beside disposable)."""
        # This test verifies the CONVENTION: the caller must use benchmarks/<id>/...
        # not .kata/. write_def itself doesn't enforce the path prefix — it's the
        # caller's responsibility. We test by using the correct convention path.
        dest = tmp_path / "benchmarks" / "abc-123" / "benchmark.def.json"
        # Must NOT start with .kata/
        assert ".kata" not in str(dest)
        benchmark_def.write_def(dest, self._build_sample())
        assert dest.exists()

    def test_write_load_round_trip(self, tmp_path):
        """load_def(write_def(path, defn)) returns a dict equal to defn."""
        dest = tmp_path / "benchmarks" / "rt-001" / "benchmark.def.json"
        defn = self._build_sample()
        benchmark_def.write_def(dest, defn)
        loaded = benchmark_def.load_def(dest)
        assert loaded == defn

    def test_write_def_creates_parent_dirs(self, tmp_path):
        """write_def creates missing parent directories automatically."""
        dest = tmp_path / "deep" / "nested" / "dir" / "benchmark.def.json"
        assert not dest.parent.exists()
        benchmark_def.write_def(dest, self._build_sample())
        assert dest.exists()

    def test_write_def_guard_rejects_traversal(self, tmp_path):
        """write_def raises ValueError for paths containing '..'."""
        bad_path = tmp_path / ".." / "outside" / "benchmark.def.json"
        with pytest.raises(ValueError, match=r"'\.\.'|traversal"):
            benchmark_def.write_def(bad_path, self._build_sample())

    def test_load_def_guard_rejects_traversal(self, tmp_path):
        """load_def raises ValueError for paths containing '..'."""
        bad_path = tmp_path / ".." / "outside" / "benchmark.def.json"
        with pytest.raises(ValueError, match=r"'\.\.'|traversal"):
            benchmark_def.load_def(bad_path)

    def test_load_def_raises_on_missing_file(self, tmp_path):
        """load_def raises FileNotFoundError when the file does not exist."""
        missing = tmp_path / "benchmarks" / "ghost" / "benchmark.def.json"
        assert not missing.exists()
        with pytest.raises(FileNotFoundError):
            benchmark_def.load_def(missing)

    def test_write_def_is_valid_json(self, tmp_path):
        """The file written by write_def is parseable as JSON."""
        dest = tmp_path / "benchmarks" / "json-check" / "benchmark.def.json"
        benchmark_def.write_def(dest, self._build_sample())
        raw = dest.read_text(encoding="utf-8")
        parsed = json.loads(raw)
        assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# resolve_repeat_from
# ---------------------------------------------------------------------------


class TestResolveRepeatFrom:
    """Tests for resolve_repeat_from(location, *, registry)."""

    def _write_sample_def(self, tmp_path: Path) -> Path:
        """Write a sample definition and return its path."""
        dest = tmp_path / "benchmarks" / "rrf-001" / "benchmark.def.json"
        defn = benchmark_def.build_def(**_make_valid_build_args(benchmark_id="rrf-001"))
        benchmark_def.write_def(dest, defn)
        return dest

    def test_resolve_path_existing_file(self, tmp_path):
        """Resolving an existing file path returns the loaded definition."""
        dest = self._write_sample_def(tmp_path)
        loaded = benchmark_def.resolve_repeat_from(str(dest))
        assert loaded["benchmark_id"] == "rrf-001"

    def test_resolve_registry_id_maps_to_path(self, tmp_path):
        """A registry-id key that maps to a path loads the definition from that path."""
        dest = self._write_sample_def(tmp_path)
        registry = {"my-bench-v1": str(dest)}
        loaded = benchmark_def.resolve_repeat_from("my-bench-v1", registry=registry)
        assert loaded["benchmark_id"] == "rrf-001"

    def test_resolve_url_http_raises_not_implemented(self):
        """http:// location raises NotImplementedError (no network call in v1)."""
        with pytest.raises(NotImplementedError, match="v1|URL|network"):
            benchmark_def.resolve_repeat_from("http://example.com/bench.def.json")

    def test_resolve_url_https_raises_not_implemented(self):
        """https:// location raises NotImplementedError (no network call in v1)."""
        with pytest.raises(NotImplementedError, match="v1|URL|network"):
            benchmark_def.resolve_repeat_from("https://example.com/bench.def.json")

    def test_resolve_url_mixed_case_raises_not_implemented(self):
        """URL detection is case-insensitive (HTTP://, HTTPS://)."""
        with pytest.raises(NotImplementedError):
            benchmark_def.resolve_repeat_from("HTTP://example.com/bench.json")
        with pytest.raises(NotImplementedError):
            benchmark_def.resolve_repeat_from("HTTPS://example.com/bench.json")

    def test_resolve_nonexistent_path_raises(self, tmp_path):
        """A path that doesn't exist raises FileNotFoundError."""
        ghost = str(tmp_path / "benchmarks" / "ghost" / "benchmark.def.json")
        with pytest.raises(FileNotFoundError):
            benchmark_def.resolve_repeat_from(ghost)

    def test_resolve_url_no_network_call(self, monkeypatch):
        """URL resolution must NOT attempt any network call.

        We monkeypatch socket.getaddrinfo (which any HTTP fetch would invoke) to
        verify it is never called for a URL location.
        """
        import socket
        calls: list = []

        def spy_getaddrinfo(*args, **kwargs):
            calls.append(args)
            return []

        monkeypatch.setattr(socket, "getaddrinfo", spy_getaddrinfo)

        with pytest.raises(NotImplementedError):
            benchmark_def.resolve_repeat_from("https://example.com/bench.def.json")

        assert calls == [], (
            "resolve_repeat_from made a network call for a URL location — "
            "this is a forbidden unregistered network sink"
        )


# ---------------------------------------------------------------------------
# compute_delta
# ---------------------------------------------------------------------------


class TestComputeDelta:
    """Tests for compute_delta(new_scorecard, prior_scorecard) → delta dict."""

    def test_compute_delta_same_definition_true(self):
        """sameDefinition=True when both scorecards carry the same benchmark_id.

        This is also mutation-proof target (b): removing the same_definition
        assignment line causes a NameError at return time — this test then fails
        because compute_delta raises instead of returning a dict.
        """
        sc_new = _make_scorecard(benchmark_id="bench-abc", q=0.9, c_norm=0.2)
        sc_prior = _make_scorecard(benchmark_id="bench-abc", q=0.7, c_norm=0.4)
        delta = benchmark_def.compute_delta(sc_new, sc_prior)
        assert delta["sameDefinition"] is True

    def test_compute_delta_same_definition_false_different_ids(self):
        """sameDefinition=False when benchmark_ids differ."""
        sc_new = _make_scorecard(benchmark_id="bench-001")
        sc_prior = _make_scorecard(benchmark_id="bench-002")
        delta = benchmark_def.compute_delta(sc_new, sc_prior)
        assert delta["sameDefinition"] is False

    def test_compute_delta_same_definition_false_missing_ids(self):
        """sameDefinition=False when benchmark_id is absent from scorecards."""
        sc_new = _make_scorecard()   # no benchmark_id
        sc_prior = _make_scorecard()  # no benchmark_id
        delta = benchmark_def.compute_delta(sc_new, sc_prior)
        assert delta["sameDefinition"] is False

    def test_compute_delta_dQuality_positive(self):
        """dQuality is positive when new q > prior q."""
        sc_new = _make_scorecard(q=0.9)
        sc_prior = _make_scorecard(q=0.6)
        delta = benchmark_def.compute_delta(sc_new, sc_prior)
        assert delta["dQuality"] is not None
        assert delta["dQuality"] > 0

    def test_compute_delta_dQuality_negative(self):
        """dQuality is negative when new q < prior q (regression)."""
        sc_new = _make_scorecard(q=0.5)
        sc_prior = _make_scorecard(q=0.8)
        delta = benchmark_def.compute_delta(sc_new, sc_prior)
        assert delta["dQuality"] is not None
        assert delta["dQuality"] < 0

    def test_compute_delta_dQuality_none_when_no_rank_one(self):
        """dQuality is None when no rank-1 arm exists in either scorecard."""
        sc_no_rank = {
            "schema": "benchmark/scorecard/v1",
            "profile": "balanced",
            "n": 1,
            "directional": True,
            "arms": [{"label": "arm1", "q": 0.5, "floor_passed": False}],
            "floor_passers": [],
            "floor_failers": ["arm1"],
            "utc": "2026-06-28T00:00:00+00:00",
        }
        delta = benchmark_def.compute_delta(sc_no_rank, sc_no_rank)
        assert delta["dQuality"] is None

    def test_compute_delta_dCost_computed(self):
        """dCost is computed as (new c_norm) - (prior c_norm)."""
        sc_new = _make_scorecard(c_norm=0.2)
        sc_prior = _make_scorecard(c_norm=0.5)
        delta = benchmark_def.compute_delta(sc_new, sc_prior)
        assert delta["dCost"] is not None
        # New is cheaper (lower c_norm) → dCost is negative
        assert delta["dCost"] < 0

    def test_compute_delta_dParetoPosition_has_new_and_prior(self):
        """dParetoPosition is a dict with 'new' and 'prior' keys."""
        sc_new = _make_scorecard(q=0.8, c_norm=0.3)
        sc_prior = _make_scorecard(q=0.7, c_norm=0.4)
        delta = benchmark_def.compute_delta(sc_new, sc_prior)
        pareto = delta["dParetoPosition"]
        assert "new" in pareto
        assert "prior" in pareto
        # Both should be pareto dicts {q, c}
        assert pareto["new"]["q"] == pytest.approx(0.8)
        assert pareto["prior"]["q"] == pytest.approx(0.7)

    def test_compute_delta_provenance_diff_when_different(self):
        """provenanceDiff is non-empty when provenance fields differ."""
        prov_old = {"tool_version": "0.1.0", "skill_versions": {"kata-report": "0.1.0"}}
        prov_new = {"tool_version": "0.2.0", "skill_versions": {"kata-report": "0.1.0"}}
        sc_new = _make_scorecard(benchmark_id="b1", provenance=prov_new)
        sc_prior = _make_scorecard(benchmark_id="b1", provenance=prov_old)
        delta = benchmark_def.compute_delta(sc_new, sc_prior)
        diff = delta["provenanceDiff"]
        assert isinstance(diff, dict)
        assert len(diff) > 0
        assert "tool_version" in diff
        assert diff["tool_version"]["new"] == "0.2.0"
        assert diff["tool_version"]["prior"] == "0.1.0"

    def test_compute_delta_provenance_diff_empty_when_same(self):
        """provenanceDiff is an empty dict when provenance is identical."""
        prov = {"tool_version": "0.1.0", "skill_versions": {}}
        sc_new = _make_scorecard(benchmark_id="b2", provenance=prov)
        sc_prior = _make_scorecard(benchmark_id="b2", provenance=prov)
        delta = benchmark_def.compute_delta(sc_new, sc_prior)
        assert delta["provenanceDiff"] == {}

    def test_compute_delta_pure_does_not_mutate_inputs(self):
        """compute_delta must not mutate either scorecard (pure function)."""
        sc_new = _make_scorecard(benchmark_id="b3")
        sc_prior = _make_scorecard(benchmark_id="b3")
        import copy
        sc_new_copy = copy.deepcopy(sc_new)
        sc_prior_copy = copy.deepcopy(sc_prior)
        benchmark_def.compute_delta(sc_new, sc_prior)
        assert sc_new == sc_new_copy
        assert sc_prior == sc_prior_copy

    def test_compute_delta_all_five_fields_in_output(self):
        """Output dict must contain all five expected keys."""
        delta = benchmark_def.compute_delta(_make_scorecard(), _make_scorecard())
        for key in ("dQuality", "dCost", "dParetoPosition", "sameDefinition", "provenanceDiff"):
            assert key in delta, f"compute_delta output missing key: {key!r}"

    def test_compute_delta_honest_harness_delta_case(self):
        """same-definition + different provenance = honest harness-delta scenario."""
        prov_v1 = {"tool_version": "0.1.0", "skill_versions": {}}
        prov_v2 = {"tool_version": "0.2.0", "skill_versions": {}}
        sc_new = _make_scorecard(benchmark_id="bench-x", provenance=prov_v2)
        sc_prior = _make_scorecard(benchmark_id="bench-x", provenance=prov_v1)
        delta = benchmark_def.compute_delta(sc_new, sc_prior)
        # Both conditions for honest harness-delta (C-on/C-off measurement):
        assert delta["sameDefinition"] is True, "Must be same benchmark"
        assert len(delta["provenanceDiff"]) > 0, "Provenance must differ (harness changed)"


# ---------------------------------------------------------------------------
# Exec safety (mirrors TestExecSafety in test_benchmark_control.py)
# ---------------------------------------------------------------------------


class TestExecSafety:
    """Verify benchmark_def.py introduces zero new exec sinks (exec-safety.md)."""

    def _source_text(self) -> str:
        return (_TOOLS / "benchmark_def.py").read_text(encoding="utf-8")

    def test_no_subprocess_import(self):
        """benchmark_def.py must not import subprocess."""
        hits = re.findall(
            r"^\s*(?:import|from)\s+subprocess\b",
            self._source_text(),
            re.MULTILINE,
        )
        assert not hits, (
            f"subprocess import found in benchmark_def.py: {hits} — "
            "zero new exec sink is a frozen invariant (exec-safety.md)"
        )

    def test_no_eval(self):
        """benchmark_def.py must not use eval()."""
        matches = re.findall(r"\beval\s*\(", self._source_text())
        assert not matches, (
            f"benchmark_def.py must not use eval() — found: {matches}"
        )

    def test_no_exec(self):
        """benchmark_def.py must not use exec()."""
        matches = re.findall(r"\bexec\s*\(", self._source_text())
        assert not matches, (
            f"benchmark_def.py must not use exec() — found: {matches}"
        )

    def test_no_shell_true(self):
        """benchmark_def.py must not use shell=True."""
        assert "shell=True" not in self._source_text(), (
            "benchmark_def.py must not use shell=True (exec-safety.md)"
        )

    def test_no_network_fetch(self):
        """benchmark_def.py must not import urllib, requests, or httpx."""
        src = self._source_text()
        for net_mod in ("urllib", "requests", "httpx", "http.client"):
            pattern = rf"^\s*(?:import|from)\s+{re.escape(net_mod)}\b"
            hits = re.findall(pattern, src, re.MULTILINE)
            assert not hits, (
                f"benchmark_def.py imports network module {net_mod!r}: {hits} — "
                "no network fetch is a frozen invariant for this module"
            )


# ---------------------------------------------------------------------------
# Mutation proofs (spawn real subprocess via prove_non_vacuous)
# ---------------------------------------------------------------------------


class TestMutationProof:
    """Mutation-proof tests for two load-bearing lines in benchmark_def.py.

    Targets:
      (a) The _hash_valid assignment in build_def — the content-hash pinning
          validation.  Removing it causes a NameError that makes the baseline
          success test fail (testWentRed=True → nonVacuous=True).
      (b) The same_definition assignment in compute_delta — removing it causes
          a NameError in the return dict construction, failing the test that
          asserts sameDefinition=True (testWentRed=True → nonVacuous=True).

    mutation_run.prove_non_vacuous always restores the source file afterward
    (try/finally guarantee), so these tests are self-healing even on failure.
    """

    def _src(self) -> str:
        return str(_TOOLS / "benchmark_def.py")

    def _cmd(self, test_spec: str) -> str:
        """Build a pytest command targeting a specific test in this file."""
        return (
            f'cd /d "{_TOOLS}" && '
            f"{sys.executable} -m pytest "
            f'"tests/test_benchmark_def.py::{test_spec}" -q --tb=no'
        )

    def test_mutation_proof_content_hash_validation_line(self):
        """Prove _hash_valid assignment in build_def is load-bearing.

        Target line (exact, in build_def):
            ``    _hash_valid = isinstance(_content_hash, str) and len(_content_hash) == _CONTENT_HASH_LEN``

        When removed: ``_hash_valid`` is undefined → NameError on ``if not _hash_valid``
        → build_def raises at runtime → test_build_def_valid_returns_dict (which
        expects a successful return) fails → testWentRed=True.
        """
        import mutation_run

        asserted_line = (
            "    _hash_valid = isinstance(_content_hash, str) and len(_content_hash) == _CONTENT_HASH_LEN"
        )
        test_cmd = self._cmd("TestBuildDef::test_build_def_valid_returns_dict")
        verdict = mutation_run.prove_non_vacuous(self._src(), asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make test_build_def_valid_returns_dict go red — "
            "the '_hash_valid = ...' line (content-hash pinning) is not load-bearing"
        )
        assert verdict["nonVacuous"], (
            "test_build_def_valid_returns_dict must catch removal of the "
            "_hash_valid assignment (content-hash pinning)"
        )

    def test_mutation_proof_same_definition_assignment(self):
        """Prove the same_definition assignment in compute_delta is load-bearing.

        Target line (exact, in compute_delta):
            ``    same_definition = new_bid is not None and prior_bid is not None and (new_bid == prior_bid)``

        When removed: ``same_definition`` is undefined → NameError building the
        return dict → test_compute_delta_same_definition_true (which expects
        sameDefinition=True) fails → testWentRed=True.
        """
        import mutation_run

        asserted_line = (
            "    same_definition = new_bid is not None and prior_bid is not None and (new_bid == prior_bid)"
        )
        test_cmd = self._cmd("TestComputeDelta::test_compute_delta_same_definition_true")
        verdict = mutation_run.prove_non_vacuous(self._src(), asserted_line, test_cmd)
        assert verdict["testWentRed"], (
            "Mutation should make test_compute_delta_same_definition_true go red — "
            "the 'same_definition = ...' line is not load-bearing"
        )
        assert verdict["nonVacuous"], (
            "test_compute_delta_same_definition_true must catch removal of the "
            "same_definition assignment"
        )
