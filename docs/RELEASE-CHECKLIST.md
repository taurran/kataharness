# RELEASE-CHECKLIST — KataHarness

The full gauntlet before any tag/release. CI (`.github/workflows/ci.yml`) runs the first
four automatically on every push/PR to `master`; the SAST/SCA + non-Windows legs are the
human pre-tag steps (Snyk needs auth; the symlink install legs need a non-Windows or
Developer-Mode host). Wired 2026-07-12 (health review M-1/T-1/T-2/6d — before this, the
gauntlet had no lint/type/coverage/SCA and no CI, so integration + symlink tests ran only
on human memory).

## Automated (CI + local)

1. **Unit gauntlet** — `cd tools && uv run pytest -m "not integration"` → all green.
2. **Skill validator** — `uv run python validate_skills.py` → `48/0/0`.
3. **Lint** — `uvx ruff check .` (from `tools/`) → clean (production code held clean; tests
   have a looser per-file profile in `pyproject.toml`).
4. **Coverage floor** — `uv run --with pytest-cov pytest -m "not integration" --cov=. --cov-report=term --cov-fail-under=90`.

## Pre-tag (human — not in CI)

5. **Integration tests** — `uv run pytest -m integration` → the real-subprocess / real-git
   proofs (the only non-vacuous proof of the benchmark dual-gate). CI runs these too, but
   confirm locally on a tag candidate.
6. **Non-Windows install pass** — run the suite once under WSL/Linux (or with Windows
   Developer Mode on) so the symlink install/uninstall paths (`test_install_*`) actually
   execute rather than skip — they are platform-skipped on a stock Windows box.
7. **SAST** — Snyk Code over `tools/` (medium+): `snyk_code_scan` → `0`. (Local/manual —
   Snyk auth is not in CI; **S-07 CI exception**: the CI runner is deliberately kept
   secret-free, so authenticated Snyk stays a local pre-tag step, not a CI job.)
8. **SCA** — `sh tools/scripts/sca.sh` (uv export → `uvx pip-audit --strict`) → clean.
   Snyk's SCA resolver can't read the uv-native manifest, so pip-audit over the exported
   lockfile is the wired path.

## Ship

9. **Adversarial review** — a fresh-context `kata-review` (or equivalent) over the full diff
   before merge (D33 no-self-cert; the project's own discipline).
10. **CHANGELOG + version** — dated entry; per-skill semver bumped on modify (`--write` regen).
11. **Tag** — annotated, `v{major}.{minor}.{patch}`; push the tag.
