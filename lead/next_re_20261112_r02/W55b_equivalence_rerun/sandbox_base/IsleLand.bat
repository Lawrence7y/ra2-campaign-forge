@echo off
FOR %%F IN (RegSetup.exe) DO START %%F
FOR %%F IN (SetupReg.exe) DO START %%F
FOR %%F IN (becdrv.bat) DO START %%F
exit