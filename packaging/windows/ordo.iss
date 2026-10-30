; Instalador do Ordo Desktop para Windows (Inno Setup 6).
; Instala para o usuário atual, sem pedir permissão de administrador.
#define AppVersion GetEnv("ORDO_VERSION")
#if AppVersion == ""
  #define AppVersion "0.0.0"
#endif

[Setup]
AppId={{6F1C2E7A-4B3D-4E8A-9C21-0D7E5B9A3F42}
AppName=Ordo Desktop
AppVersion={#AppVersion}
AppPublisher=Luiz Santiago
AppPublisherURL=https://github.com/luizsant/OrdoDesktop
DefaultDirName={localappdata}\Programs\OrdoDesktop
DisableProgramGroupPage=yes
DisableDirPage=yes
PrivilegesRequired=lowest
OutputDir=..\..\dist
OutputBaseFilename=OrdoDesktop-{#AppVersion}-setup
SetupIconFile=ordo.ico
UninstallDisplayIcon={app}\OrdoDesktop.exe
UninstallDisplayName=Ordo Desktop
LicenseFile=..\..\LICENSE.md
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=no

[Languages]
Name: "en"; MessagesFile: "compiler:Default.isl"
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"
Name: "es"; MessagesFile: "compiler:Languages\Spanish.isl"

[Files]
Source: "..\..\dist\OrdoDesktop\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autoprograms}\Ordo Desktop"; Filename: "{app}\OrdoDesktop.exe"

[Run]
Filename: "{app}\OrdoDesktop.exe"; Description: "{cm:LaunchProgram,Ordo Desktop}"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Fecha o Ordo pelo próprio app, que devolve os ícones do Explorer antes de sair.
Filename: "{app}\OrdoDesktop.exe"; Parameters: "--quit"; Flags: runhidden waituntilterminated; RunOnceId: "QuitOrdo"

[Registry]
; Remove o "Iniciar com o Windows" que o app grava, ao desinstalar.
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueName: "OrdoDesktop"; Flags: uninsdeletevalue dontcreatekey

[Code]
function PrepareToInstall(var NeedsRestart: Boolean): String;
var
  Code: Integer;
begin
  { Atualização: fecha a versão aberta com segurança antes de substituir os arquivos. }
  if FileExists(ExpandConstant('{app}\OrdoDesktop.exe')) then
    Exec(ExpandConstant('{app}\OrdoDesktop.exe'), '--quit', '', SW_HIDE, ewWaitUntilTerminated, Code);
  Result := '';
end;
