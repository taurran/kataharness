"""Tests for kata_install.py — multi-platform install + copy-mode.

The harness home is faked as a tmp tree with a couple of skill dirs, and the host
config dir is a tmp dir — so the install is exercised end-to-end without touching
the real ~/.claude.

Coverage:
- iter_skill_dirs finds skills under skills/ and modules/ (category-nested)
- ensure_plugin_manifest writes a valid .claude-plugin/plugin.json (idempotent)
- claude install flat-links every skill into <host>/skills/<name> + reports them
- claude install is idempotent (re-run replaces, no error, same result)
- codex/kiro are best-effort (flagged) and still link when a host_dir is given
- quick is a no-op
- unknown platform returns ok=False with manual steps
- copy_project copies a tree; rejects dest==src; rejects existing dest unless overwrite
- copy_project never shells out to git (it uses shutil only) — smoke: a .git in src
  is copied as data, not invoked
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

import kata_install as ki
import kata_dispatch


@pytest.fixture()
def fake_home(tmp_path):
    """A minimal harness home with two category-nested skills + a module skill."""
    home = tmp_path / "KataHarness"
    (home / "skills" / "coordinate" / "kata-bootstrap").mkdir(parents=True)
    (home / "skills" / "coordinate" / "kata-bootstrap" / "SKILL.md").write_text("---\nname: kata-bootstrap\n---\n", encoding="utf-8")
    (home / "skills" / "plan" / "kata-grill-standard").mkdir(parents=True)
    (home / "skills" / "plan" / "kata-grill-standard" / "SKILL.md").write_text("---\nname: kata-grill-standard\n---\n", encoding="utf-8")
    (home / "modules" / "closeout" / "kata-closeout").mkdir(parents=True)
    (home / "modules" / "closeout" / "kata-closeout" / "SKILL.md").write_text("---\nname: kata-closeout\n---\n", encoding="utf-8")
    (home / "README.md").write_text("# KataHarness v0.1.0-alpha.3\n", encoding="utf-8")
    return home


def test_iter_skill_dirs(fake_home):
    names = sorted(p.name for p in ki.iter_skill_dirs(fake_home))
    assert names == ["kata-bootstrap", "kata-closeout", "kata-grill-standard"]


def test_ensure_plugin_manifest(fake_home):
    m = ki.ensure_plugin_manifest(fake_home)
    assert m == fake_home / ".claude-plugin" / "plugin.json"
    data = json.loads(m.read_text(encoding="utf-8"))
    assert data["name"] == "kata"
    assert "version" in data and "description" in data
    # idempotent: second call doesn't error and keeps the file
    again = ki.ensure_plugin_manifest(fake_home)
    assert again == m


def test_claude_install_flat_links(fake_home, tmp_path):
    host = tmp_path / "dot-claude"
    res = ki.install("claude", harness_home=fake_home, host_dir=host)
    assert res["platform"] == "claude" and res["ok"] is True
    assert sorted(res["linked"]) == ["kata-bootstrap", "kata-closeout", "kata-grill-standard"]
    # each skill is discoverable flat with its SKILL.md
    for name in res["linked"]:
        assert (host / "skills" / name / "SKILL.md").exists()


def test_claude_install_idempotent(fake_home, tmp_path):
    host = tmp_path / "dot-claude"
    first = ki.install("claude", harness_home=fake_home, host_dir=host)
    second = ki.install("claude", harness_home=fake_home, host_dir=host)
    assert sorted(first["linked"]) == sorted(second["linked"])
    assert (host / "skills" / "kata-bootstrap" / "SKILL.md").exists()


def test_refuses_to_clobber_non_kata_dir(fake_home, tmp_path):
    # a user's own directory already sits where a skill would link — must NOT be destroyed
    host = tmp_path / "dot-claude"
    victim = host / "skills" / "kata-bootstrap"
    victim.mkdir(parents=True)
    (victim / "USER_DATA.txt").write_text("precious", encoding="utf-8")
    with pytest.raises(ValueError, match="non-kata"):
        ki.install("claude", harness_home=fake_home, host_dir=host)
    assert (victim / "USER_DATA.txt").read_text(encoding="utf-8") == "precious"  # survived


def _deny_symlink(*a, **k):
    raise OSError("symlinks denied (forced copy branch)")


def test_replaces_own_managed_copy(fake_home, tmp_path, monkeypatch):
    # Force the COPY branch (marker only exists for copies) so the test is FS-independent
    # rather than passing only where symlinks are denied.
    monkeypatch.setattr(ki.os, "symlink", _deny_symlink)
    host = tmp_path / "dot-claude"
    res = ki.install("claude", harness_home=fake_home, host_dir=host)
    assert res["method"] == ["copy"]
    assert (host / "skills" / "kata-bootstrap" / ki._MARKER).exists()
    ki.install("claude", harness_home=fake_home, host_dir=host)  # re-run: replaces the managed copy cleanly
    assert (host / "skills" / "kata-bootstrap" / "SKILL.md").exists()


def test_flat_link_rejects_duplicate_skill_names(tmp_path):
    home = tmp_path / "home"
    for cat in ("a", "b"):
        d = home / "skills" / cat / "dup"
        d.mkdir(parents=True)
        (d / "SKILL.md").write_text("---\nname: dup\n---\n", encoding="utf-8")
    with pytest.raises(ValueError, match="duplicate skill names"):
        ki.install("claude", harness_home=home, host_dir=tmp_path / "host")


def test_copy_project_rejects_ancestor_dest(tmp_path):
    # dest is an ANCESTOR of src → would rmtree the source; must be refused (red-team MAJOR-1)
    work = tmp_path / "work"
    src = work / "proj"
    src.mkdir(parents=True)
    (src / "keep.txt").write_text("precious", encoding="utf-8")
    with pytest.raises(ValueError, match="overlap"):
        ki.copy_project(src, work, overwrite=True)
    assert (src / "keep.txt").exists()  # source survived


def test_probe_token_not_in_prompt():
    # the expected answer must NOT appear in the prompt, else a prompt-echo false-positives (red-team F2)
    assert ki._PROBE_TOKEN not in ki._PROBE_PROMPT


def test_cli_with_parent_dir_writes_settings(fake_home, tmp_path):
    import kata_settings as ks

    parent = tmp_path / "Projects"
    parent.mkdir()
    host = tmp_path / "dot-claude"
    rc = ki.main(
        [
            "--platform", "claude",
            "--home", str(fake_home),
            "--host-dir", str(host),
            "--parent-dir", str(parent),
        ]
    )
    assert rc == 0
    saved = ks.read_settings(home=fake_home)
    assert Path(saved["parentDir"]) == parent.resolve()


def test_cli_confirm_claude(fake_home, tmp_path):
    rc = ki.main(["--platform", "claude", "--home", str(fake_home), "--confirm"])
    assert rc == 0
    import kata_settings as ks
    assert "claude" in ks.confirmed_platforms(home=fake_home)


def test_codex_best_effort(fake_home, tmp_path):
    host = tmp_path / "dot-codex"
    res = ki.install("codex", harness_home=fake_home, host_dir=host)
    assert res["platform"] == "codex" and res["bestEffort"] is True
    # best-effort installs use .agents/skills/ (cross-tool standard), NOT <host>/skills/
    assert (host / ".agents" / "skills" / "kata-bootstrap" / "SKILL.md").exists()


def test_quick_is_noop(fake_home):
    res = ki.install("quick", harness_home=fake_home)
    assert res["noop"] is True and res["ok"] is True


def test_unknown_platform(fake_home):
    res = ki.install("banana", harness_home=fake_home)
    assert res["ok"] is False
    assert any("copy" in n for n in res["notes"])


def test_confirm_claude_is_host(tmp_path):
    res = ki.confirm_platform("claude", home=tmp_path)
    assert res["confirmed"] is True and res["detail"] == "host"
    assert "claude" in res["confirmedPlatforms"]


def test_confirm_codex_probe_ok(tmp_path):
    def good_runner(cmd):
        return 0, f"sure: {ki._PROBE_TOKEN}"
    res = ki.confirm_platform("codex", runner=good_runner, home=tmp_path)
    assert res["confirmed"] is True
    import kata_settings as ks
    assert "codex" in ks.confirmed_platforms(home=tmp_path)


def test_confirm_codex_probe_no_token(tmp_path):
    def bad_runner(cmd):
        return 0, "hello"
    res = ki.confirm_platform("codex", runner=bad_runner, home=tmp_path)
    assert res["confirmed"] is False
    import kata_settings as ks
    assert "codex" not in ks.confirmed_platforms(home=tmp_path)


def test_confirm_codex_cli_absent(tmp_path):
    def absent_runner(cmd):
        raise FileNotFoundError("codex not found")
    res = ki.confirm_platform("codex", runner=absent_runner, home=tmp_path)
    assert res["confirmed"] is False and "launch" in res["detail"]


def test_confirm_unknown_platform(tmp_path):
    res = ki.confirm_platform("banana", home=tmp_path)
    assert res["confirmed"] is False


def test_copy_project(tmp_path):
    src = tmp_path / "proj"
    (src / "sub").mkdir(parents=True)
    (src / "sub" / "f.txt").write_text("hi", encoding="utf-8")
    dest = tmp_path / "proj-copy"
    out = ki.copy_project(src, dest)
    assert out == dest.resolve()
    assert (dest / "sub" / "f.txt").read_text(encoding="utf-8") == "hi"


def test_copy_project_rejects_same(tmp_path):
    src = tmp_path / "p"
    src.mkdir()
    with pytest.raises(ValueError):
        ki.copy_project(src, src)


def test_copy_project_existing_dest(tmp_path):
    src = tmp_path / "p"
    src.mkdir()
    (src / "a.txt").write_text("a", encoding="utf-8")
    dest = tmp_path / "d"
    dest.mkdir()
    with pytest.raises(ValueError):
        ki.copy_project(src, dest)  # exists, no overwrite
    ki.copy_project(src, dest, overwrite=True)  # ok with overwrite
    assert (dest / "a.txt").exists()


def test_copy_project_copies_git_as_data_not_invoked(tmp_path):
    # a .git dir in the source is copied as plain files; no git process is run
    src = tmp_path / "vaultish"
    (src / ".git").mkdir(parents=True)
    (src / ".git" / "config").write_text("[core]\n", encoding="utf-8")
    dest = tmp_path / "copy"
    ki.copy_project(src, dest)
    assert (dest / ".git" / "config").exists()  # copied verbatim, never executed


# ---------------------------------------------------------------------------
# Slice D tests: .agents/skills targeting + kiro probe + invariant (L-D, L-MP2)
# ---------------------------------------------------------------------------

def test_besteffort_links_into_agents_skills(fake_home, tmp_path):
    """Best-effort installs (codex) target .agents/skills/ (cross-tool standard, DESIGN N5)."""
    host = tmp_path / "dot-codex"
    res = ki.install("codex", harness_home=fake_home, host_dir=host)
    assert res["bestEffort"] is True
    skills_dir = Path(res["skillsDir"])
    # Path must end in .agents/skills
    assert skills_dir.parts[-1] == "skills"
    assert skills_dir.parts[-2] == ".agents", f"expected .agents/skills, got {skills_dir}"
    assert (host / ".agents" / "skills" / "kata-bootstrap" / "SKILL.md").exists()


def test_kiro_besteffort_links_into_agents_skills(fake_home, tmp_path):
    """kiro best-effort install also targets .agents/skills/ (cross-tool standard)."""
    host = tmp_path / "dot-kiro"
    res = ki.install("kiro", harness_home=fake_home, host_dir=host)
    assert res["platform"] == "kiro" and res["bestEffort"] is True
    skills_dir = Path(res["skillsDir"])
    assert skills_dir.parts[-2:] == (".agents", "skills"), f"expected .agents/skills, got {skills_dir}"
    assert (host / ".agents" / "skills" / "kata-grill-standard" / "SKILL.md").exists()


def test_claude_still_links_into_skills_not_agents(fake_home, tmp_path):
    """claude install must NOT use .agents/skills — it keeps its own <host>/skills/ (unchanged)."""
    host = tmp_path / "dot-claude"
    res = ki.install("claude", harness_home=fake_home, host_dir=host)
    skills_dir = Path(res["skillsDir"])
    assert skills_dir.parts[-1] == "skills"
    assert ".agents" not in skills_dir.parts, "claude must NOT use .agents/skills"
    assert (host / "skills" / "kata-bootstrap" / "SKILL.md").exists()


def test_confirm_kiro_probe_ok(tmp_path):
    """confirm_platform('kiro') with a token-returning stub confirms and records kiro."""
    def good_runner(cmd):
        return 0, f"answer: {ki._PROBE_TOKEN}"
    res = ki.confirm_platform("kiro", runner=good_runner, home=tmp_path)
    assert res["confirmed"] is True
    assert res["detail"] == "probe ok"
    import kata_settings as ks
    assert "kiro" in ks.confirmed_platforms(home=tmp_path)


def test_confirm_kiro_probe_no_token(tmp_path):
    """confirm_platform('kiro') with a stub that omits the token does NOT confirm."""
    def bad_runner(cmd):
        return 0, "something else entirely"
    res = ki.confirm_platform("kiro", runner=bad_runner, home=tmp_path)
    assert res["confirmed"] is False
    import kata_settings as ks
    assert "kiro" not in ks.confirmed_platforms(home=tmp_path)


def test_probe_commands_subset_of_command_builders():
    """Invariant (L-MP2): every probe-able platform must have a dispatch adapter.

    A confirmed platform is routable only when it also has a dispatch adapter —
    otherwise kata_dispatch.dispatch() would silently fail for it at runtime.
    """
    assert set(ki._PROBE_COMMANDS) <= set(kata_dispatch._COMMAND_BUILDERS), (
        "platforms in _PROBE_COMMANDS but missing dispatch adapter: "
        + str(set(ki._PROBE_COMMANDS) - set(kata_dispatch._COMMAND_BUILDERS))
    )
