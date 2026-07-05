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
from datetime import datetime, timezone

import pytest

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
    assert kt.slack_ratio(events, None, datetime.now(timezone.utc)) is None


def test_slack_ratio_zero_progress_none():
    """Zero-progress guard (v2-MED-6): done == 0 ⇒ None, never a manufactured trigger."""
    events = [{"ts": "2026-07-04T10:00:00Z", "done": 0, "owned": 1}]
    now = datetime(2026, 7, 4, 11, 0, 0, tzinfo=timezone.utc)
    assert kt.slack_ratio(events, 30.0, now) is None


def test_slack_ratio_computes():
    # start 10:00, now 10:30 = 30 min elapsed; done/owned = 2/4 = 0.5;
    # estimate 30 min → denom = 15 → ratio 2.0.
    events = [{"ts": "2026-07-04T10:00:00Z", "done": 2, "owned": 4}]
    now = datetime(2026, 7, 4, 10, 30, 0, tzinfo=timezone.utc)
    assert kt.slack_ratio(events, 30.0, now) == pytest.approx(2.0)


def test_slack_ratio_non_monotonic_raises():
    """RAISES: non-monotonic PROGRESS timestamps."""
    events = [
        {"ts": "2026-07-04T10:05:00Z", "done": 1, "owned": 4},
        {"ts": "2026-07-04T10:00:00Z", "done": 2, "owned": 4},
    ]
    now = datetime(2026, 7, 4, 10, 30, 0, tzinfo=timezone.utc)
    with pytest.raises(kt.TelemetryError, match="non-monotonic"):
        kt.slack_ratio(events, 30.0, now)


def test_slack_ratio_unparseable_ts_raises():
    """RAISES: an unparseable timestamp."""
    events = [{"ts": "not-a-timestamp", "done": 1, "owned": 4}]
    now = datetime(2026, 7, 4, 10, 30, 0, tzinfo=timezone.utc)
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
