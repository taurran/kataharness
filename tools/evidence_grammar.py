"""evidence_grammar.py — the CLOSED per-task ``evidence:`` grammar (RS-H1 / TM-F1 / R-M9).

The DECLARATION-side grammar for the per-task ``evidence:`` field of a frozen PLAN
(DESIGN §3.5 + §5.1).  Every plan item declares its completion evidence; this module
is the one place that declaration is parsed, guarded, and compiled — and the one place
a declaration is REFUSED.

Registered contract
-------------------
The four ``evidence_grammar`` rows in ``protocol/exec-safety.md`` (the sink registry)
were written BEFORE this module existed — the deliberate inversion of the D111
whack-a-mole order.  This module is built to those rows; any divergence is a contract
violation to resolve out loud, never a row to quietly rewrite.  The rows in force:

* ``artifact:`` — **spawns no subprocess, by contract.**  An ``artifact:`` value is
  NEVER executed.  It is a repo-relative path, existence/wiring-checked only, guarded
  by the ``_guard_path`` pattern (CWE-23: rejects any ``..`` component, does not
  resolve; live precedents ``tools/benchmark_def.py:85``, ``tools/benchmark.py:82``).
* ``test:`` — a ``fullmatch``-anchored node-ID grammar REUSING the ``_guard_node_id``
  grammar (``tools/benchmark_def.py:805``, ``tools/benchmark.py:106``): non-empty, no
  leading ``-`` path segment (pytest-flag injection), no ``..`` component (CWE-23, via
  ``_guard_path``), ``path::name`` shape, and resolved-containment under the repo root.
  Compiled to the fixed structured argv ``["python", "-m", "pytest", <node-id>]``;
  ``shell=False``; **no shell, ever**.  The node-ID is a positional DATA operand, never
  the program (``argv[0]``).
* ``probe:`` — the value is a **NAME, never a command**, resolved against the committed
  registry ``tools/probe_registry.json`` whose argv templates are repo-committed and
  reviewed like code.  ``shell=False``; list-argv only.  **An unregistered name is
  REFUSED (fail closed, D136)** — never fall back to executing the name, never
  auto-register on first use.

**A freeform command string is REFUSED.**  Not warned about, not documentation-only-
but-tolerated: a value that does not ``fullmatch`` one of the three forms fails the
check, and the plan does not freeze.

Trust domain: **external.**  An LLM-authored field of a frozen PLAN is external-trust —
freeze approval is a review of *intent*, not a promotion to operator trust.

The D-3 argv reconciliation (recorded here, per the conductor ruling)
---------------------------------------------------------------------
DESIGN §3.5 pins the ``test:`` compile target as ``[python, -m, pytest, <id>]``.  Every
LIVE sink in this repo instead invokes pytest through uv (``mutation_check.run_named_test``
uses ``["uv","run","pytest", …]``; ``scripts/gauntlet.py`` uses ``("uv","run","pytest", …)``),
because a bare ``python -m pytest`` misses the uv-managed venv.  The conductor's W2 ruling:

    the grammar compiles per DESIGN; the EXECUTION environment may wrap the compiled
    argv in the uv runner as an environment detail, recorded in the module contract —
    divergence resolved visibly at build, not silently.

So: :func:`compile_declaration` emits **exactly** the DESIGN argv, and the uv wrap is a
SEPARATE, explicit, opt-in step — :func:`uv_wrapped_argv` — that a caller applies at the
execution boundary and nowhere else.  Nothing in this module wraps implicitly.  A reader
comparing this module against DESIGN §3.5 sees the pinned argv; a reader comparing it
against the live runners sees the named wrap.  Neither has to guess.

Sibling grammar, NOT this one (verify-before-reuse, ``protocol/reuse-claims.md``)
--------------------------------------------------------------------------------
``tools/mutation_run.py`` landed its OWN closed grammar in wave 1 (``_compile_test_cmd``,
``_parse_runner``, ``_guard_node_id``, ``_split_cd_prefix``).  That is the **sink-side
runner grammar** — *which runner shapes may execute* at a subprocess boundary that
already exists.  This module is the **declaration-side grammar** — *which forms may be
declared* in a frozen PLAN.  Different boundary, different problem, different inputs
(a shell-ish command string vs. a three-form tagged declaration).  They are siblings,
not one implementation; this module claims none of that work and rebuilds none of it.

The one thing genuinely shared is the *pattern* of the three node-ID checks, which all
three live sites (``benchmark.py:106``, ``benchmark_def.py:805``, ``mutation_run.py:261``)
already carry as their own local copy for the same reason: each is the last guard before
its own boundary, and a cross-module import would make one module's refusal depend on
another module's import graph.  :func:`_guard_node_id` here is the fourth local copy, held
to the same three checks, deliberately — not a claimed reuse of any of them.

Determinism (Determinism Doctrine — same inputs ⇒ same bytes)
------------------------------------------------------------
Pure functions over their arguments; no clock, no randomness, no environment reads, no
filesystem discovery order.  The registry is read from an explicit path and its entries
are canonicalized (``sorted`` names, tuple argvs); every map this module returns is built
in a stated order.  Path guarding never resolves the declared path into the result — the
guard uses resolution only for the containment CHECK, so a compiled artifact path is the
declared repo-relative path on every machine.

STDLIB only.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# The closed form set
# ---------------------------------------------------------------------------

#: The three legal forms.  Closed — there is no fourth, and no escape hatch.
FORMS: tuple[str, ...] = ("artifact", "test", "probe")

#: ``fullmatch``-anchored tagged-declaration grammar.  The prefix is one of the three
#: forms; the value is the remainder.  ``fullmatch`` (never ``search``/``match``) is what
#: makes ``test:foo.py::bar; rm -rf /`` fail at the OUTER layer before any inner guard —
#: a newline or a trailing shell chain cannot ride along on a well-formed prefix.
_DECLARATION_RE = re.compile(r"(artifact|test|probe):(\S+)")

#: Characters that only have meaning to a shell.  None may appear anywhere in a
#: declaration or in a registry argv element — their presence means the author assumed
#: shell semantics this grammar does not provide (mirrors ``mutation_run._SHELL_METACHARS``
#: in intent; kept local for the same reason ``_guard_node_id`` is).
#:
#: Deliberately NOT in the set: ``[`` ``]`` ``{`` ``}`` — a parametrized pytest node-ID
#: (``test_x.py::test_y[case-1]``) is a legitimate declaration, and refusing it would push
#: authors toward a coarser, less honest evidence node.  Brackets never reach a shell here
#: (argv only, ``shell=False``), so admitting them costs nothing the other guards defend.
#: Backslash IS in the set: on POSIX ``..\\..`` survives :func:`_guard_path` (which splits
#: on ``/``), so refusing it is what makes the traversal guard cross-platform.
_SHELL_METACHARS: frozenset[str] = frozenset("&|;<>$`\n\r\t*?()!~'\"\\")

#: The committed probe registry, relative to this module's directory.
_DEFAULT_REGISTRY_NAME = "probe_registry.json"

#: Registry schema version this module reads.
_REGISTRY_VERSION = 1

#: Legal ``status`` values for a registry entry.  ``declared-before-active`` is the
#: exec-safety "registered before active" shape: the NAME resolves (so a plan citing it
#: passes the grammar) while the argv target does not exist yet.  An executor MUST NOT
#: read a missing target as a pass — that is the consuming wave's obligation, stated here
#: so it cannot be assumed away.
_REGISTRY_STATUSES: frozenset[str] = frozenset({"active", "declared-before-active"})

#: A probe program name.  ``argv[0]`` is the PROGRAM — a bare name only: no path
#: separators, no leading ``-``, no traversal, nothing a shell would expand.
_PROGRAM_RE = re.compile(r"[A-Za-z0-9_][A-Za-z0-9._-]*")

#: A registered probe name.  Deliberately narrow: lowercase words joined by ``-``.
_PROBE_NAME_RE = re.compile(r"[a-z0-9]+(-[a-z0-9]+)*")

#: The exact argv prefix DESIGN §3.5 pins for the ``test:`` form.  Held as a constant so
#: the pin is greppable and a change to it is a visible diff against the DESIGN clause.
_PYTEST_ARGV_PREFIX: tuple[str, ...] = ("python", "-m", "pytest")

#: The uv runner prefix — the EXECUTION-environment wrap (D-3), applied only by
#: :func:`uv_wrapped_argv`, never by :func:`compile_declaration`.
_UV_RUN_PREFIX: tuple[str, ...] = ("uv", "run")


class EvidenceGrammarError(ValueError):
    """A declaration (or registry entry) that the closed grammar REFUSES.

    Subclasses ``ValueError`` so existing fail-closed call sites that catch
    ``ValueError`` (the house shape for every guard in ``tools/``) keep working, while a
    caller that wants to distinguish a grammar refusal from an I/O failure can.
    """


# ---------------------------------------------------------------------------
# Guards — the CWE-23 path guard and the node-ID grammar
# ---------------------------------------------------------------------------


def _guard_path(raw: str | Path) -> Path:
    """Reject paths containing ``..`` traversal (CWE-23).  Does NOT resolve.

    The live precedent pattern (``tools/benchmark_def.py:85``, ``tools/benchmark.py:82``),
    held locally for the same last-guard-before-the-boundary reason those two are.

    Args:
        raw: The candidate path (str or Path).

    Returns:
        A Path object for the accepted path.

    Raises:
        EvidenceGrammarError: if *raw* contains a ``..`` path component.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise EvidenceGrammarError(
            f"evidence_grammar: refusing path with '..' traversal (CWE-23): {str(raw)!r}"
        )
    return p


