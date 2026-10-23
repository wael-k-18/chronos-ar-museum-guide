@echo off
title ChronosAR - Intelligent WebAR Spatial Museum Guide
color 0b

echo ======================================================================
echo    CHRONOS-AR: INTELLIGENT WEBAR SPATIAL MUSEUM GUIDE
echo    Final Year CSE Project-Based Learning (AR/VR Specialization)
echo ======================================================================
echo.

cd /d "%~dp0"

echo [1/2] Checking runtime environment...
where node >nul 2>nul
if %errorlevel% equ 0 (
    echo       Node.js detected. Launching server via Node.js...
    start "" http://localhost:3000
    node server.js
    goto end
)

where python >nul 2>nul
if %errorlevel% equ 0 (
    echo       Node.js not found. Python detected! Launching via Python server...
    start "" http://localhost:3000
    python server.py
    goto end
)

echo.
echo [ERROR] Neither Node.js nor Python 3 was detected on your system.
echo Please install Node.js (https://nodejs.org) or Python 3 (https://python.org).
echo.
pause

:end
