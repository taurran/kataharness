"""Tests for gate_emit.py — the thin artifact-emitting orchestrator.

TDD discipline: these tests were written FIRST, before gate_emit.py existed.
All tests are PURE — no real subprocess, no real git, deterministic timestamps.

Coverage:
- RESULT.json written with the pinned schema keys + correct injected counts
- footprint.json reflects in/out partition + withinFootprint
- mutation.json aggregates allNonVacuous (True when all bite, False when one vacuous)
- summary dict shape and values
- out_dir auto-created when it does not exist
"""

from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest


# ---------------------------------------------------------------------------
# Test helpers / fixtures
# ---------------------------------------------------------------------------

FIXED_UTC = "2026-06-20T12:00:00+00:00"
FAKE_BASELINE_SHA = "aaaaaaaaaaaa"
FAKE_RESULT_SHA = "bbbbbbbbbbbb"
GATE_NAME = "smoke"
COMMAND = "uv run pytest -q"

# A fake runner that returns canned output (40 passed, 2 failed, 1 skipped)
FAKE_OUTPUT = "40 passed, 2 failed, 1 skipped in 3.14s"
FAKE_EXIT_CODE = 1  # non-zero because there are failures


def fake_runner(command: str):
    """Pure fake — never touches subprocess."""
    return FAKE_OUTPUT, FAKE_EXIT_CODE


def fake_runner_passing(command: str):
    """Pure fake — returns all-pass output."""
    return "72 passed in 0.53s", 0


# ---------------------------------------------------------------------------
# Core import
# ---------------------------------------------------------------------------


def test_gate_emit_module_importable():
    """gate_emit must be importable without side-effects."""
    import gate_emit  # noqa: F401


# ---------------------------------------------------------------------------
# RESULT.json schema tests
# ---------------------------------------------------------------------------


def test_result_json_written_with_pinned_schema(tmp_path):
    """RESULT.json must contain every key defined by run_result.build_result."""
    import gate_emit

    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
        )

    result_path = tmp_path / "RESULT.json"
    assert result_path.exists(), "RESULT.json must be written"
    data = json.loads(result_path.read_text(encoding="utf-8"))

    # Pinned schema (from run_result.build_result docstring)
    required_keys = {
        "gateName", "command", "exitCode",
        "passed", "failed", "skipped",
        "stdoutTail", "baselineSha", "resultSha", "utc",
    }
    missing = required_keys - set(data.keys())
    assert not missing, f"RESULT.json missing keys: {missing}"


def test_result_json_correct_counts(tmp_path):
    """RESULT.json must reflect counts parsed from the injected runner output."""
    import gate_emit

    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
        )

    data = json.loads((tmp_path / "RESULT.json").read_text(encoding="utf-8"))
    assert data["passed"] == 40
    assert data["failed"] == 2
    assert data["skipped"] == 1
    assert data["exitCode"] == FAKE_EXIT_CODE
    assert data["gateName"] == GATE_NAME
    assert data["command"] == COMMAND
    assert data["baselineSha"] == FAKE_BASELINE_SHA
    assert data["resultSha"] == FAKE_RESULT_SHA
    assert data["utc"] == FIXED_UTC


def test_result_json_stdout_tail(tmp_path):
    """stdoutTail in RESULT.json must contain the runner's output."""
    import gate_emit

    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
        )

    data = json.loads((tmp_path / "RESULT.json").read_text(encoding="utf-8"))
    assert FAKE_OUTPUT in data["stdoutTail"]


# ---------------------------------------------------------------------------
# footprint.json tests
# ---------------------------------------------------------------------------


def test_footprint_json_written(tmp_path):
    """footprint.json must be written by emit_gate_artifacts."""
    import gate_emit

    with patch("footprint.changed_since", return_value=["tools/gate_emit.py"]), \
         patch("footprint.diff_stat", return_value="1 file changed"):
        gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
        )

    assert (tmp_path / "footprint.json").exists()


def test_footprint_json_within_footprint_true(tmp_path):
    """withinFootprint must be True when all changed files are inside the declared footprint."""
    import gate_emit

    with patch("footprint.changed_since", return_value=["tools/gate_emit.py"]), \
         patch("footprint.diff_stat", return_value="1 file changed"):
        summary = gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
        )

    data = json.loads((tmp_path / "footprint.json").read_text(encoding="utf-8"))
    assert data["withinFootprint"] is True
    assert summary["withinFootprint"] is True


def test_footprint_json_within_footprint_false(tmp_path):
    """withinFootprint must be False when a changed file is outside the declared footprint."""
    import gate_emit

    # tools/gate_emit.py is inside "tools/", README.md is outside
    changed = ["tools/gate_emit.py", "README.md"]
    with patch("footprint.changed_since", return_value=changed), \
         patch("footprint.diff_stat", return_value="2 files changed"):
        summary = gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
        )

    data = json.loads((tmp_path / "footprint.json").read_text(encoding="utf-8"))
    assert data["withinFootprint"] is False
    assert summary["withinFootprint"] is False
    assert "README.md" in data["outOfFootprint"]


def test_footprint_json_required_keys(tmp_path):
    """footprint.json must contain the keys produced by footprint.manifest."""
    import gate_emit

    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
        )

    data = json.loads((tmp_path / "footprint.json").read_text(encoding="utf-8"))
    for key in ("footprint", "changed", "inFootprint", "outOfFootprint", "withinFootprint", "diffstat"):
        assert key in data, f"footprint.json missing key: {key!r}"


# ---------------------------------------------------------------------------
# mutation.json tests
# ---------------------------------------------------------------------------


