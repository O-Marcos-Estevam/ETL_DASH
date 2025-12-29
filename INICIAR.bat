@echo off
title ETL Dashboard V2

echo.
echo ========================================
echo     ETL Dashboard V2 - Iniciando
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Encerrando processos Python...
taskkill /F /IM python.exe >nul 2>&1
ping 127.0.0.1 -n 2 >nul

echo [2/3] Iniciando Backend...
cd backend
start "ETL Backend" cmd /k "python app.py"
ping 127.0.0.1 -n 4 >nul

echo [3/3] Iniciando Frontend...
cd ..\frontend
start "ETL Frontend" cmd /k "npm run dev"
ping 127.0.0.1 -n 2 >nul

echo.
echo ========================================
echo   Sistema iniciado!
echo ========================================
echo   Backend:  http://localhost:4001
echo   Frontend: http://localhost:4000
echo   API Docs: http://localhost:4001/docs
echo ========================================
echo.
pause
