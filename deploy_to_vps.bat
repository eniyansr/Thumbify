@echo off
title Deploy THUMBIFY to VPS
cd /d "%~dp0"

echo ============================================================
echo   THUMBIFY — Deploy Bot to Cloud VPS (24/7 Hosting)
echo ============================================================
echo.

set /p VPS_IP="Enter your VPS IP Address: "
if "%VPS_IP%"=="" (
    echo [ERROR] IP address cannot be empty.
    pause
    exit /b 1
)

set /p VPS_USER="Enter SSH Username [default: root]: "
if "%VPS_USER%"=="" set VPS_USER=root

set /p VPS_PORT="Enter SSH Port [default: 22]: "
if "%VPS_PORT%"=="" set VPS_PORT=22

echo.
echo Connecting to %VPS_USER%@%VPS_IP% on port %VPS_PORT%...
echo (If prompted for a password or SSH fingerprint, enter 'yes' or type your server password)
echo.

powershell -NoProfile -ExecutionPolicy Bypass -File "deploy_to_vps.ps1" -ServerIP "%VPS_IP%" -User "%VPS_USER%" -Port %VPS_PORT%

echo.
pause
