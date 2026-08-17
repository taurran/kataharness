"""truth_serum.py — Truth Serum v1's BLOCKING (gate-refusing) detectors: B1, B3, B5.

Detectors ATTEST and NARROW; judges judge.

Standing humility, stated wherever v1 is described (burn-02 meta-finding, verbatim):
*"the judgment+human layers found all of these; the automated mechanical gates found
none."*  Nothing in this module decides whether a repository is trustworthy.  Each
detector answers one narrow, mechanical question, refuses out loud when it cannot
answer it, and hands the residue to a judge.

Scope — transcribed from the trust-model DESIGN §3.1 table, never re-derived
--------------------------------------------------------------------------
* **B1 — stub-body AST scan.**  Pure AST predicate over ``graph_gen``'s tree-sitter
  spans (an artifact already generated); five syntactic families
  (``pass``-only / TODO-comment-only / ``raise NotImplementedError`` / log-only bodies /
  hardcoded-empty returns) in task-modified files; a match blocks unless the line
  carries a ``DEF-*`` reference (the D3b rule, §3.2).  Mechanical suppressors for
  legitimately-empty classes (ABC / protocol-handler / ``__init__.py`` detection) are
  explicit predicates; residual legitimacy judgment routes to the signal channel,
  never silently suppresses.
* **B3 — debt-marker-without-``DEF-*``.**  Any TBD/FIXME/XXX in a task-modified file is
  a BLOCKER unless the same line references formal follow-up (``DEF-*`` / issue ref) —
  the gsd D3b rule, adopted.
* **B5 — citation-existence resolver.**  Every ``file:line`` / wikilink citation in a
  gated artifact resolves (the ``check_wikilinks`` precedent); existence is MECH —
  **"support" stays judgment**, routed to grounding (DESIGN §4).

NOT here, and claimed by nobody in this module: **B2** (the silent-deferral three-way
join) is close-machinery's; **B4** (evidence identity) landed in wave 3
(``evidence_grammar`` / the extended ``evidence_is_current``); **B6** (the mutation-proof
re-run) is engine+gate work.  This module imports none of them and reimplements none of
them.

The anti-vacuity companion law (TM-D3) — every detector ships one
-----------------------------------------------------------------
A check that ran over nothing must report that it ran over nothing.  The forbidden
outcome is the silent one: a detector that shrugs at what it could not read and returns
"no findings" produces the exact false clean bill of health the detector exists to
prevent.  So each detector here carries its companion, and the companion's refusal is a
first-class verdict, not a logged warning:

===========  =====================================================================
Detector     REFUSES to certify when
===========  =====================================================================
B1           the graph artifact is absent / unreadable / internally inconsistent;
             the graph is **stale** against the files being graded (per-file hash
             or ``meta.repoHash``); a graded ``.py`` file is absent from the graph;
             a graded file is unreadable or unparseable; **zero functions scanned**.
B3           the modified-file set is empty (nothing scanned ⇒ nothing certified);
             a file in that set is unreadable.
B5           the artifact could not be read.  A **zero-candidate** artifact is
             reported as ``ZERO_CANDIDATE``, never as "all citations resolve".
===========  =====================================================================

The B1/B5 asymmetry on zero is transcribed from the DESIGN table, not invented here:
B1's companion is specified as *"refuses to certify a scan over zero functions"* (a
zero-function scan is a REFUSAL), while B5's is *"zero-candidate artifacts are reported
as zero-candidate"* (a valid zero, reported as a zero, and not a certification).

D-26 applied to this module's own code
--------------------------------------
The wave-3 lesson: *a property promised in a docstring but not enforced at the boundary*
is the defect shape this whole program exists to kill.  Every guarantee stated above is
enforced in code at the entry point of its detector and pinned by a test — the refusal
paths are ``return``-ed verdicts, not prose.  Where a limit could not be enforced, it is
stated below as a limit and pinned by a test that DEMONSTRATES the miss, rather than
described as if it were covered.

Honest limits (v1) — stated, not implied away
---------------------------------------------
1. **B1 detects the five DESIGN families and no others.**  In particular an
   ``...`` (Ellipsis) -only body is **not** in the v1 family set and is **not**
   detected.  Pinned by ``test_ellipsis_only_body_is_a_stated_miss``.
2. **B1's TODO-comment family reads raw source lines** inside the function span, because
   Python's ``ast`` discards comments.  The statement predicate is AST; the comment
   predicate is lexical.  A ``TODO`` inside a string literal on its own line inside an
   otherwise-empty body would be read as a comment-shaped marker.
3. **B3 matches uppercase ``TBD`` / ``FIXME`` / ``XXX`` on word boundaries only.**
   Lowercase spellings are not matched.  ``TODO`` is deliberately absent: the
   ``protocol/deferral.md`` rule names TBD/FIXME/XXX, and this module transcribes it.
4. **B3 covers the same-line BLOCKER rule ONLY — it is not a deferral entry-schema
   parse** (DEF-9's boundary, stated where DEF-9 asked for it).  B3 checks that a debt
   marker's own line carries a formal follow-up reference.  It does **not** verify that
   the referenced ``DEF-<n>`` exists in ``.planning/DEFERRED.md``, does not parse the
   ledger's heading grammar, and does not check required fields or closure discipline.
   A marker citing a wholly fictional ``DEF-9999`` is suppressed by B3.  The ledger
   parse is a separate, still-open piece of work.
5. **B5 proves existence, never support.**  A citation that resolves is a citation whose
   target file exists and whose line number is within that file.  Whether the cited line
   *supports the claim it is attached to* is judgment and is routed to grounding.
6. **B5 resolves wikilinks against a repo file index** (relative path, path without the
   ``.md`` suffix, bare stem, and skill-directory name).  An ambiguous stem resolves;
   this detector reports existence, not uniqueness.
7. **B1's file set is Python-only.**  Non-``.py`` modified files are outside its reach
   entirely; they are counted and reported, never silently dropped.

Exec safety
-----------
This module **spawns no subprocess and calls no ``eval``/``exec``**, by contract — it
reads files, parses them, and returns dataclasses.  It therefore adds **no row** to the
``protocol/exec-safety.md`` sink registry.  That absence is asserted mechanically by
``test_no_exec_sinks_anywhere_in_module`` (the ``evidence_grammar`` / ``drift_gate``
precedent), so the contract cannot rot into a comment.

Determinism (D172, the Determinism Doctrine)
--------------------------------------------
Same inputs ⇒ same bytes.  Every filesystem walk is sorted (law 2); no set or dict
iteration drives output order (law 3); ``to_json`` uses ``sort_keys=True`` (law 5); no
wall-clock stamp appears in any report (law 6); there is no randomness (law 9); and
every findings sort ends on an explicit total order (law 10).

Public API
----------
``scan_stub_bodies(repo_root, graph, modified_files)``  -> ``DetectorReport``  (B1)
``scan_debt_markers(repo_root, modified_files)``        -> ``DetectorReport``  (B3)
``resolve_citations(repo_root, artifact)``              -> ``DetectorReport``  (B5)
``run_blocking_detectors(...)``                         -> ``dict[str, DetectorReport]``
"""

