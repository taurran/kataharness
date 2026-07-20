"""test_kata_telemetry.py — Freeze/Float M4-P0 telemetry substrate (TDD + D136 guards).

Every RAISES clause in the T1 spec has a named test proving loud failure on
absent/malformed input; BC leaves are pinned (``validate_inline_eval(None) == "off"``;
a plain commit body ⇒ ``None``); the digest round-trips stamp-mode == verify-mode on a
real tmp-repo commit, including a staged deletion as ``path:ABSENT`` and a rename as
``old:ABSENT`` + ``new:<blob>`` (AC-4). Real-git tests seed tmp repos with
``user.name``/``user.email`` set so commits work (the test_footprint pattern).
"""
from __future__ import annotations

import json
import subprocess
from datetime import UTC, datetime, timezone

import pytest

import kata_advisor as _ka
import kata_telemetry as kt

# ---------------------------------------------------------------------------
# real-git helpers (the test_footprint / test_contract_gate pattern)
# ---------------------------------------------------------------------------


def _git(args: list[str], cwd) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    )


def _seed(repo) -> None:
    _git(["init"], repo)
    _git(["checkout", "-b", "integration"], repo)
    _git(["config", "user.email", "t@t"], repo)
    _git(["config", "user.name", "t"], repo)


def _commit_with_trailer(repo, subject: str, trailer_line: str) -> str:
    _git(["commit", "-m", subject, "-m", trailer_line], repo)
    return _git(["rev-parse", "HEAD"], repo).stdout.strip()


# ===========================================================================
# 1. parse_checkpoint_trailer
# ===========================================================================


def _trailer(**over) -> str:
    rec = {"v": 1, "i": 0, "verify": {"exit": 0}}
    rec.update(over)
    return f"{kt._TRAILER_KEY} " + json.dumps(rec)


def test_parse_trailer_plain_commit_returns_none():
    assert kt.parse_checkpoint_trailer("just a normal commit\n\nno trailer here") is None


def test_parse_trailer_valid_record():
    body = "subject\n\n" + _trailer(i=2, verify={"exit": 0, "passed": 5, "failed": 0})
    rec = kt.parse_checkpoint_trailer(body)
    assert rec["v"] == 1 and rec["i"] == 2 and rec["verify"]["passed"] == 5


def test_parse_trailer_unknown_keys_tolerated():
    rec = json.dumps({"v": 1, "i": 0, "verify": {"exit": 0}, "futureKey": "ok"})
    parsed = kt.parse_checkpoint_trailer(f"{kt._TRAILER_KEY} {rec}")
    assert parsed["futureKey"] == "ok"


def test_parse_trailer_optional_nullable_ok():
    rec = json.dumps({"v": 1, "i": 0, "verify": {"exit": 0}, "lint": None, "evidence": None})
    assert kt.parse_checkpoint_trailer(f"{kt._TRAILER_KEY} {rec}") is not None


def test_parse_trailer_duplicate_raises():
    """RAISES: >1 trailer on one commit is ambiguous evidence (v2-MED-5)."""
    body = "subj\n\n" + _trailer(i=0) + "\n" + _trailer(i=1)
    with pytest.raises(kt.TelemetryError, match="trailers"):
        kt.parse_checkpoint_trailer(body)


def test_parse_trailer_malformed_json_raises():
    """RAISES: unparseable trailer JSON."""
    with pytest.raises(kt.TelemetryError, match="JSON parse failure"):
        kt.parse_checkpoint_trailer(f"{kt._TRAILER_KEY} {{not valid json")


def test_parse_trailer_schema_v_not_1_raises():
    with pytest.raises(kt.TelemetryError, match="v must == 1"):
        kt.parse_checkpoint_trailer(_trailer(v=2))


def test_parse_trailer_i_negative_raises():
    with pytest.raises(kt.TelemetryError, match="i must be"):
        kt.parse_checkpoint_trailer(_trailer(i=-1))


def test_parse_trailer_verify_exit_missing_raises():
    rec = json.dumps({"v": 1, "i": 0, "verify": {}})
    with pytest.raises(kt.TelemetryError, match="verify.exit"):
        kt.parse_checkpoint_trailer(f"{kt._TRAILER_KEY} {rec}")


def test_parse_trailer_bad_evidence_raises():
    with pytest.raises(kt.TelemetryError, match="evidence"):
        kt.parse_checkpoint_trailer(_trailer(evidence="not-a-sha"))


# --- Amendment #5 Part A (C-1): the optional owned-scoped verify exit -------


def test_parse_trailer_verify_owned_int_ok():
    """Amendment #5: verify.owned is an OPTIONAL int — the owned-file-scoped exit."""
    rec = json.dumps({"v": 1, "i": 0, "verify": {"exit": 1, "owned": 0}})
    parsed = kt.parse_checkpoint_trailer(f"{kt._TRAILER_KEY} {rec}")
    assert parsed["verify"]["owned"] == 0


def test_parse_trailer_verify_owned_null_ok():
    """owned: null ⇒ 'not measured' — valid (pre-amendment producer shape)."""
    rec = json.dumps({"v": 1, "i": 0, "verify": {"exit": 0, "owned": None}})
    assert kt.parse_checkpoint_trailer(f"{kt._TRAILER_KEY} {rec}") is not None


def test_parse_trailer_verify_owned_non_int_raises():
    """Fail-closed (D136): a present-but-non-int owned exit is malformed, never coerced."""
    rec = json.dumps({"v": 1, "i": 0, "verify": {"exit": 0, "owned": "0"}})
    with pytest.raises(kt.TelemetryError, match="verify.owned"):
        kt.parse_checkpoint_trailer(f"{kt._TRAILER_KEY} {rec}")


# ===========================================================================
# 2. scan_checkpoints
# ===========================================================================


def test_scan_checkpoints_oldest_first_and_records(tmp_path):
    repo = tmp_path
    _seed(repo)
    (repo / "base.txt").write_text("base", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "base"], repo)
    _git(["checkout", "-b", "task/T"], repo)

    (repo / "a.py").write_text("a=1\n", encoding="utf-8")
    _git(["add", "."], repo)
    _commit_with_trailer(repo, "chunk 0", _trailer(i=0))
    (repo / "b.py").write_text("b=2\n", encoding="utf-8")
    _git(["add", "."], repo)
    _commit_with_trailer(repo, "chunk 1", _trailer(i=1))

    results = kt.scan_checkpoints(str(repo), "task/T", "integration")
    assert [r["record"]["i"] for r in results] == [0, 1]  # oldest-first


def test_scan_checkpoints_plain_commit_record_none(tmp_path):
    repo = tmp_path
    _seed(repo)
    (repo / "base.txt").write_text("base", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "base"], repo)
    _git(["checkout", "-b", "task/T"], repo)
    (repo / "a.py").write_text("a=1\n", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "plain, no trailer"], repo)

    results = kt.scan_checkpoints(str(repo), "task/T", "integration")
    assert len(results) == 1 and results[0]["record"] is None


def test_scan_checkpoints_merge_without_trailer_skipped(tmp_path):
    repo = tmp_path
    _seed(repo)
    (repo / "base.txt").write_text("base", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "base"], repo)
    _git(["checkout", "-b", "task/M"], repo)
    (repo / "m.py").write_text("m=1\n", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "task work"], repo)
    _git(["checkout", "-b", "side"], repo)
    (repo / "s.py").write_text("s=1\n", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "side work"], repo)
    _git(["checkout", "task/M"], repo)
    _git(["merge", "--no-ff", "-m", "plain merge no trailer", "side"], repo)

    results = kt.scan_checkpoints(str(repo), "task/M", "integration")
    # the merge is skipped; the two non-merge commits remain (records None).
    assert len(results) == 2 and all(r["record"] is None for r in results)


def test_scan_checkpoints_merge_with_trailer_raises(tmp_path):
    """RAISES: a trailer on a merge commit — the chunk diff is undefined (v2-MED-5)."""
    repo = tmp_path
    _seed(repo)
    (repo / "base.txt").write_text("base", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "base"], repo)
    _git(["checkout", "-b", "task/M"], repo)
    (repo / "m.py").write_text("m=1\n", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "task work"], repo)
    _git(["checkout", "-b", "side"], repo)
    (repo / "s.py").write_text("s=1\n", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "side work"], repo)
    _git(["checkout", "task/M"], repo)
    _git(["merge", "--no-ff", "-m", "merge", "-m", _trailer(i=0), "side"], repo)

    with pytest.raises(kt.TelemetryError, match="merge commit"):
        kt.scan_checkpoints(str(repo), "task/M", "integration")


def test_scan_checkpoints_git_error_raises(tmp_path):
    """RAISES: any git error (D139 — never [] on a git failure)."""
    repo = tmp_path
    _seed(repo)
    (repo / "base.txt").write_text("base", encoding="utf-8")
    _git(["add", "."], repo)
    _git(["commit", "-m", "base"], repo)
    with pytest.raises(kt.TelemetryError):
        kt.scan_checkpoints(str(repo), "no-such-branch", "integration")


# ===========================================================================
# 3. evidence_digest / evidence_entries
# ===========================================================================


def _stage(repo, name, content) -> None:
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    _git(["add", name], repo)


def test_evidence_empty_paths_raises():
    """RAISES: a digest over nothing is a vacuous pin (D131 0-of-0)."""
    with pytest.raises(kt.TelemetryError, match="vacuous pin"):
        kt.evidence_digest(".", [], commit=None)


