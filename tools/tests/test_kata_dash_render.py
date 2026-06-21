"""test_kata_dash_render.py — TDD tests for DASH-render pure helpers + build_frame.

Tests import ONLY from kata_dash (render helpers + build_frame).
kata_dash_model is NOT imported here; build_frame is tested with SimpleNamespace stand-ins.
"""

import types

import pytest

# ---------------------------------------------------------------------------
# Import the module under test
# kata_dash must be importable without kata_dash_model (lazy import in main()).
# ---------------------------------------------------------------------------
import kata_dash


# ---------------------------------------------------------------------------
# Helpers: render_bar
# ---------------------------------------------------------------------------

class TestRenderBar:
    """render_bar(percent, width=20) -> str of ▰ and ▱ chars."""

    def test_zero_percent_all_empty(self):
        bar = kata_dash.render_bar(0, width=20)
        assert bar.count("▰") == 0
        assert bar.count("▱") == 20
        assert len(bar) == 20

    def test_hundred_percent_all_filled(self):
        bar = kata_dash.render_bar(100, width=20)
        assert bar.count("▰") == 20
        assert bar.count("▱") == 0
        assert len(bar) == 20

    def test_fifty_percent_half_filled(self):
        bar = kata_dash.render_bar(50, width=20)
        filled = bar.count("▰")
        empty = bar.count("▱")
        assert filled == 10
        assert empty == 10
        assert len(bar) == 20

    def test_custom_width(self):
        bar = kata_dash.render_bar(25, width=8)
        # round(25/100*8) = round(2.0) = 2
        assert bar.count("▰") == 2
        assert bar.count("▱") == 6
        assert len(bar) == 8

    def test_rounding_at_72_percent(self):
        # round(72/100*20) = round(14.4) = 14
        bar = kata_dash.render_bar(72, width=20)
        assert bar.count("▰") == 14
        assert bar.count("▱") == 6

    def test_only_bar_chars(self):
        bar = kata_dash.render_bar(50, width=20)
        assert all(c in ("▰", "▱") for c in bar)


# ---------------------------------------------------------------------------
# Helpers: spinner_frame
# ---------------------------------------------------------------------------

class TestSpinnerFrame:
    """spinner_frame(tick) -> one of ⠹⠼⠧⠿ cycling by tick%4."""

    FRAMES = ("⠹", "⠼", "⠧", "⠿")

    def test_tick_0(self):
        assert kata_dash.spinner_frame(0) == self.FRAMES[0]

    def test_tick_1(self):
        assert kata_dash.spinner_frame(1) == self.FRAMES[1]

    def test_tick_2(self):
        assert kata_dash.spinner_frame(2) == self.FRAMES[2]

    def test_tick_3(self):
        assert kata_dash.spinner_frame(3) == self.FRAMES[3]

    def test_tick_4_wraps(self):
        assert kata_dash.spinner_frame(4) == self.FRAMES[0]

    def test_tick_5_wraps(self):
        assert kata_dash.spinner_frame(5) == self.FRAMES[1]

    def test_cycles_through_all_four(self):
        seen = {kata_dash.spinner_frame(t) for t in range(4)}
        assert seen == set(self.FRAMES)


# ---------------------------------------------------------------------------
# Helpers: render_row_text
# ---------------------------------------------------------------------------

def _task(*, id="T1", label="my task", status="in-progress",
          percent=50, active=False, blocked=False, done=False):
    """Build a duck-typed TaskRow stand-in."""
    return types.SimpleNamespace(
        id=id, label=label, status=status,
        percent=percent, active=active, blocked=blocked, done=done,
    )


