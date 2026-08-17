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


# ===========================================================================
# THE ATTESTED FACT TABLE (DESIGN §4 / TM-E2 / R-M10)
# ===========================================================================

RUN_ID = "run-20260817T000000Z-deadbeef"
SHA = "0123456789abcdef0123456789abcdef01234567"


def _result_json(run_id: str = RUN_ID, sha: str = SHA) -> dict:
    """A minimal RESULT.json that ``run_result.classify_evidence`` credits."""
    return {"gateName": "task", "runId": run_id, "resultSha": sha,
            "passed": 12, "failed": 0, "skipped": 0}


def _mutation_record(non_vacuous: bool = True, run_id: str = RUN_ID) -> dict:
    return {
        "records": [{"testWentRed": non_vacuous, "nonVacuous": non_vacuous}],
        "allNonVacuous": non_vacuous,
        "result": _result_json(run_id=run_id),
    }


def _spec(path: str = "tools/a.py", line: int = 3, text: str = "assert x") -> dict:
    return {"source_path": path, "line": line, "asserted_line": text,
            "test_cmd": "uv run pytest tests/test_a.py -q"}


# ---------------------------------------------------------------------------
# The row-schema reconciliation (Loop-A carried input)
# ---------------------------------------------------------------------------

class TestRowSchemaReconciliation:
    def test_fact_row_is_a_strict_superset_of_the_signal_row(self):
        """v1-provisional -> v1: every producer key survives, and two are added.

        This is the reconciliation ITSELF, asserted rather than prosed: the provisional
        marker may only drop because the shape is a superset, so the supersetness is a test.
        """
        import truth_signals
        from grounding_gate import promote_signal_row

        producer_row = truth_signals.build_row(
            detector="S2", row_class="phantom-reuse-claim", verdict="SIGNAL",
            subject="DESIGN.md:12", detail="reuse claim with no adjacent file:line",
            limits=["extracting arbitrary claims from prose stays judgment"],
            provenance=["reuses"],
        )
        promoted = promote_signal_row(producer_row)

        assert set(producer_row).issubset(set(promoted)), "a producer key was dropped"
        assert set(promoted) - set(producer_row) == {"tier", "attestedBy"}
        for key in ("class", "detail", "detector", "humility", "subject", "verdict"):
            assert promoted[key] == producer_row[key], f"{key} semantics changed"
        assert producer_row["limits"] == promoted["limits"]
        assert set(producer_row["provenance"]).issubset(set(promoted["provenance"]))

    def test_origin_schema_is_preserved_not_erased(self):
        import truth_signals
        from grounding_gate import FACT_ROW_SCHEMA, promote_signal_row

        row = truth_signals.build_row(detector="S1", row_class="unwired-symbol",
                                      verdict="SIGNAL", subject="a.py::f", detail="d")
        promoted = promote_signal_row(row)
        assert promoted["schema"] == FACT_ROW_SCHEMA
        assert "v1-provisional" not in promoted["schema"]
        assert f"origin-schema:{truth_signals.ROW_SCHEMA}" in promoted["provenance"]

    def test_unreconciled_row_schema_is_refused(self):
        from grounding_gate import GroundingBundleError, promote_signal_row

        with pytest.raises(GroundingBundleError):
            promote_signal_row({"schema": "some.other/v9", "detector": "S1",
                                "class": "c", "verdict": "SIGNAL", "subject": "s",
                                "detail": "d"})

    def test_a_row_arriving_marked_blocking_is_refused(self):
        """Signals never block — the promotion may not launder one into a blocking row."""
        import truth_signals
        from grounding_gate import GroundingBundleError, promote_signal_row

        forged = truth_signals.build_row(detector="S1", row_class="c", verdict="SIGNAL",
                                         subject="s", detail="d")
        forged["blocking"] = True
        with pytest.raises(GroundingBundleError):
            promote_signal_row(forged)

    def test_tier_grammars_mirror_the_producers_they_name(self):
        """The per-tier verdict enums are the PRODUCERS' enums, pinned equal."""
        import truth_serum
        import truth_signals
        from grounding_gate import HUMILITY_RULE, TIER_VERDICTS

        assert TIER_VERDICTS["BLOCKING"] == frozenset(truth_serum.VERDICTS)
        assert TIER_VERDICTS["SIGNAL"] == frozenset(truth_signals.SIGNAL_VERDICTS)
        assert TIER_VERDICTS["GROUNDING"] == frozenset({"GROUND", "REJECT", "ESCALATE"})
        assert TIER_VERDICTS["IDENTITY"] == frozenset({"CREDITABLE", "INPUT_ONLY", "UNUSABLE"})
        assert HUMILITY_RULE == truth_serum.HUMILITY_LINE == truth_signals.HUMILITY_RULE

    def test_identity_verdicts_cover_every_run_result_role(self):
        import run_result
        from grounding_gate import TIER_VERDICTS

        roles = {run_result.ROLE_GATE_EVIDENCE, run_result.ROLE_INPUT, run_result.ROLE_UNUSABLE}
        assert len(roles) == len(TIER_VERDICTS["IDENTITY"])


