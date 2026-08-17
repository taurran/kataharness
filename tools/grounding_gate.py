"""grounding_gate.py — the grounding engine: verdicts (S3a-2) + the attested fact table (§4).

Two surfaces, one module:

1. **The per-finding grounding verdict** (S3a-2, unchanged): maps a kata-research finding to
   GROUND / REJECT / ESCALATE per the kata-evaluate injected-knowledge grounding rules and
   writes ``.kata/grounding.json``.
2. **The ATTESTED FACT TABLE** (trust-model DESIGN §4, PLAN W7 ``grounding-agent``): the
   artifact every judge's brief carries — **detector outputs + grounding verdicts + evidence
   identity** — plus the **R-M10 stack-head mutation attestation** that is the evaluator's
   precondition at the final gate.

**Agent proposes, engine attests.** The `kata-grounding` agent RUNS the tooling and hands this
module what the engines produced; every verdict in the emitted table is derived HERE, by code,
from those producer outputs. The agent authors no row. The honest residual, stated in-contract:
this engine attests **what it is handed** — it re-derives the identity leg (via
``run_result.classify_evidence``) and the roll-up itself, but a bundle whose detector reports
were fabricated rather than produced would be attested as supplied. The fact table is
tamper-EVIDENT (every row names its producer and its origin schema), not tamper-proof.

Standing humility (DESIGN §3.1, burn-02 meta-finding, verbatim): *"the judgment+human layers
found all of these; the automated mechanical gates found none."* **Detectors ATTEST and NARROW;
judges judge.** Scope boundary, verbatim (DESIGN §4): **grounding attests FACTS pre-judgment;
the challenger attacks JUDGMENTS post-hoc.**

Row-schema reconciliation (Loop-A carried input)
------------------------------------------------
``truth_signals.ROW_SCHEMA`` shipped as ``kata.truth-signals.row/v1-provisional`` — provisional
*pending the consumer that owns the artifact* (``truth_signals.py`` module docstring). This
module is that consumer. :data:`FACT_ROW_SCHEMA` (``kata.grounding.fact-row/v1``) is a strict
**superset** of the signal row: all ten signal keys are carried with identical semantics
(``blocking`` · ``class`` · ``detail`` · ``detector`` · ``humility`` · ``limits`` ·
``provenance`` · ``schema`` · ``subject`` · ``verdict``), and two keys are added — ``tier``
(which producer family the row came from) and ``attestedBy`` (the engine that produced it).
The provisional marker therefore DROPS on the emitted artifact; the origin schema is preserved
in the promoted row's ``provenance`` so the lineage is not erased. The producer-side constant in
``truth_signals.py`` still reads ``v1-provisional`` — that module is another task's ownership
grant, so the rename is reported as a follow-on, not edited from here.

Determinism Doctrine (docs/DETERMINISM-DOCTRINE.md) binds: every row list is sorted on an
explicit total order (laws 2/3/10), serialization is ``sort_keys=True`` (law 5), no clock is
read (laws 6/7), and the mutation sample is a stated deterministic sort-and-take (law 9).

Execution surface: **this module contains no subprocess sink.** ``main(--mutation-rerun)``
delegates to ``mutation_run.prove_many`` → ``mutation_run._default_runner``, an ALREADY
REGISTERED sink (``protocol/exec-safety.md``, the ``mutation_run._default_runner`` row) whose
closed grammar compiles the gate command to structured argv or refuses it — the
``run_result.resolve_head_sha`` precedent: a caller gains execution through a registered sink
WITHOUT growing a spawn site of its own. ``tests/test_grounding_gate.py`` asserts the absence
mechanically, so the claim cannot rot into a comment.

Public API
----------
grounding_verdict(finding, source_supports, locked_conflict) -> str
    Return "GROUND", "REJECT", or "ESCALATE".
build_verdict(finding, source_supports, locked_conflict, evidence) -> dict
    Return {finding, verdict, evidence}.
write_grounding(kata_dir, verdicts) -> str
    Write <kata_dir>/grounding.json and return the path.
fact_row(...) -> dict
    Build one validated fact-table row (fail-closed on an off-enum verdict).
promote_signal_row(row) -> dict
    Promote a ``kata.truth-signals.row/v1-provisional`` row into the v1 fact row.
detector_rows(report) -> list[dict]
    Promote one ``truth_serum.DetectorReport.to_dict()`` payload.
identity_rows(name, result_json, expected_sha, expected_run_id) -> list[dict]
    Evidence identity, re-derived here via ``run_result.classify_evidence``.
grounding_rows(verdicts) -> list[dict]
    Promote ``build_verdict`` outputs.
sample_mutation_specs(specs, size) -> dict
    The R-M10/§3.6 deterministic sample — sorted, taken, and RECORDED (no silent truncation).
attest_mutation_set(...) -> dict
    The R-M10 attestation: present + current + per-task complete + the sampled re-run.
roll_up(rows) -> str
    The pass-level GROUND / REJECT / ESCALATE roll-up (SIGNAL rows never contribute).
build_fact_table(...) / render_fact_table(table) / parse_fact_table(payload)
    Assemble / canonically serialize / validate-and-round-trip the table.
write_fact_table(kata_dir, table) -> str
    Write <kata_dir>/fact-table.json and return the path.
main(argv) -> int
    CLI: run the stack-head pass over a bundle. 0=GROUND, 1=REJECT, 2=ESCALATE.

Security note (CWE-23): ``kata_dir`` is operator-supplied.  ``_safe_path`` blocks
any ``..`` segment before reaching the filesystem sink — mirrors gate_emit._safe_path.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from fs_atomic import atomic_write_text
from run_result import classify_evidence

# ---------------------------------------------------------------------------
# Path-traversal guard (mirrors gate_emit._safe_path)
# ---------------------------------------------------------------------------


def _safe_path(raw: str) -> Path:
    """Reject path-traversal (CWE-23) in an operator-supplied path, then resolve.

    Blocks any ``..`` segment — the traversal-escape primitive — so a crafted
    argument cannot climb out of the intended tree, while still allowing the
    absolute and nested-relative paths the operator legitimately targets.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"grounding_gate: refusing path with '..' traversal: {raw!r}"
        )
    return p.resolve()


