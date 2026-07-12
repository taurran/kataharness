# KataHarness

### The best of modern agentic engineering — turned into output you can trust, for the fewest tokens it takes to prove it.

**Bottom line:** AI can write a week of code in an hour — it just can't tell you which of it is
actually *right*, and checking everything with an AI judge burns tokens fast. KataHarness exists to
close that gap. It takes the cutting-edge agentic practices the industry is converging on — a
plain-English spec interrogated until it's airtight, a **frozen plan** so nothing drifts, a team of AI
workers, and independent, adversarial review whose default verdict is **no** — and combines them into
one loop that **relentlessly proves its own output is correct while spending the fewest tokens to get
there**. What you get back is work you can *delegate and trust*, not a fast pile of code you still have
to babysit — because unverified AI output isn't a shortcut, it's a liability you inherit, and the only
output worth shipping is the output that's been proven right. The name *is* the method: the
**Improvement Kata** — *every loop sharpens the loop.*

**Easy to start.** One command installs it into the agent host you already use. *"Start a KataHarness
run on my project"* is the whole interface — the harness asks you one plain question (*how careful,
and how often should I check in?*) and tunes the entire run's depth, checkpoints, and cost from your
answer. No config safari required.

**Easy on the bill.** The loop spends models the way a good engineering lead spends senior time:
premium judgment reserved for the hard moments — and only inside a budget you approve up front —
routine work tiered down to fast, cheap models, and **zero evaluator cost while the work is green**.
It routes by evidence: failing work escalates to a stronger model, proven-easy work steps down, and
every run's telemetry teaches the next one. And economy never buys down quality — **every deliverable
still clears the same grounded, default-FAIL assessment**; the savings come from smarter routing,
never from skipping a check.

**Relentless about the result.** Nothing in this loop certifies its own work. Plans are frozen,
reviews are adversarial, tests are mutation-proven, scorecards give no credit for tests that never
ran — and the run is built to survive crashes, killed terminals, and context limits on a git-durable
trail, so a long walk-away comes back as reviewable evidence, not a mystery diff.

Whether this is your first agent harness or your fifth: if you have ever wanted to *delegate* real
work to an AI — not babysit it — this is the loop built for the trust half of that transaction.

> **v0.3.0 · beta.** New: **adaptive tiering**, the evidence-driven model routing described
> above — full story under *What's in the box* → 🎯, full history in the [CHANGELOG](./CHANGELOG.md),
> honest maturity notes under *Docs / status* at the bottom of this page. New here? Start with
> [`AGENTS.md`](./AGENTS.md).

---

## Why it stands apart

Most "agentic loops" are a thin wrapper around *prompt → generate → hope*. The disciplined ones that do
validate tend to buy rigor with tokens — an LLM judge on every step, whether or not anything is wrong.
KataHarness refuses that trade. It is built for **both**: deep, adversarial validation *and* measured
token/wall-clock efficiency, in one loop.

- **⚡ Deep validation that costs ~nothing when the work is green.** The inline corrective ladder triggers
  on cheap, rule-verifiable evidence (test exits, lane drift, missing records) — **an LLM judge runs ONLY
  after a trigger**, at an economy tier. Measured on this repo's own instrumented v0.2.1 build (retroactive
  scan, real commits, not arranged): **44 of 57 worker checkpoints scored green — 0 evaluator calls, 0
  tokens on every one** (corroborated 25/31 on the integrated branch). The green path is free; the red path
  gets judgment. Fixed-cadence "judge every step" harnesses pay that cost on every step.
- **🧊 The plan doesn't drift.** The plan is *frozen* after planning; the orchestrator guards it; worker
  subagents execute and talk laterally but **never re-plan.** An unknown escalates or parks — it is never
  silently guessed.
- **🛡️ Nothing certifies its own work.** A **fresh-context, no-write, default-FAIL** evaluator independently
  reads the evidence and must return PASS — backed by an **adversarial review** before every merge. In this
  project's own build, those fresh-context reviews have repeatedly caught real defects a 2,895-test green
  suite had blessed (the v0.2.1 merge gate alone caught and folded two HIGHs).
