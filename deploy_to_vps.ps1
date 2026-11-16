# ====================================================================
# THUMBIFY — Automated VPS Deployment Script
# Deploys your configured bot to your Linux VPS over SSH/SCP with Docker
# ====================================================================

param (
    [Parameter(Mandatory = $true, HelpMessage = "Enter your VPS IP address")]
    [string]$ServerIP,

    [Parameter(Mandatory = $false)]
    [string]$User = "root",

    [Parameter(Mandatory = $false)]
    [int]$Port = 22
)

$ErrorActionPreference = "Stop"

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  THUMBIFY — Deploying to Cloud VPS ($User@$ServerIP:$Port)  " -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

# 1. Verify required files exist locally
if (-not (Test-Path ".env")) {
    Write-Host "[ERROR] .env file not found locally. Please configure your bot credentials first." -ForegroundColor Red
    exit 1
}

if (-not (Test-Path "assets/thumbnail.jpg")) {
    Write-Host "[ERROR] assets/thumbnail.jpg not found." -ForegroundColor Red
    exit 1
}

$RemoteDir = "/opt/thumbify"

# 2. Create remote directory on VPS
Write-Host "`n[1/4] Preparing remote directory on server..." -ForegroundColor Yellow
ssh -p $Port "$User@$ServerIP" "mkdir -p $RemoteDir/downloads $RemoteDir/logs $RemoteDir/assets"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Failed to connect to VPS via SSH. Please verify IP, user, and credentials." -ForegroundColor Red
    exit 1
}

# 3. Securely upload project files via SCP
Write-Host "`n[2/4] Uploading project files and credentials to $RemoteDir..." -ForegroundColor Yellow
scp -P $Port -r app $User@${ServerIP}:$RemoteDir/
scp -P $Port -r assets $User@${ServerIP}:$RemoteDir/
scp -P $Port requirements.txt Dockerfile docker-compose.yml .env deploy_remote.sh $User@${ServerIP}:$RemoteDir/

if (Test-Path "thumbify_bot.session") {
    Write-Host "[INFO] Syncing existing Telegram session..." -ForegroundColor Green
    scp -P $Port thumbify_bot.session $User@${ServerIP}:$RemoteDir/
}

# 4. Make remote script executable and execute deployment
Write-Host "`n[3/4] Running automated Docker deployment on VPS..." -ForegroundColor Yellow
ssh -p $Port "$User@$ServerIP" "cd $RemoteDir && chmod +x deploy_remote.sh && sed -i 's/\r$//' deploy_remote.sh && ./deploy_remote.sh"

Write-Host "`n[4/4] Deployment finished successfully!" -ForegroundColor Green
Write-Host "The bot is now running in Docker on your VPS 24/7." -ForegroundColor Green
Write-Host "You can turn off your laptop, and the bot will remain online on Telegram." -ForegroundColor Cyan
