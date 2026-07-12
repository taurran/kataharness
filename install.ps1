<#
.SYNOPSIS
    KataHarness one-command Windows bootstrap.
.DESCRIPTION
    Resolves (or clones) the KataHarness home, then forwards all supplied
    arguments to tools/kata_install.py.  All install logic lives in the
    Python engine; this script is a thin wrapper.

    QUICK START
        irm https://raw.githubusercontent.com/taurran/kataharness/master/install.ps1 | iex
        # with args (download-then-run path — also checksum-verifiable):
        irm .../install.ps1 -OutFile install.ps1; .\install.ps1 --platform claude

    ENVIRONMENT VARIABLES
        KATA_HOME        reuse an existing harness home (skip the clone)
        KATA_REF         git tag / branch / SHA to pin  (default: master)
        KATA_SRC         local filesystem path; skips all network fetches
                         (offline smoke-test: $env:KATA_SRC = 'C:\Dev\KataHarness')
        KATA_PARENT_DIR  default parent project folder (forwarded to engine)
        KATA_VAULT_DIR   vault location (forwarded to engine)

    SECURITY — irm | iex tradeoff (plain statement, no overclaim)
        The piped form executes bytes as they stream — nothing to hash first.
        A checksum protects the download-THEN-run path (fetch the script,
        verify its SHA, then execute); it does NOT protect the piped form.
        Mitigations shipped here:
          • stable URL (raw.githubusercontent.com/taurran/kataharness/master/…)
          • short, readable script
          • KATA_REF env var for version-pinning to a specific tag or commit
        Audit-friendly alternatives:
          • git clone https://github.com/taurran/kataharness.git  (inspect first)
          • irm .../install.ps1 -OutFile install.ps1; notepad install.ps1; .\install.ps1
          • GitHub 'Use this template' button  (no remote script at all)
        See docs/SETUP.md for the full tradeoff discussion.

    All positional/named arguments are forwarded to tools/kata_install.py.
    Defaults --platform to 'claude' when no --platform arg is supplied.
.NOTES
    Requires PowerShell 5.1+ (ships with Windows 10/11).
    Requires git for the clone path; uv or Python 3.12+ to run the engine.
#>

$ErrorActionPreference = 'Stop'

# --------------------------------------------------------------------------
# Defaults
# --------------------------------------------------------------------------
$_KataRepoUrl     = 'https://github.com/taurran/kataharness.git'
$_KataDefaultHome = Join-Path $env:USERPROFILE '.kata-home'
$_KataRef         = if ($env:KATA_REF) { $env:KATA_REF } else { 'master' }

# --------------------------------------------------------------------------
# Step 1 — resolve the harness home (priority order)
# --------------------------------------------------------------------------
if ($env:KATA_SRC) {
    $_KataHome = $env:KATA_SRC
} elseif ($env:KATA_HOME -and (Test-Path (Join-Path $env:KATA_HOME 'tools\kata_install.py'))) {
    # KATA_HOME already contains a valid harness — idempotent, no re-clone.
    $_KataHome = $env:KATA_HOME
} elseif (Test-Path (Join-Path $_KataDefaultHome 'tools\kata_install.py')) {
    # Default home present — idempotent, no re-clone.
    $_KataHome = $_KataDefaultHome
} else {
    # Clone to the default home.  The .git inside is legitimate repo metadata.
    $_KataHome = $_KataDefaultHome
    Write-Host "kata-install: cloning KataHarness (ref=$_KataRef) to $_KataHome ..."
    & git clone --branch "$_KataRef" --depth 1 "$_KataRepoUrl" "$_KataHome"
    # PS 5.1 Stop preference does NOT trip on native nonzero exits; gate on
    # $LASTEXITCODE so a failed clone cannot fall through to false success.
    if ($LASTEXITCODE -ne 0) {
        throw "kata-install: git clone failed (exit $LASTEXITCODE; ref=$_KataRef, url=$_KataRepoUrl)"
    }
    Write-Host 'kata-install: clone complete.'
}

# --------------------------------------------------------------------------
# Step 2 — sanity check
# --------------------------------------------------------------------------
if (-not (Test-Path (Join-Path "$_KataHome" 'tools\kata_install.py'))) {
    # 'throw' (not 'exit'): piped via `irm | iex` this runs in the caller's
    # session, where 'exit' would terminate the host WINDOW. 'throw' surfaces
    # the error without closing it; as a file it still stops with a failure code.
    throw "kata-install: tools/kata_install.py not found in $_KataHome"
}

# --------------------------------------------------------------------------
# Step 3 — default --platform to 'claude' when not supplied
# --------------------------------------------------------------------------
$_PassArgs = $args
if ($args -notcontains '--platform') {
    $_PassArgs = @('--platform', 'claude') + $args
}

# --------------------------------------------------------------------------
# Steps 4–5 — locate Python → invoke engine → propagate exit code
# All install logic lives in the engine; this script adds none of its own.
# --------------------------------------------------------------------------
$_OrigLocation = Get-Location
Set-Location "$_KataHome"
try {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        & uv run python tools/kata_install.py @_PassArgs
    } elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
        & python3 tools/kata_install.py @_PassArgs
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python tools/kata_install.py @_PassArgs
    } else {
        throw 'kata-install: Python not found. Install uv (https://docs.astral.sh/uv/) or Python 3.12+.'
    }
    $_ExitCode = $LASTEXITCODE
} finally {
    Set-Location "$_OrigLocation"
}

# Propagate the engine's exit code WITHOUT 'exit' — under `irm | iex` this script
# runs in the caller's session, so a bare 'exit' (even 'exit 0') closes the host
# WINDOW. Set $LASTEXITCODE for the download-then-run path; 'throw' only on a real
# failure (surfaces in red, window stays open). Success simply falls off the end.
$global:LASTEXITCODE = $_ExitCode
if ($_ExitCode -ne 0) {
    throw "kata-install: engine exited with code $_ExitCode"
}
