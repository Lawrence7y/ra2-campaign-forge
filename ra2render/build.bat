@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x86
if errorlevel 1 exit /b 1

cd /d "%~dp0"

echo Building ra2render.dll...
cl.exe /nologo /O2 /W3 /EHsc /utf-8 /arch:SSE2 /LD dllmain.cpp blitter_hooks.cpp /Fe:ra2render.dll /link /MACHINE:X86 /SUBSYSTEM:WINDOWS kernel32.lib user32.lib winmm.lib
if errorlevel 1 exit /b 1

echo Building ra2loader.exe...
cl.exe /nologo /O2 /W3 /EHsc /utf-8 ra2loader.cpp /Fe:ra2loader.exe /link /MACHINE:X86 /SUBSYSTEM:CONSOLE kernel32.lib user32.lib
if errorlevel 1 exit /b 1

copy /y ra2render.dll "..\ra2youli\ra2render.dll"

rem [RADAR-FIX2] ra2loader.exe deployment is OPTIONAL now (default: do NOT overwrite the deployed loader).
rem Old behaviour unconditionally copied ra2loader.exe into ra2youli/, which is an out-of-scope side effect.
rem Use:  set RA2RENDER_DEPLOY_LOADER=1  then run build.bat
if /i "%RA2RENDER_DEPLOY_LOADER%"=="1" goto deploy_loader
echo [build.bat] skip ra2loader.exe deploy (default). Set RA2RENDER_DEPLOY_LOADER=1 to deploy it.
goto done

:deploy_loader
echo [build.bat] deploying ra2loader.exe to ..\ra2youli\
copy /y ra2loader.exe "..\ra2youli\ra2loader.exe"

:done
echo ALL BUILDS FINISHED SUCCESSFULLY
exit /b 0
