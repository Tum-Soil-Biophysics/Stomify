; Stomify Inno Setup Script
; Creates a professional Windows installer for Stomify - Stomatal Density Analyzer
;
; NOTE: Updated for PyInstaller --onedir mode.
; The dist\Stomify\ directory contains the EXE + all dependencies.
; This eliminates the 60-90 second temp-extraction delay on every launch.

#define MyAppName "Stomify - Stomatal Density Analyzer"
#define MyAppVersion "1.0"
#define MyAppPublisher "Vimukthi Viduranga"
#define MyAppURL "https://github.com/vimukthi-viduranga"
#define MyAppExeName "Stomify.exe"

; IMPORTANT: Update these paths to match your system
#define DistDir ".\dist\Stomify"
#define ModelDir "..\..\Models"
#define ResourceDir ".\resources"

[Setup]
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} v{#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
DefaultDirName={autopf}\Stomify
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=
OutputDir=..\installer_output
OutputBaseFilename=StomifySetup
SetupIconFile={#ResourceDir}\logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: checkedonce

[Files]
; Main application directory (PyInstaller --onedir output)
; This includes Stomify.exe + all DLLs, .pyd files, and bundled resources
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Default YOLO model
Source: "{#ModelDir}\StomifyModel.pt"; DestDir: "{app}\Models"; Flags: ignoreversion

[Icons]
Name: "{group}\Stomify"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\Uninstall Stomify"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Stomify"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
