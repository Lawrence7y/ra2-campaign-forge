# C26-01 ② AV 通道取证：趟窗 Application Error/WER 明细（含 12:13 旁证归属）
$start = [datetime]"2026-10-26 12:10:00"
$end   = [datetime]"2026-10-26 12:16:00"
Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=$start; EndTime=$end; Id=1000,1001} -ErrorAction SilentlyContinue |
  ForEach-Object {
    $first = ($_.Message -split "`n")[0]
    if ($first.Length -gt 90) { $first = $first.Substring(0,90) }
    "{0}  Id={1}  {2}" -f $_.TimeCreated.ToString("HH:mm:ss"), $_.Id, $first
  }
