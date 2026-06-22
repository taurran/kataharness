---
date: 2026-06-18
spec: loop-cognition
status: FROZEN — passed convergence + freeze-gate audit (HOLD→SHIP, D15); changes are deliberate re-freezes
source-ledger: ./GRILL-LEDGER.md (LC-GB1–9 + RS-GB1–3 + AO-GB1–3); research ./RESEARCH.md (Hermes bake-off)
tags: [design, frozen, loop-cognition, research-subagent, agent-orientation, managed-learning, engram]
---

# loop-cognition — RS + AO + ML — FROZEN DESIGN

The single contract execution serves. Compiled from the loop-cognition grill ledger (converged + freeze-gate
audited, fresh-context Opus HOLD→SHIP). No new decisions here — every LOCKED decision traces to a resolved
branch. Promoted to **D60–D69**. **Build after D16 — except β (the LEARN-only feed pipeline), which builds ∥ D16.**

## 1. Requirements satisfied
- **R1 (RS)** Deliver a feature with no in-plan solution by researching *mid-loop* — without drifting the
  frozen plan (escalation-routed, grounding-gated, deliberate re-plan only).
- **R2 (AO)** Load the *right* context when a subagent launches — thorough but prime-frame-budgeted; the
  receiving half of the handoff.
- **R3 (modularity)** Module-embedded context that rolls up (root invariants + nearest module) with lateral
  adjacency pointers to collaborating units — validated vs the 2026 nested-`AGENTS.md` standard (vertical =
  standard; lateral = our `kata-graph`-derived contribution).
- **R4 (ML)** Learn across runs (skills + a second-brain fingerprint) under a **human gate**, conservatively —
  Hermes' closed loop, our default-FAIL + promotion gate.
- **R5 (clean-room)** Everything emits through the agnostic engram CONSULT/LEARN contract so PokeVault *and*
  work loop consume identically (D30); zero IP coupling.

## 2. Where it lives (components / insertion points)
| Path | Change | Responsibility |
|---|---|---|
| `skills/plan/kata-research/SKILL.md` | **create** | in-loop research subagent; fresh-context **no-write**; returns `{claim, source, confidence, grounds-to-plan?}`. `agnostic:true`, `cost-weight:3`, `allowed-tools:[Read,Grep,Glob,WebFetch,WebSearch]` |
| `skills/handoff/kata-orient/SKILL.md` | **create** | assemble launch orientation (read-side mirror of `kata-handoff`); `agnostic:true`, `cost-weight:2`, `allowed-tools:[Read,Grep,Glob]` (no Write) |
| `skills/meta/kata-promote/SKILL.md` | **create** (post-D16) | end-of-session human promotion gate for candidate skills; `agnostic:true`, `cost-weight:2`, `allowed-tools:[Read,Grep,Glob,Edit,Write,AskUserQuestion]` |
| `protocol/orientation.md` | **create** | the orientation contract: three tiers + rollup + adjacency-pointer rules |
| `protocol/engram.md` | modify | add **skill-promotion seam row**; add a **wiki-synthesis output-schema section** (Karpathy LLM-Wiki pattern, `produced-by` marker); `engram.autonomy` reference |
| `protocol/handoff.md` | modify | the **unified loop map** (every agent × handoff edge × owning skill); boundary/orientation pairing |
| `protocol/config.md` | modify | add `engram.autonomy` (default `always-human`) + `agentSkills.dir` (first-run-configured) |
| `protocol/state.md` | modify | candidate/promotion lifecycle fields (sandboxed→promoted) |
| `skills/evaluate/kata-evaluate/SKILL.md` + `skills/evaluate/kata-review/RUBRIC.md` | modify | **injected-knowledge grounding mode** (grades RS findings + ML candidates for drift/grounding); structural invariant, D33 |
| `skills/handoff/kata-selfhandoff/SKILL.md` | modify | protected head+tail + tool-pairing guardrail + **never-summarized `{plan,goals,decisions,escalations}` block** |
| `skills/coordinate/kata-orchestrate/SKILL.md` | modify | RS-dispatch + AO-assembly **hooks only** (stays single config-driven dispatcher, D24d) |
| `skills/meta/kata-improve/SKILL.md` | modify | host the **β LEARN feed** sub-mode (emit-only; runs `kata-handoff` §7 redaction before any write) |
| `skills/plan/kata-graph/SKILL.md` | modify | emit adjacency pointers for AO (reuse `kata.graph.json` edges) |
| `tools/validate_skills.py` + tests | modify | `REQUIRED_PROTOCOL += orientation.md`; frontmatter for the 3 new skills |
| `README.md` · `.planning/SKILL-COST-RATINGS.md` · `docs/TAXONOMY.md` | modify | register kata-research/kata-orient/kata-promote |
| `.planning/DECISIONS.md` · `STATE.md` · `ROADMAP.md` | modify | promote LC/RS/AO → D60–D69; status |

**Held at version 0.1.0** (pre-release policy A). **`loop-cognition` is a SPEC name, NOT a category** — skills
are category-split by loop phase (research→plan, orient→handoff, promote→meta); the engram/second-brain
extensions are `cognition/`'s first tenant (MF2).

