"""kata_config.py — the GB12 core-config load-guard (BURN-D).

The mechanism behind the kata-orchestrate Preconditions promise that a PRESENT
``kata.config`` naming a non-existent ``mode``, a ``tiers[family]`` with no
``kata-<family>-<tier>`` skill, or a ``modules[]`` entry with no provider skill
is a **STOP + escalate**, never a guessed default (D45/GB12 — a stale or
hand-edited config on a re-entrant run is exactly the drift the harness exists
to prevent).

Style-matched to :func:`kata_models.validate_advisor_block`: RAISES
``ValueError`` on ANY malformed field so the load-guard STOPs and escalates;
a present-but-broken value is NEVER silently coerced to a default.  Absent
keys PASS — the documented default applies (``mode`` absent ⇒ ``"standard"``,
D25) and backward compatibility holds.

Scope, stated exactly (GRILL-LEDGER Amendment 6):

* ``mode`` — present ⇒ must be one of ``essential | standard | advanced``.
* ``tiers`` — present ⇒ every ``tiers[family]`` value must name a
  ``kata-<family>-<tier>`` skill in *available_skills*, with the ONE legal
  carve-out ``tiers["kata-grill"] == "skip"`` (the grill-skip rung, D71/D73).
* ``modules`` — present ⇒ every entry must have a provider skill.  Provider
  resolution follows the on-disk mechanism (protocol/config.md §Optional
  modules + validate_skills.check_tags_namespace): a module is PROVIDED iff
  some discovered skill carries the frontmatter tag ``kata/module/<module>``.
  There is no name-convention from module key to provider skill name
  (``kata/module/debug`` → ``kata-comprehend``), so the tag set — not the
  name set — answers the question; that is why this validator takes
  *provided_modules* alongside *available_skills* (see the note below).
  Both documented entry forms are accepted: the modules table's full
  ``kata/module/<x>`` key and the schema example's short ``<x>`` — both
  normalize to the tag.
* ``effort`` — EXPLICITLY OUT OF SCOPE: protocol/config.md disclaims its own
  ``reasoning`` enum ("indicative, not an API contract").  Not validated here.
* Malformed JSON — the CALLER's read step owns that; this function receives a
  parsed value.
* Every OTHER config key is outside this validator: config.md is a growing
  key registry and each strictly-validated sibling field has its own named
  validator (``kata_roles.resolve_roles``, ``kata_telemetry.validate_inline_eval``,
  ``kata_risk.resolve_inline_eval_params``, ``kata_models.validate_advisor_block``,
  ``kata_models.validate_anchor``).  Unknown-key rejection here would break
  every future additive field — deliberately not done.

PURE by contract: no subprocess, no network, no filesystem.  The caller
produces the two input sets — ``validate_skills.load_skills()`` discovers the
skill tree; :func:`available_from_skills` derives both sets from its output.

Determinism Doctrine: sets never drive output order — every set rendered into
an error message is ``sorted()`` first.

**Second responsibility, added by the trust-model burn (TM-A2 / DESIGN §5.4):** the
MACHINE-LOCAL SPLIT — :data:`MACHINE_LOCAL_KEYS`, :func:`split_machine_local`,
:func:`merge_machine_local`.  It lives here rather than in a new module because it is the
same subject (what a ``kata.config`` key MEANS) read from the other end: the load-guard
says which values are legal, the split says which of them are provenance and which are
this machine's business.  Both stay PURE and both refuse a non-dict config.
"""
from __future__ import annotations

import json
from collections.abc import Iterable

#: The unified tier+module axis (D24a); default "standard" when absent (D25).
VALID_MODES: frozenset[str] = frozenset({"essential", "standard", "advanced"})

#: The frontmatter-tag namespace that declares module provision (STANDARDS §1.1).
MODULE_TAG_PREFIX = "kata/module/"

#: The ONE legal non-skill tier value: the grill-skip rung (D71/D73).
GRILL_FAMILY = "kata-grill"
GRILL_SKIP = "skip"


