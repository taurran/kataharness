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
        .\update.ps1 --clear-stale-locks           # delete stale .git ref locks (printed), then update
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
$_clearStaleLocks = $false
$_factoryReset = $false
$_hard = $false
$_yes = $false
$_engineArgs = @()
foreach ($a in $args) {
    if ($a -eq '--check') { $_check = $true }
    elseif ($a -eq '--discard-local') { $_discardLocal = $true }
    elseif ($a -eq '--clear-stale-locks') { $_clearStaleLocks = $true }
    elseif ($a -eq '--factory-reset' -or $a -eq '--reinstall') { $_factoryReset = $true; $_engineArgs += '--factory-reset' }
    elseif ($a -eq '--hard') { $_hard = $true; $_engineArgs += '--hard' }
    elseif ($a -eq '--yes' -or $a -eq '--non-interactive') { $_yes = $true; $_engineArgs += '--non-interactive' }
    else { $_engineArgs += $a }
}

# Default --platform to 'claude' when not supplied (mirror install.ps1).
if ($_engineArgs -notcontains '--platform') {
    $_engineArgs = @('--platform', 'claude') + $_engineArgs
}

# Pass the git ref through so the engine stamps the ACTUAL ref (not hardcoded
# "master") into .kata-version - stamp-ref honesty (DESIGN B2 --ref).
$_engineArgs += @('--ref', $_KataRef)

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
    # 'throw' (not 'exit'): piped via `irm | iex` this runs in the caller's
    # session, where 'exit' would terminate the host WINDOW. 'throw' surfaces
    # the error without closing it; as a file it still stops with a failure code.
    throw 'kata-update: KataHarness home not found. Set KATA_HOME or KATA_SRC, or run install.ps1 first.'
}
if (-not (Test-Path (Join-Path $_home 'tools\kata_install.py'))) {
    throw "kata-update: tools/kata_install.py not found in $_home"
}
# --------------------------------------------------------------------------
# Helpers. No redirection of native git stderr (PS 5.1 wraps it in ErrorRecords
# under Stop preference); gate on LASTEXITCODE and use --quiet probes instead.
# --------------------------------------------------------------------------
function Test-GitClone {
    if (-not (Test-Path '.git' -PathType Container)) { return $false }
    git remote get-url origin | Out-Null
    return ($LASTEXITCODE -eq 0)
}

# PS 5.1 $ErrorActionPreference = 'Stop' does NOT trip on native nonzero exits,
# so every git call that matters is gated on $LASTEXITCODE via this helper.
function Assert-GitOk {
    param([string]$Verb)
    if ($LASTEXITCODE -ne 0) {
        throw "kata-update: git $Verb failed (exit $LASTEXITCODE)"
    }
}

# Resolve the reset target for KATA_REF (mirror update.sh's resolution chain):
# origin/<ref>, else refs/tags/<ref>, else <ref> (sha). Throws when the ref
# resolves nowhere — never silently returns an unresolvable target.
function Get-ResetTarget {
    foreach ($_cand in @("origin/$_KataRef", "refs/tags/$_KataRef", $_KataRef)) {
        git rev-parse --verify --quiet $_cand | Out-Null
        if ($LASTEXITCODE -eq 0) { return $_cand }
    }
    throw "kata-update: ref '$_KataRef' not found (tried origin/$_KataRef, refs/tags/$_KataRef, $_KataRef)"
}

# 3-leg checkout fallback (mirror update.sh): branch <ref>, else detached
# origin/<ref>, else detached <ref>. Failed legs may print git errors to
# stderr (not redirected — see helper comment above); only all three legs
# failing throws.
function Invoke-GitCheckout {
    git checkout --quiet $_KataRef
    if ($LASTEXITCODE -eq 0) { return }
    git checkout --quiet --detach "origin/$_KataRef"
    if ($LASTEXITCODE -eq 0) { return }
    git checkout --quiet --detach $_KataRef
    Assert-GitOk "checkout '$_KataRef'"
}

