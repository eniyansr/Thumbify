@echo off
title Starting THUMBIFY in Background
cd /d "%~dp0"

echo ============================================================
echo   Starting THUMBIFY in Background...
echo ============================================================

:: Check if already running
if exist "thumbify.pid" (
    set /p OLD_PID=<thumbify.pid
    tasklist /FI "PID eq %OLD_PID%" 2>NUL | find /I "%OLD_PID%" >NUL
    if not errorlevel 1 (
        echo [INFO] THUMBIFY is already running with PID %OLD_PID%!
        echo To stop it, run stop_bot.bat.
        pause
        exit /b 0
    )
)

:: Start silently with pythonw.exe (no command prompt window)
start "" ".\.venv\Scripts\pythonw.exe" -m app.main

:: Brief pause using ping for universal compatibility
ping 127.0.0.1 -n 3 >NUL

if exist "thumbify.pid" (
    set /p NEW_PID=<thumbify.pid
    echo [SUCCESS] THUMBIFY is now running silently in the background!
    echo Process ID: %NEW_PID%
    echo Logs are being written to: logs\thumbify.log
    echo.
    echo To stop the bot anytime, run stop_bot.bat.
) else (
    echo [INFO] Bot launched. Check logs\thumbify.log for status.
)

ping 127.0.0.1 -n 4 >NUL
