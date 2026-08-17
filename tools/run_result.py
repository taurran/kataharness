"""run_result.py — machine-readable gate RESULT emitter + evidence-identity gate.

Produces a JSON-serialisable dict (and optionally a file) that encodes
everything needed to trust a KataHarness gate run without re-executing it, and
answers the one question every evidence consumer must ask first: *is this
artifact evidence for THIS run, at THIS tree?*

The run-membership law (R-H2) — travels VERBATIM
------------------------------------------------
    gate evidence must carry the EXACT runId of the run being gated;
    ancestor/prior-run artifacts are legal as *inputs* but never as gate
    evidence; the sanctioned cross-run path is the parent consuming a child's
    recorded DOWN/VERDICT summary (which carries the child's runId) at
    fan-in/close. Each wave-loop's gate uses its own evidence; a re-loop pass
    re-emits its gates.

and its baseline corollary (R2-M6), also verbatim:

    The green-at-fork baseline RESULT is an input, never gate evidence:
    recorded in the consuming run's cursor as an input reference carrying its
    origin runId; the arm/re-loop's regression gate compares against it and
    emits ITS OWN result under its own runId.

The **input vs. gate-evidence distinction is part of this module's API**, not
prose a caller may re-derive: :func:`classify_evidence` returns the role, and
:func:`input_reference` mints the R2-M6 input record (never creditable).

Public surface
--------------
build_result(...)          -> dict          — pure; same inputs → same output (except utc).
                                               Carries ``runId`` and per-gate ``gates[]``.
write_result(...)          -> None          — writes result as indented JSON
run_gate(command)          -> (str, int)    — thin subprocess wrapper (optional)
parse_gate_blocks(output)  -> list[dict]    — per-gate parsed counts (BL-X13): one entry per
                                               pytest summary line, each tuple internally
                                               coherent. Kills the cross-gate chimera.
evidence_is_current(...)   -> (bool, str)   — pure identity gate: is RESULT.json's
                                               resultSha the SHA actually being
                                               credited, AND (when membership is
                                               asserted) its runId the live run's?
                                               FAIL-CLOSED (D136) on every
                                               absent/ambiguous input.
gate_evidence_is_creditable(...) -> (bool, str)
                                            — the STRICT entry point every gate/judge
                                               consumer uses: SHA fresh AND runId exact,
                                               both required, absence ⇒ refusal.
classify_evidence(...)     -> dict          — gate-evidence | input | unusable (R-H2).
input_reference(...)       -> dict          — the R2-M6 input record (origin runId carried,
                                               never creditable as gate evidence).
report_filename(...)       -> str           — `<runId>-<taskId>-<agent>-<kind>.md`
                                               (protocol/observability.md:18).
report_filename_is_current(...) -> (bool, str)
                                            — fail-closed run-membership check on a report
                                               filename.
resolve_head_sha(repo_root) -> str | None   — thin subprocess wrapper: resolves
                                               *repo_root*'s live HEAD via
                                               `git rev-parse HEAD`. Registered
                                               sink (protocol/exec-safety.md);
                                               this module is ALREADY a
                                               registered subprocess sink
                                               (run_gate) — new callers (e.g.
                                               benchmark.score_arms) call this
                                               function rather than growing a
                                               second spawn site of their own.
"""

from __future__ import annotations

import json
import re
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from fs_atomic import atomic_write_text

# ---------------------------------------------------------------------------
# The run-membership law — VERBATIM (DESIGN §2.4, R-H2 / R2-M6).
#
# Pinned as a constant so the law travels with the code that enforces it: a
# consumer that must restate it quotes THIS string rather than paraphrasing.
# tests/test_run_result.py asserts the verbatim text, so a dilution edit fails
# the suite instead of passing quietly.
# ---------------------------------------------------------------------------

RUN_MEMBERSHIP_LAW = (
    "gate evidence must carry the EXACT runId of the run being gated; "
    "ancestor/prior-run artifacts are legal as *inputs* but never as gate evidence; "
    "the sanctioned cross-run path is the parent consuming a child's recorded DOWN/VERDICT "
    "summary (which carries the child's runId) at fan-in/close. Each wave-loop's gate uses "
    "its own evidence; a re-loop pass re-emits its gates."
)

