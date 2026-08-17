"""tripwire_check.py — the judge-stack tripwire runner (trust-model TM-D3 · R-M6).

Detectors ATTEST and NARROW; judges judge.

Standing humility, stated wherever v1 is described (burn-02 meta-finding, verbatim):
*"the judgment+human layers found all of these; the automated mechanical gates found
none."*  Nothing in this module judges anything.  It answers one narrow, mechanical
question per judge — *does this judge have a known-bad corpus whose expectations are
shape-conformant with its own pinned verdict contract, and does at least one of those
expectations demand a FAILING verdict?* — and refuses out loud when it cannot answer it.

What this is
------------
[[kata-validate]] already proves per invocation that it can still fail: it runs its
critics over a known-bad corpus (``validation_report.tripwire_corpus``) and refuses to
report ``passed: true`` if nothing fired (``validation_report.assert_tripwire_flagged``).
DESIGN §3.1 generalizes that precedent to the whole judge stack (TM-D3 + R-M6):

    every judge proves it can still fail against a known-bad corpus before its verdict
    is credited.  Corpora activate PER JUDGE as they land: a judge without a corpus is
    declared **Honor-system**, never blocked (deny-everything dissolved); a judge that
    cannot demonstrate failure-capability is **Dormant, not Verified**.  Home = per-judge
    fixtures on the kata-validate precedent; proof cadence = per-build (CI) with the
    corpus hash on the cursor.

This module is that runner.  ``check_all`` derives each judge's activation state from
recorded corpus fact; ``corpus_hash`` fingerprints what was checked; ``record_corpus_hash``
writes that fingerprint onto the cursor as a NOTE line, so the activation claim is a fold
over a recorded fact rather than an assertion.

What this is NOT — the boundary, stated
---------------------------------------
**This runner never invokes a judge.**  It checks the corpus against the judge's
contract *shape* — the CLOSED per-judge enum and the pinned ``VERDICT: <enum>`` first
line, parsed by the ONE parser ``kata_dispatch.parse_verdict``.  It therefore proves
that a corpus exists, is well-formed, is filed under the right judge, and *demands a
failing verdict that the judge's own enum admits and the ONE parser accepts*.

It does **not** prove that an LLM judge, handed the fixture, actually returns that
verdict — that is an agent run, not a mechanical check, and claiming otherwise would be
the exact over-claim this program exists to kill.  The honest statement of what a
``verified`` activation means is therefore: *this judge's failure-capability corpus is
present and mechanically conformant*, not *this judge was observed failing*.

Corpus schemas — two, because the precedent is REFERENCED, not moved
--------------------------------------------------------------------
``judge-fixture`` (the six W5 judge contracts).  One JSON object per file under
``skills/evaluate/<judge>/fixtures/``, with EXACTLY these fields:

    id                one stable fixture id
    judge             the judge slug — must equal the owning directory's judge
    wrongness         one member of WRONGNESS_CLASSES (closed enum)
    expected_verdict  the verdict a competent judge MUST return — must be in that
                      judge's closed enum AND in its failing subset
    why               one paragraph: why a competent judge must fail this artifact
    artifact          non-empty list of lines — the known-bad artifact itself

Unknown keys are REFUSED rather than ignored: a typo'd field is the silent-permissive
class, and a fixture that quietly drops its ``expected_verdict`` would weaken the corpus
without anyone seeing it.

``validation-finding`` ([[kata-validate]], whose corpus is REFERENCED where it already
lives — ``tools/tests/fixtures/validation_tripwire/``, unmoved).  Those files are
``validation_report`` Finding dicts, so the expected verdict is DERIVED with that
module's own predicate (``severity_of(f) == "error" or bool(f.get("hold"))`` ⇒ the run is
not clean ⇒ the seam-dispatched envelope opens ``VERDICT: FAIL``) and then shape-checked
through the same one parser as everything else.  The derivation reuses
``validation_report.severity_of`` — the live function, not a copy — and
``tests/test_tripwire_check.py`` pins the agreement between this derivation and
``validation_report.assert_tripwire_flagged`` on the live corpus.

The anti-vacuity companion (TM-D3), applied to this runner itself
-----------------------------------------------------------------
A tripwire that certifies over nothing is precisely the leniency failure a tripwire
exists to catch, so this module refuses rather than shrugs:

=========================================  ====================================
Situation                                  Outcome
=========================================  ====================================
``skills/evaluate/`` absent/not a dir      ``TripwireRefusal`` — a scan over zero
                                           judges certifies nothing
``JUDGES`` empty                           ``TripwireRefusal`` — an unconfigured
                                           registry cannot certify a stack
corpus dir absent, or holds zero
``*.json``                                 ``honor-system`` — a RECORDED absence,
                                           never blocked (R-M6)
corpus present but a file is unreadable
/ unparseable / schema-invalid             ``dormant`` — a parse failure is a
                                           refusal, never a skip
corpus present, well-formed, but NO
fixture expects a failing verdict          ``dormant`` — it cannot demonstrate
                                           failure-capability
corpus present and at least one failing
expectation, all shape-conformant          ``verified``
=========================================  ====================================

Honest limits (v1) — stated, not implied away
---------------------------------------------
1. **No judge is invoked.**  ``verified`` means *corpus present and mechanically
   conformant*, never *observed failing*.  Pinned by
   ``test_verified_state_does_not_claim_the_judge_was_run``.
2. **The contract pin is a token-presence check, and token presence is forgeable**
   (KH-T02, the same lesson that forced the protocol fingerprints).
   ``verify_contract_pins`` asserts each declared enum token appears in that judge's
   ``SKILL.md`` in token form (backticked or double-quoted) and that the file names
   ``parse_verdict``.  It does **not** re-derive the enum from the SKILL.md, so a
   SKILL.md that keeps its tokens while inverting their meanings still passes.  The miss
   is DEMONSTRATED by ``test_contract_pin_is_token_presence_only_stated_miss``, not just
   prosed.
3. **BOTH registries are hand-maintained.**  A seventh judge landing under
   ``skills/evaluate/`` is not auto-discovered; it is invisible to this runner until it
   joins ``JUDGES``.  ``test_every_evaluate_skill_is_registered_or_named_non_judge``
   turns that into a loud failure instead of a silent gap — the protocol-folder lesson
   (nothing enumerated the directory, so new members were invisible) applied here.  But
   that mitigation has the same shape as the gap it closes: ``NON_JUDGE_EVALUATE_SKILLS``
   is hand-maintained too, and filing a REAL judge into it silences the completeness
   check by design.  Nothing mechanical distinguishes "reports, never gates" from "a
   judge nobody wanted to write a corpus for" — that call is human, and the set is where
   it is recorded.
4. **The corpus hash covers file content, not fixture meaning.**  Reordering fields
   inside a fixture changes the hash; the hash is a change-detector, not a semantic
   identity.  Line endings are normalised first (see :func:`corpus_hash`), which is a
   defensive guard, not a fix for an observed divergence — this repo's checkouts are LF
   on every platform today.
5. **NO GATE CONSUMES the activation state.**  This runner reports; nothing yet refuses
   on what it reports.  The declared consumer is the ``gate_preconditions`` work (frozen
   PLAN, W7: "per-judge tripwire preconditions activate per R-M6"), which **does not
   exist at this tip**.  :func:`main`'s exit ``1`` on a Dormant judge is a REPORT code,
   not an enforced gate: CI never invokes this CLI — only ``tests/test_tripwire_check.py``
   rides the gauntlet — so a Dormant judge fails the test suite through the tests'
   assertions, and nothing anywhere blocks a verdict on tripwire status.
6. **``record_corpus_hash`` has NO production caller.**  It is exercised by
   ``tests/test_tripwire_check.py`` and reachable by hand through the ``--record`` CLI
   flag; no seam act, conductor act, or gate calls it during a run.  Built and
   exercised, not wired — the same honest label the cursor cadence carried before its
   caller landed, and a W7 wiring candidate.
7. **The corpora test whether a judge HONORS contradicting evidence, not whether it
   FINDS it.**  Every fixture embeds its own refuting ground truth beside the claim —
   the stub body under the "fully wired" report, the empty record set under the
   "double-pass ran", the fact table under the "comprehensive coverage".  So the corpus
   exercises *"the disproof was placed in front of the judge and the judge still had to
   fail it"*, which is deliberately the easier half.  A judge that would rubber-stamp a
   claim it had to go dig against is NOT caught here; that requires handing a judge a
   real repository and a real diff, which is v2 territory (an LLM run, per limit 1).

Security posture
----------------
PURE — no subprocess, no eval, no exec, no shell, no network.  Reads JSON and text via
``json.loads`` / ``Path.read_text``.  Operator-supplied roots pass ``_guard_path``
(``..`` rejection, CWE-23) before any filesystem sink; corpus paths are joined from
registry constants, never from fixture content.  The one write path is the cursor
append, which goes through ``kata_board.append_event`` and inherits its grammar guards.
Assertable by source scan (``test_tripwire_check.py::TestExecSafety``).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import kata_board
from graph_gen import _bytes_hash, _repo_hash
from kata_dispatch import parse_verdict
from validation_report import severity_of

# ---------------------------------------------------------------------------
# Activation states (R-M6) — a DERIVED, recorded fact, never a config assertion
# ---------------------------------------------------------------------------

#: Corpus present, well-formed, and demanding at least one failing verdict.
ACTIVATION_VERIFIED = "verified"
#: Corpus present but unable to demonstrate failure-capability — Dormant, not Verified.
ACTIVATION_DORMANT = "dormant"
#: No corpus.  Declared, recorded, and NEVER blocked (deny-everything dissolved).
ACTIVATION_HONOR_SYSTEM = "honor-system"

#: The closed activation enumeration.
ACTIVATION_STATES: frozenset[str] = frozenset(
    {ACTIVATION_VERIFIED, ACTIVATION_DORMANT, ACTIVATION_HONOR_SYSTEM}
)

# ---------------------------------------------------------------------------
# Corpus schemas
# ---------------------------------------------------------------------------

#: One JSON object per file, this module's schema (the six W5 judges).
CORPUS_JUDGE_FIXTURE = "judge-fixture"
#: validation_report Finding dicts — kata-validate's precedent corpus, REFERENCED in place.
CORPUS_VALIDATION_FINDING = "validation-finding"

#: Exactly the fields a ``judge-fixture`` file carries.  Unknown keys are refused.
FIXTURE_FIELDS: frozenset[str] = frozenset(
    {"id", "judge", "wrongness", "expected_verdict", "why", "artifact"}
)

#: Closed enumeration of judge-shaped wrongness.  A corpus cannot invent a class:
#: an open vocabulary is how a corpus drifts into "known-bad" artifacts nobody can
#: say is bad.
WRONGNESS_CLASSES: frozenset[str] = frozenset(
    {
        "stub-reported-as-complete",
        "fabricated-citation",
        "vacuous-pass",
        "unverified-reuse-claim",
        "contradicted-by-evidence",
        "scope-drift",
        "inflated-claim",
        "unexamined-threat-surface",
    }
)

# ---------------------------------------------------------------------------
# The judge registry — per-judge CLOSED enums, transcribed from the W5 contracts
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class JudgeContract:
    """One judge's tripwire contract.

    ``enum`` is that judge's COMPLETE verdict space as pinned in its ``SKILL.md``;
    ``failing`` is the subset a known-bad artifact must provoke.  The split is the
    whole point: a corpus whose expectations all sit in the passing subset proves
    nothing about failure-capability.
    """

    slug: str
    skill: str
    corpus_dir: str
    enum: tuple[str, ...]
    failing: frozenset[str]
    corpus_kind: str

    @property
    def passing(self) -> frozenset[str]:
        """The verdicts that are NOT a failure for this judge."""
        return frozenset(self.enum) - self.failing


def _judge(slug: str, enum: tuple[str, ...], failing: tuple[str, ...]) -> JudgeContract:
    """Build a standard ``judge-fixture`` contract homed under the judge's skill dir."""
    return JudgeContract(
        slug=slug,
        skill=f"skills/evaluate/{slug}/SKILL.md",
        corpus_dir=f"skills/evaluate/{slug}/fixtures",
        enum=enum,
        failing=frozenset(failing),
        corpus_kind=CORPUS_JUDGE_FIXTURE,
    )


