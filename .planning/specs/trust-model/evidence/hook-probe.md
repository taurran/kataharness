# Evidence — hook capability probe (Claude host, Windows)

**Task:** `tm-w1-hook-capability-probe` (Trust Model burn, wave 1, research class).
**Serves:** DESIGN §1.7 (per-host interception + degrade table), §1.8 (deny and park semantics),
§8 S3. **Consumed by:** wave 8 `hook-activation`.
**Discipline:** UX-28 — assess, never assume. Every "Answer" below is an OBSERVED result with a
reproducible transcript. Where a question was not settled by observation it is labelled
INCONCLUSIVE or NOT PROBED and is *not* answered.

> **SCOPE, stated up front (PD-2).** This probe covers **the Claude Code host on THIS machine
> (Windows 11) only**, at the versions pinned below, in **headless `claude -p` sessions**.
> **Kiro interception is UNPROBED** ⇒ per **BL-N25** it must be planned as **detection-only,
> Honor-system declared**. Codex interception is likewise UNPROBED. No result here may be
> generalised to another host, another OS, or another Claude Code version without re-probing.

---

## 0. Environment — exact versions

| Component | Version |
|---|---|
| Claude Code | **2.1.233** (`claude --version` → `2.1.233 (Claude Code)`) |
| OS | Microsoft Windows 11 Pro **10.0.26200.0** |
| Node | v24.14.1 |
| Hook interpreter | `C:/Dev/Projects/KataHarness/tools/.venv/Scripts/python.exe` → Python **3.14.3** |
| git | 2.53.0.windows.2 |
| Worktree HEAD at probe time | `08ce3dac0a8fbed77c9f9c8e25331b7b4cb438b3`, branch `task/tm-w1-hook-capability-probe` |
| Probe date | 2026-08-16 |

**Model used in probe sessions:** `claude-haiku-4-5-20251001` (`--model haiku`), chosen for cost.
Hook dispatch is a host-level code path, not a model behaviour, so the model choice is not
believed to be load-bearing — but it was not varied, so that is an assumption, not a result.

---

## 1. Method — the scratch harness (reproducible)

All scaffolding lives **outside the repo tree** and is **not committed**:

```
C:\dev\projects\_kata_wt\trust-model\_probe-scratch\
├── hooklog.py                # the probe hook: logs stdin verbatim, then acts per mode
├── bin/{codex,kiro-cli}      # harmless echo stand-ins for the dispatch CLIs
├── logs/                     # captured hook payloads + full session streams
├── p1a-exit2/.claude/settings.json      # PreToolUse Agent -> exit 2
├── p1b-jsondeny/.claude/settings.json   # PreToolUse Agent -> JSON permissionDecision deny
├── p1c-agentonly/, p1c-taskonly/        # matcher-grammar isolation
├── p2-capture/                          # Pre+Post on Agent, Pre on Bash
├── p3-bash/                             # PreToolUse Bash visibility
├── p4-substop/                          # SubagentStop / Stop / Notification, sync agent
├── p5-async/                            # same, background (async) agent
├── p6-timeout/                          # hook stalls 8s against a 2s timeout
├── p7-nested/                           # deny a subagent-initiated Bash call
└── p8-crash/                            # hook raises -> exit 1
```

`hooklog.py` (the whole probe hook — reproduced so the transcripts below are verifiable):

```python
"""Scratch probe hook: log stdin verbatim, then optionally deny.

Usage: hooklog.py <logfile> <mode>
  mode = observe   -> log, exit 0 (transparent)
  mode = exit2     -> log, write deny reason to stderr, exit 2
  mode = jsondeny  -> log, emit hookSpecificOutput permissionDecision=deny, exit 0
  mode = crash     -> log, raise RuntimeError -> exit 1 + traceback
  mode = slowdeny  -> log, sleep 8s, then exit 2
"""
```

Each probe was run as, from inside the probe project directory:

