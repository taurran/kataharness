#!/usr/bin/env python3
"""Truth Serum v1 — the SEMI layer: S1, S2, S3. Signals feed judges; they NEVER block.

**Standing humility (TM-D2, DESIGN §3.1, verbatim):** *"the judgment+human layers found all of
these; the automated mechanical gates found none."* **Detectors ATTEST and NARROW; judges
judge.**

This module is the SIGNAL-ONLY half of the detector matrix (DESIGN §3.1). Its three detectors —

* **S1** unwired-symbol detection (graph ref edges + tests-path filter + import-level reach),
  calibrated on the T6–T11 orphan corpus;
* **S2** prose-claim narrowing (reuse-claim trigger phrases + adjacent ``file:line``);
* **S3** honesty-label propagation (clause-pin presence on a named artifact);

— emit rows into the attested-fact-table FORMAT that judges consume. They are structurally
incapable of returning a gate-refusing verdict: every row carries ``blocking: False``, the
verdict enum is disjoint from :data:`BLOCKING_VERDICTS`, and :func:`assert_non_blocking` is run
over every detector's output before it is returned.

Determinism Doctrine binds (docs/DETERMINISM-DOCTRINE.md): every output is ``sorted()`` on an
explicit total order (law 2, law 3, law 10), no clock is read (law 7), and the fact-table
serialization is ``sort_keys=True`` (law 5). Same graph in ⇒ same bytes out.

Honest scope of this module, stated up front:

* The **emitter** of the durable attested fact table is the grounding agent's
  (DESIGN §4, Loop B / W7). This module DEFINES and RETURNS the row shape; it writes nothing.
  :data:`ROW_SCHEMA` is therefore marked ``v1-provisional`` — the producer's contract, pending
  the consumer that owns the artifact.
* **S2's citation resolver is B5's** (``tools/truth_serum.py``, the sibling Loop-A task,
  UNMERGED at this module's base commit). :func:`resolve_citation` here is a deliberately narrow
  LOCAL resolver with the same existence-only semantics, and :func:`prose_claim_signals` takes
  the resolver as an injectable parameter so the swap to B5 is a call-site change, not a
  rewrite. The composition with B5 is **scheduled, not built**.
* **S3's doc-layer half is EV-1's badge registry** (DESIGN §9, Loop B / W8): the registry that
  says WHICH label is required on WHICH artifact. This module attests presence of a label it is
  HANDED. Deriving the requirement is **scheduled, not built**.
"""
from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable, Sequence
from pathlib import Path

# --------------------------------------------------------------------------- #
# The standing humility, verbatim — carried into every report string this
# module produces, not only its docstrings (TM-D2, DESIGN §3.1).
# --------------------------------------------------------------------------- #

HUMILITY_LINE = (
    "the judgment+human layers found all of these; the automated mechanical gates found none"
)
HUMILITY_RULE = "Detectors ATTEST and NARROW; judges judge."


# --------------------------------------------------------------------------- #
# The fact-table row shape (provisional producer contract — see module docstring)
# --------------------------------------------------------------------------- #

ROW_SCHEMA = "kata.truth-signals.row/v1-provisional"

#: The only verdicts a SIGNAL detector may emit.
#:   SIGNAL     — a narrowed finding for a judge to weigh. Not a failure.
#:   CLEAR      — the detector ran over real input and found nothing at this subject.
#:   UNATTESTED — the anti-vacuity companion (TM-D3): the detector REFUSES to certify over
#:                zero inputs / absent preconditions. Note this refuses to CERTIFY, it does
#:                not refuse the GATE — a signal never blocks, so a vacuous signal scan is
#:                reported as unattested rather than escalated into a refusal.
SIGNAL_VERDICTS = frozenset({"SIGNAL", "CLEAR", "UNATTESTED"})

#: Verdict tokens reserved for the BLOCKING (gate-refusing) detectors B1–B6. A signal
#: detector emitting any of these would silently promote a heuristic into a gate refusal —
#: the exact facade-one-level-up failure the trust model exists to prevent.
BLOCKING_VERDICTS = frozenset({"BLOCK", "BLOCKER", "REFUSE", "REFUSAL", "FAIL", "REJECT"})