- **🔋 The run outlives the context window.** v0.2.1's gauge-driven self-handoff + crash-proof resume
  (once the hook chain is installed via `kata_install.py --install-hooks`): a compaction, crash, or
  killed terminal costs you a wave boundary, not the run.
- **🧠 A learning loop with a gate.** Telemetry from instrumented runs feeds threshold calibration; lessons
  flow back into the shipped skills — and the candidate-skill promotion path is **two-stage and human-gated**,
  never silent self-modification *(gate built and validated; first candidate yet to pass through it)*.
- **🏁 It benchmarks itself.** A built-in scoring engine ranks candidate approaches on real fail-to-pass /
  pass-to-pass evidence and produces an **honest scorecard** — quality you can measure, not vibes.
- **🧩 Tool-agnostic core + thin adapters.** One agnostic core (protocol, skills, planning engine, quality
  loop) with per-tool adapters and per-platform config guides — not locked to one vendor.
- **🪶 Zero-dependency install.** A pure-stdlib Python **installer** — one command drops it into your
  agent host. (Engine extras — yaml for crash-restore, tree-sitter for the code graph, rich for the
  dashboard — resolve automatically via `uv` from the shipped lockfile.)

---

## Picking a harness — where KataHarness exceeds

Positioning by design philosophy, not benchmark claims — each of these tools is excellent at its own
job, and we benchmark ourselves, not others (see *Built-in benchmarking*). KataHarness is built for
one user in particular: **the developer delegating real, production-bound work to agents, who needs
the output to be *provably* right — and the token bill to stay rational while proving it.**

- **vs. Claude Code's native orchestration (subagents, workflows, the multi-agent "ultra" review).**
  Claude Code ships world-class *primitives*; KataHarness is the **opinionated discipline layered on
  top of them** — frozen plans workers structurally cannot drift, a default-FAIL fresh-context gate on
  *every* task (not review-on-request), evidence-routed model spend, and a git-durable trail that
  survives crashes and compactions. It runs **on** Claude Code — an extension of it, not a rival.
  Pick Kata when the whole loop needs governing, not just the review step.
- **vs. Hermes (Nous Research).** Hermes built its identity on the closed learning loop; we studied
  it formally and **based our approach on its applicable traits — while keeping our gates.** Hermes
  ships no default-FAIL testing model and promotes learned behavior without a human gate; Kata's
  learning is telemetry-grounded and passes a **two-stage human gate BEFORE anything executes with
  it**, and during execution the inline evaluator identifies where work must **hard-fork** (kill +
  fresh attempt branch) rather than drift on. Pick Kata when a wrong "learned lesson" or an
  unverified deliverable is expensive.
- **vs. OpenHands (ex-OpenDevin).** A leading open autonomous-dev platform — strong sandboxing, broad
  tooling, benchmark-driven. Its loop optimizes for *task completion*; Kata's optimizes for
  **provable completion**: mutation-proven tests, adversarial review before every merge, honest
  scorecards with no credit for tests that never ran. Pick Kata where "the agent said it works" is
  not evidence.
- **vs. Aider.** The benchmark interactive pair-programming CLI. Aider keeps you in the loop
  prompt-by-prompt; Kata is built for the **walk-away** — one approval bundle, then hours of gated
  autonomous execution with a crash-proof trail. Pick Aider to code *with* an AI; pick Kata to
  *delegate* to one and trust what comes back.

What no one else on this list ships together: **default-FAIL gates on everything + evidence-routed
model spend** — validation depth and token thrift as one mechanism, not a trade-off.

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

