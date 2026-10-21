[CmdletBinding()]
param(
    [switch]$Check
)

$ErrorActionPreference = 'Stop'
$RepositoryRoot = Split-Path -Parent $PSScriptRoot

function Require-Command([string]$Name, [string]$InstallHint) {
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "MISSING_PREREQUISITE: $Name is not available on PATH. $InstallHint"
    }
}

Require-Command 'node' 'Install Node.js using the approved project setup before retrying.'
Require-Command 'npm' 'Install npm with the approved Node.js distribution before retrying.'
Require-Command 'cargo' 'Install the authorized Rust toolchain before retrying.'
Require-Command 'rustc' 'Install the authorized Rust toolchain before retrying.'

$Python = Join-Path $RepositoryRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
    throw "MISSING_PREREQUISITE: project Python interpreter not found at $Python. Create the project virtual environment before retrying."
}

$FrontendPackage = Join-Path $RepositoryRoot 'frontend\package.json'
$TauriConfig = Join-Path $RepositoryRoot 'desktop\src-tauri\tauri.conf.json'
if (-not (Test-Path -LiteralPath $FrontendPackage -PathType Leaf)) {
    throw "MISSING_PROJECT_FILE: frontend package manifest not found at $FrontendPackage."
}
if (-not (Test-Path -LiteralPath $TauriConfig -PathType Leaf)) {
    throw "MISSING_PROJECT_FILE: Tauri configuration not found at $TauriConfig."
}

if ($Check) {
    Write-Output 'CHECK PASS: desktop prerequisites and project files are available.'
    exit 0
}

Push-Location (Join-Path $RepositoryRoot 'frontend')
try {
    & npm run build
    if ($LASTEXITCODE -ne 0) { throw "FRONTEND_BUILD_FAILED: npm run build exited with $LASTEXITCODE." }

    & npm exec tauri dev -- --config ../desktop/src-tauri/tauri.conf.json
    if ($LASTEXITCODE -ne 0) { throw "TAURI_DEV_FAILED: tauri dev exited with $LASTEXITCODE." }
}
finally {
    Pop-Location
}