# ---------------------------------------------------------------------------
# Row construction + the roll-up
# ---------------------------------------------------------------------------

class TestFactRow:
    def test_off_enum_verdict_for_a_tier_is_refused(self):
        from grounding_gate import GroundingBundleError, fact_row

        with pytest.raises(GroundingBundleError):
            fact_row(tier="BLOCKING", detector="B1", row_class="c", verdict="SIGNAL",
                     subject="s", detail="d", attested_by="truth_serum")

    def test_unknown_tier_is_refused(self):
        from grounding_gate import GroundingBundleError, fact_row

        with pytest.raises(GroundingBundleError):
            fact_row(tier="VIBES", detector="X", row_class="c", verdict="PASS",
                     subject="s", detail="d", attested_by="x")

    def test_signal_rows_are_never_blocking_even_when_unattested(self):
        from grounding_gate import fact_row

        row = fact_row(tier="SIGNAL", detector="S1", row_class="anti-vacuity",
                       verdict="UNATTESTED", subject="<graph>", detail="d",
                       attested_by="truth_signals")
        assert row["blocking"] is False


class TestRollUp:
    def test_escalate_beats_reject_beats_ground(self):
        from grounding_gate import fact_row, roll_up

        ok = fact_row(tier="BLOCKING", detector="B1", row_class="detector-verdict",
                      verdict="PASS", subject="<B1>", detail="d", attested_by="truth_serum")
        bad = fact_row(tier="BLOCKING", detector="B3", row_class="finding:x",
                       verdict="BLOCK", subject="a.py:1", detail="d", attested_by="truth_serum")
        cannot = fact_row(tier="BLOCKING", detector="B5", row_class="detector-verdict",
                          verdict="REFUSE", subject="<B5>", detail="d",
                          attested_by="truth_serum")
        assert roll_up([ok]) == "GROUND"
        assert roll_up([ok, bad]) == "REJECT"
        assert roll_up([ok, bad, cannot]) == "ESCALATE"

    def test_signal_rows_contribute_nothing_to_the_roll_up(self):
        """A heuristic may never promote itself into a gate refusal."""
        from grounding_gate import fact_row, roll_up

        ok = fact_row(tier="BLOCKING", detector="B1", row_class="detector-verdict",
                      verdict="PASS", subject="<B1>", detail="d", attested_by="truth_serum")
        noisy = fact_row(tier="SIGNAL", detector="S1", row_class="anti-vacuity",
                         verdict="UNATTESTED", subject="<graph>", detail="d",
                         attested_by="truth_signals")
        assert roll_up([ok, noisy]) == "GROUND"

    def test_empty_considered_set_is_escalate_never_ground(self):
        from grounding_gate import fact_row, roll_up

        assert roll_up([]) == "ESCALATE"
        only_signal = fact_row(tier="SIGNAL", detector="S1", row_class="c", verdict="CLEAR",
                               subject="s", detail="d", attested_by="truth_signals")
        assert roll_up([only_signal]) == "ESCALATE"