def test_evidence_stamp_never_tracked_raises(tmp_path):
    """RAISES: a path neither staged nor in HEAD is unresolvable (A1-Q2)."""
    repo = tmp_path
    _seed(repo)
    _stage(repo, "real.py", "x=1\n")
    _git(["commit", "-m", "base"], repo)
    with pytest.raises(kt.TelemetryError, match="neither staged nor tracked"):
        kt.evidence_entries(str(repo), ["ghost.py"], commit=None)


def test_evidence_stamp_staged_blob(tmp_path):
    repo = tmp_path
    _seed(repo)
    _stage(repo, "a.py", "a=1\n")
    entries = kt.evidence_entries(str(repo), ["a.py"], commit=None)
    assert entries[0].startswith("a.py:") and "ABSENT" not in entries[0]


def test_evidence_stamp_deletion_absent(tmp_path):
    repo = tmp_path
    _seed(repo)
    _stage(repo, "gone.py", "g=1\n")
    _git(["commit", "-m", "base"], repo)
    _git(["rm", "gone.py"], repo)  # staged deletion
    entries = kt.evidence_entries(str(repo), ["gone.py"], commit=None)
    assert entries == ["gone.py:ABSENT"]


def test_evidence_roundtrip_stamp_equals_verify(tmp_path):
    """AC-4 core: stamp-mode digest == verify-mode digest on a real commit."""
    repo = tmp_path
    _seed(repo)
    _stage(repo, "base.py", "b=0\n")
    _git(["commit", "-m", "base"], repo)
    _git(["checkout", "-b", "task/T"], repo)
    _stage(repo, "mod.py", "m=1\n")
    stamp = kt.evidence_digest(str(repo), ["mod.py"], commit=None)
    _git(["commit", "-m", "chunk"], repo)
    sha = _git(["rev-parse", "HEAD"], repo).stdout.strip()
    verify = kt.evidence_digest(str(repo), ["mod.py"], commit=sha)
    assert stamp == verify


def test_evidence_verify_root_commit_never_existed_raises(tmp_path):
    """RAISES: a path absent from a ROOT commit (empty parent tree) — F9 error class."""
    repo = tmp_path
    _seed(repo)
    _stage(repo, "only.py", "o=1\n")
    _git(["commit", "-m", "root"], repo)
    sha = _git(["rev-parse", "HEAD"], repo).stdout.strip()
    with pytest.raises(kt.TelemetryError, match="never existed"):
        kt.evidence_entries(str(repo), ["missing.py"], commit=sha)


# ===========================================================================
# 4. validate_inline_eval
# ===========================================================================


def test_validate_inline_eval_none_off():
    assert kt.validate_inline_eval(None) == "off"  # BC fail-safe


@pytest.mark.parametrize("mode", ["off", "telemetry", "on"])
def test_validate_inline_eval_valid_modes(mode):
    assert kt.validate_inline_eval(mode) == mode


@pytest.mark.parametrize("bad", ["ON", "Telemetry", "", "enabled", 1, True, ["on"]])
def test_validate_inline_eval_bad_raises(bad):
    with pytest.raises(kt.TelemetryError, match="not a valid inlineEval"):
        kt.validate_inline_eval(bad)


# ===========================================================================
# 5. Slack substrate
# ===========================================================================


def _pline(ts, task, done, owned, label="work") -> str:
    return f"{ts} | agent-1 | PROGRESS | {task} | {done}/{owned} {label}"


def test_parse_progress_events_extracts_this_task():
    board = "\n".join(
        [
            _pline("2026-07-04T10:00:00Z", "T1", 1, 5),
            _pline("2026-07-04T10:05:00Z", "T1", 3, 5),
        ]
    )
    events = kt.parse_progress_events(board, "T1")
    assert events == [
        {"ts": "2026-07-04T10:00:00Z", "done": 1, "owned": 5},
        {"ts": "2026-07-04T10:05:00Z", "done": 3, "owned": 5},
    ]


def test_parse_progress_events_ignores_other_tasks_and_types():
    board = "\n".join(
        [
            _pline("2026-07-04T10:00:00Z", "T2", 1, 5),  # other task
            "2026-07-04T10:01:00Z | agent-1 | CLAIM | T1 | started",  # other type
            _pline("2026-07-04T10:05:00Z", "T1", 2, 5),
        ]
    )
    assert kt.parse_progress_events(board, "T1") == [
        {"ts": "2026-07-04T10:05:00Z", "done": 2, "owned": 5}
    ]


def test_parse_progress_events_short_line_skipped():
    """Fail-safe (LOW-12): an unattributable <5-field line is skipped, not raised."""
    board = "corrupted line with no pipes\n" + _pline("2026-07-04T10:00:00Z", "T1", 1, 3)
    assert kt.parse_progress_events(board, "T1") == [
        {"ts": "2026-07-04T10:00:00Z", "done": 1, "owned": 3}
    ]


def test_parse_progress_events_malformed_doneowned_raises():
    """RAISES: a malformed done/owned on THIS task's PROGRESS line."""
    board = "2026-07-04T10:00:00Z | agent-1 | PROGRESS | T1 | notafraction work"
    with pytest.raises(kt.TelemetryError, match="done/owned"):
        kt.parse_progress_events(board, "T1")


def test_read_ledger_parses_rows(tmp_path):
    ledger = tmp_path / "ledger.md"
    ledger.write_text(
        "# header\n\nsome prose\n"
        + json.dumps({"v": 1, "runId": "r1"})
        + "\n"
        + json.dumps({"v": 1, "runId": "r2"})
        + "\n",
        encoding="utf-8",
    )
    rows = kt.read_ledger(ledger)
    assert [r["runId"] for r in rows] == ["r1", "r2"]


def test_read_ledger_missing_file_raises(tmp_path):
    """RAISES, always: a configured-but-dangling ledger path (MED-9/D45)."""
    with pytest.raises(kt.TelemetryError, match="absent"):
        kt.read_ledger(tmp_path / "nope.md")


def test_read_ledger_malformed_row_raises(tmp_path):
    """RAISES: a malformed row — never skip-and-average (MED-9b)."""
    ledger = tmp_path / "ledger.md"
    ledger.write_text("# header\n{not valid json here}\n", encoding="utf-8")
    with pytest.raises(kt.TelemetryError, match="malformed ledger row"):
        kt.read_ledger(ledger)


def test_class_median_below_min_samples_none():
    rows = [{"taskDurationsByClass": {"code": [10.0, 20.0]}}]
    assert kt.class_median(rows, "code", min_samples=5) is None


def test_class_median_computes():
    rows = [
        {"taskDurationsByClass": {"code": [10.0, 20.0, 30.0]}},
        {"taskDurationsByClass": {"code": [40.0, 50.0]}},
    ]
    assert kt.class_median(rows, "code", min_samples=5) == 30.0


def test_class_median_excludes_calibration():
    """F6: calibration rows never bias the real median."""
    rows = [
        {"taskDurationsByClass": {"code": [100.0, 200.0, 300.0, 400.0, 500.0]}},
        {"calibration": True, "taskDurationsByClass": {"code": [0.1, 0.1, 0.1, 0.1, 0.1]}},
    ]
    assert kt.class_median(rows, "code", min_samples=5) == 300.0


def test_resolve_estimate_ledger():
    assert kt.resolve_estimate(42.0, 99) == (42.0, "ledger")


def test_resolve_estimate_frontmatter():
    assert kt.resolve_estimate(None, 30) == (30.0, "frontmatter")


def test_resolve_estimate_absent():
    assert kt.resolve_estimate(None, None) == (None, "absent")


@pytest.mark.parametrize("bad", ["30", "abc", True, [1]])
def test_resolve_estimate_nonnumeric_raises(bad):
    """RAISES: a present-but-non-numeric frontmatter estimate (runtime backstop)."""
    with pytest.raises(kt.TelemetryError, match="non-numeric"):
        kt.resolve_estimate(None, bad)


def test_slack_ratio_none_estimate():
    events = [{"ts": "2026-07-04T10:00:00Z", "done": 2, "owned": 4}]
    assert kt.slack_ratio(events, None, datetime.now(UTC)) is None


def test_slack_ratio_zero_progress_none():
    """Zero-progress guard (v2-MED-6): done == 0 ⇒ None, never a manufactured trigger."""
    events = [{"ts": "2026-07-04T10:00:00Z", "done": 0, "owned": 1}]
    now = datetime(2026, 7, 4, 11, 0, 0, tzinfo=UTC)
    assert kt.slack_ratio(events, 30.0, now) is None


def test_slack_ratio_computes():
    # start 10:00, now 10:30 = 30 min elapsed; done/owned = 2/4 = 0.5;
    # estimate 30 min → denom = 15 → ratio 2.0.
    events = [{"ts": "2026-07-04T10:00:00Z", "done": 2, "owned": 4}]
    now = datetime(2026, 7, 4, 10, 30, 0, tzinfo=UTC)
    assert kt.slack_ratio(events, 30.0, now) == pytest.approx(2.0)


def test_slack_ratio_non_monotonic_raises():
    """RAISES: non-monotonic PROGRESS timestamps."""
    events = [
        {"ts": "2026-07-04T10:05:00Z", "done": 1, "owned": 4},
        {"ts": "2026-07-04T10:00:00Z", "done": 2, "owned": 4},
    ]
    now = datetime(2026, 7, 4, 10, 30, 0, tzinfo=UTC)
    with pytest.raises(kt.TelemetryError, match="non-monotonic"):
        kt.slack_ratio(events, 30.0, now)


