<#
.SYNOPSIS
  把单实例 Electron GUI harness 拉起到 CDP 调试端口，供 DSH harness-pilot 的 cdp 传输挂载。

.DESCRIPTION
  背景（2026-10-03 实测）：
  - harness-pilot 的 `harness_open(launch=true)` 只会"再启动一次"目标程序；
  - 对 Qoder CN / ZCode 这类 **Electron 单实例**应用，新进程会被已有实例顶掉，
    调试端口永远不会出现，报错形如：
      "the launched process was already gone — the app is most likely single-instance"
  - 而 `harness_dispatch` 的传输阶梯只走 acp → headless → pty → cdp，
    **窗口通道不参与 dispatch**，所以没有 CDP 就等于无法派发任务。
  本脚本补上缺失的一步：先结束旧实例（含 tray/helper），再带 --remote-debugging-port 启动，
  然后轮询 CDP 端点直到可用。

.NOTES
  端口必须与插件探测一致。实测（2026-10-03，harness_list probe=true）：
    qoder-cn-app  Qoder CN 桌面端  D:\Qoder CN\Qoder CN.exe        → 9344
    qoder-cn      Qoder CN IDE     D:\Qoder CN IDE\Qoder CN IDE.exe → 9336
    zcode         ZCode 桌面端     D:\zai\ZCode\ZCode.exe           → 9333
    mimo          Xiaomi MiMo      D:\mimo\Xiaomi MiMo\Xiaomi MiMo.exe
    mimo-ai       Xiaomi MiMo AI   D:\mimo\Xiaomi MiMo AI\Xiaomi MiMo AI.exe
  注意：同一个"Qoder CN"品牌有两个不同目标、两个不同端口，不要混用。
  本脚本只做"结束进程 + 启动进程 + 探测 HTTP"，不写任何游戏资产、不改任何项目文件。

.EXAMPLE
  pwsh -File tools/harness_launch_cdp.ps1 -App "Qoder CN" -Exe "D:\Qoder CN\Qoder CN.exe" -Port 9344
.EXAMPLE
  pwsh -File tools/harness_launch_cdp.ps1 -App "ZCode" -Exe "D:\zai\ZCode\ZCode.exe" -Port 9333
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory = $true)][string]$App,
  [Parameter(Mandatory = $true)][string]$Exe,
  [Parameter(Mandatory = $true)][int]$Port,
  [int]$WaitSeconds = 60,
  [int]$SettleSeconds = 5
)

$ErrorActionPreference = 'Stop'

function Write-Step([string]$m) { Write-Host "[harness_launch_cdp] $m" }

if (-not (Test-Path -LiteralPath $Exe)) {
  Write-Error "找不到可执行文件: $Exe"
  exit 2
}

$procName = [IO.Path]::GetFileNameWithoutExtension($Exe)

Write-Step "1/4 结束现有实例：进程名 '$procName'（App=$App）"
$existing = @(Get-Process -Name $procName -ErrorAction SilentlyContinue)
if ($existing.Count -eq 0) {
  Write-Step "  未发现运行中的实例"
} else {
  foreach ($p in $existing) { Write-Step "  Stop-Process pid=$($p.Id)" }
  $existing | Stop-Process -Force -ErrorAction SilentlyContinue
}
# 给 tray/helper 子进程真正退出的时间；今天实测：不等会继续命中单实例锁
Write-Step "  等待 ${SettleSeconds}s 让 tray/helper 退出"
Start-Sleep -Seconds $SettleSeconds

$still = @(Get-Process -Name $procName -ErrorAction SilentlyContinue)
if ($still.Count -gt 0) {
  Write-Warning "仍有 $($still.Count) 个 '$procName' 进程存活（pid: $($still.Id -join ', ')）——单实例锁可能仍在，后续启动可能被顶掉。"
}

Write-Step "2/4 带调试端口启动：$Exe --remote-debugging-port=$Port"
Start-Process -FilePath $Exe -ArgumentList "--remote-debugging-port=$Port"

Write-Step "3/4 轮询 CDP 端点 http://127.0.0.1:$Port/json/version （最多 ${WaitSeconds}s）"
$deadline = (Get-Date).AddSeconds($WaitSeconds)
$ok = $false
$lastErr = $null
while ((Get-Date) -lt $deadline) {
  try {
    $r = Invoke-WebRequest -Uri "http://127.0.0.1:$Port/json/version" -UseBasicParsing -TimeoutSec 2
    if ($r.StatusCode -eq 200) {
      Write-Step "  CDP 已就绪：$($r.Content)"
      $ok = $true
      break
    }
  } catch {
    $lastErr = $_.Exception.Message
    Start-Sleep -Seconds 2
  }
}

if (-not $ok) {
  Write-Error @"
CDP 端点未在 ${WaitSeconds}s 内出现（端口 $Port）。
最后一次错误：$lastErr
排查顺序：
  1) 确认旧实例（含 tray/helper）已完全退出：Get-Process -Name "$procName"
  2) 确认端口未被占用：Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
  3) 确认端口与插件探测一致（Qoder CN=9344, ZCode=9333）
  4) 有些应用需更长冷启动时间，可加大 -WaitSeconds
"@
  exit 1
}

Write-Step "4/4 完成。下一步在 DSH 中用 harness_open(target=<该 harness 名>, launch=false) 挂载，"
Write-Step "      挂上后 screen 首行应显示 transport=cdp cdp port $Port。"
exit 0
