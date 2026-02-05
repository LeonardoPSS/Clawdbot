# Deploy Nexara to DigitalOcean (Windows Client Side)
param (
    [string]$DropletIP,
    [string]$User = "root"
)

if (-not $DropletIP) {
    Write-Host "Usage: .\deploy.ps1 -DropletIP <YOUR_IP>" -ForegroundColor Yellow
    exit
}

$ZipName = "nexara_deploy.zip"
$RemoteDir = "/root/nexara"

# Check location
if (Test-Path "..\src") {
    $ProjectRoot = Resolve-Path ".."
    $LocalZip = Join-Path (Get-Location) $ZipName
}
elseif (Test-Path "src") {
    $ProjectRoot = Get-Location
    $LocalZip = Join-Path (Get-Location) "deployment\$ZipName"
}
else {
    Write-Host "Error: Could not find 'src' folder." -ForegroundColor Red
    exit
}

Write-Host "Packaging Nexara..." -ForegroundColor Cyan

# 1. Create Staging Area (Avoids file locks)
$BuildDir = Join-Path $env:TEMP "nexara_build"
if (Test-Path $BuildDir) { Remove-Item $BuildDir -Recurse -Force -ErrorAction SilentlyContinue }
New-Item -Path $BuildDir -ItemType Directory | Out-Null

# 2. Copy Files to Staging
$Exclude = @(".git", ".venv", "__pycache__", ".idea", ".vscode", "node_modules", "nexara_deploy.zip", "logs", "data")
Write-Host "Copying files to staging area..." -ForegroundColor Gray
Copy-Item -Path "$ProjectRoot\*" -Destination $BuildDir -Recurse -Exclude $Exclude -Force

# 3. Create Zip from Staging
if (Test-Path $LocalZip) { Remove-Item $LocalZip -Force -ErrorAction SilentlyContinue }
Compress-Archive -Path "$BuildDir\*" -DestinationPath $LocalZip -Force

# 4. Cleanup Staging
Remove-Item $BuildDir -Recurse -Force -ErrorAction SilentlyContinue

if (-not (Test-Path $LocalZip)) {
    Write-Host "Error: Zip file was not created." -ForegroundColor Red
    exit
}

Write-Host "Uploading to $DropletIP (Enter Password #1)..." -ForegroundColor Cyan
# Using explicit /root path
scp $LocalZip ${User}@${DropletIP}:/root/$ZipName

if ($LASTEXITCODE -ne 0) {
    Write-Host "Upload Failed. Please check SSH connection and password." -ForegroundColor Red
    exit
}

Write-Host "Upload Success." -ForegroundColor Green
Write-Host "Configuring Server (Enter Password #2)..." -ForegroundColor Cyan

# flattened command to avoid Windows CRLF issues
$RemoteScript = "echo 'Checking file existence...'; ls -la /root/$ZipName; if [ ! -f /root/$ZipName ]; then echo 'CRITICAL: Zip file not found'; exit 1; fi; echo 'Installing dependencies...'; apt update && apt install -y unzip docker-compose || true; if ! command -v docker &> /dev/null; then curl -fsSL https://get.docker.com | sh; apt install -y docker-compose; fi; echo 'Setting up project...'; mkdir -p $RemoteDir; mv /root/$ZipName $RemoteDir/; cd $RemoteDir; unzip -o $ZipName > /dev/null; rm $ZipName; cd deployment; if [ ! -f docker-compose.yaml ]; then echo 'Error: docker-compose.yaml not found'; ls -la; exit 1; fi; echo 'Launching Containers...'; docker-compose down; docker-compose up -d --build"

ssh ${User}@${DropletIP} $RemoteScript

Write-Host "Deployment Complete. Check logs with: ssh $User@$DropletIP 'docker logs -f clawdbot_vps'" -ForegroundColor Gray
