@echo off
chcp 65001 >nul
title ETL Backend - FastAPI

pushd "%~dp0.."
set "ROOT_DIR=%CD%"
popd

echo ========================================
echo   ETL Dashboard V2 - Backend
echo ========================================
echo.

REM Verificar Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado!
    echo Por favor, instale Python 3.9 ou superior.
    pause
    exit /b 1
)

REM Limpar processos na porta 4001
echo Limpando processos antigos na porta 4001...
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":4001" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 1 /nobreak >nul

REM Verificar se porta está livre
netstat -ano | findstr ":4001" | findstr "LISTENING" >nul
if not errorlevel 1 (
    echo [AVISO] Porta 4001 ainda esta em uso. Tentando usar porta 4002...
    set "ETL_PORT=4002"
) else (
    set "ETL_PORT=4001"
)

cd /d "%ROOT_DIR%\backend"

echo.
echo Iniciando Backend FastAPI na porta %ETL_PORT%...
echo.

REM Configurar variável de ambiente se necessário
if defined ETL_PORT (
    set "ETL_PORT=%ETL_PORT%"
)

python app.py

if errorlevel 1 (
    echo.
    echo [ERRO] Backend falhou ao iniciar!
    pause
)