def test_slack_ratio_unparseable_ts_raises():
    """RAISES: an unparseable timestamp."""
    events = [{"ts": "not-a-timestamp", "done": 1, "owned": 4}]
    now = datetime(2026, 7, 4, 10, 30, 0, tzinfo=UTC)
    with pytest.raises(kt.TelemetryError, match="unparseable"):
        kt.slack_ratio(events, 30.0, now)


# ===========================================================================
# 6. Records + ledger rows
# ===========================================================================


def test_build_task_telemetry_schema():
    checkpoints = [
        {"i": 0, "sha": "abc", "verifyExit": 0, "laneDrift": [], "slack": None},
        {"i": 1, "sha": "def", "verifyExit": 0, "laneDrift": [], "slack": 1.2},
    ]
    rec = kt.build_task_telemetry(
        task_id="T1",
        task_class="code",
        tier="sonnet",
        effective_mode="telemetry",
        checkpoints=checkpoints,
        gate_verdict="PASS",
        fix_cycles=1,
        wall_clock_s=123.4,
    )
    assert rec["v"] == 1
    assert rec["taskId"] == "T1"
    assert rec["chunkCount"] == 2
    assert rec["firstTripIndex"] is None  # always null in P0
    assert rec["ladderEvents"] == []  # always empty in P0
    assert rec["tokensIn"] is None and rec["tokensOut"] is None
    for key in ("class", "tier", "effectiveMode", "gateVerdict", "fixCycles", "wallClockS", "utc"):
        assert key in rec


def test_write_task_telemetry_writes_file(tmp_path):
    record = {"taskId": "T1", "v": 1}
    result = kt.write_task_telemetry(tmp_path, record)
    written = tmp_path / "telemetry" / "T1.json"
    assert written.exists()
    assert json.loads(written.read_text(encoding="utf-8")) == record
    assert "written" in result


def test_write_task_telemetry_oserror_skips(tmp_path):
    """Fail-soft: an OSError is caught and returned as a skip sentinel (LOW-15)."""
    # Make <kata_dir>/telemetry a FILE so mkdir raises FileExistsError (OSError).
    (tmp_path / "telemetry").write_text("blocker", encoding="utf-8")
    result = kt.write_task_telemetry(tmp_path, {"taskId": "T1"})
    assert "skipped" in result and "written" not in result


def test_checkpoint_changed_files(tmp_path):
    repo = tmp_path
    _seed(repo)
    _stage(repo, "base.py", "b=0\n")
    _git(["commit", "-m", "base"], repo)
    _stage(repo, "x.py", "x=1\n")
    _stage(repo, "y.py", "y=2\n")
    _git(["commit", "-m", "two files"], repo)
    sha = _git(["rev-parse", "HEAD"], repo).stdout.strip()
    assert kt.checkpoint_changed_files(str(repo), sha) == ["x.py", "y.py"]


def test_checkpoint_changed_files_git_error_raises(tmp_path):
    """RAISES: a git error (D139)."""
    repo = tmp_path
    _seed(repo)
    _stage(repo, "base.py", "b=0\n")
    _git(["commit", "-m", "base"], repo)
    with pytest.raises(kt.TelemetryError):
        kt.checkpoint_changed_files(str(repo), "deadbeefdeadbeefdeadbeefdeadbeefdeadbeef")


def test_checkpoint_lane_drift_reuses_footprint(tmp_path):
    repo = tmp_path
    _seed(repo)
    _stage(repo, "base.py", "b=0\n")
    _git(["commit", "-m", "base"], repo)
    _stage(repo, "owned/mod.py", "m=1\n")
    _stage(repo, "foreign/x.py", "x=1\n")
    _git(["commit", "-m", "mixed"], repo)
    sha = _git(["rev-parse", "HEAD"], repo).stdout.strip()
    drift = kt.checkpoint_lane_drift(str(repo), sha, ["owned/"])
    assert drift == ["foreign/x.py"]


def test_build_ledger_row_schema_and_oneline():
    row_str = kt.build_ledger_row({"runId": "r1", "target": "repo-x", "tasks": 3})
    assert "\n" not in row_str  # one line
    row = json.loads(row_str)
    for key in (
        "v", "utc", "runId", "target", "tasks", "checkpoints", "zeroCheckpointTasks",
        "firstPassAcceptanceByClassTier", "streaksByClass", "fixCycles", "gateRejections",
        "taskDurationsByClass", "wallClockS", "tokensIn", "tokensOut", "effectiveModes",
    ):
        assert key in row
    assert row["runId"] == "r1" and row["tasks"] == 3


def test_build_ledger_row_calibration_flag():
    row = json.loads(kt.build_ledger_row({"runId": "r1", "calibration": True}))
    assert row["calibration"] is True


def test_append_ledger_row_appends(tmp_path):
    ledger = tmp_path / "ledger.md"
    ledger.write_text("# header\n", encoding="utf-8")
    kt.append_ledger_row(ledger, kt.build_ledger_row({"runId": "r1"}))
    kt.append_ledger_row(ledger, kt.build_ledger_row({"runId": "r2"}))
    assert [r["runId"] for r in kt.read_ledger(ledger)] == ["r1", "r2"]


def test_append_ledger_row_missing_file_raises(tmp_path):
    """RAISES: append never creates the ledger (M4-L10/M1-L3)."""
    with pytest.raises(kt.TelemetryError, match="does not exist"):
        kt.append_ledger_row(tmp_path / "nope.md", "{}")


# ===========================================================================
# 7. CLI (worker tooling)
# ===========================================================================


def test_emit_trailer_default_staged_deletion_absent(tmp_path):
    """Named test: CLI default with a staged deletion ⇒ path:ABSENT in the digest."""
    repo = tmp_path
    _seed(repo)
    _stage(repo, "gone.py", "g=1\n")
    _git(["commit", "-m", "base"], repo)
    _git(["rm", "gone.py"], repo)  # staged deletion
    # the CLI default resolves staged paths itself; assert the entry is ABSENT.
    entries = kt.evidence_entries(str(repo), ["gone.py"], commit=None)
    assert "gone.py:ABSENT" in entries
    line = kt._emit_trailer(
        repo_root=str(repo), index=0, verify_exit=0,
        passed=None, failed=None, skipped=None, lint=None, paths=None,
    )
    rec = kt.parse_checkpoint_trailer(line)
    assert rec["evidence"] == kt.evidence_digest(str(repo), ["gone.py"], commit=None)


def test_emit_trailer_staged_rename_old_absent_new_blob(tmp_path):
    """Named test: staged RENAME ⇒ old:ABSENT AND new:<blob> both present."""
    repo = tmp_path
    _seed(repo)
    _stage(repo, "old_name.py", "content long enough to move\n")
    _git(["commit", "-m", "base"], repo)
    _git(["mv", "old_name.py", "new_name.py"], repo)  # staged rename
    entries = kt.evidence_entries(str(repo), ["old_name.py", "new_name.py"], commit=None)
    assert "old_name.py:ABSENT" in entries
    assert any(e.startswith("new_name.py:") and "ABSENT" not in e for e in entries)


def test_emit_trailer_empty_staging_raises(tmp_path):
    """F10: empty staging area maps to a worker-facing stage-first error."""
    repo = tmp_path
    _seed(repo)
    _stage(repo, "base.py", "b=0\n")
    _git(["commit", "-m", "base"], repo)  # nothing staged after commit
    with pytest.raises(kt.TelemetryError, match="nothing staged"):
        kt._emit_trailer(
            repo_root=str(repo), index=0, verify_exit=0,
            passed=None, failed=None, skipped=None, lint=None, paths=None,
        )


def test_main_missing_repo_root_usage_error():
    """Named test: absent --repo-root ⇒ usage error (the flag is required)."""
    with pytest.raises(SystemExit) as exc:
        kt.main(["emit-trailer", "--index", "0", "--verify-exit", "0"])
    assert exc.value.code == 2  # argparse usage error


def test_main_emit_prints_one_trailer_line(tmp_path, capsys):
    repo = tmp_path
    _seed(repo)
    _stage(repo, "base.py", "b=0\n")
    _git(["commit", "-m", "base"], repo)
    _stage(repo, "chunk.py", "c=1\n")
    rc = kt.main(
        ["emit-trailer", "--repo-root", str(repo), "--index", "0",
         "--verify-exit", "0", "--passed", "3"]
    )
    assert rc == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert len(out) == 1 and out[0].startswith(f"{kt._TRAILER_KEY} ")
    assert kt.parse_checkpoint_trailer(out[0])["verify"]["passed"] == 3


def test_emit_trailer_owned_exit_included(tmp_path):
    """Amendment #5: --owned-exit rides into verify.owned; absent ⇒ key omitted (BC)."""
    repo = tmp_path
    _seed(repo)
    _stage(repo, "base.py", "b=0\n")
    _git(["commit", "-m", "base"], repo)
    _stage(repo, "chunk.py", "c=1\n")
    line = kt._emit_trailer(
        repo_root=str(repo), index=0, verify_exit=1, owned_exit=0,
        passed=None, failed=None, skipped=None, lint=None, paths=None,
    )
    rec = kt.parse_checkpoint_trailer(line)
    assert rec["verify"]["exit"] == 1 and rec["verify"]["owned"] == 0
    # BC: omitting owned_exit produces a trailer with NO owned key at all.
    line_bc = kt._emit_trailer(
        repo_root=str(repo), index=0, verify_exit=1, owned_exit=None,
        passed=None, failed=None, skipped=None, lint=None, paths=None,
    )
    assert "owned" not in kt.parse_checkpoint_trailer(line_bc)["verify"]


