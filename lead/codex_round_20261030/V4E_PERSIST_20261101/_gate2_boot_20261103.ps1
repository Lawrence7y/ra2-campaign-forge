Add-Type -Namespace W -Name K -MemberDefinition '[DllImport("kernel32.dll")] public static extern ulong GetTickCount64();'
Write-Output ('TICK64_ms=' + [W.K]::GetTickCount64())
$os = Get-CimInstance Win32_OperatingSystem
Write-Output ('BOOT_TIME=' + $os.LastBootUpTime)
Write-Output ('UPTIME_ms=' + [long]((Get-Date) - $os.LastBootUpTime).TotalMilliseconds)
Write-Output ('WALL=' + (Get-Date -Format o))
Write-Output ('procs_gamemd=' + ((Get-Process gamemd,game,ra2loader,YURI -ErrorAction SilentlyContinue | Measure-Object).Count))