from __future__ import annotations

import ast
import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# Hash parity with the ARTIFACT'S PRODUCER, deliberately.  ``meta.repoHash`` and every
# per-file ``hash`` in kata.graph.json are computed by these two functions; a local
# reimplementation that drifted by one byte would turn B1's staleness check into a
# liar that refuses fresh graphs (or, worse, certifies stale ones).  Importing the
# producer's own helpers is the correct reuse here.  Precedent for reaching into
# graph_gen's private helpers from a sibling: ``contract_gate.py:34``.
from graph_gen import _bytes_hash, _repo_hash

# ---------------------------------------------------------------------------
# The TM-D2 humility line — verbatim, and carried on every report this module emits
# ---------------------------------------------------------------------------

#: DESIGN §3.1, verbatim.  Rendered into every ``DetectorReport`` and every
#: ``summary()`` string so a consumer cannot quote a verdict without the caveat.
HUMILITY_LINE = "Detectors ATTEST and NARROW; judges judge."

# ---------------------------------------------------------------------------
# Verdicts
# ---------------------------------------------------------------------------

#: Findings exist; the gate must refuse.
VERDICT_BLOCK = "BLOCK"
#: Real inputs were scanned and no finding was raised.
VERDICT_PASS = "PASS"
#: The detector could not certify.  Absence of a precondition is never a pass.
VERDICT_REFUSE = "REFUSE"
#: Real inputs were scanned and contained zero candidates.  A valid zero, reported as
#: a zero — explicitly NOT "everything resolved" and explicitly not a certification.
VERDICT_ZERO_CANDIDATE = "ZERO_CANDIDATE"

VERDICTS = (VERDICT_BLOCK, VERDICT_PASS, VERDICT_REFUSE, VERDICT_ZERO_CANDIDATE)

#: Verdicts a gate must treat as "do not proceed".  ``ZERO_CANDIDATE`` is not blocking,
#: but it is not a certification either — a gate that needs a positive attestation must
#: require ``PASS`` explicitly rather than "not blocking".
BLOCKING_VERDICTS = (VERDICT_BLOCK, VERDICT_REFUSE)

# ---------------------------------------------------------------------------
# B1 — the five DESIGN §3.1 syntactic families (transcribed; this tuple is the set)
# ---------------------------------------------------------------------------

FAMILY_PASS_ONLY = "pass-only"
FAMILY_TODO_COMMENT_ONLY = "todo-comment-only"
FAMILY_RAISE_NOTIMPLEMENTED = "raise-notimplemented"
FAMILY_LOG_ONLY = "log-only"
FAMILY_HARDCODED_EMPTY_RETURN = "hardcoded-empty-return"

STUB_FAMILIES = (
    FAMILY_PASS_ONLY,
    FAMILY_TODO_COMMENT_ONLY,
    FAMILY_RAISE_NOTIMPLEMENTED,
    FAMILY_LOG_ONLY,
    FAMILY_HARDCODED_EMPTY_RETURN,
)

#: The ONLY mechanical suppressor classes B1 may apply (DESIGN §3.1 B1, PLAN E3).
#: Adding a class here is an ESCALATION, not a code change: E3 pins "new suppressor
#: classes => ESCALATE".  Anything a builder believes is legitimately empty but which
#: is not one of these three still BLOCKS, and routes to the signal channel.
SUPPRESSOR_CLASSES = ("init-module", "abstract-method", "protocol-handler")

#: Suspected-legitimacy classes that are NOT suppressors.  A finding tagged with one of
#: these BLOCKS exactly as it otherwise would AND emits a signal, so the judgment
#: "is this one legitimately empty?" is made by a judge with the fact in hand rather
#: than by this detector behind everyone's back (E3: never silently suppresses).
SIGNAL_CLASSES = ("overload-decorated", "unresolvable-class-base")

# ---------------------------------------------------------------------------
# Regexes (module-level: compiled once, and each one is part of the stated contract)
# ---------------------------------------------------------------------------

