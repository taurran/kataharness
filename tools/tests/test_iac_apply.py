"""test_iac_apply.py — TDD suite for tools/iac_apply.py (IaC Tier-2, Slice A).

Strategy: default-FAIL, creds-free, operates on PROVIDED plan/change-set JSON
fixtures. Pure tests (no I/O except fixture loads + tmp_path writes). Mutation
proofs spawn a real subprocess via mutation_run.prove_non_vacuous and always
restore the source (try/finally in prove_non_vacuous).

Coverage map
------------
Argv builders (structured, shell=False, no -target, no -auto-approve, -- inserted):
    TestTfArgvBuilders / TestCfnArgvBuilders
Identifier anti-injection + the DEDICATED CFN ARN grammar (distinct from stack-name):
    TestIdentifierValidation
plan_hash (TF binary bytes + CFN full-response binding):
    TestPlanHash
approval_verdict (mismatch -> APPROVAL_INVALIDATED, never collapse to pass):
    TestApprovalVerdict
capability_gate_verdict (typed, distinct, SELF-BINDING):
    TestCapabilityGate
apply_state (state machine, drift-abort regardless of approval/grant):
    TestApplyState
schema / artifact / audit round-trips:
    TestSchemaArtifactAudit
run_apply deferred seam (raises; docstring states n=0-live limitation):
    TestRunApplySeam
exec-safety AST source-scan (no subprocess/eval/exec/shell=True):
    TestExecSafety
mutation non-vacuity proofs (a-f) via prove_non_vacuous:
    TestMutationProof
"""

from __future__ import annotations

import ast
import inspect
import json
import sys
from pathlib import Path

import pytest

import iac_apply as ia
import iac_detect

_TOOLS = Path(__file__).resolve().parent.parent
_FIXTURES = Path(__file__).resolve().parent / "fixtures" / "iac_apply"


def _load_json(name: str) -> dict:
    return json.loads((_FIXTURES / name).read_text(encoding="utf-8"))


def _tf_destructive() -> list[dict]:
    """Destructive TF entries via the real iac_detect family scan (proves reuse)."""
    return iac_detect.scan_tf_plan(_load_json("tf_plan_stateful_delete.json"))


def _cfn_destructive() -> list[dict]:
    """Destructive CFN entries via the real iac_detect family scan (proves reuse)."""
    return iac_detect.scan_cfn_changeset(_load_json("cfn_describe_changeset.json"))


_VALID_ARN = (
    "arn:aws:cloudformation:us-east-1:123456789012:changeSet/"
    "my-change-set/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d"
)


# ---------------------------------------------------------------------------
# Terraform argv builders
# ---------------------------------------------------------------------------


class TestTfArgvBuilders:
    def test_tf_plan_exact_argv(self):
        argv = ia.build_tf_plan_argv(
            chdir="infra/prod", out_path="tfplan", var_files=["prod.tfvars"]
        )
        assert argv == [
            "terraform", "-chdir", "infra/prod",
            "plan", "-input=false", "-lock=true",
            "-out", "tfplan", "-var-file", "prod.tfvars",
        ]
        assert all(isinstance(a, str) for a in argv)

    def test_tf_plan_no_chdir(self):
        argv = ia.build_tf_plan_argv(out_path="tfplan")
        assert argv[0] == "terraform"
        assert "-chdir" not in argv

    def test_tf_apply_exact_argv_applies_saved_plan(self):
        argv = ia.build_tf_apply_argv(chdir="infra/prod", plan_file="tfplan")
        assert argv == [
            "terraform", "-chdir", "infra/prod",
            "apply", "-input=false", "-lock=true", "--", "tfplan",
        ]

    def test_tf_apply_inserts_end_of_options_before_positional_data(self):
        argv = ia.build_tf_apply_argv(plan_file="tfplan")
        assert "--" in argv
        # plan_file is the positional DATA element, AFTER the -- separator.
        assert argv.index("--") < argv.index("tfplan")
        assert argv[0] == "terraform"

    def test_tf_builders_never_emit_target(self):
        for argv in (
            ia.build_tf_plan_argv(out_path="tfplan"),
            ia.build_tf_apply_argv(plan_file="tfplan"),
        ):
            assert not any(tok == "-target" or tok.startswith("-target") for tok in argv)

    def test_tf_apply_never_emits_auto_approve(self):
        argv = ia.build_tf_apply_argv(plan_file="tfplan")
        assert "-auto-approve" not in argv
        assert not any("auto-approve" in tok for tok in argv)

    def test_tf_builders_expose_no_target_parameter(self):
        for fn in (ia.build_tf_plan_argv, ia.build_tf_apply_argv):
            params = inspect.signature(fn).parameters
            assert "target" not in params
            assert "shell" not in params

    def test_tf_builders_emit_no_shell_string(self):
        # No element is a shell pipeline / metacharacter string.
        argv = ia.build_tf_apply_argv(plan_file="tfplan")
        for tok in argv:
            assert ";" not in tok and "|" not in tok and "&&" not in tok


