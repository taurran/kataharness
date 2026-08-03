---
title: "dispatch-authoring — DESIGN (KH-T13 dispatch roles + KH-B42 gate rubric)"
status: DRAFT — authored by a dispatched design-author, awaiting conductor gate (this build is itself
  the first exercise of the artifact it defines)
spec: dispatch-authoring
grounding:
  - .planning/TASKS-ARCHITECTURE-2026-07-26.md (KH-T13 lines 40-93, KH-B42 lines 202-204 — the frozen
    problem statement; every "Decided" item below resolves one of KH-T13's four named "Open grill
    questions", line 91-93)
  - protocol/orchestration.md (the binding contract this design is consistent with, cited throughout)
  - protocol/prime-directives.md (PD-1/PD-2 — the honesty posture this design's rubric follows)
  - .planning/DECISIONS.md D59, D70, D88, D105, D108, D131 (read, not measured — cited by section below)
tags: [design, dispatch, roles, gate-rubric, KH-T13, KH-B42]
---

# dispatch-authoring — DESIGN

## 1. Goal, and why KH-T13 and KH-B42 are one design

**KH-T13** moves design-doc authoring and plan authoring out of the main/conductor session and into
two new dispatched roles. **KH-B42** is the rubric the conductor applies when it gates the artifact
that dispatch returns. They are one design because they are load-bearing for each other in both
directions:

- **T13 needs B42 to be safe to ship.** Today, whatever session runs the grill also runs
  `kata-design-doc` and `kata-plan-<tier>` directly, in its own context, then goes on to become
  `kata-orchestrate`'s gate. The moment authoring is dispatched, that same session must **gate an
  artifact it did not write** — and no rubric for that exists. `.planning/TASKS-ARCHITECTURE-2026-07-26.md:70-71`
  names this the first of T13's "Costs to resolve at grill — do NOT build past these", and
  `.planning/TASKS-ARCHITECTURE-2026-07-26.md:202-204` records B42 as blocking T13 from shipping for
  exactly this reason.
- **B42 needs T13 to exist to have a subject.** `kata-evaluate`'s default-FAIL gate already grades
  *build* work returned by a dispatched coder (`protocol/prime-directives.md` PD-2's "done requires
  proof, not assertion" already binds that path). There is no dispatched *authoring* artifact today —
  `kata-design-doc` (`skills/plan/kata-design-doc/SKILL.md`) and `kata-plan-standard`
  (`skills/plan/kata-plan-standard/SKILL.md`) are invoked directly, in-session, by whichever agent is
  driving the grill. Without T13, B42 has nothing to gate.

**Why this is not a violation waiting to happen, but a violation already live:**
`protocol/orchestration.md:32-36` — the binding contract on this branch — states: *"You dispatch, gate,
and route; you do not author the code, tests, design doc, or plan under your own gate. … If the
conductor drafts an artifact itself, it has stopped being an orchestrator for that artifact and become
an unsupervised worker."* Today's flow (grill session → `kata-design-doc` → `kata-plan-<tier>`, all
in one context, by the same session that will later gate the build) is precisely the case that
sentence names. This design closes that gap for the two authored documents that currently sit closest
to the conductor's own hand.

## 2. Grounded starting state (verified in code — cited, not assumed)

- `tools/kata_roles.py:33` — `ROLE_GROUPS = frozenset({"coder","validator","researcher","orchestrator","evaluator"})`,
  a closed enum; `tools/kata_roles.py:104-106` raises `ValueError` fail-closed on any role not in that
  set.
- `tools/kata_roles.py:41` — `HOST_ONLY_ROLES = frozenset({"orchestrator","evaluator"})` (LD11,
  `.planning/specs/multi-model-orchestration/DESIGN.md:53`). Neither new role belongs here — see §4.
- `tools/kata_dispatch.py:42-79` — `build_brief(task_id, role, platform, *, model, objective,
  result_path, inputs=None, owned_files=None, sandbox="read-only", acceptance="",
  output_contract=None)`; `sandbox` is one of `{"read-only","write"}` (`tools/kata_dispatch.py:37`);
  `resultPath` is validated worktree-relative, no `..` (`tools/kata_dispatch.py:63-67`).
- `tools/kata_dispatch.py:199-249` — `dispatch(brief, worktree, runner=None, timeout=600)` runs the
  platform's headless CLI (or, for the host, the `Agent` tool per `kata-orchestrate`'s own binding,
  `skills/coordinate/kata-orchestrate/SKILL.md:14`) and returns a normalized RESULT envelope; a
  `failed`/`timeout`/unparseable result is caught and returned as a `failed` envelope
  (`tools/kata_dispatch.py:230-248`) — no per-role special-casing is needed for that path.
  `tools/kata_dispatch.py:263-313` — `normalize(role, raw_text)` maps a worker's raw JSON to the
  role's payload shape; every existing branch (`validator`, `evaluator`, `researcher`) raises on a
  missing required field (default-FAIL); the `coder`/`orchestrator` catch-all
  (`tools/kata_dispatch.py:310-313`) only rejects an *empty* object — it does not validate a shape,
  which is why the two new roles need their own branches (§4) rather than falling through to it.
- `tools/intent_scaffold.py:182` — `write_intent(path, answers)` is the **sole authorized `INTENT.md`
  writer**. It is untouched by this design (§6) — the two new roles never write `INTENT.md`.
- `protocol/reuse-claims.md:14-21` (LD3) — the verify-before-reuse guard this design follows for every
  claim below: a "reuses X" sentence is frozen only with a cited `file:line` that exposes the exact
  surface assumed; otherwise it is a NEW capability, scoped as such.
- `protocol/escalation.md:78-80` — **already anticipates this design**: *"Planner-workers (in-harness
  plan/design authoring, dispatched during the freeze stage) raise `advice-requested` through this SAME
  machinery — advanced + granted only (runtime-gated); classified as the advisor's
  `advisor-planning-consult` event."* This is a verified reuse (LD3-compliant): the escalation `kind`
  enum (`orchestrator-resolvable | research-needed | human-required | advice-requested`,
  `protocol/escalation.md:10`) and its async/non-halting park contract already cover a dispatched
  authoring worker with **no schema change** — see §4.4.
