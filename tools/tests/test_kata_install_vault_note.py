"""test_kata_install_vault_note.py — TDD for second-brain-target S2.

The PokeVault recommendation NOTE on the plain-install path of ``kata_install.main``
(DESIGN S2, PLAN T2). The note is a one-line stderr message (NEVER a prompt) plus a
``vault_recommendation`` field riding the plain-install result dict. It fires IFF the
effective ``vault_dir`` is unset AND ``kata_settings.vault_recommendation`` recommends
(vaultDir unset in settings AND no un-lapsed remembered decline). The note records
NOTHING — only the interactive skill-surface decline (S3) writes a decline.

File ownership: T2's NEW test file only. Does NOT modify any existing kata_install
test. Mirrors the fake_home fixture + _parse_result_json helper from
test_install_cli_headless.py so this file has zero cross-file fixture dependencies.

Coverage (PLAN T2):
- note emitted on a vaultless plain install (stderr note + result field)
- note/field absent when vaultDir is set
- note/field absent under a live remembered decline
- --json carries the vault_recommendation field (pure-JSON stdout; note on stderr)
- exit codes unchanged (note present vs. suppressed both exit 0)
- VERB-EXCLUSION (freeze-gate HIGH-2 fold): note AND field absent under --update,
  --uninstall, --confirm, --factory-reset even with vaultDir unset + KATA_PARENT_DIR set.
"""

from __future__ import annotations

import json

import pytest

import kata_install as ki

_POKEVAULT_LINK = "https://github.com/taurran/pokevault"


# ---------------------------------------------------------------------------
# Shared fixture (local copy of fake_home; mirrors test_install_cli_headless.py)
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_home(tmp_path):
    """A minimal harness home: two category-nested skills + one module skill."""
    home = tmp_path / "KataHarness"
    (home / "skills" / "coordinate" / "kata-bootstrap").mkdir(parents=True)
    (home / "skills" / "coordinate" / "kata-bootstrap" / "SKILL.md").write_text(
        "---\nname: kata-bootstrap\n---\n", encoding="utf-8"
    )
    (home / "skills" / "plan" / "kata-grill-standard").mkdir(parents=True)
    (home / "skills" / "plan" / "kata-grill-standard" / "SKILL.md").write_text(
        "---\nname: kata-grill-standard\n---\n", encoding="utf-8"
    )
    (home / "modules" / "closeout" / "kata-closeout").mkdir(parents=True)
    (home / "modules" / "closeout" / "kata-closeout" / "SKILL.md").write_text(
        "---\nname: kata-closeout\n---\n", encoding="utf-8"
    )
    (home / "README.md").write_text("# KataHarness v0.1.0-alpha.3\n", encoding="utf-8")
    return home


def _parse_result_json(stdout: str) -> dict:
    """Extract the first JSON object from a mixed stdout (JSON + note lines + banner)."""
    decoder = json.JSONDecoder()
    result, _ = decoder.raw_decode(stdout.lstrip())
    return result


# ---------------------------------------------------------------------------
# Note emitted on a vaultless plain install
# ---------------------------------------------------------------------------


def test_note_emitted_on_vaultless_plain_install(fake_home, tmp_path, capsys):
    """No vault + no decline ⇒ one-line stderr note + vault_recommendation field."""
    host = tmp_path / "dot-claude"
    rc = ki.main(
        ["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)]
    )
    assert rc == 0
    out, err = capsys.readouterr()

    # A single stderr note recommending PokeVault, framed as optional.
    assert "PokeVault" in err
    assert _POKEVAULT_LINK in err
    assert "optional" in err.lower()
    assert err.count("\n") == 1  # exactly one line

    # The field rides the plain-install result dict (surfaced on stdout here).
    result = _parse_result_json(out)
    assert result["vault_recommendation"]["recommend"] is True
    assert result["vault_recommendation"]["link"] == _POKEVAULT_LINK


def test_note_is_on_stderr_not_stdout(fake_home, tmp_path, capsys):
    """The human note text lives on stderr — stdout carries only the JSON+banner."""
    host = tmp_path / "dot-claude"
    ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])
    out, err = capsys.readouterr()
    assert "PokeVault" in err
    assert "note: a second brain is optional" not in out


# ---------------------------------------------------------------------------
# Note/field ABSENT when a vault is configured
# ---------------------------------------------------------------------------


def test_note_absent_when_vault_dir_set(fake_home, tmp_path, capsys):
    """An effective vault_dir (--vault-dir) suppresses the note and the field."""
    host = tmp_path / "dot-claude"
    parent = tmp_path / "projects"
    parent.mkdir()
    vault = tmp_path / "vault"
    vault.mkdir()
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--parent-dir", str(parent),
            "--vault-dir", str(vault),
        ]
    )
    assert rc == 0
    out, err = capsys.readouterr()
    assert "PokeVault" not in err
    # Field absent from the result dict (string check — stdout also carries the
    # "settings: wrote" line, so raw_decode of the leading token is not applicable).
    assert "vault_recommendation" not in out


