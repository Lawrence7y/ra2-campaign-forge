$ErrorActionPreference = 'Stop'
$root = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
$board = Join-Path $root 'STATUS_BOARD.md'
$archive = Join-Path $root 'BOARD_ARCHIVE.md'
$hydir = Join-Path $root '_hygiene\H34'
New-Item -ItemType Directory -Path $hydir -Force | Out-Null

# ---- backups (BEFORE any mutation) ----
Copy-Item -LiteralPath $board -Destination (Join-Path $hydir 'STATUS_BOARD.before.md') -Force
Copy-Item -LiteralPath $archive -Destination (Join-Path $hydir 'BOARD_ARCHIVE.before.md') -Force

function Get-Lines([string]$p) { [System.IO.File]::ReadAllLines($p, [System.Text.Encoding]::UTF8) }
function Save-Lines([string]$p, [string[]]$lines, [string]$nl) {
  $text = ($lines -join $nl) + $nl
  [System.IO.File]::WriteAllText($p, $text, (New-Object System.Text.UTF8Encoding($false)))
}
function Sha([string]$p) { (Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash }
function Stat([string]$p) {
  $i = Get-Item -LiteralPath $p
  ("{0:o}|{1}|{2}" -f $i.LastWriteTime, $i.Length, (Sha $p))
}

$b0 = Get-Lines $board
$a0 = Get-Lines $archive

# Detect newline style per file (board = LF, archive = CRLF)
$rawB = [System.IO.File]::ReadAllText($board, [System.Text.Encoding]::UTF8)
$rawA = [System.IO.File]::ReadAllText($archive, [System.Text.Encoding]::UTF8)
$nlB = if ($rawB.Contains("`r`n")) { "`r`n" } else { "`n" }
$nlA = if ($rawA.Contains("`r`n")) { "`r`n" } else { "`n" }
$nlBName = if ($nlB -eq "`r`n") { 'CRLF' } else { 'LF' }
$nlAName = if ($nlA -eq "`r`n") { 'CRLF' } else { 'LF' }

if ($b0.Count -ne 299) { throw "board line count unexpected: $($b0.Count) (expected 299)" }

# ---- 0-based ranges to move (content lines + their trailing blank separator) ----
$specs = @(
  @{ name='第 44–47 轮'; start=141; end=167; title='## 🔴 第 44–47 轮（2026-11-20 凌晨）· 三件事把 DoD 头条改写了' },
  @{ name='第 48–53 轮'; start=250; end=262; title='## 🔴 第 48–53 轮（2026-11-20 03:3x）· S17 依据改正 + 面板旧截面清查' },
  @{ name='第 54–56 轮'; start=263; end=274; title='## 🔴 第 54–56 轮（2026-11-20 04:1x）· **DoD 上限已证为 3/22**' }
)

foreach ($s in $specs) {
  if ($b0[$s.start] -ne $s.title) { throw ("heading mismatch for {0}: [{1}] vs [{2}]" -f $s.name, $b0[$s.start], $s.title) }
  if ($b0[$s.end].Trim() -ne '') { throw ("trailing line not blank for {0}: [{1}]" -f $s.name, $b0[$s.end]) }
  $lines = @($b0[$s.start..$s.end])
  $s['lines'] = $lines
  $s['nonblank'] = @($lines | Where-Object { $_.Trim() -ne '' })
}

$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'
$ptrs = foreach ($s in $specs) {
  "> 📦 $($s.title) 已归档至 BOARD_ARCHIVE.md（$stamp，逐字搬，missing=0；本次由 Lead 执行，卫生员 H34）"
}

# ---- build new board ----
$newBoard = @()
$newBoard += $b0[0..140]          # 1-141
$newBoard += $ptrs[0]
$newBoard += $b0[168..249]        # 169-250
$newBoard += $ptrs[1]
$newBoard += $ptrs[2]
$newBoard += $b0[275..298]        # 276-299
if ($newBoard.Count -gt 250) { throw "new board still >250: $($newBoard.Count)" }

# ---- build new archive: verbatim append ----
$newArchive = @()
$newArchive += $a0
$newArchive += ''
foreach ($s in $specs) { $newArchive += $s.lines; $newArchive += '' }

# ---- write via temp then verify then swap ----
$tmpB = Join-Path $hydir 'STATUS_BOARD.new.tmp'
$tmpA = Join-Path $hydir 'BOARD_ARCHIVE.new.tmp'
Save-Lines $tmpB $newBoard $nlB
Save-Lines $tmpA $newArchive $nlA

$vb = Get-Lines $tmpB
$va = Get-Lines $tmpA
if ($vb.Count -ne $newBoard.Count) { throw 'board temp line count mismatch' }
if ($va.Count -ne $newArchive.Count) { throw 'archive temp line count mismatch' }
foreach ($s in $specs) {
  foreach ($ln in $s.lines) {
    if (-not ($va -ccontains $ln)) { throw ("line missing in archive temp: [{0}]" -f $ln) }
  }
}
foreach ($i in 0..($b0.Count-1)) {
  # every original board line not in moved ranges must be present in new board
  $inMoved = $false
  foreach ($s in $specs) { if ($i -ge $s.start -and $i -le $s.end) { $inMoved = $true } }
  if (-not $inMoved) {
    if (-not ($vb -ccontains $b0[$i])) { throw ("kept line lost from board: [{0}]" -f $b0[$i]) }
  }
}

Move-Item -LiteralPath $tmpB -Destination $board -Force
Move-Item -LiteralPath $tmpA -Destination $archive -Force

# ---- post-move bidirectional verification ----
$afterB = Get-Lines $board
$afterA = Get-Lines $archive
$allMissingZero = $true
$report = @()
$report += "H34 整段搬家验证  时间=$stamp"
$report += "换行符：board=$nlBName, archive=$nlAName（各自原样保留）"
$report += ""
$report += "目标段 3 个：第 44–47 轮 / 第 48–53 轮 / 第 54–56 轮"
$report += ""
foreach ($s in $specs) {
  $moved = $s.nonblank.Count
  $found = 0
  $boardResidue = 0
  foreach ($ln in $s.nonblank) {
    if (@($afterA | Where-Object { $_ -ceq $ln }).Count -ge 1) { $found++ }
    $bc = @($afterB | Where-Object { $_ -ceq $ln -and $_ -notmatch '^> 📦 ' }).Count
    $origOther = @($b0 | Where-Object { $_ -ceq $ln }).Count - @($s.lines | Where-Object { $_ -ceq $ln }).Count
    if ($bc -ne $origOther) { $boardResidue++ }
  }
  $missing = $moved - $found
  if ($missing -ne 0) { $allMissingZero = $false }
  $report += ("{0}: moved={1} / found={2} / missing={3} / boardResidue={4}  (段总行数={5}, 含尾随空行)" -f $s.name, $moved, $found, $missing, $boardResidue, $s.lines.Count)
}
$report += ""
$report += ("搬后 board 行数={0}（≤250: {1}）" -f $afterB.Count, ($afterB.Count -le 250))
$report += ("搬后 archive 行数={0}" -f $afterA.Count)
Set-Content -LiteralPath (Join-Path $hydir 'VERIFY.txt') -Value $report -Encoding UTF8

$ba = @()
$ba += "BEFORE / AFTER  (mtime|bytes|sha256)"
$ba += ""
$ba += "STATUS_BOARD.md BEFORE: $(Stat (Join-Path $hydir 'STATUS_BOARD.before.md'))"
$ba += "STATUS_BOARD.md AFTER : $(Stat $board)"
$ba += ""
$ba += "BOARD_ARCHIVE.md BEFORE: $(Stat (Join-Path $hydir 'BOARD_ARCHIVE.before.md'))"
$ba += "BOARD_ARCHIVE.md AFTER : $(Stat $archive)"
$ba += ""
$ba += "board line count: 299 -> $($afterB.Count)"
$ba += "archive line count: $($a0.Count) -> $($afterA.Count)"
Set-Content -LiteralPath (Join-Path $hydir 'BEFORE_AFTER.txt') -Value $ba -Encoding UTF8

$log = @()
$log += "# H34 整段搬家日志"
$log += ""
$log += "时间：$stamp"
$log += ""
$log += "## 搬了哪几段"
foreach ($s in $specs) { $log += ("- $($s.title)  —— $($s.lines.Count) 行（含尾随空行；非空 $($s.nonblank.Count) 行）→ BOARD_ARCHIVE.md，原位置留 1 行指针") }
$log += ""
$log += "## 双向核对"
foreach ($s in $specs) {
  $moved = $s.nonblank.Count
  $found = @($s.nonblank | Where-Object { $_ -cin $afterA }).Count
  $log += ("- $($s.name): moved=$moved / found=$found / missing=$($moved-$found)")
}
$log += ""
$log += "## 搬后行数"
$log += "- STATUS_BOARD.md：$($afterB.Count) 行（≤250）"
$log += "- BOARD_ARCHIVE.md：$($afterA.Count) 行"
$log += ""
$log += "## 备份"
$log += "- _hygiene/H34/STATUS_BOARD.before.md（SHA256 $(Sha (Join-Path $hydir 'STATUS_BOARD.before.md'))）"
$log += "- _hygiene/H34/BOARD_ARCHIVE.before.md（SHA256 $(Sha (Join-Path $hydir 'BOARD_ARCHIVE.before.md'))）"
Set-Content -LiteralPath (Join-Path $hydir 'H34_LOG.md') -Value $log -Encoding UTF8

Write-Output "=== VERIFY ==="
Get-Content -LiteralPath (Join-Path $hydir 'VERIFY.txt') -Encoding UTF8
Write-Output "=== BEFORE_AFTER ==="
Get-Content -LiteralPath (Join-Path $hydir 'BEFORE_AFTER.txt') -Encoding UTF8