- `tools/kata_models.py:379,384-386` — `kata-design-doc`, `kata-plan-advanced/essential/standard` are
  already classified `"critical"` in the model-tiering work-class map, i.e. the codebase already
  treats their *content* as judgment-tier work; this design does not change that classification, only
  where the skill runs (dispatched vs. in-session).
- `skills/plan/kata-design-doc/SKILL.md:13` and `skills/plan/kata-plan-standard/SKILL.md:12` —
  `allowed-tools: [Read, Grep, Glob, Write, Edit]` on both skills already. **Verified reuse**: neither
  skill needs a tool-access change to be dispatched — they can already write files.
- `skills/coordinate/kata-orchestrate/SKILL.md:330` — `[[kata-worktree]]` is the existing per-task
  worktree isolation mechanism every dispatched task already uses. **Verified reuse**: the design/plan
  authors get their own worktree the same way a coder task does; no new isolation mechanism is
  designed here.
- `skills/coordinate/kata-orchestrate/SKILL.md:1238-1258` — the existing "Cross-model dispatch"
  section and its role→dispatch-site table (L-MP5) is the pattern this design extends: *"At each
  role-group dispatch site, if `resolved_roles[role]["platform"] ≠ host_platform`: (1) build a brief …
  (2) dispatch … (3) fold the payload."* The two new roles follow the same three steps (§4.2).