BASELINE_INPUT_LAW = (
    "The green-at-fork baseline RESULT is an input, never gate evidence: recorded in the "
    "consuming run's cursor as an input reference carrying its origin runId; the arm/re-loop's "
    "regression gate compares against it and emits ITS OWN result under its own runId."
)

# Artifact roles (R-H2). A closed set — never widen without amending the law above.
ROLE_GATE_EVIDENCE = "gate-evidence"
ROLE_INPUT = "input"
ROLE_UNUSABLE = "unusable"

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_PYTEST_COUNT_RE = re.compile(r"(\d+)\s+(passed|failed|skipped)")

# Minimum SHA prefix length treated as a meaningful identity — below this, a
# "match" would be coincidental (git's own short-SHA floor). Never treat a
# shorter prefix as a match.
_MIN_SHA_LEN = 7

# Bounded per Determinism Doctrine law 8 (gate subprocesses must not hang).
_GIT_TIMEOUT_S = 30

# Characters that would let a caller-supplied filename component escape the
# reports directory (CWE-23) or produce an unparseable name.
_UNSAFE_COMPONENT_RE = re.compile(r"[/\\\x00-\x1f]")

_COUNT_LABELS = ("passed", "failed", "skipped")


def _parse_pytest_counts(output: str) -> dict[str, int]:
    """Extract passed/failed/skipped counts from a pytest summary line.

    Returns a dict with keys 'passed', 'failed', 'skipped' (all int, default 0).
    Works on any line that contains patterns like '40 passed', '2 failed', etc.

    **Single-block use only.**  On multi-gate output this keeps last-match-per-label
    ACROSS blocks, which is exactly the BL-X13 cross-gate chimera (a 4-gate gauntlet
    yielding ``passed:2 / skipped:3`` — a tuple no single gate produced).  It is
    retained because ``gate_emit`` and existing tests bind to it for the
    single-block case; every multi-gate consumer must use
    :func:`parse_gate_blocks` (or ``build_result``'s ``gates[]``) instead.
    """
    counts: dict[str, int] = {"passed": 0, "failed": 0, "skipped": 0}
    for match in _PYTEST_COUNT_RE.finditer(output):
        n, label = int(match.group(1)), match.group(2)
        if label in counts:
            counts[label] = n
    return counts


def parse_gate_blocks(output: str) -> list[dict]:
    """Split *output* into per-gate count blocks — the BL-X13 fix.

    A pytest run emits its counts on ONE summary line ("40 passed, 2 failed in
    1.0s"), so one matching LINE is one gate block.  Each returned entry is
    therefore internally coherent: every count in it came from the same gate.

    Returns a list of dicts, in output order::

        {"index": 0, "summaryLine": "4493 passed, 3 skipped in 150.59s",
         "passed": 4493, "failed": 0, "skipped": 3}

    Empty list when no summary line is present (a non-pytest gate) — the caller
    must NOT read that as "zero failures"; ``build_result`` records it as
    ``countsScope: "no-counts"``.

    Pure: no I/O, no clock, no subprocess (Determinism Doctrine).
    """
    blocks: list[dict] = []
    for line in output.splitlines():
        matches = list(_PYTEST_COUNT_RE.finditer(line))
        if not matches:
            continue
        counts = {label: 0 for label in _COUNT_LABELS}
        for match in matches:
            label = match.group(2)
            if label in counts:
                counts[label] = int(match.group(1))
        blocks.append(
            {
                "index": len(blocks),
                "summaryLine": line.strip(),
                "passed": counts["passed"],
                "failed": counts["failed"],
                "skipped": counts["skipped"],
            }
        )
    return blocks


