"""Guard tests for the Prime Directives standing contract (2026-07-12 health review).

The Prime Directives (`protocol/prime-directives.md`) are the never-tiered behavioral
contract injected into every run: PD-1 (never silently defer/stub/skip designed work;
express operator permission before any bypass) and PD-2 (absolute truthfulness — a
stub/scaffold reported as a completed feature IS DRIFT).

These tests pin the three wiring legs so the contract cannot be silently unshipped:
1. the contract body keeps its load-bearing terms (via REQUIRED_PROTOCOL registration);
2. the launch-orientation contract (`protocol/orientation.md`) carries it at the STABLE
   tier (the tier that is never dropped under budget);
3. the canonical instruction file (`AGENTS.md`) mandates it at spine level.

All tests exercise the real validator/real tree — no rule is re-implemented here.
"""

from pathlib import Path

import validate_skills as v

PD_FILE = "prime-directives.md"
PD_TERMS = ["PD-1", "PD-2", "DRIFT", "kata-defer", "escalation", "truthful", "stable tier"]
REPO_ROOT = Path(v.__file__).resolve().parent.parent


def test_prime_directives_in_required_protocol():
    """prime-directives.md is registered in REQUIRED_PROTOCOL with every load-bearing term."""
    assert PD_FILE in v.REQUIRED_PROTOCOL, "prime-directives.md must be in REQUIRED_PROTOCOL"
    registered = v.REQUIRED_PROTOCOL[PD_FILE]
    for term in PD_TERMS:
        assert term in registered, f"REQUIRED_PROTOCOL[{PD_FILE!r}] must include {term!r}"


def test_real_tree_contract_body_passes():
    """The real protocol/prime-directives.md carries all registered terms → validator clean."""
    findings = v.check_protocol_schemas([])
    pd_findings = [f for f in findings if PD_FILE in f.where]
    assert pd_findings == [], f"expected no prime-directives.md errors; got {pd_findings}"


def test_term_removed_errors(tmp_path, monkeypatch):
    """Hollowing the contract (a load-bearing term removed) → ERROR from check_protocol_schemas."""
    protocol_dir = tmp_path / "protocol"
    protocol_dir.mkdir()
    real_text = (REPO_ROOT / "protocol" / PD_FILE).read_text(encoding="utf-8")
    (protocol_dir / PD_FILE).write_text(real_text.replace("PD-1", "PD-x"), encoding="utf-8")
    monkeypatch.setattr(v, "PROTOCOL_DIR", protocol_dir)
    monkeypatch.setattr(v, "REQUIRED_PROTOCOL", {PD_FILE: v.REQUIRED_PROTOCOL[PD_FILE]})
    findings = v.check_protocol_schemas([])
    assert any(PD_FILE in f.where and "PD-1" in f.msg for f in findings), (
        f"removing 'PD-1' from the contract body must ERROR; got {findings}"
    )


def test_orientation_stable_tier_carries_prime_directives():
    """protocol/orientation.md sources prime-directives.md in the STABLE tier row."""
    text = (REPO_ROOT / "protocol" / "orientation.md").read_text(encoding="utf-8")
    stable_rows = [ln for ln in text.splitlines() if ln.startswith("| **stable**")]
    assert stable_rows, "orientation.md must keep a '| **stable** |' tier row"
    assert any("prime-directives.md" in row for row in stable_rows), (
        "the stable tier row must source protocol/prime-directives.md"
    )


def test_agents_md_mandates_prime_directives():
    """Root AGENTS.md carries the spine-level Prime Directives mandate."""
    text = (REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "prime-directives.md" in text, "AGENTS.md must reference protocol/prime-directives.md"
    assert "PD-1" in text and "PD-2" in text, "AGENTS.md must name both directives"
