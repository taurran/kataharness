"""test_grounding_gate.py — TDD tests for tools/grounding_gate.py (S3a-2).

Run from the tools/ directory:
    uv run pytest tests/test_grounding_gate.py -q
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _finding(
    claim: str = "The sky is blue.",
    source: str = "docs/sky.md",
    confidence: str = "HIGH",
    grounds_to_plan: str = "YES",
) -> dict:
    """Build a minimal finding dict matching the kata-research output shape."""
    return {
        "claim": claim,
        "source": source,
        "confidence": confidence,
        "groundsToPlan": grounds_to_plan,
    }


# ---------------------------------------------------------------------------
# grounding_verdict
# ---------------------------------------------------------------------------

class TestGroundingVerdict:
    def test_ground_when_source_supports_and_no_conflict(self):
        from grounding_gate import grounding_verdict

        f = _finding(grounds_to_plan="YES")
        assert grounding_verdict(f, source_supports=True, locked_conflict=False) == "GROUND"

    def test_reject_when_source_does_not_support(self):
        from grounding_gate import grounding_verdict

        f = _finding(grounds_to_plan="YES")
        assert grounding_verdict(f, source_supports=False, locked_conflict=False) == "REJECT"

    def test_escalate_via_locked_conflict_even_when_source_supports(self):
        from grounding_gate import grounding_verdict

        f = _finding(grounds_to_plan="YES")
        assert grounding_verdict(f, source_supports=True, locked_conflict=True) == "ESCALATE"

    def test_escalate_via_grounds_to_plan_no_even_when_source_supports(self):
        from grounding_gate import grounding_verdict

        f = _finding(grounds_to_plan="NO")
        assert grounding_verdict(f, source_supports=True, locked_conflict=False) == "ESCALATE"

    def test_escalate_grounds_to_plan_no_overrides_source_not_supports(self):
        """ESCALATE wins over REJECT when groundsToPlan == 'NO'."""
        from grounding_gate import grounding_verdict

        f = _finding(grounds_to_plan="NO")
        assert grounding_verdict(f, source_supports=False, locked_conflict=False) == "ESCALATE"

    def test_escalate_locked_conflict_overrides_reject(self):
        """locked_conflict=True wins over REJECT (source_supports=False)."""
        from grounding_gate import grounding_verdict

        f = _finding(grounds_to_plan="YES")
        assert grounding_verdict(f, source_supports=False, locked_conflict=True) == "ESCALATE"

    def test_partial_grounds_to_plan_is_not_escalated(self):
        """PARTIAL does not trigger ESCALATE — only NO does."""
        from grounding_gate import grounding_verdict

        f = _finding(grounds_to_plan="PARTIAL")
        assert grounding_verdict(f, source_supports=True, locked_conflict=False) == "GROUND"

    def test_partial_grounds_to_plan_with_no_source_is_reject(self):
        from grounding_gate import grounding_verdict

        f = _finding(grounds_to_plan="PARTIAL")
        assert grounding_verdict(f, source_supports=False, locked_conflict=False) == "REJECT"

    # -- Q-1 (D136): groundsToPlan enum must be validated, not silently defaulted --

    def test_absent_grounds_to_plan_raises(self):
        """Absent groundsToPlan ⇒ ValueError (Q-1: no silent ESCALATE-skip)."""
        from grounding_gate import grounding_verdict

        f = {"claim": "c", "source": "s", "confidence": "HIGH"}  # no groundsToPlan
        with pytest.raises(ValueError, match=r"groundsToPlan"):
            grounding_verdict(f, source_supports=True, locked_conflict=False)

    def test_lowercase_no_grounds_to_plan_raises(self):
        """A lowercase 'no' would skip ESCALATE under the old == 'NO' check ⇒ raises."""
        from grounding_gate import grounding_verdict

        f = _finding(grounds_to_plan="no")
        with pytest.raises(ValueError, match=r"groundsToPlan"):
            grounding_verdict(f, source_supports=True, locked_conflict=False)

    def test_typo_grounds_to_plan_raises(self):
        """A bogus/typo groundsToPlan value ⇒ ValueError (D136)."""
        from grounding_gate import grounding_verdict

        f = _finding(grounds_to_plan="MAYBE")
        with pytest.raises(ValueError, match=r"groundsToPlan"):
            grounding_verdict(f, source_supports=True, locked_conflict=False)

    def test_none_grounds_to_plan_raises(self):
        """Explicit None groundsToPlan ⇒ ValueError (D136)."""
        from grounding_gate import grounding_verdict

        f = _finding(grounds_to_plan=None)  # type: ignore[arg-type]
        with pytest.raises(ValueError, match=r"groundsToPlan"):
            grounding_verdict(f, source_supports=True, locked_conflict=False)


# ---------------------------------------------------------------------------
# build_verdict
# ---------------------------------------------------------------------------

class TestBuildVerdict:
    def test_returns_dict_with_finding_verdict_evidence(self):
        from grounding_gate import build_verdict

        f = _finding()
        evidence = "Source paragraph 3 confirms the claim verbatim."
        result = build_verdict(f, source_supports=True, locked_conflict=False, evidence=evidence)

        assert result["finding"] == f
        assert result["verdict"] == "GROUND"
        assert result["evidence"] == evidence

    def test_verdict_is_reject_when_source_unsupported(self):
        from grounding_gate import build_verdict

        f = _finding()
        result = build_verdict(f, source_supports=False, locked_conflict=False, evidence="No match found.")

        assert result["verdict"] == "REJECT"
        assert result["finding"] == f
        assert result["evidence"] == "No match found."

    def test_verdict_is_escalate_via_locked_conflict(self):
        from grounding_gate import build_verdict

        f = _finding()
        result = build_verdict(f, source_supports=True, locked_conflict=True, evidence="Conflicts with LOCKED D1.")

        assert result["verdict"] == "ESCALATE"

    def test_evidence_can_be_empty_string(self):
        from grounding_gate import build_verdict

        f = _finding()
        result = build_verdict(f, source_supports=False, locked_conflict=False, evidence="")
        assert result["evidence"] == ""
        assert result["verdict"] == "REJECT"


# ---------------------------------------------------------------------------
# write_grounding
# ---------------------------------------------------------------------------

class TestWriteGrounding:
    def _make_verdicts(self, *verdict_strs: str) -> list[dict]:
        """Helper to build verdict dicts for write_grounding."""
        return [
            {"finding": _finding(claim=f"Claim {i}"), "verdict": v, "evidence": f"Evidence {i}"}
            for i, v in enumerate(verdict_strs)
        ]

    def test_writes_grounding_json_with_all_grounded_true(self, tmp_path: Path):
        from grounding_gate import write_grounding

        verdicts = self._make_verdicts("GROUND", "GROUND")
        out_path = write_grounding(str(tmp_path / "kata"), verdicts)

        p = Path(out_path)
        assert p.exists()
        assert p.name == "grounding.json"

        data = json.loads(p.read_text(encoding="utf-8"))
        assert data["allGrounded"] is True
        assert data["verdicts"] == verdicts

    def test_writes_grounding_json_with_all_grounded_false_mixed(self, tmp_path: Path):
        from grounding_gate import write_grounding

        verdicts = self._make_verdicts("GROUND", "REJECT", "ESCALATE")
        write_grounding(str(tmp_path / "kata"), verdicts)

        data = json.loads((tmp_path / "kata" / "grounding.json").read_text(encoding="utf-8"))
        assert data["allGrounded"] is False

    def test_writes_grounding_json_with_all_grounded_false_single_reject(self, tmp_path: Path):
        from grounding_gate import write_grounding

        verdicts = self._make_verdicts("REJECT")
        write_grounding(str(tmp_path / "kata"), verdicts)

        data = json.loads((tmp_path / "kata" / "grounding.json").read_text(encoding="utf-8"))
        assert data["allGrounded"] is False

    def test_creates_kata_dir_if_absent(self, tmp_path: Path):
        from grounding_gate import write_grounding

        kata_dir = tmp_path / "nested" / "kata"
        assert not kata_dir.exists()

        verdicts = self._make_verdicts("GROUND")
        write_grounding(str(kata_dir), verdicts)

        assert (kata_dir / "grounding.json").exists()

    def test_returns_path_string_to_grounding_json(self, tmp_path: Path):
        from grounding_gate import write_grounding

        verdicts = self._make_verdicts("GROUND")
        result = write_grounding(str(tmp_path / "kata"), verdicts)

        assert isinstance(result, str)
        assert result.endswith("grounding.json")

    def test_round_trips_via_json_load(self, tmp_path: Path):
        from grounding_gate import write_grounding

        verdicts = self._make_verdicts("GROUND", "REJECT")
        out = write_grounding(str(tmp_path / "kata"), verdicts)

        loaded = json.loads(Path(out).read_text(encoding="utf-8"))
        assert loaded["verdicts"] == verdicts
        assert loaded["allGrounded"] is False

    def test_empty_verdicts_all_grounded_false_vacuous(self, tmp_path: Path):
        """Empty list: allGrounded MUST be false + vacuous:true (Q-3 / D136).

        UPDATED for finding Q-3: the OLD behavior wrote allGrounded:true (a
        vacuous ``all([]) == True``), a spurious fold-authorization signal from
        zero decision input.  The fix emits an explicit non-permissive vacuous
        marker instead.
        """
        from grounding_gate import write_grounding

        out = write_grounding(str(tmp_path / "kata"), [])
        data = json.loads(Path(out).read_text(encoding="utf-8"))
        assert data["allGrounded"] is False
        assert data["vacuous"] is True
        assert data["verdicts"] == []

    def test_written_as_utf8_indent2(self, tmp_path: Path):
        from grounding_gate import write_grounding

        verdicts = self._make_verdicts("GROUND")
        out = write_grounding(str(tmp_path / "kata"), verdicts)
        raw = Path(out).read_bytes()
        # Indent-2 produces a newline after the opening brace
        text = raw.decode("utf-8")
        assert "  " in text  # indent-2 present


# ---------------------------------------------------------------------------
# Path-traversal guard
# ---------------------------------------------------------------------------

class TestSafePathGuard:
    def test_rejects_traversal_kata_dir(self, tmp_path: Path):
        from grounding_gate import write_grounding

        traversal = str(tmp_path / ".." / "escaped")
        with pytest.raises(ValueError):
            write_grounding(traversal, [])

    def test_rejects_double_dotdot_segment(self, tmp_path: Path):
        from grounding_gate import write_grounding

        traversal = str(tmp_path) + "/../../../etc/passwd"
        with pytest.raises(ValueError):
            write_grounding(traversal, [])

    def test_accepts_normal_path(self, tmp_path: Path):
        from grounding_gate import write_grounding

        # Should not raise
        verdicts = [{"finding": _finding(), "verdict": "GROUND", "evidence": "ok"}]
        write_grounding(str(tmp_path / "safe_kata"), verdicts)
        assert (tmp_path / "safe_kata" / "grounding.json").exists()
