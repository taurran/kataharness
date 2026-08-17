"""kata_close.py — ``close_run``: the plan-grounding, fail-closed close (DESIGN §5).

The seam's terminal act.  ``kata_dispatch`` owns every other row of the §1.3 engine API
surface; this module owns the one row that row-table marks ``close_run(…)`` — *"the
plan-grounding close (§5): refuses without required records, runs the three-way join +
provenance drift check + redaction scrub, writes the terminal ``run-closed`` PHASE
record"* — and it is deliberately a SEPARATE module so the close's own machinery cannot
be reached by any of the mint/claim/capture paths.

What the close actually asserts, in one sentence: **the run ends by proving itself
against the frozen plan.**  Not by an agent's report that it finished.

The five properties, each with the DESIGN clause it implements:

1. **Refuses without required records** (§5.3).  Every fact class the close grades binds
   to that class's system of record (:data:`SYSTEM_OF_RECORD`); the absent-records
   refusal is the backstop for capture-edge loss of any kind (§1.6, RS-L1).
2. **The TOTAL three-way join** (§5.2): PLAN (``kata_restore.parse_plan_tasks``) ⋈ tree
   (``Kata-Task:`` trailers) ⋈ ``DEFERRED.md``.  Every plan item mechanically resolves to
   ``built-and-exercised`` / ``recorded-deferral`` / **named drift**.  Behavioral items
   resolve through their declared ``evidence:`` form — compiled and RUN through
   ``tools/evidence_grammar.py`` — never through file-touch heuristics.
3. **Provenance drift** (§5.4 / TM-A2): committed ``kata.config`` / ``INTENT.md`` vs what
   the run actually executed; machine-specific values migrate to ``.kata-settings.json``
   (``kata_config.split_machine_local`` / ``kata_settings.record_machine_local``) so the
   committed provenance is clean and comparable across machines.
4. **Redaction at the commit act + first-run consent** (RS-M7 / RS-M6): ONE scrub
   (``learn_feed.redact``'s class table, extended — never a second scrub), reached from
   TWO named points; consent is per-target, remembered machine-local, fires exactly once,
   and PARKS rather than proceeds in an unattended run (TM-B5).
5. **The terminal ``run-closed`` PHASE record, written exactly once** (§2.6, R4 residual
   3) — through the seam's own ``kata_dispatch.phase()``, never by a second writer.

**D134 reconciliation, stated in code as well as prose** (§5.3, R3-M6).  Tier-2
integration trailers remain **AUTHORITATIVE for DONE**; the cursor gates ONLY the fact
classes for which it is the system of record (verdicts, phases, denials, spawns) — for
DONE it corroborates, exactly as D134 rules.  **The close's refusals bind per fact class
to that class's system of record**: :data:`SYSTEM_OF_RECORD` is that binding as data, and
every refusal this module raises names the class it is bound to.  A refusal that reached
for the wrong authority (e.g. failing DONE because the cursor lacks a line) would be a
D134 violation, so the table is the thing to read before adding a check.

**The §1.8 DENY boundary, for THIS surface only (DEF-12's question, answered narrowly).**
Every refusal here raises a typed :class:`CloseRefused` and emits the close VERDICT ARTIFACT; none
of them writes a cursor ``DENY`` line.  The line drawn, stated so it can be argued with: a ``DENY``
event records a refusal that **denies an act which would otherwise have proceeded and has no other
durable record** (a record-less launch, a refuse-to-mint).  A close refusal is not that — it IS a
recorded gate verdict, with its own artifact carrying the reason and the two legal paths, and §6.1
surface 2 already treats ``DENY`` and *gate refusal* as two classes both owed visibility.  Writing
a DENY per close refusal would also flood the cursor across the sanctioned refuse → fix → re-close
cycle, which is the NORMAL path out of a fail-closed close, not an incident.  **DEF-12 itself stays
OPEN**: it asks about ``claim``/``capture`` refusals on ``kata_dispatch``'s surface, which this task
does not own — though by the line above those two DO deny an act and DO lack another record, so the
principle argues for DEF-12's change rather than against it.  That is an input to the ruling, not
the ruling.

**The loop-back ruling (G20 / R3 — PROPOSED here, ratified by the conductor).**
``kata_dispatch.phase()`` refuses a ``run-closed`` line while ANY phase is still open.
The kata-loop Path-A sequence opens ``LOOP-BACK`` and then closes the phases the run
still holds — which leaves ``LOOP-BACK`` itself open, so a naive terminal write always
refuses.  The ruling implemented here, in two halves:

* **Opening ``LOOP-BACK`` over an open predecessor is LEGAL.**  A loop-back exists
  precisely to record that a run is departing while work is still open; requiring the
  predecessor to be closed first would make the record unwritable in the only situation
  it describes.  ``phase()`` already permits this (it refuses only a re-open), so the
  ruling is a statement of the existing mechanism, not a change to it.
* **Reconciliation happens at the CLOSE, never by leaving a phase open across the
  terminal line.**  :func:`close_run` closes every still-open phase **LIFO** (most
  recently opened first, so ``LOOP-BACK`` closes first — it was opened last) and only then
  writes ``run-closed``.  With ``close_open_phases=False`` it REFUSES instead, naming the
  instruction.  A run therefore never carries an open phase past its terminal record, and
  the successor's ``prev-run:`` chain is corroborated by the predecessor's own terminal
  line, which records ``loopBack=1`` when a ``LOOP-BACK`` phase was seen.

Determinism Doctrine, per law:

* law 1 — ONE pinned git helper for this module (:func:`_pinned_git`); the pin set is
  never re-derived per call site.  It is a distinct helper from ``footprint._pinned_git``
  only because that one is private and CWD-bound while every read here is
  ``repo_root``-bound (the ``run_result.resolve_head_sha`` precedent).
* law 2/3 — every filesystem walk and every set is ``sorted()`` before it reaches output.
* law 4 — the provenance digest length-prefixes each framed item (netstring), so two
  different (path, content) splits can never collide.
* law 5 — every JSON this module writes uses ``sort_keys=True``.
* law 6 — the close artifact carries wall-clock stamps (``closedUtc``); it is a record,
  never byte-compared or hashed whole.  The digests it contains are computed over content
  only and carry no stamp.
* law 7 — ``now`` is injectable everywhere a decision or a record is made.
* law 8 — the evidence runner strips ``PYTEST_ADDOPTS``, blocks the nondeterminism plugin
  by argv, and carries a timeout.
* law 9 — no randomness anywhere in this module.
* law 10 — every ranking/report ordering ends on an explicit id tie-break.

**Inherited residual, carried rather than implied away (PD-2 — labels travel with the claim).**
``kata_board._publish_cursor``'s fallback for filesystems without usable hardlinks reverts to
exclusive-create-then-write, whose zero-byte window is a stated residual (D-27).  The close READS
the cursor, so it inherits that window — and its posture on it is a **REFUSAL**: a cursor that does
not parse raises ``CursorError``, which :func:`close_run` turns into the absent-records refusal.  A
torn or zero-byte cursor can therefore make a close fail; it can never make a close SUCCEED over an
empty record, which is the direction that would matter.

Exec-safety (``protocol/exec-safety.md``): this module is a NEW subprocess sink and its
rows are owed to that registry (reported at integration — the file is not this task's to
edit).  Both sinks are ``shell=False`` structured argv: :func:`_pinned_git` (fixed git
argv, ``repo_root`` as ``cwd``) and :func:`default_evidence_runner` (an argv produced by
``evidence_grammar.compile_declaration``, whose closed three-form grammar is what makes
the argv trustworthy — a freeform command string is refused at compile, never here).
"""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import escalation
import evidence_grammar
import kata_board as _kb
import kata_config
import kata_dispatch as _kd
import kata_restore
import kata_settings
import kata_trail as _trail
import learn_feed

# --------------------------------------------------------------------------- constants

#: Sub-directory of ``.kata/`` holding the close's own artifacts.
CLOSE_DIRNAME = "close"

#: Suffix of the exactly-once close-election token (the O_CREAT|O_EXCL winner artifact).
CLOSING_TOKEN_SUFFIX = ".closing"

#: Suffix of the once-per-target consent-election token.
CONSENT_TOKEN_SUFFIX = ".consent"

#: Directory (under the harness home) holding consent-election tokens.
CONSENT_LOCK_DIRNAME = ".kata-consent"

#: Close verdict enum — CLOSED on a clean close, ACCEPTED on a recorded operator
#: acceptance of a failing close (§5.3's second legal path), NEEDS_WORK otherwise.
VERDICT_CLOSED = "CLOSED"
VERDICT_ACCEPTED = "ACCEPTED"
VERDICT_NEEDS_WORK = "NEEDS_WORK"
VERDICTS = frozenset({VERDICT_CLOSED, VERDICT_ACCEPTED, VERDICT_NEEDS_WORK})

#: The §5.2 resolution enum — TOTAL over the plan's task set.
RESOLUTION_BUILT = "built-and-exercised"
RESOLUTION_DEFERRED = "recorded-deferral"
RESOLUTION_DRIFT = "drift"
RESOLUTIONS = (RESOLUTION_BUILT, RESOLUTION_DEFERRED, RESOLUTION_DRIFT)

