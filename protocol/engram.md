# protocol/engram.md — engram plugin contract + seam registry

The **engram** (cognitive fingerprint / second-brain input) is a **future, optional** capability that
personalizes the harness to the user's known patterns. It is **gated and not wired today** (D9/D56). This
file exists so that when it is enabled we know **exactly where to wire it in** — it is the consolidated
registry of every seam, the plugin contract a backend must satisfy, and the contract invariants that keep it
safe. (Adversarially reviewed 2026-06-15: initial 9-seam draft HOLD → expanded + hardened; see history note.)

> **Core invariant (D30):** the agnostic core **never depends** on the engram. Every seam is
> **consult-if-present, no-op if absent** — graceful degradation. The engram is purely *additive*; removing
> it changes quality/autonomy, never correctness.

## Gating (when this turns on)

- **PokeVault installed** — SATISFIED (D58); a vault is one possible second-brain substrate.
- **Cognitive-fingerprint synthesis built** — from `kata-engram` (D9), tied to the cognitive-twin arc
  (kiban / kagami). NOT yet built → seams below stay reserved.

## Plugin contract

The engram is an **optional module** (`kata/module/engram`, per D20/D43) with a **pluggable backend**. The
**agnostic core defines this contract; the backend binds to it; the core never reimplements or hard-deps a
backend** — same pattern as `kata-graph` (grep / tree-sitter / Graphify, D53). Declares `needs` / `produces`
/ `slot` like any module. Two operations:

| Op | Direction | When | Effect |
|---|---|---|---|
| **CONSULT** | engram → harness | **before** a human is asked | Read the fingerprint; return a recommendation + a **confidence**; auto-resolve only when permitted (see C2/C4). Only *novel* decisions reach the human. |
| **LEARN** | harness → engram | **after** a human decides | Feed the human resolution back (subject to C3 redaction) so the next identical decision auto-resolves. |

**Net effect (D56):** as the fingerprint matures, human interrupts **asymptotically decrease** → strengthens
the long-running / autonomy promise over time.

## Backend binding — "bring your own second brain" (the differentiator)

KataHarness ships with **no** backend; it defines only the agnostic CONSULT/LEARN contract. A **backend
adapter** binds a specific second brain to that contract:

| Backend | Binds via | Notes |
|---|---|---|
| **kiban** (foundation/synthesis) | MCP / file export | the cognitive-twin base |
| **kagami** (advanced/Socratic) | MCP | deeper twin |
| **external work/private second brain** (e.g. bound via an ACP/Quick host) | external MCP/API the user points at | **clean-room — see below** |
| **plain vault** (PokeVault) | file read/write | minimal substrate |
| **custom** | MCP conforming to the contract | open extension |

- **Config:** `engram.backend` in `kata.config` names the bound backend (+ its adapter pointer). Absent ⇒ no
  engram (the no-op path).
- **Responsibility split:** the backend serves CONSULT queries (return recommendation + confidence) and
  accepts LEARN writes (store resolution). KataHarness speaks **only the contract** — it never reaches into a
  backend's internals.
- **Clean-room (D30) — the load-bearing seam:** because the contract is agnostic and the backend binds
  *externally*, pointing KataHarness at an **external/private second brain** imports **zero external IP into
  KataHarness** — that backend implements its side on its own infrastructure and merely answers the contract.
  This is the documented `protocol/` extension point D30 promised: the public KataHarness and any private/work
  harness interoperate **without coupling or IP leakage**. The differentiator is "bring your
  own cognitive fingerprint" — the harness personalizes to whatever second brain you already run, rather than
  locking you into one.

## Recall — the read-side of `engram.backend` (D30 clean-room, finally named)

The **`engram.backend`** seam (`kata.config`, `protocol/config.md`) is the CONSULT-read backend the core
points at. Its **read-side binding is now named: Recall** (`protocol/recall.md`, `tools/recall.py`). Recall
defines the agnostic **read-CONTRACT** a second brain answers — the payload schema
(`recall.recall_payload_schema()`) + the selection/staleness/read-only rules — and ships a **files-only
default adapter** (`recall.recall_from_paths`) that serves it from on-disk artifacts. External stores
(kiban / kagami / a private vault) are **deferred downstream adapters** answering the *same* contract, the
clean-room D30 promise made concrete: they drop in later **without re-contracting**.