- **No dedicated "freeze" skill file exists today.** `skills/coordinate/kata-orchestrate/SKILL.md:4-7`
  states it is invoked only "when you have a frozen plan" (design/plan authoring precede it);
  `modules/initiation/kata-initiate/SKILL.md` (D88, `.planning/DECISIONS.md:653-659`) freezes only
  `INTENT.md`, never `DESIGN.md`/`PLAN.md`; `skills/coordinate/kata-loop/SKILL.md:70-75` narrates
  "grill → freeze → execute" as part of handing off to `kata-orchestrate`, but that is a summary of
  the conceptual pipeline, not a literal call into a "freeze" skill. Today, "freeze" is executed by
  whichever session is driving the grill, invoking `kata-design-doc` then `kata-plan-<tier>` directly.
  This design does not invent a new conductor skill for that stage (§4.2 states exactly where the
  dispatch call is added instead).

## 3. KH-B42 — the conductor-gates-what-it-did-not-author rubric

### 3.1 Where it lives, and why it is a protocol file

The rubric is authored as a new file, `protocol/authored-artifact-gate.md`, following the exact
pattern `protocol/reuse-claims.md` already establishes: a small, cross-skill, binding contract
referenced **by path** from every site that needs it, never re-stated. This is a verified-reuse
pattern, not an assertion — `protocol/reuse-claims.md:51-61` names its own three producer sites
(`kata-design-doc`, `kata-plan`/`RUBRIC.md`, `kata-tdd`) by exactly this by-path convention.

### 3.2 The empirical basis (do not re-derive)

