"""Tests for run_result.py — gate RESULT emitter.

Run from the tools/ directory:
    uv run pytest tests/test_run_result.py -q
"""

import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import run_result

REQUIRED_KEYS = {
    "gateName",
    "command",
    "exitCode",
    "passed",
    "failed",
    "skipped",
    "stdoutTail",
    "baselineSha",
    "resultSha",
    "utc",
    # TM-C2: run identity travels IN the artifact, so evidence membership is a
    # property of the file rather than of where it happens to sit.
    "runId",
    # BL-X13: per-gate counts + the honesty flags that make the top-level
    # scalars readable without guessing their scope.
    "gates",
    "multiGate",
    "countsScope",
}

# The 4-gate gauntlet fixture from BL-X13's filing (burn-02's real stdoutTail,
# trimmed to its load-bearing lines): a unit block reporting 4493 passed /
# 3 skipped, then an integration block reporting 2 passed, then two non-pytest
# gates. The pre-fix last-match-per-label scan reported `passed: 2` (integration)
# beside `skipped: 3` (unit) — a tuple NO single gate produced.
FOUR_GATE_GAUNTLET_OUTPUT = """\
................................                                         [100%]
4493 passed, 3 skipped, 2 deselected in 150.59s (0:02:30)
..                                                                       [100%]
2 passed, 4496 deselected in 2.59s
All checks passed!

49 skills checked - 0 error(s), 0 warning(s).
gauntlet: running pytest-unit: uv run pytest -m not integration -q
gauntlet: running pytest-integration: uv run pytest -m integration -q
gauntlet: running ruff: uvx ruff check .
gauntlet: running validate-skills: uv run python validate_skills.py

gauntlet summary:
  gate                 exit  status
  pytest-unit             0  PASS
  pytest-integration      0  PASS
  ruff                    0  PASS
  validate-skills         0  PASS
"""

LIVE_RUN_ID = "run-20260816T101500Z-a1b2c3"
PRIOR_RUN_ID = "run-20260731T090000Z-deadbe"


def _make_result(**overrides) -> dict:
    """Return a build_result call with sensible defaults."""
    kwargs = dict(
        gate_name="smoke",
        command="pytest tests/ -q",
        output="40 passed in 0.2s",
        exit_code=0,
        baseline_sha="abc1234",
        result_sha="def5678",
        utc="2026-01-01T00:00:00+00:00",
    )
    kwargs.update(overrides)
    return run_result.build_result(**kwargs)


# ---------------------------------------------------------------------------
# Key presence
# ---------------------------------------------------------------------------


def test_all_required_keys_present():
    result = _make_result()
    missing = REQUIRED_KEYS - result.keys()
    assert missing == set(), f"Missing keys: {missing}"


def test_no_unexpected_keys():
    result = _make_result()
    extra = result.keys() - REQUIRED_KEYS
    assert extra == set(), f"Unexpected extra keys: {extra}"


# ---------------------------------------------------------------------------
# Parsing — single-line pytest summary
# ---------------------------------------------------------------------------


def test_40_passed_parses_correctly():
    result = _make_result(output="40 passed in 0.2s", exit_code=0)
    assert result["passed"] == 40
    assert result["failed"] == 0
    assert result["skipped"] == 0
    assert result["exitCode"] == 0


def test_2_failed_38_passed_parses_correctly():
    result = _make_result(output="38 passed, 2 failed in 1.0s", exit_code=1)
    assert result["failed"] == 2
    assert result["passed"] == 38
    assert result["skipped"] == 0
    assert result["exitCode"] == 1


def test_skipped_parsed():
    result = _make_result(output="5 passed, 1 skipped in 0.5s", exit_code=0)
    assert result["passed"] == 5
    assert result["skipped"] == 1
    assert result["failed"] == 0


def test_all_three_counts_parsed():
    result = _make_result(output="10 passed, 3 failed, 2 skipped in 2.1s", exit_code=1)
    assert result["passed"] == 10
    assert result["failed"] == 3
    assert result["skipped"] == 2


