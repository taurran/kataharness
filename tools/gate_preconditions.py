"""gate_preconditions.py — every gate refuses without attested facts (DESIGN §3.3).

The §3.3 gate-precondition map, TRANSCRIBED into an engine.  Each gate class in the
inventory (`.planning/specs/trust-model/evidence/gate-inventory.md`) gains a fact set it
must hold before it may proceed, and a gate that cannot cite the fact **REFUSES** — it
never warns, never degrades, never proceeds with a note.

Three laws are load-bearing here and each is enforced, not described:

1. **Refuse-not-warn** (the locked house shape, TM-D4).  The status enum below has NO
   ``warn`` member.  A precondition either holds, is REFUSED, is declared
   ``honor-system`` (an activation state, recorded, never blocking), or is
   ``legally-absent``.  There is no rung between "held" and "refused" for a fact the run
   legally owes.
2. **The never-a-de-facto-mandate law** (pass-1 residual 4).  *No gate requires a grill
   artifact of a run that legally has none.*  A ``grillDepth: skip`` run (D71) owes no
   grill ledger and no convergence-pass record, and this engine records that as
   ``legally-absent`` — a stated fact about the run's shape, never a silent pass and
   never a refusal.
3. **Activation ordering is part of the precondition itself** (§3.3, §3.6, R-M6).  The
   mutation precondition activates PER PLATFORM only off BL-X14's **recorded** closure,
   and the per-judge tripwire preconditions activate off ``tripwire_check``'s **derived**
   activation state.  Both activation tables READ RECORDED STATE.  Neither reads a config
   flag, a constant in this file, or a caller's assertion — activating early is drift
   (PLAN escalation E8), so the default in every unreadable case is NOT-active.

**Refusals are reasoned, recorded events (TM-G1's data half).**  Every refusal names its
fact class, that class's SYSTEM OF RECORD (D134 — reusing ``kata_close.SYSTEM_OF_RECORD``
where the class already has one), the reason, and the remedy.  Per the R14 rider: a
refusal's narration is a DESCRIPTION of the legal path, **never evidence the path was
taken** — the record cites the fact class and its system of record so a reader goes to the
artifact, not to this message.

**Purity.**  The gate functions are PURE over their fact bundles: no clock (``utc`` is
injected), no subprocess, no git, no filesystem.  The two activation readers
(:func:`read_mutation_closure`, :func:`judge_activation`) and the cursor recorder are the
only I/O in the module, and they are separated precisely so the gates stay testable and
deterministic (Determinism Doctrine).  **This module spawns no subprocess and calls no
``eval``/``exec``** — it needs no ``protocol/exec-safety.md`` sink row (verified against
the mechanical scan in ``tests/test_exec_safety.py``).

The B1/B3 input-set ruling (DEF-16 / the Loop-A spot-audit)
-----------------------------------------------------------
**RULED HERE, because the frozen PLAN routes the question to this task:** a task gate's
B1/B3 detector pass is credited **only over the TASK-MODIFIED file set** — the files that
task changed against its own baseline — never over the whole tree.  :func:`task_gate`
enforces it: a report whose ``files_scanned`` is not a subset of the declared modified set
is REFUSED (fact class ``detector-pass``), because a whole-tree scan answers a different
question than the one the task gate asks.

Two consequences, stated rather than smuggled:

* The three live tree findings (``drift_gate.py:79``, ``iac_apply.py:815``,
  ``kata_web.py:620``) block nothing, because no task's modified set contains them unless
  that task modifies them — at which point they are that task's findings and its problem.
* The ``truth_serum`` self-block (DEF-16) is **CORRECT behaviour under this ruling, not a
  false positive**: a task that modifies ``tools/truth_serum.py`` really does have debt
  markers in its own modified set.  This module therefore adds **no self-exemption and no
  new suppressor class** — E3 forbids inventing one, and DEF-16's own recorded fallback is
  a ``protocol/deferral.md`` carve-out through its own two-step.  The refusal stands and
  routes to the ledger.

Public API
----------
Gate fact sets (pure)
    :func:`freeze_gate` · :func:`task_gate` · :func:`wave_gate` · :func:`final_gate` ·
    :func:`convergence_gate` · :func:`sprint_stop_gate`
Activation tables (read recorded state)
    :func:`read_mutation_closure` · :func:`mutation_activation` · :func:`judge_activation`
Recording
    :func:`precondition_record` · :func:`format_precondition_line` ·
    :func:`record_preconditions` · :func:`require`
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import kata_board as _kb
import kata_close as _kc
import run_result as _rr
import tripwire_check as _tw
import truth_serum as _ts

# ---------------------------------------------------------------------------
# The laws, pinned as constants so a consumer quotes them rather than paraphrasing
# (the RUN_MEMBERSHIP_LAW precedent, run_result.py:86).
# ---------------------------------------------------------------------------

REFUSE_NOT_WARN_LAW = (
    "ALL gates gain a fact-artifact precondition and the shape is REFUSE-NOT-WARN (the "
    "locked house shape, DESIGN §3.3/TM-D4): a gate that cannot cite the fact refuses. "
    "There is no warn rung, no soft mode, and no proceed-with-a-note; the status enum "
    "carries no 'warn' member precisely so one cannot be introduced by a value."
)

NEVER_A_DE_FACTO_MANDATE_LAW = (
    "The never-a-de-facto-mandate law carries into every per-gate fact-set: no gate "
    "requires a grill artifact of a run that legally has none (D71 shapes — a "
    "grillDepth: skip run leans entirely on the autonomous-reliability floor). A fact a "
    "run legally does not owe is recorded as LEGALLY-ABSENT: a stated fact about the "
    "run's shape, never a silent pass and never a refusal."
)

ACTIVATION_ORDERING_LAW = (
    "Activation ordering is part of the precondition itself, never a silent soft mode: "
    "the mutation precondition activates PER PLATFORM only after BL-X14's closure is "
    "RECORDED for that platform (DESIGN §3.6, PLAN escalation E8 — 'no Linux task gate "
    "fail-closes on a Broken prover'; activating early is drift), and per-judge tripwire "
    "preconditions activate per R-M6. Both tables read RECORDED closure/corpus state — "
    "never a config assertion, never a constant in the engine, never a caller's claim."
)

# ---------------------------------------------------------------------------
# Closed enumerations
# ---------------------------------------------------------------------------

#: The gate classes this engine covers — the §3.3 map's rows.
GATE_FREEZE = "freeze-gate"
GATE_TASK = "task-gate"
GATE_WAVE = "wave-gate"
GATE_FINAL = "final-gate"
GATE_CONVERGENCE = "grill-convergence"
GATE_SPRINT_STOP = "sprint-stop-gate"

GATES: tuple[str, ...] = (
    GATE_FREEZE, GATE_TASK, GATE_WAVE, GATE_FINAL, GATE_CONVERGENCE, GATE_SPRINT_STOP,
)

#: Per-fact statuses.  **There is deliberately no ``warn``** (REFUSE_NOT_WARN_LAW).
STATUS_SATISFIED = "satisfied"
STATUS_REFUSED = "refused"
#: The precondition exists but its activation table says NOT-YET-ACTIVE on this
#: platform/judge — recorded, declared, and never blocking (R-M6 / E8).
STATUS_HONOR_SYSTEM = _tw.ACTIVATION_HONOR_SYSTEM  # "honor-system" — ONE vocabulary
#: The run legally has no such artifact (NEVER_A_DE_FACTO_MANDATE_LAW).
STATUS_LEGALLY_ABSENT = "legally-absent"

STATUSES: tuple[str, ...] = (
    STATUS_SATISFIED, STATUS_REFUSED, STATUS_HONOR_SYSTEM, STATUS_LEGALLY_ABSENT,
)

#: Gate-level verdicts.  Also warn-free, for the same reason.
VERDICT_SATISFIED = "SATISFIED"
VERDICT_REFUSED = "REFUSED"
VERDICTS: tuple[str, ...] = (VERDICT_SATISFIED, VERDICT_REFUSED)

#: Activation values for a precondition whose ordering is gated (mutation, tripwires).
ACTIVATION_ACTIVE = "active"
ACTIVATION_HONOR_SYSTEM = _tw.ACTIVATION_HONOR_SYSTEM

#: Grill depths (D71) — pinned from ``intent_scaffold._VALID_GRILL_DEPTH``.  ``skip`` is
#: the depth that makes grill artifacts legally absent.
GRILL_DEPTHS: frozenset[str] = frozenset({"skip", "light", "standard", "full"})
GRILL_DEPTH_NO_ARTIFACT = "skip"
#: Depths whose convergence record must prove TWO distinct dispatches (§3.3's Advanced
#: double-pass row).  ``full`` maps to the advanced grill tier (docs/DESIGN.md, D71).
GRILL_DEPTHS_DOUBLE_PASS: frozenset[str] = frozenset({"full"})

#: Record kind for the cursor NOTE (mirrors ``tripwire_check.RECORD_KIND_TRIPWIRE``).
RECORD_KIND_PRECONDITIONS = "gate-preconditions"
#: Default cursor identity for the recorded fact.
RECORD_AGENT = "gate-preconditions"


# ---------------------------------------------------------------------------
# Fact classes and their systems of record (D134)
# ---------------------------------------------------------------------------

#: Every fact class this engine can refuse on, mapped to the system of record a reader
#: must go to.  ``kata_close.SYSTEM_OF_RECORD`` is REUSED wherever the class already
#: exists there, so the close and the gates never drift into two vocabularies for one
#: fact (verified surface: kata_close.py:175 — task-done / task-evidence / deferral /
#: phase / verdict / provenance / resilience / closeout-decision / deferral-approval).
FACT_SYSTEM_OF_RECORD: dict[str, str] = dict(_kc.SYSTEM_OF_RECORD)
FACT_SYSTEM_OF_RECORD.update({
    "design": (
        "the frozen DESIGN document the run's plan serves — present-at-freeze is the fact; "
        "its content is the freeze act's subject, not this engine's."
    ),
    "plan": (
        "the frozen PLAN.md, parsed by kata_restore.parse_plan_tasks (the YAML frontmatter "
        "maps are AUTHORITATIVE for the task set; heading scraping is not a source)."
    ),
    "governing-ledger": (
        "the governing grill ledger's convergence status, read by "
        "kata_dispatch.ledger_status — a run that legally has no grill has no such record "
        "(NEVER_A_DE_FACTO_MANDATE_LAW)."
    ),
    "arm-registry": (
        "the tree run's committed arm registry (DESIGN §2.7) — required for tree runs only."
    ),
    "baseline-input": (
        "the green-at-fork baseline RESULT carried as an INPUT record "
        "(run_result.input_reference / run_result.BASELINE_INPUT_LAW): recorded with its "
        "origin runId and NEVER creditable as this run's gate evidence."
    ),
    "contract-edge-freeze": (
        "the frozen PLAN's builds_against: map and the contract-edge freeze artifacts it "
        "names — required only for a plan that declares contract edges."
    ),
    "verify-rerun": (
        "the task gate's own verify re-run RESULT.json, identity-checked through "
        "run_result.gate_evidence_is_creditable (SHA fresh AND runId exact — TM-D5/B4)."
    ),
    "lane": (
        "the task's footprint manifest (footprint.manifest -> withinFootprint / "
        "outOfFootprint) — the mechanical lane check, never a reading of the diff."
    ),
    "mutation-rerun": (
        "the ENGINE mutation re-run record for the task's OWN verify command (DESIGN "
        "§3.6): the orchestrator-triggered re-run of the worker's claimed mutation set, "
        "with any sampling recorded on the cursor — never a worker-reported union."
    ),
    "detector-pass": (
        "truth_serum's B1/B3 DetectorReports over the TASK-MODIFIED file set (the input-set "
        "ruling in this module's docstring); a REFUSE or BLOCK verdict is the detector's "
        "answer and this gate carries it, it does not overrule it."
    ),
    "task-gate-record": (
        "the per-task gate records emitted by this wave's member tasks — this engine's own "
        "task_gate reports, one per member."
    ),
    "integration-regate": (
        "the wave's integration re-gate RESULT.json, emitted on the integration branch "
        "after the wave's task branches merge."
    ),
    "judge-activation": (
        "tripwire_check.check_all's derived per-judge activation state (R-M6) — a corpus "
        "fact on disk, never a config assertion."
    ),
    "fact-table": (
        "the grounding-attested fact table (DESIGN §4 / tools/grounding_gate.py) that the "
        "W5 judge contracts consume."
    ),
    "mutation-attestation": (
        "the stack-head grounding pass's attestation of the WHOLE mutation record set "
        "(R-M10) — present + current + per-task complete — which the evaluator requires."
    ),
    "per-gate-counts": (
        "RESULT.json's gates[] blocks and countsScope (run_result.parse_gate_blocks — the "
        "BL-X13 fix); a no-counts result is unavailable counts, never 'zero failures'."
    ),
    "convergence-pass": (
        "the grill's convergence-pass record: the seam dispatch records proving a pass ran "
        "(and, at the Advanced double-pass depth, that TWO DISTINCT dispatches ran)."
    ),
    "persisted-verdict": (
        "the PERSISTED evaluate VERDICT record captured through the seam (DESIGN §1.6) — "
        "a conversational verdict value is not a record and is never credited."
    ),
})


class PreconditionError(ValueError):
    """A malformed precondition call — a programming error, never a gate outcome."""


class PreconditionRefused(Exception):
    """A gate's preconditions were not met.  Fail-closed: nothing proceeds on a refusal.

    Carries the ``report`` so a caller cites the RECORD (fact classes + systems of
    record) rather than this exception's message text — R14 rider: a refusal's narration
    is a DESCRIPTION of the legal path, never evidence the path was taken.
    """

    def __init__(self, message: str, *, report: "PreconditionReport"):
        super().__init__(message)
        self.report = report


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FactCheck:
    """One precondition's outcome — the atom every refusal is recorded as."""

    gate: str
    fact_class: str
    status: str
    reason: str
    system_of_record: str
    remedy: str = ""

    def __post_init__(self) -> None:
        # D-26: the invariants this class promises are enforced at the boundary.
        if self.gate not in GATES:
            raise PreconditionError(f"unknown gate {self.gate!r}; legal: {GATES}")
        if self.status not in STATUSES:
            raise PreconditionError(
                f"unknown status {self.status!r}; legal: {STATUSES} "
                "(there is deliberately no 'warn' — REFUSE_NOT_WARN_LAW)"
            )
        if not self.reason.strip():
            raise PreconditionError("every FactCheck carries a reason — a bare status is not a record")
        if self.status == STATUS_REFUSED and not self.remedy.strip():
            raise PreconditionError(
                "a REFUSED check must name the remedy: a refusal with no legal path is a "
                "dead end, not a gate"
            )

    def sort_key(self) -> tuple:
        """Explicit total order (Determinism Doctrine law 10 — ties never float)."""
        return (self.gate, self.fact_class, self.status, self.reason)

    def to_dict(self) -> dict[str, Any]:
        return {
            "factClass": self.fact_class,
            "gate": self.gate,
            "reason": self.reason,
            "remedy": self.remedy,
            "status": self.status,
            "systemOfRecord": self.system_of_record,
        }