#: A formal follow-up reference, D3b: ``DEF-<n>`` on the marker's own line.
_DEF_REF = re.compile(r"\bDEF-\d+\b")
#: DESIGN B3 also admits an "issue ref" as formal follow-up.  Three explicit shapes.
_ISSUE_REF = re.compile(
    r"(?:\bGH-\d+\b)"
    r"|(?:(?<![\w#])#\d+\b)"
    r"|(?:https?://\S*/issues/\d+)"
)
#: B3's marker set, verbatim from protocol/deferral.md: TBD/FIXME/XXX.  Not TODO.
_DEBT_MARKER = re.compile(r"\b(TBD|FIXME|XXX)\b")
#: B1's TODO-comment family reads comment text; its marker set is wider than B3's
#: because the family is named "TODO-comment-only" in the DESIGN table.
_TODO_COMMENT = re.compile(r"#.*\b(TODO|TBD|FIXME|XXX)\b")
#: B5 file:line citations.  Requires a file extension so that prose like "§3.1:12"
#: or "DESIGN:14" is not mistaken for a path.  URLs are stripped before this runs.
_FILE_LINE = re.compile(r"(?<![\w./\\-])((?:[\w.\-]+[/\\])*[\w.\-]+\.[A-Za-z0-9]{1,8}):(\d+)(?!\d)")
#: B5 wikilinks — the ``check_wikilinks`` shape, with alias/anchor suffixes trimmed.
_WIKILINK = re.compile(r"\[\[([^\]\[|#]+)")
_URL = re.compile(r"https?://\S+")

#: Names whose method call makes a body "log-only".  Explicit predicate, not a guess.
_LOG_CALL_TAILS = frozenset(
    {"debug", "info", "warn", "warning", "error", "exception", "critical", "log"}
)
_LOG_CALL_ROOTS = frozenset(
    {"logging", "logger", "log", "_logger", "_log", "LOG", "LOGGER", "self"}
)
_LOG_BARE_CALLS = frozenset({"print"})

#: Directories never walked when building B5's resolution index or scanning a tree.
_SKIP_DIRS = frozenset({".git", ".venv", "__pycache__", "node_modules", ".mypy_cache",
                        ".pytest_cache", ".ruff_cache"})


class TruthSerumError(ValueError):
    """Raised for a caller error (a malformed argument), never for a detector finding.

    Detectors ATTEST and NARROW; judges judge. A *finding* is data returned in a
    ``DetectorReport``; an exception here means the caller handed this module something
    it may not accept at all (e.g. a traversal path).
    """


# ---------------------------------------------------------------------------
# Path guard — the ``..``-rejection guard family invariant (CWE-23)
# ---------------------------------------------------------------------------

