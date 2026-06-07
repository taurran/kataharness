# research/NOTES.md — per-source adopt / drop / distort ledger

> DESIGN.md calls this "the most important bake-in work": exactly which patterns each source contributes, and
> what we deliberately did NOT take. Seeded by the v0.1 adversarial review (see `.planning/REVIEW-v0.1.md`).
> Honesty rule: a `source:` line in a skill must correspond to a real ADOPT row here.

## mattpocock/skills
| Skill | Source | ADOPTED | DROPPED / DISTORTED (with reason) |
|---|---|---|---|
| kata-grill | grill-with-docs, grill-me, ubiquitous-language | relentless one-at-a-time; explore-instead-of-ask; glossary challenge; concrete-scenario stress-tests; inline ADR/CONTEXT baking; 3-test ADR rule | — |
| kata-tdd | tdd | vertical slices; anti-horizontal; behavior-not-implementation; refactor-only-while-green | DROPPED the supporting refs (deep-modules/interface-design/mocking/tests/refactoring) → backlog: port as resources |
| kata-plan | to-issues | task-level decomposition; runnable acceptance per task | DISTORTED: we added disjoint-file-ownership+wave-DAG (our innovation) which leans horizontal; to-issues' vertical-tracer-slice axis must be reconciled, not replaced. DROPPED HITL/AFK slice tagging → backlog |
| kata-design-doc | to-prd | freeze-the-contract; acceptance criteria | DROPPED test-seams + Testing-Decisions → now re-added |
| kata-review | review | adversarial intent | DISTORTED: kata-review is really cpp-adversarial-validation; mattpocock review's Standards axis + parallel-2-axis structure NOT taken → Standards axis added to kata-evaluate instead |
| kata-handoff | handoff | the read-in-order + NEXT-STEP template | INVERTED (deliberately): mattpocock saves to OS temp; we go durable/in-workspace/git — correct for this harness, now acknowledged. DROPPED "suggested skills" → re-added |
| kata-context | ubiquitous-language, grill-with-docs CONTEXT-FORMAT | opinionated canonical terms; tight defs; _Avoid_ synonyms; lazy creation | overlap with kata-grill delineated (grill captures during a grill; context maintains standalone/multi-context) |

## GSD (get-shit-done)
| Skill | ADOPTED | DROPPED |
|---|---|---|
| kata-grill | discuss-phase options-with-free-text-escape interaction; spec-phase specificity bar | DROPPED discuss-phase checkpointing + thinking-partner sub-loop + user-cited-doc accumulation → checkpointing + cited-doc now added |
| kata-plan | plan-phase task/acceptance depth | — |

## BMAD-method
| Skill | ADOPTED | DROPPED |
|---|---|---|
| kata-design-doc / kata-review | **trade-offs-over-verdicts** principle (now imported into kata-design-doc); architect/QA-as-adversarial-roles reinforces the evaluate pair | role-agent persona separation (analyst/architect/PM/dev/QA) NOT taken → backlog; corrected the kata-plan name-drop |

## Anthropic (long-running agents)
| Skill | ADOPTED | DROPPED |
|---|---|---|
| kata-orchestrate | plan-guardian lead; centralized plan ownership; default-FAIL gating; commit-at-checkpoint | — |
| kata-evaluate | fresh-context no-write evaluator | structural caveat: Bash remains (gate-running) — "read-only" reworded honestly |
| kata-handoff | reset-with-handoff / durable-before-compaction | self-handoff at threshold → kata-selfhandoff (backlog) |

## Claude Agent Teams (protocol, mined NOT depended on — D4)
| Skill | ADOPTED | DROPPED |
|---|---|---|
| kata-board | append-only mailbox + escalation channel | file-locked task-claim → kata-tasklist (backlog); v0.1 uses orchestrator-assignment so no self-claim race |
| kata-worktree | per-owner isolation | — |
| kata-orchestrate | lead-as-plan-guardian; subagent dispatch (Claude binding = Agent tool; abstracted as adapter capability) | Teams itself (Claude-only) not depended on |
