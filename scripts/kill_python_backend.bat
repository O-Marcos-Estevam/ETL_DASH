@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   Encerrando processos do Backend
echo ========================================
echo.

echo Limpando processos na porta 4001...
set "CONTADOR=0"
for /f "tokens=5" %%a in ('netstat -ano 2^>nul ^| findstr ":4001" ^| findstr "LISTENING"') do (
    set "PID=%%a"
    if not "!PID!"=="" (
        echo   Encerrando processo PID: !PID!
        taskkill /F /PID !PID! >nul 2>&1
        if !errorlevel! equ 0 (
            set /a CONTADOR+=1
        )
    )
)

timeout /t 1 /nobreak >nul

netstat -ano 2^>nul | findstr ":4001" | findstr "LISTENING" >nul
if errorlevel 1 (
    echo [OK] Porta 4001 esta livre!
) else (
    echo [AVISO] Ainda ha processos na porta 4001
)

echo.
pause
endlocal