# --------------------------------------------------------------------------
# D157 - stale ref-lock guard + post-fetch remote-truth verification.
# Observed failure (2026-07-12b): a stale .git\refs\remotes\origin\master.lock
# (left by an interrupted fetch) made 'git fetch' SILENTLY fail to advance the
# remote-tracking ref; rev-parse returned the STALE sha and the hard reset
# "advanced" to the OLD sha - a silent-stale-install. Two guards close the
# class: Assert-NoStaleGitLocks (pre-fetch) and Assert-RemoteTruth (post-fetch).
# --------------------------------------------------------------------------
function Get-StaleGitLocks {
    $_locks = @()
    $_remotesDir = '.git\refs\remotes'
    if (Test-Path $_remotesDir -PathType Container) {
        $_locks += @(Get-ChildItem -Path $_remotesDir -Recurse -File -Force -Filter '*.lock' |
            ForEach-Object { $_.FullName })
    }
    $_packedLock = '.git\packed-refs.lock'
    if (Test-Path $_packedLock -PathType Leaf) {
        $_locks += @((Get-Item -Force $_packedLock).FullName)
    }
    # No comma-wrap: an empty result must unroll to a zero-length pipeline so the
    # caller's @() sees Count 0 (a `,@()` here would smuggle one empty element).
    return $_locks
}

# PRE-FETCH: abort on any stale lock (printing each path + age); delete only
# with the explicit --clear-stale-locks flag, printing every removed path -
# never silently.
function Assert-NoStaleGitLocks {
    $_locks = @(Get-StaleGitLocks)
    if ($_locks.Count -eq 0) { return }
    if ($_clearStaleLocks) {
        if ($_check) {
            Write-Host 'kata-update: ABORT - --check is a no-mutation path; stale lock(s) present but NOT deleted:'
            foreach ($_lk in $_locks) { Write-Host "  $_lk" }
            Write-Host 'Re-run --clear-stale-locks WITHOUT --check to delete them.'
            throw 'kata-update: ABORT - --check with --clear-stale-locks refuses to mutate'
        }
        Write-Host 'kata-update: --clear-stale-locks - removing stale git lock file(s):'
        foreach ($_lk in $_locks) {
            Write-Host "  removing $_lk"
            Remove-Item -Force -Confirm:$false $_lk
        }
        return
    }
    Write-Host 'kata-update: ABORT - stale git lock file(s) detected before fetch:'
    $_now = Get-Date
    foreach ($_lk in $_locks) {
        $_ageSec = [int](($_now - (Get-Item -Force $_lk).LastWriteTime).TotalSeconds)
        Write-Host "  $_lk (age: ${_ageSec}s)"
    }
    Write-Host ''
    Write-Host 'An interrupted fetch can leave these behind; fetching over them SILENTLY'
    Write-Host 'fails to advance the remote-tracking ref (silent-stale-install, D157).'
    Write-Host 'Confirm no other git process is running, then re-run with --clear-stale-locks.'
    throw 'kata-update: ABORT - stale git lock file(s); re-run with --clear-stale-locks'
}

