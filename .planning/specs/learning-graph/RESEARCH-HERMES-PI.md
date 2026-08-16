---
spec: learning-graph
kind: field-alignment research (BL-N16 input)
produced: 2026-08-16 by a dispatched read-only research agent; conductor-reviewed, evidence labels preserved
labels: DOC-SOURCED (url) · INFERRED · UNKNOWN
---

# Hermes & Pi — agent learning, memory, self-modification (vs. the BL-N16 substrate)

## 1. Hermes (Nous Research's Hermes Agent)

**Identity** — DOC-SOURCED: open-source (MIT), model-agnostic autonomous agent harness (CLI,
desktop, API server, messaging gateway; launched 2026-02-25). Its defining feature is a closed
learning loop: agent-curated MEMORY.md + autonomous skill creation + in-use skill refinement.

**Memory files** — DOC-SOURCED (hermes-agent.nousresearch.com/docs/user-guide/features/memory):
- Two plain **markdown files** (no frontmatter) in `~/.hermes/memories/`: `MEMORY.md` (learned
  facts, **hard cap 2,200 chars / ~800 tokens**) and `USER.md` (user profile, cap 1,375). Entries
  `§`-delimited. Deliberately **bounded and curated, not append-only** — add/replace/remove to
  stay under cap.
- **Capture:** automatic — a background self-improvement review after each turn; no user verbs
  required.
- **Apply:** load-time system-prompt injection, **frozen at session start** (protects prefix cache
  — no mid-session mutation).
- **Audit:** `write_approval` gates saves; `/memory pending` approve/reject queue; content is
  security-scanned (prompt-injection patterns, invisible Unicode) before save. **No diff/temporal
  history for memory files** — history lives in FTS5 search over the SQLite session store.
- Pluggable external memory providers (Honcho, Mem0, OpenViking).

**Skills = the durable learning substrate** — DOC-SOURCED (…/features/skills):
- YAML frontmatter + markdown (`name`/`description`/`version`) under `~/.hermes/skills/…/SKILL.md`.
- The agent **self-creates and self-patches skills** (`skill_manage` tool), prompted by novel
  workflows, error recoveries, and user corrections.
- **Real audit UX (opt-in):** staged writes in `~/.hermes/pending/skills/` (survive restarts),
  `/skills pending`, `/skills diff <id>` (unified diff), approve/reject; frontmatter versions; a
  content-hash manifest distinguishes user-modified vs upstream.
- ⚠ **Doc-truth correction owed in OUR tree:** `kata-promote`'s frontmatter characterizes Hermes
  as a "no-gate instant-universal model" — true only of the DEFAULT config; the staging gate
  exists opt-in. (Filed as a fix item.)

**Variants:** SOUL.md identity file + personality presets — **no mechanism for spinning specialist
variants off accumulated learning.** Per-subagent persistent memory: UNDOCUMENTED/UNKNOWN.
**Persistence:** everything under `~/.hermes`; reinstall survival INFERRED, not documented.

## 2. Pi (badlogic → Earendil, pi.dev)

- Minimal terminal coding harness (4 core tools, shortest system prompt); **memory/learning
  deliberately NOT in core** — userland TypeScript extensions can patch the system prompt at
  `before_agent_start` and persist via the JSONL session log (Pi's only native durable record).
- **Skills:** implements the Agent Skills standard (frontmatter + progressive disclosure), global +
  project tiers; agent-authored on request — **no auto-capture, no staging, no diff audit, no
  versioning documented**.
- **Agent variants:** community subagent packages; definitions are Claude-Code-style **YAML
  frontmatter + markdown** at `~/.pi/agent/agents/*.md` — static at dispatch; **no per-agent
  learning found in any package**.
- Persistence `~/.pi/agent/`; reinstall survival INFERRED.

## 3. Comparison vs the BL-N16 substrate

| Dimension | Hermes | Pi | Proposed KataHarness |
|---|---|---|---|
| Agent definition format | SOUL.md + skills (fm+md) | fm+md (community std) | fm+md — **matches the field** |
| Learning capture | automatic per-turn review | none in core | grill · flagged guidance · agent close |
| Apply | load-time injection, frozen per session | load-time injection | load-time injection — **same pattern** |
| Temporal tracking | **no** (bounded replace-in-place) | **no** (session log only) | append log + timestamps — **exceeds both** |
| Audit | staged diffs, opt-in | none | audit-by-default — **exceeds both** |
| Variants from learning | no | no | specialist spin-off — **novel, neither does it** |
| Persistence | `~/.hermes` | `~/.pi/agent` | the vault — same instinct, user-data domain |

## 4. Alignment verdict

Matches the field on format and load-time injection; **exceeds it** on temporal audit and the
learning→specialist spin-off (genuinely absent from both). **One tension, and it is the important
one:** Hermes' strongest empirical lesson is **bounded curation** — a hard cap with
add/replace/remove, explicitly to protect context budget and prefix cache. A pure append-only
per-agent log grows without bound and bloats every load. **Design consequence adopted into
BL-N16: append for audit, distill for load** — the full temporal log is the audit layer; a capped,
curated "active" section is what actually injects. Also: both harnesses put *durable, reusable*
learning into SKILLS (shareable, individually gated) — KataHarness already owns that half
(kata-promote / STANDARDS §1.3); the per-agent substrate is the **complement** (agent-specific,
non-promotable learning), not a rival channel.

## 5. Three ideas adopted as spec input

1. **Staged-write + unified-diff approval queue** (Hermes): pending dir surviving restarts,
   per-change diff, approve/reject — the concrete UX for auditable self-modification; rhymes with
   kata-promote's human gate.
2. **Bounded active section with a visible fill %** (Hermes): the injected section carries its own
   usage percentage so the agent self-curates; history is searched, never bulk-loaded.
3. **Security scan on self-written learning** (Hermes): prompt-injection patterns, invisible
   Unicode, credential shapes — a self-modifying substrate is an injection-persistence vector;
   this belongs in the spec from day one.

## 6. Open unknowns

Hermes subagent memory (undocumented) · Hermes SOUL.md self-modification (unknown) · Hermes
memory timestamp semantics (none documented) · Pi core-memory roadmap (deliberately userland
today) · reinstall survival on both (inferred only).
