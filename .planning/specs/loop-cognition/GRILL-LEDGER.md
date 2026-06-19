# Loop-cognition — Grill Decision Ledger

> Running ledger for the loop-cognition design grill (per `kata-grill` RUBRIC). Grounded in `RESEARCH.md`
> (Hermes bake-off, module-standard validation, second-brain feed). **Status: CONVERGING (2026-06-18).**
> LC-GB1–7 RESOLVED; LC-GB8 (sequencing/deconfliction) RESOLVED. Awaiting fresh-context freeze-gate audit
> before DESIGN freeze. Per L7/L8: options + a recommendation each, free-text always welcome. Branch
> prefixes: **RS** research subagent · **AO** agent orientation · **ML** managed learning · **LC** umbrella.

## Steering tenet (apply to every branch)
**Acquire knowledge mid-loop and learn across runs without drifting the frozen plan.** No-drift (D1) holds
within a run; new knowledge (RS-injected or ML-distilled) influences the build **only after passing the
grounding gate**. Learning *persists* only through a **human gate** (until the engram earns delegated
autonomy under an AND-gate). The grounding gate is a structural invariant (D33) — never tiered, never
bypassed, even at full autonomy.

## Locked directives (user, 2026-06-18 — fold into DESIGN at freeze)
- **Conservative-by-business-direction.** Trustworthy one-shotting is the value → err conservative on what
  the agent may learn/persist (confirms the §3 bake-off verdict).
- **Two producers, one output contract** → LC-GB6. **Taxonomy matched-but-marked** → LC-GB5. **Folder
  loop-defined / vault-hosted / install-seeded / location-configurable** → LC-GB7. **Human gate to persist** → LC-GB3.

---

## LC-GB1 — Umbrella vs. split + name **(RESOLVED — umbrella `loop-cognition`)**
One umbrella spec with three prefixed branch-sets (RS/AO/ML); they share the grounding gate + `kata-graph`
substrate. Each sub-feature freezes its own DESIGN section.
> **RESOLVED 2026-06-18 → A** (user "umbrella is good"). Name `loop-cognition` (negotiable at freeze).
> **AUDIT MF2 (2026-06-18):** `loop-cognition` is the **spec/theme name, NOT a category** — `cognition/` is a
> declared-but-empty category whose first tenant is the engram. The umbrella's skills are **category-split by
> loop phase**: `kata-research`→`plan`, `kata-orient`→`handoff`, `kata-promote`→`meta`; the engram/second-brain
> extensions land in `cognition/`. The earlier "matches the cognition category" rationale is **withdrawn.**

## LC-GB2 — One grounding gate for RS-injected AND ML-distilled knowledge **(RESOLVED — unify)**
A single gate (extension of `kata-evaluate`/`kata-review`, "injected-knowledge" mode), two callers:
research-subagent findings + distilled candidate skills. Structural invariant (D33).
> **RESOLVED 2026-06-18 → A** (user "agree").

## LC-GB3 — Promotion-gate placement **(RESOLVED — two-stage)**
Stage 1 = automated grounding gate at distillation → candidate sandboxed (`status: experimental`,
`scope: agent`, not loaded universally). Stage 2 = end-of-session **human promotion gate** →
`experimental → stable` + `scope` bump.
> **RESOLVED 2026-06-18 → A** (user "two stage… human gate decision to persist skills… controlled manner").

## LC-GB4 — Progressive promotion autonomy **(RESOLVED — maturity ∧ config AND-gate)**
Autonomy engages only when `opted-in (config ceiling) ∧ fingerprint-mature (maturity floor) ∧ high-confidence
∧ precedented`. Per-decision routing. **The engram replaces human judgment, NEVER the grounding gate (D33).**
Three tiers: **0 cold** (assessment runs as a grill; human decides every persist) · **1 assisted** (engram
pre-recommends + confidence; grounding runs; human confirms) · **2 autonomous, opt-in** (engram auto-approves
through grounding+adv-val, logs to drift ledger C6; novel / low-confidence / LOCKED-adjacent still stop the
human, C2/C4). Config `engram.autonomy: "always-human" | "assisted" | "auto-when-confident"`, default
**always-human** (D25-safe), per-seam overridable; **skill-promotion is the first seam to earn autonomy.**
Reuses GB6 `auto-continue-while-green` + invariants C2/C4/C5/C6.
> **RESOLVED 2026-06-18 → A** (user "Confirmed"). On freeze: add a **skill-promotion seam row** to
> `protocol/engram.md` (currently implicit in E6) + `engram.autonomy` to `protocol/config.md`.

