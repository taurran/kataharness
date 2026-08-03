---
date: 2026-07-26
supersedes: the task ordering inside MERGEBACK-INGEST.md (that file keeps the detail; this is the queue)
baseline: branch `docs/mergeback-ingest-itemization` @ `830e39d` · master untouched `fcb0338` · PR #51 open
---

# MINDBRIDGE INGEST — EXECUTION ORDER + STATUS

Everything ingested from the merge-back, ordered, with completed work marked. **Nothing is merged to
master.** A coverage audit of this plan against the source package is in §4 — it found four gaps.

---

## 1. DONE

| id | item | evidence |
|---|---|---|
| ✅ **INGEST-0** | **Itemization + coverage matrix** — 8 MCs, 5 DFs (+1 missing), 26 BL items mapped; no blank rows | `MERGEBACK-INGEST.md`, `891a054` |
| ✅ **INGEST-1** | **Clean-room verification (independent)** — 0 corp identifiers / URLs / ARNs; producer name 4× in the attestation only; no grafted history; 168 tests reproduced exactly | `MERGEBACK-INGEST.md` Part E, `7b171b2` |
| ✅ **INGEST-2** | **IaC first-party constraint** — our `kata-iac-*` surface pinned as product, not work-linkage, before any adval greps our tree | `7b171b2` |
| ✅ **T-11** | **Model-tier currency fix.** Semantic tier recognition · currency guard **WIRED** into orchestrate 0.16.1 · emit-side bump · Bedrock/Vertex/case normalization. **2 fresh-context advals folded** (2 MAJOR + 5 MED, then MAJOR-empty + 5 MED + 9 LOW). +34 tests. Every fold break-probed | `8dd648b` → `600eb4c` → `830e39d`, PR #51 |
| ✅ **TRACK-1** | **D2 verification sweep** — 13 read-only probes + 5 I ran directly. *(This had no task id in the original plan — gap G-1 below)* | `D2-VERIFICATION-RESULTS.md`, `89b96c6` |

**Gates at close:** `pytest 4106 / 3 pre-existing skip · integration 2/2 · ruff clean · validator 49/0/0 · Snyk 0 medium+`. Determinism: byte-stable across 5 hash seeds; ten-laws checker 0 findings on the changed file.

---

## 2. PROPOSED EXECUTION ORDER — remaining

Ordering rationale: **blockers → evidence-driven priority → cheap-and-certain → high-stakes → re-scoped.**
D2 findings re-ordered this queue; it is **not** the original MC numbering.

### Wave 0 — no code, clears blockers

| # | id | item | why here |
|---|---|---|---|
| 1 | ~~**T-00**~~ | ~~Request `DF-06` from the fork~~ **CLOSED unbuilt 2026-08-02 (D170)** | MindBridge out of scope; no code was ever received for it, so nothing is unbuilt as a result |
| 2 | **BL-M27** | 🔴 **Rotate the GitHub PAT** out of `~/.claude/settings.json` | Operator action. **STILL OPEN — deferred by operator 2026-08-02, explicitly not dropped.** Plaintext, injected into every spawned process. *(The old "mode 666 / world-readable" framing was **wrong** on Windows — the NTFS ACL grants only the user, Administrators, SYSTEM. Env-injection is the real exposure.)* |
| 3 | ~~**T-09**~~ | ~~Correct the "fork/branch" premise in README/STATE/HANDOFF~~ **MOOT 2026-08-02** | Verified: no "fork of"/"conversion port" claim remains in README, STATE or HANDOFF. Nothing to correct |
| 4 | ~~**T-10**~~ | ~~Decide: ingest-direction defect-carry~~ **CLOSED unbuilt 2026-08-02 (D170)** | No transfer channel exists in either direction now that MindBridge is out of scope. The reusable lesson — *hand-copied code silently loses the fixes made after the copy* — is recorded in D170 and re-opens on any future vendor/port/hand-copy, not on this item |

### Wave 1 — evidence-driven, promoted by the D2 sweep