def _stdout_tail(output: str, max_chars: int = 2000) -> str:
    """Return the last *max_chars* characters of *output*."""
    return output[-max_chars:] if len(output) > max_chars else output


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_result(
    gate_name: str,
    command: str,
    output: str,
    exit_code: int,
    baseline_sha: str,
    result_sha: str,
    utc: str | None = None,
    run_id: str | None = None,
) -> dict:
    """Build a machine-checkable result dict for a single gate run.

    Parameters
    ----------
    gate_name:    Human-readable name of the gate (e.g. "smoke").
    command:      The shell command that was executed.
    output:       Combined stdout + stderr from the command.
    exit_code:    Process exit code (0 = success).
    baseline_sha: Git SHA of the baseline being tested against.
    result_sha:   Git SHA of the commit under test.
    utc:          ISO-8601 UTC timestamp string.  Pass *None* (default) to use
                  the current time; pass a fixed string in tests for determinism.
    run_id:       The seam-minted runId of the run that produced this gate
                  (DESIGN §2.4).  Stamped into the artifact so
                  :func:`evidence_is_current` can enforce the run-membership law
                  (R-H2) instead of trusting the file's location.  ``None``
                  (default) records the artifact as run-less, which
                  :func:`gate_evidence_is_creditable` REFUSES — a run-less
                  artifact is never gate evidence, only (at most) an input.

    Returns
    -------
    dict with keys: gateName, command, exitCode, passed, failed, skipped,
                    stdoutTail, baselineSha, resultSha, utc, runId,
                    gates, multiGate, countsScope.

    Counts honesty (BL-X13)
    -----------------------
    ``gates[]`` carries ONE entry per pytest summary line, each tuple coming
    from a single gate.  The top-level ``passed``/``failed``/``skipped`` scalars
    are then:

    * one block  → that block's counts (unchanged behaviour), ``countsScope: "single-gate"``
    * N > 1      → the per-label SUM over ``gates[]`` — a real total for the whole
                   command — with ``countsScope: "aggregate"`` and ``multiGate: true``
    * no blocks  → zeros with ``countsScope: "no-counts"`` (NOT "zero failures")

    What can no longer happen is the chimera: the old last-match-per-label scan
    reported one gate's ``passed`` beside another gate's ``skipped``, a tuple no
    single gate produced.  A consumer that needs a per-gate number reads
    ``gates[]``; the scalars are never a mix of two gates.
    """
    if utc is None:
        utc = datetime.now(tz=UTC).isoformat()

    gates = parse_gate_blocks(output)

    if not gates:
        counts = {label: 0 for label in _COUNT_LABELS}
        counts_scope = "no-counts"
    elif len(gates) == 1:
        counts = {label: gates[0][label] for label in _COUNT_LABELS}
        counts_scope = "single-gate"
    else:
        counts = {label: sum(block[label] for block in gates) for label in _COUNT_LABELS}
        counts_scope = "aggregate"

    return {
        "gateName": gate_name,
        "command": command,
        "exitCode": exit_code,
        "passed": counts["passed"],
        "failed": counts["failed"],
        "skipped": counts["skipped"],
        "stdoutTail": _stdout_tail(output),
        "baselineSha": baseline_sha,
        "resultSha": result_sha,
        "utc": utc,
        "runId": run_id,
        "gates": gates,
        "multiGate": len(gates) > 1,
        "countsScope": counts_scope,
    }


def _artifact_run_id(result_json: dict) -> str | None:
    """Return *result_json*'s ``runId`` as a non-empty string, else None.

    Fail-closed: a non-string, empty, or whitespace-only value reads as ABSENT,
    never as a wildcard.
    """
    raw = result_json.get("runId")
    if not isinstance(raw, str):
        return None
    raw = raw.strip()
    return raw or None


def _run_membership(result_json: dict, expected_run_id: str | None, require_run_id: bool) -> str:
    """Return "" when run membership holds, else the refusal reason.

    runIds are compared EXACTLY (the law says EXACT) — no case folding, no
    prefix tolerance.  Unlike a git SHA, a runId has no short form, so a prefix
    match would be pure invention.

    The runId GRAMMAR (``run-<utc-compact>-<hex>``, DESIGN §2.2) belongs to the
    seam that mints it; this module treats the token as opaque on purpose, so
    two modules cannot drift into disagreeing validators.  Emptiness is still
    refused here, because an empty identity is not an identity.
    """
    if not expected_run_id or not str(expected_run_id).strip():
        return "unknown-expected-run" if require_run_id else ""

    artifact_run_id = _artifact_run_id(result_json)
    if artifact_run_id is None:
        return "evidence-missing-run-id"

    if artifact_run_id != str(expected_run_id).strip():
        return "wrong-run"

    return ""


