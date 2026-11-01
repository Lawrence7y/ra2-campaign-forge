"=== now / boot ==="
Get-Date -Format "yyyy-MM-dd HH:mm:ss"
(Get-CimInstance Win32_OperatingSystem).LastBootUpTime
"=== GameViewer/MuMu 宿主（启动时刻）==="
Get-Process -ErrorAction SilentlyContinue |
  Where-Object { $_.Name -match 'GameViewer|MuMu' } |
  Select-Object Name, Id, StartTime | Format-Table -AutoSize
"=== 监视器拓扑（Win32）==="
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class M {
  [StructLayout(LayoutKind.Sequential)] public struct R { public int l,t,r,b; }
  public delegate bool CB(IntPtr h, IntPtr dc, ref R rect, IntPtr data);
  [DllImport("user32.dll")] public static extern bool EnumDisplayMonitors(IntPtr dc, IntPtr clip, CB cb, IntPtr data);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
}
"@
$res = New-Object System.Collections.ArrayList
$cb = { param($h,$dc,[ref]$r,$d) $x = $r.Value; [void]$res.Add(("{0}x{1} @({2},{3})" -f ($x.r-$x.l), ($x.b-$x.t), $x.l, $x.t)); return $true }
[void][M]::EnumDisplayMonitors([IntPtr]::Zero, [IntPtr]::Zero, $cb, [IntPtr]::Zero)
$res
"前台窗口 hwnd: " + [M]::GetForegroundWindow()
"=== 会话状态 ==="
query session 2>&1 | Select-Object -First 6