def test_no_counts_in_output_defaults_to_zero():
    result = _make_result(output="no summary line here", exit_code=0)
    assert result["passed"] == 0
    assert result["failed"] == 0
    assert result["skipped"] == 0


# ---------------------------------------------------------------------------
# stdoutTail
# ---------------------------------------------------------------------------


def test_stdout_tail_short_output():
    short = "hello world"
    result = _make_result(output=short)
    assert result["stdoutTail"] == short


def test_stdout_tail_truncated_to_2000():
    long_output = "x" * 5000
    result = _make_result(output=long_output)
    assert len(result["stdoutTail"]) <= 2000
    assert result["stdoutTail"] == long_output[-2000:]


# ---------------------------------------------------------------------------
# sha passthrough
# ---------------------------------------------------------------------------


def test_shas_passed_through():
    result = _make_result(baseline_sha="aaaaaa", result_sha="bbbbbb")
    assert result["baselineSha"] == "aaaaaa"
    assert result["resultSha"] == "bbbbbb"


# ---------------------------------------------------------------------------
# utc — injectable for determinism
# ---------------------------------------------------------------------------


def test_utc_injectable():
    fixed = "2026-06-19T12:34:56+00:00"
    result = _make_result(utc=fixed)
    assert result["utc"] == fixed


def test_utc_defaults_to_now_when_none():
    """When utc=None, build_result must fill in a valid ISO-8601 UTC string."""
    result = run_result.build_result(
        gate_name="g",
        command="c",
        output="",
        exit_code=0,
        baseline_sha="x",
        result_sha="y",
        utc=None,
    )
    # Must parse as a valid datetime
    parsed = datetime.fromisoformat(result["utc"])
    assert parsed.tzinfo is not None


# ---------------------------------------------------------------------------
# write_result round-trip
# ---------------------------------------------------------------------------


def test_write_result_round_trips():
    result = _make_result()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "RESULT.json"
        run_result.write_result(result, path)
        loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded == result


def test_write_result_is_indented():
    result = _make_result()
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "RESULT.json"
        run_result.write_result(result, path)
        raw = path.read_text(encoding="utf-8")
    # indent=2 means lines start with spaces for nested keys
    assert "\n  " in raw


def test_write_result_accepts_str_path():
    result = _make_result()
    with tempfile.TemporaryDirectory() as tmp:
        path = str(Path(tmp) / "RESULT.json")
        run_result.write_result(result, path)
        loaded = json.loads(Path(path).read_text(encoding="utf-8"))
    assert loaded == result


# ---------------------------------------------------------------------------
# run_gate — Q-4 timeout (a hung gate must go RED, never hang; D136)
# ---------------------------------------------------------------------------


def test_run_gate_timeout_returns_failure_shaped_result(monkeypatch):
    """Q-4: subprocess.TimeoutExpired → (output-with-note, nonzero exit), never a raise."""
    import subprocess

    def hung_run(*args, **kwargs):
        raise subprocess.TimeoutExpired(
            cmd="pytest -q", timeout=kwargs.get("timeout"), output="partial gate output"
        )

    monkeypatch.setattr(run_result.subprocess, "run", hung_run)

    output, exit_code = run_result.run_gate("pytest -q", timeout=0.01)
    assert exit_code == 124, "timeout must map to a NONZERO exit code (gate red)"
    assert "[kata] gate runner timeout after 0.01s" in output
    assert "partial gate output" in output, "partial output captured before the hang is preserved"


def test_run_gate_timeout_result_feeds_build_result_as_failure(monkeypatch):
    """The timeout tuple composes into build_result as a failed (exitCode != 0) gate."""
    import subprocess

    monkeypatch.setattr(
        run_result.subprocess,
        "run",
        lambda *a, **k: (_ for _ in ()).throw(
            subprocess.TimeoutExpired(cmd="c", timeout=k.get("timeout"))
        ),
    )

    output, exit_code = run_result.run_gate("c", timeout=1.0)
    result = run_result.build_result(
        gate_name="smoke",
        command="c",
        output=output,
        exit_code=exit_code,
        baseline_sha="a",
        result_sha="b",
        utc="2026-01-01T00:00:00+00:00",
    )
    assert result["exitCode"] != 0
    assert "[kata] gate runner timeout" in result["stdoutTail"]


