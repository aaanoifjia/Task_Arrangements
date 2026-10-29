[CmdletBinding()]
param(
    [string]$Executable = (Join-Path $PSScriptRoot '..\desktop\src-tauri\target\release\codex-flow-desktop.exe'),
    [int]$Cycles = 3
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$exe = (Resolve-Path $Executable).Path
$smokeRoot = Join-Path $env:TEMP ('codex-flow-release-smoke-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $smokeRoot | Out-Null
$oldLocalAppData = $env:LOCALAPPDATA
$oldWebViewFolder = $env:WEBVIEW2_USER_DATA_FOLDER
$env:LOCALAPPDATA = $smokeRoot
$env:WEBVIEW2_USER_DATA_FOLDER = Join-Path $smokeRoot 'webview'

function Get-ProcessSnapshot {
    @(Get-CimInstance Win32_Process | Select-Object ProcessId, ParentProcessId, Name, ExecutablePath, CommandLine)
}

function Wait-ProcessById([int]$Id, [int]$Seconds = 15) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        $process = Get-Process -Id $Id -ErrorAction SilentlyContinue
        if ($process) { return $process }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)
    throw "desktop process $Id did not remain alive"
}

function Find-OwnedSidecar([string]$DatabasePath, [int]$Seconds = 15) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        $candidate = Get-ProcessSnapshot | Where-Object {
            $_.Name -eq 'codex-flow-server.exe' -and $_.CommandLine -like "*$DatabasePath*"
        } | Select-Object -First 1
        if ($candidate) { return $candidate }
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)
    throw "owned sidecar was not found for $DatabasePath"
}

function Wait-Healthy([string]$BaseUrl, [int]$Seconds = 15) {
    $deadline = (Get-Date).AddSeconds($Seconds)
    do {
        try {
            $health = Invoke-WebRequest -UseBasicParsing "$BaseUrl/healthz" -TimeoutSec 2
            if ($health.StatusCode -eq 200) { return }
        } catch {}
        Start-Sleep -Milliseconds 250
    } while ((Get-Date) -lt $deadline)
    throw "sidecar did not become healthy at $BaseUrl"
}

function Get-ListeningPort([int]$ProcessId) {
    $line = netstat -ano | Select-String "LISTENING\s+$ProcessId$" | Select-Object -First 1
    if (-not $line) { throw "sidecar $ProcessId did not expose a listening port" }
    [int](($line.ToString().Trim() -split '\s+')[1].Split(':')[-1])
}

function Invoke-JsonRequest([string]$Method, [string]$Uri, [hashtable]$Headers, [object]$Body = $null) {
    $params = @{ UseBasicParsing = $true; Method = $Method; Uri = $Uri; Headers = $Headers; TimeoutSec = 5 }
    if ($null -ne $Body) {
        $params.ContentType = 'application/json'
        $params.Body = ($Body | ConvertTo-Json -Depth 10 -Compress)
    }
    Invoke-WebRequest @params
}

