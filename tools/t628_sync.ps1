<#
.SYNOPSIS
    从 t628 回传 R17 逆向成果文本，提交并推送到 GitHub。

.DESCRIPTION
    流程：
      1) 通过 ssh 把远端白名单文件打成 tar.gz（stdin 传脚本，stdout 二进制落盘）
      2) 本机 bsdtar 解包覆盖到仓库根
      3) 用与 .gitignore 一致的口径生成路径清单（单文件 < 1 MB）
      4) git add --pathspec-from-file -> commit -> push --no-verify

    设计约束：
      - 每 2 小时由计划任务 RA2-T628-Sync 触发，须无人值守：
        任何一步失败只记日志并以非 0 退出，不弹窗、不等待输入。
      - 互斥：.sync/run.lock 独占创建，避免上一轮未结束就重入。
      - 仓库 pre-commit / pre-push 是失效的 mimosa 僵尸 hook
        （目标 cli.js 已不存在），故一律 --no-verify。

.PARAMETER DryRun
    只做采集与解包，不提交、不推送。

.PARAMETER NoPush
    提交但不推送。

.PARAMETER MaxFileMB
    单文件体积上限（MB），默认 1。超过的不入库。

.EXAMPLE
    pwsh -NoProfile -File tools\t628_sync.ps1
#>
[CmdletBinding()]
param(
    [switch]$DryRun,
    [switch]$NoPush,
    [int]$MaxFileMB = 1
)

$ErrorActionPreference = 'Stop'
$PSNativeCommandUseErrorActionPreference = $false

$Repo      = 'D:\Project\ra2-campaign-forge'
$SshKey    = 'C:\Users\Administrator\.ssh\t628_ed25519'
$Remote    = 't628@192.168.1.68'
$SyncDir   = Join-Path $Repo '.sync'
$Collector = Join-Path $Repo 'tools\remote_collect.sh'
$TarPath   = Join-Path $SyncDir 'payload.tar.gz'
$LockPath  = Join-Path $SyncDir 'run.lock'
$LogPath   = Join-Path $SyncDir 'sync.log'
$PathNul   = Join-Path $SyncDir 'paths.nul'

New-Item -ItemType Directory -Force -Path $SyncDir | Out-Null

