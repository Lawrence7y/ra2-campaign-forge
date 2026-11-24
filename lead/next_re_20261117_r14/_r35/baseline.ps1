# Baseline invariant checker (R17 round 35)
# CR invariant = count of CRLF (\r\n) occurrences, verified empirically.
$ErrorActionPreference = 'Stop'
$root = 'D:\Project\ra2-campaign-forge'
$r14  = Join-Path $root 'lead\next_re_20261117_r14'

function Get-Stat([string]$p) {
  $fi = Get-Item $p
  $t  = [IO.File]::ReadAllText($p)
  $crlf = ([regex]::Matches($t, "`r`n")).Count
  $lf   = ([regex]::Matches($t, "`n")).Count
  [pscustomobject]@{
    Path = $p; Bytes = $fi.Length; Chars = $t.Length
    CRLF = $crlf; LF = $lf; Sha256 = (Get-FileHash $p -Algorithm SHA256).Hash
  }
}

$files = [ordered]@{
  'R14_COMMON'    = Join-Path $r14 'R14_COMMON.md'
  'LEAD_LOCK'     = Join-Path $root 'lead\LEAD_LOCK'
  'LEDGER'        = Join-Path $root 'lead\GOAL_THREE_TARGETS_20261018.md'
  'STATUS_BOARD'  = Join-Path $r14 'STATUS_BOARD.md'
  'BOARD_ARCHIVE' = Join-Path $r14 'BOARD_ARCHIVE.md'
}

$expect = @{ 'R14_COMMON'=1081; 'LEAD_LOCK'=137; 'LEDGER'=337; 'STATUS_BOARD'=0; 'BOARD_ARCHIVE'=2952 }

$rows = foreach ($k in $files.Keys) { Get-Stat $files[$k] | Add-Member -NotePropertyName Key -NotePropertyValue $k -PassThru }

foreach ($r in $rows) {
  $e = $expect[$r.Key]
  $ok = if ($r.CRLF -eq $e) { 'PASS' } else { "FAIL(expected $e)" }
  '{0,-14} bytes={1,-9} CRLF={2,-6} {3}' -f $r.Key, $r.Bytes, $r.CRLF, $ok
}
''
'--- sha256 ---'
foreach ($r in $rows) { '{0,-14} {1}' -f $r.Key, $r.Sha256 }

# ledger max section
$lt = [IO.File]::ReadAllText($files['LEDGER'])
$secs = [regex]::Matches($lt, '(?m)^##\s*§(\d{4})') | ForEach-Object { [int]$_.Groups[1].Value }
$maxSec = ($secs | Measure-Object -Maximum).Maximum
''
'LEDGER sections={0} max=§{1}' -f $secs.Count, $maxSec

# board line count (LF based)
$bt = [IO.File]::ReadAllText($files['STATUS_BOARD'])
$boardLines = ([regex]::Matches($bt, "`n")).Count
if ($bt.Length -gt 0 -and $bt[-1] -ne "`n") { $boardLines++ }
'STATUS_BOARD lines={0} (limit 300)' -f $boardLines