#: Every landed judge, with its CLOSED verdict enum.  Sources, verified at build:
#: kata-evaluate ``PASS|NEEDS_WORK`` · the three review tiers ``SHIP|HOLD`` ·
#: kata-slop-check ``SLOP-DETECTED|CLEAN`` · kata-inline-eval
#: ``continue|correct|reroll`` · kata-validate ``PASS|FAIL``.
#:
#: kata-inline-eval's failing subset is ``correct`` AND ``reroll``: ``continue`` is
#: the explicit false-alarm verdict, so it is the one member a known-bad chunk must
#: NOT provoke.
JUDGES: tuple[JudgeContract, ...] = (
    _judge("kata-evaluate", ("PASS", "NEEDS_WORK"), ("NEEDS_WORK",)),
    _judge("kata-review-standard", ("SHIP", "HOLD"), ("HOLD",)),
    _judge("kata-review-essential", ("SHIP", "HOLD"), ("HOLD",)),
    _judge("kata-review-advanced", ("SHIP", "HOLD"), ("HOLD",)),
    _judge("kata-slop-check", ("SLOP-DETECTED", "CLEAN"), ("SLOP-DETECTED",)),
    _judge("kata-inline-eval", ("continue", "correct", "reroll"), ("correct", "reroll")),
    JudgeContract(
        slug="kata-validate",
        skill="skills/evaluate/kata-validate/SKILL.md",
        # REFERENCED where it already lives, per the frozen ownership grant — the
        # precedent corpus is not moved into a fixtures/ dir by this task.
        corpus_dir="tools/tests/fixtures/validation_tripwire",
        enum=("PASS", "FAIL"),
        failing=frozenset({"FAIL"}),
        corpus_kind=CORPUS_VALIDATION_FINDING,
    ),
)

