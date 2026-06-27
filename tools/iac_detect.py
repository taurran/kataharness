"""iac_detect.py — deterministic IaC file classifier and plan/change-set parser.

Pure module: no network I/O, no live cloud tools. All functions are
deterministic and depend only on their arguments (+ file content for
classify_file when content is not supplied).

Public API
----------
classify_file(path, content=None) -> "terraform"|"cloudformation"|"cdk"|None
classify_task(owned_files) -> set[str]
force_classify(path, overrides) -> str|None
scan_tf_plan(plan_json: dict) -> list[dict]
scan_cfn_changeset(desc: dict) -> list[dict]

CWE-23
------
Operator-supplied paths are ``..``-guarded at the read boundary; mirrors the
pattern in kata_settings._safe_abs (kata_settings.py:39-44).

Malformed plan/changeset contract
----------------------------------
scan_tf_plan and scan_cfn_changeset raise ``ValueError`` when required
top-level structure is absent or the wrong type (e.g. missing
``resource_changes`` / ``Changes`` key, non-list value, entry missing
``change`` / ``ResourceChange``).  Callers MUST treat ValueError as a gate
FAIL — returning [] silently on a corrupt plan would be a safety bypass
(DESIGN §3.4 / RESEARCH §2).  Per-resource optional fields (action_reason,
PolicyAction) are defaulted rather than raising.
"""

from __future__ import annotations

import re
from pathlib import Path, PurePath
from typing import Optional

# ---------------------------------------------------------------------------
# CWE-23 path-traversal guard (mirrors kata_settings._safe_abs:39-44)
# ---------------------------------------------------------------------------

def _safe_abs(raw: str | Path) -> Path:
    """Reject ``..`` traversal (CWE-23) then resolve to an absolute path.

    Raises:
        ValueError: if ``raw`` contains any ``..`` path segment.
    """
    p = Path(raw)
    if any(part == ".." for part in p.parts):
        raise ValueError(
            f"iac_detect: refusing path with '..' traversal: {raw!r}"
        )
    return p.resolve()


# ---------------------------------------------------------------------------
# CFN content signature — belt-and-suspenders (DESIGN N1 / MAJOR-5)
# ---------------------------------------------------------------------------

_CFN_VERSION_MARKER = "AWSTemplateFormatVersion"
# Regex: covers both YAML (`Type: AWS::`) and JSON (`"Type": "AWS::`) formats.
# YAML: literal `Type:` then optional whitespace then `AWS::`.
# JSON: `"Type"` then colon+optional-whitespace+quote then `AWS::`.
# The `AWS::` (double-colon) requirement prevents false positives on arbitrary files.
_CFN_TYPE_RE = re.compile(r'(?:"Type"\s*:\s*"|Type:\s*)AWS::')

_CFN_EXTENSIONS = {".yaml", ".yml", ".json", ".template"}
_TF_EXTENSIONS = {".tf", ".hcl"}


def _has_cfn_signature(text: str) -> bool:
    """Return True if text contains any CFN signature (N1 belt-and-suspenders)."""
    if _CFN_VERSION_MARKER in text:
        return True
    return bool(_CFN_TYPE_RE.search(text))


# ---------------------------------------------------------------------------
# Stateful resource type sets (used by both parsers)
# ---------------------------------------------------------------------------

