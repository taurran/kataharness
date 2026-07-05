"""Tests for kata_settings.py — the central-install settings file.

PURE except the tmp_path fixture (used as a fake harness home).

Coverage:
- build_settings returns the 2 settings + version; resolves to absolute
- build_settings with no vault stores vaultDir = None
- missing/blank parent_dir raises ValueError
- '..' traversal in a path is rejected (CWE-23)
- write_settings round-trips through read_settings
- read_settings returns {} when the file is absent
- harness_home honors $KATA_HOME, else self-locates to the repo root
- settings_path lands the file at <home>/.kata-settings.json
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import kata_settings as ks
import kata_version


def test_build_settings_shape(tmp_path):
    proj = tmp_path / "Projects"
    proj.mkdir()
    data = ks.build_settings(proj)
    assert data["settingsVersion"] == ks.SETTINGS_VERSION
    assert Path(data["parentDir"]) == proj.resolve()
    assert data["vaultDir"] is None


def test_build_settings_with_vault(tmp_path):
    proj = tmp_path / "Projects"
    vault = tmp_path / "Vault"
    proj.mkdir()
    vault.mkdir()
    data = ks.build_settings(proj, vault)
    assert Path(data["vaultDir"]) == vault.resolve()


def test_missing_parent_raises():
    with pytest.raises(ValueError):
        ks.build_settings("")
    with pytest.raises(ValueError):
        ks.build_settings("   ")


def test_traversal_rejected(tmp_path):
    with pytest.raises(ValueError):
        ks.build_settings(tmp_path / ".." / "evil")


def test_write_read_roundtrip(tmp_path):
    proj = tmp_path / "Projects"
    proj.mkdir()
    p = ks.write_settings(proj, home=tmp_path)
    assert p == tmp_path / ks.SETTINGS_FILENAME
    back = ks.read_settings(home=tmp_path)
    assert Path(back["parentDir"]) == proj.resolve()
    # file is valid JSON on disk
    assert json.loads(p.read_text(encoding="utf-8"))["settingsVersion"] == 1


def test_read_absent_returns_empty(tmp_path):
    assert ks.read_settings(home=tmp_path) == {}


def test_write_rejects_nonexistent_parent(tmp_path):
    # DESIGN §4: a parentDir that isn't an existing directory is rejected at write
    with pytest.raises(ValueError, match="parentDir"):
        ks.write_settings(tmp_path / "nope", home=tmp_path)


def test_write_rejects_nonexistent_vault(tmp_path):
    proj = tmp_path / "Projects"
    proj.mkdir()
    with pytest.raises(ValueError, match="vaultDir"):
        ks.write_settings(proj, vault_dir=tmp_path / "no-vault", home=tmp_path)


def test_confirmed_platforms_add_and_read(tmp_path):
    assert ks.confirmed_platforms(home=tmp_path) == []
    ks.add_confirmed_platform("codex", home=tmp_path)
    ks.add_confirmed_platform("codex", home=tmp_path)  # idempotent
    ks.add_confirmed_platform("kiro", home=tmp_path)
    assert ks.confirmed_platforms(home=tmp_path) == ["codex", "kiro"]


def test_add_confirmed_blank_rejected(tmp_path):
    with pytest.raises(ValueError):
        ks.add_confirmed_platform("  ", home=tmp_path)


def test_harness_home_env_override(tmp_path, monkeypatch):
    monkeypatch.setenv("KATA_HOME", str(tmp_path))
    assert ks.harness_home() == tmp_path.resolve()


def test_harness_home_self_locate(monkeypatch):
    monkeypatch.delenv("KATA_HOME", raising=False)
    home = ks.harness_home()
    # self-locate: the repo root that contains tools/ and skills/
    assert (home / "tools").is_dir()
    assert (home / "skills").is_dir()


def test_settings_path_location(tmp_path):
    assert ks.settings_path(home=tmp_path) == tmp_path / ".kata-settings.json"


# ---------------------------------------------------------------------------
# New TDD tests for write_settings MERGE-fix (FREEZE-write-settings-merge.md)
# ---------------------------------------------------------------------------


def test_write_preserves_confirmed_platforms(tmp_path):
    """A --parent-dir reconfigure must not erase prior confirmedPlatforms."""
    proj = tmp_path / "proj"
    proj.mkdir()
    ks.add_confirmed_platform("codex", home=tmp_path)
    ks.add_confirmed_platform("kiro", home=tmp_path)
    ks.write_settings(proj, home=tmp_path)
    back = ks.read_settings(home=tmp_path)
    assert back["confirmedPlatforms"] == ["codex", "kiro"]
    assert Path(back["parentDir"]) == proj.resolve()


def test_write_updates_owned_keys(tmp_path):
    """Owned keys (parentDir, vaultDir, settingsVersion) must still update correctly."""
    proj1 = tmp_path / "proj1"
    proj2 = tmp_path / "proj2"
    vault = tmp_path / "vault"
    proj1.mkdir()
    proj2.mkdir()
    vault.mkdir()

    ks.write_settings(proj1, home=tmp_path)
    back = ks.read_settings(home=tmp_path)
    assert Path(back["parentDir"]) == proj1.resolve()
    assert back["vaultDir"] is None

    ks.write_settings(proj2, vault_dir=vault, home=tmp_path)
    back = ks.read_settings(home=tmp_path)
    assert Path(back["parentDir"]) == proj2.resolve()
    assert Path(back["vaultDir"]) == vault.resolve()
    assert back["settingsVersion"] == ks.SETTINGS_VERSION


def test_write_preserves_vault_dir_when_absent(tmp_path):
    """A second write without vault_dir must preserve the prior vaultDir."""
    proj1 = tmp_path / "proj1"
    proj2 = tmp_path / "proj2"
    vault = tmp_path / "vault"
    proj1.mkdir()
    proj2.mkdir()
    vault.mkdir()

    ks.write_settings(proj1, vault_dir=vault, home=tmp_path)
    ks.write_settings(proj2, home=tmp_path)  # no vault supplied
    back = ks.read_settings(home=tmp_path)
    assert Path(back["vaultDir"]) == vault.resolve()  # preserved
    assert Path(back["parentDir"]) == proj2.resolve()  # updated


def test_write_updates_vault_when_supplied(tmp_path):
    """An explicit vault_dir replaces the prior on-disk vaultDir (owned-set wins)."""
    proj = tmp_path / "proj"
    vault1 = tmp_path / "vault1"
    vault2 = tmp_path / "vault2"
    proj.mkdir()
    vault1.mkdir()
    vault2.mkdir()

    ks.write_settings(proj, vault_dir=vault1, home=tmp_path)
    ks.write_settings(proj, vault_dir=vault2, home=tmp_path)
    back = ks.read_settings(home=tmp_path)
    assert Path(back["vaultDir"]) == vault2.resolve()

    # Also check fresh install (no prior): no vault → vaultDir is None
    fresh = tmp_path / "fresh_home"
    fresh.mkdir()
    ks.write_settings(proj, home=fresh)
    back2 = ks.read_settings(home=fresh)
    assert back2["vaultDir"] is None


def test_write_corrupt_file_fails_closed(tmp_path):
    """A corrupt (unparseable) settings file must cause ValueError; file unchanged."""
    proj = tmp_path / "proj"
    proj.mkdir()
    sp = ks.settings_path(home=tmp_path)
    garbage = "{not json"
    sp.write_text(garbage, encoding="utf-8")

    with pytest.raises(ValueError):
        ks.write_settings(proj, home=tmp_path)

    # File must be unchanged on disk (not clobbered)
    assert sp.read_text(encoding="utf-8") == garbage


def test_write_non_dict_file_fails_closed(tmp_path):
    """Valid JSON that is not a dict (e.g. []) must also fail-closed (major fold-in)."""
    proj = tmp_path / "proj"
    proj.mkdir()
    sp = ks.settings_path(home=tmp_path)
    content = "[]"
    sp.write_text(content, encoding="utf-8")

    with pytest.raises(ValueError):
        ks.write_settings(proj, home=tmp_path)

    assert sp.read_text(encoding="utf-8") == content


def test_write_preserves_unknown_key(tmp_path):
    """Unknown / future keys in the settings file must survive a write_settings call."""
    proj = tmp_path / "proj"
    proj.mkdir()
    sp = ks.settings_path(home=tmp_path)
    seed = {
        "settingsVersion": 1,
        "confirmedPlatforms": [],
        "futureKey": "keep-me",
    }
    sp.write_text(json.dumps(seed, indent=2) + "\n", encoding="utf-8")

    ks.write_settings(proj, home=tmp_path)
    back = ks.read_settings(home=tmp_path)
    assert back["futureKey"] == "keep-me"


# ---------------------------------------------------------------------------
# CA-P0 / E2 — context-autonomy per-install keys (CA-L35..L37, CA-A6, CA-A11(e))
# ---------------------------------------------------------------------------


def _stamp(home, git_sha):
    """Write a minimal .kata-version stamp with the given gitSha for tests."""
    return kata_version.write_stamp(
        home,
        git_sha=git_sha,
        suite_semver="0.2.1",
        ref="master",
        link_mode="symlink",
        platform="claude",
    )


# --- delete_settings_key: fail-closed key delete (CA-L36 named build item) ---


def test_delete_key_present_removes_and_returns_true(tmp_path):
    ks.record_first_run("deadbeef", home=tmp_path)
    assert ks.delete_settings_key("firstRunCompletedAt", home=tmp_path) is True
    back = ks.read_settings(home=tmp_path)
    assert "firstRunCompletedAt" not in back
    # sibling key untouched
    assert back["firstRunVersion"] == "deadbeef"


def test_delete_key_absent_returns_false_no_write(tmp_path):
    ks.record_first_run("deadbeef", home=tmp_path)
    sp = ks.settings_path(home=tmp_path)
    before = sp.read_text(encoding="utf-8")
    assert ks.delete_settings_key("noSuchKey", home=tmp_path) is False
    assert sp.read_text(encoding="utf-8") == before  # no write


def test_delete_key_on_absent_file_returns_false(tmp_path):
    # No settings file at all ⇒ nothing to delete, no write, no raise.
    assert ks.delete_settings_key("firstRunCompletedAt", home=tmp_path) is False
    assert not ks.settings_path(home=tmp_path).exists()


def test_delete_key_corrupt_file_fails_closed(tmp_path):
    sp = ks.settings_path(home=tmp_path)
    garbage = "{not json"
    sp.write_text(garbage, encoding="utf-8")
    with pytest.raises(ValueError):
        ks.delete_settings_key("firstRunCompletedAt", home=tmp_path)
    # File byte-unchanged (fail-closed, C-4)
    assert sp.read_text(encoding="utf-8") == garbage


def test_delete_key_blank_rejected(tmp_path):
    with pytest.raises(ValueError):
        ks.delete_settings_key("  ", home=tmp_path)


# --- record_first_run: the force-run marker writer (C-4 fail-closed) ---


def test_record_first_run_writes_both_keys(tmp_path):
    ks.record_first_run("abc123", home=tmp_path)
    back = ks.read_settings(home=tmp_path)
    assert back["firstRunVersion"] == "abc123"
    assert isinstance(back["firstRunCompletedAt"], str) and back["firstRunCompletedAt"]
    assert back["settingsVersion"] == ks.SETTINGS_VERSION


def test_record_first_run_blank_sha_rejected(tmp_path):
    with pytest.raises(ValueError):
        ks.record_first_run("", home=tmp_path)
    with pytest.raises(ValueError):
        ks.record_first_run(None, home=tmp_path)


def test_record_first_run_preserves_existing_keys(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    ks.write_settings(proj, home=tmp_path)
    ks.add_confirmed_platform("codex", home=tmp_path)
    ks.record_first_run("sha1", home=tmp_path)
    back = ks.read_settings(home=tmp_path)
    assert back["confirmedPlatforms"] == ["codex"]
    assert Path(back["parentDir"]) == proj.resolve()
    assert back["firstRunVersion"] == "sha1"


def test_record_first_run_corrupt_file_fails_closed(tmp_path):
    sp = ks.settings_path(home=tmp_path)
    garbage = "{broken"
    sp.write_text(garbage, encoding="utf-8")
    with pytest.raises(ValueError):
        ks.record_first_run("sha1", home=tmp_path)
    assert sp.read_text(encoding="utf-8") == garbage


# --- first_run_required: the CA-L36 comparator (CA-A11(e) re-arm matrix) ---


def test_first_run_required_marker_absent(tmp_path):
    _stamp(tmp_path, "aaaa1111")
    out = ks.first_run_required(home=tmp_path)
    assert out == {"required": True, "reason": "marker-absent", "clause_skipped": False}


def test_first_run_required_marker_present_sha_equal(tmp_path):
    _stamp(tmp_path, "aaaa1111")
    ks.record_first_run("aaaa1111", home=tmp_path)
    out = ks.first_run_required(home=tmp_path)
    assert out == {"required": False, "reason": None, "clause_skipped": False}


def test_first_run_required_marker_present_sha_changed(tmp_path):
    _stamp(tmp_path, "aaaa1111")
    ks.record_first_run("aaaa1111", home=tmp_path)
    _stamp(tmp_path, "bbbb2222")  # upgrade re-arms
    out = ks.first_run_required(home=tmp_path)
    assert out == {"required": True, "reason": "sha-mismatch", "clause_skipped": False}


def test_first_run_required_stamp_absent_clause_skipped(tmp_path):
    # Marker present but NO stamp ⇒ version clause skipped ⇒ marker governs ⇒ not required.
    ks.record_first_run("aaaa1111", home=tmp_path)
    out = ks.first_run_required(home=tmp_path)
    assert out == {"required": False, "reason": None, "clause_skipped": True}


def test_first_run_required_stamp_unknown_clause_skipped(tmp_path):
    _stamp(tmp_path, "unknown")
    ks.record_first_run("whatever", home=tmp_path)
    out = ks.first_run_required(home=tmp_path)
    assert out == {"required": False, "reason": None, "clause_skipped": True}


def test_first_run_required_marker_absent_stamp_unknown(tmp_path):
    # Marker absence alone forces, even when the version clause is skipped.
    _stamp(tmp_path, "unknown")
    out = ks.first_run_required(home=tmp_path)
    assert out == {"required": True, "reason": "marker-absent", "clause_skipped": True}


def test_first_run_required_corrupt_settings_single_pass(tmp_path):
    """C-3: corrupt settings ⇒ lenient READ forces (marker-absent) AND the paired
    WRITE fail-closes — the single-pass contract, never a loop."""
    _stamp(tmp_path, "aaaa1111")
    sp = ks.settings_path(home=tmp_path)
    garbage = "{corrupt"
    sp.write_text(garbage, encoding="utf-8")
    # Lenient read ⇒ marker reads absent ⇒ forced.
    out = ks.first_run_required(home=tmp_path)
    assert out["required"] is True and out["reason"] == "marker-absent"
    # Paired write fail-closes on the SAME corrupt file (caller surfaces + stops).
    with pytest.raises(ValueError):
        ks.record_first_run("aaaa1111", home=tmp_path)
    assert sp.read_text(encoding="utf-8") == garbage  # never clobbered


# --- record_host_posture: AUDIT-ONLY, last-write-wins (CA-L37/R-42) ---


def test_record_host_posture_roundtrip(tmp_path):
    posture = {
        "autoCompactChecked": True,
        "recommendedWindowTokens": 120000,
        "bridgeMode": "chained",
    }
    ks.record_host_posture(posture, home=tmp_path)
    back = ks.read_settings(home=tmp_path)["hostPosture"]
    assert back == posture


def test_record_host_posture_null_window_allowed(tmp_path):
    posture = {
        "autoCompactChecked": False,
        "recommendedWindowTokens": None,
        "bridgeMode": "none",
    }
    ks.record_host_posture(posture, home=tmp_path)
    assert ks.read_settings(home=tmp_path)["hostPosture"] == posture


def test_record_host_posture_last_write_wins(tmp_path):
    ks.record_host_posture(
        {"autoCompactChecked": True, "recommendedWindowTokens": 1, "bridgeMode": "chained"},
        home=tmp_path,
    )
    ks.record_host_posture(
        {"autoCompactChecked": False, "recommendedWindowTokens": 2, "bridgeMode": "user-only"},
        home=tmp_path,
    )
    back = ks.read_settings(home=tmp_path)["hostPosture"]
    assert back["bridgeMode"] == "user-only" and back["recommendedWindowTokens"] == 2


@pytest.mark.parametrize(
    "bad",
    [
        {"autoCompactChecked": "yes", "recommendedWindowTokens": 1, "bridgeMode": "none"},
        {"autoCompactChecked": True, "recommendedWindowTokens": 1.5, "bridgeMode": "none"},
        {"autoCompactChecked": True, "recommendedWindowTokens": True, "bridgeMode": "none"},
        {"autoCompactChecked": True, "recommendedWindowTokens": 1, "bridgeMode": "bogus"},
        {"autoCompactChecked": True, "recommendedWindowTokens": 1},  # missing bridgeMode
        ["not", "a", "dict"],
    ],
)
def test_record_host_posture_malformed_raises(tmp_path, bad):
    with pytest.raises(ValueError):
        ks.record_host_posture(bad, home=tmp_path)


def test_record_host_posture_corrupt_file_fails_closed(tmp_path):
    sp = ks.settings_path(home=tmp_path)
    garbage = "{corrupt"
    sp.write_text(garbage, encoding="utf-8")
    with pytest.raises(ValueError):
        ks.record_host_posture(
            {"autoCompactChecked": True, "recommendedWindowTokens": 1, "bridgeMode": "none"},
            home=tmp_path,
        )
    assert sp.read_text(encoding="utf-8") == garbage


# --- record_accepted_defaults: AUDIT-ONLY, per-item last-write-wins (C-1) ---


def test_record_accepted_defaults_roundtrip_and_merge(tmp_path):
    ks.record_accepted_defaults(
        {"bundleA": {"value": 42, "v": "0.2.1", "at": "2026-07-04T00:00:00Z"}},
        home=tmp_path,
    )
    ks.record_accepted_defaults(
        {"bundleB": {"value": "x", "v": "0.2.1", "at": "2026-07-04T01:00:00Z"}},
        home=tmp_path,
    )
    back = ks.read_settings(home=tmp_path)["acceptedDefaults"]
    assert set(back) == {"bundleA", "bundleB"}  # accumulated
    assert back["bundleA"]["value"] == 42


def test_record_accepted_defaults_item_last_write_wins(tmp_path):
    ks.record_accepted_defaults(
        {"bundleA": {"value": 1, "v": "0.2.1", "at": "2026-07-04T00:00:00Z"}},
        home=tmp_path,
    )
    ks.record_accepted_defaults(
        {"bundleA": {"value": 99, "v": "0.2.2", "at": "2026-07-04T02:00:00Z"}},
        home=tmp_path,
    )
    back = ks.read_settings(home=tmp_path)["acceptedDefaults"]["bundleA"]
    assert back["value"] == 99 and back["v"] == "0.2.2"


@pytest.mark.parametrize(
    "bad",
    [
        {"bundleA": "not-a-dict"},
        {"bundleA": {"v": "0.2.1", "at": "2026-07-04T00:00:00Z"}},  # missing value
        {"bundleA": {"value": 1, "at": "2026-07-04T00:00:00Z"}},  # missing v
        {"bundleA": {"value": 1, "v": "0.2.1"}},  # missing at
        {"bundleA": {"value": 1, "v": 2, "at": "x"}},  # v not str
        ["not", "a", "dict"],
    ],
)
def test_record_accepted_defaults_malformed_raises(tmp_path, bad):
    with pytest.raises(ValueError):
        ks.record_accepted_defaults(bad, home=tmp_path)


def test_record_accepted_defaults_corrupt_file_fails_closed(tmp_path):
    sp = ks.settings_path(home=tmp_path)
    garbage = "{corrupt"
    sp.write_text(garbage, encoding="utf-8")
    with pytest.raises(ValueError):
        ks.record_accepted_defaults(
            {"bundleA": {"value": 1, "v": "0.2.1", "at": "2026-07-04T00:00:00Z"}},
            home=tmp_path,
        )
    assert sp.read_text(encoding="utf-8") == garbage