# ---------------------------------------------------------------------------
# Core verdict logic
# ---------------------------------------------------------------------------


def grounding_verdict(
    finding: dict,
    source_supports: bool,
    locked_conflict: bool,
) -> str:
    """Derive the deterministic grounding verdict for a single finding.

    Rules (per kata-evaluate injected-knowledge grounding mode):

    1. ``locked_conflict`` OR ``finding["groundsToPlan"] == "NO"``  ⇒ ``"ESCALATE"``
       (LOCKED tension or the finding itself flags a plan conflict — never fold silently).
    2. ``not source_supports``                                       ⇒ ``"REJECT"``
       (source does not actually support the claim — default-FAIL).
    3. Otherwise                                                     ⇒ ``"GROUND"``
       (cited, source-supported, no LOCKED conflict — orchestrator may fold).

    Parameters
    ----------
    finding:
        The kata-research output dict ``{claim, source, confidence, groundsToPlan}``.
    source_supports:
        True if the caller has read the cited source and confirmed it supports the
        claim.  **Never assumed True** — default-FAIL: the caller must assert this.
    locked_conflict:
        True if folding this finding would contradict a LOCKED decision.

    Raises
    ------
    ValueError
        If ``finding["groundsToPlan"]`` is absent or not one of
        ``{"YES", "NO", "PARTIAL"}``.  ``escalation.build_finding`` (``tools/escalation.py:233``
        — qualified here after the Loop-A E7 lesson that a BARE-BACKTICKED identifier reads as
        this module's own) enforces this enum, but
        other producers can construct a finding dict directly — an unvalidated
        lowercase/typo/absent value would silently skip the ESCALATE branch
        (D136 — decision code hard-fails on malformed input, never a silent
        permissive default).
    """
    grounds = finding.get("groundsToPlan")
    if grounds not in {"YES", "NO", "PARTIAL"}:
        raise ValueError(
            "grounding_gate: finding['groundsToPlan'] must be one of "
            f"{{'YES', 'NO', 'PARTIAL'}}, got {grounds!r} "
            "(D136 — no silent permissive default)"
        )
    if locked_conflict or grounds == "NO":
        return "ESCALATE"
    if not source_supports:
        return "REJECT"
    return "GROUND"


# ---------------------------------------------------------------------------
# Verdict builder
# ---------------------------------------------------------------------------


def build_verdict(
    finding: dict,
    source_supports: bool,
    locked_conflict: bool,
    evidence: str,
) -> dict:
    """Build a complete verdict dict for a single finding.

    Parameters
    ----------
    finding:
        The kata-research output dict ``{claim, source, confidence, groundsToPlan}``.
    source_supports:
        Whether the caller confirmed the source supports the claim.
    locked_conflict:
        Whether folding this finding conflicts with a LOCKED decision.
    evidence:
        Quoted or paraphrased excerpt from the source (or explanation for
        REJECT/ESCALATE) — the auditable trail.

    Returns
    -------
    dict with keys ``finding``, ``verdict``, ``evidence``.
    """
    return {
        "finding": finding,
        "verdict": grounding_verdict(finding, source_supports, locked_conflict),
        "evidence": evidence,
    }


# ---------------------------------------------------------------------------
# Artifact writer
# ---------------------------------------------------------------------------


def write_grounding(kata_dir: str, verdicts: list[dict]) -> str:
    """Write ``<kata_dir>/grounding.json`` and return the absolute path.

    Atomic (D159, same-dir tmp + ``os.replace``): the fold-authorization reader may
    open this artifact while the gate is re-emitting it, and a truncate-then-write
    leaves a window in which a concurrent reader sees a partial file.  Output bytes
    are unchanged.

    Parameters
    ----------
    kata_dir:
        Operator-supplied path to the ``.kata/`` output directory (or any
        equivalent directory).  Traversal (``..``) is rejected (CWE-23).
    verdicts:
        List of verdict dicts produced by :func:`build_verdict`.

    Returns
    -------
    Absolute path string to the written ``grounding.json``.
    """
    out = _safe_path(kata_dir)
    out.mkdir(parents=True, exist_ok=True)

    if verdicts:
        payload = {
            "verdicts": verdicts,
            "allGrounded": all(v["verdict"] == "GROUND" for v in verdicts),
        }
    else:
        # Q-3 (D136): an empty verdict list makes ``all(...)`` vacuously True,
        # which would write allGrounded:true — a spurious fold-authorization
        # signal derived from zero decision input.  The module does not raise on
        # empty input elsewhere (it degrades / fail-closes), so emit an explicit
        # non-permissive vacuous marker rather than a silent permissive default.
        payload = {"verdicts": [], "allGrounded": False, "vacuous": True}

    grounding_path = out / "grounding.json"
    atomic_write_text(grounding_path, json.dumps(payload, indent=2), encoding="utf-8")
    return str(grounding_path)


# ===========================================================================
# THE ATTESTED FACT TABLE (DESIGN §4 / TM-E2 / R-M10)
# ===========================================================================

#: The burn-02 meta-finding, VERBATIM. Carried on the table itself so a consumer cannot quote a
#: fact without the caveat that produced the whole trust model.
HUMILITY_LINE = (
    "the judgment+human layers found all of these; the automated mechanical gates found none"
)

#: TM-D2, verbatim. Byte-identical to ``truth_serum.HUMILITY_LINE`` and
#: ``truth_signals.HUMILITY_RULE`` — pinned equal by test, not by hope.
HUMILITY_RULE = "Detectors ATTEST and NARROW; judges judge."

#: DESIGN §4, VERBATIM — the boundary between this agent and the challenger.
SCOPE_BOUNDARY = (
    "grounding attests FACTS pre-judgment; the challenger attacks JUDGMENTS post-hoc"
)