# ---------------------------------------------------------------------------
# CloudFormation argv builders
# ---------------------------------------------------------------------------


class TestCfnArgvBuilders:
    def test_cfn_create_changeset_exact_argv(self):
        argv = ia.build_cfn_create_changeset_argv(
            stack_name="prod-data",
            change_set_name="my-change-set",
            template_path="templates/db.yaml",
        )
        assert argv == [
            "aws", "cloudformation", "create-change-set",
            "--stack-name", "prod-data",
            "--change-set-name", "my-change-set",
            "--template-body", "file://templates/db.yaml",
            "--change-set-type", "UPDATE",
        ]

    def test_cfn_create_changeset_type_create(self):
        argv = ia.build_cfn_create_changeset_argv(
            stack_name="newstack", change_set_name="cs1",
            template_path="t.yaml", change_set_type="CREATE",
        )
        assert argv[-2:] == ["--change-set-type", "CREATE"]

    def test_cfn_create_rejects_bad_change_set_type(self):
        with pytest.raises(ValueError):
            ia.build_cfn_create_changeset_argv(
                stack_name="s", change_set_name="c",
                template_path="t.yaml", change_set_type="DELETE",
            )

    def test_cfn_execute_changeset_exact_argv_arn_is_data(self):
        argv = ia.build_cfn_execute_changeset_argv(
            stack_name="prod-data", change_set_id=_VALID_ARN
        )
        assert argv == [
            "aws", "cloudformation", "execute-change-set",
            "--stack-name", "prod-data",
            "--change-set-name", _VALID_ARN,
        ]
        assert argv[0] == "aws"

    def test_cfn_builders_expose_no_shell_parameter(self):
        for fn in (ia.build_cfn_create_changeset_argv, ia.build_cfn_execute_changeset_argv):
            assert "shell" not in inspect.signature(fn).parameters


# ---------------------------------------------------------------------------
# Identifier validation / anti-injection + dedicated ARN grammar
# ---------------------------------------------------------------------------


