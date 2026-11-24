# H34 verbatim section move: STATUS_BOARD.md -> BOARD_ARCHIVE.md
# Move exactly lines 3..38 (the 🔵 section), leave 1 pointer line.
$ErrorActionPreference = 'Stop'

$root    = 'D:\Project\ra2-campaign-forge'
$base    = Join-Path $root 'lead\next_re_20261117_r14'
$board   = Join-Path $base 'STATUS_BOARD.md'
$arch    = Join-Path $base 'BOARD_ARCHIVE.md'
$deliver = Join-Path $root 'HYGIENE\H34'

$utf8NoBom = New-Object System.Text.UTF8Encoding($false)

$boardLines = [System.IO.File]::ReadAllLines($board)
if ($boardLines.Count -ne 297) { throw "Expected 297 board lines, got $($boardLines.Count)" }

# Verify boundaries
if ($boardLines[2] -ne '## 🔵 2026-11-19 13:1x · r14-s8 接替（Lead 第 8 任）') { throw 'line 3 mismatch' }
if ($boardLines[38] -ne '## 🔴🔴 Lead 自认错误（本段最严重，必须记住）') { throw 'line 39 mismatch' }

$moved = @($boardLines[2..37])    # 36 lines, verbatim
$head  = @($boardLines[0..1])     # 2 lines (H1 + blank)
$kept  = @($boardLines[38..296])  # 259 lines (all keep-list sections)
if ($moved.Count -ne 36 -or $kept.Count -ne 259) { throw 'segment count mismatch' }

$title = $moved[0]
$stamp = Get-Date -Format 'yyyy-MM-dd HH:mm'
$pointer = "> 📦 $title 已归档至 BOARD_ARCHIVE.md（$stamp，逐字搬，missing=0；本次由 Lead 执行，卫生员 H34）"

# ---- 1) Append moved lines verbatim to BOARD_ARCHIVE.md ----
$ab = [System.IO.File]::ReadAllBytes($arch)
$sep = if ($ab.Length -gt 0 -and $ab[$ab.Length-1] -eq 10) { '' } else { "`n" }
$appendText = $sep + ([string]::Join("`n", $moved)) + "`n"
$appendBytes = $utf8NoBom.GetBytes($appendText)
$fs = [System.IO.File]::Open($arch, [System.IO.FileMode]::Append, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
try { $fs.Write($appendBytes, 0, $appendBytes.Length) } finally { $fs.Dispose() }

# ---- 2) Rewrite STATUS_BOARD.md: head + pointer + kept ----
$newBoard = @($head[0], $head[1], $pointer) + $kept
$newText = [string]::Join("`n", $newBoard) + "`n"
[System.IO.File]::WriteAllText($board, $newText, $utf8NoBom)

"MOVED_LINES=$($moved.Count)"
"POINTER=$pointer"
"NEW_BOARD_LINES=$($newBoard.Count)"
"APPEND_BYTES=$($appendBytes.Length)"