- **This names the read-side binding only.** It does **NOT** turn on the gated CONSULT *decider*. The
  decider (fuse/recommend/decide from surfaced material) is `kata-reason` — a **separate, deferred** future
  grill. CONSULT/LEARN stay **gated off** (D9/D56); `engram.backend` remains the still-gated CONSULT
  backend (config note, BC1). Recall **serves** material; it never decides, writes, or gates.
- **Invariants preserved.** Recall is bound by the read-only invariant and explicitly upholds **C2**
  (fail-to-human), **C4** (LOCKED-decision guardrail), **C5** (staleness surfaced, never pinned/dropped),
  and **C6** (audit) — see `protocol/recall.md` §4–§5. It does not weaken any C1–C6 rule.
- **The LEARN/write half stays out.** The β LEARN feed (D74, "Wiki-synthesis output schema" below) is
  emit-only and unchanged; Recall does not read it back. Recall is the **read** side; β is the **emit**
  side; the decider is deferred.

## Contract invariants (the safety rules — non-negotiable)

| # | Rule | Why |
|---|---|---|
| **C1 — Precedence** | When multiple seams fire at one event (e.g. a sprint boundary fires E2+E3+E7+E20), resolve in a **deterministic order**: all CONSULTs (in a fixed seam priority) → human (if any survive) → all LEARNs. Same event ⇒ same resolution. | D18 consistency (two runs of the "same" event must not diverge). |
| **C2 — Fail to the human** | Backend **absent / slow / erroring / low-confidence** ⇒ **fall through to asking the human.** Never silent auto-proceed on a failed or uncertain CONSULT. | The "when in doubt, stop and make the human decide" safety spine (GB3/GB4); a flaky backend must not become a drift vector. |
| **C3 — Privacy / scoping / redaction** | Define what the fingerprint MAY read (no secrets/PII — the **same redaction gate as `kata-handoff` §7**) and write; **project-scope** fingerprints (a private-project fingerprint must not leak preferences into a public KataHarness run); the LEARN path passes a redaction filter before any write. | D30 clean-room + the user's security domain; without it the LEARN path is a data-exfiltration / IP-leak surface. |
| **C4 — LOCKED-decision guardrail** | CONSULT may **NEVER** auto-resolve a conflict with a LOCKED decision. Any `lockedDecisionInTension` (D52 escalation schema) ⇒ **always** a human escalation, never an engram auto-approve. | The hardest no-drift rule (D1); `kata-orchestrate` already forbids silently re-deciding LOCKED decisions. |
| **C5 — Supersession / decay** | Learned patterns are **supersedable** — the user can reverse a preference; the fingerprint must support supersede-not-rewrite + a staleness/decay story. | The project supersedes, never rewrites (D57/D58/D59); a matured fingerprint must not pin a reversed preference. |
| **C6 — Audit every auto-resolution** | Every engram CONSULT that auto-resolves (human never asked) **still lands in the drift ledger / a CONSULT-decision log.** | Preserves the no-drift audit surface even when autonomy increases (symmetry with the LEARN log). |

## Seam registry

Every place the engram attaches. `(planned)` = a seam in a spec not yet built; reserved now. Severity = how
clearly it is a human-decision/learning surface (HIGH must be wired; MED plausible; LOW speculative).

