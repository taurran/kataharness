# Setting up KataHarness

KataHarness lives in **one central place** and installs into your agent platform from there.
It remembers **two settings** and, each run, finds the project to work on. That's the whole setup.

> No vault yet? You don't need one — KataHarness runs fine pointed at a plain project folder.
> A vault matters only for the **learning component** (the "second brain"); see *Vault* below.

---

## 1. Install into your platform

From the central KataHarness folder, run the installer for your platform. The installer makes the
skills discoverable to your agent. To record your settings at the same time, pass `--parent-dir`
(and optionally `--vault-dir`); otherwise `kata-initiate` records them on first run.

```bash
cd <where-KataHarness-lives>            # e.g. C:/Dev/Projects/KataHarness
uv run python tools/kata_install.py --platform claude \
    --parent-dir C:/Dev/Projects        # optional: also writes the settings file
```

| Platform | Status | What it does |
|----------|--------|--------------|
| **Claude Code** | ✅ Built + verified | Flat-links every skill into `~/.claude/skills/<name>` so Claude discovers them; writes `.claude-plugin/plugin.json` (so the suite is also plugin-distributable). |
| **Codex** | ⚠️ Best-effort | Same flat-link idea into the Codex skills location. Verify discovery in-host. |
| **Kiro** | ⚠️ Best-effort | Same flat-link idea. A native VS Code surface is a later adapter. |
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

- **Update:** pull the central repo. With symlinks, skills update automatically. With the copy
  fallback, re-run `tools/kata_install.py --platform <p>`.
- **Uninstall:** remove the linked/copied skill folders from your host skills directory (e.g.
  `~/.claude/skills/`) and delete `.kata-settings.json`.
