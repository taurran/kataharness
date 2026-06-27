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
--- D98 additions ---
- BLOCKER 1 (TF): aws_efs_*, aws_sqs_*, aws_sns_*, aws_kinesis_*, aws_opensearch_*,
  aws_elasticsearch_*, aws_neptune_*, aws_docdb_* → stateful True
- BLOCKER 1 (TF): aws_rds_cluster_instance / aws_rds_global_cluster caught by aws_rds_ prefix
- BLOCKER 1 (CFN): AWS::EFS::*, AWS::SQS::*, AWS::SNS::*, AWS::Kinesis::*,
  AWS::OpenSearchService::*, AWS::Elasticsearch::*, AWS::Neptune::*, AWS::DocDB::* → stateful True
- MAJOR 2: Details[].Target.RequiresRecreation=Always → flagged even when Replacement=False
- MAJOR 3 (TF): non-dict entry in resource_changes → ValueError
- MAJOR 3 (TF): non-dict change value → ValueError
- MAJOR 3 (TF): actions as string (not list) → ValueError
- MAJOR 3 (CFN): non-dict entry in Changes → ValueError
- MAJOR 3 (CFN): non-dict ResourceChange value → ValueError
"""

from __future__ import annotations

import pytest

import iac_detect


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _tf_resource(address, rtype, actions, action_reason=""):
    """Build a resource_changes entry for TF plan fixtures.

    Matches the real ``terraform show -json`` schema: ``action_reason`` is a
    SIBLING of ``change`` on the resource-change object, not nested inside it.
    """
    entry = {
        "address": address,
        "type": rtype,
        "change": {"actions": actions},
    }
    if action_reason:
        entry["action_reason"] = action_reason
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

    def test_uppercase_extension_still_terraform(self):
        """Red-team: .TF (Windows/macOS) must NOT skip the gate (case-insensitive)."""
        assert iac_detect.classify_file("/proj/Main.TF", content="x") == "terraform"
        assert iac_detect.classify_file("/proj/over.TF.JSON", content="{}") == "terraform"


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

    def test_uppercase_extensions_still_cloudformation(self):
        """Red-team: .YAML/.Template (Windows/macOS) must NOT skip the gate."""
        assert iac_detect.classify_file(
            "/proj/Stack.YAML", content=self.CFN_VERSION_YAML
        ) == "cloudformation"
        assert iac_detect.classify_file(
            "/proj/Deploy.Template", content=self.CFN_VERSION_YAML
        ) == "cloudformation"

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

    def test_force_classify_overrides_are_honored(self):
        """Red-team: forceClassify is the documented mitigation — it MUST be wired
        into classify_task (it was dead before). A file auto-detection misses
        (extensionless / odd name) is rescued by the operator override."""
        overrides = {"infra/**": "cloudformation"}
        result = iac_detect.classify_task(["infra/weird_name_no_ext"], overrides=overrides)
        assert result == {"cloudformation"}

    def test_force_classify_wins_over_autodetect(self, tmp_path):
        tf = tmp_path / "main.tf"
        tf.write_text("resource \"aws_vpc\" \"v\" {}\n", encoding="utf-8")
        # Override forces this .tf to cloudformation
        result = iac_detect.classify_task(
            [str(tf)], overrides={str(tf): "cloudformation"}
        )
        assert result == {"cloudformation"}

    def test_no_overrides_is_backward_compatible(self, tmp_path):
        f = tmp_path / "main.tf"
        f.write_text("", encoding="utf-8")
        assert iac_detect.classify_task([str(f)]) == {"terraform"}


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

    @pytest.mark.parametrize("rtype", [
        "aws_kms_key",
        "aws_secretsmanager_secret",
        "aws_msk_cluster",
        "aws_fsx_lustre_file_system",
        "aws_backup_vault",
        "aws_glacier_vault",
        "aws_timestreamwrite_database",
        "aws_qldb_ledger",
        "aws_memorydb_cluster",
        "aws_keyspaces_keyspace",
        "aws_redshiftserverless_namespace",
        "aws_dynamodb_global_table",
        "aws_cloudwatch_log_group",
        "aws_ssm_parameter",
        "aws_s3_object",
    ])
    def test_stateful_red_team_families(self, rtype):
        """Red-team: destroying these data/secret/backup types MUST escalate (stateful)."""
        plan = self._plan(_tf_resource(f"{rtype}.x", rtype, ["delete"]))
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

    @pytest.mark.parametrize("rtype", [
        "AWS::EC2::Volume",                       # EBS — closes the TF/CFN asymmetry
        "AWS::KMS::Key",
        "AWS::SecretsManager::Secret",
        "AWS::Logs::LogGroup",
        "AWS::Backup::BackupVault",
        "AWS::FSx::FileSystem",
        "AWS::MSK::Cluster",
        "AWS::Timestream::Database",
        "AWS::QLDB::Ledger",
        "AWS::MemoryDB::Cluster",
        "AWS::Cassandra::Keyspace",
        "AWS::OpenSearchServerless::Collection",
        "AWS::SSM::Parameter",
    ])
    def test_stateful_red_team_families(self, rtype):
        """Red-team: removing these data/secret/backup types MUST escalate (stateful)."""
        desc = self._desc(_cfn_change("X", rtype, "Remove"))
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

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
        # AWS::SQS::Queue is now stateful; use EC2::Instance which carries no durable data
        desc = self._desc(
            _cfn_change("MyInstance", "AWS::EC2::Instance", "Remove")
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

    # --- malformed Details/Target → ValueError (D98 re-confirm finding 7: same fail-open class as MAJOR-3) ---

    def test_details_not_list_raises_value_error(self):
        """Malformed Details (non-list) must fail closed, not silently drop the RequiresRecreation signal."""
        desc = {"Changes": [{"ResourceChange": {
            "Action": "Modify", "Replacement": "False",
            "ResourceType": "AWS::RDS::DBInstance", "Details": "oops"}}]}
        with pytest.raises(ValueError, match="Details"):
            iac_detect.scan_cfn_changeset(desc)

    def test_details_entry_non_dict_raises_value_error(self):
        desc = {"Changes": [{"ResourceChange": {
            "Action": "Modify", "Replacement": "False",
            "ResourceType": "AWS::RDS::DBInstance", "Details": ["oops"]}}]}
        with pytest.raises(ValueError, match="Details"):
            iac_detect.scan_cfn_changeset(desc)

    def test_details_target_non_dict_raises_value_error(self):
        desc = {"Changes": [{"ResourceChange": {
            "Action": "Modify", "Replacement": "False",
            "ResourceType": "AWS::RDS::DBInstance", "Details": [{"Target": "oops"}]}}]}
        with pytest.raises(ValueError, match="Target"):
            iac_detect.scan_cfn_changeset(desc)


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


# ---------------------------------------------------------------------------
# BLOCKER 1 — expanded stateful TF prefixes (D98)
# ---------------------------------------------------------------------------

class TestScanTfPlanStatefulExpanded:
    """New prefix families that the contract names but the old sets missed."""

    def _plan(self, *changes):
        return {"resource_changes": list(changes)}

    def test_stateful_aws_efs_prefix(self):
        plan = self._plan(_tf_resource("aws_efs_file_system.fs", "aws_efs_file_system", ["delete"]))
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_sqs_prefix(self):
        plan = self._plan(_tf_resource("aws_sqs_queue.q", "aws_sqs_queue", ["delete"]))
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_sns_prefix(self):
        plan = self._plan(_tf_resource("aws_sns_topic.t", "aws_sns_topic", ["delete"]))
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_kinesis_prefix(self):
        plan = self._plan(_tf_resource("aws_kinesis_stream.s", "aws_kinesis_stream", ["delete"]))
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_opensearch_prefix(self):
        plan = self._plan(
            _tf_resource("aws_opensearch_domain.d", "aws_opensearch_domain", ["delete"])
        )
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_elasticsearch_prefix(self):
        plan = self._plan(
            _tf_resource("aws_elasticsearch_domain.d", "aws_elasticsearch_domain", ["delete"])
        )
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_neptune_prefix(self):
        plan = self._plan(_tf_resource("aws_neptune_cluster.c", "aws_neptune_cluster", ["delete"]))
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_docdb_prefix(self):
        plan = self._plan(_tf_resource("aws_docdb_cluster.c", "aws_docdb_cluster", ["delete"]))
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_rds_cluster_instance_prefix(self):
        """aws_rds_cluster_instance is NOT in the exact set; must be caught by aws_rds_ prefix."""
        plan = self._plan(
            _tf_resource("aws_rds_cluster_instance.ci", "aws_rds_cluster_instance", ["delete"])
        )
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_rds_global_cluster_prefix(self):
        """aws_rds_global_cluster must be caught by aws_rds_ prefix."""
        plan = self._plan(
            _tf_resource("aws_rds_global_cluster.gc", "aws_rds_global_cluster", ["delete"])
        )
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True

    def test_stateful_aws_db_prefix(self):
        """aws_db_ prefix catches aws_db_instance and other aws_db_* variants."""
        plan = self._plan(_tf_resource("aws_db_parameter_group.pg", "aws_db_parameter_group", ["delete"]))
        assert iac_detect.scan_tf_plan(plan)[0]["stateful"] is True


# ---------------------------------------------------------------------------
# BLOCKER 1 — expanded stateful CFN prefixes (D98)
# ---------------------------------------------------------------------------

class TestScanCfnChangesetStatefulExpanded:
    """New prefix families that the contract names but the old sets missed."""

    def _desc(self, *changes):
        return {"Changes": list(changes)}

    def test_stateful_efs(self):
        desc = self._desc(_cfn_change("MyFS", "AWS::EFS::FileSystem", "Remove"))
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

    def test_stateful_sqs(self):
        desc = self._desc(_cfn_change("MyQueue", "AWS::SQS::Queue", "Remove"))
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

    def test_stateful_sns(self):
        desc = self._desc(_cfn_change("MyTopic", "AWS::SNS::Topic", "Remove"))
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

    def test_stateful_kinesis(self):
        desc = self._desc(_cfn_change("MyStream", "AWS::Kinesis::Stream", "Remove"))
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

    def test_stateful_opensearch(self):
        desc = self._desc(_cfn_change("MyDomain", "AWS::OpenSearchService::Domain", "Remove"))
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

    def test_stateful_elasticsearch(self):
        desc = self._desc(_cfn_change("MyDomain", "AWS::Elasticsearch::Domain", "Remove"))
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

    def test_stateful_neptune(self):
        desc = self._desc(_cfn_change("MyCluster", "AWS::Neptune::DBCluster", "Remove"))
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True

    def test_stateful_docdb(self):
        desc = self._desc(_cfn_change("MyDocDB", "AWS::DocDB::DBCluster", "Remove"))
        assert iac_detect.scan_cfn_changeset(desc)[0]["stateful"] is True


# ---------------------------------------------------------------------------
# MAJOR 2 — RequiresRecreation == "Always" must trigger a flag (D98)
# ---------------------------------------------------------------------------

class TestScanCfnRequiresRecreation:
    """Replacement=False + Details[].Target.RequiresRecreation=Always must be flagged."""

    def test_requires_recreation_always_flagged(self):
        """Forced replacement via RequiresRecreation=Always, even when Replacement=False."""
        desc = {"Changes": [{
            "ResourceChange": {
                "LogicalResourceId": "MyFunction",
                "ResourceType": "AWS::Lambda::Function",
                "Action": "Modify",
                "Replacement": "False",
                "Details": [
                    {"Target": {"RequiresRecreation": "Always"}}
                ],
            }
        }]}
        results = iac_detect.scan_cfn_changeset(desc)
        assert len(results) == 1
        assert results[0]["logicalId"] == "MyFunction"

    def test_requires_recreation_never_not_flagged(self):
        """RequiresRecreation=Never with no other destructive signal → not flagged."""
        desc = {"Changes": [{
            "ResourceChange": {
                "LogicalResourceId": "MyFunction",
                "ResourceType": "AWS::Lambda::Function",
                "Action": "Modify",
                "Replacement": "False",
                "Details": [
                    {"Target": {"RequiresRecreation": "Never"}}
                ],
            }
        }]}
        assert iac_detect.scan_cfn_changeset(desc) == []

    def test_requires_recreation_conditionally_not_flagged_by_this_check(self):
        """RequiresRecreation=Conditionally alone with Replacement=False → not flagged."""
        desc = {"Changes": [{
            "ResourceChange": {
                "LogicalResourceId": "MyFunction",
                "ResourceType": "AWS::Lambda::Function",
                "Action": "Modify",
                "Replacement": "False",
                "Details": [
                    {"Target": {"RequiresRecreation": "Conditionally"}}
                ],
            }
        }]}
        assert iac_detect.scan_cfn_changeset(desc) == []

    def test_no_details_key_not_flagged(self):
        """A ResourceChange with no Details key → not flagged by RequiresRecreation."""
        desc = {"Changes": [{
            "ResourceChange": {
                "LogicalResourceId": "MyRole",
                "ResourceType": "AWS::IAM::Role",
                "Action": "Modify",
                "Replacement": "False",
            }
        }]}
        assert iac_detect.scan_cfn_changeset(desc) == []


# ---------------------------------------------------------------------------
# MAJOR 3 — type guards: malformed shapes must raise ValueError (D98)
# ---------------------------------------------------------------------------

class TestScanTfPlanTypeGuards:
    """Fail-closed: bad shapes must raise ValueError, not TypeError or silently return []."""

    def test_entry_not_dict_raises(self):
        """A non-dict entry in resource_changes must raise ValueError."""
        plan = {"resource_changes": ["not-a-dict"]}
        with pytest.raises(ValueError):
            iac_detect.scan_tf_plan(plan)

    def test_change_not_dict_raises(self):
        """change must be a dict; a non-dict value must raise ValueError."""
        plan = {"resource_changes": [
            {"address": "x.y", "type": "aws_vpc", "change": "not-a-dict"}
        ]}
        with pytest.raises(ValueError):
            iac_detect.scan_tf_plan(plan)

    def test_actions_string_raises(self):
        """actions='DELETE' (a string, not list) must raise ValueError — not silently pass/fail."""
        plan = {"resource_changes": [
            {"address": "x.y", "type": "aws_vpc", "change": {"actions": "DELETE"}}
        ]}
        with pytest.raises(ValueError):
            iac_detect.scan_tf_plan(plan)

    def test_actions_string_delete_lowercase_raises(self):
        """actions='delete' (lowercase string) must also raise — even though 'delete' in 'delete' is True."""
        plan = {"resource_changes": [
            {"address": "x.y", "type": "aws_vpc", "change": {"actions": "delete"}}
        ]}
        with pytest.raises(ValueError):
            iac_detect.scan_tf_plan(plan)


class TestScanCfnChangesetTypeGuards:
    """Fail-closed: bad shapes must raise ValueError, not TypeError or silently return []."""

    def test_entry_not_dict_raises(self):
        """A non-dict entry in Changes must raise ValueError."""
        desc = {"Changes": ["not-a-dict"]}
        with pytest.raises(ValueError):
            iac_detect.scan_cfn_changeset(desc)

    def test_resource_change_not_dict_raises(self):
        """ResourceChange value must be a dict; a non-dict must raise ValueError."""
        desc = {"Changes": [{"ResourceChange": "not-a-dict"}]}
        with pytest.raises(ValueError):
            iac_detect.scan_cfn_changeset(desc)