def _guard_repo_relative(rel: str, *, what: str) -> None:
    """Reject anything that is not a clean repo-relative path.

    ``Path.is_absolute()`` alone is NOT enough and the difference is a real cross-platform
    hole: ``PureWindowsPath("/etc/passwd").is_absolute()`` is ``False`` (drive-relative),
    and ``PurePosixPath("C:/x")`` is a perfectly ordinary relative directory named ``C:``.
    So the same declaration would be judged differently on two machines — which the
    Determinism Doctrine forbids independently of the security question.  Both shapes are
    refused explicitly here, on every platform.

    Raises:
        EvidenceGrammarError: on an absolute, root-anchored, or drive-qualified value.
    """
    if rel.startswith("/"):
        raise EvidenceGrammarError(
            f"evidence_grammar: {what} must be repo-relative, got a root-anchored "
            f"path: {rel!r}"
        )
    p = Path(rel)
    if p.is_absolute():
        raise EvidenceGrammarError(
            f"evidence_grammar: {what} must be repo-relative, got {rel!r}"
        )
    if p.parts and ":" in p.parts[0]:
        raise EvidenceGrammarError(
            f"evidence_grammar: {what} must be repo-relative, got a drive-qualified "
            f"path: {rel!r}"
        )


def _guard_contained(rel: str | Path, repo_root: Path, *, what: str) -> None:
    """Containment: ``repo_root / rel`` must resolve under the resolved *repo_root*.

    Blocks symlink escape, absolute declared paths, and the OS-specific corner cases that
    survive the ``..`` check (a Windows drive-relative path, a UNC root).  Resolution is
    used for the CHECK only — the caller keeps the declared repo-relative value, so the
    compiled result is byte-identical on every machine (Determinism Doctrine).

    Raises:
        EvidenceGrammarError: if the path escapes the repo root.
    """
    resolved_root = Path(repo_root).resolve()
    resolved = (resolved_root / Path(rel)).resolve()
    if resolved != resolved_root and not resolved.is_relative_to(resolved_root):
        raise EvidenceGrammarError(
            f"evidence_grammar: refusing {what} {str(rel)!r} — it resolves outside the repo "
            f"root {str(resolved_root)!r}. An evidence declaration addresses this repo only. STOP."
        )