#: The two legal paths out of a failing close (§5.3).  Quoted in every refusal.
TWO_LEGAL_PATHS = (
    "a failing close leaves exactly TWO legal paths (DESIGN §5.3): (1) ANOTHER LOOP PASS "
    "— re-loop the wave as a sibling child run (parent-run: same parent, prev-run: the "
    "failed sibling); or (2) RECORDED OPERATOR ACCEPTANCE — re-call close_run with "
    "accepted_by=<human> and accepted_at=<ISO-8601 UTC>. The seam refuses run-closure "
    "otherwise; no third path exists and no out-of-band doc edit is one."
)

#: TM-A1 routing, operator verbatim — quoted where the routing fires.
TM_A1_VERBATIM = "if anything is false or facade it should be another loop pass"

#: D134 — the per-fact-class system of record.  **The close's refusals bind per fact
#: class to that class's system of record**, and this table IS that binding.  Trailers
#: stay AUTHORITATIVE for DONE; the cursor gates only its own classes and corroborates
#: DONE.  Read this before adding a check: a refusal that reaches for the wrong authority
#: is a D134 violation, not a stricter gate.
SYSTEM_OF_RECORD: dict[str, str] = {
    "task-done": (
        "tier-2 git integration history — the `Kata-Task:` trailers read by "
        "kata_restore.collect_integrated_tasks_ex. AUTHORITATIVE for DONE (D134); the "
        "cursor corroborates and never overrides it."
    ),
    "task-evidence": (
        "the frozen PLAN's per-task `evidence:` declarations (DESIGN §5.1/§3.5), "
        "compiled and executed through tools/evidence_grammar.py."
    ),
    "deferral": (
        "the sanctioned-deferral ledger .planning/DEFERRED.md, parsed against the "
        "protocol/deferral.md grammar (a parse failure is a refusal, never a skip)."
    ),
    "deferral-approval": (
        "the entry's own `accepted_by` / `accepted_at` field lines — a gate may credit "
        "an approval ONLY from these fields (protocol/deferral.md)."
    ),
    "phase": "the cursor's seam-authored PHASE lines (DESIGN §2.6), via kata_dispatch.phase_state.",
    "verdict": "the cursor's seam-authored VERDICT lines (DESIGN §1.6/§2.3).",
    "closeout-decision": "the cursor's DECISION lines (orchestrator-authored, DESIGN §2.3).",
    "resilience": (
        "the cursor's seam-authored durability NOTE records, via "
        "kata_dispatch.read_trail_records — a fold over recorded fact, never the config flag."
    ),
    "provenance": (
        "the COMMITTED kata.config / INTENT.md blobs (git), compared against what the run "
        "actually executed (DESIGN §5.4 / TM-A2)."
    ),
}

#: Fact classes whose records the close REQUIRES before it will grade anything (§5.3).
REQUIRED_RECORD_CLASSES = ("phase", "provenance", "task-done")

_GIT_TIMEOUT_S = 60
_EVIDENCE_TIMEOUT_S = 900

#: Test seam (house pattern — ``kata_dispatch._CLAIM_RACE_HOOK``): called with the runId
#: at the EXACT race point, after the close election and before the terminal write, so a
#: test can force an interleaving deterministically instead of relying on thread timing.
_CLOSE_RACE_HOOK = None

#: Test seam, same contract, for the consent election (called with the target key after
#: the election and before the prompt).
_CONSENT_RACE_HOOK = None


# --------------------------------------------------------------------------- errors


class CloseRefused(Exception):
    """The close REFUSED.  Fail-closed: nothing is ever closed by a swallowed error.

    Carries ``verdict_path`` (the emitted close artifact, when one was written) so a
    caller cites an ARTIFACT rather than this exception's message text — a refusal's
    narration is a DESCRIPTION of the legal path, never evidence it was taken.
    """

    def __init__(self, message: str, *, verdict_path: str | None = None,
                 fact_class: str | None = None):
        super().__init__(message)
        self.verdict_path = verdict_path
        self.fact_class = fact_class


class ConsentRequired(CloseRefused):
    """The first-run consent moment PARKED (unattended run) — never proceeded (TM-B5)."""


class RedactionRefused(CloseRefused):
    """A detected secret/key/PII class failed the commit act closed (RS-M7 / §8 S4)."""


class DeferralLedgerError(CloseRefused):
    """The deferral ledger could not be parsed — a refusal, never a skip (deferral.md)."""


# --------------------------------------------------------------------------- guards


def _safe_path(raw: str | Path) -> Path:
    """Reject a ``..`` traversal component (CWE-23).  Member of the repo path-guard family.

    Same invariant as every other member (``kata_board._safe_path``,
    ``kata_dispatch._safe_kata_dir``, …): raise ``ValueError`` on a ``..`` component,
    accept a clean relative path.  Deliberately does NOT resolve — the caller decides
    whether an absolute path is wanted.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(f"kata_close: refusing path with '..' traversal: {raw!r}")
    return p


def _kata_dir(raw: str | Path) -> Path:
    """The guarded, resolved ``.kata/`` root — :func:`_safe_path` then ``.resolve()``.

    Composed rather than copied, so this module contributes exactly ONE guard to the
    path-guard family (``tools/tests/test_path_guard_family.py``) instead of two that
    could drift apart.
    """
    return _safe_path(raw).resolve()


def _utc(now: datetime | None) -> str:
    """Record stamp (law 6: recorded, never compared).  ``now`` injectable (law 7)."""
    return (now or datetime.now(UTC)).astimezone(UTC).isoformat()


def _pinned_git(repo_root: str | Path, args: list[str]) -> subprocess.CompletedProcess[bytes]:
    """This module's ONE pinned git helper (Doctrine law 1).  ``shell=False``, fixed argv.

    Pins ``core.quotepath=off`` · ``log.follow=false`` · ``log.showSignature=false`` ·
    ``color.ui=false``.  ``footprint._pinned_git`` is private AND runs in the process CWD;
    every read here is bound to an explicitly supplied ``repo_root`` (the
    ``run_result.resolve_head_sha`` precedent), so the pin set lives here once.

    ``check=False``: the policy for a non-zero exit lives at each call site — a path
    absent at a ref is a real answer, not an error, and nothing here falls through to a
    permissive default.
    """
    return subprocess.run(
        [
            "git",
            "-c", "core.quotepath=off",
            "-c", "log.follow=false",
            "-c", "log.showSignature=false",
            "-c", "color.ui=false",
            *args,
        ],
        cwd=str(repo_root),
        capture_output=True,
        check=False,
        timeout=_GIT_TIMEOUT_S,
    )


def _blob_at(repo_root: str | Path, ref: str, rel_path: str) -> bytes | None:
    """The bytes of *rel_path* as committed at *ref*, or ``None`` when absent there.

    ``None`` means ABSENT AT THAT REF and must never be read as "unchanged" — for the
    provenance check it is the ``*-uncommitted`` drift class, not a pass.
    """
    proc = _pinned_git(repo_root, ["show", f"{ref}:{rel_path}"])
    return proc.stdout if proc.returncode == 0 else None


# --------------------------------------------------------------------------- §5.2 the ledger


_LEDGER_HEADING_RE = re.compile(
    r"^##\s+(?P<id>(?:DEF|ASM)-\d+)\s+—\s+(?P<title>.+?)\s+·\s+"
    r"(?P<status>OPEN|ACCEPTED|CLOSED)\s+\((?P<date>\d{4}-\d{2}-\d{2})\)\s*$"
)
#: Loose detector: a line that LOOKS like an entry heading but fails the strict match is
#: SURFACED as a refusal, never skipped — a silently unparsed entry is the false-clean
#: bill of health the ledger exists to prevent (protocol/deferral.md).
_LEDGER_HEADING_PREFIX_RE = re.compile(r"^##\s+(?:DEF|ASM)-\d+\b")
_LEDGER_FIELD_RE = re.compile(r"^[-*]\s+(?P<key>[A-Za-z][A-Za-z0-9_ -]*?)\s*:\s*(?P<value>.*)$")
_SUBHEADING_RE = re.compile(r"^#{3,}\s")

_DEFERRAL_REQUIRED = ("What", "Why", "Provenance", "Owed-to")
_ASSUMPTION_REQUIRED = ("Assumption", "Provenance", "Grilled")


def normalize_ledger_line(line: str) -> str:
    """Flatten the emphasis markers the deferral grammar declares meaningless.

    ``*`` and `` ` `` carry no meaning in this grammar and are flattened; whitespace runs
    collapse.  **The underscore is NOT stripped** — that is the one deliberate difference
    from ``validate_skills._normalize_protocol_text``, because this grammar's field names
    are snake_case (``accepted_by``, ``accepted_at``, ``closing_commit``) and stripping
    ``_`` would mangle exactly the fields a gate must read (protocol/deferral.md states
    this explicitly, "because the mistake is a quiet one").
    """
    return re.sub(r"[ \t]+", " ", line.replace("*", "").replace("`", "")).strip()


