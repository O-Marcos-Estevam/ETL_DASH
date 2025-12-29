@echo off
chcp 65001 >nul
title ETL Frontend - React

pushd "%~dp0.."
set "ROOT_DIR=%CD%"
popd

echo ========================================
echo   ETL Dashboard V2 - Frontend
echo ========================================
echo.

REM Verificar Node.js
node --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Node.js nao encontrado!
    echo Por favor, instale Node.js 18 ou superior.
    pause
    exit /b 1
)

cd /d "%ROOT_DIR%\frontend"

REM Verificar se node_modules existe
if not exist "node_modules" (
    echo [INFO] Instalando dependencias...
    call npm install
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar dependencias!
        pause
        exit /b 1
    )
)

echo.
echo Iniciando Frontend React na porta 4000...
echo.

call npm run dev

if errorlevel 1 (
    echo.
    echo [ERRO] Frontend falhou ao iniciar!
    pause
)
