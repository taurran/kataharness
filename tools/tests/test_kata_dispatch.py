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
    assert cmd[cmd.index("-o") + 1] == "RESULT.json"   # capture final message to the result file
    assert "--output-schema" not in cmd                # not the result path (NIT-1 fix)


def test_codex_command_write_sandbox():
    b = kd.build_brief("t2", "coder", "codex", model="m", objective="o", result_path="R", sandbox="write")
    cmd = kd.codex_command(b, "/wt")
    assert cmd[cmd.index("--sandbox") + 1] == "workspace-write"


def test_codex_command_has_skip_git_repo_check():
    """codex-cli 0.142.3 refuses to run outside a trusted git dir without --skip-git-repo-check.

    The flag must be present and ordered exec → --skip-git-repo-check → --cd ...,
    while keeping exec/--cd/--sandbox/--model/-o/prompt intact.
    """
    b = kd.build_brief("t1", "validator", "codex", model="gpt-5-codex", objective="o",
                       result_path="RESULT.json", sandbox="read-only")
    cmd = kd.codex_command(b, "/wt")
    assert "--skip-git-repo-check" in cmd
    # order: exec → skip-flag → cd
    assert cmd[0:3] == ["codex", "exec", "--skip-git-repo-check"]
    assert cmd.index("--skip-git-repo-check") < cmd.index("--cd")
    # everything else still intact
    assert cmd[cmd.index("--cd") + 1] == "/wt"
    assert cmd[cmd.index("--sandbox") + 1] == "read-only"
    assert cmd[cmd.index("--model") + 1] == "gpt-5-codex"
    assert cmd[cmd.index("-o") + 1] == "RESULT.json"
    assert cmd[-1] == kd._brief_prompt(b, capture="emit")


def test_subprocess_runner_closes_stdin(tmp_path, monkeypatch):
    """_subprocess_runner must pass stdin=DEVNULL so codex never blocks reading stdin.

    codex exec reads instructions from an open stdin and blocks until timeout otherwise
    (the live 120s-timeout finding). Capture the kwargs passed to subprocess.run.
    """
    import subprocess

    captured = {}

    class _Proc:
        returncode = 0
        stdout = "ok"

    def fake_run(cmd, **kwargs):
        captured.update(kwargs)
        return _Proc()

    monkeypatch.setattr(kd.subprocess, "run", fake_run)
    kd._subprocess_runner(["codex", "exec"], str(tmp_path), "RESULT.json", 600)
    assert captured.get("stdin") is subprocess.DEVNULL
    # existing behaviour preserved
    assert captured.get("capture_output") is True
    assert captured.get("text") is True
    assert captured.get("timeout") == 600


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


def test_dispatch_non_object_result_is_failed_not_crash():
    # valid JSON but a top-level ARRAY must fail gracefully, not raise (D98 MAJOR-1 fix)
    def array_runner(cmd, cwd, result_path, timeout):
        return 0, "ok", "[1, 2, 3]"
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R")
    res = kd.dispatch(b, "/wt", runner=array_runner)
    assert res["status"] == "failed"
    assert "error" in res["payload"]


def test_build_brief_rejects_traversal_result_path():
    with pytest.raises(ValueError, match="'\\.\\.'"):
        kd.build_brief("t", "validator", "codex", model="m", objective="o",
                       result_path="../../etc/evil.json")


def test_safe_result_path_under_cwd(tmp_path):
    rp = kd._safe_result_path("sub/RESULT.json", str(tmp_path))
    assert str(rp).startswith(str(tmp_path.resolve()))


def test_safe_result_path_rejects_escape(tmp_path):
    with pytest.raises(ValueError):
        kd._safe_result_path("../escape.json", str(tmp_path))


def test_dispatch_unroutable_platform_fails_gracefully():
    # a confirmed-but-undispatchable platform must FAIL, not crash the loop (red-team F3)
    # "cursor" is deferred (L-MP1 / PLAN.md); "kiro" is now routable so is no longer the example
    b = kd.build_brief("t1", "validator", "cursor", model="m", objective="o", result_path="R")
    res = kd.dispatch(b, "/wt", runner=_stub_runner({}))
    assert res["status"] == "failed"
    assert "no dispatch adapter" in res["payload"]["error"]


def test_dispatch_empty_result_researcher_is_failed():
    # empty result must default-FAIL for researcher (red-team F1), not report a None-filled "completed"
    def empty_runner(cmd, cwd, result_path, timeout):
        return 0, "ok", ""
    b = kd.build_brief("t1", "researcher", "codex", model="m", objective="o", result_path="R")
    res = kd.dispatch(b, "/wt", runner=empty_runner)
    assert res["status"] == "failed"