| # | id | item | why promoted |
|---|---|---|---|
| 5 | **BL-M21** | 🔴 Fix `kata_restore` integration-branch default | **Destructive**: defaults to a branch that doesn't exist here ⇒ a real restore `git branch -D`s six live `task/*` branches |
| 6 | **T-04 (MC-05)** | Run-identity / state rotation | **D2-5 confirmed BROKEN live** — our `RESULT.json` names a SHA 37 commits behind HEAD and the gate credits it. No longer speculative |
| 7 | **T-07 (MC-07)** | BUILT/WIRED/GATED vocabulary + decidable PD-2 half | **D2-11 demonstrated** a 6-line rewrite inverting both Prime Directives that passes the validator green |
| 8 | **T-05 (MC-04)** | Verdict dispatch self-declaration | **D2-4 confirmed** fresh-context is entirely unattested here — zero executable check |

### Wave 2 — cheap and certain

| # | id | item | notes |
|---|---|---|---|
| 9 | **T-01 (MC-03)** | 4 additive validator checks | Best-evidenced item in the package; **cannot flip our 49 skills red**. Rider: `STANDARDS.md:112`'s false "validator-enforced" claim must become true or be reworded |
| 10 | **BL-M24** | `learn_feed` heading regex counts the ledger's own H1 | Root-caused, benign, one-line (`^#{2,6}`) |
| 11 | **T-06 (MC-06)** | Readback-verified writes + newline guard | Verify against our `gate_emit.py` / `run_result.py` / board writer first — they explicitly don't know if we have the gap |

### Wave 3 — high-stakes, needs a real grill

| # | id | item | notes |
|---|---|---|---|
| 12 | **T-02 (MC-01)** | Ten-laws checker, **report-only** | Prereq: law-5 builder-dict carve-out (59 of 101 findings on our tree are FPs from a carve-out our own doctrine makes). Do **not** gate on day one |
| 13 | **T-03 (MC-02)** | Doctrine laws 11–16 | **Advanced grill.** Their own label: batch-reviewed, not adversarially grilled as amendments; single-corpus; from a Context-as-Code harness. Take **13 + 15** (their recommendation), not all six |

### Wave 4 — re-scoped

| # | id | item | notes |
|---|---|---|---|
| 14 | **T-08 (MC-08)** | src-layout resolver | ⚠ **RE-SCOPED** — we already shipped the resolver (`47ddc2d`). Real gap is the narrower **nested-namespace** hole at `graph_gen.py:298`. Do not merge a duplicate |
| 15 | **BL-M26** | Rebuild `kata.graph.json` (35 days stale, predates the fix) + measure rank variance | Turns MC-08's unproven PageRank claim into a measurement |

### Backlog — not scheduled

**From the D2 sweep:** BL-M17 (no executable owner for `mode`/`tiers`) · BL-M18 (no test pins D33 across tier variants) · BL-M19 (spine evidence gitignored, no audit trail) · BL-M20 (`kata-loop` unreachable from any entry point) · BL-M22 (no Stop/SessionEnd gate ⇒ runs can end with no handoff) · BL-M23 (handoff `kind:`/`trigger:` provenance BUILT-ONLY) · BL-M25 (`models.adaptive.l2` INERT; `l2_base_rung` BUILT-ONLY) · BL-M15 (7 raw-git call sites bypass the pinned helper) · BL-M16 (M4 inline eval has never fired: 0 machine-JSON verdicts)

**From their forward backlog:** BL-M01 (packet-tracing smoke — *their* top pick for us) · BL-M02 (specialist registry — mutual gap) · BL-M03 (skill evals) · BL-M04 (learning-loop deep dive) · BL-M05 (handoff thorough review) · BL-M06 (graph oracle layer) · BL-M07 (whole-repo comprehension) · BL-M08 (agent-roster review) · BL-M09 (orchestrator reference-surface **measurement**) · BL-M10 (durable "resolver ran" artifact) · BL-M11 (good/bad-code ride-along)

**From divergence flags:** BL-M12 (record DF-01 — our architecture externally validated) · BL-M13 (DF-03 §4 conversion-fossil class) · BL-M14 (audit our checkers for the `[::2]` under-count class)

---

## 3. NOT INGESTED — deliberate

