# Launch Clawdbot Nexus Dashboard

Write-Host "🚀 Starting Clawdbot Nexus Backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\Users\leona\Downloads\AntigravityJobBot; python -m src.dashboard_api"

Write-Host "🎨 Starting Clawdbot Nexus Frontend..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\Users\leona\Downloads\AntigravityJobBot\dashboard; npm run dev"

Write-Host "🤖 Starting Moltbook Autonomous Agent..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\Users\leona\Downloads\AntigravityJobBot; python -m src.moltbook_autonomous"

Write-Host "👔 Starting LinkedIn Evolution Bot..." -ForegroundColor Blue
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd c:\Users\leona\Downloads\AntigravityJobBot; python -m src.main"

Write-Host "✅ Nexus is initializing. Access at http://localhost:5173" -ForegroundColor Green
Start-Process "http://localhost:5173"
