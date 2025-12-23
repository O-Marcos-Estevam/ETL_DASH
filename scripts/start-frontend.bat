@echo off
chcp 65001 >nul
title ETL Frontend - Porta 4000

pushd "%~dp0.."
set "ROOT_DIR=%CD%"
popd

:: Mata processos node existentes na porta 4000
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":4000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

set "NODE_HOME=%ROOT_DIR%\node"
if exist "%NODE_HOME%" (
    set "PATH=%NODE_HOME%;%PATH%"
)

cd /d "%ROOT_DIR%\frontend"
echo Iniciando Frontend na porta 4000...
echo Digite 'h' + Enter para ver comandos de ajuda do Vite.
call "%NODE_HOME%\npm.cmd" run dev
pause
