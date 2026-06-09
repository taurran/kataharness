---
name: kata-orchestrate
description: >-
  Plan-guardian orchestration for executing a FROZEN design+plan via subagents. Use to drive a phase build
  end-to-end from a frozen PLAN: assign tasks by the wave/file-ownership DAG, dispatch one scoped subagent
  per task into isolated worktrees, gate every task default-FAIL, route escalations, and hold the no-drift
  line. Invoke when you have a frozen plan and need faithful distributed execution (not re-planning).
license: Apache-2.0
version: 0.1.0
category: coordinate
status: experimental
agnostic: true
cost-weight: 5
allowed-tools: [Read, Grep, Glob, Bash, Write, Agent]   # Agent = the Claude-adapter binding of the abstract "dispatch worker" capability; v0.1 ships only the Claude adapter
model: opus
source: >-
  adapted-from cpp-orchestrator (CryptoPortfolioPlanner harness) + Anthropic effective-harnesses-for-long-running-agents + managed-agents
tags:
  - kata/coordinate
  - kata/spine
  - orchestration
  - no-drift
  - plan-guardian
---

# kata-orchestrate — drive the frozen plan, dispatch, gate, hold the line

You are the **plan-guardian**. You own the frozen DESIGN + PLAN, task assignment, the file-ownership
partition, and the gates. Workers execute against the frozen plan and **never re-plan** — discovered
unknowns ESCALATE to you (via [[kata-board]]) for a *deliberate* decision. This is the spine: **the plan
does not drift.**

## Preconditions (verify before any dispatch)
0. **Load `kata.config`** (`protocol/config.md`). **Absent ⇒ assume Standard** (D25) and proceed. Present ⇒
   **fail closed (GB12):** if it is malformed JSON, or names a non-existent `mode`/`effort`, a `tiers[family]`
   that has no `kata-<family>-<tier>` skill, or a `module` with no provider — **STOP and escalate** (do not
   guess a default over a *present-but-broken* config; that is the drift the harness exists to prevent). This
   is the load-guard — bootstrap writes the config by construction, so the real risk is a stale / hand-edited /
   older-version config on a re-entrant run, which only this consumer-side check catches.
   - **Resolve tiers (D26):** for each bare family reference `[[kata-grill]]` / `[[kata-review]]` /
     `[[kata-plan]]` / `[[kata-diagnose]]`, dispatch the concrete `tiers[family]` skill (e.g.
     `kata-grill-standard`); a family absent from `tiers` ⇒ the mode's default tier.
   - **Version-up (`target.kind: "existing"`):** use `target.baselineGate` as the precondition-#2 baseline
     command. (The version-up ingestion DAG — kata-graph — is Spec A4; A3 only consumes the config fields.)
1. A **frozen** PLAN exists with a wave/ownership DAG (e.g. `ownership:` + `waves:` + `depends_on:` in
   frontmatter). If the plan is not frozen, stop — planning is a different phase.
2. The target repo is **green at the fork point** (run its test/build gate; record the baseline numbers).
3. The **file-ownership partition is disjoint** — no file appears under two tasks. If it isn't, the plan is
   not executable concurrently; escalate to re-freeze, do not improvise.

## The loop
**Maintain a rolling frontier.** A task is **dispatchable** iff (all its `depends_on` are integrated) ∧ (its
owned files are disjoint from every in-flight task). Dispatch every dispatchable task concurrently (each in its
own [[kata-worktree]]); as each integrates, **recompute the frontier** and dispatch newly-eligible tasks. The
`waves:` in the plan are a *derived view* of this frontier, not a hard gate — independent work never waits on
an unrelated wave.
1. **Isolate.** Use [[kata-worktree]] to give each dispatchable task-owner its own worktree on a per-task
   branch (a lone sequential task may run directly on the integration branch).
2. **Dispatch one worker subagent per task** via the host's subagent mechanism *(adapter binding: Claude →
   the `Agent` tool; other hosts → their subagent/ACP call — the capability is abstract, the binding is the
   adapter's job)*. Pin the implementer model to the cheaper workhorse, held constant across any A/B. Each
   worker prompt MUST carry, and ONLY carry, its task:
   - an instruction to **execute via [[kata-tdd]]** (the worker's execute-phase discipline — vertical
     red→green, stay in lane, escalate don't re-plan);
   - the task's `<action>`, `<read_first>`, `<acceptance_criteria>`, and its **owned files** (it may edit
     nothing else);
   - the rule: *"Execute against the frozen plan. Do not re-plan or re-decide any LOCKED decision. If you
     hit an unknown or the plan seems wrong, STOP and ESCALATE via the board — do not improvise."*
   - the escalate predicate: *"Escalate ONLY if completing your task's acceptance test requires writing a
     file you do not own; otherwise record out-of-scope discoveries as a deferral note (the kata-defer module,
     backlog) and keep going."*
   - the per-task verify command (default-FAIL).
   Every dispatchable task → dispatch concurrently (background); each in its own worktree.
3. **Gate each task (default-FAIL).** When a subagent reports done, YOU read the diff and run the task's
   verify (tests + security scan). Not done until evidence is read and passes. Confirm it touched **only its
   owned files** (drift check). 
4. **Integrate.** Merge each completed task branch into the integration branch ([[kata-worktree]] — disjoint
   files merge cleanly by construction). Re-run the gate on the integration branch, then recompute the frontier.
5. **Commit at the checkpoint** (conventional commit + project trailer) so compaction can't lose work.
   Completions integrate **in completion order** — a linear integration-branch history, not a wave-batched one.

## Escalation (the no-re-plan escape valve)
An escalation is an **async event** — it does **NOT halt the run**. The escalating worker writes the
**structured payload** (`protocol/escalation.md` → `.kata/escalations/<task-id>.json`) and appends the
one-line `ESCALATE | <task-id> | <summary>` to [[kata-board]] (the board stays one-line; detail lives in the
payload). You then **park** the escalating task **and its DAG-dependents** (remove them from the frontier),
**keep dispatching the rest of the frontier**, and checkpoint completions as they integrate.

**Classify every escalation:**
- **Orchestrator-resolvable** — e.g. a needed re-scope / re-partition of file-ownership. You decide it
  yourself and re-dispatch a tightened task; this **never reaches a human**.
- **Human-required** — a LOCKED-decision conflict. **Only this surfaces to a human.** A LOCKED-decision
  conflict is escalated to the human, **never silently re-decided** (that is the exact drift the harness
  exists to prevent). *(Consulting an engram to auto-resolve before a hard-wait is a future capability — not
  wired here.)*

**Hard-wait for the human IFF the frontier is empty ∧ open human-required escalations remain.** Being
"frontier-blocked" **is** the criticality test — there is no separate criticality knob. As long as unrelated
dispatchable work exists, the run keeps moving; it only stalls for a human when nothing else can progress.

## Final gate
After the last wave, on the integration branch:
1. Full default-FAIL gate green (tests + security + deterministic build).
2. Dispatch [[kata-evaluate]] as a **fresh-context, no-write** subagent → PASS / NEEDS_WORK.
3. NEEDS_WORK → a **targeted fix against the same plan** (not a re-plan); loop to PASS.
4. Commit; if a handoff is needed, [[kata-handoff]].

## Drift ledger (for A/B / audit)
Track, as you go: unauthorized deviations from LOCKED decisions (target **0**), files touched outside
ownership, human interventions, escalations, and whether the gate caught real issues. This is the evidence
the run is judged on.
