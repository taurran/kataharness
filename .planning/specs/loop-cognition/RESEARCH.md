# Loop-cognition — research + bake-off (pre-grill)

> **Status: RESEARCH (2026-06-18), pre-grill.** User-requested umbrella capability: three entangled
> **loop enhancements** that make the harness acquire knowledge mid-loop and learn across runs — *without*
> letting either drift the frozen plan. The open design branches live in `GRILL-LEDGER.md` (answer those
> first; nothing here is frozen). Sequencing target: **freeze designs now, build after D16** (same logic as
> sprint-cadence GB10) — but see §7 for the one part that is an engram *prerequisite*, not a dependent.

## 1. The three features in one paragraph each

- **RS — In-loop research subagent.** A research agent invoked *during* execution (not only at plan time)
  when the coding agent / validators / evaluators hit a feature that must be delivered but has **no solution
  in the frozen plan or system prompt**. It researches and returns guidance mid-flight. Because injecting
  fresh external knowledge into a frozen plan is a **drift vector**, its output is gated: the
  validators/evaluators must explicitly assess it for **drift and grounding** before it can influence the
  build. (The research agent applies *negative pressure*; the grounding gate is the *counter-pressure*.)

- **AO — Agent Orientation + modularity.** The *receiving* half of the handoff. The agent writes a handoff;
  **Agent Orientation** is the structured skill that *loads* the right context when a subagent launches —
  thorough but governed by context-budget discipline. Driven by **modularity**: code is structured into
  modules, each with its own `AGENTS.md`/`CLAUDE.md` context file; submodules carry embedded context that
  **rolls up** (root invariants + nearest-module context); when a module collaborates with peers, the agent
  gets **pointers to load adjacent units** (derived from `kata-graph`, not hand-maintained).

- **ML — Managed learning (Hermes-borrowed, gated).** The loop distils reusable **candidate skills** during
  execution and, at session end, presents them for a **human promotion gate**; promoted skills become
  long-term coding-agent skills. The same loop **feeds the second brain** — mining the run's decision
  artifacts into wiki-style synthesis that grows the user's cognitive fingerprint over time, behind the
  agnostic engram contract (so PokeVault *and* MindBridge consume it identically).

These share two substrates and that is why they are one umbrella: **the grounding gate** (RS-injected
knowledge and ML-distilled skills pass the *same* check) and **`kata-graph`** (AO adjacency pointers and ML
footprint reasoning read the *same* dependency edges).

## 2. Hermes Agent — deep research (the borrow target)

Nous Research's **Hermes Agent** ("the agent that grows with you") is the closest shipping system to this
feature set, and is strikingly adjacent to KataHarness (it ships an `AGENTS.md`, a `skills/` +
`optional-skills/` split, an `acp_adapter`, `plans/`, and a `trajectory_compressor.py`). Its headline is a
**closed learning loop**. Concrete mechanisms (read from the repo + docs, not the marketing):

| Mechanism | Hermes implementation | Source |
|---|---|---|
| Autonomous skill creation | Distilled after a task into `~/.hermes/skills/`, tagged `created_by:"agent"` | repo `AGENTS.md`, `agent/curator.py` |
| Skill scope | **User-universal within a profile** — instantly available to all future sessions | repo `AGENTS.md` |
| Promotion gate | **None.** Agent skills are immediately persistent + usable | repo `AGENTS.md` |
| Lifecycle | Curator touches only `created_by:agent`: `active → stale → archived (.archive/, never deleted)`; `pin` exempts; LLM review pass gates **deletion**, not activation | `agent/curator.py` |
| Self-improvement | Mid-session `skill_manage(edit/patch)`; usage telemetry `.usage.json` (`use_count`, `patch_count`, `last_activity_at`) | repo `AGENTS.md` |
| Three-layer memory | `prompt_builder.py` assembles ordered tiers **stable (identity/tools) → context (context files) → volatile (memory/profile/timestamp)**; procedural/episodic/semantic over **SQLite + FTS5** (`hermes_state.py`, `memory_manager.py`) | docs/architecture |
| Cross-session recall | FTS5 session search + LLM summarization | docs |
| User modeling | **Honcho dialectic user modeling** — a deepening model of "who you are" across sessions | docs |
| Trajectory → training | ShareGPT-format trajectories from sessions → RL data (Atropos) | docs |
| Taxonomy | Category dirs identical across `skills/`+`optional-skills/`; frontmatter `name, description, version, author, license, platforms, metadata.hermes.tags, category, related_skills, config`; **description ≤60 chars, one sentence, no marketing words** | repo `AGENTS.md` |

**Architectural bet:** Hermes optimizes **autonomy/throughput** — distil freely, go universal instantly,
prune-by-deletion later. The curator is a *garbage collector*, not a *gate*. There is **no default-FAIL
grounding gate on what gets learned** — a bad skill can be distilled, reinforced, and silently reused.

## 3. Bake-off — Hermes (autonomous) vs. ours (candidate → gate → promote)

| Criterion | Hermes (autonomous) | Ours (gated/tiered) | Winner for a **one-shot coding harness** |
|---|---|---|---|
| New-knowledge safety | bad skill → instantly universal → silently reused | grounding-gated candidate, sandboxed till approved | **Ours** (default-FAIL / no-drift) |
| Throughput / autonomy | maximal | costs an end-of-session human action | Hermes (wrong tradeoff here) |
| Auditability | `.usage.json` + archive | versioned, taxonomy-slotted, supersede-not-rewrite | **Ours** |
| Personal-assistant fit | excellent | overkill | Hermes |
| **Coding-harness fit** | **dangerous** (uncontrolled positive feedback) | **native** | **Ours** |