@dataclass(frozen=True)
class PreconditionReport:
    """One gate's whole fact set — held, refused, honor-system, and legally-absent alike.

    ``verdict`` is ``REFUSED`` **iff** at least one check refused; the equivalence is
    enforced in ``__post_init__`` rather than left to callers, so a report cannot claim
    SATISFIED while carrying a refusal.
    """

    gate: str
    verdict: str
    checks: tuple[FactCheck, ...] = ()
    subject: str = ""
    utc: str | None = None
    law: str = field(default=REFUSE_NOT_WARN_LAW)

    def __post_init__(self) -> None:
        if self.gate not in GATES:
            raise PreconditionError(f"unknown gate {self.gate!r}; legal: {GATES}")
        if self.verdict not in VERDICTS:
            raise PreconditionError(f"unknown verdict {self.verdict!r}; legal: {VERDICTS}")
        if any(c.gate != self.gate for c in self.checks):
            raise PreconditionError("every check in a report must belong to the report's gate")
        refused = any(c.status == STATUS_REFUSED for c in self.checks)
        if refused != (self.verdict == VERDICT_REFUSED):
            raise PreconditionError(
                f"verdict {self.verdict!r} contradicts the checks "
                f"({'a refusal is present' if refused else 'no refusal is present'})"
            )
        if not self.checks:
            raise PreconditionError(
                "a report over ZERO checks certifies nothing — an empty fact set is the "
                "vacuity this engine exists to prevent (TM-D3 anti-vacuity)"
            )
        if self.law != REFUSE_NOT_WARN_LAW:
            raise PreconditionError("the refuse-not-warn law is not overridable")

    @property
    def refusals(self) -> tuple[FactCheck, ...]:
        """The refused checks, in explicit order."""
        return tuple(sorted(
            (c for c in self.checks if c.status == STATUS_REFUSED), key=FactCheck.sort_key
        ))

    @property
    def honor_system(self) -> tuple[FactCheck, ...]:
        """Preconditions declared not-yet-active — recorded, never blocking."""
        return tuple(sorted(
            (c for c in self.checks if c.status == STATUS_HONOR_SYSTEM), key=FactCheck.sort_key
        ))

    @property
    def legally_absent(self) -> tuple[FactCheck, ...]:
        """Facts this run's shape does not owe (NEVER_A_DE_FACTO_MANDATE_LAW)."""
        return tuple(sorted(
            (c for c in self.checks if c.status == STATUS_LEGALLY_ABSENT), key=FactCheck.sort_key
        ))

    @property
    def blocking(self) -> bool:
        """True iff the gate must refuse to proceed."""
        return self.verdict == VERDICT_REFUSED

    def summary(self) -> str:
        """One-line human rendering.  Names the fact classes, never just a count."""
        if self.blocking:
            classes = ", ".join(c.fact_class for c in self.refusals)
            head = f"{self.gate} REFUSES: absent/unattested facts [{classes}]"
        else:
            head = (
                f"{self.gate} preconditions SATISFIED: "
                f"{sum(1 for c in self.checks if c.status == STATUS_SATISFIED)} attested"
            )
        extra = []
        if self.honor_system:
            extra.append(f"{len(self.honor_system)} honor-system")
        if self.legally_absent:
            extra.append(f"{len(self.legally_absent)} legally-absent")
        if extra:
            head += f" ({'; '.join(extra)})"
        if self.subject:
            head += f" [subject={self.subject}]"
        return head

    def to_dict(self) -> dict[str, Any]:
        return {
            "checks": [c.to_dict() for c in sorted(self.checks, key=FactCheck.sort_key)],
            "gate": self.gate,
            "law": self.law,
            "subject": self.subject,
            "utc": self.utc,
            "verdict": self.verdict,
        }

    def to_json(self) -> str:
        """Byte-stable JSON rendering (Determinism Doctrine law 5: ``sort_keys=True``)."""
        return json.dumps(self.to_dict(), sort_keys=True, ensure_ascii=False, indent=2)