def test_run_gate_forwards_default_timeout_600(monkeypatch):
    """The default 600s timeout is forwarded to subprocess.run (bounded, overridable)."""
    seen: dict = {}

    class _Proc:
        stdout = "1 passed"
        returncode = 0

    def spy_run(*args, **kwargs):
        seen.update(kwargs)
        return _Proc()

    monkeypatch.setattr(run_result.subprocess, "run", spy_run)

    output, exit_code = run_result.run_gate("pytest -q")
    assert (output, exit_code) == ("1 passed", 0)
    assert seen.get("timeout") == 600.0, (
        "Q-4: run_gate must bound the subprocess with a 600s default timeout"
    )


# ---------------------------------------------------------------------------
# evidence_is_current — pure identity gate (D136 fail-closed)
# ---------------------------------------------------------------------------


def test_stale_result_sha_does_not_pass_identity():
    """The live-repo scenario: a green RESULT.json whose resultSha is stale
    (differs from the SHA actually being credited) does NOT read as current."""
    result = _make_result(exit_code=0, result_sha="159fc9b")
    ok, reason = run_result.evidence_is_current(result, "aaaaaaa0000000000000000000000000000000")
    assert ok is False
    assert reason == "stale-evidence"


def test_matching_sha_passes_identity():
    """Matching SHAs (same length) with a passing suite read as current — no
    false positive from the identity gate itself."""
    result = _make_result(exit_code=0, result_sha="abc1234")
    ok, reason = run_result.evidence_is_current(result, "abc1234")
    assert ok is True
    assert reason == ""


def test_short_vs_long_sha_forms_of_same_commit_match():
    """A 7-char resultSha and the SAME commit's 40-char HEAD form must match
    (git's short/long form mismatch, tolerated case-insensitively)."""
    result = _make_result(exit_code=0, result_sha="AbC1234")
    long_sha = "abc1234def5678900000000000000000000000"
    ok, reason = run_result.evidence_is_current(result, long_sha)
    assert ok is True
    assert reason == ""


def test_six_char_prefix_is_not_treated_as_a_match():
    """A 6-char (or shorter) prefix is rejected outright, never matched —
    below git's own short-SHA floor, a 'match' would be coincidental."""
    result = _make_result(exit_code=0, result_sha="abc123")
    ok, reason = run_result.evidence_is_current(result, "abc123def4567890000000000000000000000000")
    assert ok is False
    assert reason == "evidence-missing-sha"


def test_missing_result_sha_fails_closed():
    """resultSha absent from RESULT.json fails closed, never treated as a pass."""
    result = _make_result(exit_code=0)
    del result["resultSha"]
    ok, reason = run_result.evidence_is_current(result, "abc1234")
    assert ok is False
    assert reason == "evidence-missing-sha"


def test_empty_result_sha_fails_closed():
    """An empty-string resultSha is treated the same as missing."""
    result = _make_result(exit_code=0, result_sha="")
    ok, reason = run_result.evidence_is_current(result, "abc1234")
    assert ok is False
    assert reason == "evidence-missing-sha"


def test_none_result_json_is_no_evidence():
    """result_json=None (RESULT.json absent/unreadable) fails closed as no-evidence."""
    ok, reason = run_result.evidence_is_current(None, "abc1234")
    assert ok is False
    assert reason == "no-evidence"


def test_expected_sha_none_fails_closed():
    """expected_sha=None (D136 case) must NOT silently pass — the caller could
    not establish what SHA is being credited, so evidence can't be current."""
    result = _make_result(exit_code=0, result_sha="abc1234")
    ok, reason = run_result.evidence_is_current(result, None)
    assert ok is False
    assert reason == "unknown-expected-sha"


