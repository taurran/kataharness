# KataHarness

**A tool-agnostic, skills-based agent harness that one-shots complex coding tasks.** It front-loads deep,
doc-grounded planning, **freezes the plan**, executes it faithfully across one or many subagents, and gates
"done" behind a **fresh-context, default-FAIL evaluator** — then folds every run's lessons back into itself.
The name is the method: the **Improvement Kata** — *every loop sharpens the loop.*

> **Status: pre-v0.1, experimental.** The single-model Claude core is the proven path; multi-model routing
> and the Codex/Kiro adapters are partially built. Honest about maturity — see [Docs / status](#docs--status).
> New here? Start with [`AGENTS.md`](./AGENTS.md) (the vision + the spine).

---

## What makes it different

Most "agentic loops" are a thin wrapper around *prompt → generate → done*. KataHarness adds the guardrails
that make autonomy trustworthy:

- **The plan doesn't drift.** The plan is *frozen* after planning; the orchestrator is its guardian; worker
  subagents execute and talk laterally but **never re-plan**. An unknown escalates or parks — it's never silently guessed.
- **Nothing is "done" until proven.** A **fresh-context, no-write, default-FAIL** evaluator independently reads
  the evidence and must return PASS. *Nothing certifies its own work.*
- **Tool-agnostic core + thin adapters.** One agnostic core (protocol, skills, planning engine, quality loop)
  with per-tool adapters (`claude` today; `codex`/`kiro` next) — not locked to one vendor.
- **Everything is versioned.** Every skill carries a semver in its frontmatter; the generated catalog is the
  machine source of truth for what exists and at what version.
- **Self-improvement folds into the skills.** Lessons from each run are distilled back into the *skills
  themselves* (through a human promotion gate) — not just appended to a ledger.
- **Adapt without forking upstream.** Customize any skill via a local **overlay** or a promoted **fork** — your
  changes survive every update; the upstream base stays pristine and is never edited or lost.
- **Zero-dependency install.** Pure-stdlib Python engine; one command drops it into your agent host.

---

## Features — what's in the box

**The Kata Loop** runs six phases, with every run feeding the next:

```
GRILL → FREEZE → EXECUTE → EVALUATE → HANDOFF → IMPROVE
interrogate  lock the   plan-faithful  fresh-context  durable,    distil + promote
the spec     design +   parallel       no-write,      two-way,    + fold lessons
             plan       workers         DEFAULT-FAIL   git-committed   → next run
```

- **47 skills** across six families — `plan` · `coordinate` · `execute` · `evaluate` · `handoff` · `meta` —
  plus the `initiation` / `closeout` modules. The full catalog is below.
- **Modes & tiers.** Three modes (**Essential · Standard · Advanced**) set breadth and depth; tiered skill
  families (`kata-grill`, `kata-plan`, `kata-review`, `kata-diagnose`) share one rubric and expose a depth dial.
  A **bake-off** runs N variants in parallel, judges them, and refines the winner up a tier.
- **The quality loop.** A **default-FAIL** evaluator owns "done," backed by an **adversarial review** before
  every merge and an optional **AI-slop check** that fails a run for spiraling / over-claiming signals.
- **Install lifecycle.** One-command install, `--update` (with `--check`), `--factory-reset`, a clean
  uninstaller, and a version stamp + skill manifest.
- **Local adaptation.** An **overlay store** customizes skills in place; deeper rewrites route through a
  **supersedes/fork** candidate and a human promotion gate — upstream is never touched.

See [`docs/SETUP.md`](./docs/SETUP.md) for the install/update/overlay/factory-reset depth.

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
| `kata-plan-advanced` | 0.1.0 | 4 | plan | experimental | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-plan-essential` | 0.1.0 | 2 | plan | experimental | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-plan-standard` | 0.1.0 | 3 | plan | experimental | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-research` | 0.1.0 | 3 | plan | experimental | new (KataHarness original, loop-cognition RS-GB1/2/3, D62) — fresh-context no-write evaluator pattern (L4/L5) applied to in-loop research; escalation-routed like kata-orchestrate's no-re-plan escape valve (D52) | Research a must-deliver gap with no in-plan solution; ground every claim; return findings for the grounding gate, never re-plan |
| `kata-board` | 0.1.0 | 2 | coordinate | experimental | adapted-from Claude Agent Teams protocol (agnostic file reimplementation); CryptoPortfolioPlanner LESSONS-LEARNED L3 | Append-only mailbox/message board for lateral peer comms |
| `kata-bootstrap` | 0.1.0 | 2 | coordinate | experimental | adapted-from GSD discuss-phase Q&A model + docs/MODES-DESIGN.md D24c composition ladder (KataHarness design) | Compose a run (run-shape + ladder), preview cost, write kata.config, launch |
| `kata-initiate` | 0.2.0 | 3 | coordinate | experimental | new (KataHarness original, Phase 1 Kata Loop — D88/D91); composes kata-readiness, kata-grill, kata-bootstrap, kata-context | — |
| `kata-loop` | 0.1.0 | 2 | coordinate | experimental | new (KataHarness original — Phase 3 Kata Loop conductor, D87/DESIGN §1) | — |
| `kata-onboard` | 0.2.0 | 3 | coordinate | experimental | new (KataHarness original, Debug-Mode P3 / LD13 — DESIGN R6/LD13); a NEW composition of the BUILT install-portability surfaces (tools/kata_settings.py, tools/project_find.py, tools/kata_install.py, tools/intent_scaffold.py) + the initiate/bootstrap/closeout/loop spine skills. "convert-to-loop" and the ".planning/ scaffold" are NEW here (see "What is NEW", below), not a reused convert flow. | — |
| `kata-orchestrate` | 0.2.0 | 5 | coordinate | experimental | adapted-from cpp-orchestrator (CryptoPortfolioPlanner harness) + Anthropic effective-harnesses-for-long-running-agents + managed-agents | Plan-guardian lead: assign, partition files, gate, no-drift |
| `kata-preflight` | 0.1.0 | 2 | coordinate | experimental | new (KataHarness original, PRE-FLIGHT spine phase D29/N2); drives tools/kata_preflight.py (N1 engine); argv-builder pattern from the _COMMAND_BUILDERS registry in tools/kata_dispatch.py; injectable-runner from _subprocess_runner in tools/kata_dispatch.py | — |
| `kata-readiness` | 0.1.0 | 1 | coordinate | experimental | new (KataHarness original); pattern echoes environment "doctor" checks (e.g. brew/flutter doctor) — abstract, no external code adapted | Pre-run harness+target readiness check (bootstrap-invoked or standalone doctor) |
| `kata-sprint` | 0.1.0 | 2 | coordinate | experimental | new (KataHarness original — sprint-cadence D80; the thin boundary coordinator, GB4-C) | Own the sprint boundary (G1–G4 change-control); incremental delivery only |
| `kata-worktree` | 0.1.0 | 1 | coordinate | experimental | adapted-from CryptoPortfolioPlanner worktree proof (LESSONS-LEARNED L2/L3) | Per-owner git-worktree isolation for concurrent code |
| `kata-characterize` | 0.1.0 | 3 | execute | experimental | new (KataHarness original, Debug Mode P2b — characterization-suite generation, DESIGN LD6+§5) | — |
| `kata-deviate` | 0.1.0 | 4 | execute | experimental | new (KataHarness original, Debug Mode P2a — deviation-discovery pipeline, DESIGN LD4–LD5) | — |
| `kata-diagnose-full` | 0.1.0 | 3 | execute | experimental | adapted-from mattpocock/skills engineering/diagnose | — |
| `kata-diagnose-light` | 0.1.0 | 2 | execute | experimental | adapted-from mattpocock/skills engineering/diagnose | — |
| `kata-iac-cloudformation` | 0.2.0 | 3 | execute | experimental | new (KataHarness original — IaC-safety specialist N3, DESIGN §2; shared safety contract protocol/iac-safety.md; Snyk IaC scanner wiring IAC-4) | — |
| `kata-iac-terraform` | 0.2.0 | 3 | execute | experimental | new (KataHarness original — IaC-safety specialist N3, DESIGN §2; shared safety contract protocol/iac-safety.md; Snyk IaC scanner wiring IAC-4) | — |
| `kata-lang-profile` | 0.1.0 | 2 | execute | experimental | new (KataHarness original — Debug Mode LD10 in-mode language prompt-profiles, DESIGN §3 LD10 / PLAN-p3 Slice D). Selection + overlay mechanism mirrors the IaC specialist-injection precedent (skills/coordinate/kata-orchestrate "IaC activation" block + iac_detect.classify_task); STYLE templates are the sibling specialists kata-iac-terraform / kata-iac-cloudformation. | — |
| `kata-tdd` | 0.1.0 | 3 | execute | experimental | adapted-from mattpocock/skills engineering/tdd | Red-green-refactor on a vertical slice |
| `kata-benchmark-report` | 0.1.0 | 1 | evaluate | experimental | new (KataHarness original — kata-loop-benchmark report; mirrors the kata-report/kata-debrief two-tier {{TOKEN}} render contract; engine tools/benchmark.py) | — |
| `kata-debrief` | 0.1.0 | 1 | evaluate | experimental | new (KataHarness original, Debug Mode P3 — LD12 closeout confidence report + LD3 recommendations / offered version-up; mirrors the kata-report two-tier + {{TOKEN}} render contract) | — |
| `kata-evaluate` | 0.1.0 | 2 | evaluate | experimental | adapted-from cpp-evaluation (CryptoPortfolioPlanner) + Anthropic fresh-context evaluator pattern | Fresh-context, no-write, default-FAIL PASS/NEEDS_WORK |
| `kata-report` | 0.1.0 | 1 | evaluate | experimental | new (KataHarness original — the D32 report, minimal v1; sprint-cadence D85/D2) | One-page report of a gated unit of work (reports the gate, never gates) |
| `kata-review-advanced` | 0.1.0 | 3 | evaluate | experimental | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-review-essential` | 0.1.0 | 1 | evaluate | experimental | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-review-standard` | 0.1.0 | 2 | evaluate | experimental | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-slop-check` | 0.1.0 | 2 | evaluate | experimental | General heuristics original to KataHarness; adopted-check concepts from ai-slop-detector by flamehaven01 (Flamehaven Labs), https://github.com/flamehaven01/ai-slop-detector, MIT License (Copyright (c) 2026 Flamehaven Labs) — concepts re-implemented as in-context heuristics, no source code copied. | — |
| `kata-validate` | 0.1.0 | 3 | evaluate | experimental | new (KataHarness original — validation mini-loop). Adapted patterns: Guardrails-AI on_fail propose-vs-apply seam; OASIS SARIF severity taxonomy (error/warning/note); Reflexion bounded self-critique loop. | — |
| `kata-closeout` | 0.1.0 | 2 | handoff | experimental | new (KataHarness original — Phase 2 Kata Loop back-half, D89/DESIGN §3) | — |
| `kata-defer` | 0.1.0 | 1 | handoff | experimental | new (KataHarness original, D42/D43 GB9) — the structural complement to the no-drift spine; assumption-log role added by D71 (Priming-and-Grill autonomous floor) | Park off-plan items + log grill-skip assumptions at the boundary, never drift the frozen plan |
| `kata-handoff` | 0.1.0 | 1 | handoff | experimental | adapted-from mattpocock/skills {handoff} + Anthropic reset-with-handoff / compaction guidance | Two-way durable handoff (session/agent/tool) |
| `kata-orient` | 0.1.0 | 2 | handoff | experimental | new (KataHarness original, loop-cognition AO-GB1/2/3 + D76) — receiving half of the two-way handoff (spine #5); three-tier assembly echoes Hermes prompt_builder (stable/context/volatile); nested-AGENTS.md rollup standard | Assemble a subagent's launch orientation: three-tier, task-type-tailored, derived pointers+callouts, routed questions — the read half of handoff |
| `kata-selfhandoff` | 0.1.0 | 1 | handoff | experimental | adapted-from Anthropic compaction guidance + mattpocock caveman compression | Configurable context-threshold self-handoff (delegates artifact to kata-handoff) |
| `kata-understand` | 0.1.0 | 2 | handoff | experimental | new (KataHarness original, Phase 2 GL-R2c / DESIGN §3 / PLAN-phase2 Task C1) — comprehension-map half of the closeout back-half; backed by the F2 graph runtime (tools/graph_gen.py → kata.graph.json) | — |
| `kata-improve` | 0.2.0 | 1 | meta | experimental | adapted-from the Improvement Kata (Toyota Kata) + mattpocock/skills engineering/improve-codebase-architecture | Fold cross-run lessons back into the skills/ tree; calls kata-write-skill |
| `kata-promote` | 0.1.0 | 2 | meta | experimental | new (KataHarness original, loop-cognition ML / LC-GB3/GB4/GB5, D60-D69) — two-stage gate vs Hermes' no-gate instant-universal model (RESEARCH.md bake-off: borrow the closed loop, keep our human gate) | Stage-2 human gate: promote a grounded agent-distilled candidate skill (experimental→stable + scope bump) into the toolkit; honors engram.autonomy |
| `kata-write-skill` | 0.1.0 | 1 | meta | experimental | adapted-from mattpocock/skills productivity/write-a-skill | Author new skills to STANDARDS (points, not restates); kata-improve calls it |
<!-- SKILL-INDEX:END -->

</details>

---

## Installation

**Prerequisites:** `git` and either [`uv`](https://docs.astral.sh/uv/) **or** Python 3.12+. Both installers
clone KataHarness to `~/.kata-home` (`%USERPROFILE%\.kata-home` on Windows) and link/copy the skills into your
agent host. Default platform is **`claude`**.

### Windows (PowerShell) — primary route

```powershell
irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 | iex
```

To choose a platform, download-then-run:

```powershell
irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 -OutFile install.ps1; .\install.ps1 --platform codex
```

### macOS / Linux (and Git Bash on Windows)

```sh
curl -fsSL https://raw.githubusercontent.com/taurran/kataharness/master/install.sh | sh
```

Pass a platform via the piped POSIX form:

```sh
curl -fsSL https://raw.githubusercontent.com/taurran/kataharness/master/install.sh | sh -s -- --platform codex
```

`--platform` accepts `claude` · `codex` · `kiro`.

### Update & uninstall

```powershell
# PowerShell
& "$env:USERPROFILE\.kata-home\update.ps1"            # add --check to report without changing anything
& "$env:USERPROFILE\.kata-home\uninstall.ps1"
```

```sh
# POSIX
sh ~/.kata-home/update.sh                             # add --check to report without changing anything
sh ~/.kata-home/uninstall.sh
```

### Reinstall / refresh

`install.ps1` / `install.sh` **reuse an existing `~/.kata-home`** (they do not re-clone). To pull the latest
engine *and* skills, either run `update` (above), or do a clean reinstall:

```powershell
# Windows — clean reinstall (safe: ~/.kata-home is just the clone; your vault is separate)
Remove-Item -Recurse -Force "$env:USERPROFILE\.kata-home"; irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 | iex
```

```sh
# POSIX — clean reinstall
rm -rf ~/.kata-home && curl -fsSL https://raw.githubusercontent.com/taurran/kataharness/master/install.sh | sh
```

### Start a run

Restart your agent so it loads the skills, then begin a run (Claude Code shown):

```text
/kata-initiate     start a run (the front door)
/kata-onboard      guided tour on an existing repo
/kata-bootstrap    configure and launch a run
```

…or just ask: **“Start a KataHarness run on `<your project>`.”** The installer prints these same next steps.

### Notes

- **Security:** `curl … | sh` and `irm … | iex` execute bytes as they stream — there is nothing to verify
  until after it runs. Pin a known ref with the `KATA_REF` env var, or download-then-run to inspect first; see
  [`docs/SETUP.md`](./docs/SETUP.md) for the full tradeoff and audit-friendly git-clone path.
- **Windows symlinks:** without Developer Mode, the installer falls back to **copy-mode** (works fine; just
  re-run `update.ps1` after each update to refresh copied skills). Detail in [`docs/SETUP.md`](./docs/SETUP.md).

---

## Docs / status

**Pre-v0.1, experimental.** The single-model Claude core is the proven path; multi-model routing and the
Codex/Kiro adapters are partially built. Read next:

- [`AGENTS.md`](./AGENTS.md) — the vision, the spine, how to work in the repo (canonical).
- [`docs/SETUP.md`](./docs/SETUP.md) — install / update / overlay / factory-reset / uninstall in depth.
- [`docs/STANDARDS.md`](./docs/STANDARDS.md) — frontmatter, versioning, and naming conventions.

Built on Anthropic's long-running-agent harness guidance and the best of
[mattpocock/skills](https://github.com/mattpocock/skills), GSD, BMAD, and DDD's ubiquitous language —
attributed per skill in the `source` column. We stand on shoulders.
