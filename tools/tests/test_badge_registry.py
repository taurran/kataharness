"""test_badge_registry.py — EV-1, the Trust Regression Suite (trust-model DESIGN §9, LOCKED).

THE RULE THIS FILE MAKES MECHANICAL: *trust can only be claimed where a machine can
re-derive the claim.* The one-time promise audit found that honest labels live exactly
where ``validate_skills`` runs. EV-1 turns that correlation into a standing CI regression
so that facade REGROWTH is a validator failure on the commit that grows it, not a finding
in some future hand-audit that may never be commissioned.

``validate_skills.check_badge_registry`` walks the registry against the tree in BOTH
directions, and the two named evidence nodes below demonstrate one direction each:

* :func:`test_uncited_badge_fails_validator`        — forward: a Guardian claim in the
  doc layer that no registry entry covers FAILS, by file and line.
* :func:`test_cited_but_dead_check_fails_validator` — backward: a registered badge whose
  cited check id does not resolve to a runnable check FAILS.

Both are REVERT-PROOF by construction: each asserts the red, then asserts that repairing
*only* the thing under test turns the same fixture green. A test that only ever sees red
cannot tell a working guard from a fixture that was broken for some other reason.

This file also covers the two riders that share the check's ownership:

* the exec-safety mechanical scan's SCOPE EXTENSION to ``adapters/**/hooks/*.py`` (RS-L4)
  — widened before the wave-8 seam guard exists, deliberately inverting the D111
  whack-a-mole order of registering a guard only after the guarded thing arrives;
* **G24**, the ``docs/DETERMINISM-DOCTRINE.md`` fingerprint pin — the gap the conductor
  demonstrated live by mutating one word of the doctrine (RETIRED -> RETAINED) and
  watching the validator exit 0.

EXPECTED RED, NAMED (G24): on the real tree ``DOCS_FINGERPRINTS`` carries the sentinel
``PENDING-CONDUCTOR-PASTE`` and therefore MISMATCHES until the conductor reviews the
printed candidate digest and pastes it at integration. That is the two-step working, not
a regression — the same shape ``cursor.md``'s pre-rename digest already carries. The
tests here assert the MECHANISM (mismatch fires, match clears, the updater prints and
never rewrites); none of them asserts the sentinel value, so the conductor's paste turns
the validator green without touching this file.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

import evidence_grammar
import validate_skills as v

REPO = v.REPO_ROOT


# ---------------------------------------------------------------------------
# Fixture helpers — a miniature doc layer + registry, pointed at by monkeypatch
# ---------------------------------------------------------------------------

def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


def _fixture_repo(tmp_path: Path, monkeypatch, registry: dict, docs: dict[str, str]) -> Path:
    """Build a tmp repo with *docs* and *registry*, and aim the checker at it."""
    for rel, text in docs.items():
        _write(tmp_path / rel, text)
    registry_path = _write(tmp_path / "tools" / "badge_registry.json",
                           json.dumps(registry, indent=2))
    monkeypatch.setattr(v, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(v, "BADGE_REGISTRY", registry_path)
    return tmp_path


def _registry(*, badges=(), pending=(), non_claims=(), doc_layer=("docs/*.md",)) -> dict:
    return {
        "version": v.BADGE_REGISTRY_VERSION,
        "doc_layer": list(doc_layer),
        "claim_terms": ["Verified", "Partially verified"],
        "badges": list(badges),
        "pending_graduation": list(pending),
        "non_claims": list(non_claims),
    }


def _errors(findings) -> list[str]:
    return [f"{f.where}: {f.msg}" for f in findings if f.level == "ERROR"]


# ---------------------------------------------------------------------------
# Evidence node 1 — FORWARD: an uncited Guardian badge fails the validator
# ---------------------------------------------------------------------------

def test_uncited_badge_fails_validator(tmp_path, monkeypatch):
    """A Guardian claim in the doc layer that no registry entry covers is an ERROR.

    This is the direction that makes facade REGROWTH cost something: a new
    ``**Verified**`` line added to any doc-layer file fails the gauntlet on the commit
    that adds it, naming the file and the line, until a human classifies it.
    """
    doc = "# Seam\n\nEnforcement of the seam: **Verified** (intercepting).\n"
    _fixture_repo(tmp_path, monkeypatch, _registry(), {"docs/seam.md": doc})

    findings = _errors(v.check_badge_registry([]))
    assert findings, "an unregistered Guardian badge must fail the validator"
    assert any("docs/seam.md:3" in f and "uncited Guardian badge" in f for f in findings), findings

    # Revert-proof: registering that exact site — and changing nothing else — clears it.
    _write(tmp_path / "tools" / "badge_registry.json", json.dumps(_registry(badges=[{
        "id": "seam-enforcement",
        "file": "docs/seam.md",
        "anchor": "**Verified** (intercepting)",
        "claim": "Verified",
        "check": "probe:gauntlet",
    }]), indent=2))
    assert _errors(v.check_badge_registry([])) == []


def test_a_downgrade_is_not_a_claim_and_needs_no_citation(tmp_path, monkeypatch):
    """Honor-system / Dormant / Broken assert no trust, so they are not claim terms.

    A guard that demanded a citation for an honest downgrade would push authors toward
    silence — the opposite of what the Guardian scale exists to buy.
    """
    doc = "# Seam\n\nEnforcement is **Dormant (pre-activation)** and capture is Honor-system.\n"
    _fixture_repo(tmp_path, monkeypatch, _registry(), {"docs/seam.md": doc})
    findings = _errors(v.check_badge_registry([]))
    assert findings and "0 Guardian claim sites" in findings[0], findings


def test_non_claim_bucket_requires_a_written_reason(tmp_path, monkeypatch):
    """The escape hatch is not a one-word edit: a `non_claims` row without a reason fails."""
    doc = "Never render it as Verified.\n"
    _fixture_repo(tmp_path, monkeypatch, _registry(non_claims=[{
        "id": "negation", "file": "docs/x.md", "anchor": "Never render it as Verified",
    }]), {"docs/x.md": doc})
    assert any("missing non-empty field(s): ['reason']" in f
               for f in _errors(v.check_badge_registry([])))


# ---------------------------------------------------------------------------
# Evidence node 2 — BACKWARD: a cited-but-dead check fails the validator
# ---------------------------------------------------------------------------

def test_cited_but_dead_check_fails_validator(tmp_path, monkeypatch):
    """A badge citing a check that does not resolve is an ERROR.

    A registry that accepted any string as a citation would be the facade one layer up:
    the badge would read as re-derivable while nothing behind it could be run. The check
    id must name a check that EXISTS NOW — a badge is a claim made in the present tense.
    """
    doc = "The plan rung is graded **Verified** here.\n"
    entry = {
        "id": "plan-rung",
        "file": "docs/rung.md",
        "anchor": "graded **Verified** here",
        "claim": "Verified",
        "check": "test:tools/tests/test_rung.py::test_the_rung_refuses_an_unfrozen_plan",
    }
    repo = _fixture_repo(tmp_path, monkeypatch, _registry(badges=[entry]),
                         {"docs/rung.md": doc})

    findings = _errors(v.check_badge_registry([]))
    assert any("cited-but-dead check" in f and "does not exist" in f for f in findings), findings

    # Revert-proof, step 1: the file exists but does NOT define the cited node.
    _write(repo / "tools" / "tests" / "test_rung.py", "def test_something_else():\n    pass\n")
    findings = _errors(v.check_badge_registry([]))
    assert any("defines no test named" in f for f in findings), findings

    # Revert-proof, step 2: define the cited node — the same fixture goes green.
    _write(repo / "tools" / "tests" / "test_rung.py",
           "def test_the_rung_refuses_an_unfrozen_plan():\n    pass\n")
    assert _errors(v.check_badge_registry([])) == []


def test_a_freeform_command_is_never_a_check_id(tmp_path, monkeypatch):
    """The check-id grammar is the CLOSED evidence grammar — no fourth form, no escape."""
    doc = "Graded **Verified** by the suite.\n"
    _fixture_repo(tmp_path, monkeypatch, _registry(badges=[{
        "id": "x", "file": "docs/x.md", "anchor": "Graded **Verified** by the suite",
        "claim": "Verified", "check": "pytest -q && echo ok",
    }]), {"docs/x.md": doc})
    assert any("not a legal evidence declaration" in f for f in _errors(v.check_badge_registry([])))


def test_the_deny_tripwire_probe_graduated_to_a_live_check():
    """RS-H4 applied to badges, AFTER graduation (Loop C, G29/G30).

    ``probe:deny-tripwire`` shipped ``declared-before-active`` while the wave-8 seam guard
    did not yet exist; the guard landed at Loop C and G29 flipped the registry status to
    ``active``. This test is the graduation event's downstream: the probe is now a LIVE
    check (``_badge_check_is_live`` returns None — a badge MAY cite it), exactly as
    ``gauntlet`` always could. The no-result-must-not-inherit rule is still guarded — by
    the seam guard's own Dormant-on-no-result derivation (test_seam_guard.py) — this row
    simply records that the target now exists.
    """
    probes = evidence_grammar.load_probe_registry()
    assert probes["deny-tripwire"].status == "active"
    assert probes["gauntlet"].status == "active"

    assert v._badge_check_is_live("probe:deny-tripwire", REPO) is None
    assert v._badge_check_is_live("probe:gauntlet", REPO) is None


# ---------------------------------------------------------------------------
# The graduation mechanism — how a facade row becomes an honest badge
# ---------------------------------------------------------------------------

def test_pending_graduation_must_carry_an_honest_downgrade(tmp_path, monkeypatch):
    """The waiting-room bucket cannot hold a Verified claim at its stated grade.

    Without this, ``pending_graduation`` would be a place to PARK a badge rather than a
    place to ROUTE one — the silent-permissive default the whole design refuses.
    """
    doc = "| Claim | Verified surface |\n"
    _fixture_repo(tmp_path, monkeypatch, _registry(pending=[{
        "id": "ritual", "file": "docs/t.md", "anchor": "| Claim | Verified surface |",
        "claim": "Verified", "honest_grade": "Verified", "route": "wave 9",
    }]), {"docs/t.md": doc})
    assert any("is not a Guardian downgrade" in f for f in _errors(v.check_badge_registry([])))


def test_deleting_a_pending_row_does_not_make_the_claim_go_away(tmp_path, monkeypatch):
    """The graduation path is MOVE-with-a-live-check; deletion re-opens the forward failure.

    This is what makes the bucket a ratchet rather than a bin: a row can leave only by
    gaining a live check (into ``badges``), by being honestly reclassified (into
    ``non_claims``, with a reason), or by the claim itself leaving the tree.
    """
    doc = "| Claim | Verified surface |\n"
    pending = {
        "id": "ritual", "file": "docs/t.md", "anchor": "| Claim | Verified surface |",
        "claim": "Verified", "honest_grade": "Honor-system", "route": "wave 9 relabel",
    }
    repo = _fixture_repo(tmp_path, monkeypatch, _registry(pending=[pending]), {"docs/t.md": doc})
    assert _errors(v.check_badge_registry([])) == []

    _write(repo / "tools" / "badge_registry.json", json.dumps(_registry(), indent=2))
    assert any("uncited Guardian badge" in f for f in _errors(v.check_badge_registry([])))


def test_a_stale_entry_whose_badge_moved_fails(tmp_path, monkeypatch):
    """Backward direction, second leg: a registry pointing at a badge that is gone."""
    repo = _fixture_repo(tmp_path, monkeypatch, _registry(non_claims=[{
        "id": "gone", "file": "docs/x.md", "anchor": "never dressed as Verified",
        "reason": "a negation",
    }], badges=[{
        "id": "live", "file": "docs/x.md", "anchor": "graded **Verified**",
        "claim": "Verified", "check": "probe:gauntlet",
    }]), {"docs/x.md": "The rung is graded **Verified**.\nnever dressed as Verified\n"})
    assert _errors(v.check_badge_registry([])) == []

    _write(repo / "docs" / "x.md", "The rung is graded **Verified**.\n")
    findings = _errors(v.check_badge_registry([]))
    assert any("stale registry entry" in f and "'gone'" in f for f in findings), findings


# ---------------------------------------------------------------------------
# Anti-vacuity companion (TM-D3) — a scan over zero inputs certifies nothing
# ---------------------------------------------------------------------------

def test_zero_doc_layer_files_is_a_refusal_not_a_pass(tmp_path, monkeypatch):
    _fixture_repo(tmp_path, monkeypatch, _registry(doc_layer=("docs/*.md",)), {})
    findings = _errors(v.check_badge_registry([]))
    assert findings and "0 doc-layer files discovered" in findings[0], findings


def test_zero_claim_sites_is_a_refusal_not_a_pass(tmp_path, monkeypatch):
    _fixture_repo(tmp_path, monkeypatch, _registry(), {"docs/x.md": "nothing to see here\n"})
    findings = _errors(v.check_badge_registry([]))
    assert findings and "0 Guardian claim sites" in findings[0], findings


@pytest.mark.parametrize("payload, fragment", [
    ("{ not json", "not valid JSON"),
    (json.dumps({"version": 99}), "is not the version"),
    (json.dumps({"version": 1, "doc_layer": [], "claim_terms": ["Verified"],
                 "badges": [], "pending_graduation": [], "non_claims": []}), "'doc_layer'"),
    (json.dumps({"version": 1, "doc_layer": ["docs/*.md"], "claim_terms": ["Verified"],
                 "badges": {}, "pending_graduation": [], "non_claims": []}), "'badges'"),
])
def test_a_malformed_registry_is_a_loud_refusal(tmp_path, monkeypatch, payload, fragment):
    """An unreadable decision input is never a permissive pass (D136)."""
    path = _write(tmp_path / "badge_registry.json", payload)
    monkeypatch.setattr(v, "BADGE_REGISTRY", path)
    findings = _errors(v.check_badge_registry([]))
    assert findings and fragment in findings[0], findings


def test_an_absent_registry_is_a_loud_refusal(tmp_path, monkeypatch):
    monkeypatch.setattr(v, "BADGE_REGISTRY", tmp_path / "nope.json")
    findings = _errors(v.check_badge_registry([]))
    assert findings and "cannot read the committed badge registry" in findings[0], findings


# ---------------------------------------------------------------------------
# The REAL tree — the initial population, and its honesty
# ---------------------------------------------------------------------------

def test_real_tree_badge_registry_is_green():
    """Every Guardian claim in the real doc layer is classified, and every badge is live."""
    assert _errors(v.check_badge_registry([])) == []


def test_real_tree_initial_population_covers_every_guardian_badge():
    """Population completeness, asserted as a JOIN rather than a remembered count.

    The acceptance criterion is that the initial population covers EVERY Guardian badge
    currently in the doc layer. That is exactly "every scanned site is matched by some
    entry", which this recomputes from the tree instead of trusting a number written down
    once and never re-derived.
    """
    registry = v.load_badge_registry()
    sites = v._badge_sites(registry, REPO)
    assert sites, "the real doc layer must contain Guardian claim sites"

    entries = [e for bucket in v.BADGE_BUCKETS for e in registry[bucket]]
    uncovered = [
        f"{rel}:{lineno}" for rel, lineno, line in sites
        if not any(e["file"] == rel and e["anchor"] in line for e in entries)
    ]
    assert not uncovered, f"unclassified Guardian claim site(s): {uncovered}"

    ids = [e["id"] for e in entries]
    assert len(ids) == len(set(ids)), "registry entry ids must be unique"


def test_every_real_badge_cites_a_live_check():
    registry = v.load_badge_registry()
    assert registry["badges"], "the badges bucket must not be empty on the real tree"
    dead = {e["id"]: v._badge_check_is_live(e["check"], REPO) for e in registry["badges"]}
    assert not {k: r for k, r in dead.items() if r}, dead


def test_downgrades_are_deliberately_absent_from_the_claim_terms():
    """DESIGN §6.2: EV-1 guards the CLAIM of verification, never the honest downgrade."""
    terms = v.load_badge_registry()["claim_terms"]
    assert set(terms) == {"Verified", "Partially verified"}
    assert not (set(terms) & v.BADGE_DOWNGRADES)


def test_the_declared_doc_layer_is_pinned():
    """Scope SHRINKAGE is the cheap way to silence this guard, so the scope is pinned.

    Dropping ``skills/*/*/SKILL.md`` from ``doc_layer`` would stop covering every skill
    while leaving the check green — sites from the other globs keep the anti-vacuity legs
    satisfied. Pinning the list here makes narrowing it a loud, deliberate act that fails
    by name, exactly as ``PROTOCOL_EXEMPT``'s contents are pinned on the protocol side.
    Widening it is meant to be easy; this test is the one line you also update.
    """
    assert v.load_badge_registry()["doc_layer"] == [
        "protocol/*.md",
        "docs/*.md",
        "docs/platforms/*.md",
        "skills/*/*/SKILL.md",
        "skills/*/*/RUBRIC.md",
        "modules/*/*/SKILL.md",
        "AGENTS.md",
        "CONTEXT.md",
        "README.md",
        ".planning/BACKLOG.md",
        ".planning/specs/trust-model/evidence/promise-audit.md",
    ]


def test_the_new_checks_are_wired_into_the_gauntlet():
    """PD-1: present-in-the-tree but never called is NOT built.

    ``run_checks`` iterates the ``CHECKS`` registry, and the ``@check`` decorator is the
    only thing that puts a function there. A check that existed but was never registered
    would read as delivered while enforcing nothing on any commit — the exact facade
    shape EV-1 exists to catch, one layer down.
    """
    registered = {fn.__name__ for fn in v.CHECKS}
    for name in ("check_badge_registry", "check_adapter_hook_exec_safety", "check_docs_integrity"):
        assert name in registered, f"{name} is not registered in validate_skills.CHECKS"


# ---------------------------------------------------------------------------
# Exec-safety mechanical scan — the adapters/**/hooks/*.py scope extension (RS-L4)
# ---------------------------------------------------------------------------

def _hook_fixture(tmp_path, monkeypatch, name: str, body: str, doc: str = "no sinks here") -> Path:
    hooks = tmp_path / "adapters" / "claude" / "hooks"
    _write(hooks / name, body)
    monkeypatch.setattr(v, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(v, "ADAPTERS_DIR", tmp_path / "adapters")
    monkeypatch.setattr(v, "EXEC_SAFETY_DOC", _write(tmp_path / "protocol" / "exec-safety.md", doc))
    return tmp_path


def test_hook_scan_covers_the_wave8_seam_guard_path(tmp_path, monkeypatch):
    """The scope is widened BEFORE the guarded file exists — the inverted D111 order.

    ``adapters/claude/hooks/kata-seam-guard.py`` is a later wave's deliverable. The scan
    that will judge it is proven, here, to reach that exact path today.
    """
    _hook_fixture(tmp_path, monkeypatch, "kata-seam-guard.py",
                  "import subprocess\nsubprocess.run(['git', 'status'])\n")
    paths = [p.name for p in v._hook_scan_paths()]
    assert paths == ["kata-seam-guard.py"]
    findings = _errors(v.check_adapter_hook_exec_safety([]))
    assert any("UNREGISTERED hook" in f and "kata-seam-guard" in f for f in findings), findings

    # Revert-proof: registering the sink in the contract — nothing else — clears it.
    _write(tmp_path / "protocol" / "exec-safety.md", "| `kata-seam-guard` | host payload | external |")
    assert _errors(v.check_adapter_hook_exec_safety([])) == []


def test_shell_true_in_a_hook_is_an_error(tmp_path, monkeypatch):
    """A hook has no operator-domain standing: it runs on the host's trigger with the
    host's environment and a host-supplied payload on stdin."""
    _hook_fixture(tmp_path, monkeypatch, "kata-hook.py",
                  "import subprocess\nsubprocess.run('ls', shell=True)\n",
                  doc="| `kata-hook` | registered |")
    assert any("shell=True in an adapter hook" in f
               for f in _errors(v.check_adapter_hook_exec_safety([])))