def _check(gate: str, fact_class: str, status: str, reason: str, remedy: str = "") -> FactCheck:
    """Build a check, resolving the fact class's system of record.

    An unregistered fact class RAISES: a refusal whose system of record is unknown cannot
    be audited, which is exactly the assertive-refusal shape the D134 table exists to end.
    """
    try:
        sor = FACT_SYSTEM_OF_RECORD[fact_class]
    except KeyError:  # pragma: no cover - programming error, asserted by test
        raise PreconditionError(
            f"unregistered fact class {fact_class!r}: add it to FACT_SYSTEM_OF_RECORD "
            "with its system of record before refusing on it (D134)"
        ) from None
    return FactCheck(
        gate=gate, fact_class=fact_class, status=status,
        reason=reason, system_of_record=sor, remedy=remedy,
    )


def _settle(gate: str, checks: list[FactCheck], *, subject: str = "",
            utc: str | None = None) -> PreconditionReport:
    """Fold a gate's checks into its report — the ONE place the verdict is derived."""
    refused = any(c.status == STATUS_REFUSED for c in checks)
    return PreconditionReport(
        gate=gate,
        verdict=VERDICT_REFUSED if refused else VERDICT_SATISFIED,
        checks=tuple(checks),
        subject=subject,
        utc=utc,
    )


def require(report: PreconditionReport) -> PreconditionReport:
    """Return *report* when satisfied; RAISE :class:`PreconditionRefused` when not.

    The strict door for a caller that must not proceed (the
    ``gate_evidence_is_creditable`` precedent: a permissive reading and a strict one, with
    the strict one named).
    """
    if report.blocking:
        raise PreconditionRefused(report.summary(), report=report)
    return report


# ---------------------------------------------------------------------------
# Activation table 1 — the mutation precondition, per platform, off X14's RECORD
# ---------------------------------------------------------------------------

#: Where the BL-X14 closure is RECORDED.  This is a pointer to the record, NOT an
#: assertion about its contents: the activation state is parsed out of the artifact every
#: time, so a note that does not record a green leg cannot activate anything.
MUTATION_CLOSURE_ARTIFACT = ".planning/specs/trust-model/evidence/x14-ci-green.md"

#: CI runner-label prefix -> ``sys.platform`` family.  Callers pass ``sys.platform`` so
#: the engine never reads the ambient platform itself (Determinism Doctrine).
RUNNER_PLATFORMS: dict[str, str] = {
    "ubuntu": "linux",
    "windows": "win32",
    "macos": "darwin",
}

#: Every platform family the activation table reports on.  A platform absent from the
#: record is honor-system, never active.
PLATFORMS: tuple[str, ...] = ("linux", "win32", "darwin")

#: ``| `gauntlet (<runner-label>)` | **completed / success** — job `<job-id>` |``
_LEG_RE = re.compile(r"^\|\s*`?gauntlet\s*\(([A-Za-z0-9._-]+)\)`?\s*\|(.+?)\|\s*$")
#: ``| run URL | https://github.com/<owner>/<repo>/actions/runs/<ci-run-id> |``
_RUN_URL_RE = re.compile(r"(https://\S*/actions/runs/(\d+))")
#: ``| SHA | `<40-hex-sha>` |``
_SHA_ROW_RE = re.compile(r"^\|\s*SHA\s*\|\s*`?([0-9a-fA-F]{7,40})`?\s*\|\s*$")
_FAIL_TOKENS = ("failure", "failed", "cancelled", "canceled", "timed_out", "red")