#: Skill dirs under ``skills/evaluate/`` that are deliberately NOT judges — they
#: report, they never return a gating VERDICT.  Enumerated so the completeness check
#: can tell "not a judge" from "a judge nobody registered".
NON_JUDGE_EVALUATE_SKILLS: frozenset[str] = frozenset(
    {"kata-report", "kata-benchmark-report", "kata-debrief", "kata-review"}
)

#: Record kind for the cursor NOTE (mirrors kata_trail's RECORD_KIND_* convention).
RECORD_KIND_TRIPWIRE = "tripwire-corpus"

#: Default cursor identity for the recorded fact.
RECORD_AGENT = "tripwire-check"
RECORD_TASK = "judge-tripwire-corpora"

_CTRL_RE = re.compile(r"[\x00-\x1f\x7f-\x9f]")

#: Token form of an enum member inside a contract file: backticked (`PASS`) or
#: double-quoted (the ``allowed={"PASS","FAIL"}`` binding).  Prose mention alone
#: does not satisfy the pin.
def _token_forms(token: str) -> tuple[str, ...]:
    """The literal spellings that count as a pinned token in a SKILL.md."""
    return (f"`{token}`", f'"{token}"')


class TripwireRefusal(Exception):
    """The runner refused to certify — a vacuous input, never a silent pass."""