class TestIdentifierValidation:
    @pytest.mark.parametrize("bad", ["../etc/passwd", "a;rm -rf", "a|b", "-rf", "a b", "s3://x/y"])
    def test_tf_plan_out_path_injection_rejected(self, bad):
        with pytest.raises(ValueError):
            ia.build_tf_plan_argv(out_path=bad)

    @pytest.mark.parametrize("bad", ["../../tfplan", "plan;evil", "-flag", "two words"])
    def test_tf_apply_plan_file_injection_rejected(self, bad):
        with pytest.raises(ValueError):
            ia.build_tf_apply_argv(plan_file=bad)

    @pytest.mark.parametrize("bad", ["-stack", "st;ack", "a b", "9starts-digit-bad" * 20, "has_underscore"])
    def test_cfn_stack_name_injection_rejected(self, bad):
        with pytest.raises(ValueError):
            ia.build_cfn_create_changeset_argv(
                stack_name=bad, change_set_name="cs", template_path="t.yaml"
            )

    def test_cfn_stack_name_grammar_rejects_a_valid_arn(self):
        # The stricter stack-name grammar forbids ':' and '/', so an ARN is rejected.
        with pytest.raises(ValueError):
            ia.build_cfn_execute_changeset_argv(stack_name=_VALID_ARN, change_set_id=_VALID_ARN)

    def test_cfn_arn_grammar_accepts_valid_arn(self):
        # The dedicated ARN grammar accepts an ARN containing ':' and '/'.
        argv = ia.build_cfn_execute_changeset_argv(stack_name="prod-data", change_set_id=_VALID_ARN)
        assert argv[-1] == _VALID_ARN

    @pytest.mark.parametrize("bad", [
        "not-an-arn",
        "prod-data",  # a valid stack name is NOT a valid ARN
        "arn:aws:cloudformation:us-east-1:123:changeSet/x/short",  # bad account/uuid
        "arn:aws:s3:::bucket/key",  # wrong service
        "-arn:aws:cloudformation:us-east-1:123456789012:changeSet/x/9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
    ])
    def test_cfn_change_set_id_rejects_non_arn(self, bad):
        with pytest.raises(ValueError):
            ia.build_cfn_execute_changeset_argv(stack_name="prod-data", change_set_id=bad)

    def test_two_grammars_are_distinct(self):
        # A value accepted by the ARN grammar is rejected by the stack-name grammar.
        ia._validate_change_set_id(_VALID_ARN)  # accepted
        with pytest.raises(ValueError):
            ia._validate_cfn_name(_VALID_ARN, "stack_name")  # rejected


# ---------------------------------------------------------------------------
# plan_hash
# ---------------------------------------------------------------------------


class TestPlanHash:
    def test_tf_binary_bytes_hash_is_sha256_hex(self):
        h = ia.plan_hash(b"binary tfplan v1")
        assert isinstance(h, str) and len(h) == 64
        assert h == ia.plan_hash(b"binary tfplan v1")  # deterministic

    def test_tf_one_byte_change_changes_hash(self):
        assert ia.plan_hash(b"binary tfplan v1") != ia.plan_hash(b"binary tfplan v2")

    def test_plan_hash_rejects_non_bytes(self):
        with pytest.raises(TypeError):
            ia.plan_hash("not-bytes")  # type: ignore[arg-type]

    def test_cfn_full_response_binding_includes_arn_and_stack(self):
        desc = _load_json("cfn_describe_changeset.json")
        h1 = ia.plan_hash(ia.canonical_cfn_plan_bytes(desc))
        # Replay against a DIFFERENT change-set ARN -> different hash (ARN is inside).
        desc2 = json.loads(json.dumps(desc))
        desc2["ChangeSetId"] = desc2["ChangeSetId"].replace("my-change-set", "other-change-set")
        assert ia.plan_hash(ia.canonical_cfn_plan_bytes(desc2)) != h1
        # Replay against a DIFFERENT target stack -> different hash (StackName inside).
        desc3 = json.loads(json.dumps(desc))
        desc3["StackName"] = "dev-data"
        assert ia.plan_hash(ia.canonical_cfn_plan_bytes(desc3)) != h1

    def test_canonical_cfn_bytes_deterministic_regardless_of_key_order(self):
        a = {"StackName": "s", "ChangeSetId": "x", "Changes": []}
        b = {"Changes": [], "ChangeSetId": "x", "StackName": "s"}
        assert ia.canonical_cfn_plan_bytes(a) == ia.canonical_cfn_plan_bytes(b)


# ---------------------------------------------------------------------------
# approval_verdict
# ---------------------------------------------------------------------------


