"""Tests for iac_detect.py — TDD-first (written before implementation).

Coverage (DESIGN §6 acceptance — all acceptance criteria exercised):
- classify_file: .tf → "terraform"  [§6 AC1]
- classify_file: .hcl → "terraform"
- classify_file: .tf.json → "terraform"
- classify_file: CFN YAML with AWSTemplateFormatVersion → "cloudformation"  [§6 AC1]
- classify_file: CFN YAML with no AWSTemplateFormatVersion but Type: AWS:: (belt-and-suspenders N1) → "cloudformation"
- classify_file: CFN JSON .template → "cloudformation"
- classify_file: cdk.json by name → "cdk"  [§6 AC1]
- classify_file: path under cdk.out/ → "cdk"
- classify_file: non-IaC .yaml (no AWS:: marker) → None (false-positive guard)  [§6 AC1]
- classify_file: non-IaC .json (no AWS:: marker) → None
- classify_task: mixed set → set of kinds  [§6 AC1]
- classify_task: empty set → empty set  [§6 AC1]
- force_classify: override wins over auto-detection  [§6 AC1]
- force_classify: no match → None
- scan_tf_plan: ["delete"] → flagged  [§6 AC2]
- scan_tf_plan: ["delete","create"] → flagged (replace)  [§6 AC2]
- scan_tf_plan: ["create","delete"] → flagged (replace)  [§6 AC2]
- scan_tf_plan: clean plan → []  [§6 AC2]
- scan_tf_plan: stateful detection (aws_s3_bucket, aws_elasticache_*, etc.)  [§6 AC2]
- scan_tf_plan: malformed plan (missing resource_changes) → ValueError  [mutation proof target]
- scan_cfn_changeset: Action=Remove → flagged  [§6 AC2]
- scan_cfn_changeset: Replacement=True → flagged  [§6 AC2]
- scan_cfn_changeset: Replacement=Conditional → flagged  [§6 AC2]
- scan_cfn_changeset: PolicyAction=Delete → flagged  [§6 AC2]
- scan_cfn_changeset: PolicyAction=ReplaceAndDelete → flagged  [§6 AC2]
- scan_cfn_changeset: clean changeset → []
- scan_cfn_changeset: stateful detection (AWS::RDS::*, AWS::DynamoDB::*, etc.)
- scan_cfn_changeset: malformed changeset (missing Changes) → ValueError
- CWE-23: classify_file with .. path → ValueError
"""

from __future__ import annotations

import pytest

import iac_detect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tf_resource(address, rtype, actions, action_reason=""):
    """Build a resource_changes entry for TF plan fixtures."""
    entry = {
        "address": address,
        "type": rtype,
        "change": {"actions": actions},
    }
    if action_reason:
        entry["change"]["action_reason"] = action_reason
    return entry


def _cfn_change(logical_id, resource_type, action="Modify",
                replacement="False", policy_action=None):
    """Build a Changes entry for CFN changeset fixtures."""
    rc = {
        "LogicalResourceId": logical_id,
        "ResourceType": resource_type,
        "Action": action,
        "Replacement": replacement,
    }
    if policy_action is not None:
        rc["PolicyAction"] = policy_action
    return {"ResourceChange": rc}


# ---------------------------------------------------------------------------
# classify_file — extension-based (terraform)
# ---------------------------------------------------------------------------

class TestClassifyFileTerraform:
    def test_tf_extension(self, tmp_path):
        f = tmp_path / "main.tf"
        f.write_text("resource \"aws_s3_bucket\" \"b\" {}\n", encoding="utf-8")
        assert iac_detect.classify_file(str(f)) == "terraform"

    def test_hcl_extension(self, tmp_path):
        f = tmp_path / "vars.hcl"
        f.write_text("variable \"name\" {}\n", encoding="utf-8")
        assert iac_detect.classify_file(str(f)) == "terraform"

    def test_tf_json_extension(self, tmp_path):
        f = tmp_path / "override.tf.json"
        f.write_text('{"resource": {}}', encoding="utf-8")
        assert iac_detect.classify_file(str(f)) == "terraform"

    def test_content_kwarg_shortcircuits_read(self):
        # Path need not exist when content is supplied
        assert iac_detect.classify_file("/nonexistent/main.tf", content="anything") == "terraform"


