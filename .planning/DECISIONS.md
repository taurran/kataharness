# DECISIONS — KataHarness (ADR log)

Locked decisions. Format: ID · decision · why. Never silently reverse — supersede with a new ID.

- **D1 — The plan does not drift.** Orchestrator = plan-guardian (owns frozen plan, task assignment,
  file-ownership, gating); peers execute + communicate, never re-plan; unknowns escalate. *Why:* drift
  is the enemy of one-shot; evidence (Anthropic managed-agents + harness) favors centralized plan ownership.
- **D2 — One-shot = no plan churn.** Deep plan → execute → eval → targeted fix vs the same plan.
- **D3 — Agnostic via adapter pattern.** Agnostic core + thin per-tool adapters. *Why:* pure-files-only
  forfeits every tool's good parts; depending on one tool forfeits agnosticism.
- **D4 — Do NOT depend on Claude Agent Teams; mine its protocol.** Reimplement mailbox + file-locked
  task-claim + lead as agnostic files. *Why:* Teams is Claude-only/experimental; cross-tool is the goal.
  Teams remains a reference + optional Claude-adapter feature.
- **D5 — AGENTS.md is canonical; CLAUDE.md is a pointer.** *Why:* AGENTS.md is the cross-tool industry
  standard; Claude is the exception.
- **D6 — Per-skill semver in frontmatter; README index is the source of truth.** Frontmatter + naming
  are first-class. *Why:* the suite must be independently versionable and discoverable.
- **D7 — Naming: `kata-<verb>`, categorized by loop phase.** Permeates skills/files/protocol/adapters.
- **D8 — Self-handoff threshold is configurable and anti-over-conservative; task-boundary preferred;
  re-anchor on plan.** *Why:* a naive fixed % kills sessions early / degrades context (user-flagged).
- **D9 — Engram/cognitive-fingerprint = designed extension point, backlog (not v0.1).** Gated on a
  mature second brain (kiban/kagami).
- **D10 — KataHarness is its own standalone public project, not a CPP sub-package.** *Why:* independent
  release; public vs private CPP; cross-tool by nature; own license/docs. CPP consumes it at v0.1.
- **D11 — Durable artifacts are Obsidian-native (YAML frontmatter + [[wikilinks]] + tags); machine
  coordination state kept separate.**
- **D12 — Provenance required (`source:` frontmatter) when adapting external skills.** Stand on
  shoulders *and* attribute.
- **D13 — Model routing for build vs test.** Building KataHarness skills → **Opus 4.8** (best foot
  forward; the harness quality matters most). The CPP Phase-3 **test arms → Sonnet 4.6** (both arms).
  *Why:* the headline claim is "the harness lifts the cheaper workhorse model"; Opus would mask the lift.
  If the test flubs, retry later. Subagent models are pinned on spawn; the main-session model is the
  operator's `/model`.
- **D14 — A/B test design (see docs/TEST-PLAN.md).** Target = CPP Phase 3 @ tag `cpp-phase2-baseline`.
  Arm A = KataHarness loop; Arm B = our **current GSD process** (the honest baseline, not a naive agent).
  **Hold model constant (Sonnet) across arms; fresh context per arm on its own branch; same frozen
  Phase-3 design+plan to both.** Metrics: one-shot-to-green, plan-drift (target 0, esp. sleeve
  classification), interventions, gate integrity, handoff recovery, hygiene. **Validate the loop manually
  (Wizard-of-Oz) before building all skills.**