def _guard_path(raw: str | Path) -> Path:
    """Reject a path-traversal component, then return the path unresolved.

    Family invariant (``tools/tests/test_path_guard_family.py``): raises ``ValueError``
    on any ``..`` component, accepts a clean relative path.  Deliberately does NOT
    ``.resolve()`` — callers join against an already-guarded repo root and containment
    is checked there, so resolving here would only smuggle in symlink surprises.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"path-traversal component '..' refused (CWE-23): {raw!r}")
    return p


def _guard_root(raw: str | Path) -> Path:
    """Guard and resolve a repo root."""
    return Path(_guard_path(raw)).resolve()


def _rel_posix(path: Path, root: Path) -> str:
    """Repo-relative POSIX form; falls back to the POSIX form of an outside path."""
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class Finding:
    """One mechanical observation, attributable to a file and a line.

    Detectors ATTEST and NARROW; judges judge. A ``Finding`` is an attested fact
    ("this line matched this predicate"), never a verdict about intent.
    """

    detector: str
    path: str
    line: int
    family: str
    message: str
    symbol: str | None = None

    def sort_key(self) -> tuple:
        """Explicit total order (Determinism Doctrine law 10 — ties never float)."""
        return (self.detector, self.path, self.line, self.family,
                self.symbol or "", self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "detector": self.detector,
            "family": self.family,
            "line": self.line,
            "message": self.message,
            "path": self.path,
            "symbol": self.symbol,
        }


@dataclass(frozen=True)
class DetectorReport:
    """A single detector's whole answer, including its refusal to answer.

    Detectors ATTEST and NARROW; judges judge.

    ``verdict`` is one of :data:`VERDICTS`.  ``candidates_scanned`` is the count of
    things the detector actually looked at — it is the number that makes a
    ``ZERO_CANDIDATE`` honest and a ``PASS`` meaningful, so it is always reported.
    ``refusal_reason`` is populated **iff** the verdict is ``REFUSE``.
    """

    detector: str
    verdict: str
    findings: tuple[Finding, ...] = ()
    signals: tuple[Finding, ...] = ()
    candidates_scanned: int = 0
    files_scanned: tuple[str, ...] = ()
    refusal_reason: str | None = None
    notes: tuple[str, ...] = ()
    humility: str = field(default=HUMILITY_LINE)

    def __post_init__(self) -> None:
        # D-26: the invariants this class's docstring promises are enforced HERE, at
        # the boundary, not described above and hoped for.
        if self.verdict not in VERDICTS:
            raise TruthSerumError(f"unknown verdict {self.verdict!r}; legal: {VERDICTS}")
        if (self.verdict == VERDICT_REFUSE) != (self.refusal_reason is not None):
            raise TruthSerumError(
                "refusal_reason must be set iff verdict is REFUSE "
                f"(verdict={self.verdict!r}, refusal_reason={self.refusal_reason!r})"
            )
        if self.verdict == VERDICT_BLOCK and not self.findings:
            raise TruthSerumError("verdict BLOCK requires at least one finding")
        if self.verdict == VERDICT_PASS and self.findings:
            raise TruthSerumError("verdict PASS is impossible with findings present")
        if self.verdict == VERDICT_ZERO_CANDIDATE and self.candidates_scanned != 0:
            raise TruthSerumError(
                f"verdict ZERO_CANDIDATE requires candidates_scanned == 0, "
                f"got {self.candidates_scanned}"
            )
        if self.humility != HUMILITY_LINE:
            raise TruthSerumError("the TM-D2 humility line is not overridable")

    @property
    def blocking(self) -> bool:
        """True iff a gate must refuse to proceed on this report."""
        return self.verdict in BLOCKING_VERDICTS

    @property
    def certifies(self) -> bool:
        """True iff this report is a positive attestation.

        Only ``PASS`` certifies.  ``ZERO_CANDIDATE`` deliberately does not: nothing was
        found because there was nothing to find, which is a fact about the input, not a
        clean bill of health.
        """
        return self.verdict == VERDICT_PASS

    def summary(self) -> str:
        """One-line human-readable rendering.  Carries the TM-D2 line, always."""
        if self.verdict == VERDICT_REFUSE:
            head = f"{self.detector} REFUSES to certify: {self.refusal_reason}"
        elif self.verdict == VERDICT_ZERO_CANDIDATE:
            head = (
                f"{self.detector} scanned {len(self.files_scanned)} file(s) and found "
                f"ZERO candidates — reported as zero-candidate, NOT as 'all resolve'"
            )
        elif self.verdict == VERDICT_BLOCK:
            head = (
                f"{self.detector} BLOCKS: {len(self.findings)} finding(s) over "
                f"{self.candidates_scanned} candidate(s)"
            )
        else:
            head = (
                f"{self.detector} PASS: 0 findings over {self.candidates_scanned} "
                f"candidate(s) in {len(self.files_scanned)} file(s)"
            )
        if self.signals:
            head += f"; {len(self.signals)} signal(s) routed to the signal channel"
        return f"{head}. {self.humility}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidates_scanned": self.candidates_scanned,
            "detector": self.detector,
            "files_scanned": list(self.files_scanned),
            "findings": [f.to_dict() for f in self.findings],
            "humility": self.humility,
            "notes": list(self.notes),
            "refusal_reason": self.refusal_reason,
            "signals": [s.to_dict() for s in self.signals],
            "verdict": self.verdict,
        }

    def to_json(self) -> str:
        """Byte-stable JSON rendering (Determinism Doctrine law 5: ``sort_keys=True``)."""
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2)


def _refuse(detector: str, reason: str, *, files: tuple[str, ...] = (),
            notes: tuple[str, ...] = ()) -> DetectorReport:
    """Build the anti-vacuity refusal (TM-D3).  Absence is never rendered as a pass."""
    return DetectorReport(
        detector=detector,
        verdict=VERDICT_REFUSE,
        refusal_reason=reason,
        files_scanned=files,
        notes=notes,
    )


def _settle(detector: str, findings: list[Finding], signals: list[Finding],
            candidates: int, files: tuple[str, ...], *,
            zero_candidate_is_refusal: bool, zero_candidate_reason: str,
            notes: tuple[str, ...] = ()) -> DetectorReport:
    """Turn a completed scan into its verdict.  The one place a non-refusal is minted."""
    if candidates == 0:
        if zero_candidate_is_refusal:
            return _refuse(detector, zero_candidate_reason, files=files, notes=notes)
        return DetectorReport(
            detector=detector,
            verdict=VERDICT_ZERO_CANDIDATE,
            signals=tuple(sorted(signals, key=Finding.sort_key)),
            candidates_scanned=0,
            files_scanned=files,
            notes=notes,
        )
    ordered = tuple(sorted(findings, key=Finding.sort_key))
    return DetectorReport(
        detector=detector,
        verdict=VERDICT_BLOCK if ordered else VERDICT_PASS,
        findings=ordered,
        signals=tuple(sorted(signals, key=Finding.sort_key)),
        candidates_scanned=candidates,
        files_scanned=files,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Shared input normalisation
# ---------------------------------------------------------------------------

def _normalise_modified(modified_files: Any, root: Path) -> tuple[str, ...]:
    """Normalise the task-modified file set to sorted, guarded, repo-relative POSIX.

    Sorted at the boundary (Determinism Doctrine law 2) and de-duplicated through a
    sorted list rather than set iteration (law 3).
    """
    if modified_files is None:
        return ()
    if isinstance(modified_files, (str, Path)):
        raise TruthSerumError(
            "modified_files must be an iterable of paths, not a single path"
        )
    out: list[str] = []
    for raw in modified_files:
        p = _guard_path(raw)
        rel = _rel_posix(root / p if not p.is_absolute() else p, root)
        if rel not in out:
            out.append(rel)
    return tuple(sorted(out))


def _read_text(path: Path) -> str | None:
    """Read UTF-8 text, or None if the file cannot be read/decoded.

    ``None`` is never treated as "empty" by any caller in this module — it is the
    trigger for a refusal (TM-D3).
    """
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


# ===========================================================================
# B1 — stub-body AST scan over graph_gen's tree-sitter spans
# ===========================================================================

def _decorator_names(node: ast.AST) -> tuple[str, ...]:
    """Dotted names of a def's decorators, best-effort and purely syntactic."""
    out: list[str] = []
    for dec in getattr(node, "decorator_list", []):
        target = dec.func if isinstance(dec, ast.Call) else dec
        name = _dotted_name(target)
        if name:
            out.append(name)
    return tuple(out)


