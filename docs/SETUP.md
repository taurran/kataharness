# Setting up KataHarness

KataHarness lives in **one central place** and installs into your agent platform from there.
It remembers **two settings** and, each run, finds the project to work on. That's the whole setup.

> No vault yet? You don't need one — KataHarness runs fine pointed at a plain project folder.
> A vault matters only for the **learning component** (the "second brain"); see *Vault* below.

---

## 1. Install into your platform

### One-command install (recommended)

```sh
# POSIX shell — macOS / Linux / Git Bash on Windows
curl -fsSL https://raw.githubusercontent.com/taurran/kataharness/master/install.sh | sh
```

```powershell
# PowerShell — Windows
irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 | iex
```

Both one-liners clone KataHarness to `~/.kata-home` (`%USERPROFILE%\.kata-home` on Windows) and
invoke the installer. Default platform: **claude**.  Pass extra arguments via
`sh -s -- --platform <p> --parent-dir <dir>` or as direct arguments to the `.ps1`.

**Honest security caveat — read before piping:** `curl … | sh` and `irm … | iex` execute bytes as
they stream — there is nothing to hash until after execution.  A checksum protects the
*download-then-run* path (fetch the script to a file, verify its SHA, then execute); it **does not**
protect the piped form.  Mitigations shipped: stable URL, short readable script, `KATA_REF` env var
for version-pinning.  For a stronger guarantee, use one of the git-clone paths below.

### Git-clone / manual path (audit-friendly)

Already have a clone, or want to inspect first?

```bash
# If you cloned manually or used "Use this template":
cd <where-KataHarness-lives>            # e.g. C:/Dev/Projects/KataHarness
uv run python tools/kata_install.py --platform claude \
    --parent-dir C:/Dev/Projects        # optional: also writes the settings file
```

Or clone and install in one go:

```sh
git clone https://github.com/taurran/kataharness.git ~/.kata-home
cd ~/.kata-home
uv run python tools/kata_install.py --platform claude
```

**"Use this template"** on GitHub forks the repo to your own account — no remote install script
involved at all.

### Env var support

| Variable | Purpose |
|---|---|
| `KATA_HOME` | Reuse an existing harness home (skip the clone) |
| `KATA_REF` | Pin the clone to a git tag / branch / SHA (default: `master`) |
| `KATA_SRC` | Local path to use as harness home — skips all network fetches (for CI or offline use) |
| `KATA_PARENT_DIR` | Default parent project folder (forwarded to the engine) |
| `KATA_VAULT_DIR` | Vault location (forwarded to the engine) |

| Platform | Status | What it does |
|----------|--------|--------------|
| **Claude Code** | ✅ Built + verified | Flat-links every skill into `~/.claude/skills/<name>` so Claude discovers them; writes `.claude-plugin/plugin.json` (so the suite is also plugin-distributable). |
| **Codex** | ⚠️ Best-effort | Flat-links into the host skills dir you pass. The correct Codex target is `.agents/skills/` (or `~/.codex/skills/` on older versions) — **verify discovery in-host**; the default link dir is not yet Codex-specific. |
| **Kiro** | ⚠️ Best-effort | Flat-links into the host skills dir you pass; the Kiro target is `.kiro/skills/`. **Verify in-host.** A native VS Code surface is a later adapter. |
| **Quick / ACP** | Brings its own | The work/ACP host ships its own installer; KataHarness defines only the contract. |
| _other_ | Manual | The installer prints where to copy `skills/*/<name>/` + `modules/*/<name>/`. |

### Symlink vs copy (Windows note)
The Claude installer tries a **symlink** first (so edits to the central repo show up immediately).
On Windows without **Developer Mode** (or admin), symlinks aren't permitted, so it **falls back to a
copy** — which works fine, but means you should **re-run the installer after you update KataHarness**
to refresh the copied skills. Enable Developer Mode (Settings → Privacy & security → For developers)
to get auto-updating symlinks instead.

### `$KATA_HOME`
By default the harness finds its own install location. To pin it explicitly (CI, multiple installs),
set `KATA_HOME` to the central folder.

---

## 2. The two settings

These are recorded in `<KataHarness>/.kata-settings.json` (git-ignored — machine-specific paths),
written by the installer when you pass `--parent-dir`, or by `kata-initiate` on first run:

- **`parentDir`** — your **default parent project folder** (e.g. `C:/Dev/Projects`). Each run searches
  here for the project you name. You can point at a different folder for any single run.
- **`vaultDir`** — where your **vault / second brain** sits (optional). The learning component reads and
  writes here. Absent ⇒ learning is simply a no-op; everything else works.

These values **seed** the per-run `kata.config` path fields; a run may override them. With no settings
file at all, KataHarness runs in-repo exactly as before (nothing changes).

---

## 3. Each run

When you start a run, preflight asks **what the project is called and roughly where it is**, searches
under your parent folder, and shows the match to **confirm**:

- **One match** → confirm it.
- **Several matches** → pick from the list.
- **No match** → type the full path.

That folder becomes the codebase for the run.

### Copy mode
If you choose to work on a **copy** (e.g. Debug Mode's import-a-copy, for aggressive changes on
untrusted/large repos), preflight also asks for a **destination folder** first. KataHarness copies the
project there and works on the copy — your original is left untouched. (The copy uses a plain file
copy; it never runs git against your vault.)

---

## 4. Updating / uninstalling

- **Update:** pull the central repo (`git pull` inside `~/.kata-home`). With symlinks, skills update
  automatically. With the copy fallback, re-run `install.sh` / `install.ps1` (or
  `tools/kata_install.py --platform <p>` directly) to refresh the copied skills.

### Uninstall (shipped uninstaller — recommended)

```sh
# POSIX — removes skills, settings, and router stanza from the supplied project
sh ~/.kata-home/uninstall.sh --target-dir /path/to/project --yes
```

```powershell
# PowerShell
& "$env:USERPROFILE\.kata-home\uninstall.ps1" --target-dir C:\path\to\project --yes
```

Or invoke the engine directly:

```bash
uv run python tools/kata_install.py --uninstall --platform claude \
    --target-dir /path/to/project --yes
```

The uninstaller removes:
- Flat-linked skills from the host skills directory (e.g. `~/.claude/skills/kata-*`)
- `.kata-settings.json`
- The `<!-- kata:begin … kata:end -->` router stanza from `<target-dir>/AGENTS.md`

Re-running on an already-uninstalled target exits `0` (no-op).

**Scope honesty — router stanza removal is scoped to the supplied `--target-dir` only.** The
harness keeps no registry of every project where a stanza was written (deliberately simple design,
no `~/.kata` registry). For each additional project, re-run with that project's path:

```sh
sh ~/.kata-home/uninstall.sh --target-dir /path/to/other-project --yes
```

### Manual fallback (if the scripts are unavailable)

Remove the linked/copied skill folders from your host skills directory (e.g. `~/.claude/skills/`)
and delete `.kata-settings.json`.  To remove a router stanza, delete the
`<!-- kata:begin -->…<!-- kata:end -->` block from the target project's `AGENTS.md`.
