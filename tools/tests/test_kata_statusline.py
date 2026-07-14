"""test_kata_statusline.py — TDD tests for kata_statusline (S1.5a).

Tests follow the FROZEN format from PLAN-s1.5.md Task S1.5a.
All tests are hermetic (tmp_path only, no real .kata dirs).
"""

from __future__ import annotations

import json
import os
import sys
import types
from datetime import UTC, datetime, timezone
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers to build duck-typed ViewModels and TaskRows
# ---------------------------------------------------------------------------


def _task(percent: int = 50, done: bool = False) -> types.SimpleNamespace:
    """Return a duck-typed task with .percent and .done."""
    t = types.SimpleNamespace()
    t.percent = percent
    t.done = done
    return t


def _vm(
    *,
    waiting: bool = False,
    phase: str = "EXECUTE",
    tasks=None,
    gate: str | None = None,
    drift: int = 0,
) -> types.SimpleNamespace:
    """Return a duck-typed ViewModel."""
    vm = types.SimpleNamespace()
    vm.waiting = waiting
    vm.phase = phase
    vm.tasks = tasks if tasks is not None else []
    vm.gate = gate
    vm.driftEscalations = (drift, 0)
    return vm


# ---------------------------------------------------------------------------
# Import the module under test
# ---------------------------------------------------------------------------

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import kata_statusline  # noqa: E402  (must come after sys.path update)

# ---------------------------------------------------------------------------
# render_statusline — waiting / idle line
# ---------------------------------------------------------------------------


class TestRenderStatuslineWaiting:
    def test_waiting_returns_idle_line(self):
        vm = _vm(waiting=True)
        result = kata_statusline.render_statusline(vm)
        assert result == "KATAHARNESS 改善型 │ ⏳ idle — no active run"

    def test_waiting_ignores_tasks(self):
        vm = _vm(waiting=True, tasks=[_task(50)])
        result = kata_statusline.render_statusline(vm)
        assert result == "KATAHARNESS 改善型 │ ⏳ idle — no active run"


# ---------------------------------------------------------------------------
# render_statusline — active line (frozen format)
# ---------------------------------------------------------------------------


