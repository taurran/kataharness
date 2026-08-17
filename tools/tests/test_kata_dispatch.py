"""Tests for kata_dispatch.py — cross-model dispatch (N1 brief, N2 adapter, N3 result).

The dispatch chain is proven end-to-end with a STUB runner (no live Codex), exactly the
test seam DESIGN §7 names. The real subprocess runner is gated on the CLI being installed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import kata_dispatch as kd
import kata_roles as kr

# BL-F01: build_brief now REQUIRES a plan_path and refuses to build against a plan that
# is not frozen (kata_restore.assert_frozen). These two fixtures let every OTHER test in
# this file — which is not itself testing the freeze gate — pass a plan that satisfies it
# without each test having to write its own PLAN.md.
_FROZEN_PLAN = Path(__file__).parent / "fixtures" / "frozen_plan" / "PLAN.md"
_DRAFT_PLAN = Path(__file__).parent / "fixtures" / "draft_plan" / "PLAN.md"


# ----- N1 build_brief -----
def test_build_brief_shape():
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="check it",
                       result_path=".kata/dispatch/t1/RESULT.json", sandbox="read-only",
                       plan_path=_FROZEN_PLAN)
    assert b["taskId"] == "t1" and b["role"] == "validator" and b["platform"] == "codex"
    assert b["boundaries"]["sandbox"] == "read-only"
    assert b["resultPath"].endswith("RESULT.json")
    assert b["outputContract"] == "validator"


# ----- BL-F01: the freeze chokepoint -----
def test_build_brief_refuses_non_frozen_plan():
    """A draft (not-yet-frozen) plan must be refused — RAISE, never a degraded brief."""
    with pytest.raises(ValueError, match="not frozen"):
        kd.build_brief("t1", "validator", "codex", model="m", objective="o",
                       result_path="R", plan_path=_DRAFT_PLAN)


def test_build_brief_succeeds_on_frozen_plan():
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o",
                       result_path="R", plan_path=_FROZEN_PLAN)
    assert b["taskId"] == "t1"


def test_build_brief_plan_path_is_required_kwarg():
    """plan_path has NO default — an omitted plan silently bypassing the gate (D136) is
    exactly the posture this chokepoint exists to prevent."""
    with pytest.raises(TypeError, match="plan_path"):
        kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R")


def test_build_brief_delegates_freeze_check_to_kata_restore_assert_frozen(monkeypatch):
    """Proves build_brief's gate is kata_restore.assert_frozen itself (not a re-implementation
    that could silently drift from it) — patch assert_frozen and see build_brief call it."""
    calls = []

    def fake_assert_frozen(plan_path):
        calls.append(plan_path)

    monkeypatch.setattr(kd, "assert_frozen", fake_assert_frozen)
    kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R",
                   plan_path="whatever/PLAN.md")
    assert calls == ["whatever/PLAN.md"]


def test_build_brief_rejects_bad_role_and_sandbox():
    with pytest.raises(ValueError, match="unknown role"):
        kd.build_brief("t", "banana", "codex", model="m", objective="o", result_path="r", plan_path=_FROZEN_PLAN)
    with pytest.raises(ValueError, match="sandbox"):
        kd.build_brief("t", "coder", "codex", model="m", objective="o", result_path="r", sandbox="rw", plan_path=_FROZEN_PLAN)
    with pytest.raises(ValueError, match="required"):
        kd.build_brief("t", "coder", "codex", model="m", objective="", result_path="r", plan_path=_FROZEN_PLAN)


# ----- N2 codex_command -----
def test_codex_command_readonly():
    b = kd.build_brief("t1", "validator", "codex", model="gpt-5-codex", objective="o",
                       result_path="RESULT.json", sandbox="read-only", plan_path=_FROZEN_PLAN)
    cmd = kd.codex_command(b, "/wt")
    assert cmd[0:2] == ["codex", "exec"]
    assert "--sandbox" in cmd and cmd[cmd.index("--sandbox") + 1] == "read-only"
    assert cmd[cmd.index("--model") + 1] == "gpt-5-codex"
    assert cmd[cmd.index("-o") + 1] == "RESULT.json"   # capture final message to the result file
    assert "--output-schema" not in cmd                # not the result path (NIT-1 fix)


def test_codex_command_write_sandbox():
    b = kd.build_brief("t2", "coder", "codex", model="m", objective="o", result_path="R", sandbox="write", plan_path=_FROZEN_PLAN)
    cmd = kd.codex_command(b, "/wt")
    assert cmd[cmd.index("--sandbox") + 1] == "workspace-write"


def test_codex_command_has_skip_git_repo_check():
    """codex-cli 0.142.3 refuses to run outside a trusted git dir without --skip-git-repo-check.

    The flag must be present and ordered exec → --skip-git-repo-check → --cd ...,
    while keeping exec/--cd/--sandbox/--model/-o/prompt intact.
    """
    b = kd.build_brief("t1", "validator", "codex", model="gpt-5-codex", objective="o",
                       result_path="RESULT.json", sandbox="read-only", plan_path=_FROZEN_PLAN)
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
        stderr = "warn: something"

    def fake_run(cmd, **kwargs):
        captured.update(kwargs)
        return _Proc()

    monkeypatch.setattr(kd.subprocess, "run", fake_run)
    code, stdout, stderr, result_text = kd._subprocess_runner(["codex", "exec"], str(tmp_path), "RESULT.json", 600)
    assert captured.get("stdin") is subprocess.DEVNULL
    # existing behaviour preserved
    assert captured.get("capture_output") is True
    assert captured.get("text") is True
    assert captured.get("timeout") == 600
    # the 4-tuple contract: stderr is CARRIED, not discarded (dispatch-stderr-fix D1)
    assert (code, stdout, stderr, result_text) == (0, "ok", "warn: something", "")


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
def _stub_runner(result_obj, exit_code=0, stdout="ok", stderr=""):
    """A runner that simulates a worker writing `result_obj` as its result file."""
    def run(cmd, cwd, result_path, timeout):
        return exit_code, stdout, stderr, json.dumps(result_obj)
    return run


def test_dispatch_success_validator():
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=_stub_runner({"verdict": "ship", "findings": []}))
    assert res["status"] == "completed"
    assert res["payload"]["verdict"] == "ship"


def test_dispatch_nonzero_exit_is_failed():
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=_stub_runner({}, exit_code=2))
    assert res["status"] == "failed"


def test_dispatch_unparseable_result_is_failed():
    def bad_runner(cmd, cwd, result_path, timeout):
        return 0, "ok", "", "not json{{"
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=bad_runner)
    assert res["status"] == "failed"


def test_dispatch_timeout():
    import subprocess

    def timeout_runner(cmd, cwd, result_path, timeout):
        raise subprocess.TimeoutExpired(cmd, timeout)
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=timeout_runner)
    assert res["status"] == "timeout"


def test_dispatch_non_object_result_is_failed_not_crash():
    # valid JSON but a top-level ARRAY must fail gracefully, not raise (D98 MAJOR-1 fix)
    def array_runner(cmd, cwd, result_path, timeout):
        return 0, "ok", "", "[1, 2, 3]"
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=array_runner)
    assert res["status"] == "failed"
    assert "error" in res["payload"]


def test_build_brief_rejects_traversal_result_path():
    with pytest.raises(ValueError, match="'\\.\\.'"):
        kd.build_brief("t", "validator", "codex", model="m", objective="o",
                       result_path="../../etc/evil.json", plan_path=_FROZEN_PLAN)


def test_safe_result_path_under_cwd(tmp_path):
    rp = kd._safe_result_path("sub/RESULT.json", str(tmp_path))
    assert str(rp).startswith(str(tmp_path.resolve()))


def test_safe_result_path_rejects_escape(tmp_path):
    with pytest.raises(ValueError):
        kd._safe_result_path("../escape.json", str(tmp_path))


def test_dispatch_unroutable_platform_fails_gracefully():
    # a confirmed-but-undispatchable platform must FAIL, not crash the loop (red-team F3)
    # "cursor" is deferred (L-MP1 / PLAN.md); "kiro" is now routable so is no longer the example
    b = kd.build_brief("t1", "validator", "cursor", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=_stub_runner({}))
    assert res["status"] == "failed"
    assert "no dispatch adapter" in res["payload"]["error"]


def test_dispatch_empty_result_researcher_is_failed():
    # empty result must default-FAIL for researcher (red-team F1), not report a None-filled "completed"
    def empty_runner(cmd, cwd, result_path, timeout):
        return 0, "ok", "", ""
    b = kd.build_brief("t1", "researcher", "codex", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=empty_runner)
    assert res["status"] == "failed"


def test_dispatch_empty_result_coder_is_failed():
    def empty_runner(cmd, cwd, result_path, timeout):
        return 0, "ok", "", "{}"
    b = kd.build_brief("t1", "coder", "codex", model="m", objective="o", result_path="R", sandbox="write", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=empty_runner)
    assert res["status"] == "failed"


def test_normalize_researcher_requires_claim():
    payload = kd.normalize(
        "researcher", json.dumps({"claim": "x", "source": "doc:1", "groundsToPlan": "y"})
    )
    assert payload["claim"] == "x"
    with pytest.raises(ValueError, match="claim"):
        kd.normalize("researcher", json.dumps({"source": "s"}))


def test_normalize_researcher_rejects_ungrounded_claim():
    # Q-13: a claim without a source citation is an ungrounded claim — not a finding.
    # It must be rejected (default-FAIL), never flow in as a completed result.
    with pytest.raises(ValueError, match="ungrounded|source"):
        kd.normalize("researcher", json.dumps({"claim": "the sky is green", "groundsToPlan": "y"}))
    with pytest.raises(ValueError, match="ungrounded|source"):
        kd.normalize("researcher", json.dumps({"claim": "x", "source": "  "}))


def test_normalize_evaluator_score_range():
    kd.normalize("evaluator", json.dumps({"score": 0.5, "decision": "accept"}))  # ok
    with pytest.raises(ValueError, match="score"):
        kd.normalize("evaluator", json.dumps({"score": "banana", "decision": "accept"}))
    with pytest.raises(ValueError, match="score"):
        kd.normalize("evaluator", json.dumps({"score": 1.5, "decision": "accept"}))


def test_build_brief_rejects_absolute_result_path():
    with pytest.raises(ValueError, match="worktree-relative"):
        kd.build_brief("t", "validator", "codex", model="m", objective="o", result_path="/etc/evil.json", plan_path=_FROZEN_PLAN)


def test_brief_prompt_conveys_inputs_and_ownership():
    b = kd.build_brief("t", "coder", "codex", model="m", objective="do it", result_path="R",
                       inputs=["a.py"], owned_files=["b.py"], sandbox="write", plan_path=_FROZEN_PLAN)
    prompt = kd._brief_prompt(b)
    assert "a.py" in prompt and "b.py" in prompt
    assert "do not write files" in prompt.casefold()


# ----- Slice C: kiro dispatch adapter (MAJOR-1 + kiro_command) -----

def test_brief_prompt_capture_emit_unchanged():
    """codex path (capture="emit"): unchanged wording — still says 'do not write files'."""
    b = kd.build_brief("t", "researcher", "codex", model="m", objective="research it",
                       result_path="RESULT.json", plan_path=_FROZEN_PLAN)
    prompt = kd._brief_prompt(b, capture="emit")
    assert "do not write files" in prompt.casefold()
    assert "RESULT.json" not in prompt or "Write" not in prompt  # no write-to-file instruction


def test_brief_prompt_capture_write_contains_result_path():
    """kiro path (capture="write"): prompt instructs the worker to WRITE resultPath itself.

    MAJOR-1 regression guard: kiro has no -o capture (DESIGN §4 N2); the worker must write.
    """
    b = kd.build_brief("t", "researcher", "kiro", model="m", objective="research it",
                       result_path="RESULT.json", plan_path=_FROZEN_PLAN)
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
                       result_path="RESULT.json", plan_path=_FROZEN_PLAN)
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
        plan_path=_FROZEN_PLAN,
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


# ----- dispatch-stderr-fix: the provider error signal survives failure (GRILL-LEDGER D1-D3) -----

def test_dispatch_failed_carries_stderr():
    """exit != 0: the provider error text on stderr rides the failure payload (D3)."""
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=_stub_runner({}, exit_code=1, stderr="429 Too Many Requests: rate limit"))
    assert res["status"] == "failed"
    assert res["payload"]["error"] == "worker exited 1"
    assert res["payload"]["stderr"] == "429 Too Many Requests: rate limit"
    assert res["raw"] == "ok"  # raw keeps stdout-only semantics


def test_dispatch_failed_empty_stderr_adds_no_key():
    """Empty stderr => no key added; the failure payload stays minimal (D2 edge)."""
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=_stub_runner({}, exit_code=2))
    assert res["status"] == "failed"
    assert "stderr" not in res["payload"]


def test_dispatch_success_envelope_has_no_stderr_key():
    """completed envelope is byte-unchanged: stderr never rides success (D3 / AC#4)."""
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=_stub_runner({"verdict": "ship", "findings": []},
                                                    stderr="warning: noise on stderr"))
    assert res["status"] == "completed"
    assert "stderr" not in res["payload"]
    assert res["payload"] == {"verdict": "ship", "findings": []}