## 3. LOCKED decisions (each traces to a branch; tunables marked `[TUNABLE]`)

**L1 (LC-GB1/GB8) — one umbrella spec, three sub-features, spine-compatible.** RS + AO + ML share the
grounding gate + `kata-graph` substrate. No-drift (D1) holds within a run; new knowledge influences the build
*only* after the grounding gate; learning *persists* only through a human gate. *Rejected:* split AO out
(loses the shared substrate framing).

**L2 (LC-GB2) — ONE grounding gate, two callers.** An "injected-knowledge" assessment mode of
`kata-evaluate`/`kata-review` grades both RS findings and ML candidate skills for grounding + drift +
adversarial soundness. **Structural invariant (D33) — never tiered, never bypassed, even at full autonomy.**

**L3 (RS-GB1/GB2/GB3) — `kata-research` is escalation-routed, fresh-context, no-write.** Worker hits a
must-deliver feature with no in-plan solution → emits the **D52 escalation payload** → orchestrator dispatches
`kata-research` (fresh context, no Write) → findings → L2 grounding gate → orchestrator folds *grounded*
findings via a **deliberate re-plan baked as a superseding decision** (audited), or rejects (logged). Research
that can't ground → escalate to the human. `category: plan` (control-flow: orchestrator-owned, feeds re-plan,
kin to `kata-grill`/`kata-context`). *Rejected:* worker-direct research (silent drift, spine #1 violation).

**L4 (AO-GB1/GB2/GB3) — `kata-orient` assembles launch orientation, orchestrator-owned, prime-frame-budgeted.**
Three tiers **stable** (spine/identity/tools) → **context** (frozen-plan slice + module-context rollup +
adjacency pointers) → **volatile** (task + current state) (Hermes `prompt_builder` pattern). Vertical rollup =
**root invariants + nearest module `AGENTS.md`/`CLAUDE.md`** (2026 nearest-along-path standard); lateral =
**`kata-graph`-derived adjacency *pointers*, lazy-loaded** (never inlined — rot-proof, token-safe); whole
orientation **capped to the prime frame** (sprint-cadence SC-GB7). Orchestrate gains **hooks only** (D24d
preserved). Contract → `protocol/orientation.md`. *Rejected:* fold logic into `kata-orchestrate` (bloats the
weight-5 dispatcher).

**L5 (LC-GB3/GB5/GB7) — two-stage skill lifecycle, matched-but-marked, vault-hosted.** Stage 1: agent distils
a **candidate** (`status:experimental`, `scope:agent`, **not** loaded universally) → L2 grounding gate
(automated, in-loop). Stage 2: **end-of-session human promotion gate** (`kata-promote`) → `experimental→stable`
+ `scope` bump. Taxonomy = same `kata-<verb>`/category + frontmatter v2 **plus discriminators** (`provenance:
agent-distilled`, `scope: agent|coding-agent|universal`, tag `kata/origin/agent`) + a ≤60-char `summary` field.
Home = a toolkit agent-skills dir, **install-seeded**, **first-run location-configured** (`agentSkills.dir`),
`toolkit/skills/candidates/` → promote into `toolkit/skills/<category>/` (`kata-promote` must preserve
`name==dir`, D27). *Rejected:* Hermes' no-gate instant-universal model (uncontrolled positive feedback — wrong
for a one-shot harness).

**L6 (LC-GB4) — progressive promotion autonomy is a maturity ∧ config AND-gate; grounding never bypassed.**
`engram.autonomy: always-human | assisted | auto-when-confident`, default **always-human** (D25-safe),
per-seam overridable; **skill-promotion is the first seam.** Autonomy fires only when `opted-in ∧
fingerprint-mature ∧ high-confidence ∧ precedented`, per-decision; novel/low-confidence/LOCKED-adjacent always
stop the human (C2/C4). **The engram replaces human *judgment*, never the *grounding gate* (D33/L2).** Reuses
the sprint-cadence `auto-continue-while-green` pattern + engram C2/C4/C5/C6.

**L7 (LC-GB6 + RESEARCH §5/§7) — second-brain LEARN feed; one wiki-synthesis output contract; the feed is an
engram PREREQUISITE.** The loop mines decision artifacts (DECISIONS/LESSONS/GRILL-LEDGERs/REVIEWs) into
**Karpathy-LLM-Wiki-pattern synthesis pages** (raw↔synthesis split, markdown, frontmatter taxonomy,
cross-linked, `produced-by: loop|wiki|agent`), emitted via the agnostic LEARN contract, redaction-gated (C3).
Two producers (loop LEARN + the vault's own llm-wiki pipeline), **one output schema** (a section of
`protocol/engram.md`); the **loop contract LEADS** the immature vault. **Building the feed is the prerequisite
for the engram CONSULT (D9), not gated by it.** *Rejected:* a separate `protocol/wiki-synthesis.md` file (SF3 —
folded into engram.md).

