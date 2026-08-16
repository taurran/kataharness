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


# Per-branch contract for the no-phantom guard. `_next_steps_banner` has two
# branch classes and they advertise kata differently:
#   "commands" -> the branch tells the user to type slash commands (claude).
#                 Its tokens must be NON-EMPTY and every one of them real.
#   "skills"   -> the branch names SKILLS instead (codex/kiro say "the
#                 kata-initiate / kata-onboard skill"; the generic fallback says
#                 "the kata-initiate skill"), with no leading slash, because
#                 those hosts do not expose kata as slash commands. Emitting
#                 ZERO slash tokens IS that branch's contract, so that is what
#                 the param asserts.
_BRANCH_CONTRACT = {
    "claude": "commands",
    "codex": "skills",
    "kiro": "skills",
    "other": "skills",
    "": "skills",
}


@pytest.mark.parametrize("platform", sorted(_BRANCH_CONTRACT))
def test_no_platform_branch_emits_a_phantom_command(platform):
    """The guard holds for every branch, each against its OWN contract.

    Non-vacuity, per param. This test used to assert only ``tokens - real ==
    set()`` for all five params. The four non-claude branches emit no slash
    tokens at all, so for them the extracted set was empty and the subtraction
    was empty for free: the assertion could not tell "no phantoms because none
    are possible" from "no phantoms because we checked". Each param now carries
    the expectation that actually binds its branch, so every param can red.
    """
    tokens = _banner_command_tokens(platform)
    real = _real_command_names()
    if _BRANCH_CONTRACT[platform] == "commands":
        assert tokens, f"{platform!r} banner advertised no /kata command at all"
        phantom = tokens - real
        assert not phantom, (
            f"{platform!r} banner names phantom command(s): {sorted(phantom)}; "
            f"real commands are {sorted(real)}"
        )
    else:
        assert tokens == set(), (
            f"{platform!r} banner emitted slash-command token(s) "
            f"{sorted(tokens)}; this branch's contract is to name SKILLS "
            "without a leading slash, because its host does not expose kata as "
            "slash commands. If that contract genuinely changed, move the "
            "platform into the 'commands' class of _BRANCH_CONTRACT so its "
            "tokens get checked against the real command set."
        )