def parse_deferral_ledger(path: str | Path, *, kind: str = "DEF") -> list[dict]:
    """Parse a sanctioned-deferral ledger against the ``protocol/deferral.md`` grammar.

    Fail-closed on every shape that contract names: a malformed heading, a missing
    required field, a ``CLOSED`` entry with no ``closing_commit``, an ``ACCEPTED`` entry
    without both approval fields, an unreadable ledger.  **A parse failure is a REFUSAL,
    never a skip** — a parser that shrugs at what it cannot read and returns "no
    deferrals found" produces the exact false clean bill of health the ledger exists to
    prevent (the TM-D3 anti-vacuity companion law applied to the ledger).

    A ledger with ZERO entries is a valid zero and is reported as zero; a ledger that
    could not be READ is not a zero and raises.

    Args:
        path: The ledger path (``.planning/DEFERRED.md`` / ``.planning/ASSUMPTIONS.md``).
        kind: ``"DEF"`` or ``"ASM"`` — selects the required-field set.

    Returns:
        One dict per entry: ``{id, title, status, date, fields, text}`` in file order
        (file order IS the append-only record's order; nothing is re-sorted).

    Raises:
        DeferralLedgerError: on any of the shapes above.
    """
    p = _safe_path(path)
    required = _DEFERRAL_REQUIRED if kind == "DEF" else _ASSUMPTION_REQUIRED
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise DeferralLedgerError(
            f"kata_close: deferral ledger at {p!s} is present but UNREADABLE ({exc}) — "
            "a ledger that could not be read is NOT a zero (protocol/deferral.md). "
            "Refusing to certify.",
            fact_class="deferral",
        ) from exc

    lines = text.splitlines()
    entries: list[dict] = []
    current: dict | None = None
    in_field_block = False

    for raw in lines:
        line = normalize_ledger_line(raw)
        if line.startswith("## "):
            match = _LEDGER_HEADING_RE.match(line)
            if not match:
                if _LEDGER_HEADING_PREFIX_RE.match(line):
                    raise DeferralLedgerError(
                        f"kata_close: malformed ledger entry heading in {p!s}: {line!r} — "
                        "the canonical pattern is '## DEF-<n> — <title> · <OPEN|ACCEPTED|"
                        "CLOSED> (YYYY-MM-DD)'. A heading that does not parse is a REFUSAL, "
                        "never a skip (protocol/deferral.md).",
                        fact_class="deferral",
                    )
                current = None
                in_field_block = False
                continue
            current = {
                "id": match.group("id"),
                "title": match.group("title"),
                "status": match.group("status"),
                "date": match.group("date"),
                "fields": {},
                "text": [line],
            }
            entries.append(current)
            in_field_block = True
            continue
        if current is None:
            continue
        current["text"].append(line)
        if _SUBHEADING_RE.match(line):
            # Content under a sub-heading is preserved RECORD (a closure record, an
            # original filing) and is never read as a second set of fields.
            in_field_block = False
            continue
        if not in_field_block:
            continue
        field = _LEDGER_FIELD_RE.match(line)
        if field:
            current["fields"][field.group("key").strip()] = field.group("value").strip()

    for entry in entries:
        if not entry["id"].startswith(kind):
            continue
        missing = [f for f in required if f not in entry["fields"]]
        if missing:
            raise DeferralLedgerError(
                f"kata_close: ledger entry {entry['id']} in {p!s} is missing required "
                f"field(s) {missing} — a missing required field is a REFUSAL to certify "
                "(protocol/deferral.md).",
                fact_class="deferral",
            )
        if entry["status"] == "CLOSED" and not entry["fields"].get("closing_commit"):
            raise DeferralLedgerError(
                f"kata_close: ledger entry {entry['id']} in {p!s} is CLOSED with no "
                "`closing_commit` — captured is not closed (protocol/deferral.md).",
                fact_class="deferral",
            )
        if entry["status"] == "ACCEPTED" and not (
            entry["fields"].get("accepted_by") and entry["fields"].get("accepted_at")
        ):
            raise DeferralLedgerError(
                f"kata_close: ledger entry {entry['id']} in {p!s} is ACCEPTED without both "
                "`accepted_by` and `accepted_at` — a gate may credit an approval ONLY from "
                "those fields (protocol/deferral.md).",
                fact_class="deferral-approval",
            )
        entry["text"] = "\n".join(entry["text"])
    for entry in entries:
        if isinstance(entry["text"], list):
            entry["text"] = "\n".join(entry["text"])
    return entries


def _token_re(task_id: str) -> re.Pattern[str]:
    """Whole-token matcher for a task-id (so ``T1`` never matches inside ``T12``)."""
    return re.compile(rf"(?<![A-Za-z0-9_-]){re.escape(task_id)}(?![A-Za-z0-9_-])")


#: The ONLY fields a plan-item binding may be read from (see :func:`bind_deferrals`).
BINDING_FIELDS = ("What",)


def bind_deferrals(entries: list[dict], task_ids: set[str]) -> dict[str, list[dict]]:
    """Bind ledger entries to plan tasks — ``{task_id: [entry, …]}``.  PURE.

    **The binding rule, stated so it can be argued with.**  An entry binds to a plan task
    when the task-id appears as a WHOLE TOKEN in the entry's **heading** or its **``What``**
    field — and NOWHERE else.  Three deliberate narrowings, each closing a real hole:

    1. **Whole-token, never substring.**  A substring rule lets ``t1`` claim ``t12``'s
       entry and silently resolve a drifted item.
    2. **``What`` only, never the whole entry.**  ``What`` is contractually *"the concrete
       thing not done"* (protocol/deferral.md); ``Why`` is rationale, ``Provenance`` is
       origin, ``Owed-to`` is the successor who will discharge it.  **None of those three
       says "this plan item was not built."**  Measured on the live ledger before this
       narrowing existed, a whole-entry rule bound ``close-machinery`` to DEF-6 and DEF-12
       purely because both say *"W7 close-machinery adjacency"* in ``Why``/``Owed-to`` —
       neither is a deferral OF that task, and either would have resolved it as
       ``recorded-deferral`` had it drifted.  That is the silent-deferral hole this join
       exists to close, so the loose rule was removed rather than documented.
    3. **``OPEN``/``ACCEPTED`` only.**  A ``CLOSED`` entry says the owed work was BUILT and
       can never stand in for an unbuilt plan item — the "filed, never built, read as
       discharged" confusion protocol/deferral.md names.

    **Honest residual (PD-2), not implied away:** ``What`` is prose, so the binding is
    prose-derived and an entry whose ``What`` merely *mentions* a task-id over-binds.  The
    structural fix is a dedicated binding field (deferral.md already permits additional
    labelled fields), which is a change to a clause-pinned contract this task does not own
    — filed as a deferral candidate rather than taken.  The residual's direction is stated
    too: it over-binds (an item reads deferred), which is the WRONG direction, and the
    narrowing above is what keeps the observed instances out of it.

    Ordering is by entry number then id — an explicit total order (law 10).
    """
    out: dict[str, list[dict]] = {}
    for task_id in sorted(task_ids):
        pattern = _token_re(task_id)
        bound = []
        for entry in entries:
            if not entry["id"].startswith("DEF-") or entry["status"] not in ("OPEN", "ACCEPTED"):
                continue
            surfaces = [entry["title"]] + [
                entry["fields"].get(f, "") for f in BINDING_FIELDS
            ]
            if any(pattern.search(s) for s in surfaces):
                bound.append(entry)
        if bound:
            out[task_id] = sorted(bound, key=lambda e: (int(e["id"].split("-")[1]), e["id"]))
    return out


# --------------------------------------------------------------------------- §5.2 evidence


def default_evidence_runner(argv: tuple[str, ...], cwd: str | Path) -> int:
    """Execute one COMPILED evidence argv and return its RAW exit code.  ``shell=False``.

    The argv arrives from ``evidence_grammar.compile_declaration``, whose closed
    three-form grammar is what makes it trustworthy: a freeform command string is refused
    at compile time and never reaches this function.  There is no code path here that
    accepts a command STRING.

    Doctrine law 8 (gate subprocesses run in a declared environment): ``PYTEST_ADDOPTS``
    is stripped, the nondeterminism plugin is blocked by argv on the known-pytest path
    (surgical, never the blanket autoload disable — a blanket disable would fail a
    target's autoload-reliant tests and deflate the result), and the run carries a
    timeout, because a hung gate is a nondeterministic outcome.

    Returns the RAW exit code.  A timeout or a missing program returns a non-zero code —
    never ``0``, never an exception swallowed into a pass.
    """
    env = {k: v for k, v in os.environ.items() if k != "PYTEST_ADDOPTS"}
    argv = tuple(argv)
    if "pytest" in argv:
        index = argv.index("pytest") + 1
        argv = (*argv[:index], "-p", "no:randomly", *argv[index:])
    try:
        return subprocess.run(
            list(argv), cwd=str(cwd), env=env, capture_output=True,
            check=False, timeout=_EVIDENCE_TIMEOUT_S,
        ).returncode
    except subprocess.TimeoutExpired:
        return 124
    except OSError:
        return 127


