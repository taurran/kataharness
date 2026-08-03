---
date: 2026-07-26
purpose: every one of MindBridge's 26 forward-backlog items, brought over as OUR item
status: operator ruled "Worth building is ALL OF IT" — none of these is dismissed
---

# MINDBRIDGE'S BACKLOG, AS OURS — all 26, itemized

Their `BACKLOG-FULL.md` carried 26 items. My first pass mapped 12 and filed 14 as "intelligence
only." **That was wrong** — the operator's ruling is that these are features that matter to
MindBridge and should matter here. Every one is listed below as our own item, in their words where
their words were right, adapted where our architecture differs.

**Their status ≠ our status.** They mark what *they* built. Everything here is unbuilt on our side
unless the "Our side" column says otherwise.

---

## TIER A — items where we have a confirmed defect or gap RIGHT NOW

| ours | theirs | Plain description | Our side |
|---|---|---|---|
| **KH-B01** | BL-019 | **Does the learn-from-mistakes loop actually work?** They ask for an honest, evidence-based audit: do lessons actually change skills run-over-run, or do they stall in a lessons file? Are they captured → distilled → promoted → re-applied? Guardrail: promotion stays human-gated so "recursive learning" can't drift skills unreviewed. | **Half-confirmed.** Our writing half is genuinely live (269 pages). Nothing has ever been shown to read them back. |
| **KH-B02** | BL-022 | **Does the handoff mechanism actually work, on every path?** Does self-handoff fire at the right threshold and lose zero tasks? Does a boundary handoff correctly supersede a coincident self-handoff? Does the staleness rule demote correctly? **Can a genuinely fresh agent resume from artifacts alone?** Is there any silent path where a run ends with no handoff? | **Confirmed broken in parts.** Boundary-supersedes is prose with zero code. Staleness comparator doesn't exist. No run has ever written a `kind:`/`trigger:` field. The 0.70 trigger has never fired (peak seen: 69%). **Operator: BIG DEAL — see KH-T01.** |
| **KH-B03** | BL-026 | **Formalize "smoke check" into tracing a packet through the system.** Inject a real datum with an identity at the entry, assert the *same* unit (by content/id, not mere existence) reached and left each stage, emit a deterministic pass/fail + a durable trace. Catches silent-drop bugs by design. Their motivating incident: a build-time glob silently dropped a file class from a shipped payload — present, green, and missing. | Nothing owns end-to-end transit fidelity here either. **Their top recommendation for us.** |
| **KH-B04** | BL-002 | **Nothing proves the model-picking logic actually ran.** On a non-adaptive run a skipped resolver leaves no trace — "resolved to nothing" is indistinguishable from "never selected a model." A lazy orchestrator could omit the model argument on every dispatch and the economy saving silently evaporates with nothing noticing. Fix: emit a per-dispatch record of the resolved rung on **every** dispatch. | Same gap. Directly related to the Opus-5 fix — that defect was invisible for exactly this reason. |
| **KH-B05** | BL-023 | **A full reproducibility conformance pass over every authoring file.** One exhaustive sweep confirming: every must-happen step has an in-fence verify, every gate asserts **content not existence**, no model-filled gate parameters, no completion signal before the terminal gate. Theirs found 25 confirmed defects in 10 classes, 3 critical — including a live outage every automated gate reported green throughout. | Our analogue is running the ten-laws checker over the whole tree and triaging. Currently buried inside another task; deserves its own sweep. |

---

## TIER B — architecture and enforcement