def _guard_node_id(node_id: str, repo_root: Path | None) -> str:
    """Validate a pytest node-ID before it is compiled into argv.

    The ``_guard_node_id`` grammar, held to the same checks as the three live copies
    (``benchmark.py:106``, ``benchmark_def.py:805``, ``mutation_run.py:261``):

    1. Non-empty string.
    2. Does not start with ``-`` (a node-ID that reads as a pytest CLI flag).
    3. ``path::name`` shape — must contain ``::``.
    4. No ``..`` component in the path part (CWE-23, via :func:`_guard_path`).
    5. No leading ``-`` on the FIRST path segment (flag injection through a path).
    6. Containment: ``repo_root / <path part>`` resolves under *repo_root* (skipped when
       *repo_root* is ``None``; checks 1-5 still apply).

    The test NAME part after ``::`` is checked for shell metacharacters by the caller's
    outer declaration grammar (``\\S+`` + the metachar sweep), so a name cannot smuggle a
    separator into argv even though argv never reaches a shell.

    Args:
        node_id: The candidate node-ID string.
        repo_root: Repo root the node-ID's path part is relative to, or ``None``.

    Returns:
        *node_id* unchanged if it passes every check.

    Raises:
        EvidenceGrammarError: on any violation (fail-closed — a bad ID never reaches argv).
    """
    if not isinstance(node_id, str) or not node_id:
        raise EvidenceGrammarError(
            f"evidence_grammar: node-ID must be a non-empty string, got {node_id!r}"
        )
    if node_id.startswith("-"):
        raise EvidenceGrammarError(
            f"evidence_grammar: node-ID must not start with '-' (pytest-flag injection "
            f"risk in argv list): {node_id!r}"
        )
    if "::" not in node_id:
        raise EvidenceGrammarError(
            f"evidence_grammar: node-ID must be 'path::name' shape (must contain '::', "
            f"e.g. 'tools/tests/test_x.py::test_name'): {node_id!r}"
        )
    sep = node_id.rfind("::")
    rel_path = node_id[:sep]
    if not rel_path:
        raise EvidenceGrammarError(
            f"evidence_grammar: node-ID has an empty path part: {node_id!r}"
        )
    if not node_id[sep + 2:]:
        raise EvidenceGrammarError(
            f"evidence_grammar: node-ID has an empty test-name part: {node_id!r}"
        )
    guarded = _guard_path(rel_path)
    _guard_repo_relative(rel_path, what="node-ID path")
    parts = guarded.parts
    if parts and parts[0].startswith("-"):
        raise EvidenceGrammarError(
            f"evidence_grammar: refusing node-ID with a leading '-' path segment: {node_id!r}"
        )
    if repo_root is not None:
        _guard_contained(rel_path, repo_root, what="node-ID path")
    return node_id