# Terraform — exact type names and prefix families
# Exact set retained for back-compat; the prefix tuples below now subsume most of these.
_TF_STATEFUL_EXACT: frozenset[str] = frozenset({
    "aws_db_instance",
    "aws_rds_cluster",
    "aws_s3_bucket",
    "aws_ebs_volume",
    # Single-resource data stores not covered by a safe prefix family.
    "aws_ssm_parameter",
    "aws_cloudwatch_log_group",
    "aws_s3_object",
    "aws_s3_bucket_object",
})
_TF_STATEFUL_PREFIXES: tuple[str, ...] = (
    # Broadened RDS/DB prefixes (catch cluster_instance, global_cluster, db_parameter_group, etc.)
    "aws_db_",
    "aws_rds_",
    "aws_dynamodb_",       # table, global_table, table_item (catches global-table variant)
    # Data-bearing queue/stream/search/graph/document types (BLOCKER 1 — D98)
    "aws_efs_",
    "aws_sqs_",
    "aws_sns_",
    "aws_kinesis_",
    "aws_opensearch_",
    "aws_elasticsearch_",
    "aws_neptune_",
    "aws_docdb_",
    # Holistic red-team (D108/D109/D110 pass): data/secret/backup families whose
    # destruction is unrecoverable and MUST escalate, not silently fail.
    "aws_kms_",                 # destroying a key renders data encrypted under it unrecoverable
    "aws_secretsmanager_",
    "aws_msk_",                 # managed Kafka
    "aws_fsx_",
    "aws_backup_",
    "aws_glacier_",
    "aws_timestream",           # aws_timestreamwrite_*
    "aws_qldb_",
    "aws_memorydb_",
    "aws_keyspaces_",
    "aws_redshiftserverless_",  # not caught by the aws_redshift_ prefix
    # Pre-existing
    "aws_elasticache_",
    "aws_redshift_",
)


def _is_tf_stateful(resource_type: str) -> bool:
    return resource_type in _TF_STATEFUL_EXACT or resource_type.startswith(
        _TF_STATEFUL_PREFIXES
    )


# CloudFormation — prefix families and exact type names
_CFN_STATEFUL_EXACT: frozenset[str] = frozenset({
    "AWS::S3::Bucket",
    "AWS::EC2::Volume",       # EBS — TF flags aws_ebs_volume; close the CFN asymmetry
    "AWS::SSM::Parameter",
})
_CFN_STATEFUL_PREFIXES: tuple[str, ...] = (
    # Pre-existing
    "AWS::RDS::",
    "AWS::DynamoDB::",
    "AWS::ElastiCache::",
    "AWS::Redshift::",
    # Data-bearing queue/stream/search/graph/document types (BLOCKER 1 — D98)
    "AWS::EFS::",
    "AWS::SQS::",
    "AWS::SNS::",
    "AWS::Kinesis::",
    "AWS::OpenSearchService::",
    "AWS::Elasticsearch::",
    "AWS::Neptune::",
    "AWS::DocDB::",
    # Holistic red-team (D108/D109/D110 pass): data/secret/backup families.
    "AWS::KMS::",
    "AWS::SecretsManager::",
    "AWS::Logs::",                  # LogGroup (retained log data)
    "AWS::Backup::",
    "AWS::FSx::",
    "AWS::MSK::",
    "AWS::Timestream::",
    "AWS::QLDB::",
    "AWS::MemoryDB::",
    "AWS::Cassandra::",             # Keyspaces
    "AWS::OpenSearchServerless::",  # distinct from AWS::OpenSearchService::
)


def _is_cfn_stateful(resource_type: str) -> bool:
    return resource_type in _CFN_STATEFUL_EXACT or resource_type.startswith(
        _CFN_STATEFUL_PREFIXES
    )


# ---------------------------------------------------------------------------
# classify_file
# ---------------------------------------------------------------------------

def classify_file(
    path: str | Path,
    content: Optional[str] = None,
) -> Optional[str]:
    """Classify a single file as an IaC kind or None.

    Args:
        path:    File path (validated against ``..`` traversal even when
                 ``content`` is supplied).
        content: File text.  When None, the file at ``path`` is read; the
                 caller must ensure the file exists.

    Returns:
        ``"terraform"`` | ``"cloudformation"`` | ``"cdk"`` | ``None``.

    Raises:
        ValueError: if ``path`` contains a ``..`` segment (CWE-23).
        OSError:    if ``content`` is None and the file cannot be read.
    """
    # CWE-23: always validate the path (even when content bypasses the read).
    safe = _safe_abs(path)
    p = PurePath(path)

    # Case-insensitive matching: on Windows/macOS (and per CloudFormation, which
    # places NO casing constraint on the file extension) ``Stack.YAML`` / ``main.TF``
    # / ``deploy.Template`` are valid IaC files. Matching the literal lowercase
    # extension would let them skip the gate entirely. Normalise first.
    suffix = p.suffix.lower()
    name_lower = p.name.lower()
    parts_lower = {part.lower() for part in p.parts}

    # ---- Terraform: extension-based, checked first ----
    # .tf.json has suffix ".json" but name ends in ".tf.json"; check the
    # compound extension before the single-suffix CFN check.
    if suffix == ".tf" or suffix == ".hcl" or name_lower.endswith(".tf.json"):
        return "terraform"

    # ---- CDK: by filename or by path location ----
    # Check CDK BEFORE CFN so that cdk.out/ synthesised templates (which look
    # like CFN) are classified as "cdk" rather than "cloudformation".
    if name_lower == "cdk.json":
        return "cdk"
    if "cdk.out" in parts_lower:
        return "cdk"

    # ---- CloudFormation: extension + content signature ----
    if suffix in _CFN_EXTENSIONS:
        text = content if content is not None else safe.read_text(encoding="utf-8")
        if _has_cfn_signature(text):
            return "cloudformation"

    return None