def test_main_emit_owned_exit_flag(tmp_path, capsys):
    """The CLI --owned-exit flag round-trips through the printed trailer."""
    repo = tmp_path
    _seed(repo)
    _stage(repo, "base.py", "b=0\n")
    _git(["commit", "-m", "base"], repo)
    _stage(repo, "chunk.py", "c=1\n")
    rc = kt.main(
        ["emit-trailer", "--repo-root", str(repo), "--index", "0",
         "--verify-exit", "1", "--owned-exit", "0"]
    )
    assert rc == 0
    out = capsys.readouterr().out.strip().splitlines()
    assert kt.parse_checkpoint_trailer(out[0])["verify"]["owned"] == 0


# ===========================================================================
# AC-4 — full round-trip: CLI-emitted trailers reproduce stamped records exactly,
# including a deleted path as path:ABSENT and a rename as old:ABSENT + new:<blob>.
# ===========================================================================


def test_roundtrip_cli_trailers_reproduce_records(tmp_path):
    repo = tmp_path
    _seed(repo)
    # Base commit carries the files a later chunk will delete / rename.
    _stage(repo, "old_del.py", "will be deleted\n")
    _stage(repo, "to_rename.py", "will be renamed away\n")
    _git(["commit", "-m", "base"], repo)
    _git(["checkout", "-b", "task/T1"], repo)

    # Chunk 0: add a new module.
    _stage(repo, "mod_a.py", "a=1\n")
    line0 = kt._emit_trailer(
        repo_root=str(repo), index=0, verify_exit=0,
        passed=3, failed=0, skipped=None, lint=0, paths=None,
    )
    _commit_with_trailer(repo, "chunk 0", line0)

    # Chunk 1: delete one file, rename another (staged), add nothing new.
    _git(["rm", "old_del.py"], repo)
    _git(["mv", "to_rename.py", "renamed.py"], repo)
    line1 = kt._emit_trailer(
        repo_root=str(repo), index=1, verify_exit=0,
        passed=2, failed=0, skipped=None, lint=0, paths=None,
    )
    _commit_with_trailer(repo, "chunk 1", line1)

    # Scan reproduces both records oldest-first.
    results = kt.scan_checkpoints(str(repo), "task/T1", "integration")
    assert [r["record"]["i"] for r in results] == [0, 1]

    # Verify-mode digest over each commit's changed files reproduces the stamp.
    for entry in results:
        sha = entry["sha"]
        stamped = entry["record"]["evidence"]
        changed = kt.checkpoint_changed_files(str(repo), sha)
        assert kt.evidence_digest(str(repo), changed, commit=sha) == stamped

    # Chunk 1 verify-mode entries: deletion + rename-source ABSENT, rename-dest a blob.
    sha1 = results[1]["sha"]
    changed1 = kt.checkpoint_changed_files(str(repo), sha1)
    verify_entries = kt.evidence_entries(str(repo), changed1, commit=sha1)
    assert "old_del.py:ABSENT" in verify_entries  # deleted path round-trips as ABSENT
    assert "to_rename.py:ABSENT" in verify_entries  # rename source: old:ABSENT
    assert any(
        e.startswith("renamed.py:") and "ABSENT" not in e for e in verify_entries
    )  # rename dest: new:<blob>


# ===========================================================================
# P0.1 — ledger schema v2 (additive): perTask + failureKinds + degraded,
# reader tolerance (absent v ⇒ v1, unknown v ⇒ RAISE), failure_kinds_of accessor.
# ===========================================================================


# The EXACT committed row 1 from .planning/telemetry-ledger.md, verbatim (raw string
# so the ``×`` JSON escape stays byte-identical to the committed artifact).
_COMMITTED_V1_ROW = (
    r'{"v":1,"utc":"2026-07-04T19:03:44Z","runId":"m4p0-t5-calibration-2026-07-04",'
    r'"target":"scratch/strutil (calibration exercise)","tasks":2,"checkpoints":4,'
    r'"zeroCheckpointTasks":0,"firstPassAcceptanceByClassTier":{"code×sonnet":1.0},'
    r'"streaksByClass":{"code":[2,2]},"fixCycles":0,"gateRejections":0,'
    r'"taskDurationsByClass":{"code":[2.21,3.5]},"wallClockS":342.9,"tokensIn":null,'
    r'"tokensOut":116105,"effectiveModes":{"T-A":"telemetry","T-B":"telemetry"},'
    r'"calibration":true}'
)


def test_build_ledger_row_v2_schema_defaults():
    """A caller passing no v2 data still gets the v2 additive fields (now stamped v3)."""
    row = json.loads(kt.build_ledger_row({"runId": "r1"}))
    assert row["v"] == 3  # CA-L40: schema v2 → v3; the v2 additive fields are retained
    assert row["perTask"] == {}
    assert row["failureKinds"] == []
    assert row["degraded"] == []
    # every v1 field is retained
    for key in (
        "utc", "runId", "target", "tasks", "checkpoints", "zeroCheckpointTasks",
        "firstPassAcceptanceByClassTier", "streaksByClass", "fixCycles", "gateRejections",
        "taskDurationsByClass", "wallClockS", "tokensIn", "tokensOut", "effectiveModes",
    ):
        assert key in row


def test_build_ledger_row_v2_carries_additive_fields():
    row = json.loads(
        kt.build_ledger_row(
            {
                "runId": "r1",
                "perTask": {"T1": {"tokensIn": 10, "tokensOut": 20, "wallClockS": 5.0}},
                "failureKinds": [
                    {"taskId": "T2", "kind": "test-regression", "at": "2026-07-04T00:00:00Z"}
                ],
                "degraded": [{"scope": "T3", "reason": "tools-dir-unresolvable"}],
            }
        )
    )
    assert row["perTask"]["T1"] == {"tokensIn": 10, "tokensOut": 20, "wallClockS": 5.0}
    assert row["failureKinds"] == [
        {"taskId": "T2", "kind": "test-regression", "at": "2026-07-04T00:00:00Z"}
    ]
    assert row["degraded"] == [{"scope": "T3", "reason": "tools-dir-unresolvable"}]


def test_build_ledger_row_per_task_explicit_nulls():
    """perTask entries are forced to the 3-key shape with explicit nulls, never fabricated."""
    row = json.loads(
        kt.build_ledger_row({"runId": "r1", "perTask": {"T1": {"tokensOut": 99}}})
    )
    assert row["perTask"]["T1"] == {"tokensIn": None, "tokensOut": 99, "wallClockS": None}


def test_build_ledger_row_unknown_kind_raises():
    """RAISES at BUILD time: an unknown failure kind is a producer bug (P0.1 U1)."""
    with pytest.raises(kt.TelemetryError, match="not in the producer vocabulary"):
        kt.build_ledger_row(
            {"runId": "r1", "failureKinds": [{"taskId": "T1", "kind": "made-up", "at": "z"}]}
        )


def test_build_ledger_row_missing_kind_raises():
    """RAISES at BUILD time: a missing kind is a producer bug (unclassified is reader-only)."""
    with pytest.raises(kt.TelemetryError, match="not in the producer vocabulary"):
        kt.build_ledger_row({"runId": "r1", "failureKinds": [{"taskId": "T1", "at": "z"}]})


def test_unclassified_never_in_producer_vocabulary():
    """'unclassified' is reader-side only — never a producible FAILURE_KINDS value."""
    assert "unclassified" not in kt.FAILURE_KINDS
    with pytest.raises(kt.TelemetryError, match="not in the producer vocabulary"):
        kt.build_ledger_row(
            {"runId": "r1", "failureKinds": [{"taskId": "T1", "kind": "unclassified", "at": "z"}]}
        )


def test_ledger_v2_round_trip(tmp_path):
    """v2 round-trip: build → append → read_ledger → additive fields intact."""
    ledger = tmp_path / "ledger.md"
    ledger.write_text("# header\n", encoding="utf-8")
    kt.append_ledger_row(
        ledger,
        kt.build_ledger_row(
            {
                "runId": "r2",
                "perTask": {"T1": {"tokensIn": 1, "tokensOut": 2, "wallClockS": 3.0}},
                "failureKinds": [{"taskId": "T1", "kind": "lane-drift", "at": "2026-07-04T00:00:00Z"}],
                "degraded": [{"scope": "run", "reason": "x"}],
            }
        ),
    )
    rows = kt.read_ledger(ledger)
    assert len(rows) == 1
    row = rows[0]
    assert row["v"] == 3  # CA-L40: builder stamps v3; v2 additive fields carry through
    assert row["perTask"]["T1"]["tokensOut"] == 2
    assert row["failureKinds"][0]["kind"] == "lane-drift"
    assert row["degraded"] == [{"scope": "run", "reason": "x"}]


def test_read_ledger_v1_committed_row_tolerance(tmp_path):
    """v1 tolerance: the EXACT committed row 1 still parses via read_ledger (P0.1 U1)."""
    ledger = tmp_path / "ledger.md"
    ledger.write_text(
        "# M4 telemetry ledger\n\n<!-- rows below -->\n" + _COMMITTED_V1_ROW + "\n",
        encoding="utf-8",
    )
    rows = kt.read_ledger(ledger)
    assert len(rows) == 1
    row = rows[0]
    assert row["v"] == 1
    assert row["runId"] == "m4p0-t5-calibration-2026-07-04"
    assert row["firstPassAcceptanceByClassTier"] == {"code×sonnet": 1.0}
    assert row["calibration"] is True


def test_read_ledger_absent_v_reads_as_v1(tmp_path):
    """A row with an ABSENT v reads as v1 (parses; no raise) — LOW-5 contract edge."""
    ledger = tmp_path / "ledger.md"
    ledger.write_text('# header\n{"runId":"r1","tasks":1}\n', encoding="utf-8")
    rows = kt.read_ledger(ledger)
    assert rows == [{"runId": "r1", "tasks": 1}]


