# GRILL-LEDGER — statusline-decouple (essential tier, 2026-07-12c, operator present)

> Subject: decouple the GSD statusline from kata sessions (operator directive: "GSD-like
> functionality should be baked into KataHarness but it should not use GSD itself"). This grill is
> ALSO the D153 live smoke: one-question-at-a-time UX + the first live ELEVATE. Ground truth from
> the Q0 diagnosis + the GSD-dependency assessment (session notes): the harness has ZERO runtime
> GSD dependency (provenance/example text only); couplings are environment-level.

### D1 — the global statusline slot · LOCKED
- **Question:** the slot is global (one command, all projects); kata chains around GSD today. What should it do?
- **Provenance:** operator 2026-07-12c ("I'm not supposed to be using GSD with kataharness anyway. It should be its own workflow"); Q0 A1 diagnosis.
- **Options considered:** keep chain (zero change) · kata-native segment (build) · remove GSD (breaks Mise).
- **Decision:** **Add a kata-native segment** — the chain wrapper grows its own kata renderer.
- **Rationale:** content-level separation already existed, but GSD's renderer painting kata state (via the STATE.md schema) is workflow-mixing; kata should render kata.
- **Edges/scenarios:** Mise/GSD projects keep their statusline untouched (D2); the build is M8-adjacent and gets its own freeze-gate before implementation.
- **Doc-baked:** D160 (DECISIONS.md); BACKLOG build item.

### D2 — composition: replace-in-kata-scopes · LOCKED
- **Question:** how does the kata segment compose with the GSD passthrough?
- **Provenance:** D1 resolution + the assessment finding (GSD renders kata's STATE.md in repo-cwd sessions).
- **Options considered:** replace in kata scopes (recommended) · prepend to GSD output · kata segment everywhere.
- **Decision:** **Replace in kata scopes** — kata-scoped cwd ⇒ kata segment ONLY (child not executed); elsewhere ⇒ GSD passthrough byte-identical (unchanged CA-L1 never-clobber).
- **Rationale:** full workflow separation, each tool sole owner of its turf.
- **Edges/scenarios:** (a) "kata-scoped" = the SAME rule as the D152 gauge hook (`.kata/` dir or `kata.config` at/above cwd, bounded upward walk) — ONE definition, never two; (b) child not executed in kata scopes ⇒ GSD's own bridge (`claude-ctx-*.json`) absent there ⇒ GSD's context-monitor hooks go inert in kata scopes BY DESIGN (kata's D152 gauge owns that turf); (c) segment content anchor: gauge meter from kata's own bridge + run phase from kata.config/board presence — refined at the build's freeze-gate, not here; (d) a repo that is somehow both GSD- and kata-scoped resolves to kata (the scope rule fires first).
- **Doc-baked:** D160; the interim (pre-build) state keeps today's passthrough — no behavior change until the gated build lands.

### D3 — GSD vestiges in the harness repo · LOCKED
- **Question:** `.planning/STATE.md` carries `gsd_state_version: 1.0` (zero in-harness consumers) and untracked `.planning/config.json` is a GSD statusline config. Keep or drop?
- **Provenance:** dependency assessment 2026-07-12c; adval A1-1 (the config was once swept into a commit).
- **Options considered:** drop both (recommended) · drop key only · leave both.
- **Decision:** **Drop both** — remove the `gsd_state_version` key (keep milestone/status frontmatter — genuinely useful state) and delete `.planning/config.json`. *(Operator initially misclicked "drop key only", corrected to the recommended "drop both" — recorded as the corrected choice.)*
- **Rationale:** no GSD version-schema marker left in the repo; cleaner MindBridge export. (Honest
  scope, per the convergence gate: the retained milestone/status keys remain GSD-*parseable*, so
  visible decoupling in repo-cwd sessions arrives with the D1/D2 build, not with D3 alone.)
- **Edges/scenarios:** the GSD statusline parser does not require the key (code-verified at the
  gate: zero references; parseStateMd reads only status/milestone/phase), so dropping it is inert
  even during the pre-build interim; config.json is untracked so deletion has no git impact.
- **Doc-baked:** D160; applied on this branch (gate finding 1 fold — was a forward-claim, now true).

### EV-1 — Elevate: shared kata-scope helper · LOCKED
- **Recommendation:** the D1/D2 segment build extracts `_is_kata_scope` into ONE shared adapter
  module (`adapters/claude/kata_scope.py`) consumed by BOTH the D152 gauge hook and the chain
  wrapper, with a drift-test pinning both call sites to the shared helper. Grounding: D2 edge (a)
  pins "kata-scoped" to one definition, but the definition physically lives only inside
  `kata-gauge-check.py`; the segment build would otherwise copy it — creating exactly the
  two-definitions drift the edge forbids — and scope semantics already produced a live surprise
  this session (F-9 blocked by the upward-walk behavior).
- **Decision:** Accepted (the recommendation) — a LOCKED design anchor for the segment build's
  freeze-gate: shared `kata_scope.py` + drift test, both call sites pinned.
- **Rationale:** operator accepted at the first live ELEVATE posing (2026-07-12c, D153 live smoke);
  structural one-place answer to "am I in a kata scope?" beats review-enforced duplication.

