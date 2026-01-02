; ============================================================
; ETL Dashboard - Inno Setup Installer Script
; ============================================================
; Para compilar: iscc setup.iss
; Requer: Inno Setup 6.x (https://jrsoftware.org/isinfo.php)
; ============================================================

#define MyAppName "ETL Dashboard"
#define MyAppVersion "2.1.0"
#define MyAppPublisher "BLOKO/REAG"
#define MyAppURL "https://github.com/O-Marcos-Estevam/ETL_DASH"
#define MyAppExeName "ETL_Dashboard.exe"
#define MyAppAssocName "ETL Dashboard"

[Setup]
; Identificador unico da aplicacao
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
AllowNoIcons=yes
; Arquivo de licenca (opcional)
; LicenseFile=..\..\..\LICENSE.txt
; Arquivo de informacoes pre-instalacao
; InfoBeforeFile=..\..\..\README.txt
; Diretorio de output
OutputDir=..\dist
OutputBaseFilename=ETL_Dashboard_Setup_v{#MyAppVersion}
; Icone do instalador
SetupIconFile=..\..\scripts\icon.ico
; Compressao
Compression=lzma2/ultra64
SolidCompression=yes
; Estilo do wizard
WizardStyle=modern
; Privilegios
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "portuguese"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
; Todos os arquivos da distribuicao
Source: "..\dist\ETL_Dashboard\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs
; NOTA: Nao use "Flags: ignoreversion" em arquivos compartilhados do sistema

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; Limpar logs e dados ao desinstalar (opcional)
Type: filesandordirs; Name: "{app}\logs"
Type: filesandordirs; Name: "{app}\data"

[Code]
// Codigo Pascal para verificacoes customizadas (opcional)
function InitializeSetup(): Boolean;
begin
  Result := True;
  // Adicionar verificacoes aqui se necessario
  // Ex: verificar versao do Windows, etc.
end;
