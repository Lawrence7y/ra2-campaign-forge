$ErrorActionPreference = 'Stop'

$root    = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
$board   = Join-Path $root 'STATUS_BOARD.md'
$archive = Join-Path $root 'BOARD_ARCHIVE.md'
$work    = Join-Path $root '_hygiene\H34\pass4'
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

Assert ($bl.Count -eq 294) "board lines $($bl.Count) != 294"
Assert ($al.Count -eq 2923) "archive lines $($al.Count) != 2923"

# 1-based inclusive:
#   seg1 = 231-244 (header + blank + content + trailing blank) -> 0-based 230..243
#   seg2 = 245-259 (header + blank + content + trailing blank) -> 0-based 244..258
Assert ($bl[230] -like '## 🔴 第 96–98 轮*') 'seg1 header mismatch (line 231)'
Assert ($bl[243] -eq '') 'seg1 trailing blank mismatch (line 244)'
Assert ($bl[244] -like '## 🔴 第 99–104 轮*') 'seg2 header mismatch (line 245)'
Assert ($bl[258] -eq '') 'seg2 trailing blank mismatch (line 259)'
Assert ($bl[259] -like '## 🔴 第 105–106 轮*') 'KEEP 105-106 header mismatch (line 260)'

$seg1 = $bl[230..243]
$seg2 = $bl[244..258]

$ts = Get-Date -Format 'yyyy-MM-dd HH:mm'
$ptr1 = '> 📦 ' + $bl[230] + ' 已归档至 BOARD_ARCHIVE.md（' + $ts + '，逐字搬，missing=0；本次由 Lead 执行，卫生员 H34）'
$ptr2 = '> 📦 ' + $bl[244] + ' 已归档至 BOARD_ARCHIVE.md（' + $ts + '，逐字搬，missing=0；本次由 Lead 执行，卫生员 H34）'

