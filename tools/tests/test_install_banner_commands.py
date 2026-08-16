"""test_install_banner_commands.py — the banner cannot name a phantom slash command.

Structural guard for BL-X02: the claude-branch next-steps banner shipped
`/kata-initiate` and `/kata-bootstrap` for months. Both exist as SKILLS but
neither is a slash command, so a first-run user who typed what the installer
told them to type got nothing. The old test pinned those exact strings, so it
green-lit the rot instead of catching it.

This guard is structural rather than a name list: every `/kata...` token the
banner emits must correspond to a real file in `adapters/claude/commands/`.
It therefore cannot rot the way the banner did — add, rename, or delete a
command and this test tracks it automatically.

SANCTIONED CONVENTION CROSSING
------------------------------
`test_install_commands.py:4` states that the real `adapters/claude/commands/`
directory is deliberately NOT used by install tests (fixtures in tmp dirs
substitute, for isolation). This file knowingly crosses that convention: it
reads the REAL commands directory on purpose, because coupling the banner to
the actual shipped command set IS the entire point of the guard — a fixture
copy would re-introduce exactly the drift being fixed. The crossing is
explicitly sanctioned by the frozen plan at
`.planning/specs/backlog-burn-02/PLAN.md` (Item 2 · BL-X02, note [LOW-2]).
The read is read-only and touches no host or user directory.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]  # tools/
sys.path.insert(0, str(ROOT))

REPO_ROOT = ROOT.parent
COMMANDS_DIR = REPO_ROOT / "adapters" / "claude" / "commands"

import kata_install as ki  # noqa: E402  (path bootstrap must precede the import)

# A home path deliberately free of the substring "/kata" so the extractor cannot
# mistake a path segment for a command token.
_HOME = "/home/u/.kata-home"

# Matches a slash-command token: "/kata", "/kata-start", "/kata-loop", ...
_SLASH_TOKEN = re.compile(r"/kata[-a-z]*")


def _real_command_names() -> set[str]:
    """Basenames (stems) of the real shipped claude commands."""
    return {p.stem for p in COMMANDS_DIR.glob("*.md")}


def _banner_command_tokens(platform: str) -> set[str]:
    """Every /kata... token the banner emits, normalized to bare names."""
    out = ki._next_steps_banner(platform, _HOME, "symlink", 47)
    return {tok.lstrip("/") for tok in _SLASH_TOKEN.findall(out)}


def test_real_commands_dir_is_present_and_populated():
    # Non-vacuity floor: if this dir vanished or emptied, the subset assertion
    # below would pass trivially against an empty universe.
    assert COMMANDS_DIR.is_dir(), f"missing real commands dir: {COMMANDS_DIR}"
    assert len(_real_command_names()) >= 5


def test_claude_banner_names_only_real_commands():
    """THE self-gate: banner slash-commands are a subset of the real command set."""
    tokens = _banner_command_tokens("claude")
    real = _real_command_names()
    # Non-vacuity: the claude branch must actually advertise commands, otherwise
    # an empty token set would satisfy the subset check for free.
    assert tokens, "claude banner advertised no /kata command at all"
    phantom = tokens - real
    assert not phantom, (
        f"banner names slash command(s) that do not exist: {sorted(phantom)}; "
        f"real commands are {sorted(real)}"
    )


def test_the_specific_phantoms_stay_gone():
    """Regression pin for the two names BL-X02 removed (skills, never commands)."""
    out = ki._next_steps_banner("claude", _HOME, "symlink", 47)
    assert "/kata-initiate" not in out
    assert "/kata-bootstrap" not in out


@pytest.mark.parametrize("platform", ["claude", "codex", "kiro", "other", ""])
def test_no_platform_branch_emits_a_phantom_command(platform):
    """The guard holds for every branch, not just the one that regressed."""
    phantom = _banner_command_tokens(platform) - _real_command_names()
    assert not phantom, f"{platform!r} banner names phantom command(s): {sorted(phantom)}"