#: DESIGN §4's overhead record — MODELED, and labeled as modeled wherever it is quoted
#: (TM-E1 as corrected by R3-H3). The exception is the whole point: engines are free EXCEPT
#: the mutation re-run: ``mutation_run.prove_non_vacuous`` copies the project tree to a sandbox
#: and runs the test command twice per asserted line (DESIGN §3.6 anchors that at
#: ``mutation_run.py:218-315``), and its caps are §3.6's.
OVERHEAD_RECORD = (
    "MODELED, not measured (TM-E1, corrected by R3-H3): per-task agent dispatches "
    "~ +15-30 serialized minutes on a mid-size run; stack-head-only ~ +2-5 minutes per run; "
    "engines are milliseconds and token-free -- EXCEPT the mutation re-run, whose real cost "
    "basis and caps are DESIGN section 3.6's."
)

#: The v1 fact-table + fact-row schemas. NOT provisional: the consumer that owns the artifact
#: (this module) now exists, and the row shape is a strict superset of the producer's.
FACT_TABLE_SCHEMA = "kata.grounding.fact-table/v1"
FACT_ROW_SCHEMA = "kata.grounding.fact-row/v1"

#: Producer row schemas this emitter reconciles. A row carrying an unlisted schema is REFUSED
#: (D136 — no silent permissive default), because silently promoting an unknown shape is how a
#: fabricated row would enter the table wearing a producer's name.
RECONCILED_ROW_SCHEMAS: tuple[str, ...] = ("kata.truth-signals.row/v1-provisional",)

#: The closed per-tier verdict grammar. BLOCKING mirrors ``truth_serum.VERDICTS``; SIGNAL
#: mirrors ``truth_signals.SIGNAL_VERDICTS``; GROUNDING mirrors this module's own three rules.
#: IDENTITY is the upper-cased form of ``run_result``'s three artifact ROLES. MUTATION is the
#: R-M10 attestation's own space. Both mirrors are pinned equal by test.
TIER_VERDICTS: dict[str, frozenset[str]] = {
    "BLOCKING": frozenset({"BLOCK", "PASS", "REFUSE", "ZERO_CANDIDATE"}),
    "SIGNAL": frozenset({"SIGNAL", "CLEAR", "UNATTESTED"}),
    "IDENTITY": frozenset({"CREDITABLE", "INPUT_ONLY", "UNUSABLE"}),
    "GROUNDING": frozenset({"GROUND", "REJECT", "ESCALATE"}),
    "MUTATION": frozenset({"ATTESTED", "REJECT", "UNATTESTED"}),
}

#: Verdicts meaning "this fact could not be attested at all". Absence of a precondition is
#: never a pass — it routes to a human, exactly like ``grounding_verdict``'s rule 1.
ESCALATING_VERDICTS = frozenset({"REFUSE", "UNATTESTED", "UNUSABLE", "ESCALATE"})

#: Verdicts meaning "an engine attested a fact that contradicts the claim".
REJECTING_VERDICTS = frozenset({"BLOCK", "REJECT", "INPUT_ONLY"})

#: The pass-level verdict space — deliberately the SAME three tokens ``grounding_verdict``
#: already returns, in the same priority order. The grounding pass is not a judge and invents
#: no verdict vocabulary of its own.
PASS_VERDICTS: tuple[str, ...] = ("GROUND", "REJECT", "ESCALATE")

#: DESIGN §4's signal-trigger table — CLOSED. The stack-head pass runs unconditionally; at
#: OTHER gates the agent fires only when an engine flags one of exactly these four. Adding a
#: trigger is a DESIGN change (telemetry-informed promotion is tracked in BL-N24), not a code
#: edit — so the table is data here and the closure is asserted by test.
SIGNAL_TRIGGERS: tuple[tuple[str, str, str], ...] = (
    ("reuse-claim-phrase", "S2",
     "a reuse-claim trigger phrase in gated prose (truth_signals.REUSE_TRIGGER_PHRASES)"),
    ("unattestable-done", "B2/B4",
     "a DONE claim no record set can attest (absent/stale/wrong-run evidence)"),
    ("research-finding", "grounding_verdict",
     "a kata-research finding about to be folded (the injected-knowledge L2 gate)"),
    ("resolved-but-unread-citation", "B5",
     "a citation that RESOLVES but whose support was never read (existence is not support)"),
)

#: §3.6's declared cap: all lines when <= N, else sample N and RECORD the sampling.
MUTATION_SAMPLE_DEFAULT = 5


class GroundingBundleError(ValueError):
    """Raised when the bundle handed to the engine is malformed.

    A caller error, never a finding. A FINDING is a row in the table; this exception means the
    engine was handed something it may not attest at all — refusal, never a permissive default.
    """


# ---------------------------------------------------------------------------
# Row construction
# ---------------------------------------------------------------------------


def fact_row(
    *,
    tier: str,
    detector: str,
    row_class: str,
    verdict: str,
    subject: str,
    detail: str,
    attested_by: str,
    limits: Sequence[str] = (),
    provenance: Sequence[str] = (),
) -> dict:
    """Build one validated fact-table row. Pure; key order fixed; list fields sorted.

    ``blocking`` is DERIVED (never a parameter): a SIGNAL-tier row can never be blocking —
    the invariant ``truth_signals.assert_non_blocking`` enforces at the producer survives the
    promotion here — and any other tier's row is blocking iff its verdict is in
    :data:`REJECTING_VERDICTS` or :data:`ESCALATING_VERDICTS`.

    Fail-closed (D136): an unknown ``tier``, or a ``verdict`` outside that tier's closed
    grammar, RAISES. There is no "unknown ⇒ treat as informational" path — that is precisely
    how an off-enum token would launder itself past the roll-up.
    """
    legal = TIER_VERDICTS.get(tier)
    if legal is None:
        raise GroundingBundleError(
            f"grounding_gate: unknown fact-row tier {tier!r}; legal: {sorted(TIER_VERDICTS)}"
        )
    if verdict not in legal:
        raise GroundingBundleError(
            f"grounding_gate: verdict {verdict!r} is not legal for tier {tier!r}; "
            f"legal: {sorted(legal)} (D136 — no silent permissive default)"
        )
    blocking = tier != "SIGNAL" and verdict in (REJECTING_VERDICTS | ESCALATING_VERDICTS)
    return {
        "attestedBy": attested_by,
        "blocking": blocking,
        "class": row_class,
        "detail": detail,
        "detector": detector,
        "humility": HUMILITY_RULE,
        "limits": sorted(limits),
        "provenance": sorted(provenance),
        "schema": FACT_ROW_SCHEMA,
        "subject": subject,
        "tier": tier,
        "verdict": verdict,
    }


