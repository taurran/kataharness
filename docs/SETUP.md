# Setting up KataHarness

KataHarness lives in **one central place** and installs into your agent platform from there.
It remembers **two settings** and, each run, finds the project to work on. That's the whole setup.

> No vault yet? You don't need one — KataHarness runs fine pointed at a plain project folder.
> A vault matters only for the **learning component** (the "second brain") — an **optional target**,
> never a requirement. Any vault path works; a good starter is **PokeVault**
> (https://github.com/taurran/pokevault). See *The two settings* below.

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
- **`vaultDir`** — where your **vault / second brain** sits (optional — a *target*, never a requirement).
  The learning component reads and writes here; **any vault path works**. Absent ⇒ learning is simply a
  no-op and everything else works. No vault yet? A good starter is **PokeVault** →
  https://github.com/taurran/pokevault.

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

### Update (one command)

Run the update script from your installed home:

```sh
# POSIX shell — macOS / Linux / Git Bash on Windows
sh ~/.kata-home/update.sh
```

```powershell
# PowerShell — Windows
& "$env:USERPROFILE\.kata-home\update.ps1"
```

Or fetch and run the latest bootstrap remotely (ensures you also pick up any bootstrap fixes):

```sh
curl -fsSL https://raw.githubusercontent.com/taurran/kataharness/master/update.sh | sh
```

```powershell
irm https://raw.githubusercontent.com/taurran/kataharness/master/update.ps1 | iex
```

Both scripts fast-forward the home to the latest ref (`master` by default; set `KATA_REF` to pin a
tag/branch/SHA), then invoke the engine (`kata_install.py --update --git-sha <sha>`) to re-link or
re-copy skills and write a version stamp. The engine's exit code propagates.

**Check for an update without applying it:**

```sh
sh ~/.kata-home/update.sh --check
```

Reports "update available" or "already current" and exits without mutating anything.

**Dirty-base guard:** If you have hand-edited any tracked base file inside the home, the script
detects the dirty tree (`git status --porcelain`) and **aborts** — printing the dirty paths — rather
than silently overwriting your edits. To acknowledge and proceed (discarding your local base edits):

```sh
sh ~/.kata-home/update.sh --discard-local
```

**Symlink vs copy mode on update:**
- **Symlink mode** (POSIX, or Windows with Developer Mode): non-overlaid skills already track the
  home; the git fast-forward alone refreshes them. `--update` additionally re-stamps the version
  file.
- **Copy mode** (Windows without Developer Mode): copied skill files are stale between update runs.
  `--update` re-copies **every** skill — files do **not** auto-refresh without an explicit
  `update.sh` run. Enable Developer Mode (Settings → Privacy & security → For developers) to get
  live symlinks instead.

**Non-git-clone homes:** If your home was set up via "Use this template" or copied (no fetchable
git remote), `update.sh` detects the missing remote, prints
`"this home is not a git clone — re-install to update"`, and exits without mutating. Re-run the
one-command installer (`install.sh` / `install.ps1`) to update such homes instead.

### Local adaptation (overlays)

KataHarness lets you adapt individual skills to your workflow **without touching the installed base**.
The base skills under `<home>/skills/` are immutable from the user's side — every `--update` cleanly
overwrites them. Local adaptations live exclusively in the **overlay store**, which is preserved across
updates and factory-resets.

**Overlay store — `<home>/.kata-overlay/overlay.json`.** User-owned, git-ignored, per-install. The
file is keyed by skill name; each entry can hold:

| Key | Purpose |
|---|---|
| `frontmatterOverrides` | Field-level overrides merged over the base frontmatter. Shallow, per-key replace — list-valued keys (`tags`, `allowed-tools`, `aliases`, `supersedes`) are replaced entirely, not element-merged. To extend a list, restate the full intended list in the overlay. |
| `prepend` / `append` | Ordered content blocks spliced at a named heading anchor in the skill body (e.g. `"## Output"`), or at the start / end of the body when `anchor` is `null`. Multiple blocks for the same anchor apply in array order. |
| `pin` | Advisory semver the entry was authored against (informational). |

**Authoring overlays — `kata-improve` local-adaptation mode.**
Before entering its authoring path, `kata-improve` calls `kata_overlay.adaptation_context(home)`:

- **`"install"`** — a `.kata-version` stamp is present in the home (written by every successful install
  or `--update`; git-ignored; every real user install self-identifies). In this context, `kata-improve`'s
  kata mode **refuses to run** — it will not mutate the installed base — unless the operator explicitly
  passes `improve.allowUpstreamEdit`. The safety rail defaults to "never mutate the installed base."
- **`"dev-repo"`** — no stamp; a canonical maintainer checkout. The authoring-upstream path runs as
  normal (edits `skills/**` in place, bumps semver, updates the README index).

In install context, the **pinned writable footprint** is exactly:
1. `<home>/.kata-overlay/overlay.json` — overlay entries, via `kata_overlay.write_overlay_entry`
   (read-merge-write one skill; all others preserved).
2. `<agentSkills.dir>/candidates/<name>/` — fork candidates, via `kata-write-skill`
   (sandboxed, pre-`kata-promote`-gate).

For change shapes that cannot be expressed as a frontmatter override or append block — deep prose or
contract rewrites — `kata-improve` routes to a **fork**: authored via `kata-write-skill` into
`<agentSkills.dir>/candidates/<name>/` (carrying `supersedes: <upstream>`), then passed through the
`kata-promote` human gate before it can shadow the upstream skill.

**Materialization — how an overlay reaches the host slot.**
The engine applies overlays at the end of every install or `--update` run (a post-link materialize
pass):

- A skill **with** an overlay entry is materialized as a **concrete host slot**: the base dir is copied
  into the slot, the `SKILL.md` is composed (base + overlay → single concrete file), and two markers are
  written — `.kata-managed` (the uninstaller removes it) and `.kata-overlay-materialized` (factory-reset
  uses this to restore the slot to a pristine link).
- A skill **without** an overlay stays a verbatim **symlink** (or copy on Windows without Developer
  Mode), exactly as before.

**One honest tradeoff:** a materialized slot is a concrete file — it no longer auto-tracks the home
symlink. Upstream base changes do not propagate live into a materialized slot. Running `--update`
re-materializes the slot from the updated base, which is the expected update path.

**Stale overlays (base skill removed upstream).** If a base skill is removed or renamed by an update
and an overlay entry still exists for it, the materialize pass emits a NOTE and skips that entry — it
never crashes, and the entry is retained in the overlay store (it re-activates if the skill returns):

```
NOTE: overlay for '<name>': base skill no longer exists — skipped
```

---

### Factory-reset

Restores the pristine base skills while keeping all your user-owned state (`.kata-settings.json`,
`.planning/`, vault, and your overlay store):

```sh
# POSIX — bootstrap path (also fast-forwards the base via git)
sh ~/.kata-home/update.sh --factory-reset
```

```powershell
& "$env:USERPROFILE\.kata-home\update.ps1" --factory-reset
```

Or invoke the engine directly (re-links pristine base, no git step):

```bash
uv run python tools/kata_install.py --factory-reset --platform claude --yes
```

**`--hard` additionally clears the overlay store** (local skill adaptations you have authored),
yielding a fully pristine tree with no local adaptations:

```sh
sh ~/.kata-home/update.sh --factory-reset --hard
```

| Operation | Base skills | Your overlays | Materialized slots |
|---|---|---|---|
| `--update` | refreshed from upstream | preserved | re-applied |
| `--factory-reset` | re-linked pristine | preserved | dropped → pristine links |
| `--factory-reset --hard` | re-linked pristine | cleared | dropped → pristine links |

> **Overlay preserve / re-apply:** a plain `--factory-reset` un-materializes overlaid slots back to
> pristine links but leaves the overlay store intact. Running `--update` afterwards re-materializes
> every overlay from the (now-refreshed) base. `--factory-reset --hard` additionally clears the
> overlay store (`NOTE: --hard: overlay store cleared`); the next `--update` will produce a fully
> pristine install with no local adaptations.

### Manual fallback (if the update scripts are unavailable)

```bash
cd ~/.kata-home && git pull
uv run python tools/kata_install.py --platform claude
```

In symlink mode, skills update automatically after `git pull`. In copy mode, re-running the
installer re-copies the updated skills.

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