def test_read_ledger_unknown_version_raises(tmp_path):
    """RAISES: a PRESENT unknown ledger row version (P0.1 U1)."""
    ledger = tmp_path / "ledger.md"
    ledger.write_text('# header\n{"v":99,"runId":"r1"}\n', encoding="utf-8")
    with pytest.raises(kt.TelemetryError, match="unknown ledger row version"):
        kt.read_ledger(ledger)


def test_failure_kinds_of_v2_returns_field():
    row = {
        "v": 2,
        "failureKinds": [{"taskId": "T1", "kind": "packaging", "at": "z"}],
    }
    assert kt.failure_kinds_of(row) == [{"taskId": "T1", "kind": "packaging", "at": "z"}]


def test_failure_kinds_of_v1_with_rejections_unclassified():
    """A v1 row WITH gate rejections maps to the reader-side unclassified sentinel."""
    row = {"v": 1, "gateRejections": 2}
    assert kt.failure_kinds_of(row) == [{"kind": "unclassified"}]


def test_failure_kinds_of_v1_without_rejections_empty():
    """A v1 row with NO gate rejections maps to [] — never a fabricated failure."""
    assert kt.failure_kinds_of({"v": 1, "gateRejections": 0}) == []
    assert kt.failure_kinds_of({"v": 1}) == []


def test_class_median_v2_row_flows_identically():
    """A v2 row flows through class_median identically (duration source untouched)."""
    v2_row = json.loads(
        kt.build_ledger_row(
            {
                "runId": "r1",
                "taskDurationsByClass": {"code": [10.0, 20.0, 30.0, 40.0, 50.0]},
                "perTask": {"T1": {"tokensIn": None, "tokensOut": None, "wallClockS": 30.0}},
                "failureKinds": [{"taskId": "T1", "kind": "other", "at": "z"}],
            }
        )
    )
    assert v2_row["v"] == 3  # CA-L40: builder stamps v3; duration source untouched
    assert kt.class_median([v2_row], "code", min_samples=5) == 30.0


# ===========================================================================
# CA-P0 E6 — ledger schema v3 (additive): parentTokens per-phase readings,
# reader tolerance (v1/v2 committed shapes still parse, unknown v4 RAISES),
# parent_tokens_of accessor, null-vs-zero honesty. (DESIGN CA-L40; D142 precedent.)
# ===========================================================================


# The EXACT committed v2 row (m4p1 dogfood) from .planning/telemetry-ledger.md, verbatim
# (raw string so the ``×`` JSON escape stays byte-identical to the committed artifact).
_COMMITTED_V2_ROW = (
    r'{"v":2,"utc":"2026-07-04T20:38:54Z","runId":"m4p1-dogfood-build-2026-07-04",'
    r'"target":"KataHarness (self, P1 dogfooded build)","tasks":4,"checkpoints":10,'
    r'"zeroCheckpointTasks":0,"firstPassAcceptanceByClassTier":{"code×opus":1.0},'
    r'"streaksByClass":{"code":[3,2,3,2]},"fixCycles":0,"gateRejections":0,'
    r'"taskDurationsByClass":{"code":[11.1,7.2,9.5,3.6]},"wallClockS":1882.2,'
    r'"tokensIn":null,"tokensOut":509407,"effectiveModes":{"m4p1-W1":"telemetry",'
    r'"m4p1-W2":"telemetry","m4p1-W3":"telemetry","m4p1-W4":"telemetry"},'
    r'"perTask":{"m4p1-W1":{"tokensIn":null,"tokensOut":115127,"wallClockS":665.1},'
    r'"m4p1-W2":{"tokensIn":null,"tokensOut":111428,"wallClockS":433.2},'
    r'"m4p1-W3":{"tokensIn":null,"tokensOut":185088,"wallClockS":568.2},'
    r'"m4p1-W4":{"tokensIn":null,"tokensOut":97764,"wallClockS":215.7}},'
    r'"failureKinds":[],"degraded":[]}'
)


def test_known_ledger_versions_includes_three():
    """The reader's known-version set is exactly {1, 2, 3} after the CA-L40 v3 bump."""
    assert kt._KNOWN_LEDGER_VERSIONS == frozenset({1, 2, 3})


def test_build_ledger_row_v3_schema_defaults():
    """A caller passing no parentTokens still gets v:3 + an empty parentTokens map."""
    row = json.loads(kt.build_ledger_row({"runId": "r1"}))
    assert row["v"] == 3
    assert row["parentTokens"] == {}
    # every prior (v1 + v2) field is retained (additive, no backfill)
    for key in ("perTask", "failureKinds", "degraded", "utc", "runId", "tokensOut"):
        assert key in row


def test_build_ledger_row_v3_carries_parent_tokens():
    """parentTokens is carried through per-phase, ints preserved (CA-L40 additive)."""
    row = json.loads(
        kt.build_ledger_row(
            {"runId": "r1", "parentTokens": {"P0": 40000, "P1": 52310}}
        )
    )
    assert row["parentTokens"] == {"P0": 40000, "P1": 52310}


def test_build_ledger_row_parent_tokens_null_vs_zero_honesty():
    """A phase with no reading serializes as null — NEVER 0 (CA-L40 honesty pin)."""
    row_str = kt.build_ledger_row(
        {"runId": "r1", "parentTokens": {"P0": None, "P1": 40000}}
    )
    # the serialized JSON carries an explicit null, not a fabricated zero
    assert '"P0":null' in row_str
    assert '"P0":0' not in row_str
    row = json.loads(row_str)
    assert row["parentTokens"]["P0"] is None
    assert row["parentTokens"]["P1"] == 40000


def test_ledger_v3_round_trip(tmp_path):
    """v3 round-trip: build → append → read_ledger → parentTokens intact (nulls preserved)."""
    ledger = tmp_path / "ledger.md"
    ledger.write_text("# header\n", encoding="utf-8")
    kt.append_ledger_row(
        ledger,
        kt.build_ledger_row(
            {"runId": "r3", "parentTokens": {"P0": 41000, "P1": None}}
        ),
    )
    rows = kt.read_ledger(ledger)
    assert len(rows) == 1
    row = rows[0]
    assert row["v"] == 3
    assert row["parentTokens"] == {"P0": 41000, "P1": None}


def test_read_ledger_v3_row_parses(tmp_path):
    """A PRESENT v:3 row parses (the version-set guard mutation target: {1,2,3})."""
    ledger = tmp_path / "ledger.md"
    ledger.write_text(
        '# header\n{"v":3,"runId":"r3","parentTokens":{"P0":40000}}\n', encoding="utf-8"
    )
    rows = kt.read_ledger(ledger)
    assert rows[0]["v"] == 3
    assert rows[0]["parentTokens"] == {"P0": 40000}


def test_read_ledger_v2_committed_row_tolerance(tmp_path):
    """v2 tolerance: the EXACT committed v2 row still parses unchanged (§4 row 12 canary)."""
    ledger = tmp_path / "ledger.md"
    ledger.write_text(
        "# telemetry ledger\n\n<!-- rows below -->\n" + _COMMITTED_V2_ROW + "\n",
        encoding="utf-8",
    )
    rows = kt.read_ledger(ledger)
    assert len(rows) == 1
    row = rows[0]
    assert row["v"] == 2
    assert row["runId"] == "m4p1-dogfood-build-2026-07-04"
    assert row["firstPassAcceptanceByClassTier"] == {"code×opus": 1.0}
    assert row["perTask"]["m4p1-W3"]["tokensOut"] == 185088
    # a v2 row has NO parentTokens field (no backfill) — the accessor degrades to {}
    assert "parentTokens" not in row
    assert kt.parent_tokens_of(row) == {}


def test_read_ledger_v1_committed_row_still_parses_after_v3(tmp_path):
    """v1 tolerance survives the v3 bump: the committed v1 row still reads (§4 row 12)."""
    ledger = tmp_path / "ledger.md"
    ledger.write_text(
        "# header\n" + _COMMITTED_V1_ROW + "\n", encoding="utf-8"
    )
    rows = kt.read_ledger(ledger)
    assert rows[0]["v"] == 1
    assert kt.parent_tokens_of(rows[0]) == {}


def test_read_ledger_unknown_v4_raises(tmp_path):
    """RAISES: a PRESENT unknown v:4 row (fail-closed; D142/CA-L40 — present-unknown RAISES)."""
    ledger = tmp_path / "ledger.md"
    ledger.write_text('# header\n{"v":4,"runId":"r1"}\n', encoding="utf-8")
    with pytest.raises(kt.TelemetryError, match="unknown ledger row version"):
        kt.read_ledger(ledger)


def test_parent_tokens_of_v3_returns_field_nulls_preserved():
    """The accessor returns the parentTokens map verbatim, explicit nulls preserved."""
    row = {"v": 3, "parentTokens": {"P0": 40000, "P1": None}}
    assert kt.parent_tokens_of(row) == {"P0": 40000, "P1": None}


def test_parent_tokens_of_v1_v2_absent_returns_empty():
    """v1/v2/absent-field rows have no readings ⇒ {} (presence-discriminated, no backfill)."""
    assert kt.parent_tokens_of({"v": 1, "runId": "r1"}) == {}
    assert kt.parent_tokens_of({"v": 2, "perTask": {}}) == {}
    assert kt.parent_tokens_of({}) == {}