def build_row(
    *,
    detector: str,
    row_class: str,
    verdict: str,
    subject: str,
    detail: str,
    limits: Sequence[str] = (),
    provenance: Sequence[str] = (),
) -> dict:
    """Build one attested-fact-table row. Pure; key order is fixed; lists are sorted.

    ``blocking`` is a hardcoded ``False`` rather than a parameter: there is no argument a
    caller could pass that would make a signal row blocking, and a parameter would be a
    surface through which one could.
    """
    if verdict not in SIGNAL_VERDICTS:
        raise ValueError(
            f"truth_signals: verdict {verdict!r} is not a signal verdict "
            f"{sorted(SIGNAL_VERDICTS)} (signals never return a blocking verdict type)"
        )
    return {
        "blocking": False,
        "class": row_class,
        "detail": detail,
        "detector": detector,
        "humility": HUMILITY_RULE,
        "limits": sorted(limits),
        "provenance": sorted(provenance),
        "schema": ROW_SCHEMA,
        "subject": subject,
        "verdict": verdict,
    }


def assert_non_blocking(rows: Iterable[dict]) -> list[dict]:
    """Return ``rows`` unchanged, or RAISE if any row could act as a gate refusal.

    Run over every detector's output before it leaves this module, so the "signals never
    block" invariant is enforced by the code path and not only by a test that could be
    deleted.
    """
    out = list(rows)
    for row in out:
        if row.get("blocking"):
            raise ValueError(f"truth_signals: signal row is marked blocking: {row!r}")
        verdict = row.get("verdict")
        if verdict in BLOCKING_VERDICTS or verdict not in SIGNAL_VERDICTS:
            raise ValueError(
                f"truth_signals: signal row carries a blocking verdict type {verdict!r}: {row!r}"
            )
    return out


def fact_table(rows: Iterable[dict]) -> dict:
    """Assemble rows into the attested-fact-table shape (deterministically ordered)."""
    ordered = sorted(
        assert_non_blocking(rows),
        key=lambda r: (r["detector"], r["class"], r["subject"], r["detail"]),
    )
    return {
        "humility": HUMILITY_LINE,
        "rows": ordered,
        "schema": ROW_SCHEMA,
        "tier": "SIGNAL",
    }


def render_fact_table(rows: Iterable[dict]) -> str:
    """Canonical JSON for the fact table — ``sort_keys=True`` (Determinism Doctrine law 5)."""
    return json.dumps(fact_table(rows), sort_keys=True, indent=2) + "\n"


# --------------------------------------------------------------------------- #
# S1 — unwired-symbol detection
# --------------------------------------------------------------------------- #

#: Path components that mark a file as test code. Deliberately the test half of
#: ``graph_gen._NON_SOURCE_ROOTS`` (``graph_gen.py:261``) — the same convention the graph
#: builder already uses to decide what is not product source.
DEFAULT_TEST_PATH_PARTS: tuple[str, ...] = ("tests", "test")

#: S1's honest limits, carried VERBATIM from DESIGN §3.1's S1 row. Every one of these has a
#: test in ``tools/tests/test_truth_signals.py`` that DEMONSTRATES the wrong answer against
#: the T6–T11 orphan corpus — pinned, not prosed.
S1_HONEST_LIMITS: tuple[str, ...] = (
    "call-only edges",
    "bare-name matching",
    "fabricated `src` attribution",
    "dynamic imports invisible",
    "entry points outside the graph look dead",
)


def _path_of(node_id: str) -> str:
    """Repo-relative file path of a graph node id (``path::name`` for symbols, ``path`` for files)."""
    return node_id.split("::", 1)[0]


def is_test_path(path: str, test_path_parts: Sequence[str] = DEFAULT_TEST_PATH_PARTS) -> bool:
    """True when any component of ``path`` marks it as test code."""
    parts = set(test_path_parts)
    return any(part in parts for part in Path(path.replace("\\", "/")).parts)


def _graph_precondition(graph: object, detector: str) -> dict | None:
    """The TM-D3 anti-vacuity companion for a graph-consuming detector.

    Returns an UNATTESTED row when the graph is absent, malformed, or carries no
    ``meta.repoHash`` (an absent/stale graph artifact must never be certified as "no
    findings"); ``None`` when the graph is fit to scan.
    """
    if not isinstance(graph, dict):
        return build_row(
            detector=detector,
            row_class="anti-vacuity",
            verdict="UNATTESTED",
            subject="<graph>",
            detail="refusing to certify: no graph artifact supplied",
            limits=S1_HONEST_LIMITS,
        )
    if not isinstance(graph.get("nodes"), list) or not isinstance(graph.get("edges"), list):
        return build_row(
            detector=detector,
            row_class="anti-vacuity",
            verdict="UNATTESTED",
            subject="<graph>",
            detail="refusing to certify: graph artifact has no nodes/edges lists",
            limits=S1_HONEST_LIMITS,
        )
    meta = graph.get("meta")
    if not isinstance(meta, dict) or not meta.get("repoHash"):
        return build_row(
            detector=detector,
            row_class="anti-vacuity",
            verdict="UNATTESTED",
            subject="<graph>",
            detail="refusing to certify: graph artifact carries no meta.repoHash (absent or stale)",
            limits=S1_HONEST_LIMITS,
        )
    return None


