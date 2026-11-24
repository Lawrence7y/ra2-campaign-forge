$ErrorActionPreference = 'Stop'

$root    = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
$board   = Join-Path $root 'STATUS_BOARD.md'
$archive = Join-Path $root 'BOARD_ARCHIVE.md'
$work    = Join-Path $root '_hygiene\H34\pass3'
New-Item -ItemType Directory -Path $work -Force | Out-Null
$rb = Join-Path $work 'ROLLBACK.txt'
if (Test-Path $rb) { Remove-Item -LiteralPath $rb -Force }

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

Assert ($bl.Count -eq 295) "board lines $($bl.Count) != 295"
Assert ($al.Count -eq 2893) "archive lines $($al.Count) != 2893"

# 1-based inclusive: seg1 229-245 (header + content + trailing blank) -> 0-based 228..244
#                  seg2 246-258 (header + content + trailing blank) -> 0-based 245..257
Assert ($bl[228] -like '## 🔴 第 86–92 轮*') 'seg1 header mismatch (line 229)'
Assert ($bl[244] -eq '') 'seg1 trailing blank mismatch (line 245)'
Assert ($bl[245] -like '## 🔴 第 93–95 轮*') 'seg2 header mismatch (line 246)'
Assert ($bl[257] -eq '') 'seg2 trailing blank mismatch (line 258)'
Assert ($bl[258] -like '## 🔴 第 96–98 轮*') 'KEEP 96-98 header mismatch (line 259)'

$seg1 = $bl[228..244]
$seg2 = $bl[245..257]

$ts = Get-Date -Format 'yyyy-MM-dd HH:mm'
$ptr1 = '> 📦 ' + $bl[228] + ' 已归档至 BOARD_ARCHIVE.md（' + $ts + '，逐字搬，missing=0；本次由 Lead 执行，卫生员 H34）'
$ptr2 = '> 📦 ' + $bl[245] + ' 已归档至 BOARD_ARCHIVE.md（' + $ts + '，逐字搬，missing=0；本次由 Lead 执行，卫生员 H34）'

$newBoard = New-Object 'System.Collections.Generic.List[string]'
for ($i=0; $i -le 227; $i++) { [void]$newBoard.Add($bl[$i]) }
[void]$newBoard.Add($ptr1)
[void]$newBoard.Add($ptr2)
for ($i=258; $i -le 294; $i++) { [void]$newBoard.Add($bl[$i]) }

$newArch = New-Object 'System.Collections.Generic.List[string]'
foreach ($x in $al) { [void]$newArch.Add($x) }
foreach ($x in $seg1) { [void]$newArch.Add($x) }
foreach ($x in $seg2) { [void]$newArch.Add($x) }

