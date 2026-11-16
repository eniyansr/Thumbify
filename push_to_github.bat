@echo off
title Push THUMBIFY to GitHub
cd /d "%~dp0"

echo ============================================================
echo   Pushing THUMBIFY to GitHub (https://github.com/eniyansr/Thumbify)
echo ============================================================
echo.

git push -u origin main

if errorlevel 1 (
    echo.
    echo [ERROR] Push failed.
    echo Please make sure you have created the empty repository 'Thumbify'
    echo on GitHub at: https://github.com/new
) else (
    echo.
    echo [SUCCESS] Successfully pushed to https://github.com/eniyansr/Thumbify!
)

echo.
pause
