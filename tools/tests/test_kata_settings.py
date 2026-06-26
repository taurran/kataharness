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
