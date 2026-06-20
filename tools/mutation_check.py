"""Non-vacuity (mutation) proof utilities for KataHarness TDD loop.

These are pure functions; no I/O beyond the subprocess helper.
Run from the ``tools/`` directory so pytest's pythonpath resolves them.
"""

from __future__ import annotations

import subprocess


def mutation_verdict(baseline_passed: bool, mutated_passed: bool) -> dict:
    """Return a verdict dict describing whether a test provides non-vacuous proof.

    A test is *non-vacuous* (it actually bites) if and only if:
    - it passed on the un-mutated source (``baseline_passed`` is True), AND
    - it failed on the mutated source (``mutated_passed`` is False).

    Args:
        baseline_passed: True if the test passed before mutation was applied.
        mutated_passed:  True if the test still passed after mutation was applied.

    Returns:
        A dict with two boolean keys:
        ``testWentRed`` — True iff the test newly failed after mutation.
        ``nonVacuous``  — True iff baseline passed AND mutated failed (proof of bite).
    """
    went_red = baseline_passed and not mutated_passed
    non_vacuous = baseline_passed and not mutated_passed
    return {"testWentRed": went_red, "nonVacuous": non_vacuous}


def apply_line_removal(source: str, target_line: str) -> str:
    """Return *source* with the first exact occurrence of *target_line* removed.

    The match is line-content exact: ``target_line`` is compared against each
    line with its newline stripped.  The line (including its trailing newline, if
    any) is removed.  Only the *first* matching line is removed.

    Args:
        source:      The full text of the file to mutate (in-memory; not written).
        target_line: The exact content of the line to remove (no newline needed).

    Returns:
        The mutated source string with the matching line excised.

    Raises:
        ValueError: If ``target_line`` is not found in ``source``.
    """
    lines = source.splitlines(keepends=True)
    for idx, line in enumerate(lines):
        if line.rstrip("\n").rstrip("\r") == target_line:
            return "".join(lines[:idx] + lines[idx + 1:])
    raise ValueError(f"Line not found in source: {target_line!r}")


def run_named_test(test_path: str, test_name: str) -> bool:
    """Run a single named pytest test via ``uv run pytest`` and return True if it passed.

    This is a thin shell around subprocess — not required by the test suite but
    provided for orchestrator use when automating the mutation-proof loop.

    Args:
        test_path: Path to the test file (absolute or relative to cwd).
        test_name: The test function name (no ``::`` prefix).

    Returns:
        True if pytest exits 0 (test passed), False otherwise.
    """
    result = subprocess.run(
        ["uv", "run", "pytest", f"{test_path}::{test_name}", "-q"],
        capture_output=True,
    )
    return result.returncode == 0