class TestApprovalVerdict:
    def test_approved_on_match(self):
        h = ia.plan_hash(b"plan-A")
        v = ia.approval_verdict(computed_plan_hash=h, approval={"approvedPlanHash": h})
        assert v["state"] == "APPROVED"

    def test_mismatch_is_invalidated_never_passes(self):
        h = ia.plan_hash(b"plan-A")
        other = ia.plan_hash(b"plan-B")
        v = ia.approval_verdict(computed_plan_hash=h, approval={"approvedPlanHash": other})
        assert v["state"] == "APPROVAL_INVALIDATED"
        assert v["state"] != "APPROVED"

    def test_one_byte_replan_invalidates_approval(self):
        approved = ia.plan_hash(b"binary tfplan v1")
        # operator approved v1; a re-plan produced v2 (one byte differs)
        recomputed = ia.plan_hash(b"binary tfplan v2")
        v = ia.approval_verdict(computed_plan_hash=recomputed, approval={"approvedPlanHash": approved})
        assert v["state"] == "APPROVAL_INVALIDATED"

    def test_no_approval_is_pending(self):
        assert ia.approval_verdict(computed_plan_hash="abc", approval=None)["state"] == "PENDING_PLAN"

    def test_malformed_approval_is_blocked(self):
        v = ia.approval_verdict(computed_plan_hash="abc", approval={"noHashHere": 1})
        assert v["state"] == "BLOCKED"


# ---------------------------------------------------------------------------
# capability_gate_verdict
# ---------------------------------------------------------------------------


class TestCapabilityGate:
    def _hash(self) -> str:
        return ia.plan_hash(b"plan-with-stateful-destroy")

    def _stateful_addrs(self) -> list[str]:
        return [e["address"] for e in _tf_destructive() if e["stateful"]]

    def test_no_stateful_destroy_not_required(self):
        non_stateful = [{"address": "aws_instance.web", "stateful": False}]
        v = ia.capability_gate_verdict(
            computed_plan_hash=self._hash(), destructive=non_stateful, grant=None
        )
        assert v["state"] == "NOT_REQUIRED"

    def test_stateful_destroy_no_grant_requires_capability(self):
        v = ia.capability_gate_verdict(
            computed_plan_hash=self._hash(), destructive=_tf_destructive(), grant=None
        )
        assert v["state"] == "CAPABILITY_REQUIRED"
        assert "aws_db_instance.primary" in v["statefulAddresses"]

    def test_plan_approval_alone_never_authorizes_empty_set(self):
        h = self._hash()
        grant = ia.build_capability_grant(
            approved_plan_hash=h, authorized_stateful_addresses=[], confirmed_token="tok"
        )
        v = ia.capability_gate_verdict(
            computed_plan_hash=h, destructive=_tf_destructive(), grant=grant
        )
        assert v["state"] == "CAPABILITY_REQUIRED"

    def test_matching_hash_but_omits_address_still_required(self):
        h = self._hash()
        # authorizes a DIFFERENT address, not the stateful db instance
        grant = ia.build_capability_grant(
            approved_plan_hash=h,
            authorized_stateful_addresses=["aws_db_instance.SOMEOTHER"],
            confirmed_token="tok",
        )
        v = ia.capability_gate_verdict(
            computed_plan_hash=h, destructive=_tf_destructive(), grant=grant
        )
        assert v["state"] == "CAPABILITY_REQUIRED"

    def test_missing_token_still_required(self):
        h = self._hash()
        grant = {
            "approvedPlanHash": h,
            "authorizedStatefulAddresses": self._stateful_addrs(),
            # no confirmedToken
        }
        v = ia.capability_gate_verdict(
            computed_plan_hash=h, destructive=_tf_destructive(), grant=grant
        )
        assert v["state"] == "CAPABILITY_REQUIRED"

    def test_self_binding_mismatched_grant_hash_never_clears(self):
        """A STALE grant (valid set + token) bound to a DIFFERENT plan must NOT clear."""
        h = self._hash()
        stale = ia.build_capability_grant(
            approved_plan_hash=ia.plan_hash(b"a-different-prior-plan"),
            authorized_stateful_addresses=self._stateful_addrs(),
            confirmed_token="tok",
        )
        v = ia.capability_gate_verdict(
            computed_plan_hash=h, destructive=_tf_destructive(), grant=stale
        )
        assert v["state"] == "CAPABILITY_REQUIRED"
        assert "approvedPlanHash" in v["missing"]

    def test_all_three_conditions_clears(self):
        h = self._hash()
        grant = ia.build_capability_grant(
            approved_plan_hash=h,
            authorized_stateful_addresses=self._stateful_addrs(),
            confirmed_token="typed-confirm",
        )
        v = ia.capability_gate_verdict(
            computed_plan_hash=h, destructive=_tf_destructive(), grant=grant
        )
        assert v["state"] == "CAPABILITY_CLEARED"

    def test_cfn_stateful_family_keys_off_logical_id(self):
        h = self._hash()
        dz = _cfn_destructive()
        v = ia.capability_gate_verdict(computed_plan_hash=h, destructive=dz, grant=None)
        assert v["state"] == "CAPABILITY_REQUIRED"
        assert "PrimaryDatabase" in v["statefulAddresses"]

    def test_malformed_destructive_entry_fails_closed(self):
        with pytest.raises(ValueError):
            ia.capability_gate_verdict(
                computed_plan_hash="h", destructive=["not-a-dict"], grant=None  # type: ignore[list-item]
            )