def test_a_mention_of_subprocess_in_prose_is_not_a_sink(tmp_path, monkeypatch):
    """AST, not grep: a docstring that says `subprocess.run` is not a subprocess sink."""
    _hook_fixture(tmp_path, monkeypatch, "kata-hook.py",
                  '"""This hook never calls subprocess.run or subprocess.Popen."""\nX = 1\n')
    assert _errors(v.check_adapter_hook_exec_safety([])) == []


def test_an_unparseable_hook_is_never_a_permissive_pass(tmp_path, monkeypatch):
    _hook_fixture(tmp_path, monkeypatch, "kata-hook.py", "def broken(:\n")
    assert any("does not parse" in f for f in _errors(v.check_adapter_hook_exec_safety([])))


def test_zero_hooks_discovered_is_a_refusal(tmp_path, monkeypatch):
    monkeypatch.setattr(v, "ADAPTERS_DIR", tmp_path / "adapters")
    findings = _errors(v.check_adapter_hook_exec_safety([]))
    assert findings and "0 adapter hook modules discovered" in findings[0], findings


def test_real_tree_hooks_pass_the_exec_safety_scan():
    assert _errors(v.check_adapter_hook_exec_safety([])) == []
    assert v._hook_scan_paths(), "the real tree must contain adapter hooks to scan"