class TestRenderRowText:
    """render_row_text(task, tick) -> str with marker, label, bar, pct, glyph, status."""

    def test_done_task_shows_checkmark(self):
        task = _task(label="done task", percent=100, done=True)
        text = kata_dash.render_row_text(task, tick=0)
        assert "✓" in text
        assert "done task" in text
        assert "100%" in text

    def test_blocked_task_shows_x(self):
        task = _task(label="blocked task", percent=50, blocked=True)
        text = kata_dash.render_row_text(task, tick=0)
        assert "✗" in text
        assert "blocked task" in text
        assert "50%" in text

    def test_active_task_shows_spinner(self):
        task = _task(label="active task", percent=72, active=True)
        spinner_chars = {"⠹", "⠼", "⠧", "⠿"}
        text = kata_dash.render_row_text(task, tick=0)
        assert any(c in text for c in spinner_chars)
        assert "active task" in text
        assert "72%" in text

    def test_active_task_spinner_varies_by_tick(self):
        task = _task(label="spinning", percent=50, active=True)
        texts = [kata_dash.render_row_text(task, tick=t) for t in range(4)]
        # Each tick should produce a valid spinner char; not all necessarily same
        spinner_chars = {"⠹", "⠼", "⠧", "⠿"}
        for text in texts:
            assert any(c in text for c in spinner_chars)

    def test_idle_task_shows_dot(self):
        task = _task(label="idle task", percent=5, active=False, blocked=False, done=False)
        text = kata_dash.render_row_text(task, tick=0)
        assert "·" in text
        assert "idle task" in text
        assert "5%" in text

    def test_row_contains_marker(self):
        task = _task(label="marked", percent=50)
        text = kata_dash.render_row_text(task, tick=0)
        assert "▸" in text

    def test_row_contains_label(self):
        task = _task(label="special-label-xyz", percent=10)
        text = kata_dash.render_row_text(task, tick=0)
        assert "special-label-xyz" in text

    def test_row_contains_percent_string(self):
        task = _task(label="pct test", percent=93)
        text = kata_dash.render_row_text(task, tick=0)
        assert "93%" in text

    def test_done_takes_priority_over_blocked(self):
        # done=True + blocked=True → checkmark (done wins)
        task = _task(label="both", percent=100, done=True, blocked=True)
        text = kata_dash.render_row_text(task, tick=0)
        assert "✓" in text

    def test_bar_chars_present_in_row(self):
        task = _task(label="bar row", percent=50)
        text = kata_dash.render_row_text(task, tick=0)
        assert "▰" in text or "▱" in text


# ---------------------------------------------------------------------------
# Helpers: render_ribbon
# ---------------------------------------------------------------------------

RIBBON_PHASES = ["GRILL", "FREEZE", "EXECUTE", "EVALUATE", "HANDOFF", "IMPROVE"]


class TestRenderRibbon:
    """render_ribbon(phase) -> str with all 6 phases, active one marked."""

    def test_all_phases_present(self):
        ribbon = kata_dash.render_ribbon("EXECUTE")
        for phase in RIBBON_PHASES:
            assert phase in ribbon

    def test_active_phase_highlighted(self):
        # Active phase must be visually distinct — we accept ◉EXECUTE or [EXECUTE]
        ribbon = kata_dash.render_ribbon("EXECUTE")
        # At minimum the active phase word is present (already tested above),
        # and the ribbon doesn't highlight a non-active phase the same way.
        assert "EXECUTE" in ribbon

    @pytest.mark.parametrize("phase", RIBBON_PHASES)
    def test_each_phase_can_be_highlighted(self, phase):
        ribbon = kata_dash.render_ribbon(phase)
        assert phase in ribbon
        # The highlighted phase must appear distinctly — check a marker char is nearby.
        # Acceptable: ◉PHASE, [PHASE], or similar — look for ◉ or [ adjacent to the phase.
        idx = ribbon.index(phase)
        window = ribbon[max(0, idx - 2):idx + len(phase) + 2]
        marker_found = ("◉" in window or "[" in window)
        assert marker_found, (
            f"Phase {phase!r} not visibly highlighted in ribbon: {ribbon!r}"
        )

    def test_ribbon_contains_separator(self):
        ribbon = kata_dash.render_ribbon("GRILL")
        assert "▸" in ribbon

    def test_non_active_phases_not_marked_same_as_active(self):
        # When EXECUTE is active, GRILL must not also be bracketed/◉'d
        ribbon = kata_dash.render_ribbon("EXECUTE")
        # Find GRILL and check no ◉ immediately precedes it
        idx = ribbon.index("GRILL")
        before_grill = ribbon[max(0, idx - 2):idx]
        assert "◉" not in before_grill
        assert "[" not in before_grill


