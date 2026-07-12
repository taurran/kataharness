"""contract_gate.py — Freeze/Float M1-P2 final-gate re-derivation (decision code).

The P2 final gate that INDEPENDENTLY re-derives contract-edge soundness from
git-durable trailers + the frozen PLAN's ``builds_against`` — mutation-provable
decision code (D136; sanctioned as a new module by DESIGN Amendment #2 #3 — the
IaC-gate independent-re-derivation pattern, relocated out of prose). It composes
the pure ``contract_edges`` engine and the ``kata_restore`` git-trailer parsers;
it owns no state and holds no cache.

Fail-closed everywhere (M1-L9): every function that consumes trailers/edges RAISES
on a malformed structure, a git error, or an unresolvable scan bound rather than
returning a silent permissive result — a gate that swallows an error to a ``{}``
or ``[]`` would vacuously PASS the coverage audit (the exact defect this module
exists to prevent). NO ``except`` anywhere catches-and-continues a decision path:
raises from the engine and the parsers PROPAGATE to the orchestrator, which maps
them to NEEDS_WORK (DESIGN P2 obligation iii).

BC (M1-L7): a plan declaring no ``builds_against`` edge yields a vacuous PASS and
the orchestrator writes no artifact — every surface no-ops.
"""

from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Union

import tree_sitter_python as tsp
from tree_sitter import Language, Parser

import contract_edges as ce
from graph_gen import _module_to_path, _node_text
from kata_restore import (
    _KATA_INVALIDATED_PREFIX_RE,
    _KATA_INVALIDATED_RE,
    _KATA_SUPERSEDE_PREFIX_RE,
    _KATA_SUPERSEDE_RE,
    parse_supersede_trailers,
)

_PY_LANG = Language(tsp.language())
_PARSER = Parser(_PY_LANG)

# The one contract-namespace prefix (posix) a dangling import must target to be a
# gate finding — imports outside contracts/ are the provider/dependent's own tree.
_CONTRACTS_PREFIX = "contracts/"


# ---------------------------------------------------------------------------
# pinned_contracts — the frozen PLAN's contract → pin map (fail-closed)
# ---------------------------------------------------------------------------


def pinned_contracts(builds_against: object) -> dict[str, str]:
    """Return ``{contractId: pinnedHash}`` from a frozen PLAN's ``builds_against``.

    RAISES ``ValueError`` on any malformed edge (bad top-level shape or bad
    ``<id>@<hash>`` grammar, via the ``contract_edges`` canonical validators) and
    on CONFLICTING pins for a single id — one contract, one pin (two tasks pinning
    the same contract to different hashes is an authoring error, never silently
    resolved). A well-formed empty map returns ``{}`` (vacuous, BC).
    """
    ce._validate_shape(builds_against)  # raises on bad top-level shape (M1-L9)
    pins: dict[str, str] = {}
    for _task, edges in builds_against.items():
        for entry in edges:
            cid, h = ce._parse_edge(entry)  # raises on bad grammar (M1-L9)
            if set(cid) == {"."}:
                # Sweep C4: "." / ".." pass the edge grammar but escape the
                # contracts/ namespace when joined as a path — reject at the
                # choke point (authoring error, never silently resolved).
                raise ValueError(
                    f"degenerate contract id {cid!r} — a dot-only id escapes "
                    f"the contracts/ namespace (M1-L9)"
                )
            if cid in pins and pins[cid] != h:
                raise ValueError(
                    f"conflicting pins for contract {cid!r}: {pins[cid]!r} vs {h!r} "
                    f"— one contract, one pin (M1-L1)"
                )
            pins[cid] = h
    return pins


# ---------------------------------------------------------------------------
# _scan_integration_commits — commit-DELIMITED bounded scan (gate semantics)
# ---------------------------------------------------------------------------


