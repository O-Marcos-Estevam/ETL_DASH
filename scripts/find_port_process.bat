@echo off
echo Processos usando a porta 4001:
echo.

netstat -ano | findstr :4001 | findstr LISTENING

echo.
echo PID dos processos:
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :4001 ^| findstr LISTENING') do (
    echo.
    echo PID: %%a
    tasklist /FI "PID eq %%a" /FO LIST
    echo -------------------------
)

pause

