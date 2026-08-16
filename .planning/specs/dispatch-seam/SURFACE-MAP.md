---
spec: dispatch-seam
artifact: ground-truth surface map (Phase 0 evidence)
date: 2026-08-16
baseline: master `de8578c` (branched to grill/dispatch-seam) · gauntlet 4/4 PASS · tree clean
method: three read-only survey agents (skill-prose launch sites · tools/ code surfaces · host/adapter
  attach points) + conductor spot-verification of the load-bearing claims. Evidence labels —
  [VERIFIED] read directly by the conductor this session; [SWEPT] agent-reported with file:line,
  spot-checked by class not by line. Re-verify any [SWEPT] line before it becomes load-bearing in a
  DESIGN (the verify-before-reuse standing rule).
---

# BL-M33 · the conductor↔host dispatch seam — GROUND-TRUTH SURFACE MAP

**In plain terms:** every way the harness starts an agent today, what is real code vs. prose at each
one, which enforcement primitives already exist but hang unwired, and where a seam with authority
could physically attach. This is the map the grill runs on — no design decisions live here.

## 0. The structural truth the whole map reduces to

The harness is **two layers by design, and the layers barely touch**:

- **Layer 1 — Python engines (`tools/`).** Rich, tested, mutation-proven — and almost entirely
  **orphaned**: `kata_dispatch`, `kata_roles`, `kata_models.resolve()`, `kata_config`,
  `escalation.py`, `kata_board` (writer), `kata_preflight`, `contract_gate`, the entire telemetry
  suite — **zero production callers each**. [VERIFIED for kata_dispatch/kata_roles/kata_config;
  SWEPT for the rest]
- **Layer 2 — SKILL.md prose.** The *actual* dispatcher is an LLM reading instructions.
  `kata-orchestrate/SKILL.md` alone carries **~52 launch sites**; the canonical worker dispatch is
  one sentence: *"dispatch one worker subagent per task via the host's subagent mechanism (adapter
  binding: Claude → the `Agent` tool)"* (`SKILL.md:339-343`). [SWEPT]

**The only code the host executes mechanically:** the three Claude hooks + statusline chain
(`adapters/claude/settings.snippet.json` — SessionStart, PreCompact, UserPromptSubmit; **no
PreToolUse**; every shipped hook is deliberately fail-soft and never blocks) [VERIFIED], the
maintainer CLIs (gauntlet, validate_skills — prose-conformance checks, not dispatch checks), and
`run_result.evidence_is_current` via benchmark/debug tooling. [SWEPT]

**Consequence (the BL-M33 filing, re-confirmed):** when the conductor dispatches any host-side
agent it *writes a prompt*. There is no function call, therefore no chokepoint, therefore nowhere
for enforcement to live. Both Backlog Burns bypassed the entire loop through exactly this gap
(BL-M34, operator-caught).

## 1. Dispatch surfaces — every way an agent gets started today

| # | Surface | Mechanism | Code or prose? |
|---|---|---|---|
| D1 | **Worker dispatch** (the loop, per task) | host `Agent` tool, one subagent per task in a worktree | PROSE (`kata-orchestrate:339-343`) |
| D2 | **Judge dispatches** — kata-evaluate, kata-slop-check, kata-review, kata-inline-eval | `Agent` tool, "fresh-context, no-write" | PROSE; no-write IS structural (frontmatter), **freshness is an unverified convention** (`kata-evaluate:27-32`, post-EDR-7 honest wording) |
| D3 | **Author dispatches** — design-author / plan-author (KH-T13) | prose *names* `build_brief`/`dispatch` (`kata-design-doc:38-44`) | PROSE citing dead code — the named functions have no production caller |
| D4 | **Advisor** — kata-advise, conductor-only | `Agent` tool; gate/spend/rung via `kata_models.advisor_status` + `kata_advisor.*` | PROSE dispatch + CF gates (`kata-orchestrate:1159-1203`) |
| D5 | **Research** — kata-research on escalation | `Agent` tool; payload via `escalation.py` (orphaned) | PROSE |
| D6 | **Cross-model dispatch** — codex/kiro workers | `kata_dispatch.build_brief` → `dispatch()` → headless CLI subprocess | **CODE — the only real dispatch path in the repo** (`kata_dispatch.py:127-171,219`), stub-test-proven, never run live |
| D7 | **Debug-module dispatches** — comprehend / deviate / characterize / tdd fix workers | `Agent` tool + engine calls inside callees | PROSE |
| D8 | **Loop-module invocations** — kata-loop → initiate → bootstrap → orchestrate → closeout | in-session skill invocation | PROSE (slash commands are 5-line trampolines) |
| D9 | **kata-validate critics** | fresh-context `Agent` dispatches; METHOD-by-reference (LOCKED anti-dispatch rule, `kata-validate:96-110`) | PROSE |
| D10 | **Kill / reroll / re-dispatch** (M4 ladder) | host background-task stop + fresh `Agent` dispatch from checkpoint | PROSE + host primitive (`ADAPTER-CONTRACT-M4` (b)) |
| D11 | **Grill convergence passes** — kata-review fresh-context | `Agent` tool | PROSE |
| D12 | **THE BYPASS** — conductor dispatches designed work straight through the `Agent` tool with none of the above | host `Agent` tool, bare | The anti-surface. Proven live ×2 (burn-01, burn-02). Nothing observes it, nothing counts it, nothing can. |

