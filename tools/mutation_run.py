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

Execution contract (BL-X14 / RS-H1)
-----------------------------------
The sink runs **structured argv with ``shell=False``**.  ``test_cmd`` is
compiled by ``_compile_test_cmd`` through a CLOSED grammar
(``[cd [/d] <dir> &&] <runner> <target|flag>*``) and anything outside it is
REFUSED, never degraded.  This is a platform-correctness fix before it is a
safety fix: the old ``shell=True`` path ran a cmd.exe-only string, so on Linux
``cd /d`` short-circuited the whole command, both runs "failed", and every
mutation proof returned ``{'testWentRed': False}`` — the anti-vacuity engine was
itself vacuous there for 12 days.  The consumed ``cd`` target must resolve
inside the sandbox, which is what structurally guarantees the re-run imports the
SANDBOX copy rather than the live tree.

Security note
-------------
source_path / project_root are operator-supplied.  A ``..``-guard (CWE-23) is
applied at the boundary — mirrors the pattern in gate_emit._safe_path.  test_cmd
runs at the same trust level as the existing gate (operator/orchestrator), and
its pytest targets are additionally guarded by ``_guard_node_id`` (leading-``-``
flag injection, ``..`` traversal, resolved containment) — the same treatment as
``benchmark.py`` / ``benchmark_def.py``.
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
    occurrences that continue into ``.venv`` (grill D4/D5; adval folds F1/F2).

    Two boundary guards (adval-caught):
    - a RIGHT boundary ``(?![A-Za-z0-9._~-])`` so a root that is a PREFIX of a
      sibling path (``C:\\proj`` vs ``C:\\proj2``, ``<root>-backup``) is never
      rewritten and never trips the residual guard;
    - the ``.venv`` preservation matches only a TRUE ``.venv`` component
      (``[\\/]+\\.venv`` followed by a non-name char) — ``<root>\\.venv-old`` is
      substituted like any other subpath (loud sandbox miss, never a silent
      live reference), and a doubled separator before ``.venv`` still preserves.

    Guard limits (stated, not solved): alternate SPELLINGS of the root — 8.3
    short names (``C:\\DEVPRO~1``), symlinked roots, UNC/admin-share forms — are
    invisible to a literal pattern.  Accepted at the test_cmd trust level:
    commands are machine-built from ``Path.resolve()``/``sys.executable``.
    """
    parts = project_root.parts  # ('C:\\', 'Dev', ...) — first part carries the sep
    escaped = [re.escape(parts[0].rstrip("\\/"))] + [re.escape(p) for p in parts[1:]]
    pattern = (
        r"[\\/]+".join(escaped)
        + r"(?![A-Za-z0-9._~-])"                      # F1: right boundary
        + r"(?![\\/]+\.venv(?![A-Za-z0-9._-]))"        # F2: true .venv component only
    )
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
# The closed test_cmd grammar (BL-X14 / RS-H1) — compile to argv or REFUSE
# ---------------------------------------------------------------------------
#
# WHY THIS EXISTS.  The mutation sink used to run ``test_cmd`` through
# ``shell=True``.  Every mutation-proof caller in this repo builds the shape
# ``cd /d "<dir>" && <py> -m pytest "<node-id>" -q --tb=no``.  ``cd /d`` is a
# **cmd.exe builtin flag**: on POSIX ``shell=True`` invokes ``/bin/sh``, whose
# ``cd`` takes one operand, so the command died before pytest was ever reached
# and BOTH the baseline and the mutated run reported failure — yielding
# ``{'testWentRed': False}`` for mutations that bite.  The anti-vacuity engine
# was itself vacuous on Linux (BL-X14; ~61 red meta-tests, CI red 12 days).
#
# THE GRAMMAR (closed; anything outside it is REFUSED, never degraded):
#
#     <command> ::= [ "cd" [ "/d" ] <dir> "&&" ] <runner> <arg>*
#     <runner>  ::= <python> "-m" "pytest" | "uv" "run" "pytest" | "pytest"
#     <python>  ::= a token whose basename (case-folded, ".exe" stripped) is
#                   python | python3[.N] | pythonw | py
#     <arg>     ::= <flag> | <target>
#     <flag>    ::= "-x" | "--long" | "--long=value"
#     <target>  ::= a pytest node-ID / path, guarded by _guard_node_id
#
# The optional ``cd`` prefix is CONSUMED, not executed: its directory becomes
# the subprocess ``cwd``.  That is the whole platform fix — a working-directory
# change expressed as a parameter instead of a shell dialect.
#
# Node-ID guarding reuses the live precedents ``benchmark.py:_guard_node_id``
# and ``benchmark_def.py:_guard_node_id`` (leading ``-`` = flag injection;
# ``..`` = CWE-23 traversal; resolved containment under the root).

#: Interpreter basenames accepted as the head of a ``-m pytest`` invocation.
_PY_BASENAMES: frozenset[str] = frozenset({"python", "pythonw", "py"})

#: ``python3`` / ``python3.12`` and friends.
_PY_VERSIONED = re.compile(r"^python3(\.\d+)?$")

#: A pytest CLI flag (short or long, optionally ``=value``).
_FLAG_RE = re.compile(r"^--?[A-Za-z][A-Za-z0-9-]*(=\S*)?$")

#: Characters that only have meaning to a shell.  None may survive into argv —
#: their presence means the caller assumed shell semantics the sink no longer
#: provides, and running anyway would silently change the command's meaning.
_SHELL_METACHARS: frozenset[str] = frozenset("&|;<>$`\n\r")


def _tokenize(cmd: str) -> list[str]:
    """Split *cmd* on whitespace, honouring double quotes.  No shell semantics.

    Deliberately NOT ``shlex``: ``shlex(posix=True)`` eats the backslashes in a
    Windows path (``C:\\Dev\\x`` -> ``C:Devx``) and ``posix=False`` keeps the
    quote characters inside the token.  Double quotes here mean exactly what
    they mean to every caller that built one of these strings — "this run of
    characters is one argument" — with no escape processing, which matches
    cmd.exe's own treatment of the quoted paths in the corpus.

    Raises:
        ValueError: on an unbalanced double quote.
    """
    tokens: list[str] = []
    buf: list[str] = []
    quoted = False        # inside a "..." run
    started = False       # buf is a real (possibly empty) token
    for ch in cmd:
        if ch == '"':
            quoted = not quoted
            started = True
        elif not quoted and ch in " \t":
            if started or buf:
                tokens.append("".join(buf))
                buf, started = [], False
        else:
            buf.append(ch)
            started = True
    if quoted:
        raise ValueError(f"mutation_run: unbalanced quote in test_cmd: {cmd!r}")
    if started or buf:
        tokens.append("".join(buf))
    return tokens


def _guard_node_id(target: str, root: Path | None) -> str:
    """Validate a pytest target (node-ID or path) before it enters argv.

    Mirrors the live precedents ``benchmark.py:_guard_node_id`` and
    ``benchmark_def.py:_guard_node_id``:

    1. Reject a leading ``-`` (a target that reads as a CLI flag).
    2. Reject any ``..`` component in the path part (CWE-23).
    3. Containment: ``root / <path part>`` must resolve under *root* — blocks
       symlink escape and absolute targets pointing out of the sandbox.

    Args:
        target: the candidate token (``path``, or ``path::name``).
        root:   the effective working directory targets are relative to; when
                ``None`` (a caller invoking the runner with no cwd) checks 1–2
                still apply and containment is skipped.

    Returns:
        *target* unchanged if it passes every check.

    Raises:
        ValueError: on any violation (fail-closed — a bad target never reaches
                    the subprocess).
    """
    if not target:
        raise ValueError("mutation_run: empty pytest target in test_cmd")
    if target.startswith("-"):
        raise ValueError(
            f"mutation_run: refusing pytest target that reads as a flag: {target!r}"
        )
    sep = target.rfind("::")
    rel = target[:sep] if sep >= 0 else target
    if any(part == ".." for part in Path(rel).parts):
        raise ValueError(
            f"mutation_run: refusing pytest target with '..' traversal (CWE-23): {target!r}"
        )
    if root is not None:
        resolved_root = Path(root).resolve()
        resolved = (resolved_root / rel).resolve()
        if resolved != resolved_root and not resolved.is_relative_to(resolved_root):
            raise ValueError(
                f"mutation_run: pytest target {target!r} resolves outside the run root "
                f"{str(resolved_root)!r} — a mutation gate must only address the sandbox "
                "(D1/D136). STOP."
            )
    return target


def _split_cd_prefix(tokens: list[str]) -> tuple[str | None, list[str]]:
    """Consume an optional leading ``cd [/d] <dir> &&`` and return (dir, rest).

    The ``cd`` is CONSUMED, never executed — its target becomes the subprocess
    ``cwd``.  A ``cd`` that is not followed by exactly ``[/d] <dir> &&`` is a
    refusal, not a best-effort parse.
    """
    if not tokens or tokens[0].lower() != "cd":
        return None, tokens
    idx = 1
    if idx < len(tokens) and tokens[idx].lower() in ("/d", "-d"):
        idx += 1
    if idx + 1 >= len(tokens) or tokens[idx + 1] != "&&":
        raise ValueError(
            "mutation_run: test_cmd starts with 'cd' but does not match the "
            f"grammar 'cd [/d] <dir> && <runner> ...': {tokens!r}"
        )
    return tokens[idx], tokens[idx + 2:]


def _parse_runner(rest: list[str]) -> tuple[list[str], list[str]]:
    """Split *rest* into (runner-argv-prefix, remaining args) or refuse."""
    if not rest:
        raise ValueError("mutation_run: test_cmd has no command after the 'cd' prefix")
    base = Path(rest[0]).name.lower()
    if base.endswith(".exe"):
        base = base[:-4]
    if base in _PY_BASENAMES or _PY_VERSIONED.match(base):
        if rest[1:3] != ["-m", "pytest"]:
            raise ValueError(
                f"mutation_run: interpreter {rest[0]!r} must be followed by '-m pytest' "
                f"(closed grammar); got {rest[1:3]!r}"
            )
        return rest[:3], rest[3:]
    if base == "uv":
        if rest[1:3] != ["run", "pytest"]:
            raise ValueError(
                f"mutation_run: 'uv' must be followed by 'run pytest' (closed grammar); "
                f"got {rest[1:3]!r}"
            )
        return rest[:3], rest[3:]
    if base == "pytest":
        return rest[:1], rest[1:]
    raise ValueError(
        f"mutation_run: refusing test_cmd — {rest[0]!r} is not a recognised runner. "
        "The closed grammar accepts '<python> -m pytest ...', 'uv run pytest ...', or "
        "'pytest ...', each optionally preceded by 'cd [/d] <dir> &&'. "
        "(protocol/exec-safety.md: structured argv, never a shell string.)"
    )


def _compile_test_cmd(
    test_cmd: str | list[str], cwd: str | None = None
) -> tuple[list[str], str | None]:
    """Compile *test_cmd* into ``(argv, run_cwd)`` under the closed grammar.

    Pure function of its inputs — identical on every platform, which is the
    point (BL-X14).  A pre-built argv list is accepted and passed through with
    the same target guarding.

    Args:
        test_cmd: the (already root-redirected) command string, or an argv list.
        cwd:      the sandbox root supplied by ``prove_non_vacuous``.  When
                  given, a ``cd`` target MUST be it or a directory beneath it —
                  the structural guarantee that the re-run happens inside the
                  sandbox and therefore imports the sandbox copy.

    Returns:
        ``(argv, run_cwd)`` ready for ``subprocess.run(..., shell=False)``.

    Raises:
        ValueError: on anything outside the grammar, on a shell metacharacter
                    surviving into argv, on a guarded-target violation, or on a
                    ``cd`` target that escapes *cwd*.
    """
    tokens = list(test_cmd) if isinstance(test_cmd, list) else _tokenize(test_cmd)
    cd_dir, rest = _split_cd_prefix(tokens)

    for tok in rest:
        bad = sorted(set(tok) & _SHELL_METACHARS)
        if bad:
            raise ValueError(
                f"mutation_run: refusing test_cmd — token {tok!r} carries shell "
                f"metacharacter(s) {bad!r} that the sink no longer interprets "
                "(shell=False). Express it as structured argv, or as the single "
                "supported 'cd [/d] <dir> &&' prefix."
            )

    # The run directory: the consumed `cd` target if present, else the sandbox cwd.
    run_cwd: str | None = cd_dir if cd_dir is not None else cwd
    if cd_dir is not None and cwd is not None:
        sandbox = Path(cwd).resolve()
        target = Path(cd_dir).resolve()
        if target != sandbox and not target.is_relative_to(sandbox):
            raise ValueError(
                f"mutation_run: test_cmd would 'cd' to {cd_dir!r}, outside the sandbox "
                f"{cwd!r} — the mutated copy would not be what the re-run imports "
                "(BL-X14 / D1/D136). STOP."
            )

    prefix, args = _parse_runner(rest)
    argv = list(prefix)
    for tok in args:
        argv.append(tok if _FLAG_RE.match(tok) else _guard_node_id(tok, run_cwd))
    return argv, run_cwd


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
    """Compile *cmd* through the closed grammar and run it as structured argv.

    **No ``shell=True``** (BL-X14 / RS-H1).  The command is compiled by
    :func:`_compile_test_cmd` into ``(argv, run_cwd)`` and executed with
    ``shell=False``, so its meaning is identical on every platform — the
    property the old shell string did NOT have (``cd /d`` is a cmd.exe builtin
    flag; under ``/bin/sh`` the whole ``&&`` chain short-circuited and every
    mutation proof on Linux was vacuous for 12 days).  An unparseable command
    RAISES rather than running degraded (compile-through-grammar-or-refuse).

    ``cwd`` is the sandbox root during a prove run (grill D2); ``run_cwd`` is it
    or a directory beneath it — never outside (enforced in the compiler), which
    is what structurally guarantees the re-run imports the SANDBOX copy.

    Deterministic gate execution (DET-09): the command runs under a **sanitized
    env** — ``PYTEST_ADDOPTS`` stripped, plugin autoload disabled — which is the
    determinism win that matters (those flip the Axis-Q boolean across hosts).

    A hung command is bounded by *timeout* (seconds, default 600); on
    ``subprocess.TimeoutExpired`` the runner returns **False** — a timeout is a
    FAILURE-shaped verdict, never a hang and never an exception surfacing as
    success (D136: no silent-permissive default; the gate goes red).

    A missing executable (``FileNotFoundError``) deliberately PROPAGATES rather
    than reading as a failed test: under ``shell=False`` that is a broken
    harness, and swallowing it as ``False`` is exactly the silent-vacuity shape
    BL-X14 was.
    """
    argv, run_cwd = _compile_test_cmd(cmd, cwd)
    try:
        result = subprocess.run(
            argv, capture_output=True, timeout=timeout,
            env=_sanitized_gate_env(), cwd=run_cwd,
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
        test_cmd:      The test command (identical to the gate's ``command``).
                       Absolute references to the project root are redirected into
                       the sandbox; relative commands run with the sandbox root as
                       ``cwd``.  The default runner compiles it through the closed
                       grammar into structured argv (``shell=False``) and REFUSES
                       anything outside it.
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
