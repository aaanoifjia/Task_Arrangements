[CmdletBinding()]
param(
    [Parameter()]
    [string]$ManifestPath = (Join-Path $PSScriptRoot "..\docs\windows-build-artifacts.md")
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$manifestFile = (Resolve-Path -LiteralPath $ManifestPath).Path
$manifest = Get-Content -LiteralPath $manifestFile -Raw
$rowPattern = '(?m)^\|\s*`(?<path>[^`]+)`\s*\|\s*(?<size>[0-9]+)\s*\|\s*`(?<hash>[A-Fa-f0-9]{64})`\s*\|'
$rows = [regex]::Matches($manifest, $rowPattern)

if ($rows.Count -eq 0) {
    throw "No artifact rows found in manifest: $manifestFile"
}

foreach ($row in $rows) {
    $relativePath = $row.Groups["path"].Value
    if ([IO.Path]::IsPathRooted($relativePath)) {
        throw "Artifact path must be repository-relative: $relativePath"
    }

    $artifactPath = Join-Path $repositoryRoot $relativePath
    $resolvedArtifact = (Resolve-Path -LiteralPath $artifactPath).Path
    if (-not $resolvedArtifact.StartsWith($repositoryRoot, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Artifact path escapes repository root: $relativePath"
    }

    $artifact = Get-Item -LiteralPath $resolvedArtifact
    $expectedSize = [int64]$row.Groups["size"].Value
    if ($artifact.Length -ne $expectedSize) {
        throw "Artifact size mismatch for ${relativePath}: expected $expectedSize, actual $($artifact.Length)"
    }

    $expectedHash = $row.Groups["hash"].Value.ToUpperInvariant()
    $actualHash = (Get-FileHash -LiteralPath $resolvedArtifact -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($actualHash -ne $expectedHash) {
        throw "Artifact SHA256 mismatch for ${relativePath}: expected $expectedHash, actual $actualHash"
    }

    Write-Output "PASS $relativePath size=$expectedSize sha256=$actualHash"
}
