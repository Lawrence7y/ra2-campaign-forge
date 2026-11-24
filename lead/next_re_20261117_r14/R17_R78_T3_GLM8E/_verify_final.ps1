# R43-T3 最终复测快照（只读；全部文件带 LastWriteTime）
$root = 'D:\Project\ra2-campaign-forge'
$base = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
$NL = "`n"

function Read-Raw([string]$p) { Get-Content -LiteralPath $p -Raw }
function CountSub([string]$t, [string]$pat) {
  if ($pat.Length -eq 0) { return 0 }
  return (($t.Length - $t.Replace($pat, '').Length) / $pat.Length)
}
function Stat([string]$p) {
  $i = Get-Item -LiteralPath $p
  Write-Output ("  FILE " + $i.FullName)
  Write-Output ("    bytes=" + $i.Length + " last_write=" + $i.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))
}

Write-Output ("NOW=" + (Get-Date).ToString('yyyy-MM-dd HH:mm:ss'))

Write-Output '=== F1 V518 tsv ==='
$fi = Join-Path $base 'R17_R77_FACTINDEX_V518\FACT_INDEX.tsv'
Stat $fi
$t1 = Read-Raw $fi
$ends1 = $t1.EndsWith("`n")
$lines1 = @($t1 -split "`r?`n")
if ($ends1) { $lines1 = @($lines1[0..($lines1.Count - 2)]) }
$data = @()
for ($i = 1; $i -lt $lines1.Count; $i++) {
  if ($lines1[$i].Length -eq 0) { continue }
  $data += ,@($lines1[$i] -split "`t")
}
$dist = @{}
foreach ($r in $data) {
  $g = $r[2]
  if (-not $dist.ContainsKey($g)) { $dist[$g] = 0 }
  $dist[$g] = $dist[$g] + 1
}
$gstr = ($dist.Keys | Sort-Object | ForEach-Object { $_ + "=" + $dist[$_] }) -join ' '
Write-Output ("    data_rows=" + $data.Count + " cols_of_header=" + (@($lines1[0] -split "`t")).Count + " ; " + $gstr)
$f24 = @($data | Where-Object { $_[0] -eq 'F24' })[0]
$ev = $f24[3]
$parts = @()
$cur = ''
$depth = 0
for ($i = 0; $i -lt $ev.Length; $i++) {
  $ch = $ev[$i]
  if ($ch -eq '(' -or $ch -eq '（') { $depth = $depth + 1; $cur = $cur + $ch }
  elseif ($ch -eq ')' -or $ch -eq '）') { $depth = $depth - 1; $cur = $cur + $ch }
  elseif ($ch -eq ';' -and $depth -eq 0) { $parts += $cur; $cur = '' }
  else { $cur = $cur + $ch }
}
$parts += $cur
$ne = @($parts | Where-Object { $_.Trim().Length -gt 0 })
Write-Output ("    F24_evidence_items=" + $ne.Count)

Write-Output '=== F2 anchor_check ==='
$ac = Join-Path $base 'R17_R77_FACTINDEX_V518\anchor_check.txt'
Stat $ac

Write-Output '=== F4 R14_COMMON ==='
$r14 = Join-Path $base 'R14_COMMON.md'
Stat $r14
$t4 = Read-Raw $r14
Write-Output ("    sub_2_29=" + (CountSub $t4 '## 2.29') + " sub_2_30=" + (CountSub $t4 '## 2.30') + " sub_2_31=" + (CountSub $t4 '## 2.31'))

Write-Output '=== F5 ledger ==='
$led = Join-Path $root 'lead\GOAL_THREE_TARGETS_20261018.md'
Stat $led
$heads = @(Select-String -LiteralPath $led -Pattern '^## §[0-9]+')
$nums = @($heads | ForEach-Object { $_.Line.Substring(4).PadLeft(7, '0') })
$order = @()
for ($i = 0; $i -lt $heads.Count; $i++) { $order += ,@($nums[$i], $heads[$i].LineNumber) }
$byNum = @($order | Sort-Object -Property @{Expression = { $_[0] }; Descending = $true })
Write-Output ("    heading_count=" + $heads.Count + " max_heading=" + $byNum[0][0] + " at_line=" + $byNum[0][1])
$byFile = @($order | Sort-Object -Property @{Expression = { $_[1] }; Descending = $true })
Write-Output ("    last_heading_in_file_order=" + $byFile[0][0] + " at_line=" + $byFile[0][1])
foreach ($s in @('0001082', '0001083', '0001084', '0001085')) {
  $hit = @($order | Where-Object { $_[0] -eq $s })
  Write-Output ("    heading_" + $s + " exists=" + ($hit.Count -gt 0))
}

Write-Output '=== F6 board ==='
$sbp = Join-Path $base 'STATUS_BOARD.md'
Stat $sbp
$t6 = Read-Raw $sbp
$nl6 = CountSub $t6 $NL
$ends6 = $t6.EndsWith("`n")
Write-Output ("    newline_chars=" + $nl6 + " cr_chars=" + (CountSub $t6 "`r") + " ends_with_newline=" + $ends6)
$tl = @(@($t6 -split "`r?`n") | Where-Object { $_.Trim().Length -gt 0 } | Select-Object -Last 2)
foreach ($l in $tl) {
  $cut = 100
  if ($l.Length -lt $cut) { $cut = $l.Length }
  Write-Output ("    tail| " + $l.Substring(0, $cut))
}

Write-Output '=== F7 LEAD_LOCK ==='
$ll = Join-Path $root 'lead\LEAD_LOCK'
Stat $ll
$t7 = Read-Raw $ll
Write-Output ("    raw_BH=" + (CountSub $t7 '## BH ·') + " raw_BI=" + (CountSub $t7 '## BI ·') + " raw_BJ=" + (CountSub $t7 '## BJ ·'))

Write-Output '=== F8 SUPERSEDED ==='
$sup = @(Get-ChildItem -LiteralPath $base -Recurse -Filter 'SUPERSEDED.md' -File -ErrorAction SilentlyContinue | Sort-Object FullName)
$withArr = @()
$withoutArr = @()
foreach ($f in $sup) {
  $t = Read-Raw $f.FullName
  if ($t.Contains('R17_R77_FACTINDEX_V518')) { $withArr += $f.Directory.Name }
  else { $withoutArr += $f }
}
Write-Output ("    total=" + $sup.Count + " with_v518=" + $withArr.Count + " without=" + $withoutArr.Count)
foreach ($f in $withoutArr) { Write-Output ("    EXCEPT " + $f.Directory.Name + " (mtime=" + $f.LastWriteTime.ToString('HH:mm:ss') + ")") }

Write-Output '=== V519 annotation ==='
$p19 = Join-Path $base 'R17_R79_FACTINDEX_V519\FACT_INDEX.tsv'
if (Test-Path -LiteralPath $p19) { Stat $p19 }