# ---------------------------------------------------------------------------
# Path-traversal guard (CWE-23) — family member, mirrors truth_serum._guard_path
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


#: The repo this module ships inside — ``tools/``'s parent.  Module-relative, the way
#: ``validation_report._TRIPWIRE_DIR`` is, so the runner finds its corpora regardless of
#: the caller's cwd.  ``..`` is not a usable default: ``_guard_path`` rejects it by the
#: family invariant, and weakening that guard to buy a convenient relative path would
#: trade a CWE-23 defence for typing three characters.
REPO_ROOT: Path = Path(__file__).resolve().parents[1]


def _guard_root(raw: str | Path | None) -> Path:
    """Guard and resolve a repo root; ``None`` means this module's own repo."""
    if raw is None:
        return REPO_ROOT
    return Path(_guard_path(raw)).resolve()


def _scrub(text: str) -> str:
    """Strip control/ANSI-range characters and neutralise the cursor separator.

    DESIGN §6.3 rendering law, mirrored from ``kata_trail._scrub``: cursor-derived
    text can never repaint a terminal or forge an extra ``" | "`` field.
    """
    return _CTRL_RE.sub("", str(text)).replace("|", "/")


# ---------------------------------------------------------------------------
# Shape conformance — the corpus expectation against the judge's pinned contract
# ---------------------------------------------------------------------------


def render_verdict_line(verdict: str) -> str:
    """Render the pinned machine-parseable first line for a verdict token."""
    return f"VERDICT: {verdict}"


def check_shape(contract: JudgeContract, verdict: str) -> str | None:
    """Return an error string when ``verdict`` does not conform to ``contract``.

    Three mechanical questions, in order, all answered by the judge's OWN contract:

    1. does ``VERDICT: <verdict>`` survive the ONE parser
       (``kata_dispatch.parse_verdict``, strict ``fullmatch`` on line 1)?
    2. bound to this judge's CLOSED enum, does the parser still accept it?
    3. is it in the FAILING subset — i.e. does the corpus actually demand a failure?

    ``None`` means conformant.  There is no third state: a shape that cannot be
    parsed is an error, never a skip.
    """
    line = render_verdict_line(verdict)
    if parse_verdict(line) != verdict:
        return f"verdict {verdict!r} does not parse as a pinned VERDICT first line"
    if parse_verdict(line, allowed=frozenset(contract.enum)) != verdict:
        return (
            f"verdict {verdict!r} is outside {contract.slug}'s closed enum "
            f"{list(contract.enum)}"
        )
    if verdict not in contract.failing:
        return (
            f"verdict {verdict!r} is a PASSING verdict for {contract.slug} "
            f"(failing subset: {sorted(contract.failing)}) — a known-bad fixture "
            "must demand a failure"
        )
    return None


# ---------------------------------------------------------------------------
# Corpus loading — a parse failure is a REFUSAL, never a skip
# ---------------------------------------------------------------------------


def corpus_files(contract: JudgeContract, repo_root: str | Path | None = None) -> list[Path]:
    """Every ``*.json`` file in this judge's corpus dir, sorted by name.

    Sorted, non-recursive, and extension-bound so the file set (and therefore the
    corpus hash) is deterministic across platforms and filesystems.
    """
    root = _guard_root(repo_root)
    directory = root / _guard_path(contract.corpus_dir)
    if not directory.is_dir():
        return []
    return sorted(directory.glob("*.json"))


