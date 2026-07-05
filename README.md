# KataHarness

### One-shot complex coding tasks — with the guardrails that make autonomy trustworthy.

KataHarness front-loads deep, doc-grounded planning, **freezes the plan**, executes it faithfully across one or
many subagents, and refuses to call anything "done" until a **fresh-context, default-FAIL evaluator** proves it —
then folds every run's lessons back into itself. The name *is* the method: the **Improvement Kata** — *every loop
sharpens the loop.*

> **v0.2.0 · experimental.** NEW in v0.2.0 (Freeze/Float M4): the inline evaluator/reroll — an
> event-triggered, checkpoint-chunked corrective ladder (`inlineEval: off|telemetry|on`; absent ⇒ off,
> byte-for-byte BC). Rule-verifiable trigger signals only; LLM judgment ONLY after a trigger, at a
> strictly-below-anchor tier; recovery = kill-and-restart on attempt branches; the final gate is
> untouched as authority. Live-proven once (D145): trigger → diff-cited verdict → corrective
> redispatch → green, with zero LLM calls on the green path. HONEST LIMITS: the <1% green-run
> overhead cap is AT-RISK at owned-module chunking (remediation named); research/debug class extras
> await producers; one live proof, not a statistical base. The single-model Claude core is the proven, dogfooded path (KataHarness builds
> itself); multi-model routing and the Codex/Kiro adapters are partially built; IaC *apply* is gated and not yet
> shipped runnable. We're honest about maturity — that honesty is the product. New here? Start with
> [`AGENTS.md`](./AGENTS.md) (the vision + the spine).

---

## Why it stands apart

Most "agentic loops" are a thin wrapper around *prompt → generate → hope*. KataHarness is a disciplined system:

- **🧊 The plan doesn't drift.** The plan is *frozen* after planning; the orchestrator guards it; worker
  subagents execute and talk laterally but **never re-plan.** An unknown escalates or parks — it is never
  silently guessed.
- **🛡️ Nothing certifies its own work.** A **fresh-context, no-write, default-FAIL** evaluator independently
  reads the evidence and must return PASS — backed by an **adversarial review** before every merge. In this
  project's own build, that fresh-context review caught bugs the passing test suite had blessed.
- **🔁 Crash-proof resume.** Lose a session to a crash or a context compaction and pick up **exactly where you
  left off** — see below. Most harnesses just lose the work.
- **🏁 It benchmarks itself.** A built-in scoring engine ranks candidate approaches on real pass/fail evidence
  and produces an **honest scorecard** — quality you can measure, not vibes. *(v0.1 scores single-arm + k-repeat
  runs; the parallel multi-arm bake-off driver is next.)*
- **🧩 Tool-agnostic core + thin adapters.** One agnostic core (protocol, skills, planning engine, quality loop)
  with per-tool adapters — not locked to one vendor.
- **🪶 Zero-dependency install.** A pure-stdlib Python engine; one command drops it into your agent host.

---

## The Kata Loop

Six phases, every run feeding the next:

```
GRILL   →   FREEZE   →   EXECUTE   →   EVALUATE   →   HANDOFF   →   IMPROVE
interrogate  lock the    plan-faithful  fresh-context   durable,     distil + promote
the spec     design +    parallel       no-write,       two-way,     lessons back into
             the plan    workers        DEFAULT-FAIL    git-committed  the skills → next run
```

---

## What's in the box

### 🔁 Crash-proof resume *(new)*
A session death — a crash, a killed terminal, an auto-compaction that wipes context mid-build — no longer costs
you the run. KataHarness keeps a **durable, git-committed progress trail** and restores the exact frontier:

- **Durable board.** The live work-board is snapshotted to a dedicated git ref (`refs/kata/trail`) with pure git
  plumbing — it never touches your working tree, never pushes, and can't corrupt a thing.