def resolve_evidence(
    decl: evidence_grammar.EvidenceDeclaration | str,
    *,
    repo_root: str | Path,
    runner=None,
    registry=None,
    uv_wrap: bool = True,
) -> dict:
    """Resolve ONE declared ``evidence:`` item to exercised / not-exercised.

    ``artifact:`` is an EXISTENCE question and is never executed (that ``argv is None`` is
    the grammar's contract, not an omission).  ``test:`` and ``probe:`` are EXECUTION
    questions and are actually RUN — this is the clause that keeps §5.2's "behavioral
    deliverables resolve through their declared ``evidence:`` form rather than degrading
    to file-touch heuristics" true rather than asserted.

    ``uv_wrap`` applies ``evidence_grammar.uv_wrapped_argv`` at the execution boundary
    (this repo's pytest lives in a uv-managed venv); a caller in another environment
    passes ``False``.  The wrap is explicit and separate precisely so the DESIGN's pinned
    compile target is never silently edited.

    Returns ``{raw, form, exercised, detail, exitCode}``; ``exitCode`` is ``None`` for the
    non-executed ``artifact`` form and the RAW code otherwise (D-6a).
    """
    runner = default_evidence_runner if runner is None else runner
    compiled = evidence_grammar.compile_declaration(decl, repo_root=repo_root, registry=registry)
    if compiled.form == "artifact":
        exists = evidence_grammar.artifact_exists(compiled, repo_root)
        return {
            "raw": compiled.raw, "form": "artifact", "exercised": exists, "exitCode": None,
            "detail": f"artifact {'present' if exists else 'ABSENT'}: {compiled.path!s}",
        }
    argv = evidence_grammar.uv_wrapped_argv(compiled.argv) if uv_wrap else compiled.argv
    cwd = Path(repo_root) / compiled.cwd if compiled.cwd else Path(repo_root)
    code = runner(tuple(argv), cwd)
    return {
        "raw": compiled.raw, "form": compiled.form, "exercised": code == 0, "exitCode": code,
        "detail": f"{' '.join(argv)} → exit {code} (cwd={cwd!s})",
    }


# --------------------------------------------------------------------------- §5.2 the join


def three_way_join(
    *,
    plan_path: str | Path,
    repo_root: str | Path,
    integration_branch: str = "HEAD",
    deferred_path: str | Path | None = None,
    evidence_runner=None,
    registry=None,
    uv_wrap: bool = True,
) -> dict:
    """The TOTAL three-way join (DESIGN §5.2): PLAN ⋈ tree ⋈ ``DEFERRED.md``.

    TOTAL means every task in the frozen PLAN's authoritative task set lands in exactly
    one of the three resolutions — there is no fourth bucket and no silent omission:

    * ``built-and-exercised`` — a ``Kata-Task:`` integration trailer exists for it (tier-2,
      AUTHORITATIVE for DONE per D134) **and every one of its declared ``evidence:`` items
      resolves** (artifacts present; tests/probes RUN and green).  Both halves are
      required: a trailer with dead evidence is not built, and evidence without a trailer
      is not integrated.
    * ``recorded-deferral`` — no trailer, but an ``OPEN``/``ACCEPTED`` ledger entry binds
      to it (:func:`bind_deferrals`).  "A deferral exists only if the operator can see
      it" (PD-1) is what makes this a resolution rather than an excuse.
    * ``drift`` — everything else, **NAMED**.  Not "unknown", not "in progress".

    ``parse_plan_tasks(check_evidence=True)`` is called with the check ON: this function
    is that argument's production caller (D-22 recorded it as having none).  A plan whose
    ``evidence:`` map is missing or ungrammatical fails HERE, before any resolution is
    computed — an undeclared plan cannot be certified.

    Anti-vacuity (TM-D3): a degraded integration scan (unreadable history, an unbounded
    fallback, a malformed invalidation trailer) is REPORTED and makes the join
    ``degraded``; the caller fails closed on it.  A join that ran over nothing must say it
    ran over nothing — it must never render an empty integrated set as "no tasks done".

    Returns ``{items, drift, deferred, built, degraded, reasons, ledger, taskCount}`` with
    every list ``sorted()`` (laws 2/3/10).
    """
    plan_path = _safe_path(plan_path)
    repo_root = Path(repo_root)
    task_ids = kata_restore.parse_plan_tasks(plan_path, check_evidence=True)
    declarations = kata_restore.parse_plan_evidence(plan_path, repo_root=repo_root)

    scan = kata_restore.collect_integrated_tasks_ex(
        str(repo_root), integration_branch, plan_path
    )
    integrated: set[str] = set(scan["tasks"])
    reasons = sorted(set(scan["reasons"]))

    ledger_path = (
        Path(deferred_path) if deferred_path is not None
        else repo_root / ".planning" / "DEFERRED.md"
    )
    if ledger_path.exists():
        entries = parse_deferral_ledger(ledger_path, kind="DEF")
        ledger_present = True
    else:
        # A ledger that is ABSENT is a legal zero and is reported as zero; a ledger that
        # is present but unreadable raises above.  The two cases are never conflated.
        entries, ledger_present = [], False
    bound = bind_deferrals(entries, task_ids)

    items: dict[str, dict] = {}
    for task_id in sorted(task_ids):
        evidence = [
            resolve_evidence(
                decl, repo_root=repo_root, runner=evidence_runner,
                registry=registry, uv_wrap=uv_wrap,
            )
            for decl in declarations.get(task_id, ())
        ]
        has_trailer = task_id in integrated
        all_exercised = bool(evidence) and all(e["exercised"] for e in evidence)
        if has_trailer and all_exercised:
            resolution, why = RESOLUTION_BUILT, "integration trailer + every declared evidence item resolved"
        elif task_id in bound:
            resolution = RESOLUTION_DEFERRED
            why = "no integration trailer; bound to " + ", ".join(
                f"{e['id']} ({e['status']})" for e in bound[task_id]
            )
        elif has_trailer:
            resolution = RESOLUTION_DRIFT
            why = (
                "integration trailer present but declared evidence did NOT resolve: "
                + "; ".join(e["detail"] for e in evidence if not e["exercised"])
            )
        else:
            resolution = RESOLUTION_DRIFT
            why = "no integration trailer and no bound deferral entry"
        items[task_id] = {
            "task": task_id,
            "resolution": resolution,
            "why": why,
            "trailer": has_trailer,
            "evidence": evidence,
            "deferrals": [
                {"id": e["id"], "status": e["status"], "acceptedBy": e["fields"].get("accepted_by"),
                 "acceptedAt": e["fields"].get("accepted_at")}
                for e in bound.get(task_id, [])
            ],
        }

    return {
        "taskCount": len(task_ids),
        "items": items,
        "built": sorted(t for t, i in items.items() if i["resolution"] == RESOLUTION_BUILT),
        "deferred": sorted(t for t, i in items.items() if i["resolution"] == RESOLUTION_DEFERRED),
        "drift": sorted(t for t, i in items.items() if i["resolution"] == RESOLUTION_DRIFT),
        "degraded": bool(scan["degraded"]),
        "reasons": reasons,
        "ledger": {
            "path": str(ledger_path), "present": ledger_present, "entries": len(entries),
            "bound": {k: [e["id"] for e in v] for k, v in sorted(bound.items())},
        },
    }


# --------------------------------------------------------------------------- §5.4 provenance


def _netstring_digest(items: list[tuple[str, bytes]]) -> str:
    """sha256 over LENGTH-PREFIXED (name, content) frames (Doctrine law 4).

    Without the length prefix, ``("ab", b"c")`` and ``("a", b"bc")`` would hash the same —
    the D98 collision lesson.  Items are sorted by name (law 3) before framing.
    """
    digest = hashlib.sha256()
    for name, content in sorted(items, key=lambda i: i[0]):
        name_bytes = name.encode("utf-8")
        digest.update(f"{len(name_bytes)}:".encode("ascii"))
        digest.update(name_bytes)
        digest.update(f"{len(content)}:".encode("ascii"))
        digest.update(content)
    return digest.hexdigest()


def _canonical_provenance(rel_path: str, content: bytes | None) -> bytes | None:
    """Canonicalize a provenance file's bytes for comparison.

    ``kata.config`` is JSON: it is parsed, stripped of its MACHINE-LOCAL values
    (``kata_config.split_machine_local`` — personal paths that legitimately differ per
    machine and now live in ``.kata-settings.json``), and re-serialized ``sort_keys=True``
    (law 5), so a formatting difference or a machine-local path is never read as drift and
    a real value change always is.  ``INTENT.md`` is text: line endings are normalized to
    LF and trailing whitespace stripped, nothing else — its content IS the provenance.

    Returns ``None`` unchanged (absent is absent, never "empty").  Unparseable JSON is
    returned as its raw bytes: a broken committed config must READ as different from a
    valid one, never be silently normalized into agreement.
    """
    if content is None:
        return None
    if rel_path.endswith(".json") or Path(rel_path).name == "kata.config":
        try:
            parsed = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return content
        if isinstance(parsed, dict):
            clean, _ = kata_config.split_machine_local(parsed)
            parsed = clean
        return json.dumps(parsed, sort_keys=True, separators=(",", ":")).encode("utf-8")
    text = content.decode("utf-8", "replace").replace("\r\n", "\n").replace("\r", "\n")
    return "\n".join(line.rstrip() for line in text.split("\n")).strip().encode("utf-8")