def _load_judge_fixture(path: Path, contract: JudgeContract) -> tuple[dict | None, str | None]:
    """Load and validate one ``judge-fixture`` file: ``(fixture, error)``."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"{path.name}: unreadable ({exc.__class__.__name__})"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"{path.name}: not valid JSON ({exc.msg} at line {exc.lineno})"
    if not isinstance(data, dict):
        return None, f"{path.name}: expected a JSON object, got {type(data).__name__}"

    keys = set(data)
    missing = sorted(FIXTURE_FIELDS - keys)
    unknown = sorted(keys - FIXTURE_FIELDS)
    if missing:
        return None, f"{path.name}: missing required field(s) {missing}"
    if unknown:
        return None, f"{path.name}: unknown field(s) {unknown} (schema is closed)"

    for field_name in ("id", "judge", "wrongness", "expected_verdict", "why"):
        value = data[field_name]
        if not isinstance(value, str) or not value.strip():
            return None, f"{path.name}: {field_name} must be a non-empty string"

    artifact = data["artifact"]
    if not isinstance(artifact, list) or not artifact:
        return None, f"{path.name}: artifact must be a non-empty list of lines"
    if not all(isinstance(line, str) for line in artifact):
        return None, f"{path.name}: artifact lines must all be strings"

    if data["judge"] != contract.slug:
        return None, (
            f"{path.name}: judge field {data['judge']!r} does not match the owning "
            f"corpus dir ({contract.slug}) — fixture filed under the wrong judge"
        )
    if data["wrongness"] not in WRONGNESS_CLASSES:
        return None, (
            f"{path.name}: wrongness {data['wrongness']!r} is outside the closed "
            f"class set {sorted(WRONGNESS_CLASSES)}"
        )

    shape_error = check_shape(contract, data["expected_verdict"])
    if shape_error:
        return None, f"{path.name}: {shape_error}"
    return data, None


def _load_validation_findings(
    path: Path, contract: JudgeContract
) -> tuple[list[dict] | None, str | None]:
    """Load one ``validation-finding`` file: ``(findings, error)``.

    Accepts a single Finding dict or a list of them — the shape
    ``validation_report.tripwire_corpus`` reads.  Unlike that loader, a malformed
    file here is an ERROR rather than a silently-skipped file: this runner's job is
    to notice a corpus that stopped working.
    """
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, f"{path.name}: unreadable ({exc.__class__.__name__})"
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"{path.name}: not valid JSON ({exc.msg} at line {exc.lineno})"
    findings = data if isinstance(data, list) else [data]
    if not findings or not all(isinstance(f, dict) for f in findings):
        return None, f"{path.name}: expected a Finding object or a list of them"
    return findings, None


def derive_finding_verdict(finding: dict, contract: JudgeContract) -> str:
    """Derive the verdict a Finding implies for a ``validation-finding`` judge.

    Reuses ``validation_report.severity_of`` — the live predicate, not a copy — under
    the same rule ``assert_tripwire_flagged`` applies: an error-severity finding or a
    ``hold`` means the run is not clean, and kata-validate's seam-dispatched envelope
    opens ``VERDICT: FAIL`` exactly when ``compute_passed`` would have returned False.
    """
    if len(contract.failing) != 1 or len(contract.passing) != 1:
        raise TripwireRefusal(
            f"tripwire_check: {contract.slug}'s verdict space is not the binary "
            "pass/fail shape this derivation is defined for — refusing to guess "
            f"(failing={sorted(contract.failing)}, passing={sorted(contract.passing)})"
        )
    failing = severity_of(finding) == "error" or bool(finding.get("hold"))
    return next(iter(contract.failing)) if failing else next(iter(contract.passing))


# ---------------------------------------------------------------------------
# Corpus hash — the recorded fingerprint of what was checked
# ---------------------------------------------------------------------------


def corpus_hash(paths: list[Path], *, repo_root: str | Path | None = None) -> str:
    """Stable sha256 over the corpus files' repo-relative paths and contents.

    Deterministic by construction (Determinism Doctrine): POSIX-normalised relative
    paths, sorted by ``_repo_hash``, no clock and no host path in the digest.  Reuses
    ``graph_gen._bytes_hash`` / ``_repo_hash`` — the same pair ``truth_serum`` reuses
    for its staleness check.

    **Line endings are normalised before hashing — DEFENSIVELY, against a divergence
    this repo does not currently have.**  Stated precisely, because the first version
    of this docstring claimed an observed divergence that does not exist here:
    ``.gitattributes`` carries ``* text=auto eol=lf`` AND ``*.json text eol=lf``, so
    checkouts land LF on every platform (verified against a Windows working tree under
    ``core.autocrlf=true``), and a raw-bytes digest would agree across the gauntlet legs
    today.  The normalisation is kept anyway because the *fingerprint* must not depend
    on a checkout attribute that lives outside this module: drop or narrow that
    ``.gitattributes`` rule and a raw-bytes hash would start reporting a corpus change
    on a corpus nobody touched.  A fingerprint that moves when nothing moved is a false
    tamper signal, and a check that cries wolf trains people to ignore it — so this
    guards the property directly rather than inheriting it.
    """
    root = _guard_root(repo_root)
    file_hashes: dict[str, str] = {}
    for path in paths:
        try:
            rel = path.resolve().relative_to(root).as_posix()
        except ValueError:
            rel = path.name
        data = path.read_bytes().replace(b"\r\n", b"\n")
        file_hashes[rel] = _bytes_hash(data)
    return _repo_hash(file_hashes)


# ---------------------------------------------------------------------------
# Per-judge check + the derived activation state
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class JudgeResult:
    """The derived, recordable fact about one judge's tripwire."""

    slug: str
    activation: str
    corpus_dir: str
    corpus_kind: str
    files: tuple[str, ...]
    fixtures: int
    failable: int
    corpus_hash: str | None
    reasons: tuple[str, ...]

    def as_dict(self) -> dict:
        """JSON-ready mapping — the shape the CLI and the cursor record consume."""
        return {
            "judge": self.slug,
            "activation": self.activation,
            "corpusDir": self.corpus_dir,
            "corpusKind": self.corpus_kind,
            "files": list(self.files),
            "fixtures": self.fixtures,
            "failable": self.failable,
            "corpusHash": self.corpus_hash,
            "reasons": list(self.reasons),
        }


