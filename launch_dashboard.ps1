# PowerShell script to launch Clawd-Vision Dashboard and Backend
$botDir = "C:\Users\leona\Downloads\AntigravityJobBot"
Set-Location $botDir

Write-Host "🚀 Launching Clawd-Vision Backend..."
$backendProcess = Start-Process python -ArgumentList "-m src.dashboard_api" -WindowStyle Hidden -WorkingDirectory $botDir -PassThru

Write-Host "🖥️ Launching Clawd-Vision Frontend..."
Set-Location "$botDir\dashboard"
$frontendProcess = Start-Process npm -ArgumentList "run dev" -WindowStyle Hidden -WorkingDirectory "$botDir\dashboard" -PassThru

Write-Host "✨ Clawd-Vision is starting! Wait 8 seconds for initialization..."
Start-Sleep -Seconds 8
Start-Process "http://localhost:5173"

Write-Host "✅ Command Center Active."