def reference_provenance(
    graph: dict,
    test_path_parts: Sequence[str] = DEFAULT_TEST_PATH_PARTS,
) -> dict[str, list[str]]:
    """Map every symbol id to the sorted NON-TEST symbol ids that reference it.

    This is the wiring evidence S1 decides on, exposed so callers can inspect it — and so the
    verbatim limit **"fabricated `src` attribution"** is demonstrable: ``graph_gen._extract_refs``
    attributes each ref edge to ``next(iter(sorted(file_symbol_ids)))`` (``graph_gen.py:453``),
    the alphabetically-first symbol in the calling FILE, not the symbol that actually made the
    call. The referencing FILE in this map is trustworthy; the referencing SYMBOL is not.
    """
    out: dict[str, set[str]] = {}
    for edge in graph.get("edges", []):
        if edge.get("kind") not in ("ref", "call"):
            continue
        src = edge.get("src")
        dst = edge.get("dst")
        if not isinstance(src, str) or not isinstance(dst, str):
            continue
        if is_test_path(_path_of(src), test_path_parts):
            continue
        out.setdefault(dst, set()).add(src)
    return {k: sorted(v) for k, v in sorted(out.items())}


def unwired_symbols(
    graph: dict,
    test_path_parts: Sequence[str] = DEFAULT_TEST_PATH_PARTS,
) -> list[dict]:
    """S1, symbol level: product symbols with zero non-test references in the graph.

    A symbol is reported when no ``ref``/``call`` edge reaches it from a file outside the
    tests tree. Symbols DEFINED in test files are excluded from the scan — a test helper is
    not product surface, and flagging every one of them would drown the signal.

    Honest limits (DESIGN §3.1, VERBATIM), each demonstrated by a test:
    **call-only edges** · **bare-name matching** · **fabricated `src` attribution** ·
    **dynamic imports invisible** · **entry points outside the graph look dead**.

    Anti-vacuity companion (TM-D3): an absent/malformed graph, a graph with no
    ``meta.repoHash``, or a scan over zero product symbols returns a single UNATTESTED row —
    never an empty list presented as "nothing unwired". Standing humility: *"the
    judgment+human layers found all of these; the automated mechanical gates found none."*
    """
    refusal = _graph_precondition(graph, "S1")
    if refusal is not None:
        return assert_non_blocking([refusal])

    symbols = [
        n for n in graph["nodes"]
        if n.get("kind") == "symbol"
        and isinstance(n.get("id"), str)
        and not is_test_path(str(n.get("path", _path_of(n["id"]))), test_path_parts)
    ]
    if not symbols:
        return assert_non_blocking([build_row(
            detector="S1",
            row_class="anti-vacuity",
            verdict="UNATTESTED",
            subject="<graph>",
            detail="refusing to certify: scan covered zero product symbols",
            limits=S1_HONEST_LIMITS,
        )])

    provenance = reference_provenance(graph, test_path_parts)
    rows: list[dict] = []
    unwired = 0
    for sym in sorted(symbols, key=lambda n: n["id"]):
        if provenance.get(sym["id"]):
            continue
        unwired += 1
        rows.append(build_row(
            detector="S1",
            row_class="unwired-symbol",
            verdict="SIGNAL",
            subject=sym["id"],
            detail=(
                f"no non-test reference reaches {sym['id']} in the graph — "
                f"{HUMILITY_RULE}"
            ),
            limits=S1_HONEST_LIMITS,
        ))
    rows.append(build_row(
        detector="S1",
        row_class="scan-coverage",
        verdict="CLEAR",
        subject="<graph>",
        detail=f"scanned {len(symbols)} product symbols; {unwired} carry no non-test reference",
        limits=S1_HONEST_LIMITS,
    ))
    return assert_non_blocking(rows)