# ---------------------------------------------------------------------------
# The parsed + compiled shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class EvidenceDeclaration:
    """One parsed ``evidence:`` declaration — form + value, nothing executable yet."""

    form: str
    value: str
    raw: str


@dataclass(frozen=True)
class CompiledEvidence:
    """A declaration compiled to its execution-or-inspection shape.

    Exactly one of *path* / *argv* is populated, by form:

    * ``artifact`` -> *path* set, *argv* ``None``.  **Never executed** — the ``None`` argv
      is the contract, not an omission.
    * ``test``     -> *argv* = ``("python", "-m", "pytest", <node-id>)``, *path* ``None``.
    * ``probe``    -> *argv* = the registry template, *path* ``None``; *cwd* is the
      registry entry's repo-relative working directory.

    ``argv`` is a tuple so a compiled result cannot be mutated between guard and use.
    Every consumer runs it with ``shell=False``.  There is no field carrying a command
    string, deliberately: there is nothing for a caller to hand to a shell.
    """

    form: str
    raw: str
    path: Path | None = None
    argv: tuple[str, ...] | None = None
    cwd: str | None = None
    #: Probe form only — ``active`` or ``declared-before-active`` (see ``_REGISTRY_STATUSES``).
    status: str | None = None

    @property
    def is_executable(self) -> bool:
        """True when this form compiles to argv at all (``artifact`` never does)."""
        return self.argv is not None


@dataclass(frozen=True)
class ProbeEntry:
    """One committed probe-registry entry: a NAME bound to a fixed argv template."""

    name: str
    argv: tuple[str, ...]
    cwd: str
    description: str
    status: str