def test_dispatch_unparseable_result_carries_stderr():
    """exit 0 but garbage result file: stderr may explain why — it rides the payload (D3)."""
    def bad_runner(cmd, cwd, result_path, timeout):
        return 0, "ok", "worker crashed mid-write", "not json{{"
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=bad_runner)
    assert res["status"] == "failed"
    assert "unparseable result" in res["payload"]["error"]
    assert res["payload"]["stderr"] == "worker crashed mid-write"


def test_dispatch_timeout_carries_captured_stderr_str_and_bytes():
    """TimeoutExpired's captured-so-far stderr rides the timeout envelope; bytes decoded (D3)."""
    import subprocess

    for stderr_val, expected in [
        ("quota exhausted; upgrade at https://x", "quota exhausted; upgrade at https://x"),
        (b"quota exhausted (bytes form)", "quota exhausted (bytes form)"),
    ]:
        def timeout_runner(cmd, cwd, result_path, timeout, _s=stderr_val):
            exc = subprocess.TimeoutExpired(cmd, timeout)
            exc.stderr = _s
            raise exc
        b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
        res = kd.dispatch(b, "/wt", runner=timeout_runner)
        assert res["status"] == "timeout"
        assert res["payload"]["stderr"] == expected


def test_dispatch_timeout_without_stderr_stays_minimal():
    """A TimeoutExpired with no captured stderr => empty payload, exactly as before (D3 edge)."""
    import subprocess

    def timeout_runner(cmd, cwd, result_path, timeout):
        raise subprocess.TimeoutExpired(cmd, timeout)
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=timeout_runner)
    assert res["status"] == "timeout"
    assert res["payload"] == {}


def test_stderr_tail_cap_boundary():
    """Deterministic tail cap: exactly-cap => untouched, no marker; over-cap => marker + LAST chars (D2)."""
    exact = "x" * kd._STDERR_TAIL_CHARS
    assert kd._stderr_tail(exact) == exact  # no marker at exactly the cap
    over = "HEAD-" + ("y" * kd._STDERR_TAIL_CHARS) + "-TAIL"
    capped = kd._stderr_tail(over)
    assert capped.startswith(kd._STDERR_TRUNCATION_MARKER)
    assert capped.endswith("-TAIL")                      # the END survives (provider text lives there)
    assert "HEAD-" not in capped                          # the head is what gets dropped
    assert len(capped) == len(kd._STDERR_TRUNCATION_MARKER) + kd._STDERR_TAIL_CHARS
    assert kd._stderr_tail(None) == ""                    # None-safe
    assert kd._stderr_tail(b"\xff\xfebytes") != ""        # undecodable bytes never raise (errors=replace)


def test_dispatch_failed_oversized_stderr_is_tail_capped():
    """The cap is applied AT DISPATCH — a runner returning megabytes cannot bloat the envelope (D2)."""
    huge = ("z" * 10_000) + "\nFINAL: 429 rate limited"
    b = kd.build_brief("t1", "validator", "codex", model="m", objective="o", result_path="R", plan_path=_FROZEN_PLAN)
    res = kd.dispatch(b, "/wt", runner=_stub_runner({}, exit_code=1, stderr=huge))
    got = res["payload"]["stderr"]
    assert got.startswith(kd._STDERR_TRUNCATION_MARKER)
    assert got.endswith("FINAL: 429 rate limited")
    assert len(got) == len(kd._STDERR_TRUNCATION_MARKER) + kd._STDERR_TAIL_CHARS


# ----- dispatch-authoring: design-author / plan-author normalize() branches (DESIGN §4.3, T1) -----

def test_normalize_design_author():
    payload = kd.normalize("design-author", json.dumps({"designPath": "DESIGN.md", "verdict": "ready"}))
    assert payload == {"designPath": "DESIGN.md", "verdict": "ready", "deviations": []}


def test_normalize_design_author_missing_designpath_raises():
    with pytest.raises(ValueError, match="designPath"):
        kd.normalize("design-author", json.dumps({"verdict": "ready"}))


def test_normalize_design_author_bad_verdict_raises():
    with pytest.raises(ValueError, match="verdict"):
        kd.normalize("design-author", json.dumps({"designPath": "x", "verdict": "sideways"}))


def test_normalize_design_author_preserves_deviations():
    payload = kd.normalize(
        "design-author",
        json.dumps({"designPath": "DESIGN.md", "verdict": "needs-rework", "deviations": ["extrapolated X"]}),
    )
    assert payload["deviations"] == ["extrapolated X"]


def test_normalize_plan_author():
    payload = kd.normalize("plan-author", json.dumps({"planPath": "PLAN.md", "verdict": "ready"}))
    assert payload == {"planPath": "PLAN.md", "verdict": "ready", "deviations": []}


def test_normalize_plan_author_missing_planpath_raises():
    with pytest.raises(ValueError, match="planPath"):
        kd.normalize("plan-author", json.dumps({"verdict": "ready"}))


def test_normalize_plan_author_bad_verdict_raises():
    with pytest.raises(ValueError, match="verdict"):
        kd.normalize("plan-author", json.dumps({"planPath": "x", "verdict": "sideways"}))


def test_build_brief_design_author_write_sandbox():
    b = kd.build_brief("t1", "design-author", "claude", model="m", objective="o",
                       result_path="R", sandbox="write", plan_path=_FROZEN_PLAN)
    assert b["role"] == "design-author"
    assert b["boundaries"]["sandbox"] == "write"


def test_build_brief_plan_author_write_sandbox():
    b = kd.build_brief("t1", "plan-author", "claude", model="m", objective="o",
                       result_path="R", sandbox="write", plan_path=_FROZEN_PLAN)
    assert b["role"] == "plan-author"
    assert b["boundaries"]["sandbox"] == "write"


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
        plan_path=_FROZEN_PLAN,
    )

    # 3) dispatch with a stub Codex that returns a HOLD verdict (the worker's structured output)
    codex_output = {"verdict": "hold", "findings": [{"severity": "MAJOR", "note": "unguarded path"}]}
    result = kd.dispatch(brief, str(tmp_path), runner=_stub_runner(codex_output, stdout="codex done"))

    # 4) the normalized envelope: dispatch succeeded, validator verdict came back
    assert result["status"] == "completed"        # dispatch outcome
    assert result["platform"] == "codex"
    assert result["payload"]["verdict"] == "hold"  # the role verdict (distinct axis)
    assert result["payload"]["findings"][0]["severity"] == "MAJOR"


# ===========================================================================
# THE SEAM — trust-model DESIGN §1 (PLAN wave 3, task seam-engine)
# ===========================================================================

import collections  # noqa: E402
import concurrent.futures  # noqa: E402
import inspect  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import sys  # noqa: E402
import threading  # noqa: E402
from datetime import UTC, datetime  # noqa: E402

import kata_board as kb  # noqa: E402
import kata_trail as ktr  # noqa: E402