# ---------------------------------------------------------------------------
# The R-M10 mutation attestation
# ---------------------------------------------------------------------------

class TestMutationAttestation:
    def _attest(self, **over):
        from grounding_gate import attest_mutation_set

        kwargs = dict(
            planned_task_ids=["t1"],
            task_records={"t1": _mutation_record()},
            expected_sha=SHA,
            expected_run_id=RUN_ID,
            sample_specs=[_spec()],
            sample_results=[{"testWentRed": True, "nonVacuous": True}],
        )
        kwargs.update(over)
        return attest_mutation_set(**kwargs)

    def test_full_set_attests(self):
        out = self._attest()
        assert out["verdict"] == "GROUND"
        classes = {r["class"] for r in out["rows"]}
        assert "mutation-record-attested" in classes
        assert "mutation-sample-bit" in classes

    def test_absent_record_rejects(self):
        out = self._attest(planned_task_ids=["t1", "t2"])
        classes = {r["class"] for r in out["rows"]}
        assert "mutation-record-absent" in classes
        assert out["verdict"] == "REJECT"

    def test_wrong_run_record_is_not_current(self):
        out = self._attest(task_records={"t1": _mutation_record(run_id="run-other-1")})
        row = next(r for r in out["rows"] if r["class"] == "mutation-record-not-current")
        assert "wrong-run" in row["detail"]
        assert out["verdict"] == "REJECT"

    def test_vacuous_record_rejects(self):
        out = self._attest(task_records={"t1": _mutation_record(non_vacuous=False)})
        assert any(r["class"] == "mutation-record-vacuous" for r in out["rows"])
        assert out["verdict"] == "REJECT"

    def test_no_sample_is_unattested_not_a_pass(self):
        """R-M10 is not satisfied by records alone — the sampled re-run is the seam."""
        out = self._attest(sample_specs=[], sample_results=[])
        assert any(r["class"] == "mutation-sample-absent" for r in out["rows"])
        assert out["verdict"] == "ESCALATE"

    def test_sample_that_did_not_bite_rejects(self):
        out = self._attest(sample_results=[{"testWentRed": False, "nonVacuous": False}])
        assert any(r["class"] == "mutation-sample-did-not-bite" for r in out["rows"])
        assert out["verdict"] == "REJECT"

    def test_empty_planned_set_refuses_to_attest(self):
        out = self._attest(planned_task_ids=[])
        assert out["rows"][0]["verdict"] == "UNATTESTED"
        assert out["verdict"] == "ESCALATE"

    def test_sample_source_label_travels_with_the_row(self):
        supplied = self._attest()
        row = next(r for r in supplied["rows"] if r["class"] == "mutation-sample-bit")
        assert "sampleSource=supplied" in row["detail"]
        assert "agent-supplied" in row["attestedBy"]
        engine = self._attest(sample_source="engine-rerun")
        row = next(r for r in engine["rows"] if r["class"] == "mutation-sample-bit")
        assert row["attestedBy"] == "mutation_run.prove_many"

    def test_worker_asserted_residual_travels_verbatim(self):
        out = self._attest()
        assert "claimed-set completeness stays worker-asserted" in out["residual"]
        assert all("claimed-set completeness stays worker-asserted" in " ".join(r["limits"])
                   for r in out["rows"])