| ours | theirs | Plain description | Our side |
|---|---|---|---|
| **KH-B06** | BL-005 | **A real plug-in registry for specialist agents.** The pattern already exists in three places, each grown ad hoc. Formalize: declared entry points × **mechanical selection keys** (file patterns / module flags / event names — *never model-noticed*) × a common envelope contract × per-point gating posture. **Registry invariant: a consult-class specialist can never attach to a judge-class entry point** — judge independence is structural, not conventional. | Same gap, same shape. **Neither side has built it.** If either does, the other should ingest rather than re-derive. |
| **KH-B07** | BL-017 | **Define the specialists as an organized cadre** — a typed registry where each declares identity, domain, capabilities, eligible entry points, tools/auth, and **judge-vs-consult class** — plus the mechanism that picks the right one for a need. | Unbuilt. Pairs with KH-B06. |
| **KH-B08** | BL-013 | **Choose specialists by the *meaning* of the current need**, not just mechanical file-pattern keys — across grill/plan/execute/evaluate and inside the mini-loops, while specialists **augment, never reshape, the spine**. Includes a recursion: *"advise the advisor"* — the advisor may consult a specialist for a scoped sub-question. **Open: how deep can that recurse before it's a loop (depth cap)?** | Unbuilt. Builds on KH-B06 + KH-B07. |
| **KH-B09** | BL-012 | **A typed ontology for execution types, code decisions, and run patterns** — a canonical schema so run metadata is machine-checkable instead of organically grown frontmatter. ⚠ **Their central tension:** a runtime schema layer is code, which their prose-first doctrine restricts. Options: (a) approved exception, (b) keep YAML+prose with the ontology enforced by the existing validator, (c) dev-tooling only. | **Our tension is weaker** — prose-first is a CHOICE here, not a host constraint, so we can use code where a script is optimal. See KH-T05. |
| **KH-B10** | BL-014 | **Ubiquitous language in the grill + a normalized self-glossary for the harness** — resolve and normalize domain terms *as decisions are made*, and define one vocabulary for the harness's own terms so grill/freeze/mini-loop/advisor/run-shape/tier/gate/drift each mean exactly one thing everywhere. | We have `kata-context` + `CONTEXT.md`, so we're ahead — but conformance is unenforced. Grill together with KH-B09. |
| **KH-B11** | BL-020 | **Build the real code-graph oracle layer.** Today the builder produces `def`/`ref`/`import` edges only. The richer backend — `call` edges, community assignments, **blast-radius** queries — exists as a config enum value and a table row, **with no implementation anywhere.** It was ingested as an option, never built. | Identical state here. Our graph has 425 `def`, 104 `ref`, **3 `import`** edges. |
| **KH-B12** | BL-021 | **A first-class "understand anything" tool.** Elevate the run-scoped comprehension map into a whole-repo capability — ask questions about any codebase and get a graph-backed answer (architecture, components, relationships, blast-radius, diffs), **usable outside a run.** Hard dependency on KH-B11. | Ours has only ever run its **diff-fallback** path; the graph-backed path has never produced an artifact. |

---

## TIER C — quality of the agents themselves

| ours | theirs | Plain description | Our side |
|---|---|---|---|
| **KH-B13** | BL-025 | **Skill evals — don't ship skills without them.** Two halves, deliberately separated. **(a) Static quality:** mechanical floors GATE (no-op instruction density, over-long body with no reference files, missing negative/anti-trigger cases, an invariant workflow left as prose), judgment findings ADVISORY. **(b) Behavioral eval harness:** execute a skill against known input, assert resulting state. ≥5 happy-path + ≥5 **negative/anti-trigger** prompts per skill, isolated workspaces, multi-trial, **ablation** — a skill that doesn't move evals is inert, a retirement signal. Their cited research: curated skills lift performance ~+16pp; **self-generated skills give NO benefit (−1.3pp)**; focused skills beat comprehensive docs. | We ship 49 skills and check **only formatting**. Their line *"an invariant workflow should be a SCRIPT, not a skill"* is our architecture, reached from the opposite direction. |
| **KH-B14** | BL-018 | **Deep review of the agent roster** — the agents that *do* work and the agents that *judge* it. Three tracks: coding-agent review (staying in scope, escalating rather than improvising), adversarial-validation review (**where are the legs redundant vs gappy?**), and evaluation-agent review → **explicit rubrics and scoring per test type**, so PASS means something auditable rather than vibed. **Open: how do rubrics stay in sync with the evaluator so they don't drift apart?** | Unbuilt. Our advals are already earning their keep; nobody has assessed whether they're redundant or gappy. |
| **KH-B15** | BL-011 | **Ride-along good-code/bad-code context for every code execution.** Coding models are trained to make tests pass, not to preserve maintainability — the reward signal never teaches architecture. A harness can raise the floor: give the **worker** explicit repo-specific patterns and smells (shotgun surgery, needless try/catch, cast-to-pass, commenting-out tests) and give the **evaluator** a maintainability leg grading the diff against those same definitions. Mechanically an overlay, keyed by stack/repo, **never model-noticed**. | Unbuilt. **Open: gate or advisory first?** They lean advisory-then-harden. |
| **KH-B16** | BL-015 | **A program-design step between architecture and execution** — explicit module boundaries, interfaces/contracts, signatures, call-graph layout — captured in the design doc and enforced through file-ownership and vertical slices, so coding fills in against defined seams instead of inventing structure. Their note: **least-defined item, scope it first.** | Unbuilt. |