# POST-FETCH: one 'git ls-remote origin <ref>' call confirms the local
# remote-tracking target equals the REAL remote sha BEFORE any reset. A pinned
# sha target has no remote ref to verify (immutable) - skipped with a NOTE.
function Assert-RemoteTruth {
    param([string]$Target)
    $_lsRef = $null
    if ($Target -eq "origin/$_KataRef") { $_lsRef = "refs/heads/$_KataRef" }
    elseif ($Target -eq "refs/tags/$_KataRef") { $_lsRef = "refs/tags/$_KataRef" }
    if (-not $_lsRef) {
        Write-Host "kata-update: NOTE - target '$Target' is a pinned sha; ls-remote verification not applicable."
        return
    }
    $_localTargetSha = (git rev-parse --verify --quiet $Target)
    if ($LASTEXITCODE -ne 0 -or -not $_localTargetSha) {
        throw "kata-update: ABORT - could not resolve local target '$Target' after fetch."
    }
    $_lsOut = @(git ls-remote origin $_lsRef)
    if ($LASTEXITCODE -ne 0) {
        throw 'kata-update: ABORT - git ls-remote origin failed immediately after a successful fetch; that is suspicious (the network was just reachable) - refusing to proceed.'
    }
    $_remoteSha = $null
    foreach ($_line in $_lsOut) {
        if (-not $_line) { continue }
        $_parts = "$_line" -split "`t"
        if ($_parts.Count -ge 2 -and $_parts[1] -eq $_lsRef) { $_remoteSha = $_parts[0]; break }
    }
    if (-not $_remoteSha) {
        throw "kata-update: ABORT - ls-remote returned no sha for '$_lsRef' on origin."
    }
    if ($_localTargetSha -ne $_remoteSha) {
        Write-Host "  local  $Target = $_localTargetSha"
        Write-Host "  remote $_lsRef = $_remoteSha"
        throw 'kata-update: ABORT - fetch did not advance the remote-tracking ref - likely a stale ref lock; re-run with --clear-stale-locks'
    }
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
        throw 'kata-update: Python not found. Install uv (https://docs.astral.sh/uv/) or Python 3.12+.'
    }
    # Propagate the engine's exit code WITHOUT 'exit' — under `irm | iex` this script
    # runs in the caller's session, so a bare 'exit' (even 'exit 0') closes the host
    # WINDOW. Set $LASTEXITCODE for the download-then-run path; 'throw' only on a real
    # failure (surfaces in red, window stays open). Success simply falls off the end.
    $_ExitCode = $LASTEXITCODE
    $global:LASTEXITCODE = $_ExitCode
    if ($_ExitCode -ne 0) {
        throw "kata-update: engine exited with code $_ExitCode"
    }
}

