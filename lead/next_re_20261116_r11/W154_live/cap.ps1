Add-Type -AssemblyName System.Drawing
$p = Get-Process gamemd
$h = $p.MainWindowHandle
Add-Type @"
using System;
using System.Runtime.InteropServices;
public class W {
  [DllImport("user32.dll")] public static extern bool GetWindowRect(IntPtr h, out RECT r);
  [DllImport("user32.dll")] public static extern bool SetProcessDPIAware();
  public struct RECT { public int Left, Top, Right, Bottom; }
}
"@
[void][W]::SetProcessDPIAware()
$r = New-Object W+RECT
[void][W]::GetWindowRect($h, [ref]$r)
$w = $r.Right - $r.Left; $hh = $r.Bottom - $r.Top
"window rect: $($r.Left),$($r.Top) ${w}x${hh}"
$bmp = New-Object System.Drawing.Bitmap $w, $hh
$g = [System.Drawing.Graphics]::FromImage($bmp)
$g.CopyFromScreen($r.Left, $r.Top, 0, 0, (New-Object System.Drawing.Size $w, $hh))
$out = "D:\Project\ra2-campaign-forge\lead\next_re_20261116_r11\W154_live\now_ingame.png"
$bmp.Save($out, [System.Drawing.Imaging.ImageFormat]::Png)
$g.Dispose(); $bmp.Dispose()
"saved $out"