_NOW = datetime(2026, 8, 16, 12, 0, 0, tzinfo=UTC)

#: Rounds the in-process claim race runs (see test_record_claim_is_atomic_single_use).
#: The defect this guards reproduced ~1 run in 5, so a single round could pass while the
#: RS-H2 property was broken; 25 rounds makes one pytest invocation decisive.
_RACE_ROUNDS = 25


def _write_md(path: Path, frontmatter: str, body: str = "# doc\n") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"---\n{frontmatter}\n---\n\n{body}", encoding="utf-8")
    return path


def _kata(tmp_path: Path, *, entropy: str = "abcd1234") -> Path:
    """A kata dir carrying one live (open) run."""
    kata = tmp_path / ".kata"
    kb.start_run(kata, now=_NOW, entropy=entropy)
    return kata


def _mint_ok(kata: Path, plan: Path, **kw):
    return kd.mint(
        governs="plan", role="coder", task_id=kw.pop("task_id", "t1"), kata_dir=kata,
        plan_path=plan, brief={"objective": "build it"}, now=_NOW, **kw,
    )


# --------------------------------------------------------------------- §1.4 the ladder


class TestLedgerStatus:
    """The `ledger` rung's predicate — the closed four-value enum (DESIGN §1.4, R2-H1)."""

    @pytest.mark.parametrize("raw,expected", [
        ("status: draft", "draft"),
        ("status: converged", "converged"),
        ("status: frozen", "frozen"),
        ("status: absorbed", "absorbed"),
        ("status: CONVERGED — closed 2026-08-16 after the fifth SHIP", "converged"),
        ("status: frozen (D169 freeze act, conductor-performed)", "frozen"),
        ("spec: x", "absent"),
        ("status: ''", "absent"),
    ])
    def test_first_word_parse(self, tmp_path, raw, expected):
        """First-word parse (BL-F01), mirroring plan_status / intent_status exactly."""
        led = _write_md(tmp_path / "GRILL-LEDGER.md", raw)
        assert kd.ledger_status(led) == expected

    def test_unrecognized_status_raises_never_coerces(self, tmp_path):
        led = _write_md(tmp_path / "GRILL-LEDGER.md", "status: mostly-done-ish")
        with pytest.raises(ValueError, match="unrecognized status"):
            kd.ledger_status(led)

    def test_missing_frontmatter_raises(self, tmp_path):
        led = tmp_path / "GRILL-LEDGER.md"
        led.write_text("# no frontmatter here\n", encoding="utf-8")
        with pytest.raises(ValueError, match="no YAML frontmatter"):
            kd.ledger_status(led)

    def test_ordering(self):
        """draft < converged; frozen satisfies whatever converged satisfies."""
        assert kd.ledger_satisfies("converged", "draft") is True
        assert kd.ledger_satisfies("draft", "converged") is False
        assert kd.ledger_satisfies("frozen", "converged") is True
        assert kd.ledger_satisfies("frozen", "draft") is True
        # absorbed ROUTES; it never satisfies. absent never satisfies.
        assert kd.ledger_satisfies("absorbed", "draft") is False
        assert kd.ledger_satisfies("absent", "draft") is False


class TestAbsorbedRouting:
    """`absorbed` ROUTES the mint to the absorbing ledger (E6, pass-1 SHIP residual 2)."""

    def _corpus(self, tmp_path):
        """The LIVE corpus shape: a prose-only routing target in the status line.

        The status VALUE is quoted here because the live `dispatch-seam` ledger's is not,
        and its unquoted ``operator-ruled: ONE …`` makes that file's frontmatter invalid
        YAML — see ``test_unquoted_colon_in_a_status_line_refuses_never_guesses``, the
        corpus defect this build found and reported rather than silently worked around.
        """
        specs = tmp_path / "specs"
        target = _write_md(specs / "trust-model" / "GRILL-LEDGER.md", "status: converged")
        source = _write_md(
            specs / "dispatch-seam" / "GRILL-LEDGER.md",
            'status: "absorbed — 2026-08-16, operator-ruled: ONE unified trust-model grill. '
            "This ledger's tree carries forward as INPUT to ../trust-model/GRILL-LEDGER.md "
            '(B1 to B). Do NOT resolve branches here."',
        )
        return source, target

    def test_unquoted_colon_in_a_status_line_refuses_never_guesses(self, tmp_path):
        """The LIVE dispatch-seam ledger's frontmatter is not valid YAML (build finding).

        Its unquoted ``status: absorbed — …, operator-ruled: ONE …`` carries a second
        ``": "`` inside a plain scalar, which no YAML parser accepts. The predicate holds
        the same fail-closed posture as ``plan_status`` / ``intent_status``: a broken
        status is a DATA problem to resolve by hand (quote the value or add an
        ``absorbed-into:`` key), never a guess and never a default.
        """
        led = _write_md(
            tmp_path / "GRILL-LEDGER.md",
            "status: absorbed — 2026-08-16, operator-ruled: ONE unified grill",
        )
        with pytest.raises(ValueError, match="not valid YAML"):
            kd.ledger_status(led)

    def test_prose_token_resolution_matches_the_live_corpus(self, tmp_path):
        source, target = self._corpus(tmp_path)
        assert kd.resolve_absorbed_ledger(source) == target.resolve()

    def test_absorbed_into_key_wins_over_prose(self, tmp_path):
        specs = tmp_path / "specs"
        declared = _write_md(specs / "declared" / "GRILL-LEDGER.md", "status: converged")
        _write_md(specs / "prose" / "GRILL-LEDGER.md", "status: converged")
        source = _write_md(
            specs / "src" / "GRILL-LEDGER.md",
            "absorbed-into: ../declared/GRILL-LEDGER.md\n"
            "status: absorbed — see ../prose/GRILL-LEDGER.md for the story",
        )
        assert kd.resolve_absorbed_ledger(source) == declared.resolve()

    def test_two_candidate_tokens_is_ambiguous_and_parks(self, tmp_path):
        specs = tmp_path / "specs"
        _write_md(specs / "a" / "GRILL-LEDGER.md", "status: converged")
        _write_md(specs / "b" / "GRILL-LEDGER.md", "status: converged")
        source = _write_md(
            specs / "src" / "GRILL-LEDGER.md",
            "status: absorbed into ../a/GRILL-LEDGER.md and ../b/GRILL-LEDGER.md",
        )
        with pytest.raises(kd.AbsorbedRoutingAmbiguous, match="ambiguous"):
            kd.resolve_absorbed_ledger(source)

    def test_no_token_is_ambiguous_and_parks(self, tmp_path):
        source = _write_md(
            tmp_path / "specs" / "src" / "GRILL-LEDGER.md",
            "status: absorbed — folded into the other grill, ask the conductor",
        )
        with pytest.raises(kd.AbsorbedRoutingAmbiguous, match="names no routing target"):
            kd.resolve_absorbed_ledger(source)

    def test_absent_target_parks(self, tmp_path):
        source = _write_md(
            tmp_path / "specs" / "src" / "GRILL-LEDGER.md",
            "status: absorbed into ../ghost/GRILL-LEDGER.md",
        )
        with pytest.raises(kd.AbsorbedRoutingAmbiguous, match="does not exist"):
            kd.resolve_absorbed_ledger(source)

    def test_target_escaping_the_specs_root_parks(self, tmp_path):
        _write_md(tmp_path / "outside" / "GRILL-LEDGER.md", "status: converged")
        source = _write_md(
            tmp_path / "specs" / "src" / "GRILL-LEDGER.md",
            "status: absorbed into ../../outside/GRILL-LEDGER.md",
        )
        with pytest.raises(kd.AbsorbedRoutingAmbiguous, match="escapes the specs root"):
            kd.resolve_absorbed_ledger(source)

    def test_absolute_target_parks(self, tmp_path):
        source = _write_md(
            tmp_path / "specs" / "src" / "GRILL-LEDGER.md",
            "absorbed-into: /etc/GRILL-LEDGER.md\nstatus: absorbed",
        )
        with pytest.raises(kd.AbsorbedRoutingAmbiguous, match="not a ledger-relative"):
            kd.resolve_absorbed_ledger(source)

    def test_chain_longer_than_the_hop_cap_parks(self, tmp_path):
        """An acyclic chain past ABSORBED_MAX_HOPS refuses — bounded, never a long walk."""
        specs = tmp_path / "specs"
        depth = kd.ABSORBED_MAX_HOPS + 2
        for i in range(depth):
            _write_md(
                specs / f"s{i}" / "GRILL-LEDGER.md",
                f"absorbed-into: ../s{i + 1}/GRILL-LEDGER.md\nstatus: absorbed",
            )
        _write_md(specs / f"s{depth}" / "GRILL-LEDGER.md", "status: converged")
        with pytest.raises(kd.AbsorbedRoutingAmbiguous, match="exceeds"):
            kd.resolve_absorbed_ledger(specs / "s0" / "GRILL-LEDGER.md")

    def test_routing_refusals_carry_the_park_path_when_minting(self, tmp_path):
        """The docstring promises "⇒ park"; the refusal must actually CARRY the park path."""
        kata = _kata(tmp_path)
        source = _write_md(
            tmp_path / "specs" / "src" / "GRILL-LEDGER.md",
            "status: absorbed — folded in, ask the conductor",
        )
        with pytest.raises(kd.AbsorbedRoutingAmbiguous) as exc:
            kd.mint(
                governs="ledger", role="design-author", task_id="t-absorb", kata_dir=kata,
                ledger_path=source, brief={"o": "author"}, now=_NOW,
            )
        assert exc.value.park_path is not None
        assert exc.value.park_path.endswith(os.path.join("escalations", "t-absorb.json"))
        assert exc.value.task_id == "t-absorb"
        assert exc.value.escalation_kind == "human-required"
        # ...and a bare diagnostic call (no dispatch in flight) leaves it unset
        with pytest.raises(kd.AbsorbedRoutingAmbiguous) as bare:
            kd.resolve_absorbed_ledger(source)
        assert bare.value.park_path is None

    def test_routing_cycle_parks(self, tmp_path):
        specs = tmp_path / "specs"
        _write_md(specs / "a" / "GRILL-LEDGER.md",
                  "absorbed-into: ../b/GRILL-LEDGER.md\nstatus: absorbed")
        _write_md(specs / "b" / "GRILL-LEDGER.md",
                  "absorbed-into: ../a/GRILL-LEDGER.md\nstatus: absorbed")
        with pytest.raises(kd.AbsorbedRoutingAmbiguous, match="cycle"):
            kd.resolve_absorbed_ledger(specs / "a" / "GRILL-LEDGER.md")

    def test_mint_routes_through_an_absorbed_ledger(self, tmp_path):
        """The whole point: a mint against an absorbed ledger lands on the absorbing one."""
        source, target = self._corpus(tmp_path)
        kata = _kata(tmp_path)
        record = kd.mint(
            governs="ledger", role="design-author", task_id="t-author", kata_dir=kata,
            ledger_path=source, brief={"o": "author the design"}, now=_NOW,
        )
        assert record["governedRef"] == str(target.resolve())
        assert record["governedState"] == "converged"
        assert record["governedRoutedFrom"] == str(source.resolve())


