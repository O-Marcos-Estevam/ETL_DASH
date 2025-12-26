@echo off
chcp 65001 >nul
title ETL Frontend V2 - Vite - Porta 4000

pushd "%~dp0.."
set "ROOT_DIR=%CD%"
popd

:: Mata processos node na porta 4000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":4000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

:: Procurar node
set "NODE_HOME=%ROOT_DIR%\..\node"
if exist "%NODE_HOME%" (
    set "PATH=%NODE_HOME%;%PATH%"
)

cd /d "%ROOT_DIR%"
echo ========================================
echo   ETL Dashboard V2 - Frontend React
echo   Porta: 4000
echo ========================================
echo.

:: Verificar node_modules
if not exist "node_modules" (
    echo Instalando dependencias...
    call npm install
)

echo Iniciando Frontend Vite...
call npm run dev
pause
