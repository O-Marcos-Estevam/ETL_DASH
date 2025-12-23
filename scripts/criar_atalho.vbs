Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

' Obtem o caminho do script atual para definir a raiz
strScriptPath = WScript.ScriptFullName
strScriptFolder = fso.GetParentFolderName(strScriptPath)
strDevETL = fso.GetParentFolderName(strScriptFolder)

' Caminho do VBS de inicio
strVBS = strDevETL & "\scripts\iniciar.vbs"
strWorkingDir = strDevETL & "\scripts"

' Icone Customizado (convertido do usuario)
strIcon = strDevETL & "\scripts\icon.ico"

' Funcao para criar atalho
Sub CriarAtalho(strPath, strName)
    Set oShortcut = WshShell.CreateShortcut(strPath & "\" & strName & ".lnk")
    oShortcut.TargetPath = "wscript.exe"
    oShortcut.Arguments = """" & strVBS & """"
    oShortcut.WorkingDirectory = strWorkingDir
    oShortcut.Description = "ETL Dashboard V2"
    oShortcut.IconLocation = strIcon
    oShortcut.Save
End Sub

' 1. Cria na pasta DEV_ETL
CriarAtalho strDevETL, "ETL Dashboard V2"

' 2. Cria na Area de Trabalho
strDesktop = WshShell.SpecialFolders("Desktop")
strLnkPath = strDesktop & "\ETL Dashboard V2.lnk"
If fso.FileExists(strLnkPath) Then
    fso.DeleteFile(strLnkPath)
End If
CriarAtalho strDesktop, "ETL Dashboard V2"

WScript.Echo "Atalhos atualizados com ICONE PERSONALIZADO!"