# ---------------------------------------------------------------------------
# classify_file — content-based (cloudformation)
# ---------------------------------------------------------------------------

class TestClassifyFileCFN:
    CFN_VERSION_YAML = """\
AWSTemplateFormatVersion: "2010-09-09"
Resources:
  Bucket:
    Type: AWS::S3::Bucket
"""
    CFN_NO_VERSION_YAML = """\
Description: A template without AWSTemplateFormatVersion
Resources:
  Queue:
    Type: AWS::SQS::Queue
"""
    NON_IAC_YAML = """\
name: my-app
version: 1.0.0
services:
  web:
    image: nginx
"""

    def test_yaml_with_awstemplateformatversion(self, tmp_path):
        f = tmp_path / "stack.yaml"
        f.write_text(self.CFN_VERSION_YAML, encoding="utf-8")
        assert iac_detect.classify_file(str(f)) == "cloudformation"

    def test_yml_with_awstemplateformatversion(self, tmp_path):
        f = tmp_path / "stack.yml"
        f.write_text(self.CFN_VERSION_YAML, encoding="utf-8")
        assert iac_detect.classify_file(str(f)) == "cloudformation"

    def test_yaml_no_version_but_type_aws_belt_and_suspenders(self, tmp_path):
        """N1 belt-and-suspenders: Type: AWS:: without AWSTemplateFormatVersion must still classify."""
        f = tmp_path / "fragment.yaml"
        f.write_text(self.CFN_NO_VERSION_YAML, encoding="utf-8")
        assert iac_detect.classify_file(str(f)) == "cloudformation"

    def test_json_with_type_aws(self, tmp_path):
        f = tmp_path / "stack.json"
        f.write_text('{"Resources": {"Bucket": {"Type": "AWS::S3::Bucket"}}}', encoding="utf-8")
        assert iac_detect.classify_file(str(f)) == "cloudformation"

    def test_template_extension(self, tmp_path):
        f = tmp_path / "deploy.template"
        f.write_text(self.CFN_VERSION_YAML, encoding="utf-8")
        assert iac_detect.classify_file(str(f)) == "cloudformation"

    def test_content_kwarg(self):
        """Pass content directly — path need not exist."""
        assert iac_detect.classify_file(
            "/nonexistent/stack.yaml",
            content=self.CFN_VERSION_YAML,
        ) == "cloudformation"

    def test_non_iac_yaml_returns_none(self, tmp_path):
        """False-positive guard: plain YAML with no AWS:: markers → None."""
        f = tmp_path / "config.yaml"
        f.write_text(self.NON_IAC_YAML, encoding="utf-8")
        assert iac_detect.classify_file(str(f)) is None

    def test_non_iac_json_returns_none(self, tmp_path):
        f = tmp_path / "package.json"
        f.write_text('{"name": "my-app", "version": "1.0.0"}', encoding="utf-8")
        assert iac_detect.classify_file(str(f)) is None

    def test_aws_single_colon_no_false_positive(self):
        """'Type: AWS:' (one colon only) must NOT trigger cloudformation."""
        content = "Type: AWS:notmatch"
        assert iac_detect.classify_file("/fake/stack.yaml", content=content) is None

    def test_type_aws_inline_spacing(self):
        """Regex must handle varying whitespace: 'Type:AWS::' and 'Type:  AWS::'."""
        assert iac_detect.classify_file(
            "/fake/s.yaml", content="Type:AWS::S3::Bucket"
        ) == "cloudformation"
        assert iac_detect.classify_file(
            "/fake/s.yaml", content="Type:  AWS::EC2::Instance"
        ) == "cloudformation"


# ---------------------------------------------------------------------------
# classify_file — CDK
# ---------------------------------------------------------------------------