def test_expected_sha_empty_string_fails_closed():
    """expected_sha='' is treated the same as None."""
    result = _make_result(exit_code=0, result_sha="abc1234")
    ok, reason = run_result.evidence_is_current(result, "")
    assert ok is False
    assert reason == "unknown-expected-sha"


def test_evidence_is_current_is_pure_and_repeatable():
    """Determinism: same inputs -> same output, repeatable, no I/O/clock/subprocess."""
    result = _make_result(exit_code=0, result_sha="abc1234")
    results = {run_result.evidence_is_current(result, "abc1234def") for _ in range(5)}
    assert results == {(True, "")}

    stale_result = _make_result(exit_code=0, result_sha="0000000")
    stale_results = {
        run_result.evidence_is_current(stale_result, "abc1234def") for _ in range(5)
    }
    assert stale_results == {(False, "stale-evidence")}


# ---------------------------------------------------------------------------
# resolve_head_sha — the identity gate's subprocess sink (registered:
# protocol/exec-safety.md). Lives here (run_result.py is ALREADY a registered
# sink module via run_gate) rather than in benchmark.py, which must stay
# subprocess-free (test_benchmark.py::TestExecSafety::test_no_subprocess_import,
# a frozen invariant).
# ---------------------------------------------------------------------------

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_resolve_head_sha_resolves_via_git_rev_parse():
    """resolve_head_sha runs `git rev-parse HEAD` against the given root and
    returns the SAME SHA a direct `git rev-parse HEAD` reports for THIS repo —
    proves the sink is wired to real git, not a stub."""
    import subprocess as _subprocess
    real = _subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=str(_REPO_ROOT), capture_output=True, text=True, check=True,
    ).stdout.strip()
    assert run_result.resolve_head_sha(_REPO_ROOT) == real


def test_resolve_head_sha_returns_none_for_non_git_directory(tmp_path):
    """resolve_head_sha returns None (never raises) for a directory that is
    not inside a git repository."""
    non_repo = tmp_path / "not-a-repo"
    non_repo.mkdir()
    assert run_result.resolve_head_sha(non_repo) is None


def test_resolve_head_sha_returns_none_on_timeout(monkeypatch):
    """A hung git call fails closed (None), never hangs, never raises through."""
    import subprocess as _subprocess

    def _timeout(*args, **kwargs):
        raise _subprocess.TimeoutExpired(cmd="git", timeout=30)

    monkeypatch.setattr(run_result.subprocess, "run", _timeout)
    assert run_result.resolve_head_sha("/some/path") is None


def test_resolve_head_sha_returns_none_on_nonzero_exit(monkeypatch):
    """A non-zero git exit (e.g. detached/corrupt repo) fails closed (None),
    even when stdout carries SOMETHING non-empty (e.g. a partial/garbage
    line) — the exit code must gate the result, not just an empty-string check."""
    class _Proc:
        returncode = 128
        stdout = "fatal: not a git repository (or any of the parent directories): .git\n"

    monkeypatch.setattr(run_result.subprocess, "run", lambda *a, **k: _Proc())
    assert run_result.resolve_head_sha("/some/path") is None


# ---------------------------------------------------------------------------
# BL-X13 — per-gate parsed counts; no cross-gate chimera tuple.
# ---------------------------------------------------------------------------