---

## TIER D — run shapes and economy

| ours | theirs | Plain description | Our side |
|---|---|---|---|
| **KH-B17** | BL-006 | **An assess-only run profile** — comprehend → find deviations (annotated findings, **no fix loop**) → recommendations-led report → closeout offers "develop the plan forward" as a primed version-up. Optional: export findings to tracker issues, deduped by stable id, **dry-run by default**. | **This is exactly what our verification sweep did by hand this week.** Making it a run-shape makes it repeatable. |
| **KH-B18** | BL-009 | **Tune the mini-loops as a set.** The inline evaluator (risk-score fired), the advisor consults, and the diagnose loops each grew their own cadence and triggers and **were never tuned together.** Unify the trigger signals, define a cadence policy per run level, give each a budget and an exhaustion behavior. | We have the same three mini-loops with the same independent growth. |
| **KH-B19** | BL-001 | **Reasoning-on-demand.** Today tiering picks one model per phase, and the top model is reachable only via a whole-dispatch premium elevation carrying full cost. Instead: let a cheaper agent **package a small, well-scoped reasoning question**, send just that to the top model, and continue cheap with the answer. **Pay for top-tier reasoning by the question, not the phase.** Mirrors the inline evaluator, aimed upward. | Unbuilt. Needs a per-run budget so the saving isn't eaten by unbounded upward calls. |
| **KH-B20** | BL-004 | **Add a non-Anthropic model family as first-class.** Their implementation was **mostly data**: populate an empty family ladder, add the id map, optionally a per-family step table. Then family + anchor + coder-floor makes per-phase tiering fire the same relative way. ⚠ Their hard-won warnings: **confirm whether a platform can spawn subagents before giving a family an orchestrator role**; and treat vendor tier-superiority claims as **unverified marketing** until real tasks are run. | Directly adjacent to the Opus-5 fix. Our `_OPENAI_LADDER` / `_GEMINI_LADDER` / `_GENERIC_LADDER` are still empty. |
| **KH-B21** | BL-010 | **Multi-pass runs** — (a) several execution passes against the *same* frozen plan, and (b) an iterative loop that **re-grills between passes**. ⚠ **Resolve first:** our spine says *the plan does not drift / one-shot = no plan churn.* Iterative re-grilling deliberately reopens the plan. The grill must define what separates legitimate iterative deepening from churn — likely by making the sprint boundary the **only** sanctioned re-grill seam. | Unbuilt. **Spine-adjacent — highest care.** |
| **KH-B22** | BL-016 | **Multi-repo coding.** Coordinate one change across several repos in order, with per-repo worktree isolation, cross-repo contracts at slice boundaries, coordinated gates, and a handoff that spans repos. ⚠ **There is no cross-repo transaction** — partial-failure semantics must be decided. | Unbuilt. We isolate one target repo today. |

---

## TIER E — polish and operations