def check_judge(contract: JudgeContract, repo_root: str | Path | None = None) -> JudgeResult:
    """Derive one judge's activation state from its corpus on disk.

    Never raises on a bad corpus — a bad corpus is a ``dormant`` RESULT, which is the
    reportable fact.  The refusals in this module are reserved for vacuous INPUT
    (``check_all``'s zero-judge / absent-tree cases), where there is nothing to report
    a fact about.
    """
    paths = corpus_files(contract, repo_root)
    if not paths:
        return JudgeResult(
            slug=contract.slug,
            activation=ACTIVATION_HONOR_SYSTEM,
            corpus_dir=contract.corpus_dir,
            corpus_kind=contract.corpus_kind,
            files=(),
            fixtures=0,
            failable=0,
            corpus_hash=None,
            reasons=(
                "no corpus — declared Honor-system per R-M6 (a judge without a corpus "
                "is never blocked)",
            ),
        )

    names = tuple(p.name for p in paths)
    reasons: list[str] = []
    fixtures = 0
    failable = 0

    for path in paths:
        if contract.corpus_kind == CORPUS_JUDGE_FIXTURE:
            _fixture, error = _load_judge_fixture(path, contract)
            if error:
                reasons.append(error)
                continue
            fixtures += 1
            # _load_judge_fixture already ran check_shape, which refuses any verdict
            # outside the failing subset — so a loaded fixture is a failable one.
            failable += 1
        else:
            findings, error = _load_validation_findings(path, contract)
            if error:
                reasons.append(error)
                continue
            for finding in findings:
                fixtures += 1
                verdict = derive_finding_verdict(finding, contract)
                if verdict not in contract.failing:
                    continue
                shape_error = check_shape(contract, verdict)
                if shape_error:
                    reasons.append(f"{path.name}: {shape_error}")
                    continue
                failable += 1

    try:
        digest: str | None = corpus_hash(paths, repo_root=repo_root)
    except OSError as exc:
        digest = None
        reasons.append(f"corpus hash unavailable: {exc.__class__.__name__}")

    if reasons:
        activation = ACTIVATION_DORMANT
    elif failable == 0:
        activation = ACTIVATION_DORMANT
        reasons.append(
            f"corpus present ({fixtures} entr{'y' if fixtures == 1 else 'ies'}) but no "
            "entry demands a failing verdict — this judge cannot demonstrate "
            "failure-capability: Dormant, not Verified"
        )
    else:
        activation = ACTIVATION_VERIFIED
        reasons.append(
            f"{failable} of {fixtures} corpus entries demand a failing verdict "
            f"({sorted(contract.failing)}), all shape-conformant with the judge's "
            "closed enum under kata_dispatch.parse_verdict"
        )

    return JudgeResult(
        slug=contract.slug,
        activation=activation,
        corpus_dir=contract.corpus_dir,
        corpus_kind=contract.corpus_kind,
        files=names,
        fixtures=fixtures,
        failable=failable,
        corpus_hash=digest,
        reasons=tuple(reasons),
    )


