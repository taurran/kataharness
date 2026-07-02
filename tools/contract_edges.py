"""contract_edges.py — Freeze/Float M1 engine (pure, fail-closed; NO wiring).

Contract edges (`builds_against`) let a contract-only dependent dispatch at freeze
instead of waiting for its provider task. This module is the deterministic engine
behind that scheduling float and its safety companions. It is PURE — nothing in the
harness calls it yet (M1-P0); wiring lands in M1-P1/P2. See
`.planning/specs/freeze-float-m1/DESIGN.md`.

Edge grammar (M1-L1):
    builds_against: { "<task>": [ "<contractId>@<surfaceHash>" ] }

Fail-closed discipline (M1-L9 / F7): every function that consumes `builds_against`
RAISES ``ValueError`` on a malformed structure rather than returning a silent
empty/permissive result. Only a *well-formed* empty map is vacuous. This mirrors
``kata_restore.parse_plan_tasks``'s raise-on-malformed template — an invalidation
set driving abort/re-open must never silently under-invalidate.
"""

from __future__ import annotations

import re

# <contractId>@<surfaceHash> — id is a path-safe slug; hash is lowercase hex (8–64).
_EDGE_RE = re.compile(r"^(?P<id>[A-Za-z0-9._-]+)@(?P<hash>[0-9a-f]{8,64})$")


def _parse_edge(entry: object) -> tuple[str, str]:
    """Validate + split one ``"<contractId>@<hash>"`` entry. RAISE if malformed."""
    if not isinstance(entry, str):
        raise ValueError(f"builds_against edge entry must be a string, got {type(entry).__name__}")
    m = _EDGE_RE.match(entry)
    if m is None:
        raise ValueError(
            f"malformed builds_against edge {entry!r} — expected '<contractId>@<surfaceHash>' "
            f"(hash = 8-64 lowercase hex)"
        )
    return m.group("id"), m.group("hash")


def _validate_shape(builds_against: object) -> dict:
    """Validate ONLY the top-level shape ``{ task_str: [list] }``. RAISE if malformed.

    Entry-grammar validation lives in ``_parse_edge`` (the single place entries are
    split), so it is not duplicated here. An empty ``{}`` is well-formed (vacuous, BC).
    """
    if not isinstance(builds_against, dict):
        raise ValueError(
            f"builds_against must be a dict of task -> [edges], got {type(builds_against).__name__}"
        )
    for task, edges in builds_against.items():
        if not isinstance(task, str):
            raise ValueError(f"builds_against task key must be a string, got {type(task).__name__}")
        if not isinstance(edges, list):
            raise ValueError(
                f"builds_against[{task!r}] must be a list of edges, got {type(edges).__name__}"
            )
    return builds_against


def invert(builds_against: object) -> dict[str, list[str]]:
    """Invert ``{task: [contractId@hash]}`` to ``{contractId: [task, ...]}``.

    Tasks per contract are sorted + deduped. RAISES ``ValueError`` on any malformed
    structure — bad top-level shape (via ``_validate_shape``) or any malformed entry
    (via ``_parse_edge``) (M1-L9); a well-formed empty map returns ``{}``.
    """
    _validate_shape(builds_against)
    out: dict[str, set[str]] = {}
    for task, edges in builds_against.items():
        for entry in edges:
            contract_id, _hash = _parse_edge(entry)  # raises on malformed grammar
            out.setdefault(contract_id, set()).add(task)
    return {cid: sorted(tasks) for cid, tasks in out.items()}


def invalidation_set(builds_against: object, changed_contract_id: str) -> list[str]:
    """Return the sorted tasks bound to ``changed_contract_id``.

    The set a contract supersede must abort/re-open (M1-L3). RAISES on malformed
    ``builds_against`` (never a silent empty set); an unknown contract id or a
    contract with no dependents returns ``[]``.
    """
    if not isinstance(changed_contract_id, str) or not changed_contract_id:
        raise ValueError("changed_contract_id must be a non-empty string")
    inverted = invert(builds_against)
    return inverted.get(changed_contract_id, [])
