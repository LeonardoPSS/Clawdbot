# PowerShell script to monitor Chrome, trigger learning and ensure Extension Gateway is alive
$botDir = "C:\Users\leona\Downloads\AntigravityJobBot"
$gatewayCmd = "C:\Users\leona\.clawdbot\gateway_runner.cmd"
Set-Location $botDir

$chromeDetected = $false
$lastTriggerTime = [DateTime]::MinValue
$cooldownMinutes = 10

Write-Host "👀 Clawdbot Chrome & Gateway Watcher Started..."

while ($true) {
    # 1. Gateway Health Check (Ensures extension is always ready)
    $gatewayProcess = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*clawdbot gateway*" }
    if (-not $gatewayProcess) {
        Write-Host "⚠️ Extension Gateway (clawdbot gateway) not found! Restarting..."
        Start-Process cmd -ArgumentList "/c $gatewayCmd" -WindowStyle Hidden
    }

    # 2. Chrome Activity Watcher
    $chromeProcess = Get-Process chrome -ErrorAction SilentlyContinue
    if ($chromeProcess) {
        if (-not $chromeDetected) {
            $currentTime = Get-Date
            $timeSinceLastTrigger = ($currentTime - $lastTriggerTime).TotalMinutes
            
            if ($timeSinceLastTrigger -ge $cooldownMinutes) {
                Write-Host "🚀 Chrome detected! Triggering user learning..."
                Start-Process python -ArgumentList "-m src.history_observer" -WindowStyle Hidden -WorkingDirectory $botDir
                $lastTriggerTime = $currentTime
            }
            $chromeDetected = $true
        }
    }
    else {
        $chromeDetected = $false
    }
    
    Start-Sleep -Seconds 15
}