def _row_sort_key(row: Mapping) -> tuple:
    """Explicit total order over rows (Determinism Doctrine law 10 — ties never float)."""
    return (
        str(row.get("tier", "")),
        str(row.get("detector", "")),
        str(row.get("class", "")),
        str(row.get("subject", "")),
        str(row.get("verdict", "")),
        str(row.get("detail", "")),
    )


# ---------------------------------------------------------------------------
# Promotion — producer outputs become fact rows
# ---------------------------------------------------------------------------


def promote_signal_row(row: Mapping) -> dict:
    """Promote one ``truth_signals`` row (``v1-provisional``) into the v1 fact row.

    The reconciliation, concretely: every one of the producer's ten keys is carried with
    identical semantics; ``tier`` and ``attestedBy`` are added; the ORIGIN schema is preserved
    in ``provenance`` so dropping the provisional marker does not erase the lineage.

    Fail-closed: a row whose ``schema`` is not in :data:`RECONCILED_ROW_SCHEMAS` is REFUSED,
    and a row arriving marked ``blocking: True`` is REFUSED — signals never block, and a
    promotion that could launder one into a blocking row would dissolve that invariant at the
    boundary this module owns.
    """
    schema = row.get("schema")
    if schema not in RECONCILED_ROW_SCHEMAS:
        raise GroundingBundleError(
            f"grounding_gate: signal row carries unreconciled schema {schema!r}; "
            f"reconciled: {list(RECONCILED_ROW_SCHEMAS)}"
        )
    if row.get("blocking"):
        raise GroundingBundleError(
            f"grounding_gate: signal row is marked blocking — signals never block: {row!r}"
        )
    provenance = list(row.get("provenance") or [])
    provenance.append(f"origin-schema:{schema}")
    return fact_row(
        tier="SIGNAL",
        detector=str(row.get("detector", "")),
        row_class=str(row.get("class", "")),
        verdict=str(row.get("verdict", "")),
        subject=str(row.get("subject", "")),
        detail=str(row.get("detail", "")),
        attested_by="truth_signals",
        limits=list(row.get("limits") or []),
        provenance=provenance,
    )


def detector_rows(report: Mapping) -> list[dict]:
    """Promote one ``truth_serum.DetectorReport.to_dict()`` payload into fact rows.

    Emits the report's own verdict row (so a REFUSE or a ZERO_CANDIDATE is a first-class fact
    and not an empty finding list a judge could read as "clean"), plus one row per finding and
    one SIGNAL-tier row per routed signal — E3's never-silently-suppresses routing survives the
    promotion, so a judge sees the suspected-legitimacy cases the detector deliberately did NOT
    suppress.
    """
    detector = str(report.get("detector", ""))
    verdict = str(report.get("verdict", ""))
    findings = list(report.get("findings") or [])
    scanned = report.get("candidates_scanned", 0)
    files = list(report.get("files_scanned") or [])
    notes = [str(n) for n in (report.get("notes") or [])]

    if verdict == "REFUSE":
        detail = f"REFUSES to certify: {report.get('refusal_reason')}"
    elif verdict == "ZERO_CANDIDATE":
        detail = (
            f"scanned {len(files)} file(s) and found ZERO candidates — reported as "
            "zero-candidate, NEVER as 'all resolve'"
        )
    else:
        detail = (
            f"{verdict}: {len(findings)} finding(s) over {scanned} candidate(s) in "
            f"{len(files)} file(s)"
        )

    rows = [fact_row(
        tier="BLOCKING",
        detector=detector,
        row_class="detector-verdict",
        verdict=verdict,
        subject=f"<{detector}>",
        detail=f"{detail}. {HUMILITY_RULE}",
        attested_by="truth_serum",
        limits=notes,
        provenance=files,
    )]
    for finding in findings:
        rows.append(fact_row(
            tier="BLOCKING",
            detector=detector,
            row_class=f"finding:{finding.get('family')}",
            verdict="BLOCK",
            subject=f"{finding.get('path')}:{finding.get('line')}",
            detail=str(finding.get("message", "")),
            attested_by="truth_serum",
            provenance=[str(finding.get("symbol"))] if finding.get("symbol") else [],
        ))
    for signal in report.get("signals") or []:
        rows.append(fact_row(
            tier="SIGNAL",
            detector=detector,
            row_class=f"routed-signal:{signal.get('family')}",
            verdict="SIGNAL",
            subject=f"{signal.get('path')}:{signal.get('line')}",
            detail=str(signal.get("message", "")),
            attested_by="truth_serum",
        ))
    return rows