# ---------------------------------------------------------------------------
# Parsing — the outer closed grammar
# ---------------------------------------------------------------------------


def parse_declaration(raw: Any) -> EvidenceDeclaration:
    """Parse one ``evidence:`` declaration string against the closed three-form grammar.

    Anything that is not ``artifact:<v>`` / ``test:<v>`` / ``probe:<v>`` — a freeform
    command string above all — is REFUSED here, before any inner guard runs.

    Args:
        raw: The declaration as authored in the PLAN frontmatter.

    Returns:
        The parsed :class:`EvidenceDeclaration`.

    Raises:
        EvidenceGrammarError: on any non-conforming value.
    """
    if not isinstance(raw, str):
        raise EvidenceGrammarError(
            f"evidence_grammar: an evidence declaration must be a string, got "
            f"{type(raw).__name__}: {raw!r}"
        )
    if not raw:
        raise EvidenceGrammarError("evidence_grammar: empty evidence declaration")
    if raw != raw.strip():
        raise EvidenceGrammarError(
            f"evidence_grammar: evidence declaration has leading/trailing whitespace "
            f"(exact match required): {raw!r}"
        )
    bad = sorted({ch for ch in raw if ch in _SHELL_METACHARS})
    if bad:
        raise EvidenceGrammarError(
            f"evidence_grammar: refusing evidence declaration containing shell "
            f"metacharacter(s) {bad!r} — the three forms are not commands: {raw!r}"
        )
    m = _DECLARATION_RE.fullmatch(raw)
    if not m:
        raise EvidenceGrammarError(
            f"evidence_grammar: REFUSED — {raw!r} is not one of the three legal evidence "
            f"forms. The grammar is CLOSED: 'artifact:<repo-relative-path>' | "
            f"'test:<pytest-node-id>' | 'probe:<registered-name>'. A freeform command "
            f"string is never evidence and is never executed (protocol/exec-safety.md)."
        )
    return EvidenceDeclaration(form=m.group(1), value=m.group(2), raw=raw)


# ---------------------------------------------------------------------------
# The probe registry
# ---------------------------------------------------------------------------


def default_registry_path(tools_dir: str | Path | None = None) -> Path:
    """Path to the committed probe registry (``tools/probe_registry.json``)."""
    base = Path(__file__).parent if tools_dir is None else Path(tools_dir)
    return base / _DEFAULT_REGISTRY_NAME


def _guard_probe_argv(name: str, argv: Any) -> tuple[str, ...]:
    """Validate one registry argv template: a list of plain strings, argv[0] a program.

    The registry is repo-committed and code-reviewed, so its templates are INTERNAL
    trust — but "reviewed like code" only holds if a malformed entry fails loudly rather
    than reaching a subprocess, so the shape is checked on every load.
    """
    if not isinstance(argv, list) or not argv:
        raise EvidenceGrammarError(
            f"evidence_grammar: probe {name!r} argv must be a non-empty LIST of strings "
            f"(structured argv, never a command string), got {argv!r}"
        )
    for element in argv:
        if not isinstance(element, str) or not element:
            raise EvidenceGrammarError(
                f"evidence_grammar: probe {name!r} argv element must be a non-empty "
                f"string, got {element!r}"
            )
        bad = sorted({ch for ch in element if ch in _SHELL_METACHARS})
        if bad:
            raise EvidenceGrammarError(
                f"evidence_grammar: probe {name!r} argv element {element!r} contains shell "
                f"metacharacter(s) {bad!r} — templates are argv, never shell strings"
            )
        if ".." in Path(element).parts:
            raise EvidenceGrammarError(
                f"evidence_grammar: probe {name!r} argv element {element!r} contains a "
                f"'..' traversal component (CWE-23)"
            )
    if not _PROGRAM_RE.fullmatch(argv[0]):
        raise EvidenceGrammarError(
            f"evidence_grammar: probe {name!r} argv[0] must be a bare program name "
            f"(no path separators, no leading '-'), got {argv[0]!r}"
        )
    return tuple(argv)