def provenance_drift(
    *,
    repo_root: str | Path,
    config_path: str = "kata.config",
    intent_path: str = "INTENT.md",
    ref: str = "HEAD",
    executed: dict | None = None,
    arms: list[dict] | None = None,
) -> dict:
    """The TM-A2 / §5.4 provenance drift check.

    *"At branch close, if ``kata.config``/``INTENT.md`` as committed do not match what the
    run actually executed (per the cursor record), the close FAILS and the run routes per
    §5.3."*

    The COMMITTED side is read from git at *ref* (never from the working tree — that is
    the whole point of the check).  The EXECUTED side is, in order of authority:

    1. ``executed`` — a recorded ``{rel_path: canonical-bytes-digest}`` map handed in by
       the caller from the run's own cursor record.  AUTHORITATIVE when present.
    2. the working-tree content of the same paths, labelled ``source: "working-tree"`` in
       the result.  **Stated honestly, not implied away:** the seam records no
       config-provenance digest at ``run_start`` today, so with no recorded map this leg
       compares what the run READ (the files on disk it executed against) with what was
       COMMITTED.  That catches the real class — a config edited or never committed — and
       it does NOT catch a config edited after the run read it and before the close.  The
       recorded-map leg (1) is the closure for that residual and the argument this
       function takes for it.

    Drift classes, each NAMED (never a bare boolean): ``config-drift`` · ``intent-drift`` ·
    ``config-uncommitted`` · ``intent-uncommitted`` · ``config-absent`` · ``intent-absent``.

    **Tree semantics (TM-A2 rider / R-M8):** the drift check for a tree is the committed
    config + arm registry versus EACH arm's recorded execution.  *arms* is
    ``[{"label": …, "executed": {…}}, …]``; each is checked against the SAME committed
    side, which is sound by construction because child runs never rewrite the committed
    config — so fan-in cannot conflict on config.

    Returns ``{drift, classes, committed, executed, source, arms}``; ``drift`` is True iff
    ``classes`` is non-empty.
    """
    repo_root = Path(repo_root)
    paths = {"config": config_path, "intent": intent_path}
    committed: dict[str, str | None] = {}
    committed_raw: dict[str, bytes | None] = {}
    for label, rel in sorted(paths.items()):
        blob = _canonical_provenance(rel, _blob_at(repo_root, ref, rel))
        committed_raw[label] = blob
        committed[label] = None if blob is None else hashlib.sha256(blob).hexdigest()

    def _executed_side(recorded: dict | None) -> tuple[dict[str, str | None], str]:
        if recorded:
            return ({k: recorded.get(k) for k in sorted(paths)}, "recorded")
        out: dict[str, str | None] = {}
        for label, rel in sorted(paths.items()):
            path = repo_root / rel
            raw = path.read_bytes() if path.is_file() else None
            blob = _canonical_provenance(rel, raw)
            out[label] = None if blob is None else hashlib.sha256(blob).hexdigest()
        return out, "working-tree"

    def _classes(exec_side: dict[str, str | None]) -> list[str]:
        found: list[str] = []
        for label in sorted(paths):
            if exec_side[label] is None:
                found.append(f"{label}-absent")
            elif committed[label] is None:
                found.append(f"{label}-uncommitted")
            elif committed[label] != exec_side[label]:
                found.append(f"{label}-drift")
        return sorted(found)

    exec_side, source = _executed_side(executed)
    classes = _classes(exec_side)

    arm_results: list[dict] = []
    for arm in sorted(arms or [], key=lambda a: str(a.get("label", ""))):
        arm_exec, arm_source = _executed_side(arm.get("executed"))
        arm_classes = _classes(arm_exec)
        arm_results.append({
            "label": str(arm.get("label", "")), "executed": arm_exec,
            "source": arm_source, "classes": arm_classes, "drift": bool(arm_classes),
        })
        classes = sorted(set(classes) | {f"arm:{arm.get('label', '')}:{c}" for c in arm_classes})

    return {
        "drift": bool(classes),
        "classes": classes,
        "committed": committed,
        "executed": exec_side,
        "source": source,
        "ref": ref,
        "paths": paths,
        "arms": arm_results,
        "digest": _netstring_digest(
            [(k, v or b"") for k, v in committed_raw.items() if v is not None]
        ),
    }


