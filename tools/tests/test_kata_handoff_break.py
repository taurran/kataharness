"""Tests for kata_handoff_break - the SESSION BREAK notice."""
from __future__ import annotations

import kata_handoff_break as khb

_ARGS = dict(
    handoff_path=".planning/HANDOFF.md", repo="C:/Dev/Projects/KataHarness",
    branch="docs/x", head="abc1234", master="fcb0338",
    gates="pytest 4122/3 skip - ruff clean",
)
_RE = dict(handoff_path="H.md", branch="b", master="m")


class TestDeterminism:
    def test_same_inputs_same_bytes(self):
        assert khb.render_break(**_ARGS) == khb.render_break(**_ARGS)

    def test_no_ambient_time_is_read(self):
        """Law 7: a stamp appears ONLY when the caller passes one."""
        assert not [x for x in khb.render_break(**_ARGS).splitlines()
                    if x.strip().startswith("written")]
        assert "2026-07-26T00:00:00Z" in khb.render_break(
            **_ARGS, stamp="2026-07-26T00:00:00Z")

    def test_owed_order_is_caller_order(self):
        """Law 3: no set/dict drives output order."""
        lines = [x for x in khb.render_break(**_ARGS, owed=("zebra", "alpha")).splitlines()
                 if x.startswith("  \u00b7 ")]
        assert lines == ["  \u00b7 zebra", "  \u00b7 alpha"]


class TestPrescriptiveness:
    def test_prescribes_clear_over_compact_in_one_line(self):
        out = khb.render_break(**_ARGS)
        assert "RUN /clear" in out and "not /compact" in out

    def test_state_block_carries_every_field(self):
        out = khb.render_break(**_ARGS)
        for x in (".planning/HANDOFF.md", "docs/x", "abc1234", "fcb0338", "4122"):
            assert x in out, x

    def test_is_concise(self):
        """Wordiness was the operator's complaint; this guards the regression."""
        assert len(khb.render_break(**_ARGS).splitlines()) <= 45


class TestShellVsAgentSeparation:
    """The cd is a terminal action; the prompt goes in a chat box. Never one block."""

    def test_agent_prompt_contains_NO_shell_command(self):
        b = khb.render_reentry(**_RE)
        assert not b.lstrip().startswith("cd ")
        assert "cd C:" not in b

    def test_break_presents_them_as_two_numbered_steps(self):
        out = khb.render_break(**_ARGS)
        assert "\u2460" in out and "SHELL" in out
        assert "\u2461" in out and "AGENT PROMPT" in out
        assert out.index("\u2460") < out.index("\u2461")

    def test_shell_step_carries_the_repo_path(self):
        assert "cd C:/Dev/Projects/KataHarness" in khb.render_break(**_ARGS)

    def test_shell_step_says_when_to_skip_it(self):
        """Running /clear in place needs no cd - say so, or it reads as mandatory."""
        out = khb.render_break(**_ARGS)
        assert "Skip to" in out and "/clear" in out


class TestReentryBlock:
    def test_carries_concrete_commands_with_expected_values(self):
        """DEFINED, not generic: every check names its expected result."""
        b = khb.render_reentry(handoff_path="H.md", branch="br", master="fcb0338")
        for cmd in ("git status --porcelain", "git stash list",
                    "git rev-parse --short origin/master",
                    "git rev-parse --abbrev-ref HEAD",
                    "uv run python scripts/gauntlet.py"):
            assert cmd in b, cmd
        assert "-> fcb0338" in b and "-> br" in b and "4/4 PASS" in b

    def test_warns_off_the_venv_python_false_red(self):
        assert "false-red" in khb.render_reentry(**_RE)

    def test_forbids_acting_on_mismatch(self):
        assert "STOP and report" in khb.render_reentry(**_RE)

    def test_is_short(self):
        assert len(khb.render_reentry(**_RE).splitlines()) <= 14

    def test_embedded_copy_is_identical(self):
        """One source of truth for the orientation text."""
        b = khb.render_reentry(handoff_path=".planning/HANDOFF.md",
                               branch="docs/x", master="fcb0338")
        assert b in khb.render_break(**_ARGS)


class TestRendering:
    def test_brand_matches_kata_banner(self):
        import kata_banner
        assert khb.BRAND == kata_banner.BRAND

    def test_cjk_width_is_measured(self):
        assert khb._dwidth("\u6539\u5584\u578b") == 6
        assert khb._dwidth("abc") == 3

    def test_optional_sections_omitted_when_empty(self):
        out = khb.render_break(**_ARGS)
        assert "OWED TO YOU" not in out
        assert "NEXT:" not in out

    def test_optional_sections_appear_when_supplied(self):
        out = khb.render_break(**_ARGS, owed=("rotate token",), next_step="grill KH-T01")
        assert "OWED TO YOU" in out and "rotate token" in out
        assert "NEXT: grill KH-T01" in out
