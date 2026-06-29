<#
.SYNOPSIS
    KataHarness uninstaller (thin Windows wrapper).
.DESCRIPTION
    Reverses the KataHarness install by invoking the engine's --uninstall
    verb.  All removal logic lives in the Python engine; this script is
    a thin wrapper.

    USAGE
        .\uninstall.ps1 --platform claude --target-dir C:\path\to\project [--yes]
        # with explicit harness home:
        $env:KATA_HOME = 'C:\path\to\kataharness'
        .\uninstall.ps1 --platform claude --target-dir C:\path\to\project --yes

    ENVIRONMENT VARIABLES
        KATA_HOME    path to the KataHarness home (default: %USERPROFILE%\.kata-home)
        KATA_SRC     local path override (same semantics as install.ps1)

    REVERSAL SCOPE
        Removes flat-linked skills from the host, the settings file, and
        the router stanza from the SUPPLIED --target-dir only.  The harness
        keeps no registry of every project where a stanza was written, so
        other projects' AGENTS.md files are not crawled.  For each
        additional project:
          .\uninstall.ps1 --platform claude --target-dir C:\path\to\other

    Re-running on an already-uninstalled target exits 0 (no-op).
.NOTES
    Requires PowerShell 5.1+ (ships with Windows 10/11).
    Requires uv or Python 3.12+ to run the engine.
#>

$ErrorActionPreference = 'Stop'

# --------------------------------------------------------------------------
# Defaults
# --------------------------------------------------------------------------
$_KataDefaultHome = Join-Path $env:USERPROFILE '.kata-home'

# --------------------------------------------------------------------------
# Resolve harness home (no cloning — harness must already be present)
# --------------------------------------------------------------------------
if ($env:KATA_SRC) {
    $_KataHome = $env:KATA_SRC
} elseif ($env:KATA_HOME -and (Test-Path (Join-Path $env:KATA_HOME 'tools\kata_install.py'))) {
    $_KataHome = $env:KATA_HOME
} elseif (Test-Path (Join-Path $_KataDefaultHome 'tools\kata_install.py')) {
    $_KataHome = $_KataDefaultHome
} else {
    Write-Error 'kata-uninstall: KataHarness home not found. Set $env:KATA_HOME to your install path, or $env:KATA_SRC for a local path.'
    exit 1
}

if (-not (Test-Path (Join-Path "$_KataHome" 'tools\kata_install.py'))) {
    Write-Error "kata-uninstall: tools/kata_install.py not found in $_KataHome"
    exit 1
}

# --------------------------------------------------------------------------
# Default --platform to 'claude' when not supplied
# --------------------------------------------------------------------------
$_PassArgs = $args
if ($args -notcontains '--platform') {
    $_PassArgs = @('--platform', 'claude') + $args
}

# --------------------------------------------------------------------------
# Invoke the engine's --uninstall verb; propagate its exit code.
# --------------------------------------------------------------------------
$_OrigLocation = Get-Location
Set-Location "$_KataHome"
try {
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        & uv run python tools/kata_install.py --uninstall @_PassArgs
    } elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
        & python3 tools/kata_install.py --uninstall @_PassArgs
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python tools/kata_install.py --uninstall @_PassArgs
    } else {
        Write-Error 'kata-uninstall: Python not found. Install uv (https://docs.astral.sh/uv/) or Python 3.12+.'
        exit 1
    }
    $_ExitCode = $LASTEXITCODE
} finally {
    Set-Location "$_OrigLocation"
}
exit $_ExitCode