class TestRenderStatuslineActive:
    def _active_vm(self):
        """A VM with two tasks: 50% undone and 100% done."""
        t1 = _task(percent=50, done=False)
        t2 = _task(percent=100, done=True)
        return _vm(
            waiting=False,
            phase="EXECUTE",
            tasks=[t1, t2],
            gate="ok",
            drift=2,
        )

    def test_contains_header(self):
        vm = self._active_vm()
        result = kata_statusline.render_statusline(vm)
        assert result.startswith("KATAHARNESS 改善型 │")

    def test_contains_phase(self):
        vm = self._active_vm()
        result = kata_statusline.render_statusline(vm)
        assert " │ EXECUTE │ " in result

    def test_bar_is_exactly_8_chars(self):
        vm = self._active_vm()
        result = kata_statusline.render_statusline(vm)
        # Bar is between the phase segment and the percent number
        # Format: phase │ <bar> <pct>% │ …
        parts = result.split(" │ ")
        # parts[2] should be "<bar> <pct>%"
        bar_pct_segment = parts[2]
        bar_part = bar_pct_segment.split()[0]
        assert len(bar_part) == 8
        assert all(c in ("▰", "▱") for c in bar_part)

    def test_bar_chars_are_block_chars(self):
        vm = _vm(
            waiting=False,
            phase="EXECUTE",
            tasks=[_task(percent=0, done=False)],
            gate=None,
            drift=0,
        )
        result = kata_statusline.render_statusline(vm)
        parts = result.split(" │ ")
        bar_pct_segment = parts[2]
        bar_part = bar_pct_segment.split()[0]
        # At 0% all should be empty
        assert bar_part == "▱" * 8

    def test_bar_full_at_100pct(self):
        vm = _vm(
            waiting=False,
            phase="EXECUTE",
            tasks=[_task(percent=100, done=True)],
            gate=None,
            drift=0,
        )
        result = kata_statusline.render_statusline(vm)
        parts = result.split(" │ ")
        bar_pct_segment = parts[2]
        bar_part = bar_pct_segment.split()[0]
        assert bar_part == "▰" * 8

    def test_mean_pct_two_tasks(self):
        """mean of 50+100 = 75, so bar should be round(75/100*8) = 6 filled."""
        vm = self._active_vm()
        result = kata_statusline.render_statusline(vm)
        parts = result.split(" │ ")
        bar_pct_segment = parts[2]
        tokens = bar_pct_segment.split()
        bar_part = tokens[0]
        pct_str = tokens[1]  # "75%"
        assert pct_str == "75%"
        # filled = round(75/100*8) = round(6.0) = 6
        assert bar_part == "▰" * 6 + "▱" * 2

    def test_done_total_tasks(self):
        vm = self._active_vm()
        result = kata_statusline.render_statusline(vm)
        assert " │ 1/2 tasks │ " in result

    def test_gate_present(self):
        vm = self._active_vm()
        result = kata_statusline.render_statusline(vm)
        assert " │ gate ok │ " in result

    def test_gate_absent_becomes_dash(self):
        vm = _vm(
            waiting=False,
            phase="EXECUTE",
            tasks=[_task(50, False)],
            gate=None,
            drift=0,
        )
        result = kata_statusline.render_statusline(vm)
        assert " │ gate – │ " in result

    def test_drift_appears(self):
        vm = self._active_vm()
        result = kata_statusline.render_statusline(vm)
        assert result.endswith("drift 2")

    def test_drift_zero(self):
        vm = _vm(
            waiting=False,
            phase="EXECUTE",
            tasks=[_task(50, False)],
            gate=None,
            drift=0,
        )
        result = kata_statusline.render_statusline(vm)
        assert result.endswith("drift 0")

    def test_zero_tasks_pct_zero(self):
        vm = _vm(waiting=False, phase="EXECUTE", tasks=[], gate=None, drift=0)
        result = kata_statusline.render_statusline(vm)
        # 0 tasks → pct=0, done/total = 0/0
        assert "0%" in result
        assert "0/0 tasks" in result

    def test_separator_is_u2502(self):
        """Separator must be U+2502 BOX DRAWINGS LIGHT VERTICAL."""
        vm = self._active_vm()
        result = kata_statusline.render_statusline(vm)
        assert "│" in result

    def test_evaluate_phase(self):
        vm = _vm(
            waiting=False,
            phase="EVALUATE",
            tasks=[_task(100, True)],
            gate="pass",
            drift=0,
        )
        result = kata_statusline.render_statusline(vm)
        assert " │ EVALUATE │ " in result


# ---------------------------------------------------------------------------
# build_statusline — integration over a real temp .kata dir
# ---------------------------------------------------------------------------