def test_per_gate_parsed_counts():
    """DECLARED EVIDENCE NODE (PLAN evidence: evidence-identity).

    BL-X13: a 4-gate gauntlet must yield per-gate counts, and the top-level
    scalars must never be a cross-gate chimera. Pre-fix the artifact reported
    `passed: 2` (the INTEGRATION block) beside `skipped: 3` (the UNIT block) —
    a tuple no single gate produced.
    """
    result = _make_result(output=FOUR_GATE_GAUNTLET_OUTPUT, exit_code=0)

    # (a) Per-gate blocks exist, each internally coherent (one gate per tuple).
    gates = result["gates"]
    assert len(gates) == 2, f"two pytest summary blocks expected, got {gates}"

    unit, integration = gates
    assert (unit["passed"], unit["failed"], unit["skipped"]) == (4493, 0, 3)
    assert "4493 passed, 3 skipped" in unit["summaryLine"]
    assert (integration["passed"], integration["failed"], integration["skipped"]) == (2, 0, 0)
    assert "2 passed, 4496 deselected" in integration["summaryLine"]

    # (b) The honesty flags say what the scalars mean.
    assert result["multiGate"] is True
    assert result["countsScope"] == "aggregate"

    # (c) THE CHIMERA IS GONE: the exact pre-fix tuple must not be reproduced.
    chimera = (2, 0, 3)  # integration's `passed` beside unit's `skipped`
    assert (result["passed"], result["failed"], result["skipped"]) != chimera, (
        "BL-X13 regression: top-level counts are a cross-gate chimera again"
    )

    # (d) The scalars are a real aggregate — every label summed over gates[],
    #     so each number is attributable, none is borrowed from a sibling gate.
    for label in ("passed", "failed", "skipped"):
        assert result[label] == sum(block[label] for block in gates)
    assert (result["passed"], result["failed"], result["skipped"]) == (4495, 0, 3)


def test_single_gate_output_keeps_its_own_tuple_and_scope():
    """One gate → that gate's counts, scope declared as single-gate."""
    result = _make_result(output="10 passed, 3 failed, 2 skipped in 2.1s", exit_code=1)
    assert result["countsScope"] == "single-gate"
    assert result["multiGate"] is False
    assert len(result["gates"]) == 1
    assert (result["passed"], result["failed"], result["skipped"]) == (10, 3, 2)


def test_no_summary_line_is_scoped_no_counts_not_zero_failures():
    """A non-pytest gate parses to zeros, but the scope says so — zeros must not
    be readable as 'zero failures were observed'."""
    result = _make_result(output="All checks passed!", exit_code=0)
    assert result["gates"] == []
    assert result["countsScope"] == "no-counts"
    assert result["multiGate"] is False


def test_parse_gate_blocks_is_pure_and_repeatable():
    """Determinism: same output -> same blocks, no I/O/clock/subprocess."""
    first = run_result.parse_gate_blocks(FOUR_GATE_GAUNTLET_OUTPUT)
    for _ in range(4):
        assert run_result.parse_gate_blocks(FOUR_GATE_GAUNTLET_OUTPUT) == first


def test_legacy_flat_parser_is_documented_as_single_block_only():
    """_parse_pytest_counts is retained for gate_emit/BC and still exhibits the
    last-match-per-label behaviour — pinned here so nobody 'fixes' the flat
    parser by accident and thinks the chimera class is closed there."""
    counts = run_result._parse_pytest_counts(FOUR_GATE_GAUNTLET_OUTPUT)
    assert (counts["passed"], counts["skipped"]) == (2, 3)


# ---------------------------------------------------------------------------
# TM-C2 / TM-D5 — run membership: evidence is credited only for THIS run.
# ---------------------------------------------------------------------------


def _artifact(*, run_id=LIVE_RUN_ID, result_sha="abc1234def", **overrides) -> dict:
    return _make_result(exit_code=0, result_sha=result_sha, run_id=run_id, **overrides)


def test_run_id_is_stamped_into_the_artifact():
    """RESULT.json gains runId (DESIGN §2.4) — present, and None when unstamped."""
    assert _artifact()["runId"] == LIVE_RUN_ID
    assert _make_result()["runId"] is None