def unimported_modules(
    graph: dict,
    test_path_parts: Sequence[str] = DEFAULT_TEST_PATH_PARTS,
) -> list[dict]:
    """S1, import level: product FILES no non-test file imports.

    The import-level leg. **Verified-surface note (protocol/reuse-claims.md):** DESIGN §3.1
    names ``edge_honesty`` for this leg. The built surface is
    ``contract_edges.edge_honesty(dependent_files, provider_paths, repo_root)``
    (``contract_edges.py:356``) and its semantics are CONTRACT-EDGE honesty — "does this
    dependent import a provider's implementation path" — not orphan detection; calling it here
    would be a phantom reuse claim. What this leg actually consumes is the graph's ``import``
    edges, produced by ``graph_gen._extract_imports`` (``graph_gen.py:192``) — which is the
    same import scanner ``edge_honesty`` itself reuses (``contract_edges.py:380``). Same
    resolution machinery, reached through the artifact instead of the wrapper, and the same
    documented residual travels with it: DYNAMIC imports are a mechanical bypass this scan
    cannot see (``contract_edges.py:371``, adval P0-F9).

    Anti-vacuity companion (TM-D3): absent/malformed graph, missing ``meta.repoHash``, or zero
    product files ⇒ one UNATTESTED row, never a silent clean bill.
    """
    refusal = _graph_precondition(graph, "S1")
    if refusal is not None:
        return assert_non_blocking([refusal])

    files = [
        n for n in graph["nodes"]
        if n.get("kind") == "file"
        and isinstance(n.get("id"), str)
        and not is_test_path(n["id"], test_path_parts)
    ]
    if not files:
        return assert_non_blocking([build_row(
            detector="S1",
            row_class="anti-vacuity",
            verdict="UNATTESTED",
            subject="<graph>",
            detail="refusing to certify: scan covered zero product files",
            limits=S1_HONEST_LIMITS,
        )])

    importers: dict[str, set[str]] = {}
    for edge in graph["edges"]:
        if edge.get("kind") != "import":
            continue
        src, dst = edge.get("src"), edge.get("dst")
        if not isinstance(src, str) or not isinstance(dst, str):
            continue
        if is_test_path(src, test_path_parts):
            continue
        importers.setdefault(dst, set()).add(src)

    rows: list[dict] = []
    for node in sorted(files, key=lambda n: n["id"]):
        if importers.get(node["id"]):
            continue
        rows.append(build_row(
            detector="S1",
            row_class="unimported-module",
            verdict="SIGNAL",
            subject=node["id"],
            detail=(
                f"no non-test file imports {node['id']} in the graph — {HUMILITY_RULE}"
            ),
            limits=S1_HONEST_LIMITS,
        ))
    return assert_non_blocking(rows)


def s1_signals(
    graph: dict,
    test_path_parts: Sequence[str] = DEFAULT_TEST_PATH_PARTS,
) -> list[dict]:
    """S1 in full: the symbol-level and import-level legs, one row list."""
    return assert_non_blocking(
        unwired_symbols(graph, test_path_parts) + unimported_modules(graph, test_path_parts)
    )


# --------------------------------------------------------------------------- #
# S2 — prose-claim narrowing
# --------------------------------------------------------------------------- #

#: The reuse-claim trigger set, transcribed from the verbatim guard text in
#: ``protocol/reuse-claims.md`` ("The guard (LD3 — verbatim contract text)"):
#: *"reuses / composes / via the existing X"* … *"the orchestrator already writes Y"*,
#: *"this already exists/has Z"*. Matched case-insensitively as substrings.
REUSE_TRIGGER_PHRASES: tuple[str, ...] = (
    "already exists",
    "already has",
    "already writes",
    "composes",
    "reuses",
    "via the existing",
)

S2_HONEST_LIMITS: tuple[str, ...] = (
    "existence is not support — a citation that resolves may still be fabricated (OBSERVATIONS D-5)",
    "extracting arbitrary claims from prose stays judgment",
    "trigger-phrase matching narrows; it does not enumerate every reuse claim",
)

#: ``path.ext:line``, optionally backticked. The extension requirement is what keeps prose like
#: "`file:line`" or a bare "note:12" out of the candidate set.
_CITATION_RE = re.compile(r"`?([A-Za-z0-9_][A-Za-z0-9_./\\-]*\.[A-Za-z0-9]+):(\d+)`?")

#: How far from the trigger line a citation may sit and still count as adjacent. One line —
#: the paragraph-wrap tolerance. A stated heuristic, not a derived constant.
_ADJACENCY_LINES = 1