### 🛡️ The quality loop — nothing certifies its own work
The backbone everything else hangs on — and the reason you can trust a run you walked away from.
Nothing here grades its own work. A **default-FAIL evaluator** owns the definition of "done" (work is
guilty until it proves it passed). A separate **adversarial reviewer** attacks the design before every
merge. Every test is **mutation-proven** — if it still passes after you delete what it checks, it
doesn't count. An optional **slop check** fails a run that starts spiraling or over-claiming, and a
standing guard stops decision-code from quietly degrading on bad input.

### 🎯 Adaptive tiering — the loop picks models by evidence *(new in v0.3.0)*
Most tools pick one model and pay its price for everything. KataHarness decides per task, using what
the run is actually telling it. A task that fails its check twice is **retried on a stronger model**.
Work rated simple, or on a clean streak, **drops down a rung** (coding only, and it backs off the
moment anything fails). Cancelling work gets a **cheap second opinion first**.

Your most expensive "premium" model is reserved for **the hard moments you approved** — final gates,
re-reviews, escalations, retries — inside a **spending cap you consent to up front** (you see the exact
triggers and the limit). Run out, and it drops back to your normal model, loudly. Every choice is
logged as an auditable line.

On this repo's own prior build, the shipped engine **modeled an 86% cut in premium-model calls
(59→8)** while telling real failures from false alarms with **perfect precision — every one of 13
noise signals correctly ignored**, so no good work is redone on a false trigger *(modeled from
committed inputs, not yet measured live; the precision figure rests on an n=1 overturn
observation — the model's weakest assumption — and a real A/B is queued)*. None of this turns on unless you add
the config; without it, every part stays off.

### ⚡ The inline evaluator/reroll — catch a bad chunk as it happens *(v0.2.0)*
A cheap way to catch a bad piece of work the moment it lands, without paying a model to babysit every
step. The idea (scheduler *principles*, not code, adapted from DeepSeek's **DSpark** paper): watch a
**cheap, rule-checkable signal** on each checkpoint — never the worker scoring itself — and only call
a judge when that signal trips. The default-FAIL gate keeps the final say, so a mis-tuned version just
falls back to normal behavior.

We deliberately **don't** run a judge on a fixed timer: judging a chunk costs about as much as building
it, so grading healthy work is a net loss. Proven end to end: signal trips → judge cites the diff →
the chunk is redone → green. `inlineEval: off | telemetry | on`; leave it off and behavior is
byte-for-byte unchanged.

### 🔋 Context autonomy — the 8-hour walk-away *(v0.2.1)*
Long runs used to rot once the context window filled. Now — once the hook chain is installed via
`kata_install.py --install-hooks` — the conductor watches its own **context gauge** and hands off to
itself at 70% full: it writes a durable `HANDOFF.md` and commits it **before** any reset, then a hook
re-anchors the fresh context and picks up at the next task boundary — **no work lost**. On Claude it
reads the gauge from a statusline **bridge** that never clobbers your own statusline; where there's no
gauge (headless `-p` runs, which we **verified never update the statusline**), it falls back to a fixed
rotation cadence that gives the same guarantee. (The live host-fired-compaction leg, R6, remains a
named-open proof — see Docs / status.)

A single **preflight approval** collects everything an unattended run needs up front — installs,
permissions, the model-cost gate, the recovery checks — so it never stalls waiting on you. And a
walk-away run that's missing every recovery path is **blocked before it starts**, not found dead six
hours in. A side benefit showed up in a same-protocol A/B: **−23% tokens, −44% tool calls, −29%
wall-clock at identical results** *(n=1, directional, not pinned to any single change — full caveats
in the committed LIVE-PROOF)*.

### 🧠 The learning loop — Hermes-informed, human-gated
KataHarness gets better across runs — but it never quietly rewrites itself. The cross-run learning
design borrows the useful ideas from **Hermes** (a learning-loop agent surfaced by a formal research
bake-off) while keeping our own gates, which Hermes doesn't have.

In practice: a committed **telemetry ledger** records instrumented runs' results, costs, and failure
types (row commits are human-gated, so a run can honestly ship without one), and tuning works from
logged evidence rather than hunches — the first τ calibration is itself gated on ≥3 instrumented
runs and deliberately hasn't fired yet. **Recall** surfaces past lessons (read-only) when a new run
starts — the always-on read-back path, live today. Lessons already flow back into the shipped skills
through the normal gated build loop (a ledger-era finding has changed scorer code). And `kata-improve`
can distil lessons into candidate skills that join the toolkit only through a **two-stage human
approval — granted *before* any run uses them**; that promotion gate is built and validator-enforced,
and honestly: no candidate has yet made the trip. The loop learns; nothing self-modifies silently,
and nothing it learns runs without a gate.

### 🏁 Built-in benchmarking
Quality you can *measure*, not just assert. A two-axis scoring engine ranks candidate builds on real
**fail-to-pass / pass-to-pass** test evidence (weighted by the same mutation check above) and prints an
**honest scorecard** — it tells a real all-pass from a hollow one, and gives **no credit for tests that
never ran**. *(v0.1 scores single-arm and repeat runs; the multi-arm bake-off — run N approaches at
once and promote the winner — is next. Honest maturity: the scoring machinery is live-proven on a
**synthetic** control only — it has not yet scored a real operator-supplied control repo, so treat
results to date as machinery proof, not real-repo benchmarks.)*

### 🔁 Crash-proof resume
A crash, a closed terminal, or a mid-build auto-compaction no longer costs you the run. KataHarness
keeps a **durable, git-committed progress trail** and rebuilds the exact spot it left off:

- **Durable board.** The live work-board is snapshotted to its own git ref (`refs/kata/trail`) with
  plain git plumbing — it never touches your working tree, never pushes, and can't corrupt anything.
- **Checkpoint before compaction.** A pre-compaction hook saves the board *before* the window is
  squeezed. *(We're still live-verifying that Claude's hook fires in time — but your progress is
  already durable at every checkpoint regardless.)*
- **Task-level restore.** On `/kata-resume`, it reads the git history to see which tasks actually
  finished and re-runs only the rest — no double work, no dropped work, no manual cleanup.

### 📊 Live run dashboard + web viewer
Watch a run without interrupting it: a **rich terminal dashboard** (`tools/kata_dash.py` — per-worker
heartbeat bars, wave/gate ribbon) and a **localhost-only web viewer** (`tools/kata_web.py`) render the
live board read-only from the same durable artifacts the run already writes. Point either at a running
target from a side terminal; they never write, never gate, and double as the status surface on hosts
with no statusline. *(Shipped in the early sprint milestones; see `adapters/claude/README.md` for the
side-terminal recipe.)*

### 🎛️ Frontmatter as the contract — and no model IDs, ever
Every skill carries machine-read policy in its frontmatter: a **version** (format-enforced), a
**cost-weight** (feeds run-cost previews), its **allowed tools** (least-privilege), source credit, and
tags — and the catalog below is generated straight from it, so the docs can't drift from the code. One
thing is deliberately **missing**: any hard-coded model name. Model choice is **relative to your
session's model** — the hard work runs on your model, cheaper work a rung down, with an optional
approved premium rung above (event-scoped and budgeted; steered by run evidence once the v0.3.0
adaptive layer is on). So a renamed, gated, or unavailable model never breaks the loop.

### 🐞 Debug Mode — a bug-hunting pipeline
Point it at a broken or unfamiliar codebase and it works like an engineer, not a guesser: it builds a
**model of the code**, hunts for **where behavior drifts from intent**, writes a **suite that pins the
current behavior**, **diagnoses** the root cause (light or full depth), and hands back a **debrief**
with a confidence level and an optional offer to fix. *(Built and gated on `kata/module/debug`; proven
on seeded fixtures. Start one with `/kata-onboard`, or just say "debug my repo" at `/kata-start`.)*

### ☁️ Specialized Infrastructure-as-Code agents
Dedicated specialists for **Terraform** and **CloudFormation** that switch on automatically when a task
touches infrastructure. They share a **safety contract** (`protocol/iac-safety.md`): plan-only (never
apply), a **Snyk IaC** scan gate, an explicit approval step, and no destructive targeting. Authoring,
review, and planning are live; *apply* is deliberately still gated off — safety before convenience.

### 🎚️ Modes, tiers & relative model routing
Three **modes** — **Essential, Standard, Advanced** — dial how much breadth and depth a run gets. Four
skill families (`kata-grill`, `kata-plan`, `kata-review`, `kata-diagnose`) share one rubric with a
depth control. And model routing is **relative**, as above — your model for the hard parts, a rung down
for the cheap parts — so a gated or renamed model never breaks the loop, and nothing is hard-coded.

### 🌐 Platform compatibility
One shared core, delivered per platform at three honest levels. **Claude Code** is the proven,
dogfooded home — KataHarness builds itself on it (hooks, statusline bridge, slash-commands). **Codex
CLI and Kiro** are installer-supported (`--platform codex|kiro`), with the multi-model chain
live-proven on a real Codex install. **Gemini CLI, GitHub Copilot, and Cursor** ship
**recommended-config guides** (`docs/platforms/`) that map each host onto the harness contract — the
fixed-rotation fallback is built exactly for hosts with no gauge. A platform earns "supported" by live
proof, not by a claim here.

### 🔧 Adapt without forking upstream
Customize any skill via a local **overlay** or a promoted **fork** — your changes survive every update; the
upstream base stays pristine and is never edited or lost.

### 🗂️ Discoverable slash-commands *(Claude)*
`/kata` prints the index; `/kata-start`, `/kata-onboard`, `/kata-resume`, `/kata-status`, and `/kata-validate`
route straight to the right skill — no logic to drift, always in sync with the toolkit.

### 📚 48 versioned skills
Across six families — `plan` · `coordinate` · `execute` · `evaluate` · `handoff` · `meta` — plus the
`initiation` / `closeout` modules. Every skill carries a semver in its frontmatter; the generated catalog below
is the machine source of truth for what exists and at what version.

<details>
<summary><b>Full skill catalog</b> — name · version · cost · category · status · source · use (auto-generated from frontmatter; the versioning source of truth)</summary>

<!-- SKILL-INDEX:START -->
| Skill | Ver | Cost | Category | Status | Source | Use |
|---|---|---|---|---|---|---|
| `kata-comprehend` | 0.1.0 | 3 | plan | beta | new (KataHarness original, Debug Mode P1 — function-model oracle, DESIGN LD2/LD7) | — |
| `kata-context` | 0.1.0 | 1 | plan | beta | adapted-from mattpocock/skills {ubiquitous-language, grill-with-docs CONTEXT-FORMAT} | Build/maintain CONTEXT.md shared/ubiquitous language |
| `kata-design-doc` | 0.1.0 | 2 | plan | beta | adapted-from mattpocock/skills {to-prd} + superpowers brainstorming + GSD spec-phase | Synthesize the frozen design doc / spec |
| `kata-graph` | 0.1.0 | 3 | plan | beta | adapted-from aider repo-map (MIT — tree-sitter tag-queries + personalized PageRank + token budget) + Graphify (safishamsi/graphify, MIT — AST graph + MCP oracle get_neighbors/shortest_path/get_pr_impact) | Token-budgeted structural map of an existing repo (version-up ingestion); builds kata.graph.json |
| `kata-grill-advanced` | 0.3.0 | 5 | plan | beta | adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model | — |
| `kata-grill-essential` | 0.3.0 | 3 | plan | beta | adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model | — |
| `kata-grill-standard` | 0.3.0 | 4 | plan | beta | adapted-from mattpocock/skills {grill-with-docs, grill-me, ubiquitous-language} + GSD discuss-phase/spec-phase interaction model | — |
| `kata-plan-advanced` | 0.1.4 | 4 | plan | beta | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-plan-essential` | 0.1.4 | 2 | plan | beta | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-plan-standard` | 0.1.4 | 3 | plan | beta | adapted-from mattpocock/skills {to-issues vertical-slicing} + GSD plan-phase + BMAD {trade-offs-over-verdicts} + CPP plan format | — |
| `kata-research` | 0.1.0 | 3 | plan | beta | new (KataHarness original, loop-cognition RS-GB1/2/3, D62) — fresh-context no-write evaluator pattern (L4/L5) applied to in-loop research; escalation-routed like kata-orchestrate's no-re-plan escape valve (D52) | Research a must-deliver gap with no in-plan solution; ground every claim; return findings for the grounding gate, never re-plan |
| `kata-board` | 0.1.0 | 2 | coordinate | beta | adapted-from Claude Agent Teams protocol (agnostic file reimplementation); CryptoPortfolioPlanner LESSONS-LEARNED L3 | Append-only mailbox/message board for lateral peer comms |
| `kata-bootstrap` | 0.5.1 | 2 | coordinate | beta | adapted-from GSD discuss-phase Q&A model + docs/MODES-DESIGN.md D24c composition ladder (KataHarness design) | Compose a run (run-shape + ladder), preview cost, write kata.config, launch |
| `kata-initiate` | 0.6.0 | 3 | coordinate | beta | new (KataHarness original, Phase 1 Kata Loop — D88/D91); composes kata-readiness, kata-grill, kata-bootstrap, kata-context | — |
| `kata-loop` | 0.1.0 | 2 | coordinate | beta | new (KataHarness original — Phase 3 Kata Loop conductor, D87/DESIGN §1) | — |
| `kata-onboard` | 0.2.0 | 3 | coordinate | beta | new (KataHarness original, Debug-Mode P3 / LD13 — DESIGN R6/LD13); a NEW composition of the BUILT install-portability surfaces (tools/kata_settings.py, tools/project_find.py, tools/kata_install.py, tools/intent_scaffold.py) + the initiate/bootstrap/closeout/loop spine skills. "convert-to-loop" and the ".planning/ scaffold" are NEW here (see "What is NEW", below), not a reused convert flow. | — |
| `kata-orchestrate` | 0.12.1 | 5 | coordinate | beta | adapted-from cpp-orchestrator (CryptoPortfolioPlanner harness) + Anthropic effective-harnesses-for-long-running-agents + managed-agents | Plan-guardian lead: assign, partition files, gate, no-drift |
| `kata-preflight` | 0.3.0 | 2 | coordinate | beta | new (KataHarness original, PRE-FLIGHT spine phase D29/N2); drives tools/kata_preflight.py (N1 engine); argv-builder pattern from the _COMMAND_BUILDERS registry in tools/kata_dispatch.py; injectable-runner from _subprocess_runner in tools/kata_dispatch.py | — |
| `kata-readiness` | 0.2.2 | 1 | coordinate | beta | new (KataHarness original); pattern echoes environment "doctor" checks (e.g. brew/flutter doctor) — abstract, no external code adapted | Pre-run harness+target readiness check (bootstrap-invoked or standalone doctor) |
| `kata-sprint` | 0.1.0 | 2 | coordinate | beta | new (KataHarness original — sprint-cadence D80; the thin boundary coordinator, GB4-C) | Own the sprint boundary (G1–G4 change-control); incremental delivery only |
| `kata-worktree` | 0.1.0 | 1 | coordinate | beta | adapted-from CryptoPortfolioPlanner worktree proof (LESSONS-LEARNED L2/L3) | Per-owner git-worktree isolation for concurrent code |
| `kata-characterize` | 0.1.0 | 3 | execute | beta | new (KataHarness original, Debug Mode P2b — characterization-suite generation, DESIGN LD6+§5) | — |
| `kata-deviate` | 0.1.0 | 4 | execute | beta | new (KataHarness original, Debug Mode P2a — deviation-discovery pipeline, DESIGN LD4–LD5) | — |
| `kata-diagnose-full` | 0.1.0 | 3 | execute | beta | adapted-from mattpocock/skills engineering/diagnose | — |
| `kata-diagnose-light` | 0.1.0 | 2 | execute | beta | adapted-from mattpocock/skills engineering/diagnose | — |
| `kata-iac-cloudformation` | 0.2.0 | 3 | execute | beta | new (KataHarness original — IaC-safety specialist N3, DESIGN §2; shared safety contract protocol/iac-safety.md; Snyk IaC scanner wiring IAC-4) | — |
| `kata-iac-terraform` | 0.2.0 | 3 | execute | beta | new (KataHarness original — IaC-safety specialist N3, DESIGN §2; shared safety contract protocol/iac-safety.md; Snyk IaC scanner wiring IAC-4) | — |
| `kata-lang-profile` | 0.1.2 | 2 | execute | beta | new (KataHarness original — Debug Mode LD10 in-mode language prompt-profiles, DESIGN §3 LD10 / PLAN-p3 Slice D). Selection + overlay mechanism mirrors the IaC specialist-injection precedent (skills/coordinate/kata-orchestrate "IaC activation" block + iac_detect.classify_task); STYLE templates are the sibling specialists kata-iac-terraform / kata-iac-cloudformation. | — |
| `kata-tdd` | 0.4.0 | 3 | execute | beta | adapted-from mattpocock/skills engineering/tdd | Red-green-refactor on a vertical slice |
| `kata-benchmark-report` | 0.1.0 | 1 | evaluate | beta | new (KataHarness original — kata-loop-benchmark report; mirrors the kata-report/kata-debrief two-tier {{TOKEN}} render contract; engine tools/benchmark.py) | — |
| `kata-debrief` | 0.1.0 | 1 | evaluate | beta | new (KataHarness original, Debug Mode P3 — LD12 closeout confidence report + LD3 recommendations / offered version-up; mirrors the kata-report two-tier + {{TOKEN}} render contract) | — |
| `kata-evaluate` | 0.3.1 | 2 | evaluate | beta | adapted-from cpp-evaluation (CryptoPortfolioPlanner) + Anthropic fresh-context evaluator pattern | Fresh-context, no-write, default-FAIL PASS/NEEDS_WORK |
| `kata-inline-eval` | 0.1.0 | 1 | evaluate | beta | — | — |
| `kata-report` | 0.1.2 | 1 | evaluate | beta | new (KataHarness original — the D32 report, minimal v1; sprint-cadence D85/D2) | One-page report of a gated unit of work (reports the gate, never gates) |
| `kata-review-advanced` | 0.1.2 | 3 | evaluate | beta | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-review-essential` | 0.1.2 | 1 | evaluate | beta | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-review-standard` | 0.1.2 | 2 | evaluate | beta | adapted-from CryptoPortfolioPlanner cpp-adversarial-validation (primary) + mattpocock/skills review (its Standards axis lives in kata-evaluate) | — |
| `kata-slop-check` | 0.1.0 | 2 | evaluate | beta | General heuristics original to KataHarness; adopted-check concepts from ai-slop-detector by flamehaven01 (Flamehaven Labs), https://github.com/flamehaven01/ai-slop-detector, MIT License (Copyright (c) 2026 Flamehaven Labs) — concepts re-implemented as in-context heuristics, no source code copied. | — |
| `kata-validate` | 0.1.0 | 3 | evaluate | beta | new (KataHarness original — validation mini-loop). Adapted patterns: Guardrails-AI on_fail propose-vs-apply seam; OASIS SARIF severity taxonomy (error/warning/note); Reflexion bounded self-critique loop. | — |
| `kata-closeout` | 0.1.0 | 2 | handoff | beta | new (KataHarness original — Phase 2 Kata Loop back-half, D89/DESIGN §3) | — |
| `kata-defer` | 0.1.0 | 1 | handoff | beta | new (KataHarness original, D42/D43 GB9) — the structural complement to the no-drift spine; assumption-log role added by D71 (Priming-and-Grill autonomous floor) | Park off-plan items + log grill-skip assumptions at the boundary, never drift the frozen plan |
| `kata-handoff` | 0.2.0 | 1 | handoff | beta | adapted-from mattpocock/skills {handoff} + Anthropic reset-with-handoff / compaction guidance | Two-way durable handoff (session/agent/tool) |
| `kata-orient` | 0.4.0 | 2 | handoff | beta | new (KataHarness original, loop-cognition AO-GB1/2/3 + D76) — receiving half of the two-way handoff (spine #5); three-tier assembly echoes Hermes prompt_builder (stable/context/volatile); nested-AGENTS.md rollup standard | Assemble a subagent's launch orientation: three-tier, task-type-tailored, derived pointers+callouts, routed questions — the read half of handoff |
| `kata-selfhandoff` | 0.2.1 | 1 | handoff | beta | adapted-from Anthropic compaction guidance + mattpocock caveman compression | Configurable context-threshold self-handoff (delegates artifact to kata-handoff) |
| `kata-understand` | 0.1.0 | 2 | handoff | beta | new (KataHarness original, Phase 2 GL-R2c / DESIGN §3 / PLAN-phase2 Task C1) — comprehension-map half of the closeout back-half; backed by the F2 graph runtime (tools/graph_gen.py → kata.graph.json) | — |
| `kata-improve` | 0.3.0 | 1 | meta | beta | adapted-from the Improvement Kata (Toyota Kata) + mattpocock/skills engineering/improve-codebase-architecture | Fold cross-run lessons back into the skills/ tree; calls kata-write-skill |
| `kata-promote` | 0.1.0 | 2 | meta | beta | new (KataHarness original, loop-cognition ML / LC-GB3/GB4/GB5, D60-D69) — two-stage gate vs Hermes' no-gate instant-universal model (RESEARCH.md bake-off: borrow the closed loop, keep our human gate) | Stage-2 human gate: promote a grounded agent-distilled candidate skill (experimental→stable + scope bump) into the toolkit; honors engram.autonomy |
| `kata-write-skill` | 0.1.0 | 1 | meta | beta | adapted-from mattpocock/skills productivity/write-a-skill | Author new skills to STANDARDS (points, not restates); kata-improve calls it |
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

**v0.3.0, beta.** The single-model Claude core is the proven path; the Codex/Kiro adapters are
install-supported with partial live proof; Gemini CLI / Copilot / Cursor ship as config guides; the live
host-fired-compaction leg of context autonomy (R6) and the adaptive-vs-static live A/B are queued, in
that order; L2 acceptance routing ships activation-OFF pending run volume; IaC *apply* is gated and not
shipped runnable. We're honest about maturity — that honesty is the product. Read next:

- [`AGENTS.md`](./AGENTS.md) — the vision, the spine, how to work in the repo (canonical).
- [`docs/SETUP.md`](./docs/SETUP.md) — install / update / overlay / factory-reset / uninstall in depth, plus the
  `curl | sh` security tradeoff and the audit-friendly git-clone path.
- [`docs/STANDARDS.md`](./docs/STANDARDS.md) — frontmatter, versioning, and naming conventions.

> **Security note.** `curl … | sh` and `irm … | iex` execute bytes as they stream — there's nothing to verify
> until after it runs. Pin a known ref with `KATA_REF`, or download-then-run to inspect first (see
> [`docs/SETUP.md`](./docs/SETUP.md)). On Windows without Developer Mode, the installer falls back to copy-mode
> (works fine; re-run `update` after each change to refresh copied skills).

Built on Anthropic's long-running-agent harness guidance and the best of
[mattpocock/skills](https://github.com/mattpocock/skills), GSD, BMAD, and DDD's ubiquitous language — plus
scheduler principles from DeepSeek's DSpark paper and learning-loop mechanisms surveyed from the Hermes
agent (both adopted with our gates kept in place) — attributed per skill in the `source` column and per
design doc in `.planning/specs/`. We stand on shoulders.