def test_class_median_v3_row_flows_identically():
    """A v3 row flows through class_median identically (duration source untouched, BC)."""
    v3_row = json.loads(
        kt.build_ledger_row(
            {
                "runId": "r1",
                "taskDurationsByClass": {"code": [10.0, 20.0, 30.0, 40.0, 50.0]},
                "parentTokens": {"P0": 40000},
            }
        )
    )
    assert v3_row["v"] == 3
    assert kt.class_median([v3_row], "code", min_samples=5) == 30.0


# ===========================================================================
# Adaptive-tiering AT-L20 / M4 Amendment #6 item 3 — additive v3 calibration
# keys: verdictByTier ("<verdict>×<tier>" counts, the τ/verdict calibration
# input) + tierEvents (the adaptive move audit trail). Rows STAY v:3 — NO v4
# is minted (AT-L20 hard rule; a v4 would RAISE in every deployed reader).
# Build-time RAISE on malformed producer input (the failureKinds precedent);
# absent ⇒ key OMITTED (pre-amendment row shape preserved); reader accessors
# absent-honest ({}/[]); calibration-row exclusion (the class_median F6
# discipline); overturn_rate as the first-class calibration metric.
# ===========================================================================


_VBT_VALID = {
    "continue×haiku": 12,
    "correct×sonnet": 2,
    "reroll×sonnet": 1,
    "overturned×haiku": 3,
}

_TIER_EVENT_VALID = {
    "at": "2026-07-05T10:00:00Z",
    "dispatch": "T1-attempt-3",
    "from": "haiku",
    "to": "sonnet",
    "reason": "failbump",
}


# --- build-time verdictByTier validation (the failureKinds RAISE precedent) --


def test_build_ledger_row_verdict_by_tier_valid_roundtrip(tmp_path):
    """Valid verdictByTier: build → append → read_ledger → accessor, intact, still v:3."""
    ledger = tmp_path / "ledger.md"
    ledger.write_text("# header\n", encoding="utf-8")
    kt.append_ledger_row(
        ledger, kt.build_ledger_row({"runId": "r1", "verdictByTier": dict(_VBT_VALID)})
    )
    rows = kt.read_ledger(ledger)
    assert len(rows) == 1
    assert rows[0]["v"] == 3  # AT-L20: additive keys, NEVER a v4
    assert rows[0]["verdictByTier"] == _VBT_VALID
    assert kt.verdict_by_tier_of(rows[0]) == _VBT_VALID


def test_build_ledger_row_verdict_by_tier_overturned_token_accepted():
    """'overturned' is a LEGAL verdict token — the overturned-screen-verdict convention key."""
    row = json.loads(
        kt.build_ledger_row({"runId": "r1", "verdictByTier": {"overturned×haiku": 1}})
    )
    assert row["verdictByTier"] == {"overturned×haiku": 1}
    assert "overturned" in kt.VERDICT_TOKENS


def test_build_ledger_row_verdict_by_tier_unknown_verdict_raises():
    """RAISES at BUILD time: an unknown verdict token is a producer bug (the failureKinds precedent)."""
    with pytest.raises(kt.TelemetryError, match="verdict token"):
        kt.build_ledger_row({"runId": "r1", "verdictByTier": {"approve×haiku": 1}})


def test_build_ledger_row_verdict_by_tier_case_variant_raises():
    """RAISES: verdict tokens are exact — a case-variant is malformed, never coerced (D45/GB12)."""
    with pytest.raises(kt.TelemetryError, match="verdict token"):
        kt.build_ledger_row({"runId": "r1", "verdictByTier": {"Continue×haiku": 1}})


@pytest.mark.parametrize(
    "bad_key",
    [
        "continue",  # no × separator at all
        "continue-haiku",  # wrong separator (ASCII hyphen, not ×)
        "×haiku",  # empty verdict
        "correct×",  # empty tier
        "correct×a×b",  # more than one separator — ambiguous tier
    ],
)
def test_build_ledger_row_verdict_by_tier_malformed_key_raises(bad_key):
    """RAISES at BUILD time: a key not of the exact '<verdict>×<tier>' shape."""
    with pytest.raises(kt.TelemetryError, match="verdictByTier"):
        kt.build_ledger_row({"runId": "r1", "verdictByTier": {bad_key: 1}})


def test_build_ledger_row_verdict_by_tier_negative_count_raises():
    """RAISES at BUILD time: a negative count (a count is a tally, never a delta)."""
    with pytest.raises(kt.TelemetryError, match="non-negative int"):
        kt.build_ledger_row({"runId": "r1", "verdictByTier": {"continue×haiku": -1}})


@pytest.mark.parametrize("bad_count", [1.5, "2", None, True, [1]])
def test_build_ledger_row_verdict_by_tier_non_int_count_raises(bad_count):
    """RAISES at BUILD time: a non-int count (bool rejected too — it subclasses int)."""
    with pytest.raises(kt.TelemetryError, match="non-negative int"):
        kt.build_ledger_row({"runId": "r1", "verdictByTier": {"continue×haiku": bad_count}})


@pytest.mark.parametrize("bad_value", [None, ["continue×haiku"], "continue×haiku", 3])
def test_build_ledger_row_verdict_by_tier_non_dict_raises(bad_value):
    """RAISES at BUILD time: a PRESENT verdictByTier must be an object — a present
    null is malformed, never read as absent (fail-closed, D136)."""
    with pytest.raises(kt.TelemetryError, match="verdictByTier"):
        kt.build_ledger_row({"runId": "r1", "verdictByTier": bad_value})


# --- build-time tierEvents validation ----------------------------------------


def test_build_ledger_row_tier_events_valid_carried():
    """A valid tierEvents entry (exactly the five string keys) is carried verbatim."""
    row = json.loads(
        kt.build_ledger_row({"runId": "r1", "tierEvents": [dict(_TIER_EVENT_VALID)]})
    )
    assert row["tierEvents"] == [_TIER_EVENT_VALID]


@pytest.mark.parametrize("missing", ["at", "dispatch", "from", "to", "reason"])
def test_build_ledger_row_tier_events_missing_key_raises(missing):
    """RAISES at BUILD time: a tierEvents entry missing any of the five keys."""
    entry = {k: v for k, v in _TIER_EVENT_VALID.items() if k != missing}
    with pytest.raises(kt.TelemetryError, match="tierEvents"):
        kt.build_ledger_row({"runId": "r1", "tierEvents": [entry]})


def test_build_ledger_row_tier_events_extra_key_raises():
    """RAISES at BUILD time: a tierEvents entry with an extra key — EXACTLY five keys."""
    entry = dict(_TIER_EVENT_VALID, surprise="x")
    with pytest.raises(kt.TelemetryError, match="tierEvents"):
        kt.build_ledger_row({"runId": "r1", "tierEvents": [entry]})


@pytest.mark.parametrize("key", ["at", "dispatch", "from", "to", "reason"])
def test_build_ledger_row_tier_events_non_str_value_raises(key):
    """RAISES at BUILD time: every tierEvents value must be a string."""
    entry = dict(_TIER_EVENT_VALID)
    entry[key] = 42
    with pytest.raises(kt.TelemetryError, match="tierEvents"):
        kt.build_ledger_row({"runId": "r1", "tierEvents": [entry]})


@pytest.mark.parametrize("bad_value", [None, {}, "event", 3])
def test_build_ledger_row_tier_events_non_list_raises(bad_value):
    """RAISES at BUILD time: a PRESENT tierEvents must be a list (present null ≠ absent)."""
    with pytest.raises(kt.TelemetryError, match="tierEvents"):
        kt.build_ledger_row({"runId": "r1", "tierEvents": bad_value})


def test_build_ledger_row_tier_events_non_object_entry_raises():
    """RAISES at BUILD time: a tierEvents entry must be a JSON object."""
    with pytest.raises(kt.TelemetryError, match="tierEvents"):
        kt.build_ledger_row({"runId": "r1", "tierEvents": ["not-an-object"]})


# --- absent ⇒ OMITTED (pre-amendment row shape preserved) + absent-honest reads


def test_build_ledger_row_new_keys_absent_omitted():
    """Absent verdictByTier/tierEvents ⇒ keys OMITTED from the row — not null, not
    defaulted; the pre-amendment v3 row shape is byte-preserved (AT-L20)."""
    row_str = kt.build_ledger_row({"runId": "r1"})
    row = json.loads(row_str)
    assert "verdictByTier" not in row
    assert "tierEvents" not in row
    assert "verdictByTier" not in row_str and "tierEvents" not in row_str


def test_verdict_by_tier_of_absent_returns_empty():
    """Absent-honest ({} — the parent_tokens_of/failure_kinds_of precedent): v1/v2/
    pre-amendment-v3 rows carry no verdictByTier and read as {}, never fabricated."""
    assert kt.verdict_by_tier_of({"v": 1, "runId": "r1"}) == {}
    assert kt.verdict_by_tier_of({"v": 2, "perTask": {}}) == {}
    assert kt.verdict_by_tier_of({"v": 3, "parentTokens": {}}) == {}
    assert kt.verdict_by_tier_of({}) == {}


def test_tier_events_of_absent_returns_empty():
    """Absent-honest ([]): rows without tierEvents read as an empty audit trail."""
    assert kt.tier_events_of({"v": 1, "runId": "r1"}) == []
    assert kt.tier_events_of({"v": 3, "parentTokens": {}}) == []
    assert kt.tier_events_of({}) == []