# ---------------------------------------------------------------------------
# build_frame
# ---------------------------------------------------------------------------

def _task_row(*, id="T1", label="Task One", status="in-progress",
              percent=50, active=True, blocked=False, done=False):
    return types.SimpleNamespace(
        id=id, label=label, status=status,
        percent=percent, active=active, blocked=blocked, done=done,
    )


def _normal_view_model():
    return types.SimpleNamespace(
        spec="test-spec",
        wave="1/2",
        phase="EXECUTE",
        gate="green",
        tasks=[
            _task_row(id="T1", label="Alpha", status="in-progress",
                      percent=72, active=True, blocked=False, done=False),
            _task_row(id="T2", label="Beta", status="done",
                      percent=100, active=False, blocked=False, done=True),
        ],
        driftEscalations=(0, 0),
        events=["2026-06-21T10:00Z | agent-A | CLAIM | T1 | starting"],
        waiting=False,
        updatedUtc="2026-06-21T10:01Z",
    )


def _waiting_view_model():
    return types.SimpleNamespace(
        spec=None,
        wave=None,
        phase="EXECUTE",
        gate=None,
        tasks=[],
        driftEscalations=(0, 0),
        events=[],
        waiting=True,
        updatedUtc=None,
    )


class TestBuildFrame:
    """build_frame(view_model, tick) -> rich RenderableType."""

    def test_normal_view_model_returns_renderable(self):
        vm = _normal_view_model()
        result = kata_dash.build_frame(vm, tick=0)
        # Must be a rich renderable — Panel, Text, or object with __rich_console__
        assert result is not None

    def test_waiting_view_model_returns_renderable(self):
        vm = _waiting_view_model()
        result = kata_dash.build_frame(vm, tick=0)
        assert result is not None

    def test_normal_does_not_raise(self):
        vm = _normal_view_model()
        try:
            kata_dash.build_frame(vm, tick=5)
        except Exception as exc:
            pytest.fail(f"build_frame raised on normal ViewModel: {exc}")

    def test_waiting_does_not_raise(self):
        vm = _waiting_view_model()
        try:
            kata_dash.build_frame(vm, tick=0)
        except Exception as exc:
            pytest.fail(f"build_frame raised on waiting ViewModel: {exc}")

    def test_both_tick_values(self):
        vm = _normal_view_model()
        for tick in [0, 1, 2, 3, 10, 99]:
            result = kata_dash.build_frame(vm, tick=tick)
            assert result is not None

    def test_normal_is_panel(self):
        from rich.panel import Panel
        vm = _normal_view_model()
        result = kata_dash.build_frame(vm, tick=0)
        assert isinstance(result, Panel)

    def test_waiting_is_panel(self):
        from rich.panel import Panel
        vm = _waiting_view_model()
        result = kata_dash.build_frame(vm, tick=0)
        assert isinstance(result, Panel)

    def test_view_model_with_no_tasks(self):
        vm = _normal_view_model()
        vm.tasks = []
        result = kata_dash.build_frame(vm, tick=0)
        assert result is not None

    def test_view_model_with_none_spec(self):
        vm = _normal_view_model()
        vm.spec = None
        result = kata_dash.build_frame(vm, tick=0)
        assert result is not None

    def test_view_model_with_none_wave(self):
        vm = _normal_view_model()
        vm.wave = None
        result = kata_dash.build_frame(vm, tick=0)
        assert result is not None


# ---------------------------------------------------------------------------
# S1b: new title + progressLabel in row text
# ---------------------------------------------------------------------------


def _task_with_progress_label(label="T1", progressLabel="writing tests",
                               percent=60, active=True):
    """Duck-typed TaskRow with progressLabel field."""
    return types.SimpleNamespace(
        id=label, label=label, status="in-progress",
        percent=percent, active=active, blocked=False, done=False,
        progressLabel=progressLabel,
    )