def migrate_machine_local(
    config_path: str | Path,
    *,
    home: str | Path | None = None,
    write: bool = True,
) -> dict:
    """Move machine-specific values out of ``kata.config`` into ``.kata-settings.json``.

    The completion of the cursor's machine-change story (§5.4): personal paths move to the
    existing machine-local home so ``kata.config`` becomes clean, COMMITTED run
    provenance that means the same thing on every machine — which is what makes the drift
    check above a signal rather than noise.

    Idempotent: a config with nothing machine-specific left is a no-op returning
    ``{"moved": {}}``.  ``write=False`` previews without touching either file.

    Returns ``{moved, clean, configPath, settingsPath}``.
    """
    path = _safe_path(config_path)
    config = json.loads(path.read_text(encoding="utf-8"))
    clean, moved = kata_config.split_machine_local(config)
    settings_path = kata_settings.settings_path(home)
    if write and moved:
        kata_settings.record_machine_local(moved, home=home)
        path.write_text(json.dumps(clean, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "moved": moved, "clean": clean,
        "configPath": str(path), "settingsPath": str(settings_path),
    }


# --------------------------------------------------------------------------- RS-M7 redaction


def _scrub(text: str) -> tuple[str, dict[str, int]]:
    """THE scrub — ``learn_feed.redact``, unchanged and unwrapped.

    RS-M7: *"the scrub extends ``learn_feed.redact``'s class table (one scrub, not two)"*.
    Both named points below call THIS function, which calls THAT one.  There is no second
    pattern table in this module, deliberately: a second table is how two scrubs drift
    apart and one of them silently stops covering a class.
    """
    return learn_feed.redact(text)


def redact_at_commit_act(payload: dict[str, str]) -> dict:
    """**Named point 1 (RS-M7):** the scrub over committed run provenance, at BRANCH CLOSE.

    At the commit act, never at mint — that placement is what closes the TOCTOU window
    (a file scanned at mint can be edited before it is committed).

    **Fail-closed** (§8 S4): any detected class REFUSES the commit act.  Redaction is
    DETECTION and says so — undetected content is a stated residual (§11), and this
    function's clean return means "no class in the table matched", never "no secret is
    present".

    Args:
        payload: ``{name: text}`` — the content about to be committed.

    Returns:
        ``{"clean": True, "scanned": [names…], "counts": {}}`` when nothing matched.

    Raises:
        RedactionRefused: naming every class that hit and where.
    """
    counts: dict[str, dict[str, int]] = {}
    for name in sorted(payload):
        _, hits = _scrub(payload[name] or "")
        if hits:
            counts[name] = dict(sorted(hits.items()))
    if counts:
        detail = "; ".join(
            f"{name}: {', '.join(f'{cls}×{n}' for cls, n in sorted(hits.items()))}"
            for name, hits in sorted(counts.items())
        )
        raise RedactionRefused(
            f"kata_close: REFUSING the commit act — the redaction scrub detected "
            f"secret/key/PII class(es) in the content about to be committed: {detail}. "
            "Detected classes fail CLOSED at the commit act (DESIGN §8 S4 / RS-M7). "
            "Remove the value, rotate it if it was ever real, and re-run the close. "
            "Redaction is detection, not prevention: a clean result means no class in "
            "learn_feed's table matched, never that no secret is present.",
            fact_class="provenance",
        )
    return {"clean": True, "scanned": sorted(payload), "counts": {}}


def redact_at_snapshot_edge(text: str) -> tuple[str, dict[str, int]]:
    """**Named point 2 (RS-M7):** the scrub over cursor/trail content at the snapshot-or-push edge.

    The same ONE scrub as :func:`redact_at_commit_act`, applied where cursor content
    leaves the machine.  This point SCRUBS rather than refuses: the cursor is an
    append-only record that has already been written, so refusing here would only make
    the run undurable while leaving the bytes exactly where they were.  Returning the
    scrubbed text with its counts is the honest act — the counts are what a caller
    records.
    """
    return _scrub(text)


# --------------------------------------------------------------------------- RS-M6 consent


def consent_key(target_repo: str | Path) -> str:
    """The per-target consent key — the target repo's resolved absolute path."""
    return str(_safe_path(target_repo).resolve())


def _consent_token_path(target: str, home: str | Path | None) -> Path:
    base = kata_settings.settings_path(home).parent / CONSENT_LOCK_DIRNAME
    digest = hashlib.sha256(target.encode("utf-8")).hexdigest()
    return base / f"{digest}{CONSENT_TOKEN_SUFFIX}"


def is_own_repo(target_repo: str | Path, *, home: str | Path | None = None) -> bool:
    """True when *target_repo* IS the harness's own repo — which consents by standing config.

    §5.4: *"the harness's own repo consents by standing config"*.  Everything else is a
    TARGET repo and gets the first-run consent moment.
    """
    try:
        return Path(consent_key(target_repo)) == kata_settings.settings_path(home).parent.resolve()
    except (OSError, ValueError):
        return False


def target_consent(
    target_repo: str | Path,
    *,
    prompter=None,
    home: str | Path | None = None,
    kata_dir: str | Path | None = None,
    now: datetime | None = None,
) -> dict:
    """The RS-M6 first-run consent moment: per-target, remembered, fires EXACTLY once.

    Committing ``INTENT.md``/``kata.config`` into a TARGET repo is an outward act, so it
    gets a human moment the first time — and only the first time.  The decision is
    remembered machine-local in ``.kata-settings.json`` (never in the target repo, which
    is the thing being consented to).  **Redaction is not consent; both apply** — the
    commit act runs its scrub regardless of what this returns.

    **Exactly-once under a race** is structural, not hoped for.  Three steps:

    1. read the remembered decision — if one exists, RETURN it and never prompt;
    2. elect a prompter by ``O_CREAT|O_EXCL`` exclusive create of a per-target token.
       Exactly one caller can create a given path.  ``os.rename`` is deliberately NOT the
       election: renaming a file onto the path it already occupies is a documented no-op
       SUCCESS on Windows, so a rename-election degrades to everyone-wins (D-25, measured);
    3. the winner prompts and records; every loser is REFUSED (it must not prompt, and it
       must not proceed on an un-recorded decision).

    **Unattended runs PARK, never proceed** (TM-B5): with no *prompter*, the consent
    moment writes a ``human-required`` escalation to ``<kata_dir>/escalations/`` — the
    park is the CALLER's act and this function performs it, rather than merely naming a
    path nothing is obliged to create (DEF-13's class) — and raises
    :class:`ConsentRequired`.

    Returns ``{granted, target, source, at, by, parkPath}``.
    """
    target = consent_key(target_repo)
    remembered = kata_settings.target_consent(target, home=home)
    if remembered is not None:
        return {**remembered, "target": target, "source": "remembered", "parkPath": None}

    if is_own_repo(target_repo, home=home):
        return {
            "granted": True, "target": target, "source": "standing-config",
            "at": _utc(now), "by": "standing config (the harness's own repo)", "parkPath": None,
        }

    token = _consent_token_path(target, home)
    token.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.close(os.open(token, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError as exc:
        # A concurrent caller holds the prompt election.  Re-read: it may have recorded
        # while we raced.  If not, REFUSE — a loser never prompts and never assumes.
        recorded = kata_settings.target_consent(target, home=home)
        if recorded is not None:
            return {**recorded, "target": target, "source": "remembered", "parkPath": None}
        raise ConsentRequired(
            f"kata_close: the first-run consent moment for target {target!r} is already "
            "held by another caller and no decision is recorded yet — the prompt fires "
            "EXACTLY once per target (RS-M6). Wait for that caller to record the "
            "decision, then re-run the close.",
            fact_class="provenance",
        ) from exc
    except OSError as exc:
        raise ConsentRequired(
            f"kata_close: cannot elect a consent prompter for target {target!r} at "
            f"{token!s} ({exc}) — refusing to commit run provenance into a target repo "
            "without a recorded consent decision.",
            fact_class="provenance",
        ) from exc

    if _CONSENT_RACE_HOOK is not None:  # test seam — the exact race point
        _CONSENT_RACE_HOOK(target)

    if prompter is None:
        park_path = None
        if kata_dir is not None:
            park_path = escalation.write_escalation(
                str(kata_dir),
                escalation.build_escalation(
                    taskId="close-consent",
                    kind="human-required",
                    decisionNeeded=(
                        f"Commit run provenance (kata.config / INTENT.md) into the target "
                        f"repo {target}? This is an outward act and needs first-run consent."
                    ),
                    optionsConsidered=[
                        "grant consent (remembered machine-local, per-target, asked once)",
                        "decline — the close does not commit provenance into this target",
                    ],
                    agentRecommendation=(
                        "PARK for the operator. An unattended run never grants an outward-act "
                        "consent on the operator's behalf."
                    ),
                    rationale=(
                        "RS-M6: the consent moment is per-target and remembered machine-local; "
                        "TM-B5: an unattended run PARKS the task, never proceeds and never dies "
                        "silently. Redaction is not consent — both apply."
                    ),
                ),
            )
        raise ConsentRequired(
            f"kata_close: PARKED — target {target!r} has no recorded consent decision and "
            "this run is unattended (no prompter). An unattended run PARKS the consent "
            f"moment, never proceeds (TM-B5). Park artifact: {park_path}",
            fact_class="provenance",
        )

    granted = bool(prompter(target))
    decision = {"granted": granted, "by": "operator", "at": _utc(now)}
    kata_settings.record_target_consent(target, decision, home=home)
    return {**decision, "target": target, "source": "prompted", "parkPath": None}


# --------------------------------------------------------------------------- §5.3 records


def missing_required_records(
    cursor: _kb.Cursor,
    *,
    kata_dir: str | Path,
    provenance: dict,
    join: dict | None,
) -> list[dict]:
    """The §5.3 absent-records check — *"refuses without required records"*.

    The backstop for capture-edge loss of ANY kind (§1.6, RS-L1): if the record a fact
    class is graded from does not exist, the close refuses rather than grading the class
    from something else.  Each finding names its fact class AND that class's system of
    record (D134) so the refusal is auditable rather than assertive.

    Returns a list of ``{class, systemOfRecord, reason}`` — empty when every required
    record is present.  PURE over its inputs (no clock, no subprocess).
    """
    kata = _kata_dir(kata_dir)
    missing: list[dict] = []

    def _miss(fact_class: str, reason: str) -> None:
        missing.append({
            "class": fact_class,
            "systemOfRecord": SYSTEM_OF_RECORD[fact_class],
            "reason": reason,
        })

    state = _kd.phase_state(cursor)
    if not (state["open"] or state["closed"]):
        _miss("phase", (
            "the cursor records NO phase events at all — a run with no recorded position "
            "cannot be closed against its plan; the close would be grading an empty record."
        ))
    if provenance.get("committed", {}).get("config") is None:
        _miss("provenance", (
            "kata.config is not committed at the close ref — committed run provenance is "
            "the record the drift check compares against, and it does not exist."
        ))
    if join is not None and join.get("degraded"):
        _miss("task-done", (
            "the integration-trailer scan is DEGRADED "
            f"({', '.join(join.get('reasons') or ['unspecified'])}) — an unreadable or "
            "unbounded history cannot be credited as 'no tasks done' (anti-vacuity, TM-D3)."
        ))
    if join is not None and join.get("taskCount", 0) == 0:
        _miss("task-done", (
            "the frozen PLAN yields an EMPTY task set — a join over zero items certifies "
            "nothing and must report that it ran over nothing (anti-vacuity, TM-D3)."
        ))
    if not _kb.cursor_path(kata).is_file():
        _miss("phase", f"no cursor file at {_kb.cursor_path(kata)!s}.")
    return sorted(missing, key=lambda m: (m["class"], m["reason"]))


# --------------------------------------------------------------------------- §5.1 metrics


def truth_metrics(
    join: dict,
    *,
    provenance: dict,
    declared: dict | None = None,
    derived: dict | None = None,
) -> dict:
    """The §5.1 rider-2 truth metrics + the TM-A1 remediation routing.

    *"Truth metrics at the final report: items resolved, evidence per item, drift named,
    deferrals with approvals; leftovers are always displayed, with the option to execute
    them in another run."*  ``leftovers`` is therefore always present and always carries
    ``runAgain: True`` — never suppressed when empty, because "no leftovers" is itself
    the fact the operator is owed.

    **TM-A1 routing.**  A ``Broken`` finding, or a ``Dormant`` capability CLAIMED as
    ``Verified``, is NEEDS_WORK-class and routes to a re-loop — operator verbatim:
    *"if anything is false or facade it should be another loop pass"*.  ``declared`` is
    what the run's surfaces CLAIMED (``{enforcement, capture, resilience}``); ``derived``
    is what the probes/folds actually produced.  A claim stronger than its derivation is
    the facade class by definition, and it is graded here rather than left to prose.

    Returns ``{itemsResolved, evidencePerItem, driftNamed, deferralsWithApprovals,
    leftovers, guardian, needsWork, routing}``.
    """
    items = join["items"]
    leftovers = sorted(join["drift"] + join["deferred"])

    findings: list[dict] = []
    declared = declared or {}
    derived = derived or {}
    rank = {"Broken": 0, "Dormant": 1, "Honor-system": 2, "Partially verified": 3, "Verified": 4}

    def _grade(value: str | None) -> tuple[str, int]:
        head = (value or "").split(" (")[0].strip()
        return head, rank.get(head, -1)

    for surface in sorted(set(declared) | set(derived)):
        claimed_head, claimed_rank = _grade(declared.get(surface))
        actual_head, actual_rank = _grade(derived.get(surface))
        if actual_head == "Broken":
            findings.append({
                "surface": surface, "declared": declared.get(surface),
                "derived": derived.get(surface), "class": "broken",
            })
        elif claimed_rank > actual_rank >= 0:
            findings.append({
                "surface": surface, "declared": declared.get(surface),
                "derived": derived.get(surface), "class": "claimed-stronger-than-derived",
            })

    needs_work = bool(join["drift"]) or bool(provenance["drift"]) or bool(findings)
    return {
        "itemsResolved": {
            RESOLUTION_BUILT: len(join["built"]),
            RESOLUTION_DEFERRED: len(join["deferred"]),
            RESOLUTION_DRIFT: len(join["drift"]),
        },
        "evidencePerItem": {
            task: [
                {"raw": e["raw"], "exercised": e["exercised"], "exitCode": e["exitCode"]}
                for e in items[task]["evidence"]
            ]
            for task in sorted(items)
        },
        "driftNamed": sorted(join["drift"]),
        "provenanceDrift": sorted(provenance["classes"]),
        "deferralsWithApprovals": {
            task: items[task]["deferrals"] for task in sorted(join["deferred"])
        },
        "leftovers": {"items": leftovers, "runAgain": True},
        "guardian": {"declared": dict(sorted(declared.items())),
                     "derived": dict(sorted(derived.items())), "findings": findings},
        "needsWork": needs_work,
        "routing": ("re-loop" if needs_work else "close"),
        "operatorVerbatim": TM_A1_VERBATIM,
    }


# --------------------------------------------------------------------------- the verdict artifact


def close_dir(kata_dir: str | Path) -> Path:
    """``<kata_dir>/close/`` — the close's own artifact directory."""
    return _kata_dir(kata_dir) / CLOSE_DIRNAME


def closing_token_path(kata_dir: str | Path, run_id: str) -> Path:
    """The exactly-once close-election token for *run_id*."""
    return close_dir(kata_dir) / f"{_kb.validate_run_id(run_id)}{CLOSING_TOKEN_SUFFIX}"


def emit_close_verdict(
    kata_dir: str | Path, run_id: str, verdict: str, payload: dict, *, now: datetime | None = None
) -> dict:
    """Write the close verdict artifact in the TM-C4 shape: a VERDICT line + a payload.

    Line 1 of the ``.md`` is ``VERDICT: <enum>`` — the SAME strict first-line shape the
    seam's ONE verdict parser reads, so the close's own verdict cannot be forged from
    body content.  The payload is a pointed-to JSON file (the escalation line+payload
    idiom), written ``sort_keys=True`` (law 5).

    The artifact is emitted on EVERY outcome, refusals included.  That is deliberate: a
    refusal must leave an artifact a report can cite, because a refusal message's
    narration is a description of the legal path and never evidence the path was taken.
    """
    if verdict not in VERDICTS:
        raise ValueError(f"kata_close: verdict {verdict!r} is not in the closed enum {sorted(VERDICTS)}")
    out_dir = close_dir(kata_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    run = _kb.validate_run_id(run_id)
    json_path = out_dir / f"{run}-close.json"
    md_path = out_dir / f"{run}-close.md"
    body = {**payload, "verdict": verdict, "runId": run, "closedUtc": _utc(now)}
    json_path.write_text(json.dumps(body, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    md_path.write_text(
        f"VERDICT: {verdict}\n"
        f"payload={json_path.name}\n"
        f"runId: {run}\n",
        encoding="utf-8",
    )
    return {"verdict": verdict, "verdictPath": str(md_path), "payloadPath": str(json_path)}


# --------------------------------------------------------------------------- §1.3 close_run


def close_run(
    kata_dir: str | Path,
    *,
    plan_path: str | Path,
    repo_root: str | Path = ".",
    integration_branch: str = "HEAD",
    deferred_path: str | Path | None = None,
    config_path: str = "kata.config",
    intent_path: str = "INTENT.md",
    ref: str = "HEAD",
    executed_provenance: dict | None = None,
    arms: list[dict] | None = None,
    declared: dict | None = None,
    derived: dict | None = None,
    consent_prompter=None,
    settings_home: str | Path | None = None,
    accepted_by: str | None = None,
    accepted_at: str | None = None,
    close_open_phases: bool = True,
    evidence_runner=None,
    registry=None,
    uv_wrap: bool = True,
    now: datetime | None = None,
) -> dict:
    """**The plan-grounding close** (DESIGN §1.3 row 7, §5).  Fail-closed at every step.

    The run ends by PROVING itself against the frozen plan.  In order:

    1. **Election.**  The terminal record is written exactly once, and that is structural:
       an ``O_CREAT|O_EXCL`` exclusive create of ``<kata>/close/<runId>.closing`` elects
       one closer; every other caller is refused.  ``os.rename`` is deliberately not the
       election (a rename onto an occupied path is a documented no-op success on Windows —
       D-25, measured 8/8 winners per round).  ``kata_dispatch.phase()``'s own terminality
       is the second, independent layer.
    2. **Absent-records refusal** (§5.3) — per fact class, bound to that class's system of
       record (:data:`SYSTEM_OF_RECORD`, D134).
    3. **Provenance drift** (§5.4 / TM-A2), including per-arm tree semantics.
    4. **The TOTAL three-way join** (§5.2).
    5. **Redaction at the commit act** (RS-M7) over the provenance about to be committed —
       fail-closed on any detected class.
    6. **First-run consent** (RS-M6) for a TARGET repo — remembered, once, PARKS unattended.
    7. **Truth metrics + TM-A1 routing** (§5.1 rider 2).
    8. **The verdict** — ``CLOSED`` clean; ``NEEDS_WORK`` otherwise, unless a recorded
       operator acceptance (``accepted_by`` + ``accepted_at``, the TM-D1 shape) makes it
       ``ACCEPTED``.  The artifact is emitted on every outcome, refusals included.
    9. **The terminal write** — open phases closed LIFO (the loop-back ruling in this
       module's docstring), then one ``run-closed`` PHASE line through the seam.

    A failing verdict raises :class:`CloseRefused` carrying ``verdict_path``.  Nothing
    appends to the cursor after ``run-closed`` — the seam refuses it.

    Returns the close record: ``{runId, verdict, verdictPath, payloadPath, join,
    provenance, metrics, consent, phasesClosed, terminalLine}``.
    """
    kata = _kata_dir(kata_dir)
    repo_root = Path(repo_root)

    try:
        cursor = _kb.read_cursor(kata)
    except _kb.CursorError as exc:
        raise CloseRefused(
            f"kata_close: no readable cursor at {_kb.cursor_path(kata)!s} ({exc}) — the "
            "close refuses without the required records; there is nothing to close and "
            "nothing to close it against (DESIGN §5.3).",
            fact_class="phase",
        ) from exc

    run_id = cursor.run_id
    if _kd.is_run_closed(cursor):
        raise CloseRefused(
            f"kata_close: run {run_id} is ALREADY CLOSED — the terminal 'run-closed' PHASE "
            "line is recorded and is written exactly once (DESIGN §2.6, R4 residual 3). "
            "Nothing is legal on this cursor after it.",
            fact_class="phase",
        )

    # --- 1. ELECTION: atomic exclusive create.  Exactly one closer can win. ---
    token = closing_token_path(kata, run_id)
    token.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.close(os.open(token, os.O_CREAT | os.O_EXCL | os.O_WRONLY))
    except FileExistsError as exc:
        raise CloseRefused(
            f"kata_close: run {run_id} is already being closed by another caller (the "
            f"close election at {token!s} is held) — the terminal 'run-closed' record is "
            "written EXACTLY ONCE. If that closer died, remove the token by hand after "
            "verifying no terminal line was written.",
            fact_class="phase",
        ) from exc
    except OSError as exc:
        raise CloseRefused(
            f"kata_close: cannot elect a closer for run {run_id} at {token!s} ({exc}) — "
            "refusing to close without an election.",
            fact_class="phase",
        ) from exc

    if _CLOSE_RACE_HOOK is not None:  # test seam — the exact race point
        _CLOSE_RACE_HOOK(run_id)

    try:
        return _close_elected(
            kata=kata, cursor=cursor, run_id=run_id, repo_root=repo_root,
            plan_path=plan_path, integration_branch=integration_branch,
            deferred_path=deferred_path, config_path=config_path, intent_path=intent_path,
            ref=ref, executed_provenance=executed_provenance, arms=arms,
            declared=declared, derived=derived, consent_prompter=consent_prompter,
            settings_home=settings_home, accepted_by=accepted_by, accepted_at=accepted_at,
            close_open_phases=close_open_phases, evidence_runner=evidence_runner,
            registry=registry, uv_wrap=uv_wrap, now=now,
        )
    except BaseException:
        # RELEASE the election on any outcome that did NOT write the terminal line.
        #
        # This is the one place the claim-token analogy from `kata_dispatch.claim_record`
        # deliberately does NOT carry over.  There, a stuck token denying a record forever
        # is the safe direction (a dispatch record is single-use and re-mintable).  Here,
        # a refusal is the EXPECTED outcome of a fail-closed close: §5.3's two legal paths
        # both end in calling close_run again (after another loop pass, or with the
        # recorded operator acceptance).  A token retained across a refusal would make
        # the sanctioned legal path unreachable without manual filesystem surgery — the
        # gate would be enforcing "you may never close this run" rather than "prove it
        # first".  Exactly-once is unharmed: the token is held for the duration of a close
        # IN FLIGHT, which is precisely the window a second closer must lose, and the
        # written terminal line (plus `is_run_closed`) is what makes a SUCCESSFUL close
        # unrepeatable.
        try:
            os.unlink(token)
        except OSError:
            pass
        raise


def _close_elected(
    *,
    kata: Path,
    cursor: _kb.Cursor,
    run_id: str,
    repo_root: Path,
    plan_path: str | Path,
    integration_branch: str,
    deferred_path: str | Path | None,
    config_path: str,
    intent_path: str,
    ref: str,
    executed_provenance: dict | None,
    arms: list[dict] | None,
    declared: dict | None,
    derived: dict | None,
    consent_prompter,
    settings_home: str | Path | None,
    accepted_by: str | None,
    accepted_at: str | None,
    close_open_phases: bool,
    evidence_runner,
    registry,
    uv_wrap: bool,
    now: datetime | None,
) -> dict:
    """Steps 2-9 of :func:`close_run`, run by the ELECTED closer only.

    Split out so the election's release semantics live in exactly one place (the caller's
    ``except``) instead of being repeated at every refusal site — a released-here /
    forgotten-there split is how a fail-closed gate quietly becomes unreachable.
    """
    base: dict = {"runId": run_id, "planPath": str(plan_path), "repoRoot": str(repo_root)}

    def _refuse(exc: CloseRefused, extra: dict) -> CloseRefused:
        """Emit the artifact FIRST, then attach its path to the refusal (R14)."""
        emitted = emit_close_verdict(
            kata, run_id, VERDICT_NEEDS_WORK,
            {**base, **extra, "refusal": {"class": exc.fact_class, "message": str(exc)},
             "legalPaths": TWO_LEGAL_PATHS},
            now=now,
        )
        exc.verdict_path = emitted["verdictPath"]
        return exc

    # --- 3. PROVENANCE DRIFT (before the join: it feeds the records check). ---
    provenance = provenance_drift(
        repo_root=repo_root, config_path=config_path, intent_path=intent_path,
        ref=ref, executed=executed_provenance, arms=arms,
    )

    # --- 4. THE THREE-WAY JOIN. ---
    try:
        join = three_way_join(
            plan_path=plan_path, repo_root=repo_root, integration_branch=integration_branch,
            deferred_path=deferred_path, evidence_runner=evidence_runner,
            registry=registry, uv_wrap=uv_wrap,
        )
    except CloseRefused as exc:
        raise _refuse(exc, {"provenance": provenance}) from exc
    except ValueError as exc:
        raise _refuse(
            CloseRefused(
                f"kata_close: the frozen PLAN at {plan_path!s} cannot be joined ({exc}) — "
                "the close refuses to certify a plan it cannot read (DESIGN §5.1/§5.2).",
                fact_class="task-evidence",
            ),
            {"provenance": provenance},
        ) from exc

    # --- 2. ABSENT-RECORDS REFUSAL (§5.3). ---
    missing = missing_required_records(
        cursor, kata_dir=kata, provenance=provenance, join=join
    )
    if missing:
        detail = "; ".join(f"{m['class']}: {m['reason']}" for m in missing)
        raise _refuse(
            CloseRefused(
                f"kata_close: REFUSING to close run {run_id} — required records are ABSENT. "
                f"{detail} Each refusal binds to that fact class's system of record (D134); "
                "the absent-records refusal is the backstop for capture-edge loss of any "
                f"kind (DESIGN §1.6, RS-L1). {TWO_LEGAL_PATHS}",
                fact_class=missing[0]["class"],
            ),
            {"provenance": provenance, "join": join, "missingRecords": missing},
        )

    # --- 5. REDACTION AT THE COMMIT ACT (RS-M7) + 6. CONSENT (RS-M6). ---
    to_commit: dict[str, str] = {}
    for label, rel in sorted({"config": config_path, "intent": intent_path}.items()):
        candidate = repo_root / rel
        if candidate.is_file():
            to_commit[label] = candidate.read_text(encoding="utf-8", errors="replace")
    try:
        scrub = redact_at_commit_act(to_commit)
    except RedactionRefused as exc:
        raise _refuse(exc, {"provenance": provenance, "join": join}) from exc

    try:
        consent = target_consent(
            repo_root, prompter=consent_prompter, home=settings_home, kata_dir=kata, now=now
        )
    except ConsentRequired as exc:
        raise _refuse(exc, {"provenance": provenance, "join": join, "scrub": scrub}) from exc
    if not consent["granted"]:
        raise _refuse(
            CloseRefused(
                f"kata_close: consent for target {consent['target']!r} is recorded as "
                "DECLINED — committing run provenance into it is an outward act the "
                "operator has refused (RS-M6).",
                fact_class="provenance",
            ),
            {"provenance": provenance, "join": join, "scrub": scrub, "consent": consent},
        )

    # --- 7. TRUTH METRICS + TM-A1 ROUTING. ---
    metrics = truth_metrics(join, provenance=provenance, declared=declared, derived=derived)

    # --- 8. THE VERDICT. ---
    acceptance: dict | None = None
    if metrics["needsWork"]:
        if accepted_by and accepted_at:
            acceptance = {"accepted_by": str(accepted_by), "accepted_at": str(accepted_at)}
            verdict = VERDICT_ACCEPTED
        elif accepted_by or accepted_at:
            raise _refuse(
                CloseRefused(
                    "kata_close: a recorded operator acceptance needs BOTH accepted_by and "
                    "accepted_at (the TM-D1 approval shape) — a half-recorded approval is "
                    "never credited (protocol/deferral.md: a gate may credit an approval "
                    "ONLY from these fields).",
                    fact_class="deferral-approval",
                ),
                {"provenance": provenance, "join": join, "scrub": scrub, "consent": consent,
                 "metrics": metrics},
            )
        else:
            raise _refuse(
                CloseRefused(
                    f"kata_close: REFUSING to close run {run_id} — "
                    f"drift: {metrics['driftNamed']}; provenance drift: "
                    f"{metrics['provenanceDrift']}; guardian findings: "
                    f"{[f['surface'] for f in metrics['guardian']['findings']]}. "
                    f"TM-A1 routing: NEEDS_WORK-class ⇒ re-loop — {TM_A1_VERBATIM!r} "
                    f"(operator verbatim). {TWO_LEGAL_PATHS}",
                    fact_class="task-done",
                ),
                {"provenance": provenance, "join": join, "scrub": scrub, "consent": consent,
                 "metrics": metrics},
            )
    else:
        verdict = VERDICT_CLOSED

    # --- 9. THE TERMINAL WRITE (the loop-back ruling — see the module docstring). ---
    state = _kd.phase_state(cursor)
    open_phases = list(state["open"])
    if open_phases and not close_open_phases:
        raise _refuse(
            CloseRefused(
                f"kata_close: run {run_id} still holds open phase(s) {open_phases} and "
                "close_open_phases=False. The terminal 'run-closed' line is refused while "
                "any phase is open (DESIGN §2.6). INSTRUCTION: close them — call close_run "
                "with close_open_phases=True, which closes them LIFO (LOOP-BACK first, "
                "because it was opened last), or close each one yourself via "
                "kata_dispatch.phase(kata, 'close <PHASE>') and re-run the close.",
                fact_class="phase",
            ),
            {"provenance": provenance, "join": join, "scrub": scrub, "consent": consent,
             "metrics": metrics, "openPhases": open_phases},
        )

    loop_back = "LOOP-BACK" in open_phases or "LOOP-BACK" in state["closed"]
    closed_now: list[str] = []
    for key in reversed(open_phases):  # LIFO — LOOP-BACK closes first, it was opened last
        _kd.phase(kata, f"close {_phase_close_msg(key)}", task="close",
                  repo_root=str(repo_root), now=now)
        closed_now.append(key)

    emitted = emit_close_verdict(
        kata, run_id, verdict,
        {**base, "provenance": provenance, "join": join, "scrub": scrub, "consent": consent,
         "metrics": metrics, "acceptance": acceptance, "phasesClosed": closed_now,
         "loopBack": loop_back, "legalPaths": TWO_LEGAL_PATHS,
         "systemOfRecord": SYSTEM_OF_RECORD},
        now=now,
    )

    terminal_msg = f"run-closed verdict={verdict}" + (" loopBack=1" if loop_back else "")
    terminal = _kd.phase(kata, terminal_msg, task="close", repo_root=str(repo_root), now=now)

    return {
        "runId": run_id, "verdict": verdict, "verdictPath": emitted["verdictPath"],
        "payloadPath": emitted["payloadPath"], "join": join, "provenance": provenance,
        "metrics": metrics, "consent": consent, "scrub": scrub, "acceptance": acceptance,
        "phasesClosed": closed_now, "loopBack": loop_back,
        "terminalLine": {"seq": terminal["line"].seq, "msg": terminal["line"].msg},
    }


def _phase_close_msg(key: str) -> str:
    """Render a ``phase_state`` key back into the ``close <PHASE> [k=v…]`` msg it closes.

    ``EXECUTION(wave=2)`` is the one parameterized identity; every other key IS the phase
    name.  Round-tripping through the seam's own grammar (rather than hand-building a
    string) is what keeps the close honest: an unrenderable key would raise at
    ``parse_phase_msg`` instead of writing a line that means something else.
    """
    match = re.fullmatch(r"EXECUTION\(wave=(\d+)\)", key)
    return f"EXECUTION wave={match.group(1)}" if match else key


# --------------------------------------------------------------------------- resilience feed


def close_resilience(kata_dir: str | Path, config: dict | None = None) -> dict:
    """The close's resilience fold — a fold over RECORDED fact, never over the config flag.

    ``full`` requires a push RECEIPT recorded on the cursor (§2.5, R-M4); the
    ``cursor.pushTrail`` preference is informational and can never raise the level.  The
    close reports it so the final report's resilience line is derived, not asserted.
    """
    return _trail.derive_resilience(
        _kd.read_trail_records(kata_dir),
        push_trail_configured=_trail.read_push_trail(config),
    )
