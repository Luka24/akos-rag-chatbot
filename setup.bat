@echo off
REM AKOS RAG Chatbot - Windows launcher za setup.ps1
REM Dvojni klik ali zazeni: setup.bat

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
if errorlevel 1 (
    echo.
    echo Setup ni uspel. Glej napake zgoraj.
    pause
    exit /b 1
)

echo.
pause
