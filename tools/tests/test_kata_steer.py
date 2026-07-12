"""Tests for tools/kata_steer.py — the operator->agent steering channel reader.

Wired 2026-07-12 (health review F-3): STEERING.md previously CLAIMED "the harness reads
this on a cadence" + an AGENT_STOP kill-switch with ZERO implementation. These tests pin
the real engine so the claim can never regress to a facade again.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import kata_steer  # noqa: E402

# --------------------------------------------------------------------------- #
# stop_requested — the graceful kill-switch
# --------------------------------------------------------------------------- #

def _steering(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "STEERING.md"
    p.write_text(body, encoding="utf-8")
    return p


def test_stop_false_when_no_marker(tmp_path):
    kata = tmp_path / ".kata"
    kata.mkdir()
    _steering(tmp_path, "# STEERING\n## Active directives\n_(none active)_\n")
    assert kata_steer.stop_requested(kata) is False


def test_stop_true_on_agent_stop_file(tmp_path):
    kata = tmp_path / ".kata"
    kata.mkdir()
    (kata / "AGENT_STOP").write_text("", encoding="utf-8")
    # MUTATION PROOF: delete the file-presence branch and this goes RED.
    assert kata_steer.stop_requested(kata) is True


def test_stop_true_on_steering_sentinel(tmp_path):
    kata = tmp_path / ".kata"
    kata.mkdir()
    _steering(tmp_path, "# STEERING\n## AGENT_STOP\nplease halt at the next boundary\n")
    assert kata_steer.stop_requested(kata) is True


def test_stop_false_when_steering_absent(tmp_path):
    kata = tmp_path / ".kata"
    kata.mkdir()
    assert kata_steer.stop_requested(kata) is False


def test_stop_rejects_traversal_kata_dir(tmp_path):
    with pytest.raises(ValueError, match="traversal"):
        kata_steer.stop_requested(tmp_path / ".." / "evil")


# --------------------------------------------------------------------------- #
# read_active_directives
# --------------------------------------------------------------------------- #

def test_reads_active_directives_in_order(tmp_path):
    body = (
        "# STEERING\n\n"
        "## Active directives\n"
        "- Prioritize the auth module.\n"
        "- Skip the perf pass this run.\n\n"
        "## Consumed / delivered\n"
        "- Old thing (done).\n"
    )
    p = _steering(tmp_path, body)
    got = kata_steer.read_active_directives(p)
    assert got == ["- Prioritize the auth module.", "- Skip the perf pass this run."]
    # Consumed-section lines must NOT leak in (heading-scoping mutation proof).
    assert all("Old thing" not in d for d in got)


def test_placeholder_none_line_is_not_a_directive(tmp_path):
    p = _steering(tmp_path, "## Active directives\n_(none active — nothing pending)_\n")
    assert kata_steer.read_active_directives(p) == []
    assert kata_steer.has_active_steering(p) is False


def test_absent_file_is_fail_soft(tmp_path):
    assert kata_steer.read_active_directives(tmp_path / "nope.md") == []


def test_real_directive_starting_with_none_is_not_dropped(tmp_path):
    """adval #3: a real directive that merely starts with '(none-blocking)' must NOT be
    skipped as the italic placeholder — only the shipped `_( none … )_` form is a placeholder."""
    p = _steering(tmp_path, "## Active directives\n(none-blocking) refactor the auth module\n")
    assert kata_steer.read_active_directives(p) == ["(none-blocking) refactor the auth module"]
    # but the actual italic placeholder is still skipped
    p2 = _steering(tmp_path, "## Active directives\n_(none active — nothing pending)_\n")
    assert kata_steer.read_active_directives(p2) == []


def test_only_active_section_scoped(tmp_path):
    body = (
        "## Preamble\n- not a directive (wrong section)\n"
        "## Active directives\n- real directive\n"
        "## Notes\n- also not a directive\n"
    )
    p = _steering(tmp_path, body)
    assert kata_steer.read_active_directives(p) == ["- real directive"]
    assert kata_steer.has_active_steering(p) is True
