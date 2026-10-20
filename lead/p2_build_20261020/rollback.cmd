@echo off
setlocal EnableExtensions
set "PKG=%~dp0"
set "GAMEDIR=%~1"
set "BK=%~2"
if "%GAMEDIR%"=="" set "GAMEDIR=D:\Project\ra2-campaign-forge\ra2youli"
if "%BK%"=="" (
  for /f "delims=" %%d in ('dir /b /ad /o-d "%PKG%backup_*" 2^>nul') do (
    set "BK=%PKG%%%d"
    goto :found
  )
)
:found
if "%BK%"=="" (
  echo [rollback] ERROR: no backup_* directory found
  exit /b 2
)
if not exist "%BK%\ra2render.dll" (
  echo [rollback] ERROR: missing "%BK%\ra2render.dll"
  exit /b 3
)
if not exist "%BK%\ra2render.ini" (
  echo [rollback] ERROR: missing "%BK%\ra2render.ini"
  exit /b 4
)
copy /y "%BK%\ra2render.dll" "%GAMEDIR%\ra2render.dll" >nul || exit /b 5
copy /y "%BK%\ra2render.ini" "%GAMEDIR%\ra2render.ini" >nul || exit /b 6
echo [rollback] OK from %BK%
exit /b 0