# ---------------------------------------------------------------------------
# G24 — the doctrine fingerprint pin
# ---------------------------------------------------------------------------

DOCTRINE_KEY = "docs/DETERMINISM-DOCTRINE.md"


def test_g24_the_doctrine_is_pinned_at_all():
    """The gap ruling G24 closes: the doctrine had no pin of any kind."""
    assert DOCTRINE_KEY in v.DOCS_FINGERPRINTS
    assert (REPO / DOCTRINE_KEY).exists()


def test_g24_a_one_word_doctrine_mutation_is_caught(tmp_path, monkeypatch):
    """The conductor's live spot-audit, re-run as a regression.

    One word of the doctrine was mutated (RETIRED -> RETAINED), the validator exited 0,
    and the mutation was not caught. With the pin in place the same edit is an ERROR.
    """
    doc = _write(tmp_path / DOCTRINE_KEY, "# Doctrine\n\nLaw 9: this rule is RETIRED.\n")
    monkeypatch.setattr(v, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(v, "DOCS_FINGERPRINTS", {DOCTRINE_KEY: v.protocol_fingerprint(doc)})
    assert _errors(v.check_docs_integrity([])) == []

    doc.write_text("# Doctrine\n\nLaw 9: this rule is RETAINED.\n", encoding="utf-8")
    findings = _errors(v.check_docs_integrity([]))
    assert findings and "fingerprint mismatch" in findings[0], findings


def test_g24_reflow_and_emphasis_do_not_trip_the_pin(tmp_path, monkeypatch):
    """The false-positive guard that keeps the gate usable: a check that cried wolf on
    every re-wrap would train blind re-approval and protect nothing."""
    doc = _write(tmp_path / DOCTRINE_KEY, "# Doctrine\n\nLaw 9: this rule is RETIRED.\n")
    monkeypatch.setattr(v, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(v, "DOCS_FINGERPRINTS", {DOCTRINE_KEY: v.protocol_fingerprint(doc)})
    doc.write_text("# Doctrine\n\nLaw 9:   this rule\nis **RETIRED**.\n", encoding="utf-8")
    assert _errors(v.check_docs_integrity([])) == []


def test_g24_a_missing_pinned_doc_is_an_error(tmp_path, monkeypatch):
    monkeypatch.setattr(v, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(v, "DOCS_FINGERPRINTS", {DOCTRINE_KEY: "deadbeef"})
    assert any("pinned doc-layer contract missing" in f for f in _errors(v.check_docs_integrity([])))


def test_g24_the_two_tables_stay_separate_and_uniformly_keyed():
    """PROTOCOL_FINGERPRINTS is keyed by BARE FILENAME under protocol/; DOCS_FINGERPRINTS
    by REPO-RELATIVE PATH. Mixing them would break the folder enumerator and the
    fingerprint-set equality test that guard the protocol side."""
    assert all("/" not in k for k in v.PROTOCOL_FINGERPRINTS)
    assert all("/" in k for k in v.DOCS_FINGERPRINTS)
    assert not (set(v.PROTOCOL_FINGERPRINTS) & set(v.DOCS_FINGERPRINTS))


def test_g24_the_updater_prints_both_tables_and_rewrites_neither():
    """The two-step is the whole point: a tamper-check that re-blesses itself is not one.

    Run as a real subprocess so the CLI contract is exercised, not a hand-call of main().
    """
    source = Path(v.__file__)
    before = source.read_bytes()
    proc = subprocess.run(
        [sys.executable, str(source), "--update-protocol-fingerprint"],
        cwd=str(source.parent), capture_output=True, text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "# PROTOCOL_FINGERPRINTS" in proc.stdout
    assert "# DOCS_FINGERPRINTS (G24)" in proc.stdout
    assert f'"{DOCTRINE_KEY}": "{v.protocol_fingerprint(REPO / DOCTRINE_KEY)}",' in proc.stdout
    assert source.read_bytes() == before, "the updater must PRINT the pin, never rewrite it"