def identity_rows(
    name: str,
    result_json: Mapping | None,
    expected_sha: str | None,
    expected_run_id: str | None,
) -> list[dict]:
    """The evidence-identity leg — RE-DERIVED here, never taken on the bundle's word.

    Routes the artifact through ``run_result.classify_evidence`` (TM-D5 / R-H2: SHA fresh AND
    runId exact) and renders its role as a fact row. ``run_result``'s three roles map to the
    IDENTITY tier's three verdicts: ``gate-evidence`` -> ``CREDITABLE``, ``input`` ->
    ``INPUT_ONLY`` (a real artifact, legal to consume, never creditable as THIS run's gate),
    ``unusable`` -> ``UNUSABLE`` (nothing to classify — a refusal, never a pass).

    The run-membership law travels verbatim on the row (``run_result.RUN_MEMBERSHIP_LAW`` via
    the classification's ``law`` field) so a consumer restates it rather than paraphrasing it.
    """
    classification = classify_evidence(
        dict(result_json) if isinstance(result_json, Mapping) else None,
        expected_sha,
        expected_run_id,
    )
    role_to_verdict = {
        "gate-evidence": "CREDITABLE",
        "input": "INPUT_ONLY",
        "unusable": "UNUSABLE",
    }
    verdict = role_to_verdict[classification["role"]]
    reason = classification["reason"] or "SHA fresh AND runId exact"
    provenance = [f"law:{classification['law']}"]
    if classification.get("originRunId"):
        provenance.append(f"originRunId:{classification['originRunId']}")
    if classification.get("resultSha"):
        provenance.append(f"resultSha:{classification['resultSha']}")
    return [fact_row(
        tier="IDENTITY",
        detector="B4",
        row_class="evidence-identity",
        verdict=verdict,
        subject=name,
        detail=f"role={classification['role']}; {reason}",
        attested_by="run_result.classify_evidence",
        provenance=provenance,
    )]


def grounding_rows(verdicts: Iterable[Mapping]) -> list[dict]:
    """Promote ``build_verdict`` outputs (the injected-knowledge L2 gate) into fact rows."""
    rows: list[dict] = []
    for entry in verdicts:
        finding = entry.get("finding") or {}
        rows.append(fact_row(
            tier="GROUNDING",
            detector="grounding_verdict",
            row_class="research-finding",
            verdict=str(entry.get("verdict", "")),
            subject=str(finding.get("source") or finding.get("claim") or "<finding>"),
            detail=str(entry.get("evidence", "")),
            attested_by="grounding_gate.grounding_verdict",
            provenance=[f"groundsToPlan:{finding.get('groundsToPlan')}"]
            if finding.get("groundsToPlan") else [],
        ))
    return rows


# ---------------------------------------------------------------------------
# R-M10 — the stack-head mutation attestation
# ---------------------------------------------------------------------------


def _spec_sort_key(spec: Mapping) -> tuple:
    """DESIGN §3.6's compile specification: ``(file path, line number)`` ascending.

    A spec that carries no ``line`` sorts at line 0 and breaks its ties on the asserted line's
    TEXT — declared here rather than left to insertion order, so the order stays TOTAL (law 10)
    for the record set shapes that exist today (``mutation_run.prove_many`` specs carry the
    line's text, not its number).
    """
    return (
        str(spec.get("source_path", "")),
        int(spec.get("line", 0) or 0),
        str(spec.get("asserted_line", "")),
    )


def sample_mutation_specs(
    specs: Sequence[Mapping],
    size: int = MUTATION_SAMPLE_DEFAULT,
) -> dict:
    """The declared cap, §3.6: all lines when <= N; beyond that sample N and RECORD it.

    Deterministic by construction — an explicit total order and a take, no randomness
    (Determinism Doctrine laws 9/10). Returns
    ``{"sampled": [...], "total": int, "size": int, "sampled_count": int, "truncated": bool,
    "sortKey": "(file path, line number) ascending", "record": "<human line>"}``.

    ``truncated`` and ``record`` exist so **no silent truncation** is structural: a caller that
    serializes this dict has recorded the sampling whether or not it reads the flag.
    """
    if size < 1:
        raise GroundingBundleError(
            f"grounding_gate: mutation sample size must be >= 1, got {size} "
            "(a zero-sample attestation would certify nothing while looking like a pass)"
        )
    ordered = sorted(specs, key=_spec_sort_key)
    sampled = ordered[:size]
    truncated = len(ordered) > len(sampled)
    return {
        "record": (
            f"sampled {len(sampled)} of {len(ordered)} asserted line(s), cap N={size}, "
            "sort key (file path, line number) ascending — "
            + ("TRUNCATED (recorded, never silent)" if truncated else "no truncation")
        ),
        "sampleSize": size,
        "sampled": [dict(s) for s in sampled],
        "sampledCount": len(sampled),
        "sortKey": "(file path, line number) ascending",
        "total": len(ordered),
        "truncated": truncated,
    }