| # | Seam (skill / phase) | Op | What the engram does | Sev | Backed by |
|---|---|---|---|---|---|
| E1 | `kata-orchestrate` escalation routing | CONSULT + LEARN | Auto-resolve known escalation patterns; feed each human resolution back. Surface = `.kata/escalations/<id>.json`. | HIGH | D52, D56, D9 |
| E2 | `kata-sprint` boundary auto-continue `(planned)` | CONSULT | `auto-continue-while-green` → "…or engram-resolvable". | MED | GB6, D56 |
| E3 | `kata-sprint` course-correct delta-grill `(planned)` | CONSULT | Pre-recommend likely corrections; user still approves (G1). | MED | GB6 |
| E4 | `kata-grill` (planning) — option biasing | CONSULT | Bias decision *defaults*/options toward known preferences (never auto-locks). | MED | D9 |
| E5 | `kata-bootstrap` — config recommendation | CONSULT | Recommend mode / run-shape / `delivery` / effort from history. | MED | D9, D46 |
| E6 | `kata-improve` + `LESSONS-LEARNED` — IMPROVE | LEARN | Each milestone's decisions/lessons/surprises feed the fingerprint. | HIGH | D9 |
| E7 | Durable trail / superseding decisions `(planned)` | LEARN | Approved corrections + accepted-drift = preference signals. | MED | GB3, GB5 |
| ~~E8~~ | ~~`kata-understand` → PokeVault~~ | — | **NOT a seam — a substrate dependency** (the vault the engram READS FROM). Kept as a dependency note, moved out of the seam list. | — | D54, D55, D58 |
| ~~E9~~ | ~~`kata-selfhandoff` re-anchoring~~ | — | **RETIRED 2026-06-15** (adversarial review): self-handoff is agent→self, **no human in the loop** → fails the membership test. | — | — |
| **E10** | `kata-preflight` dependency approval gate `(planned, D29)` | CONSULT + LEARN | Learn which sources/packages the user trusts; pre-recommend approval for known-good deps. The most explicit human gate in the harness. | **HIGH** | D29, D-registry |
| **E11** | `kata-evaluate` PASS/NEEDS_WORK verdict + fix-loop | LEARN (+ latent CONSULT) | Learn which NEEDS_WORK classes the user accepts vs forces a fix. Highest-frequency judgment; conformance floor. | **HIGH** | D22 |
| **E12** | `kata-review` SHIP/HOLD + finding priority | CONSULT + LEARN | Weight findings by the user's risk priorities (their cybersecurity lens); learn SHIP/HOLD tolerance. | **HIGH** | D15 |
| **E13** | `kata-grill` convergence-gate SHIP-to-close | CONSULT + LEARN | Pre-recommend / learn the "specific enough to stop grilling?" call. Distinct from E4. | **HIGH** | grill RUBRIC |
| **E14** | `kata-diagnose` hypothesis ranking + fix-vs-escalate | CONSULT + LEARN | Learn which hypotheses the user favors / what they treat as architectural. (Named "orchestrator/human may re-rank" point.) | **HIGH** | D-diagnose RUBRIC |
| **E15** | `kata-tdd` test-seam / mocking boundary | CONSULT | Bias integration-vs-unit / what-to-mock toward known preference. | MED | tdd SKILL |
| **E16** | `kata-bootstrap` composition ladder (modules / cross-tier / ingestion) | CONSULT | Learn ladder habits (e.g. always pulls `grill-advanced` into Standard). Extends E5 to D24c rungs 2–4. | MED | D24c |
| **E17** | `kata-readiness` WARN-proceed-vs-stop | CONSULT | Learn the proceed-on-WARN pattern (dirty tree, missing CONTEXT). | MED | readiness SKILL |
| **E18** | `kata-defer` park-vs-pursue / what-to-defer `(planned, D42)` | LEARN | What the user habitually parks vs pursues — a strong preference stream (defer-vs-escalate is "the main lever", D51). | MED | D42, D51 |
| **E19** | `kata-sprint` re-entry routing `(planned)` | CONSULT | Learn continue / course-correct / change-cadence / abort routing (T3). | MED | GB4, T3 |
| **E20** | G4 snowball "tweak-vs-re-scope" + E1→A capped approval loop `(planned)` | CONSULT + LEARN | The re-scope judgment when blast-radius exceeds the remaining roadmap footprint. | MED | GB3 G4 |
| **E21** | `kata-handoff` "open decisions for the human" | LEARN | A handoff's parked open-decisions list is a learning surface. | LOW-MED | handoff SKILL |
| **E22** | `kata-slop-check` SLOP-DETECTED verdict + fix-loop | LEARN (+ latent CONSULT) | Learn which slop classes the user accepts vs forces a fix; latent CONSULT pre-weights by the user's tolerance. A SLOP-DETECTED verdict is a default-FAIL EVALUATE gate finding. | MED | kata-slop-check, D41/GB8 |
| **E23** | `protocol/persona.md` register adaptation | LEARN (+ latent CONSULT) | **Substrate:** observed comprehension/correction signals in the conversation + grill-ledger choices (D72 LEARN feed). **Seam:** latent CONSULT sets the persona register from the matured fingerprint — calibrating voice register toward the user's real sophistication over time. **Gated off** (D9/D56): emit/observe-only, zero CONSULT; the feed builds the corpus a future CONSULT will synthesize against. The static moderate-non-expert default (`protocol/persona.md` Defaults section) is the live register until CONSULT matures. Claiming this seam is active before CONSULT lights is a forbidden overclaim (K1). | MED | protocol/persona.md, D9, D56, D72, D74 |

