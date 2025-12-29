@echo off
echo Parando processos do backend na porta 4001...

for /f "tokens=5" %%a in ('netstat -ano ^| findstr :4001 ^| findstr LISTENING') do (
    echo Encerrando processo PID: %%a
    taskkill /F /PID %%a 2>nul
)

echo Processos encerrados.
pause


