param(
    [string]$BaseUrl = "http://127.0.0.1:8000",
    [string]$UserId = "rahul",
    [string]$Message = "log 100 food",
    [int]$Runs = 20,
    [string]$ApiKey = "",
    [int]$DebugLimit = 100
)

if (-not $ApiKey) {
    $ApiKey = $env:API_KEY
}
if (-not $ApiKey) {
    $ApiKey = "dev-key-change-in-production"
}

function Get-Percentile {
    param(
        [double[]]$Values,
        [double]$Percent
    )

    if (-not $Values -or $Values.Count -eq 0) {
        return $null
    }

    $sorted = $Values | Sort-Object
    $rank = [math]::Ceiling(($Percent / 100.0) * $sorted.Count)

    if ($rank -lt 1) { $rank = 1 }
    if ($rank -gt $sorted.Count) { $rank = $sorted.Count }

    return [double]$sorted[$rank - 1]
}

$headers = @{ "x-api-key" = $ApiKey }
$latencies = New-Object System.Collections.Generic.List[double]

Write-Host "Running $Runs requests against $BaseUrl/chat"
Write-Host "UserId=$UserId"
Write-Host "Message=$Message"
Write-Host "Tip: keep CRITIC_NON_BLOCKING=true in server env and restart server before this run."
Write-Host ""

for ($i = 1; $i -le $Runs; $i++) {
    $body = @{ user_id = $UserId; message = $Message } | ConvertTo-Json -Compress
    $sw = [System.Diagnostics.Stopwatch]::StartNew()

    try {
        $requestParams = @{
            Uri = "$BaseUrl/chat"
            Method = "Post"
            Headers = $headers
            ContentType = "application/json"
            Body = $body
        }
        if ((Get-Command Invoke-WebRequest).Parameters.ContainsKey("UseBasicParsing")) {
            $requestParams["UseBasicParsing"] = $true
        }
        $response = Invoke-WebRequest @requestParams

        $sw.Stop()

        $clientMs = [math]::Round($sw.Elapsed.TotalMilliseconds, 2)
        $latencyMs = $clientMs
        $headerMsRaw = $response.Headers["X-Process-Time-ms"]

        if ($headerMsRaw) {
            $parsedHeader = 0.0
            if ([double]::TryParse([string]$headerMsRaw, [ref]$parsedHeader)) {
                $latencyMs = [math]::Round($parsedHeader, 2)
            }
        }

        $null = $latencies.Add($latencyMs)

        $runId = "n/a"
        $respText = ""
        try {
            $respObj = $response.Content | ConvertFrom-Json
            if ($respObj.run_id) {
                $runId = [string]$respObj.run_id
            }
            if ($respObj.response) {
                $respText = [string]$respObj.response
            }
        } catch {
        }

        $modeHint = ""
        if ($respText -match "queued in background") {
            $modeHint = "background_note=true"
        }

        Write-Host ([string]::Format("[{0}/{1}] status={2} latency_ms={3} run_id={4} {5}", $i, $Runs, $response.StatusCode, $latencyMs, $runId, $modeHint))
    }
    catch {
        $sw.Stop()
        $clientMs = [math]::Round($sw.Elapsed.TotalMilliseconds, 2)
        $null = $latencies.Add($clientMs)
        Write-Host ([string]::Format("[{0}/{1}] request_failed latency_ms={2} error={3}", $i, $Runs, $clientMs, $_.Exception.Message)) -ForegroundColor Red
    }
}

if ($latencies.Count -gt 0) {
    $avg = [math]::Round(($latencies | Measure-Object -Average).Average, 2)
    $min = [math]::Round(($latencies | Measure-Object -Minimum).Minimum, 2)
    $max = [math]::Round(($latencies | Measure-Object -Maximum).Maximum, 2)
    $p50 = [math]::Round((Get-Percentile -Values $latencies.ToArray() -Percent 50), 2)
    $p95 = [math]::Round((Get-Percentile -Values $latencies.ToArray() -Percent 95), 2)

    Write-Host ""
    Write-Host "Latency Summary (ms)"
    Write-Host "avg=$avg p50=$p50 p95=$p95 min=$min max=$max"
}

Write-Host ""
Write-Host "Checking /debug/runs for critic_mode background evidence..."

try {
    $debugRuns = Invoke-RestMethod -Uri "$BaseUrl/debug/runs?limit=$DebugLimit" -Headers $headers -Method Get

    $userRuns = @($debugRuns | Where-Object { $_.user_id -eq $UserId })
    $checkedRuns = @($userRuns | Select-Object -First $Runs)

    $backgroundCount = 0
    $inlineCount = 0
    $skippedCount = 0
    $bgCompletedCount = 0
    $bgTimeoutCount = 0
    $bgFailedCount = 0
    $bgPendingOrMissingCount = 0

    foreach ($run in $checkedRuns) {
        $mode = $null
        $bgStatus = $null
        if ($run.result -and $run.result.metadata) {
            $mode = $run.result.metadata.critic_mode
            $bgStatus = $run.result.metadata.critic_background_status
        }

        if ($mode -eq "background") {
            $backgroundCount++
        } elseif ($mode -eq "inline") {
            $inlineCount++
        } else {
            $skippedCount++
        }

        if ($mode -eq "background") {
            if ($bgStatus -eq "completed") {
                $bgCompletedCount++
            } elseif ($bgStatus -eq "timeout") {
                $bgTimeoutCount++
            } elseif ($bgStatus -eq "failed") {
                $bgFailedCount++
            } else {
                $bgPendingOrMissingCount++
            }
        }
    }

    Write-Host ([string]::Format("Checked {0} recent runs for user={1}", $checkedRuns.Count, $UserId))
    Write-Host ([string]::Format("critic_mode background={0} inline={1} skipped_or_missing={2}", $backgroundCount, $inlineCount, $skippedCount))
    Write-Host ([string]::Format("background_status completed={0} timeout={1} failed={2} pending_or_missing={3}", $bgCompletedCount, $bgTimeoutCount, $bgFailedCount, $bgPendingOrMissingCount))
}
catch {
    Write-Host ([string]::Format("Could not verify /debug/runs: {0}", $_.Exception.Message)) -ForegroundColor Yellow
}
