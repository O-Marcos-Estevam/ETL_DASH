@echo off
REM ============================================================
REM ETL Dashboard V2 - Script de Testes Unificado
REM ============================================================
REM Executa testes do backend (Pytest) e frontend (Vitest)
REM
REM Uso:
REM   run-tests.bat           - Executa todos os testes
REM   run-tests.bat backend   - Apenas testes do backend
REM   run-tests.bat frontend  - Apenas testes do frontend
REM   run-tests.bat coverage  - Todos os testes com coverage
REM ============================================================

setlocal enabledelayedexpansion

set ROOT_DIR=%~dp0..
set BACKEND_DIR=%ROOT_DIR%\backend
set FRONTEND_DIR=%ROOT_DIR%\frontend

echo.
echo ============================================================
echo   ETL Dashboard V2 - Test Runner
echo ============================================================
echo.

REM Verificar argumento
set MODE=%1
if "%MODE%"=="" set MODE=all

REM ============================================================
REM Backend Tests (Pytest)
REM ============================================================
if "%MODE%"=="all" goto :run_backend
if "%MODE%"=="backend" goto :run_backend
if "%MODE%"=="coverage" goto :run_backend
goto :skip_backend

:run_backend
echo [BACKEND] Executando testes Python...
echo.

cd /d "%BACKEND_DIR%"

REM Verificar se pytest esta instalado
python -c "import pytest" 2>nul
if errorlevel 1 (
    echo [WARN] Pytest nao encontrado. Instalando dependencias...
    pip install -r requirements-dev.txt
)

REM Executar testes
if "%MODE%"=="coverage" (
    echo [BACKEND] Rodando com coverage...
    python -m pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
) else (
    python -m pytest tests/ -v
)

set BACKEND_RESULT=%errorlevel%

if %BACKEND_RESULT%==0 (
    echo.
    echo [BACKEND] ✓ Todos os testes passaram!
) else (
    echo.
    echo [BACKEND] ✗ Alguns testes falharam
)

echo.
:skip_backend

REM ============================================================
REM Frontend Tests (Vitest)
REM ============================================================
if "%MODE%"=="all" goto :run_frontend
if "%MODE%"=="frontend" goto :run_frontend
if "%MODE%"=="coverage" goto :run_frontend
goto :skip_frontend

:run_frontend
echo [FRONTEND] Executando testes React/TypeScript...
echo.

cd /d "%FRONTEND_DIR%"

REM Verificar se node_modules existe
if not exist "node_modules" (
    echo [WARN] node_modules nao encontrado. Instalando dependencias...
    npm install
)

REM Verificar se vitest esta instalado
npm list vitest >nul 2>&1
if errorlevel 1 (
    echo [WARN] Vitest nao encontrado. Instalando...
    npm install
)

REM Executar testes
if "%MODE%"=="coverage" (
    echo [FRONTEND] Rodando com coverage...
    npm run test:coverage
) else (
    npm run test:run
)

set FRONTEND_RESULT=%errorlevel%

if %FRONTEND_RESULT%==0 (
    echo.
    echo [FRONTEND] ✓ Todos os testes passaram!
) else (
    echo.
    echo [FRONTEND] ✗ Alguns testes falharam
)

echo.
:skip_frontend

REM ============================================================
REM Summary
REM ============================================================
echo ============================================================
echo   RESUMO
echo ============================================================

if "%MODE%"=="backend" (
    if %BACKEND_RESULT%==0 (
        echo   Backend: ✓ PASSOU
    ) else (
        echo   Backend: ✗ FALHOU
    )
)

if "%MODE%"=="frontend" (
    if %FRONTEND_RESULT%==0 (
        echo   Frontend: ✓ PASSOU
    ) else (
        echo   Frontend: ✗ FALHOU
    )
)

if "%MODE%"=="all" (
    if %BACKEND_RESULT%==0 (
        echo   Backend: ✓ PASSOU
    ) else (
        echo   Backend: ✗ FALHOU
    )
    if %FRONTEND_RESULT%==0 (
        echo   Frontend: ✓ PASSOU
    ) else (
        echo   Frontend: ✗ FALHOU
    )
)

if "%MODE%"=="coverage" (
    echo.
    echo   Coverage reports gerados:
    echo   - Backend:  %BACKEND_DIR%\htmlcov\index.html
    echo   - Frontend: %FRONTEND_DIR%\coverage\index.html
)

echo ============================================================
echo.

REM Retornar codigo de erro se algum teste falhou
if defined BACKEND_RESULT if %BACKEND_RESULT% neq 0 exit /b %BACKEND_RESULT%
if defined FRONTEND_RESULT if %FRONTEND_RESULT% neq 0 exit /b %FRONTEND_RESULT%

exit /b 0