def check_all(repo_root: str | Path | None = None) -> dict:
    """Check every registered judge and summarise the stack.

    Raises:
        TripwireRefusal: the registry is empty, or ``skills/evaluate/`` is absent —
            a scan over zero judges certifies nothing (the TM-D3 anti-vacuity law
            applied to this runner itself).
    """
    if not JUDGES:
        raise TripwireRefusal(
            "tripwire_check: the judge registry is empty — an unconfigured runner "
            "cannot certify a judge stack (anti-vacuity, TM-D3)"
        )
    root = _guard_root(repo_root)
    evaluate_dir = root / "skills" / "evaluate"
    if not evaluate_dir.is_dir():
        raise TripwireRefusal(
            f"tripwire_check: {evaluate_dir.as_posix()} is absent or not a directory — "
            "refusing to certify a judge stack that could not be read (anti-vacuity, "
            "TM-D3)"
        )

    results = [check_judge(contract, root) for contract in JUDGES]
    per_judge = {r.slug: (r.corpus_hash or "") for r in results}
    return {
        "corpusHash": _repo_hash(per_judge),
        "judges": [r.as_dict() for r in results],
        "verified": sum(1 for r in results if r.activation == ACTIVATION_VERIFIED),
        "dormant": sum(1 for r in results if r.activation == ACTIVATION_DORMANT),
        "honorSystem": sum(1 for r in results if r.activation == ACTIVATION_HONOR_SYSTEM),
        "dormantJudges": [r.slug for r in results if r.activation == ACTIVATION_DORMANT],
    }


# ---------------------------------------------------------------------------
# Contract pins — the registry's enums against the judges' own SKILL.md files
# ---------------------------------------------------------------------------


def verify_contract_pins(repo_root: str | Path | None = None) -> list[str]:
    """Return a list of pin violations; empty means every enum token is pinned.

    Guards the drift this registry is exposed to: the enums here are TRANSCRIBED from
    the W5 judge contracts, so a contract that changes its verdict space while this
    table does not is a silent divergence — the corpus would then be checked against
    an enum no judge honours.

    Per the module's stated limit 2 this is token presence, not semantic equivalence:
    each declared token must appear in the judge's ``SKILL.md`` in token form
    (backticked, or double-quoted as in an ``allowed={...}`` binding), and the file
    must name ``parse_verdict`` (the ONE parser the pin is worth anything under).
    """
    root = _guard_root(repo_root)
    violations: list[str] = []
    for contract in JUDGES:
        skill = root / _guard_path(contract.skill)
        if not skill.is_file():
            violations.append(f"{contract.slug}: contract file {contract.skill} is absent")
            continue
        text = skill.read_text(encoding="utf-8")
        if "parse_verdict" not in text:
            violations.append(
                f"{contract.slug}: {contract.skill} does not name parse_verdict — the "
                "pinned first line is not bound to the ONE parser"
            )
        for token in contract.enum:
            if not any(form in text for form in _token_forms(token)):
                violations.append(
                    f"{contract.slug}: enum token {token!r} is not pinned in "
                    f"{contract.skill} (expected `{token}` or \"{token}\")"
                )
    return violations


# ---------------------------------------------------------------------------
# The recorded fact — corpus hash on the cursor
# ---------------------------------------------------------------------------


def corpus_record(summary: dict, *, run_id: str) -> dict:
    """Build the cursor-appendable RECORD for a tripwire run (the R-M4 shape).

    Mirrors ``kata_trail.snapshot_record``: the outcome stops being a value that
    lived only in a process and becomes a fact a later fold can read, so "this
    judge is verified" is derivable from the cursor rather than asserted in prose.
    """
    return {
        "kind": RECORD_KIND_TRIPWIRE,
        "runId": run_id,
        "corpusHash": summary["corpusHash"],
        "verified": summary["verified"],
        "dormant": summary["dormant"],
        "honorSystem": summary["honorSystem"],
        "dormantJudges": list(summary["dormantJudges"]),
    }


def format_corpus_line(record: dict) -> str:
    """Render a tripwire record as a one-line cursor ``msg`` — scrubbed.

    Mirrors ``kata_trail.format_record_line``: control/ANSI characters are stripped
    and the field separator is neutralised so a rendered value cannot forge extra
    cursor fields.
    """
    dormant = record.get("dormantJudges") or []
    parts = [
        str(record.get("kind")),
        f"hash={record.get('corpusHash')}",
        f"verified={record.get('verified')}",
        f"dormant={record.get('dormant')}",
        f"honor-system={record.get('honorSystem')}",
        f"dormant-judges={','.join(dormant) if dormant else '-'}",
    ]
    return _scrub(" ".join(parts))