# ---------------------------------------------------------------------------
# apply_state
# ---------------------------------------------------------------------------


class TestApplyState:
    def _h(self) -> str:
        return ia.plan_hash(b"plan-X")

    def _cleared_grant(self) -> dict:
        return ia.build_capability_grant(
            approved_plan_hash=self._h(),
            authorized_stateful_addresses=[e["address"] for e in _tf_destructive() if e["stateful"]],
            confirmed_token="tok",
        )

    def test_drift_abort_regardless_of_approval_and_grant(self):
        st = ia.apply_state(
            computed_plan_hash=self._h(),
            approval={"approvedPlanHash": self._h()},
            destructive=_tf_destructive(),
            grant=self._cleared_grant(),
            drift_detected=True,
            creds_present=True,
        )
        assert st == "DRIFT_ABORT"

    def test_pending_plan_when_no_hash(self):
        st = ia.apply_state(
            computed_plan_hash="", approval=None, destructive=[], grant=None,
            drift_detected=False, creds_present=True,
        )
        assert st == "PENDING_PLAN"

    def test_plan_captured_when_no_approval(self):
        st = ia.apply_state(
            computed_plan_hash=self._h(), approval=None, destructive=[], grant=None,
            drift_detected=False, creds_present=True,
        )
        assert st == "PLAN_CAPTURED"

    def test_approval_invalidated(self):
        st = ia.apply_state(
            computed_plan_hash=self._h(),
            approval={"approvedPlanHash": ia.plan_hash(b"other")},
            destructive=[], grant=None, drift_detected=False, creds_present=True,
        )
        assert st == "APPROVAL_INVALIDATED"

    def test_capability_required_when_stateful_destroy_without_grant(self):
        st = ia.apply_state(
            computed_plan_hash=self._h(),
            approval={"approvedPlanHash": self._h()},
            destructive=_tf_destructive(), grant=None,
            drift_detected=False, creds_present=True,
        )
        assert st == "CAPABILITY_REQUIRED"

    def test_creds_absent_when_all_gates_pass_but_no_creds(self):
        st = ia.apply_state(
            computed_plan_hash=self._h(),
            approval={"approvedPlanHash": self._h()},
            destructive=_tf_destructive(), grant=self._cleared_grant(),
            drift_detected=False, creds_present=False,
        )
        assert st == "CREDS_ABSENT"

    def test_ready_deferred_when_all_gates_pass(self):
        st = ia.apply_state(
            computed_plan_hash=self._h(),
            approval={"approvedPlanHash": self._h()},
            destructive=_tf_destructive(), grant=self._cleared_grant(),
            drift_detected=False, creds_present=True,
        )
        assert st == "READY_DEFERRED"

    def test_ready_deferred_non_destructive_no_grant_needed(self):
        st = ia.apply_state(
            computed_plan_hash=self._h(),
            approval={"approvedPlanHash": self._h()},
            destructive=[], grant=None, drift_detected=False, creds_present=True,
        )
        assert st == "READY_DEFERRED"


