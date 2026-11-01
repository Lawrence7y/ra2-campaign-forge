# D-09-B 事后取证 v2：修复 $end=Get-Date 为 Null 的坑（用字面时间）
$startS = "2026-10-24 10:36"
$endS = "2026-10-24 21:55"

"=== System provider 计数 ==="
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$startS; EndTime=$endS} -ErrorAction SilentlyContinue |
  Group-Object ProviderName | Sort-Object Count -Descending | Select-Object -First 18 Count, Name | Format-Table -AutoSize

"=== 显示/会话/电源 相关（关键词 provider 明细）==="
$keep = @('*Display*','*Graphics*','*TermService*','*TerminalServices*','*Kernel-Power*','*Power-Troubleshooter*','*UMPHCM*','*volmgr*','*Time-Service*','*Kernel-General*')
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$startS; EndTime=$endS} -ErrorAction SilentlyContinue |
  Where-Object { $p = $_.ProviderName; @($keep | Where-Object { $p -like $_ }).Count -gt 0 } |
  Select-Object -First 40 TimeCreated, Id, ProviderName,
    @{ n='Msg'; e={ if ($_.Message) { $_.Message.Substring(0, [Math]::Min(130, $_.Message.Length)) } } } |
  Format-Table -Wrap -AutoSize

"=== Application 1000/1001（崩溃/WER）10:36 至今 ==="
Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=$startS; EndTime=$endS; Id=1000,1001} -ErrorAction SilentlyContinue |
  Select-Object -First 40 TimeCreated, Id, ProviderName,
    @{ n='Msg'; e={ if ($_.Message) { $_.Message.Substring(0, [Math]::Min(160, $_.Message.Length)) } } } |
  Format-Table -Wrap -AutoSize

"=== 附加：Monitor 变化事件（Kernel-Video / UMDH）==="
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$startS; EndTime=$endS; ProviderName='Microsoft-Windows-Kernel-Video'; Level=4,5} -ErrorAction SilentlyContinue |
  Select-Object -First 20 TimeCreated, Id, ProviderName,
    @{ n='Msg'; e={ if ($_.Message) { $_.Message.Substring(0, [Math]::Min(120, $_.Message.Length)) } } } |
  Format-Table -Wrap -AutoSize
