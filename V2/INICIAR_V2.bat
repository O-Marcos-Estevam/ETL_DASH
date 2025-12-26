@echo off
chcp 65001 >nul
title ETL Dashboard V2 - Launcher

echo ========================================
echo   ETL Dashboard V2 - Iniciando...
echo ========================================
echo.

pushd "%~dp0"
set "V2_DIR=%CD%"
popd

:: Verificar portas
echo Verificando portas...
netstat -ano | findstr ":4001" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo AVISO: Porta 4001 ja esta em uso!
)
netstat -ano | findstr ":4000" | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 (
    echo AVISO: Porta 4000 ja esta em uso!
)

:: Iniciar Backend em nova janela
echo.
echo Iniciando Backend FastAPI (porta 4001)...
start "ETL Backend V2" cmd /c ""%V2_DIR%\scripts\start-backend-v2.bat""
timeout /t 5 /nobreak >nul

:: Iniciar Frontend em nova janela
echo Iniciando Frontend React (porta 4000)...
start "ETL Frontend V2" cmd /c ""%V2_DIR%\scripts\start-frontend-v2.bat""
timeout /t 5 /nobreak >nul

:: Abrir navegador
echo.
echo Abrindo navegador...
start http://localhost:4000

echo.
echo ========================================
echo   Dashboard V2 iniciado!
echo   Frontend: http://localhost:4000
echo   Backend:  http://localhost:4001
echo   API Docs: http://localhost:4001/docs
echo ========================================
echo.
echo Feche esta janela para manter rodando em background
echo ou pressione qualquer tecla para sair...
pause >nul