def attest_mutation_set(
    *,
    planned_task_ids: Sequence[str],
    task_records: Mapping[str, Mapping | None],
    expected_sha: str | None,
    expected_run_id: str | None,
    sample_specs: Sequence[Mapping] = (),
    sample_results: Sequence[Mapping] = (),
    sample_source: str = "supplied",
    sample_size: int = MUTATION_SAMPLE_DEFAULT,
) -> dict:
    """R-M10: attest the WHOLE mutation record set as the evaluator's precondition.

    Three legs, each a row, none of them optional:

    * **present** — every planned task has a mutation record. Absent ⇒ ``REJECT``.
    * **current** — each record's accompanying RESULT.json is creditable gate evidence for
      THIS run (``run_result.classify_evidence``: SHA fresh AND runId exact). Not creditable
      ⇒ ``REJECT``, naming the reason.
    * **per-task complete** — the record's ``records`` list is non-empty and every entry is
      ``nonVacuous``. Empty ⇒ ``UNATTESTED`` (nothing scanned certifies nothing); a vacuous
      entry ⇒ ``REJECT``.

    Plus the sampled re-run: the sampled subset must have BITTEN (``testWentRed`` and
    ``nonVacuous`` both true). No sample at all ⇒ ``UNATTESTED`` — the attestation is not
    satisfied by records alone, which is the entire point of R-M10 (the worker-union hole
    closes at a named seam).

    Anti-vacuity companion (TM-D3): an EMPTY planned-task set returns a single ``UNATTESTED``
    row. Zero tasks is never "all tasks attested".

    ``sample_source`` is carried into every sample row's detail and is an honesty label, not a
    behaviour switch: ``"engine-rerun"`` means this process re-ran the subset via
    ``mutation_run``; ``"supplied"`` means the agent ran it and the engine attests only the
    CONSISTENCY of what it was handed. The two are never reported as the same fact.

    Honest residual, carried verbatim from DESIGN §3.6: the re-run proves the worker's CLAIMED
    mutation set bites — **claimed-set completeness stays worker-asserted**.
    """
    rows: list[dict] = []
    residual = (
        "the re-run proves the worker's CLAIMED mutation set bites — claimed-set "
        "completeness stays worker-asserted (DESIGN §3.6)"
    )

    if not planned_task_ids:
        rows.append(fact_row(
            tier="MUTATION",
            detector="B6",
            row_class="anti-vacuity",
            verdict="UNATTESTED",
            subject="<mutation-record-set>",
            detail=(
                "refusing to attest: the planned-task set is empty — zero tasks is never "
                "'all tasks attested'"
            ),
            attested_by="grounding_gate.attest_mutation_set",
            limits=[residual],
        ))
        sampling = sample_mutation_specs(sample_specs, sample_size)
        return {"rows": rows, "sampling": sampling, "sampleSource": sample_source,
                "verdict": "ESCALATE", "residual": residual}

    for task_id in sorted(set(str(t) for t in planned_task_ids)):
        record = task_records.get(task_id)
        if not isinstance(record, Mapping):
            rows.append(fact_row(
                tier="MUTATION",
                detector="B6",
                row_class="mutation-record-absent",
                verdict="REJECT",
                subject=task_id,
                detail="no mutation record for this planned task (present leg fails)",
                attested_by="grounding_gate.attest_mutation_set",
                limits=[residual],
            ))
            continue

        classification = classify_evidence(
            dict(record.get("result")) if isinstance(record.get("result"), Mapping) else None,
            expected_sha,
            expected_run_id,
        )
        if not classification["creditableAsGateEvidence"]:
            rows.append(fact_row(
                tier="MUTATION",
                detector="B6",
                row_class="mutation-record-not-current",
                verdict="REJECT",
                subject=task_id,
                detail=(
                    f"mutation record is not this run's gate evidence "
                    f"(role={classification['role']}, reason={classification['reason']})"
                ),
                attested_by="run_result.classify_evidence",
                limits=[residual],
            ))
            continue

        entries = record.get("records")
        if not isinstance(entries, list) or not entries:
            rows.append(fact_row(
                tier="MUTATION",
                detector="B6",
                row_class="mutation-record-empty",
                verdict="UNATTESTED",
                subject=task_id,
                detail="mutation record carries zero proved lines — nothing scanned, nothing certified",
                attested_by="grounding_gate.attest_mutation_set",
                limits=[residual],
            ))
            continue

        vacuous = [i for i, e in enumerate(entries) if not (isinstance(e, Mapping)
                                                           and e.get("nonVacuous") is True)]
        if vacuous:
            rows.append(fact_row(
                tier="MUTATION",
                detector="B6",
                row_class="mutation-record-vacuous",
                verdict="REJECT",
                subject=task_id,
                detail=f"{len(vacuous)} of {len(entries)} proved line(s) are VACUOUS (index {vacuous})",
                attested_by="grounding_gate.attest_mutation_set",
                limits=[residual],
            ))
            continue

        rows.append(fact_row(
            tier="MUTATION",
            detector="B6",
            row_class="mutation-record-attested",
            verdict="ATTESTED",
            subject=task_id,
            detail=(
                f"present + current + complete: {len(entries)} proved line(s), evidence "
                "creditable for this run"
            ),
            attested_by="grounding_gate.attest_mutation_set",
            limits=[residual],
        ))

    sampling = sample_mutation_specs(sample_specs, sample_size)
    sampled = sampling["sampled"]
    if not sampled:
        rows.append(fact_row(
            tier="MUTATION",
            detector="B6",
            row_class="mutation-sample-absent",
            verdict="UNATTESTED",
            subject="<mutation-sample>",
            detail=(
                "refusing to attest: no sampled subset was re-run against the gate command — "
                "R-M10 is not satisfied by records alone"
            ),
            attested_by="grounding_gate.attest_mutation_set",
            limits=[residual],
        ))
    elif len(sample_results) != len(sampled):
        rows.append(fact_row(
            tier="MUTATION",
            detector="B6",
            row_class="mutation-sample-incomplete",
            verdict="UNATTESTED",
            subject="<mutation-sample>",
            detail=(
                f"refusing to attest: {len(sample_results)} re-run result(s) for "
                f"{len(sampled)} sampled line(s) — an unmatched sample certifies nothing"
            ),
            attested_by="grounding_gate.attest_mutation_set",
            limits=[residual],
        ))
    else:
        for spec, result in zip(sampled, sample_results, strict=True):
            subject = f"{spec.get('source_path')}::{spec.get('asserted_line')}"
            bit = (isinstance(result, Mapping)
                   and result.get("testWentRed") is True
                   and result.get("nonVacuous") is True)
            rows.append(fact_row(
                tier="MUTATION",
                detector="B6",
                row_class="mutation-sample-bit" if bit else "mutation-sample-did-not-bite",
                verdict="ATTESTED" if bit else "REJECT",
                subject=subject,
                detail=(
                    ("the re-run went RED for this line" if bit
                     else "the re-run did NOT go red — the proof is vacuous for this line")
                    + f" [sampleSource={sample_source}]"
                ),
                attested_by=(
                    "mutation_run.prove_many" if sample_source == "engine-rerun"
                    else "grounding_gate.attest_mutation_set (agent-supplied re-run result)"
                ),
                limits=[residual],
                provenance=[f"sampleSource:{sample_source}"],
            ))

    return {
        "residual": residual,
        "rows": rows,
        "sampleSource": sample_source,
        "sampling": sampling,
        "verdict": roll_up(rows),
    }


# ---------------------------------------------------------------------------
# Roll-up + table assembly
# ---------------------------------------------------------------------------