def test_wrong_runid_evidence_refused():
    """DECLARED EVIDENCE NODE (PLAN evidence: evidence-identity).

    R-H2: gate evidence must carry the EXACT runId of the run being gated. A
    PRIOR run's artifact sitting at the very same, perfectly fresh SHA is still
    refused — freshness alone never established membership, which is the
    July-artifact-read-raw class.
    """
    prior_run_artifact = _artifact(run_id=PRIOR_RUN_ID)

    # SHA-freshness alone would have said yes — prove the pre-fix leg passes.
    sha_only_ok, _ = run_result.evidence_is_current(prior_run_artifact, "abc1234def")
    assert sha_only_ok is True, "fixture must be SHA-FRESH so only membership can refuse it"

    ok, reason = run_result.evidence_is_current(
        prior_run_artifact, "abc1234def", expected_run_id=LIVE_RUN_ID
    )
    assert ok is False
    assert reason == "wrong-run"

    # The strict gate-consumer entry point refuses it too.
    ok, reason = run_result.gate_evidence_is_creditable(
        prior_run_artifact, "abc1234def", LIVE_RUN_ID
    )
    assert ok is False
    assert reason == "wrong-run"

    # ...and the matching-run artifact at the same SHA is credited, so the
    # refusal is discriminating, not blanket.
    ok, reason = run_result.gate_evidence_is_creditable(_artifact(), "abc1234def", LIVE_RUN_ID)
    assert ok is True
    assert reason == ""


def test_stale_sha_refused_even_when_the_run_matches():
    """Both legs are required: right run, wrong tree is still not evidence."""
    ok, reason = run_result.gate_evidence_is_creditable(
        _artifact(result_sha="0000000abc"), "abc1234def", LIVE_RUN_ID
    )
    assert ok is False
    assert reason == "stale-evidence"


def test_run_less_artifact_refused_when_membership_is_asserted():
    """A pre-runId (or hand-made) artifact fails closed — an absent runId is
    never a wildcard."""
    ok, reason = run_result.gate_evidence_is_creditable(
        _artifact(run_id=None), "abc1234def", LIVE_RUN_ID
    )
    assert ok is False
    assert reason == "evidence-missing-run-id"


def test_blank_run_id_on_either_side_fails_closed():
    """Whitespace-only identities are not identities."""
    ok, reason = run_result.gate_evidence_is_creditable(
        _artifact(run_id="   "), "abc1234def", LIVE_RUN_ID
    )
    assert (ok, reason) == (False, "evidence-missing-run-id")

    ok, reason = run_result.gate_evidence_is_creditable(_artifact(), "abc1234def", "  ")
    assert (ok, reason) == (False, "unknown-expected-run")


def test_run_id_match_is_exact_never_a_prefix():
    """Unlike a git SHA, a runId has no short form — a prefix match would be
    pure invention, so it must be refused."""
    ok, reason = run_result.gate_evidence_is_creditable(
        _artifact(run_id=LIVE_RUN_ID), "abc1234def", LIVE_RUN_ID + "-arm2"
    )
    assert (ok, reason) == (False, "wrong-run")

    ok, reason = run_result.gate_evidence_is_creditable(
        _artifact(run_id=LIVE_RUN_ID.upper()), "abc1234def", LIVE_RUN_ID
    )
    assert (ok, reason) == (False, "wrong-run")


def test_strict_gate_requires_the_caller_to_know_the_live_run():
    """require_run_id: a caller that cannot name the live run gets a refusal,
    never a skipped check (D136)."""
    ok, reason = run_result.gate_evidence_is_creditable(_artifact(), "abc1234def", None)
    assert (ok, reason) == (False, "unknown-expected-run")


def test_absent_artifact_is_a_refusal_not_a_pass():
    """Anti-vacuity (TM-D2 B4): absence of evidence is not evidence of green."""
    ok, reason = run_result.gate_evidence_is_creditable(None, "abc1234def", LIVE_RUN_ID)
    assert (ok, reason) == (False, "no-evidence")

    assert run_result.classify_evidence(None, "abc1234def", LIVE_RUN_ID)["role"] == "unusable"
    assert run_result.input_reference(None)["role"] == "unusable"