**Substrate dependency (not a seam):** `kata-understand` / research-mode emit into PokeVault (D54/D55/D58);
that vault is what a vault-style backend READS FROM. It is upstream of the contract, not a CONSULT/LEARN
call-site.

## Wiki-synthesis output schema (the LEARN feed — β)

The **LEARN-only second-brain feed** (`β`, D66; the **primary** cognitive-fingerprint feed, D72) is the
harness *observing and emitting* its own decision history as synthesis pages, so a future fingerprint has raw
material to learn from. **It is an engram PREREQUISITE, not gated by the engram** (L7/LC-GB6): the feed builds
the corpus the CONSULT side will later synthesize against. It is **emit-only — zero CONSULT** (no read-back
path exists, so it can never influence a build; the structural guarantee, not a procedural one).

**One schema, two producers (the loop contract LEADS):** both the **loop's LEARN feed** and the vault's own
**llm-wiki** pipeline emit pages in *this* format. Defining it here (a section of this contract, **not** a
separate `protocol/wiki-synthesis.md`) keeps the immature vault aligned to the loop's lead.

**Karpathy "LLM-Wiki" pattern** — a **raw ↔ synthesis split**: the raw decision artifacts
(`DECISIONS.md` / `LESSONS-LEARNED.md` / `GRILL-LEDGER.md` / `REVIEW-*.md`) stay as-is; the feed emits compact,
cross-linked **synthesis pages** *over* them. Markdown, Obsidian-native, no embeddings.

**Page contract (every emitted synthesis page):**
- **YAML frontmatter:** `produced-by: loop | wiki | agent` (the provenance marker — the loop feed writes
  `loop`); `source:` (the raw artifact paths it synthesizes); `date:`; `tags:` (namespaced taxonomy, e.g.
  `kata/synthesis/<topic>`); `scope: project | universal` (C3 project-scoping — a private project's synthesis
  must not leak into a public run).
- **Body:** a tight synthesis of one coherent pattern (a recurring decision rationale, a preference signal, a
  lesson cluster) with `[[wikilinks]]` to the raw artifacts and to sibling synthesis pages. One page = one
  pattern, not a dump.
- **Redaction (C3 — pre-write gate, fail-closed by contract):** every page passes the **`kata-handoff` §7
  redaction filter** (no secrets / keys / PII) **before any write**; redaction failure ⇒ the page is not emitted.
  **Honest maturity note:** today §7 is a **prose contract** the emitting agent must honor — there is no
  automated filter yet. A **structural redaction filter + a test seam** land with β-runtime (BACKLOG); until
  then "fail-closed" is an instruction, not an enforced guarantee. This is the egress surface — treat it as such.

**Emit target + no-op (BC1):** pages are written to **`engram.learnFeed.dir`** (`protocol/config.md`). Absent ⇒
**no emit** (the no-op path — the feed is purely additive, like every seam). This dir is the LEARN-feed target,
**distinct from `engram.backend`** (the CONSULT backend, still gated/off): the feed is active now; CONSULT is not.

**Producer:** the loop feed rides the `kata-improve` **LEARN-feed emit-only sub-mode** (seam E6), run at
IMPROVE / handoff time — out of the one-shot loop budget, never a per-task hook.

## Lifecycle of a seam

1. **Reserved (now):** documented here; the host skill behaves identically with or without the engram.
2. **Bound (when enabled):** the engram module + a backend are installed; CONSULT/LEARN activate at each
   registered seam, under the C1–C6 invariants.
3. **Maturing:** LEARN seams feed the fingerprint; CONSULT seams resolve a growing share automatically — each
   auto-resolution logged (C6).

## Notes

- **Maintenance rule:** when a new skill or spec adds a human-decision point or a learning surface, add a seam
  row here **in the same change**. A human-in-the-loop decision *anywhere* in the harness routes through the
  engram once enabled (D56) — an unregistered decision point is a missed seam (this registry was itself HOLD'd
  for exactly that on its first draft).
- This file is a forward contract, like the reserved `hooks:` / `context: fork` extension points
  (STANDARDS §1.2) — declared, not yet populated.
- **History:** drafted 2026-06-15 (9 seams); adversarial `kata-review-advanced` pass same day returned HOLD
  (5 HIGH misses + 4 contract gaps); expanded to E1–E21 (E8 reclassified, E9 retired) + the C1–C6 invariants
  + the backend-binding section. Re-review before the engram is built.
