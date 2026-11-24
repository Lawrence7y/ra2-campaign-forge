$ErrorActionPreference = 'Stop'

$root    = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
$board   = Join-Path $root 'STATUS_BOARD.md'
$archive = Join-Path $root 'BOARD_ARCHIVE.md'
$work    = Join-Path $root '_hygiene\H34\pass2'
New-Item -ItemType Directory -Path $work -Force | Out-Null
if (Test-Path (Join-Path $work 'ROLLBACK.txt')) { Remove-Item -LiteralPath (Join-Path $work 'ROLLBACK.txt') -Force }

$utf8 = New-Object System.Text.UTF8Encoding($false)

function Snap([string]$p) {
    $it = Get-Item -LiteralPath $p
    return [pscustomobject]@{
        path   = $p
        lines  = ([IO.File]::ReadAllLines($p, [Text.Encoding]::UTF8)).Count
        bytes  = ([IO.File]::ReadAllBytes($p)).Length
        sha256 = (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash
        mtime  = $it.LastWriteTime.ToString('o')
    }
}
function Assert($cond, $msg) { if (-not $cond) { throw $msg } }

$b0 = Snap $board
$a0 = Snap $archive

Copy-Item -LiteralPath $board   -Destination (Join-Path $work 'STATUS_BOARD.before.md') -Force
Copy-Item -LiteralPath $archive -Destination (Join-Path $work 'BOARD_ARCHIVE.before.md') -Force

$bl = [IO.File]::ReadAllLines($board, [Text.Encoding]::UTF8)
$al = [IO.File]::ReadAllLines($archive, [Text.Encoding]::UTF8)

Assert ($bl.Count -eq 294) "board lines $($bl.Count) != 294"
Assert ($al.Count -eq 2868) "archive lines $($al.Count) != 2868"
Assert ($bl[226] -like '## 🔴 第 64–67 轮*') 'seg1 header mismatch'
Assert ($bl[236] -like '## 🔴 第 75–78 轮*') 'seg2 header mismatch'
Assert ($bl[251] -like '## 🔴 第 86–92 轮*') 'keep 86-92 header mismatch'

# 1-based inclusive 227-236 -> 0-based 226..235 ; 237-251 -> 236..250
$seg1 = $bl[226..235]
$seg2 = $bl[236..250]

$ts = '2026-11-20 19:50'
$ptr1 = '> 📦 ' + $bl[226] + ' 已归档至 BOARD_ARCHIVE.md（' + $ts + '，逐字搬，missing=0；本次由 Lead 执行，卫生员 H34）'
$ptr2 = '> 📦 ' + $bl[236] + ' 已归档至 BOARD_ARCHIVE.md（' + $ts + '，逐字搬，missing=0；本次由 Lead 执行，卫生员 H34）'

$newBoard = New-Object 'System.Collections.Generic.List[string]'
for ($i=0; $i -le 225; $i++) { [void]$newBoard.Add($bl[$i]) }
[void]$newBoard.Add($ptr1)
[void]$newBoard.Add($ptr2)
for ($i=251; $i -le 293; $i++) { [void]$newBoard.Add($bl[$i]) }

$newArch = New-Object 'System.Collections.Generic.List[string]'
foreach ($x in $al) { [void]$newArch.Add($x) }
foreach ($x in $seg1) { [void]$newArch.Add($x) }
foreach ($x in $seg2) { [void]$newArch.Add($x) }

try {
    [IO.File]::WriteAllText($board,   (($newBoard.ToArray() -join "`n")  + "`n"), $utf8)
    [IO.File]::WriteAllText($archive, (($newArch.ToArray()  -join "`r`n") + "`r`n"), $utf8)

    $nb = [IO.File]::ReadAllLines($board, [Text.Encoding]::UTF8)
    $na = [IO.File]::ReadAllLines($archive, [Text.Encoding]::UTF8)

    Assert ($nb.Count -eq 271) "new board lines $($nb.Count) != 271"
    Assert ($na.Count -eq ($al.Count + $seg1.Count + $seg2.Count)) "new archive lines $($na.Count) mismatch"

    for ($i=0; $i -le 225; $i++) { Assert ($nb[$i] -ceq $bl[$i]) "board prefix line $($i+1) changed" }
    Assert ($nb[226] -ceq $ptr1) 'pointer1 mismatch'
    Assert ($nb[227] -ceq $ptr2) 'pointer2 mismatch'
    for ($k=0; $k -le 42; $k++) { Assert ($nb[(228+$k)] -ceq $bl[(251+$k)]) "board suffix line $($k+252) changed" }
    for ($i=0; $i -lt $al.Count; $i++) { Assert ($na[$i] -ceq $al[$i]) "archive original line $($i+1) changed" }

    $archSet  = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($x in $na) { [void]$archSet.Add($x) }
    $boardSet = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($x in $nb) { [void]$boardSet.Add($x) }

    $results = @()
    $allOk = $true
    foreach ($seg in @(@{name='第 64–67 轮'; lines=$seg1}, @{name='第 75–78 轮'; lines=$seg2})) {
        $moved = $seg.lines.Count
        $found = 0
        foreach ($x in $seg.lines) { if ($archSet.Contains($x)) { $found++ } }
        $missing = $moved - $found
        $residual = @()
        foreach ($x in $seg.lines) { if ($x.Trim().Length -gt 0 -and $boardSet.Contains($x)) { $residual += $x } }
        if ($missing -ne 0 -or $residual.Count -gt 0) { $allOk = $false }
        $results += [pscustomobject]@{ segment=$seg.name; moved=$moved; found=$found; missing=$missing; residual=$residual.Count }
    }

    $keepHeaders = @(
      '## 🔴🔴 Lead 自认错误（本段最严重，必须记住）',
      '## 🔴 本段第二个系统性发现：**③b 才是真瓶颈，不是 ②④**（第 19–21 轮已量化到底）',
      '## 🔴 第 21 轮：`0045A640` 两卡相反，第三方裁决**推翻审计**',
      '## 🔴 流程缺陷（本段第三个，根因在我）',
      '## 🔴🔴 第 5 个错 + 最重大发现：`F3a` 317 行，「3 个达标」里 2 个是名义达标',
      '## 🔴 第 86–92 轮（2026-11-20 19:0x）· **具名通道收口，proved 累计 +173 行**',
      '## 🔴 第 93–95 轮（2026-11-20 19:2x）· **两条通道全部耗尽，proved 定格 1,654**',
      '## 🔴 第 96–98 轮（2026-11-20 19:4x）· **`[已证]` 的 ④ 完整性缺口：1,347 行（81.4%）没写成文 ④**',
      '## 基线与并发控制', '## 常设真机授权（已生效）', '## Lead 口径裁定（流程规范，非技术结论）'
    )
    foreach ($h in $keepHeaders) { Assert ($boardSet.Contains($h)) "KEEP header missing: $h" }

    if (-not $allOk) { throw "verification failed: missing/residual nonzero" }

    $b1 = Snap $board
    $a1 = Snap $archive

    # ---- deliverables ----
    $ba = @("BEFORE / AFTER (H34 pass2, 2026-11-20 19:50)", "")
    foreach ($s in @(@{tag='BEFORE';b=$b0;a=$a0},@{tag='AFTER';b=$b1;a=$a1})) {
        $ba += "$($s.tag) STATUS_BOARD.md : lines=$($s.b.lines) bytes=$($s.b.bytes) sha256=$($s.b.sha256) mtime=$($s.b.mtime)"
        $ba += "$($s.tag) BOARD_ARCHIVE.md: lines=$($s.a.lines) bytes=$($s.a.bytes) sha256=$($s.a.sha256) mtime=$($s.a.mtime)"
    }
    [IO.File]::WriteAllText((Join-Path $work 'BEFORE_AFTER.txt'), ($ba -join "`r`n") + "`r`n", $utf8)

    $vl = @("H34 pass2 VERIFY — 逐段 moved/found/missing", "")
    foreach ($r in $results) { $vl += ("{0}: moved={1} / found={2} / missing={3} / residual_in_board={4}" -f $r.segment,$r.moved,$r.found,$r.missing,$r.residual) }
    $vl += ""
    $vl += "board lines after = $($b1.lines)  (before $($b0.lines))"
    $vl += "archive lines after = $($a1.lines)  (before $($a0.lines))"
    $vl += "keep-list headers still present = $($keepHeaders.Count)/$($keepHeaders.Count)"
    $vl += "board prefix/suffix byte-identical = YES ; archive pre-existing lines byte-identical = YES"
    [IO.File]::WriteAllText((Join-Path $work 'VERIFY.txt'), ($vl -join "`r`n") + "`r`n", $utf8)

    $lg = @("H34 pass2 LOG — 整段搬家", "", "moved segments:")
    $lg += "1. 第 64–67 轮（board 原 227–236 行, $($seg1.Count) 行）-> BOARD_ARCHIVE.md 末尾；原位置留 1 行指针"
    $lg += "2. 第 75–78 轮（board 原 237–251 行, $($seg2.Count) 行）-> BOARD_ARCHIVE.md 末尾；原位置留 1 行指针"
    $lg += ""
    $lg += "逐字核对（双向）：每段每一行在 archive 中出现 >=1；board 中原文行已不存在（指针行除外）。"
    foreach ($r in $results) { $lg += ("  {0}: moved={1} / found={2} / missing={3}" -f $r.segment,$r.moved,$r.found,$r.missing) }
    $lg += ""
    $lg += "保留清单（Lead 自认错误 / ③b / 0045A640 / 流程缺陷 / F3a 317 / 第 86–92 / 第 93–95 / 第 96–98 / 基线与并发控制 / 常设真机授权 / Lead 口径裁定）一字未动。"
    $lg += "board: $($b0.lines) -> $($b1.lines) 行（目标 <=250 未达：仅获授权搬 2 段，净减 $($b0.lines-$b1.lines) 行）。"
    $lg += "rollback: 备份 STATUS_BOARD.before.md / BOARD_ARCHIVE.before.md 保留于本目录。"
    [IO.File]::WriteAllText((Join-Path $work 'H34_LOG.md'), ($lg -join "`r`n") + "`r`n", $utf8)

    $out = [pscustomobject]@{
        ok = $true
        board_lines_before = $b0.lines
        board_lines_after  = $b1.lines
        segments = $results
        board_before = $b0; board_after = $b1
        archive_before = $a0; archive_after = $a1
    }
    Write-Output ($out | ConvertTo-Json -Depth 6)
}
catch {
    Copy-Item -LiteralPath (Join-Path $work 'STATUS_BOARD.before.md')   -Destination $board   -Force
    Copy-Item -LiteralPath (Join-Path $work 'BOARD_ARCHIVE.before.md') -Destination $archive -Force
    $rb = @("H34 pass2 ROLLBACK", "error: $($_.Exception.Message)", "both files restored from backups in this directory.")
    [IO.File]::WriteAllText((Join-Path $work 'ROLLBACK.txt'), ($rb -join "`r`n") + "`r`n", $utf8)
    Write-Output ([pscustomobject]@{ok=$false; error=$_.Exception.Message} | ConvertTo-Json)
    exit 1
}
