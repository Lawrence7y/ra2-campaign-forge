# H34 verification: bidirectional check for the moved section
$ErrorActionPreference = 'Stop'

$root    = 'D:\Project\ra2-campaign-forge'
$base    = Join-Path $root 'lead\next_re_20261117_r14'
$board   = Join-Path $base 'STATUS_BOARD.md'
$arch    = Join-Path $base 'BOARD_ARCHIVE.md'
$deliver = Join-Path $root 'HYGIENE\H34'
$backup  = Join-Path $deliver 'STATUS_BOARD.before.md'

# Original moved block = lines 3..38 of the backup (1-indexed), i.e. index 2..37
$orig = [System.IO.File]::ReadAllLines($backup)
$moved = @($orig[2..37])

$archLines  = [System.IO.File]::ReadAllLines($arch)
$boardLines = [System.IO.File]::ReadAllLines($board)

# --- Direction 1: every moved line appears in ARCHIVE >= 1 time ---
$foundArchive = 0
$missingArchive = @()
foreach ($ln in $moved) {
  $c = @($archLines | Where-Object { $_ -ceq $ln }).Count
  if ($c -ge 1) { $foundArchive++ } else { $missingArchive += $ln }
}

# --- Direction 2: substantive moved lines no longer in BOARD ---
# blank lines are structural separators that legitimately exist elsewhere; excluded.
$nonBlank = @($moved | Where-Object { $_ -ne '' })
$stillInBoard = @()
foreach ($ln in $nonBlank) {
  $c = @($boardLines | Where-Object { $_ -ceq $ln }).Count
  if ($c -ge 1) { $stillInBoard += $ln }
}

# --- Pointer present exactly once ---
$ptr = @($boardLines | Where-Object { $_ -cmatch '^> 📦 ## 🔵 2026-11-19 13:1x' }).Count

# --- Keep-list sections still intact (compare to backup, byte-for-byte lines 39..297) ---
$origKept = @($orig[38..296])
$newKept  = @($boardLines[3..261])   # board now: 0,1 head; 2 pointer; 3..261 = 259 kept lines
$keepDiff = 0
for ($i=0; $i -lt $origKept.Count; $i++) {
  if ($origKept[$i] -cne $newKept[$i]) { $keepDiff++ }
}

"MOVED_TOTAL=$($moved.Count)"
"ARCHIVE_FOUND=$foundArchive"
"ARCHIVE_MISSING=$($missingArchive.Count)"
"NONBLANK_MOVED=$($nonBlank.Count)"
"STILL_IN_BOARD=$($stillInBoard.Count)"
"POINTER_COUNT=$ptr"
"KEEP_LINES=$($origKept.Count)"
"KEEP_DIFF=$keepDiff"
"BOARD_LINES=$($boardLines.Count)"
"ARCHIVE_LINES=$($archLines.Count)"

if ($missingArchive.Count -gt 0) {
  "--- ARCHIVE MISSING LINES ---"
  $missingArchive | ForEach-Object { "MISS: $_" }
}
if ($stillInBoard.Count -gt 0) {
  "--- STILL IN BOARD ---"
  $stillInBoard | ForEach-Object { "STILL: $_" }
}
