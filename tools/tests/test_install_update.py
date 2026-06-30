"""test_install_update.py — TDD for A2: install stamp (M1), --update, --factory-reset,
uninstall sweep, --dry-run, and exit-code table.

Task A2 of install-update-polish/PLAN.md.  The 5 frozen engine functions are never
modified — only new branches / helpers are exercised here.

Coverage:
- M1: plain install writes .kata-version (gitSha:"unknown") + .kata-manifest.json
- M1: stamp means adaptation_context will return "install" (stamp_path exists)
- M1: --git-sha flag records the supplied SHA
- --update: idempotent (re-run → exit 0, same links, structural stamp equality)
- --update: copy-mode re-copies stale host slot when source changes
- minor-a: hand-edited base skill surfaces drift NOTE on --update
- --factory-reset / --reinstall: re-links + re-stamps (Phase-A form)
- --factory-reset --hard: passthrough (no-op on overlay in Phase A)
- _sweep_managed_slots: removes orphaned kata symlinks; removes .kata-managed dirs;
  leaves non-kata dirs intact (fail-closed); dry_run=True classifies without mutating
- --dry-run: short-circuits before any mutation on update / factory-reset
- uninstall integration: sweep catches rename-orphans that basename loop misses
- Exit-code table: --update / --factory-reset return 0 on success, 3 on ok:False
- _materialize_pass: no-op when kata_overlay absent (Phase A stub)
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

import kata_install as ki
import kata_version as kv


# ---------------------------------------------------------------------------
# Shared fixture
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_home(tmp_path):
    """Minimal harness home: two category-nested skills + one module skill."""
    home = tmp_path / "KataHarness"
    (home / "skills" / "coordinate" / "kata-bootstrap").mkdir(parents=True)
    (home / "skills" / "coordinate" / "kata-bootstrap" / "SKILL.md").write_text(
        "---\nname: kata-bootstrap\ntags: [meta]\n---\nbody\n", encoding="utf-8"
    )
    (home / "skills" / "plan" / "kata-grill-standard").mkdir(parents=True)
    (home / "skills" / "plan" / "kata-grill-standard" / "SKILL.md").write_text(
        "---\nname: kata-grill-standard\ntags: [plan]\n---\nbody\n", encoding="utf-8"
    )
    (home / "modules" / "closeout" / "kata-closeout").mkdir(parents=True)
    (home / "modules" / "closeout" / "kata-closeout" / "SKILL.md").write_text(
        "---\nname: kata-closeout\ntags: [meta]\n---\nbody\n", encoding="utf-8"
    )
    (home / "README.md").write_text("# KataHarness v0.1.0-alpha.3\n", encoding="utf-8")
    return home


# ---------------------------------------------------------------------------
# M1 — plain install writes stamp + manifest
# ---------------------------------------------------------------------------


def test_plain_install_writes_stamp_with_unknown_sha(fake_home, tmp_path):
    """A plain install (no --git-sha) writes .kata-version with gitSha:'unknown'."""
    host = tmp_path / "dot-claude"
    rc = ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])
    assert rc == 0
    stamp = kv.read_stamp(fake_home)
    assert stamp, "stamp must be written after plain install"
    assert stamp["gitSha"] == "unknown"
    assert stamp["platform"] == "claude"
    assert stamp["schema"] == 1
    assert "installedAt" in stamp
    assert "linkMode" in stamp


def test_plain_install_writes_manifest(fake_home, tmp_path):
    """A plain install writes .kata-manifest.json with all skill hashes."""
    host = tmp_path / "dot-claude"
    rc = ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])
    assert rc == 0
    manifest = kv.read_manifest(fake_home)
    assert manifest, "manifest must be written after plain install"
    assert "skills" in manifest
    skill_names = set(manifest["skills"].keys())
    assert "kata-bootstrap" in skill_names
    assert "kata-grill-standard" in skill_names
    assert "kata-closeout" in skill_names
    assert manifest["gitSha"] == "unknown"


def test_plain_install_stamp_enables_adaptation_context(fake_home, tmp_path):
    """After plain install, .kata-version exists → adaptation_context returns 'install'."""
    host = tmp_path / "dot-claude"
    rc = ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])
    assert rc == 0
    # adaptation_context (kata_overlay, Phase B) checks: stamp_path(home).exists()
    assert kv.stamp_path(fake_home).exists(), (
        "stamp must exist so adaptation_context returns 'install'"
    )


def test_plain_install_with_git_sha_records_sha(fake_home, tmp_path):
    """--git-sha is accepted; the stamp records the supplied SHA."""
    host = tmp_path / "dot-claude"
    sha = "a" * 40
    rc = ki.main([
        "--platform", "claude",
        "--home", str(fake_home),
        "--host-dir", str(host),
        "--git-sha", sha,
    ])
    assert rc == 0
    stamp = kv.read_stamp(fake_home)
    assert stamp["gitSha"] == sha


def test_plain_install_git_sha_unknown_when_absent(fake_home, tmp_path):
    """Without --git-sha the stamp records gitSha:'unknown' (never computes a SHA)."""
    host = tmp_path / "dot-claude"
    ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])
    stamp = kv.read_stamp(fake_home)
    assert stamp["gitSha"] == "unknown"


def test_plain_install_manifest_git_sha_unknown_when_absent(fake_home, tmp_path):
    """Without --git-sha the manifest also records gitSha:'unknown'."""
    host = tmp_path / "dot-claude"
    ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])
    manifest = kv.read_manifest(fake_home)
    assert manifest["gitSha"] == "unknown"


# ---------------------------------------------------------------------------
# --update: idempotency + link mode + minor-a drift NOTE
# ---------------------------------------------------------------------------


def test_update_flag_exits_zero(fake_home, tmp_path):
    """--update on a valid platform exits 0."""
    host = tmp_path / "dot-claude"
    rc = ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--update",
    ])
    assert rc == 0


def test_update_flag_links_are_present(fake_home, tmp_path):
    """--update leaves skills accessible in the host dir."""
    host = tmp_path / "dot-claude"
    ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--update",
    ])
    assert (host / "skills" / "kata-bootstrap" / "SKILL.md").exists()
    assert (host / "skills" / "kata-closeout" / "SKILL.md").exists()


def test_update_idempotent_exit_zero_on_second_run(fake_home, tmp_path):
    """--update re-run exits 0 (idempotency: re-linking over existing links is clean)."""
    host = tmp_path / "dot-claude"
    ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])
    rc2 = ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--update",
    ])
    assert rc2 == 0


def test_update_idempotent_structural_stamp_equality(fake_home, tmp_path):
    """Two --update runs with same SHA produce structurally equal stamps (idempotent)."""
    host = tmp_path / "dot-claude"
    sha = "c" * 40
    ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])

    ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--update", "--git-sha", sha,
    ])
    stamp1 = kv.read_stamp(fake_home)

    ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--update", "--git-sha", sha,
    ])
    stamp2 = kv.read_stamp(fake_home)

    for key in ("gitSha", "platform", "linkMode", "schema"):
        assert stamp1[key] == stamp2[key], (
            f"stamp[{key!r}] changed between identical --update runs"
        )


def test_update_rewrites_stamp_with_provided_sha(fake_home, tmp_path):
    """--update --git-sha <sha> records the new SHA in the stamp."""
    host = tmp_path / "dot-claude"
    ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])

    new_sha = "b" * 40
    ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--update", "--git-sha", new_sha,
    ])
    stamp = kv.read_stamp(fake_home)
    assert stamp["gitSha"] == new_sha


def test_copy_mode_recopies_stale_slot_on_update(fake_home, tmp_path, monkeypatch):
    """In copy mode, --update re-copies all skills so the host slot reflects updated source."""
    def _deny_symlink(*a, **k):
        raise OSError("symlinks denied (copy-mode test)")
    monkeypatch.setattr(ki.os, "symlink", _deny_symlink)

    host = tmp_path / "dot-claude"
    ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])
    assert (host / "skills" / "kata-bootstrap" / ki._MARKER).exists()

    # Modify source skill content
    src = fake_home / "skills" / "coordinate" / "kata-bootstrap" / "SKILL.md"
    src.write_text("---\nname: kata-bootstrap\n---\nupdated body\n", encoding="utf-8")

    ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--update",
    ])

    dst = host / "skills" / "kata-bootstrap" / "SKILL.md"
    assert "updated body" in dst.read_text(encoding="utf-8"), (
        "--update must re-copy in copy mode so the host slot reflects the updated source"
    )


def test_minor_a_drift_note_on_update(fake_home, tmp_path, capsys):
    """minor-a: a hand-edited base skill surfaces a drift NOTE on --update."""
    host = tmp_path / "dot-claude"
    # First install writes baseline manifest
    ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])

    # Simulate hand-edit of a tracked base skill after install
    base_skill = fake_home / "skills" / "coordinate" / "kata-bootstrap" / "SKILL.md"
    base_skill.write_text("---\nname: kata-bootstrap\n---\nHAND EDITED\n", encoding="utf-8")

    capsys.readouterr()  # clear previous output
    ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--update",
    ])
    out, err = capsys.readouterr()
    combined = out + err
    assert "kata-bootstrap" in combined, (
        "A hand-edited tracked base skill must be mentioned in output on --update"
    )
    # At least one of the drift/NOTE signals must appear
    assert any(token in combined.lower() for token in ("drift", "note", "hand", "edited", "pristine")), (
        "minor-a: drift NOTE must appear on --update for a hand-edited base skill"
    )


# ---------------------------------------------------------------------------
# --factory-reset / --reinstall: re-links + re-stamps (Phase-A form)
# ---------------------------------------------------------------------------


def test_factory_reset_exits_zero(fake_home, tmp_path):
    """--factory-reset on a valid platform exits 0."""
    host = tmp_path / "dot-claude"
    rc = ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--factory-reset",
    ])
    assert rc == 0


def test_factory_reset_restores_links(fake_home, tmp_path):
    """--factory-reset re-links all skills."""
    host = tmp_path / "dot-claude"
    ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])
    ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--factory-reset",
    ])
    assert (host / "skills" / "kata-bootstrap" / "SKILL.md").exists()
    assert (host / "skills" / "kata-closeout" / "SKILL.md").exists()


def test_factory_reset_writes_stamp(fake_home, tmp_path):
    """--factory-reset re-writes the version stamp."""
    host = tmp_path / "dot-claude"
    ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--factory-reset",
    ])
    stamp = kv.read_stamp(fake_home)
    assert stamp, "stamp must be (re-)written by --factory-reset"
    assert stamp["schema"] == 1


def test_reinstall_alias_exits_zero(fake_home, tmp_path):
    """--reinstall is an alias for --factory-reset (Phase-A form); exits 0."""
    host = tmp_path / "dot-claude"
    rc = ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--reinstall",
    ])
    assert rc == 0
    assert (host / "skills" / "kata-bootstrap" / "SKILL.md").exists()


def test_factory_reset_hard_passthrough_exits_zero(fake_home, tmp_path):
    """--factory-reset --hard is a no-op on overlay in Phase A; exits 0."""
    host = tmp_path / "dot-claude"
    ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])
    rc = ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--factory-reset", "--hard",
    ])
    assert rc == 0
    # Skills still present; stamp refreshed
    assert (host / "skills" / "kata-closeout" / "SKILL.md").exists()
    stamp = kv.read_stamp(fake_home)
    assert stamp


# ---------------------------------------------------------------------------
# _sweep_managed_slots — orphan-link removal, fail-closed
# ---------------------------------------------------------------------------


def test_sweep_removes_orphaned_kata_symlink(fake_home, tmp_path):
    """_sweep_managed_slots removes a symlink pointing into home (orphaned kata link)."""
    host = tmp_path / "dot-claude"
    skills_dst = host / "skills"
    skills_dst.mkdir(parents=True)

    # The target already exists in fake_home (kata-bootstrap is created by the fixture).
    # We create a *different-named* symlink pointing at it (simulating a skill rename).
    target = fake_home / "skills" / "coordinate" / "kata-bootstrap"
    orphan = skills_dst / "kata-old-orphan"
    try:
        os.symlink(target, orphan, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not available on this platform")

    removed, left_intact = ki._sweep_managed_slots(skills_dst, fake_home)
    assert "kata-old-orphan" in removed
    assert not orphan.exists()
    assert not orphan.is_symlink()


def test_sweep_leaves_non_kata_dir_intact(fake_home, tmp_path):
    """_sweep_managed_slots never removes a non-kata dir (fail-closed)."""
    host = tmp_path / "dot-claude"
    skills_dst = host / "skills"
    skills_dst.mkdir(parents=True)

    non_kata = skills_dst / "user-own-skill"
    non_kata.mkdir()
    (non_kata / "README.md").write_text("user content", encoding="utf-8")

    removed, left_intact = ki._sweep_managed_slots(skills_dst, fake_home)
    assert "user-own-skill" not in removed
    assert non_kata.is_dir(), "non-kata dir must survive sweep"
    assert any("user-own-skill" in s for s in left_intact)


def test_sweep_removes_kata_managed_copy_dir(fake_home, tmp_path, monkeypatch):
    """_sweep_managed_slots removes a .kata-managed copy dir."""
    def _deny(*a, **k):
        raise OSError("no symlinks")
    monkeypatch.setattr(ki.os, "symlink", _deny)

    host = tmp_path / "dot-claude"
    ki.install("claude", harness_home=fake_home, host_dir=host)
    skills_dst = host / "skills"
    assert (skills_dst / "kata-bootstrap" / ki._MARKER).exists()

    removed, left_intact = ki._sweep_managed_slots(skills_dst, fake_home)
    assert "kata-bootstrap" in removed
    assert not (skills_dst / "kata-bootstrap").exists()


def test_sweep_dry_run_classifies_without_mutating(fake_home, tmp_path, monkeypatch):
    """_sweep_managed_slots dry_run=True returns names but does not remove anything."""
    def _deny(*a, **k):
        raise OSError("no symlinks — copy mode")
    monkeypatch.setattr(ki.os, "symlink", _deny)

    host = tmp_path / "dot-claude"
    ki.install("claude", harness_home=fake_home, host_dir=host)
    skills_dst = host / "skills"

    removed, _ = ki._sweep_managed_slots(skills_dst, fake_home, dry_run=True)
    assert len(removed) > 0, "dry_run should classify at least one would-remove entry"
    for name in removed:
        assert (skills_dst / name).is_dir() or (skills_dst / name).is_symlink(), (
            f"dry_run must not remove {name!r}"
        )


def test_sweep_nonexistent_host_dir_returns_empty(fake_home, tmp_path):
    """_sweep_managed_slots on a non-existent host skills dir returns empty lists."""
    no_dir = tmp_path / "does-not-exist" / "skills"
    removed, left_intact = ki._sweep_managed_slots(no_dir, fake_home)
    assert removed == []
    assert left_intact == []


# ---------------------------------------------------------------------------
# --dry-run: short-circuits before any mutation
# ---------------------------------------------------------------------------


def test_dry_run_on_update_mutates_nothing(fake_home, tmp_path):
    """--update --dry-run prints a plan but does not re-write stamp or links."""
    host = tmp_path / "dot-claude"
    ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])
    stamp_before = kv.read_stamp(fake_home)

    rc = ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--update", "--dry-run",
    ])
    assert rc == 0
    stamp_after = kv.read_stamp(fake_home)
    assert stamp_before.get("installedAt") == stamp_after.get("installedAt"), (
        "--dry-run must not re-write the stamp"
    )


def test_dry_run_on_factory_reset_mutates_nothing(fake_home, tmp_path):
    """--factory-reset --dry-run prints a plan but does not re-write stamp."""
    host = tmp_path / "dot-claude"
    ki.main(["--platform", "claude", "--home", str(fake_home), "--host-dir", str(host)])
    stamp_before = kv.read_stamp(fake_home)

    rc = ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--factory-reset", "--dry-run",
    ])
    assert rc == 0
    stamp_after = kv.read_stamp(fake_home)
    assert stamp_before.get("installedAt") == stamp_after.get("installedAt"), (
        "--dry-run --factory-reset must not re-write the stamp"
    )


# ---------------------------------------------------------------------------
# Exit-code table — new flags preserve existing semantic codes
# ---------------------------------------------------------------------------


def test_update_unknown_platform_exits_three(fake_home):
    """--update on an unknown platform → install ok:False → exit 3 NOT_FOUND."""
    rc = ki.main(["--platform", "banana", "--home", str(fake_home), "--update"])
    assert rc == 3


def test_factory_reset_unknown_platform_exits_three(fake_home):
    """--factory-reset on an unknown platform → exit 3 NOT_FOUND."""
    rc = ki.main(["--platform", "banana", "--home", str(fake_home), "--factory-reset"])
    assert rc == 3


def test_update_exit_zero_on_success(fake_home, tmp_path):
    """--update on a valid platform exits 0 (OK)."""
    host = tmp_path / "dot-claude"
    rc = ki.main([
        "--platform", "claude", "--home", str(fake_home),
        "--host-dir", str(host), "--update",
    ])
    assert rc == 0


# ---------------------------------------------------------------------------
# _materialize_pass stub — Phase A no-op guard
# ---------------------------------------------------------------------------


def test_materialize_pass_is_noop_without_kata_overlay(fake_home, tmp_path):
    """_materialize_pass returns immediately when kata_overlay is absent (Phase A stub)."""
    host_skills = tmp_path / "skills"
    host_skills.mkdir()
    # Must not raise, must not mutate
    ki._materialize_pass(fake_home, host_skills, "symlink")
    assert list(host_skills.iterdir()) == [], (
        "_materialize_pass must not mutate the host skills dir in Phase A"
    )


def test_materialize_pass_accepts_copy_link_mode(fake_home, tmp_path):
    """_materialize_pass accepts 'copy' link_mode without error."""
    host_skills = tmp_path / "skills"
    host_skills.mkdir()
    ki._materialize_pass(fake_home, host_skills, "copy")  # must not raise


def test_materialize_pass_accepts_mixed_link_mode(fake_home, tmp_path):
    """_materialize_pass accepts 'mixed' link_mode without error."""
    host_skills = tmp_path / "skills"
    host_skills.mkdir()
    ki._materialize_pass(fake_home, host_skills, "mixed")  # must not raise


# ---------------------------------------------------------------------------
# Sweep integration with uninstall() — catches rename-orphans
# ---------------------------------------------------------------------------


def test_uninstall_sweep_catches_rename_orphan(fake_home, tmp_path):
    """uninstall() sweep removes an orphaned host kata symlink (rename simulation)."""
    host = tmp_path / "dot-claude"
    ki.install("claude", harness_home=fake_home, host_dir=host)
    skills_dst = host / "skills"

    # Plant an orphaned kata symlink (simulates a skill renamed in home)
    target = fake_home / "skills" / "coordinate" / "kata-bootstrap"
    orphan = skills_dst / "kata-old-renamed"
    try:
        os.symlink(target, orphan, target_is_directory=True)
    except OSError:
        pytest.skip("symlinks not available on this platform")

    assert orphan.is_symlink(), "orphan must exist before uninstall"

    result = ki.uninstall("claude", harness_home=fake_home, host_dir=host)
    assert result["ok"] is True
    assert not orphan.exists() and not orphan.is_symlink(), (
        "uninstall sweep must remove the orphaned kata link"
    )


def test_uninstall_sweep_leaves_non_kata_intact(fake_home, tmp_path):
    """uninstall() sweep does not remove non-kata dirs (fail-closed)."""
    host = tmp_path / "dot-claude"
    ki.install("claude", harness_home=fake_home, host_dir=host)
    skills_dst = host / "skills"

    non_kata = skills_dst / "user-custom-skill"
    non_kata.mkdir()
    (non_kata / "my.md").write_text("precious", encoding="utf-8")

    result = ki.uninstall("claude", harness_home=fake_home, host_dir=host)
    assert result["ok"] is True
    assert non_kata.is_dir(), "non-kata dir must survive uninstall"
    assert (non_kata / "my.md").read_text(encoding="utf-8") == "precious"
