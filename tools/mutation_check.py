"""Non-vacuity (mutation) proof utilities for KataHarness TDD loop.

These are pure functions; no I/O beyond the subprocess helper.
Run from the ``tools/`` directory so pytest's pythonpath resolves them.
"""

from __future__ import annotations

import os
import subprocess
import sys


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


def run_named_test(
    test_path: str,
    test_name: str,
    *,
    cwd: str | None = None,
    timeout: float = 600.0,
) -> bool:
    """Run a single named pytest test via ``uv run pytest`` and return True if it passed.

    This is a thin shell around subprocess — not required by the test suite but
    provided for orchestrator use when automating the mutation-proof loop.

    FIX A1 — cwd parameter: when *cwd* is provided, pytest runs from that working
    directory AND *cwd* is prepended to ``PYTHONPATH`` so that a simple
    ``from src import X`` in the control's tests resolves correctly.
    BC: *cwd=None* is the default and preserves exactly the previous behavior
    (no cwd, no PYTHONPATH mutation, env unchanged).

    NOTE: Full per-control dependency-env isolation (a control with its own
    3rd-party deps) is a D5/real-fixture concern.  v1 only needs simple-import
    controls (flat ``src/`` package) to resolve via PYTHONPATH.

    Args:
        test_path: Path to the test file (absolute, or relative to *cwd*).
        test_name: The test function name (no ``::`` prefix).
        cwd:       Optional working directory for pytest subprocess.  When set,
                   *cwd* is also prepended to ``PYTHONPATH`` so imports from the
                   clone root resolve.  Default None = current working directory
                   (BC, unchanged behavior).
        timeout:   Wall-clock bound in seconds for the pytest subprocess
                   (default 600).  On ``subprocess.TimeoutExpired`` this returns
                   **False** — a timeout is a FAILURE-shaped verdict, never a
                   hang and never an exception surfacing as success (D136: no
                   silent-permissive default; the gate goes red).

    Returns:
        True if pytest exits 0 (test passed), False otherwise (including timeout).
    """
    # DET-09 (surgical — adval R1): this is the SCORING path (benchmark dual-gate),
    # so it must not DEFLATE a target's numbers. Strip PYTEST_ADDOPTS (env-injected
    # order/early-exit nondeterminism) but KEEP plugin autoload — blanket-disabling it
    # makes a target's pytest-asyncio/mock/django tests FAIL under the gate when they
    # PASS normally (a gold F2P scored unresolved). We block only the one nondeterminism
    # plugin by argv (`-p no:randomly`, a harmless no-op when it isn't installed).
    # cwd's PYTHONPATH prepend composes on top. (DETERMINISM-DOCTRINE law 8.)
    run_env: dict = os.environ.copy()
    run_env.pop("PYTEST_ADDOPTS", None)
    if cwd is not None:
        existing_pp = run_env.get("PYTHONPATH", "")
        run_env["PYTHONPATH"] = cwd + (os.pathsep + existing_pp if existing_pp else "")

    try:
        result = subprocess.run(
            ["uv", "run", "pytest", "-p", "no:randomly", f"{test_path}::{test_name}", "-q"],
            capture_output=True,
            cwd=cwd,
            env=run_env,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        print(
            f"[kata] gate runner timeout after {timeout}s: {test_path}::{test_name}",
            file=sys.stderr,
        )
        return False
    return result.returncode == 0