try {
    $workflowId = 'smoke-release-' + [guid]::NewGuid().ToString('N')
    $workflow = @{
        id = $workflowId
        name = 'Quick Smoke Test'
        description = $null
        tasks = @(
            @{ id = 'A'; name = 'Create File'; prompt = 'Create a file named task_a.txt in the current working directory. Its content must be exactly: TASK_A_DONE'; cwd = 'D:\codex-flow-smoke'; execution_mode = 'NEW_THREAD' },
            @{ id = 'B'; name = 'Verify And Continue'; prompt = 'Read task_a.txt from the current working directory. Verify that its content is exactly: TASK_A_DONE. Then create a file named task_b.txt containing exactly: TASK_B_DONE'; cwd = 'D:\codex-flow-smoke'; execution_mode = 'CONTINUE_THREAD'; continue_from_task_id = 'A' }
        )
        edges = @(@{ source_task_id = 'A'; target_task_id = 'B' })
    }
    $sidecarExe = (Resolve-Path (Join-Path $repo 'desktop\src-tauri\binaries\codex-flow-server-x86_64-pc-windows-msvc.exe')).Path
    for ($cycle = 1; $cycle -le $Cycles; $cycle++) {
        $apiRoot = Join-Path $smokeRoot "api-$cycle"
        New-Item -ItemType Directory -Path $apiRoot | Out-Null
        $db = Join-Path $apiRoot 'smoke.sqlite3'
        $logDir = Join-Path $apiRoot 'logs'
        $stdout = Join-Path $apiRoot 'stdout.log'
        $stderr = Join-Path $apiRoot 'stderr.log'
        $token = 'release-smoke-token'
        $sidecar = Start-Process -FilePath $sidecarExe -ArgumentList @('--host','127.0.0.1','--port','0','--db',$db,'--token',$token,'--log-dir',$logDir) -RedirectStandardOutput $stdout -RedirectStandardError $stderr -PassThru
        Wait-ProcessById $sidecar.Id | Out-Null
        $portLine = $null
        $deadline = (Get-Date).AddSeconds(15)
        do { Start-Sleep -Milliseconds 250; $portLine = Get-Content $stdout -ErrorAction SilentlyContinue | Select-String '"event":"ready"' | Select-Object -First 1 } while (-not $portLine -and (Get-Date) -lt $deadline)
        if (-not $portLine) { throw "cycle $cycle sidecar readiness was not emitted" }
        $port = ([regex]::Match($portLine.ToString(), '"port":(\d+)')).Groups[1].Value
        $base = "http://127.0.0.1:$port"
        Wait-Healthy $base
        $desktop = Start-Process -FilePath $exe -PassThru
        Wait-ProcessById $desktop.Id | Out-Null
        $health = Invoke-WebRequest -UseBasicParsing "$base/healthz" -TimeoutSec 5
        if ($health.StatusCode -ne 200) { throw "cycle $cycle health failed" }
        $headers = @{ Authorization = "Bearer $token"; Origin = 'http://tauri.localhost'; Accept = 'application/json' }
        $preflight = Invoke-WebRequest -UseBasicParsing -Method Options "$base/api/workflows" -Headers ($headers + @{ 'Access-Control-Request-Method' = 'GET'; 'Access-Control-Request-Headers' = 'authorization' }) -TimeoutSec 5
        if ($preflight.StatusCode -ne 200 -or $preflight.Headers['Access-Control-Allow-Origin'] -ne 'http://tauri.localhost') { throw "cycle $cycle CORS preflight failed" }
        $list = Invoke-JsonRequest 'GET' "$base/api/workflows" $headers
        if ($list.Headers['Content-Type'] -notmatch 'application/json') { throw "cycle $cycle workflow list was not JSON" }
        $created = Invoke-JsonRequest 'POST' "$base/api/workflows" ($headers + @{ 'Content-Type' = 'application/json' }) $workflow
        $createdBody = $created.Content | ConvertFrom-Json
        if ($created.StatusCode -ne 201 -or $createdBody.workflow.id -ne $workflowId) { throw "cycle $cycle workflow create failed" }
        $loaded = Invoke-JsonRequest 'GET' "$base/api/workflows/$([uri]::EscapeDataString($workflowId))" $headers
        $loadedBody = $loaded.Content | ConvertFrom-Json
        if ($loadedBody.workflow.tasks.Count -ne 2 -or $loadedBody.workflow.edges.Count -ne 1 -or $loadedBody.workflow.tasks[0].cwd -ne 'D:\codex-flow-smoke') { throw "cycle $cycle workflow persistence failed" }
        Write-Output "CYCLE $cycle PASS origin=http://tauri.localhost sidecar=$($sidecar.Id) port=$port"
        Stop-Process -Id $desktop.Id -Force
        Stop-Process -Id $sidecar.Id -Force
        $deadline = (Get-Date).AddSeconds(10)
        do { Start-Sleep -Milliseconds 250; $owned = Get-Process -Id $sidecar.Id -ErrorAction SilentlyContinue } while ($owned -and (Get-Date) -lt $deadline)
        if ($owned) { throw "cycle $cycle owned sidecar survived controlled desktop shutdown" }
    }
    Write-Output "PACKAGED_RELEASE_SMOKE PASS cycles=$Cycles"
}
finally {
    $env:LOCALAPPDATA = $oldLocalAppData
    if ($null -eq $oldWebViewFolder) { Remove-Item Env:WEBVIEW2_USER_DATA_FOLDER -ErrorAction SilentlyContinue } else { $env:WEBVIEW2_USER_DATA_FOLDER = $oldWebViewFolder }
}
