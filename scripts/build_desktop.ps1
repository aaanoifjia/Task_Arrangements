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
try {
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

    Write-Output "ARTIFACT: frontend dist = $(Join-Path $RepositoryRoot 'frontend\dist')"
    Write-Output "ARTIFACT: staged sidecar = $TauriBinary"
    Write-Output "ARTIFACT: Tauri bundles = $BundleRoot"
}
finally {
    Pop-Location
}