class TestMutationSampling:
    def test_sort_is_the_design_compile_specification(self):
        from grounding_gate import sample_mutation_specs

        specs = [_spec("tools/b.py", 1), _spec("tools/a.py", 9), _spec("tools/a.py", 2)]
        out = sample_mutation_specs(specs, 2)
        assert [(s["source_path"], s["line"]) for s in out["sampled"]] == [
            ("tools/a.py", 2), ("tools/a.py", 9)]

    def test_truncation_is_recorded_never_silent(self):
        from grounding_gate import sample_mutation_specs

        specs = [_spec("tools/a.py", i) for i in range(1, 9)]
        out = sample_mutation_specs(specs, 5)
        assert out["truncated"] is True
        assert out["total"] == 8 and out["sampledCount"] == 5
        assert "TRUNCATED" in out["record"]

    def test_under_cap_takes_every_line(self):
        from grounding_gate import sample_mutation_specs

        out = sample_mutation_specs([_spec("tools/a.py", 1)], 5)
        assert out["truncated"] is False and out["sampledCount"] == 1

    def test_zero_sample_size_is_refused(self):
        from grounding_gate import GroundingBundleError, sample_mutation_specs

        with pytest.raises(GroundingBundleError):
            sample_mutation_specs([_spec()], 0)


# ---------------------------------------------------------------------------
# THE DECLARED EVIDENCE NODE
# ---------------------------------------------------------------------------

