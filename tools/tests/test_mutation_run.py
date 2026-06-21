"""Tests for tools/mutation_run.py — TDD first (red → green).

Strategy
--------
All tests inject a ``runner`` callable so no real subprocess or pytest process
is spawned.  Real filesystem writes/restores use ``tmp_path``.

Coverage:
- non-vacuous:  runner True then False → nonVacuous True
- vacuous:      runner True then True  → nonVacuous False
- restore:      file bytes identical after a normal run
- restore on raise: file bytes identical even when runner raises mid-way
- ValueError propagation: apply_line_removal of a missing line surfaces cleanly,
  no mutation left behind
- path-traversal guard: '..' in source_path → SystemExit
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_source(tmp_path: Path, content: str) -> Path:
    """Write a tiny source file and return its absolute path."""
    p = tmp_path / "sample.py"
    p.write_text(content, encoding="utf-8")
    return p


_SOURCE = "def add(a, b):\n    return a + b\n"
_ASSERTED_LINE = "    return a + b"


# ---------------------------------------------------------------------------
# TDD tests — these are RED until mutation_run.py is implemented
# ---------------------------------------------------------------------------

def test_non_vacuous_runner_true_then_false(tmp_path):
    """Baseline passes, mutated fails → nonVacuous True, testWentRed True."""
    import mutation_run

    src_path = _write_source(tmp_path, _SOURCE)
    calls = []

    def fake_runner(cmd):
        calls.append(cmd)
        # 1st call: pristine → passes; 2nd call: mutated → fails
        return len(calls) == 1

    result = mutation_run.prove_non_vacuous(
        str(src_path), _ASSERTED_LINE, "dummy-cmd", runner=fake_runner
    )

    assert result["nonVacuous"] is True
    assert result["testWentRed"] is True
    assert len(calls) == 2


def test_vacuous_runner_true_both(tmp_path):
    """Baseline passes, mutated also passes → nonVacuous False."""
    import mutation_run

    src_path = _write_source(tmp_path, _SOURCE)

    def always_pass(_cmd):
        return True

    result = mutation_run.prove_non_vacuous(
        str(src_path), _ASSERTED_LINE, "dummy-cmd", runner=always_pass
    )

    assert result["nonVacuous"] is False
    assert result["testWentRed"] is False


def test_restore_after_normal_run(tmp_path):
    """After prove_non_vacuous completes, source file bytes are identical to original."""
    import mutation_run

    src_path = _write_source(tmp_path, _SOURCE)
    original_bytes = src_path.read_bytes()

    mutation_run.prove_non_vacuous(
        str(src_path), _ASSERTED_LINE, "dummy-cmd", runner=lambda _: True
    )

    assert src_path.read_bytes() == original_bytes, (
        "File was not restored after a normal run"
    )


def test_restore_when_runner_raises(tmp_path):
    """Even when the runner raises on the 2nd call, the file MUST be restored."""
    import mutation_run

    src_path = _write_source(tmp_path, _SOURCE)
    original_bytes = src_path.read_bytes()
    call_count = [0]

    def raising_runner(_cmd):
        call_count[0] += 1
        if call_count[0] == 1:
            return True          # baseline passes
        raise RuntimeError("injected failure on mutated run")

    with pytest.raises(RuntimeError, match="injected failure"):
        mutation_run.prove_non_vacuous(
            str(src_path), _ASSERTED_LINE, "dummy-cmd", runner=raising_runner
        )

    # The file MUST be byte-identical despite the exception
    assert src_path.read_bytes() == original_bytes, (
        "File was NOT restored when the runner raised mid-way"
    )


def test_missing_line_raises_and_file_unchanged(tmp_path):
    """apply_line_removal of a line not in source → ValueError; file still original."""
    import mutation_run

    src_path = _write_source(tmp_path, _SOURCE)
    original_bytes = src_path.read_bytes()
    call_count = [0]

    def counting_runner(_cmd):
        call_count[0] += 1
        return True

    with pytest.raises(ValueError):
        mutation_run.prove_non_vacuous(
            str(src_path),
            "this line does not exist in the source",
            "dummy-cmd",
            runner=counting_runner,
        )

    # File must be unchanged
    assert src_path.read_bytes() == original_bytes, (
        "File was modified despite apply_line_removal raising"
    )


def test_path_traversal_guard_raises(tmp_path):
    """A source_path containing '..' must be rejected with SystemExit (CWE-23)."""
    import mutation_run

    traversal = str(tmp_path / ".." / "evil.py")

    with pytest.raises(SystemExit):
        mutation_run.prove_non_vacuous(
            traversal, "anything", "dummy-cmd", runner=lambda _: True
        )


def test_prove_many_collects_verdicts(tmp_path):
    """prove_many returns a list of verdict dicts, one per spec."""
    import mutation_run

    src_path = _write_source(tmp_path, _SOURCE)
    call_count = [0]

    def alternating_runner(_cmd):
        # Calls: 1=baseline True, 2=mutated False → nonVacuous True
        # Then for the 2nd spec (same file): 3=baseline True, 4=mutated False → nonVacuous True
        call_count[0] += 1
        return call_count[0] % 2 == 1  # odd calls pass, even calls fail

    specs = [
        {
            "source_path": str(src_path),
            "asserted_line": _ASSERTED_LINE,
            "test_cmd": "dummy-cmd",
        },
        {
            "source_path": str(src_path),
            "asserted_line": _ASSERTED_LINE,
            "test_cmd": "dummy-cmd",
        },
    ]

    results = mutation_run.prove_many(specs, runner=alternating_runner)
    assert len(results) == 2
    for r in results:
        assert "nonVacuous" in r
        assert "testWentRed" in r