| ours | theirs | Plain description | Our side |
|---|---|---|---|
| **KH-B23** | BL-024 | **A full context-quality pass** across every context file — clarity, redundancy, reachability/pointerization, **fidelity-preserving** reorg. **The constraint is the interesting part: reorganization not reduction, zero fidelity loss, verbatim relocation.** A pass that "improves" by dropping detail has failed. Their honest history: the item originally assumed a context-quality skill already existed; a search found none — *"a remembered capability is not a built one."* | Unbuilt. Pairs with KH-B10 + KH-B05. |
| **KH-B24** | BL-008 | **UX pass** — a consistent, friendly menu vocabulary across intake, decision gates, and closing; plus grill legibility: plain language, grouped by theme, **one decision at a time, recommendation-first**. Keep the rigor, change the surface. | We already do one-question-at-a-time. The plain-language layer is the gap. |
| **KH-B25** | BL-003 | **Tighten two skimmable evaluator clauses.** (1) An exemption's load-bearing qualifier sat in a trailing clause a careless grader could miss, waving a silent scope drop through. (2) "Resolves to the frozen deferral scope" didn't require the **specific** dropped criterion to be covered — so a forged approval could rubber-stamp against a list that never mentioned it. Tightened to *"resolves to an entry covering THIS criterion."* | Worth checking our evaluator for the same two shapes. Wording-only. |
| **KH-B26** | BL-007 | **A repo-platform operations specialist** that owns issues/PRs/labels/links and **encodes which auth method actually works**, so repo-ops are one-shot rather than an auth fight. Their general rules, all learned the hard way: authorship follows the token owner so set assignee explicitly · **list existing labels before creating any** · dedupe by title **and** flag semantic overlaps · cross-link overlapping issues · traceability trailer in every body · **dry-run first, stay idempotent**. | ⚠ Their concrete auth matrix is internal infrastructure and was omitted. The operating rules are portable and good. |

---

## OUR OWN FINDINGS — not from MindBridge

These came from testing our tree this week. Full evidence in `D2-VERIFICATION-RESULTS.md`.

| ours | Plain description |
|---|---|
| **KH-B27** | The "run the whole loop" conductor **can't be started from any command** — no entry point reaches it. |
| **KH-B28** | An adaptive setting (`l2`) is validated, stored, and **never read by anything**; its engine function has zero non-test callers. |
| **KH-B29** | Handoff notes have "why was this written" fields **no real handoff has ever filled in.** |
| **KH-B30** | The mid-build quality checker has **never once** produced machine-readable output — 210 mentions in history, zero results. |
| **KH-B31** | **Nothing in code reads the "how careful should this run be" setting** — mode and tiers are notes for the AI to interpret. |
| **KH-B32** | **No test checks that quality rules survive cheaper modes.** Deleting the invariant sentence from a cheap tier keeps the validator green. |
| **KH-B33** | 7 places call git directly instead of the shared wrapper that keeps output consistent across machines. |
| **KH-B34** | The files proving a run happened are **excluded from git** — no permanent audit trail. |
| **KH-B35** | Rebuild the code map (35 days stale, predates a resolver fix) and **measure** whether the claimed ranking improvement is real. |
| **KH-B36** | Audit our own checkers for the counting bug they found in theirs — it silently checked half its targets while reporting success. |
| **KH-B37** | Check our repo for **conversion fossils**: code that looks live but does nothing. |
| **KH-B38** | Record DF-01 accurately: they adopted prose-first under HOST CONSTRAINT and recommend we not follow them into it. ⚠ NOT a validation of "scripts-first" — we are prose-first by choice (see ARCHITECTURE-CORRECTION-2026-07-26.md). |
| **KH-B39** | Build a checker that takes **every promise in our docs and greps for the code behind it.** Neither team has this. It is the direct mechanical answer to the pattern below. |
| **KH-B40** | Measure how much reference material the orchestrator loads **before doing any work.** Theirs was 102,750 tokens — **51% of the window**, before starting. Ours has never been measured. |

---

## THE PATTERN

> **The rule is written in a document for the AI to follow. Nothing in code enforces it.**

Every subsystem with real code behind it came back working. Every one relying on an instruction being
obeyed came back unverifiable or quietly broken. **KH-B39 is the mechanical answer to this**, and
`KH-T05` is the policy question behind it.