```bash
claude -p "$(cat ../<probe>-prompt.txt)" \
  --setting-sources project \
  --model haiku \
  --dangerously-skip-permissions \
  --output-format stream-json --include-hook-events --verbose \
  < /dev/null > ../logs/<probe>-stream.jsonl 2>&1
```

Two harness notes that matter for reproduction:

- **`--setting-sources project`** isolates the probe from the operator's global
  `~/.claude/settings.json` (which already carries unrelated hooks). Without it the global hook
  set also fires and pollutes the transcript.
- **`--include-hook-events` with `--output-format stream-json`** emits `hook_started` /
  `hook_response` system events carrying the hook's `exit_code`, `stdout`, `stderr` and
  `outcome`. This is the primary evidence channel — it shows what the *host* concluded, not just
  what the hook wrote.
- `< /dev/null` avoids a 3s "no stdin data received" stall.

---

## 2. Probe 1 — PreToolUse deny edge on the `Agent` tool

**Question (DESIGN §1.7 TM-B2.1 / §1.8 TM-B5):** can a PreToolUse-class hook on the Claude Code
host **DENY** an `Agent` tool call (fail-closed), and does the deny message reach the model?

### 2.1 Answer — **OBSERVED: YES, both deny forms work, and the model sees the reason.**

Settings (`p1a-exit2/.claude/settings.json`, matcher `Agent|Task`, mode `exit2`), prompt
(`p1-prompt.txt`):

```
Use the Agent tool to launch a general-purpose subagent whose entire task is: "Reply with
exactly the text SUBAGENT_OK and nothing else." Do not do the work yourself and do not use any
other tool. After the subagent returns (or fails), reply with one line describing exactly what
happened.
```

**Verbatim payload the hook received** (`logs/p1a-pre.log`):

```json
{"session_id":"7ec3966e-46ce-4d3c-bbed-e66061b38ae5","transcript_path":"C:\\Users\\taurr_nvs748q\\.claude\\projects\\C--dev-projects--kata-wt-trust-model--probe-scratch-p1a-exit2\\7ec3966e-46ce-4d3c-bbed-e66061b38ae5.jsonl","cwd":"C:\\dev\\projects\\_kata_wt\\trust-model\\_probe-scratch\\p1a-exit2","prompt_id":"b18e69a8-a940-45b6-9af0-69bc5a684a4a","permission_mode":"bypassPermissions","hook_event_name":"PreToolUse","tool_name":"Agent","tool_input":{"description":"Test subagent response","prompt":"Reply with exactly the text SUBAGENT_OK and nothing else.","subagent_type":"general-purpose"},"tool_use_id":"toolu_01UEa9o2VeL6D34z3qioaZ8G"}
```

Payload keys: `["cwd","hook_event_name","permission_mode","prompt_id","session_id","tool_input","tool_name","tool_use_id","transcript_path"]`

**Verbatim host verdict** (`logs/p1a-stream.jsonl`, event 11):

```json
{"type":"system","subtype":"hook_response","hook_id":"8d7d05a4-70b8-44e5-ac5f-984d47898080","hook_name":"PreToolUse:Agent","hook_event":"PreToolUse","output":"KATA-PROBE-DENY: this Agent launch carries no valid dispatch record. Legal path: mint a record via the seam engine first.","stdout":"","stderr":"KATA-PROBE-DENY: this Agent launch carries no valid dispatch record. Legal path: mint a record via the seam engine first.","exit_code":2,"outcome":"error",...}
```

**Verbatim tool result handed back to the model** (event 12):

```json
{"type":"user","message":{"role":"user","content":[{"type":"tool_result","content":"PreToolUse:Agent hook error: [\"C:/Dev/Projects/KataHarness/tools/.venv/Scripts/python.exe\" \"...hooklog.py\" \"...p1a-pre.log\" exit2]: KATA-PROBE-DENY: this Agent launch carries no valid dispatch record. Legal path: mint a record via the seam engine first.","is_error":true,"tool_use_id":"toolu_01UEa9o2VeL6D34z3qioaZ8G"}]},...,"tool_result_meta":[{"id":"toolu_01UEa9o2VeL6D34z3qioaZ8G","non_execution_kind":"permission-rule"}]}
```