class TestClassifyFileCDK:
    def test_cdk_json_by_name(self, tmp_path):
        f = tmp_path / "cdk.json"
        f.write_text('{"app": "npx ts-node bin/app.ts"}', encoding="utf-8")
        assert iac_detect.classify_file(str(f)) == "cdk"

    def test_path_under_cdk_out(self, tmp_path):
        cdk_out = tmp_path / "cdk.out"
        cdk_out.mkdir()
        f = cdk_out / "MyStack.template.json"
        f.write_text('{"Resources": {"Bucket": {"Type": "AWS::S3::Bucket"}}}', encoding="utf-8")
        # Even though content looks CFN, the path location → "cdk"
        assert iac_detect.classify_file(str(f)) == "cdk"

    def test_content_kwarg_cdk_json_name(self):
        assert iac_detect.classify_file("/project/cdk.json", content="{}") == "cdk"


# ---------------------------------------------------------------------------
# classify_task
# ---------------------------------------------------------------------------

class TestClassifyTask:
    def test_empty_owned_files(self):
        assert iac_detect.classify_task([]) == set()

    def test_all_none(self, tmp_path):
        f = tmp_path / "app.py"
        f.write_text("print('hello')", encoding="utf-8")
        assert iac_detect.classify_task([str(f)]) == set()

    def test_single_terraform(self, tmp_path):
        f = tmp_path / "main.tf"
        f.write_text("resource \"aws_s3_bucket\" \"b\" {}\n", encoding="utf-8")
        assert iac_detect.classify_task([str(f)]) == {"terraform"}

    def test_mixed_terraform_and_cloudformation(self, tmp_path):
        tf = tmp_path / "main.tf"
        tf.write_text("resource \"aws_vpc\" \"v\" {}\n", encoding="utf-8")
        cfn = tmp_path / "stack.yaml"
        cfn.write_text("AWSTemplateFormatVersion: '2010-09-09'\nResources: {}\n", encoding="utf-8")
        other = tmp_path / "README.md"
        other.write_text("# docs", encoding="utf-8")
        result = iac_detect.classify_task([str(tf), str(cfn), str(other)])
        assert result == {"terraform", "cloudformation"}

    def test_returns_set_not_list(self, tmp_path):
        f = tmp_path / "main.tf"
        f.write_text("", encoding="utf-8")
        result = iac_detect.classify_task([str(f), str(f)])
        assert isinstance(result, set)
        assert result == {"terraform"}


# ---------------------------------------------------------------------------
# force_classify
# ---------------------------------------------------------------------------

class TestForceClassify:
    def test_exact_path_override(self):
        overrides = {"infra/special.yaml": "cloudformation"}
        assert iac_detect.force_classify("infra/special.yaml", overrides) == "cloudformation"

    def test_glob_pattern_override(self):
        overrides = {"infra/**/*.yaml": "cloudformation"}
        assert iac_detect.force_classify("infra/dev/stack.yaml", overrides) == "cloudformation"

    def test_no_match_returns_none(self):
        overrides = {"infra/**/*.tf": "terraform"}
        assert iac_detect.force_classify("src/app.py", overrides) is None

    def test_empty_overrides_returns_none(self):
        assert iac_detect.force_classify("anything.tf", {}) is None

    def test_wildcard_star_pattern(self):
        overrides = {"*.hcl": "terraform"}
        assert iac_detect.force_classify("providers.hcl", overrides) == "terraform"


# ---------------------------------------------------------------------------
# scan_tf_plan — destructive detection
# ---------------------------------------------------------------------------

