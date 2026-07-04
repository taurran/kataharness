# DETAILED HANDOFF — M4 session: the inline evaluator/reroll, executed to FINAL STATE (v0.2.0)

> **Paste-companion for a fresh coding-agent window (anchor: Fable 5).** This brief carries (1) the full
> derivation behind M4, (2) exactly what was learned from DeepSeek DSpark and what was rejected, (3) the
> complete ingest list the session must load for this to work effectively, and (4) the execution recipe to
> the operator-defined FINAL STATE — with the anti-surprise discipline that is now a standing order.
> The DESIGN under execution: **`.planning/specs/inline-eval-m4/DESIGN.md`** (draft-pending-grill-and-gate;
> proposed LOCKED M4-L1..L10). ⚠️ IGNORE `C:\Dev\CLAUDE.md` (unrelated "Mise" project).

---

## 0. STANDING ORDERS FROM THE OPERATOR (verbatim intent — these override convenience)

1. **No more "oops" surprises.** Before claiming anything exists, was built, or shipped: cite the artifact
   (file, commit, D-record, gate output). The last surprise was believing M4 was already shipped when only
   its SUBSTRATE existed — the WHAT-IS-BUILT table in §2 exists to make that class of confusion impossible.
   If you are not certain a thing exists, grep/read before you speak.
2. **No premature "completed!" celebrations.** "Done" requires, in the same message: the gate numbers
   (pytest / validator / Snyk / mutation proofs), the D-record reference, and the merged SHA. Anything less
   is "in progress." A phase is complete when its FINAL-STATE checklist row (§7) is checkable, not before.
3. **The mini loop ships INTACT and SHARPENED**: corrective action at chunk level so the OUTER loop runs
   measurably fewer times (fewer gate rejections + fix cycles). That outcome — not "inline evals ran" —
   is the milestone's success metric (M4-L1).
4. **Cross-model enabled + ACP compatible are requirements, not aspirations** (§5). If a design choice
   would work only for same-session Claude subagents, it is wrong.
5. **Execute while Fable is the anchor.** Judgment/grill/gates at anchor; build workers tier down (D131).

---

## 1. WHAT WE DERIVED (the reasoning the DESIGN encodes — do not re-derive, do not drop)

**The economics that shape everything.** DSpark's verifier is a free parallel forward pass; ours is a paid
LLM call that costs roughly as much as the work it judges. DSpark started from a 45.7% draft-acceptance
baseline; our first-pass task gate acceptance is historically ~85% (Kenjiri 14/14 with 1 fix cycle; P2
build 5/5). Consequences, quantified:
- Addressable waste pool ≈ **7%** of run tokens (≈15% task failure rate × ≈0.5C fix-loop cost).
- Failure-salvage alone (catch mid-task, reroll suffix) ≈ **1.5–2% tokens** — real but NOT the payoff.
- **The dominant lever is second-order:** a mid-task safety net lets planned task size safely grow ~1.5×,
  deleting per-task fixed overhead (dispatch context, worktree, gate ceremony) → **~5–10% tokens**.
  This is the harness analog of DSpark's actual win (+30% accepted draft LENGTH, not cheaper checks).
- **Wall-clock gains more than tokens** because the end-of-task failure path is serial (finish → gate →
  diagnose → re-dispatch → re-gate) and failures concentrate in long tasks: **~10–20% typical,
  25–35% on long-task/failure-heavy runs.**
- **The spiral case is real and quantified:** fixed-cadence mid-task LLM evaluation ≈ −40..−100% tokens
  (judging a green chunk costs ~a chunk). Every M4 mechanism is therefore EVENT-TRIGGERED with a
  zero-cost happy path (M4-L1). This is the single most important constraint in the milestone.
- All numbers are estimates from 3 unmeasured parameters (acceptance rate, failure-type mix, trigger
  precision) — which is WHY telemetry ships first (M4-L10) and the milestone carries a kill-switch:
  if P0 data says break-even can't be cleared, STOP at P0, keep the telemetry, shelve the mechanism.

**The corrective-action ladder (operator-directed shape, M4-L5):** trigger → economy-tier inline eval on
the CHUNK (continue / correct-note / reroll) → auto-reroll #1 from the last good commit (orchestrator-
resolvable, board-logged) → **trigger #2 ⇒ GROUNDING PASS against the frozen plan + a tightened task
brief BEFORE reroll #2** (repeated failure is evidence the SPEC may be the defect; plan defects route
through the supersede path, never silently patched) → trigger #3 ⇒ human-required. Mirrors the thrash
valve and liveness ladder; the final gate runs unchanged regardless (M4-L8 lossless invariant).

