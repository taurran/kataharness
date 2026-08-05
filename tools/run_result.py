"""run_result.py — machine-readable gate RESULT emitter.

Produces a JSON-serialisable dict (and optionally a file) that encodes
everything needed to trust a KataHarness gate run without re-executing it.

Public surface
--------------
build_result(...)          -> dict          — pure; same inputs → same output (except utc)
write_result(...)          -> None          — writes result as indented JSON
run_gate(command)          -> (str, int)    — thin subprocess wrapper (optional)
evidence_is_current(...)   -> (bool, str)   — pure identity gate: is RESULT.json's
                                               resultSha the SHA actually being
                                               credited? FAIL-CLOSED (D136) on every
                                               absent/ambiguous input.
resolve_head_sha(repo_root) -> str | None   — thin subprocess wrapper: resolves
                                               *repo_root*'s live HEAD via
                                               `git rev-parse HEAD`. Registered
                                               sink (protocol/exec-safety.md);
                                               this module is ALREADY a
                                               registered subprocess sink
                                               (run_gate) — new callers (e.g.
                                               benchmark.score_arms) call this
                                               function rather than growing a
                                               second spawn site of their own.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from fs_atomic import atomic_write_text

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PYTEST_COUNT_RE = re.compile(r"(\d+)\s+(passed|failed|skipped)")

# Minimum SHA prefix length treated as a meaningful identity — below this, a
# "match" would be coincidental (git's own short-SHA floor). Never treat a
# shorter prefix as a match.
_MIN_SHA_LEN = 7

# Bounded per Determinism Doctrine law 8 (gate subprocesses must not hang).
_GIT_TIMEOUT_S = 30


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
    utc: str | None = None,
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
        utc = datetime.now(tz=UTC).isoformat()

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


def evidence_is_current(result_json: dict | None, expected_sha: str | None) -> tuple[bool, str]:
    """Is *result_json*'s ``resultSha`` the SHA actually being credited?

    Gate evidence (RESULT.json) faithfully records the SHA it was produced
    against, but nothing previously checked that SHA against the tree being
    credited — a RESULT.json 56 commits stale was fully creditable as proof the
    *current* build passes. This closes that gap.

    Pure: no subprocess, no clock, no I/O (Determinism Doctrine). The caller is
    responsible for resolving *expected_sha* (e.g. ``git rev-parse HEAD`` of the
    tree under test) — this function only compares.

    FAIL-CLOSED throughout (D136 — no silent-permissive default): every absent
    or ambiguous input is a hard NO, never treated as "assume current".

    An ancestry check (``git merge-base --is-ancestor``) is deliberately NOT
    used here — it tests *validity* (was this SHA ever real), not *freshness*
    (is this SHA the one being credited RIGHT NOW). A 56-commits-stale SHA is a
    perfectly valid ancestor of HEAD and would pass an ancestry check while
    still being stale evidence.

    Args:
        result_json:  Parsed RESULT.json dict (``build_result``'s output), or
                       None if the artifact is absent/unreadable.
        expected_sha: The SHA of the tree actually being credited, resolved by
                       the caller. None/empty means the caller could not
                       establish what SHA is being credited.

    Returns:
        (True, "") when ``result_json["resultSha"]`` and *expected_sha* name the
        SAME commit — compared case-insensitively over the shorter of the two
        lengths (a 7-char short SHA matches its own 40-char long form), with
        both sides required to be at least 7 characters (git's own short-SHA
        floor; a shorter prefix is never treated as a match). Otherwise
        (False, reason):
          - result_json is None                      -> "no-evidence"
          - resultSha missing/empty                   -> "evidence-missing-sha"
          - expected_sha None/empty                   -> "unknown-expected-sha"
          - either SHA shorter than 7 chars            -> "evidence-missing-sha"
          - SHAs differ                                -> "stale-evidence"
    """
    if result_json is None:
        return False, "no-evidence"

    result_sha = result_json.get("resultSha")
    if not result_sha:
        return False, "evidence-missing-sha"

    if not expected_sha:
        return False, "unknown-expected-sha"

    result_sha = str(result_sha)
    expected = str(expected_sha)

    if len(result_sha) < _MIN_SHA_LEN or len(expected) < _MIN_SHA_LEN:
        return False, "evidence-missing-sha"

    compare_len = min(len(result_sha), len(expected))
    if result_sha[:compare_len].lower() != expected[:compare_len].lower():
        return False, "stale-evidence"

    return True, ""


def resolve_head_sha(repo_root: str | Path) -> str | None:
    """Resolve *repo_root*'s current HEAD SHA via ``git rev-parse HEAD``.

    Registered sink (protocol/exec-safety.md): fixed argv, ``shell=False``, no
    external input — *repo_root* is a harness-supplied path (e.g. an arm's own
    clone root from ``benchmark.score_arms``' ``arm_map``), never
    externally-controlled data reaching argv. Law-1 pins (Determinism Doctrine)
    inlined here the way ``contract_gate.py:150`` does — there is no shared
    pinned git helper in this repo.

    This module (``run_result.py``) is ALREADY a registered subprocess sink
    (``run_gate``) — callers needing a resolved SHA (e.g. the benchmark
    identity gate, D136) call this function rather than growing a second,
    unregistered spawn site of their own.

    Returns None on ANY resolution failure (not a git repo, git absent, a
    non-zero exit, an empty result, or a timeout). This function never raises;
    the typical caller passes the None straight through to
    :func:`evidence_is_current`, which fail-closes it as
    "unknown-expected-sha" — resolution failure is NEVER treated as "skip the
    check".
    """
    try:
        proc = subprocess.run(
            [
                "git",
                "-c", "log.follow=false",
                "-c", "log.showSignature=false",
                "-c", "core.quotepath=off",
                "rev-parse", "HEAD",
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    sha = proc.stdout.strip()
    return sha or None


def write_result(result: dict, path: str | Path) -> None:
    """Write *result* as indented JSON to *path*.

    Atomic (D159, same-dir tmp + ``os.replace``): ``RESULT.json`` is read
    concurrently by the evaluator and the benchmark scorer while a gate is still
    emitting, and a truncate-then-write leaves a window where a reader sees a
    partial file.  Output bytes are unchanged.

    Parameters
    ----------
    result: dict as returned by :func:`build_result`.
    path:   Destination file path (str or :class:`~pathlib.Path`).
            Parent directory must already exist.
    """
    atomic_write_text(Path(path), json.dumps(result, indent=2), encoding="utf-8")


def run_gate(command: str, *, timeout: float = 600.0) -> tuple[str, int]:
    """Run *command* in a subprocess and return (combined_output, exit_code).

    stdout and stderr are merged into a single string (same order as terminal).
    This is a thin convenience wrapper; the core logic lives in :func:`build_result`.

    A hung gate command is bounded by *timeout* (seconds, default 600).  On
    ``subprocess.TimeoutExpired`` this returns a FAILURE-shaped result — any
    partial output plus a ``[kata] gate runner timeout`` note, with exit code
    124 (the conventional timeout code; nonzero → gate red).  It never hangs
    and never raises through as success (D136: no silent-permissive default).
    """
    try:
        proc = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or ""
        if isinstance(partial, bytes):  # TimeoutExpired may carry bytes even with text=True
            partial = partial.decode("utf-8", errors="replace")
        return partial + f"\n[kata] gate runner timeout after {timeout}s\n", 124
    return proc.stdout, proc.returncode
