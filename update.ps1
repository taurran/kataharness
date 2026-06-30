<#
.SYNOPSIS
    KataHarness update / factory-reset Windows bootstrap (mirror of update.sh).
.DESCRIPTION
    Fetches the harness home to KATA_REF, fast-forwards the tracked base, then
    invokes tools/kata_install.py --update --git-sha <sha>.  ALL git lives here;
    the Python engine never calls git (DESIGN Invariant 3).

    USAGE
        & "$env:USERPROFILE\.kata-home\update.ps1"
        irm https://raw.githubusercontent.com/taurran/kataharness/master/update.ps1 | iex
        .\update.ps1 --check                       # report available, no mutation
        .\update.ps1 --discard-local               # proceed past a dirty-base abort
        .\update.ps1 --factory-reset [--hard] [--yes]

    ENVIRONMENT VARIABLES
        KATA_HOME   existing harness home (default: ~/.kata-home)
        KATA_SRC    local path override - skips all git (offline / copy homes)
        KATA_REF    git ref / branch / tag to update to (default: master)

    SECURITY - irm | iex tradeoff (plain statement, no overclaim)
        The piped form executes bytes as they stream - nothing to hash first.
        A checksum protects the download-THEN-run path; it does NOT protect the
        pipe. Mitigations: stable URL, short readable script, KATA_REF pinning.
        See docs/SETUP.md for the full tradeoff discussion.

    M2 (dirty-base guard): a home with local TRACKED modifications ABORTS by
    default; pass --discard-local to overwrite them. Never silently clobbers.
.NOTES
    Requires PowerShell 5.1+, git, and uv or Python 3.12+.
#>

$ErrorActionPreference = 'Stop'

$_KataDefaultHome = Join-Path $env:USERPROFILE '.kata-home'
$_KataRef = if ($env:KATA_REF) { $env:KATA_REF } else { 'master' }

# --------------------------------------------------------------------------
# Parse our own flags; collect the rest as engine pass-through
# --------------------------------------------------------------------------
$_check = $false
$_discardLocal = $false
$_factoryReset = $false
$_hard = $false
$_yes = $false
$_engineArgs = @()
foreach ($a in $args) {
    if ($a -eq '--check') { $_check = $true }
    elseif ($a -eq '--discard-local') { $_discardLocal = $true }
    elseif ($a -eq '--factory-reset' -or $a -eq '--reinstall') { $_factoryReset = $true; $_engineArgs += '--factory-reset' }
    elseif ($a -eq '--hard') { $_hard = $true; $_engineArgs += '--hard' }
    elseif ($a -eq '--yes' -or $a -eq '--non-interactive') { $_yes = $true; $_engineArgs += '--non-interactive' }
    else { $_engineArgs += $a }
}

# Default --platform to 'claude' when not supplied (mirror install.ps1).
if ($_engineArgs -notcontains '--platform') {
    $_engineArgs = @('--platform', 'claude') + $_engineArgs
}

# --------------------------------------------------------------------------
# Resolve the harness home (no cloning - must already be present)
# --------------------------------------------------------------------------
if ($env:KATA_SRC) {
    $_home = $env:KATA_SRC
} elseif ($env:KATA_HOME -and (Test-Path (Join-Path $env:KATA_HOME 'tools\kata_install.py'))) {
    $_home = $env:KATA_HOME
} elseif (Test-Path (Join-Path $_KataDefaultHome 'tools\kata_install.py')) {
    $_home = $_KataDefaultHome
} else {
    Write-Error 'kata-update: KataHarness home not found. Set KATA_HOME or KATA_SRC.'
    exit 1
}
if (-not (Test-Path (Join-Path $_home 'tools\kata_install.py'))) {
    Write-Error "kata-update: tools/kata_install.py not found in $_home"
    exit 1
}
Set-Location $_home

# --------------------------------------------------------------------------
# Helpers. No redirection of native git stderr (PS 5.1 wraps it in ErrorRecords
# under Stop preference); gate on LASTEXITCODE and use --quiet probes instead.
# --------------------------------------------------------------------------
function Test-GitClone {
    if (-not (Test-Path '.git' -PathType Container)) { return $false }
    git remote get-url origin | Out-Null
    return ($LASTEXITCODE -eq 0)
}