def test_fact_table_emit_and_attest(tmp_path: Path):
    """The frozen PLAN's declared evidence node for `grounding-agent`.

    One end-to-end stack-head pass over REAL producer outputs — `truth_serum` detector
    reports, `truth_signals` rows, `run_result` evidence identity, `grounding_gate`'s own
    per-finding verdicts, and the R-M10 mutation attestation — proving BOTH halves of the
    acceptance: the fact table emits and ROUND-TRIPS (build -> render -> parse -> write ->
    read, byte-stable), and the mutation record set is ATTESTED (present + current +
    per-task complete + the sampled subset re-run).
    """
    import truth_serum
    import truth_signals
    from grounding_gate import (
        FACT_ROW_SCHEMA,
        FACT_TABLE_SCHEMA,
        build_fact_table,
        build_verdict,
        detector_rows,
        grounding_rows,
        identity_rows,
        parse_fact_table,
        promote_signal_row,
        render_fact_table,
        run_stack_head_pass,
        write_fact_table,
    )

    # --- REAL producer outputs -------------------------------------------------
    repo = tmp_path / "repo"
    (repo / "tools").mkdir(parents=True)
    (repo / "tools" / "clean.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    b3 = truth_serum.scan_debt_markers(repo, ["tools/clean.py"])

    signal = truth_signals.build_row(
        detector="S1", row_class="unwired-symbol", verdict="SIGNAL",
        subject="tools/clean.py::f", detail="no non-test reference reaches it",
        limits=list(truth_signals.S1_HONEST_LIMITS),
    )
    verdict = build_verdict(_finding(), True, False, "the source says it verbatim")

    # --- compose ---------------------------------------------------------------
    rows = detector_rows(b3.to_dict())
    rows.append(promote_signal_row(signal))
    rows.extend(grounding_rows([verdict]))
    rows.extend(identity_rows("RESULT.json", _result_json(), SHA, RUN_ID))

    from grounding_gate import attest_mutation_set

    attestation = attest_mutation_set(
        planned_task_ids=["tm-lb-grounding-agent"],
        task_records={"tm-lb-grounding-agent": _mutation_record()},
        expected_sha=SHA,
        expected_run_id=RUN_ID,
        sample_specs=[_spec()],
        sample_results=[{"testWentRed": True, "nonVacuous": True}],
        sample_source="engine-rerun",
    )
    rows.extend(attestation["rows"])

    table = build_fact_table(
        target={"runId": RUN_ID, "sha": SHA, "taskId": "tm-lb-grounding-agent",
                "gate": "final"},
        rows=rows,
        mutation=attestation,
    )

    # --- the table carries all three declared input classes ---------------------
    tiers = {r["tier"] for r in table["rows"]}
    assert {"BLOCKING", "SIGNAL", "GROUNDING", "IDENTITY", "MUTATION"} == tiers
    assert table["schema"] == FACT_TABLE_SCHEMA
    assert all(r["schema"] == FACT_ROW_SCHEMA for r in table["rows"])
    assert table["verdict"] == "GROUND"
    assert table["vacuous"] is False

    # --- the mutation set is ATTESTED (R-M10) -----------------------------------
    assert attestation["verdict"] == "GROUND"
    mutation_rows = {r["class"]: r["verdict"] for r in table["rows"] if r["tier"] == "MUTATION"}
    assert mutation_rows["mutation-record-attested"] == "ATTESTED"
    assert mutation_rows["mutation-sample-bit"] == "ATTESTED"
    assert table["mutationAttestation"]["sampling"]["truncated"] is False

    # --- the honesty labels travel ---------------------------------------------
    assert "MODELED, not measured" in table["overheadRecord"]
    assert "EXCEPT the mutation re-run" in table["overheadRecord"]
    assert table["scopeBoundary"] == (
        "grounding attests FACTS pre-judgment; the challenger attacks JUDGMENTS post-hoc")
    assert table["humility"] == (
        "the judgment+human layers found all of these; "
        "the automated mechanical gates found none")

    # --- ROUND-TRIP: build -> render -> parse -> write -> read ------------------
    rendered = render_fact_table(table)
    assert parse_fact_table(rendered) == table
    assert render_fact_table(parse_fact_table(rendered)) == rendered  # byte-stable

    out = write_fact_table(str(tmp_path / "kata"), table)
    reloaded = parse_fact_table(Path(out).read_text(encoding="utf-8"))
    assert reloaded == table

    # --- the same pass, driven end-to-end through the bundle entry point --------
    from_bundle = run_stack_head_pass({
        "target": {"runId": RUN_ID, "sha": SHA, "taskId": "tm-lb-grounding-agent"},
        "detectors": [b3.to_dict()],
        "signals": [signal],
        "verdicts": [verdict],
        "identity": [{"name": "RESULT.json", "result": _result_json()}],
        "mutation": {
            "plannedTaskIds": ["tm-lb-grounding-agent"],
            "taskRecords": {"tm-lb-grounding-agent": _mutation_record()},
            "sampleSpecs": [_spec()],
            "sampleResults": [{"testWentRed": True, "nonVacuous": True}],
        },
    })
    assert from_bundle["verdict"] == "GROUND"
    assert {r["tier"] for r in from_bundle["rows"]} == tiers


# ---------------------------------------------------------------------------
# Round-trip refusals + the table contract
# ---------------------------------------------------------------------------

class TestFactTableRoundTrip:
    def _table(self):
        from grounding_gate import build_fact_table, fact_row

        row = fact_row(tier="BLOCKING", detector="B1", row_class="detector-verdict",
                       verdict="PASS", subject="<B1>", detail="d", attested_by="truth_serum")
        return build_fact_table(target={"runId": RUN_ID, "sha": SHA}, rows=[row])

    def test_a_hand_edited_verdict_is_refused_not_believed(self):
        """Recompute, don't shape-check (Determinism Doctrine law 13)."""
        from grounding_gate import GroundingBundleError, parse_fact_table, render_fact_table

        table = self._table()
        table["rows"][0]["verdict"] = "BLOCK"  # rows now recompute to REJECT
        with pytest.raises(GroundingBundleError, match="recompute"):
            parse_fact_table(render_fact_table(table))

    def test_foreign_row_schema_is_refused(self):
        from grounding_gate import GroundingBundleError, parse_fact_table

        table = self._table()
        table["rows"][0]["schema"] = "kata.truth-signals.row/v1-provisional"
        with pytest.raises(GroundingBundleError):
            parse_fact_table(table)

    def test_unparseable_payload_is_refused(self):
        from grounding_gate import GroundingBundleError, parse_fact_table

        with pytest.raises(GroundingBundleError):
            parse_fact_table("{not json")

    def test_write_refuses_a_table_it_would_not_read_back(self, tmp_path: Path):
        from grounding_gate import GroundingBundleError, write_fact_table

        table = self._table()
        table["verdict"] = "GROUND-ISH"
        with pytest.raises(GroundingBundleError):
            write_fact_table(str(tmp_path / "kata"), table)
        assert not (tmp_path / "kata" / "fact-table.json").exists()

    def test_bundle_without_identity_is_refused(self):
        from grounding_gate import GroundingBundleError, run_stack_head_pass

        with pytest.raises(GroundingBundleError):
            run_stack_head_pass({"target": {"taskId": "t"}})

    def test_write_path_traversal_is_refused(self, tmp_path: Path):
        from grounding_gate import write_fact_table

        with pytest.raises(ValueError):
            write_fact_table(str(tmp_path / ".." / "escaped"), self._table())


# ---------------------------------------------------------------------------
# The standing contract text (DESIGN §4) — closed table, labeled overhead
# ---------------------------------------------------------------------------

class TestStandingContract:
    def test_signal_trigger_table_is_closed_and_exact(self):
        """DESIGN §4's four triggers, and ONLY those four."""
        from grounding_gate import SIGNAL_TRIGGERS

        assert [t[0] for t in SIGNAL_TRIGGERS] == [
            "reuse-claim-phrase", "unattestable-done", "research-finding",
            "resolved-but-unread-citation",
        ]
        assert len(SIGNAL_TRIGGERS) == 4

    def test_overhead_record_is_quoted_as_modeled_and_labeled(self):
        from grounding_gate import OVERHEAD_RECORD

        assert OVERHEAD_RECORD.startswith("MODELED, not measured")
        assert "+15-30 serialized minutes" in OVERHEAD_RECORD
        assert "+2-5 minutes per run" in OVERHEAD_RECORD
        assert "EXCEPT the mutation re-run" in OVERHEAD_RECORD

    def test_pass_verdicts_are_the_modules_own_three(self):
        from grounding_gate import PASS_VERDICTS, grounding_verdict

        assert set(PASS_VERDICTS) == {"GROUND", "REJECT", "ESCALATE"}
        assert grounding_verdict(_finding(), True, False) in PASS_VERDICTS


class TestExecSafety:
    def test_module_contains_no_subprocess_sink(self):
        """The exec-safety claim, asserted mechanically so it cannot rot into a comment.

        Execution reaches this module ONLY by delegation to `mutation_run.prove_many` ->
        `mutation_run._default_runner`, an already-registered sink (protocol/exec-safety.md).
        The `run_result.resolve_head_sha` precedent: a caller gains execution through a
        registered sink WITHOUT growing a spawn site of its own.
        """
        import ast

        source = Path(__file__).resolve().parent.parent / "grounding_gate.py"
        tree = ast.parse(source.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                value = node.func.value
                assert not (isinstance(value, ast.Name) and value.id == "subprocess"), (
                    "grounding_gate grew a subprocess sink — it needs an exec-safety row"
                )
            if isinstance(node, ast.Import):
                assert all(a.name != "subprocess" for a in node.names)


class TestCli:
    def _bundle(self, tmp_path: Path, records: dict) -> str:
        bundle = {
            "target": {"runId": RUN_ID, "sha": SHA, "taskId": "t1"},
            "identity": [{"name": "RESULT.json", "result": _result_json()}],
            "mutation": {
                "plannedTaskIds": ["t1"],
                "taskRecords": {"t1": records},
                "sampleSpecs": [_spec()],
                "sampleResults": [{"testWentRed": True, "nonVacuous": True}],
            },
        }
        path = tmp_path / "bundle.json"
        path.write_text(json.dumps(bundle), encoding="utf-8")
        return str(path)

    def test_ground_exits_zero_and_writes_the_table(self, tmp_path: Path):
        from grounding_gate import main

        code = main(["--bundle", self._bundle(tmp_path, _mutation_record()),
                     "--out", str(tmp_path / "kata")])
        assert code == 0
        assert (tmp_path / "kata" / "fact-table.json").exists()

    def test_reject_exits_one(self, tmp_path: Path):
        from grounding_gate import main

        code = main(["--bundle", self._bundle(tmp_path, _mutation_record(non_vacuous=False)),
                     "--out", str(tmp_path / "kata")])
        assert code == 1
