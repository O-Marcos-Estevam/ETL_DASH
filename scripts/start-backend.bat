@echo off
chcp 65001 >nul
title ETL Backend - Porta 4001

pushd "%~dp0.."
set "ROOT_DIR=%CD%"
popd

:: Mata processos java existentes na porta 4001
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":4001" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

cd /d "%ROOT_DIR%\backend"
set "JAVA_HOME=%ROOT_DIR%\java\jdk-17.0.2"
echo Iniciando Backend na porta 4001...
"%JAVA_HOME%\bin\java.exe" -jar target\etl-dashboard-2.0.0.jar
pause