def load_probe_registry(registry_path: str | Path | None = None) -> dict[str, ProbeEntry]:
    """Load + validate the committed probe registry.

    Fail-closed at every step: an absent, unreadable, non-JSON, wrong-version, or
    malformed registry RAISES.  There is no permissive empty-registry fallback — an empty
    registry would silently turn every ``probe:`` declaration into a refusal that looks
    like a plan defect instead of a tooling defect.

    Args:
        registry_path: Explicit registry path, or ``None`` for the committed default.

    Returns:
        ``{name: ProbeEntry}``, insertion-ordered by sorted name (Determinism Doctrine
        law 3 — a dict this module returns never inherits file order).

    Raises:
        EvidenceGrammarError: on any load or schema violation.
    """
    path = default_registry_path() if registry_path is None else Path(registry_path)
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise EvidenceGrammarError(
            f"evidence_grammar: cannot read the committed probe registry at {str(path)!r} "
            f"({exc}) — refusing to resolve any probe: declaration. Resolve manually."
        ) from exc
    try:
        data = json.loads(text)
    except json.JSONDecodeError as exc:
        raise EvidenceGrammarError(
            f"evidence_grammar: probe registry at {str(path)!r} is not valid JSON — {exc}"
        ) from exc
    if not isinstance(data, dict):
        raise EvidenceGrammarError(
            f"evidence_grammar: probe registry at {str(path)!r} must be a JSON object"
        )
    if data.get("version") != _REGISTRY_VERSION:
        raise EvidenceGrammarError(
            f"evidence_grammar: probe registry version must be {_REGISTRY_VERSION}, got "
            f"{data.get('version')!r} — refusing to read an unknown registry schema."
        )
    probes = data.get("probes")
    if not isinstance(probes, dict):
        raise EvidenceGrammarError(
            f"evidence_grammar: probe registry at {str(path)!r} has no 'probes' object"
        )

    entries: dict[str, ProbeEntry] = {}
    for name in sorted(probes):
        entry = probes[name]
        if not _PROBE_NAME_RE.fullmatch(name):
            raise EvidenceGrammarError(
                f"evidence_grammar: probe name {name!r} is not a legal registered name "
                f"(pattern {_PROBE_NAME_RE.pattern!r})"
            )
        if not isinstance(entry, dict):
            raise EvidenceGrammarError(
                f"evidence_grammar: probe {name!r} entry must be an object, got {entry!r}"
            )
        argv = _guard_probe_argv(name, entry.get("argv"))
        cwd = entry.get("cwd")
        if not isinstance(cwd, str) or not cwd:
            raise EvidenceGrammarError(
                f"evidence_grammar: probe {name!r} needs a non-empty repo-relative 'cwd' "
                f"(stated, never inferred — a probe run from the wrong directory is a "
                f"different probe), got {cwd!r}"
            )
        _guard_path(cwd)
        if Path(cwd).is_absolute():
            raise EvidenceGrammarError(
                f"evidence_grammar: probe {name!r} 'cwd' must be repo-relative, got {cwd!r}"
            )
        status = entry.get("status")
        if status not in _REGISTRY_STATUSES:
            raise EvidenceGrammarError(
                f"evidence_grammar: probe {name!r} 'status' must be one of "
                f"{sorted(_REGISTRY_STATUSES)}, got {status!r}"
            )
        description = entry.get("description")
        if not isinstance(description, str) or not description:
            raise EvidenceGrammarError(
                f"evidence_grammar: probe {name!r} needs a non-empty 'description' — an "
                f"argv template nobody can read is not reviewable"
            )
        entries[name] = ProbeEntry(
            name=name, argv=argv, cwd=cwd, description=description, status=status
        )
    return entries


# ---------------------------------------------------------------------------
# Compilation
# ---------------------------------------------------------------------------


