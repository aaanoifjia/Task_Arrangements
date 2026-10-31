[CmdletBinding()]
param(
    [int]$Port = 0,
    [string]$InstalledExe = "$env:LOCALAPPDATA\Codex Flow\codex-flow-desktop.exe",
    [switch]$KeepOpen,
    [switch]$CloseExisting,
    [string]$ProbeScript = ""
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path -LiteralPath $InstalledExe)) { throw "Installed Codex Flow executable not found: $InstalledExe" }
if ([string]::IsNullOrWhiteSpace($ProbeScript)) { $ProbeScript = Join-Path $PSScriptRoot 'webview2_cdp_probe.mjs' }

function Get-OwnedProcessIds {
    param([int[]]$RootIds)
    $all = @(Get-CimInstance Win32_Process -ErrorAction Stop)
    $ids = @($RootIds)
    do {
        $children = @($all | Where-Object { $ids -contains $_.ParentProcessId } | Select-Object -ExpandProperty ProcessId)
        $children = @($children | Where-Object { $ids -notcontains $_ })
        if ($children.Count -eq 0) { break }
        $ids += $children
    } while ($true)
    return $ids
}

function Stop-OwnedProcessTree {
    param([string]$ExecutablePath)
    $roots = @(Get-CimInstance Win32_Process -ErrorAction Stop | Where-Object {
        $_.ExecutablePath -and [string]::Equals($_.ExecutablePath, $ExecutablePath, [System.StringComparison]::OrdinalIgnoreCase)
    } | Select-Object -ExpandProperty ProcessId)
    if ($roots.Count -eq 0) { return }
    $ids = @(Get-OwnedProcessIds -RootIds $roots)
    [array]::Reverse($ids)
    foreach ($id in $ids) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Milliseconds 500
    Write-Output ("CLOSED existing Codex Flow tree ids={0}" -f ($ids -join ','))
}

if ($CloseExisting) { Stop-OwnedProcessTree -ExecutablePath $InstalledExe }

if ($Port -eq 0) {
    $listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
    $listener.Start()
    $Port = ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
    $listener.Stop()
}

$browserArguments = "--disable-features=msWebOOUI,msPdfOOUI,msSmartScreenProtection --remote-debugging-port=$Port --remote-debugging-address=127.0.0.1"
$envArgs = @{
    WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = $browserArguments
    CODEX_FLOW_WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = $browserArguments
}
$profile = Join-Path $env:LOCALAPPDATA "CodexFlowDebug\WebView2-$Port"
New-Item -ItemType Directory -Force -Path $profile | Out-Null
$tempRoot = Join-Path (Split-Path -Parent $PSScriptRoot) '.codex-flow-debug-temp'
New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null
$envArgs.WEBVIEW2_USER_DATA_FOLDER = $profile
$oldArgs = $env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS
$oldCodexFlowArgs = $env:CODEX_FLOW_WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS
$oldFolder = $env:WEBVIEW2_USER_DATA_FOLDER
$oldTemp = $env:TEMP
$oldTmp = $env:TMP
$env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = $envArgs.WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS
$env:CODEX_FLOW_WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = $envArgs.CODEX_FLOW_WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS
$env:WEBVIEW2_USER_DATA_FOLDER = $envArgs.WEBVIEW2_USER_DATA_FOLDER
$env:TEMP = $tempRoot
$env:TMP = $tempRoot
try {
    $process = Start-Process -FilePath $InstalledExe -PassThru
} finally {
    if ($null -eq $oldArgs) { Remove-Item Env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS -ErrorAction SilentlyContinue } else { $env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = $oldArgs }
    if ($null -eq $oldCodexFlowArgs) { Remove-Item Env:CODEX_FLOW_WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS -ErrorAction SilentlyContinue } else { $env:CODEX_FLOW_WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = $oldCodexFlowArgs }
    if ($null -eq $oldFolder) { Remove-Item Env:WEBVIEW2_USER_DATA_FOLDER -ErrorAction SilentlyContinue } else { $env:WEBVIEW2_USER_DATA_FOLDER = $oldFolder }
    if ($null -eq $oldTemp) { Remove-Item Env:TEMP -ErrorAction SilentlyContinue } else { $env:TEMP = $oldTemp }
    if ($null -eq $oldTmp) { Remove-Item Env:TMP -ErrorAction SilentlyContinue } else { $env:TMP = $oldTmp }
}
Write-Output ("STARTED pid={0} port={1} exe={2}" -f $process.Id, $Port, $InstalledExe)

$deadline = (Get-Date).AddSeconds(30)
$target = $null
while ((Get-Date) -lt $deadline) {
    try {
        $target = Invoke-RestMethod -Uri "http://127.0.0.1:$Port/json/list" -TimeoutSec 2
        if ($target) { break }
    } catch { }
    Start-Sleep -Milliseconds 250
}
if (-not $target) {
    if (-not $KeepOpen -and -not $process.HasExited) {
        $ids = @(Get-OwnedProcessIds -RootIds @($process.Id)); [array]::Reverse($ids)
        foreach ($id in $ids) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
    }
    throw "WebView2 CDP target did not become available on 127.0.0.1:$Port"
}

$json = node $ProbeScript --port $Port
Write-Output $json
if (-not $KeepOpen -and -not $process.HasExited) {
    $ids = @(Get-OwnedProcessIds -RootIds @($process.Id)); [array]::Reverse($ids)
    foreach ($id in $ids) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
}
