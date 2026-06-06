# PROJECT — KataHarness

**What:** A tool-agnostic, iteratively-improved agent harness that one-shots complex tasks from a frozen
design doc + plan. An iteration on Anthropic's long-running-agent harness with industry best practices
baked in (mattpocock/skills, GSD, BMAD, DDD ubiquitous language).

**Why:** Maximize one-shot success on complex work by front-loading deep planning and executing it
faithfully (no drift), across tools, with durable two-way handoff. Reusable across every project rather
than re-derived per repo.

**Who / where:** Personal open-source project at `C:\Dev\Projects\KataHarness` (public-intended). Incubated
out of CryptoPortfolioPlanner's `cpp-*` harness (the medium). A separate **work version** will target
**Quick** (AWS BI desktop app with MCP/ACP/skills/tasks) — so cross-tool agnosticism and an **ACP**
adapter are first-class long-term requirements; the orchestrator eventually runs in the desktop app and
drives coding agents via ACP.

**Relationship to other projects:** CPP will *consume* KataHarness at v0.1 (keeps its `cpp-*` skills until
then). Cognitive tie-in to `[[project-framework]]` (kiban) / `[[project-kagami]]` second brain via the
backlog `kata-engram` extension point. See `[[cognitive-twin-architecture]]`.

**Principles & decisions:** `AGENTS.md` (spine) + `.planning/DECISIONS.md`. **Standards:** `docs/STANDARDS.md`.
**Charter:** `docs/DESIGN.md`. **Plan:** `.planning/ROADMAP.md`.
