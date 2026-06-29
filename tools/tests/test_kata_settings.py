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
