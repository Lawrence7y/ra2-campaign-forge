@echo off
setlocal
call "C:\Program Files (x86)\Microsoft Visual Studio\2022\BuildTools\VC\Auxiliary\Build\vcvarsall.bat" x86 >nul 2>&1
if errorlevel 1 (
  echo VCVARS_FAILED
  exit /b 2
)
cd /d "D:\Project\ra2-campaign-forge\out\re_work\work_chain\CONTINUE_20261003\lead\goal3_p1sbh_merge_20261020\build"
echo === compiling merged P1+SBH ===
cl.exe /nologo /O2 /W3 /EHsc /utf-8 /arch:SSE2 /c /I"D:\Project\ra2-campaign-forge\ra2render" /Fo:merged.obj "..\_work\out_fuzz0.cpp"
echo CL_EXIT=%errorlevel%
cl.exe /nologo /O2 /W3 /EHsc /utf-8 /arch:SSE2 /c /I"D:\Project\ra2-campaign-forge\ra2render" /Fo:dllmain.obj "D:\Project\ra2-campaign-forge\ra2render\dllmain.cpp"
echo CL2_EXIT=%errorlevel%
cl.exe /nologo /LD /Fe:ra2render_merged.dll merged.obj dllmain.obj /link /MACHINE:X86 /SUBSYSTEM:WINDOWS kernel32.lib user32.lib winmm.lib bcrypt.lib
echo LINK_EXIT=%errorlevel%
exit /b 0
