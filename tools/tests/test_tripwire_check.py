"""Tests for tripwire_check.py — the judge-stack tripwire runner (TM-D3 · R-M6).

Detectors ATTEST and NARROW; judges judge.

Coverage
--------
(1)  THE EVIDENCE NODE: every landed judge fails its known-bad corpus — each
     registered judge is ``verified``, carries at least one entry demanding a FAILING
     verdict, and every expectation parses under the ONE parser bound to that judge's
     own CLOSED enum.  A deleted or weakened corpus turns this red.
(2)  Activation is a DERIVED, recorded fact with three states: ``honor-system`` (no
     corpus — never blocked, R-M6), ``dormant`` (corpus present but failure-capability
     undemonstrable), ``verified``.
(3)  A parse failure is a REFUSAL, never a skip: unreadable / non-JSON / wrong type /
     missing field / unknown field / wrong-judge / unknown-wrongness all go dormant
     with a named reason.
(4)  Anti-vacuity (TM-D3) applied to the runner itself: an empty registry and an absent
     ``skills/evaluate/`` both REFUSE rather than certify.
(5)  Shape conformance: out-of-enum and PASSING verdicts are rejected; only the failing
     subset counts as a known-bad expectation.
(6)  kata-validate's precedent corpus is REFERENCED in place, and this runner's
     derivation AGREES with ``validation_report.assert_tripwire_flagged`` on it.
(7)  The corpus hash is deterministic, content-sensitive, and RECORDED on the cursor as
     a NOTE line that parses back through the cursor grammar.
(8)  Contract pins: the registry's enums are pinned in the judges' own SKILL.md files —
     and the stated limit (token presence is forgeable, KH-T02) is PINNED BY A TEST THAT
     DEMONSTRATES THE MISS, not prosed away.
(9)  Registry completeness: a new judge under ``skills/evaluate/`` cannot be silently
     invisible to this runner.
(10) The boundary is enforced, not merely claimed: nothing here invokes a judge, and
     ``verified`` never asserts an observed failure.
(11) Exec safety: no subprocess / eval / exec anywhere in the module (AST-asserted).
(12) The path-guard family invariant (the registry row itself is a conductor
     integration act, not a builder self-paste).
(13) CLI exit codes: 0 clean, 1 dormant-or-pin-violation, 2 refusal.

No network, no subprocess, no mutation of the repo.
"""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

import kata_board
import tripwire_check as tc
from kata_dispatch import parse_verdict
from validation_report import assert_tripwire_flagged, tripwire_corpus

TOOLS_DIR = Path(__file__).resolve().parents[1]
MODULE_PATH = TOOLS_DIR / "tripwire_check.py"
REPO_ROOT = TOOLS_DIR.parent

#: The six judge contracts rewritten in W5, plus the precedent this task generalizes.
_W5_JUDGES = (
    "kata-evaluate",
    "kata-review-standard",
    "kata-review-essential",
    "kata-review-advanced",
    "kata-slop-check",
    "kata-inline-eval",
)

#: A cursor run id in the pinned grammar (``run-`` + utc-compact + ``-`` + hex).
_RUN_ID = "run-20260817T041200Z-abc123"


# ---------------------------------------------------------------------------
# Synthetic-repo helpers — a judge stack we fully control
# ---------------------------------------------------------------------------


def _skill_text(tokens: tuple[str, ...]) -> str:
    """A minimal contract file that satisfies the pin: tokens + the ONE parser."""
    rows = "\n".join(f"| `{t}` | meaning of {t}. |" for t in tokens)
    return (
        "# synthetic judge contract\n\n"
        "The literal FIRST LINE is `VERDICT: <enum>`.\n\n"
        "| Verdict | Meaning |\n|---|---|\n" + rows + "\n\n"
        "Parsed by the ONE verdict parser, `kata_dispatch.parse_verdict`.\n"
    )