# --------------------------------------------------------------------------
# All git + engine work runs inside the harness home; restore the caller's
# location on every exit path (mirror install.ps1 / uninstall.ps1).
# --------------------------------------------------------------------------
$_OrigLocation = Get-Location
Set-Location $_home
try {

# --------------------------------------------------------------------------
# FACTORY-RESET path (engine re-links; bootstrap owns the optional --hard reset)
# --------------------------------------------------------------------------
if ($_factoryReset) {
    # Best-effort SHA for the version stamp; stays 'unknown' if HEAD is
    # unresolvable (mirror update.sh's `|| printf 'unknown'`).
    $_gitSha = 'unknown'
    if (Test-GitClone) {
        $_headSha = (git rev-parse --verify --quiet HEAD)
        if ($LASTEXITCODE -eq 0 -and $_headSha) { $_gitSha = $_headSha }
    }

    if ($_hard) {
        if (-not $_yes) {
            if ([Console]::IsInputRedirected) {
                throw 'kata-update: --factory-reset --hard requires --yes in non-interactive mode.'
            }
            $confirm = Read-Host 'kata-update: --factory-reset --hard will CLEAR the overlay store and reset the base tree. Type YES to continue'
            if ($confirm -ne 'YES') { throw 'kata-update: aborted.' }
        }
        if (Test-GitClone) {
            Assert-NoStaleGitLocks
            Write-Host "kata-update: fetching and resetting to $_KataRef ..."
            git fetch origin
            Assert-GitOk 'fetch'
            Invoke-GitCheckout
            $_target = Get-ResetTarget
            git reset --hard $_target
            Assert-GitOk "reset --hard '$_target'"
            $_gitSha = (git rev-parse HEAD)
            Assert-GitOk 'rev-parse HEAD'
        }
    }
    Invoke-Engine (@('--git-sha', $_gitSha) + $_engineArgs)
    # Invoke-Engine throws on failure and sets $global:LASTEXITCODE on success;
    # return here so the update path below does not execute after a factory reset.
    return
}

# --------------------------------------------------------------------------
# UPDATE path - minor-c: requires a git-clone home with a fetchable origin
# --------------------------------------------------------------------------
if (-not (Test-GitClone)) {
    throw 'kata-update: this home is not a git clone - re-install to update'
}

# D157: stale-lock guard runs BEFORE the fetch
Assert-NoStaleGitLocks
Write-Host 'kata-update: fetching origin ...'
git fetch origin
Assert-GitOk 'fetch'
$_localSha = (git rev-parse HEAD)
Assert-GitOk 'rev-parse HEAD'
$_target = Get-ResetTarget
$_remoteSha = (git rev-parse --verify --quiet $_target)
if ($LASTEXITCODE -ne 0 -or -not $_remoteSha) {
    throw "kata-update: could not resolve update target '$_target'"
}
# Peel annotated tags to their COMMIT for HEAD comparisons: `reset --hard` lands
# HEAD on the peeled commit, so comparing HEAD against a tag-OBJECT sha would
# false-abort every annotated-tag update (adval env-hardening finding 1).
# Assert-RemoteTruth still compares UNPEELED shas (internally consistent).
$_remoteCommit = (git rev-parse --verify --quiet "$_target^{commit}")
if ($LASTEXITCODE -ne 0 -or -not $_remoteCommit) { $_remoteCommit = $_remoteSha }

# --check: report current vs available, no mutation
if ($_check) {
    $_lShort = $_localSha.Substring(0, [Math]::Min(12, $_localSha.Length))
    $_rShort = $_remoteCommit.Substring(0, [Math]::Min(12, $_remoteCommit.Length))
    if ($_localSha -eq $_remoteCommit) {
        Write-Host "kata-update --check: already current at $_lShort (ref: $_KataRef)"
    } else {
        Write-Host 'kata-update --check: update available'
        Write-Host "  current:   $_lShort"
        Write-Host "  available: $_rShort (ref: $_KataRef)"
    }
    $global:LASTEXITCODE = 0
    return
}

# M2 - dirty-tree guard (tracked files only; untracked '??' and ignored are safe)
$_dirtyLines = @((git status --porcelain) | Where-Object { $_ -and (-not $_.StartsWith('??')) })
if ($_dirtyLines.Count -gt 0) {
    if (-not $_discardLocal) {
        Write-Host 'kata-update: ABORT - tracked base files have local modifications:'
        $_dirtyLines | ForEach-Object { Write-Host $_ }
        Write-Host ''
        Write-Host 'Re-run with --discard-local to overwrite them, or commit/stash first.'
        throw 'kata-update: ABORT - dirty base; re-run with --discard-local'
    }
    Write-Host 'kata-update: WARNING - --discard-local: discarding modifications to tracked base files:'
    $_dirtyLines | ForEach-Object { Write-Host $_ }
}

# D157 POST-FETCH truth check - BEFORE any checkout/reset: the local
# remote-tracking target must equal the REAL remote sha (one ls-remote call).
Assert-RemoteTruth $_target

Invoke-GitCheckout
git reset --hard $_target
Assert-GitOk "reset --hard '$_target'"
$_newSha = (git rev-parse HEAD)
Assert-GitOk 'rev-parse HEAD'
# D157(c) - the advancement message prints ONLY on true advancement: HEAD must
# equal the verified target sha (pinned to the ls-remote truth above).
if ($_newSha -ne $_remoteCommit) {
    throw "kata-update: ABORT - reset did not land on the verified sha (HEAD $_newSha != $_remoteCommit)."
}
$_nShort = $_newSha.Substring(0, [Math]::Min(12, $_newSha.Length))
Write-Host "kata-update: advanced to $_nShort (ref: $_KataRef)"

Invoke-Engine (@('--update', '--git-sha', $_newSha) + $_engineArgs)

} finally {
    Set-Location $_OrigLocation
}
