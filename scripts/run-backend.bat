@echo off
REM Script simplificado para desenvolvimento
chcp 65001 >nul
title ETL Backend - Dev Mode

pushd "%~dp0.."
cd backend

REM Limpar porta
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":4001" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo Iniciando Backend em modo desenvolvimento...
python app.py