def compile_declaration(
    decl: EvidenceDeclaration | str,
    *,
    repo_root: str | Path | None = None,
    registry: dict[str, ProbeEntry] | None = None,
) -> CompiledEvidence:
    """Compile one declaration to its path / argv / registry-resolved shape.

    Grammar + guards only — **nothing is executed here, and nothing is checked for
    existence here**.  Existence is a CLOSE-time question (:func:`artifact_exists`), not a
    freeze-time one: a frozen PLAN legitimately declares evidence for tasks whose files do
    not exist yet, which is the entire point of declaring evidence at freeze.

    Args:
        decl: A parsed declaration, or a raw string (parsed here).
        repo_root: Repo root for the containment checks.  ``None`` skips containment
            (the ``..`` / leading-``-`` / shape guards still apply) — for callers
            validating a plan they do not have checked out.
        registry: Pre-loaded probe registry; ``None`` loads the committed default, and
            only for a ``probe:`` declaration (an artifact/test-only plan never needs the
            registry file to exist).

    Returns:
        The :class:`CompiledEvidence`.

    Raises:
        EvidenceGrammarError: on any grammar, guard, or registry-resolution failure.
    """
    if isinstance(decl, str):
        decl = parse_declaration(decl)
    root = None if repo_root is None else Path(repo_root)

    if decl.form == "artifact":
        path = _guard_path(decl.value)
        _guard_repo_relative(decl.value, what="artifact path")
        if path.parts and path.parts[0].startswith("-"):
            raise EvidenceGrammarError(
                f"evidence_grammar: refusing artifact path with a leading '-' segment: "
                f"{decl.value!r}"
            )
        if root is not None:
            _guard_contained(path, root, what="artifact path")
        # argv stays None — an artifact is NEVER executed (protocol/exec-safety.md).
        return CompiledEvidence(form="artifact", raw=decl.raw, path=path)

    if decl.form == "test":
        node_id = _guard_node_id(decl.value, root)
        return CompiledEvidence(
            form="test", raw=decl.raw, argv=(*_PYTEST_ARGV_PREFIX, node_id)
        )

    # probe — the value is a NAME, never a command.
    if not _PROBE_NAME_RE.fullmatch(decl.value):
        raise EvidenceGrammarError(
            f"evidence_grammar: probe name {decl.value!r} is not a legal registered name "
            f"(pattern {_PROBE_NAME_RE.pattern!r}) — a probe declaration names a registry "
            f"entry, it is never a command."
        )
    probes = load_probe_registry() if registry is None else registry
    entry = probes.get(decl.value)
    if entry is None:
        raise EvidenceGrammarError(
            f"evidence_grammar: REFUSED — probe {decl.value!r} is not in the committed "
            f"registry (known: {sorted(probes)}). An unregistered probe is never executed "
            f"as a command and is never auto-registered (fail closed, D136); add it to "
            f"tools/probe_registry.json in a reviewed commit."
        )
    return CompiledEvidence(
        form="probe", raw=decl.raw, argv=entry.argv, cwd=entry.cwd, status=entry.status
    )


def uv_wrapped_argv(argv: tuple[str, ...] | list[str]) -> tuple[str, ...]:
    """The D-3 EXECUTION-environment wrap — explicit, separate, never implicit.

    :func:`compile_declaration` emits the argv DESIGN §3.5 pins
    (``["python","-m","pytest",<id>]``).  The live sinks in this repo run pytest through
    uv, because a bare ``python -m pytest`` misses the uv-managed venv
    (``mutation_check.run_named_test``; ``scripts/gauntlet.py``).  A caller executing a
    compiled ``test:`` argv in THIS repo's environment applies this wrap at the execution
    boundary; a caller in a different environment does not.

    That split is the whole point: the DESIGN clause stays literally implemented, and the
    environment detail stays visible as an environment detail instead of silently editing
    the pinned compile target.

    Returns:
        ``("uv", "run", *argv)`` — still structured argv, still ``shell=False``.
    """
    return (*_UV_RUN_PREFIX, *tuple(argv))


def artifact_exists(compiled: CompiledEvidence, repo_root: str | Path) -> bool:
    """CLOSE-time existence check for an ``artifact:`` form (never an execution).

    Raises:
        EvidenceGrammarError: if *compiled* is not an ``artifact`` form — the caller has
            confused the forms, which must be loud.
    """
    if compiled.form != "artifact" or compiled.path is None:
        raise EvidenceGrammarError(
            f"evidence_grammar: artifact_exists is for the 'artifact' form only, got "
            f"{compiled.form!r}"
        )
    return (Path(repo_root) / compiled.path).exists()


