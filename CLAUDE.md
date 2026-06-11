# CLAUDE.md — pointer

**This project uses `AGENTS.md` as the canonical agent-instructions file** (the cross-tool industry
standard). Claude Code is the exception that reads `CLAUDE.md`, so this file exists only to redirect.

➡️ **Read [`AGENTS.md`](./AGENTS.md) first** — it holds the vision, the spine principles, the working
conventions, and the routing. Then read `docs/DESIGN.md`, `docs/STANDARDS.md`, and `.planning/STATE.md`.

## Claude-specific notes (only what differs from AGENTS.md)

- **Model routing (D59):** deep research/planning/grilling → **Claude Fable 5** (`claude-fable-5`);
  build/encode/refactor → **Sonnet**; evaluation → fresh-context **no-write** subagent.
- **Native features the Claude adapter MAY use** (never depended on by the core): Agent Teams
  (`CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), hooks, subagent frontmatter, `/compact`.
- Everything else: follow `AGENTS.md`.
