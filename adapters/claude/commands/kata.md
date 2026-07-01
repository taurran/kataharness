---
description: KataHarness command index
---

KataHarness slash-command index. Available commands:

- `/kata-start` — begin a new Kata run (initialise config, evaluate readiness, launch the loop)
- `/kata-onboard` — onboard an existing repo into the Kata loop; the on-ramp for **Debug Mode** (systematically debug a repo in confidence) on a fresh repo
- `/kata-resume` — resume a Kata run after a break or a lost session
- `/kata-status` — show the current run frontier and board status
- `/kata-validate` — run the skill validator against the installed skill set

**Run-shapes** — `/kata-start` accepts *what kind of run* you want (selected at bootstrap, pre-fills `mode`+`modules`+`target`):

- `individual` — one new build
- `batch` — best-of-N (bake-off)
- `version-up` — improve a repo that already ran the loop
- `debug` — **systematically debug an existing repo in confidence** (bugs out, behavior preserved). Just ask: "debug my repo" at `/kata-start`, or use `/kata-onboard` on a fresh repo.
- `advanced` — top of the ladder (cross-tier picks + external ingest)
