$boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime
Write-Output ("BOOT=" + $boot.ToString("yyyy-MM-dd HH:mm:ss"))
$e6005 = Get-WinEvent -FilterHashtable @{LogName='System'; ID=6005} -MaxEvents 1 -ErrorAction SilentlyContinue
if ($e6005) { Write-Output ("6005=" + $e6005.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")) } else { Write-Output "6005=none" }
$e6006 = Get-WinEvent -FilterHashtable @{LogName='System'; ID=6006} -MaxEvents 1 -ErrorAction SilentlyContinue
if ($e6006) { Write-Output ("6006prevshutdown=" + $e6006.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")) } else { Write-Output "6006=none" }
$reboot = Get-WinEvent -FilterHashtable @{LogName='System'; ProviderName='Microsoft-Windows-Kernel-General'; ID=127} -MaxEvents 1 -ErrorAction SilentlyContinue
if ($reboot) { Write-Output ("planreboot=" + $reboot.TimeCreated.ToString("yyyy-MM-dd HH:mm:ss")) }
