[CmdletBinding()]
param(
    [switch]$DryRun,
    [ValidateSet('all', 'nsis', 'msi')]
    [string]$BundleTarget = 'all'
)

$ErrorActionPreference = 'Stop'
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $RepositoryRoot '.venv\Scripts\python.exe'
$SidecarBuilder = Join-Path $RepositoryRoot 'backend\scripts\build_sidecar.py'
$SidecarDist = Join-Path $RepositoryRoot 'desktop\sidecar\dist'
$SidecarExecutable = Join-Path $SidecarDist 'codex-flow-server.exe'
$TauriBinaryRoot = Join-Path $RepositoryRoot 'desktop\src-tauri\binaries'
$TauriBinary = Join-Path $RepositoryRoot 'desktop\src-tauri\binaries\codex-flow-server-x86_64-pc-windows-msvc.exe'
$BundleRoot = Join-Path $RepositoryRoot 'desktop\src-tauri\target\release\bundle'
$ReleaseExecutable = Join-Path $RepositoryRoot 'desktop\src-tauri\target\release\codex-flow-desktop.exe'
$BuildLockPath = Join-Path $env:TEMP 'codex-flow-desktop-build.lock'

function Require-Command([string]$Name, [string]$InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "MISSING_PREREQUISITE: $Name is not available on PATH. $InstallHint"
    }
}

function Require-File([string]$Path, [string]$Description) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "MISSING_PROJECT_FILE: $Description not found at $Path."
    }
}

function Invoke-Step([string]$Label, [string]$Executable, [string[]]$Arguments) {
    Write-Output "STEP: $Label"
    Write-Output ("COMMAND: " + $Executable + ' ' + ($Arguments -join ' '))
    if ($DryRun) { return }
    & $Executable @Arguments
    if ($LASTEXITCODE -ne 0) { throw "BUILD_STEP_FAILED: $Label exited with $LASTEXITCODE." }
}

function Assert-NsisPayloadIdentity {
    $installer = Join-Path $BundleRoot 'nsis\Codex Flow_0.1.0_x64-setup.exe'
    Require-File $ReleaseExecutable 'Tauri release executable'
    Require-File $installer 'NSIS installer'

    $inspectionRoot = Join-Path $env:TEMP ('codex-flow-nsis-payload-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Force -Path $inspectionRoot | Out-Null
    try {
        $inspection = Start-Process -FilePath $installer -ArgumentList @('/S', ('/D=' + $inspectionRoot)) -Wait -PassThru
        if ($inspection.ExitCode -ne 0) {
            throw "NSIS_PAYLOAD_INSPECTION_FAILED: installer exited with $($inspection.ExitCode)."
        }
        $payload = Get-ChildItem -LiteralPath $inspectionRoot -Recurse -Filter 'codex-flow-desktop.exe' -File |
            Select-Object -First 1
        if ($null -eq $payload) {
            throw 'NSIS_PAYLOAD_INSPECTION_FAILED: packaged codex-flow-desktop.exe was not found.'
        }
        $releaseHash = (Get-FileHash -LiteralPath $ReleaseExecutable -Algorithm SHA256).Hash
        $payloadHash = (Get-FileHash -LiteralPath $payload.FullName -Algorithm SHA256).Hash
        Write-Output "IDENTITY_GATE: release EXE SHA256 = $releaseHash"
        Write-Output "IDENTITY_GATE: NSIS payload EXE = $($payload.FullName)"
        Write-Output "IDENTITY_GATE: NSIS payload SHA256 = $payloadHash"
        if ($releaseHash -ne $payloadHash) {
            throw 'NSIS_PAYLOAD_IDENTITY_MISMATCH: installer payload differs from the release executable.'
        }
    }
    finally {
        if (Test-Path -LiteralPath $inspectionRoot) {
            Remove-Item -LiteralPath $inspectionRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

Require-Command 'node' 'Install Node.js using the approved project setup before retrying.'
Require-Command 'npm' 'Install npm with the approved Node.js distribution before retrying.'
Require-Command 'cargo' 'Install the authorized Rust toolchain before retrying.'
Require-Command 'rustc' 'Install the authorized Rust toolchain before retrying.'
Require-File $Python 'project Python interpreter'
Require-File $SidecarBuilder 'sidecar build script'
Require-File (Join-Path $RepositoryRoot 'frontend\package.json') 'frontend package manifest'
Require-File (Join-Path $RepositoryRoot 'desktop\src-tauri\tauri.conf.json') 'Tauri configuration'

if (-not $DryRun) {
    & $Python -c 'import PyInstaller'
    if ($LASTEXITCODE -ne 0) { throw 'MISSING_PREREQUISITE: PyInstaller is not available in the project virtual environment.' }
}

Push-Location $RepositoryRoot
$BuildLock = $null
try {
    try {
        $BuildLock = [System.IO.File]::Open($BuildLockPath, [System.IO.FileMode]::OpenOrCreate, [System.IO.FileAccess]::ReadWrite, [System.IO.FileShare]::None)
    }
    catch {
        throw 'BUILD_ALREADY_RUNNING: another Codex Flow desktop build holds the build lock.'
    }
    Invoke-Step 'frontend production build' 'npm' @('--prefix', 'frontend', 'run', 'build')
    Invoke-Step 'PyInstaller sidecar build and Tauri staging' $Python @($SidecarBuilder)
    if (-not $DryRun) {
        Require-File $TauriBinary 'staged target-named sidecar executable'
        Require-File $SidecarExecutable 'single-file PyInstaller sidecar executable'
        Write-Output "ARTIFACT: sidecar executable = $SidecarExecutable"
    }
    $TauriBuildArguments = @('--prefix', 'frontend', 'exec', 'tauri', 'build', '--', '--config', 'desktop/src-tauri/tauri.conf.json')
    if ($BundleTarget -ne 'all') {
        $TauriBuildArguments += @('--bundles', $BundleTarget)
    }
    Write-Output "BUNDLE_TARGET: $BundleTarget"
    Invoke-Step 'Tauri production build' 'npm' $TauriBuildArguments
    if (-not $DryRun -and $BundleTarget -eq 'nsis') {
        Assert-NsisPayloadIdentity
    }

    Write-Output "ARTIFACT: frontend dist = $(Join-Path $RepositoryRoot 'frontend\dist')"
    Write-Output "ARTIFACT: staged sidecar = $TauriBinary"
    Write-Output "ARTIFACT: Tauri bundles = $BundleRoot"
}
finally {
    Pop-Location
    if ($null -ne $BuildLock) {
        $BuildLock.Dispose()
    }
}