function Write-Log {
    param([string]$Message, [string]$Level = 'INFO')
    $line = '{0} [{1}] {2}' -f (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'), $Level, $Message
    Add-Content -Path $LogPath -Value $line -Encoding utf8
    Write-Host $line
}

# 日志轮转：保留最近 2000 行
if ((Test-Path $LogPath) -and ((Get-Item $LogPath).Length -gt 2MB)) {
    $tail = Get-Content $LogPath -Tail 2000
    Set-Content -Path $LogPath -Value $tail -Encoding utf8
}

# ---------- 互斥 ----------
if (Test-Path $LockPath) {
    $age = (Get-Date) - (Get-Item $LockPath).LastWriteTime
    if ($age.TotalMinutes -lt 90) {
        Write-Log "上一轮仍在运行（锁龄 $([int]$age.TotalMinutes) 分钟），本轮跳过" 'WARN'
        exit 0
    }
    Write-Log "发现陈旧锁（锁龄 $([int]$age.TotalMinutes) 分钟），接管" 'WARN'
    Remove-Item $LockPath -Force -ErrorAction SilentlyContinue
}
try {
    New-Item -ItemType File -Path $LockPath -ErrorAction Stop | Out-Null
} catch {
    Write-Log "无法创建锁：$($_.Exception.Message)" 'ERROR'
    exit 1
}

$exitCode = 0
try {
    Set-Location $Repo

    # ---------- 1. 采集 ----------
    if (-not (Test-Path $Collector)) { throw "缺少远端采集脚本：$Collector" }
    if (Test-Path $TarPath) { Remove-Item $TarPath -Force }

    Write-Log '开始从 t628 采集'
    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName  = 'ssh'
    $psi.Arguments = '-i "{0}" -o BatchMode=yes -o ConnectTimeout=15 -o ServerAliveInterval=15 -o ServerAliveCountMax=3 {1} bash -s' -f $SshKey, $Remote
    $psi.UseShellExecute        = $false
    $psi.RedirectStandardInput  = $true
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError  = $true
    $psi.CreateNoWindow         = $true

    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $proc = [System.Diagnostics.Process]::Start($psi)

    # stderr 异步读取，避免与 stdout 阻塞互锁
    $errTask = $proc.StandardError.ReadToEndAsync()

    # 传脚本到远端 stdin
    $scriptBytes = [System.IO.File]::ReadAllBytes($Collector)
    $proc.StandardInput.BaseStream.Write($scriptBytes, 0, $scriptBytes.Length)
    $proc.StandardInput.BaseStream.Flush()
    $proc.StandardInput.Close()

    # stdout（tar.gz）二进制落盘
    $outStream = [System.IO.File]::Create($TarPath)
    try   { $proc.StandardOutput.BaseStream.CopyTo($outStream) }
    finally { $outStream.Dispose() }

    $proc.WaitForExit()
    $sshExit = $proc.ExitCode
    $sw.Stop()

    $errText = $errTask.Result
    if ($errText) {
        foreach ($line in ($errText -split "`r?`n")) {
            if ($line.Trim()) { Write-Log "ssh: $line" }
        }
    }
    Write-Log ("ssh 采集结束 exit={0} 用时={1:N0}s" -f $sshExit, $sw.Elapsed.TotalSeconds)

    if ($sshExit -ne 0) { throw "ssh 采集失败（exit=$sshExit）" }
    if (-not (Test-Path $TarPath)) { throw '未生成 payload.tar.gz' }
    $tarSize = (Get-Item $TarPath).Length
    if ($tarSize -lt 1024) { throw "payload 异常小（$tarSize B），疑似空包" }
    Write-Log ("payload: {0:N1} MB" -f ($tarSize / 1MB))

    # ---------- 2. 解包 ----------
    & tar -xzf $TarPath -C $Repo
    if ($LASTEXITCODE -ne 0) { Write-Log "tar 解包返回 $LASTEXITCODE（部分文件可能跳过）" 'WARN' }
    Write-Log '解包完成'

    if ($DryRun) { Write-Log 'DryRun：跳过提交' 'WARN'; return }

    # ---------- 3. 生成清单 ----------
    $dry = git add -A --dry-run 2>&1
    $changed = @($dry | Where-Object { $_ -match '^add ' } | ForEach-Object {
        (($_ -replace "^add '", '') -replace "'$", '')
    })

    $maxBytes = $MaxFileMB * 1MB
    $keep = New-Object System.Collections.Generic.List[string]
    foreach ($p in $changed) {
        if (-not (Test-Path -LiteralPath $p)) { continue }
        $item = Get-Item -LiteralPath $p -ErrorAction SilentlyContinue
        if ($null -eq $item) { continue }
        if ($item.Length -ge $maxBytes) {
            Write-Log ("跳过超大文件（{0:N1} MB）：{1}" -f ($item.Length / 1MB), $p) 'WARN'
            continue
        }
        $keep.Add($p)
    }

    if ($keep.Count -eq 0) { Write-Log '无变更，跳过提交'; return }
    Write-Log "待提交 $($keep.Count) 个文件"

    $bytes = New-Object System.Collections.Generic.List[byte]
    foreach ($p in $keep) {
        $b = [System.Text.Encoding]::UTF8.GetBytes($p)
        $bytes.AddRange($b)
        $bytes.Add(0)
    }
    [System.IO.File]::WriteAllBytes($PathNul, $bytes.ToArray())

    git add --pathspec-from-file $PathNul --pathspec-file-nul 2>&1 | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "git add 失败（exit=$LASTEXITCODE）" }
    $staged = @(git diff --cached --name-only)
    if ($staged.Count -eq 0) { Write-Log '暂存区为空，跳过提交'; return }

    # ---------- 4. 提交 ----------
    $round = 'R?'
    $compact = Join-Path $Repo 'lead\next_re_20261117_r14\COMPACT_STATE.md'
    if (Test-Path $compact) {
        $m = Select-String -Path $compact -Pattern '当前已完成轮次：\s*(R\d+)' -Encoding utf8 |
             Select-Object -First 1
        if ($m) { $round = $m.Matches[0].Groups[1].Value }
    }

    $msg = @"
sync(t628): $round 回传（$($staged.Count) 文件）

自动同步：$(Get-Date -Format 'yyyy-MM-dd HH:mm')
来源：t628 /home/t628/projects/ra2-campaign-forge（R17 静态逆向权威态）
口径：md/py/tsv/txt/json/sh，排除写前备份、EVIDENCE/_audit、单文件 >= $MaxFileMB MB、游戏资源。

由 tools/t628_sync.ps1 生成，--no-verify（pre-commit/pre-push 为失效的 mimosa 僵尸 hook）。
"@
    $msgFile = Join-Path $SyncDir 'commit_msg.txt'
    Set-Content -Path $msgFile -Value $msg -Encoding utf8

    git commit --no-verify -F $msgFile 2>&1 | Select-Object -First 2 | ForEach-Object { Write-Log $_ }
    if ($LASTEXITCODE -ne 0) { throw "git commit 失败（exit=$LASTEXITCODE）" }
    $head = (git log --oneline -1)
    Write-Log "已提交：$head"

    # ---------- 5. 推送 ----------
    if ($NoPush) { Write-Log 'NoPush：跳过推送' 'WARN'; return }

    git push --no-verify origin main 2>&1 | Select-Object -Last 3 | ForEach-Object { Write-Log $_ }
    if ($LASTEXITCODE -ne 0) { throw "git push 失败（exit=$LASTEXITCODE）" }
    Write-Log "推送成功：$round / $($staged.Count) 文件"

} catch {
    Write-Log "失败：$($_.Exception.Message)" 'ERROR'
    $exitCode = 1
} finally {
    Remove-Item $LockPath -Force -ErrorAction SilentlyContinue
    if ((Test-Path $TarPath) -and -not $DryRun) { Remove-Item $TarPath -Force -ErrorAction SilentlyContinue }
}

exit $exitCode
