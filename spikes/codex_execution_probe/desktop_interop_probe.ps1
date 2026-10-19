$resultPath = Join-Path $PSScriptRoot "results\basic_execution.json"
$checklistPath = Join-Path $PSScriptRoot "results\desktop_interop_checklist.md"

$result = Get-Content -Raw $resultPath | ConvertFrom-Json
$threadId = [string]$result.thread_id
if ([string]::IsNullOrWhiteSpace($threadId)) {
    throw "basic_execution.json does not contain a thread_id"
}

$deepLink = "codex://threads/$threadId"
$checklist = @"
# Codex Desktop Interop Checklist

- Thread ID: $threadId
- Test date: $(Get-Date -Format 'yyyy-MM-dd')
- Deep link: $deepLink

- [ ] Codex Desktop opened
- [ ] Correct thread opened
- [ ] Thread appears in sidebar without restart
- [ ] Thread is searchable
- [ ] Thread is associated with expected project
"@

Set-Content -LiteralPath $checklistPath -Value $checklist -Encoding utf8
Start-Process $deepLink