# Resolve the reset target for KATA_REF: prefer origin/<ref>, else <ref> (tag/sha).
function Get-ResetTarget {
    git rev-parse --verify --quiet "origin/$_KataRef" | Out-Null
    if ($LASTEXITCODE -eq 0) { return "origin/$_KataRef" }
    return $_KataRef
}

function Invoke-Engine {
    param([string[]]$EngineArgs)
    if (Get-Command uv -ErrorAction SilentlyContinue) {
        & uv run python tools/kata_install.py @EngineArgs
    } elseif (Get-Command python3 -ErrorAction SilentlyContinue) {
        & python3 tools/kata_install.py @EngineArgs
    } elseif (Get-Command python -ErrorAction SilentlyContinue) {
        & python tools/kata_install.py @EngineArgs
    } else {
        Write-Error 'kata-update: Python not found. Install uv or Python 3.12+.'
        exit 1
    }
    exit $LASTEXITCODE
}

# --------------------------------------------------------------------------
# FACTORY-RESET path (engine re-links; bootstrap owns the optional --hard reset)
# --------------------------------------------------------------------------
if ($_factoryReset) {
    $_gitSha = 'unknown'
    if (Test-GitClone) { $_gitSha = (git rev-parse HEAD) }

    if ($_hard) {
        if (-not $_yes) {
            if ([Console]::IsInputRedirected) {
                Write-Error 'kata-update: --factory-reset --hard requires --yes in non-interactive mode.'
                exit 1
            }
            $confirm = Read-Host 'kata-update: --factory-reset --hard will CLEAR the overlay store and reset the base tree. Type YES to continue'
            if ($confirm -ne 'YES') { Write-Error 'kata-update: aborted.'; exit 1 }
        }
        if (Test-GitClone) {
            Write-Host "kata-update: fetching and resetting to $_KataRef ..."
            git fetch origin
            $_target = Get-ResetTarget
            git checkout $_KataRef
            git reset --hard $_target
            $_gitSha = (git rev-parse HEAD)
        }
    }
    Invoke-Engine (@('--git-sha', $_gitSha) + $_engineArgs)
}

# --------------------------------------------------------------------------
# UPDATE path - minor-c: requires a git-clone home with a fetchable origin
# --------------------------------------------------------------------------
if (-not (Test-GitClone)) {
    Write-Host 'kata-update: this home is not a git clone - re-install to update'
    exit 1
}

Write-Host 'kata-update: fetching origin ...'
git fetch origin
$_localSha = (git rev-parse HEAD)
$_target = Get-ResetTarget
$_remoteSha = (git rev-parse $_target)

# --check: report current vs available, no mutation
if ($_check) {
    $_lShort = $_localSha.Substring(0, [Math]::Min(12, $_localSha.Length))
    $_rShort = $_remoteSha.Substring(0, [Math]::Min(12, $_remoteSha.Length))
    if ($_localSha -eq $_remoteSha) {
        Write-Host "kata-update --check: already current at $_lShort (ref: $_KataRef)"
    } else {
        Write-Host 'kata-update --check: update available'
        Write-Host "  current:   $_lShort"
        Write-Host "  available: $_rShort (ref: $_KataRef)"
    }
    exit 0
}

# M2 - dirty-tree guard (tracked files only; untracked '??' and ignored are safe)
$_dirtyLines = @((git status --porcelain) | Where-Object { $_ -and (-not $_.StartsWith('??')) })
if ($_dirtyLines.Count -gt 0) {
    if (-not $_discardLocal) {
        Write-Host 'kata-update: ABORT - tracked base files have local modifications:'
        $_dirtyLines | ForEach-Object { Write-Host $_ }
        Write-Host ''
        Write-Host 'Re-run with --discard-local to overwrite them, or commit/stash first.'
        exit 1
    }
    Write-Host 'kata-update: WARNING - --discard-local: discarding modifications to tracked base files:'
    $_dirtyLines | ForEach-Object { Write-Host $_ }
}

git checkout $_KataRef
git reset --hard $_target
$_newSha = (git rev-parse HEAD)
$_nShort = $_newSha.Substring(0, [Math]::Min(12, $_newSha.Length))
Write-Host "kata-update: advanced to $_nShort (ref: $_KataRef)"

Invoke-Engine (@('--update', '--git-sha', $_newSha) + $_engineArgs)
