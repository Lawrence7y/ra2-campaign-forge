# D-09-B 事后取证 v3：时间必须显式 [datetime]
$start = [datetime]"2026-10-24 10:36:00"
$end = [datetime]"2026-10-24 21:55:00"

"=== System provider 计数（开机至今）==="
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$start; EndTime=$end} -ErrorAction SilentlyContinue |
  Group-Object ProviderName | Sort-Object Count -Descending | Select-Object -First 20 Count, Name | Format-Table -AutoSize

"=== 显示/会话/电源 关键词 provider 明细 ==="
$kw = 'Display','Graphics','TermService','Session','Kernel-Power','Power-Troubleshooter','UMPHCM','volmgr','Time-Service','Kernel-General','Kernel-Boot'
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$start; EndTime=$end} -ErrorAction SilentlyContinue |
  Where-Object { $p = $_.ProviderName; @($kw | Where-Object { $p -match [regex]::Escape($_) }).Count -gt 0 } |
  Select-Object -First 45 TimeCreated, Id, LevelDisplayName, ProviderName,
    @{ n='Msg'; e={ if ($_.Message) { $_.Message.Substring(0, [Math]::Min(130, $_.Message.Length)) } } } |
  Format-Table -Wrap -AutoSize

"=== Application 1000/1001（崩溃/WER）==="
Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=$start; EndTime=$end; Id=1000,1001} -ErrorAction SilentlyContinue |
  Select-Object -First 45 TimeCreated, Id, ProviderName,
    @{ n='Msg'; e={ if ($_.Message) { $_.Message.Substring(0, [Math]::Min(160, $_.Message.Length)) } } } |
  Format-Table -Wrap -AutoSize