def evidence_is_current(
    result_json: dict | None,
    expected_sha: str | None,
    *,
    expected_run_id: str | None = None,
    require_run_id: bool = False,
) -> tuple[bool, str]:
    """Is *result_json*'s ``resultSha`` the SHA actually being credited?

    Gate evidence (RESULT.json) faithfully records the SHA it was produced
    against, but nothing previously checked that SHA against the tree being
    credited — a RESULT.json 56 commits stale was fully creditable as proof the
    *current* build passes. This closes that gap.

    Pure: no subprocess, no clock, no I/O (Determinism Doctrine). The caller is
    responsible for resolving *expected_sha* (e.g. ``git rev-parse HEAD`` of the
    tree under test) — this function only compares.

    FAIL-CLOSED throughout (D136 — no silent-permissive default): every absent
    or ambiguous input is a hard NO, never treated as "assume current".

    An ancestry check (``git merge-base --is-ancestor``) is deliberately NOT
    used here — it tests *validity* (was this SHA ever real), not *freshness*
    (is this SHA the one being credited RIGHT NOW). A 56-commits-stale SHA is a
    perfectly valid ancestor of HEAD and would pass an ancestry check while
    still being stale evidence.

    Run membership (R-H2, DESIGN §2.4)
    ----------------------------------
    Freshness alone was never enough: an artifact from a *different run* can sit
    at the very same SHA (a re-loop pass, a sibling arm, a docs-only follow-on),
    and the July-artifact-read-raw class is exactly that. When *expected_run_id*
    is supplied, the artifact's ``runId`` must match it EXACTLY, or the evidence
    is refused. The law travels verbatim in :data:`RUN_MEMBERSHIP_LAW`.

    **Backward compatibility — a DECLARED choice, not an accident.** Calling
    without *expected_run_id* (the pre-TM signature) keeps the SHA-only
    behaviour and the exact pre-existing reason codes. That default does NOT
    mean "membership passed"; it means **membership was NOT ASSERTED**, because
    the caller did not say which run is live. A SHA-only verdict is therefore
    NOT sufficient to credit gate evidence under R-H2. Every gate/judge consumer
    must call :func:`gate_evidence_is_creditable` (equivalently:
    ``expected_run_id=<live run>, require_run_id=True``). The two in-tree
    callers today — ``benchmark.score_arms`` and ``debug_report`` — are per-arm
    / per-report identity floors that do not yet carry a runId; they keep
    SHA-only semantics until their owning tasks route one, and nothing about
    their behaviour changes in this build.

    Args:
        result_json:  Parsed RESULT.json dict (``build_result``'s output), or
                       None if the artifact is absent/unreadable.
        expected_sha: The SHA of the tree actually being credited, resolved by
                       the caller. None/empty means the caller could not
                       establish what SHA is being credited.
        expected_run_id: The live run's runId. None/empty = membership not
                       asserted (see the BC note above) unless *require_run_id*.
        require_run_id: When True, the caller MUST supply *expected_run_id* —
                       failing to do so is itself a refusal
                       ("unknown-expected-run"), never a skipped check (D136).

    Returns:
        (True, "") when ``result_json["resultSha"]`` and *expected_sha* name the
        SAME commit — compared case-insensitively over the shorter of the two
        lengths (a 7-char short SHA matches its own 40-char long form), with
        both sides required to be at least 7 characters (git's own short-SHA
        floor; a shorter prefix is never treated as a match) — AND run
        membership holds. Otherwise (False, reason):
          - result_json is None                      -> "no-evidence"
          - resultSha missing/empty                   -> "evidence-missing-sha"
          - expected_sha None/empty                   -> "unknown-expected-sha"
          - either SHA shorter than 7 chars            -> "evidence-missing-sha"
          - SHAs differ                                -> "stale-evidence"
          - membership asserted, artifact has no runId -> "evidence-missing-run-id"
          - artifact's runId is another run's          -> "wrong-run"
          - require_run_id with no expected_run_id     -> "unknown-expected-run"
    """
    if result_json is None:
        return False, "no-evidence"

    result_sha = result_json.get("resultSha")
    if not result_sha:
        return False, "evidence-missing-sha"

    if not expected_sha:
        return False, "unknown-expected-sha"

    result_sha = str(result_sha)
    expected = str(expected_sha)

    if len(result_sha) < _MIN_SHA_LEN or len(expected) < _MIN_SHA_LEN:
        return False, "evidence-missing-sha"

    compare_len = min(len(result_sha), len(expected))
    if result_sha[:compare_len].lower() != expected[:compare_len].lower():
        return False, "stale-evidence"

    membership_reason = _run_membership(result_json, expected_run_id, require_run_id)
    if membership_reason:
        return False, membership_reason

    return True, ""


