@echo off
chcp 65001 >nul
title ETL Dashboard - Modo Desenvolvimento

echo ========================================
echo   ETL Dashboard V2 - Dev Mode
echo ========================================
echo.
echo Este script inicia Backend e Frontend
echo em janelas separadas para desenvolvimento
echo.

pushd "%~dp0.."
set "ROOT_DIR=%CD%"
popd

REM Limpar processos
echo Limpando processos antigos...
call "%ROOT_DIR%\scripts\kill_python_backend.bat" >nul 2>&1

timeout /t 2 /nobreak >nul

REM Iniciar Backend
echo [1/2] Iniciando Backend...
cd /d "%ROOT_DIR%\backend"
start "ETL Backend DEV" cmd /k "title ETL Backend DEV && python app.py"

timeout /t 3 /nobreak >nul

REM Iniciar Frontend
echo [2/2] Iniciando Frontend...
cd /d "%ROOT_DIR%\frontend"
start "ETL Frontend DEV" cmd /k "title ETL Frontend DEV && npm run dev"

echo.
echo ========================================
echo   Backend:  http://localhost:4001
echo   Frontend: http://localhost:4000
echo ========================================
echo.
echo Pressione qualquer tecla para fechar...
pause >nul