## LC-GB5 — Agent-skill taxonomy: matched-but-marked **(RESOLVED — same schema + discriminators)**
Reuse `kata-<verb>`/category + STANDARDS frontmatter v2; add discriminators `provenance: agent-distilled`
(extends `source:`), `scope: agent | coding-agent | universal`, tag `kata/origin/agent`. Lifecycle rides the
existing `status` (experimental=candidate → stable=promoted). **Description rule:** keep v2 `description`
≤1024 trigger-rich (host model needs it to invoke) **AND add a ≤60-char one-sentence `summary`** for catalog
rows (adopts Hermes' machine-readable discipline as a *second* field, not a replacement).
> **RESOLVED 2026-06-18 → A** (user "Confirm. That is a good middle ground.").

## LC-GB6 — Wiki-synthesis output contract (two producers, one schema) **(RESOLVED — Karpathy-pattern, loop leads)**
- **"llm-wiki" = Karpathy's LLM Wiki pattern** (confirmed, user 2026-06-18): an LLM-maintained Obsidian KB
  separating **raw sources** from **synthesized concept/entity/synthesis pages** — markdown-only,
  human-auditable, no vector embeddings, cross-linked. PokeVault's `wiki/.../pages/{sources,entities,
  concepts,synthesis,references}` layer is an instance of it; **its synthesis side is underdeveloped and
  needs growing** (based on Karpathy's "LLM wiki" + the "onebrain/second-brain" community pattern).
- **Decision: define an agnostic wiki-synthesis output schema both producers bind to** — page shape +
  frontmatter taxonomy + a `produced-by: loop | wiki | agent` marker — as a Karpathy-pattern markdown page.
  The loop's LEARN step specializes in **decision-pattern synthesis** (how the user decides); the vault's own
  pipeline does general research/domain synthesis. **The loop's contract LEADS** — it is the reference the
  immature vault synthesis grows toward. Aligns natively with STANDARDS §5 (Obsidian frontmatter + wikilinks).
> **RESOLVED 2026-06-18 → A** (user "Yes, align, but the PokeVault llm-wiki synthesis may be underdeveloped…
> needs to be grown more"). Schema home: a new `protocol/wiki-synthesis.md` (or a section of
> `protocol/engram.md`) — pin at freeze. Targets the vault `pages/synthesis/` layer via the agnostic LEARN
> contract (PokeVault one backend; MindBridge another — D30).

## LC-GB7 — Agent-skills directory: install-seeding + first-run location config **(RESOLVED — rec A; two specifics flagged)**
KataHarness install seeds the agent-skills section under the toolkit; on first invocation `kata-bootstrap`
asks where it lives (progressive disclosure, D46) → `kata.config`; vault update handed to PokeVault later.
> **RESOLVED 2026-06-18 → A.** Two build-detail specifics (non-blocking for the path-2 parallel work, since
> skill-distillation is post-D16 — override welcome before that build): (1) **staging folder** rec
> `toolkit/skills/candidates/` → promote into `toolkit/skills/<category>/` (flavor alt `forge/`);
> (2) **promotion ceremony** rec a **new single-responsibility skill `kata-promote`** (the human gate is a
> distinct, security-flavored action) rather than folding into `kata-improve`. `kata.config` gains
> `agentSkills.dir` + a first-run prompt.

---

## LC-GB8 — Sequencing / delivery: how loop-cognition reaches the plan vs. D16 **(RESOLVED — Path 2, deconflicted)**
User goal: ingest loop-cognition to the plan, then **build KataHarness fully → full tests → self-improve the
harness on itself (version-up).** Tension: D16-first is LOCKED (GB10/ROADMAP); building loop-cognition pre-D16
is the rework-exposure that killed KG-first.
- **Path 1: hold the line — D16 first, build all loop-cognition after.** Safest; slowest to self-improvement.
- **Path 2 (CHOSEN): D16 first, but build the loop-cognition *feed pipeline* in parallel.** The
  LEARN/second-brain feed is a **prerequisite for the engram CONSULT, not a dependent** (RESEARCH §7), and is
  low-drift pure data-capture — the one piece safe to pull forward. Starts the fingerprint maturing while D16
  runs; D16's paired decision corpus is the richest harvest we'll ever get.
- **Path 3: re-sequence — build everything before D16.** Rejected — the rework exposure the 2026-06-10
  review rejected for KG-first.

> **RESOLVED 2026-06-18 → Path 2** (user "Let's go with 2. Deconflict… go deep so everything is aligned").
>
> **Scope of the parallel "feed pipeline" (IN):** a **LEARN-only, observe-and-emit** step (in IMPROVE +
> optionally at handoff/boundary) that reads the run's durable decision artifacts (DECISIONS, LESSONS,
> GRILL-LEDGERs, REVIEWs) → extracts decision patterns → emits **Karpathy-pattern synthesis pages**
> (`produced-by: loop`, LC-GB6 schema) → through the **agnostic engram LEARN contract**, **redaction-gated
> (C3)**, into the configured backend. Minimal; could be a sub-mode of `kata-improve` to avoid pre-v0.1 skill
> sprawl.
>
> **Scope (OUT — frozen design, build after D16):** RS research subagent; AO agent orientation; ML candidate
> **skill** distillation + human promotion gate + `kata-promote`; the grounding-gate "injected-knowledge"
> mode; the **CONSULT** side; progressive autonomy (GB4). The feed pipeline feeds the *second brain*
> (decision-pattern fingerprint) — it does **not** distil skills (that needs the grounding gate + human gate,
> which are post-D16).
>
> **Deconfliction matrix (Path 2 vs the locked corpus):**
> | Locked constraint | Risk | Resolution |
> |---|---|---|
> | **D16-first** (GB10/ROADMAP) | Building pre-D16 = rework exposure | Only the LEARN-only feed is pulled forward; it never touches planning/execution. Everything else stays build-after-D16. |
> | **D14/D57 — D16 arms held constant** | Altering the harness confounds the A/B | **HARD RULE: feed pipeline is OBSERVE-AND-EMIT only — zero CONSULT into either arm's planning/execution.** Runs as a post-hoc pass over durable artifacts, outside the loop's decision path. Both arms stay behaviorally identical. |
> | **Spine #1/#2 no-drift** | A learner could feed back and drift the plan | LEARN-only + no CONSULT ⇒ no read-back path exists yet ⇒ drift is structurally impossible. |
> | **D9 engram gating** | Building "engram" pre-gate | The gate is on **CONSULT** (using the fingerprint). **LEARN (building it) is the explicit prerequisite, not gated** (RESEARCH §7). |
> | **C3 redaction (engram invariant)** | Writing artifacts to a vault could leak secrets/PII | Redaction gate (same as `kata-handoff` §7) is **in the minimal scope from day one** — non-negotiable. |
> | **Versioning hold** | New-skill versioning | Any new surface enters `0.1.0/experimental`; no bump (policy A). |
> | **GB6 two-producer contract** | Loop output vs immature vault schema | Define the output contract **now**; the loop conforms and **leads**; the vault grows toward it. |
> | **D30 clean-room (MindBridge)** | Hard-coding PokeVault | Emits via the **agnostic LEARN contract**; PokeVault one backend, MindBridge another. |
> | **D16 experimenter neutrality** | Human consulting fresh fingerprint biases D16 judgments | Procedural rule: during D16 the feed runs but its output is **not consulted** for any arm decision (preserves D14 honesty). |
>
> **Build arc toward the user's endgame (records the path, not yet a frozen PLAN):**
> α. close grill → freeze-gate audit → freeze loop-cognition DESIGN → write into ROADMAP. ·
> β. (∥ D16) build the **minimal LEARN/feed pipeline** (redaction-gated, agnostic contract); it harvests
> D16's decision corpus. · γ. (post-D16 SHIP) build the rest of loop-cognition (RS, AO, ML skill-distillation
> + promotion + grounding "injected-knowledge" mode, CONSULT, autonomy) — now with a fed fingerprint to
> consult. · δ. close remaining unbuilt skills → **full tests**. · ε. **self-improvement endgame:** run the
> A4 **version-up** machinery **on KataHarness itself**, CONSULT-enabled — dogfood the harness improving the
> harness.

---

## RS — In-loop research subagent (dense; opened + RECOMMENDED 2026-06-18, confirm in one pass)
> Closes the HIGH "RS handoff undefined / spine-violating" finding. Each branch: rec only, free-text welcome.

**RS-GB1 — Invocation: escalation-routed, never worker-direct.** Worker hits a *must-deliver* feature with no
in-plan solution → emits the **structured escalation payload (D52)** → **orchestrator** dispatches RS. Research
that still can't ground it → **escalate to the human** (never guess). Keeps RS inside spine #1 (no silent
mid-loop research). *Rejected:* worker spawns RS directly (drift vector).

**RS-GB2 — Output handoff: gate → deliberate re-plan, never silent.** RS findings → **grounding gate
(LC-GB2 injected-knowledge mode)** → orchestrator folds *grounded* findings via a **deliberate re-plan**,
baked as a **superseding decision** (audited, supersede-not-rewrite). Rejected/ungrounded findings logged, not
applied. The re-plan IS the spine-#2 "re-planning is an event" door.

**RS-GB3 — Isolation: fresh-context, no-write (mirror `kata-evaluate`).** New skill **`kata-research`**
(category `plan` — it feeds re-planning): `allowed-tools` = Read/Grep/Glob/Web only, **no Edit/Write**;
returns a structured artifact `{claim, source, confidence, grounds-to-frozen-plan?}`. Fresh context per
dispatch (no contamination of the asking agent). **Category = `plan`** (confirmed 2026-06-18 — category
encodes control-flow/product: orchestrator-owned, feeds re-plan; kin to `kata-grill`/`kata-context`; reversible).

## AO — Agent orientation (dense; opened + RECOMMENDED 2026-06-18)
> Closes the HIGH "AO has no owner/contract" finding. The receiving half of handoff.

**AO-GB1 — Owner + structure: orchestrator assembles, three tiers (Hermes `prompt_builder`).**
**stable** (spine/identity/tools) → **context** (frozen-plan slice + module-context rollup + adjacency
pointers) → **volatile** (the task + current state). The orchestrator owns it (already owns task assignment +
file-ownership — D24d untouched). Orientation = the read-side mirror of `kata-handoff`'s write-side.

**AO-GB2 — Rollup + adjacency, prime-frame budgeted.** Vertical = **root invariants + nearest module
`AGENTS.md`/`CLAUDE.md`** (the 2026 nearest-along-path standard). Lateral = **`kata-graph`-derived adjacency
*pointers*, lazy-loaded**, never inlined (avoids the token blow-up; rot-proof). Whole orientation **capped to
the prime frame (GB7)**. "Deeper tier = more *specific*," not "more *total*."

**AO-GB3 — Home: `protocol/orientation.md` + thin `kata-orient` skill.** Single-responsibility, symmetric
with `kata-handoff` (handoff writes, orient reads). *Rejected:* fold into `kata-orchestrate` (bloats the
weight-5 dispatcher; AO is a first-class named feature).

## LC-GB9 — Unified loop map + self-handoff structured preservation (dense; RECOMMENDED 2026-06-18)
> Closes the MED "no single loop map" + the HIGH "self-handoff doesn't guarantee plan survival" findings.

**(a) Loop map → `protocol/handoff.md`.** One table: **every agent × every handoff edge × owning skill** —
the completeness artifact that made the RS/AO gaps visible. Every edge MUST name an owning skill (no
ownerless handoffs — the user's "fully managed and defined by skills/agents" requirement).
**(b) `kata-selfhandoff` EXTEND.** Borrow Hermes' **protected head + tail** compaction and **tool-call/
response pairing guardrail**; ADD a **never-summarized invariant block** `{frozen-plan ref, goals, open
decisions, open escalations}`. This converts Hermes' documented vulnerability (plan "emerges organically,"
risks lossy encoding) into our **guarantee** — the spine-#5 re-anchor made structural. **D33 invariant.**

## Artifact map (NEW / EXTEND / REUSE) — surgical implementation surface
> The "be SURE we implement properly" tracker. Promote to DESIGN's tie-in table at freeze.

| Class | Surface | Driver |
|---|---|---|
| **NEW skill** | `kata-research` (`plan`, fresh-context no-write) · `kata-orient` (`handoff`) · `kata-promote` (`meta`, post-D16) — all `agnostic:true`/`experimental`/`0.1.0`, frontmatter pinned MF1 | RS-GB3 / AO-GB3 / GB3 |
| **NEW protocol** | `protocol/orientation.md` (AO contract). *(wiki-synthesis schema → a SECTION of `protocol/engram.md`, not a new file — SF3.)* | AO-GB3 / GB6 |
| **EXTEND skill** | `kata-evaluate`+`kata-review` (injected-knowledge grounding mode) · `kata-selfhandoff` (structured preservation) · `kata-orchestrate` (RS-dispatch + AO-assembly hooks — stays single dispatcher, D24d) · `kata-handoff` (loop-map + orientation pairing) · `kata-improve` (β LEARN feed) · `kata-graph` (adjacency-pointer emit) | LC-GB2 / GB9 / RS+AO / GB9 / GB8-β / AO-GB2 |
| **EXTEND protocol** | `protocol/handoff.md` (loop map) · `protocol/config.md` (`engram.autonomy`, `agentSkills.dir`) · `protocol/engram.md` (skill-promotion seam row) · `protocol/state.md` (candidate/promotion lifecycle) | GB9 / GB4+GB7 / GB4 / GB3 |
| **REUSE verbatim** | escalation payload (D51/D52) for RS routing · `kata-evaluate` default-FAIL floor · blast-radius (D50/D51) · `kata-board`/`kata-worktree` · `kata-handoff` §7 redaction filter for the β LEARN write (C3, SF1). *(`kata-report` struck — MF3: β emits synthesis pages directly.)* | — |

---

## Convergence
LC-GB1–9 + RS-GB1–3 + AO-GB1–3 **CONFIRMED by user 2026-06-18** (`kata-research` `category` = **`plan`**, confirmed 2026-06-18). The adversarial pass (2026-06-18) reopened the grill on the under-specified
loop-structure/handoff layer (RS/AO) and it re-converged — **this is no-self-certification working (L8).**
Per the RUBRIC the grill does not grade its own convergence — a **fresh-context audit** (convergence +
negative-drift + complexity + loose-ends) runs before freeze. On SHIP → promote to D-numbers → freeze
`DESIGN.md` → write β into ROADMAP/PLAN → build per the α–ε arc.

### Status board (2026-06-18)
| Branch | Verdict |
|---|---|
| LC-GB1 umbrella + name | RESOLVED — umbrella `loop-cognition` |
| LC-GB2 unified grounding gate | RESOLVED — one gate, two callers |
| LC-GB3 promotion-gate placement | RESOLVED — two-stage |
| LC-GB4 progressive autonomy | RESOLVED — maturity ∧ config AND-gate; grounding never bypassed |
| LC-GB5 agent-skill taxonomy | RESOLVED — matched-but-marked + ≤60-char summary |
| LC-GB6 wiki-synthesis contract | RESOLVED — Karpathy-pattern, loop leads |
| LC-GB7 agent-skills dir + install/config | RESOLVED — install-seed + first-run location (2 specifics flagged) |
| LC-GB8 sequencing / delivery | RESOLVED — Path 2, deconflicted (feed pipeline ∥ D16, LEARN-only) |
| RS-GB1 invocation | REC — escalation-routed, never worker-direct |
| RS-GB2 output handoff | REC — grounding gate → deliberate re-plan (superseding decision); never silent |
| RS-GB3 isolation | REC — `kata-research` NEW, fresh-context no-write, structured findings |
| AO-GB1 owner+structure | REC — orchestrator assembles; stable→context→volatile tiers |
| AO-GB2 rollup+adjacency | REC — root+nearest vertical; kata-graph adjacency pointers (lazy); prime-frame capped |
| AO-GB3 home | REC — `protocol/orientation.md` + `kata-orient` skill (mirror of kata-handoff) |
| LC-GB9 loop map + self-handoff | REC — loop-map in protocol/handoff.md; never-summarized {plan,goals,decisions,escalations} block |

---

## FREEZE-GATE AUDIT (2026-06-18) — fresh-context Opus (Fable 5 unavailable) → **HOLD → resolutions**
The mandatory pre-freeze adversarial pass (RUBRIC; no self-certification, L8). Verdict: **decisions sound,
specification fidelity not yet freeze-ready** (same class as the sprint-cadence audit). **CLEARED — do NOT
reopen:** RS-GB1/GB2 spine-#1 compliance; AO-GB1 vs D24d (orchestrator marshals data it already owns, logic
lives in `kata-orient`); LC-GB9 self-handoff vs D8/D33; Path-2 A/B isolation (LEARN-only ⇒ no read-back path
⇒ drift structurally impossible); LC-GB4 autonomy vs C2/C4/D1; cross-spec consistency w/ sprint-cadence;
LC-GB6 two-producer contract is minimal-not-over-engineered. Resolutions below.

**MUST-FIX (freeze-blocking):**
- **MF1 — frontmatter stubs for the 3 NEW skills (pin at freeze; validator-enforced, D27/D31/STANDARDS §1):**
  - `kata-research`: `category: plan`, `agnostic: true`, `status: experimental`, `version: 0.1.0`,
    `license: Apache-2.0`, `cost-weight: 3`, `allowed-tools: [Read, Grep, Glob, WebFetch, WebSearch]`
    (**no Write/Edit** — RS-GB3 promoted into frontmatter).
  - `kata-orient`: `category: handoff` (it is the *receiving half of HANDOFF* — most accurate; see MF2),
    `agnostic: true`, `status: experimental`, `version: 0.1.0`, `license: Apache-2.0`, `cost-weight: 2`,
    `allowed-tools: [Read, Grep, Glob]` (read-side, no Write).
  - `kata-promote`: `category: meta` (skill-management kin to `kata-improve`/`kata-write-skill`; see MF2),
    `agnostic: true`, `status: experimental`, `version: 0.1.0`, `license: Apache-2.0`, `cost-weight: 2`,
    `allowed-tools: [Read, Grep, Glob, Edit, Write, AskUserQuestion]` (human-gated write ceremony).
- **MF2 — drop the "umbrella = the `cognition/` category" rationale (it's factually wrong + self-contradictory).**
  Verified: `skills/cognition/` is **declared-but-empty** (STANDARDS §2 + DESIGN diagram name it; no skill
  exists). The spec name `loop-cognition` is a **theme/spec name, NOT a category**; its skills distribute by
  loop-phase: **`kata-research`→plan · `kata-orient`→handoff · `kata-promote`→meta**, with the engram /
  second-brain-feed extensions landing in **`cognition/`** (kata-engram territory — the actual first tenant of
  that category). Correct LC-GB1 wording: umbrella = one *spec*, **category-split** skills. (`kata-research`
  `category: plan` stays — control-flow-correct — but the "cognition umbrella" framing that justified it is dropped.)
- **MF3 — strike `kata-report` from REUSE; β emits synthesis pages directly.** `kata-report` is UNBUILT (D32)
  and owned by sprint-cadence (frozen *after* β, which runs ∥ D16) — an unsatisfiable REUSE at β-build time,
  and a different job (build-report vs LEARN synthesis). Resolution (auditor's option a): **β emits
  Karpathy-pattern synthesis pages directly via the LEARN contract + the LC-GB6 wiki-synthesis schema** — the
  "synthesis-page machinery" IS the schema, not `kata-report`. `kata-report` removed from the artifact map.

**SHOULD-FIX (applied):**
- **SF1 — name the C3 redaction owner in β scope:** the β LEARN emitter runs the `kata-handoff` §7 redaction
  filter as a **precondition to any vault write** (C3). Pinned into the β build scope (Task #8).
- **SF2 — keep LEARN-only *structural*, not procedural:** the β sub-mode of `kata-improve` **emits only**;
  DESIGN must state nothing reads the fingerprint back into a run during D16 (a structural property of where β
  sits, beyond the experimenter-neutrality procedure).
- **SF3 — collapse `protocol/wiki-synthesis.md` into a section of `protocol/engram.md`** (it *is* the LEARN
  payload shape) unless a concrete second standalone consumer forces a file. Net: **one** new protocol file
  (`protocol/orientation.md`), not two. Update the artifact map accordingly.
- **SF4 — `kata-promote` cross-category move constraint:** moving a candidate from `toolkit/skills/candidates/`
  into `toolkit/skills/<category>/` must preserve `name == dir` + pass the validator (D27) — recorded as a
  `kata-promote` design constraint. (LC-GB7 micro-picks confirmed genuinely non-blocking for β.)

**Freeze path:** apply MF1–MF3 + SF1–SF4 into `DESIGN.md` (frontmatter stubs as the tie-in table; corrected
category story; β-emits-directly; one new protocol file) → **re-confirm SHIP** (lightweight fresh-context
re-check, since all resolutions are direct applications of this audit's own prescriptions) → freeze.

## RE-CONFIRM (2026-06-18) — fresh-context Opus, no-write → **SHIP**
Focused re-check that MF1–MF3 + SF1–SF4 fully close the HOLD with no new drift. **VERDICT: SHIP.** All 8
STANDARDS §1 required fields satisfiable per skill; categories valid §2 enum (`plan`/`handoff`/`meta`); no-Write
correctly pinned (research/orient) and Write legitimately allowed for the human-gated `kata-promote`. Category
story internally consistent (MF2); `kata-report` cleanly struck with no orphan refs (MF3); SF1–SF4 coherent
with `protocol/engram.md` (C3 redaction match, wiki-synthesis as LEARN-payload section). No CLEARED item
reopened; no LOCKED decision rewritten. Lone non-blocking nit (uneven version/license enumeration in two
stubs) **fixed** 2026-06-18. **The spec is freeze-ready.**
