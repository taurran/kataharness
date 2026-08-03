# protocol/orchestration.md — the orchestrator's own contract

**Binding contract for every conductor role under KataHarness** (`kata-orchestrate`, `kata-loop`, and any
skill that dispatches workers into the frontier). Until this file existed, the doctrine below lived only
in `.planning/THIN-ORCHESTRATOR-DOCTRINE.md` — a planning document, not a binding one: a described rule
with no enforced home. This file is that home.

## The doctrine

> **A well-behaved orchestrator does not do the work itself.**

Independently reached in Anthropic's own guidance on agent workflows: *"No direct filesystem or shell
access from the workflow itself — Agents read, write, and run commands. The script coordinates the
agents."* The conductor is the script; the dispatched agents are the ones who touch the tree.

## 1. What the conductor DOES own

The conductor is the **plan-guardian** (spine principle #1). It owns:
- the **frozen design + plan** — the artifact everything else executes against;
- **task assignment** — which unit of work goes to which dispatch;
- **file-ownership partitioning** — the disjoint DAG that makes concurrent dispatch safe;
- **dispatch** — launching one scoped subagent per dispatchable task;
- **gating returned work default-FAIL** — nothing is "done" until the conductor reads the evidence
  and it passes; a subagent's own account of its work is not confirmation;
- **routing escalations** — a discovered unknown goes to the conductor for a *deliberate* decision,
  never resolved silently by the worker that hit it;
- **holding the no-drift line** — the plan does not drift, and the conductor is the one who refuses
  the drift when it shows up.

## 2. What it does NOT do

The conductor does not author the artifacts under test. **Writing the code, the tests, the design doc,
or the plan IS doing the work** — indistinguishable from any other unit of designed work, and it does
not become orchestration merely because the same session also holds the gate. If the conductor drafts
an artifact itself, it has stopped being an orchestrator for that artifact and become an unsupervised
worker.

## 3. Why it matters

The order below is deliberate — read top to bottom, not as an unordered list:

1. **Context economics.** The main session is the scarcest resource in a run and must survive the
   whole of it. Every artifact it drafts personally is context it cannot get back.
2. **Model economics.** Dispatched work is routed independently — economy work tiers down, critical
   work stays at the anchor. When the conductor does the work itself, everything runs at the anchor
   whether it needs to or not.
3. **Consistency.** A conductor that authors is not a conductor; it is a worker that also happens to
   hold the gate, which collapses the separation the default-FAIL loop depends on.

## 4. The honest residual

The conductor cannot reach zero judgment. It still routes, reads gate output, decides escalations, and
interprets drift. There is a floor; it is far lower than "the anchor is the ceiling for all critical
work," but it is not zero.

## 5. Honesty clause

This is a **BEHAVIOURAL** norm: it is graded at review and evaluate time, and it is **NOT mechanically provable**
— no check can prove a conductor never touched the keyboard it shouldn't have. What **IS** mechanical is
narrower and different in kind: this contract cannot be silently deleted or inverted. It is clause-pinned
and fingerprinted by `validate_skills.check_protocol_integrity`, the same machinery that protects
`protocol/prime-directives.md` — so the *document* is tamper-evident even though the *behavior* it
describes is not mechanically enforced. Do not read "the contract is protected" as "the behavior is
enforced"; those are two different claims, and only the first one is true by construction.

## Producer / consumer

**Primary consumer:** `kata-orchestrate` — the conductor role this contract binds, referenced directly
from its SKILL.md. **Graders:** `kata-evaluate` (fresh-context, no-write, default-FAIL — judges whether
the conductor's own output crossed into authored work) and `kata-review` (adversarial pass that hunts
for a conductor quietly doing the job it was meant to only supervise). Registered in `validate_skills.py`
`REQUIRED_PROTOCOL` — erasing this file, or removing any of its load-bearing terms, fails the validator
the same way tampering with the Prime Directives does.
