"""Tests for kata_banner.py — the loop-init readout."""

from __future__ import annotations

from kata_banner import BRAND, render_banner, render_validation_banner


def test_full_banner_has_brand_and_all_lines():
    out = render_banner(
        goal="harden the install path vs. path-traversal",
        run_shape="version-up", mode="Standard", grill="standard", delivery="one-shot",
        tasks=5, slices=3, gate="default-FAIL", drift=0,
    )
    lines = out.splitlines()
    assert BRAND in lines[0] and "executing" in lines[0]
    assert lines[0].startswith("━━") and lines[-1].startswith("━")
    body = "\n".join(lines)
    assert "run-shape" in body and "version-up" in body and "Standard" in body
    assert "goal" in body and "harden the install path" in body
    assert "plan" in body and "5 tasks" in body and "3 slices" in body and "gate default-FAIL" in body


def test_deterministic():
    kw = dict(goal="g", run_shape="batch", mode="Essential", tasks=2)
    assert render_banner(**kw) == render_banner(**kw)


def test_missing_plan_fields_omitted():
    # before a plan exists, no tasks/slices → no plan line, still renders
    out = render_banner(goal="just a goal", run_shape="individual")
    assert "goal        just a goal" in out
    assert "tasks" not in out  # no plan stats supplied → omitted (drift/gate also gone)


def test_run_line_omitted_when_no_run_fields():
    out = render_banner(goal="g")
    assert "run-shape" not in out
    assert "goal        g" in out


def test_blank_goal_placeholder():
    out = render_banner(goal="   ")
    assert "(goal pending)" in out


def test_compact_is_single_line_loopback():
    out = render_banner(goal="re-run the build", tasks=4, compact=True)
    assert "\n" not in out
    assert out.startswith("↻") and BRAND in out
    assert "loop-back" in out and "re-run the build" in out and "4 tasks" in out


def test_grill_label_rendered():
    out = render_banner(goal="g", grill="full")
    assert "grill full" in out


def test_no_color_by_default():
    out = render_banner(goal="g", run_shape="batch", tasks=2)
    assert "\x1b[" not in out  # no ANSI unless color=True


def test_color_emits_report_palette_ansi():
    out = render_banner(goal="g", run_shape="batch", tasks=2, color=True)
    assert "\x1b[" in out and out.rstrip().endswith("\x1b[0m")
    # the ochre brand-mark accent (#B5894B = 181,137,75) is present
    assert "38;2;181;137;75" in out


def test_color_compact():
    out = render_banner(goal="re-run", tasks=3, compact=True, color=True)
    assert "\x1b[" in out and "\n" not in out


# ── render_validation_banner ─────────────────────────────────────────────────

def test_validation_banner_contains_marker():
    """Marker text is present and banner is non-trivial — RED if string is changed or function stubbed."""
    out = render_validation_banner()
    assert "Running KataHarness validation loop" in out
    assert len(out) > len("Running KataHarness validation loop")


def test_validation_banner_structure():
    """Three-line banner: top rule (with BRAND), marker body, bottom rule."""
    out = render_validation_banner()
    lines = out.splitlines()
    assert len(lines) == 3
    assert lines[0].startswith("━━") and BRAND in lines[0]
    assert "Running KataHarness validation loop" in lines[1]
    assert lines[2].startswith("━")


def test_validation_banner_deterministic():
    """Two calls with the same args produce byte-identical output."""
    assert render_validation_banner() == render_validation_banner()
    assert render_validation_banner(color=False) == render_validation_banner(color=False)


def test_validation_banner_no_color_by_default():
    """No ANSI escape codes when color=False (the default)."""
    out = render_validation_banner()
    assert "\x1b[" not in out


def test_validation_banner_color_wraps_brand_in_ochre():
    """color=True wraps BRAND in the ochre 24-bit code — RED if palette wrap is removed."""
    out = render_validation_banner(color=True)
    assert "\x1b[" in out
    # ochre = (181, 137, 75) = #B5894B
    assert "38;2;181;137;75" in out