def test_verdict_by_tier_of_present_malformed_raises():
    """RAISES read-side: a PRESENT-but-malformed verdictByTier is fail-closed (the
    read_ledger row-validation posture) — never skipped, never coerced."""
    with pytest.raises(kt.TelemetryError, match="verdictByTier"):
        kt.verdict_by_tier_of({"v": 3, "verdictByTier": {"nonsense-key": 1}})
    with pytest.raises(kt.TelemetryError, match="verdictByTier"):
        kt.verdict_by_tier_of({"v": 3, "verdictByTier": None})


def test_tier_events_of_present_malformed_raises():
    """RAISES read-side: a PRESENT-but-malformed tierEvents is fail-closed."""
    with pytest.raises(kt.TelemetryError, match="tierEvents"):
        kt.tier_events_of({"v": 3, "tierEvents": [{"at": "z"}]})
    with pytest.raises(kt.TelemetryError, match="tierEvents"):
        kt.tier_events_of({"v": 3, "tierEvents": None})


def test_tier_events_of_present_valid_returns_verbatim():
    row = {"v": 3, "tierEvents": [dict(_TIER_EVENT_VALID)]}
    assert kt.tier_events_of(row) == [_TIER_EVENT_VALID]


# --- verdict_by_tier_totals (the class_median calibration-exclusion discipline)


def test_verdict_by_tier_totals_sums_across_rows():
    rows = [
        {"v": 3, "verdictByTier": {"continue×haiku": 2, "reroll×sonnet": 1}},
        {"v": 3, "verdictByTier": {"continue×haiku": 3, "overturned×haiku": 1}},
        {"v": 2, "runId": "old"},  # pre-amendment row contributes nothing
    ]
    assert kt.verdict_by_tier_totals(rows) == {
        "continue×haiku": 5,
        "reroll×sonnet": 1,
        "overturned×haiku": 1,
    }


def test_verdict_by_tier_totals_excludes_calibration_by_default():
    """F6 discipline: calibration:true rows never bias the verdict×tier totals."""
    rows = [
        {"v": 3, "verdictByTier": {"continue×haiku": 2}},
        {"v": 3, "calibration": True, "verdictByTier": {"continue×haiku": 100}},
    ]
    assert kt.verdict_by_tier_totals(rows) == {"continue×haiku": 2}


def test_verdict_by_tier_totals_include_calibration_flag():
    rows = [
        {"v": 3, "verdictByTier": {"continue×haiku": 2}},
        {"v": 3, "calibration": True, "verdictByTier": {"continue×haiku": 100}},
    ]
    assert kt.verdict_by_tier_totals(rows, include_calibration=True) == {
        "continue×haiku": 102
    }


def test_verdict_by_tier_totals_malformed_row_raises():
    """A malformed verdictByTier inside any aggregated row RAISES — the totals never
    silently skip a broken row (MED-9b's never-skip-and-average)."""
    rows = [{"v": 3, "verdictByTier": {"bogus": 1}}]
    with pytest.raises(kt.TelemetryError, match="verdictByTier"):
        kt.verdict_by_tier_totals(rows)


# --- overturn_rate (the first-class calibration metric) -----------------------


def test_overturn_rate_none_below_min_samples():
    """< 5 total correct+reroll+overturned counts ⇒ None (the class_median
    not-yet-meaningful discipline), never a rate over noise."""
    rows = [
        {
            "v": 3,
            "verdictByTier": {
                "overturned×haiku": 2,
                "correct×sonnet": 1,
                "reroll×sonnet": 1,
                # continue verdicts are NOT samples — the green path never re-adjudicates
                "continue×haiku": 500,
            },
        }
    ]
    assert kt.overturn_rate(rows) is None  # 4 < min_samples=5


def test_overturn_rate_arithmetic():
    """At exactly min_samples=5: 2 overturned of (2+2+1)=5 costly verdicts ⇒ 0.4."""
    rows = [
        {
            "v": 3,
            "verdictByTier": {
                "overturned×haiku": 2,
                "correct×sonnet": 2,
                "reroll×sonnet": 1,
                "continue×haiku": 50,
            },
        }
    ]
    assert kt.overturn_rate(rows) == pytest.approx(0.4)


def test_overturn_rate_continue_never_counted():
    """Mutation pin: continue verdicts are neither numerator nor denominator — only
    the costly (correct/reroll/overturned) verdicts are calibration samples."""
    rows = [{"v": 3, "verdictByTier": {"continue×haiku": 1000}}]
    assert kt.overturn_rate(rows) is None  # 0 samples, not 0.0


def test_overturn_rate_tier_filter():
    """tier= restricts to that tier's keys: overturned screens AT the screen tier +
    standing verdicts DECIDED at that tier (the documented key convention)."""
    rows = [
        {
            "v": 3,
            "verdictByTier": {
                "overturned×haiku": 3,
                "correct×haiku": 2,
                "correct×sonnet": 10,
                "reroll×sonnet": 5,
            },
        }
    ]
    assert kt.overturn_rate(rows, tier="haiku") == pytest.approx(0.6)  # 3 of 5
    assert kt.overturn_rate(rows, tier="sonnet") == pytest.approx(0.0)  # 0 of 15
    # unfiltered: 3 of 20
    assert kt.overturn_rate(rows) == pytest.approx(0.15)


def test_overturn_rate_excludes_calibration_by_default():
    real = {"v": 3, "verdictByTier": {"overturned×haiku": 1, "correct×sonnet": 4}}
    cal = {
        "v": 3,
        "calibration": True,
        "verdictByTier": {"overturned×haiku": 50, "correct×sonnet": 50},
    }
    assert kt.overturn_rate([real, cal]) == pytest.approx(0.2)  # 1 of 5, cal excluded
    assert kt.overturn_rate([real, cal], include_calibration=True) == pytest.approx(
        51 / 105
    )


# --- the reverse-direction test (freeze-gate H5's demand; §4 criterion 8) ------


def test_reverse_direction_v3_new_keys_read_by_strict_reader(tmp_path):
    """H5/criterion 8: a v:3 row CARRYING the new keys round-trips through the CURRENT
    strict read_ledger WITHOUT raising — the reader has no key whitelist; the additive
    keys ride v:3 and no v4 exists to brick a deployed reader mid-scan (AT-L20)."""
    new_code_row = json.dumps(
        {
            "v": 3,
            "runId": "at-run-1",
            "parentTokens": {"P0": 40000},
            "verdictByTier": {"continue×haiku": 4, "overturned×haiku": 1},
            "tierEvents": [dict(_TIER_EVENT_VALID)],
        },
        separators=(",", ":"),
    )
    ledger = tmp_path / "ledger.md"
    ledger.write_text("# telemetry ledger\n\n" + new_code_row + "\n", encoding="utf-8")
    rows = kt.read_ledger(ledger)  # the v0.2.1-era strict read path — must NOT raise
    assert len(rows) == 1
    assert rows[0]["v"] == 3
    assert kt.verdict_by_tier_of(rows[0]) == {"continue×haiku": 4, "overturned×haiku": 1}
    assert kt.tier_events_of(rows[0]) == [_TIER_EVENT_VALID]


def test_reverse_direction_pre_amendment_rows_absent_honest(tmp_path):
    """The other direction: a pre-amendment ledger (committed v1 + v2 rows, plus a
    pre-amendment v3 row with NO new keys) reads with the accessors returning {}/[]."""
    pre_v3 = kt.build_ledger_row({"runId": "pre-amendment"})
    assert "verdictByTier" not in pre_v3 and "tierEvents" not in pre_v3
    ledger = tmp_path / "ledger.md"
    ledger.write_text(
        "# header\n" + _COMMITTED_V1_ROW + "\n" + _COMMITTED_V2_ROW + "\n" + pre_v3 + "\n",
        encoding="utf-8",
    )
    rows = kt.read_ledger(ledger)
    assert len(rows) == 3
    for row in rows:
        assert kt.verdict_by_tier_of(row) == {}
        assert kt.tier_events_of(row) == []


def test_new_keys_row_json_roundtrip_byte_stable(tmp_path):
    """build_ledger_row output with the new keys parses via read_ledger AND re-serializes
    byte-identically (insertion order + compact separators preserved)."""
    row_str = kt.build_ledger_row(
        {
            "runId": "r1",
            "verdictByTier": dict(_VBT_VALID),
            "tierEvents": [dict(_TIER_EVENT_VALID)],
        }
    )
    assert "\n" not in row_str  # still one append-ready line
    ledger = tmp_path / "ledger.md"
    ledger.write_text("# header\n", encoding="utf-8")
    kt.append_ledger_row(ledger, row_str)
    rows = kt.read_ledger(ledger)
    # same serialization pins as the builder (compact separators, default ensure_ascii
    # — the ``×`` rides as the × escape, byte-identical to the committed rows)
    assert json.dumps(rows[0], separators=(",", ":")) == row_str


# ===========================================================================
# DET-03 / DET-08 (2026-07-12 health review) — pins + ledger byte stability
# ===========================================================================


def test_run_git_argv_pins_quotepath_and_show_signature(tmp_path, monkeypatch):
    """DET-03: _run_git is the single pin site — its fixed argv must carry
    core.quotepath=off (digest/lane-drift byte stability) AND
    log.showSignature=false (a signed commit under operator
    log.showSignature=true injects gpg: lines that misparse %P in
    scan_checkpoints' positional %P%n%B read)."""
    captured: dict = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

    monkeypatch.setattr(kt.subprocess, "run", fake_run)
    kt._run_git(str(tmp_path), ["show", "-s", "--format=%P%n%B", "HEAD"])

    cmd = captured["cmd"]
    assert cmd[0] == "git"
    sub_idx = cmd.index("show")
    pins = {
        cmd[i + 1] for i in range(sub_idx - 1) if cmd[i] == "-c"
    }
    assert "core.quotepath=off" in pins
    assert "log.showSignature=false" in pins


