"""Tests for kata_dispatch.py — cross-model dispatch (N1 brief, N2 adapter, N3 result).

The dispatch chain is proven end-to-end with a STUB runner (no live Codex), exactly the
test seam DESIGN §7 names. The real subprocess runner is gated on the CLI being installed.
"""

from __future__ import annotations

import json

import pytest

import kata_dispatch as kd
import kata_roles as kr


# ----- N1 build_brief -----
def test_build_brief_shape():
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="check it",
                       result_path=".kata/dispatch/t1/RESULT.json", sandbox="read-only")
    assert b["taskId"] == "t1" and b["role"] == "validator" and b["platform"] == "codex"
    assert b["boundaries"]["sandbox"] == "read-only"
    assert b["resultPath"].endswith("RESULT.json")
    assert b["outputContract"] == "validator"


def test_build_brief_rejects_bad_role_and_sandbox():
    with pytest.raises(ValueError, match="unknown role"):
        kd.build_brief("t", "banana", "codex", model="m", objective="o", result_path="r")
    with pytest.raises(ValueError, match="sandbox"):
        kd.build_brief("t", "coder", "codex", model="m", objective="o", result_path="r", sandbox="rw")
    with pytest.raises(ValueError, match="required"):
        kd.build_brief("t", "coder", "codex", model="m", objective="", result_path="r")


# ----- N2 codex_command -----
def test_codex_command_readonly():
    b = kd.build_brief("t1", "validator", "codex", model="gpt-5-codex", objective="o",
                       result_path="RESULT.json", sandbox="read-only")
    cmd = kd.codex_command(b, "/wt")
    assert cmd[0:2] == ["codex", "exec"]
    assert "--sandbox" in cmd and cmd[cmd.index("--sandbox") + 1] == "read-only"
    assert cmd[cmd.index("--model") + 1] == "gpt-5-codex"
    assert cmd[cmd.index("--output-schema") + 1] == "RESULT.json"


def test_codex_command_write_sandbox():
    b = kd.build_brief("t2", "coder", "codex", model="m", objective="o", result_path="R", sandbox="write")
    cmd = kd.codex_command(b, "/wt")
    assert cmd[cmd.index("--sandbox") + 1] == "workspace-write"


# ----- N3 normalize / build_result -----
def test_normalize_validator():
    payload = kd.normalize("validator", json.dumps({"verdict": "hold", "findings": [{"t": "x"}]}))
    assert payload["verdict"] == "hold" and len(payload["findings"]) == 1


def test_normalize_validator_missing_verdict_raises():
    with pytest.raises(ValueError, match="verdict"):
        kd.normalize("validator", json.dumps({"findings": []}))


def test_normalize_evaluator():
    payload = kd.normalize("evaluator", json.dumps({"score": 0.4, "decision": "reroll", "reason": "weak"}))
    assert payload["decision"] == "reroll" and payload["score"] == 0.4


def test_build_result_rejects_bad_status():
    with pytest.raises(ValueError, match="status"):
        kd.build_result("t", "validator", "codex", "m", "bogus", {})


# ----- N2 dispatch with a STUB runner -----
def _stub_runner(result_obj, exit_code=0, stdout="ok"):
    """A runner that simulates a worker writing `result_obj` as its result file."""
    def run(cmd, cwd, result_path, timeout):
        return exit_code, stdout, json.dumps(result_obj)
    return run


def test_dispatch_success_validator():
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R")
    res = kd.dispatch(b, "/wt", runner=_stub_runner({"verdict": "ship", "findings": []}))
    assert res["status"] == "completed"
    assert res["payload"]["verdict"] == "ship"


def test_dispatch_nonzero_exit_is_failed():
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R")
    res = kd.dispatch(b, "/wt", runner=_stub_runner({}, exit_code=2))
    assert res["status"] == "failed"


def test_dispatch_unparseable_result_is_failed():
    def bad_runner(cmd, cwd, result_path, timeout):
        return 0, "ok", "not json{{"
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R")
    res = kd.dispatch(b, "/wt", runner=bad_runner)
    assert res["status"] == "failed"


def test_dispatch_timeout():
    import subprocess

    def timeout_runner(cmd, cwd, result_path, timeout):
        raise subprocess.TimeoutExpired(cmd, timeout)
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R")
    res = kd.dispatch(b, "/wt", runner=timeout_runner)
    assert res["status"] == "timeout"


def test_dispatch_unknown_platform_raises():
    b = kd.build_brief("t1", "validator", "kiro", model="m", objective="o", result_path="R")
    with pytest.raises(ValueError, match="no dispatch adapter"):
        kd.dispatch(b, "/wt", runner=_stub_runner({}))


# ----- THE END-TO-END PROOF: roles -> brief -> dispatch(stub) -> normalized verdict -----
def test_end_to_end_validator_on_codex(tmp_path):
    # 1) routing config: validator -> codex (confirmed)
    resolved = kr.resolve_roles({"validator": {"platform": "codex", "model": "gpt-5-codex"}}, ["codex"])
    assert resolved["validator"]["platform"] == "codex"
    assert kr.is_multimodal(resolved) is True

    # 2) build the cross-model brief for a validator task
    assign = resolved["validator"]
    brief = kd.build_brief(
        "t-007", "validator", assign["platform"], model=assign["model"],
        objective="Adversarially validate the diff in this worktree.",
        result_path="RESULT.json", sandbox="read-only",
        acceptance="Return verdict ship|hold with findings.",
    )

    # 3) dispatch with a stub Codex that returns a HOLD verdict (the worker's structured output)
    codex_output = {"verdict": "hold", "findings": [{"severity": "MAJOR", "note": "unguarded path"}]}
    result = kd.dispatch(brief, str(tmp_path), runner=_stub_runner(codex_output, stdout="codex done"))

    # 4) the normalized envelope: dispatch succeeded, validator verdict came back
    assert result["status"] == "completed"        # dispatch outcome
    assert result["platform"] == "codex"
    assert result["payload"]["verdict"] == "hold"  # the role verdict (distinct axis)
    assert result["payload"]["findings"][0]["severity"] == "MAJOR"