def _synth_repo(
    tmp_path: Path,
    slug: str,
    *,
    fixtures: dict[str, str] | None = None,
    tokens: tuple[str, ...] = ("SHIP", "HOLD"),
    skill_text: str | None = None,
) -> Path:
    """Build a repo root holding one synthetic judge, optionally with a corpus."""
    root = tmp_path / "repo"
    skill_dir = root / "skills" / "evaluate" / slug
    skill_dir.mkdir(parents=True, exist_ok=True)
    (skill_dir / "SKILL.md").write_text(
        skill_text if skill_text is not None else _skill_text(tokens), encoding="utf-8"
    )
    if fixtures is not None:
        corpus = skill_dir / "fixtures"
        corpus.mkdir(exist_ok=True)
        for name, text in fixtures.items():
            (corpus / name).write_text(text, encoding="utf-8")
    return root


def _fixture(slug: str, verdict: str, **overrides) -> str:
    """A schema-valid judge-fixture payload, before any override."""
    payload = {
        "id": "tw-synth-001",
        "judge": slug,
        "wrongness": "vacuous-pass",
        "expected_verdict": verdict,
        "why": "a competent judge must fail this",
        "artifact": ["known-bad line one", "known-bad line two"],
    }
    payload.update(overrides)
    for key in [k for k, v in overrides.items() if v is _DROP]:
        payload.pop(key)
    return json.dumps(payload)


class _Drop:
    """Sentinel: remove this key from the fixture payload."""


_DROP = _Drop()


def _synth_contract(slug: str = "kata-synth") -> tc.JudgeContract:
    return tc._judge(slug, ("SHIP", "HOLD"), ("HOLD",))


# ===========================================================================
# (1) THE EVIDENCE NODE
# ===========================================================================


def test_every_landed_judge_fails_its_known_bad_corpus() -> None:
    """Every registered judge demonstrably demands a failing verdict on known-bad input.

    This is the task's declared evidence node.  It fails if a corpus is deleted, if a
    corpus stops demanding a failure, if an expectation drifts outside its judge's
    CLOSED enum, or if any judge goes Dormant.

    Honesty label, carried with the claim: this proves the corpora are present and
    MECHANICALLY conformant with each judge's pinned contract — it does not run an LLM
    judge over them (see the module's stated limit 1).
    """
    summary = tc.check_all()

    assert summary["judges"], "the judge registry is empty — nothing was certified"
    assert summary["dormant"] == 0, (
        f"Dormant judges (corpus present, failure-capability undemonstrable): "
        f"{summary['dormantJudges']}"
    )

    registered = {c.slug for c in tc.JUDGES}
    for slug in (*_W5_JUDGES, "kata-validate"):
        assert slug in registered, f"{slug} is not in the tripwire registry"

    by_slug = {row["judge"]: row for row in summary["judges"]}
    for contract in tc.JUDGES:
        row = by_slug[contract.slug]
        assert row["activation"] == tc.ACTIVATION_VERIFIED, (contract.slug, row["reasons"])
        assert row["failable"] >= 1, contract.slug
        assert row["corpusHash"], contract.slug

    # Read the corpora directly rather than trusting the runner's own count: every
    # expectation must be a FAILING verdict this judge's closed enum admits, and the
    # ONE parser must accept it on line 1.
    for contract in tc.JUDGES:
        if contract.corpus_kind != tc.CORPUS_JUDGE_FIXTURE:
            continue
        paths = tc.corpus_files(contract)
        assert paths, f"{contract.slug} has no corpus files"
        for path in paths:
            data = json.loads(path.read_text(encoding="utf-8"))
            expected = data["expected_verdict"]
            assert expected in contract.failing, (path.name, expected)
            line = f"VERDICT: {expected}"
            assert parse_verdict(line, allowed=frozenset(contract.enum)) == expected


def test_the_evidence_node_would_notice_a_weakened_corpus(tmp_path: Path) -> None:
    """Flipping one expectation to the PASSING verdict turns the check red.

    Without this, "every judge fails its known-bad corpus" could be satisfied by a
    corpus that demands nothing.
    """
    contract = _synth_contract()
    root = _synth_repo(
        tmp_path, contract.slug, fixtures={"weak.json": _fixture(contract.slug, "SHIP")}
    )
    result = tc.check_judge(contract, root)
    assert result.activation == tc.ACTIVATION_DORMANT
    assert result.failable == 0
    assert any("PASSING verdict" in r for r in result.reasons), result.reasons


# ===========================================================================
# (2) activation is a DERIVED fact — three states
# ===========================================================================