# ----- THE DECLARED EVIDENCE NODE (PLAN frontmatter `evidence:` for seam-engine) -----
def test_mint_refuses_unmet_governor_state(tmp_path):
    """Per-rung refusal: EVERY governor x an unmet state ⇒ refuse-to-mint ⇒ park (TM-B5).

    The engine's refusal is typed, names the park path, and lands a DENY cursor event
    naming the legal path (DESIGN §1.8). No rung has a silent-permissive edge.
    """
    kata = _kata(tmp_path)
    draft_plan = _write_md(tmp_path / "PLAN.md", "status: DRAFT — awaiting freeze-gate")
    draft_ledger = _write_md(tmp_path / "specs" / "s" / "GRILL-LEDGER.md", "status: draft")
    keyless_ledger = _write_md(tmp_path / "specs" / "k" / "GRILL-LEDGER.md", "spec: k")
    draft_intent = _write_md(tmp_path / "INTENT.md", "status: draft")
    missing_ledger = tmp_path / "specs" / "gone" / "GRILL-LEDGER.md"
    # The LIVE corpus shape (D-23): an unquoted second ": " makes the frontmatter invalid
    # YAML. This reaches the engine through the absorbed-ROUTING pre-step, which used to
    # let a raw ValueError escape mint() with no park path and no DENY event.
    bad_yaml_ledger = _write_md(
        tmp_path / "specs" / "y" / "GRILL-LEDGER.md",
        "status: absorbed — 2026-08-16, operator-ruled: ONE unified grill",
    )
    unrouted_ledger = _write_md(
        tmp_path / "specs" / "u" / "GRILL-LEDGER.md",
        "status: absorbed — folded into the other grill, ask the conductor",
    )

    cases = [
        # (mint kwargs, expected refusal fragment)
        (dict(governs="plan", role="coder", plan_path=draft_plan), "plan rung unmet"),
        (dict(governs="ledger", role="design-author", ledger_path=draft_ledger), "ledger rung unmet"),
        (dict(governs="ledger", role="researcher", ledger_path=keyless_ledger), "ledger rung unmet"),
        # a role class with NO ledger row is refused there — an unlisted row is an unruled one
        (dict(governs="ledger", role="coder", ledger_path=draft_ledger), "no ledger-governed rung"),
        # the ROUTING pre-step reads frontmatter too: an unreadable ledger, and the live
        # corpus's invalid YAML, must both be TYPED refusals, never a raw ValueError
        (dict(governs="ledger", role="design-author", ledger_path=missing_ledger),
         "cannot read ledger"),
        (dict(governs="ledger", role="design-author", ledger_path=bad_yaml_ledger),
         "not valid YAML"),
        # ...and an absorbed ledger naming no routing target parks like every other rung
        (dict(governs="ledger", role="design-author", ledger_path=unrouted_ledger),
         "names no routing target"),
        (dict(governs="intent", role="coder", intent_path=draft_intent), "intent rung unmet"),
        # the initiation rung with no open INITIATION/AUTHORING phase on the live cursor
        (dict(governs="initiation", role="plan-author", priming_prompt_hash="deadbeef"),
         "no INITIATION or AUTHORING phase is open"),
        # ...and with an open phase but no priming-prompt hash (the rung's provenance)
        (dict(governs="initiation", role="plan-author"), "requires priming_prompt_hash"),
        # unknown governor ⇒ the closed vocabulary refuses
        (dict(governs="vibes", role="coder"), "unknown governor"),
        # unknown role ⇒ refused before any predicate runs
        (dict(governs="plan", role="wizard", plan_path=draft_plan), "unknown role"),
    ]

    for kwargs, fragment in cases:
        with pytest.raises(kd.MintRefused) as exc:
            kd.mint(task_id="t-refuse", kata_dir=kata, brief={"o": "x"}, now=_NOW, **kwargs)
        assert fragment in str(exc.value), f"{kwargs} did not refuse with {fragment!r}"
        # TM-B5: the refusal names the park path and the escalation kind
        assert exc.value.park_path.endswith(os.path.join("escalations", "t-refuse.json"))
        assert exc.value.escalation_kind == "human-required"

    # ...and no record was written for any of them
    assert not list(kd.dispatch_dir(kata).glob("*.json"))
    # ...while every denial IS a cursor DENY event naming a legal path (DESIGN §1.8)
    denies = [ln for ln in kb.read_cursor(kata).lines if ln.type == "DENY"]
    assert len(denies) == len(cases)
    assert all("legal path:" in ln.msg for ln in denies)


def test_governs_is_required_keyword_only_with_no_default(tmp_path):
    """R3-M4 / BL-F01 verbatim: an omittable governor is the D136 silent-permissive class."""
    kata = _kata(tmp_path)
    with pytest.raises(TypeError, match="governs"):
        kd.mint(role="coder", task_id="t", kata_dir=kata, brief={})
    param = inspect.signature(kd.mint).parameters["governs"]
    assert param.kind is inspect.Parameter.KEYWORD_ONLY
    assert param.default is inspect.Parameter.empty


class TestRungExclusivity:
    """RS-H3 — the initiation rung is refused once a stronger governor exists."""

    def test_initiation_mint_succeeds_while_the_phase_is_open(self, tmp_path):
        kata = _kata(tmp_path)
        kd.phase(kata, "open INITIATION", repo_root=str(tmp_path), now=_NOW)
        record = kd.mint(
            governs="initiation", role="plan-author", task_id="t-init", kata_dir=kata,
            priming_prompt_hash="cafe1234", brief={"o": "author"}, now=_NOW,
        )
        assert record["governs"] == "initiation"
        # graded Honor-system, never dressed as Verified (R3-H2 / R4-H1)
        assert record["governorGrade"] == "Honor-system"

    def test_refused_once_a_stronger_governor_is_recorded(self, tmp_path):
        kata = _kata(tmp_path)
        kd.phase(kata, "open INITIATION", repo_root=str(tmp_path), now=_NOW)
        _mint_ok(kata, _FROZEN_PLAN, task_id="t-plan")  # records plan:frozen
        with pytest.raises(kd.MintRefused, match="initiation-rung exclusivity"):
            kd.mint(
                governs="initiation", role="plan-author", task_id="t-init", kata_dir=kata,
                priming_prompt_hash="cafe1234", brief={"o": "author"}, now=_NOW,
            )

    def test_refused_once_the_phase_has_closed(self, tmp_path):
        kata = _kata(tmp_path)
        kd.phase(kata, "open AUTHORING", repo_root=str(tmp_path), now=_NOW)
        kd.phase(kata, "close AUTHORING", repo_root=str(tmp_path), now=_NOW)
        with pytest.raises(kd.MintRefused, match="already CLOSED"):
            kd.mint(
                governs="initiation", role="design-author", task_id="t-init", kata_dir=kata,
                priming_prompt_hash="cafe1234", brief={"o": "author"}, now=_NOW,
            )

    def test_reopening_initiation_is_a_recorded_deny_class_event(self, tmp_path):
        kata = _kata(tmp_path)
        kd.phase(kata, "open INITIATION", repo_root=str(tmp_path), now=_NOW)
        kd.phase(kata, "close INITIATION", repo_root=str(tmp_path), now=_NOW)
        _mint_ok(kata, _FROZEN_PLAN, task_id="t-plan")
        with pytest.raises(kd.PhaseRefused, match="DENY-class event"):
            kd.phase(kata, "open INITIATION", repo_root=str(tmp_path), now=_NOW)
        denies = [ln for ln in kb.read_cursor(kata).lines if ln.type == "DENY"]
        assert denies and "RS-H3" in denies[-1].msg


# --------------------------------------------------------------------- §1.5 the record


def test_mint_writes_the_full_record_and_a_chained_spawn_line(tmp_path):
    """DESIGN §1.5 field list + the SPAWN lineage that makes fabrication post-hoc detectable."""
    kata = _kata(tmp_path)
    record = _mint_ok(kata, _FROZEN_PLAN)
    for field in ("runId", "taskId", "role", "platform", "model", "effort", "governs",
                  "governedRef", "briefHash", "mintedUtc", "seq", "agentDef"):
        assert field in record
    assert record["agentDef"] is None            # RESERVED for BL-N20, unpopulated in v1
    assert record["governs"] == "plan"
    assert record["briefHash"] == kd.brief_hash({"objective": "build it"})

    on_disk = json.loads(Path(record["recordPath"]).read_text(encoding="utf-8"))
    assert on_disk["recordId"] == record["recordId"]

    cursor = kb.read_cursor(kata)
    spawn = [ln for ln in cursor.lines if ln.type == "SPAWN"]
    assert len(spawn) == 1
    assert spawn[0].seq == record["seq"]
    assert kd._spawn_fields(spawn[0].msg)["record"] == record["recordId"]


