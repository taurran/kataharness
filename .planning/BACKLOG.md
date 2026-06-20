# BACKLOG — KataHarness

Promote to ROADMAP milestones when ready.

- **research/NOTES.md deep-eval** — score mattpocock skills, BMAD, GSD; record exactly what each
  `kata-*` skill adopts from where (the core bake-in work). *(do before/with v0.1)*
- **Adapters** — `codex`, `kiro`, `acp-quick`; AGENTS.md→tool-instruction-file normalization; skill-format mapping. *(v0.3/v0.4)*
  - **Per-tool instruction-file mechanics (D60–D63 AO forward-dependency, user 2026-06-18):** Claude = `CLAUDE.md`
    pointer→`AGENTS.md` (done); **Codex** = reads `AGENTS.md` natively incl. nested (~zero work); **Copilot** =
    `.github/copilot-instructions.md` (AGENTS.md support firming up) → pointer/generator; **Kiro** = **steering**
    (`.kiro/steering/*.md` with inclusion modes: always / `fileMatch`-glob / manual) — **NOT a tree-walk**, the
    structurally-different one. **AO seam:** `kata-orient`'s agnostic orientation contract (`protocol/orientation.md`:
    tiers + nested-module rollup + `kata-graph` adjacency pointers) is *rendered* per tool by the adapter — Claude/
    Codex→nested AGENTS.md/CLAUDE.md tree-walk; **Kiro adapter must render the module rollup as steering `fileMatch`
    files**, not per-folder tree-walk files. Verify current Copilot AGENTS.md adoption + Kiro steering details at
    build time (facts may have moved past the Jan-2026 cutoff). Captured for design later; do NOT reopen frozen specs.
- **`kata-engram`** — cognitive-fingerprint/engram injection from kiban/kagami; gated on a mature second brain. *(v0.4)*
- **Engram-mediated escalation (FUTURE phase, harness-wide — A4-GB10)** — every human-in-the-loop escalation
  *anywhere* in the harness routes through the engram: (a) consult the cognitive fingerprint first → auto-resolve
  known patterns, only novel decisions reach the human; (b) feed every human resolution back into the engram so
  the next identical escalation auto-resolves. Net: human interrupts asymptotically decrease as the engram matures
  → strengthens the long-running promise. **Gated on PokeVault installed (READY, D58) + cognitive-fingerprint
  synthesis built**; grows from `kata-engram` (D9). Ties to the cognitive-twin arc (kiban/kagami). Prereq for
  trusting version-up's escalate-not-silent-expand at scale.