def test_build_ledger_row_byte_stable_across_producer_dict_order():
    """DET-08: two run summaries identical up to dict INSERTION ORDER must
    serialize to identical bytes — pass-through maps must not leak producer
    dict order into the committed calibration ledger. Readers are key-based
    (read_ledger + the *_of accessors + class_median), so sort_keys is safe."""
    a = {"runId": "r1", "target": "t", "utc": "2026-07-12T00:00:00Z"}
    a["streaksByClass"] = {"code": [3, 1], "doc": [2]}
    a["effectiveModes"] = {"on": 2, "off": 1}

    b = {"utc": "2026-07-12T00:00:00Z", "target": "t", "runId": "r1"}
    b["effectiveModes"] = {"off": 1, "on": 2}
    b["streaksByClass"] = {"doc": [2], "code": [3, 1]}

    row_a = kt.build_ledger_row(a)
    row_b = kt.build_ledger_row(b)
    assert row_a == row_b, "producer dict order leaked into the serialized ledger row"
    assert json.loads(row_a) == json.loads(row_b)


# --- DET-10 fold (2026-07-12 health review): netstring-framed evidence digest ----

def test_evidence_digest_netstring_disambiguates_newline_collision(monkeypatch):
    """DET-10: two entry partitions that collide under a bare '\n'.join must
    produce DISTINCT digests once netstring length-prefixed. A git-legal newline
    in a filename lets ``["a\nb"]`` (one entry) and ``["a", "b"]`` (two entries)
    stream the same bytes under bare join — the length prefix removes the frame
    ambiguity (the benchmark_control.content_hash / contract_edges pattern)."""
    partitions = iter([["a\nb"], ["a", "b"]])
    monkeypatch.setattr(kt, "evidence_entries", lambda *a, **k: next(partitions))
    d1 = kt.evidence_digest(".", ["x"], commit=None)
    d2 = kt.evidence_digest(".", ["x"], commit=None)
    assert d1 != d2, "bare-join collision leaked — evidence digest is not netstring-framed"


# ===========================================================================
# Advisor-executor run-ledger key (DESIGN §3.9 — additive, presence-discriminated;
# the verdictByTier/tierEvents precedent). ABSENT ⇒ OMITTED, pre-feature row
# byte-preserved (BC / AC #6). PRESENT ⇒ validated fail-closed (shape, non-negative
# ints, EV-1 outcome enum, null-pending allowed).
# ===========================================================================

_ADVISOR_VALID = {
    "consults": [
        {"id": "T1-1", "outcome": "advised-pass"},
        {"id": "T2-1", "outcome": None},  # pending pairing — explicit null is LEGAL
    ],
    "byEvent": {"advisor-fail-threshold": 1, "advisor-fix-loop-ceiling": 1},
    "budgetUsed": 2,
    "budgetCap": 5,
    "lapses": ["budget-exhausted"],
}


# --- BC: absent ⇒ omitted, row byte-preserved (AC #6, S-4) -------------------


def test_build_ledger_row_no_advisor_key_is_byte_preserved():
    """A pre-feature run summary (no advisor key) ⇒ NO advisor key in the row, and the
    row is deterministic/byte-identical for the identical summary (no null backfill)."""
    summary = {"utc": "2026-07-12T00:00:00Z", "runId": "r1", "target": "t", "tasks": 3}
    row_str = kt.build_ledger_row(summary)
    assert row_str == kt.build_ledger_row(dict(summary))  # byte-identical
    assert "advisor" not in json.loads(row_str)  # presence-discriminated, never null


# --- valid present ⇒ carried, round-trips, stays v:3 -------------------------


def test_build_ledger_row_advisor_valid_roundtrip(tmp_path):
    ledger = tmp_path / "ledger.md"
    ledger.write_text("# header\n", encoding="utf-8")
    kt.append_ledger_row(
        ledger, kt.build_ledger_row({"runId": "r1", "advisor": dict(_ADVISOR_VALID)})
    )
    rows = kt.read_ledger(ledger)
    assert len(rows) == 1
    assert rows[0]["v"] == 3  # additive key, NEVER a v4
    assert rows[0]["advisor"] == _ADVISOR_VALID


def test_build_ledger_row_advisor_from_ledger_fragment_roundtrips():
    """The producer (kata_advisor.ledger_fragment) and the consumer (this validator)
    agree end-to-end — a real fragment builds without RAISE and survives the row."""
    state = _ka.new_advisor_state()
    _ka.record_advisor_spend(state, "advisor-fail-threshold")
    _ka.record_outcome(state, "T1-1", "advised-pass")
    _ka.record_outcome(state, "T2-1", None)
    frag = _ka.ledger_fragment(state, 5)
    row = json.loads(kt.build_ledger_row({"runId": "r1", "advisor": frag}))
    assert row["advisor"] == frag


def test_build_ledger_row_advisor_every_outcome_enum_and_null_accepted():
    consults = [{"id": f"T{i}-1", "outcome": o} for i, o in enumerate(list(_ka.ADVISOR_OUTCOMES) + [None])]
    advisor = {"consults": consults, "byEvent": {}, "budgetUsed": 0, "budgetCap": 10, "lapses": []}
    row = json.loads(kt.build_ledger_row({"runId": "r1", "advisor": advisor}))
    assert row["advisor"]["consults"] == consults


# --- present-but-malformed ⇒ RAISE (fail-closed, D136) -----------------------


@pytest.mark.parametrize("bad_value", [None, [], "advisor", 3, True])
def test_build_ledger_row_advisor_non_dict_raises(bad_value):
    with pytest.raises(kt.TelemetryError, match="advisor"):
        kt.build_ledger_row({"runId": "r1", "advisor": bad_value})


@pytest.mark.parametrize("drop", sorted(kt._ADVISOR_LEDGER_KEYS))
def test_build_ledger_row_advisor_missing_key_raises(drop):
    advisor = {k: v for k, v in _ADVISOR_VALID.items() if k != drop}
    with pytest.raises(kt.TelemetryError, match="advisor"):
        kt.build_ledger_row({"runId": "r1", "advisor": advisor})


def test_build_ledger_row_advisor_extra_key_raises():
    advisor = dict(_ADVISOR_VALID, surprise="x")
    with pytest.raises(kt.TelemetryError, match="advisor"):
        kt.build_ledger_row({"runId": "r1", "advisor": advisor})


@pytest.mark.parametrize("key", ["budgetUsed", "budgetCap"])
@pytest.mark.parametrize("bad", [-1, 1.5, "2", None, True])
def test_build_ledger_row_advisor_bad_budget_int_raises(key, bad):
    advisor = dict(_ADVISOR_VALID, **{key: bad})
    with pytest.raises(kt.TelemetryError, match="non-negative int"):
        kt.build_ledger_row({"runId": "r1", "advisor": advisor})


@pytest.mark.parametrize("bad", [-1, 1.5, "1", None, True])
def test_build_ledger_row_advisor_bad_by_event_count_raises(bad):
    advisor = dict(_ADVISOR_VALID, byEvent={"advisor-fail-threshold": bad})
    with pytest.raises(kt.TelemetryError, match="non-negative int"):
        kt.build_ledger_row({"runId": "r1", "advisor": advisor})


@pytest.mark.parametrize("bad", [None, "x", 3, {"a": 1}])
def test_build_ledger_row_advisor_by_event_non_dict_raises(bad):
    advisor = dict(_ADVISOR_VALID, byEvent=bad) if not isinstance(bad, dict) else dict(_ADVISOR_VALID, byEvent={5: 1})
    with pytest.raises(kt.TelemetryError, match="byEvent"):
        kt.build_ledger_row({"runId": "r1", "advisor": advisor})


@pytest.mark.parametrize("bad", [None, "budget-exhausted", ["ok", 5], [None]])
def test_build_ledger_row_advisor_bad_lapses_raises(bad):
    advisor = dict(_ADVISOR_VALID, lapses=bad)
    with pytest.raises(kt.TelemetryError, match="lapses"):
        kt.build_ledger_row({"runId": "r1", "advisor": advisor})


def test_build_ledger_row_advisor_consults_non_list_raises():
    advisor = dict(_ADVISOR_VALID, consults={"id": "T1-1", "outcome": None})
    with pytest.raises(kt.TelemetryError, match="consults"):
        kt.build_ledger_row({"runId": "r1", "advisor": advisor})


@pytest.mark.parametrize(
    "entry",
    [
        {"id": "T1-1"},  # missing outcome
        {"outcome": None},  # missing id
        {"id": "T1-1", "outcome": None, "extra": 1},  # extra key
        {"id": "", "outcome": None},  # empty id
        {"id": 5, "outcome": None},  # non-string id
        "T1-1",  # non-object entry
    ],
)
def test_build_ledger_row_advisor_bad_consult_shape_raises(entry):
    advisor = dict(_ADVISOR_VALID, consults=[entry])
    with pytest.raises(kt.TelemetryError, match="advisor.consults"):
        kt.build_ledger_row({"runId": "r1", "advisor": advisor})


@pytest.mark.parametrize("bad", ["pass", "advised", "PASS", "advised_pass", 1, True])
def test_build_ledger_row_advisor_unknown_outcome_raises(bad):
    advisor = dict(_ADVISOR_VALID, consults=[{"id": "T1-1", "outcome": bad}])
    with pytest.raises(kt.TelemetryError, match="EV-1 enum"):
        kt.build_ledger_row({"runId": "r1", "advisor": advisor})
