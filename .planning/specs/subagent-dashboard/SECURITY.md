---
date: 2026-06-21
spec: subagent-dashboard
scope: Snyk Code SAST on the two new modules (tools/kata_dash_model.py, tools/kata_dash.py)
tags: [security, snyk, dashboard, accepted-risk]
---

# subagent-dashboard — Snyk remediation record

Snyk Code on `tools/` after the dashboard integration: **7 Low findings, all CWE-23 Path Traversal**, 0 Med/High/Crit.

- **5 findings** are the **pre-existing, documented** CWE-23 false positives in `gate_emit.py`/`graph_gen.py`
  (see `greater-loop/SECURITY-phase0.md`) — unchanged.
- **2 new findings** are in `tools/kata_dash.py`: the `--kata-dir` CLI argument flows into a `pathlib.Path`
  concatenation when reading `board.md` / `state.json`.

## Disposition (2 new kata_dash findings): accepted documented FP — same class as Phase 0
- **Source = the maintainer's own CLI argument** on a **non-shipped local tool** (`pyproject.toml`: "maintainer
  tooling … Not shipped"). No trust boundary is crossed; the dashboard is a **read-only observer** that only
  reads the repo's own `.kata/` files. There is no privilege escalation CWE-23 models here.
- **Real control present:** `kata_dash._safe_path` rejects any `..` traversal segment before use — the same
  defense-in-depth `..`-guard used by `gate_emit`/`graph_gen`. Snyk's taint engine flows *through* the guard
  (visible in the dataflow) because it does not model custom Python path sanitizers — empirically established
  over the Phase-0 remediation rounds. Contorting a read-only dev tool's `--kata-dir` contract to satisfy a
  scanner FP is the wrong trade-off.
- **Verdict:** accepted, documented. The `..`-guard stands as the mitigation. No Med/High/Crit at any point; no
  weak-hash or injection issue introduced by the dashboard.
