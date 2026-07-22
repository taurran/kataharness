"""mutation_run.py — deterministic, SANDBOXED mutation-proof runner for KataHarness.

Public API
----------
prove_non_vacuous(source_path, asserted_line, test_cmd, *, runner=None, project_root=None) -> dict
    Run the non-vacuity PROVE step for ONE asserted line — against a SANDBOXED COPY
    of the project tree.  The live source file is read once and NEVER written
    (the D1 phantom-corruption fix: the old mutate-live/restore-in-finally design
    exposed concurrent readers to a corrupted window and persisted the mutation on
    a hard kill; grill record `.planning/specs/mutation-sandbox/GRILL-LEDGER.md`).

prove_many(specs, *, runner=None) -> list[dict]
    Thin collector: run prove_non_vacuous over a list of spec dicts, return all
    verdict dicts.  Feed the result to gate_emit.emit_gate_artifacts(mutation_records=...).

Sandbox contract (grill D1–D5)
------------------------------
- The PROJECT ROOT (first ancestor of the source carrying ``pyproject.toml`` or
  ``.git``; explicit ``project_root=`` overrides; no marker ⇒ raise, D136) is
  copied to a temp tree, excluding ``.git``/``.venv``/``.kata``/``__pycache__``/
  ``.pytest_cache``/``.ruff_cache``/``node_modules``.
- ``test_cmd`` is PATH-REDIRECTED: every literal occurrence of the resolved root
  (``str()`` and ``as_posix()`` flavors) is substituted with the sandbox root —
  EXCEPT occurrences continuing into ``.venv`` (the live interpreter reference,
  e.g. ``<root>\\.venv\\Scripts\\python.exe``, is read-only and must survive).
- A RESIDUAL LIVE-ROOT GUARD then scans the redirected command: any remaining
  slash-agnostic occurrence of the root not followed by ``.venv`` — matched
  case-insensitively on Windows (``os.name == "nt"``), where a case-mismatched
  spelling would silently target the LIVE tree — raises instead of running.
- BOTH runs (baseline on the pristine copy, mutated after the copy's source is
  rewritten) execute inside the sandbox with ``cwd`` = the sandbox root, so the
  comparison differs ONLY by the mutation (DETERMINISM-DOCTRINE law 8).
- ``finally`` removes the sandbox (best-effort) — a leaked temp dir on a hard
  kill is harmless; a mutated live file was not.

Security note
-------------
source_path / project_root are operator-supplied.  A ``..``-guard (CWE-23) is
applied at the boundary — mirrors the pattern in gate_emit._safe_path.  test_cmd
runs at the same trust level as the existing gate (operator/orchestrator).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from pathlib import Path

#: Directories never copied into the sandbox (grill D1).
_SANDBOX_EXCLUDES: tuple[str, ...] = (
    ".git", ".venv", ".kata", "__pycache__", ".pytest_cache", ".ruff_cache", "node_modules",
)

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
# Sandbox plumbing (grill D1/D4/D5)
# ---------------------------------------------------------------------------

def _find_project_root(source: Path) -> Path:
    """First ancestor of *source* carrying ``pyproject.toml`` or ``.git`` (grill D1).

    Fail-closed (D136): no marker anywhere up the tree ⇒ raise — the copy scope is
    never guessed.  Callers with markerless trees pass ``project_root=`` explicitly.
    """
    for candidate in source.parents:
        if (candidate / "pyproject.toml").exists() or (candidate / ".git").exists():
            return candidate
    raise ValueError(
        f"mutation_run: no project root found above {source} (looked for "
        "pyproject.toml/.git in every ancestor). Pass project_root= explicitly."
    )


def _root_pattern(project_root: Path, *, ignorecase: bool) -> re.Pattern:
    """A slash-agnostic regex matching the literal *project_root*, excluding
    occurrences that continue into ``.venv`` (grill D4/D5)."""
    parts = project_root.parts  # ('C:\\', 'Dev', ...) — first part carries the sep
    escaped = [re.escape(parts[0].rstrip("\\/"))] + [re.escape(p) for p in parts[1:]]
    pattern = r"[\\/]+".join(escaped) + r"(?![\\/]\.venv)"
    return re.compile(pattern, re.IGNORECASE if ignorecase else 0)


def _redirect_cmd(test_cmd: str, project_root: Path, sandbox_root: Path) -> str:
    """Substitute live-root references in *test_cmd* with the sandbox root (grill D4),
    then apply the residual live-root guard (grill D5).

    Pure function of its inputs on a given platform.  Substitution is exact-case
    and slash-agnostic; the residual scan is case-insensitive on Windows (where a
    case-mismatched spelling would silently target the LIVE tree) and exact-case
    on POSIX (where a case-different path is a genuinely different path).
    """
    redirected = _root_pattern(project_root, ignorecase=False).sub(
        lambda _m: str(sandbox_root), test_cmd
    )
    residual = _root_pattern(project_root, ignorecase=(os.name == "nt"))
    leftover = residual.search(redirected)
    if leftover:
        raise ValueError(
            "mutation_run: test_cmd still references the LIVE project root after "
            f"redirection ({leftover.group(0)!r}) — a mutation gate must never run "
            "against the live tree (D1/D136). Fix the command's root spelling."
        )
    return redirected


def _make_sandbox(project_root: Path) -> tuple[Path, Path]:
    """Copy *project_root* into a fresh temp tree (grill D1 excludes applied).

    Returns ``(holder, sandbox_root)`` — *holder* is the mkdtemp dir to remove.
    """
    holder = Path(tempfile.mkdtemp(prefix="kata-mutation-"))
    sandbox_root = holder / "tree"
    shutil.copytree(
        project_root, sandbox_root, ignore=shutil.ignore_patterns(*_SANDBOX_EXCLUDES)
    )
    return holder, sandbox_root


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


def _default_runner(cmd: str, cwd: str | None = None, *, timeout: float = 600.0) -> bool:
    """Run *cmd* in a shell (sanitized env, *cwd*) and return True if it exits 0.

    ``cwd`` is the sandbox root during a prove run (grill D2) — relative test
    commands thereby execute inside the sandbox.  Deterministic gate execution
    (DET-09): the command runs under a **sanitized env** — ``PYTEST_ADDOPTS``
    stripped, plugin autoload disabled — which is the determinism win that matters
    (those flip the Axis-Q boolean across hosts).  ``shell=True`` is deliberately
    RETAINED: the ``test_cmd`` contract is a shell string using shell
    metacharacters (``cd /d "<dir>" && <py> -m pytest ...``), so argv-tokenizing
    it would break every caller; the sink runs at operator/orchestrator trust and
    is registered in ``protocol/exec-safety.md``.  A hung command is bounded by
    *timeout* (seconds, default 600); on ``subprocess.TimeoutExpired`` the runner
    returns **False** — a timeout is a FAILURE-shaped verdict, never a hang and
    never an exception surfacing as success (D136: no silent-permissive default;
    the gate goes red).
    """
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, timeout=timeout,
            env=_sanitized_gate_env(), cwd=cwd,
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
    runner: Callable[[str, str], bool] | None = None,
    project_root: str | None = None,
) -> dict:
    """Run the deterministic, SANDBOXED non-vacuity PROVE step for one asserted line.

    Algorithm (grill D1–D5)
    -----------------------
    1. Guard ``source_path`` (and ``project_root`` when given) against ``..``
       traversal (CWE-23); derive the project root from markers otherwise
       (``pyproject.toml``/``.git``; none ⇒ raise, D136).
    2. Read the original file bytes from the LIVE tree — its ONLY access; the
       live file is never written.
    3. Copy the project root into a fresh temp sandbox (excludes: ``.git``,
       ``.venv``, ``.kata``, ``__pycache__``, ``.pytest_cache``, ``.ruff_cache``,
       ``node_modules``) and PATH-REDIRECT ``test_cmd`` into it (live-root
       substitution with a ``.venv`` lookahead + the residual live-root guard).
    4. Run the redirected command in the pristine sandbox → ``baseline_passed``.
    5. Apply ``mutation_check.apply_line_removal`` and write the mutated text to
       the SANDBOX copy of the source; run again → ``mutated_passed``.
    6. In a ``finally`` block: remove the sandbox (best-effort — a leaked temp
       dir on a hard kill is harmless).
    7. Return ``mutation_check.mutation_verdict(baseline_passed, mutated_passed)``.

    Args:
        source_path:   Path to the source file to mutate.  Must not contain ``..``
                       and must live under the project root.
        asserted_line: The exact content of the line to remove for the mutation
                       (no trailing newline needed).  Passed to
                       ``mutation_check.apply_line_removal``; a missing line raises
                       ``ValueError`` — surfaced to the caller (the live file was
                       never touched).
        test_cmd:      Shell command to run (identical to the gate's ``command``).
                       Absolute references to the project root are redirected into
                       the sandbox; relative commands run with the sandbox root as
                       ``cwd``.
        runner:        Injectable ``(cmd: str, cwd: str) -> bool`` — True means
                       tests passed.  Defaults to a real ``subprocess.run`` wrapper.
                       Inject a callable in tests to stay pure (no real pytest).
        project_root:  Optional explicit tree root to sandbox (``..``-guarded).
                       Defaults to marker derivation from ``source_path``.

    Returns:
        ``{testWentRed: bool, nonVacuous: bool}`` — the verdict dict from
        ``mutation_check.mutation_verdict``.

    Raises:
        ValueError:  if ``source_path``/``project_root`` contains a ``..`` segment,
                     no project-root marker is found, the source is not under the
                     project root, the redirected command still references the
                     live root (grill D5), or ``asserted_line`` is not found.
        Any exception the runner raises is propagated; the sandbox is still removed.
    """
    # Lazy import so importing mutation_run never hard-fails if mutation_check
    # is missing (e.g. during isolated unit-test collection).
    import mutation_check  # noqa: PLC0415

    if runner is None:
        runner = _default_runner

    path = _safe_source_path(source_path)
    root = _safe_source_path(project_root) if project_root is not None else _find_project_root(path)
    try:
        rel_source = path.relative_to(root)
    except ValueError:
        raise ValueError(
            f"mutation_run: source {path} is not under the project root {root} — "
            "the sandbox copy could not contain it (D136). STOP."
        ) from None

    # 2. Read original bytes — the live tree's ONLY access (never written).
    original_text = path.read_bytes().decode("utf-8")

    # Compute the mutated text BEFORE paying for the sandbox copy
    # (raises ValueError if the line is not found — nothing was copied or run).
    mutated_text = mutation_check.apply_line_removal(original_text, asserted_line)

    # 3. Sandbox + redirect (grill D1/D4/D5).
    holder, sandbox_root = _make_sandbox(root)
    try:
        redirected_cmd = _redirect_cmd(test_cmd, root, sandbox_root)
        sandbox_cwd = str(sandbox_root)

        # 4. Baseline on the PRISTINE sandbox copy (grill D3).
        baseline_passed: bool = runner(redirected_cmd, sandbox_cwd)

        # 5. Mutate the SANDBOX copy and re-run.
        (sandbox_root / rel_source).write_bytes(mutated_text.encode("utf-8"))
        mutated_passed: bool = runner(redirected_cmd, sandbox_cwd)
    finally:
        # 6. Remove the sandbox — best-effort; the live tree needs no restore.
        shutil.rmtree(holder, ignore_errors=True)

    # 7. Return verdict
    return mutation_check.mutation_verdict(baseline_passed, mutated_passed)


def prove_many(
    specs: list[dict],
    *,
    runner: Callable[[str, str], bool] | None = None,
) -> list[dict]:
    """Run prove_non_vacuous over a list of spec dicts and collect verdicts.

    Each spec dict must contain:
        ``source_path``   — path to the source file
        ``asserted_line`` — the line to remove for mutation
        ``test_cmd``      — the shell command to run
    and may contain:
        ``project_root``  — explicit tree root to sandbox (else marker-derived)

    Returns a list of verdict dicts (one per spec), suitable for passing to
    ``gate_emit.emit_gate_artifacts(mutation_records=...)``.

    Args:
        specs:  List of dicts with keys ``source_path``, ``asserted_line``,
                ``test_cmd`` (optionally ``project_root``).
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
            project_root=spec.get("project_root"),
        )
        results.append(verdict)
    return results