**Result envelope:**

```json
"permission_denials":[{"tool_name":"Task","tool_use_id":"toolu_01UEa9o2VeL6D34z3qioaZ8G","tool_input":{"description":"Test subagent response","prompt":"Reply with exactly the text SUBAGENT_OK and nothing else.","subagent_type":"general-purpose"}}]
```

The model's own final line: *"The subagent launch was blocked by a hook that requires a valid
dispatch record to be minted via the seam engine before the Agent tool can proceed."*

**The subagent never ran.** The `PostToolUse` hook registered on the same matcher in the same
settings file **did not fire at all** — `logs/p1a-post.log` was never created. Denial is
therefore clean: no half-executed launch, no post-edge record for a call that did not happen.

### 2.2 The JSON deny form — **OBSERVED: works, and produces a cleaner model-facing message**

`p1b-jsondeny`, hook prints and exits 0:

```json
{"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny", "permissionDecisionReason": "KATA-PROBE-JSONDENY: no valid dispatch record; mint via the seam engine first."}}
```

Host verdict (`logs/p1b-stream.jsonl`): `"exit_code": 0, "outcome": "success"` — and the call was
**still blocked**:

```json
{"type":"user","message":{"role":"user","content":[{"type":"tool_result","content":"KATA-PROBE-JSONDENY: no valid dispatch record; mint via the seam engine first.","is_error":true,"tool_use_id":"toolu_019rw2CUKhxGtgqtUgEHySDz"}]},...,"tool_result_meta":[{"id":"toolu_019rw2CUKhxGtgqtUgEHySDz","non_execution_kind":"permission-rule"}]}
```

**Design consequence.** Both forms fail-closed. The **JSON form is the better choice for the
wave-8 hook**: the model receives *only* the `permissionDecisionReason` string, whereas the
`exit 2` form wraps it in `PreToolUse:Agent hook error: [<full interpreter and script command
line>]: <reason>` — leaking the hook's absolute paths into the model's context and burying the
"legal path" sentence behind noise. DESIGN §1.8 requires the deny message to *name the legal
path*; the JSON form delivers that sentence verbatim and nothing else.

### 2.3 Enforcement survives the most permissive mode — **OBSERVED**

Every probe ran under `--dangerously-skip-permissions`; every hook payload carries
`"permission_mode":"bypassPermissions"`; the deny still held. **Hooks are not bypassed by
permission-skipping.** This is load-bearing for BBM-11 unattended shapes, which run permissive.

### 2.4 Matcher grammar — **OBSERVED, with a trap**

| Settings matcher | Hook fired? | `hook_name` reported | `tool_name` in payload |
|---|---|---|---|
| `Agent\|Task` | yes | `PreToolUse:Agent` | `"Agent"` |
| `Agent` | yes | `PreToolUse:Agent` | `"Agent"` |
| `Task` | **yes** | `PreToolUse:Agent` | **`"Agent"`** |

**The quirk wave 8 must not step in:** the subagent tool is **aliased**. The session `init` event
lists it as `"Task"` in its `tools` array; the `result` envelope reports denials as
`"tool_name":"Task"`; but the **hook payload always says `tool_name: "Agent"`**, and the matcher
accepts *either* spelling. Therefore:

- Matching on `Task` alone **does** fire the hook (verified, `logs/p1c-taskonly-pre.log`).
- A hook that matches `Task` and then asserts `payload["tool_name"] == "Task"` will **silently
  no-op on every call** — an enforcement layer that looks installed and enforces nothing. This is
  exactly the fail-open shape §8 warns about.
