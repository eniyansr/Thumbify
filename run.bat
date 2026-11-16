@echo off
title THUMBIFY - Telegram Auto Thumbnail Bot
cls

echo ============================================================
echo   THUMBIFY - Telegram Auto Thumbnail Bot Launcher
echo ============================================================
echo.

:: Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [ERROR] Virtual environment not found in .venv.
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment. Ensure Python 3.12+ is installed and added to PATH.
        pause
        exit /b 1
    )
    echo Installing dependencies...
    .\.venv\Scripts\pip.exe install -r requirements.txt
)

:: Check if .env exists
if not exist ".env" (
    echo [WARNING] .env file not found!
    if exist ".env.example" (
        echo Copying .env.example to .env...
        copy .env.example .env
        echo.
        echo Please edit .env with your Telegram credentials and run this script again.
        echo.
    )
    pause
    exit /b 1
)

:: Run bot
echo Starting THUMBIFY Bot...
echo.
.\.venv\Scripts\python.exe -m app.main

echo.
echo ============================================================
echo [INFO] THUMBIFY Bot has stopped.
echo Check logs/thumbify.log for complete logs.
echo ============================================================
pause