def _guard_path(raw: str | Path) -> Path:
    """Reject path traversal (CWE-23) in a caller-supplied path, without resolving.

    The ``_guard_path`` pattern, per the live precedents ``truth_serum.py:247``,
    ``benchmark_def.py:85``, ``benchmark.py:82``.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise PreconditionError(f"gate_preconditions: refusing path with '..' traversal: {raw!r}")
    return p


def read_mutation_closure(
    repo_root: str | Path,
    *,
    artifact: str = MUTATION_CLOSURE_ARTIFACT,
) -> dict:
    """Read BL-X14's RECORDED closure and return the per-leg facts it records.

    E8, verbatim in effect: *the activation table reads X14's recorded closure.*  This
    function is the read.  It parses the committed evidence note for (a) the citation —
    the CI run URL/id and the SHA it ran at, because §6.6 makes the citation what licenses
    the transition — and (b) one boolean per CI runner leg.

    Returns::

        {"artifact": <rel path>, "readable": bool, "runUrl": str|None,
         "ciRunId": str|None, "sha": str|None, "legs": {"<runner>": bool},
         "reasons": [str, ...]}

    An absent or unparseable note yields ``readable: False`` with the reason recorded and
    NO legs — which leaves every platform honor-system.  That direction is deliberate and
    is E8's own: *"Activating early = drift"*, so the safe default is never-active.

    **Honest residual, stated in-contract:** the closure lives in a human-authored
    markdown evidence note, so this parse is only as strong as that note's table shape.
    It is a *recorded* fact (committed, reviewable, citation-bearing) rather than an
    *asserted* one, which is what the law requires — but a machine-emitted closure record
    would be stronger, and that gap is a deferral candidate, not a claim silently made
    good here.
    """
    rel = _guard_path(artifact).as_posix()
    path = _guard_path(repo_root) / rel
    out: dict[str, Any] = {
        "artifact": rel, "readable": False, "runUrl": None, "ciRunId": None,
        "sha": None, "legs": {}, "reasons": [],
    }
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        out["reasons"].append(
            f"closure record {rel} is unreadable ({exc.__class__.__name__}) — no platform "
            "activates off a record that could not be read"
        )
        return out

    # Parse per TABLE BLOCK, not per file.  An evidence note records several CI runs (the
    # falsified-hypothesis runs, the task-branch runs, the closure run), each in its own
    # table.  A file-wide scan would pair the closure run's URL with an earlier table's
    # SHA — a citation that names a pair no CI run ever produced, which is the BL-X13
    # chimera in another costume.  The leg rows and the citation must come from ONE block.
    blocks = _table_blocks(text)
    closing = [b for b in blocks if b["legs"]]

    if not closing:
        out["reasons"].append(
            f"closure record {rel} names no `gauntlet (<runner>)` leg — nothing is recorded "
            "closed, so nothing activates"
        )
        return out
    if len(closing) > 1:
        out["reasons"].append(
            f"closure record {rel} carries {len(closing)} tables with CI leg rows — which "
            "one is the closure is ambiguous, and an ambiguous closure activates nothing"
        )
        return out

    block = closing[0]
    out["legs"] = dict(sorted(block["legs"].items()))
    out["runUrl"], out["ciRunId"], out["sha"] = block["runUrl"], block["ciRunId"], block["sha"]

    if not out["runUrl"] or not out["sha"]:
        out["reasons"].append(
            f"closure record {rel} carries leg results but no run-URL + SHA citation in the "
            "SAME table — per DESIGN §6.6 the citation is what makes the transition legal, "
            "so an uncited closure does not activate"
        )
        return out

    out["readable"] = True
    return out


def _table_blocks(text: str) -> list[dict]:
    """Split *text* into markdown table blocks, each parsed for legs + citation.

    A block is a run of consecutive lines starting with ``|``; any other line ends it.
    Each block yields ``{"legs": {runner: green}, "runUrl", "ciRunId", "sha"}``.
    """
    blocks: list[dict] = []
    current: dict | None = None

    def _new() -> dict:
        return {"legs": {}, "runUrl": None, "ciRunId": None, "sha": None}

    for raw in text.splitlines():
        line = raw.strip()
        if not line.startswith("|"):
            current = None
            continue
        if current is None:
            current = _new()
            blocks.append(current)

        leg = _LEG_RE.match(line)
        if leg:
            runner, cell = leg.group(1).lower(), leg.group(2).lower()
            green = "success" in cell and not any(tok in cell for tok in _FAIL_TOKENS)
            # A runner named twice in one block must agree; a contradiction is not a closure.
            current["legs"][runner] = (
                green if runner not in current["legs"] else (current["legs"][runner] and green)
            )
            continue
        if current["runUrl"] is None:
            url = _RUN_URL_RE.search(line)
            if url:
                current["runUrl"], current["ciRunId"] = url.group(1), url.group(2)
        if current["sha"] is None:
            sha = _SHA_ROW_RE.match(line)
            if sha:
                current["sha"] = sha.group(1)
    return blocks


@dataclass(frozen=True)
class PlatformActivation:
    """The derived, recordable activation fact for one platform."""

    platform: str
    activation: str
    reason: str
    citation: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "activation": self.activation,
            "citation": self.citation,
            "platform": self.platform,
            "reason": self.reason,
        }


def mutation_activation(
    repo_root: str | Path | None = None,
    *,
    closure: dict | None = None,
) -> dict[str, PlatformActivation]:
    """Per-platform mutation-precondition activation, DERIVED from the recorded closure.

    One entry per member of :data:`PLATFORMS`.  A platform activates only when the closure
    record shows its CI leg green AND carries the run/SHA citation; every other case is
    ``honor-system`` with the reason recorded — E8's *"no Linux task gate fail-closes on a
    Broken prover"*, generalised to every platform in the same direction.

    Pass ``closure=`` to supply an already-read record (keeps callers to one read); pass
    ``repo_root=`` to have this function read it.
    """
    if closure is None:
        if repo_root is None:
            raise PreconditionError(
                "mutation_activation needs a repo_root to read the closure record, or a "
                "closure= record to derive from — it never assumes an activation state"
            )
        closure = read_mutation_closure(repo_root)

    citation = None
    if closure.get("runUrl") and closure.get("sha"):
        citation = f"{closure['runUrl']} @ {closure['sha']}"
    record_reason = "; ".join(closure.get("reasons") or []) or "closure not recorded"

    green_platforms: dict[str, str] = {}
    for runner, green in (closure.get("legs") or {}).items():
        family = next(
            (fam for prefix, fam in RUNNER_PLATFORMS.items() if runner.startswith(prefix)),
            None,
        )
        if family is None or not green:
            continue
        green_platforms[family] = runner

    table: dict[str, PlatformActivation] = {}
    for platform in PLATFORMS:
        if closure.get("readable") and platform in green_platforms:
            table[platform] = PlatformActivation(
                platform=platform,
                activation=ACTIVATION_ACTIVE,
                reason=(
                    f"BL-X14 closure RECORDED green on {green_platforms[platform]} in "
                    f"{closure['artifact']} — the mutation precondition is blocking here"
                ),
                citation=citation,
            )
        else:
            why = (
                f"no green leg recorded for {platform} in {closure.get('artifact')}"
                if closure.get("readable") else record_reason
            )
            table[platform] = PlatformActivation(
                platform=platform,
                activation=ACTIVATION_HONOR_SYSTEM,
                reason=(
                    f"{why} — the mutation precondition is declared Honor-system on this "
                    "platform (E8: activating before the recorded closure is drift)"
                ),
                citation=citation,
            )
    return table


# ---------------------------------------------------------------------------
# Activation table 2 — per-judge tripwires, off tripwire_check's DERIVED state
# ---------------------------------------------------------------------------


def judge_activation(
    repo_root: str | Path | None = None,
    *,
    summary: dict | None = None,
) -> tuple[dict[str, str], str | None]:
    """Per-judge tripwire activation (R-M6), read from ``tripwire_check``'s derivation.

    Returns ``({judge-slug: activation}, stack_error)``.  The activation values are
    ``tripwire_check``'s own (:data:`tripwire_check.ACTIVATION_VERIFIED` /
    ``ACTIVATION_DORMANT`` / ``ACTIVATION_HONOR_SYSTEM``) — this function transcribes, it
    does not re-derive, because a second derivation is a second source of truth.

    ``stack_error`` is non-None only when the judge STACK itself could not be read
    (``tripwire_check.TripwireRefusal`` — an empty registry or an absent
    ``skills/evaluate/``).  That is not a per-judge activation question: a gate that cannot
    enumerate the judges cannot check their verdicts at all, so it REFUSES rather than
    reporting an empty table as clean (anti-vacuity, TM-D3).
    """
    if summary is None:
        try:
            summary = _tw.check_all(repo_root)
        except _tw.TripwireRefusal as exc:
            return {}, str(exc)
    table = {
        str(j.get("judge")): str(j.get("activation"))
        for j in (summary.get("judges") or [])
    }
    if not table:
        return {}, (
            "the tripwire summary lists NO judges — an activation table over zero judges "
            "certifies nothing (anti-vacuity, TM-D3)"
        )
    return dict(sorted(table.items())), None


# ---------------------------------------------------------------------------
# Shared fact helpers
# ---------------------------------------------------------------------------


def _grill_depth(facts: Mapping[str, Any]) -> str | None:
    """The run's declared grill depth, or None when it was not supplied.

    An UNKNOWN depth is not the same as ``skip``: the never-a-de-facto-mandate law
    excuses a run that legally has no grill, and a run whose shape nobody stated is not
    such a run.  Unknown therefore keeps the grill facts REQUIRED (fail-closed, D136).
    """
    raw = facts.get("grillDepth")
    if not isinstance(raw, str):
        return None
    raw = raw.strip()
    if raw not in GRILL_DEPTHS:
        return None
    return raw


def _legally_has_no_grill(facts: Mapping[str, Any]) -> bool:
    return _grill_depth(facts) == GRILL_DEPTH_NO_ARTIFACT


def _present_check(gate: str, fact_class: str, present: bool, subject: str,
                   remedy: str) -> FactCheck:
    """The plain present/absent precondition — the shape most fact classes take."""
    if present:
        return _check(gate, fact_class, STATUS_SATISFIED, f"{subject} is present and recorded")
    return _check(
        gate, fact_class, STATUS_REFUSED,
        f"{subject} is ABSENT — the gate has no fact to stand on and refuses "
        "(absence of evidence is not evidence, TM-D3)",
        remedy,
    )


def _identity_check(gate: str, fact_class: str, artifact: dict | None,
                    expected_sha: str | None, expected_run_id: str | None,
                    subject: str, remedy: str) -> FactCheck:
    """The B4 identity precondition — SHA fresh AND runId exact (TM-D5).

    Delegates to ``run_result.gate_evidence_is_creditable`` (run_result.py:423) — the ONE
    strict identity gate.  A second implementation here would be a second law.
    """
    ok, reason = _rr.gate_evidence_is_creditable(artifact, expected_sha, expected_run_id)
    if ok:
        return _check(gate, fact_class, STATUS_SATISFIED,
                      f"{subject} identity holds: SHA fresh and runId exact")
    return _check(
        gate, fact_class, STATUS_REFUSED,
        f"{subject} fails the identity gate ({reason}) — {_rr.RUN_MEMBERSHIP_LAW}",
        remedy,
    )


# ---------------------------------------------------------------------------
# §3.3 row 1 — the freeze gate (D169)
# ---------------------------------------------------------------------------


def freeze_gate(facts: Mapping[str, Any], *, utc: str | None = None) -> PreconditionReport:
    """Freeze-gate fact set (§3.3 row 1).  PURE.

    Fact bundle keys (every absent key reads as an absent fact — fail-closed):

    ``designPresent`` / ``planPresent`` (bool)
        The frozen DESIGN and PLAN exist.
    ``ledgerStatus`` (str|None)
        The governing ledger's convergence status, as ``kata_dispatch.ledger_status``
        returns it.  ``"converged"`` satisfies.
    ``evidenceValid`` (bool|None) / ``evidenceError`` (str|None)
        The outcome of ``kata_restore.parse_plan_tasks(plan, check_evidence=True)`` — per
        task ``evidence:`` present AND grammar-valid (a raise is the invalid case, and its
        message belongs in ``evidenceError``).
    ``isTreeRun`` (bool) / ``armRegistryPresent`` (bool)
        The arm registry is required for tree runs ONLY (§2.7).
    ``baselineInput`` (dict|None)
        The green-at-fork baseline carried as an INPUT record
        (``run_result.input_reference``).  A record whose ``creditableAsGateEvidence`` is
        true is REFUSED: crediting the baseline as gate evidence is precisely what
        ``BASELINE_INPUT_LAW`` forbids.
    ``declaresContractEdges`` (bool) / ``contractEdgeFreezePresent`` (bool)
        Contract-edge freeze artifacts, required only for a plan that declares edges.
    ``grillDepth`` (str|None)
        D71 depth.  ``"skip"`` makes the governing-ledger record LEGALLY ABSENT.
    """
    gate = GATE_FREEZE
    checks: list[FactCheck] = [
        _present_check(gate, "design", bool(facts.get("designPresent")), "the frozen DESIGN",
                       "author/commit the frozen DESIGN before the freeze act"),
        _present_check(gate, "plan", bool(facts.get("planPresent")), "the frozen PLAN",
                       "author/commit the frozen PLAN before the freeze act"),
    ]

    # --- governing ledger, under the never-a-de-facto-mandate law -----------------
    if _legally_has_no_grill(facts):
        checks.append(_check(
            gate, "governing-ledger", STATUS_LEGALLY_ABSENT,
            "this run declares grillDepth: skip, so it legally has NO grill ledger and owes "
            f"no converged record. {NEVER_A_DE_FACTO_MANDATE_LAW}",
        ))
    else:
        status = facts.get("ledgerStatus")
        if status == "converged":
            checks.append(_check(gate, "governing-ledger", STATUS_SATISFIED,
                                 "the governing ledger records status converged"))
        else:
            depth = _grill_depth(facts)
            checks.append(_check(
                gate, "governing-ledger", STATUS_REFUSED,
                f"the governing ledger's recorded status is {status!r}, not 'converged'"
                + ("" if depth else " (and no grillDepth was declared, so the grill facts "
                                   "stay REQUIRED — an undeclared run shape is not a "
                                   "legally-grill-less one)"),
                "converge the grill and record it, or declare grillDepth: skip if this run "
                "legally has no grill",
            ))

    # --- per-task evidence: declarations -----------------------------------------
    if facts.get("evidenceValid") is True:
        checks.append(_check(gate, "task-evidence", STATUS_SATISFIED,
                             "every task declares evidence: and every declaration is "
                             "grammar-valid (the closed three-form grammar)"))
    else:
        err = facts.get("evidenceError") or "no evidence: validation result was supplied"
        checks.append(_check(
            gate, "task-evidence", STATUS_REFUSED,
            f"the PLAN's per-task evidence: map is absent or grammar-invalid: {err}",
            "declare evidence: for every task in the closed three-form grammar "
            "(artifact: | test: | probe:); a freeform command is refused at freeze",
        ))

    # --- arm registry (tree runs only) -------------------------------------------
    if facts.get("isTreeRun"):
        checks.append(_present_check(
            gate, "arm-registry", bool(facts.get("armRegistryPresent")),
            "the tree run's arm registry",
            "commit the arm registry before freezing a tree run (§2.7)",
        ))
    else:
        checks.append(_check(
            gate, "arm-registry", STATUS_LEGALLY_ABSENT,
            "this is not a tree run, so no arm registry is owed. "
            f"{NEVER_A_DE_FACTO_MANDATE_LAW}",
        ))

    # --- green-at-fork baseline, AS INPUT ----------------------------------------
    baseline = facts.get("baselineInput")
    if not isinstance(baseline, dict):
        checks.append(_check(
            gate, "baseline-input", STATUS_REFUSED,
            "no green-at-fork baseline RESULT is recorded — the freeze gate has no "
            "regression datum for the arm/re-loop to compare against",
            "record the baseline via run_result.input_reference(...) as an INPUT reference "
            "carrying its origin runId",
        ))
    elif baseline.get("creditableAsGateEvidence"):
        checks.append(_check(
            gate, "baseline-input", STATUS_REFUSED,
            "the green-at-fork baseline is recorded as CREDITABLE GATE EVIDENCE — "
            f"{_rr.BASELINE_INPUT_LAW}",
            "re-record it through run_result.input_reference (role=input, "
            "creditableAsGateEvidence=False); the consuming run emits its own result",
        ))
    elif baseline.get("role") != _rr.ROLE_INPUT:
        checks.append(_check(
            gate, "baseline-input", STATUS_REFUSED,
            f"the baseline record's role is {baseline.get('role')!r}, not "
            f"{_rr.ROLE_INPUT!r} — an unusable artifact is not a recorded baseline",
            "supply a readable prior-run RESULT.json to run_result.input_reference",
        ))
    else:
        checks.append(_check(
            gate, "baseline-input", STATUS_SATISFIED,
            "the green-at-fork baseline RESULT is recorded AS INPUT "
            f"(origin runId {baseline.get('originRunId')!r}, never gate evidence)",
        ))

    # --- contract-edge freeze artifacts ------------------------------------------
    if facts.get("declaresContractEdges"):
        checks.append(_present_check(
            gate, "contract-edge-freeze", bool(facts.get("contractEdgeFreezePresent")),
            "the contract-edge freeze artifacts",
            "emit the contract-edge freeze artifacts for every builds_against: edge",
        ))
    else:
        checks.append(_check(
            gate, "contract-edge-freeze", STATUS_LEGALLY_ABSENT,
            "the plan declares no contract edges (builds_against:), so no contract-edge "
            f"freeze artifact is owed. {NEVER_A_DE_FACTO_MANDATE_LAW}",
        ))

    return _settle(gate, checks, subject=str(facts.get("runId") or ""), utc=utc)


# ---------------------------------------------------------------------------
# §3.3 row 2 — the task gate
# ---------------------------------------------------------------------------


def task_gate(facts: Mapping[str, Any], *, utc: str | None = None) -> PreconditionReport:
    """Per-task gate record (§3.3 row 2).  PURE.

    Fact bundle keys:

    ``taskId`` (str) · ``expectedSha`` (str|None) · ``expectedRunId`` (str|None)
    ``verifyRerun`` (dict|None)
        The task gate's own re-run RESULT.json — identity-checked (B4).
    ``footprintManifest`` (dict|None)
        ``footprint.manifest`` output; ``withinFootprint`` false is a lane refusal and
        ``outOfFootprint`` names the offending paths.
    ``mutationRerun`` (dict|None)
        The ENGINE mutation re-run record (§3.6).  **Its absence is a refusal exactly when
        this platform's mutation activation is ``active``** — E8.
    ``platform`` (str)
        The ``sys.platform`` family the gate ran on.  Supplied by the caller; this module
        never reads the ambient platform.
    ``mutationActivation`` (Mapping[str, PlatformActivation|Mapping])
        :func:`mutation_activation`'s table — a table READ FROM THE RECORD.
    ``detectorReports`` (Mapping[str, DetectorReport|Mapping])
        truth_serum's B1/B3 reports, keyed ``"B1"``/``"B3"``.
    ``modifiedFiles`` (Iterable[str])
        The task-modified file set — the input set B1/B3 must have scanned (the ruling in
        this module's docstring).
    """
    gate = GATE_TASK
    task_id = str(facts.get("taskId") or "")
    checks: list[FactCheck] = []

    # --- verify re-run + B4 identity ---------------------------------------------
    verify = facts.get("verifyRerun")
    if not isinstance(verify, dict):
        checks.append(_check(
            gate, "verify-rerun", STATUS_REFUSED,
            "no verify re-run RESULT is recorded for this task — the orchestrator's task "
            "gate has no machine output, only the worker's word",
            "re-run the task's own verify command at the task gate and emit its RESULT.json",
        ))
    else:
        checks.append(_check(gate, "verify-rerun", STATUS_SATISFIED,
                             "the task gate's verify re-run RESULT is recorded"))
        checks.append(_identity_check(
            gate, "task-evidence", verify, facts.get("expectedSha"),
            facts.get("expectedRunId"), "the task gate's verify re-run RESULT",
            "re-run the gate at the tree being credited, under this run's runId",
        ))

    # --- footprint lane check -----------------------------------------------------
    manifest = facts.get("footprintManifest")
    if not isinstance(manifest, dict):
        checks.append(_check(
            gate, "lane", STATUS_REFUSED,
            "no footprint manifest is recorded — the lane check did not run, and an "
            "unrun lane check is not a clean lane",
            "compute footprint.manifest(changed, footprint, diffstat) for the task branch",
        ))
    elif not manifest.get("withinFootprint"):
        outside = ", ".join(manifest.get("outOfFootprint") or []) or "unspecified"
        checks.append(_check(
            gate, "lane", STATUS_REFUSED,
            f"the task changed files OUTSIDE its declared footprint: {outside}",
            "revert the out-of-lane changes or ESCALATE the ownership question — a lane "
            "breach is never waived at the task gate",
        ))
    else:
        checks.append(_check(gate, "lane", STATUS_SATISFIED,
                             "every changed file is inside the task's declared footprint"))

    # --- the engine mutation re-run, per-platform activation (E8) -----------------
    checks.append(_mutation_check(gate, facts))

    # --- B1/B3 detector passes over the TASK-MODIFIED set -------------------------
    checks.extend(_detector_checks(gate, facts))

    return _settle(gate, checks, subject=task_id, utc=utc)


def _activation_for(facts: Mapping[str, Any]) -> tuple[str, str, str | None]:
    """(activation, reason, citation) for this task's platform, from the recorded table."""
    platform = str(facts.get("platform") or "")
    table = facts.get("mutationActivation")
    if not isinstance(table, Mapping) or platform not in table:
        return (
            ACTIVATION_HONOR_SYSTEM,
            f"no recorded activation entry for platform {platform!r} — the closure table "
            "does not cover it, so the precondition stays Honor-system here (E8)",
            None,
        )
    entry = table[platform]
    if isinstance(entry, PlatformActivation):
        return entry.activation, entry.reason, entry.citation
    if isinstance(entry, Mapping):
        return (
            str(entry.get("activation") or ACTIVATION_HONOR_SYSTEM),
            str(entry.get("reason") or "activation reason not recorded"),
            entry.get("citation"),
        )
    raise PreconditionError(
        f"mutationActivation[{platform!r}] is {type(entry).__name__}, not a "
        "PlatformActivation or mapping — an activation state must be a READ RECORD"
    )


def _mutation_check(gate: str, facts: Mapping[str, Any]) -> FactCheck:
    """The §3.6 mutation re-run precondition, gated by the recorded activation table."""
    activation, reason, citation = _activation_for(facts)
    record = facts.get("mutationRerun")
    cite = f" [closure citation: {citation}]" if citation else ""

    if isinstance(record, Mapping) and record.get("records") is not None:
        return _check(
            gate, "mutation-rerun", STATUS_SATISFIED,
            f"the engine mutation re-run record is present ({len(record['records'])} "
            f"record(s)); activation={activation}{cite}",
        )

    if activation != ACTIVATION_ACTIVE:
        return _check(
            gate, "mutation-rerun", STATUS_HONOR_SYSTEM,
            f"no engine mutation re-run record, and the mutation precondition is NOT "
            f"ACTIVE on this platform: {reason}{cite}. Declared Honor-system and recorded; "
            "the gate is NOT blocked here (E8).",
        )

    return _check(
        gate, "mutation-rerun", STATUS_REFUSED,
        "no ENGINE mutation re-run record for this task, and the mutation precondition is "
        f"ACTIVE on this platform: {reason}{cite}. A worker-reported mutation set is not "
        "the record — the orchestrator's own re-run against the task's verify command is.",
        "trigger the engine mutation re-run at the task gate using the task's OWN verify "
        "command (cap N=5, sampling recorded on the cursor by (file path, line number) "
        "ascending — no silent truncation)",
    )


def _report_field(report: Any, name: str, default: Any) -> Any:
    """Read a field off a ``DetectorReport`` or its ``to_dict()`` form, indifferently."""
    if isinstance(report, Mapping):
        return report.get(name, default)
    return getattr(report, name, default)


def _detector_checks(gate: str, facts: Mapping[str, Any]) -> list[FactCheck]:
    """B1/B3 passes, bound to the TASK-MODIFIED input set (the DEF-16 ruling)."""
    reports = facts.get("detectorReports")
    if not isinstance(reports, Mapping) or not reports:
        return [_check(
            gate, "detector-pass", STATUS_REFUSED,
            "no B1/B3 detector reports are recorded for this task — an unrun detector is "
            "not a clean one (TM-D3 anti-vacuity)",
            "run truth_serum.run_blocking_detectors over the task-modified file set and "
            "record both reports",
        )]

    declared = {str(p).replace("\\", "/") for p in (facts.get("modifiedFiles") or [])}
    checks: list[FactCheck] = []
    for key in ("B1", "B3"):
        report = reports.get(key)
        if report is None:
            checks.append(_check(
                gate, "detector-pass", STATUS_REFUSED,
                f"detector {key} has no recorded report for this task",
                f"run {key} over the task-modified file set and record its report",
            ))
            continue

        verdict = str(_report_field(report, "verdict", ""))
        scanned = {
            str(p).replace("\\", "/")
            for p in (_report_field(report, "files_scanned", ()) or ())
        }

        # The input-set binding — the mechanical half of the DEF-16 ruling.
        if declared and not scanned <= declared:
            extra = ", ".join(sorted(scanned - declared)[:5])
            checks.append(_check(
                gate, "detector-pass", STATUS_REFUSED,
                f"detector {key} scanned files OUTSIDE the task-modified set (e.g. {extra}) "
                "— a whole-tree scan answers a different question than the task gate asks, "
                "and cannot be credited as this task's detector pass",
                f"re-run {key} with modified_files = the task's own changed set",
            ))
            continue
        if not declared:
            checks.append(_check(
                gate, "detector-pass", STATUS_REFUSED,
                f"no task-modified file set was declared, so detector {key}'s scope cannot "
                "be checked — an unbounded input set is the vacuity the input-set ruling "
                "closes",
                "declare modifiedFiles (the task's own changed set) alongside the reports",
            ))
            continue

        if verdict in _ts.BLOCKING_VERDICTS:
            checks.append(_check(
                gate, "detector-pass", STATUS_REFUSED,
                f"detector {key} returned {verdict} over the task-modified set: "
                f"{_report_field(report, 'refusal_reason', None) or ''}"
                f"{len(_report_field(report, 'findings', ()) or ())} finding(s). "
                "Detectors ATTEST and NARROW; this gate carries their answer, it does not "
                "overrule it.",
                "resolve the findings, or file the sanctioned deferral (protocol/deferral.md) "
                "and cite it on the marker's own line — never add a suppressor (E3)",
            ))
        elif verdict == _ts.VERDICT_ZERO_CANDIDATE:
            # Honest label, carried: ZERO_CANDIDATE is a fact about the INPUT, not a clean
            # bill of health (truth_serum.DetectorReport.certifies is False for it).  It is
            # non-blocking because refusing here would make "every task must contain a
            # candidate" a de-facto mandate — a task that changed only prose has none.
            checks.append(_check(
                gate, "detector-pass", STATUS_SATISFIED,
                f"detector {key} returned {verdict} over {len(scanned)} task-modified "
                "file(s): the input carried nothing to examine. Recorded as zero-candidate, "
                "NOT as a positive attestation — it certifies nothing about content.",
            ))
        else:
            checks.append(_check(
                gate, "detector-pass", STATUS_SATISFIED,
                f"detector {key} returned {verdict} over {len(scanned)} task-modified file(s)",
            ))
    return checks


# ---------------------------------------------------------------------------
# §3.3 row 3 — the wave gate (BBM-12)
# ---------------------------------------------------------------------------


def wave_gate(facts: Mapping[str, Any], *, utc: str | None = None) -> PreconditionReport:
    """Wave-gate record (§3.3 row 3).  PURE.

    Fact bundle keys:

    ``wave`` (str) · ``memberTasks`` (Iterable[str])
    ``taskGateRecords`` (Mapping[str, PreconditionReport|Mapping])
        One per member task; a member with no record, or with a REFUSED one, refuses the
        wave.
    ``integrationRegate`` (dict|None) · ``expectedSha`` / ``expectedRunId``
        The integration re-gate RESULT emitted after the wave's branches merge.
    ``requiredJudges`` (Iterable[str]) · ``judgeVerdicts`` (Iterable[Mapping])
        Each verdict record needs ``judge``, ``verdict`` and a ``payload`` pointer — a
        verdict with no payload is a conversational value, not a captured record.
    ``judgeActivation`` (Mapping[str, str]) · ``judgeStackError`` (str|None)
        :func:`judge_activation`'s two returns.  A judge whose tripwire is not
        ``verified`` is recorded honor-system; an unreadable STACK refuses.
    """
    gate = GATE_WAVE
    checks: list[FactCheck] = []
    members = [str(t) for t in (facts.get("memberTasks") or [])]
    records = facts.get("taskGateRecords")
    records = records if isinstance(records, Mapping) else {}

    if not members:
        checks.append(_check(
            gate, "task-gate-record", STATUS_REFUSED,
            "the wave declares NO member tasks — a wave gate over zero tasks certifies "
            "nothing (anti-vacuity, TM-D3)",
            "name the wave's member tasks from the frozen PLAN's waves: map",
        ))
    for task_id in members:
        record = records.get(task_id)
        if record is None:
            checks.append(_check(
                gate, "task-gate-record", STATUS_REFUSED,
                f"member task {task_id!r} has no recorded task-gate report",
                f"run the task gate for {task_id} and record its report",
            ))
            continue
        verdict = (record.verdict if isinstance(record, PreconditionReport)
                   else str(record.get("verdict", "")))
        if verdict != VERDICT_SATISFIED:
            checks.append(_check(
                gate, "task-gate-record", STATUS_REFUSED,
                f"member task {task_id!r} has a {verdict or 'missing'} task-gate report — "
                "a wave cannot be greener than its members",
                f"resolve {task_id}'s refused preconditions and re-gate it",
            ))
        else:
            checks.append(_check(
                gate, "task-gate-record", STATUS_SATISFIED,
                f"member task {task_id!r} has a SATISFIED task-gate report",
            ))

    # --- integration re-gate ------------------------------------------------------
    regate = facts.get("integrationRegate")
    if not isinstance(regate, dict):
        checks.append(_check(
            gate, "integration-regate", STATUS_REFUSED,
            "no integration re-gate RESULT is recorded — green task branches are not "
            "evidence that their merge is green",
            "run the gate on the integration branch after merging the wave and emit its "
            "RESULT.json",
        ))
    else:
        checks.append(_identity_check(
            gate, "integration-regate", regate, facts.get("expectedSha"),
            facts.get("expectedRunId"), "the wave's integration re-gate RESULT",
            "re-run the integration gate at the integration tip under this run's runId",
        ))

    # --- judge VERDICT records ----------------------------------------------------
    checks.extend(_judge_checks(gate, facts))
    return _settle(gate, checks, subject=str(facts.get("wave") or ""), utc=utc)


def _judge_checks(gate: str, facts: Mapping[str, Any]) -> list[FactCheck]:
    """VERDICT-record + per-judge tripwire-activation preconditions (R-M6)."""
    stack_error = facts.get("judgeStackError")
    if stack_error:
        return [_check(
            gate, "judge-activation", STATUS_REFUSED,
            f"the judge stack could not be enumerated: {stack_error}. A gate that cannot "
            "list its judges cannot check their verdicts, and an empty table is not a "
            "clean one (anti-vacuity, TM-D3).",
            "restore the judge registry / skills tree, then re-derive the activation table "
            "with tripwire_check.check_all",
        )]

    activation = facts.get("judgeActivation")
    activation = activation if isinstance(activation, Mapping) else {}
    verdicts = {
        str(v.get("judge")): v
        for v in (facts.get("judgeVerdicts") or []) if isinstance(v, Mapping)
    }
    required = [str(j) for j in (facts.get("requiredJudges") or [])]

    checks: list[FactCheck] = []
    for judge in required:
        record = verdicts.get(judge)
        if record is None:
            checks.append(_check(
                gate, "verdict", STATUS_REFUSED,
                f"judge {judge!r} has no captured VERDICT record for this wave",
                f"dispatch {judge} through the seam and capture its VERDICT line + payload",
            ))
            continue
        if not record.get("payload"):
            checks.append(_check(
                gate, "verdict", STATUS_REFUSED,
                f"judge {judge!r}'s verdict carries no payload pointer — a verdict with no "
                "pointed-to payload is a conversational value, not a captured record",
                f"capture {judge}'s verdict through the seam so the VERDICT line carries "
                "its required payload= pointer",
            ))
            continue
        checks.append(_check(
            gate, "verdict", STATUS_SATISFIED,
            f"judge {judge!r} has a captured VERDICT record "
            f"({record.get('verdict')}) with payload {record.get('payload')}",
        ))

        state = str(activation.get(judge, ACTIVATION_HONOR_SYSTEM))
        if state == _tw.ACTIVATION_VERIFIED:
            checks.append(_check(
                gate, "judge-activation", STATUS_SATISFIED,
                f"judge {judge!r}'s tripwire is {state} — its corpus demonstrates "
                "failure-capability, so its verdict is credited",
            ))
        else:
            checks.append(_check(
                gate, "judge-activation", STATUS_HONOR_SYSTEM,
                f"judge {judge!r}'s tripwire activation is {state} (R-M6): a judge that "
                "cannot demonstrate failure-capability is Dormant, not Verified — its "
                "verdict is recorded and declared Honor-system, and is NOT blocked here "
                "(deny-everything dissolved).",
            ))
    if not required:
        checks.append(_check(
            gate, "verdict", STATUS_REFUSED,
            "the wave names NO required judges — a wave gate that demands no verdict "
            "certifies nothing (anti-vacuity, TM-D3)",
            "name the wave's judges (at minimum its default-FAIL final eval)",
        ))
    return checks


# ---------------------------------------------------------------------------
# §3.3 row 4 — the final gate (kata-evaluate)
# ---------------------------------------------------------------------------


def final_gate(facts: Mapping[str, Any], *, utc: str | None = None) -> PreconditionReport:
    """Final-gate preconditions (§3.3 row 4).  PURE.

    Fact bundle keys: ``result`` (RESULT.json dict|None) · ``expectedSha`` ·
    ``expectedRunId`` · ``factTable`` (dict|None, the §4 grounding-attested table) ·
    ``mutationAttestation`` (dict|None, R-M10).

    The mutation attestation must be the GROUNDING pass's, and must attest the whole set:
    ``{"attestedBy": <grounding record>, "complete": True, "sampled": [...],
    "recordCount": n}``.  ``complete: False`` is a refusal, because the evaluator's
    precondition is the whole set's records being present + current + per-task complete.
    """
    gate = GATE_FINAL
    checks: list[FactCheck] = []
    result = facts.get("result")

    if not isinstance(result, dict):
        checks.append(_check(
            gate, "verify-rerun", STATUS_REFUSED,
            "no RESULT.json is recorded for the final gate — kata-evaluate's machine-input "
            "step has nothing to read, and absent inputs are NEEDS_WORK, never a pass",
            "emit the final gate's RESULT.json via gate_emit before dispatching the evaluator",
        ))
        checks.append(_check(
            gate, "per-gate-counts", STATUS_REFUSED,
            "no RESULT.json, so no per-gate parsed counts exist to read",
            "emit the final gate's RESULT.json",
        ))
    else:
        checks.append(_identity_check(
            gate, "task-evidence", result, facts.get("expectedSha"),
            facts.get("expectedRunId"), "the final gate's RESULT",
            "re-run the final gate at the tree being credited, under this run's runId "
            "(the BL-X11 fix: the evaluator checks identity FIRST)",
        ))
        blocks = result.get("gates") or []
        scope = result.get("countsScope")
        if blocks:
            checks.append(_check(
                gate, "per-gate-counts", STATUS_SATISFIED,
                f"{len(blocks)} per-gate count block(s) recorded (countsScope={scope!r}) — "
                "every count in a block came from one gate (the BL-X13 fix)",
            ))
        else:
            checks.append(_check(
                gate, "per-gate-counts", STATUS_REFUSED,
                f"RESULT records no per-gate count blocks (countsScope={scope!r}) — counts "
                "are UNAVAILABLE, which is never to be read as zero failures",
                "run a gate whose output carries a parseable summary line, or record the "
                "honesty flag rather than crediting a success-shaped 0/0",
            ))

    checks.append(_present_check(
        gate, "fact-table", isinstance(facts.get("factTable"), dict),
        "the grounding-attested fact table",
        "run the grounding gate and emit its attested fact table (DESIGN §4) before the "
        "evaluator reads anything",
    ))

    attestation = facts.get("mutationAttestation")
    if not isinstance(attestation, dict):
        checks.append(_check(
            gate, "mutation-attestation", STATUS_REFUSED,
            "no grounding-attested mutation record set — the evaluator refuses without a "
            "grounding-run mutation record (R-M10); the worker-union hole closes at that "
            "seam and nowhere else",
            "run the stack-head grounding pass: re-run a sampled subset against the gate "
            "command and attest the whole record set (present + current + per-task complete)",
        ))
    elif not attestation.get("complete"):
        checks.append(_check(
            gate, "mutation-attestation", STATUS_REFUSED,
            "the mutation attestation is recorded INCOMPLETE — the attestation covers the "
            "WHOLE record set or it is not the evaluator's precondition",
            "complete the per-task mutation record set, then re-attest",
        ))
    elif not attestation.get("attestedBy"):
        checks.append(_check(
            gate, "mutation-attestation", STATUS_REFUSED,
            "the mutation attestation names no attesting grounding record — an unattributed "
            "attestation is an assertion",
            "record the grounding pass's own record id as attestedBy",
        ))
    else:
        checks.append(_check(
            gate, "mutation-attestation", STATUS_SATISFIED,
            f"the grounding pass ({attestation.get('attestedBy')}) attests the whole "
            f"mutation record set ({attestation.get('recordCount')} record(s), sampled "
            f"subset re-run)",
        ))

    return _settle(gate, checks, subject=str(facts.get("runId") or ""), utc=utc)


# ---------------------------------------------------------------------------
# §3.3 row 5 — grill convergence
# ---------------------------------------------------------------------------


def convergence_gate(facts: Mapping[str, Any], *, utc: str | None = None) -> PreconditionReport:
    """Convergence-pass record (§3.3 row 5).  PURE.

    Fact bundle keys: ``grillDepth`` (str|None) · ``convergenceRecord``
    (``{"passes": [{"recordId": ...}, ...]}`` | None).

    **This is where the never-a-de-facto-mandate law bites hardest.**  A ``skip`` run owes
    NO convergence record and is recorded legally-absent.  A ``full`` (Advanced) run must
    prove the double-pass ran as **two distinct dispatches**, via distinct seam record ids
    — the §3.3 row's own words.
    """
    gate = GATE_CONVERGENCE
    depth = _grill_depth(facts)

    if depth == GRILL_DEPTH_NO_ARTIFACT:
        return _settle(gate, [_check(
            gate, "convergence-pass", STATUS_LEGALLY_ABSENT,
            "this run declares grillDepth: skip — it legally has no grill and therefore no "
            f"convergence pass to record. {NEVER_A_DE_FACTO_MANDATE_LAW}",
        )], subject=str(depth), utc=utc)

    record = facts.get("convergenceRecord")
    passes = record.get("passes") if isinstance(record, Mapping) else None
    if not isinstance(passes, list) or not passes:
        return _settle(gate, [_check(
            gate, "convergence-pass", STATUS_REFUSED,
            "no convergence-pass record — nothing records that a grill pass ran, and a "
            "self-assessed convergence with no artifact is exactly the faith this gate "
            f"replaces (declared grillDepth={depth!r})",
            "record the convergence pass with its seam dispatch record id(s)",
        )], subject=str(depth or "undeclared"), utc=utc)

    record_ids = [str(p.get("recordId")) for p in passes if isinstance(p, Mapping)
                  and p.get("recordId")]
    if len(record_ids) != len(passes):
        return _settle(gate, [_check(
            gate, "convergence-pass", STATUS_REFUSED,
            f"{len(passes) - len(record_ids)} of {len(passes)} recorded pass(es) carry no "
            "seam record id — a pass with no dispatch record is a claim that it ran",
            "record each pass's minted seam record id",
        )], subject=str(depth or "undeclared"), utc=utc)

    if depth in GRILL_DEPTHS_DOUBLE_PASS and len(set(record_ids)) < 2:
        return _settle(gate, [_check(
            gate, "convergence-pass", STATUS_REFUSED,
            f"grillDepth={depth!r} owes an Advanced DOUBLE pass, but the record shows "
            f"{len(set(record_ids))} distinct dispatch(es) — two passes in one context are "
            "one pass twice",
            "dispatch the second pass as a DISTINCT fresh-context dispatch and record its "
            "own record id",
        )], subject=str(depth), utc=utc)

    return _settle(gate, [_check(
        gate, "convergence-pass", STATUS_SATISFIED,
        f"the convergence pass is recorded as {len(set(record_ids))} distinct seam "
        f"dispatch(es) at grillDepth={depth!r}",
    )], subject=str(depth), utc=utc)


# ---------------------------------------------------------------------------
# §3.3 row 6 — the sprint stop-gate
# ---------------------------------------------------------------------------


def sprint_stop_gate(facts: Mapping[str, Any], *, utc: str | None = None) -> PreconditionReport:
    """Sprint stop-gate persisted-verdict check (§3.3 row 6).  PURE.

    Fact bundle keys: ``persistedVerdict`` (Mapping|None) · ``expectedRunId`` (str|None).

    The stop-gate *"consumes the PERSISTED evaluate VERDICT record with identity check
    (never a conversational value)"*.  A verdict with no payload pointer, or carrying
    another run's identity, is refused.
    """
    gate = GATE_SPRINT_STOP
    verdict = facts.get("persistedVerdict")
    expected = facts.get("expectedRunId")
    checks: list[FactCheck] = []

    if not isinstance(verdict, Mapping):
        checks.append(_check(
            gate, "persisted-verdict", STATUS_REFUSED,
            "no PERSISTED evaluate VERDICT record — the stop-gate will not read a verdict "
            "that lived only in a conversation",
            "capture the evaluator's verdict through the seam so a VERDICT record exists",
        ))
    elif not verdict.get("payload"):
        checks.append(_check(
            gate, "persisted-verdict", STATUS_REFUSED,
            "the verdict record carries no payload pointer — that is a conversational "
            "value wearing a record's shape",
            "capture the verdict through the seam (a VERDICT line REQUIRES its payload)",
        ))
    elif not expected or not str(expected).strip():
        checks.append(_check(
            gate, "persisted-verdict", STATUS_REFUSED,
            "the stop-gate did not state which run it is stopping — identity cannot be "
            "checked, and an unchecked identity is not an identity (D136)",
            "pass expectedRunId = the live run's runId",
        ))
    elif str(verdict.get("runId") or "") != str(expected).strip():
        checks.append(_check(
            gate, "persisted-verdict", STATUS_REFUSED,
            f"the persisted verdict belongs to run {verdict.get('runId')!r}, not "
            f"{expected!r} — {_rr.RUN_MEMBERSHIP_LAW}",
            "read this run's own persisted verdict; a prior run's is an input, never this "
            "gate's evidence",
        ))
    else:
        checks.append(_check(
            gate, "persisted-verdict", STATUS_SATISFIED,
            f"the persisted VERDICT record ({verdict.get('verdict')}) carries this run's "
            f"identity and a payload pointer ({verdict.get('payload')})",
        ))
    return _settle(gate, checks, subject=str(expected or ""), utc=utc)


# ---------------------------------------------------------------------------
# Recording — a refusal is an EVENT, not a message (TM-G1's data half)
# ---------------------------------------------------------------------------

_CTRL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")


def _scrub(text: str) -> str:
    """Strip control/ANSI characters and neutralise the cursor field separator.

    Mirrors ``tripwire_check._scrub`` / ``kata_trail``'s rendering guard: a rendered value
    must not be able to forge extra cursor fields.
    """
    cleaned = _CTRL_RE.sub("", str(text))
    return cleaned.replace(_kb.FS, " / ").replace("payload=", "payload-")


def precondition_record(report: PreconditionReport, *, run_id: str) -> dict:
    """Build the cursor-appendable RECORD for a gate's precondition fold.

    Mirrors ``tripwire_check.corpus_record``: the outcome stops being a value that lived
    only in a process and becomes a fact a later fold can read.
    """
    return {
        "kind": RECORD_KIND_PRECONDITIONS,
        "runId": run_id,
        "gate": report.gate,
        "subject": report.subject,
        "verdict": report.verdict,
        "refusedClasses": [c.fact_class for c in report.refusals],
        "honorSystemClasses": [c.fact_class for c in report.honor_system],
        "legallyAbsentClasses": [c.fact_class for c in report.legally_absent],
        "report": report.to_dict(),
    }


def format_precondition_line(record: Mapping[str, Any]) -> str:
    """Render a precondition record as a one-line cursor ``msg`` — scrubbed."""
    def _join(key: str) -> str:
        vals = record.get(key) or []
        return ",".join(str(v) for v in vals) if vals else "-"

    parts = [
        str(record.get("kind")),
        f"gate={record.get('gate')}",
        f"subject={record.get('subject') or '-'}",
        f"verdict={record.get('verdict')}",
        f"refused={_join('refusedClasses')}",
        f"honor-system={_join('honorSystemClasses')}",
        f"legally-absent={_join('legallyAbsentClasses')}",
    ]
    return _scrub(" ".join(parts))


def record_preconditions(
    kata_dir: str | Path,
    report: PreconditionReport,
    *,
    run_id: str,
    agent: str = RECORD_AGENT,
    task: str | None = None,
    parent_seq: int | None = None,
    now: datetime | None = None,
) -> _kb.CursorLine:
    """Append a gate's precondition fold to the cursor as a NOTE + pointed-to payload.

    ``NOTE`` is a worker-authored cursor type, so this engine may write it directly —
    unlike the seam-authored types (PHASE/VERDICT/SPAWN/DOWN/DENY), which it never emits.
    The full report goes to the payload so the refusal is auditable as DATA, and the line
    carries only the scrubbed summary.  This is what makes every refusal a *recorded*
    event rather than a message that scrolled past (TM-G1's data half).
    """
    _kb.validate_run_id(run_id)
    kata = Path(kata_dir)
    record = precondition_record(report, run_id=run_id)
    cursor = _kb.read_cursor(kata)
    seq = _kb.next_seq(cursor)
    pointer = _kb.payload_pointer(run_id, seq)
    _kb.write_payload(kata, pointer, record)
    return _kb.append_event(
        kata,
        agent,
        "NOTE",
        task or report.subject or report.gate,
        format_precondition_line(record),
        parent_seq=parent_seq,
        payload=pointer,
        seq=seq,
        now=now,
    )


# ---------------------------------------------------------------------------
# Report (de)serialisation — so gate_emit can be handed a report as a file
# ---------------------------------------------------------------------------


def report_from_dict(data: Mapping[str, Any]) -> PreconditionReport:
    """Rebuild a :class:`PreconditionReport` from its ``to_dict()`` form.

    Fail-closed: a malformed document RAISES rather than degrading into a permissive
    empty report (D136).
    """
    if not isinstance(data, Mapping):
        raise PreconditionError("a precondition report must be a JSON object")
    try:
        checks = tuple(
            FactCheck(
                gate=str(c["gate"]), fact_class=str(c["factClass"]),
                status=str(c["status"]), reason=str(c["reason"]),
                system_of_record=str(c["systemOfRecord"]), remedy=str(c.get("remedy", "")),
            )
            for c in data["checks"]
        )
        return PreconditionReport(
            gate=str(data["gate"]), verdict=str(data["verdict"]), checks=checks,
            subject=str(data.get("subject", "")), utc=data.get("utc"),
        )
    except (KeyError, TypeError) as exc:
        raise PreconditionError(f"malformed precondition report: {exc}") from None


def load_report(path: str | Path) -> PreconditionReport:
    """Read a precondition report from a JSON file.  Raises on absent/malformed input."""
    text = _guard_path(path).read_text(encoding="utf-8")
    return report_from_dict(json.loads(text))


def combine(reports: Iterable[PreconditionReport]) -> tuple[PreconditionReport, ...]:
    """Order a set of reports deterministically (doctrine law 10) for recording."""
    return tuple(sorted(reports, key=lambda r: (r.gate, r.subject)))