**The model-matrix finding (M4-L7):** the current tiering (anchor = judgment, economy = build) has the
RIGHT shape — it independently converged with speculative decoding's economics — but is role-static with
no feedback loop. M4 adds the loop: acceptance telemetry per (task-class × tier), report-and-recommend
routing adjustments (NO automatic tier mutation in v1 — that would be a D131 resolver behavior change
needing its own gate). The inline evaluator itself runs at **anchor −1, never anchor** — anchor-tier
inline eval is the overhead spiral wearing a badge.

## 2. WHAT IS AND IS NOT BUILT (the anti-surprise truth table — verify, don't trust)

| Thing | Status | Evidence |
|---|---|---|
| PROGRESS heartbeat + slack fields (F3) | **BUILT** (Milestone 1) | `protocol/board.md`, orchestrate dispatch template; D137-L5 |
| Per-file hash stamping (F5, "M4 evidence substrate") | **BUILT** | `tools/footprint.py::file_content_hashes`; D137-L4 |
| Checkpoint commits + `Kata-Task:` trailers | **BUILT** | orchestrate step-5 cadence; D132–D135 |
| Fix-loop cheap deterministic gate | **BUILT** | orchestrate fix loop; hardened in D139/D140 |
| Freeze/Float M1 (the float, contract edges) | **BUILT + MERGED** | PR #5, master `0c82bc4`; D137–D140 |
| **The M4 mechanism (risk score, triggers, inline evaluator, reroll ladder, telemetry)** | **NOT BUILT — this milestone** | `specs/inline-eval-m4/DESIGN.md` is a DRAFT pending grill + freeze-gate |
| M4 live proof / calibration data | **DOES NOT EXIST** | telemetry ledger not yet created |
| v0.2.0 tag | **DOES NOT EXIST** | it is this milestone's finish line |

## 3. WHAT WE LEARNED FROM DEEPSEEK DSPARK (provenance — carry these INTO the grill and gates)

Source of record: **`github.com/deepseek-ai/DeepSpec`** (MIT; DSpark + DFlash + Eagle3; paper
`DSpark_paper.pdf` in-repo: "Confidence-Scheduled Speculative Decoding with Semi-Autoregressive
Generation", DeepSeek + Peking Univ., 2026-06; checkpoints `deepseek-ai/DeepSeek-V4-Pro-DSpark` + Qwen3
4B/8B/14B + Gemma 12B on HF). Production numbers: 57–85% single-user speedup, ~400% aggregate throughput,
lossless. **The mechanism itself is inference-layer and NOT adoptable** (logits, KV cache, GPU batches —
we sit above hosted models). Five principles ARE adopted, one philosophy underneath them:

1. **Lossless via verifier-final-say** → our default-FAIL gates keep unmoved authority; M4 is detection
   ahead of them; worst-case mistuning = wasted eval calls, never worse output (M4-L8).
2. **Score acceptance LENGTH, not pass/fail** → the **clean-checkpoint streak** is the primary metric;
   it locates WHERE failures root and drives both threshold tuning and safe task-length growth (M4-L10).
3. **Confidence is a SEPARATE cheap module, never the drafter self-scoring** → triggers are
   rule-verifiable durable artifacts ONLY; worker self-assessment never gates (D33/D136; M4-L3).
4. **Context-conditional leash** (deterministic ⇒ long drafts; open-ended ⇒ short) → per-task-class τ:
   code = long leash on cheap verifiable signals; research = shorter chunks on grounding/citation
   artifacts; debug = hypothesis-cycle signals (M4-L6).
5. **Calibrate against cached verifier outputs** (their drafters train on cached target outputs) →
   thresholds calibrated from the logged (signal-vector → gate verdict) ledger, conservative defaults
   until ≥3 instrumented runs (M4-L4/L10).
- Philosophy: **verifiable rewards over judged rewards** (the R1-lineage signature) — push scoring into
  mechanically checkable form; LLM judgment only AFTER a trigger, never AS a trigger.

**Explicitly rejected (do not let the grill or a builder reintroduce):** the Markov head / low-rank
factorization (token machinery, no harness analog); fixed-cadence or realtime LLM evaluation (the
spiral); rich per-signal rule engines (one dial, M4-L4); learned confidence models in v1 (heuristic +
logged calibration; a trained scorer is M4.1 material once the ledger is deep); DSpark-for-us at the
FM level (only relevant if a self-hosted worker tier lands — a deployment choice, zero harness code).