def record_corpus_hash(
    kata_dir: str | Path,
    *,
    run_id: str,
    repo_root: str | Path | None = None,
    summary: dict | None = None,
    agent: str = RECORD_AGENT,
    task: str = RECORD_TASK,
    parent_seq: int | None = None,
    now: datetime | None = None,
) -> kata_board.CursorLine:
    """Append the tripwire's corpus hash to the cursor as a NOTE line.

    ``NOTE`` is a worker-authored cursor type, so this runner may write it directly —
    unlike the seam-authored types (PHASE/VERDICT/SPAWN/DOWN/DENY), which this module
    never emits.  The append goes through ``kata_board.append_event`` and inherits its
    grammar guards (kata-dir traversal rejection, separator/newline refusal, append-only).

    Args:
        kata_dir: the running kata's ``.kata/`` directory (must already carry a run header).
        run_id: the run identity the record is stamped with (validated).
        repo_root: repo to check when ``summary`` is not supplied.
        summary: a ``check_all`` result to record; computed here when omitted.
        agent, task, parent_seq, now: passed through to ``kata_board.append_event``.

    Returns:
        The appended ``CursorLine``.
    """
    kata_board.validate_run_id(run_id)
    if summary is None:
        summary = check_all(repo_root)
    record = corpus_record(summary, run_id=run_id)
    return kata_board.append_event(
        kata_dir,
        agent,
        "NOTE",
        task,
        format_corpus_line(record),
        parent_seq=parent_seq,
        now=now,
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _render_text(summary: dict, pins: list[str]) -> str:
    """Human-readable report — one line per judge, then the stack rollup."""
    lines = ["Judge tripwires (TM-D3 · R-M6) — activation is a derived, recorded fact", ""]
    width = max(len(j["judge"]) for j in summary["judges"])
    for judge in summary["judges"]:
        lines.append(
            f"  {judge['judge']:<{width}}  {judge['activation']:<13} "
            f"fixtures={judge['fixtures']:<3} failable={judge['failable']:<3} "
            f"{judge['corpusDir']}"
        )
        for reason in judge["reasons"]:
            lines.append(f"      - {reason}")
    lines += [
        "",
        f"  corpus hash : {summary['corpusHash']}",
        f"  verified={summary['verified']}  dormant={summary['dormant']}  "
        f"honor-system={summary['honorSystem']}",
    ]
    if pins:
        lines.append("")
        lines.append("  CONTRACT PIN VIOLATIONS (registry enum vs the judge's SKILL.md):")
        lines += [f"      - {v}" for v in pins]
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    """Run every judge's tripwire.

    Exit codes: ``0`` clean (dormant-free; Honor-system judges never block), ``1`` at
    least one judge is Dormant or a contract pin is violated, ``2`` the runner REFUSED
    over a vacuous input.
    """
    parser = argparse.ArgumentParser(
        prog="tripwire_check",
        description="Judge-stack tripwire runner — every judge proves it can still fail.",
    )
    parser.add_argument(
        "--repo-root",
        default=None,
        help="repo root to check (default: the repo this module ships inside)",
    )
    parser.add_argument("--json", action="store_true", help="emit the summary as JSON")
    parser.add_argument("--record", action="store_true", help="append the corpus hash to the cursor")
    parser.add_argument("--kata-dir", default=".kata", help="kata dir for --record (default: .kata)")
    parser.add_argument("--run-id", default=None, help="run identity for --record")
    parser.add_argument("--agent", default=RECORD_AGENT, help="cursor agent id for --record")
    parser.add_argument("--task", default=RECORD_TASK, help="cursor task id for --record")
    args = parser.parse_args(argv)

    try:
        summary = check_all(args.repo_root)
    except (TripwireRefusal, ValueError) as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2

    pins = verify_contract_pins(args.repo_root)
    if args.json:
        print(json.dumps({**summary, "contractPinViolations": pins}, indent=2))
    else:
        print(_render_text(summary, pins))

    if args.record:
        if not args.run_id:
            print("REFUSED: --record requires --run-id", file=sys.stderr)
            return 2
        try:
            line = record_corpus_hash(
                args.kata_dir,
                run_id=args.run_id,
                repo_root=args.repo_root,
                summary=summary,
            )
        except (ValueError, OSError, kata_board.CursorError) as exc:
            print(f"REFUSED: could not record the corpus hash: {exc}", file=sys.stderr)
            return 2
        print(f"recorded on the cursor: seq={line.seq}")

    return 1 if (summary["dormant"] or pins) else 0


if __name__ == "__main__":
    raise SystemExit(main())