# ---------------------------------------------------------------------------
# schema / artifact / audit
# ---------------------------------------------------------------------------


class TestSchemaArtifactAudit:
    def test_schema_required_keys_and_state_enum(self):
        schema = ia.iac_apply_schema()
        for key in ("schemaVersion", "kind", "capturedPlanRef", "planHash",
                    "state", "destructive", "audit", "generatedAt"):
            assert key in schema["required"]
        for st in ("READY_DEFERRED", "CAPABILITY_REQUIRED", "APPROVAL_INVALIDATED",
                   "DRIFT_ABORT", "CREDS_ABSENT", "BLOCKED", "PENDING_PLAN", "PLAN_CAPTURED"):
            assert st in schema["properties"]["state"]["enum"]

    def test_build_artifact_matches_schema_required(self):
        art = ia.build_iac_apply_artifact(
            kind="terraform", captured_plan_ref="tfplan",
            plan_hash=ia.plan_hash(b"x"), state="READY_DEFERRED",
            destructive=_tf_destructive(), audit=[],
        )
        for key in ia.iac_apply_schema()["required"]:
            assert key in art

    def test_emit_load_round_trip(self, tmp_path):
        art = ia.build_iac_apply_artifact(
            kind="cloudformation", captured_plan_ref=_VALID_ARN,
            plan_hash=ia.plan_hash(b"x"), state="CAPABILITY_REQUIRED",
        )
        dest = tmp_path / ".kata" / "iac-apply.json"
        assert not dest.parent.exists()
        ia.emit_iac_apply(art, dest)
        loaded = ia.load_iac_apply(dest)
        assert loaded["state"] == "CAPABILITY_REQUIRED"
        assert loaded["kind"] == "cloudformation"

    def test_load_missing_returns_none(self, tmp_path):
        assert ia.load_iac_apply(tmp_path / "nope.json") is None

    def test_audit_record_shape(self):
        rec = ia.build_apply_audit_record(
            task_id="T1", kind="terraform", plan_hash="abc", state="READY_DEFERRED",
            actor="operator", ts="2026-06-27T00:00:00Z", rationale="approved + granted",
        )
        for key in ("taskId", "kind", "planHash", "state", "actor", "ts", "rationale"):
            assert key in rec

    def test_approval_artifact_shape(self):
        h = ia.plan_hash(b"x")
        grant = ia.build_capability_grant(
            approved_plan_hash=h, authorized_stateful_addresses=["a"], confirmed_token="t"
        )
        art = ia.build_approval_artifact(approved_plan_hash=h, grant=grant)
        assert art["approvedPlanHash"] == h
        assert art["grant"]["confirmedToken"] == "t"

    def test_load_approval_round_trip(self, tmp_path):
        h = ia.plan_hash(b"x")
        art = ia.build_approval_artifact(approved_plan_hash=h)
        dest = tmp_path / "kata.iac-apply-approval.json"
        dest.write_text(json.dumps(art), encoding="utf-8")
        loaded = ia.load_approval(dest)
        assert loaded["approvedPlanHash"] == h

    def test_load_approval_absent_returns_none(self, tmp_path):
        assert ia.load_approval(tmp_path / "absent.json") is None


# ---------------------------------------------------------------------------
# run_apply — the DEFERRED execution seam (the creds wall)
# ---------------------------------------------------------------------------


class TestRunApplySeam:
    def test_run_apply_raises_not_implemented(self):
        with pytest.raises(NotImplementedError):
            ia.run_apply()

    def test_run_apply_raises_even_with_args(self):
        with pytest.raises(NotImplementedError):
            ia.run_apply(approval={"approvedPlanHash": "x"}, grant={"confirmedToken": "t"}, creds=True)

    def test_run_apply_docstring_states_limitation(self):
        doc = (ia.run_apply.__doc__ or "").lower()
        assert "n=0-live" in doc or "deferred" in doc
        assert "creds" in doc