def _task_without_progress_label(label="T2", percent=50, active=True):
    """Duck-typed TaskRow WITHOUT progressLabel (no attribute) to test fallback."""
    return types.SimpleNamespace(
        id=label, label=label, status="in-progress",
        percent=percent, active=active, blocked=False, done=False,
        progressLabel="",
    )


class TestNewTitle:
    """build_frame must use the new 改善型 header text."""

    def test_build_frame_title_contains_kaizen_no_kata(self):
        """build_frame output panel title must contain '改善型'."""
        from rich.console import Console
        from io import StringIO

        vm = _normal_view_model()
        frame = kata_dash.build_frame(vm, tick=0)
        # Render to string and check for the new title
        buf = StringIO()
        console = Console(file=buf, width=120, legacy_windows=False, force_terminal=True)
        console.print(frame)
        output = buf.getvalue()
        assert "改善型" in output, f"Expected '改善型' in output but got: {output[:200]}"

    def test_waiting_panel_title_contains_kaizen_no_kata(self):
        """waiting Panel must also use '改善型' title."""
        from rich.console import Console
        from io import StringIO

        vm = _waiting_view_model()
        frame = kata_dash.build_frame(vm, tick=0)
        buf = StringIO()
        console = Console(file=buf, width=120, legacy_windows=False, force_terminal=True)
        console.print(frame)
        output = buf.getvalue()
        assert "改善型" in output, f"Expected '改善型' in waiting output but got: {output[:200]}"

    def test_build_frame_does_not_contain_old_motif(self):
        """build_frame must NOT contain the old '道' or the torii '⛩' (removed per operator)."""
        from rich.console import Console
        from io import StringIO

        vm = _normal_view_model()
        frame = kata_dash.build_frame(vm, tick=0)
        buf = StringIO()
        console = Console(file=buf, width=120, legacy_windows=False, force_terminal=True)
        console.print(frame)
        output = buf.getvalue()
        assert "KATAHARNESS" in output
        assert "道" not in output, "old '道' motif must be gone"
        assert "⛩" not in output, "torii removed per operator — title is just 改善型"


class TestProgressLabelInRow:
    """render_row_text must include progressLabel when non-empty."""

    def test_render_row_text_shows_progress_label(self):
        """render_row_text must include progressLabel in output when set."""
        task = _task_with_progress_label(progressLabel="writing tests")
        text = kata_dash.render_row_text(task, tick=0)
        assert "writing tests" in text

    def test_render_row_text_empty_progress_label_not_appended(self):
        """render_row_text must not add extra text when progressLabel is empty."""
        task = _task_without_progress_label()
        text = kata_dash.render_row_text(task, tick=0)
        # Just check it renders normally and doesn't crash
        assert "▸" in text
        assert "T2" in text

    def test_render_row_text_progress_label_with_step_fraction(self):
        """progressLabel (just the label part, not the fraction) appears in row."""
        task = _task_with_progress_label(progressLabel="deploying containers", percent=80)
        text = kata_dash.render_row_text(task, tick=0)
        assert "deploying containers" in text

    def test_render_row_text_progress_label_missing_attr_does_not_crash(self):
        """render_row_text must not crash if task has no progressLabel attribute."""
        # Old-style task without progressLabel attribute
        task = types.SimpleNamespace(
            id="T1", label="old task", status="in-progress",
            percent=50, active=True, blocked=False, done=False,
        )
        try:
            text = kata_dash.render_row_text(task, tick=0)
        except Exception as exc:
            pytest.fail(f"render_row_text crashed without progressLabel attr: {exc}")
        assert "old task" in text

    def test_build_frame_shows_progress_label_in_task_row(self):
        """build_frame renders a task row containing the progressLabel text."""
        from rich.console import Console
        from io import StringIO

        vm = _normal_view_model()
        # Add a task with a progressLabel
        task_with_label = _task_with_progress_label(
            label="Alpha", progressLabel="running validators", percent=60
        )
        vm.tasks = [task_with_label]
        frame = kata_dash.build_frame(vm, tick=0)
        buf = StringIO()
        console = Console(file=buf, width=120, legacy_windows=False, force_terminal=True)
        console.print(frame)
        output = buf.getvalue()
        assert "running validators" in output