def gate_evidence_is_creditable(
    result_json: dict | None,
    expected_sha: str | None,
    expected_run_id: str | None,
) -> tuple[bool, str]:
    """The STRICT identity gate every evidence consumer routes through (TM-D5).

    Both legs are mandatory: **SHA fresh AND runId exact**. There is no
    membership-not-asserted mode here — that is the whole point of the function
    existing alongside :func:`evidence_is_current`. An absent artifact is a
    refusal ("no-evidence"), never a pass: **absence of evidence is not evidence
    of a green gate** (anti-vacuity, TM-D2 row B4).

    Consumers (DESIGN §3.4): kata-evaluate's machine-input step FIRST (the
    BL-X11 fix), then review / debrief / closeout / sprint-stop.

    Pure (no I/O, no clock, no subprocess). Returns ``(True, "")`` or
    ``(False, reason)`` using the reason vocabulary of
    :func:`evidence_is_current`.
    """
    return evidence_is_current(
        result_json,
        expected_sha,
        expected_run_id=expected_run_id,
        require_run_id=True,
    )


def classify_evidence(
    result_json: dict | None,
    expected_sha: str | None,
    expected_run_id: str | None,
) -> dict:
    """Sort an artifact into the R-H2 roles: gate-evidence | input | unusable.

    This is the input-vs-evidence distinction as an API — the close (§5) and any
    consumer that legitimately reads a prior run's artifact must be able to say
    *which* it is holding without re-deriving the law from prose.

    * ``gate-evidence`` — SHA fresh AND runId exact. Creditable.
    * ``input``        — a real artifact that is NOT creditable: a prior/ancestor
                         run's (``wrong-run``), a run-less one
                         (``evidence-missing-run-id``, origin unknown), or one at
                         another tree (``stale-evidence``). Legal to CONSUME as an
                         input, per the law; never to credit as this run's gate.
    * ``unusable``     — nothing to classify: no artifact at all, or the caller
                         could not establish the SHA/run being credited. Refusal,
                         never a pass.

    Returns a dict::

        {"role": ..., "creditableAsGateEvidence": bool, "reason": str,
         "originRunId": str | None, "originKnown": bool,
         "resultSha": str | None, "gateName": str | None,
         "law": RUN_MEMBERSHIP_LAW}

    ``reason`` is "" only for the creditable case.
    """
    ok, reason = gate_evidence_is_creditable(result_json, expected_sha, expected_run_id)

    if ok:
        role = ROLE_GATE_EVIDENCE
    elif reason in ("no-evidence", "unknown-expected-sha", "unknown-expected-run"):
        role = ROLE_UNUSABLE
    else:
        role = ROLE_INPUT

    origin_run_id = _artifact_run_id(result_json) if isinstance(result_json, dict) else None
    result_sha = result_json.get("resultSha") if isinstance(result_json, dict) else None
    gate_name = result_json.get("gateName") if isinstance(result_json, dict) else None

    return {
        "role": role,
        "creditableAsGateEvidence": role == ROLE_GATE_EVIDENCE,
        "reason": reason,
        "originRunId": origin_run_id,
        "originKnown": origin_run_id is not None,
        "resultSha": str(result_sha) if result_sha else None,
        "gateName": gate_name,
        "law": RUN_MEMBERSHIP_LAW,
    }