def test_mutation_json_not_written_when_no_records(tmp_path):
    """mutation.json must NOT be written when mutation_records is None."""
    import gate_emit

    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        summary = gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
            mutation_records=None,
        )

    assert not (tmp_path / "mutation.json").exists()
    assert summary["mutationPath"] is None


def test_mutation_json_all_non_vacuous_true(tmp_path):
    """allNonVacuous must be True when all records have nonVacuous=True."""
    import gate_emit

    records = [
        {"testWentRed": True, "nonVacuous": True},
        {"testWentRed": True, "nonVacuous": True},
    ]

    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        summary = gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
            mutation_records=records,
        )

    data = json.loads((tmp_path / "mutation.json").read_text(encoding="utf-8"))
    assert data["allNonVacuous"] is True
    assert data["records"] == records
    assert summary["mutationPath"] is not None


def test_mutation_json_all_non_vacuous_false_when_one_vacuous(tmp_path):
    """allNonVacuous must be False when at least one record has nonVacuous=False."""
    import gate_emit

    records = [
        {"testWentRed": True, "nonVacuous": True},
        {"testWentRed": False, "nonVacuous": False},  # vacuous
    ]

    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
            mutation_records=records,
        )

    data = json.loads((tmp_path / "mutation.json").read_text(encoding="utf-8"))
    assert data["allNonVacuous"] is False


def test_mutation_json_empty_list_all_non_vacuous_true(tmp_path):
    """allNonVacuous must be True for an empty records list (vacuous truth / no counter-evidence)."""
    import gate_emit

    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
            mutation_records=[],
        )

    data = json.loads((tmp_path / "mutation.json").read_text(encoding="utf-8"))
    assert data["allNonVacuous"] is True
    assert data["records"] == []


# ---------------------------------------------------------------------------
# Summary dict tests
# ---------------------------------------------------------------------------


def test_summary_dict_shape(tmp_path):
    """emit_gate_artifacts must return a dict with the documented keys."""
    import gate_emit

    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        summary = gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
        )

    required_keys = {
        "resultPath", "footprintPath", "mutationPath",
        "withinFootprint", "passed", "failed", "skipped", "exitCode",
    }
    missing = required_keys - set(summary.keys())
    assert not missing, f"Summary dict missing keys: {missing}"


# ---------------------------------------------------------------------------
# Path-traversal guard (CWE-23)
# ---------------------------------------------------------------------------


def test_safe_path_rejects_dotdot_traversal():
    """_safe_path must raise ValueError for any path containing '..'."""
    import gate_emit

    with pytest.raises(ValueError, match="refusing path with '\\.\\.'" ):
        gate_emit._safe_path("../../etc/passwd")


def test_safe_path_rejects_dotdot_in_middle():
    """_safe_path must reject '..' even when embedded mid-path."""
    import gate_emit

    with pytest.raises(ValueError):
        gate_emit._safe_path("valid/../../escape")


def test_safe_path_accepts_normal_path(tmp_path):
    """_safe_path must resolve a clean path without raising."""
    import gate_emit

    result = gate_emit._safe_path(str(tmp_path / "sub" / "dir"))
    from pathlib import Path
    assert isinstance(result, Path)


def test_summary_dict_paths_are_pathlike(tmp_path):
    """resultPath and footprintPath in the summary must point to existing files."""
    import gate_emit

    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        summary = gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
        )

    assert Path(summary["resultPath"]).exists()
    assert Path(summary["footprintPath"]).exists()


def test_summary_dict_counts_match_result_json(tmp_path):
    """passed/failed/skipped/exitCode in summary must match RESULT.json values."""
    import gate_emit

    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        summary = gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            runner=fake_runner,
            utc=FIXED_UTC,
        )

    data = json.loads((tmp_path / "RESULT.json").read_text(encoding="utf-8"))
    assert summary["passed"] == data["passed"]
    assert summary["failed"] == data["failed"]
    assert summary["skipped"] == data["skipped"]
    assert summary["exitCode"] == data["exitCode"]


# ---------------------------------------------------------------------------
# out_dir auto-creation test
# ---------------------------------------------------------------------------


def test_out_dir_auto_created(tmp_path):
    """emit_gate_artifacts must create out_dir if it does not exist."""
    import gate_emit

    nested = tmp_path / "deep" / "nested" / ".kata"
    assert not nested.exists(), "nested dir must not exist before the call"

    with patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=nested,
            runner=fake_runner,
            utc=FIXED_UTC,
        )

    assert nested.exists()
    assert (nested / "RESULT.json").exists()
    assert (nested / "footprint.json").exists()


# ---------------------------------------------------------------------------
# Default runner injection test (runner defaults to run_result.run_gate)
# ---------------------------------------------------------------------------


def test_default_runner_is_run_gate(tmp_path):
    """When no runner is passed, run_result.run_gate must be used (patched so no subprocess)."""
    import gate_emit
    import run_result

    with patch.object(run_result, "run_gate", side_effect=fake_runner_passing) as mock_runner, \
         patch("footprint.changed_since", return_value=[]), \
         patch("footprint.diff_stat", return_value=""):
        gate_emit.emit_gate_artifacts(
            gate_name=GATE_NAME,
            command=COMMAND,
            footprint=["tools/"],
            baseline_sha=FAKE_BASELINE_SHA,
            result_sha=FAKE_RESULT_SHA,
            out_dir=tmp_path,
            utc=FIXED_UTC,
            # NOTE: no runner= arg — should default to run_result.run_gate
        )

    mock_runner.assert_called_once_with(COMMAND)