- **Recommendation:** register matcher `Agent|Task` (belt and braces against a future rename) and
  branch on `tool_name in {"Agent", "Task"}`, never on a single spelling.

### 2.5 The dispatch payload is fully visible to the hook — **OBSERVED**

`tool_input` carries `description`, the **entire `prompt` string**, `subagent_type`, and (when the
model sets it) `run_in_background`. A wave-8 hook can therefore read the worker brief itself to
find or validate a dispatch-record token, without any side channel. `tool_use_id` is present and
is the correlation key to the post edge (§3.4).

---

## 3. Probe 2 — PostToolUse capture edge

**Question (DESIGN §1.7 R-H3):** can a PostToolUse-class hook read the returning tool result —
specifically the **first line of a subagent's return envelope**?

### 3.1 Answer — **OBSERVED: YES, but ONLY on the synchronous path. The async path returns a handle, not content.** This is a conditional the design must carry.

### 3.2 Synchronous agent (`run_in_background: false`) — content IS delivered

`p4-substop`, prompt asked the model to *wait* for the subagent; the model issued
`run_in_background: false`. Verbatim PostToolUse payload (`logs/p4-post-agent.log`):

```json
{"session_id":"a99836aa-1d09-4c39-b645-6f0132ff105c","cwd":"C:\\dev\\projects\\_kata_wt\\trust-model\\_probe-scratch\\p4-substop","permission_mode":"bypassPermissions","hook_event_name":"PostToolUse","tool_name":"Agent","tool_input":{"description":"Test subagent response format","prompt":"Reply with exactly two lines and nothing else. Line 1: VERDICT: PASS. Line 2: evidence: none.","subagent_type":"general-purpose","run_in_background":false},"tool_response":{"status":"completed","prompt":"Reply with exactly two lines and nothing else. Line 1: VERDICT: PASS. Line 2: evidence: none.","agentId":"ac948bb64ceb7bfdb","agentType":"general-purpose","content":[{"type":"text","text":"VERDICT: PASS.\nevidence: none."}],"resolvedModel":"claude-haiku-4-5-20251001","totalDurationMs":2049,"totalTokens":16629,"totalToolUseCount":0,"usage":{...}},"tool_use_id":"toolu_01LpCqV4GrM6kxn1c9guh7G5","duration_ms":2050}
```

`tool_response.content[0].text` is the **complete return envelope**, `\n`-joined, with
**`VERDICT: PASS.` as the first line** — exactly what R-H3 needs. Also free: `agentId`,
`agentType`, `resolvedModel`, `totalDurationMs`, `totalTokens`, `totalToolUseCount`, and the full
token `usage` block.

### 3.3 Asynchronous / background agent — content is NOT delivered

`p2-capture` (model omitted `run_in_background`) and `p5-async` (model set
`run_in_background: true`) both produced a PostToolUse fire **~4 ms after launch**, carrying only
a handle. Verbatim (`logs/p5-post-agent.log`):

```json
"tool_response":{"isAsync":true,"status":"async_launched","agentId":"a794c33fb3386dec1","description":"Background task verification","resolvedModel":"claude-haiku-4-5-20251001","prompt":"Reply with exactly one line and nothing else: VERDICT: PASS_ASYNC","outputFile":"C:\\Users\\TAURR_~1\\AppData\\Local\\Temp\\claude\\C--dev-projects--kata-wt-trust-model--probe-scratch-p5-async\\a3b676e6-10ef-45bb-ba59-ff2d00d756bd\\tasks\\a794c33fb3386dec1.output","canReadOutputFile":true},"tool_use_id":"toolu_01W9eW2BSypEWjf1iFiv6Ez9","duration_ms":4}
```

There is **no `content` key** — `status` is `async_launched`, not `completed`. A wave-8 post-edge
hook that reads `tool_response.content` unconditionally would capture **nothing** on every
background dispatch and would have no way to tell that from an empty verdict.