# ---------------------------------------------------------------------------
# classify_task
# ---------------------------------------------------------------------------

def classify_task(
    owned_files: list[str | Path],
    overrides: dict[str, str] | None = None,
) -> set[str]:
    """Return the set of IaC kinds present across a task's owned files.

    An empty set means no IaC was detected (no gate fires — BC).

    ``overrides`` is the operator's ``iac.forceClassify`` map (glob → kind). It is
    consulted FIRST per file and is the documented mitigation for auto-detection
    false-negatives (an operator force-classifies a file auto-detection misses). A
    matched override wins over auto-detection; a non-match falls through to it.

    Args:
        owned_files: List of file paths belonging to the task.
        overrides:   Optional ``{glob: kind}`` force-classify map (``iac.forceClassify``).

    Returns:
        A set of kind strings (subset of ``{"terraform","cloudformation","cdk"}``).
    """
    kinds: set[str] = set()
    for f in owned_files:
        kind = force_classify(f, overrides) if overrides else None
        if kind is None:
            kind = classify_file(f)
        if kind is not None:
            kinds.add(kind)
    return kinds


# ---------------------------------------------------------------------------
# force_classify
# ---------------------------------------------------------------------------

def force_classify(
    path: str | Path,
    overrides: dict[str, str],
) -> Optional[str]:
    """Honor an operator force-classify list (paths/globs → kind).

    Iterates ``overrides`` in insertion order; returns the kind for the first
    pattern that matches ``path``, or ``None`` if no pattern matches.

    Pattern matching uses ``pathlib.PurePath.match()`` (Python 3.12+ ``**``
    support is available; requires-python >=3.12 in pyproject.toml).

    Args:
        path:      File path to classify.
        overrides: Mapping of glob pattern → kind (e.g.
                   ``{"infra/**/*.yaml": "cloudformation"}``).

    Returns:
        The matched kind, or ``None``.
    """
    pp = PurePath(path)
    for pattern, kind in overrides.items():
        if pp.match(pattern):
            return kind
    return None


# ---------------------------------------------------------------------------
# scan_tf_plan
# ---------------------------------------------------------------------------

_TF_DESTRUCTIVE_ACTIONS: frozenset[str] = frozenset({"delete"})