def test_mint_refuses_to_overwrite_an_existing_record_path(tmp_path):
    """Same defect class as the claim election: a colliding seq must be LOUD, not silent.

    `seq` comes from next_seq(cursor), a read-then-write, so two concurrent mints would
    compute the same seq and the second would silently clobber the first's record while
    both appended a SPAWN line naming the same id. kata_board's contract assumes the
    seam is a single writer; the record path is now reserved exclusively, so a violation
    refuses instead of destroying a minted record.
    """
    kata = _kata(tmp_path)
    cursor = kb.read_cursor(kata)
    collided = kd.record_path(kata, kd.record_id(cursor.run_id, kb.next_seq(cursor)))
    collided.parent.mkdir(parents=True, exist_ok=True)
    collided.write_text('{"squatter": true}', encoding="utf-8")

    with pytest.raises(kd.MintRefused, match="already exists"):
        _mint_ok(kata, _FROZEN_PLAN)
    # the pre-existing record is intact — nothing was overwritten
    assert json.loads(collided.read_text(encoding="utf-8")) == {"squatter": True}


def test_mint_wires_the_role_resolver(tmp_path):
    """resolve_roles had ZERO callers (SURFACE-MAP); the mint is its call site."""
    kata = _kata(tmp_path)
    record = kd.mint(
        governs="plan", role="validator", task_id="t-mm", kata_dir=kata,
        plan_path=_FROZEN_PLAN, brief={"o": "check"},
        roles_block={"validator": {"platform": "codex", "model": "gpt-5-codex"}},
        confirmed_platforms=["codex"], now=_NOW,
    )
    assert record["platform"] == "codex" and record["model"] == "gpt-5-codex"


def test_mint_fails_closed_on_an_unconfirmed_platform(tmp_path):
    kata = _kata(tmp_path)
    with pytest.raises(ValueError, match="not confirmed"):
        kd.mint(
            governs="plan", role="validator", task_id="t-mm", kata_dir=kata,
            plan_path=_FROZEN_PLAN, brief={"o": "check"},
            roles_block={"validator": {"platform": "codex"}}, confirmed_platforms=[], now=_NOW,
        )


def test_claim_election_is_exclusive_under_a_forced_interleaving(tmp_path, monkeypatch):
    """RS-H2, proven DETERMINISTICALLY — no thread timing, no luck.

    Claimant A is suspended at the EXACT race point (after the winner election, before
    the retention move) and claimant B is run to completion inside that window. B must
    be denied. This is the property a probabilistic thread race can only sample: it
    pins the one interleaving that matters, every run.
    """
    kata = _kata(tmp_path)
    rid = _mint_ok(kata, _FROZEN_PLAN)["recordId"]
    observed = {}

    def at_race_point(claimed_rid):
        # Disarm first so B's own claim does not re-enter this hook.
        monkeypatch.setattr(kd, "_CLAIM_RACE_HOOK", None)
        assert claimed_rid == rid
        # B runs fully while A holds the election but has NOT yet moved the record.
        with pytest.raises(kd.RecordClaimRefused, match="RE-MINT") as exc:
            kd.claim_record(kata, rid)
        observed["b_denied"] = str(exc.value)
        # B must not have consumed anything: the pending record is still A's to move.
        observed["pending_intact"] = kd.record_path(kata, rid).is_file()

    monkeypatch.setattr(kd, "_CLAIM_RACE_HOOK", at_race_point)
    record = kd.claim_record(kata, rid)          # A wins

    assert observed["b_denied"], "the losing claimant was never denied"
    assert observed["pending_intact"] is True
    assert record["recordId"] == rid
    assert kd.record_path(kata, rid, consumed=True).is_file()
    assert not kd.record_path(kata, rid).exists()


def test_the_election_precedes_the_move_so_a_held_token_denies(tmp_path):
    """The token is what elects: a pre-existing token denies even with a pending record.

    This is the structural half of the fix — if the election were the rename (as DESIGN
    §1.5's POSIX reasoning assumed), a live pending record would still be claimable.
    """
    kata = _kata(tmp_path)
    rid = _mint_ok(kata, _FROZEN_PLAN)["recordId"]
    token = kd.claim_token_path(kata, rid)
    token.parent.mkdir(parents=True, exist_ok=True)
    token.touch()

    assert kd.record_path(kata, rid).is_file()          # the record IS still pending
    with pytest.raises(kd.RecordClaimRefused, match="RE-MINT"):
        kd.claim_record(kata, rid)
    assert kd.record_path(kata, rid).is_file()          # ...and was not consumed


def _raw_rename_race(root: Path, *, threads: int = 8) -> int:
    """Race raw ``os.rename`` (NO kata code). Returns how many callers reported success."""
    root.mkdir(parents=True, exist_ok=True)
    src, dst = root / "src", root / "dst"
    src.write_text("payload", encoding="utf-8")
    barrier = threading.Barrier(threads)

    def worker():
        barrier.wait()
        try:
            os.rename(src, dst)
            return 1
        except OSError:
            return 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=threads) as pool:
        return sum(f.result() for f in [pool.submit(worker) for _ in range(threads)])


def test_a_retained_record_is_never_clobbered_on_either_platform(tmp_path):
    """Platform-uniform refusal when a retained record exists but its token does not.

    Windows' rename refuses to replace; POSIX's rename replaces silently. Left to the OS
    this would destroy retained lineage and return a false "win" on Linux only — the same
    divergence class as the election defect itself. The engine refuses on both.
    """
    kata = _kata(tmp_path)
    rid = _mint_ok(kata, _FROZEN_PLAN)["recordId"]
    kd.claim_record(kata, rid)                       # legitimate claim: record retained
    retained = kd.record_path(kata, rid, consumed=True)
    assert retained.is_file()
    original = retained.read_text(encoding="utf-8")

    # A second record appears at the pending path and the token is gone (hand-removed).
    kd.record_path(kata, rid).write_text('{"impostor": true}', encoding="utf-8")
    kd.claim_token_path(kata, rid).unlink()

    with pytest.raises(kd.RecordClaimRefused, match="RE-MINT"):
        kd.claim_record(kata, rid)
    assert retained.read_text(encoding="utf-8") == original, "retained lineage was clobbered"


def test_os_rename_alone_is_not_a_portable_single_winner_primitive(tmp_path):
    """Why the claim election is O_CREAT|O_EXCL — the OS facts, pinned PER PLATFORM.

    DESIGN §1.5 reasons from POSIX: "two racing pre-hooks ⇒ one rename wins; the loser's
    validation fails". That reasoning is CORRECT on POSIX and WRONG on Windows, and the
    claim has to be single-winner on both. This pins the divergence so the fix's rationale
    stays evidence rather than folklore.

    **Windows** — measured by the builder on this host (CPython 3.14.3, NTFS)::

        rename(EXISTING -> EXISTING) : FileExistsError    (no replace)
        rename(SAME     -> SAME    ) : SUCCESS, a no-op   <-- the mechanism
        8 threads, same src -> same dst : ALL 8 succeeded, 200/200 rounds

    A Windows rename is issued against an OPEN HANDLE to the source (``FileRenameInfo``),
    so claimants that opened the source before the winner's rename landed are renaming a
    file to the path it already occupies — the no-op success above — and all report
    success. The primitive degrades from an election into a no-op.

    **POSIX** — reasoned from POSIX.1 ``rename(2)``, and PROVEN BY CI RATHER THAN BY THE
    BUILDER: I have no Linux host and did not run these locally, so the ubuntu leg is the
    evidence, not my assertion::

        rename(EXISTING -> EXISTING) : SUCCESS, atomically REPLACING dst
        rename(MISSING  -> *       ) : ENOENT / FileNotFoundError
        8 threads, same src -> same dst : exactly 1 winner

    POSIX ``rename`` resolves the source BY PATH and unlinks its directory entry
    atomically, so after the winner the source is gone and every later caller gets ENOENT
    — a genuine election. The replace-on-existing behaviour is exactly why ``os.replace``
    exists: to give Windows the POSIX semantics.

    An earlier revision of this test asserted the Windows refusal
    (``pytest.raises(OSError)`` on rename-over-existing) UNCONDITIONALLY and went red on
    the ubuntu CI leg — the D-25 lesson (platform-divergent primitives need
    platform-honest tests) applied to its own pin.

    Either way **the CLAIM is single-winner on both platforms**; that property is proven
    platform-agnostically by ``test_record_claim_is_atomic_single_use`` (25 in-process
    rounds) and ``test_claim_election_is_exclusive_under_a_forced_interleaving``.
    """
    src, dst = tmp_path / "src", tmp_path / "dst"
    src.write_text("x", encoding="utf-8")
    dst.write_text("y", encoding="utf-8")

    if sys.platform == "win32":
        with pytest.raises(FileExistsError):
            os.rename(src, dst)                  # Windows refuses to replace
        same = tmp_path / "same"
        same.write_text("z", encoding="utf-8")
        os.rename(same, same)                    # no raise: rename-to-self is a no-op
        assert same.is_file()
    else:
        os.rename(src, dst)                      # POSIX silently REPLACES the destination
        assert not src.exists()
        assert dst.read_text(encoding="utf-8") == "x"
        with pytest.raises(FileNotFoundError):   # the source is gone — the POSIX election
            os.rename(src, dst)

    winners = _raw_rename_race(tmp_path / "race")
    if sys.platform == "win32":
        # Deliberately WEAK. >1 is the defect and it is timing-dependent, so asserting it
        # exactly would be flaky — the very failure mode that produced this whole cure.
        # What matters is that 1 is NOT guaranteed here, which the docstring's measured
        # 200/200 tally records.
        assert winners >= 1
    else:
        assert winners == 1, "POSIX rename must elect exactly one winner"