The advertised `outputFile` was **empty (0 bytes)** when inspected after the session ended, so
"read the outputFile from the PostToolUse hook" is **not** a working substitute — the file does
not yet hold the return at the moment the hook fires, and in this probe it never did.

> **In the `p2-capture` run the model omitted `run_in_background` entirely and the host still
> launched async** (`isAsync: true`). Observed once. Do **not** encode "absent ⇒ synchronous".

### 3.4 `SubagentStop` — the capture edge that works on BOTH paths — **OBSERVED**

A `SubagentStop` hook fired on subagent completion in the sync run **and** the async run, in both
cases carrying the return text. Verbatim, async run (`logs/p5-substop.log`):

```json
{"session_id":"a3b676e6-10ef-45bb-ba59-ff2d00d756bd","cwd":"...\\p5-async","permission_mode":"bypassPermissions","agent_id":"a794c33fb3386dec1","agent_type":"general-purpose","hook_event_name":"SubagentStop","stop_hook_active":false,"agent_transcript_path":"C:\\Users\\taurr_nvs748q\\.claude\\projects\\C--dev-projects--kata-wt-trust-model--probe-scratch-p5-async\\a3b676e6-10ef-45bb-ba59-ff2d00d756bd\\subagents\\agent-a794c33fb3386dec1.jsonl","last_assistant_message":"VERDICT: PASS_ASYNC","background_tasks":[{"id":"a794c33fb3386dec1","type":"subagent","status":"running","description":"Background task verification","agent_type":"general-purpose"}],"session_crons":[]}
```

and sync run (`logs/p4-substop.log`): `"last_assistant_message":"VERDICT: PASS.\nevidence: none."`,
`"agent_id":"ac948bb64ceb7bfdb"`.

`last_assistant_message` is the verdict text, first line included. `agent_transcript_path` points
at the subagent's own JSONL for deeper forensics.

**The correlation chain wave 8 should build on (all three links observed):**

```
PreToolUse(Agent)   tool_use_id ──┐
                                  ├─ same tool_use_id
PostToolUse(Agent)  tool_use_id ──┘  and tool_response.agentId ──┐
                                                                 ├─ same id
SubagentStop        agent_id ────────────────────────────────────┘
                    + last_assistant_message  (the VERDICT line)
```

**Note the gap:** `SubagentStop` carries `agent_id` but **no `tool_use_id`**. So the post edge is
still required — it is the only event that binds `tool_use_id` ↔ `agentId`. **Both hooks are
needed**; neither alone closes the loop.

**Recommended wave-8 capture design (from these observations, not assumed):** bind identity at
`PostToolUse` (always available, both paths), and take the verdict text from `SubagentStop`
`last_assistant_message` (always available, both paths). Do **not** make the capture depend on
`PostToolUse.tool_response.content`, which exists only on the sync path.

### 3.5 Hooks fire for subagent-initiated tool calls — **OBSERVED**

`p2-capture` registered PreToolUse on `Bash`; the *subagent* ran the echo. The hook fired
(`logs/p2-bash-pre.log`) with two extra keys the parent-initiated payloads do not have:

```json
"agent_id":"a86ba01cf8172f8de","agent_type":"general-purpose","hook_event_name":"PreToolUse","tool_name":"Bash","tool_input":{"command":"echo SUBAGENT_INNER_BASH_MARKER","description":"Run test command"}
```

So a hook can **distinguish parent-initiated from subagent-initiated calls** by the presence of
`agent_id` / `agent_type`. Useful for governor-ladder scoping (a worker must not be able to
mint its own dispatch).

---

## 4. Probe 3 — Bash-leg visibility (`codex exec` / `kiro-cli chat` shapes)

**Question (DESIGN §1.7 TM-B2.2):** what can a PreToolUse hook on the `Bash` tool see of a
dispatch-shaped command line?

