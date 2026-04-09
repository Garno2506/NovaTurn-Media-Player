<<<<<<< HEAD
; --- Versioning (safe mode) ---
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0.0"
#endif

[Setup]
AppId={{F4C9C9C4-9F0E-4F3E-9F11-ABCD1234NOVA}}
AppName=NovaTurn
AppVersion={#MyAppVersion}
AppPublisher=Micks Media
DefaultDirName={pf}\NovaTurn
DefaultGroupName=NovaTurn
DisableDirPage=no
DisableProgramGroupPage=no
OutputBaseFilename=NovaTurnSetup-{#MyAppVersion}
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
Source: "dist\NovaTurn\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs
Source: "app\assets\branding\novaturn.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\NovaTurn"; Filename: "{app}\NovaTurn.exe"; WorkingDir: "{app}"; IconFilename: "{app}\NovaTurn.ico"
Name: "{commondesktop}\NovaTurn"; Filename: "{app}\NovaTurn.exe"; WorkingDir: "{app}"; IconFilename: "{app}\NovaTurn.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\NovaTurn.exe"; Flags: nowait postinstall


=======
; --- Versioning (safe mode) ---
#ifndef MyAppVersion
  #define MyAppVersion "1.0.0.0"
#endif

[Setup]
AppId={{F4C9C9C4-9F0E-4F3E-9F11-ABCD1234NOVA}}
AppName=NovaTurn
AppVersion={#MyAppVersion}
AppPublisher=Micks Media
DefaultDirName={pf}\NovaTurn
DefaultGroupName=NovaTurn
DisableDirPage=no
DisableProgramGroupPage=no
OutputBaseFilename=NovaTurnSetup-{#MyAppVersion}
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
Source: "dist\NovaTurn\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs
Source: "app\assets\branding\novaturn.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\NovaTurn"; Filename: "{app}\NovaTurn.exe"; WorkingDir: "{app}"; IconFilename: "{app}\NovaTurn.ico"
Name: "{commondesktop}\NovaTurn"; Filename: "{app}\NovaTurn.exe"; WorkingDir: "{app}"; IconFilename: "{app}\NovaTurn.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\NovaTurn.exe"; Flags: nowait postinstall


>>>>>>> be9547aaccb1857afa059ff99cc82f20dba6ff7b