def scan_tf_plan(plan_json: dict) -> list[dict]:
    """Parse a Terraform plan JSON and return destructive resource changes.

    Flags any resource whose ``change.actions`` list contains ``"delete"``
    (covers ``["delete"]``, ``["delete","create"]``, ``["create","delete"]``).

    Args:
        plan_json: The parsed JSON from ``terraform show -json tfplan``.
                   Must contain a top-level ``"resource_changes"`` list.

    Returns:
        List of dicts: ``{address, type, actions, action_reason, stateful}``.
        ``stateful`` is True for data-bearing resource types (RDS/DB-*,
        DynamoDB, S3, EBS, EFS-*, SQS-*, SNS-*, Kinesis-*, OpenSearch-*,
        Elasticsearch-*, Neptune-*, DocDB-*, ElastiCache-*, Redshift-*).
        An empty list means no destructive changes were detected.

    Raises:
        ValueError: if ``plan_json`` is malformed (missing ``resource_changes``,
                    wrong type, or entries missing required ``change``/``actions``
                    keys).  Callers must treat this as a gate FAIL — a corrupt
                    plan must not silently pass (DESIGN §3.4 / RESEARCH §2).
    """
    if "resource_changes" not in plan_json:
        raise ValueError(
            "scan_tf_plan: malformed plan — 'resource_changes' key is absent; "
            "cannot safely parse destructive changes"
        )
    rc_list = plan_json["resource_changes"]
    if not isinstance(rc_list, list):
        raise ValueError(
            f"scan_tf_plan: 'resource_changes' must be a list, got {type(rc_list).__name__!r}"
        )

    results: list[dict] = []
    for idx, entry in enumerate(rc_list):
        # Type guard: each entry must be a dict (MAJOR 3 — D98)
        if not isinstance(entry, dict):
            raise ValueError(
                f"scan_tf_plan: resource_changes[{idx}] must be a dict, "
                f"got {type(entry).__name__!r}"
            )
        # Validate required structural keys (raise rather than silently skip)
        if "change" not in entry:
            raise ValueError(
                f"scan_tf_plan: resource_changes[{idx}] is missing the "
                f"'change' key (address={entry.get('address', '?')!r})"
            )
        change = entry["change"]
        # Type guard: change must be a dict (MAJOR 3 — D98)
        if not isinstance(change, dict):
            raise ValueError(
                f"scan_tf_plan: resource_changes[{idx}].change must be a dict, "
                f"got {type(change).__name__!r} "
                f"(address={entry.get('address', '?')!r})"
            )
        if "actions" not in change:
            raise ValueError(
                f"scan_tf_plan: resource_changes[{idx}].change is missing "
                f"'actions' key (address={entry.get('address', '?')!r})"
            )
        actions = change["actions"]
        # Type guard: actions must be a list — a bare string like "DELETE" must RAISE,
        # not silently pass through the `"delete" in actions` membership check (MAJOR 3 — D98)
        if not isinstance(actions, list):
            raise ValueError(
                f"scan_tf_plan: resource_changes[{idx}].change.actions must be a list, "
                f"got {type(actions).__name__!r} "
                f"(address={entry.get('address', '?')!r})"
            )

        # A destructive change contains "delete" in the actions list
        if "delete" not in actions:  # MUTATION PROOF TARGET — removing this guard → false negatives
            continue

        resource_type: str = entry.get("type", "")
        results.append({
            "address": entry.get("address", ""),
            "type": resource_type,
            "actions": actions,
            # `action_reason` is a SIBLING of `change` on the resource-change object
            # in `terraform show -json` (NOT inside `change`). Reading it from `change`
            # made it always "" on real plans, dropping the delete_because_* signals.
            "action_reason": entry.get("action_reason", ""),
            "stateful": _is_tf_stateful(resource_type),
        })

    return results


# ---------------------------------------------------------------------------
# scan_cfn_changeset
# ---------------------------------------------------------------------------

_CFN_DESTRUCTIVE_ACTIONS: frozenset[str] = frozenset({"Remove"})
_CFN_DESTRUCTIVE_REPLACEMENTS: frozenset[str] = frozenset({"True", "Conditional"})
_CFN_DESTRUCTIVE_POLICY_ACTIONS: frozenset[str] = frozenset({"Delete", "ReplaceAndDelete"})


