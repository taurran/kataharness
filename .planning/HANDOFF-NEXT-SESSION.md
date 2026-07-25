# HANDOFF — next session (written 2026-07-25, end of the overnight-delegated run + v0.4.0)

> **Supersedes the 2026-07-20 advisor-executor handoff** (its next-item — quota-resilience —
> is now SHIPPED; that history is preserved in `.planning/STATE.md` CURRENT blocks — nothing
> is lost). This doc is the **detailed re-entry brief**; `.planning/HANDOFF.md` points here.
> **Written for a fresh Opus 5 session** (operator is updating Claude Code + starting clean).
> ⚠ IGNORE `C:\Dev\CLAUDE.md` (that is the unrelated **Mise** meal-planning project, not this repo).

---

## 0. GROUND TRUTH AT WRITE TIME (cite-before-claim — verify all of this FIRST)

- **CWD:** start **inside the repo** — `cd C:\Dev\Projects\KataHarness` (the statusline/gauge scope
  and the F-9/R6 live smokes walk UP from cwd; a repo-cwd session collects them passively).
- **Master:** `8e6096f` (PR #47 merged). **Tag:** `v0.4.0` on `8e6096f`.
- **Tree:** clean. **`git stash list`:** EMPTY (the closeout tripwire — if it is not empty, STOP and
  investigate before any work; the D1 stash-corruption lesson).
- **Open PRs:** none.
- **Gauntlet at v0.4.0** (the "confirm green" first action — re-run `cd tools && uv run python
  scripts/gauntlet.py` and expect): **pytest 4072 pass / 3 pre-existing skip · integration 2/2 ·
  ruff clean · validator 49/0/0**. Snyk code med+ **0** (run `snyk_code_scan` over `tools/` if a
  scanner is configured; otherwise record a one-line deferred-security note and proceed).
- **Installed harness note:** the flat-linked skills at `~/.claude/skills` are the STABLE released
  version. The `~/.kata-home` git clone lags master (cosmetic; self-heals at the operator's next
  default `update.ps1` run — which now brings v0.4.0). The SKILLS surface is what matters and is
  current. `kata-advise` (49th skill) present = the advisor-era install is live.

### FIRST: the Opus 5 update itself (Windows gotcha — do BEFORE relying on the new model)
`claude update` **silently rolls back if any `claude.exe` is running** (Windows locks the exe).
Close ALL Claude Code sessions/windows, then from **PowerShell** run `Update-Claude` (or
`claude-update`) — NOT `claude update` from inside a session. Verify the new version, then start the
fresh session and `/model` to Opus 5. (Memory: `reference_claude_windows_update`.)

---

## 1. WHAT SHIPPED — the 2026-07-21/22 session (PRs #41→#47, v0.4.0)

Two things you cannot re-derive from git alone: this was a **single operator-present-then-delegated
session** that cleared the entire A/B/C/D execution plan, and the run TARGET was the **INSTALLED**
harness (operator's target-toggle choice), against the KataHarness repo itself (version-up on self).

| Item | PR | Master | Substance |
|---|---|---|---|
| Bootstrap stderr fix | #41 | `d765e93` | (carried from prior session) PS 5.1 merged-stream native-git stderr no longer aborts ps1 scripts |
| **A** — dispatch stderr | #42 | `f73f66c` | `_subprocess_runner` 4-tuple; `_stderr_tail` cap; stderr rides all 3 failure envelopes; completed envelope byte-unchanged. **THE quota prerequisite.** |
| **B** — advisor deferral pins + smoke | #43 | `924f494` | `TestAdvisorDeferralCompat` (3 pins from the live consult sketch) + 6-seam smoke promoted to `tools/tests/test_advisor_smoke.py`. Test-only. |
| **D** — D1 phantom-corruption fix | #44 | `71e25df` | Mutation proving SANDBOXED — live tree NEVER written; ~60 real proofs route through the sandbox; kata-tdd 0.4.1. **The D1 interim discipline is CLOSED.** |
| STATE record (triple-fix) | #45 | — | — |
| **C** — quota-resilience Tier 1+2 | #46 | `7223ad8` | see §2 |
| v0.4.0 release closeout | #47 | `8e6096f` | CHANGELOG cut + this-session STATE block |

Each item ran the full loop: INTENT freeze (`intent_scaffold.write_intent`) → grill (ledgers under
`.planning/specs/<name>/GRILL-LEDGER.md`) → build → gauntlet (default-FAIL) → **fresh-context adval**
→ own branch → PR → merge-on-green. Grill ledgers emitted to the second brain (learn feed).

**Adval earned its keep every time** (see `feedback_adversarial_review_discipline`): stale cross-refs
(A), a seam5 overclaim (B), a confirmed MEDIUM regex prefix-mangle in my own sandbox fix (D), and
**two confirmed MAJORs in the quota classifier** (C — traceback line-numbers + test-identifier auth
words classifying as provider signals). All folded + pinned before merge.

---

## 2. ITEM C IN DETAIL — quota-resilience Tier 1+2 (the last thing built; know it well)

**What it does:** a provider rate-limit / token-quota / auth failure is now detected from dispatch
RESULT envelopes, lapses the failing lane run-wide, and — on the primary path — **parks the run**
(plain operator message, `human-required` escalation + breakthrough alert, automatic handoff write,
`/kata-resume` re-entry). NEVER a retry loop, NEVER a silent model downgrade.

**The engine — `tools/kata_quota.py`** (pure stdlib, deterministic, fail-closed D136):
- `classify_dispatch_result(result)` — ordered pattern table over the envelope's stderr/error/raw
  text; reasons `rate-limited` / `quota-exhausted` / `auth`; only `failed`/`timeout` envelopes are
  classifiable; malformed envelope RAISES. Post-adval: bare status numbers carry `(?<!line )` so
  tracebacks don't classify; auth words are word-bounded.
- `lapse_decision(consecutive_generic, classified_reason)` — G-2 hybrid: FIRST classified signal, or
  2 consecutive generic failures ⇒ `provider-unavailable`.
- `parse_kill_switch(directives)` — `KATA_OFF advisor|provider[:name]` over the EXISTING
  `kata_steer.read_active_directives` output (`kata_steer.py` byte-untouched); malformed uses surface
  in `unknown`, never vanish.
- `park_message(reason, evidence, platform)` — plain words, provider named when known, **NO URLs**
  (the registry is Tier 3's grill; a stale URL is worse than none, PD-2).

**The wiring — kata-orchestrate 0.15.0:** boundary kill-switch parse (operator-directed lapse) +
the dispatch-failure quota step (classify → `lapse_decision` → route by path criticality G-9:
optional subsystems lapse-and-continue per LD7; the primary path PARKS per G-4). Plus
`kata_telemetry._validate_degraded` (the passthrough joined the fail-closed `_validate_*` family),
`protocol/steering.md` (`KATA_OFF` verb) and `protocol/handoff.md` (additive `trigger:` field).

**BC floor (G-12, diff-verified):** `kata_dispatch` · `kata_models` · `kata_steer` · `kata_adaptive`
all **byte-untouched**. Absent signals ⇒ byte-identical behavior.

**HONESTY (PD-2) — read before trusting this in the field:**
- Engine legs are **test-proven** (59 quota + 9 telemetry pins). The orchestrate park sequence is
  **prose, live-if-it-occurs, UNFIRED** — no real quota event has exercised it end-to-end.
- **The park trigger covers ROUTED-lane dispatches only.** Host-session quota exhaustion produces no
  RESULT envelope to classify and remains uncovered — the manual playbook + restore path still owns
  it. (This is the exact scenario in the three prior real incidents; G-7 left the host/gauge branch
  closed until a host reports plan quota.)
- **Known precision limit (adval F3, recorded, NOT fixed):** a dogfood run testing quota code itself
  can false-positive the classifier from a failing worker's stderr. Consequence is a loud premature
  lapse + a false `degraded` row — recoverable, never a silent wrong answer. The structural fix
  (require an HTTP-ish anchor near the match, or two-field corroboration) is an **operator-ordered
  G-8 amendment** if wanted.

Full grill: `.planning/specs/quota-resilience/GRILL-LEDGER.md` (G-1..G-12 LOCKED + adval addendum).
Original brief (still accurate for Tier 3): `.planning/specs/quota-resilience/REQUIREMENT.md`.

---

## 3. READ-IN ORDER (rebuild context, then act)

1. `protocol/prime-directives.md` — PD-1 (never silently defer/stub/skip designed work) / PD-2
   (absolute truthfulness). Binds the conductor from its first action.
2. This file, then `.planning/STATE.md` **CURRENT block** (top).
3. `AGENTS.md` (spine + conventions) · `docs/DETERMINISM-DOCTRINE.md` (ten laws — LOAD-BEARING on any
   new engine code).
4. For quota follow-on: `.planning/specs/quota-resilience/GRILL-LEDGER.md` +
   `.../REQUIREMENT.md` §3 (Tier 3 scope) + `tools/kata_quota.py`.
5. For a MindBridge import: **§6 of this file FIRST** (the clean-room gate), then the incoming task list.

---

## 4. NEXT STEP — in order (the backlog, prioritized)

**A. Owed to the operator (quick decisions, no code — clear these first):**
1. **Confirm the overnight-delegation record.** The quota grill ledger cites the operator's
   authorization from conversation, not the repo (the adval's F6 flagged that the quote lives in the
   session transcript). One line of operator confirmation closes it.
2. **Two in-absentia ELEVATE offers** (both default DECLINED — declines are signal, D153): ①
   mirror-by-docstring = a defect-duplication pattern (prefer a shared helper / executable pin over a
   docstring pointer when two sites must stay aligned); ② `budget-exhausted` (kata's own spend) vs
   provider quota exhaustion = a same-word namespace hazard → name the namespace in the enum value.
3. **F3 precision-limit design call** — do you want the structural classifier fix (a G-8 amendment)?
4. **v0.4.0 tag veto window** — delete-and-retag if the release framing isn't what you want.

**B. The MindBridge feature import (operator-initiated 2026-07-25) — see §6 for the protocol.**
This is the operator's stated next initiative: bring a set of tasks/features from the MindBridge fork
(a branch off THIS repo) and apply them here. Translates well structurally; **must pass the clean-room
scrub gate (§6) before any merge.** Await the incoming task list, then grill each feature normally.

**C. Real engineering work (grill-gated):**
- **Quota Tier 3** (its own grill — two policy calls): per-provider upgrade **registry** (URL/slash
  freshness ownership) · **silent-hang watchdog** for the codex-402 class (false-positive policy:
  killing a legitimately slow worker is worse than a late detection) · **preflight quota-headroom**
  (shaped like `stranding_verdict`). Brief material: `REQUIREMENT.md` §3 Tier 3.
- **E-queue:** E1 calibration proper · E2 adaptive A/B (both now have ≥1 real ledger row).

**D. Housekeeping (do at natural moments, don't force):**
- `~/.kata-home` default `update.ps1` run — brings the clone + bootstrap to v0.4.0.
- **F-9 / R6 live smokes** — a repo-cwd session collects them passively; flip
  `GROUNDING-CLAUDE` G1b + the adapter README GROUNDED-BY-PATTERN → CONFIRMED **only if actually
  observed** (context crossing 0.70 / a host auto-compaction). Honestly UNOBSERVED to date.
- Long tail (not scheduled, not cancelled): the 2026-07-12 health-review deferrals (STEERING wiring
  residuals, DET-06/10/12/13/14).

---

## 5. STANDING ORDERS (all hold — the operating discipline)

cite-before-claim · done = gates + record + SHA · **fresh-context adval before every merge** (it
catches what author tests miss — ~confirmed 3× this session) · D136 fail-closed on decision-code
INPUT · bump-on-modify + validator `--write` when a skill changes · branch → PR → merge · PD-1/PD-2 ·
**conductor = SOLE main-tree git writer** (workers no-git or own worktrees) · **closeout tripwire:
stash empty + status reviewed** · gates via `tools/scripts/gauntlet.py`, never `pytest | tail &&
commit` · supersede-don't-edit for grill-ledger findings · conductor diff-verifies byte-untouched
claims itself · aim any live n=1 exercise at the run's own riskiest seam · new projects/specs follow
the `.planning/specs/<name>/` convention · emit grill ledgers to the second-brain learn feed
(`tools/learn_feed.py`, feed dir `~/Kiban/Vault/second-brain/wiki/pages/synthesis`, log
`.../wiki/log.md`).

---

## 6. MINDBRIDGE FEATURE IMPORT — the protocol (READ BEFORE IMPORTING ANYTHING)

**Context:** MindBridge is the operator's AWS-internal harness/product — a **fork/branch of
KataHarness**. Features developed there are being ported BACK into this public, clean-room repo.
Structurally this translates well (same spine, same file conventions). **But the direction matters:**
the sanctioned cross-pollination flow is KataHarness → MindBridge (public → AWS ingest, D30). Porting
MindBridge → KataHarness is the **reverse** direction and lands AWS-side work into a **public repo**,
so it carries a hard gate.

**THE CLEAN-ROOM SCRUB GATE (D30 — non-negotiable, PD-1/PD-2 class):**
Every incoming feature must be scrubbed of **AWS-internal IP and work-linkage** before it touches
master. This is exactly the discipline the Kiban publish used (memory `project_framework`: a pre-push
adversarial-validation pass scrubbed all MindBridge/work-linkage and rebuilt history so no sensitive
blob was ever published). Concretely, for each imported feature:
1. **No AWS-internal identifiers** — service names, internal URLs/endpoints, account IDs, ticket refs,
   team/system names, internal doc links, employee handles. (Memory: 38 pre-existing "MindBridge"
   string hits already sit in old `.planning` specs from the E3 ingest queue — those are a separate
   older scrub item, NOT introduced by this import; don't add more.)
2. **No AWS IP** — proprietary designs, internal architecture, work-confidential logic. Port the
   *general* capability, re-expressed in KataHarness's clean-room terms — not the AWS implementation.
3. **A fresh-context adversarial-validation pass scoped to work-linkage** runs BEFORE the PR merges
   (in addition to the normal correctness adval) — the reviewer's explicit job is to find any
   AWS/work leak. HOLD on any finding.
4. **History hygiene** — land imported work as fresh commits authored in THIS repo; do not graft
   MindBridge branch history (it may carry sensitive blobs). If a private migration branch is needed,
   keep it local and NEVER push (the `private/migration-history` precedent).

**Reference material that already exists:** `C:\Dev\_mindbridge-handoff\ADVISOR-EXECUTOR-INTEGRATION-
GUIDE.md` is a PRIVATE front-to-back guide for the REVERSE port (KataHarness advisor → MindBridge). It
is PRIVATE (C:\Dev is not a git repo) and **must NEVER be moved into the public repos.** It is useful
as a worked example of the two-way translation mapping, read-only.

**Process per imported feature:** treat each as a normal version-up — INTENT freeze → grill (the
scrub gate is an extra freeze-gate criterion) → build → gauntlet → correctness adval **+** work-linkage
adval → PR → merge. Grill each on its merits.

### 6a. ROUND-TRIP STATUS — the outbound alignment package IS SENT (2026-07-25)

The operator's plan: the MindBridge Loop session reads THIS public repo + a prepared **alignment
package**, and returns a **merge-back deliverable** (alignment report + clean drop-in files) that a
KataHarness session ingests and grills. Status at this handoff:

- **OUTBOUND (done):** the alignment package was built and handed to the operator (it lives in the
  operator's LOCAL Downloads as `mindbridge-alignment/` + `.zip` — **deliberately kept OUT of this repo**
  so the fork relationship is not published into public git history). It contains: an orientation, a
  feature/contract/**seam map** (with a deliberate-lacks inventory Z1–Z12), the three named alignment
  targets, a **return-package spec** (the exact shape the merge-back must arrive in), and the clean-room
  contract. It also pins frozen snapshots of our doctrine/rubric/prime-directives @ `0270f81`.
- **INBOUND (expect this):** a **merge-back zip** structured as `kataharness-mergeback/` — an `INDEX.md`
  manifest, a package-level clean-room attestation, an `alignment-report.md`, then per-item
  `merge-candidates/MC-NN-*/` (each with a `PROPOSAL.md` + `files/` + `tests/`) and `divergence-flags/`.
  Each candidate names the KataHarness target it aligns to (a `01` subsystem, a §Z lack, or a named
  target below), states BC impact, its **disposition** (script/prose/hybrid — see 6b), and a clean-room
  attestation.
- **HANDLING when it arrives:** for each `merge-candidate`, run the §6 process — grill on its own
  branch, correctness adval **+ work-linkage adval**, HOLD on any leak, merge-on-green. `divergence-flags`
  are surfaced to the operator, never auto-applied.

**The three named merge targets** (more advanced on the fork side → merge back here, respecting our
seams): **(1) Determinism Doctrine** — we HAVE it (`docs/DETERMINISM-DOCTRINE.md`, ten laws + DET-01..14
straggler registry); the fork's is more advanced → superset preserving the 10-law spine + the
"where judgment is allowed" line. **(2) skill-assessment rubric** — our family is `kata-evaluate` (the
fresh-context no-write default-FAIL gate) + `kata-review/RUBRIC.md` + `docs/STANDARDS.md` +
`tools/validate_skills.py`; merge additively, never weakening the D33 never-tiered floor or the
README-index-in-sync invariant. **(3) Prime Directives** — we HAVE `protocol/prime-directives.md`
(PD-1/PD-2, fully wired: REQUIRED_PROTOCOL + orientation stable tier); the fork built stronger
*enforcement* (it actually built things prose merely claimed) → bring the enforcement machinery mapped
to our D33/D136/kata-evaluate hooks; a change to PD *text* is advanced-grill, high-stakes.

### 6b. THE SCRIPT-vs-CONTEXT TRANSLATION AXIS (load-bearing for every merge-back)

MindBridge is **mostly context-as-code** (behavior in prose the model interprets); KataHarness pushes
anything deterministic into **scripts** (`tools/*.py`, pure stdlib, tested, gated) and keeps prose only
for genuine judgment — the Determinism Doctrine's "where judgment is allowed" line as an engineering
default (`kata_quota.py`, `kata_advisor.py`, `kata_adaptive.py`, `contract_edges.py` are all
deterministic-engine + thin-prose-wiring). **So a merge-back is often a prose→script conversion, and
that is frequently where the significant efficiency lives** (determinism · gate-ability · testability ·
no LLM round-trip · token savings). Heuristic when grilling each incoming item: **rule-decidable**
(gate/score/order/hash/parse/classify/durable-write) ⇒ land it as a `tools/*.py` script + tests with
thin skill wiring, NOT as re-derived prose; **genuine judgment** ⇒ stays prose; **hybrid** (script
computes the signal, prose decides the residual) is common and correct. A verbatim prose port of a
script-able mechanism is a **determinism regression** here — convert it or flag it, don't merge it as-is.

**Reference material that already exists:** `C:\Dev\_mindbridge-handoff\ADVISOR-EXECUTOR-INTEGRATION-
GUIDE.md` is a PRIVATE front-to-back guide for the REVERSE port (KataHarness advisor → MindBridge). It
is PRIVATE (C:\Dev is not a git repo) and **must NEVER be moved into the public repos.** It is useful
as a worked example of the two-way translation mapping, read-only.

---

## 7. SUGGESTED NEXT SKILLS (what the resumer will likely invoke)

- `/kata-start` (→ `kata-initiate`) — for the MindBridge import features and quota Tier 3, each as a
  fresh version-up with its own INTENT + grill.
- `kata-grill-standard` — the default grill; `kata-grill-advanced` for Tier 3's watchdog (high
  false-positive stakes) and any security-sensitive MindBridge feature.
- `kata-evaluate` (fresh-context no-write gate) + a fresh-context adval subagent before each merge.
- `kata-context` — pin any new ubiquitous-language terms as they appear.

---

## 8. REDACTION

No secrets, keys, or PII in this handoff or the artifacts it references. The MindBridge import protocol
(§6) exists specifically to keep it that way — the clean-room scrub gate is the standing guarantee.