$newBoard = New-Object 'System.Collections.Generic.List[string]'
for ($i=0; $i -le 229; $i++) { [void]$newBoard.Add($bl[$i]) }
[void]$newBoard.Add($ptr1)
[void]$newBoard.Add($ptr2)
for ($i=259; $i -le 293; $i++) { [void]$newBoard.Add($bl[$i]) }

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

    # byte-identical prefix/suffix
    for ($i=0; $i -le 229; $i++) { Assert ($nb[$i] -ceq $bl[$i]) "board prefix line $($i+1) changed" }
    Assert ($nb[230] -ceq $ptr1) 'pointer1 mismatch'
    Assert ($nb[231] -ceq $ptr2) 'pointer2 mismatch'
    for ($k=0; $k -le 34; $k++) { Assert ($nb[(232+$k)] -ceq $bl[(259+$k)]) "board suffix line $($k+260) changed" }
    for ($i=0; $i -lt $al.Count; $i++) { Assert ($na[$i] -ceq $al[$i]) "archive original line $($i+1) changed" }

    $archSet  = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($x in $na) { [void]$archSet.Add($x) }
    $boardSet = New-Object 'System.Collections.Generic.HashSet[string]'
    foreach ($x in $nb) { [void]$boardSet.Add($x) }

    $results = @()
    $allOk = $true
    foreach ($seg in @(@{name='第 96–98 轮'; lines=$seg1}, @{name='第 99–104 轮'; lines=$seg2})) {
        $moved = $seg.lines.Count
        $found = 0
        foreach ($x in $seg.lines) { if ($archSet.Contains($x)) { $found++ } }
        $missing = $moved - $found
        $residual = @()
        foreach ($x in $seg.lines) { if ($x.Trim().Length -gt 0 -and $boardSet.Contains($x)) { $residual += $x } }
        if ($missing -ne 0 -or $residual.Count -gt 0) { $allOk = $false }
        $results += [pscustomobject]@{ segment=$seg.name; moved=$moved; found=$found; missing=$missing; residual=$residual.Count }
    }

    # keep-list headers (user's 11-item list, verbatim from original board)
    $keepHdrIdx = @(3,28,54,68,76,259,268,285,142,163,167)
    $keepHeaders = @()
    foreach ($i in $keepHdrIdx) { $keepHeaders += $bl[$i] }
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

    # moved headers must no longer be present as standalone lines in board
    Assert (-not ($boardSet.Contains($bl[230]))) 'moved seg1 header still in board'
    Assert (-not ($boardSet.Contains($bl[244]))) 'moved seg2 header still in board'

    if (-not $allOk) { throw "verification failed: missing/residual nonzero" }
    foreach ($r in $results) { Assert ($r.missing -eq 0) "missing != 0 for $($r.segment)" }

    $b1 = Snap $board
    $a1 = Snap $archive

    # ---- deliverables ----
    $ba = @("BEFORE / AFTER (H34 pass4, $ts)", "")
    foreach ($s in @(@{tag='BEFORE';b=$b0;a=$a0},@{tag='AFTER';b=$b1;a=$a1})) {
        $ba += "$($s.tag) STATUS_BOARD.md : lines=$($s.b.lines) bytes=$($s.b.bytes) sha256=$($s.b.sha256) mtime=$($s.b.mtime)"
        $ba += "$($s.tag) BOARD_ARCHIVE.md: lines=$($s.a.lines) bytes=$($s.a.bytes) sha256=$($s.a.sha256) mtime=$($s.a.mtime)"
    }
    [IO.File]::WriteAllText((Join-Path $work 'BEFORE_AFTER.txt'), ($ba -join "`r`n") + "`r`n", $utf8)

    $vl = @("H34 pass4 VERIFY — 逐段 moved/found/missing", "")
    foreach ($r in $results) { $vl += ("{0}: moved={1} / found={2} / missing={3} / residual_in_board={4}" -f $r.segment,$r.moved,$r.found,$r.missing,$r.residual) }
    $vl += ""
    $vl += "board lines after = $($b1.lines)  (before $($b0.lines))"
    $vl += "archive lines after = $($a1.lines)  (before $($a0.lines))"
    $vl += "keep-list headers still present = $($keepHeaders.Count)/$($keepHeaders.Count) ; F3a subsections = $($f3aSubs.Count)/$($f3aSubs.Count)"
    $vl += "board prefix/suffix byte-identical = YES ; archive pre-existing lines byte-identical = YES"
    $vl += "target <=265: $(if($b1.lines -le 265){'MET'}else{'NOT MET (floor under keep-list + 2 pointer lines = 267, same as pass3)'})"
    [IO.File]::WriteAllText((Join-Path $work 'VERIFY.txt'), ($vl -join "`r`n") + "`r`n", $utf8)

    $lg = @("H34 pass4 LOG — 整段搬家", "", "moved segments:")
    $lg += "1. 第 96–98 轮（board 原 231–244 行, $($seg1.Count) 行含尾随空行）-> BOARD_ARCHIVE.md 末尾；原位置留 1 行指针"
    $lg += "2. 第 99–104 轮（board 原 245–259 行, $($seg2.Count) 行含尾随空行）-> BOARD_ARCHIVE.md 末尾；原位置留 1 行指针"
    $lg += ""
    $lg += "逐字核对（双向）：每段每一行在 archive 中出现 >=1；board 中原文非空行已不存在（指针行除外，空行按 pass2 惯例不计 residual）。"
    foreach ($r in $results) { $lg += ("  {0}: moved={1} / found={2} / missing={3} / residual={4}" -f $r.segment,$r.moved,$r.found,$r.missing,$r.residual) }
    $lg += ""
    $lg += "保留清单一字未动：Lead 自认错误 / ③b 才是真瓶颈 / 0045A640 裁决 / 流程缺陷 / F3a 317 行(含(1)-(6)) / 第 105–106 / 第 107–109 / 第 110 / 基线与并发控制 / 常设真机授权 / Lead 口径裁定。"
    $lg += "board: $($b0.lines) -> $($b1.lines) 行（可搬仅两段，29 源行 -> 2 指针行，净减 27；keep-list + 2 指针约束下的地板为 267，目标 <=265 不可达）。"
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
    $r = @("H34 pass4 ROLLBACK", "error: $($_.Exception.Message)", "both files restored from backups in this directory.")
    [IO.File]::WriteAllText($rb, ($r -join "`r`n") + "`r`n", $utf8)
    Write-Output ([pscustomobject]@{ok=$false; error=$_.Exception.Message} | ConvertTo-Json)
    exit 1
}
