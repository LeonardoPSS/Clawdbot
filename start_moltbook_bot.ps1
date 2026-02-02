# PowerShell script to run the Moltbook Autonomous Bot in background
$botDir = "C:\Users\leona\Downloads\AntigravityJobBot"
Set-Location $botDir

# Run Moltbook Autonomous Bot
Start-Process python -ArgumentList "-m src.moltbook_autonomous" -WindowStyle Hidden -WorkingDirectory $botDir

# Run Chrome Watcher for responsive learning
Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -File .\chrome_watcher.ps1" -WindowStyle Hidden -WorkingDirectory $botDir

Write-Host "✅ Clawdbot Moltbook Autonomy & Chrome Watcher launched in background."