def test_dispatch_empty_result_coder_is_failed():
    def empty_runner(cmd, cwd, result_path, timeout):
        return 0, "ok", "{}"
    b = kd.build_brief("t1", "coder", "codex", model="m", objective="o", result_path="R", sandbox="write")
    res = kd.dispatch(b, "/wt", runner=empty_runner)
    assert res["status"] == "failed"


def test_normalize_researcher_requires_claim():
    payload = kd.normalize("researcher", json.dumps({"claim": "x", "groundsToPlan": "y"}))
    assert payload["claim"] == "x"
    with pytest.raises(ValueError, match="claim"):
        kd.normalize("researcher", json.dumps({"source": "s"}))


def test_normalize_evaluator_score_range():
    kd.normalize("evaluator", json.dumps({"score": 0.5, "decision": "accept"}))  # ok
    with pytest.raises(ValueError, match="score"):
        kd.normalize("evaluator", json.dumps({"score": "banana", "decision": "accept"}))
    with pytest.raises(ValueError, match="score"):
        kd.normalize("evaluator", json.dumps({"score": 1.5, "decision": "accept"}))


def test_build_brief_rejects_absolute_result_path():
    with pytest.raises(ValueError, match="worktree-relative"):
        kd.build_brief("t", "validator", "codex", model="m", objective="o", result_path="/etc/evil.json")


def test_brief_prompt_conveys_inputs_and_ownership():
    b = kd.build_brief("t", "coder", "codex", model="m", objective="do it", result_path="R",
                       inputs=["a.py"], owned_files=["b.py"], sandbox="write")
    prompt = kd._brief_prompt(b)
    assert "a.py" in prompt and "b.py" in prompt
    assert "do not write files" in prompt.casefold()


# ----- Slice C: kiro dispatch adapter (MAJOR-1 + kiro_command) -----

def test_brief_prompt_capture_emit_unchanged():
    """codex path (capture="emit"): unchanged wording — still says 'do not write files'."""
    b = kd.build_brief("t", "researcher", "codex", model="m", objective="research it",
                       result_path="RESULT.json")
    prompt = kd._brief_prompt(b, capture="emit")
    assert "do not write files" in prompt.casefold()
    assert "RESULT.json" not in prompt or "Write" not in prompt  # no write-to-file instruction


def test_brief_prompt_capture_write_contains_result_path():
    """kiro path (capture="write"): prompt instructs the worker to WRITE resultPath itself.

    MAJOR-1 regression guard: kiro has no -o capture (DESIGN §4 N2); the worker must write.
    """
    b = kd.build_brief("t", "researcher", "kiro", model="m", objective="research it",
                       result_path="RESULT.json")
    prompt = kd._brief_prompt(b, capture="write")
    # must contain the file-write instruction …
    assert "Write" in prompt
    assert "RESULT.json" in prompt
    # … and must NOT contain the emit/no-write instruction
    assert "do not write files" not in prompt.casefold()
    assert "emit" not in prompt.casefold()


def test_kiro_command_argv_shape():
    """kiro_command returns the documented kiro-cli headless argv (DESIGN §4 N2)."""
    b = kd.build_brief("t", "researcher", "kiro", model="m", objective="research it",
                       result_path="RESULT.json")
    cmd = kd.kiro_command(b, "/wt")
    assert isinstance(cmd, list)
    assert cmd[0] == "kiro-cli"
    assert cmd[1] == "chat"
    assert "--no-interactive" in cmd
    assert "--agent" in cmd
    assert cmd[cmd.index("--agent") + 1] == "researcher"
    # prompt (last arg) must contain the write-to-file instruction, not the emit instruction
    prompt = cmd[-1]
    assert "Write" in prompt and "RESULT.json" in prompt
    assert "do not write files" not in prompt.casefold()


def test_dispatch_researcher_on_kiro_returns_completed_envelope(tmp_path):
    """End-to-end: kiro brief → dispatch(stub) → completed envelope with researcher payload.

    Mirrors test_end_to_end_validator_on_codex for the kiro/researcher path (Slice C acceptance).
    The stub runner simulates a kiro worker that wrote resultPath itself (no -o capture).
    """
    b = kd.build_brief(
        "t-kiro-1", "researcher", "kiro", model="m",
        objective="Research the topic.",
        result_path="RESULT.json",
        acceptance="Return claim + groundsToPlan.",
    )
    kiro_output = {
        "claim": "kiro proved it",
        "source": "https://example.com",
        "confidence": 0.9,
        "groundsToPlan": "Use approach X.",
    }
    result = kd.dispatch(b, str(tmp_path), runner=_stub_runner(kiro_output, stdout="kiro done"))
    assert result["status"] == "completed"
    assert result["platform"] == "kiro"
    # normalized researcher payload shape
    assert result["payload"]["claim"] == "kiro proved it"
    assert result["payload"]["source"] == "https://example.com"
    assert result["payload"]["confidence"] == 0.9
    assert result["payload"]["groundsToPlan"] == "Use approach X."


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