def validate_core_config(
    config: dict,
    available_skills: set[str],
    provided_modules: set[str],
) -> None:
    """Fail-closed shape guard for a PRESENT ``kata.config`` (GB12/D45).

    Args:
        config: The parsed ``kata.config`` JSON object.  The absent-file case
            (⇒ assume Standard, D25) is the caller's branch and never reaches
            this guard — mirroring ``validate_advisor_block``'s absent-block
            contract.
        available_skills: Discovered skill NAMES (not paths) — e.g.
            ``{s.name for s in validate_skills.load_skills()}``.
        provided_modules: Discovered ``kata/module/<x>`` frontmatter tags —
            the on-disk provider declarations.  Derive both sets at once via
            :func:`available_from_skills`.

    Raises:
        ValueError: Any malformed in-scope field, naming the offending
            key/value — the load-guard STOPs and escalates; never a silent
            coercion to a default.
    """
    if not isinstance(config, dict):
        raise ValueError(
            f"kata.config must be a dict, got {type(config).__name__}"
        )

    # mode — absent ⇒ "standard" (D25) applies; present ⇒ strict enum.
    if "mode" in config:
        mode = config["mode"]
        if not isinstance(mode, str) or mode not in VALID_MODES:
            raise ValueError(
                f"kata.config.mode must be one of {sorted(VALID_MODES)} "
                f"when present, got {mode!r}"
            )

    # tiers — absent family ⇒ the mode's default tier; a present value must
    # name a real kata-<family>-<tier> skill (grill-skip excepted).
    if "tiers" in config:
        tiers = config["tiers"]
        if not isinstance(tiers, dict):
            raise ValueError(
                f"kata.config.tiers must be a dict, got {type(tiers).__name__}"
            )
        for family in sorted(tiers):
            tier = tiers[family]
            if not isinstance(family, str) or not isinstance(tier, str):
                raise ValueError(
                    f"kata.config.tiers entries must be str -> str, "
                    f"got {family!r}: {tier!r}"
                )
            if family == GRILL_FAMILY and tier == GRILL_SKIP:
                continue  # the grill-skip rung (D71/D73) — the ONE carve-out
            if f"{family}-{tier}" not in available_skills:
                raise ValueError(
                    f"kata.config.tiers[{family!r}] = {tier!r} names no "
                    f"'{family}-{tier}' skill — a present-but-broken tier is "
                    f"never guessed over (GB12/D45)"
                )

    # modules — every entry must have a provider skill (a skill tagged
    # kata/module/<module>).  Full and short forms both accepted.
    if "modules" in config:
        modules = config["modules"]
        if not isinstance(modules, list):
            raise ValueError(
                f"kata.config.modules must be a list, got {type(modules).__name__}"
            )
        unprovided: list[str] = []
        for entry in modules:
            if not isinstance(entry, str):
                raise ValueError(
                    f"kata.config.modules entries must be str, got {entry!r}"
                )
            tag = entry if entry.startswith(MODULE_TAG_PREFIX) else MODULE_TAG_PREFIX + entry
            if tag not in provided_modules:
                unprovided.append(entry)
        if unprovided:
            raise ValueError(
                "kata.config.modules entr(y/ies) with no provider skill "
                f"(no skill tagged {MODULE_TAG_PREFIX}<module>): "
                f"{sorted(unprovided)!r} — a module key with no matching "
                "provider is a load-guard STOP (fail-closed, D45)"
            )


# ---------------------------------------------------------------------------
# TM-A2 / DESIGN §5.4 — the machine-local split
#
# "Machine-specific values (personal paths) migrate to `.kata-settings.json` (the
# existing machine-local home); `kata.config` and `INTENT.md` become clean, COMMITTED
# run provenance — completing the cursor's machine-change story."
#
# The provenance drift check (`kata_close.provenance_drift`) compares a COMMITTED
# `kata.config` against what a run executed.  A personal absolute path inside that file
# makes the comparison meaningless: it differs on every machine, so either the check
# screams drift on a clean run or the operator learns to ignore it.  Splitting the two
# kinds of value is what makes the check a signal.
#
# The three keys below are the ones whose VALUES are paths into a specific operator's
# filesystem.  Everything else in the schema is a policy value that means the same thing
# everywhere and stays committed, deliberately — this is a narrow, named list, not a
# heuristic over "things that look like paths".
# ---------------------------------------------------------------------------