try {
    [IO.File]::WriteAllText($board,   (($newBoard.ToArray() -join "`n")  + "`n"), $utf8)
    [IO.File]::WriteAllText($archive, (($newArch.ToArray()  -join "`r`n") + "`r`n"), $utf8)

    $nb = [IO.File]::ReadAllLines($board, [Text.Encoding]::UTF8)
    $na = [IO.File]::ReadAllLines($archive, [Text.Encoding]::UTF8)

    Assert ($nb.Count -eq 267) "new board lines $($nb.Count) != 267"
    Assert ($na.Count -eq ($al.Count + $seg1.Count + $seg2.Count)) "new archive lines mismatch"

    for ($i=0; $i -le 227; $i++) { Assert ($nb[$i] -ceq $bl[$i]) "board prefix line $($i+1) changed" }
    Assert ($nb[228] -ceq $ptr1) 'pointer1 mismatch'
    Assert ($nb[229] -ceq $ptr2) 'pointer2 mismatch'
    for ($k=0; $k -le 36; $k++) { Assert ($nb[(230+$k)] -ceq $bl[(258+$k)]) "board suffix line $($k+259) changed" }
    for ($i=0; $i -lt $al.Count; $i++) { Assert ($na[$i] -ceq $al[$i]) "archive original line $($i+1) changed" }

    $archSet  = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($x in $na) { [void]$archSet.Add($x) }
    $boardSet = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($x in $nb) { [void]$boardSet.Add($x) }

    $results = @()
    $allOk = $true
    foreach ($seg in @(@{name='第 86–92 轮'; lines=$seg1}, @{name='第 93–95 轮'; lines=$seg2})) {
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
      '## 🔴 第 96–98 轮（2026-11-20 19:4x）· **`[已证]` 的 ④ 完整性缺口：1,347 行（81.4%）没写成文 ④**',
      '## 🔴 第 99–104 轮（2026-11-20 20:4x）· 91 行 ④ 补写成文：13.78% → 19.29%',
      '## 🔴 第 105–106 轮（2026-11-20 21:1x）· 746 批判死；11 行「0 引用」实为名字错',
      '## 基线与并发控制', '## 常设真机授权（已生效）', '## Lead 口径裁定（流程规范，非技术结论）'
    )
    foreach ($h in $keepHeaders) { Assert ($boardSet.Contains($h)) "KEEP header missing: $h" }

    # F3a (1)-(6) subsections must all still be present, verbatim
    $f3aSubs = @(
      '### (1) 我的扫描正则又太窄 —— 上段错 #8 的原样复发，且漏得更多',
      '### (2) 达标稳健性：**S15、S16 是名义达标；S17 仅在 D-38 不裁 (B) 时稳健**',
      '### (3) 这条发现意味着什么',
      '### (4) `MEASURE-F3A` 已把这 274 行逐行判完：**(甲) = 1 行、(乙) = 273 行**',
      '### (5) 🔴 结论必须更正：**「3 个达标」是名义的，严格口径下是 1 个（S17）**',
      '### (6) 附带发现（独立于 F3a，CONFLICT 级）'
    )
    foreach ($h in $f3aSubs) { Assert ($boardSet.Contains($h)) "KEEP F3a subsection missing: $h" }

    # moved headers must no longer be present as section headers in board
    Assert (-not ($boardSet.Contains($bl[228]))) 'moved seg1 header still in board'
    Assert (-not ($boardSet.Contains($bl[245]))) 'moved seg2 header still in board'

    if (-not $allOk) { throw "verification failed: missing/residual nonzero" }

    $b1 = Snap $board
    $a1 = Snap $archive

    # ---- deliverables ----
    $ba = @("BEFORE / AFTER (H34 pass3, $ts)", "")
    foreach ($s in @(@{tag='BEFORE';b=$b0;a=$a0},@{tag='AFTER';b=$b1;a=$a1})) {
        $ba += "$($s.tag) STATUS_BOARD.md : lines=$($s.b.lines) bytes=$($s.b.bytes) sha256=$($s.b.sha256) mtime=$($s.b.mtime)"
        $ba += "$($s.tag) BOARD_ARCHIVE.md: lines=$($s.a.lines) bytes=$($s.a.bytes) sha256=$($s.a.sha256) mtime=$($s.a.mtime)"
    }
    [IO.File]::WriteAllText((Join-Path $work 'BEFORE_AFTER.txt'), ($ba -join "`r`n") + "`r`n", $utf8)

    $vl = @("H34 pass3 VERIFY — 逐段 moved/found/missing", "")
    foreach ($r in $results) { $vl += ("{0}: moved={1} / found={2} / missing={3} / residual_in_board={4}" -f $r.segment,$r.moved,$r.found,$r.missing,$r.residual) }
    $vl += ""
    $vl += "board lines after = $($b1.lines)  (before $($b0.lines))"
    $vl += "archive lines after = $($a1.lines)  (before $($a0.lines))"
    $vl += "keep-list headers still present = $($keepHeaders.Count)/$($keepHeaders.Count) ; F3a subsections = $($f3aSubs.Count)/$($f3aSubs.Count)"
    $vl += "board prefix/suffix byte-identical = YES ; archive pre-existing lines byte-identical = YES"
    $vl += "target <=265: $(if($b1.lines -le 265){'MET'}else{'NOT MET (max reduction under keep-list + 2 pointer lines = 267)'})"
    [IO.File]::WriteAllText((Join-Path $work 'VERIFY.txt'), ($vl -join "`r`n") + "`r`n", $utf8)

    $lg = @("H34 pass3 LOG — 整段搬家", "", "moved segments:")
    $lg += "1. 第 86–92 轮（board 原 229–245 行, $($seg1.Count) 行含尾随空行）-> BOARD_ARCHIVE.md 末尾；原位置留 1 行指针"
    $lg += "2. 第 93–95 轮（board 原 246–258 行, $($seg2.Count) 行含尾随空行）-> BOARD_ARCHIVE.md 末尾；原位置留 1 行指针"
    $lg += ""
    $lg += "逐字核对（双向）：每段每一行在 archive 中出现 >=1；board 中原文非空行已不存在（指针行除外，空行按 pass2 惯例不计 residual）。"
    foreach ($r in $results) { $lg += ("  {0}: moved={1} / found={2} / missing={3} / residual={4}" -f $r.segment,$r.moved,$r.found,$r.missing,$r.residual) }
    $lg += ""
    $lg += "保留清单一字未动：Lead 自认错误 / ③b 才是真瓶颈 / 0045A640 裁决 / 流程缺陷 / F3a 317 行(含(1)-(6)) / 第 96–98 / 第 99–104 / 第 105–106 / 基线与并发控制 / 常设真机授权 / Lead 口径裁定。"
    $lg += "board: $($b0.lines) -> $($b1.lines) 行（目标 <=265 未达：仅两段可搬，30 源行 -> 2 指针行，净减 28 行为 keep-list 约束下的最大值）。"
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
    $r = @("H34 pass3 ROLLBACK", "error: $($_.Exception.Message)", "both files restored from backups in this directory.")
    [IO.File]::WriteAllText($rb, ($r -join "`r`n") + "`r`n", $utf8)
    Write-Output ([pscustomobject]@{ok=$false; error=$_.Exception.Message} | ConvertTo-Json)
    exit 1
}
