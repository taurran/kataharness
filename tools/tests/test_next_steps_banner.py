"""test_next_steps_banner.py — the post-install human guidance block.

Covers kata_install._next_steps_banner: platform-aware copy, accurate skill
count, the documented entry-point skills, learn-more pointers, and the
Windows-console safety invariant (ASCII-only — no box-drawing or emoji).
The banner is a pure string builder; main() owns routing and --json suppression.
"""

from __future__ import annotations

import kata_install as ki


def test_claude_banner_has_steps_and_entrypoints():
    out = ki._next_steps_banner("claude", "/home/u/.kata-home", "symlink", 47)
    assert "KataHarness installed" in out
    assert "47 skills" in out and "mode: symlink" in out
    # the three guided steps
    assert "1) Restart your tool" in out
    assert "2) Start a run" in out
    assert "3) Your first run" in out
    # documented entry points (grounded against README/skills, D124)
    assert "/kata-initiate" in out
    assert "/kata-onboard" in out
    assert "/kata-bootstrap" in out
    # platform-correct skills location + restart wording
    assert "~/.claude/skills" in out
    assert "Claude Code: exit and reopen" in out
    # learn-more pointers anchored to the resolved home
    assert "/home/u/.kata-home/docs/SETUP.md" in out
    assert "/home/u/.kata-home/README.md" in out
    assert "Home: /home/u/.kata-home" in out


def test_best_effort_banner_uses_agents_skills_path():
    out = ki._next_steps_banner("codex", "/h/.kata-home", "copy", 47)
    assert ".agents/skills" in out
    assert "Restart codex" in out
    # best-effort does not advertise the slash-command entry points
    assert "/kata-initiate" not in out
    assert "kata-initiate" in out  # mentioned as a skill name, not a command


def test_count_omitted_when_zero():
    out = ki._next_steps_banner("codex", "/h", "unknown", 0)
    assert "skills *" not in out  # no "N skills" token when count is 0
    assert "KataHarness installed" in out


def test_banner_is_ascii_only():
    # Windows legacy console safety — no box-drawing/emoji that mojibake on cp437.
    for plat in ("claude", "codex", "kiro", "other"):
        out = ki._next_steps_banner(plat, "/h", "symlink", 47)
        out.encode("ascii")  # raises UnicodeEncodeError if any non-ASCII slipped in


def test_banner_is_deterministic():
    a = ki._next_steps_banner("claude", "/h", "symlink", 47)
    b = ki._next_steps_banner("claude", "/h", "symlink", 47)
    assert a == b