def test_membership_not_asserted_is_the_declared_bc_default():
    """BC posture, DECLARED: omitting expected_run_id keeps the pre-TM SHA-only
    behaviour and its exact reason codes for the existing callers
    (benchmark.score_arms, debug_report). It means 'membership NOT ASSERTED',
    NOT 'membership passed' — which is why gate consumers must use the strict
    entry point instead."""
    prior_run_artifact = _artifact(run_id=PRIOR_RUN_ID)

    # Old two-positional-arg call shape still works, unchanged.
    assert run_result.evidence_is_current(prior_run_artifact, "abc1234def") == (True, "")
    assert run_result.evidence_is_current(prior_run_artifact, "0000000000") == (
        False,
        "stale-evidence",
    )
    assert run_result.evidence_is_current(None, "abc1234def") == (False, "no-evidence")

    # ...and the SAME artifact is refused the moment membership IS asserted.
    assert run_result.gate_evidence_is_creditable(
        prior_run_artifact, "abc1234def", LIVE_RUN_ID
    ) == (False, "wrong-run")


def test_extended_identity_gate_is_pure_and_repeatable():
    """Determinism: same inputs -> same verdict, no I/O/clock/subprocess."""
    artifact = _artifact(run_id=PRIOR_RUN_ID)
    verdicts = {
        run_result.gate_evidence_is_creditable(artifact, "abc1234def", LIVE_RUN_ID)
        for _ in range(5)
    }
    assert verdicts == {(False, "wrong-run")}


# ---------------------------------------------------------------------------
# R-H2 / R2-M6 — the input-vs-gate-evidence distinction, exposed in the API.
# ---------------------------------------------------------------------------


def test_run_membership_law_travels_verbatim():
    """The law is pinned in code, not paraphrased. A dilution edit fails here."""
    law = run_result.RUN_MEMBERSHIP_LAW
    assert "gate evidence must carry the EXACT runId of the run being gated" in law
    assert "ancestor/prior-run artifacts are legal as *inputs* but never as gate evidence" in law
    assert "the sanctioned cross-run path is the parent consuming a child's recorded DOWN/VERDICT" in law
    assert "Each wave-loop's gate uses its own evidence; a re-loop pass re-emits its gates." in law

    baseline_law = run_result.BASELINE_INPUT_LAW
    assert "The green-at-fork baseline RESULT is an input, never gate evidence" in baseline_law
    assert "emits ITS OWN result under its own runId" in baseline_law


def test_prior_run_artifact_classifies_as_input_not_gate_evidence():
    """The law's positive half: an ancestor/prior-run artifact is LEGAL as an
    input, and the API says so — with its origin runId carried."""
    verdict = run_result.classify_evidence(
        _artifact(run_id=PRIOR_RUN_ID), "abc1234def", LIVE_RUN_ID
    )
    assert verdict["role"] == "input"
    assert verdict["creditableAsGateEvidence"] is False
    assert verdict["reason"] == "wrong-run"
    assert verdict["originRunId"] == PRIOR_RUN_ID
    assert verdict["originKnown"] is True
    assert verdict["law"] == run_result.RUN_MEMBERSHIP_LAW


def test_this_run_artifact_classifies_as_gate_evidence():
    verdict = run_result.classify_evidence(_artifact(), "abc1234def", LIVE_RUN_ID)
    assert verdict["role"] == "gate-evidence"
    assert verdict["creditableAsGateEvidence"] is True
    assert verdict["reason"] == ""
    assert verdict["originRunId"] == LIVE_RUN_ID


def test_run_less_artifact_classifies_as_input_with_unknown_origin():
    verdict = run_result.classify_evidence(_artifact(run_id=None), "abc1234def", LIVE_RUN_ID)
    assert verdict["role"] == "input"
    assert verdict["originRunId"] is None
    assert verdict["originKnown"] is False
    assert verdict["reason"] == "evidence-missing-run-id"


def test_unresolvable_context_classifies_as_unusable_never_input():
    """If the caller cannot say which SHA/run is being credited, the artifact is
    unusable — it must not quietly demote to a usable input."""
    assert run_result.classify_evidence(_artifact(), None, LIVE_RUN_ID)["role"] == "unusable"
    assert run_result.classify_evidence(_artifact(), "abc1234def", None)["role"] == "unusable"


