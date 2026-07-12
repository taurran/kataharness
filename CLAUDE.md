# CLAUDE.md — pointer

**This project uses `AGENTS.md` as the canonical agent-instructions file** (the cross-tool industry
standard). Claude Code is the exception that reads `CLAUDE.md`, so this file exists only to redirect.

➡️ **FIRST, load [`protocol/prime-directives.md`](./protocol/prime-directives.md)** — the standing
behavioral contract every kata execution runs under (PD-1 never-silently-defer/stub/skip designed
work; PD-2 absolute truthfulness — a stub reported as built is drift). Then **read
[`AGENTS.md`](./AGENTS.md)** — the vision, spine principles, working conventions (incl. the
**Determinism Doctrine**, `docs/DETERMINISM-DOCTRINE.md`), and routing. Then `docs/DESIGN.md`,
`docs/STANDARDS.md`, and `.planning/STATE.md`.

## Claude-specific notes (only what differs from AGENTS.md)

- **Model routing (D59 — RELATIVE, never hard-baked):** model selection is a *differential off the
  operator's current session model* (the **anchor**), resolved at dispatch — NOT a fixed model ID in any
  skill. **Critical work** (judgment / planning / grilling / evaluation / the gate) runs at the **anchor**;
  **economy work** (build / encode / refactor / reporting / lower-priority loops) tiers **down** on the anchor's
  model family (Anthropic `haiku < sonnet < opus < fable·mythos`: coding −1; economy **−1 in advanced, −2 in
  standard/essential** — economy lands on Opus/Sonnet 5; **non-Anthropic families currently run
  everything at the anchor** — their ladders in `kata_models.py` are empty placeholders until those
  adapters land, so no tier-down applies),
  clamped to the family floor and falling back if a tier is unavailable. Skills carry **no
  `model:` frontmatter** — a hard alias there force-switches the host model and breaks when that model is
  gated/unavailable (the Fable outage). Evaluation additionally runs as a fresh-context **no-write** subagent.
  *(The dispatch-time relative-tier resolver is the model-agnostic abstraction; see the model-tiering spec.)*
- **Native features the Claude adapter MAY use** (never depended on by the core): Agent Teams
  (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), hooks, subagent frontmatter, `/compact`.
- Everything else: follow `AGENTS.md`.