- **Auto-checkpoint before compaction.** A pre-compaction hook is wired to checkpoint the board *before* the
  context window is squeezed. *(Being live-verified: that Claude's PreCompact hook fires synchronously with a
  usable budget. Even if it doesn't, your progress is already durable at every integration checkpoint — above.)*
- **Task-granular restore.** On resume, `/kata-resume` re-derives which tasks were finished (from the git
  history, the authoritative source) and re-dispatches only the ones that weren't — no double work, no dropped
  work, no manual reconstruction.

### 🏁 Built-in benchmarking
Quality you can *measure*, not assert. A complete two-axis scoring engine ranks candidate build artifacts on real
**fail-to-pass / pass-to-pass** test evidence (weighted by a mutation-non-vacuity multiplier) and produces an
**honest scorecard** — it distinguishes a genuine all-pass from a vacuous one, with **no free credit for tests
that never ran**. *(v0.1 scores single-arm + k-repeat runs; the parallel multi-arm bake-off driver — launch N
approaches at once, judge, and promote the winner — is the next planned capability.)*

### 🐞 Debug Mode — a bug-hunting pipeline
Point it at a failing or mysterious codebase and it's *designed* to work like an engineer, not a guesser: build a
**function model** of the code, run a **deviation-discovery** pass to surface where behavior diverges from intent,
generate a **characterization suite** that pins current behavior, **diagnose** root cause (light or full depth),
and hand back a **debrief** with confidence and an optional version-up offer. *(Built and wired — P1–P3, gated on
`kata/module/debug`; proven on seeded fixtures. Launch it with `/kata-onboard` on a fresh repo, or just ask for a
**debug run** at `/kata-start` — "debug my repo".)*

### ☁️ Specialized Infrastructure-as-Code agents
First-class IaC specialists for **Terraform** and **CloudFormation**, injected automatically when a task touches
infra. They share a **safety contract** (`protocol/iac-safety.md`): structured plan-only argv, a **Snyk IaC**
scan gate, an explicit approval-artifact gate, and **no destructive `-target`**. Authoring, review, and planning
are live; *apply* is deliberately gated behind approval and not yet shipped runnable — safety before convenience.

### 🎚️ Modes, tiers & relative model routing
Three **modes** (**Essential · Standard · Advanced**) set breadth and depth. Tiered skill families
(`kata-grill`, `kata-plan`, `kata-review`, `kata-diagnose`) share one rubric and expose a depth dial. Model
selection is **relative** — critical work runs at your session's anchor model, economy work tiers *down* a rung —
so a gated or renamed model never breaks the loop, and no model ID is ever hard-baked into a skill.

### 🛡️ The quality loop
A **default-FAIL** evaluator owns the definition of "done." An **adversarial review** attacks the design before
every merge. Every code behavior is **mutation-proven non-vacuous** (a test that stays green when its assertion
is removed doesn't count). An optional **AI-slop check** fails a run for spiraling or over-claiming. And a
standing **silent-permissive-default guard** forbids decision-code from quietly degrading on bad input.

### 🔧 Adapt without forking upstream
Customize any skill via a local **overlay** or a promoted **fork** — your changes survive every update; the
upstream base stays pristine and is never edited or lost.

### 🗂️ Discoverable slash-commands *(Claude)*
`/kata` prints the index; `/kata-start`, `/kata-onboard`, `/kata-resume`, `/kata-status`, and `/kata-validate`
route straight to the right skill — no logic to drift, always in sync with the toolkit.

### 📚 47 versioned skills
Across six families — `plan` · `coordinate` · `execute` · `evaluate` · `handoff` · `meta` — plus the
`initiation` / `closeout` modules. Every skill carries a semver in its frontmatter; the generated catalog below
is the machine source of truth for what exists and at what version.

<details>
<summary><b>Full skill catalog</b> — name · version · cost · category · status · source · use (auto-generated from frontmatter; the versioning source of truth)</summary>

<!-- SKILL-INDEX:START -->
| Skill | Ver | Cost | Category | Status | Source | Use |
|---|---|---|---|---|---|---|
| `kata-comprehend` | 0.1.0 | 3 | plan | experimental | new (KataHarness original, Debug Mode P1 — function-model oracle, DESIGN LD2/LD7) | — |
| `kata-context` | 0.1.0 | 1 | plan | experimental | adapted-from mattpocock/skills {ubiquitous-language, grill-with-docs CONTEXT-FORMAT} | Build/maintain CONTEXT.md shared/ubiquitous language |
| `kata-design-doc` | 0.1.0 | 2 | plan | experimental | adapted-from mattpocock/skills {to-prd} + superpowers brainstorming + GSD spec-phase | Synthesize the frozen design doc / spec |
| `kata-graph` | 0.1.0 | 3 | plan | experimental | adapted-from aider repo-map (MIT — tree-sitter tag-queries + personalized PageRank + token budget) + Graphify (safishamsi/graphify, MIT — AST graph + MCP oracle get_neighbors/shortest_path/get_pr_impact) | Token-budgeted structural map of an existing repo (version-up ingestion); builds kata.graph.json |
| `kata-grill-advanced` | 0.1.0 | 5 | plan | experimental | adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model | — |
| `kata-grill-essential` | 0.1.0 | 3 | plan | experimental | adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model | — |
| `kata-grill-standard` | 0.1.0 | 4 | plan | experimental | adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model | — |
| `kata-plan-advanced` | 0.1.3 | 4 | plan | experimental | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-plan-essential` | 0.1.3 | 2 | plan | experimental | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-plan-standard` | 0.1.3 | 3 | plan | experimental | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-research` | 0.1.0 | 3 | plan | experimental | new (KataHarness original, loop-cognition RS-GB1/2/3, D62) — fresh-context no-write evaluator pattern (L4/L5) applied to in-loop research; escalation-routed like kata-orchestrate's no-re-plan escape valve (D52) | Research a must-deliver gap with no in-plan solution; ground every claim; return findings for the grounding gate, never re-plan |
| `kata-board` | 0.1.0 | 2 | coordinate | experimental | adapted-from Claude Agent Teams protocol (agnostic file reimplementation); CryptoPortfolioPlanner LESSONS-LEARNED L3 | Append-only mailbox/message board for lateral peer comms |
| `kata-bootstrap` | 0.3.0 | 2 | coordinate | experimental | adapted-from GSD discuss-phase Q&A model + docs/MODES-DESIGN.md D24c composition ladder (KataHarness design) | Compose a run (run-shape + ladder), preview cost, write kata.config, launch |
| `kata-initiate` | 0.2.1 | 3 | coordinate | experimental | new (KataHarness original, Phase 1 Kata Loop — D88/D91); composes kata-readiness, kata-grill, kata-bootstrap, kata-context | — |
| `kata-loop` | 0.1.0 | 2 | coordinate | experimental | new (KataHarness original — Phase 3 Kata Loop conductor, D87/DESIGN §1) | — |
| `kata-onboard` | 0.2.0 | 3 | coordinate | experimental | new (KataHarness original, Debug-Mode P3 / LD13 — DESIGN R6/LD13); a NEW composition of the BUILT install-portability surfaces (tools/kata_settings.py, tools/project_find.py, tools/kata_install.py, tools/intent_scaffold.py) + the initiate/bootstrap/closeout/loop spine skills. "convert-to-loop" and the ".planning/ scaffold" are NEW here (see "What is NEW", below), not a reused convert flow. | — |
| `kata-orchestrate` | 0.10.2 | 5 | coordinate | experimental | adapted-from cpp-orchestrator (CryptoPortfolioPlanner harness) + Anthropic effective-harnesses-for-long-running-agents + managed-agents | Plan-guardian lead: assign, partition files, gate, no-drift |
| `kata-preflight` | 0.2.0 | 2 | coordinate | experimental | new (KataHarness original, PRE-FLIGHT spine phase D29/N2); drives tools/kata_preflight.py (N1 engine); argv-builder pattern from the _COMMAND_BUILDERS registry in tools/kata_dispatch.py; injectable-runner from _subprocess_runner in tools/kata_dispatch.py | — |
| `kata-readiness` | 0.2.1 | 1 | coordinate | experimental | new (KataHarness original); pattern echoes environment "doctor" checks (e.g. brew/flutter doctor) — abstract, no external code adapted | Pre-run harness+target readiness check (bootstrap-invoked or standalone doctor) |
| `kata-sprint` | 0.1.0 | 2 | coordinate | experimental | new (KataHarness original — sprint-cadence D80; the thin boundary coordinator, GB4-C) | Own the sprint boundary (G1–G4 change-control); incremental delivery only |
| `kata-worktree` | 0.1.0 | 1 | coordinate | experimental | adapted-from CryptoPortfolioPlanner worktree proof (LESSONS-LEARNED L2/L3) | Per-owner git-worktree isolation for concurrent code |
| `kata-characterize` | 0.1.0 | 3 | execute | experimental | new (KataHarness original, Debug Mode P2b — characterization-suite generation, DESIGN LD6+§5) | — |
| `kata-deviate` | 0.1.0 | 4 | execute | experimental | new (KataHarness original, Debug Mode P2a — deviation-discovery pipeline, DESIGN LD4–LD5) | — |
| `kata-diagnose-full` | 0.1.0 | 3 | execute | experimental | adapted-from mattpocock/skills engineering/diagnose | — |
| `kata-diagnose-light` | 0.1.0 | 2 | execute | experimental | adapted-from mattpocock/skills engineering/diagnose | — |
| `kata-iac-cloudformation` | 0.2.0 | 3 | execute | experimental | new (KataHarness original — IaC-safety specialist N3, DESIGN §2; shared safety contract protocol/iac-safety.md; Snyk IaC scanner wiring IAC-4) | — |
| `kata-iac-terraform` | 0.2.0 | 3 | execute | experimental | new (KataHarness original — IaC-safety specialist N3, DESIGN §2; shared safety contract protocol/iac-safety.md; Snyk IaC scanner wiring IAC-4) | — |
| `kata-lang-profile` | 0.1.2 | 2 | execute | experimental | new (KataHarness original — Debug Mode LD10 in-mode language prompt-profiles, DESIGN §3 LD10 / PLAN-p3 Slice D). Selection + overlay mechanism mirrors the IaC specialist-injection precedent (skills/coordinate/kata-orchestrate "IaC activation" block + iac_detect.classify_task); STYLE templates are the sibling specialists kata-iac-terraform / kata-iac-cloudformation. | — |
| `kata-tdd` | 0.4.0 | 3 | execute | experimental | adapted-from mattpocock/skills engineering/tdd | Red-green-refactor on a vertical slice |
| `kata-benchmark-report` | 0.1.0 | 1 | evaluate | experimental | new (KataHarness original — kata-loop-benchmark report; mirrors the kata-report/kata-debrief two-tier {{TOKEN}} render contract; engine tools/benchmark.py) | — |
| `kata-debrief` | 0.1.0 | 1 | evaluate | experimental | new (KataHarness original, Debug Mode P3 — LD12 closeout confidence report + LD3 recommendations / offered version-up; mirrors the kata-report two-tier + {{TOKEN}} render contract) | — |
| `kata-evaluate` | 0.3.1 | 2 | evaluate | experimental | adapted-from cpp-evaluation (CryptoPortfolioPlanner) + Anthropic fresh-context evaluator pattern | Fresh-context, no-write, default-FAIL PASS/NEEDS_WORK |
| `kata-inline-eval` | 0.1.0 | 1 | evaluate | experimental | — | — |
| `kata-report` | 0.1.2 | 1 | evaluate | experimental | new (KataHarness original — the D32 report, minimal v1; sprint-cadence D85/D2) | One-page report of a gated unit of work (reports the gate, never gates) |
| `kata-review-advanced` | 0.1.2 | 3 | evaluate | experimental | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-review-essential` | 0.1.2 | 1 | evaluate | experimental | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-review-standard` | 0.1.2 | 2 | evaluate | experimental | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-slop-check` | 0.1.0 | 2 | evaluate | experimental | General heuristics original to KataHarness; adopted-check concepts from ai-slop-detector by flamehaven01 (Flamehaven Labs), https://github.com/flamehaven01/ai-slop-detector, MIT License (Copyright (c) 2026 Flamehaven Labs) — concepts re-implemented as in-context heuristics, no source code copied. | — |
| `kata-validate` | 0.1.0 | 3 | evaluate | experimental | new (KataHarness original — validation mini-loop). Adapted patterns: Guardrails-AI on_fail propose-vs-apply seam; OASIS SARIF severity taxonomy (error/warning/note); Reflexion bounded self-critique loop. | — |
| `kata-closeout` | 0.1.0 | 2 | handoff | experimental | new (KataHarness original — Phase 2 Kata Loop back-half, D89/DESIGN §3) | — |
| `kata-defer` | 0.1.0 | 1 | handoff | experimental | new (KataHarness original, D42/D43 GB9) — the structural complement to the no-drift spine; assumption-log role added by D71 (Priming-and-Grill autonomous floor) | Park off-plan items + log grill-skip assumptions at the boundary, never drift the frozen plan |
| `kata-handoff` | 0.2.0 | 1 | handoff | experimental | adapted-from mattpocock/skills {handoff} + Anthropic reset-with-handoff / compaction guidance | Two-way durable handoff (session/agent/tool) |
| `kata-orient` | 0.2.1 | 2 | handoff | experimental | new (KataHarness original, loop-cognition AO-GB1/2/3 + D76) — receiving half of the two-way handoff (spine #5); three-tier assembly echoes Hermes prompt_builder (stable/context/volatile); nested-AGENTS.md rollup standard | Assemble a subagent's launch orientation: three-tier, task-type-tailored, derived pointers+callouts, routed questions — the read half of handoff |
| `kata-selfhandoff` | 0.2.0 | 1 | handoff | experimental | adapted-from Anthropic compaction guidance + mattpocock caveman compression | Configurable context-threshold self-handoff (delegates artifact to kata-handoff) |
| `kata-understand` | 0.1.0 | 2 | handoff | experimental | new (KataHarness original, Phase 2 GL-R2c / DESIGN §3 / PLAN-phase2 Task C1) — comprehension-map half of the closeout back-half; backed by the F2 graph runtime (tools/graph_gen.py → kata.graph.json) | — |
| `kata-improve` | 0.2.0 | 1 | meta | experimental | adapted-from the Improvement Kata (Toyota Kata) + mattpocock/skills engineering/improve-codebase-architecture | Fold cross-run lessons back into the skills/ tree; calls kata-write-skill |
| `kata-promote` | 0.1.0 | 2 | meta | experimental | new (KataHarness original, loop-cognition ML / LC-GB3/GB4/GB5, D60-D69) — two-stage gate vs Hermes' no-gate instant-universal model (RESEARCH.md bake-off: borrow the closed loop, keep our human gate) | Stage-2 human gate: promote a grounded agent-distilled candidate skill (experimental→stable + scope bump) into the toolkit; honors engram.autonomy |
| `kata-write-skill` | 0.1.0 | 1 | meta | experimental | adapted-from mattpocock/skills productivity/write-a-skill | Author new skills to STANDARDS (points, not restates); kata-improve calls it |
<!-- SKILL-INDEX:END -->

</details>

---

## Install

**Prerequisites:** `git`, and either [`uv`](https://docs.astral.sh/uv/) **or** Python 3.12+. The installer clones
KataHarness to `~/.kata-home` (`%USERPROFILE%\.kata-home` on Windows) and links (or copies) the skills into your
agent host. Default platform is **`claude`**; `--platform` also accepts `codex` and `kiro`.

**Windows (PowerShell):**
```powershell
irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 | iex
```

**macOS / Linux (and Git Bash on Windows):**
```sh
curl -fsSL https://raw.githubusercontent.com/taurran/kataharness/master/install.sh | sh
```

**Choose a platform** (download-then-run so you can pass a flag — and inspect the script first):
```powershell
# Windows
irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 -OutFile install.ps1; .\install.ps1 --platform codex
```
```sh
# macOS / Linux
curl -fsSL https://raw.githubusercontent.com/taurran/kataharness/master/install.sh -o install.sh; sh install.sh --platform codex
```

---

## Lifecycle — update · factory-reset · wipe & reinstall · uninstall

Every command below is copy-paste ready. Windows uses the scripts in `%USERPROFILE%\.kata-home\`; macOS/Linux
uses the mirrors in `~/.kata-home/`.

### ↻ Update — pull the latest engine + skills
Fast-forwards your clone and re-links the skills. Add `--check` to preview without changing anything; set
`KATA_REF` to pin a branch/tag/SHA (default `master`).

```powershell
# Windows
& "$env:USERPROFILE\.kata-home\update.ps1"            # apply the update
& "$env:USERPROFILE\.kata-home\update.ps1" --check    # preview only, no changes
```
```sh
# macOS / Linux
sh ~/.kata-home/update.sh                             # apply the update
sh ~/.kata-home/update.sh --check                    # preview only, no changes
```
> If you customized tracked base files, update **aborts** rather than clobbering them — re-run with
> `--discard-local` to overwrite, or commit/stash first. (Your overlays and forks are safe; they're separate.)

### ⟲ Factory-reset — restore pristine skills
Re-links the shipped skills without touching your clone's git history. Add `--hard` to also **clear the overlay
store** and reset the base tree (destructive — requires `--yes` when non-interactive).

```powershell
# Windows
& "$env:USERPROFILE\.kata-home\update.ps1" --factory-reset
& "$env:USERPROFILE\.kata-home\update.ps1" --factory-reset --hard --yes   # also wipe overlays/forks
```
```sh
# macOS / Linux
sh ~/.kata-home/update.sh --factory-reset
sh ~/.kata-home/update.sh --factory-reset --hard --yes                    # also wipe overlays/forks
```

### ⤾ Wipe & reinstall — nuke the clone and start fresh
Deletes `~/.kata-home` entirely and reinstalls from scratch. Safe: `~/.kata-home` is just the harness clone —
your projects and vault live elsewhere.

```powershell
# Windows
Remove-Item -Recurse -Force "$env:USERPROFILE\.kata-home"; irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 | iex
```
```sh
# macOS / Linux
rm -rf ~/.kata-home && curl -fsSL https://raw.githubusercontent.com/taurran/kataharness/master/install.sh | sh
```

### ✖ Uninstall — remove KataHarness from a project/host
Removes the flat-linked skills, the settings entry, and the router stanza from the **given** project. Run once
per project you installed into (the harness keeps no registry of every target). Add `--yes` to skip the prompt.

```powershell
# Windows
& "$env:USERPROFILE\.kata-home\uninstall.ps1" --platform claude --target-dir "C:\path\to\project" --yes
```
```sh
# macOS / Linux
sh ~/.kata-home/uninstall.sh --platform claude --target-dir /path/to/project --yes
```
> To remove the harness itself as well, follow up with the **wipe** command above
> (`Remove-Item …\.kata-home` / `rm -rf ~/.kata-home`).

---

## Start a run

Restart your agent so it loads the skills, then use a slash-command (Claude Code shown) — or just ask:

```text
/kata            show the command index
/kata-start      start a run (the front door → kata-initiate)
/kata-onboard    guided tour / convert an existing repo
/kata-status     show the live run board
/kata-resume     pick up a crashed or compacted run where it left off
/kata-validate   run the skill-conformance validator
```

> **“Start a KataHarness run on `<your project>`.”** — plain English works too; the installer prints these same
> next steps on success.

---

## Docs / status

**v0.2.0, experimental.** The single-model Claude core is the proven path; multi-model routing and the
Codex/Kiro adapters are partially built; IaC *apply* is gated and not shipped runnable. Read next:

- [`AGENTS.md`](./AGENTS.md) — the vision, the spine, how to work in the repo (canonical).
- [`docs/SETUP.md`](./docs/SETUP.md) — install / update / overlay / factory-reset / uninstall in depth, plus the
  `curl | sh` security tradeoff and the audit-friendly git-clone path.
- [`docs/STANDARDS.md`](./docs/STANDARDS.md) — frontmatter, versioning, and naming conventions.

> **Security note.** `curl … | sh` and `irm … | iex` execute bytes as they stream — there's nothing to verify
> until after it runs. Pin a known ref with `KATA_REF`, or download-then-run to inspect first (see
> [`docs/SETUP.md`](./docs/SETUP.md)). On Windows without Developer Mode, the installer falls back to copy-mode
> (works fine; re-run `update` after each change to refresh copied skills).

Built on Anthropic's long-running-agent harness guidance and the best of
[mattpocock/skills](https://github.com/mattpocock/skills), GSD, BMAD, and DDD's ubiquitous language — attributed
per skill in the `source` column. We stand on shoulders.