**Verdict (drives both KataHarness and the sister MindBridge Loop): borrow Hermes' *mechanisms*, keep our
*gates*.**
- **Borrow:** autonomous distillation; `.usage.json`-style telemetry; mid-flight patch; `stale → archive
  (never delete)` curation; the ≤60-char description discipline.
- **Keep/add:** the candidate tier (agent-scoped, sandboxed, grounding-gated); the **end-of-session human
  promotion gate**; taxonomy + versioning; supersede-not-rewrite.

This is the harness's differentiator stated precisely: **Hermes' learning loop, gated by default-FAIL +
human promotion.** It reuses machinery we already own — `kata-evaluate` (D22), `kata-review` (D15), the
`status: experimental → beta → stable` lifecycle, and the engram C1–C6 invariants.

## 4. Module / Agent-Orientation — validated against the 2026 standard

The nested-context convention is mainstream: **OpenAI's monorepo runs 88 `AGENTS.md` files**; GitLab Duo,
Codex CLI, and the `agents.md` spec all do **nearest-along-the-path resolution** — when touching a file, walk
`root → … → that directory`, closest file wins, token-budget-optimized.

- **Vertical rollup (root invariants + module context) — MATCHES the standard.** Adopt as-is.
- **"Higher tier → more context" — needs the token caveat.** The standard loads *only* root + nearest, not
  everything cumulatively, to protect the window. Agent Orientation must load **nearest-module context + root
  invariants + *pointers* to adjacent units**, pulling adjacent content lazily — dovetails with the
  sprint-cadence **prime-frame** budget (GB7).
- **Lateral "adjacent-module pointers" — NOT in the standard; our novel contribution.** AGENTS.md nesting is
  a pure **tree** (ancestral). Cross-module links make it a **graph** — and we already built the substrate:
  **`kata-graph` (D54/D55) emits the dependency edges.** Adjacency pointers are *derived from kata-graph*,
  never hand-maintained per module file (which would rot).

**Validation result:** vertical = industry-standard (safe to adopt); lateral = novel-but-already-resourced.

Sources: NousResearch/hermes-agent (repo + docs.nousresearch.com) · turingpost.com/p/hermes ·
augmentcode.com "How to Build AGENTS.md (2026)" · codegateway.dev "AGENTS.md playbook 2026" ·
agentsmd/agents.md#53 (nearest-wins) · mcsee Medium "Nested AGENTS.md files".

## 5. How the loop *feeds* the second brain

Hermes feeds memory via Honcho (opaque user-model service) + FTS5 + auto-nudges + ShareGPT trajectories.
**Our equivalent is artifact-grounded — better for the spine.** The loop already emits the richest learning
signal as durable, git-versioned, Obsidian-native artifacts:

- **GRILL-LEDGERs are the gold.** Each branch records `{options considered → chosen answer → rationale →
  provenance}` — a structured record of *how the user decides* (control-first, supersede-not-rewrite,
  orthogonal-axis-over-new-shape, "when in doubt, stop"). That is the cognitive fingerprint in raw form.
- **DECISIONS / LESSONS-LEARNED / REVIEW** — decision patterns, surprises, adversarial verdicts.

**The feed** (a new LEARN step in IMPROVE + at each handoff/boundary): mine decision patterns → crystallize
into **wiki-style synthesis pages** → emit through the agnostic engram **LEARN** contract, redaction-gated
(C3), audited (C6).

- **Two producers, one output contract (user directive).** The llm-wiki's own synthesis pipeline and the
  loop's LEARN/synthesis are *deliberately different processes* that must conform to **one shared
  output schema** — same wiki-page shape, same frontmatter taxonomy, growing over time. (LC-GB6.)
- **Differentiator vs Hermes:** our fingerprint is mined from **auditable, versioned artifacts**, not opaque
  chat state — so it is supersede-able and no-drift-compatible.

## 6. MindBridge / clean-room alignment

MindBridge Loop (sister project) is a first-class consumer. Therefore **everything above emits through the
agnostic CONSULT/LEARN contract** (`protocol/engram.md`), never hard-coding PokeVault. PokeVault is one
backend; MindBridge binds externally and answers the same contract → **zero IP coupling** (D30 clean-room).
These features become the first real consumers of that documented extension point.

## 7. Spine compatibility + the one sequencing nuance

- **RS** respects no-drift because injected knowledge is **gated, not auto-applied** — the grounding gate is
  the deliberate-re-plan event (escalation), not silent improvisation. (Spine #1/#2.)
- **AO** is pure context management — it changes *what context loads*, never *the plan*. (Spine #5.)
- **ML** persistence is **default-FAIL + human-gated**; the engram replaces *judgment*, never the *grounding
  gate* (a structural invariant, D33). (Spine #4/#6.)
- **Sequencing nuance:** the **LEARN/feed pipeline (§5) is a prerequisite for the engram CONSULT**, not a
  dependent of it — you cannot consult a fingerprint you never fed. So while the CONSULT-side features stay
  gated on a mature fingerprint (D9), the **feed-side data collection can begin earlier** (low drift risk,
  pure capture). This partially reorders the engram backlog and is the lever toward the user's goal:
  **build KataHarness fully → full tests → self-improve the harness on itself (version-up).**

> Open branches: `GRILL-LEDGER.md` (LC-GB1…LC-GB7). On convergence → fresh-context freeze-gate audit (RUBRIC,
> no self-certification) → freeze `DESIGN.md` → PLAN → build after D16.