## 2. Enforcement primitives that EXIST but are UNWIRED

| Primitive | What it enforces | Status |
|---|---|---|
| `build_brief` + `assert_frozen` (`kata_dispatch.py:43,76`) | **D169: no brief for a non-frozen plan** — required kwarg, fail-closed, first action | [VERIFIED] built, tested, **zero production callers** — transitively dead |
| `resolve_roles` + `HOST_ONLY_ROLES` (`kata_roles.py:85,46`) | role→platform routing fail-closed; orchestrator/evaluator host-only | [VERIFIED] zero callers. config.md advertises "validated fail-closed at preflight" — **nothing at preflight calls it** |
| `kata_models.resolve()` (~1300 lines) | dispatch-time model tiering, premium/advisor gates | [SWEPT] zero callers |
| `kata_config.validate_core_config` | mode/tiers/modules load-guard (D45) | [VERIFIED] zero non-test importers; **does NOT validate `roles` or `confirmedPlatforms`** — delegates to the resolver nothing calls |
| `kata_board.append_event/append_progress/write_state` | the board writer, single-writer state | [SWEPT] only caller is the dash demo simulator |
| `contract_gate.write_contract_gate` | gate-ran artifact | [SWEPT] producer-only; no Python reader; zero ever written in a real run |
| `escalation.py` | escalation payload builder/writer | [SWEPT] zero callers; `kata_dispatch.normalize` re-implements its source-required rule **by copy, not import** |
| `kata_preflight` (66 KB) | preflight gate; re-implements the builders table + runner *as deliberate copies* | [SWEPT] zero importers |
| `kata_settings.confirmed_platforms` (read side) | the designed reader of what `confirm_platform` writes | [SWEPT] write side live via installer; **read side dead** |
| telemetry suite (`kata_telemetry` 71 KB, usage_meter, recurrence_detect, validation_misses) | run accounting | [SWEPT] zero importers; `runId` exists only as a passthrough field no code produces |

## 3. Missing primitives — verified absences

| Absence | Evidence |
|---|---|
| **No run identity anywhere.** Board grammar is `<utc> \| <agent> \| <TYPE> \| <task> \| <msg>` — five fields, no run-id | [VERIFIED] `protocol/board.md:9`. BL-M34's fix direction *presumes* "board run-id" — the primitive does not exist |
| **No code launches a Claude worker.** `_COMMAND_BUILDERS = {codex, kiro}`; `confirm_platform("claude")` short-circuits to `{"confirmed": True, "detail": "host"}` without running anything; no `claude -p` anywhere | [VERIFIED] `kata_dispatch.py:171`; [SWEPT] `kata_install.py:533-535` |
| **No worktree provisioning code** — teardown only (`cleanup_stale_task`); creation is prose | [SWEPT] |
| **No agent definitions** (`adapters/claude/agents/` absent; every agent ever dispatched is a host-default shaped by its brief) | [SWEPT]; independently recorded in BL-N20 as verified 2026-08-16 |
| **No PreToolUse hook** — shipped hooks are SessionStart/PreCompact/UserPromptSubmit, all fail-soft by design ("never blocks" is a stated invariant of the gauge hook) | [VERIFIED] `settings.snippet.json`; [SWEPT] `kata-gauge-check.py:35-37` |
| The one identity primitive, `evidence_is_current`, checks **git-SHA freshness, not run membership**, and is reachable only from benchmark/debug tooling | [SWEPT] `run_result.py:122` |

## 4. Hard constraints any seam design inherits (recorded rulings + physics)

1. **D172 [VERIFIED]:** seam actions are engine-code surfaces under the Determinism Doctrine —
   "guaranteeing proper execution rather than requesting it." Minimal-Python preference relaxed here.
