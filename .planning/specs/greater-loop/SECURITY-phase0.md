---
date: 2026-06-20
spec: greater-loop
phase: 0
scope: Snyk Code SAST remediation for the two new Python modules (tools/gate_emit.py, tools/graph_gen.py)
tags: [security, snyk, phase-0, sast, accepted-risk]
---

# Phase 0 — Snyk remediation record

Snyk Code (SAST) was run on `tools/` after the F1+F2 integration. Initial scan: **9 issues** (all Low).

## Fixed (real issues)
- **CWE-916 — Use of insecure hash (`hashlib.sha1`), ×3 in `graph_gen.py`.** The hashes are used for
  content-addressed cache keys (file/repo fingerprints), not passwords — but `sha1` is a weak primitive.
  **Fixed:** switched all three to `hashlib.sha256`. Rescan confirms these are **gone**. (No behavior change;
  the cache simply keys on a stronger digest.)

## Mitigated + documented (Snyk false positives it cannot clear in-code)
- **CWE-23 — Path Traversal, residual Low findings** where a CLI argument (`--out`, `--root`, `--prev`) flows
  into `pathlib.Path` in the `__main__` entry points of both modules.
  - **Why these are false positives for this context:** the taint source is the **maintainer's own command-line
    arguments** on a **local, non-shipped dev tool** (`pyproject.toml`: *"KataHarness maintainer tooling … Not
    shipped with the skill suite"*). There is **no trust boundary crossed** — no web/network/untrusted input
    reaches these paths. The operator can already write anywhere their shell account permits; CWE-23 models a
    *privilege escalation across a boundary* that does not exist here.
  - **Real control added anyway (defense-in-depth):** both CLIs route every path argument through a `_safe_path`
    helper that **rejects any `..` traversal segment** (the canonical CWE-23 escape primitive) and resolves the
    path before use. This is genuine runtime hardening.
  - **Why Snyk still reports them:** Snyk Code's taint engine does **not model custom Python path sanitizers** —
    verified empirically across three remediation rounds (bare `..`-rejection AND `is_relative_to` base
    containment both leave the taint flowing *through* the helper in the reported dataflow). Only replacing the
    operator's path with a hardcoded/allowlisted constant would clear it — which would break the tool's
    legitimate contract (operator chooses where artifacts/graphs are written; the F2 CLI test writes to an
    external `tmp_path`). Contorting a dev tool's output-path contract to satisfy a scanner FP is the wrong
    trade-off.
  - **Disposition:** accepted as documented Low false positives. The `..`-guard stands as the real mitigation.
    If a future decision wants a clean Snyk board, add a `.snyk` ignore policy referencing this note (not done
    now — left as an explicit operator choice).

## Rescan trail
9 (initial) → 5 (after sha256 + `..`-guard) → documented-accepted residual (all Low CWE-23 CLI-path FPs).
Real issues fixed; no Medium/High/Critical at any point.
