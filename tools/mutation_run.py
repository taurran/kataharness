"""mutation_run.py — deterministic, restoring mutation-proof runner for KataHarness.

Public API
----------
prove_non_vacuous(source_path, asserted_line, test_cmd, *, runner=None) -> dict
    Run the non-vacuity PROVE step for ONE asserted line.  Always restores the
    source file to its original bytes — even on exception / interrupt (try/finally).

prove_many(specs, *, runner=None) -> list[dict]
    Thin collector: run prove_non_vacuous over a list of spec dicts, return all
    verdict dicts.  Feed the result to gate_emit.emit_gate_artifacts(mutation_records=...).

Security note
-------------
source_path is operator-supplied.  A ``..``-guard (CWE-23) is applied at the
boundary — mirrors the pattern in gate_emit._safe_path.  test_cmd runs at the
same trust level as the existing gate (operator/orchestrator).
"""

from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Callable
from pathlib import Path

# ---------------------------------------------------------------------------
# Path-traversal guard (CWE-23) — mirrors gate_emit._safe_path
# ---------------------------------------------------------------------------

def _safe_source_path(raw: str) -> Path:
    """Reject any path containing a ``..`` segment, then resolve.

    Blocks the traversal-escape primitive so a crafted argument cannot climb
    out of the intended tree.  Sanitises the tainted input at the boundary
    before any filesystem sink.

    Raises:
        ValueError: if ``raw`` contains a ``..`` segment.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"mutation_run: refusing source_path with '..' traversal: {raw!r}"
        )
    return p.resolve()


# ---------------------------------------------------------------------------
# Default subprocess runner (injectable so tests are pure)
# ---------------------------------------------------------------------------

def _sanitized_gate_env() -> dict:
    """Return an env for gate/score subprocesses with nondeterminism stripped (DET-09).

    A gate's exit code feeds a scored/gated result, so the run must be reproducible
    across hosts (DETERMINISM-DOCTRINE law 8). ``PYTEST_ADDOPTS`` (e.g. ``-x --ff``)
    and pytest plugin autoload (e.g. pytest-randomly) can flip a boolean that reaches
    Axis-Q. We strip ``PYTEST_ADDOPTS`` and disable plugin autoload; PATH/uv/git env
    is preserved. Autoload-disable (env) beats ``-p no:randomly`` (argv) because the
    gate command is arbitrary — it may not be pytest at all, where an injected argv
    flag would break it; a target that needs an autoloaded plugin opts back in via
    ``-p <plugin>`` / config (which still loads under autoload-disable).
    """
    env = os.environ.copy()
    env.pop("PYTEST_ADDOPTS", None)
    env["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    return env


def _default_runner(cmd: str, *, timeout: float = 600.0) -> bool:
    """Run *cmd* in a shell (sanitized env) and return True if it exits 0.

    Deterministic gate execution (DET-09): the command runs under a **sanitized
    env** — ``PYTEST_ADDOPTS`` stripped, plugin autoload disabled — which is the
    determinism win that matters (those flip the Axis-Q boolean across hosts).
    ``shell=True`` is deliberately RETAINED: the ``test_cmd`` contract is a shell
    string using shell metacharacters (``cd /d "<dir>" && <py> -m pytest ...``),
    so argv-tokenizing it would break every caller; the sink runs at
    operator/orchestrator trust and is registered in ``protocol/exec-safety.md``.
    A hung command is bounded by *timeout* (seconds, default 600); on
    ``subprocess.TimeoutExpired`` the runner returns **False** — a timeout is a
    FAILURE-shaped verdict, never a hang and never an exception surfacing as
    success (D136: no silent-permissive default; the gate goes red).
    """
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, timeout=timeout, env=_sanitized_gate_env()
        )
    except subprocess.TimeoutExpired:
        print(f"[kata] gate runner timeout after {timeout}s: {cmd!r}", file=sys.stderr)
        return False
    return result.returncode == 0


# ---------------------------------------------------------------------------
# Core API
# ---------------------------------------------------------------------------

def prove_non_vacuous(
    source_path: str,
    asserted_line: str,
    test_cmd: str,
    *,
    runner: Callable[[str], bool] | None = None,
) -> dict:
    """Run the deterministic, restoring non-vacuity PROVE step for one asserted line.

    Algorithm
    ---------
    1. Guard ``source_path`` against ``..`` traversal (CWE-23).
    2. Read the original file bytes.
    3. Run ``test_cmd`` on the pristine source → ``baseline_passed`` (bool).
    4. In a ``try``:
       a. Apply ``mutation_check.apply_line_removal(original_text, asserted_line)``
          to produce the mutated text.
       b. Write the mutated text to ``source_path``.
       c. Run ``test_cmd`` → ``mutated_passed`` (bool).
    5. In a ``finally`` block: **ALWAYS restore** the original bytes — even if
       (4a)/(4b)/(4c) raised or the process is interrupted.  The file is
       byte-identical to the original after this call returns (or raises).
    6. Return ``mutation_check.mutation_verdict(baseline_passed, mutated_passed)``.

    Args:
        source_path:   Path to the source file to mutate.  Must not contain ``..``.
        asserted_line: The exact content of the line to remove for the mutation
                       (no trailing newline needed).  Passed to
                       ``mutation_check.apply_line_removal``; a missing line raises
                       ``ValueError`` — surfaced to the caller without leaving the
                       file mutated.
        test_cmd:      Shell command to run (identical to the gate's ``command``).
        runner:        Injectable ``(cmd: str) -> bool`` — True means tests passed.
                       Defaults to a real ``subprocess.run`` wrapper.  Inject a
                       callable in tests to stay pure (no real pytest).

    Returns:
        ``{testWentRed: bool, nonVacuous: bool}`` — the verdict dict from
        ``mutation_check.mutation_verdict``.

    Raises:
        ValueError:  if ``source_path`` contains a ``..`` traversal segment.
        ValueError:  if ``asserted_line`` is not found in the source text
                     (propagated from ``apply_line_removal``; file is restored).
        Any exception the runner raises is propagated; the file is still restored.
    """
    # Lazy import so importing mutation_run never hard-fails if mutation_check
    # is missing (e.g. during isolated unit-test collection).
    import mutation_check  # noqa: PLC0415

    if runner is None:
        runner = _default_runner

    path = _safe_source_path(source_path)

    # 2. Read original bytes (source of truth for the restore)
    original_bytes = path.read_bytes()
    original_text = original_bytes.decode("utf-8")

    # 3. Baseline run on pristine source
    baseline_passed: bool = runner(test_cmd)

    # 4. Mutation: apply → write → run; restore in finally no matter what
    mutated_passed: bool = False
    try:
        # 4a. Compute mutated text (raises ValueError if line not found)
        mutated_text = mutation_check.apply_line_removal(original_text, asserted_line)
        # 4b. Write mutated text
        path.write_bytes(mutated_text.encode("utf-8"))
        # 4c. Run on mutated source
        mutated_passed = runner(test_cmd)
    finally:
        # 5. ALWAYS restore — byte-identical, even on exception
        path.write_bytes(original_bytes)

    # 6. Return verdict
    return mutation_check.mutation_verdict(baseline_passed, mutated_passed)


def prove_many(
    specs: list[dict],
    *,
    runner: Callable[[str], bool] | None = None,
) -> list[dict]:
    """Run prove_non_vacuous over a list of spec dicts and collect verdicts.

    Each spec dict must contain:
        ``source_path``   — path to the source file
        ``asserted_line`` — the line to remove for mutation
        ``test_cmd``      — the shell command to run

    Returns a list of verdict dicts (one per spec), suitable for passing to
    ``gate_emit.emit_gate_artifacts(mutation_records=...)``.

    Args:
        specs:  List of dicts with keys ``source_path``, ``asserted_line``,
                ``test_cmd``.
        runner: Optional injectable runner (same semantics as prove_non_vacuous).

    Returns:
        List of ``{testWentRed, nonVacuous}`` dicts.
    """
    results: list[dict] = []
    for spec in specs:
        verdict = prove_non_vacuous(
            spec["source_path"],
            spec["asserted_line"],
            spec["test_cmd"],
            runner=runner,
        )
        results.append(verdict)
    return results
