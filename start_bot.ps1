# LinkedIn Bot Launcher - Startup Version
$OutputEncoding = [Console]::InputEncoding = [Console]::OutputEncoding = New-Object System.Text.UTF8Encoding
Write-Host "Setting up environment..."
Set-Location "C:\Users\leona\Downloads\AntigravityJobBot"
$env:PYTHONPATH = "C:\Users\leona\Downloads\AntigravityJobBot"

Write-Host "⏳ Waiting 30 seconds for system to stabilize..."
Start-Sleep -Seconds 30

Write-Host "🚀 Starting AntigravityJobBot..."
python bot_manager.py