**Answer — OBSERVED: the full, verbatim, untruncated command string, exactly as the model issued
it, in `tool_input.command`.**

Verbatim captures (`logs/p3-pre.log`), harmless stand-ins:

```json
"tool_input":{"command":"codex exec --model o3 --cd /c/scratch/wt \"implement task w1-foo per the frozen PLAN; return VERDICT on line 1\" || true","description":"Run first command with error handling"}
```
```json
"tool_input":{"command":"kiro-cli chat --no-interactive --trust-all-tools \"implement task w1-foo per the frozen PLAN\" || true","description":"Run second command with error handling"}
```
```json
"tool_input":{"command":"PATH=\"C:/dev/projects/_kata_wt/trust-model/_probe-scratch/bin:$PATH\" codex exec --model o3 \"indirection check\"","description":"Run third command with PATH modification"}
```

**Truncation check — OBSERVED: none at 1468 characters.** A single realistic dispatch command of
**1468 chars** (a `codex exec --dispatch-record dr-0001 "<~1.3 KB worker brief>"`) was issued;
the string the model emitted in the stream and the string the hook received were compared
programmatically:

```
ISSUED len = 1468
HOOK-SAW lens = [1468]
BYTE-IDENTICAL: True
HOOK TAIL: 'n the full suite before returning; return VERDICT on line 1 followed by the evidence block;" || true'
```

No truncation limit was found. **INCONCLUSIVE above ~1.5 KB** — a limit may exist further out; it
was not searched for. Wave 8 should not assume unlimited length for a multi-KB inlined brief.

### 4.1 What the Bash leg **cannot** see — the honest residual, now with evidence

The hook receives the **pre-execution literal string**, not the command that actually runs. Two
observed consequences:

- **Shell expansion is invisible.** `echo LONGARG_START $(printf 'A%.0s' $(seq 1 3000)) LONGARG_END`
  reached the hook as that 63-character literal; the 3000-character expansion the shell produced
  was never visible to the hook.
- **Indirection defeats shape-matching.** The `PATH="...bin:$PATH" codex exec ...` form still
  contains the literal token `codex exec` and would be caught, but nothing observed here would
  stop `eval "$(printf '\x63odex exec ...')"`, a wrapper script, or an alias from executing the
  same dispatch while presenting a command string that matches no pattern.

This **confirms DESIGN §1.7's stated residual as observed fact, not caution**: the Bash leg is
best-effort and evadable by indirection. Its run-start declaration must be **Partially verified**,
never "intercepting". **Only the Agent-tool leg may claim interception** — and only subject to §5.

---

## 5. LIMITS — the fail-open findings. Read before designing wave 8.

### 5.1 A hook that TIMES OUT fails **OPEN** — **OBSERVED**

`p6-timeout`: PreToolUse on `Agent`, `"timeout": 2`, hook sleeps 8 s then would exit 2.

Host verdict (`logs/p6-stream.jsonl`):

```json
{"type":"system","subtype":"hook_response","hook_id":"de1e1ea3-92f1-4324-a1b6-f52367672ed3","hook_name":"PreToolUse:Agent","hook_event":"PreToolUse","output":"","stdout":"","stderr":"","exit_code":1,"outcome":"cancelled",...}
```

**The Agent call then PROCEEDED.** The subagent ran and returned `VERDICT: PASS\nevidence: none`;
`permission_denials` was empty. The hook process was killed at the timeout (the `SLOWDENY: woke
after 8s` breadcrumb never appears in `logs/p6-pre.log`), so the intended `exit 2` never
happened. A timeout is reported as `exit_code: 1, outcome: "cancelled"` — **and exit 1 does not
block.**

### 5.2 A hook that CRASHES fails **OPEN** — **OBSERVED**

`p8-crash`: PreToolUse on `Agent` raises `RuntimeError`.