def roll_up(rows: Sequence[Mapping]) -> str:
    """The pass-level verdict over fact rows, in ``grounding_verdict``'s priority order.

    1. Cannot-attest anywhere (:data:`ESCALATING_VERDICTS`) ⇒ ``ESCALATE``.
    2. An engine attested a contradiction (:data:`REJECTING_VERDICTS`) ⇒ ``REJECT``.
    3. Otherwise ⇒ ``GROUND``.

    **SIGNAL-tier rows contribute NOTHING.** ``truth_signals`` is structurally incapable of
    returning a blocking verdict, and a roll-up that let one escalate a gate would promote a
    heuristic into a refusal — the facade-one-level-up failure the trust model exists to
    prevent. An UNATTESTED signal scan is a fact about the scan, not a gate event.

    An empty considered-set is ``ESCALATE``, never ``GROUND``: ``all([])`` is the vacuous-pass
    shape ``write_grounding`` already refuses (Q-3 / D136).
    """
    considered = [r for r in rows if r.get("tier") != "SIGNAL"]
    if not considered:
        return "ESCALATE"
    verdicts = {str(r.get("verdict")) for r in considered}
    if verdicts & ESCALATING_VERDICTS:
        return "ESCALATE"
    if verdicts & REJECTING_VERDICTS:
        return "REJECT"
    return "GROUND"


def build_fact_table(
    *,
    target: Mapping,
    rows: Sequence[Mapping],
    mutation: Mapping | None = None,
) -> dict:
    """Assemble the attested fact table judges consume (TM-E2).

    ``target`` names WHAT was attested — ``{runId, sha, taskId, gate}``; the identity of the
    table itself, so a judge holding it can tell whether it belongs to the run being gated.
    ``mutation`` is :func:`attest_mutation_set`'s return (its rows are expected to be included
    in ``rows`` already; the block is carried whole so the SAMPLING RECORD travels with the
    verdict rather than being reconstructable only from prose).
    """
    ordered = sorted((dict(r) for r in rows), key=_row_sort_key)
    blocking = [r for r in ordered if r.get("blocking")]
    return {
        "blockingRowCount": len(blocking),
        "humility": HUMILITY_LINE,
        "humilityRule": HUMILITY_RULE,
        "mutationAttestation": dict(mutation) if mutation is not None else None,
        "overheadRecord": OVERHEAD_RECORD,
        "rowCount": len(ordered),
        "rowSchema": FACT_ROW_SCHEMA,
        "rows": ordered,
        "scopeBoundary": SCOPE_BOUNDARY,
        "schema": FACT_TABLE_SCHEMA,
        "target": dict(target),
        "vacuous": not [r for r in ordered if r.get("tier") != "SIGNAL"],
        "verdict": roll_up(ordered),
    }


def render_fact_table(table: Mapping) -> str:
    """Canonical JSON for the fact table — ``sort_keys=True`` (Determinism Doctrine law 5)."""
    return json.dumps(table, sort_keys=True, ensure_ascii=False, indent=2) + "\n"


def parse_fact_table(payload: str | bytes | Mapping) -> dict:
    """Validate a rendered fact table and return it — the round-trip half of the contract.

    Fail-closed on every structural defect: unparseable JSON, a wrong/absent ``schema``, a row
    carrying a foreign ``schema``, an off-enum tier/verdict, or a ``verdict`` field that does
    not equal the roll-up recomputed from the rows. That last check is the load-bearing one:
    a hand-edited table claiming ``GROUND`` over REJECT rows is REFUSED rather than believed —
    the table is recomputed, never shape-checked (Determinism Doctrine law 13).
    """
    if isinstance(payload, (str, bytes)):
        try:
            table = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise GroundingBundleError(f"grounding_gate: fact table is not valid JSON: {exc}") from exc
    else:
        table = dict(payload)

    if not isinstance(table, dict):
        raise GroundingBundleError("grounding_gate: fact table must be a JSON object")
    if table.get("schema") != FACT_TABLE_SCHEMA:
        raise GroundingBundleError(
            f"grounding_gate: fact table schema {table.get('schema')!r} != {FACT_TABLE_SCHEMA!r}"
        )
    rows = table.get("rows")
    if not isinstance(rows, list):
        raise GroundingBundleError("grounding_gate: fact table has no rows list")
    for row in rows:
        if not isinstance(row, dict):
            raise GroundingBundleError(f"grounding_gate: fact row is not an object: {row!r}")
        if row.get("schema") != FACT_ROW_SCHEMA:
            raise GroundingBundleError(
                f"grounding_gate: fact row schema {row.get('schema')!r} != {FACT_ROW_SCHEMA!r}"
            )
        legal = TIER_VERDICTS.get(str(row.get("tier")))
        if legal is None:
            raise GroundingBundleError(f"grounding_gate: fact row has unknown tier {row.get('tier')!r}")
        if row.get("verdict") not in legal:
            raise GroundingBundleError(
                f"grounding_gate: fact row verdict {row.get('verdict')!r} illegal for tier "
                f"{row.get('tier')!r}"
            )
    recomputed = roll_up(rows)
    if table.get("verdict") != recomputed:
        raise GroundingBundleError(
            f"grounding_gate: fact table claims verdict {table.get('verdict')!r} but its rows "
            f"recompute to {recomputed!r} — REFUSED (recompute, don't shape-check)"
        )
    return table


def write_fact_table(kata_dir: str, table: Mapping) -> str:
    """Write ``<kata_dir>/fact-table.json`` (validated first) and return the absolute path.

    Atomic (D159) for the same reason ``write_grounding`` is: a judge may be reading the table
    while the pass re-emits it, and a truncate-then-write leaves a partial-file window.
    The table is routed through :func:`parse_fact_table` BEFORE the write — the engine never
    persists a table it would refuse to read back.
    """
    parse_fact_table(table)
    out = _safe_path(kata_dir)
    out.mkdir(parents=True, exist_ok=True)
    table_path = out / "fact-table.json"
    atomic_write_text(table_path, render_fact_table(table), encoding="utf-8")
    return str(table_path)


# ---------------------------------------------------------------------------
# The stack-head pass — bundle in, attested table out
# ---------------------------------------------------------------------------