# ----- THE DECLARED EVIDENCE NODE (PLAN frontmatter `evidence:` for seam-engine) -----
def test_record_claim_is_atomic_single_use(tmp_path):
    """RS-H2 — consumption is an ATOMIC CLAIM: exactly ONE winner, every loser denied.

    "Parallel-dispatch order-independence is ACHIEVED BY the claim, never assumed."

    The race is run ``_RACE_ROUNDS`` times IN-PROCESS. That is deliberate and is the
    regression guard for the defect this node originally missed: with a single round
    the bug reproduced only ~1 run in 5, so one pytest invocation could pass while the
    property was broken. A single invocation now samples the interleaving many times,
    and the deterministic proof lives in
    ``test_claim_election_is_exclusive_under_a_forced_interleaving``.
    """
    claimants = 8
    tally = collections.Counter()

    for round_no in range(_RACE_ROUNDS):
        kata = _kata(tmp_path / f"r{round_no}")
        record = _mint_ok(kata, _FROZEN_PLAN)
        rid = record["recordId"]
        barrier = threading.Barrier(claimants)

        def claim(_kata=kata, _rid=rid, _barrier=barrier):
            _barrier.wait()
            try:
                return ("won", kd.claim_record(_kata, _rid))
            except kd.RecordClaimRefused as exc:
                return ("denied", str(exc))

        with concurrent.futures.ThreadPoolExecutor(max_workers=claimants) as pool:
            futures = [pool.submit(claim) for _ in range(claimants)]
            outcomes = [f.result() for f in futures]

        winners = [o for o in outcomes if o[0] == "won"]
        losers = [o for o in outcomes if o[0] == "denied"]
        tally[len(winners)] += 1
        assert len(winners) == 1, (
            f"round {round_no}: exactly one claimant may win, got {len(winners)} "
            f"(outcomes={[o[0] for o in outcomes]})"
        )
        assert len(losers) == claimants - 1
        assert all("RE-MINT" in o[1] for o in losers), "every loser must name the re-mint path"
        assert winners[0][1]["recordId"] == rid

        # mark-consumed-and-RETAIN (R3-M1): the record persists for lineage...
        assert kd.record_path(kata, rid, consumed=True).is_file()
        # ...and the pending copy is gone, so a replay cannot re-claim it.
        assert not kd.record_path(kata, rid).exists()

        # A serial replay is refused with the RE-MINT path named (retry-race, pass-2 low 11).
        with pytest.raises(kd.RecordClaimRefused, match="RE-MINT"):
            kd.claim_record(kata, rid)

    assert tally == collections.Counter({1: _RACE_ROUNDS}), f"winner tally: {dict(tally)}"


def test_claim_of_a_never_minted_record_is_denied(tmp_path):
    kata = _kata(tmp_path)
    rid = kd.record_id(kb.read_cursor(kata).run_id, 99)
    with pytest.raises(kd.RecordClaimRefused, match="no pending dispatch record"):
        kd.claim_record(kata, rid)


def test_record_id_is_guarded_against_traversal(tmp_path):
    kata = _kata(tmp_path)
    with pytest.raises(kd.RecordClaimRefused, match="not a dispatch-record id"):
        kd.record_path(kata, "../../etc/passwd")


class TestValidateRecord:
    """Hook validation is SEMANTIC, not existence (TM-B4) — the T-04 staleness class."""

    def test_valid_record_passes(self, tmp_path):
        kata = _kata(tmp_path)
        record = _mint_ok(kata, _FROZEN_PLAN)
        report = kd.validate_record(
            record, kata_dir=kata, expected_brief_hash=record["briefHash"],
            expected_role="coder", plan_path=_FROZEN_PLAN, now=_NOW,
        )
        assert report["ok"] is True and report["expired"] is False

    def test_record_from_another_run_never_validates(self, tmp_path):
        kata = _kata(tmp_path)
        record = _mint_ok(kata, _FROZEN_PLAN)
        record = {**record, "runId": kb.mint_run_id(now=_NOW, entropy="ffff0000")}
        with pytest.raises(kd.SeamError, match="run-membership law"):
            kd.validate_record(record, kata_dir=kata, plan_path=_FROZEN_PLAN)

    def test_fabricated_record_without_cursor_lineage_fails(self, tmp_path):
        """S1: a record can be forged on disk; it cannot forge the cursor line beside it."""
        kata = _kata(tmp_path)
        real = _mint_ok(kata, _FROZEN_PLAN)
        seq = real["seq"] + 50
        forged = {**real, "seq": seq, "recordId": kd.record_id(real["runId"], seq)}
        with pytest.raises(kd.SeamError, match="NO matching SPAWN line"):
            kd.validate_record(forged, kata_dir=kata, plan_path=_FROZEN_PLAN)

    def test_brief_hash_mismatch_fails(self, tmp_path):
        kata = _kata(tmp_path)
        record = _mint_ok(kata, _FROZEN_PLAN)
        with pytest.raises(kd.SeamError, match="briefHash mismatch"):
            kd.validate_record(record, kata_dir=kata, expected_brief_hash="0" * 64,
                               plan_path=_FROZEN_PLAN)

    def test_expiry_is_advisory_never_load_bearing(self, tmp_path):
        """RS-M12: the atomic claim is THE replay control; wall-clock never refuses."""
        kata = _kata(tmp_path)
        record = _mint_ok(kata, _FROZEN_PLAN)
        much_later = datetime(2026, 8, 20, 12, 0, 0, tzinfo=UTC)
        report = kd.validate_record(record, kata_dir=kata, plan_path=_FROZEN_PLAN, now=much_later)
        assert report["ok"] is True          # a judge may legally return hours (days) later
        assert report["expired"] is True
        assert report["expiryIsAdvisory"] is True

    def test_claim_and_validate_denies_the_second_caller(self, tmp_path):
        kata = _kata(tmp_path)
        record = _mint_ok(kata, _FROZEN_PLAN)
        first = kd.claim_and_validate(kata, record["recordId"], plan_path=_FROZEN_PLAN, now=_NOW)
        assert first["validation"]["ok"] is True
        with pytest.raises(kd.RecordClaimRefused):
            kd.claim_and_validate(kata, record["recordId"], plan_path=_FROZEN_PLAN, now=_NOW)


# --------------------------------------------------------------------- §1.6 the parser


class TestVerdictParser:
    """The ONE verdict parser: strict fullmatch on LINE 1 of the ENVELOPE (DESIGN §1.6)."""

    def test_line_one_verdict_parses(self):
        assert kd.parse_verdict("VERDICT: PASS\nreasoning follows") == "PASS"
        assert kd.parse_verdict({"text": "VERDICT: NEEDS_WORK\nbody"}) == "NEEDS_WORK"
        assert kd.parse_verdict({"content": [{"text": "VERDICT: SHIP"}]}) == "SHIP"

    def test_body_embedded_verdict_is_not_a_verdict(self):
        """A fake VERDICT line in the BODY must not parse — repo content cannot forge one."""
        assert kd.parse_verdict("Here is my analysis.\nVERDICT: PASS\n") is None
        assert kd.parse_verdict("```\nVERDICT: PASS\n```") is None
        assert kd.parse_verdict("intro\n\nVERDICT: PASS") is None
        # ...including a diff hunk quoting a real verdict line
        assert kd.parse_verdict("+++ b/x\n+VERDICT: PASS\n") is None

    def test_line_one_must_fullmatch(self):
        assert kd.parse_verdict("VERDICT: PASS (with caveats)") is None
        assert kd.parse_verdict("The VERDICT: PASS") is None
        assert kd.parse_verdict("  VERDICT: PASS") is None
        assert kd.parse_verdict("VERDICT:PASS") is None
        assert kd.parse_verdict("") is None
        assert kd.parse_verdict(None) is None

    def test_trailing_whitespace_and_crlf_tolerated(self):
        assert kd.parse_verdict("VERDICT: PASS  \r\nbody") == "PASS"

    def test_closed_enum_binds_when_supplied(self):
        allowed = frozenset({"PASS", "NEEDS_WORK"})
        assert kd.parse_verdict("VERDICT: PASS", allowed=allowed) == "PASS"
        assert kd.parse_verdict("VERDICT: RUBBERSTAMP", allowed=allowed) is None


class TestCapture:
    def _minted(self, tmp_path):
        kata = _kata(tmp_path)
        record = kd.mint(
            governs="plan", role="evaluator", task_id="t-gate", kata_dir=kata,
            plan_path=_FROZEN_PLAN, brief={"o": "judge it"}, now=_NOW,
        )
        return kata, record

    def test_capture_writes_a_valid_verdict_line_and_payload(self, tmp_path):
        kata, record = self._minted(tmp_path)
        out = kd.capture(
            "VERDICT: PASS\nthe gate held", record["recordId"], kata_dir=kata,
            evidence_pointers=["RESULT.json"], repo_root=str(tmp_path), now=_NOW,
        )
        assert out["verdict"] == "PASS"
        # the conductor-invoked leg is declared Honor-system (RS-M5)
        assert out["grade"] == "Honor-system (engine-by-conductor)"
        line = out["line"]
        assert line.type == "VERDICT" and line.payload           # payload REQUIRED
        assert line.parent_seq == record["seq"]                  # chained to the SPAWN
        payload = json.loads(kb.payload_path(kata, line.payload).read_text(encoding="utf-8"))
        kb.validate_verdict_payload(payload)
        assert payload["judgeDispatchSeq"] == record["seq"]

    def test_no_match_is_the_absent_records_refusal_never_a_body_scan(self, tmp_path):
        kata, record = self._minted(tmp_path)
        with pytest.raises(kd.CaptureRefused, match="body is NEVER scanned"):
            kd.capture(
                "Summary of my work.\nVERDICT: PASS\n", record["recordId"], kata_dir=kata,
                repo_root=str(tmp_path), now=_NOW,
            )
        assert not [ln for ln in kb.read_cursor(kata).lines if ln.type == "VERDICT"]

    def test_absent_record_refuses(self, tmp_path):
        kata = _kata(tmp_path)
        rid = kd.record_id(kb.read_cursor(kata).run_id, 42)
        with pytest.raises(kd.CaptureRefused, match="ABSENT RECORD"):
            kd.capture("VERDICT: PASS", rid, kata_dir=kata, repo_root=str(tmp_path))

    def test_capture_works_on_a_consumed_record(self, tmp_path):
        """A judge returns AFTER its record was claimed — the normal path, not an error."""
        kata, record = self._minted(tmp_path)
        kd.claim_record(kata, record["recordId"])
        out = kd.capture("VERDICT: PASS", record["recordId"], kata_dir=kata,
                         repo_root=str(tmp_path), now=_NOW)
        assert out["verdict"] == "PASS"

    def test_down_line_for_a_child_run(self, tmp_path):
        """Children NEVER write the parent's log — the PARENT's seam writes DOWN (§2.3)."""
        kata, record = self._minted(tmp_path)
        child = kb.mint_run_id(now=_NOW, entropy="beef0001")
        out = kd.capture(
            "VERDICT: PASS\ndone", record["recordId"], kata_dir=kata, kind="down",
            child_run_id=child, reason="rendezvous", repo_root=str(tmp_path), now=_NOW,
        )
        assert out["line"].type == "DOWN"
        payload = json.loads(kb.payload_path(kata, out["line"].payload).read_text(encoding="utf-8"))
        assert payload["childRunId"] == child

    def test_capture_fires_the_snapshot_cadence_and_records_it(self, tmp_path):
        """D-17 wiring: the cadence fires on VERDICT and its outcome is RECORDED (R-M4)."""
        kata, record = self._minted(tmp_path)
        out = kd.capture("VERDICT: PASS", record["recordId"], kata_dir=kata,
                         repo_root=str(tmp_path), now=_NOW)
        assert out["snapshot"] is not None
        assert out["snapshot"]["kind"] == ktr.RECORD_KIND_SNAPSHOT
        assert out["snapshot"]["trigger"] == "VERDICT"
        recorded = kd.read_trail_records(kata)
        assert recorded and recorded[-1]["trigger"] == "VERDICT"


