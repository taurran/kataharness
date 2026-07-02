"""Tests for contract_edges.py — Freeze/Float M1 engine (M1-P0).

Slice A: invert + invalidation_set (pure, fail-closed). Every malformed shape must
RAISE (M1-L9 / F7 discipline) — a silent empty set would under-invalidate.
"""

from __future__ import annotations

import pytest

import contract_edges as ce

_H = "deadbeefcafe1234"  # a valid 16-hex surface hash


def _ba() -> dict:
    """A well-formed builds_against: T2,T3 build against C1; T3 also against C2."""
    return {
        "T2": [f"C1@{_H}"],
        "T3": [f"C1@{_H}", f"C2@{_H}"],
    }


# --- invert -------------------------------------------------------------------

def test_invert_happy_path():
    inv = ce.invert(_ba())
    assert inv == {"C1": ["T2", "T3"], "C2": ["T3"]}


def test_invert_empty_is_vacuous():
    assert ce.invert({}) == {}


def test_invert_dedupes_and_sorts():
    # A task listing the same contract twice collapses; tasks come out sorted.
    ba = {"T9": [f"C1@{_H}"], "T1": [f"C1@{_H}", f"C1@{_H}"]}
    assert ce.invert(ba) == {"C1": ["T1", "T9"]}


# --- invert: fail-closed on malformed (M1-L9) ---------------------------------

def test_invert_raises_not_a_dict():
    with pytest.raises(ValueError):
        ce.invert(["T2", "C1"])


def test_invert_raises_non_string_task_key():
    with pytest.raises(ValueError):
        ce.invert({1: [f"C1@{_H}"]})


def test_invert_raises_value_not_a_list():
    with pytest.raises(ValueError):
        ce.invert({"T2": f"C1@{_H}"})


def test_invert_raises_entry_not_a_string():
    with pytest.raises(ValueError):
        ce.invert({"T2": [123]})


def test_invert_raises_missing_at_separator():
    with pytest.raises(ValueError):
        ce.invert({"T2": ["C1_no_hash"]})


def test_invert_raises_bad_hash_charset():
    with pytest.raises(ValueError):
        ce.invert({"T2": ["C1@NOTHEX!!"]})


def test_invert_raises_hash_too_short():
    with pytest.raises(ValueError):
        ce.invert({"T2": ["C1@dead"]})  # < 8 hex


# --- invalidation_set ---------------------------------------------------------

def test_invalidation_set_returns_bound_tasks():
    assert ce.invalidation_set(_ba(), "C1") == ["T2", "T3"]
    assert ce.invalidation_set(_ba(), "C2") == ["T3"]


def test_invalidation_set_unknown_contract_is_empty():
    assert ce.invalidation_set(_ba(), "C_missing") == []


def test_invalidation_set_empty_map_is_empty():
    assert ce.invalidation_set({}, "C1") == []


def test_invalidation_set_raises_on_malformed():
    # A malformed map must RAISE, never silently return [] (would under-invalidate).
    with pytest.raises(ValueError):
        ce.invalidation_set({"T2": "C1@" + _H}, "C1")


def test_invalidation_set_raises_on_bad_changed_id():
    with pytest.raises(ValueError):
        ce.invalidation_set(_ba(), "")