# ---------------------------------------------------------------------------
# exec-safety: no subprocess / eval / exec / shell=True (mirror drift_gate)
# ---------------------------------------------------------------------------


class TestExecSafety:
    def _source(self) -> str:
        return (_TOOLS / "iac_apply.py").read_text(encoding="utf-8")

    def test_no_eval(self):
        import re
        hits = [m.group() for m in re.finditer(r"\beval\s*\(", self._source())]
        assert not hits, f"eval() call found in iac_apply.py: {hits}"

    def test_no_exec(self):
        import re
        hits = [m.group() for m in re.finditer(r"\bexec\s*\(", self._source())]
        assert not hits, f"exec() call found in iac_apply.py: {hits}"

    def test_no_subprocess_import(self):
        import re
        hits = [
            m.group()
            for m in re.finditer(r"^\s*(?:import|from)\s+subprocess\b", self._source(), re.MULTILINE)
        ]
        assert not hits, f"subprocess import found in iac_apply.py: {hits}"

    def test_no_shell_true(self):
        assert "shell=True" not in self._source()

    def test_pure_ast_parseable(self):
        ast.parse(self._source())

    def test_no_subprocess_call_node(self):
        """AST: no subprocess.* / os.system / popen call anywhere."""
        tree = ast.parse(self._source())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    assert node.func.id not in {"eval", "exec"}
                if isinstance(node.func, ast.Attribute):
                    assert node.func.attr not in {"system", "popen", "run", "Popen", "call"}


# ---------------------------------------------------------------------------
# Mutation non-vacuity proofs (a-f) — spawn real subprocess via prove_non_vacuous
# ---------------------------------------------------------------------------


class TestMutationProof:
    """Each test removes exactly one load-bearing line and proves a guard goes red.

    Plan mutation targets: (a) approval equality, (b) capability containment,
    (c) the self-binding grant-hash equality, (d) drift -> DRIFT_ABORT,
    (e) the stateful:True filter feed, (f) the run_apply raise seam.
    """

    def _source(self) -> str:
        return str(_TOOLS / "iac_apply.py")

    def _test_cmd(self, test_spec: str) -> str:
        return (
            f'cd /d "{_TOOLS}" && '
            f"{sys.executable} -m pytest "
            f'"tests/test_iac_apply.py::{test_spec}" -q --tb=no'
        )

    def _prove(self, asserted_line: str, test_spec: str):
        import mutation_run
        verdict = mutation_run.prove_non_vacuous(self._source(), asserted_line, self._test_cmd(test_spec))
        assert verdict["testWentRed"], f"mutation did not make {test_spec} go red: {asserted_line!r}"
        assert verdict["nonVacuous"], f"{test_spec} did not catch removal of: {asserted_line!r}"

    def test_mutation_a_approval_equality(self):
        self._prove(
            "    matched = approved == computed_plan_hash",
            "TestApprovalVerdict::test_approved_on_match",
        )

    def test_mutation_b_capability_containment(self):
        self._prove(
            '        missing.append("authorizedStatefulAddresses")',
            "TestCapabilityGate::test_matching_hash_but_omits_address_still_required",
        )

    def test_mutation_c_self_binding_grant_hash(self):
        self._prove(
            '        missing.append("approvedPlanHash")',
            "TestCapabilityGate::test_self_binding_mismatched_grant_hash_never_clears",
        )

    def test_mutation_d_drift_abort_branch(self):
        self._prove(
            "        return _DRIFT_ABORT",
            "TestApplyState::test_drift_abort_regardless_of_approval_and_grant",
        )

    def test_mutation_e_stateful_filter_feed(self):
        self._prove(
            "            addrs.add(addr)",
            "TestCapabilityGate::test_stateful_destroy_no_grant_requires_capability",
        )

    def test_mutation_f_run_apply_seam(self):
        self._prove(
            "    raise NotImplementedError(_RUN_APPLY_MSG)",
            "TestRunApplySeam::test_run_apply_raises_not_implemented",
        )