# --------------------------------------------------------------------- §2.6 phases


class TestPhaseGrammar:
    def test_the_closed_vocabulary(self, tmp_path):
        kata = _kata(tmp_path)
        for msg in ("open INITIATION", "close INITIATION", "open GRILL", "close GRILL",
                    "open EXECUTION wave=1", "close EXECUTION wave=1", "open FINAL-GATE"):
            kd.phase(kata, msg, repo_root=str(tmp_path), now=_NOW)
        lines = [ln for ln in kb.read_cursor(kata).lines if ln.type == "PHASE"]
        assert len(lines) == 7

    @pytest.mark.parametrize("msg,fragment", [
        ("open DESIGNING", "vocabulary is CLOSED"),
        ("start GRILL", "legal verb"),
        ("open", "with no phase"),
        ("open EXECUTION", "REQUIRES 'wave="),
        ("open EXECUTION wave=one", "REQUIRES 'wave="),
        ("open GRILL notakv", "not a 'k=v' parameter"),
        ("", "non-empty string"),
    ])
    def test_grammar_refusals(self, tmp_path, msg, fragment):
        kata = _kata(tmp_path)
        with pytest.raises(kd.PhaseRefused, match=re.escape(fragment)):
            kd.phase(kata, msg, repo_root=str(tmp_path), now=_NOW)

    def test_close_without_open_is_refused(self, tmp_path):
        kata = _kata(tmp_path)
        with pytest.raises(kd.PhaseRefused, match="not open on this run"):
            kd.phase(kata, "close GRILL", repo_root=str(tmp_path), now=_NOW)

    def test_double_open_is_refused(self, tmp_path):
        kata = _kata(tmp_path)
        kd.phase(kata, "open GRILL", repo_root=str(tmp_path), now=_NOW)
        with pytest.raises(kd.PhaseRefused, match="already OPEN"):
            kd.phase(kata, "open GRILL", repo_root=str(tmp_path), now=_NOW)

    def test_execution_waves_are_distinct_phase_identities(self, tmp_path):
        kata = _kata(tmp_path)
        kd.phase(kata, "open EXECUTION wave=1", repo_root=str(tmp_path), now=_NOW)
        kd.phase(kata, "close EXECUTION wave=1", repo_root=str(tmp_path), now=_NOW)
        kd.phase(kata, "open EXECUTION wave=2", repo_root=str(tmp_path), now=_NOW)
        assert kd.phase_state(kb.read_cursor(kata))["open"] == ["EXECUTION(wave=2)"]

    def test_phase_fires_the_snapshot_cadence(self, tmp_path):
        kata = _kata(tmp_path)
        out = kd.phase(kata, "open GRILL", repo_root=str(tmp_path), now=_NOW)
        assert out["snapshot"]["trigger"] == "PHASE"


class TestRunClosedTerminality:
    """'Run is closed' is a RECORDED terminal state, never convention (R4 residual 3)."""

    def _closed(self, tmp_path):
        kata = _kata(tmp_path)
        kd.phase(kata, "run-closed verdict=PASS", repo_root=str(tmp_path), now=_NOW)
        return kata

    def test_nothing_is_legal_after_run_closed(self, tmp_path):
        kata = self._closed(tmp_path)
        assert kd.is_run_closed(kb.read_cursor(kata)) is True
        with pytest.raises(kd.PhaseRefused, match="NOTHING is legal"):
            kd.phase(kata, "open CLOSEOUT", repo_root=str(tmp_path), now=_NOW)
        with pytest.raises(kd.MintRefused, match="is CLOSED"):
            _mint_ok(kata, _FROZEN_PLAN)
        with pytest.raises(kd.SeamError, match="is CLOSED"):
            kd.deny(kata, "late denial", legal_path="start a new run")

    def test_run_closed_refused_while_phases_are_open(self, tmp_path):
        kata = _kata(tmp_path)
        kd.phase(kata, "open CLOSEOUT", repo_root=str(tmp_path), now=_NOW)
        with pytest.raises(kd.PhaseRefused, match="still open"):
            kd.phase(kata, "run-closed", repo_root=str(tmp_path), now=_NOW)


def test_deny_names_the_legal_path(tmp_path):
    kata = _kata(tmp_path)
    line = kd.deny(kata, "record-less Agent launch", legal_path=kd.RETRY_RACE_LEGAL_PATH,
                   task="t1", now=_NOW)
    assert line.type == "DENY"
    assert "legal path:" in line.msg and "re-mint" in line.msg


def test_retry_race_message_names_the_remint():
    msg = kd.retry_race_deny_message("run-20260816T120000Z-abcd1234-3")
    assert "already consumed" in msg and "single-use" in msg
    assert "re-mint" in kd.RETRY_RACE_LEGAL_PATH


def test_every_seam_line_round_trips_through_the_cursor_parser(tmp_path):
    """SPAWN / DENY / PHASE / VERDICT are all valid under the W2 grammar (round-trip)."""
    kata = _kata(tmp_path)
    kd.phase(kata, "open EXECUTION wave=3", repo_root=str(tmp_path), now=_NOW)
    record = _mint_ok(kata, _FROZEN_PLAN)
    kd.capture("VERDICT: PASS", record["recordId"], kata_dir=kata, repo_root=str(tmp_path),
               now=_NOW)
    kd.deny(kata, "a bare launch", legal_path="mint via kata_dispatch.mint()", now=_NOW)

    raw = kb.cursor_path(kata).read_text(encoding="utf-8")
    cursor = kb.parse_cursor(raw)                       # a refusal here would raise
    types = {ln.type for ln in cursor.lines}
    assert {"PHASE", "SPAWN", "VERDICT", "DENY"} <= types
    # every parsed line re-renders through the canonical formatter (round-trip)
    for line in cursor.lines:
        rendered = kb.format_line(
            utc=line.utc, seq=line.seq, agent=line.agent, type=line.type,
            task=line.task, msg=line.msg, parent_seq=line.parent_seq, payload=line.payload,
        )
        assert kb.parse_line(rendered) == kb.CursorLine(
            utc=line.utc, seq=line.seq, agent=line.agent, type=line.type, task=line.task,
            msg=line.msg, parent_seq=line.parent_seq, payload=line.payload, pos=0,
        )


# --------------------------------------------------------------------- §2.4 run_start