def _dotted_name(node: ast.AST | None) -> str | None:
    """``a.b.c`` for Name/Attribute/Subscript chains; None when not statically a name."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    if isinstance(node, ast.Subscript):
        return _dotted_name(node.value)
    return None


def _class_suppressor(cls: ast.ClassDef | None) -> str | None:
    """Explicit mechanical suppressor derived from an enclosing class, or None.

    Two of the three DESIGN-sanctioned classes live here (``abstract-method`` via an
    ABC base/metaclass, ``protocol-handler`` via a Protocol base).  Every predicate is
    a literal name comparison — no heuristics, no "looks abstract to me".
    """
    if cls is None:
        return None
    for base in cls.bases:
        name = _dotted_name(base)
        if name in ("ABC", "abc.ABC"):
            return "abstract-method"
        if name in ("Protocol", "typing.Protocol", "t.Protocol", "typing_extensions.Protocol"):
            return "protocol-handler"
    for kw in cls.keywords:
        if kw.arg == "metaclass" and _dotted_name(kw.value) in ("ABCMeta", "abc.ABCMeta"):
            return "abstract-method"
    for dec in _decorator_names(cls):
        if dec in ("runtime_checkable", "typing.runtime_checkable"):
            return "protocol-handler"
    return None


def _class_signal(cls: ast.ClassDef | None) -> str | None:
    """A base this module could NOT statically resolve — suspected, never suppressed."""
    if cls is None:
        return None
    for base in cls.bases:
        if _dotted_name(base) is None:
            return "unresolvable-class-base"
    return None


def _suppressor_for(path: str, fn: ast.AST, cls: ast.ClassDef | None) -> str | None:
    """The ONE explicit-suppressor entry point (DESIGN §3.1 B1; PLAN E3 pins the set)."""
    if Path(path).name == "__init__.py":
        return "init-module"
    for dec in _decorator_names(fn):
        if dec in ("abstractmethod", "abc.abstractmethod",
                   "abstractproperty", "abc.abstractproperty"):
            return "abstract-method"
    return _class_suppressor(cls)


def _signal_for(fn: ast.AST, cls: ast.ClassDef | None) -> str | None:
    """A suspected-legitimacy class.  Routes to the signal channel; never suppresses."""
    for dec in _decorator_names(fn):
        if dec in ("overload", "typing.overload", "typing_extensions.overload"):
            return "overload-decorated"
    return _class_signal(cls)


def _body_residue(fn: ast.AST) -> list[ast.stmt]:
    """The body with a leading docstring removed.

    A docstring is prelude, not implementation: a body that is *only* a docstring has an
    empty residue and is classified by the ``pass-only`` family (the residue carries no
    executable statement).  This is a property of that family, not a sixth family.
    """
    body = list(getattr(fn, "body", []))
    if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant) \
            and isinstance(body[0].value.value, str):
        return body[1:]
    return body


def _is_empty_constant(node: ast.expr | None) -> bool:
    """True for the hardcoded-empty return values: None/''/0/False and empty displays."""
    if node is None:
        return True
    if isinstance(node, ast.Constant):
        return node.value in (None, "", 0, False) and not isinstance(node.value, float)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        return not node.elts
    if isinstance(node, ast.Dict):
        return not node.keys
    return False


def _is_log_call(stmt: ast.stmt) -> bool:
    """True iff the statement is a bare call to an explicitly-named logging surface."""
    if not isinstance(stmt, ast.Expr) or not isinstance(stmt.value, ast.Call):
        return False
    name = _dotted_name(stmt.value.func)
    if name is None:
        return False
    if name in _LOG_BARE_CALLS:
        return True
    parts = name.split(".")
    if len(parts) < 2:
        return False
    return parts[-1] in _LOG_CALL_TAILS and parts[0] in _LOG_CALL_ROOTS


def _raises_not_implemented(stmt: ast.stmt) -> bool:
    exc = getattr(stmt, "exc", None)
    if not isinstance(stmt, ast.Raise) or exc is None:
        return False
    target = exc.func if isinstance(exc, ast.Call) else exc
    return _dotted_name(target) in ("NotImplementedError", "NotImplemented")


def _classify_stub(fn: ast.AST, lines: list[str]) -> tuple[str, int] | None:
    """Classify a function body into one of the five DESIGN families.

    Returns ``(family, line)`` where ``line`` is the OFFENDING line — the line the
    ``DEF-*`` same-line suppression is checked against — or None when the body is not a
    stub under the v1 family set.

    Classification order is fixed (determinism: a body matching two families always
    reports the same one).
    """
    residue = _body_residue(fn)
    def_line = fn.lineno

    # 1. raise NotImplementedError
    if len(residue) == 1 and _raises_not_implemented(residue[0]):
        return FAMILY_RAISE_NOTIMPLEMENTED, residue[0].lineno

    # 2. hardcoded-empty return
    if len(residue) == 1 and isinstance(residue[0], ast.Return) \
            and _is_empty_constant(residue[0].value):
        return FAMILY_HARDCODED_EMPTY_RETURN, residue[0].lineno

    # 3. log-only body (one or more bare logging calls and nothing else)
    if residue and all(_is_log_call(s) for s in residue):
        return FAMILY_LOG_ONLY, residue[0].lineno

    # Families 4 and 5 both require an empty-or-`pass` residue.
    if residue and not all(isinstance(s, ast.Pass) for s in residue):
        return None

    # 4. TODO-comment-only — the comment predicate is lexical (ast drops comments).
    end = getattr(fn, "end_lineno", def_line) or def_line
    for idx in range(def_line, min(end, len(lines))):
        if _TODO_COMMENT.search(lines[idx]):
            return FAMILY_TODO_COMMENT_ONLY, idx + 1

    # 5. pass-only (including the docstring-only body: empty residue)
    return FAMILY_PASS_ONLY, (residue[0].lineno if residue else def_line)


def _load_graph(graph: Any) -> tuple[dict | None, str | None]:
    """Load the graph artifact from a dict or a path.  Returns ``(graph, refusal)``."""
    if graph is None:
        return None, "graph artifact is absent (TM-D3: absence is a refusal, not a pass)"
    if isinstance(graph, dict):
        return graph, None
    try:
        raw = Path(_guard_path(graph)).read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return None, f"graph artifact unreadable at {graph!r}: {exc.__class__.__name__}"
    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"graph artifact is not valid JSON at {graph!r}: {exc.msg}"
    if not isinstance(loaded, dict):
        return None, f"graph artifact is not a JSON object at {graph!r}"
    return loaded, None


def scan_stub_bodies(
    repo_root: str | Path,
    graph: dict | str | Path | None,
    modified_files: Any,
) -> DetectorReport:
    """B1 — stub-body AST scan over ``graph_gen``'s tree-sitter spans.

    Detectors ATTEST and NARROW; judges judge.

    A function in a task-modified ``.py`` file whose body matches one of the five
    DESIGN §3.1 families BLOCKS, unless the offending line carries a ``DEF-*``
    reference (the D3b rule) or one of the three explicit mechanical suppressors
    applies (``__init__.py`` / abstract method / protocol handler).  Residual
    legitimacy judgment is **routed to the signal channel** — a suspected-legitimacy
    finding still blocks and additionally appears in ``signals`` (E3: this detector
    never silently suppresses, and a new suppressor class is an escalation, not a
    patch).

    Anti-vacuity companion (TM-D3) — REFUSES to certify when the graph is absent,
    unreadable, internally inconsistent, or **stale** against the graded files; when a
    graded ``.py`` file is missing from the graph, unreadable, or unparseable; or when
    the scan would cover **zero functions**.

    Parameters
    ----------
    repo_root: repository root the modified paths are relative to.
    graph: the ``kata.graph.json`` dict, or a path to it.  Required — B1 is defined
        over the graph's spans and refuses without them.
    modified_files: the task-modified file set (iterable of paths).
    """
    det = "B1"
    root = _guard_root(repo_root)
    rels = _normalise_modified(modified_files, root)

    loaded, refusal = _load_graph(graph)
    if refusal is not None:
        return _refuse(det, refusal)
    assert loaded is not None  # narrowed by the refusal above

    meta = loaded.get("meta")
    if not isinstance(meta, dict) or not isinstance(meta.get("repoHash"), str):
        return _refuse(det, "graph artifact carries no meta.repoHash (cannot prove freshness)")
    nodes = loaded.get("nodes")
    if not isinstance(nodes, list):
        return _refuse(det, "graph artifact carries no nodes list")

    file_hashes: dict[str, str] = {}
    for n in nodes:
        if isinstance(n, dict) and n.get("kind") == "file":
            p, h = n.get("path"), n.get("hash")
            if isinstance(p, str) and isinstance(h, str):
                file_hashes[p] = h
    if _repo_hash(file_hashes) != meta["repoHash"]:
        return _refuse(
            det,
            "graph meta.repoHash does not match its own file-node hashes "
            "(the artifact is internally inconsistent; refusing rather than trusting it)",
        )

    py_rels = tuple(r for r in rels if r.endswith(".py"))
    skipped = tuple(r for r in rels if not r.endswith(".py"))
    notes: tuple[str, ...] = ()
    if skipped:
        notes += (
            f"{len(skipped)} non-.py modified file(s) are outside B1's reach "
            f"and were NOT scanned: {', '.join(skipped)}",
        )

    # Freshness + readability, per graded file.  Every one of these is a refusal.
    sources: dict[str, str] = {}
    for rel in py_rels:
        if rel not in file_hashes:
            return _refuse(
                det,
                f"graded file {rel!r} is absent from the graph artifact "
                "(the graph does not cover the code being graded)",
                files=py_rels, notes=notes,
            )
        try:
            data = (root / rel).read_bytes()
        except OSError as exc:
            return _refuse(det, f"graded file {rel!r} is unreadable: {exc.__class__.__name__}",
                           files=py_rels, notes=notes)
        if _bytes_hash(data) != file_hashes[rel]:
            return _refuse(
                det,
                f"graph is STALE for {rel!r} (recorded hash does not match the file on disk)",
                files=py_rels, notes=notes,
            )
        try:
            sources[rel] = data.decode("utf-8")
        except UnicodeDecodeError:
            return _refuse(det, f"graded file {rel!r} is not valid UTF-8", files=py_rels, notes=notes)

    # The graph decides WHAT is scanned; the AST decides WHETHER it is a stub.
    graph_spans: dict[str, set[tuple[str, int]]] = {}
    for n in nodes:
        if not isinstance(n, dict) or n.get("kind") != "symbol":
            continue
        if n.get("symKind") not in ("function", "method"):
            continue
        p, name, span = n.get("path"), n.get("name"), n.get("span")
        if isinstance(p, str) and isinstance(name, str) and isinstance(span, list) and span:
            graph_spans.setdefault(p, set()).add((name, int(span[0])))

    findings: list[Finding] = []
    signals: list[Finding] = []
    candidates = 0

    for rel in py_rels:  # already sorted by _normalise_modified
        src = sources[rel]
        lines = src.splitlines()
        try:
            tree = ast.parse(src)
        except SyntaxError as exc:
            return _refuse(det, f"graded file {rel!r} does not parse: line {exc.lineno}",
                           files=py_rels, notes=notes)
        in_graph = graph_spans.get(rel, set())

        # Walk with the enclosing class carried down, in source order (deterministic).
        for fn, cls in _iter_functions(tree):
            if (fn.name, fn.lineno) not in in_graph:
                # The graph and the AST disagree about what exists in a file whose hash
                # they agree on.  That is a broken precondition, not a function to skip.
                return _refuse(
                    det,
                    f"graph/AST disagreement in {rel!r}: {fn.name} at line {fn.lineno} "
                    "is not a graph symbol (refusing rather than scanning a partial set)",
                    files=py_rels, notes=notes,
                )
            candidates += 1
            classified = _classify_stub(fn, lines)
            if classified is None:
                continue
            family, line = classified
            source_line = lines[line - 1] if 0 < line <= len(lines) else ""
            if _DEF_REF.search(source_line):
                continue  # D3b: a formal follow-up on the marker's own line suppresses
            suppressor = _suppressor_for(rel, fn, cls)
            if suppressor is not None:
                continue  # explicit mechanical suppressor — one of exactly three
            finding = Finding(
                detector=det, path=rel, line=line, family=family, symbol=fn.name,
                message=(f"stub body ({family}) with no DEF-* reference on line {line}"),
            )
            findings.append(finding)
            signal_class = _signal_for(fn, cls)
            if signal_class is not None:
                # E3: suspected legitimacy NEVER suppresses.  It blocks AND signals.
                signals.append(Finding(
                    detector=det, path=rel, line=line, family=signal_class, symbol=fn.name,
                    message=("suspected-legitimacy class routed to the signal channel; "
                             "the finding still BLOCKS (E3: new suppressor classes escalate)"),
                ))

    return _settle(
        det, findings, signals, candidates, py_rels,
        zero_candidate_is_refusal=True,
        zero_candidate_reason=(
            "zero functions scanned — nothing was examined, so nothing is certified "
            "(TM-D3 anti-vacuity companion)"
        ),
        notes=notes,
    )


def _iter_functions(tree: ast.Module):
    """Yield ``(function_node, enclosing_ClassDef_or_None)`` in source order.

    Explicit recursion rather than ``ast.walk`` because the enclosing class must travel
    with each function (the ABC/Protocol suppressors need it) and because ``ast.walk``'s
    breadth-first order is not source order.
    """
    def _rec(node: ast.AST, cls: ast.ClassDef | None):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                yield child, cls
                yield from _rec(child, None)  # nested defs lose the class context
            elif isinstance(child, ast.ClassDef):
                yield from _rec(child, child)
            else:
                yield from _rec(child, cls)

    yield from _rec(tree, None)


# ===========================================================================
# B3 — debt-marker-without-DEF-*
# ===========================================================================

def scan_debt_markers(repo_root: str | Path, modified_files: Any) -> DetectorReport:
    """B3 — a TBD/FIXME/XXX in a task-modified file without same-line formal follow-up.

    Detectors ATTEST and NARROW; judges judge.

    The ``protocol/deferral.md`` rule, transcribed: *"A debt marker (TBD/FIXME/XXX) in
    gated work without a ``DEF-*`` reference on the same line is a BLOCKER."*  The
    reference must be on the marker's own line, because a marker whose follow-up lives
    in a nearby paragraph is one refactor away from being an orphan.

    **DEF-9 boundary, stated where DEF-9 asked for it.**  B3 covers the same-line
    BLOCKER rule and NOTHING ELSE.  It is **not** a deferral entry-schema parse: it does
    not open ``.planning/DEFERRED.md``, does not check that the cited ``DEF-<n>``
    exists, does not validate the heading grammar, the required What/Why/Provenance/
    Owed-to fields, the ``accepted_by``/``accepted_at`` approval record, or the closure
    discipline.  A marker citing a wholly fictional ``DEF-9999`` is suppressed here.
    Ledger conformance remains Honor-system until a ledger parser lands (DEF-9).

    Anti-vacuity companion (TM-D3) — REFUSES when the modified-file set is empty
    (nothing scanned ⇒ nothing certified) or when a file in the set cannot be read.
    """
    det = "B3"
    root = _guard_root(repo_root)
    rels = _normalise_modified(modified_files, root)

    if not rels:
        return _refuse(
            det,
            "the task-modified file set is EMPTY — nothing was scanned, so nothing is "
            "certified (TM-D3 anti-vacuity companion)",
        )

    findings: list[Finding] = []
    scanned_lines = 0
    for rel in rels:
        text = _read_text(root / rel)
        if text is None:
            return _refuse(
                det,
                f"modified file {rel!r} is unreadable or not UTF-8 — refusing to certify "
                "a scan that skipped part of its own input",
                files=rels,
            )
        for idx, line in enumerate(text.splitlines(), start=1):
            scanned_lines += 1
            marker = _DEBT_MARKER.search(line)
            if marker is None:
                continue
            if _DEF_REF.search(line) or _ISSUE_REF.search(line):
                continue  # formal follow-up on the marker's own line — D3b satisfied
            findings.append(Finding(
                detector=det, path=rel, line=idx, family=f"debt-marker:{marker.group(1)}",
                message=(f"debt marker {marker.group(1)} with no DEF-* or issue "
                         "reference on the same line (protocol/deferral.md D3b)"),
            ))

    return _settle(
        det, findings, [], scanned_lines, rels,
        zero_candidate_is_refusal=False,
        zero_candidate_reason="",
    )


# ===========================================================================
# B5 — citation-existence resolver
# ===========================================================================

def _repo_index(root: Path) -> tuple[frozenset[str], frozenset[str]]:
    """Build the wikilink resolution index: (relative paths, resolvable bare names).

    Generalises the ``check_wikilinks`` precedent (``validate_skills.py:1042``), which
    resolved wikilinks against ``_valid_skill_targets()``.  Here the target set is the
    repo's own files: relative path, path minus a ``.md`` suffix, bare stem, and the
    directory name of any ``skills/*/<name>/SKILL.md``.

    Sorted walk (Determinism Doctrine law 2); the returned frozensets are membership
    tests only and never drive output order (law 3).
    """
    rel_paths: list[str] = []
    names: list[str] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if any(part in _SKIP_DIRS for part in rel.parts):
            continue
        posix = rel.as_posix()
        rel_paths.append(posix)
        names.append(rel.stem)
        if posix.endswith(".md"):
            names.append(posix[: -len(".md")])
        if rel.name == "SKILL.md" and len(rel.parts) >= 2:
            names.append(rel.parts[-2])
    return frozenset(rel_paths), frozenset(names)


def resolve_citations(repo_root: str | Path, artifact: str | Path) -> DetectorReport:
    """B5 — every ``file:line`` / wikilink citation in a gated artifact must resolve.

    Detectors ATTEST and NARROW; judges judge.

    **Existence is MECH; support is judgment.**  A citation resolves when its target
    file exists inside the repo and, for a ``file:line`` citation, when the line number
    falls inside that file.  Whether the cited line actually *supports the claim it is
    attached to* is not decided here and never will be — that is routed to grounding
    (DESIGN §4).  A report of "all citations resolve" is therefore a statement about
    files, not about truth.

    Anti-vacuity companion (TM-D3) — REFUSES to certify an artifact it could not read.
    An artifact containing **zero** citations returns ``ZERO_CANDIDATE``, reported as a
    zero-candidate artifact and never as "all citations resolve"; ``certifies`` is False
    for that verdict, so a consumer cannot launder absence into attestation.
    """
    det = "B5"
    root = _guard_root(repo_root)
    if not root.is_dir():
        return _refuse(det, f"repo root {str(root)!r} is not a directory")

    art_path = Path(_guard_path(artifact))
    if not art_path.is_absolute():
        art_path = root / art_path
    art_rel = _rel_posix(art_path, root)
    text = _read_text(art_path)
    if text is None:
        return _refuse(
            det,
            f"artifact {art_rel!r} could not be read — refusing to certify citations in "
            "a file this detector never saw (TM-D3 anti-vacuity companion)",
        )

    scrubbed = _URL.sub(" ", text)
    findings: list[Finding] = []
    candidates = 0
    rel_paths, names = _repo_index(root)

    for lineno, line in enumerate(scrubbed.splitlines(), start=1):
        for m in _FILE_LINE.finditer(line):
            candidates += 1
            raw_path, raw_line = m.group(1).replace("\\", "/"), int(m.group(2))
            reason = _file_line_failure(root, raw_path, raw_line)
            if reason is not None:
                findings.append(Finding(
                    detector=det, path=art_rel, line=lineno, family="file-line-citation",
                    symbol=f"{raw_path}:{raw_line}",
                    message=f"citation does not resolve: {reason}",
                ))
        for m in _WIKILINK.finditer(line):
            candidates += 1
            target = m.group(1).strip()
            if target and target not in rel_paths and target not in names:
                findings.append(Finding(
                    detector=det, path=art_rel, line=lineno, family="wikilink-citation",
                    symbol=target,
                    message=f"citation does not resolve: no repo file matches [[{target}]]",
                ))

    return _settle(
        det, findings, [], candidates, (art_rel,),
        zero_candidate_is_refusal=False,
        zero_candidate_reason="",
        notes=("existence is MECH; whether a resolved citation SUPPORTS its claim is "
               "judgment, routed to grounding (DESIGN §4) and not decided here.",),
    )


def _file_line_failure(root: Path, raw_path: str, raw_line: int) -> str | None:
    """None when the ``file:line`` citation resolves; otherwise the failure reason."""
    try:
        rel = _guard_path(raw_path)
    except ValueError:
        return "path contains a '..' traversal component (CWE-23)"
    if rel.is_absolute():
        return "citation is an absolute path; repo-relative citations only"
    target = root / rel
    if not target.is_file():
        return f"no such file in the repo: {rel.as_posix()}"
    if raw_line < 1:
        return f"line {raw_line} is not a valid 1-indexed line number"
    text = _read_text(target)
    if text is None:
        return f"cited file {rel.as_posix()} is unreadable"
    count = len(text.splitlines())
    if raw_line > count:
        return f"line {raw_line} is past end of file ({rel.as_posix()} has {count} lines)"
    return None


# ===========================================================================
# The v1 blocking set, run together
# ===========================================================================

def run_blocking_detectors(
    repo_root: str | Path,
    graph: dict | str | Path | None,
    modified_files: Any,
    artifacts: Any = (),
) -> dict[str, DetectorReport]:
    """Run B1, B3 and B5 and return their reports keyed by detector id.

    Detectors ATTEST and NARROW; judges judge.  This function composes; it does not
    gate.  A caller decides what a ``BLOCK`` or a ``REFUSE`` means for its gate — see
    :attr:`DetectorReport.blocking` and :attr:`DetectorReport.certifies`.

    B5 keys are ``B5:<artifact-rel-path>``, one per artifact, so a per-artifact refusal
    is never collapsed into another artifact's pass.  Artifacts are processed in sorted
    order (Determinism Doctrine law 2).
    """
    root = _guard_root(repo_root)
    out: dict[str, DetectorReport] = {
        "B1": scan_stub_bodies(root, graph, modified_files),
        "B3": scan_debt_markers(root, modified_files),
    }
    if isinstance(artifacts, (str, Path)):
        raise TruthSerumError("artifacts must be an iterable of paths, not a single path")
    for art in sorted(str(a) for a in artifacts):
        report = resolve_citations(root, art)
        out[f"B5:{report.files_scanned[0] if report.files_scanned else art}"] = report
    return out
