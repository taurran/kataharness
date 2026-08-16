# Operator checklist — the PAT rotation + probes 2–6, in plain steps

Written 2026-08-16 at the operator's request ("ELI5 style, with steps"). Each item says what it
is, why it matters, the exact steps, and what to tell the session afterward. None of these blocks
the trust-model work — do them whenever you have a few minutes. Check items off as you go.

---

## ☐ 1. Rotate the GitHub token (~3 minutes) 🔴 oldest item, do first

**What this is:** your GitHub password-equivalent currently sits as plain text in a settings file,
and every helper process the session spawns can see it.
**Why now:** it's been deferred since Aug 2, and you just changed your GitHub MFA anyway — a fresh
login rides the new MFA cleanly.

1. In the Claude session, type exactly: `! gh auth login`
2. Answer the menu: **GitHub.com** → **HTTPS** → **Login with a web browser** → press Enter.
3. Your browser opens — approve the login (it will use your new MFA).
4. Tell the session **"gh login done"** — it will verify everything still works, then (with your
   OK) delete the old token line from the settings file.
5. Last step, on the website: github.com → your avatar → **Settings** → **Developer settings** →
   **Personal access tokens** → find the old token → **Delete/Revoke**. (The session will confirm
   nothing still needs it before you do this.)

**Tell the session:** "gh login done" (step 4), then "old token revoked" (step 5).

---

## ☐ 2. Probe 2 — does the kata status strip show up inside VS Code? (~3 minutes)

**What this checks:** whether the little kata status display (the strip at the bottom of a
session) appears when Claude runs inside VS Code, not just in a terminal.
**Why we care:** the new UX design needs to know which windows can show the phase rail.

1. Open **VS Code**.
2. Open the folder `C:\dev\projects\KataHarness`.
3. Start a Claude session in the VS Code panel (the extension).
4. Look at the bottom of the session panel: is there a kata status strip (a line with run info)?

**Tell the session:** "probe 2: strip visible" or "probe 2: no strip" (a screenshot is even
better).

---

## ☐ 3. Probe 3 — does Codex show colors or gibberish? (~2 minutes)

**What this checks:** when a program prints colored text inside Codex's interactive window, do
you SEE the color, or raw codes like `[31m`?
**Why we care:** decides whether Codex transcripts get colors or the glyph-only look.

1. Open a terminal.
2. Run: `codex`  (an interactive Codex session opens)
3. Ask it to run exactly this: `printf '\033[31mRED\033[0m plain\n'`
4. Look at the output: is the word **RED** actually red? Or do you see gibberish like
   `[31mRED[0m`?

**Tell the session:** "probe 3: red is red" or "probe 3: gibberish codes".

---

## ☒ 4. Probe 4 — DEFERRED to BL-N25 (operator, 2026-08-16) — skip this section

**Deferred with the PATH issue unresolved (reboot untried). Kiro plans as detection-only until
the probe runs. Nothing for you to do here now.** Original steps kept below for when BL-N25
executes.

## (deferred) Probe 4 — Kiro hooks check (2 minutes you, then 5 together)

**Status 2026-08-16:** kiro-cli 2.18.1 confirmed working and now on your PATH (the session fixed
the installer's PATH gap). Only login remains before the probe.
**What this checks:** whether Kiro can safely run our hooks (known Kiro issue #5527 must be
re-verified before EVER registering kata hooks there).
**Why we care more now:** the result decides whether Kiro gets real dispatch enforcement or a
declared detection-only mode in the trust model's per-host table.

1. Open a **new** terminal (fresh PATH).
2. Run: `kiro-cli login` and finish the sign-in it shows you.
3. Tell the session: **"kiro login done"** — it prepares a tiny harmless test hook (prints one
   line, touches nothing), you run one chat turn together, it checks hook-stdout visibility +
   #5527, removes the test hook, and records both answers.

Do NOT install any kata hooks in Kiro yourself — the probe must come first.

---

## ☐ 5. Probe 5 — are Kiro's command flags still current? (~1 minute)

**What this checks:** our Kiro adapter launches workers with `kiro-cli chat --no-interactive
--agent <name>`. Kiro updates sometimes rename flags.

1. Open a terminal.
2. Run: `kiro-cli chat --help`
3. Copy the output.

**Tell the session:** paste the output. It will check the two flags itself.

---

## ☐ 6. Probe 6 — does the status strip behave in Windows Terminal? (~2 minutes)

**What this checks:** whether the strip can use two lines without flickering in Windows Terminal
(two lines would double the room for the phase rail).

1. Open **Windows Terminal**.
2. Run a Claude session in `C:\dev\projects\KataHarness` (just `claude` in that folder).
3. Look at the strip at the bottom for ~30 seconds while the session works.

**Tell the session:** "probe 6: one line / two lines, steady" or "…, flickers".

---

*When any result comes back, the session records it in `specs/ux-rework/PLATFORM-MATRIX.md` with
a live-probed (LP) label and the date — that's what upgrades a guess to a fact in the design.*