- **DF-01 / DF-04** — both say *keep ours*. DF-04 protects four validator strengths (empty-tree guard, `REQUIRED_PROTOCOL` PD registration, `steering.md` registration, `--only`) that merging their validator wholesale would cost.
- **DF-02** — informational; read before the T-03 grill.
- **DF-05 §3a/§3b** — thin orchestrator and loop engine explicitly **withheld by the producer**, who recommends against adoption. Only the *measurement* is taken (BL-M09).
- **14 of their 26 BL items** — see gap G-3, this was under-filed.

---

## 4. ⚠ COVERAGE AUDIT OF THIS PLAN — four gaps found

Auditing my own itemization against the source package, the way the DET registry should have been audited.

### G-1 — The verification sweep had no task id
Track 1 was executed and committed but never carried a `T-` number, so it was invisible in the task
list. Assigned **TRACK-1** retroactively above.

### G-2 — Two of the 14 "already aligned" claims were never probed
I built 14 D2 probes but they are **not 1:1** with the fork's 14 aligned claims. Unprobed:
- **Aligned #4 — `AGENTS.md` canonical + `CLAUDE.md` as pointer, "never a second instruction source."**
  No probe. Worth one: we have BOTH files plus `C:\Dev\CLAUDE.md` (the unrelated Mise project) which
  the handoff explicitly warns to ignore — exactly the second-instruction-source hazard the claim is about.
  → **new probe D2-15**
- **Aligned #14 — the "where judgment is allowed" line.** MC-02 claims its two appended clauses
  *narrow* the judgment zone rather than widen it. **That claim is unverified and it is the crux of
  the highest-stakes item in the package.** → **new probe D2-16, a hard prerequisite for T-03**

### G-3 — 14 of their 26 backlog items were filed as "intelligence only" without assessment
That was a dodge. At least four have real hooks into our work:
- **BL-004** (third-party frontier model family + anchor) — same territory as **T-11 and §Z1**; their
  implementation was "mostly DATA: populate an empty family ladder + id map." Directly informs the
  layer-1 rung-vocabulary question the operator scoped out for now. → **BL-M28**
- **BL-006** (assess-only codebase-improvement run profile) — **this is what TRACK-1 just did by hand.**
  Convergence worth recording; a run-shape would make it repeatable. → **BL-M29**
- **BL-009** (mini-loop cadence + triggers, never tuned as a set) — we have the same three mini-loops
  (inline evaluator, advisor consults, diagnose) with independently-grown triggers. → **BL-M30**
- **BL-023** (full determinism conformance pass) — the work MC-01/MC-02 came from. Our analogue is
  running the ten-laws checker over the whole tree and triaging the 101 findings; currently folded
  inside T-02 rather than tracked as its own sweep. → **BL-M31**

### G-4 — One of the producer's four self-disclosed defects names a capability NEITHER side has
`INDEX.md`: *"A checker for the 'grep every promised identifier for a producing code site' rule was
scoped and never landed."* On their side it is prose-only — a §22.1 violation inside the wave that
authored §22.1. **We don't have it either**, and it is the direct mechanical answer to TRACK-1's
cross-cutting finding (*every gap is an invariant with no executable owner*). I filed only the
`[::2]` defect (BL-M14) and missed this one. → **BL-M32**

---

## 5. Still owed by the operator

1. ~~**DF-06** — chase the fork, or accept it as withdrawn (T-00)~~ → **CLOSED 2026-08-02 (D170)**, accepted as withdrawn under the MindBridge out-of-scope ruling.
2. ~~**T-10** — task or backlog?~~ → **CLOSED unbuilt 2026-08-02 (D170)**. Neither: the seam it guarded no longer exists.
3. **MC-02 scope** — all six laws, or the 13+15 subset (T-03) — **STILL OPEN**
4. ~~**PR #51** — review and merge decision~~ → **MERGED to master 2026-08-03** (`74efe98`). PR #53 retargeted to master and merged (`cf2ee50`); gauntlet 4/4 on the merged tree.
5. **PAT rotation** (BL-M27) — **STILL OPEN**, deferred by operator 2026-08-02 (deferred, not dropped)
6. Four items carried from before this ingest: the overnight-delegation confirmation, **two in-absentia ELEVATEs (both default DECLINED)**, the F3 quota classifier-precision call, and the v0.4.0 tag veto window