# ---------------------------------------------------------------------------
# Note/field ABSENT under a live remembered decline
# ---------------------------------------------------------------------------


def test_note_absent_under_live_decline(fake_home, tmp_path, capsys):
    """A remembered decline (dev-posture hold: no stamp ⇒ clause skipped) suppresses it."""
    import kata_settings as ks

    ks.record_vault_decline(home=fake_home)
    host = tmp_path / "dot-claude"
    rc = ki.main(
        ["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)]
    )
    assert rc == 0
    out, err = capsys.readouterr()
    assert "PokeVault" not in err
    assert "vault_recommendation" not in out


# ---------------------------------------------------------------------------
# --json carries the field (pure-JSON stdout; note on stderr)
# ---------------------------------------------------------------------------


def test_json_carries_vault_recommendation_field(fake_home, tmp_path, capsys):
    """--json ⇒ the field is inside the pure-JSON stdout; the note stays on stderr."""
    host = tmp_path / "dot-claude"
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--json",
        ]
    )
    assert rc == 0
    out, err = capsys.readouterr()

    result = json.loads(out)  # raises if stdout is not pure JSON
    assert result["vault_recommendation"]["recommend"] is True
    assert result["vault_recommendation"]["link"] == _POKEVAULT_LINK
    # Human note remains on stderr, never on the --json stdout channel.
    assert "PokeVault" in err
    assert "PokeVault" not in out


# ---------------------------------------------------------------------------
# Exit codes unchanged (note present vs. suppressed)
# ---------------------------------------------------------------------------


def test_exit_code_unchanged_with_and_without_note(fake_home, tmp_path, capsys):
    """The note does not alter the exit code: both the note and the suppressed
    (declined) install exit 0."""
    import kata_settings as ks

    host_note = tmp_path / "dot-claude-note"
    rc_note = ki.main(
        ["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host_note)]
    )
    capsys.readouterr()
    assert rc_note == 0

    ks.record_vault_decline(home=fake_home)  # suppress on the next run
    host_quiet = tmp_path / "dot-claude-quiet"
    rc_quiet = ki.main(
        ["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host_quiet)]
    )
    _, err = capsys.readouterr()
    assert rc_quiet == 0
    assert "PokeVault" not in err  # suppressed by the decline


# ---------------------------------------------------------------------------
# VERB-EXCLUSION (freeze-gate HIGH-2 fold): note AND field absent under every verb
# even with vaultDir unset AND KATA_PARENT_DIR set (which alone WOULD recommend).
# ---------------------------------------------------------------------------


def test_verb_exclusion_update(fake_home, tmp_path, capsys, monkeypatch):
    """--update never emits the note/field (returns before the plain-install path)."""
    parent = tmp_path / "projects"
    parent.mkdir()
    monkeypatch.setenv("KATA_PARENT_DIR", str(parent))
    host = tmp_path / "dot-claude"
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--update",
        ]
    )
    out, err = capsys.readouterr()
    assert rc == 0
    assert "PokeVault" not in err
    assert "vault_recommendation" not in out


def test_verb_exclusion_uninstall(fake_home, tmp_path, capsys, monkeypatch):
    """--uninstall never emits the note/field."""
    parent = tmp_path / "projects"
    parent.mkdir()
    monkeypatch.setenv("KATA_PARENT_DIR", str(parent))
    host = tmp_path / "dot-claude"
    ki.install("claude", harness_home=fake_home, host_dir=host)
    capsys.readouterr()
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--uninstall",
        ]
    )
    out, err = capsys.readouterr()
    assert rc == 0
    assert "PokeVault" not in err
    assert "vault_recommendation" not in out


def test_verb_exclusion_confirm(fake_home, tmp_path, capsys, monkeypatch):
    """--confirm never emits the note/field (probe result, not the install result)."""
    parent = tmp_path / "projects"
    parent.mkdir()
    monkeypatch.setenv("KATA_PARENT_DIR", str(parent))
    # codex is not on PATH in CI ⇒ probe not confirmed ⇒ exit 1, prints the probe dict.
    rc = ki.main(["--platform", "codex", "--home", str(fake_home), "--confirm"])
    out, err = capsys.readouterr()
    assert rc == 1
    assert "PokeVault" not in err
    assert "vault_recommendation" not in out


def test_verb_exclusion_factory_reset(fake_home, tmp_path, capsys, monkeypatch):
    """--factory-reset never emits the note/field."""
    parent = tmp_path / "projects"
    parent.mkdir()
    monkeypatch.setenv("KATA_PARENT_DIR", str(parent))
    host = tmp_path / "dot-claude"
    ki.install("claude", harness_home=fake_home, host_dir=host)
    capsys.readouterr()
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--factory-reset",
        ]
    )
    out, err = capsys.readouterr()
    assert rc == 0
    assert "PokeVault" not in err
    assert "vault_recommendation" not in out
