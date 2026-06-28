# Config / build / context profile — debug-mode overlay

A prose lens over `[[kata-tdd]]` (debug fix-loop) and `[[kata-diagnose]]` (diagnosis) for the
**build / config / IaC-adjacent** surface of a codebase — the files that are not application source but
determine how the application builds, runs, and is wired. Guidance only — it relaxes no gate. This profile
is **additive**: inject it alongside a language profile when a task touches both.

Scope examples: `Dockerfile` / `compose.yaml`, `Makefile`, `*.toml` (`pyproject.toml`, `Cargo.toml`),
`package.json` / lockfiles, `*.gradle[.kts]` / `pom.xml`, `*.yaml`/`*.yml` config and CI
(`.github/workflows/*`), `.env`(.example), `*.ini`/`*.cfg`, `tsconfig.json`, `*.properties`.

> **IaC boundary.** True infrastructure-as-code (Terraform `.tf`/`.hcl`, CloudFormation/CDK) is owned by
> the dedicated **`[[kata-iac-terraform]]`** / **`[[kata-iac-cloudformation]]`** specialists with their own
> safety gate (`protocol/iac-safety.md`). This profile covers *build/config context*, not the IaC gate — if
> a task touches real IaC, defer that surface to the IaC specialists; do not duplicate their gate here.

## Idioms that matter when fixing without drift
- **Config is behavior.** A changed default, a flipped feature flag, a bumped dependency version, or a
  reordered build step changes runtime behavior as surely as a code edit — and is **easy to drift on**
  because there is often no unit test pinning it. Treat config edits with the same caution as code.
- **Pin, don't float.** Prefer the minimal, explicit change. Loosening a version constraint (`^`, `~`, `*`)
  or removing a lockfile pin can pull in a behavior change on the next install — a hidden regression.
- **Reproducibility** — preserve lockfiles (`package-lock.json`, `uv.lock`, `Cargo.lock`, `poetry.lock`,
  `go.sum`). A fix that regenerates a lockfile may quietly upgrade transitive deps; keep the diff scoped.
- **Secrets** — never inline a secret into a config file as part of a fix; keep them in env/`.env`(ignored)
  or a vault. Surfacing a previously-hidden secret is a security regression.
- **Env-specific config** — changing a value used across environments (dev/CI/prod) can fix one and break
  another. Scope the change to the right layer/profile.

## "Test-runner" conventions (objective signals for config)
Config rarely has unit tests, so lean on **deterministic validators** as the pass/fail signal:
- **Build / install**: `make`, `npm ci` / `pnpm i --frozen-lockfile`, `cargo build`, `dotnet build`,
  `./gradlew build` — a clean build is the primary signal that config still wires up.
- **Schema / lint**: `docker build` (or `hadolint` for Dockerfiles), `yamllint`, `actionlint` for GitHub
  workflows, `tsc --noEmit` for `tsconfig`, JSON-schema validators, `terraform validate` / `cfn-lint` where
  the IaC specialists own the gate.
- **Diff review**: for a config-only fix, the *diff itself* is much of the evidence — read it carefully and
  confirm only the intended key changed.

## Common failure modes (diagnosis hooks)
- **Dependency / version skew** — a transitive upgrade changes behavior; lockfile vs manifest drift.
- **Path / working-directory** assumptions in scripts and CI; relative paths that differ per runner.
- **Env-var precedence** — which layer wins (shell vs `.env` vs CI secret vs default); missing var → silent
  empty string.
- **Build-step ordering / caching** — stale caches masking or causing failures; non-deterministic builds.
- **Cross-platform** — line endings (CRLF/LF), case-sensitive vs insensitive filesystems, shell differences.
- **Docker** — base-image tag drift (`latest`), layer caching, build-arg vs runtime-env confusion,
  `COPY` context surprises.

## Diagnosis loop (feedback-first)
Reproduce in the cleanest possible environment: a from-scratch `--frozen`/`ci` install, a no-cache build
(`docker build --no-cache`, `cargo build` after `cargo clean`), and run the CI workflow locally where
possible (`act` for GitHub Actions) to get a fast deterministic loop. Bisect config changes one key at a
time. Compare resolved/effective config (e.g. `npm config ls`, `pip config list`, rendered compose) against
the intended state.

## Characterization / drift hints
- The drift signal for config is often the **resolved/effective output** (the rendered config, the resolved
  dependency tree, the produced build artifact's manifest) — snapshot that, scrubbing volatile fields
  (timestamps, build hashes) so the gate compares intent, not noise.
- Keep the fix **footprint-scoped**: one config concern per change, so the behavioral drift gate can
  attribute any baseline-green→red transition to the right edit.
