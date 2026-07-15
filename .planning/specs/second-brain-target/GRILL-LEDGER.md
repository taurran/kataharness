# GRILL-LEDGER — second-brain-target (standard tier, 2026-07-13, operator present)

> Subject: the E3 run, reframed live by the operator. Original queue item read "PokeVault install /
> MindBridge ingest"; the grill surfaced both halves and the operator corrected the frame twice:
> MindBridge is out entirely, and there is NO third install — kata already lives in the code repo
> and the claude install. The run that survived: **second brain as a user-definable, optional
> target** + a **PokeVault recommendation flow** when a user has none. Instrumented (inlineEval
> telemetry) — the E1/E2 verify.owned unblock rides these real code tasks.

### D1 — MindBridge is OUT · LOCKED
- **Question:** the E-queue item's "MindBridge ingest" half — what does it comprise and what is DONE?
- **Provenance:** operator 2026-07-13, firm mid-grill interrupt: "You shouldn't be doing anything with mindbridge."
- **Options considered:** point MindBridge at master · prepare an export artifact · ingest vault pages.
- **Decision:** **None of them — MindBridge drops from scope entirely.** It is operator-side; kata never plans, builds, or ingests for it.
- **Rationale:** the planning-doc mentions (BACKLOG E3, STATE, handoffs, inline-eval-m4 DESIGN "D30 direction") are stale/aspirational boundary markers, not work items.
- **Edges/scenarios:** future sessions must not resurrect it from those mentions — memory `mindbridge-hands-off` written; queue-item text corrected at closeout.
- **Doc-baked:** task #6 renamed; INTENT.md v2 carries zero MindBridge trace.

### D2 — no third install; second brain = user-definable optional TARGET · LOCKED
- **Question:** what does "install KataHarness into the vault under toolkit/" (D58 wording) mean today?
- **Provenance:** operator 2026-07-13: "Kataharness is installed in our code repo under Dev. There is an installed copy in claude. We should be very careful not to corrupt either the codebase or any of the installs… Second brain is not a requirement but it should be a target."
- **Options considered (asked + superseded):** copy 48 skills into toolkit/skills/ · skills+agent-sop · minimal pointer — operator initially picked the copy, then reframed: none of them.
- **Decision:** **No vault install at all.** The vault's role is the second-brain TARGET. The run builds/verifies: (a) the location is user-definable (any vault path, not just PokeVault); (b) second brain is OPTIONAL — absent ⇒ everything works (feed no-op, the existing BC1 contract); (c) it stays a recommended target, never a requirement.
- **Rationale:** two working installs already exist; a third copy in the vault is churn and corruption risk, not capability. This supersedes the D58 "installs into toolkit/" reading for this run (D58's install/test-home framing predates the second-brain architecture).
- **Edges/scenarios:** the existing surface already covers most of (a): `kata_install --vault-dir` / `KATA_VAULT_DIR` / answers-json → `kata_settings.vaultDir` → learn-feed seeding (SB-L7) with operator override. The run VERIFIES it end-to-end with tests + documents it plainly.
- **Doc-baked:** INTENT.md v2 goal + AC1/AC3.

### D3 — the PokeVault recommendation flow (the NEW build) · LOCKED
- **Question:** what happens when a user has no vault at all?
- **Provenance:** operator 2026-07-13: "If they don't have a vault, kataharness can recommend pokevault to them via repo link or install. Per their discretion."
- **Options considered:** silent no-op (today's behavior) · require a vault · recommend-once per discretion.
- **Decision:** **Recommend, per discretion:** when `vaultDir` is unset at the install/first-run surface, kata surfaces an optional recommendation — PokeVault via repo link (`https://github.com/taurran/pokevault`) or install — and a decline leaves a fully functional no-feed run.
- **Rationale:** the learning loop compounds with a vault, so kata should offer one; requirement would violate the optional-target principle (D2).
- **Edges/scenarios:** recommendation must never block or nag (EV-1); the repo-link path is zero-install (clone + bootstrap is PokeVault's own flow); headless/non-interactive runs skip the prompt (no TTY ⇒ no recommendation, never a hang).
- **Doc-baked:** INTENT.md v2 AC2; the build's DESIGN pins the exact surface.

### D4 — honest per-task verification (verify.owned) · LOCKED
- **Question:** what is each task's verify so verify.owned emits honestly?
- **Provenance:** operator picked "byte read-back" for the (since-dropped) copy tasks; translated at convergence to the surviving code tasks with the same honesty principle.
- **Decision:** **Owned-scoped test runs**: each task's verify = targeted pytest over the tests covering that task's owned files; the exit feeds `verify.owned`. The byte-read-back answer is recorded as the operator's honesty bar, applied to the task shape that survived.
- **Rationale:** telemetry that measures real per-task verification is the whole point of the E1/E2 unblock.
- **Doc-baked:** INTENT.md v2 AC4; plan frontmatter carries per-task verify commands.

### D5 — vault AGENTS.md instantiation DROPPED · LOCKED
- **Question (convergence HOLD):** grill 4/4 chose "instantiate the vault AGENTS.md template" before the D2 reframe; mirror v2 locks zero vault churn. Which wins?
- **Decision:** **Drop it — v2 wins.** The template stays as-is; deliberately out-of-scope (vault-side housekeeping, not this run's feature).
- **Rationale:** operator resolution at the convergence gate, 2026-07-13; cleanest read of the don't-touch correction.
- **Doc-baked:** this entry (the out-of-scope record); no DEFERRED.md entry needed — it was never designed work in the frozen intent.

### EV-1 — Elevate: remember-decline for the recommendation · LOCKED
- **Recommendation:** when a user declines the PokeVault recommendation, record the decline via
  `kata_settings.record_accepted_defaults` (the existing C-1 `{value, v, at}` audit schema,
  exercised live this session) so the recommendation surfaces ONCE and never nags — re-armed only
  by install/upgrade, mirroring the first-run marker pattern (CA-L36/L37).
- **Decision:** Accepted — a LOCKED design anchor for the build's freeze-gate: the recommendation
  flow ships WITH the remembered-decline leg.
- **Rationale:** operator accepted at the ELEVATE posing (2026-07-13); a recommendation that nags
  becomes a requirement in practice, which D2 forbids.
