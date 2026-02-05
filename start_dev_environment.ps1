# Start Dev Environment for Condomínio Entregas
Write-Host "🚀 Iniciando ambiente de desenvolvimento: Condomínio Entregas..." -ForegroundColor Cyan

$projectPath = "c:\Users\leona\Downloads\condominio-entregas"
cd $projectPath

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host "📦 Instalando dependências..." -ForegroundColor Yellow
    npm install
}

# Start the dev server in a new window
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev"

Write-Host "✅ Servidor Vite iniciado!" -ForegroundColor Green