```json
{"type":"system","subtype":"hook_response","hook_name":"PreToolUse:Agent","hook_event":"PreToolUse","output":"Traceback (most recent call last):\r\n  File \"C:\\dev\\projects\\_kata_wt\\trust-model\\_probe-scratch\\hooklog.py\", line 33, in <module>\r\n    raise RuntimeError(\"KATA-PROBE-CRASH: enforcement hook is broken\")\r\nRuntimeError: KATA-PROBE-CRASH: enforcement hook is broken\r\n","stderr":"...","exit_code":1,"outcome":"error",...}
```

Result: `is_error: false`, `permission_denials: []`, model result `'VERDICT: PASS'` — **the
subagent ran.**

### 5.3 The rule these two findings establish

> **Only a clean `exit 2`, or a clean `exit 0` carrying a valid `permissionDecision: "deny"` JSON
> object, blocks a tool call. EVERY other outcome — timeout, crash, missing interpreter,
> malformed JSON, non-zero-but-not-2 — lets the call through, and the host reports it as a
> non-fatal hook error the operator may never look at.**

This is the sharpest constraint on DESIGN §1.7's claim that the hook *"fail-closes any `Agent`
call lacking a valid record"*. That property is **conditional on the hook itself never failing**.
Concretely, wave 8 must:

1. **Deny on internal error, not just on missing record.** Wrap the whole hook body; any
   exception path must still emit a deny and `exit 2` / deny-JSON rather than propagate. This is
   the deliberate inversion of the `kata-gauge-check.py:34-36` fail-soft precedent (which is
   correct *there* — a `UserPromptSubmit` exit 2 erases the user's prompt — and wrong here).
2. **Set a generous explicit `timeout`** and keep the hook's work trivially cheap (no network, no
   subprocess, no repo walk that can block on a lock). Note the timeout kill is silent to the
   model: `output`, `stdout` and `stderr` all come back empty.
3. **Treat the post-hoc verification leg as mandatory, not belt-and-braces.** A run whose hook
   silently died has no denial record and no cursor DENY event; only the §5 three-way join and the
   §5.4 provenance drift check can catch it after the fact.
4. **Probe the tripwire at run start and derive the Guardian grade from it** (§1.7 degrade table
   already says this): a deny-tripwire that returns *no result* must land on **Dormant**, never
   inherit a prior "Verified". These findings are why that clause is load-bearing rather than
   pedantic — a broken hook is indistinguishable from an absent one from inside the session.

### 5.4 Other limits and non-results, stated honestly

- **Interactive sessions NOT PROBED.** Every run was headless `claude -p`. Hook dispatch is
  believed to be the same host code path, but that is an inference. See Human Moments.
- **Only `--model haiku` was exercised.** Model was not varied.
- **`--setting-sources project` was used throughout**, so these results describe hooks loaded
  from a **project** `.claude/settings.json`. Loading from user or local scope was NOT probed;
  DESIGN's scope gate (§8 RS-L5, the run marker) is the mechanism that would make a global
  install safe, and it was NOT exercised here.
- **Settings-drift detection NOT probed** (§1.7 "settings drift is detected at seam init").
- **Denial of an `Agent` call issued *by a subagent* (nested) was NOT directly probed.** What
  *was* probed (`p7-nested`) is that a PreToolUse deny **does** apply to a **subagent-initiated
  `Bash`** call: `permission_denials: [{"tool_name":"Bash","tool_use_id":"toolu_01SU6KMwhTQE6MzW1jzqE1pZ","tool_input":{"command":"echo NESTED_BASH_MARKER",...}}]`, and the
  subagent reported back `RAN=no`. Since the interception path is the same PreToolUse dispatch and
  the payload carries `agent_id`, nested `Agent` deny is *expected* to work — but that is an
  inference, **not an observation**. Wave 8 should add it to the tripwire suite.
- **Windows only.** Path handling (backslash-escaped JSON, `TAURR_~1` 8.3 short paths in the
  async `outputFile`, `\r\n` line endings in hook stdout/stderr) is Windows-shaped. A POSIX host
  was not probed.
