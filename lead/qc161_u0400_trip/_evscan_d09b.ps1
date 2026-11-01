# D-09-B 事后取证：本机 10-24 10:36 开机以来，显示/会话/电源/崩溃事件
# 只读查询。目的：分离「无调试器 9 连败零窗口」= 会话内机器态漂移 的证据。
$start = Get-Date "2026-10-24 10:36"
$end = Get-Date

"=== 当前显示状态 ==="
Get-CimInstance Win32_VideoController | Select-Object -First 3 Name, CurrentHorizontalResolution, CurrentVerticalResolution, VideoModeDescription | Format-List

"=== System 日志 provider 计数（10:36 至今）==="
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$start; EndTime=$end} -ErrorAction SilentlyContinue |
  Group-Object ProviderName | Sort-Object Count -Descending | Select-Object -First 18 Count, Name | Format-Table -AutoSize

"=== 显示/会话/电源/磁盘 相关事件明细 ==="
$keep = @('Display','Graphics','TermService','TerminalServices','Session','Kernel-Power','Power-Troubleshooter','UMPHCM','volmgr','Ntfs','Time-Service')
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=$start; EndTime=$end} -ErrorAction SilentlyContinue |
  Where-Object { $p = $_.ProviderName; @($keep | Where-Object { $p -like ('*{0}*' -f $_) }).Count -gt 0 } |
  Select-Object -First 60 TimeCreated, Id, LevelDisplayName, ProviderName,
    @{ n='Msg'; e={ if ($_.Message) { $_.Message.Substring(0, [Math]::Min(130, $_.Message.Length)) } } } |
  Format-Table -Wrap -AutoSize

"=== 11:14-20:05（h7 末次成功→晚间首败）窗口内全部 Warning/Error ==="
Get-WinEvent -FilterHashtable @{LogName='System'; StartTime=(Get-Date '2026-10-24 11:14'); EndTime=(Get-Date '2026-10-24 20:05'); Level=2,3} -ErrorAction SilentlyContinue |
  Select-Object TimeCreated, Id, ProviderName,
    @{ n='Msg'; e={ if ($_.Message) { $_.Message.Substring(0, [Math]::Min(130, $_.Message.Length)) } } } |
  Format-Table -Wrap -AutoSize

"=== Application 日志 1000/1001（崩溃/WER，含 gamemd 关键词）10:36 至今 ==="
Get-WinEvent -FilterHashtable @{LogName='Application'; StartTime=$start; EndTime=$end; Id=1000,1001} -ErrorAction SilentlyContinue |
  Select-Object -First 40 TimeCreated, Id, ProviderName,
    @{ n='Msg'; e={ if ($_.Message) { $_.Message.Substring(0, [Math]::Min(150, $_.Message.Length)) } } } |
  Format-Table -Wrap -AutoSize
