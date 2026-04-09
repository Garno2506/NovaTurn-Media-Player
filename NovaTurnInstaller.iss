[Setup]
AppId={{F4C9C9C4-9F0E-4F3E-9F11-ABCD1234NOVA}}
AppName=NovaTurn
AppVersion=1.0.0
AppPublisher=Micks Media
DefaultDirName={pf}\NovaTurn
DefaultGroupName=NovaTurn
DisableDirPage=no
DisableProgramGroupPage=no
OutputBaseFilename=NovaTurnSetup
Compression=lzma
SolidCompression=yes
SetupIconFile=app\assets\branding\novaturn.ico

UninstallDisplayIcon={app}\NovaTurn.exe
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a &desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Copy the entire PyInstaller output folder
Source: "dist\NovaTurn\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs



[Icons]
Name: "{group}\NovaTurn"; Filename: "{app}\NovaTurn.exe"; WorkingDir: "{app}"; IconFilename: "{app}\NovaTurn.ico"
Name: "{commondesktop}\NovaTurn"; Filename: "{app}\NovaTurn.exe"; WorkingDir: "{app}"; IconFilename: "{app}\NovaTurn.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\NovaTurn.exe"; Flags: nowait postinstall