class TestScanTfPlan:
    def _plan(self, *changes):
        return {"resource_changes": list(changes)}

    def test_empty_resource_changes(self):
        assert iac_detect.scan_tf_plan(self._plan()) == []

    def test_no_op_action(self):
        plan = self._plan(_tf_resource("aws_vpc.main", "aws_vpc", ["no-op"]))
        assert iac_detect.scan_tf_plan(plan) == []

    def test_create_only(self):
        plan = self._plan(_tf_resource("aws_s3_bucket.b", "aws_s3_bucket", ["create"]))
        assert iac_detect.scan_tf_plan(plan) == []

    def test_update_only(self):
        plan = self._plan(_tf_resource("aws_s3_bucket.b", "aws_s3_bucket", ["update"]))
        assert iac_detect.scan_tf_plan(plan) == []

    def test_delete_flagged(self):
        plan = self._plan(
            _tf_resource("aws_vpc.old", "aws_vpc", ["delete"])
        )
        results = iac_detect.scan_tf_plan(plan)
        assert len(results) == 1
        assert results[0]["address"] == "aws_vpc.old"
        assert results[0]["actions"] == ["delete"]
        assert "delete" in results[0]["actions"]

    def test_delete_create_flagged(self):
        """['delete','create'] is a replace — must be flagged."""
        plan = self._plan(
            _tf_resource("aws_db_instance.db", "aws_db_instance", ["delete", "create"])
        )
        results = iac_detect.scan_tf_plan(plan)
        assert len(results) == 1
        assert results[0]["address"] == "aws_db_instance.db"

    def test_create_delete_flagged(self):
        """['create','delete'] is also a replace (create-before-destroy) — must be flagged."""
        plan = self._plan(
            _tf_resource("aws_db_instance.db", "aws_db_instance", ["create", "delete"])
        )
        results = iac_detect.scan_tf_plan(plan)
        assert len(results) == 1

    def test_action_reason_preserved(self):
        plan = self._plan(
            _tf_resource(
                "aws_instance.web[0]", "aws_instance",
                ["delete"], "delete_because_count_index"
            )
        )
        results = iac_detect.scan_tf_plan(plan)
        assert results[0]["action_reason"] == "delete_because_count_index"

    def test_action_reason_default_empty(self):
        plan = self._plan(_tf_resource("aws_vpc.v", "aws_vpc", ["delete"]))
        results = iac_detect.scan_tf_plan(plan)
        assert results[0]["action_reason"] == ""

    def test_clean_plan_returns_empty(self):
        """A plan with only create/update/no-op → no destructive flags."""
        plan = self._plan(
            _tf_resource("aws_s3_bucket.b", "aws_s3_bucket", ["create"]),
            _tf_resource("aws_vpc.v", "aws_vpc", ["update"]),
            _tf_resource("aws_iam_role.r", "aws_iam_role", ["no-op"]),
        )
        assert iac_detect.scan_tf_plan(plan) == []

    def test_stateful_aws_db_instance(self):
        plan = self._plan(
            _tf_resource("aws_db_instance.main", "aws_db_instance", ["delete"])
        )
        results = iac_detect.scan_tf_plan(plan)
        assert results[0]["stateful"] is True

    def test_stateful_aws_rds_cluster(self):
        plan = self._plan(
            _tf_resource("aws_rds_cluster.c", "aws_rds_cluster", ["delete"])
        )
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_dynamodb_table(self):
        plan = self._plan(
            _tf_resource("aws_dynamodb_table.t", "aws_dynamodb_table", ["delete"])
        )
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_s3_bucket(self):
        plan = self._plan(
            _tf_resource("aws_s3_bucket.b", "aws_s3_bucket", ["delete"])
        )
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_ebs_volume(self):
        plan = self._plan(
            _tf_resource("aws_ebs_volume.v", "aws_ebs_volume", ["delete"])
        )
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_elasticache_prefix(self):
        plan = self._plan(
            _tf_resource("aws_elasticache_cluster.c", "aws_elasticache_cluster", ["delete"])
        )
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_redshift_prefix(self):
        plan = self._plan(
            _tf_resource("aws_redshift_cluster.r", "aws_redshift_cluster", ["delete"])
        )
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_non_stateful_resource(self):
        plan = self._plan(
            _tf_resource("aws_vpc.v", "aws_vpc", ["delete"])
        )
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is False

    def test_multiple_resources_only_destructive_returned(self):
        plan = self._plan(
            _tf_resource("aws_s3_bucket.b", "aws_s3_bucket", ["create"]),
            _tf_resource("aws_db_instance.db", "aws_db_instance", ["delete"]),
            _tf_resource("aws_vpc.v", "aws_vpc", ["update"]),
        )
        results = iac_detect.scan_tf_plan(plan)
        assert len(results) == 1
        assert results[0]["address"] == "aws_db_instance.db"

    def test_result_contains_type_field(self):
        plan = self._plan(
            _tf_resource("aws_s3_bucket.b", "aws_s3_bucket", ["delete"])
        )
        r = iac_detect.scan_tf_plan(plan)[0]
        assert r["type"] == "aws_s3_bucket"

    # --- malformed plan → ValueError (NOT silent return []) ---

    def test_missing_resource_changes_raises_value_error(self):
        """A plan missing 'resource_changes' must raise ValueError — callers must FAIL, not silently pass."""
        with pytest.raises(ValueError, match="resource_changes"):
            iac_detect.scan_tf_plan({})

    def test_resource_changes_not_list_raises_value_error(self):
        with pytest.raises(ValueError):
            iac_detect.scan_tf_plan({"resource_changes": "not-a-list"})

    def test_entry_missing_change_raises_value_error(self):
        """An entry missing the 'change' key must surface as ValueError."""
        plan = {"resource_changes": [{"address": "aws_vpc.v", "type": "aws_vpc"}]}
        with pytest.raises(ValueError):
            iac_detect.scan_tf_plan(plan)

    def test_entry_missing_actions_raises_value_error(self):
        """An entry with 'change' but no 'actions' must raise ValueError."""
        plan = {"resource_changes": [
            {"address": "aws_vpc.v", "type": "aws_vpc", "change": {}}
        ]}
        with pytest.raises(ValueError):
            iac_detect.scan_tf_plan(plan)