def resolve_citation(path: str, line: int, repo_root: str | Path) -> bool:
    """EXISTENCE-only citation resolution: does ``repo_root/path`` exist and have that line?

    The narrow LOCAL resolver. B5 (``tools/truth_serum.py``, the sibling Loop-A task) owns the
    canonical resolver on the ``check_wikilinks`` precedent (``validate_skills.py:1042``); it is
    UNMERGED at this module's base commit and is deliberately NOT imported from an unmerged
    branch. :func:`prose_claim_signals` takes ``resolver`` as a parameter so the swap is a
    call-site change. The composition with B5 is **scheduled, not built**.

    Existence is all this attests. Whether the cited line SUPPORTS the claim stays judgment,
    routed to grounding (DESIGN §3.1 B5) — OBSERVATIONS D-5 is the standing proof that the two
    are different questions: ``kata-validate/SKILL.md:276``'s ``:13`` anchor resolved to a real
    line that had never, in any of the file's nine revisions, contained the quoted sentence.
    Authoring-time fabrication passes an existence check.
    """
    rel = Path(path.replace("\\", "/"))
    if rel.is_absolute() or any(part == ".." for part in rel.parts):
        return False  # never resolve outside the supplied root (CWE-23)
    if line < 1:
        return False
    target = Path(repo_root) / rel
    if not target.is_file():
        return False
    try:
        text = target.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return line <= len(text.splitlines())


def prose_claim_signals(
    text: str | None,
    source: str,
    repo_root: str | Path,
    resolver: Callable[[str, int, str | Path], bool] = resolve_citation,
    trigger_phrases: Sequence[str] = REUSE_TRIGGER_PHRASES,
) -> list[dict]:
    """S2: narrow prose to the reuse claims whose cited surface does not resolve.

    Each line carrying a trigger phrase becomes a candidate. A candidate with no ``file:line``
    within :data:`_ADJACENCY_LINES` is a ``phantom-reuse-claim``; one whose citation does not
    resolve is an ``unresolved-citation``; one that resolves is ``resolved-citation`` (CLEAR)
    and carries the existence-is-not-support limit.

    Anti-vacuity companions (TM-D3), on the ``check_reuse_claims_producers_exist`` precedent
    (``validate_skills.py:1098`` — a guard that silently skips a missing producer stops
    enforcing and nobody notices):

    * ``text`` absent/empty ⇒ UNATTESTED, never "no phantom claims".
    * ``repo_root`` absent ⇒ UNATTESTED — with no root every citation would resolve to
      "missing" and a clean document would be reported as all-phantom.
    * zero candidates ⇒ reported explicitly AS zero-candidate (CLEAR), never as
      "all citations resolve".
    """
    if not text or not text.strip():
        return assert_non_blocking([build_row(
            detector="S2",
            row_class="anti-vacuity",
            verdict="UNATTESTED",
            subject=source,
            detail="refusing to certify: artifact is empty or could not be read",
            limits=S2_HONEST_LIMITS,
        )])
    if not Path(repo_root).is_dir():
        return assert_non_blocking([build_row(
            detector="S2",
            row_class="anti-vacuity",
            verdict="UNATTESTED",
            subject=source,
            detail=f"refusing to certify: citation root {repo_root!s} does not exist",
            limits=S2_HONEST_LIMITS,
        )])

    lines = text.splitlines()
    lowered = [ln.lower() for ln in lines]
    phrases = [p.lower() for p in trigger_phrases]

    rows: list[dict] = []
    for idx, low in enumerate(lowered):
        hits = sorted(p for p in phrases if p in low)
        if not hits:
            continue
        lo = max(0, idx - _ADJACENCY_LINES)
        hi = min(len(lines), idx + _ADJACENCY_LINES + 1)
        citations: list[tuple[str, int]] = []
        for near in range(lo, hi):
            citations.extend(
                (m.group(1), int(m.group(2))) for m in _CITATION_RE.finditer(lines[near])
            )
        subject = f"{source}:{idx + 1}"
        if not citations:
            rows.append(build_row(
                detector="S2",
                row_class="phantom-reuse-claim",
                verdict="SIGNAL",
                subject=subject,
                detail=(
                    f"reuse-claim trigger {hits!r} with no adjacent file:line — "
                    f"a claim to verify, not an assumption. {HUMILITY_RULE}"
                ),
                limits=S2_HONEST_LIMITS,
                provenance=hits,
            ))
            continue
        for cited_path, cited_line in sorted(set(citations)):
            resolved = resolver(cited_path, cited_line, repo_root)
            rows.append(build_row(
                detector="S2",
                row_class="resolved-citation" if resolved else "unresolved-citation",
                verdict="CLEAR" if resolved else "SIGNAL",
                subject=subject,
                detail=(
                    f"reuse-claim trigger {hits!r} cites {cited_path}:{cited_line} — "
                    + ("resolves (existence only; support stays judgment)" if resolved
                       else "does NOT resolve")
                    + f". {HUMILITY_RULE}"
                ),
                limits=S2_HONEST_LIMITS,
                provenance=[f"{cited_path}:{cited_line}"],
            ))

    if not rows:
        rows.append(build_row(
            detector="S2",
            row_class="scan-coverage",
            verdict="CLEAR",
            subject=source,
            detail=(
                f"zero-candidate: {len(lines)} lines scanned, no reuse-claim trigger phrase "
                "present (reported as zero-candidate, never as 'all citations resolve')"
            ),
            limits=S2_HONEST_LIMITS,
        ))
    return assert_non_blocking(rows)


