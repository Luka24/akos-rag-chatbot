@echo off
REM AKOS RAG Chatbot - Windows launcher (zazene vse 3 servise)
REM Vsak servis se odpre v svojem oknu, da lahko spremljas loge.

set ROOT=%~dp0
cd /d "%ROOT%"

echo Zaganjam mock RAG API (port 8000)...
start "AKOS - API (8000)" cmd /k "cd /d ""%ROOT%"" && uvicorn api:app --port 8000"

REM Kratek premor, da API uspe vzpostaviti port pred Chainlitom
timeout /t 2 /nobreak >nul

echo Zaganjam HTML UI (port 7860)...
start "AKOS - HTML UI (7860)" cmd /k "cd /d ""%ROOT%"" && uvicorn app:app --port 7860"

timeout /t 1 /nobreak >nul

echo Zaganjam Chainlit UI (port 8080)...
start "AKOS - Chainlit (8080)" cmd /k "cd /d ""%ROOT%"" && chainlit run chainlit_app.py --port 8080"

echo.
echo ============================================
echo  Vse aplikacije zagnane v svojih oknih.
echo.
echo  HTML UI:     http://localhost:7860
echo  Chainlit UI: http://localhost:8080
echo  API docs:    http://localhost:8000/docs
echo ============================================
echo.
pause