- **No result here says anything about Kiro or Codex.** See scope banner.

---

## 6. Answers, one line each (for the wave-8 design inputs)

| # | Question | Verdict | Answer |
|---|---|---|---|
| 1 | Can a PreToolUse hook DENY an `Agent` call? | **OBSERVED** | Yes. `exit 2` and `permissionDecision: "deny"` both block; the subagent does not run; PostToolUse does not fire; the deny reason reaches the model verbatim. Use the JSON form. |
| 1b | Does deny survive `--dangerously-skip-permissions`? | **OBSERVED** | Yes. All probes ran under `bypassPermissions` and the deny held. |
| 1c | Matcher grammar | **OBSERVED** | `Agent`, `Task`, and `Agent\|Task` all match; the payload always says `tool_name: "Agent"`. Never assert a single spelling. |
| 2 | Can a PostToolUse hook read the subagent return envelope's first line? | **OBSERVED, CONDITIONAL** | Yes on the **sync** path (`tool_response.content[0].text`). **No** on the async/background path (handle only: `agentId` + an empty `outputFile`). |
| 2b | Is there an edge that works on both paths? | **OBSERVED** | Yes — `SubagentStop.last_assistant_message`, plus `agent_id`. Pair it with PostToolUse for the `tool_use_id` ↔ `agentId` binding. |
| 3 | What can a Bash PreToolUse hook see of `codex exec` / `kiro-cli chat`? | **OBSERVED** | The full verbatim pre-expansion command literal, untruncated to at least 1468 chars. It cannot see shell expansion, and shape-matching is evadable by indirection ⇒ **Partially verified**, never "intercepting". |
| 4 | Do hooks fire for subagent-initiated tool calls? | **OBSERVED** | Yes, with `agent_id` + `agent_type` added to the payload; deny applies to them too (verified on `Bash`). |
| 5 | Does a timed-out or crashed enforcement hook fail closed? | **OBSERVED** | **No — it fails OPEN.** Only clean `exit 2` / deny-JSON blocks. This is the governing limit on the whole enforcement claim. |
| 6 | Kiro / Codex interception? | **UNPROBED** | Detection-only, **Honor-system declared**, per BL-N25. |
| 7 | Interactive-session behaviour? | **NOT PROBED** | Headless only. Escalated as a Human Moment. |

---

## 7. HUMAN MOMENTS — escalated, not fabricated

1. **Interactive-session confirmation.** Everything above was observed in headless `claude -p`.
   Confirming the deny edge and the `SubagentStop` capture edge behave identically in a normal
   interactive session needs an operator at a terminal. Low expected risk (same host code path),
   but it is an inference and the enforcement layer rests on it. Suggested check: install the
   wave-8 hook, open an interactive session, ask for a record-less subagent launch, confirm the
   deny renders and the run continues.
2. **Kiro host probe.** Requires the operator's Kiro environment; not available here. Until then
   BL-N25 stands: **detection-only, Honor-system**.
3. **Global-scope install.** These probes loaded hooks from project scope only. Before shipping a
   user-scope hook, the §8 RS-L5 run-marker scope gate must be exercised for real so non-kata
   sessions are provably untouched — the `kata-gauge-check.py` scope gate is the existing
   precedent to reuse.

---

## 8. Reproducing this probe

The scratch harness is deliberately **not committed** (probe scaffolding, not product). To
rebuild it: create the tree in §1, write `hooklog.py` with the four modes, write one
`.claude/settings.json` per probe registering the relevant event/matcher, and run the
`claude -p ...` invocation in §1 from inside each probe directory. Every transcript quoted above
is a verbatim excerpt of `logs/<probe>-{pre,post,substop,stream}.{log,jsonl}` produced by exactly
those commands on 2026-08-16 against Claude Code 2.1.233.
