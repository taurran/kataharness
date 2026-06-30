# CLAUDE.md — pointer

**This project uses `AGENTS.md` as the canonical agent-instructions file** (the cross-tool industry
standard). Claude Code is the exception that reads `CLAUDE.md`, so this file exists only to redirect.

➡️ **Read [`AGENTS.md`](./AGENTS.md) first** — it holds the vision, the spine principles, the working
conventions, and the routing. Then read `docs/DESIGN.md`, `docs/STANDARDS.md`, and `.planning/STATE.md`.

## Claude-specific notes (only what differs from AGENTS.md)

- **Model routing (D59 — RELATIVE, never hard-baked):** model selection is a *differential off the
  operator's current session model* (the **anchor**), resolved at dispatch — NOT a fixed model ID in any
  skill. **Critical work** (judgment / planning / grilling / evaluation / the gate) runs at the **anchor**;
  **economy work** (build / encode / refactor / reporting / lower-priority loops) tiers **down one rung** on
  the anchor's model family (e.g. Anthropic `haiku < sonnet < opus < fable·mythos`; for other families, one
  version down), clamped to the family floor and falling back if a tier is unavailable. Skills carry **no
  `model:` frontmatter** — a hard alias there force-switches the host model and breaks when that model is
  gated/unavailable (the Fable outage). Evaluation additionally runs as a fresh-context **no-write** subagent.
  *(The dispatch-time relative-tier resolver is the model-agnostic abstraction; see the model-tiering spec.)*
- **Native features the Claude adapter MAY use** (never depended on by the core): Agent Teams
  (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), hooks, subagent frontmatter, `/compact`.
- Everything else: follow `AGENTS.md`.