def run_stack_head_pass(bundle: Mapping, *, rerun_sample: bool = False) -> dict:
    """Compose one grounding pass over a producer-output bundle and return the fact table.

    Bundle keys (all optional except ``target``)::

        target          {"runId","sha","taskId","gate"}   — identity of what is attested
        detectorInputs  {"repoRoot","graph","modifiedFiles","artifacts"} — RUN the B-detectors
        detectors       [ truth_serum.DetectorReport.to_dict(), ... ]
        signals         [ truth_signals row, ... ]
        verdicts        [ grounding_gate.build_verdict(...), ... ]
        identity        [ {"name": str, "result": <RESULT.json dict>}, ... ]
        mutation        {"plannedTaskIds","taskRecords","sampleSpecs","sampleResults",
                         "sampleSize"}

    ``detectorInputs`` is the AC-10 leg: given it, this function IMPORTS and RUNS
    ``truth_serum.run_blocking_detectors`` rather than trusting reports from the bundle, so the
    blocking facts in the table are produced by the engine in-process. ``rerun_sample`` is the
    R-M10 leg: the sampled subset is re-run here via ``mutation_run.prove_many`` (the registered
    sink) and labeled ``engine-rerun``; without it, supplied results are attested and labeled
    ``supplied``. Both imports are LAZY — the pure library path stays stdlib-only.
    """
    target = bundle.get("target")
    if not isinstance(target, Mapping) or not target.get("runId") or not target.get("sha"):
        raise GroundingBundleError(
            "grounding_gate: bundle 'target' must carry at least runId and sha — a table with "
            "no identity cannot be attested to a run (anti-vacuity)"
        )
    expected_sha = str(target.get("sha"))
    expected_run_id = str(target.get("runId"))

    rows: list[dict] = []

    detector_reports = list(bundle.get("detectors") or [])
    inputs = bundle.get("detectorInputs")
    if isinstance(inputs, Mapping):
        import truth_serum  # noqa: PLC0415 — lazy: keeps the pure path free of the graph stack

        produced = truth_serum.run_blocking_detectors(
            inputs.get("repoRoot", "."),
            inputs.get("graph"),
            inputs.get("modifiedFiles") or (),
            inputs.get("artifacts") or (),
        )
        detector_reports.extend(report.to_dict() for _, report in sorted(produced.items()))
    for report in detector_reports:
        rows.extend(detector_rows(report))

    for row in bundle.get("signals") or []:
        rows.append(promote_signal_row(row))

    rows.extend(grounding_rows(bundle.get("verdicts") or []))

    for artifact in bundle.get("identity") or []:
        rows.extend(identity_rows(
            str(artifact.get("name", "<artifact>")),
            artifact.get("result"),
            expected_sha,
            expected_run_id,
        ))

    mutation_block = bundle.get("mutation")
    attestation: dict | None = None
    if isinstance(mutation_block, Mapping):
        sample_specs = list(mutation_block.get("sampleSpecs") or [])
        sample_size = int(mutation_block.get("sampleSize") or MUTATION_SAMPLE_DEFAULT)
        sample_results = list(mutation_block.get("sampleResults") or [])
        sample_source = "supplied"
        if rerun_sample:
            import mutation_run  # noqa: PLC0415 — lazy: the registered sink, CLI path only

            chosen = sample_mutation_specs(sample_specs, sample_size)["sampled"]
            sample_results = mutation_run.prove_many([
                {k: v for k, v in spec.items() if k != "line"} for spec in chosen
            ])
            sample_source = "engine-rerun"
        attestation = attest_mutation_set(
            planned_task_ids=list(mutation_block.get("plannedTaskIds") or []),
            task_records=dict(mutation_block.get("taskRecords") or {}),
            expected_sha=expected_sha,
            expected_run_id=expected_run_id,
            sample_specs=sample_specs,
            sample_results=sample_results,
            sample_source=sample_source,
            sample_size=sample_size,
        )
        rows.extend(attestation["rows"])

    return build_fact_table(target=target, rows=rows, mutation=attestation)


# ---------------------------------------------------------------------------
# CLI entry-point
# ---------------------------------------------------------------------------

#: CLI exit codes — RAW and meaningful: the pass verdict IS the exit status, so a caller that
#: reads only ``$?`` still fails closed (a refusal never exits 0).
_EXIT_CODES = {"GROUND": 0, "REJECT": 1, "ESCALATE": 2}


def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="grounding_gate",
        description=(
            "Run the stack-head grounding pass: compose engine outputs into the attested "
            "fact table judges consume, and attest the mutation record set (R-M10). "
            "Agent proposes, engine attests."
        ),
    )
    p.add_argument("--bundle", required=True, metavar="PATH",
                   help="JSON bundle of producer outputs (see run_stack_head_pass)")
    p.add_argument("--out", default=".kata", metavar="DIR",
                   help="Output directory for fact-table.json (default: .kata)")
    p.add_argument("--mutation-rerun", action="store_true",
                   help="Re-run the sampled mutation subset in-process via mutation_run "
                        "(R-M10 engine-rerun); without it, supplied results are attested and "
                        "labeled as agent-supplied")
    return p


def main(argv: Sequence[str] | None = None) -> int:
    """CLI: emit the attested fact table. Returns 0 GROUND / 1 REJECT / 2 ESCALATE."""
    args = _build_parser().parse_args(list(argv) if argv is not None else None)
    bundle = json.loads(_safe_path(args.bundle).read_text(encoding="utf-8"))
    table = run_stack_head_pass(bundle, rerun_sample=args.mutation_rerun)
    path = write_fact_table(args.out, table)
    print(f"VERDICT: {table['verdict']}")
    print(f"rows={table['rowCount']} blocking={table['blockingRowCount']} -> {path}")
    print(HUMILITY_LINE)
    return _EXIT_CODES[table["verdict"]]


if __name__ == "__main__":  # pragma: no cover - CLI wiring
    sys.exit(main())
