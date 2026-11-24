Add-Type -AssemblyName System.Drawing
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class WP {
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool PrintWindow(IntPtr h, IntPtr hdc, uint flags);
  [DllImport("user32.dll")] public static extern bool SetForegroundWindow(IntPtr h);
  [DllImport("user32.dll")] public static extern IntPtr GetForegroundWindow();
  [DllImport("user32.dll")] public static extern bool ShowWindow(IntPtr h, int c);
  public struct RECT { public int Left, Top, Right, Bottom; }
}
"@
[void][WP]::SetProcessDPIAware()
$p = Get-Process gamemd
$h = $p.MainWindowHandle
"gamemd hwnd=$h  title=$($p.MainWindowTitle)"
$r = New-Object WP+RECT; [void][WP]::GetWindowRect($h, [ref]$r)
$w = $r.Right-$r.Left; $hh = $r.Bottom-$r.Top
"rect=$($r.Left),$($r.Top) ${w}x${hh}  dpiAware"
$bmp = New-Object System.Drawing.Bitmap $w, $hh
$g = [System.Drawing.Graphics]::FromImage($bmp)
$hdc = $g.GetHdc()
$ok = [WP]::PrintWindow($h, $hdc, 2)
$g.ReleaseHdc($hdc); $g.Dispose()
"PrintWindow(flags=2) => $ok"
$bmp.Save("D:\Project\ra2-campaign-forge\lead\next_re_20261116_r11\W154_live\pw_ingame.png", [System.Drawing.Imaging.ImageFormat]::Png)
$bmp.Dispose()
[void][WP]::ShowWindow($h, 9)
[void][WP]::SetForegroundWindow($h)
Start-Sleep -Milliseconds 800
"foreground now = $([WP]::GetForegroundWindow())  (game=$h)"