class TestRunStart:
    def test_new_run_mints_and_rotates(self, tmp_path):
        kata = tmp_path / ".kata"
        first = kd.run_start(kata, repo_root=str(tmp_path), now=_NOW, entropy="aaaa0001")
        assert first["mode"] == "new" and first["rotated"] is False
        second = kd.run_start(kata, repo_root=str(tmp_path), now=_NOW, entropy="aaaa0002",
                              force_new=True)
        assert second["mode"] == "new" and second["rotated"] is True
        assert second["runId"] != first["runId"]
        assert second["prevRun"] == first["runId"]      # the loop-back chain pointer

    def test_resume_adopts_the_header_run_id_and_never_re_mints(self, tmp_path):
        kata = tmp_path / ".kata"
        first = kd.run_start(kata, repo_root=str(tmp_path), now=_NOW, entropy="bbbb0001")
        kd.phase(kata, "open EXECUTION wave=1", repo_root=str(tmp_path), now=_NOW)
        again = kd.run_start(kata, repo_root=str(tmp_path), now=_NOW, entropy="bbbb0002")
        assert again["mode"] == "resume" and again["adopted"] is True
        assert again["runId"] == first["runId"]
        assert again["rotated"] is False
        # the pre-resume cursor content survives (no rotation happened)
        assert [ln.type for ln in kb.read_cursor(kata).lines].count("PHASE") == 1

    def test_a_closed_run_rotates_and_mints(self, tmp_path):
        kata = tmp_path / ".kata"
        first = kd.run_start(kata, repo_root=str(tmp_path), now=_NOW, entropy="cccc0001")
        kd.phase(kata, "run-closed verdict=PASS", repo_root=str(tmp_path), now=_NOW)
        nxt = kd.run_start(kata, repo_root=str(tmp_path), now=_NOW, entropy="cccc0002")
        assert nxt["mode"] == "new" and nxt["rotated"] is True
        assert nxt["runId"] != first["runId"]

    def test_torn_rotation_is_detected(self, tmp_path):
        kata = tmp_path / ".kata"
        kata.mkdir(parents=True)
        kb.cursor_path(kata).write_text("this is not a run header\n", encoding="utf-8")
        with pytest.raises(kd.SeamError, match="TORN ROTATION"):
            kd.run_start(kata, repo_root=str(tmp_path), now=_NOW)

    def test_empty_cursor_is_reported_and_recovered(self, tmp_path):
        kata = tmp_path / ".kata"
        kata.mkdir(parents=True)
        kb.cursor_path(kata).write_text("   \n", encoding="utf-8")
        out = kd.run_start(kata, repo_root=str(tmp_path), now=_NOW, entropy="dddd0001")
        assert out["tornRotation"].startswith("empty-cursor")
        assert out["mode"] == "new"

    def test_orphan_records_are_reaped_never_deleted(self, tmp_path):
        """Crash mid-mint => a record with no cursor lineage => reaped at seam init (§1.5.5)."""
        kata = _kata(tmp_path)
        run_id = kb.read_cursor(kata).run_id
        orphan = kd.record_path(kata, kd.record_id(run_id, 7))
        orphan.parent.mkdir(parents=True, exist_ok=True)
        orphan.write_text(json.dumps({"runId": run_id, "seq": 7}), encoding="utf-8")
        live = _mint_ok(kata, _FROZEN_PLAN)

        out = kd.run_start(kata, repo_root=str(tmp_path), now=_NOW)
        assert out["mode"] == "resume"
        reaped = {r["recordId"] for r in out["reaped"]}
        assert orphan.stem in reaped
        assert live["recordId"] not in reaped                 # the in-flight record survives
        assert (kd.dispatch_dir(kata) / kd.REAPED_DIRNAME / orphan.name).is_file()
        assert kd.record_path(kata, live["recordId"]).is_file()

    def test_rotation_reaps_every_prior_run_record(self, tmp_path):
        kata = _kata(tmp_path)
        record = _mint_ok(kata, _FROZEN_PLAN)
        out = kd.run_start(kata, repo_root=str(tmp_path), now=_NOW, entropy="eeee0001",
                           force_new=True)
        assert {r["recordId"] for r in out["reaped"]} == {record["recordId"]}

    def test_run_marker_is_written_for_the_future_hook(self, tmp_path):
        """RS-L5 — the deny hook reads a marker, never walks the filesystem per call."""
        kata = tmp_path / ".kata"
        out = kd.run_start(kata, repo_root=str(tmp_path), now=_NOW, entropy="ffff0001")
        marker = kd.read_run_marker(kata)
        assert marker["runId"] == out["runId"]
        assert Path(marker["kataDir"]) == kata.resolve()

    def test_mint_refuses_without_a_live_cursor(self, tmp_path):
        with pytest.raises(kd.MintRefused, match="Call run_start"):
            kd.mint(governs="plan", role="coder", task_id="t", kata_dir=tmp_path / ".kata",
                    plan_path=_FROZEN_PLAN, brief={})


class TestProbesAndDeclaration:
    """The declaration is DERIVED from probes, never asserted (DESIGN §1.7 / §6.2 / §6.4)."""

    def test_pre_hook_declaration_is_honest(self, tmp_path):
        out = kd.run_start(tmp_path / ".kata", repo_root=str(tmp_path), now=_NOW,
                           entropy="1111aaaa")
        assert out["hook"]["installed"] is False
        assert out["tripwire"]["result"] == "no-result"
        assert out["enforcement"] == "Dormant (pre-activation)"
        assert out["capture"] == "Honor-system (engine-by-conductor)"
        assert out["resilience"]["display"] == "Partially verified (local)"
        assert out["declaration"].splitlines() == [
            "enforcement: Dormant (pre-activation)",
            "capture: Honor-system (engine-by-conductor)",
            "resilience: Partially verified (local)",
        ]

    def test_no_result_tripwire_never_inherits_a_prior_declaration(self):
        """pass-2 high 2: no result => Dormant, and a green fingerprint cannot rescue it."""
        green_fp = {"installed": True, "digest": "d", "matches": True}
        assert kd.derive_enforcement(
            green_fp, {"result": "no-result", "denied": None}
        ) == "Dormant (pre-activation)"

    def test_tripwire_and_fingerprint_are_jointly_necessary(self):
        denied = {"result": "probed", "denied": True}
        assert kd.derive_enforcement(
            {"installed": True, "matches": False}, denied) == "Dormant (pre-activation)"
        assert kd.derive_enforcement(
            {"installed": True, "matches": True}, denied) == "Verified (intercepting)"
        assert kd.derive_enforcement(
            {"installed": True, "matches": True}, denied, bash_leg=True
        ) == "Partially verified (bash-leg)"
        assert kd.derive_enforcement(
            {"installed": True, "matches": True}, denied, host_intercepts=False
        ) == "Honor-system (detection-only host)"

    def test_an_undenied_tripwire_is_dormant_not_verified(self):
        assert kd.derive_enforcement(
            {"installed": True, "matches": True}, {"result": "probed", "denied": False}
        ) == "Dormant (pre-activation)"

    def test_a_crashing_prober_is_a_no_result_never_a_pass(self):
        def boom():
            raise RuntimeError("hook wedged")
        assert kd.deny_tripwire_probe(boom)["result"] == "no-result"

    def test_injected_prober_is_honoured(self, tmp_path):
        out = kd.run_start(tmp_path / ".kata", repo_root=str(tmp_path), now=_NOW,
                           entropy="2222aaaa", tripwire_prober=lambda: True)
        assert out["tripwire"] == {"result": "probed", "denied": True, "reason": None}
        # ...but with no hook file the fingerprint cannot match, so it stays Dormant
        assert out["enforcement"] == "Dormant (pre-activation)"

    def test_hook_fingerprint_of_a_present_file(self, tmp_path):
        hook = tmp_path / "hook.py"
        hook.write_text("print('deny')\n", encoding="utf-8")
        fp = kd.hook_fingerprint(tmp_path, path=hook)
        assert fp["installed"] is True and len(fp["digest"]) == 64
        assert fp["matches"] is None                       # nothing to compare against
        matched = kd.hook_fingerprint(tmp_path, path=hook, expected_digest=fp["digest"])
        assert matched["matches"] is True

    def test_declaration_refuses_invented_vocabulary(self):
        with pytest.raises(ValueError, match="ONLY trust vocabulary"):
            kd.format_run_start_declaration(
                enforcement="Mostly working", capture="Verified (post-edge)",
                resilience="Partially verified (local)",
            )
        with pytest.raises(ValueError, match="table"):
            kd.format_run_start_declaration(
                enforcement="Dormant (pre-activation)", capture="Great",
                resilience="Partially verified (local)",
            )

    def test_capture_edge_derivation(self):
        assert kd.derive_capture(None) == "Honor-system (engine-by-conductor)"
        assert kd.derive_capture({"result": "probed", "captured": True}) == "Verified (post-edge)"


class TestConfigSettingsConsistency:
    """TM-H2 — settings drift is DETECTED at seam init."""

    def _settings(self, command, digest=None):
        hook = {"type": "command", "command": command}
        if digest:
            hook["digest"] = digest
        return {"hooks": {"PreToolUse": [{"matcher": "Agent", "hooks": [hook]}]}}

    def test_both_absent_is_consistent(self):
        out = kd.config_settings_consistency(None, None, fingerprint={"installed": False})
        assert out["consistent"] is True and out["drift"] == []

    def test_settings_registering_an_absent_hook_is_drift(self):
        out = kd.config_settings_consistency(
            None, self._settings("python adapters/claude/hooks/kata-seam-guard.py"),
            fingerprint={"installed": False},
        )
        assert out["drift"] == ["settings-registers-absent-hook"]

    def test_present_but_unregistered_is_drift(self):
        out = kd.config_settings_consistency(
            None, {}, fingerprint={"installed": True, "digest": "a"})
        assert out["drift"] == ["hook-present-but-unregistered"]

    def test_digest_mismatch_is_drift(self):
        out = kd.config_settings_consistency(
            None, self._settings("py kata-seam-guard.py", digest="old"),
            fingerprint={"installed": True, "digest": "new"},
        )
        assert "hook-digest-mismatch" in out["drift"]

    def test_config_declaring_an_unregistered_hook_is_drift(self):
        out = kd.config_settings_consistency(
            {"hooks": {"seamGuard": True}}, {}, fingerprint={"installed": False},
        )
        assert out["drift"] == ["config-declares-unregistered-hook"]


def test_a_worker_note_cannot_lift_the_resilience_level(tmp_path):
    """NOTE is a WORKER-authored type; only SEAM-authored ones feed the resilience fold.

    Without the agent filter, any worker could append a NOTE whose payload carried a
    40-hex commit + ref and lift the run's declared durability to Verified (full) — a
    trust claim manufactured by the thing being judged.
    """
    kata = _kata(tmp_path)
    cursor = kb.read_cursor(kata)
    seq = kb.next_seq(cursor)
    pointer = kb.payload_pointer(cursor.run_id, seq)
    kb.write_payload(kata, pointer, ktr.push_receipt_record(
        run_id=cursor.run_id, ref="refs/kata/trails/x", commit="a" * 40, remote="origin",
    ))
    kb.append_event(kata, "sneaky-worker", "NOTE", "t1", "totally a push receipt",
                    payload=pointer, seq=seq, now=_NOW)

    assert kd.read_trail_records(kata) == []
    assert ktr.derive_resilience(kd.read_trail_records(kata))["level"] == ktr.RESILIENCE_LOCAL

    # ...while the seam's own record IS folded (the filter is not simply "drop everything")
    kd.phase(kata, "open GRILL", repo_root=str(tmp_path), now=_NOW)
    assert kd.read_trail_records(kata), "seam-authored durability records must still fold"


def test_resilience_is_a_fold_over_recorded_fact(tmp_path):
    """R-M4: the declared level folds RECORDED snapshot outcomes, never the config flag."""
    kata = _kata(tmp_path)
    kd.phase(kata, "open GRILL", repo_root=str(tmp_path), now=_NOW)
    records = kd.read_trail_records(kata)
    assert records, "the cadence outcome must be recorded on the cursor"
    derived = ktr.derive_resilience(records, push_trail_configured=True)
    # tmp_path is not a git repo, so the snapshot honestly SKIPS — and a skip dominates.
    assert derived["level"] == ktr.RESILIENCE_DEGRADED
    assert derived["basis"]["pushConfigured"] is True      # echoed, never an input
