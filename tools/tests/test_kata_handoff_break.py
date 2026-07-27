"""Tests for kata_handoff_break — the SESSION BREAK notice."""
from __future__ import annotations

import kata_handoff_break as khb
import pytest

_ARGS = dict(
    handoff_path=".planning/HANDOFF.md",
    branch="docs/x", head="abc1234", master="fcb0338",
    gates="pytest 4106/3 skip · ruff clean",
)


class TestDeterminism:
    def test_same_inputs_same_bytes(self):
        """Law: same inputs => same bytes. No clock, no I/O, no ambient state."""
        assert khb.render_break(**_ARGS) == khb.render_break(**_ARGS)

    def test_no_ambient_time_is_read(self):
        """A stamp appears ONLY when the caller passes one (law 7 — injected clocks)."""
        # Match the LABEL line, not the word "written" (which occurs in the /compact prose).
        assert not [l for l in khb.render_break(**_ARGS).splitlines()
                    if l.strip().startswith("written")]
        out = khb.render_break(**_ARGS, stamp="2026-07-26T00:00:00Z")
        assert "2026-07-26T00:00:00Z" in out

    def test_owed_order_is_caller_order_not_set_order(self):
        """Law 3: no set/dict may drive output order."""
        owed = ("zebra", "alpha", "middle")
        lines = [ln for ln in khb.render_break(**_ARGS, owed=owed).splitlines()
                 if ln.startswith("  · ")]
        assert lines == ["  · zebra", "  · alpha", "  · middle"]


class TestPrescriptiveness:
    def test_it_prescribes_clear_and_warns_against_compact(self):
        out = khb.render_break(**_ARGS)
        assert "run /clear" in out
        assert "NOT /compact" in out
        assert "LOSSY SUMMARY" in out

    def test_it_states_the_harness_CANNOT_cross_the_boundary(self):
        """The honesty the whole notice exists to carry."""
        out = khb.render_break(**_ARGS)
        assert "cannot cross this boundary for you" in out

    def test_state_block_carries_every_field(self):
        out = khb.render_break(**_ARGS)
        for expected in (".planning/HANDOFF.md", "docs/x", "abc1234", "fcb0338", "4106"):
            assert expected in out, expected


class TestReentryBlock:
    def test_reentry_names_the_handoff_and_forbids_acting_first(self):
        block = khb.render_reentry(handoff_path=".planning/HANDOFF.md")
        assert ".planning/HANDOFF.md" in block
        assert "do not act before step 3" in block

    def test_reentry_requires_ground_truth_verification(self):
        block = khb.render_reentry(handoff_path="H.md")
        assert "stash list" in block and "EMPTY" in block

    def test_reentry_warns_off_the_venv_python_false_red(self):
        """The false-red that cost a real false alarm."""
        assert "false red" in khb.render_reentry(handoff_path="H.md")

    def test_reentry_is_short(self):
        """Orientation stays small when the handoff is large and prescriptive."""
        assert len(khb.render_reentry(handoff_path="H.md").splitlines()) <= 16

    def test_reentry_embedded_in_break_is_identical(self):
        """One source of truth for the orientation text."""
        block = khb.render_reentry(handoff_path=".planning/HANDOFF.md")
        out = khb.render_break(**_ARGS)
        for line in block.splitlines():
            if line.strip():
                assert line.strip() in out

    def test_repo_root_is_optional_and_prepended(self):
        assert "Working directory:" not in khb.render_reentry(handoff_path="H.md")
        assert "Working directory: C:/x" in khb.render_reentry(
            handoff_path="H.md", repo_root="C:/x")


class TestRendering:
    def test_brand_matches_kata_banner(self):
        """The break must read as the same system that printed the loop banner."""
        import kata_banner
        assert khb.BRAND == kata_banner.BRAND

    def test_cjk_width_is_measured_not_counted(self):
        assert khb._dwidth("改善型") == 6
        assert khb._dwidth("abc") == 3

    def test_optional_sections_are_omitted_when_empty(self):
        out = khb.render_break(**_ARGS)
        assert "OWED TO YOU" not in out
        # "NEXT STEP" also appears inside the re-entry block's step 4, so match the
        # section HEADING (two-space indent, nothing after it) rather than the substring.
        assert "  NEXT STEP" not in out.splitlines()

    def test_optional_sections_appear_when_supplied(self):
        out = khb.render_break(**_ARGS, owed=("rotate token",), next_step="grill KH-T01")
        assert "OWED TO YOU" in out and "rotate token" in out
        assert "NEXT STEP" in out and "grill KH-T01" in out
