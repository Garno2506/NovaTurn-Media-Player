; --- Automatic Versioning ---

; If MyBuildNumber is not passed from the command line, default to 0
#ifndef MyBuildNumber
  #define MyBuildNumber "0"
#endif

; Build full version string: 1.0.0.<build>
#define MyAppVersion "1.0.0." + MyBuildNumber

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
Name: "desktopicon"; Description: "Create a &desktop shortcut";
GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
; Copy the entire PyInstaller output folder
Source: "dist\NovaTurn\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs

; Copy the icon file so shortcuts can use it
Source: "app\assets\branding\novaturn.ico"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\NovaTurn"; Filename: "{app}\NovaTurn.exe";
WorkingDir: "{app}"; IconFilename: "{app}\NovaTurn.ico"

Name: "{commondesktop}\NovaTurn"; Filename: "{app}\NovaTurn.exe";
WorkingDir: "{app}"; IconFilename: "{app}\NovaTurn.ico"; Tasks: desktopicon

[Run]
Filename: "{app}\NovaTurn.exe"; Flags: nowait postinstall