def scan_cfn_changeset(desc: dict) -> list[dict]:
    """Parse a CloudFormation describe-change-set response and return destructive changes.

    Flags any ``ResourceChange`` where:
    - ``Action == "Remove"`` (deletion), or
    - ``Replacement in {"True", "Conditional"}`` (replace = destroy+recreate), or
    - ``PolicyAction in {"Delete", "ReplaceAndDelete"}`` (old resource not retained).

    Args:
        desc: The parsed JSON from ``aws cloudformation describe-change-set``.
              Must contain a top-level ``"Changes"`` list with entries that
              each have a ``"ResourceChange"`` dict.

    Returns:
        List of dicts: ``{logicalId, resourceType, action, replacement,
        policyAction, requiresRecreation, stateful}``.
        ``policyAction`` is ``None`` when absent.
        ``requiresRecreation`` is True when any ``Details[].Target.RequiresRecreation``
        equals ``"Always"`` (forced replacement — MAJOR 2 D98).
        ``stateful`` is True for data-bearing types (RDS::*, DynamoDB::*,
        S3::Bucket, ElastiCache::*, Redshift::*, EFS::*, SQS::*, SNS::*,
        Kinesis::*, OpenSearchService::*, Elasticsearch::*, Neptune::*,
        DocDB::*).

    Raises:
        ValueError: if ``desc`` is malformed (missing ``Changes``, wrong type,
                    or entries missing ``ResourceChange``).  Callers must treat
                    this as a gate FAIL.
    """
    if "Changes" not in desc:
        raise ValueError(
            "scan_cfn_changeset: malformed changeset — 'Changes' key is absent; "
            "cannot safely parse destructive changes"
        )
    changes_list = desc["Changes"]
    if not isinstance(changes_list, list):
        raise ValueError(
            f"scan_cfn_changeset: 'Changes' must be a list, got {type(changes_list).__name__!r}"
        )

    results: list[dict] = []
    for idx, entry in enumerate(changes_list):
        # Type guard: each entry must be a dict (MAJOR 3 — D98)
        if not isinstance(entry, dict):
            raise ValueError(
                f"scan_cfn_changeset: Changes[{idx}] must be a dict, "
                f"got {type(entry).__name__!r}"
            )
        if "ResourceChange" not in entry:
            raise ValueError(
                f"scan_cfn_changeset: Changes[{idx}] is missing the "
                f"'ResourceChange' key"
            )
        rc = entry["ResourceChange"]
        # Type guard: ResourceChange must be a dict (MAJOR 3 — D98)
        if not isinstance(rc, dict):
            raise ValueError(
                f"scan_cfn_changeset: Changes[{idx}].ResourceChange must be a dict, "
                f"got {type(rc).__name__!r}"
            )

        action: str = rc.get("Action", "")
        replacement: str = rc.get("Replacement", "False")
        policy_action: Optional[str] = rc.get("PolicyAction")  # absent = None
        resource_type: str = rc.get("ResourceType", "")

        # RequiresRecreation=Always is a forced replacement even when Replacement=False
        # (MAJOR 2 — D98; protocol/iac-safety.md §5b). Fail-closed on malformed Details/Target
        # (D98 re-confirm finding 7 — same fail-open class as MAJOR-3; never silently no-op the signal).
        details = rc.get("Details", [])
        if not isinstance(details, list):
            raise ValueError(
                f"scan_cfn_changeset: Changes[{idx}].ResourceChange.Details must be a list, "
                f"got {type(details).__name__!r}"
            )
        requires_recreation = False
        for detail in details:
            if not isinstance(detail, dict):
                raise ValueError(
                    f"scan_cfn_changeset: Changes[{idx}].ResourceChange.Details[] entries must be "
                    f"dicts, got {type(detail).__name__!r}"
                )
            target = detail.get("Target", {})
            if not isinstance(target, dict):
                raise ValueError(
                    f"scan_cfn_changeset: Changes[{idx}].ResourceChange.Details[].Target must be a "
                    f"dict, got {type(target).__name__!r}"
                )
            if target.get("RequiresRecreation") == "Always":
                requires_recreation = True
                break

        is_destructive = (
            action in _CFN_DESTRUCTIVE_ACTIONS
            or replacement in _CFN_DESTRUCTIVE_REPLACEMENTS
            or policy_action in _CFN_DESTRUCTIVE_POLICY_ACTIONS
            or requires_recreation  # MUTATION PROOF TARGET — removing → misses forced replacements
        )
        if not is_destructive:
            continue

        results.append({
            "logicalId": rc.get("LogicalResourceId", ""),
            "resourceType": resource_type,
            "action": action,
            "replacement": replacement,
            "policyAction": policy_action,
            "requiresRecreation": requires_recreation,
            "stateful": _is_cfn_stateful(resource_type),
        })

    return results
