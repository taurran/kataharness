"""run_result.py — machine-readable gate RESULT emitter.

Produces a JSON-serialisable dict (and optionally a file) that encodes
everything needed to trust a KataHarness gate run without re-executing it.

Public surface
--------------
build_result(...)  -> dict   — pure; same inputs → same output (except utc)
write_result(...)  -> None   — writes result as indented JSON
run_gate(command)  -> (str, int)  — thin subprocess wrapper (optional)
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Union


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PYTEST_COUNT_RE = re.compile(r"(\d+)\s+(passed|failed|skipped)")


def _parse_pytest_counts(output: str) -> dict[str, int]:
    """Extract passed/failed/skipped counts from a pytest summary line.

    Returns a dict with keys 'passed', 'failed', 'skipped' (all int, default 0).
    Works on any line that contains patterns like '40 passed', '2 failed', etc.
    """
    counts: dict[str, int] = {"passed": 0, "failed": 0, "skipped": 0}
    for match in _PYTEST_COUNT_RE.finditer(output):
        n, label = int(match.group(1)), match.group(2)
        if label in counts:
            counts[label] = n
    return counts


def _stdout_tail(output: str, max_chars: int = 2000) -> str:
    """Return the last *max_chars* characters of *output*."""
    return output[-max_chars:] if len(output) > max_chars else output


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_result(
    gate_name: str,
    command: str,
    output: str,
    exit_code: int,
    baseline_sha: str,
    result_sha: str,
    utc: Union[str, None] = None,
) -> dict:
    """Build a machine-checkable result dict for a single gate run.

    Parameters
    ----------
    gate_name:    Human-readable name of the gate (e.g. "smoke").
    command:      The shell command that was executed.
    output:       Combined stdout + stderr from the command.
    exit_code:    Process exit code (0 = success).
    baseline_sha: Git SHA of the baseline being tested against.
    result_sha:   Git SHA of the commit under test.
    utc:          ISO-8601 UTC timestamp string.  Pass *None* (default) to use
                  the current time; pass a fixed string in tests for determinism.

    Returns
    -------
    dict with keys: gateName, command, exitCode, passed, failed, skipped,
                    stdoutTail, baselineSha, resultSha, utc.
    """
    if utc is None:
        utc = datetime.now(tz=timezone.utc).isoformat()

    counts = _parse_pytest_counts(output)

    return {
        "gateName": gate_name,
        "command": command,
        "exitCode": exit_code,
        "passed": counts["passed"],
        "failed": counts["failed"],
        "skipped": counts["skipped"],
        "stdoutTail": _stdout_tail(output),
        "baselineSha": baseline_sha,
        "resultSha": result_sha,
        "utc": utc,
    }


def write_result(result: dict, path: Union[str, Path]) -> None:
    """Write *result* as indented JSON to *path*.

    Parameters
    ----------
    result: dict as returned by :func:`build_result`.
    path:   Destination file path (str or :class:`~pathlib.Path`).
            Parent directory must already exist.
    """
    Path(path).write_text(json.dumps(result, indent=2), encoding="utf-8")


def run_gate(command: str) -> tuple[str, int]:
    """Run *command* in a subprocess and return (combined_output, exit_code).

    stdout and stderr are merged into a single string (same order as terminal).
    This is a thin convenience wrapper; the core logic lives in :func:`build_result`.
    """
    proc = subprocess.run(
        command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return proc.stdout, proc.returncode
