[CmdletBinding()]
param(
    [string]$InstalledExe = "$env:LOCALAPPDATA\Codex Flow\codex-flow-desktop.exe",
    [int]$TimeoutSeconds = 300
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$runner = Join-Path $PSScriptRoot 'desktop_e2e_v1.mjs'
if (-not (Test-Path -LiteralPath $InstalledExe)) { throw "Installed Codex Flow executable not found: $InstalledExe" }

$listener = [System.Net.Sockets.TcpListener]::new([System.Net.IPAddress]::Loopback, 0)
$listener.Start()
$port = ([System.Net.IPEndPoint]$listener.LocalEndpoint).Port
$listener.Stop()
$workflowId = 'desktop-e2e-' + [guid]::NewGuid().ToString('N')

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
    param([int]$RootId)
    $ids = @(Get-OwnedProcessIds -RootIds @($RootId))
    [array]::Reverse($ids)
    foreach ($id in $ids) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
}

$arguments = "--disable-features=msWebOOUI,msPdfOOUI,msSmartScreenProtection --remote-debugging-port=$port --remote-debugging-address=127.0.0.1"
$profile = Join-Path $env:LOCALAPPDATA "CodexFlowDebug\E2E-$workflowId"
$oldArgs = $env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS
$oldCodexFlowArgs = $env:CODEX_FLOW_WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS
$oldFolder = $env:WEBVIEW2_USER_DATA_FOLDER
$env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = $arguments
$env:CODEX_FLOW_WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = $arguments
$env:WEBVIEW2_USER_DATA_FOLDER = $profile

try {
    $desktop = Start-Process -FilePath $InstalledExe -PassThru
    $deadline = (Get-Date).AddSeconds(30)
    do {
        try {
            $targets = Invoke-RestMethod -Uri "http://127.0.0.1:$port/json/list" -TimeoutSec 2
            if ($targets) { break }
        } catch { }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)
    if (-not $targets) { throw "WebView2 CDP target did not become available on 127.0.0.1:$port" }

    $reportJson = node $runner --port $port --workflow-id $workflowId --timeout-ms ($TimeoutSeconds * 1000)
    if ($LASTEXITCODE -ne 0) { throw 'Desktop E2E runner failed.' }
    $report = $reportJson | ConvertFrom-Json
    if ($report.finalUi.status -ne 'SUCCESS' -or -not $report.websocketObserved) { throw 'Desktop E2E runner did not meet installed UI acceptance.' }

    $database = Join-Path $env:LOCALAPPDATA 'Codex Flow\codex-flow.sqlite3'
    $query = @"
import json, sqlite3, sys
connection = sqlite3.connect(sys.argv[1])
connection.row_factory = sqlite3.Row
workflow_id, run_id = sys.argv[2:]
workflow = connection.execute('select id from workflows where id = ?', (workflow_id,)).fetchone()
run = connection.execute('select status from workflow_runs where id = ?', (run_id,)).fetchone()
tasks = connection.execute('select task_id, status, thread_id, turn_id from task_runs where workflow_run_id = ? order by task_id', (run_id,)).fetchall()
events = connection.execute('select event_type from events where workflow_run_id = ?', (run_id,)).fetchall()
print(json.dumps({'workflow': bool(workflow), 'run_status': run['status'] if run else None, 'tasks': [dict(row) for row in tasks], 'events': [row['event_type'] for row in events]}))
"@
    $databaseEvidence = & .\.venv\Scripts\python.exe -c $query $database $workflowId $report.runId | ConvertFrom-Json
    if (-not $databaseEvidence.workflow -or $databaseEvidence.run_status -ne 'SUCCESS') { throw 'SQLite acceptance did not match the installed UI result.' }
    if ($databaseEvidence.tasks.Count -ne 3 -or @($databaseEvidence.tasks | Where-Object { $_.status -ne 'SUCCESS' }).Count -ne 0) { throw 'SQLite task states did not match A→B→C success.' }
    if (@($databaseEvidence.events | Where-Object { $_ -eq 'TURN_STARTED' }).Count -lt 3) { throw 'Expected persisted turn events were not found.' }
    foreach ($marker in @('task_a.txt', 'task_b.txt', 'task_c.txt')) {
        $path = Join-Path 'D:\codex-flow-smoke' $marker
        if (-not (Test-Path -LiteralPath $path)) { throw "Expected marker missing: $path" }
        if ((Get-Content -Raw -LiteralPath $path).Trim() -notmatch 'TASK_[ABC]_DONE') { throw "Expected marker content missing: $path" }
    }
    [pscustomobject]@{ workflow_id = $workflowId; run_id = $report.runId; ui = $report; sqlite = $databaseEvidence } | ConvertTo-Json -Depth 8
}
finally {
    if ($desktop) { Stop-OwnedProcessTree -RootId $desktop.Id }
    if ($null -eq $oldArgs) { Remove-Item Env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS -ErrorAction SilentlyContinue } else { $env:WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = $oldArgs }
    if ($null -eq $oldCodexFlowArgs) { Remove-Item Env:CODEX_FLOW_WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS -ErrorAction SilentlyContinue } else { $env:CODEX_FLOW_WEBVIEW2_ADDITIONAL_BROWSER_ARGUMENTS = $oldCodexFlowArgs }
    if ($null -eq $oldFolder) { Remove-Item Env:WEBVIEW2_USER_DATA_FOLDER -ErrorAction SilentlyContinue } else { $env:WEBVIEW2_USER_DATA_FOLDER = $oldFolder }
}
