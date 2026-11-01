# 桌面锁定/输入桌面状态探针（只读，零写入）
Add-Type @"
using System;
using System.Runtime.InteropServices;
using System.Text;
public class D {
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern int GetClassNameW(IntPtr h, StringBuilder s, int n);
  [DllImport("user32.dll")] public static extern IntPtr OpenInputDesktop(uint flags, bool inherit, uint access);
  [DllImport("user32.dll", CharSet=CharSet.Unicode)] public static extern bool GetUserObjectInformationW(IntPtr h, int idx, StringBuilder pv, int n, out int needed);
}
"@
$fg = [D]::GetForegroundWindow()
"foreground hwnd = $fg"
$sb = New-Object System.Text.StringBuilder 256
[void][D]::GetClassNameW($fg, $sb, 256)
"foreground class = " + $sb.ToString()

# DESKTOP_READOBJECTS = 0x0001
$h = [D]::OpenInputDesktop(0, $false, 0x0001)
if ($h -eq [IntPtr]::Zero) {
  "OpenInputDesktop failed err=" + [Runtime.InteropServices.Marshal]::GetLastWin32Error()
} else {
  $name = New-Object System.Text.StringBuilder 256
  $need = 0
  [void][D]::GetUserObjectInformationW($h, 2, $name, 256, [ref]$need)
  "input desktop = " + $name.ToString()
}
"=== LogonUI / LockApp ==="
Get-Process -ErrorAction SilentlyContinue | Where-Object { $_.Name -match 'LogonUI|LockApp' } | Select-Object Name, Id | Format-Table -AutoSize
"=== sessions ==="
query session 2>&1 | Select-Object -First 6
