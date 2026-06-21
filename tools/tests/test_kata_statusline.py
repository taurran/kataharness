"""test_kata_statusline.py — TDD tests for kata_statusline (S1.5a).

Tests follow the FROZEN format from PLAN-s1.5.md Task S1.5a.
All tests are hermetic (tmp_path only, no real .kata dirs).
"""

from __future__ import annotations

import json
import sys
import types
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
        with pytest.raises(SystemExit):
            kata_statusline.build_statusline(evil_path)

    def test_dotdot_in_string_path_raises(self):
        with pytest.raises(SystemExit):
            kata_statusline.build_statusline(Path("../etc/passwd"))

    def test_double_dotdot_raises(self, tmp_path: Path):
        evil = tmp_path / ".." / ".." / "etc"
        with pytest.raises(SystemExit):
            kata_statusline.build_statusline(evil)


# ---------------------------------------------------------------------------
# statusline_from_event — the Claude adapter entry point
# ---------------------------------------------------------------------------


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

    # --- .kata absent ---

    def test_kata_dir_absent_returns_empty(self, tmp_path: Path):
        # tmp_path exists but no .kata subdir
        payload = json.dumps({"cwd": str(tmp_path)})
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

        import tempfile, os
        with tempfile.TemporaryDirectory() as d:
            kata_dir = Path(d) / ".kata"
            kata_dir.mkdir()
            payload = json.dumps({"cwd": d})
            result = kata_statusline.statusline_from_event(payload)
        assert result == ""