# --------------------------------------------------------------------------- #
# S3 — honesty-label propagation
# --------------------------------------------------------------------------- #

S3_HONEST_LIMITS: tuple[str, ...] = (
    "token presence is forgeable (KH-T02) — a reviewer kept every guarded token and inverted the meaning",
    "which label a given artifact REQUIRES is EV-1's badge registry (§9) — scheduled, not built",
)


def _normalize_clause_text(text: str) -> str:
    """Flatten line endings, markdown emphasis, and whitespace runs for clause matching.

    Same semantics as the validator's clause-pin normaliser
    (``validate_skills._normalize_protocol_text:720``) so a reflowed or bolded label still
    matches while a deleted one does not. Reimplemented rather than imported: the validator is
    maintainer tooling pinned to the real repo root (``validate_skills.py:22``) and a gate
    engine must not depend on it. Pure and deterministic — no clock, no environment.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[*`_]", "", text)
    return re.sub(r"\s+", " ", text).strip()


def label_propagation_signals(
    text: str | None,
    artifact: str,
    required_labels: Sequence[str],
) -> list[dict]:
    """S3: does each required honesty label survive, verbatim-in-substance, on this artifact?

    Clause-pin machinery (the ``check_protocol_integrity`` pattern,
    ``validate_skills.py:979``) applied to PD-2's traveling honesty labels: modeled says
    modeled, n=1 says n=1, unproven legs stay named wherever the claim appears.

    A SIGNAL, never a block, and honestly so — **token presence is forgeable (KH-T02)**: a
    reviewer once rewrote both Prime Directives to say the opposite, kept all seven guarded
    tokens, and the validator passed green. Presence is evidence a label was not silently
    DELETED; it is not evidence the artifact is honest.

    The doc-layer half — the registry deciding WHICH label a named artifact requires — is
    **EV-1's badge registry (DESIGN §9, W8): scheduled, not built.** This function attests
    presence of labels it is handed.

    Anti-vacuity companion (TM-D3): empty artifact text, or an empty required-label set,
    returns UNATTESTED — a label check over no labels certifies nothing.
    """
    labels = [lab for lab in required_labels if lab and lab.strip()]
    if not text or not text.strip():
        return assert_non_blocking([build_row(
            detector="S3",
            row_class="anti-vacuity",
            verdict="UNATTESTED",
            subject=artifact,
            detail="refusing to certify: artifact is empty or could not be read",
            limits=S3_HONEST_LIMITS,
        )])
    if not labels:
        return assert_non_blocking([build_row(
            detector="S3",
            row_class="anti-vacuity",
            verdict="UNATTESTED",
            subject=artifact,
            detail=(
                "refusing to certify: no required labels supplied — the requirement map is "
                "EV-1's badge registry (scheduled, not built)"
            ),
            limits=S3_HONEST_LIMITS,
        )])

    normalized = _normalize_clause_text(text)
    rows: list[dict] = []
    for label in sorted(set(labels)):
        present = _normalize_clause_text(label) in normalized
        rows.append(build_row(
            detector="S3",
            row_class="label-present" if present else "label-absent",
            verdict="CLEAR" if present else "SIGNAL",
            subject=f"{artifact}#{label}",
            detail=(
                f"honesty label {label!r} "
                + ("is present (presence is forgeable — KH-T02)" if present
                   else "is ABSENT from the artifact")
                + f". {HUMILITY_RULE}"
            ),
            limits=S3_HONEST_LIMITS,
            provenance=[artifact],
        ))
    return assert_non_blocking(rows)
