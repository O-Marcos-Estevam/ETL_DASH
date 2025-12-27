@echo off
title ETL Dashboard
echo.
echo ========================================
echo        ETL Dashboard - Iniciando
echo ========================================
echo.

echo [1/2] Iniciando Backend (FastAPI)...
start "ETL Backend" cmd /k "cd backend && python app.py"

timeout /t 2 >nul

echo [2/2] Iniciando Frontend (React)...
cd frontend
start "ETL Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo   Backend:  http://localhost:4001
echo   Frontend: http://localhost:4000
echo   API Docs: http://localhost:4001/docs
echo ========================================
echo.
echo Pressione qualquer tecla para fechar esta janela...
pause >nul