The six rows below are the checks that caught real defects while the conductor gated four dispatched
builds already merged on this branch (`KH-T02` — `4f16cbc`/`0a44bc2`; `T-04` — `bf163fd`; `BL-M21` —
`2828040`; `KH-T12` — `6d02f1e`, per this branch's own `git log`). This is the brief's own grounding
and is recorded here as the rubric's provenance, not re-derived from first principles.

### 3.3 The rubric

Applies to **any** artifact the conductor did not author itself and is about to write into the main
tree — in this build's scope, a returned `DESIGN.md` or `PLAN.md`. Each row states the check, the
evidence that satisfies it, what a FAIL looks like, and whether it is **mechanical** (a command or a
grep either finds the defect or it does not) or **judgment** (a human-grade reading call — see the
honesty note in §3.4).

| # | Row | What is checked | Evidence that satisfies it | FAIL looks like | Kind |
|---|---|---|---|---|---|
| 1 | **SCOPE** | The author touched only its declared `owned_files` (one file: the returned `DESIGN.md` or `PLAN.md`) inside its own worktree. | `git diff --stat` (or worktree file listing) against the brief's `boundaries.ownedFiles` shows exactly the one file, nothing else. | The worktree diff includes a second file, a code file, or a change outside the worktree. | **Mechanical.** |
| 2 | **CLAIM vs ARTIFACT** | The conductor reads the returned **file itself** — never the dispatch payload's self-reported `verdict` (§4.3) as a substitute for reading it. | A record that the conductor opened the file at the returned path (`designPath`/`planPath`) before writing anything into the main tree. | The conductor writes the artifact into the main tree on the strength of the payload's `verdict` field alone, without having read the file. | **Mechanical to confirm the file was opened; judgment to assess what it says** (split row — see §3.4). |
| 3 | **CITATIONS RESOLVE** *(the design-document analogue of GATE RE-RUN)* | Every `file:line` citation in the artifact is independently re-opened by the conductor, not trusted because the author claims it checked. | The conductor re-greps/re-reads each cited `file:line` and confirms the cited text exists. | A citation points at a line that does not say what the artifact claims, or does not exist. | **Mechanical for existence** (grep resolves or it does not); **judgment for whether the cited text actually supports the claim.** |
| 4 | **NO UNCITED REUSE CLAIM** *(the design-document analogue of EVIDENCE VERIFIED, per `protocol/reuse-claims.md`)* | Every "reuses / composes / via the existing X" sentence carries a cited `file:line` exposing the exact surface assumed. | `protocol/reuse-claims.md:14-21`'s guard applied by the conductor: grep the phrase pattern, confirm each hit has an adjacent citation. | A reuse claim with no citation, or a citation that names a file but not the specific field/event/output/path assumed. | **Mechanical to detect an uncited claim; judgment to confirm a cited one actually substantiates it.** |
| 5 | **DEVIATIONS CONFIRMED** *(frozen decisions are cited and not contradicted)* | Every decision the artifact states as LOCKED is checked against the real ledger/`DECISIONS.md` entry it cites, and every deviation the author self-flagged (`deviations`, §4.3) is independently checked against the ledger — never accepted at face value. | The conductor opens the cited ledger/`DECISIONS.md` entry for each LOCKED decision and each self-flagged deviation, and states whether it confirms or contradicts. | The artifact states a decision as LOCKED that the cited entry does not actually support, or a self-flagged deviation goes unchecked. | **Judgment** — comparing stated text to ledger semantics is not mechanically decidable. |
| 6 | **NO FROZEN INVARIANT RETIRED** *(every decision has defined edges; could two independent builders read this and diverge)* | The artifact does not silently weaken, retire, or leave ambiguous a Prime Directive, a `protocol/orchestration.md` clause, or a decision `DECISIONS.md` marks LOCKED — and every LOCKED decision it restates is specific enough that two independent readers could not diverge on it. | A read-back that (a) checks the artifact against the pinned/fingerprinted clauses in `protocol/prime-directives.md` and `protocol/orchestration.md` (`protocol/prime-directives.md:79-93` — the same tamper-evidence machinery), and (b) asks, for each LOCKED decision restated, "could a second builder read this and build something different?" | An invariant is quietly narrowed ("stub it for now" reworded as a LOCKED decision), or a decision is restated vaguely enough that two builds could diverge. | **Judgment — explicitly not mechanically provable**, same posture as `protocol/orchestration.md:58-64`'s own honesty clause: *"no check can prove a conductor never touched the keyboard it shouldn't have."* |

### 3.4 Honesty note — do not overstate enforcement (PD-2)

Rows 1 and 3's existence-check half, and row 4's uncited-claim-detection half, are genuinely
mechanical: a `git diff` or a `grep` either finds the violation or it does not, and that half can be a
real command a future task could script. **Rows 2 (content), 3 (citation-supports-claim), 5, and 6 are
judgment** — the same class of check `protocol/orchestration.md:58-64` already names as binding but
"NOT mechanically provable." This design does not claim B42 makes gating a design doc as mechanical
as re-running a test suite; it claims the six checks are now **named, ordered, and traceable to the
defects that motivated each one** — which is the improvement PD-1/PD-2 ask for (never silently defer,
never overstate what is proven).

### 3.5 Applying the same six rows to a returned PLAN.md

The rubric is one table, not two — a `PLAN.md` gate re-reads the same six rows with plan-specific
evidence: row 1 (scope) still checks the one owned file; row 3 (citations resolve) covers every
`owns:`/file-path the plan names, confirming the file exists and the ownership does not collide with
another task's; row 4 (no uncited reuse) applies to the plan's own reuse claims about existing tooling;
row 5 (deviations confirmed) checks that every task's `depends_on`/wave placement matches the DESIGN it
was built from; row 6 (no invariant retired) checks that no task silently narrows an acceptance
criterion the DESIGN stated. No new rows are needed for `PLAN.md` — this is stated explicitly so a
future reader does not invent a second rubric.

## 4. KH-T13 — the role design

### 4.1 Role names

**`design-author`** and **`plan-author`** — chosen to match the terminology
`.planning/TASKS-ARCHITECTURE-2026-07-26.md:54-55` already uses ("Design-doc author", "Plan author"),
kebab-cased to match the existing kind-string convention in this codebase (e.g.
`"advice-requested"`/`"research-needed"`, `protocol/escalation.md:10`). They are **new entries added
to** `tools/kata_roles.py:33`'s `ROLE_GROUPS`, which is otherwise unchanged — this is additive to a
closed enum, not a redefinition (§6).

### 4.2 Where they are dispatched from

**The freeze stage** — after the grill ledger passes its adversarial convergence gate
(`skills/plan/kata-design-doc/SKILL.md:30-33`'s own Precondition: *"Do not freeze a ledger that hasn't
passed [[kata-grill]]'s fresh-context convergence check"*) and before `kata-orchestrate` is invoked
(which requires an already-frozen plan, `skills/coordinate/kata-orchestrate/SKILL.md:4-7`).
`protocol/escalation.md:78` already names this exact point "the freeze stage." Per §2's grounded
finding that no single skill file owns this stage today, the dispatch call is added at the two real
sites that currently run these skills directly:

1. **`kata-design-doc`'s own Precondition section** gains the instruction: once the grill ledger has
   converged, the conductor session dispatches `kata-design-doc` as role `design-author`
   (`kata_dispatch.build_brief`/`dispatch`, `tools/kata_dispatch.py:42`/`:199`) instead of running it
   in its own context. `kata-design-doc`'s Output section (`skills/plan/kata-design-doc/SKILL.md:66-68`,
   "Hand to [[kata-plan]]") is the natural place for the parallel instruction for `plan-author`, since
   the two skills already hand off to each other by name.
2. **Each `kata-plan-<tier>`'s Precondition** gains the mirrored instruction once `DESIGN.md` is
   frozen.
3. **`kata-loop`'s step-2 preamble** (`skills/coordinate/kata-loop/SKILL.md:70-75`, the "grill → freeze
   → execute" line), for operators who go through the loop conductor rather than invoking the plan
   skills directly, gains one clause naming what "freeze" now is: the `design-author` then
   `plan-author` dispatch.

This mirrors `skills/coordinate/kata-orchestrate/SKILL.md:1238-1258`'s existing three-step pattern for
`validator`/`researcher` (build a brief → dispatch → fold the payload) — no new dispatch *mechanism* is
designed; only its call sites are new.

**Sandbox and worktree:** `sandbox="write"` (the author writes its one file into its own
`[[kata-worktree]]` worktree, `skills/coordinate/kata-orchestrate/SKILL.md:330` — verified reuse, §2),
mirroring the existing `coder` role's `sandbox="write"` usage
(`tools/kata_dispatch.py:59-79`/`skills/coordinate/kata-orchestrate/SKILL.md:1244`).

### 4.3 Payload shapes

Both are new branches in `tools/kata_dispatch.py:263-313`'s `normalize(role, raw_text)`, alongside the
existing `validator`/`evaluator`/`researcher` branches — they are **not** routed through the
`coder`/`orchestrator` catch-all (`:310-313`) because that branch only rejects an empty object; the two
new roles need their own required-field validation (default-FAIL on a missing path, mirroring
`validator`'s missing-verdict raise, `tools/kata_dispatch.py:278-281`).

```
design-author  -> { "designPath": str,   "verdict": "ready" | "needs-rework", "deviations": [str] }
plan-author    -> { "planPath":   str,   "verdict": "ready" | "needs-rework", "deviations": [str] }
```

- `designPath`/`planPath` — **REQUIRED**, worktree-relative. This is the artifact **path**, per
  `.planning/TASKS-ARCHITECTURE-2026-07-26.md:74`'s mitigation ("return the artifact as a FILE; the
  payload is a path + verdict, and the conductor reads the file") — never pasted content. Missing ⇒
  `normalize` raises (default-FAIL), matching every other role's posture.
- `verdict` — **REQUIRED**, the author's own self-assessment. `"needs-rework"` is not a FAIL by
  itself (the conductor still applies the B42 rubric either way, per row 2 — the verdict is never a
  substitute for reading the file) — it is a signal the author found something it could not fully
  resolve without deciding it, and is distinct from an escalation (§4.4): the author still produced a
  document, it is flagging low confidence in a scoped part of it.
- `deviations` — optional, defaults to `[]` (mirrors `researcher`'s optional fields,
  `tools/kata_dispatch.py:306-309`). Each entry names a place the author extrapolated beyond, or found
  ambiguous in, the cited ledger — this is the list B42 row 5 (DEVIATIONS CONFIRMED) independently
  checks; it is never accepted at face value.

The RESULT envelope's outer `status` (`completed`/`failed`/`timeout`/`fallback`,
`tools/kata_dispatch.py:38`) is unchanged and orthogonal to the payload `verdict` field, exactly as it
already is for `validator`/`evaluator` (`tools/kata_dispatch.py:253` docstring: *"`status` = the
DISPATCH OUTCOME (not the verdict)"*).

### 4.4 What each receives — by path, not pasted

Per the frozen decision (`.planning/TASKS-ARCHITECTURE-2026-07-26.md:92-93`'s open question, "does the
design-author get the full grill ledger or a distilled brief," now resolved): **by path, and the full
ledger — never a conductor-distilled brief.** A conductor distillation would itself be doing the work
this design exists to stop the conductor from doing (§1). This mirrors the discipline
`skills/coordinate/kata-handoff` already applies to context handoff artifacts (point to paths, don't
re-derive).

- **`design-author`** receives (as `inputs` in its brief, `tools/kata_dispatch.py:74`): the converged
  grill ledger's path, `.planning/DECISIONS.md`'s path, `protocol/reuse-claims.md`'s path, and
  `protocol/orchestration.md`'s path (so the author's own output is checkable against the same
  contract the conductor gates it with).
- **`plan-author`** receives: the frozen `DESIGN.md`'s path (this build's own output, once the
  conductor has gated and written it — see the sequencing note in §6), the relevant
  `skills/plan/kata-plan/RUBRIC.md`'s path, and `.planning/DECISIONS.md`'s path.

**Escalation, not silent deciding, on a genuinely unresolved ledger branch.** `kata-design-doc`'s
existing instruction (`skills/plan/kata-design-doc/SKILL.md:26-28`: *"If the design-doc author finds an
unresolved branch, that is a signal the grill was incomplete: return to grilling, do not decide it
here"*) cannot literally "return to grilling" as a dispatched worker — it has no `AskUserQuestion`
channel (`.planning/TASKS-ARCHITECTURE-2026-07-26.md:47`: *"Subagents cannot [talk to the human] —
`AskUserQuestion` is withheld from them structurally"*). This is **already a solved case, not a new
one**: `protocol/escalation.md:9-19`'s existing `kind: "human-required"` is exactly the classification
for a discovered unknown that only a human can resolve, and its async/non-halting park contract
(`protocol/escalation.md:21-30`) applies unchanged. No new escalation `kind` is designed here — a
`design-author`/`plan-author` that hits a genuinely unresolved branch raises the existing
`human-required` kind, the task parks, and the conductor (which still holds the human channel, since it
is the same session that ran the grill) routes it back to a human decision. `protocol/escalation.md:78-80`
already names "planner-workers... dispatched during the freeze stage" using this exact machinery for
`advice-requested`; this design's escalation path for a genuinely unresolved branch is the sibling case
using `human-required` instead.

## 5. Out of scope — named, not silently dropped

- **The grill itself is never dispatched.** `.planning/DECISIONS.md:478-488` (D70): *"the grill's
  engine is interrogating the human, which is OFF in autonomous mode."*
  `.planning/TASKS-ARCHITECTURE-2026-07-26.md:46-51` restates this as the dividing line for the whole
  T13 split. This design adds no dispatch path for `kata-grill-*`, `kata-context`, or any grill-tier
  skill.
- **ELEVATE's dispatch/present split is untouched.** `.planning/TASKS-ARCHITECTURE-2026-07-26.md:53`
  already marks it 🟡 ("generate dispatched → present in-session") and line 92 lists "is ELEVATE's
  split real or over-engineering" as a still-open grill question. This design does not resolve it —
  ELEVATE is out of scope, named here so it is not silently assumed settled.
- **Dispatch depth stays 1.** `.planning/TASKS-ARCHITECTURE-2026-07-26.md:72`'s named risk ("a
  dispatch level, on an unstable number — Claude Code's depth default swung 5 → 1 → 3 across four
  releases") is resolved by **not** letting a `design-author`/`plan-author` itself dispatch anything —
  neither role gains a nested-dispatch capability in this build. If a future author genuinely needs to
  dispatch a `researcher` mid-authoring, that is a revisit item, not built here.
- **`KH-T10` (per-role model override as a general mechanism) is not built here.** T13's own ranked
  benefits (`.planning/TASKS-ARCHITECTURE-2026-07-26.md:65-66`) note a dispatched author "takes an
  explicit model override" and that this "gives `KH-T10` somewhere to land" — this design gives it that
  landing spot (a role is a role; `kata_roles.resolve_roles`'s existing `model`/relative-token handling,
  `tools/kata_roles.py:120-136`, already covers any role uniformly) but does not design or build a new
  override mechanism. Nothing beyond what `resolve_roles` already does for every role is added.
- **The evaluator/orchestrator host-only constraint is unchanged.** Neither new role is added to
  `HOST_ONLY_ROLES` (§4.1) — they may be routed off-host exactly like `validator`/`researcher` already
  are.

## 6. Backward compatibility

- **Closed-enum addition, additive only.** `tools/kata_roles.py:33`'s `ROLE_GROUPS` gains two members;
  every existing member, and `resolve_roles`'s fail-closed behavior on an unrecognized role
  (`tools/kata_roles.py:104-106`), is untouched. A `kata.config.roles` block that names none of the
  five original roles is unaffected; a `roles` block that is absent still resolves every role
  (including the two new ones) to the host, byte-for-byte (`tools/kata_roles.py:99-102`, BC1).
- **`normalize()` gains two branches, no existing branch is edited.** `validator`/`evaluator`/`researcher`/
  `coder`/`orchestrator` payload shapes are byte-unchanged.
- **`protocol/escalation.md`'s `kind` enum is unchanged** (§4.4) — the design reuses
  `human-required`, adding no new value.
- **`intent_scaffold.write_intent` is untouched** (§2) — neither new role writes `INTENT.md`; the
  conductor remains its sole writer.
- **Existing runs are unaffected.** A `kata.config` with no `roles` block, or a `roles` block that
  predates this design, resolves exactly as it does today — the two new roles only exist to be
  assigned; nothing defaults a run into dispatching them.
- **The conductor remains the sole main-tree git writer.** The author writes into its own worktree
  (§4.2); the returned path is read, gated (§3), and only then written into the main tree by the
  conductor — the single-writer discipline `.planning/TASKS-ARCHITECTURE-2026-07-26.md:76-78` calls out
  as the risk to decide explicitly is resolved by never letting the dispatched author touch the main
  tree at all.

## 7. Honest residual — what this design does NOT solve

- **B42's judgment rows (§3.4) are not made mechanical by this design.** A future project could script
  the existence-checking half of rows 1/3/4; rows 2/5/6 stay human-graded, same as
  `protocol/orchestration.md`'s own honesty clause already accepts for the orchestrator's behavior
  generally.
- **The "no dedicated freeze-stage skill" gap (§2) is not closed, only worked around.** This design
  adds the dispatch instruction into the skills that already run at that point rather than inventing a
  new conductor file for the stage. A future pass could decide a dedicated freeze-stage skill is worth
  building; this design does not make that call.
- **The depth-budget question (§5) is deferred, not answered.** If an author ever needs to dispatch a
  researcher mid-authoring, this design has no answer for what that does to the dispatch-depth-1
  constraint.
- **ELEVATE's split (§5) is explicitly unresolved** — a future grill question, not a gap introduced by
  this design.
- **No live dispatch of either new role exists yet at design time.** Like the `validator`/`researcher`
  roles before them (`.planning/DECISIONS.md:1035`: *"codex NOT installed → proven against the
  stub"*), this design's plan (PLAN.md) proves the wiring against the injectable stub runner
  (`tools/kata_dispatch.py:191-196`'s seam); a live cross-model run is gated on install + confirm, the
  same honest-scope posture the codebase already carries for every dispatched role.