def test_green_at_fork_baseline_is_recorded_as_an_input_with_origin_run_id():
    """R2-M6: the baseline RESULT is carried as an input reference bearing its
    ORIGIN runId, and can never be credited as this run's gate evidence."""
    baseline = _artifact(run_id=PRIOR_RUN_ID, result_sha="fork1234ab")
    ref = run_result.input_reference(baseline)

    assert ref["role"] == "input"
    assert ref["kind"] == "green-at-fork"
    assert ref["creditableAsGateEvidence"] is False
    assert ref["originRunId"] == PRIOR_RUN_ID
    assert ref["originKnown"] is True
    assert ref["resultSha"] == "fork1234ab"
    assert ref["exitCode"] == 0
    assert ref["law"] == run_result.BASELINE_INPUT_LAW


def test_input_reference_is_never_creditable_whatever_the_artifact_says():
    """Hard-wired False — an input record cannot be talked into being a verdict,
    even by an artifact that carries the LIVE runId."""
    ref = run_result.input_reference(_artifact(run_id=LIVE_RUN_ID), kind="prior-wave-gate")
    assert ref["creditableAsGateEvidence"] is False
    assert ref["kind"] == "prior-wave-gate"


# ---------------------------------------------------------------------------
# Report filenames carry the runId — protocol/observability.md:18.
# ---------------------------------------------------------------------------


def test_report_filename_carries_the_run_id():
    name = run_result.report_filename(LIVE_RUN_ID, "evidence-identity", "evaluator", "eval")
    assert name == f"{LIVE_RUN_ID}-evidence-identity-evaluator-eval.md"
    assert name.startswith(LIVE_RUN_ID + "-"), "runId leads so membership is legible from the name"


def test_report_filename_rejects_traversal_components():
    """CWE-23: a component may never carry a separator, '..', or a control char."""
    for bad in ("../escape", "a/b", "a\\b", "", "   ", "x\x00y"):
        try:
            run_result.report_filename(LIVE_RUN_ID, bad, "evaluator", "eval")
        except ValueError:
            continue
        raise AssertionError(f"report_filename accepted an unsafe component: {bad!r}")


def test_report_filename_membership_check_is_fail_closed():
    good = run_result.report_filename(LIVE_RUN_ID, "t1", "evaluator", "eval")
    assert run_result.report_filename_is_current(good, LIVE_RUN_ID) == (True, "")

    other = run_result.report_filename(PRIOR_RUN_ID, "t1", "evaluator", "eval")
    assert run_result.report_filename_is_current(other, LIVE_RUN_ID) == (False, "wrong-run")

    assert run_result.report_filename_is_current("t1-evaluator-eval.md", LIVE_RUN_ID) == (
        False,
        "evidence-missing-run-id",
    )
    assert run_result.report_filename_is_current(None, LIVE_RUN_ID) == (False, "no-evidence")
    assert run_result.report_filename_is_current("", LIVE_RUN_ID) == (False, "no-evidence")
    assert run_result.report_filename_is_current(good, None) == (False, "unknown-expected-run")


def test_report_filename_membership_ignores_the_directory():
    good = run_result.report_filename(LIVE_RUN_ID, "t1", "evaluator", "eval")
    assert run_result.report_filename_is_current(f".kata/reports/{good}", LIVE_RUN_ID) == (True, "")


# ---------------------------------------------------------------------------
# Artifact round-trip with the new fields
# ---------------------------------------------------------------------------


def test_run_id_and_gates_survive_the_write_read_round_trip():
    result = _make_result(output=FOUR_GATE_GAUNTLET_OUTPUT, run_id=LIVE_RUN_ID)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "RESULT.json"
        run_result.write_result(result, path)
        loaded = json.loads(path.read_text(encoding="utf-8"))

    assert loaded == result
    assert loaded["runId"] == LIVE_RUN_ID
    assert len(loaded["gates"]) == 2
    ok, reason = run_result.gate_evidence_is_creditable(loaded, "def5678", LIVE_RUN_ID)
    assert (ok, reason) == (True, "")
