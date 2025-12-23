Set WshShell = CreateObject("WScript.Shell")
WshShell.CurrentDirectory = "C:\bloko\Fundos - Documentos\00. Monitoramento\01. Rotinas\03. Arquivos Rotina\DEV_ETL\scripts"
WshShell.Run "cmd /c iniciar.bat", 1, False