- **Plugin packaging** — package the suite as a Claude Code plugin + a portable bundle; `plugin.json`/suite version.
- **License selection** — choose an OSS license before public release.
- **★ Install & portability layer (NEXT after self-dogfood — the "plug into any vault/project" bridge).**
  Today the harness operates *in its own repo*; getting it to run against an arbitrary user's vault or project
  dir needs two unbuilt layers: **(1) distribution/discovery** — place the skills where the host agent finds
  them (Claude Code plugin or `.claude/skills/`; other tools via adapters) — overlaps "Plugin packaging" + the
  v0.3 adapter layer (spine #3); **(2) a one-time workspace-binding config** — distinct from per-run
  `kata.config`: user-set **roots** (vault root · project root · where `.planning/`, the LEARN feed
  `engram.learnFeed.dir`, and candidate skills `agentSkills.dir` live relative to the user's workspace). The
  config schema already has the *seeds* (those dir fields are path-configurable); what's missing is the init
  flow + the top-level workspace binding so it is **not PokeVault-shaped**. Likely a small spec → a `kata-install`
  /init capability. **Sequencing:** self-dogfood (needs none of this) → spec this layer → plugin packaging +
  adapters. *(Raised 2026-06-19 in the positioning/portability assessment — "control + plugs into your vault".)*
- **PokeVault install path (D58)** — the *reference* instance of the install & portability layer above: how the
  PokeVault vault (`C:\Users\taurr_nvs748q\PokeVault\PokeVault`, `toolkit/` area) installs/pins KataHarness.
  (Replaces the retired CPP consumption path, D57.)
- **Protocol specs** — flesh out `protocol/{board,tasklist,state,handoff}.md` schemas.
- **Quick/work version** — fork/branch strategy for the AWS-internal variant.
- **`kata-tasklist` reframe (D23)** — virtual task board over GSD structure + backlog, syncing to Jira/Asana
  via MCP (env has `pm-skills`/`atlassian`). Replaces the old file-locked-claim purpose.
- **A3 REVIEW carry-overs (2026-06-08, non-blocking)** — (a) `tools/` example-`kata.config` coherence check
  (validate a config's `tiers` keys resolve, `mode`/`effort` valid, modules have providers) — the maintainer-time
  complement to orchestrate's runtime load-guard (GB12/D45). (b) **A4:** sharpen `kata-readiness` Scope 1 wording
  so "validator green" clearly means the *harness* install vs the *target* repo when running version-up on an
  existing codebase. (c) `tiers`-key format (bare-verb vs `kata-<verb>`) is documented-consistent but unenforced.
- **Validator deeper checks (A1 REVIEW backlog)** — (3.1) `check_protocol_schemas`/`check_taxonomy_present`
  use substring matching → can't detect substantive erasure; add structural checks if it bites. (3.3)
  `check_tags_namespace` allows bogus `kata/...` sub-namespaces; add a `kata/...` prefix allowlist when
  `kata/tier/<tier>` becomes load-bearing (A2-time).
- **AO lateral/module-rollup is unexercised until a multi-module target (D76 follow-up, 2026-06-19)** — the
  validation stack confirmed `kata-orient`'s **nearest-module `AGENTS.md`/`CLAUDE.md` vertical rollup** + the
  **kata-graph lateral adjacency pointers** are a **latent no-op in *this* repo** (only root `AGENTS.md`/`CLAUDE.md`
  exist; no `kata.graph.json` on a greenfield run). It **degrades correctly** to root-only (graceful, triplicated
  in orientation.md / kata-orient / the AO hook) — forward-wiring for the 2026 nested-AGENTS.md standard, not a
  bug. **Exercise + test it when the harness orients inside a real multi-module target** (e.g. the dogfood
  version-up on KataHarness itself, or a consumer repo with per-module instruction files): add an AO test seam
  that proves rollup picks the nearest module + adjacency pointers resolve. Until then it's correct-but-inert.
- **β-runtime: structural redaction filter + test seam (D74 follow-up, 2026-06-19)** — today the LEARN-feed
  redaction (C3) is a **prose contract** (`kata-handoff` §7 "confirm no secrets/keys/PII") the emitting agent
  honors; "fail-closed" is an instruction, not enforcement. The β feed writes synthesis to an **external dir**
  (egress surface). **When β goes runtime** (the dogfood/ε arc), add an **automated redaction filter** the emit
  path must pass + a **pytest seam** that proves a secret/PII-bearing page is blocked. Until then the guarantee
  rests on agent obedience. *(Security-domain priority before any real second-brain backend is bound.)*
- **AI-slop / spiraling-session detection in the review process (user 2026-06-18)** — ingest the OSS
  **ai-slop-detector** (`https://github.com/flamehaven01/ai-slop-detector`) and **deep-eval which of its checks
  to adopt** to catch **spiraling agents / degraded sessions / AI-slop output** — a common, real risk in
  long-running loops. **Design decision to make:** *embed* the adopted checks into `kata-review` (a new
  review axis / mode) **vs.** stand up a *separate* skill that runs as part of the EVALUATE phase (e.g.
  `kata-slop-check`, dispatched alongside `kata-review`/`kata-evaluate`). Lean on the **minimal-step bake-in
  discipline** (D41/GB8 — extract only the necessary stripped-down checks; do not over-port). **License + `source:`
  attribution required** before adopting any code (spine #12 / D12 — verify the repo's license). **Seams:** ties
  to `kata-review` (adversarial), `kata-diagnose` (bad-session symptoms), and `kata-selfhandoff` (session-health
  trigger — slop/spiral signal could fire a self-handoff/abort); a slop verdict should be a **default-FAIL gate
  finding**, never advisory-only. Captured for a later spec; do NOT reopen frozen specs. *(post-v0.1; quality module.)*
- **`kata-report` (D32)** — post-loop, handoff-phase build report: lite-synthesis of loop artifacts (DESIGN,
  DAG, decision ledger, manifest, diffs, evaluate/review verdicts, gate numbers) → durable `BUILD-REPORT.md`
  with a Mermaid structural diagram (of our own build DAG). Non-goal: from-scratch comprehension — that is
  `kata-understand`'s job (the two are complementary: report = what the loop did, understand = what the code
  is). Feeds `kata-improve`; open pointer for a future PM overlay (D30). Baseline near-free (spine-light);
  visuals tier up.
- **`kata-graph` — pre-processing structural map (PROMOTED to active A4, GB6).** New skill: builds a compact
  symbol/dependency map of an **existing** codebase so grill/plan/orchestrate ingest a large repo cheaply
  (token-saving). The version-up ingestion engine (was working-name `kata-map`). **Optional module
  (`kata/module/graph`, GB10) — the version-up preset bundles it by default. The *skill* ships in A4**;
  the *accelerated backend* (Graphify's AST graph / an MCP graph server) stays an **optional adapter binding,
  never a core dep** (agnostic core = grep/glob/Read; pre-staged via D29). Usage discipline for the accelerated
  backend if adopted: AST-only in-loop, bounded `--budget` queries, out-of-context oracle, NO always-on hook,
  no semantic pass in-loop. Plan it by evaluating OSS minimal-step examples (GB8). Graphify attributed in
  `source:` (spine #12).
- **`kata-understand` — post-processing comprehension map (desired state, GB7).** Post-loop comprehension map
  of a **newly-built** codebase → helps the *user* navigate/understand what KataHarness created (Understand-
  Anything nod). **Distinct from `kata-report`:** report = build-log synthesis (comprehension is its non-goal);
  understand = from-scratch comprehension of the result. **Optional module (`kata/module/understand`, GB10).**
  **Base: Understand-Anything** (`Lum1104/Understand-Anything`, MIT — purpose-built for teach-the-human
  comprehension/onboarding: `/understand-onboard`, `/understand-domain`; "graphs that teach"); Graphify a
  secondary source (multimodal/infra). Compose pluggable skills, don't fork-splice (A4 RESEARCH §5b). Name by
  job not vendor (§5c). Own later spec, post-v0.1. Plan via OSS minimal-step eval (GB8).
- **`kata-defer` — in-loop deferral / "nice-to-haves" capture (GB9).** Optional module
  (`kata/module/defer`). During a run, any out-of-scope-but-worth-keeping item (nice-to-have, post-processing
  candidate, deferred-for-a-reason) is appended to a run-scoped `DEFERRED.md` instead of being dropped or
  scope-crept into the frozen plan; compiled at HANDOFF; feeds project backlog / `kata-improve` /
  post-processing. **The structural complement to no-drift** (#1/#2): the pressure-release valve that makes
  one-shot=no-churn sustainable. Name soft (`kata-park`/`kata-icebox` alt). Post-v0.1 unless pulled forward.
- **Research mode (major post-v0.1 spec — path-forward brief done 2026-06-09, `.planning/specs/research-mode/RESEARCH.md`).**
  A `research` run-shape + module: `projects/Research/<project>/` roots; a recursive loop of disciplinary
  **research** + **adversarial-validation** + **evaluation** agents (the Co-Scientist roster). Thesis: the SAME
  spine with three swaps — work-unit = question/hypothesis, conformance floor = an **evidence floor** (citation
  integrity + adversarial survival + empirical ratchet; the never-tiered D22 analog), roster = disciplinary
  researchers. Reuses `kata-review` (adversarial), generalizes the bake-off judge (Elo tournament) and
  `kata-graph` (→ evidence graph `protocol/evidence.md`), and **shares the KG-emit contract with
  `kata-understand`** (research-mode is the upstream producer that fills the PokeVault vault, D58). Empirical sub-loop =
  Karpathy's ratchet = version-up's no-regression gate. Optional backends (GPT Researcher / STORM / Co-Scientist
  OSS) behind module contracts (the aider/Graphify pattern). **Sequence:** after v0.1 validation (D16) + Spec B
  (bake-off judge) + the Obsidian-KG/`kata-understand` spec. Coherence-audited (no chimera). Discipline-lens
  registry + recursion/budget guard (depth×breadth×exploration) are the only genuinely new substrates.
- **`design` module (own spec)** — UI/UX, 2D/3D assets, slides, mobile, image-FM imagery; slots into Advanced.
- **`docs/TAXONOMY.md`** — categories + `kata-<verb>` naming + tier-family convention (`kata-<verb>-<tier>`) +
  spine-vs-module. Motivated by the modes tiering work; partially specced in `docs/MODES-DESIGN.md`.
- **Skill efficiency refactors** (`.planning/SKILL-COST-RATINGS.md`) — grill L8-narrative + convergence
  checklist → `resources/` (~30% lighter); orchestrate worker-prompt → `protocol/`; tdd supporting-depth → pointer.
  Fold the grill one into Spec A (we restructure grill for tiering anyway).
