"""Drift-guard for the path-traversal guard family (2026-07-12 health review Q-12).

The engine has ~30 hand-copied ``..``-rejection guards (``_safe_path`` / ``_guard_path``
/ ``_safe_kata_dir`` / ``_safe_source_path`` / ``_safe_abs``). They were unified to raise
``ValueError`` on a ``..`` component, but drift had begun at the edges (kata_supersede
swallowed it — fixed; recall/validation_misses deliberately don't ``.resolve()`` — a
documented variant). Rather than a risky 30-file refactor to a shared helper right before a
merge, this test pins the ONE invariant that actually protects correctness: **every guard in
the family rejects a ``..`` component with ValueError.** A new guard that forgets the reject,
or an existing one that regresses to swallowing it, goes RED here.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# (module, guard function name) — every single-path-arg guard in the family.
_GUARDS = [
    ("kata_board", "_safe_path"),
    ("gate_emit", "_safe_path"),
    ("grounding_gate", "_safe_path"),
    ("escalation", "_safe_kata_dir"),
    ("intent_scaffold", "_safe_path"),
    ("mutation_run", "_safe_source_path"),
    ("kata_router", "_safe_path"),
    ("recall", "_guard_path"),
    ("validation_misses", "_guard_path"),
    ("validation_report", "_safe_path"),
    ("benchmark", "_guard_path"),
    ("benchmark_control", "_guard_path"),
    ("graph_gen", "_safe_path"),
    ("kata_web", "_safe_path"),
    ("kata_steer", "_safe_path"),
    ("kata_supersede", "_safe_abs"),
    ("benchmark_def", "_guard_path"),
    ("iac_apply", "_safe_abs"),
    ("iac_detect", "_safe_abs"),
    ("kata_dash", "_safe_path"),
    ("kata_dash_demo", "_safe_path"),
    ("kata_install", "_safe_abs"),
    ("kata_overlay", "_safe_abs"),
    ("kata_preflight", "_safe_abs"),
    ("kata_settings", "_safe_abs"),
    ("kata_statusline", "_safe_path"),
    ("kata_version", "_safe_abs"),
    ("recurrence_detect", "_guard_path"),
    ("usage_meter", "_guard_path"),
]


@pytest.mark.parametrize("module_name,func_name", _GUARDS)
def test_guard_rejects_dotdot_traversal(module_name, func_name):
    """Every path-guard in the family raises ValueError on a '..' component."""
    mod = importlib.import_module(module_name)
    guard = getattr(mod, func_name, None)
    assert guard is not None, f"{module_name}.{func_name} missing — guard family drifted"
    with pytest.raises(ValueError):
        guard("../evil/x")


@pytest.mark.parametrize("module_name,func_name", _GUARDS)
def test_guard_accepts_clean_relative_path(module_name, func_name):
    """A clean path with no '..' component is accepted (guard isn't over-broad)."""
    mod = importlib.import_module(module_name)
    guard = getattr(mod, func_name)
    # Must not raise; return type varies (Path or normalized) — only the no-raise
    # contract is universal across the family.
    guard(".kata/sub/thing")


def test_guard_family_membership_is_complete():
    """If a new tools/*.py adds a single-arg path guard, it must join _GUARDS.

    Cheap structural tripwire: scan for guard-shaped defs and flag any module
    that defines one but isn't enumerated above (so the family can't silently
    grow an unchecked member)."""
    import re

    tools_dir = Path(__file__).resolve().parents[1]
    listed = {m for m, _ in _GUARDS}
    pattern = re.compile(r"^def (_safe_path|_guard_path|_safe_kata_dir|_safe_source_path|_safe_abs)\(",
                         re.MULTILINE)
    missing = []
    for py in sorted(tools_dir.glob("*.py")):
        text = py.read_text(encoding="utf-8")
        if pattern.search(text) and py.stem not in listed:
            missing.append(py.stem)
    assert not missing, (
        f"path-guard modules not enumerated in _GUARDS (drift risk): {missing}"
    )