def test_a_judge_without_a_corpus_is_honor_system_and_never_blocked(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R-M6: deny-everything is dissolved — no corpus means declared, not blocked."""
    contract = _synth_contract()
    root = _synth_repo(tmp_path, contract.slug, fixtures=None)
    monkeypatch.setattr(tc, "JUDGES", (contract,))

    result = tc.check_judge(contract, root)
    assert result.activation == tc.ACTIVATION_HONOR_SYSTEM
    assert result.corpus_hash is None
    assert any("Honor-system" in r for r in result.reasons)

    summary = tc.check_all(root)
    assert (summary["honorSystem"], summary["dormant"], summary["verified"]) == (1, 0, 0)
    assert tc.main(["--repo-root", str(root)]) == 0, "an Honor-system judge must not block"


def test_an_empty_fixtures_dir_is_honor_system_not_verified(tmp_path: Path) -> None:
    """A dir that exists but holds nothing is an absence, not a certification."""
    contract = _synth_contract()
    root = _synth_repo(tmp_path, contract.slug, fixtures={})
    result = tc.check_judge(contract, root)
    assert result.activation == tc.ACTIVATION_HONOR_SYSTEM
    assert result.fixtures == 0


def test_a_corpus_that_cannot_fail_is_dormant_not_verified(tmp_path: Path) -> None:
    """All-clean findings ⇒ no failing expectation ⇒ Dormant, with the reason named."""
    contract = tc.JudgeContract(
        slug="kata-validate-synth",
        skill="skills/evaluate/kata-validate-synth/SKILL.md",
        corpus_dir="corpus",
        enum=("PASS", "FAIL"),
        failing=frozenset({"FAIL"}),
        corpus_kind=tc.CORPUS_VALIDATION_FINDING,
    )
    root = tmp_path / "repo"
    (root / "corpus").mkdir(parents=True)
    (root / "corpus" / "clean.json").write_text(
        json.dumps({"id": "c1", "severity": "info", "hold": False}), encoding="utf-8"
    )
    result = tc.check_judge(contract, root)
    assert result.activation == tc.ACTIVATION_DORMANT
    assert result.fixtures == 1 and result.failable == 0
    assert any("Dormant, not Verified" in r for r in result.reasons), result.reasons


def test_activation_states_are_a_closed_set() -> None:
    summary = tc.check_all()
    for row in summary["judges"]:
        assert row["activation"] in tc.ACTIVATION_STATES


# ===========================================================================
# (3) a parse failure is a REFUSAL, never a skip
# ===========================================================================


@pytest.mark.parametrize(
    "name,text,needle",
    [
        ("broken.json", "{not json", "not valid JSON"),
        ("list.json", "[1, 2]", "expected a JSON object"),
        (
            "missing.json",
            _fixture("kata-synth", "HOLD", expected_verdict=_DROP),
            "missing required field",
        ),
        (
            "unknown.json",
            _fixture("kata-synth", "HOLD", severity="high"),
            "unknown field",
        ),
        ("empty-why.json", _fixture("kata-synth", "HOLD", why="  "), "why must be"),
        (
            "no-artifact.json",
            _fixture("kata-synth", "HOLD", artifact=[]),
            "artifact must be a non-empty list",
        ),
        (
            "bad-artifact.json",
            _fixture("kata-synth", "HOLD", artifact=["ok", 3]),
            "artifact lines must all be strings",
        ),
        (
            "wrong-judge.json",
            _fixture("kata-synth", "HOLD", judge="kata-evaluate"),
            "does not match the owning",
        ),
        (
            "bad-class.json",
            _fixture("kata-synth", "HOLD", wrongness="it-felt-wrong"),
            "outside the closed",
        ),
        (
            "out-of-enum.json",
            _fixture("kata-synth", "MAYBE"),
            "outside kata-synth's closed enum",
        ),
    ],
)
def test_a_malformed_corpus_entry_goes_dormant_with_a_named_reason(
    tmp_path: Path, name: str, text: str, needle: str
) -> None:
    contract = _synth_contract()
    root = _synth_repo(tmp_path, contract.slug, fixtures={name: text})
    result = tc.check_judge(contract, root)
    assert result.activation == tc.ACTIVATION_DORMANT
    assert any(needle in r for r in result.reasons), (needle, result.reasons)


def test_one_bad_entry_dormants_the_judge_even_beside_a_good_one(tmp_path: Path) -> None:
    """A corpus is not 'mostly fine' — an unreadable member is an unanswered question."""
    contract = _synth_contract()
    root = _synth_repo(
        tmp_path,
        contract.slug,
        fixtures={
            "good.json": _fixture(contract.slug, "HOLD"),
            "bad.json": "{oops",
        },
    )
    result = tc.check_judge(contract, root)
    assert result.activation == tc.ACTIVATION_DORMANT
    assert result.failable == 1, "the good entry still counted — the reason is the bad one"


# ===========================================================================
# (4) anti-vacuity applied to the runner itself
# ===========================================================================


def test_check_all_refuses_over_an_empty_registry(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(tc, "JUDGES", ())
    with pytest.raises(tc.TripwireRefusal, match="registry is empty"):
        tc.check_all()


def test_check_all_refuses_when_the_judge_tree_is_absent(tmp_path: Path) -> None:
    (tmp_path / "empty").mkdir()
    with pytest.raises(tc.TripwireRefusal, match="absent or not a directory"):
        tc.check_all(tmp_path / "empty")


def test_derive_finding_verdict_refuses_a_non_binary_verdict_space() -> None:
    """The pass/fail derivation refuses to guess on a three-valued enum."""
    inline = next(c for c in tc.JUDGES if c.slug == "kata-inline-eval")
    with pytest.raises(tc.TripwireRefusal, match="not the binary"):
        tc.derive_finding_verdict({"severity": "error"}, inline)


# ===========================================================================
# (5) shape conformance against the judge's own CLOSED enum
# ===========================================================================


def test_check_shape_accepts_a_failing_verdict() -> None:
    evaluate = next(c for c in tc.JUDGES if c.slug == "kata-evaluate")
    assert tc.check_shape(evaluate, "NEEDS_WORK") is None


@pytest.mark.parametrize(
    "verdict,needle",
    [
        ("", "does not parse"),
        ("needs work", "does not parse"),
        ("MAYBE", "outside kata-evaluate's closed enum"),
        ("PASS", "is a PASSING verdict"),
    ],
)
def test_check_shape_rejects_everything_else(verdict: str, needle: str) -> None:
    evaluate = next(c for c in tc.JUDGES if c.slug == "kata-evaluate")
    error = tc.check_shape(evaluate, verdict)
    assert error is not None and needle in error, (verdict, error)


def test_inline_eval_treats_continue_as_the_one_non_failing_verdict() -> None:
    """`continue` is the explicit false-alarm verdict — a known-bad chunk must not get it."""
    inline = next(c for c in tc.JUDGES if c.slug == "kata-inline-eval")
    assert inline.passing == frozenset({"continue"})
    assert tc.check_shape(inline, "continue") is not None
    assert tc.check_shape(inline, "correct") is None
    assert tc.check_shape(inline, "reroll") is None


# ===========================================================================
# (6) the kata-validate precedent — REFERENCED, and agreed with
# ===========================================================================


def test_kata_validate_corpus_is_referenced_where_it_already_lives() -> None:
    validate = next(c for c in tc.JUDGES if c.slug == "kata-validate")
    assert validate.corpus_dir == "tools/tests/fixtures/validation_tripwire"
    assert validate.corpus_kind == tc.CORPUS_VALIDATION_FINDING
    assert not (REPO_ROOT / "skills" / "evaluate" / "kata-validate" / "fixtures").exists(), (
        "the precedent corpus must be referenced, not moved"
    )


def test_this_runners_derivation_agrees_with_the_precedent_engine() -> None:
    """The generalization must not disagree with the tripwire it generalizes.

    ``assert_tripwire_flagged`` raises unless the live corpus contains an
    error-severity-or-hold finding; this runner independently derives ``FAIL`` for
    exactly those findings.  Both legs are asserted over the SAME live corpus.
    """
    validate = next(c for c in tc.JUDGES if c.slug == "kata-validate")
    corpus = tripwire_corpus()
    assert corpus, "the precedent corpus is empty"
    assert_tripwire_flagged(corpus)  # raises on leniency — the precedent's own guard

    derived_failures = [
        f for f in corpus if tc.derive_finding_verdict(f, validate) in validate.failing
    ]
    assert derived_failures, "this runner derived no failing verdict where the engine did"

    result = tc.check_judge(validate)
    assert result.activation == tc.ACTIVATION_VERIFIED
    assert result.failable == len(derived_failures)


# ===========================================================================
# (7) the corpus hash, and the recorded fact on the cursor
# ===========================================================================


def test_corpus_hash_is_deterministic_and_content_sensitive(tmp_path: Path) -> None:
    contract = _synth_contract()
    root = _synth_repo(
        tmp_path, contract.slug, fixtures={"a.json": _fixture(contract.slug, "HOLD")}
    )
    paths = tc.corpus_files(contract, root)
    first = tc.corpus_hash(paths, repo_root=root)
    assert first == tc.corpus_hash(paths, repo_root=root), "not stable across re-runs"

    paths[0].write_text(
        _fixture(contract.slug, "HOLD", why="a competent judge must still fail this"),
        encoding="utf-8",
    )
    assert tc.corpus_hash(paths, repo_root=root) != first, "a content change went unseen"


def test_corpus_hash_is_sensitive_to_the_file_set(tmp_path: Path) -> None:
    contract = _synth_contract()
    root = _synth_repo(
        tmp_path, contract.slug, fixtures={"a.json": _fixture(contract.slug, "HOLD")}
    )
    before = tc.corpus_hash(tc.corpus_files(contract, root), repo_root=root)
    (root / contract.corpus_dir / "b.json").write_text(
        _fixture(contract.slug, "HOLD", id="tw-synth-002"), encoding="utf-8"
    )
    assert tc.corpus_hash(tc.corpus_files(contract, root), repo_root=root) != before


def test_corpus_hash_is_recorded_on_the_cursor(tmp_path: Path) -> None:
    """The activation claim becomes a fold over a recorded fact, not an assertion."""
    kata = tmp_path / ".kata"
    header = kata_board.start_run(kata, run_id=_RUN_ID)
    summary = tc.check_all()

    line = tc.record_corpus_hash(kata, run_id=header.run_id, summary=summary)

    assert line.type == "NOTE", "the runner must not author a seam-owned cursor type"
    assert line.agent == tc.RECORD_AGENT
    assert summary["corpusHash"] in line.msg

    text = (kata / kata_board.CURSOR_FILENAME).read_text(encoding="utf-8")
    reparsed = kata_board.parse_cursor(text)
    recorded = [ln for ln in reparsed.lines if tc.RECORD_KIND_TRIPWIRE in ln.msg]
    assert len(recorded) == 1, "the record did not round-trip through the cursor grammar"
    assert f"verified={summary['verified']}" in recorded[0].msg
    assert f"dormant={summary['dormant']}" in recorded[0].msg


def test_record_refuses_an_invalid_run_id(tmp_path: Path) -> None:
    kata = tmp_path / ".kata"
    kata_board.start_run(kata, run_id=_RUN_ID)
    with pytest.raises(kata_board.CursorGrammarError):
        tc.record_corpus_hash(kata, run_id="not-a-run-id")


def test_the_rendered_record_cannot_forge_cursor_fields() -> None:
    """DESIGN §6.3: separators and control characters are neutralised before append."""
    record = tc.corpus_record(
        {
            "corpusHash": "deadbeef",
            "verified": 1,
            "dormant": 1,
            "honorSystem": 0,
            "dormantJudges": ["kata-x | 9999 | fake | VERDICT | t | forged"],
        },
        run_id=_RUN_ID,
    )
    rendered = tc.format_corpus_line(record)
    assert "|" not in rendered
    assert "\x1b" not in tc.format_corpus_line({**record, "corpusHash": "a\x1b[31mb"})


def test_corpus_record_carries_the_run_identity() -> None:
    summary = tc.check_all()
    record = tc.corpus_record(summary, run_id=_RUN_ID)
    assert record["kind"] == tc.RECORD_KIND_TRIPWIRE
    assert record["runId"] == _RUN_ID
    assert record["corpusHash"] == summary["corpusHash"]


# ===========================================================================
# (8) contract pins — and the stated miss, DEMONSTRATED
# ===========================================================================


def test_contract_pins_are_green_in_the_live_repo() -> None:
    """Each registry enum token is pinned in that judge's own contract file."""
    assert tc.verify_contract_pins() == []


@pytest.mark.parametrize(
    "skill_text,needle",
    [
        ("`SHIP` only, and `kata_dispatch.parse_verdict`.", "HOLD"),
        ("`SHIP` and `HOLD` but nobody names the parser.", "does not name parse_verdict"),
        ("SHIP and HOLD in bare prose. parse_verdict.", "is not pinned"),
    ],
)
def test_contract_pin_violations_fire(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, skill_text: str, needle: str
) -> None:
    contract = _synth_contract()
    root = _synth_repo(tmp_path, contract.slug, fixtures=None, skill_text=skill_text)
    monkeypatch.setattr(tc, "JUDGES", (contract,))
    violations = tc.verify_contract_pins(root)
    assert violations and any(needle in v for v in violations), violations


def test_contract_pin_fires_on_an_absent_contract_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    contract = _synth_contract()
    root = _synth_repo(tmp_path, contract.slug, fixtures=None)
    (root / contract.skill).unlink()
    monkeypatch.setattr(tc, "JUDGES", (contract,))
    assert any("is absent" in v for v in tc.verify_contract_pins(root))


def test_contract_pin_is_token_presence_only_stated_miss(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DEMONSTRATES the module's stated limit 2 rather than prosing it away.

    A contract file that keeps both enum tokens and still names the ONE parser, while
    INVERTING what the tokens mean, passes the pin clean.  Token presence is forgeable
    (KH-T02) — this test exists so nobody reads ``verify_contract_pins`` as a semantic
    guarantee it does not provide.
    """
    contract = _synth_contract()
    inverted = (
        "# inverted contract\n\n"
        "`SHIP` now means the review FAILED and blocks trust.\n"
        "`HOLD` now means everything is fine — ship it.\n"
        "Parsed by `kata_dispatch.parse_verdict`.\n"
    )
    root = _synth_repo(tmp_path, contract.slug, fixtures=None, skill_text=inverted)
    monkeypatch.setattr(tc, "JUDGES", (contract,))
    assert tc.verify_contract_pins(root) == [], (
        "the miss is real and stated: this check cannot see an inverted meaning"
    )


# ===========================================================================
# (9) registry completeness — a new judge cannot be silently invisible
# ===========================================================================


def test_every_evaluate_skill_is_registered_or_named_non_judge() -> None:
    """The protocol-folder lesson: nothing enumerated the dir, so new members vanished.

    Every skill under ``skills/evaluate/`` must be either a registered judge or an
    explicitly named non-judge.  A new judge that is neither fails here BY NAME instead
    of quietly having no tripwire.
    """
    registered = {c.slug for c in tc.JUDGES}
    present = {p.parent.name for p in (REPO_ROOT / "skills" / "evaluate").glob("*/SKILL.md")}
    assert present, "no evaluate skills found — the scan itself is vacuous"
    unaccounted = present - registered - tc.NON_JUDGE_EVALUATE_SKILLS
    assert not unaccounted, (
        f"evaluate skills with no tripwire registry decision: {sorted(unaccounted)}"
    )


def test_the_two_registry_sets_do_not_overlap() -> None:
    assert not ({c.slug for c in tc.JUDGES} & tc.NON_JUDGE_EVALUATE_SKILLS)


def test_every_registered_judge_declares_a_failing_and_a_passing_verdict() -> None:
    """A judge whose whole enum is 'failing' proves nothing by failing."""
    for contract in tc.JUDGES:
        assert contract.failing, contract.slug
        assert contract.passing, contract.slug
        assert contract.failing <= frozenset(contract.enum), contract.slug


# ===========================================================================
# (10) the boundary is enforced, not merely claimed
# ===========================================================================


def test_verified_state_does_not_claim_the_judge_was_run() -> None:
    """``verified`` is a corpus-conformance fact; it never asserts an observed failure."""
    doc = ast.get_docstring(ast.parse(MODULE_PATH.read_text(encoding="utf-8"))) or ""
    assert "This runner never invokes a judge" in doc
    assert "not *this judge was observed failing*" in doc

    for row in tc.check_all()["judges"]:
        for reason in row["reasons"]:
            lowered = reason.lower()
            assert "observed" not in lowered, reason
            assert "was run" not in lowered, reason
        if row["activation"] == tc.ACTIVATION_VERIFIED:
            assert any("shape-conformant" in r for r in row["reasons"]), row


def test_the_module_dispatches_nothing() -> None:
    """No agent launch, no capture, no mint — the runner is a mechanical check."""
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imported.update(f"{node.module}.{a.name}" for a in node.names)
    # kata_dispatch is imported for ONE thing: the shared verdict parser.
    dispatch_uses = {n for n in imported if n.startswith("kata_dispatch.")}
    assert dispatch_uses == {"kata_dispatch.parse_verdict"}, dispatch_uses


# ===========================================================================
# (11) exec safety — asserted, not asserted-about
# ===========================================================================


def test_no_exec_sinks_anywhere_in_module() -> None:
    """The module spawns no subprocess and calls no eval/exec, BY CONTRACT.

    Asserted mechanically (the truth_serum / evidence_grammar precedent) so the claim in
    the module docstring — and the consequent absence of a protocol/exec-safety.md sink
    row — cannot rot into a stale comment.
    """
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    banned_modules = {"subprocess", "os", "shutil", "socket", "pty", "multiprocessing"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_modules, alias.name
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_modules, node.module
        elif isinstance(node, ast.Call):
            name = node.func.id if isinstance(node.func, ast.Name) else None
            assert name not in ("eval", "exec", "compile", "__import__"), name


# ===========================================================================
# (12) the path-guard family invariant
# ===========================================================================


def test_guard_path_rejects_traversal() -> None:
    with pytest.raises(ValueError):
        tc._guard_path("../evil/x")


def test_guard_path_accepts_a_clean_relative_path() -> None:
    tc._guard_path(".kata/sub/thing")


def test_a_traversal_repo_root_is_refused() -> None:
    with pytest.raises(ValueError):
        tc.check_all("../..")


def test_the_default_root_is_this_modules_own_repo() -> None:
    assert tc.REPO_ROOT == REPO_ROOT
    assert (tc.REPO_ROOT / "skills" / "evaluate").is_dir()


# ===========================================================================
# (13) CLI exit codes
# ===========================================================================


def test_cli_is_clean_on_the_live_repo(capsys: pytest.CaptureFixture[str]) -> None:
    assert tc.main([]) == 0
    assert "verified=" in capsys.readouterr().out


def test_cli_json_is_machine_readable(capsys: pytest.CaptureFixture[str]) -> None:
    assert tc.main(["--json"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["contractPinViolations"] == []
    assert {row["judge"] for row in payload["judges"]} == {c.slug for c in tc.JUDGES}


def test_cli_fails_when_a_judge_is_dormant(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    contract = _synth_contract()
    root = _synth_repo(tmp_path, contract.slug, fixtures={"bad.json": "{oops"})
    monkeypatch.setattr(tc, "JUDGES", (contract,))
    assert tc.main(["--repo-root", str(root)]) == 1
    assert "dormant" in capsys.readouterr().out


def test_cli_refuses_a_vacuous_input(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    (tmp_path / "empty").mkdir()
    assert tc.main(["--repo-root", str(tmp_path / "empty")]) == 2
    assert "REFUSED" in capsys.readouterr().err


def test_cli_record_requires_a_run_id(capsys: pytest.CaptureFixture[str]) -> None:
    assert tc.main(["--record"]) == 2
    assert "requires --run-id" in capsys.readouterr().err


def test_cli_records_on_the_cursor(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    kata = tmp_path / ".kata"
    kata_board.start_run(kata, run_id=_RUN_ID)
    assert tc.main(["--record", "--kata-dir", str(kata), "--run-id", _RUN_ID]) == 0
    assert "recorded on the cursor" in capsys.readouterr().out
    text = (kata / kata_board.CURSOR_FILENAME).read_text(encoding="utf-8")
    assert tc.RECORD_KIND_TRIPWIRE in text