# ---------------------------------------------------------------------------
# Plan-level check (R-M9 / TM-F1)
# ---------------------------------------------------------------------------


def check_evidence_map(
    evidence: Any,
    task_ids: set[str],
    *,
    repo_root: str | Path | None = None,
    registry: dict[str, ProbeEntry] | None = None,
) -> dict[str, tuple[EvidenceDeclaration, ...]]:
    """Grammar-check a whole PLAN ``evidence:`` map against its task set (TM-F1 / R-M9).

    Fail-closed on all four defect shapes:

    1. no ``evidence:`` map at all,
    2. a task in *task_ids* with no declaration (**no plan item freezes without its
       completion-evidence declaration**),
    3. a declaration that does not fullmatch the closed grammar (a freeform command
       string above all), or that fails an inner guard,
    4. an evidence key naming a task that does not exist — a typo here silently leaves a
       REAL task undeclared, so it is a defect in its own right.

    Args:
        evidence: The raw ``evidence:`` value from PLAN frontmatter.
        task_ids: The authoritative task set (``kata_restore.parse_plan_tasks``).
        repo_root: Repo root for containment checks; ``None`` skips containment.
        registry: Pre-loaded probe registry, or ``None`` to load the committed default
            lazily (only if a ``probe:`` declaration is present).

    Returns:
        ``{task_id: (EvidenceDeclaration, ...)}`` — keys in sorted order, declarations in
        authored order (the authored order is data; the map order is ours to make
        deterministic).

    Raises:
        EvidenceGrammarError: on any of the four shapes above.
    """
    if evidence is None:
        raise EvidenceGrammarError(
            "evidence_grammar: frozen PLAN has no per-task 'evidence:' frontmatter map — "
            "no plan item freezes without its completion-evidence declaration (TM-F1). "
            "Refusing to certify an undeclared plan."
        )
    if not isinstance(evidence, dict):
        raise EvidenceGrammarError(
            f"evidence_grammar: PLAN 'evidence:' must be a map of task-id -> declaration "
            f"list, got {type(evidence).__name__}"
        )

    unknown = sorted(str(k) for k in evidence if str(k) not in task_ids)
    if unknown:
        raise EvidenceGrammarError(
            f"evidence_grammar: PLAN 'evidence:' declares evidence for task-id(s) "
            f"{unknown} that are not in the plan's task set — a mistyped key silently "
            f"leaves a real task undeclared. Resolve manually."
        )

    missing = sorted(t for t in task_ids if not evidence.get(t))
    if missing:
        raise EvidenceGrammarError(
            f"evidence_grammar: task(s) {missing} have no 'evidence:' declaration — no "
            f"plan item freezes without its completion-evidence declaration (TM-F1/R-M9)."
        )

    probes = registry
    out: dict[str, tuple[EvidenceDeclaration, ...]] = {}
    for task_id in sorted(task_ids):
        raw_list = evidence[task_id]
        if isinstance(raw_list, str):
            raise EvidenceGrammarError(
                f"evidence_grammar: task {task_id!r} evidence must be a LIST of "
                f"declarations, got a bare string {raw_list!r}"
            )
        if not isinstance(raw_list, list):
            raise EvidenceGrammarError(
                f"evidence_grammar: task {task_id!r} evidence must be a list, got "
                f"{type(raw_list).__name__}"
            )
        parsed: list[EvidenceDeclaration] = []
        for raw in raw_list:
            try:
                decl = parse_declaration(raw)
                if decl.form == "probe" and probes is None:
                    probes = load_probe_registry()
                compile_declaration(decl, repo_root=repo_root, registry=probes)
            except EvidenceGrammarError as exc:
                raise EvidenceGrammarError(
                    f"evidence_grammar: task {task_id!r}: {exc}"
                ) from exc
            parsed.append(decl)
        out[task_id] = tuple(parsed)
    return out
