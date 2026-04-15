; PyCNCSync Installer
; Using NSIS

!include "MUI2.nsh"

; Basic settings
Name "PyCNCSync"
OutFile "dist\PyCNCSync-Installer.exe"
InstallDir "$PROGRAMFILES\PyCNCSync"
InstallDirRegKey HKLM "Software\PyCNCSync" "InstallDir"

; Pages
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_LANGUAGE "English"

; Installer sections
Section "Install"
  SetOutPath "$INSTDIR"
  File "dist\PyCNCSync.exe"
  
  ; Create Start Menu shortcuts
  CreateDirectory "$SMPROGRAMS\PyCNCSync"
  CreateShortcut "$SMPROGRAMS\PyCNCSync\PyCNCSync.lnk" "$INSTDIR\PyCNCSync.exe"
  CreateShortcut "$SMPROGRAMS\PyCNCSync\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  
  ; Create uninstaller
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  
  ; Registry entry for uninstall
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyCNCSync" "DisplayName" "PyCNCSync"
  WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyCNCSync" "UninstallString" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKLM "Software\PyCNCSync" "InstallDir" "$INSTDIR"
SectionEnd

; Uninstaller section
Section "Uninstall"
  RMDir /r "$SMPROGRAMS\PyCNCSync"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PyCNCSync"
  DeleteRegKey HKLM "Software\PyCNCSync"
SectionEnd
