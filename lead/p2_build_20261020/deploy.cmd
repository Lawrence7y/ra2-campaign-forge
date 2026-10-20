@echo off
setlocal EnableExtensions
set "PKG=%~dp0"
set "GAMEDIR=%~1"
if "%GAMEDIR%"=="" set "GAMEDIR=D:\Project\ra2-campaign-forge\ra2youli"
if not exist "%GAMEDIR%\gamemd.exe" (
  echo [deploy] ERROR: gamemd.exe not found in "%GAMEDIR%"
  exit /b 2
)
for /f %%h in ('powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath '%PKG%ra2render.dll').Hash"') do set "DLLHASH=%%h"
if /i not "%DLLHASH%"=="39CBD665501416109368174394613C9608876728A3B57CA386AEE8BDFD60CCE3" (
  echo [deploy] ERROR: package DLL hash mismatch: %DLLHASH%
  exit /b 3
)
for /f %%h in ('powershell -NoProfile -Command "(Get-FileHash -Algorithm SHA256 -LiteralPath '%PKG%ra2render.ini').Hash"') do set "INIHASH=%%h"
if /i not "%INIHASH%"=="27C9A60C55A8A1B422D3EF06B90E3D343A93EB523A600286C937198B363ECEE4" (
  echo [deploy] ERROR: package ini hash mismatch: %INIHASH%
  exit /b 4
)
for /f %%t in ('powershell -NoProfile -Command "Get-Date -Format yyyyMMdd_HHmmss"') do set "TS=%%t"
set "BK=%PKG%backup_%TS%"
mkdir "%BK%" || exit /b 5
copy /y "%GAMEDIR%\ra2render.dll" "%BK%\ra2render.dll" >nul || exit /b 6
copy /y "%GAMEDIR%\ra2render.ini" "%BK%\ra2render.ini" >nul || exit /b 7
copy /y "%PKG%ra2render.dll" "%GAMEDIR%\ra2render.dll" >nul || exit /b 8
copy /y "%PKG%ra2render.ini" "%GAMEDIR%\ra2render.ini" >nul || exit /b 9
echo [deploy] OK. Backup: %BK%
echo [deploy] Next: cold start the game manually, then check ra2render.log per DEPLOY.md.
echo [deploy] Rollback: rollback.cmd "%GAMEDIR%" "%BK%"
exit /b 0
