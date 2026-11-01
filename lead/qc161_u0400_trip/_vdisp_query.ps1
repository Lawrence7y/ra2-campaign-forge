"=== 虚拟显示宿主进程（MuMu/GameViewer/雷电等）==="
Get-Process -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match 'MuMu|Nemu|GameViewer|AeonHD|Nox|Ldbox|VMware|VirtualBox' } |
  Select-Object Name, Id, StartTime | Format-Table -AutoSize
"=== 显示设备/监视器 CIM ==="
Get-CimInstance Win32_VideoController -ErrorAction SilentlyContinue |
  Select-Object Name, PNPDeviceID | Format-List
Get-CimInstance Win32_DesktopMonitor -ErrorAction SilentlyContinue |
  Select-Object Name, Status | Format-List
