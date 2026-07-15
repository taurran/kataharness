"""Tests for the PokeVault second-brain recommendation engine (second-brain-target S1 / T1).

PURE except the tmp_path fixture (used as a fake harness home) and the .kata-version
stamp writer helper. Mirrors the house style in test_kata_settings.py.

Coverage (PLAN T1 required set):
- recommend on empty settings (no vault, no decline)
- no-recommend when vaultDir is set
- no-recommend under a live remembered decline
- a LAPSED decline re-arms on gitSha mismatch (upgrade)
- an `unknown`-sha stamp SKIPS the version clause ⇒ the decline HOLDS
- corrupt settings ⇒ lenient read ⇒ recommend (WRITE stays fail-closed)
- AC1: default_learn_feed_dir seeds correctly from a CUSTOM (non-PokeVault) vaultDir
Plus record_vault_decline schema / stamp / fail-closed coverage and the constant link.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import kata_settings as ks
import kata_version

POKEVAULT_LINK = "https://github.com/taurran/pokevault"


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


# --- vault_recommendation: the pure decision (S1) --------------------------


def test_recommend_on_empty_settings(tmp_path):
    """No vault + no decline ⇒ recommend, with reason + the PokeVault link."""
    out = ks.vault_recommendation({}, home=tmp_path)
    assert out["recommend"] is True
    assert out["link"] == POKEVAULT_LINK
    assert isinstance(out["reason"], str) and out["reason"]


def test_no_recommend_when_vault_set(tmp_path):
    """A configured vaultDir ⇒ nothing to recommend."""
    out = ks.vault_recommendation({"vaultDir": str(tmp_path)}, home=tmp_path)
    assert out["recommend"] is False
    assert out["link"] == POKEVAULT_LINK


def test_no_recommend_under_live_decline(tmp_path):
    """A remembered decline recorded under the current stamp HOLDS ⇒ no recommend."""
    _stamp(tmp_path, "aaaa1111")
    ks.record_vault_decline(home=tmp_path)
    settings = ks.read_settings(home=tmp_path)
    out = ks.vault_recommendation(settings, home=tmp_path)
    assert out["recommend"] is False


def test_lapsed_decline_rearms_on_sha_mismatch(tmp_path):
    """An upgrade (stamp gitSha changes) LAPSES the decline ⇒ recommend again."""
    _stamp(tmp_path, "aaaa1111")
    ks.record_vault_decline(home=tmp_path)
    _stamp(tmp_path, "bbbb2222")  # upgrade re-arms
    settings = ks.read_settings(home=tmp_path)
    out = ks.vault_recommendation(settings, home=tmp_path)
    assert out["recommend"] is True


def test_unknown_sha_skip_holds_decline(tmp_path):
    """Stamp gitSha == 'unknown' ⇒ version clause skipped ⇒ the decline HOLDS."""
    _stamp(tmp_path, "unknown")
    ks.record_vault_decline(home=tmp_path)  # v recorded as "unknown"
    settings = ks.read_settings(home=tmp_path)
    assert settings["acceptedDefaults"]["vault-recommendation"]["v"] == "unknown"
    out = ks.vault_recommendation(settings, home=tmp_path)
    assert out["recommend"] is False


def test_corrupt_settings_lenient_read_recommends(tmp_path):
    """A corrupt settings file reads leniently as {} ⇒ no decline ⇒ recommend."""
    sp = ks.settings_path(home=tmp_path)
    sp.write_text("{corrupt", encoding="utf-8")
    settings = ks.read_settings(home=tmp_path)  # lenient degrade to {}
    assert settings == {}
    out = ks.vault_recommendation(settings, home=tmp_path)
    assert out["recommend"] is True


def test_recommendation_always_carries_pokevault_link(tmp_path):
    """Every branch returns the PokeVault repo link (recommend or not)."""
    rec = ks.vault_recommendation({}, home=tmp_path)
    not_rec = ks.vault_recommendation({"vaultDir": str(tmp_path)}, home=tmp_path)
    assert rec["link"] == not_rec["link"] == POKEVAULT_LINK


def test_non_dict_settings_read_leniently(tmp_path):
    """A non-dict settings arg degrades to {} (no decline) ⇒ recommend."""
    out = ks.vault_recommendation(None, home=tmp_path)
    assert out["recommend"] is True


# --- record_vault_decline: the thin fail-closed writer ---------------------


def test_record_vault_decline_writes_schema(tmp_path):
    """The decline lands in acceptedDefaults under the C-1 schema, v = stamp gitSha."""
    _stamp(tmp_path, "abc123")
    ks.record_vault_decline(home=tmp_path)
    entry = ks.read_settings(home=tmp_path)["acceptedDefaults"]["vault-recommendation"]
    assert entry["value"] == "declined"
    assert entry["v"] == "abc123"
    assert isinstance(entry["at"], str) and entry["at"]


def test_record_vault_decline_no_stamp_records_unknown(tmp_path):
    """No comparable stamp ⇒ v is recorded as 'unknown' (the decline then holds)."""
    ks.record_vault_decline(home=tmp_path)
    entry = ks.read_settings(home=tmp_path)["acceptedDefaults"]["vault-recommendation"]
    assert entry["v"] == "unknown"


def test_record_vault_decline_preserves_other_accepted_defaults(tmp_path):
    """The wrapper merges — it must not clobber sibling acceptedDefaults items."""
    ks.record_accepted_defaults(
        {"bundleA": {"value": 1, "v": "0.2.1", "at": "2026-07-04T00:00:00Z"}},
        home=tmp_path,
    )
    ks.record_vault_decline(home=tmp_path)
    accepted = ks.read_settings(home=tmp_path)["acceptedDefaults"]
    assert set(accepted) == {"bundleA", "vault-recommendation"}


def test_record_vault_decline_corrupt_file_fails_closed(tmp_path):
    """Fail-closed inherited from record_accepted_defaults: corrupt ⇒ ValueError, file untouched."""
    sp = ks.settings_path(home=tmp_path)
    garbage = "{corrupt"
    sp.write_text(garbage, encoding="utf-8")
    with pytest.raises(ValueError):
        ks.record_vault_decline(home=tmp_path)
    assert sp.read_text(encoding="utf-8") == garbage  # byte-unchanged


def test_record_then_recommend_roundtrip_holds(tmp_path):
    """End-to-end: record a decline, then the recommendation reads it back as HELD."""
    _stamp(tmp_path, "cafe0001")
    assert ks.vault_recommendation(ks.read_settings(home=tmp_path), home=tmp_path)["recommend"] is True
    ks.record_vault_decline(home=tmp_path)
    assert ks.vault_recommendation(ks.read_settings(home=tmp_path), home=tmp_path)["recommend"] is False


# --- AC1: seeding from a CUSTOM vault path (any user vault, not just PokeVault) ---


def test_ac1_default_learn_feed_dir_seeds_from_custom_vault(tmp_path):
    """AC1: default_learn_feed_dir seeds the synthesis dir from ANY custom vaultDir."""
    custom = tmp_path / "my-own-notes-vault"
    settings = {"vaultDir": str(custom)}
    out = ks.default_learn_feed_dir(settings)
    expected = custom.resolve() / "second-brain" / "wiki" / "pages" / "synthesis"
    assert out == str(expected)
    assert Path(out).is_absolute()