def input_reference(result_json: dict | None, *, kind: str = "green-at-fork") -> dict:
    """Mint the R2-M6 input record for a prior-run artifact.

    Verbatim (:data:`BASELINE_INPUT_LAW`): *"The green-at-fork baseline RESULT is
    an input, never gate evidence: recorded in the consuming run's cursor as an
    input reference carrying its origin runId; the arm/re-loop's regression gate
    compares against it and emits ITS OWN result under its own runId."*

    ``creditableAsGateEvidence`` is hard-wired ``False`` — this record is not a
    verdict and cannot become one; the consuming run still emits its own result
    under its own runId. An absent artifact yields a ``role: "unusable"`` record
    (absence is never silently promoted to an input either).

    Args:
        result_json: The prior/ancestor run's parsed RESULT.json, or None.
        kind:        Why it is being carried in ("green-at-fork" for the R2-M6
                     baseline; callers may name another input class).
    """
    usable = isinstance(result_json, dict)
    artifact: dict = result_json if usable else {}
    origin_run_id = _artifact_run_id(artifact) if usable else None
    result_sha = artifact.get("resultSha")

    return {
        "role": ROLE_INPUT if usable else ROLE_UNUSABLE,
        "kind": kind,
        "creditableAsGateEvidence": False,
        "originRunId": origin_run_id,
        "originKnown": origin_run_id is not None,
        "resultSha": str(result_sha) if result_sha else None,
        "gateName": artifact.get("gateName"),
        "exitCode": artifact.get("exitCode"),
        "utc": artifact.get("utc"),
        "law": BASELINE_INPUT_LAW,
    }


# ---------------------------------------------------------------------------
# Report filenames carry the runId — protocol/observability.md:18
# ---------------------------------------------------------------------------


def _guard_component(value: str, field: str) -> str:
    """Reject a filename component that could escape the reports directory.

    CWE-23 treatment (the ``_guard_path`` house pattern, DESIGN §3.5): no path
    separators, no NUL/control characters, no ``..``, no empties. Raises
    ``ValueError`` — a bad component is a caller bug, never a sanitised
    best-effort name.
    """
    text = str(value).strip()
    if not text:
        raise ValueError(f"{field} must be a non-empty string")
    if _UNSAFE_COMPONENT_RE.search(text):
        raise ValueError(f"{field} must not contain path separators or control characters: {value!r}")
    if ".." in text:
        raise ValueError(f"{field} must not contain '..': {value!r}")
    return text


def report_filename(run_id: str, task_id: str, agent: str, kind: str) -> str:
    """Build the report filename ``<runId>-<taskId>-<agent>-<kind>.md``.

    ``protocol/observability.md:18`` has always DOCUMENTED this shape; until the
    runId existed nothing could produce it, which is why that row was false.
    This constructor is what makes it true on the emitting side (the prose
    relabel itself belongs to the observability pass).

    The runId leads so a report's run membership is legible from the name alone
    and a directory listing sorts by run.
    """
    parts = [
        _guard_component(run_id, "run_id"),
        _guard_component(task_id, "task_id"),
        _guard_component(agent, "agent"),
        _guard_component(kind, "kind"),
    ]
    return "-".join(parts) + ".md"