def _scan_integration_commits(
    repo_root: str,
    integration_branch: str,
    plan_path: Union[str, Path],
) -> list[list[str]]:
    """Return per-commit body line-lists of THIS run's integration commits, newest-first.

    Commit-DELIMITED (R1): ``_scan_integration_commit_bodies``'s flat ``%B`` stream
    carries NO commit boundaries — "same commit" is unrecoverable from it, which the
    F7 temporal-coverage clause requires. This scan uses
    ``git log --format=%x00%H%n%B`` and splits on the NUL sentinel so each element of
    the returned list is exactly one commit's body lines; commit_index 0 = newest.
    The ``%H`` first line guarantees every commit — including an EMPTY-body one —
    occupies its own index slot (a bare ``%x00%B`` would collapse consecutive
    empty-body commits and corrupt the temporal ordering); it is stripped from the
    returned body lines. git refuses a literal NUL in a commit message, so the frame
    is unbreakable (a raw-object NUL only truncates ``%B``, reducing coverage —
    fail-closed).

    Same fork-point bounding as ``_scan_integration_commit_bodies`` (the most recent
    integration commit that touched the frozen PLAN). **Gate semantics (R8, M1-L9):**
    an unresolvable fork-point RAISES ``ValueError`` (the restore parser's degraded
    unbounded fallback is over-dispatch-safe but NOT audit-safe — prior-run trailers
    for reused contract ids would corrupt coverage); a git error RAISES ``ValueError``.
    """
    root = Path(repo_root).resolve()
    if plan_path is None:
        raise ValueError(
            "contract_gate: plan_path is required to bound the integration scan "
            "(M1-L9/R8) — refusing an unbounded audit that could read prior-run "
            "trailers. Resolve manually."
        )

    plan_abs = Path(plan_path).resolve()
    try:
        plan_spec = str(plan_abs.relative_to(root))
    except ValueError:
        plan_spec = str(plan_abs)

    # Resolve fork-point: most recent commit on integration_branch that touched the
    # frozen PLAN (committed before the run started). A git error or an empty result
    # both RAISE (gate semantics — never fall back to an unbounded scan).
    # Determinism pins (DET-02/DET-03, DETERMINISM-DOCTRINE law 1/5): the single-
    # pathspec shape activates an operator `log.follow=true`, which follows renames
    # to an OLDER commit — a wrong fork point silently ingests prior-run trailers;
    # `log.showSignature=false` keeps gpg: lines out of the parsed %H stdout;
    # `core.quotepath=off` for path-output symmetry with the other pinned calls.
    try:
        fp = subprocess.run(
            [
                "git",
                "-c", "log.follow=false",
                "-c", "log.showSignature=false",
                "-c", "core.quotepath=off",
                "log", "-1", "--format=%H", integration_branch, "--", plan_spec,
            ],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        raise ValueError(
            f"contract_gate: git error resolving plan fork-point for {plan_spec!r} on "
            f"{integration_branch!r} — the audit cannot bound its scan (M1-L9). "
            f"Resolve manually. ({exc})"
        ) from exc
    fork_point = fp.stdout.strip()
    if not fork_point:
        raise ValueError(
            f"contract_gate: cannot resolve the plan fork-point for {plan_spec!r} on "
            f"{integration_branch!r} (the frozen PLAN is not in this branch's history) "
            f"— refusing an unbounded audit (M1-L9/R8). The orchestrator must commit "
            f"the frozen PLAN to the integration branch at freeze. Resolve manually."
        )

    # Bounded, commit-delimited scan of THIS run's commits (after plan-freeze).
    # `log.showSignature=false` is load-bearing (DET-03): a signed commit under an
    # operator `log.showSignature=true` injects gpg: lines into the parsed stdout,
    # silently shifting commit_index — the temporal-invalidation comparison would
    # read the WRONG commit ordering. `core.quotepath=off` for symmetry.
    try:
        result = subprocess.run(
            [
                "git",
                "-c", "log.showSignature=false",
                "-c", "core.quotepath=off",
                "log", f"{fork_point}..{integration_branch}",
                "--format=%x00%H%n%B", "--",
            ],
            cwd=str(root),
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, OSError) as exc:
        raise ValueError(
            f"contract_gate: git error scanning integration commits on "
            f"{integration_branch!r} (M1-L9). Resolve manually. ({exc})"
        ) from exc

    commits: list[list[str]] = []
    for chunk in result.stdout.split("\x00"):
        if not chunk:
            continue  # leading empty element before the first NUL sentinel
        lines = chunk.splitlines()
        # lines[0] is the commit SHA (the index-slot guarantee); the rest is %B.
        commits.append(lines[1:])
    return commits


# ---------------------------------------------------------------------------
# parse_trailer_events — commit-indexed supersede/invalidated events
# ---------------------------------------------------------------------------


def parse_trailer_events(
    repo_root: str,
    integration_branch: str,
    plan_path: Union[str, Path],
) -> list[tuple[int, str, str, str]]:
    """Return ``(commit_index, kind, id, hash|"")`` events, newest-first.

    ``kind`` ∈ ``{"supersede", "invalidated"}``; ``commit_index`` 0 = newest (from
    ``_scan_integration_commits``); supersede hashes are lowercased (matching
    ``contract_edges._EDGE_RE``'s lowercase-hex pin); invalidated events carry ``""``
    (the id is the task-id). Reuses the ``kata_restore`` trailer grammar + the P1
    prefix-detectors so a malformed-looking trailer line (key matches, grammar
    doesn't) is surfaced with a loud NOTE — never silently swallowed (R7 parity,
    M1-L9). Raises from the scan (unresolvable fork-point / git error) PROPAGATE —
    this function never returns a permissive ``[]`` on error.
    """
    commits = _scan_integration_commits(repo_root, integration_branch, plan_path)
    events: list[tuple[int, str, str, str]] = []
    for idx, body_lines in enumerate(commits):
        for line in body_lines:
            ms = _KATA_SUPERSEDE_RE.match(line)
            if ms:
                events.append((idx, "supersede", ms.group(1), ms.group(2).lower()))
                continue
            if _KATA_SUPERSEDE_PREFIX_RE.match(line):
                print(
                    "NOTE: contract_gate: malformed Kata-Supersede trailer "
                    f"{line.strip()!r} — expected '<contractId>@<8-64 hex>'; this "
                    "supersede is INVISIBLE to the coverage audit. The M1-L8 "
                    "surface-drift check is the backstop for the unauthorized "
                    "change itself. Resolve manually.",
                    flush=True,
                )
                continue
            mi = _KATA_INVALIDATED_RE.match(line)
            if mi:
                events.append((idx, "invalidated", mi.group(1), ""))
                continue
            if _KATA_INVALIDATED_PREFIX_RE.match(line):
                print(
                    "NOTE: contract_gate: malformed Kata-Invalidated trailer "
                    f"{line.strip()!r} — cannot recover the task-id; this "
                    "invalidation is INVISIBLE to the coverage audit and the "
                    "affected task may under-dispatch. Resolve manually.",
                    flush=True,
                )
    return events


# ---------------------------------------------------------------------------
# dangling_contract_imports — NEW raw-import scan (F6; NOT a graph_gen reuse)
# ---------------------------------------------------------------------------


def _raw_import_modules(source_bytes: bytes) -> list[str]:
    """Collect the RAW (base) dotted module names imported by a file.

    Reuses the ``graph_gen`` tree-sitter parser + import-node walk PATTERN but emits
    the raw module names ONLY — the ``from X import name`` NAMES are never expanded
    to paths (R2: base-module existence). ``import a.b`` / ``import a.b as c`` →
    ``"a.b"``; ``from a.b import c`` → ``"a.b"`` (never ``a.b.c``).
    """
    tree = _PARSER.parse(source_bytes)
    mods: list[str] = []

    def _walk(node) -> None:
        if node.type == "import_statement":
            for child in node.children:
                if child.type == "dotted_name":
                    mods.append(_node_text(child))
                elif child.type == "aliased_import":
                    mods.append(_node_text(child.children[0]))
        elif node.type == "import_from_statement":
            mod_node = node.child_by_field_name("module_name")
            if mod_node is not None:
                mods.append(_node_text(mod_node))
        for child in node.children:
            _walk(child)

    _walk(tree.root_node)
    return mods


def dangling_contract_imports(
    dependent_files: list[str],
    repo_root: str | Path,
) -> list[dict]:
    """Return sorted ``[{"file": …, "import": …}]`` for imports that target the
    `contracts/` namespace but resolve to NO file on the merged tree (F6 — NEW logic).

    ``graph_gen._extract_imports`` emits edges only for imports that RESOLVE, so a
    dangler (a dependent still importing a deleted/renamed contract module) is
    invisible to it by construction. Mechanism: parse each dependent file, extract
    RAW module names, map each through ``graph_gen._module_to_path`` candidates; if
    ANY candidate path targets a `contracts/` prefix (the import names the contract
    namespace) AND NO candidate exists on disk ⇒ a dangler. Existence is decided at
    the BASE-MODULE level (R2): only the raw module's own candidates are checked —
    from-import NAMES are never expanded (expanding ``from contracts.c1 import
    SomeClass`` to ``contracts/c1/SomeClass.py`` would false-flag the commonest
    import form).

    Documented residual (suite-backstopped): a deleted submodule behind a surviving
    ``__init__.py`` referenced as ``from contracts.c1 import iface`` is invisible to
    this scan (``contracts/c1/__init__.py`` resolves the base module) — the
    full-suite re-run's ImportError is the behavioral backstop; the raw-module form
    ``from contracts.c1.iface import X`` IS caught. T2's ``__init__.py`` mandate makes
    the base-module candidates well-defined.

    Fail-closed (M1-L9): an unreadable/absent dependent file RAISES (``OSError``) — a
    file the gate cannot read cannot be certified dangler-free.
    """
    root = Path(repo_root)
    danglers: list[dict] = []
    for f in dependent_files:
        f_norm = f.replace("\\", "/")
        src = (root / f_norm).read_bytes()  # raises → fail-closed
        src_dir = str(Path(f_norm).parent)
        for mod in _raw_import_modules(src):
            candidates = _module_to_path(mod, src_dir, ())
            targets_contract = any(
                c.replace("\\", "/").startswith(_CONTRACTS_PREFIX) for c in candidates
            )
            if not targets_contract:
                continue  # not a contract-namespace import — not this gate's concern
            # Sweep C1: the BARE namespace module (`import contracts` /
            # `from contracts import c1`) resolves at runtime as a PEP-420
            # namespace package with no __init__.py on disk — it is a dangler
            # only if the contracts/ dir itself is gone. A deleted SUBMODULE
            # behind it is the documented base-module residual (suite backstop).
            if mod.lstrip(".") == "contracts":
                if (root / "contracts").is_dir():
                    continue
                danglers.append({"file": f_norm, "import": mod})
                continue
            resolves = any((root / c).is_file() for c in candidates)
            if not resolves:
                danglers.append({"file": f_norm, "import": mod})
    return sorted(danglers, key=lambda d: (d["file"], d["import"]))


# ---------------------------------------------------------------------------
# expand_ownership_paths — ownership dirs → .py files (F5 exclusion applied)
# ---------------------------------------------------------------------------


def expand_ownership_paths(
    ownership_entry: list[str],
    repo_root: str | Path,
    exclude_prefixes: tuple[str, ...] = (),
) -> list[str]:
    """Expand an ``ownership:`` entry (list of dir/file paths) to repo-relative ``.py``
    file paths — dir entries recurse to their ``.py`` files, file entries pass through.

    The T3 2(c) caller passes ``exclude_prefixes`` = the resolved ``contracts/`` dirs
    so the PROVIDER-owned contract itself is never in the edge-honesty forbidden set
    (F5 — the honest contract-only dependent must pass). ``exclude_prefixes`` are
    posix-normalized WITH a trailing slash before matching (R10 — ``contracts/C1/``
    never matches ``contracts/C10/...``).

    Fail-closed (M1-L9): a missing ownership path RAISES ``ValueError`` — an
    unresolvable forbidden-set entry cannot be silently dropped.
    """
    root = Path(repo_root)
    excludes = tuple(p.replace("\\", "/").rstrip("/") + "/" for p in exclude_prefixes)
    out: set[str] = set()
    for entry in ownership_entry:
        e = entry.replace("\\", "/")
        abs_p = root / e
        if not abs_p.exists():
            raise ValueError(
                f"contract_gate: ownership path not found: {entry!r} — refusing to "
                f"silently drop it from the forbidden set (M1-L9)."
            )
        if abs_p.is_dir():
            members = [p.relative_to(root).as_posix() for p in abs_p.rglob("*.py")]
        else:
            members = [abs_p.relative_to(root).as_posix()]
        for rel in members:
            if any(rel.startswith(ex) for ex in excludes):
                continue
            out.add(rel)
    return sorted(out)


# ---------------------------------------------------------------------------
# verify_contract_gate — the independent re-derivation (steps 1-6)
# ---------------------------------------------------------------------------


def verify_contract_gate(
    repo_root: str,
    integration_branch: str,
    builds_against: object,
    plan_path: Union[str, Path],
) -> dict:
    """Independently re-derive contract-edge soundness at the FINAL gate (M1-L3/L8 +
    obligations i/iii). Returns ``{"passed": bool, "vacuous": bool, "findings": [...]}``.

    Steps:
      1. ``pins = pinned_contracts(builds_against)``; a well-formed EMPTY map ⇒
         ``{"passed": True, "vacuous": True, "findings": []}`` (BC no-op).
      2. ``events = parse_trailer_events(...)`` and ``supersedes =
         parse_supersede_trailers(...)`` — a raise PROPAGATES (obligation iii; no
         catch anywhere in this module).
      3. (i) every supersede id ∈ ``pins`` else finding ``unknown-supersede-id``
         (a typo'd/case-variant id has an empty invalidation_set and would be
         vacuously "fully covered").
      4. Surface drift (M1-L8, R3): a NEVER-superseded contract's ``surface_hash``
         must == its pin; a SUPERSEDED contract's must == its NEWEST supersede hash
         — at the FINAL gate the pin branch is CLOSED for superseded contracts (a
         provider reverting to the pre-supersede pin after dependents re-dispatched
         against the new surface is drift, not authorization). Else finding
         ``unauthorized-surface-drift``. A missing / no-``.py`` contract dir RAISES
         (whole-dir retirement is OUT of M1 scope — the pinned dir must survive the
         run with bodies filled).
      5. Invalidation coverage + temporal (M1-L3/F7, R1 — COMMIT granularity): for
         each superseded C, every task in ``invalidation_set(builds_against, C)`` must
         have an ``invalidated`` event whose ``commit_index`` ≤ the ``commit_index``
         of C's NEWEST ``supersede`` event (newest-first: lower index = newer; equal
         = the same commit — intra-body line order is IRRELEVANT). Else finding
         ``invalidation-coverage-gap``.
      6. ``passed`` is True iff no findings; every failure is a NAMED finding
         ``{"kind": …, "detail": …}`` — never None/empty-on-failure.
    """
    # Step 1 — pins (raises on malformed/conflict); vacuous BC on well-formed empty.
    pins = pinned_contracts(builds_against)
    if not pins:
        return {"passed": True, "vacuous": True, "findings": []}

    # Step 2 — durable signals; raises PROPAGATE (obligation iii, no catch).
    events = parse_trailer_events(repo_root, integration_branch, plan_path)
    supersedes = parse_supersede_trailers(repo_root, integration_branch, plan_path)

    findings: list[dict] = []
    root = Path(repo_root)

    # Step 3 — unknown-supersede-id cross-check (obligation i).
    for cid in sorted(supersedes):
        if cid not in pins:
            findings.append({"kind": "unknown-supersede-id", "detail": cid})

    # Step 4 — surface drift (final-gate rule: superseded ⇒ newest-supersede-hash ONLY).
    for cid in sorted(pins):
        contract_dir = root / "contracts" / cid
        actual = ce.surface_hash(str(contract_dir))  # raises on missing / no-.py dir
        expected = supersedes[cid] if cid in supersedes else pins[cid]
        if actual != expected:
            findings.append({"kind": "unauthorized-surface-drift", "detail": cid})

    # Step 5 — invalidation coverage + temporal (COMMIT granularity).
    for cid in sorted(supersedes):
        sup_indices = [i for (i, kind, cid_, _h) in events if kind == "supersede" and cid_ == cid]
        if not sup_indices:
            # Sweep C3: the two scanners share one regex + one bounded scan, so
            # this divergence is unreachable today — if it EVER happens, the
            # coverage audit's inputs disagree and skipping would be a silent
            # coverage bypass. Fail closed (module charter, M1-L9/D136).
            raise ValueError(
                f"contract_gate: supersede for {cid!r} visible to "
                f"parse_supersede_trailers but absent from parse_trailer_events "
                f"— scan divergence; refusing a silent coverage bypass."
            )
        newest_sup = min(sup_indices)  # newest-first ⇒ smallest index = newest
        for task in ce.invalidation_set(builds_against, cid):
            inv_indices = [
                i for (i, kind, id_, _h) in events if kind == "invalidated" and id_ == task
            ]
            covered = any(i <= newest_sup for i in inv_indices)
            if not covered:
                findings.append(
                    {"kind": "invalidation-coverage-gap", "detail": f"{cid}:{task}"}
                )

    return {"passed": not findings, "vacuous": False, "findings": findings}


# ---------------------------------------------------------------------------
# write_contract_gate — the durable artifact (F4)
# ---------------------------------------------------------------------------


def write_contract_gate(kata_dir: str | Path, verdict: dict) -> Path:
    """Emit ``<kata_dir>/contract-gate.json`` — the durable artifact the evaluator's
    independence leg reads (F4; its ABSENCE is the evaluator's signal that the gate
    was skipped). The schema is the ``verify_contract_gate`` dict PLUS ``utc`` (stamped
    here) and the step-5 companion results the caller folds in: ``branch``,
    ``surviving_stubs: [paths]``, and ``danglers: [dicts]`` — so the artifact proves
    ALL THREE final-gate contract checks ran (the re-derivation, the sentinel scan,
    and the dangling-import scan), not just the re-derivation.
    """
    kata_path = Path(kata_dir)
    kata_path.mkdir(parents=True, exist_ok=True)
    payload = dict(verdict)
    payload["utc"] = datetime.now(timezone.utc).isoformat()
    out = kata_path / "contract-gate.json"
    out.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return out