2. **D169 [VERIFIED]:** dispatch against a non-frozen plan BLOCKS, never warns.
3. **EDR-7 [VERIFIED]:** any token/record the judged agent can read off disk is **forgeable** — the
   evaluator has Read/Bash and is pointed at `.kata/`. A comparator that is prose is no comparator.
   The judge never certifies itself (EDR-1 survives its ledger's supersession as a principle).
4. **Isolated worktrees cannot read the main tree's `.kata/`** — advice must be INLINED VERBATIM
   into briefs (`protocol/escalation.md:74-77`). Any dispatch-context artifact has the same reach
   problem. [SWEPT]
5. **Plugin-shipped agents cannot carry `hooks`/`mcpServers`/`permissionMode`** — if the pack ships
   as a plugin, those enforcement levers are unavailable there; hooks install via settings instead
   (`kata_install --install-hooks` is live machinery). [SWEPT] agent-cadre RESEARCH-AGENTS.md
6. **BBM-11: headless must never block** on a human — bypass semantics must resolve fail-closed
   *without* requiring an interactive human in unattended shapes. [SWEPT]
7. **AC-1 / cross-cutting cadre ruling:** every agent is "loaded via the dispatch seam ONLY
   (BL-M33/M34)"; a bare host-default dispatch fails closed. The cadre DEPENDS on this seam. [SWEPT]
8. **Orchestrator roster row (agent-cadre):** "thin + code-seam-backed: the definition assumes the
   seam, never re-implements it in prose." [SWEPT]
9. **BBM-12 [VERIFIED via STATE/HANDOFF]:** burns run the ENTIRE loop; conductor-driven bypass is
   recorded DRIFT. The seam is the mechanism that retires this class.
10. **Kill-binding degradation precedent:** a platform missing a required primitive degrades LOUDLY
    to a weaker mode, never silently (`inlineEval` → `telemetry`). The house pattern for
    hosts-without-hooks. [SWEPT]

## 5. Candidate attach points for AUTHORITY (inventory only — the grill decides)

The operator's requirement: *"it needs some aspect of authority over everything the harness does."*
Ground truth offers exactly four physical places authority can live, with different reach:

| Attach point | What it can mechanically do | Reach & limits |
|---|---|---|
| **A. The Python engine as the only door** — extend `kata_dispatch` so every dispatch (host included) is a function call that mints/validates run context | real chokepoint for everything routed through it; wires the orphan layer (assert_frozen, resolve_roles, resolve, board writer, roster) in one move | code called by prose can still be *walked around* — the bypass class survives unless something external checks or intercepts |
| **B. Host hook interception — a PreToolUse-class hook on the `Agent` tool** that fails closed unless valid run context exists | the ONLY mechanism that can mechanically intercept an in-process `Agent` dispatch on the Claude host; exit-2/deny blocks the call | per-host capability (Claude: real; Kiro: PreToolUse exists per PLATFORM-MATRIX with a risk flag; Codex: assess); needs installing (live machinery exists: `--install-hooks`); **capability must be probed, not assumed** (the UX-28 discipline). Breaks the all-hooks-fail-soft precedent — deliberately |
| **C. The wrapper door (UX-28/BL-N21)** — env provisioner that installs/verifies the hook + config before the host starts | makes B's presence a launch invariant; the enforcing door for always-loop | zero code today; wrapper can be skipped (in-session doors remain by ruling — "no door is removed") |
| **D. Post-hoc identity verification** — extend `evidence_is_current`-class checks so gates/evaluators refuse artifacts that lack seam-minted run identity | catches a bypass *after the fact* at the next gate; no host dependency | detection, not prevention; and today's verifier of gate evidence is itself partly prose (BL-X11) |

These compose rather than compete — A mints authority, B enforces it at the host boundary, C
provisions B, D audits it — but **which are in BL-M33's scope vs. M34's vs. later is a grill
decision, not a map fact.**

## 6. Blast radius of any seam build

- `kata-orchestrate/SKILL.md` — ~52 launch sites; every one either routes through the seam or is
  explicitly exempted. The largest single rewrite surface. [SWEPT]
- The dispatched-target skills that declare inbound launch contracts (kata-evaluate, kata-inline-eval,
  kata-advise, kata-research, kata-tdd, authors) — their "how I am launched" sections change. [SWEPT]
- `protocol/board.md` grammar if run identity lands there (clause-pinned + fingerprinted —
  a deliberate two-step re-approval). [VERIFIED]
- `protocol/config.md` if a seam/enforcement key lands (registry, fingerprint-exempt). [VERIFIED]
- `docs/DETERMINISM-DOCTRINE.md` scope statement gains loop-execution language when the program
  builds (named in D172 as a deliberate two-step). [VERIFIED]
- The stale `tools/kata_dispatch.py` line anchors cited across five skills (`:42`/`:177`/`:199` vs
  actual `:43`/`:219`) — whatever the design, the citations are already wrong and ride along. [SWEPT]