#: Dotted paths whose values are machine-specific and home in `.kata-settings.json`.
#: Ordered; the order is the migration's apply order and is part of its determinism.
MACHINE_LOCAL_KEYS: tuple[str, ...] = (
    "agentSkills.dir",       # the agent-skills toolkit root — outside this repo by contract
    "engram.learnFeed.dir",  # the second-brain vault feed target — a personal vault path
    "target.path",           # the existing repo a version-up run points at
)


def _dig(config: dict, parts: tuple[str, ...]):
    """Walk *parts* through nested dicts; return ``(found, value)``.  PURE."""
    node = config
    for part in parts:
        if not isinstance(node, dict) or part not in node:
            return False, None
        node = node[part]
    return True, node


def split_machine_local(config: dict) -> tuple[dict, dict]:
    """Split a parsed ``kata.config`` into ``(committed_clean, machine_values)``.  PURE.

    ``committed_clean`` is a deep-ish copy with every :data:`MACHINE_LOCAL_KEYS` entry
    removed (and any dict left empty by the removal removed too, so a migrated config has
    no hollow blocks to diff against).  ``machine_values`` is ``{dotted_key: value}`` for
    every key that was present — absent keys are simply absent, never ``None``, because a
    ``None`` would then be written into the settings file as a real recorded decision.

    The input is never mutated: a caller comparing before/after must be able to.

    Raises:
        ValueError: when *config* is not a dict (fail-closed, the house rule — a
            present-but-broken config is never silently coerced).
    """
    if not isinstance(config, dict):
        raise ValueError(f"kata.config must be a dict, got {type(config).__name__}")
    clean = json.loads(json.dumps(config, sort_keys=True))  # deep copy, canonical order
    moved: dict[str, object] = {}
    for dotted in MACHINE_LOCAL_KEYS:
        parts = tuple(dotted.split("."))
        found, value = _dig(clean, parts)
        if not found:
            continue
        moved[dotted] = value
        node = clean
        for part in parts[:-1]:
            node = node[part]
        del node[parts[-1]]
        # Drop blocks the removal emptied, innermost first — a hollow `{"target": {}}`
        # is a formatting difference that would read as provenance drift.
        for depth in range(len(parts) - 1, 0, -1):
            parent = clean
            for part in parts[:depth - 1]:
                parent = parent[part]
            if isinstance(parent.get(parts[depth - 1]), dict) and not parent[parts[depth - 1]]:
                del parent[parts[depth - 1]]
    return clean, dict(sorted(moved.items()))


def merge_machine_local(clean: dict, machine: dict) -> dict:
    """Re-attach machine-local values to a committed-clean config.  PURE, non-mutating.

    The read-side inverse of :func:`split_machine_local`: a consumer that needs the real
    ``agentSkills.dir`` calls this with the machine's recorded values.  A key not in
    :data:`MACHINE_LOCAL_KEYS` is IGNORED — this function re-attaches provenance, it is
    not a general config-merge back door.
    """
    if not isinstance(clean, dict):
        raise ValueError(f"kata.config must be a dict, got {type(clean).__name__}")
    merged = json.loads(json.dumps(clean, sort_keys=True))
    for dotted in MACHINE_LOCAL_KEYS:
        if dotted not in (machine or {}):
            continue
        parts = tuple(dotted.split("."))
        node = merged
        for part in parts[:-1]:
            if not isinstance(node.get(part), dict):
                node[part] = {}
            node = node[part]
        node[parts[-1]] = machine[dotted]
    return merged


def available_from_skills(skills: Iterable) -> tuple[set[str], set[str]]:
    """Derive ``(available_skills, provided_modules)`` from discovered skills.

    The producer bridge over ``validate_skills.load_skills()`` output — pure
    over data (no I/O here; discovery already happened).  Accepts any iterable
    of objects with ``.name`` and ``.frontmatter`` (duck-typed to
    ``validate_skills.Skill``).

    Args:
        skills: Discovered skill records (``validate_skills.load_skills()``).

    Returns:
        ``(names, module_tags)`` — skill names, and every frontmatter tag
        under ``kata/module/``.
    """
    names: set[str] = set()
    provided: set[str] = set()
    for skill in skills:
        names.add(skill.name)
        for tag in skill.frontmatter.get("tags") or []:
            if str(tag).startswith(MODULE_TAG_PREFIX):
                provided.add(str(tag))
    return names, provided
