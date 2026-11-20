#define AppName "Golden Cookie Catcher"
#define AppVersion "1.5.0"
#define AppExe "GoldenCookieCatcher.exe"

[Setup]
AppId={{8C1D4E6A-2B77-4F19-9C33-7A5E0B1D4C21}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\GoldenCookieCatcher
DefaultGroupName={#AppName}
OutputBaseFilename=GoldenCookieCatcher_{#AppVersion}_setup
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico
UninstallDisplayIcon={app}\{#AppExe}
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
DisableProgramGroupPage=yes

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "dist\{#AppExe}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}"; Filename: "{app}\{#AppExe}"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\{#AppExe}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#AppExe}"; Description: "{cm:LaunchProgram,{#AppName}}"; Flags: nowait postinstall skipifsilent