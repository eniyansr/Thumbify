@echo off
title Stopping THUMBIFY
cd /d "%~dp0"

echo ============================================================
echo   Stopping THUMBIFY Background Process...
echo ============================================================

if exist "thumbify.pid" (
    set /p BOT_PID=<thumbify.pid
    echo Found PID %BOT_PID%. Terminating process...
    taskkill /F /PID %BOT_PID% >NUL 2>&1
    del /f /q "thumbify.pid" >NUL 2>&1
    echo [SUCCESS] THUMBIFY has been stopped.
) else (
    echo [INFO] thumbify.pid file not found. Searching for running pythonw instances...
    taskkill /F /IM pythonw.exe >NUL 2>&1
    echo [INFO] Any background pythonw processes stopped.
)

echo.
ping 127.0.0.1 -n 3 >NUL