## 4. INGEST LIST — what the session MUST load for this to work effectively and properly (in order)

1. **This brief**, then **`.planning/specs/inline-eval-m4/DESIGN.md`** end-to-end (M4-L1..L10, the
   architecture sketch, acceptance criteria, the 5 open grill questions).
2. `AGENTS.md` (spine) + `.planning/DECISIONS.md` **D131** (tier resolver — M4-L7 composes with it),
   **D136** (fail-closed decision-code), **D137-L5/L4** (the substrate's original intent), **D139/D140**
   (the adval + float precedents for gates, mutation proofs, and deviation handling) +
   `LESSONS-LEARNED.md` **L18** (verify field lessons before freezing) + **L19** (integrated cross-seam
   sweep before building on multi-piece work; name adjacent seams in reviewer prompts).
3. **The substrate implementations M4 consumes** (read the CODE, not summaries — line anchors in older
   docs are stale by definition): `tools/footprint.py` (`file_content_hashes`, `changed_in_task`),
   `protocol/board.md` (PROGRESS semantics + cadence incl. the wall-clock floor + zero-module form),
   `skills/coordinate/kata-orchestrate/SKILL.md` **as it exists on master** (0.5.0 — dispatch template,
   checkpoint cadence, fix-loop cheap gate, liveness ladder, escalation kinds, the contract final-gate
   step; RE-GROUND every anchor you cite — they moved twice last session and stale anchors were a named
   gate finding), `skills/evaluate/kata-evaluate/SKILL.md` (0.3.0 — where the never-tiered floor lives),
   `protocol/config.md` (where `inlineEval` lands), `protocol/escalation.md` (kinds; the grounding pass
   reuses this machinery), `tools/kata_models.py` (D131 resolver — the inline evaluator's tier
   resolution goes through it).
4. **Cross-model surface:** orchestrate LD6/LD7 (off-host dispatch, RESULT envelope, host fallback) —
   M4's scheduler must treat cross-model workers identically (§5).
5. Provenance (skim, cite, do not re-research): DeepSpec repo README + paper abstract.

## 5. HARD REQUIREMENTS: cross-model + ACP (these are load-bearing, M4-L9)

- **Every M4 signal is a durable artifact written at checkpoint time** — board line, checkpoint commit,
  per-checkpoint record committed in the task worktree. NEVER an in-session observation. The scheduler
  POLLS files at checkpoint granularity. This single rule is what makes the mini loop identical for:
  a Claude subagent, a cross-model background subprocess (LD6), and a Quick-driven ACP session.
- **Recovery is kill-and-restart, never in-flight steering** (M4-L2): reroll = kill session/subprocess +
  fresh dispatch from the last good commit with the (possibly tightened) brief. This is the ONLY recovery
  primitive; it exists on every platform. No M4 feature may depend on streaming output, mid-session
  injection, or shared session memory.
- **Adapter contract (normative):** (a) worker context can append to the shared board at the integration
  root (S3b rule); (b) platform provides kill + fresh-dispatch; (c) absent either ⇒ M4 degrades to
  `telemetry` mode on that platform, surfaced never silent.
- **Tiering cross-model:** the inline evaluator resolves at anchor −1 through the D131 RELATIVE resolver
  (family-aware, clamped, fallback) — never a hard model id (the Fable-outage lesson).
- **BC kill switch:** `kata.config.inlineEval: off | telemetry | on`; **absent ⇒ off, byte-for-byte BC**;
  bootstrap writes `telemetry` for new runs until the ledger has ≥3 runs, then offers `on`.

## 6. EXECUTION RECIPE — to FINAL STATE, no shortcuts (each arrow is a gate you do not skip)

1. **Confirm green** on master (`0daf746` or later): pytest 2306/3, validator 47/0/0. Branch
   `m4/inline-eval` (all work on it; PRs per phase or per the operator's call; commits only on approval).
2. **Grill** the DESIGN's 5 open questions (§Open questions) at anchor: corrective-NOTE transport;
   checkpoint-record format (board-msg vs committed JSON — durability vs board single-purpose);
   slack-estimate source (plan frontmatter vs ledger class-median); τ defaults + rationale;
   debug-class double-ladder precedence vs kata-diagnose. Fold answers into the DESIGN as dated
   amendments; keep M4-L1..L10 stable unless the grill finds unsoundness (then amend LOUDLY).
3. **Fresh-context adversarial freeze-gate on the DESIGN** (HOLD→SHIP). Expect HOLDs — the M1/P2 gates
   held 5 times total and every catch was real. Reviewer prompt must name the ADJACENT SEAMS (L19):
   board protocol, fix-loop, liveness ladder, escalation kinds, D131 resolver, LD6 envelope, the M1
   contract final-gate step (M4 inserts near it — renumber/re-anchor discipline applies AGAIN).
4. **Freeze PLAN-p0-telemetry** (pure measurement, zero behavior change, BC by construction — the
   Freeze/Float-P0 pattern) → gate → build → integrated sweep. P0 output: telemetry module + committed
   ledger (`.planning/telemetry-ledger.md`) + first instrumented run rows. **P0 validates/refutes the §1
   estimates — pause here and REPORT the numbers to the operator before P1 builds.**
5. **Freeze PLAN-p1-code-class** (risk score tool + scheduler prose + ladder + grounding pass + reroll +
   `inlineEval` config + adapter-contract prose) → gate → dogfooded build (disjoint ownership, TDD,
   mutation-proven decision code, conductor-gated tasks) → **L19 integrated cross-seam adval** → merge
   gate. Then **PLAN-p2-research+debug adapters** on the proven scheduler, same recipe.
6. **Live proof** (n=0→1): one real run with `inlineEval: on`, code class — ideally a run that ALSO
   serves as the float's live proof (a new-project one-shot with a real `builds_against` edge kills two
   deferred proofs with one run). Benchmark A/B (D16 machinery) against a control run: outer-loop
   iterations must DROP; green-path overhead < 1% (M4-L1) — pasted numbers, not adjectives.
7. **Closeout:** D-records (≥ D141), CHANGELOG, README claims (honest-maturity — no over-claims; that
   class of error is a repeat offender), context docs synced, **tag `v0.2.0`** and push the tag —
   the operator ingests this release downstream. Only after §7's checklist is fully checkable.

## 7. FINAL-STATE CHECKLIST (the definition of done — celebrate ONLY when every row is checkable)

- [ ] DESIGN frozen post-gate (SHIP recorded with the gate history in the spec, like PLAN-p2-float.md).
- [ ] P0 telemetry merged; ledger exists with ≥1 instrumented run; §1 estimates confronted with data.
- [ ] P1 code-class mechanism merged: risk score (mutation-proven, fail-closed per D136 where it gates),
      ladder incl. the grounding-pass rung, reroll-from-commit, `inlineEval` config (absent ⇒ off BC test).
- [ ] P2 research + debug signal adapters merged (same scheduler; grounding/citation + hypothesis-cycle
      signals; double-ladder precedence rule vs kata-diagnose resolved and written).
- [ ] Cross-model: scheduler consumes only durable artifacts (test proves a signal set written by a
      non-session worker path is fully readable); tier resolution via D131 resolver (no hard model ids).
- [ ] ACP: adapter contract documented in `adapters/` + protocol; degrade-to-telemetry path stated.
- [ ] Live proof run complete; A/B numbers show outer-loop reduction; green-run overhead < 1%.
- [ ] Full gauntlet green: pytest (grown from 2306), validator 0/0, Snyk medium+ 0, all new decision
      guards mutation-proven, L19 sweep SHIP, operator merge gates passed.
- [ ] Docs: D-records, CHANGELOG, README (honest), HANDOFF/ORIENTATION/STATE synced, **v0.2.0 tagged**.
- [ ] Every claim of completion in the session cited its artifact. Zero "oops" entries in LESSONS-LEARNED.

## 8. THE THREE THINGS MOST LIKELY TO BITE (pre-registered, so they can't be surprises)

1. **The spiral by a thousand cuts:** each individually-reasonable "let's also check X mid-task" adds
   happy-path cost. M4-L1's <1% green-run overhead cap is the tripwire — measure it in P0's A/B, and
   let the freeze-gate attack every mechanism for hidden per-checkpoint cost.
2. **Trigger precision on day one:** heuristic signals + hand-set τ will false-trigger. That is WHY
   defaults are trigger-shy, why `telemetry` mode exists, and why calibration is data-driven. Do not
   "fix" early false triggers by adding rules — adjust τ, feed the ledger.
3. **Double-ladder interactions:** M4's ladder × the liveness ladder × kata-diagnose's loop × the fix
   loop can chase each other on one sick task. The grill question #5 exists for this; the freeze-gate
   must attack it; the precedence rule must be ONE paragraph a compliant orchestrator can't misread.