def report_filename_is_current(name: str | None, expected_run_id: str | None) -> tuple[bool, str]:
    """Does report *name* belong to the run identified by *expected_run_id*?

    Fail-closed (D136), same posture as :func:`gate_evidence_is_creditable`:

      - name None/empty                       -> (False, "no-evidence")
      - expected_run_id None/empty            -> (False, "unknown-expected-run")
      - name carries no ``<runId>-`` prefix   -> (False, "evidence-missing-run-id")
      - prefix names another run              -> (False, "wrong-run")

    Membership is decided by an EXACT ``<expected_run_id>-`` prefix test rather
    than by splitting on ``-``: a runId contains hyphens itself
    (``run-<utc>-<hex>``), so field-splitting a filename is ambiguous while the
    prefix test never is.
    """
    if not name or not str(name).strip():
        return False, "no-evidence"
    if not expected_run_id or not str(expected_run_id).strip():
        return False, "unknown-expected-run"

    stem = Path(str(name).strip()).name
    prefix = str(expected_run_id).strip() + "-"

    if stem.startswith(prefix):
        return True, ""

    # A leading `run-…-` token that is not ours is a different run; anything
    # else never carried a run identity at all.
    if re.match(r"^run-[0-9A-Za-z]+-[0-9A-Za-z]+-", stem):
        return False, "wrong-run"
    return False, "evidence-missing-run-id"


def resolve_head_sha(repo_root: str | Path) -> str | None:
    """Resolve *repo_root*'s current HEAD SHA via ``git rev-parse HEAD``.

    Registered sink (protocol/exec-safety.md): fixed argv, ``shell=False``, no
    external input — *repo_root* is a harness-supplied path (e.g. an arm's own
    clone root from ``benchmark.score_arms``' ``arm_map``), never
    externally-controlled data reaching argv. Law-1 pins (Determinism Doctrine)
    inlined here the way ``contract_gate.py:150`` does — there is no shared
    pinned git helper in this repo.

    This module (``run_result.py``) is ALREADY a registered subprocess sink
    (``run_gate``) — callers needing a resolved SHA (e.g. the benchmark
    identity gate, D136) call this function rather than growing a second,
    unregistered spawn site of their own.

    Returns None on ANY resolution failure (not a git repo, git absent, a
    non-zero exit, an empty result, or a timeout). This function never raises;
    the typical caller passes the None straight through to
    :func:`evidence_is_current`, which fail-closes it as
    "unknown-expected-sha" — resolution failure is NEVER treated as "skip the
    check".
    """
    try:
        proc = subprocess.run(
            [
                "git",
                "-c", "log.follow=false",
                "-c", "log.showSignature=false",
                "-c", "core.quotepath=off",
                "rev-parse", "HEAD",
            ],
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=_GIT_TIMEOUT_S,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if proc.returncode != 0:
        return None
    sha = proc.stdout.strip()
    return sha or None


def write_result(result: dict, path: str | Path) -> None:
    """Write *result* as indented JSON to *path*.

    Atomic (D159, same-dir tmp + ``os.replace``): ``RESULT.json`` is read
    concurrently by the evaluator and the benchmark scorer while a gate is still
    emitting, and a truncate-then-write leaves a window where a reader sees a
    partial file.  Output bytes are unchanged.

    Parameters
    ----------
    result: dict as returned by :func:`build_result`.
    path:   Destination file path (str or :class:`~pathlib.Path`).
            Parent directory must already exist.
    """
    atomic_write_text(Path(path), json.dumps(result, indent=2), encoding="utf-8")


def run_gate(command: str, *, timeout: float = 600.0) -> tuple[str, int]:
    """Run *command* in a subprocess and return (combined_output, exit_code).

    stdout and stderr are merged into a single string (same order as terminal).
    This is a thin convenience wrapper; the core logic lives in :func:`build_result`.

    A hung gate command is bounded by *timeout* (seconds, default 600).  On
    ``subprocess.TimeoutExpired`` this returns a FAILURE-shaped result — any
    partial output plus a ``[kata] gate runner timeout`` note, with exit code
    124 (the conventional timeout code; nonzero → gate red).  It never hangs
    and never raises through as success (D136: no silent-permissive default).
    """
    try:
        proc = subprocess.run(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=timeout,
        )
    except subprocess.TimeoutExpired as exc:
        partial = exc.stdout or ""
        if isinstance(partial, bytes):  # TimeoutExpired may carry bytes even with text=True
            partial = partial.decode("utf-8", errors="replace")
        return partial + f"\n[kata] gate runner timeout after {timeout}s\n", 124
    return proc.stdout, proc.returncode
