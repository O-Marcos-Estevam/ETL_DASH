@echo off
chcp 65001 >nul
title ETL Backend V2 - FastAPI - Porta 4001

pushd "%~dp0.."
set "ROOT_DIR=%CD%"
popd

:: Mata processos python na porta 4001
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":4001" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

cd /d "%ROOT_DIR%\backend"
echo ========================================
echo   ETL Dashboard V2 - Backend FastAPI
echo   Porta: 4001
echo ========================================
echo.

:: Verificar se uvicorn esta instalado
python -c "import uvicorn" >nul 2>&1
if errorlevel 1 (
    echo Instalando dependencias...
    pip install fastapi uvicorn[standard]
)

echo Iniciando Backend FastAPI...
python app.py
pause
