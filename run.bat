@echo off
REM AKOS Asistent – zagon (Windows)
REM Zazeni: run.bat

set ROOT=%~dp0
cd /d "%ROOT%"

REM Preveri da .env obstaja
if not exist "%ROOT%.env" (
    echo [NAPAKA] Datoteka .env ne obstaja!
    echo Najprej zazeni: setup.bat
    pause
    exit /b 1
)

echo Zaganjam mock RAG API na portu 8000...
start "AKOS - API (8000)" cmd /k "cd /d ""%ROOT%"" && python -m uvicorn api:app --port 8000"

REM Kratka pavza da API odpre port
timeout /t 3 /nobreak >nul

echo Zaganjam Chainlit UI na portu 8081...
start "AKOS - Chainlit (8081)" cmd /k "cd /d ""%ROOT%"" && python -m chainlit run chainlit_app.py --port 8081"

timeout /t 4 /nobreak >nul

echo.
echo ============================================
echo  AKOS Asistent zagnan!
echo.
echo  Odprite brskalnik na:
echo  http://localhost:8081
echo.
echo  API docs: http://localhost:8000/docs
echo ============================================
echo.

REM Odpri brskalnik
start http://localhost:8081

pause