class TestBuildStatusline:
    def _make_kata_dir(self, tmp_path: Path) -> Path:
        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()
        board_text = (
            "2026-06-21T10:00:00Z | agent-1 | START | task-a | starting\n"
            "2026-06-21T10:01:00Z | agent-1 | PROGRESS | task-a | 1/2 coding\n"
        )
        (kata_dir / "board.md").write_text(board_text, encoding="utf-8")
        state = {
            "tasks": {"task-a": "in-progress", "task-b": "done"},
            "gate": None,
            "driftLedger": {"unauthorizedDeviations": 1, "escalations": 0},
            "plan": "test-plan",
        }
        (kata_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return kata_dir

    def test_returns_string(self, tmp_path: Path):
        kata_dir = self._make_kata_dir(tmp_path)
        result = kata_statusline.build_statusline(kata_dir)
        assert isinstance(result, str)

    def test_contains_harness_header(self, tmp_path: Path):
        kata_dir = self._make_kata_dir(tmp_path)
        result = kata_statusline.build_statusline(kata_dir)
        assert "KATAHARNESS 改善型" in result

    def test_missing_board_still_works(self, tmp_path: Path):
        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()
        state = {"tasks": {"task-a": "done"}}
        (kata_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        result = kata_statusline.build_statusline(kata_dir)
        assert "KATAHARNESS 改善型" in result

    def test_missing_state_returns_waiting_or_idle(self, tmp_path: Path):
        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()
        (kata_dir / "board.md").write_text("", encoding="utf-8")
        result = kata_statusline.build_statusline(kata_dir)
        # No state + empty board → waiting
        assert result == "KATAHARNESS 改善型 │ ⏳ idle — no active run"

    def test_missing_both_returns_waiting(self, tmp_path: Path):
        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()
        result = kata_statusline.build_statusline(kata_dir)
        assert result == "KATAHARNESS 改善型 │ ⏳ idle — no active run"

    def test_bad_state_json_treated_as_absent(self, tmp_path: Path):
        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()
        (kata_dir / "state.json").write_text("NOT JSON {{{", encoding="utf-8")
        result = kata_statusline.build_statusline(kata_dir)
        # bad JSON → state=None → waiting (with empty board)
        assert "KATAHARNESS 改善型" in result


# ---------------------------------------------------------------------------
# build_statusline — _safe_path / ..  traversal guard
# ---------------------------------------------------------------------------


class TestSafePath:
    def test_dotdot_in_path_raises(self, tmp_path: Path):
        evil_path = tmp_path / ".." / "evil"
        with pytest.raises(ValueError):
            kata_statusline.build_statusline(evil_path)

    def test_dotdot_in_string_path_raises(self):
        with pytest.raises(ValueError):
            kata_statusline.build_statusline(Path("../etc/passwd"))

    def test_double_dotdot_raises(self, tmp_path: Path):
        evil = tmp_path / ".." / ".." / "etc"
        with pytest.raises(ValueError):
            kata_statusline.build_statusline(evil)


# ---------------------------------------------------------------------------
# statusline_from_event — the Claude adapter entry point
# ---------------------------------------------------------------------------


def _deep_nonkata(tmp_path: Path, depth: int = 12) -> Path:
    """Return a cwd nested *depth* empty levels below tmp_path.

    U3 adopts the bounded upward walk (kata_scope.find_kata_root, cap _SCOPE_WALK_CAP = 10),
    so a "no evidence" assertion must confine the walk to a subtree we KNOW is empty — otherwise
    a stray ``.kata``/``kata.config`` in a real ancestor of tmp_path could flip the result.
    Nesting >= the walk cap keeps all probed dirs inside this empty subtree (mirrors the
    test_statusline_chain fixture-hermeticity note)."""
    d = tmp_path
    for i in range(depth):
        d = d / f"d{i}"
    d.mkdir(parents=True)
    return d


class TestStatuslineFromEvent:
    def _make_kata_dir(self, tmp_path: Path) -> Path:
        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()
        (kata_dir / "board.md").write_text("", encoding="utf-8")
        state = {"tasks": {"t1": "in-progress"}}
        (kata_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return kata_dir

    # --- missing cwd ---

    def test_no_cwd_returns_empty(self):
        payload = json.dumps({"model": "sonnet"})
        result = kata_statusline.statusline_from_event(payload)
        assert result == ""

    def test_empty_cwd_returns_empty(self):
        payload = json.dumps({"cwd": ""})
        result = kata_statusline.statusline_from_event(payload)
        assert result == ""

    def test_malformed_json_returns_empty(self):
        result = kata_statusline.statusline_from_event("NOT JSON }{")
        assert result == ""

    def test_null_json_returns_empty(self):
        result = kata_statusline.statusline_from_event("null")
        assert result == ""

    def test_empty_string_returns_empty(self):
        result = kata_statusline.statusline_from_event("")
        assert result == ""

    # --- no evidence anywhere within the walk cap ---

    def test_no_evidence_within_walk_cap_returns_empty(self, tmp_path: Path):
        # U3: a bare cwd with NO .kata/kata.config at or above it (within the bounded walk)
        # renders nothing. Nested deep so the walk cannot escape into real-filesystem evidence.
        cwd = _deep_nonkata(tmp_path)
        payload = json.dumps({"cwd": str(cwd)})
        result = kata_statusline.statusline_from_event(payload)
        assert result == ""

    # --- .kata present ---

    def test_kata_present_returns_statusline(self, tmp_path: Path):
        self._make_kata_dir(tmp_path)
        payload = json.dumps({"cwd": str(tmp_path)})
        result = kata_statusline.statusline_from_event(payload)
        assert "KATAHARNESS 改善型" in result
        assert "改善型" in result

    def test_kata_present_via_workspace_current_dir(self, tmp_path: Path):
        """Fallback: cwd from workspace.current_dir when cwd key absent."""
        self._make_kata_dir(tmp_path)
        payload = json.dumps({"workspace": {"current_dir": str(tmp_path)}})
        result = kata_statusline.statusline_from_event(payload)
        assert "KATAHARNESS 改善型" in result

    def test_cwd_takes_precedence_over_workspace(self, tmp_path: Path):
        """cwd should win over workspace.current_dir."""
        self._make_kata_dir(tmp_path)
        payload = json.dumps({
            "cwd": str(tmp_path),
            "workspace": {"current_dir": "/nonexistent/path/xyz"},
        })
        result = kata_statusline.statusline_from_event(payload)
        assert "KATAHARNESS 改善型" in result

    def test_exception_in_build_returns_empty(self, monkeypatch):
        """Any exception inside the body must return "" (fail-soft)."""

        def _exploding_build(kata_dir):
            raise RuntimeError("simulated failure")

        monkeypatch.setattr(kata_statusline, "build_statusline", _exploding_build)

        import os
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            kata_dir = Path(d) / ".kata"
            kata_dir.mkdir()
            payload = json.dumps({"cwd": d})
            result = kata_statusline.statusline_from_event(payload)
        assert result == ""

    def test_valueerror_in_build_returns_empty(self, monkeypatch):
        """ValueError (raised by the shared _safe_path .. guard) must be
        caught and degrade to "" — fail-soft aligns with fail-secure so a
        traversal cwd never crashes Claude's statusline."""

        def _raising_build(kata_dir):
            raise ValueError("kata_statusline: refusing path with '..' traversal")

        monkeypatch.setattr(kata_statusline, "build_statusline", _raising_build)

        import tempfile
        with tempfile.TemporaryDirectory() as d:
            kata_dir = Path(d) / ".kata"
            kata_dir.mkdir()
            payload = json.dumps({"cwd": d})
            result = kata_statusline.statusline_from_event(payload)
        assert result == ""

    def test_systemexit_in_build_returns_empty(self, monkeypatch):
        """SystemExit in build_statusline must also degrade to "" — the handler
        retains (Exception, SystemExit) for defense-in-depth."""

        def _exiting_build(kata_dir):
            raise SystemExit("unexpected exit")

        monkeypatch.setattr(kata_statusline, "build_statusline", _exiting_build)

        import tempfile
        with tempfile.TemporaryDirectory() as d:
            kata_dir = Path(d) / ".kata"
            kata_dir.mkdir()
            payload = json.dumps({"cwd": d})
            result = kata_statusline.statusline_from_event(payload)
        assert result == ""

    # --- U3 behavior deltas: walk semantics (subdir render + kata.config-only idle) ---

    def test_subdir_of_kata_repo_renders_same_as_root(self, tmp_path: Path):
        """U3 delta 1: a subdirectory of a kata repo now renders — byte-identical to the
        line rendered from the repo root (the bounded walk finds the ancestor's .kata)."""
        repo = tmp_path / "repo"
        repo.mkdir()
        self._make_kata_dir(repo)
        subdir = repo / "src" / "pkg" / "mod"
        subdir.mkdir(parents=True)

        root_line = kata_statusline.statusline_from_event(
            json.dumps({"cwd": str(repo)})
        )
        sub_line = kata_statusline.statusline_from_event(
            json.dumps({"cwd": str(subdir)})
        )
        assert "KATAHARNESS 改善型" in root_line  # the root cwd renders (baseline)
        assert sub_line == root_line  # subdir renders the SAME line

    def test_kata_config_only_repo_renders_idle_line(self, tmp_path: Path):
        """U3 delta 2: a kata.config-only repo (no .kata/board.md + state.json) now renders
        the FROZEN idle line — coherent 'configured, no active run'."""
        repo = tmp_path / "repo"
        repo.mkdir()
        (repo / "kata.config").write_text("{}", encoding="utf-8")  # config, but no .kata/
        result = kata_statusline.statusline_from_event(
            json.dumps({"cwd": str(repo)})
        )
        assert result == "KATAHARNESS 改善型 │ ⏳ idle — no active run"

    def test_resolve_start_cwd_wins_through_event(self, tmp_path: Path):
        """U3: resolve_start's 'cwd wins over workspace.current_dir' convention holds end-to-end.
        cwd → an ACTIVE kata repo, workspace → an IDLE kata repo; the ACTIVE line renders."""
        active = tmp_path / "active"
        active.mkdir()
        self._make_kata_dir(active)  # board + in-progress state ⇒ active line
        idle = tmp_path / "idle"
        idle.mkdir()
        (idle / "kata.config").write_text("{}", encoding="utf-8")  # ⇒ idle line

        payload = json.dumps({
            "cwd": str(active),
            "workspace": {"current_dir": str(idle)},
        })
        result = kata_statusline.statusline_from_event(payload)

        expected_active = kata_statusline.build_statusline(active / ".kata")
        expected_idle = kata_statusline.build_statusline(idle / ".kata")
        assert result == expected_active  # cwd (active) won
        assert result != expected_idle  # NOT the workspace (idle) repo
        assert result != "KATAHARNESS 改善型 │ ⏳ idle — no active run"


# ---------------------------------------------------------------------------
# write_bridge — kata superset context-usage bridge writer (CA-L1 / CA-L2)
# ---------------------------------------------------------------------------


class TestWriteBridge:
    _SID = "abc123-session-DEF"

    _NO_SID = object()

    def _payload(self, *, remaining=30, total=200000, session_id=_NO_SID):
        cw = {}
        if remaining is not None:
            cw["remaining_percentage"] = remaining
        if total is not None:
            cw["total_tokens"] = total
        sid = self._SID if session_id is self._NO_SID else session_id
        return {"session_id": sid, "context_window": cw}

    # --- schema round-trip: all five fields, numeric types ---

    def test_round_trip_all_five_fields(self, tmp_path: Path):
        result = kata_statusline.write_bridge(tmp_path, self._payload())
        assert result is not None
        assert result == tmp_path / f"kata-ctx-{self._SID}.json"
        data = json.loads(result.read_text(encoding="utf-8"))
        assert set(data) == {
            "session_id",
            "remaining_percentage",
            "used_pct",
            "timestamp",
            "total_tokens",
        }
        assert data["session_id"] == self._SID
        assert data["remaining_percentage"] == 30
        assert data["used_pct"] == 70
        assert isinstance(data["timestamp"], int)
        assert isinstance(data["total_tokens"], int)
        assert data["total_tokens"] == 200000

    def test_used_pct_is_100_minus_remaining_float(self, tmp_path: Path):
        result = kata_statusline.write_bridge(
            tmp_path, self._payload(remaining=30.5)
        )
        data = json.loads(result.read_text(encoding="utf-8"))
        assert data["remaining_percentage"] == 30.5
        assert data["used_pct"] == 69.5

    def test_round_trips_through_kata_gauge_full(self, tmp_path: Path):
        """The superset file parses as a FULL-mode gauge in kata_gauge.read_bridge."""
        import kata_gauge  # noqa: E402

        result = kata_statusline.write_bridge(tmp_path, self._payload())
        gauge = kata_gauge.read_bridge(
            result, now_utc=datetime.now(UTC)
        )
        assert gauge["mode"] == "full"
        assert gauge["total_tokens"] == 200000
        assert gauge["used_pct"] == 70
        assert gauge["stale"] is False

    # --- total_tokens absent ⇒ percentage-only degrade (CA-L2) ---

    def test_absent_total_tokens_writes_null_percentage_only(self, tmp_path: Path):
        import kata_gauge  # noqa: E402

        result = kata_statusline.write_bridge(
            tmp_path, self._payload(total=None)
        )
        assert result is not None
        data = json.loads(result.read_text(encoding="utf-8"))
        assert data["total_tokens"] is None
        gauge = kata_gauge.read_bridge(
            result, now_utc=datetime.now(UTC)
        )
        assert gauge["mode"] == "percentage-only"

    # --- atomicity: os.replace is the mechanism (mutation proof) ---

    def test_atomic_rename_via_os_replace(self, tmp_path: Path, monkeypatch):
        calls = []
        real_replace = os.replace

        def _recording_replace(src, dst):
            calls.append((str(src), str(dst)))
            return real_replace(src, dst)

        monkeypatch.setattr(kata_statusline.os, "replace", _recording_replace)
        result = kata_statusline.write_bridge(tmp_path, self._payload())

        assert result is not None
        # os.replace was called exactly once, temp name != final name.
        assert len(calls) == 1
        src, dst = calls[0]
        assert src != dst
        assert dst == str(tmp_path / f"kata-ctx-{self._SID}.json")
        # The temp source is a sibling in the same dir, distinct from the final.
        assert Path(src).parent == tmp_path
        assert Path(src).name != f"kata-ctx-{self._SID}.json"

    def test_no_partial_final_file_left_by_temp(self, tmp_path: Path):
        """Only the final name (never a *.tmp) survives a successful write."""
        kata_statusline.write_bridge(tmp_path, self._payload())
        names = sorted(p.name for p in tmp_path.iterdir())
        assert names == [f"kata-ctx-{self._SID}.json"]

    # --- absent-field no-write guards (mutation proof) ---

    def test_absent_context_window_writes_nothing(self, tmp_path: Path):
        result = kata_statusline.write_bridge(
            tmp_path, {"session_id": self._SID}
        )
        assert result is None
        assert list(tmp_path.iterdir()) == []

    def test_absent_session_id_writes_nothing(self, tmp_path: Path):
        result = kata_statusline.write_bridge(
            tmp_path, {"context_window": {"remaining_percentage": 30}}
        )
        assert result is None
        assert list(tmp_path.iterdir()) == []

    def test_empty_session_id_writes_nothing(self, tmp_path: Path):
        result = kata_statusline.write_bridge(
            tmp_path, self._payload(session_id="")
        )
        assert result is None
        assert list(tmp_path.iterdir()) == []

    def test_absent_remaining_percentage_writes_nothing(self, tmp_path: Path):
        result = kata_statusline.write_bridge(
            tmp_path, self._payload(remaining=None)
        )
        assert result is None
        assert list(tmp_path.iterdir()) == []

    def test_non_numeric_remaining_percentage_writes_nothing(self, tmp_path: Path):
        result = kata_statusline.write_bridge(
            tmp_path, {"session_id": self._SID,
                       "context_window": {"remaining_percentage": "lots"}}
        )
        assert result is None
        assert list(tmp_path.iterdir()) == []

    def test_bool_remaining_percentage_rejected(self, tmp_path: Path):
        # bool subclasses int — must be rejected (mirrors kata_gauge._is_number).
        result = kata_statusline.write_bridge(
            tmp_path, {"session_id": self._SID,
                       "context_window": {"remaining_percentage": True}}
        )
        assert result is None

    def test_non_dict_payload_returns_none(self, tmp_path: Path):
        assert kata_statusline.write_bridge(tmp_path, "not a dict") is None
        assert kata_statusline.write_bridge(tmp_path, None) is None

    # --- session_id filename-safety guard (CWE-22/CWE-23) ---

    @pytest.mark.parametrize(
        "evil",
        ["../evil", "..", "a/b", "a\\b", "with space", "a/../b", "id;rm"],
    )
    def test_unsafe_session_id_writes_nothing(self, tmp_path: Path, evil):
        result = kata_statusline.write_bridge(
            tmp_path, self._payload(session_id=evil)
        )
        assert result is None
        # nothing (not even a temp) was created under tmp_path
        assert list(tmp_path.iterdir()) == []

    # --- fail-soft: a write OSError never raises ---

    def test_write_oserror_returns_none(self, tmp_path: Path, monkeypatch):
        def _boom(src, dst):
            raise OSError("simulated rename failure")

        monkeypatch.setattr(kata_statusline.os, "replace", _boom)
        result = kata_statusline.write_bridge(tmp_path, self._payload())
        assert result is None
        # the orphan temp is cleaned up — no *.tmp left behind
        assert list(tmp_path.iterdir()) == []


# ---------------------------------------------------------------------------
# statusline_from_event × write_bridge — bridge written before render path
# ---------------------------------------------------------------------------


class TestStatuslineFromEventBridge:
    _SID = "sess-XYZ-001"

    def _make_kata_dir(self, tmp_path: Path) -> Path:
        kata_dir = tmp_path / ".kata"
        kata_dir.mkdir()
        (kata_dir / "board.md").write_text("", encoding="utf-8")
        state = {"tasks": {"t1": "in-progress"}}
        (kata_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        return kata_dir

    def _payload(self, cwd):
        return json.dumps({
            "cwd": str(cwd),
            "session_id": self._SID,
            "context_window": {"remaining_percentage": 40, "total_tokens": 200000},
        })

    def test_render_byte_identical_and_bridge_written(self, tmp_path, monkeypatch):
        """The rendered line is byte-identical to build_statusline AND the kata
        bridge landed in %TEMP% (write happens before the render path)."""
        cwd = tmp_path / "repo"
        cwd.mkdir()
        kata_dir = self._make_kata_dir(cwd)
        bridge_dir = tmp_path / "temp"
        bridge_dir.mkdir()
        monkeypatch.setattr(
            kata_statusline.tempfile, "gettempdir", lambda: str(bridge_dir)
        )

        expected = kata_statusline.build_statusline(kata_dir)
        result = kata_statusline.statusline_from_event(self._payload(cwd))

        assert result == expected  # byte-identical render (unchanged behavior)
        assert (bridge_dir / f"kata-ctx-{self._SID}.json").exists()

    def test_bridge_written_even_for_non_kata_cwd(self, tmp_path, monkeypatch):
        """A non-kata cwd still writes the gauge (bridge must not depend on .kata)."""
        # Nested deep (U3): the bounded walk stays inside this empty subtree, so the "no .kata"
        # assertion can't be flipped by real-filesystem evidence above tmp_path.
        cwd = _deep_nonkata(tmp_path)  # no .kata anywhere within the walk cap
        bridge_dir = tmp_path / "temp"
        bridge_dir.mkdir()
        monkeypatch.setattr(
            kata_statusline.tempfile, "gettempdir", lambda: str(bridge_dir)
        )

        result = kata_statusline.statusline_from_event(self._payload(cwd))

        assert result == ""  # no .kata ⇒ blank line (unchanged)
        assert (bridge_dir / f"kata-ctx-{self._SID}.json").exists()

    def test_write_oserror_does_not_break_rendered_line(self, tmp_path, monkeypatch):
        """A bridge write OSError must not blank/crash the rendered statusline."""
        cwd = tmp_path / "repo"
        cwd.mkdir()
        kata_dir = self._make_kata_dir(cwd)
        bridge_dir = tmp_path / "temp"
        bridge_dir.mkdir()
        monkeypatch.setattr(
            kata_statusline.tempfile, "gettempdir", lambda: str(bridge_dir)
        )

        def _boom(src, dst):
            raise OSError("rename failed")

        monkeypatch.setattr(kata_statusline.os, "replace", _boom)

        expected = kata_statusline.build_statusline(kata_dir)
        result = kata_statusline.statusline_from_event(self._payload(cwd))

        assert result == expected  # render intact despite the write failure
        assert not (bridge_dir / f"kata-ctx-{self._SID}.json").exists()

    def test_no_session_id_no_bridge_render_unchanged(self, tmp_path, monkeypatch):
        """A statusline event without session_id writes no bridge, renders normally."""
        cwd = tmp_path / "repo"
        cwd.mkdir()
        kata_dir = self._make_kata_dir(cwd)
        bridge_dir = tmp_path / "temp"
        bridge_dir.mkdir()
        monkeypatch.setattr(
            kata_statusline.tempfile, "gettempdir", lambda: str(bridge_dir)
        )

        expected = kata_statusline.build_statusline(kata_dir)
        payload = json.dumps({"cwd": str(cwd)})  # no session_id/context_window
        result = kata_statusline.statusline_from_event(payload)

        assert result == expected
        assert list(bridge_dir.iterdir()) == []