# ---------------------------------------------------------------------------
# scan_cfn_changeset — destructive detection
# ---------------------------------------------------------------------------

class TestScanCfnChangeset:
    def _desc(self, *changes):
        return {"Changes": list(changes)}

    def test_empty_changes(self):
        assert iac_detect.scan_cfn_changeset(self._desc()) == []

    def test_modify_no_replacement(self):
        desc = self._desc(_cfn_change("MyBucket", "AWS::S3::Bucket", "Modify", "False"))
        assert iac_detect.scan_cfn_changeset(desc) == []

    def test_action_remove_flagged(self):
        desc = self._desc(
            _cfn_change("OldQueue", "AWS::SQS::Queue", "Remove")
        )
        results = iac_detect.scan_cfn_changeset(desc)
        assert len(results) == 1
        assert results[0]["logicalId"] == "OldQueue"
        assert results[0]["action"] == "Remove"

    def test_replacement_true_flagged(self):
        desc = self._desc(
            _cfn_change("MyDB", "AWS::RDS::DBInstance", "Modify", "True")
        )
        results = iac_detect.scan_cfn_changeset(desc)
        assert len(results) == 1
        assert results[0]["replacement"] == "True"

    def test_replacement_conditional_flagged(self):
        desc = self._desc(
            _cfn_change("MyTable", "AWS::DynamoDB::Table", "Modify", "Conditional")
        )
        results = iac_detect.scan_cfn_changeset(desc)
        assert len(results) == 1
        assert results[0]["replacement"] == "Conditional"

    def test_policy_action_delete_flagged(self):
        desc = self._desc(
            _cfn_change("MyBucket", "AWS::S3::Bucket", "Remove", "True", "Delete")
        )
        results = iac_detect.scan_cfn_changeset(desc)
        assert len(results) == 1
        assert results[0]["policyAction"] == "Delete"

    def test_policy_action_replace_and_delete_flagged(self):
        desc = self._desc(
            _cfn_change("MyBucket", "AWS::S3::Bucket", "Modify", "True", "ReplaceAndDelete")
        )
        results = iac_detect.scan_cfn_changeset(desc)
        assert len(results) == 1
        assert results[0]["policyAction"] == "ReplaceAndDelete"

    def test_clean_changeset_returns_empty(self):
        """Modify with no replacement → nothing flagged."""
        desc = self._desc(
            _cfn_change("MyVPC", "AWS::EC2::VPC", "Modify", "False"),
            _cfn_change("MySubnet", "AWS::EC2::Subnet", "Add", "False"),
        )
        assert iac_detect.scan_cfn_changeset(desc) == []

    def test_result_has_all_fields(self):
        desc = self._desc(
            _cfn_change("MyDB", "AWS::RDS::DBInstance", "Remove")
        )
        r = iac_detect.scan_cfn_changeset(desc)[0]
        assert "logicalId" in r
        assert "resourceType" in r
        assert "action" in r
        assert "replacement" in r
        assert "policyAction" in r
        assert "stateful" in r

    # --- stateful detection ---

    def test_stateful_rds(self):
        desc = self._desc(_cfn_change("MyDB", "AWS::RDS::DBInstance", "Remove"))
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

    def test_stateful_rds_cluster(self):
        desc = self._desc(_cfn_change("Cluster", "AWS::RDS::DBCluster", "Remove"))
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

    def test_stateful_dynamodb(self):
        desc = self._desc(
            _cfn_change("MyTable", "AWS::DynamoDB::Table", "Modify", "True")
        )
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

    def test_stateful_s3_bucket(self):
        desc = self._desc(_cfn_change("MyBucket", "AWS::S3::Bucket", "Remove"))
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

    def test_stateful_elasticache(self):
        desc = self._desc(
            _cfn_change("Cache", "AWS::ElastiCache::CacheCluster", "Remove")
        )
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

    def test_stateful_redshift(self):
        desc = self._desc(
            _cfn_change("DW", "AWS::Redshift::Cluster", "Remove")
        )
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

    def test_non_stateful_resource(self):
        desc = self._desc(
            _cfn_change("MyQueue", "AWS::SQS::Queue", "Remove")
        )
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is False

    def test_multiple_only_destructive_returned(self):
        desc = self._desc(
            _cfn_change("MyVPC", "AWS::EC2::VPC", "Modify", "False"),
            _cfn_change("MyDB", "AWS::RDS::DBInstance", "Remove"),
        )
        results = iac_detect.scan_cfn_changeset(desc)
        assert len(results) == 1
        assert results[0]["logicalId"] == "MyDB"

    # --- malformed changeset → ValueError ---

    def test_missing_changes_raises_value_error(self):
        """A changeset dict missing 'Changes' must raise ValueError."""
        with pytest.raises(ValueError, match="Changes"):
            iac_detect.scan_cfn_changeset({})

    def test_changes_not_list_raises_value_error(self):
        with pytest.raises(ValueError):
            iac_detect.scan_cfn_changeset({"Changes": "bad"})

    def test_entry_missing_resource_change_raises_value_error(self):
        """An entry missing 'ResourceChange' must raise ValueError."""
        with pytest.raises(ValueError):
            iac_detect.scan_cfn_changeset({"Changes": [{"NotResourceChange": {}}]})


# ---------------------------------------------------------------------------
# CWE-23 path traversal guard
# ---------------------------------------------------------------------------

class TestCwe23Guard:
    def test_dotdot_in_path_raises(self, tmp_path):
        bad_path = str(tmp_path / ".." / "evil.tf")
        with pytest.raises(ValueError, match="\\.\\."):
            iac_detect.classify_file(bad_path)

    def test_dotdot_in_middle_raises(self):
        with pytest.raises(ValueError):
            iac_detect.classify_file("/legit/path/../../../etc/passwd")

    def test_normal_path_with_content_not_rejected(self):
        # Content kwarg bypasses the read (no CWE-23 on content itself), but
        # path is still validated.
        with pytest.raises(ValueError):
            iac_detect.classify_file("../escaped.tf", content="resource {}")