**L8 (LC-GB9) — unified loop map + self-handoff structured preservation.** `protocol/handoff.md` carries the
**loop map**: every agent × handoff edge × owning skill (no ownerless edges). `kata-selfhandoff` EXTEND: Hermes'
**protected head+tail** compaction + **tool-call/response pairing guardrail** + a **never-summarized invariant
block `{frozen-plan ref, goals, open decisions, open escalations}`** — converting Hermes' "plan emerges
organically (lossy)" vulnerability into our structural guarantee. **D33 invariant.**

**L9 (LC-GB8) — Path 2 sequencing.** D16-first stays LOCKED. **Only β** (the L7 LEARN-only feed) builds **∥
D16** — observe-and-emit, **zero CONSULT**, redaction-gated; everything else (RS, AO, ML skill-distillation +
`kata-promote`, the L2 injected-knowledge mode, CONSULT, autonomy) builds **after D16**. *Rejected:* build all
pre-D16 (rework exposure, the KG-first failure).

## 4. Integrity / edge cases
- **RS can't ground a must-deliver feature:** escalate to the human — never guess, never inject ungrounded. ✔
- **Orchestrator "assembles orientation" vs D24d:** marshaling data the orchestrator already owns (task +
  file-ownership) is dispatcher-shaped; the *logic* lives in `kata-orient` + `protocol/orientation.md`. ✔
- **Adjacency pointers rotting:** derived from `kata-graph` at orient-time, never hand-maintained per file. ✔
- **β contaminating the D16 A/B:** LEARN-only ⇒ no read-back path exists ⇒ drift is structurally impossible
  (not merely procedurally avoided); arms stay byte-identical (D14/D57). ✔
- **A bad skill auto-persisting:** impossible — two-stage gate (grounding + human); autonomy never bypasses the
  grounding gate. ✔
- **Self-handoff losing the plan:** the never-summarized invariant block guarantees `{plan,goals,decisions,
  escalations}` survive every compaction. ✔

## 5. Backward-compatibility contract (checkable claims)
- **BC1** Absent config ⇒ today's behavior: `engram.autonomy` defaults `always-human`; no `agentSkills.dir`
  ⇒ no distillation persists; no β backend ⇒ no LEARN emit (the no-op path, D25/D30). *Check:* a run with no
  loop-cognition config behaves exactly as the current loop.
- **BC2** No CONSULT pre-D16: β is emit-only. *Check:* no skill reads a fingerprint into planning/execution
  during a D16 arm; grep shows no CONSULT call-site wired.
- **BC3** Grounding gate is structural: `kata-evaluate` stays default-FAIL, no Write/Edit. *Check:* validator
  reports kata-evaluate cost 2, no Write.
- **BC4** All skills `0.1.0` (policy A). *Check:* validator green; no version bumped.
- **BC5** One new protocol file only (`orientation.md`); wiki-synthesis lives in `engram.md`. *Check:*
  `protocol/wiki-synthesis.md` does not exist.

## 6. Acceptance criteria (default-FAIL, runnable)
- **A1** `cd tools && uv run pytest -q` → all pass (incl. new `orientation.md` required-terms test).
- **A2** `uv run python validate_skills.py` → `N skills checked — 0 error(s)` (N = 27: 25 + kata-research +
  kata-orient; kata-promote lands post-D16), README in sync, the new skills' frontmatter conformant
  (categories plan/handoff/meta; `kata/origin/agent` machinery documented).
- **A3** `protocol/orientation.md` documents the three tiers + rollup + adjacency rules; `protocol/handoff.md`
  carries the loop map with an owning skill per edge; `protocol/engram.md` has the skill-promotion seam row +
  the wiki-synthesis schema section; both enforced by `REQUIRED_PROTOCOL`/required-terms.
- **A4** Behavioral (fresh-context `kata-review` on the diff): (a) `kata-research` has no Write/Edit; (b) RS
  routing escalates, never worker-direct; (c) `kata-orient` is read-only and orchestrate gained hooks not
  logic; (d) `kata-selfhandoff` carries the never-summarized block; (e) β has no CONSULT call-site; (f) no
  `wiki-synthesis.md` file.
- **A5** Adversarial `kata-review` (D15) over the full diff returns SHIP.

## 7. Test seams / testability
- **Machine seam:** `tools/` validator (`REQUIRED_PROTOCOL` for orientation.md; new-skill frontmatter; README
  sync) — pytest-gated, the default-FAIL floor for the prose/schema work.
- **Contract seam:** `protocol/orientation.md` + the loop-map table + the engram wiki-synthesis schema are
  testable fixtures.
- **Prose-correctness seam:** fresh-context adversarial `kata-review` (A4/A5) — the no-write evaluator for the
  skill-body changes (RS routing, AO assembly, self-handoff preservation, β emit-only).
- Runtime (actual research dispatch, orientation assembly, fingerprint feed) is exercised when the harness runs
  for real (dogfood, the ε self-improvement arc); this DESIGN ships the contracts + schemas + prose, gated by
  schema/frontmatter conformance + adversarial review.

---
**FROZEN.** Hand to `kata-plan` for the task-level PLAN. β (L9/L7 LEARN-only feed) is the only slice that
builds ∥ D16; the rest is post-D16. Changes to this DESIGN are deliberate re-freezes, not edits-in-flight.
