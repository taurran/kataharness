"""gate_emit.py — thin orchestrator that turns the three KataHarness pure libraries
(run_result, footprint, mutation_check) into an actually-produced artifact set.

COMPOSES; never reimplements the underlying libraries.

Public API
----------
emit_gate_artifacts(...)  -> dict   — writes RESULT.json, footprint.json, mutation.json (opt.)
                                      and returns a summary dict.

CLI
---
python -m gate_emit --gate-name N --command C --footprint A B C \\
                    --baseline SHA --result SHA [--out .kata]

Security note (from PLAN threat model): the ``command`` argument is operator-supplied
and runs via run_result.run_gate (shell=True).  Attacker-reachable only through the
operator/orchestrator — same trust level as the existing gate invocation; no new
external surface introduced.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Callable, List, Optional, Union

import footprint as _footprint
import run_result


# ---------------------------------------------------------------------------
# Public function
# ---------------------------------------------------------------------------


def emit_gate_artifacts(
    gate_name: str,
    command: str,
    footprint: List[str],
    baseline_sha: str,
    result_sha: str,
    out_dir: Union[str, Path],
    *,
    mutation_records: Optional[List[dict]] = None,
    runner: Optional[Callable[[str], tuple]] = None,
    utc: Optional[str] = None,
) -> dict:
    """Compose run_result / footprint / mutation_check into the gate artifact set.

    Parameters
    ----------
    gate_name:
        Human-readable name of the gate (e.g. ``"smoke"``).
    command:
        Shell command to run (passed verbatim to the runner).
    footprint:
        Declared file/directory paths that this gate is allowed to touch.
    baseline_sha:
        Git SHA of the baseline commit (the tip *before* the work).
    result_sha:
        Git SHA of the integration HEAD being evaluated.
    out_dir:
        Directory to write artifacts into.  Created (including parents) if absent.
    mutation_records:
        Optional list of ``{testWentRed, nonVacuous}`` dicts produced by
        ``mutation_check.mutation_verdict``.  Pass ``None`` (default) to skip
        writing ``mutation.json``.  An empty list is valid — ``allNonVacuous``
        is ``True`` (vacuous truth: no counter-evidence; documented choice).
    runner:
        Callable ``(command: str) -> (output: str, exit_code: int)``.
        Defaults to ``run_result.run_gate`` so callers need not import it.
        Injectable so tests are pure (no real subprocess).
    utc:
        ISO-8601 UTC timestamp string.  ``None`` (default) → current wall time.
        Injectable for deterministic tests.

    Returns
    -------
    dict with keys:
        ``resultPath``      — absolute path to ``RESULT.json``
        ``footprintPath``   — absolute path to ``footprint.json``
        ``mutationPath``    — absolute path to ``mutation.json``, or ``None``
        ``withinFootprint`` — bool: every changed file was inside the footprint
        ``passed``          — int: test-case passed count
        ``failed``          — int: test-case failed count
        ``skipped``         — int: test-case skipped count
        ``exitCode``        — int: process exit code from the gate command
    """
    if runner is None:
        runner = run_result.run_gate

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # 1. Run the gate and write RESULT.json
    # ------------------------------------------------------------------
    output, exit_code = runner(command)

    result = run_result.build_result(
        gate_name=gate_name,
        command=command,
        output=output,
        exit_code=exit_code,
        baseline_sha=baseline_sha,
        result_sha=result_sha,
        utc=utc,
    )
    result_path = out / "RESULT.json"
    run_result.write_result(result, result_path)

    # ------------------------------------------------------------------
    # 2. Compute and write footprint.json
    # ------------------------------------------------------------------
    changed = _footprint.changed_since(baseline_sha)
    diffstat = _footprint.diff_stat(baseline_sha)
    man = _footprint.manifest(changed, footprint, diffstat)

    footprint_path = out / "footprint.json"
    footprint_path.write_text(json.dumps(man, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # 3. Write mutation.json if mutation_records were supplied
    # ------------------------------------------------------------------
    mutation_path: Optional[Path] = None
    if mutation_records is not None:
        mutation_payload = {
            "records": mutation_records,
            # Vacuous-truth choice: an empty list has no counter-evidence → True.
            # Rationale: "no mutations ran" is not evidence of vacuity; treat as clean.
            "allNonVacuous": all(r["nonVacuous"] for r in mutation_records),
        }
        mutation_path = out / "mutation.json"
        mutation_path.write_text(json.dumps(mutation_payload, indent=2), encoding="utf-8")

    # ------------------------------------------------------------------
    # 4. Return summary dict
    # ------------------------------------------------------------------
    return {
        "resultPath": str(result_path.resolve()),
        "footprintPath": str(footprint_path.resolve()),
        "mutationPath": str(mutation_path.resolve()) if mutation_path is not None else None,
        "withinFootprint": man["withinFootprint"],
        "passed": result["passed"],
        "failed": result["failed"],
        "skipped": result["skipped"],
        "exitCode": result["exitCode"],
    }


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

def _safe_path(raw: str) -> Path:
    """Reject path-traversal (CWE-23) in an operator-supplied CLI path, then resolve.

    Blocks any ``..`` segment — the traversal-escape primitive — so a crafted
    argument cannot climb out of the intended tree, while still allowing the
    absolute and nested-relative paths the maintainer legitimately targets.
    Sanitizes the tainted CLI input at the boundary before any filesystem sink.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"gate_emit: refusing path with '..' traversal: {raw!r}")
    return p.resolve()


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="gate_emit",
        description=(
            "Emit KataHarness gate artifacts (RESULT.json, footprint.json, "
            "mutation.json) by composing run_result / footprint / mutation_check."
        ),
    )
    p.add_argument("--gate-name", required=True, metavar="NAME",
                   help="Human-readable name of the gate (e.g. 'smoke')")
    p.add_argument("--command", required=True, metavar="CMD",
                   help="Shell command to run as the gate")
    p.add_argument("--footprint", required=True, nargs="+", metavar="PATH",
                   help="Declared footprint paths / directory prefixes")
    p.add_argument("--baseline", required=True, metavar="SHA",
                   dest="baseline_sha",
                   help="Git SHA of the baseline commit")
    p.add_argument("--result", required=True, metavar="SHA",
                   dest="result_sha",
                   help="Git SHA of the integration HEAD under evaluation")
    p.add_argument("--out", default=".kata", metavar="DIR",
                   help="Output directory for artifacts (default: .kata)")
    return p


if __name__ == "__main__":
    args = _build_parser().parse_args()
    summary = emit_gate_artifacts(
        gate_name=args.gate_name,
        command=args.command,
        footprint=args.footprint,
        baseline_sha=args.baseline_sha,
        result_sha=args.result_sha,
        out_dir=_safe_path(args.out),
    )
    print(json.dumps(summary, indent=2))
