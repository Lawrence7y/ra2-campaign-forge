# _auditprobe_a3_thirdparty.ps1 — 第三口径：.NET System.Drawing 标准 PNG 解码器
Add-Type -AssemblyName System.Drawing
function Check($p) {
  try {
    $b = [System.Drawing.Bitmap]::FromFile($p)
    $w = $b.Width; $h = $b.Height; $pf = $b.PixelFormat
    $tl = $b.GetPixel(0,0); $mid = $b.GetPixel([int]($w/2),[int]($h/2))
    Write-Output ("OK  {0}  {1}x{2} {3} TL={4} MID={5}" -f (Split-Path $p -Leaf), $w, $h, $pf, $tl, $mid)
    $b.Dispose()
  } catch {
    Write-Output ("FAIL {0} :: {1}" -f $p, $_.Exception.Message)
  }
}
Check 'D:\Project\ra2-campaign-forge\lead\qc161_u0400_trip\c2ab_x\_preflight\20261027T125912\desktop.png'
Check 'C:\Users\Administrator\AppData\Local\Temp\auditprobe_a3\h7_roundtrip.png'
Check 'C:\Users\Administrator\AppData\Local\Temp\auditprobe_a3\v2_capture_sim.png'
Check 'C:\Users\Administrator\AppData\Local\Temp\auditprobe_a3\desktop_via_v2_capture.png'
Check 'C:\Users\Administrator\AppData\Local\Temp\auditprobe_a3\desktop_via_probe_capture.png'
