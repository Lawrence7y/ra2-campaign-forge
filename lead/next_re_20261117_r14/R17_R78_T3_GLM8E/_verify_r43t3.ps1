# R43-T3-GLM8E 八项纯文本核对脚本（只读，不改任何既有文件）
$ErrorActionPreference = 'Continue'
$base = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
$root = 'D:\Project\ra2-campaign-forge'
$NL = "`n"

function Read-Raw([string]$p) { Get-Content -LiteralPath $p -Raw }
function FileLen([string]$p) { (Get-Item -LiteralPath $p).Length }
function CountSub([string]$t, [string]$pat) {
  if ($pat.Length -eq 0) { return 0 }
  return (($t.Length - $t.Replace($pat, '').Length) / $pat.Length)
}

Write-Output '=== ITEM 1 FACT_INDEX.tsv ==='
$fi = Join-Path $base 'R17_R77_FACTINDEX_V518\FACT_INDEX.tsv'
Write-Output ("path=" + $fi)
Write-Output ("path_exists=" + (Test-Path -LiteralPath $fi))
$t1 = Read-Raw $fi
$len1 = FileLen $fi
$nl1 = CountSub $t1 $NL
$cr1 = CountSub $t1 "`r"
$ends1 = $t1.EndsWith("`n")
$lines1 = @($t1 -split "`r?`n")
if ($ends1) { $lines1 = @($lines1[0..($lines1.Count - 2)]) }
Write-Output ("bytes=" + $len1 + " newline_chars=" + $nl1 + " cr_chars=" + $cr1 + " ends_with_newline=" + $ends1 + " total_lines=" + $lines1.Count)
$hdr = @($lines1[0] -split "`t")
Write-Output ("header_cols=" + $hdr.Count + " header=" + ($hdr -join ' | '))
$data = @()
$bad = @()
for ($i = 1; $i -lt $lines1.Count; $i++) {
  if ($lines1[$i].Length -eq 0) { $bad += ("empty_line@" + ($i + 1)); continue }
  $f = @($lines1[$i] -split "`t")
  if ($f.Count -ne $hdr.Count) { $bad += ("line" + ($i + 1) + "_cols=" + $f.Count) }
  $data += ,$f
}
Write-Output ("data_rows=" + $data.Count + " anomalies=[" + ($bad -join ',') + "]")
$dist = @{}
foreach ($r in $data) {
  $g = $r[2]
  if (-not $dist.ContainsKey($g)) { $dist[$g] = 0 }
  $dist[$g] = $dist[$g] + 1
}
foreach ($k in ($dist.Keys | Sort-Object)) { Write-Output ("grade[" + $k + "]=" + $dist[$k]) }
Write-Output ("first_id=" + $data[0][0] + " last_id=" + $data[$data.Count - 1][0])

Write-Output '=== ITEM 2 anchor_check.txt ==='
$ac = Join-Path $base 'R17_R77_FACTINDEX_V518\anchor_check.txt'
$t2 = Read-Raw $ac
$lines2 = @($t2 -split "`r?`n")
foreach ($l in $lines2) { Write-Output ("| " + $l) }

Write-Output '=== ITEM 3 F24 evidence_paths ==='
$f24 = @($data | Where-Object { $_[0] -eq 'F24' })[0]
if ($null -eq $f24) {
  Write-Output 'F24 未找到'
} else {
  Write-Output ("f24_cols=" + $f24.Count)
  $ev = $f24[3]
  Write-Output ("ev_chars=" + $ev.Length)
  $cut = 120
  if ($ev.Length -lt $cut) { $cut = $ev.Length }
  Write-Output ("ev_first120=" + $ev.Substring(0, $cut))
  Write-Output ("ev_contains_fullwidth_semicolon=" + $ev.Contains('；'))
  $naive = @($ev -split ';')
  Write-Output ("naive_semicolon_split_count=" + $naive.Count)
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
  $nonEmpty = @($parts | Where-Object { $_.Trim().Length -gt 0 })
  Write-Output ("bracket_aware_items=" + $nonEmpty.Count)
  $idx = 0
  foreach ($p in $nonEmpty) { $idx = $idx + 1; Write-Output ("  [" + $idx + "] " + $p) }
  $withSemi = @($nonEmpty | Where-Object { $_.Contains(';') })
  Write-Output ("items_containing_inner_semicolon=" + $withSemi.Count)
  foreach ($p in $withSemi) { Write-Output ("  inner: " + $p) }
}

Write-Output '=== ITEM 4 R14_COMMON.md ==='
$r14 = Join-Path $base 'R14_COMMON.md'
$t4 = Read-Raw $r14
$len4 = FileLen $r14
$c229raw = CountSub $t4 '## 2.29'
$c230raw = CountSub $t4 '## 2.30'
$l229 = @(@($t4 -split "`r?`n") | Where-Object { $_ -match '^## 2\.29(?!\d)' })
$l230 = @(@($t4 -split "`r?`n") | Where-Object { $_ -match '^## 2\.30(?!\d)' })
Write-Output ("bytes=" + $len4)
Write-Output ("raw_substring_2_29=" + $c229raw + " line_start_2_29=" + $l229.Count)
foreach ($l in $l229) { Write-Output ("  H229: " + $l) }
Write-Output ("raw_substring_2_30=" + $c230raw + " line_start_2_30=" + $l230.Count)
foreach ($l in $l230) { Write-Output ("  H230: " + $l) }

Write-Output '=== ITEM 5 GOAL_THREE_TARGETS_20261018.md ==='
$led = Join-Path $root 'lead\GOAL_THREE_TARGETS_20261018.md'
Write-Output ("path_exists=" + (Test-Path -LiteralPath $led))
$len5 = FileLen $led
Write-Output ("bytes=" + $len5)
$toks = @(Select-String -LiteralPath $led -Pattern '§[0-9]+' -AllMatches | ForEach-Object { $_.Matches } | ForEach-Object { $_.Value })
Write-Output ("section_tokens=" + $toks.Count)
$padded = @($toks | ForEach-Object { $_.Substring(1).PadLeft(7, '0') })
$sorted = @($padded | Sort-Object -Descending)
Write-Output ("max_token=" + $sorted[0])
Write-Output ("top5=" + ((@($sorted | Select-Object -First 5)) -join ','))
$t5 = Read-Raw $led
$c1082 = CountSub $t5 '§1082'
$c1083 = CountSub $t5 '§1083'
Write-Output ("occurrences_1082=" + $c1082 + " occurrences_1083=" + $c1083)
$m2 = @(Select-String -LiteralPath $led -Pattern '§1082' | Select-Object -First 1)
$m3 = @(Select-String -LiteralPath $led -Pattern '§1083' | Select-Object -First 1)
if ($m2.Count -gt 0) {
  $l = $m2[0].Line
  $cut = 120
  if ($l.Length -lt $cut) { $cut = $l.Length }
  Write-Output ("first_line_1082: " + $l.Substring(0, $cut))
} else { Write-Output 'first_line_1082: 未取得' }
if ($m3.Count -gt 0) {
  $l = $m3[0].Line
  $cut = 120
  if ($l.Length -lt $cut) { $cut = $l.Length }
  Write-Output ("first_line_1083: " + $l.Substring(0, $cut))
} else { Write-Output 'first_line_1083: 未取得' }

Write-Output '=== ITEM 6 STATUS_BOARD.md (next_re_20261117_r14) ==='
$sbp = Join-Path $base 'STATUS_BOARD.md'
$t6 = Read-Raw $sbp
$len6 = FileLen $sbp
$nl6 = CountSub $t6 $NL
$cr6 = CountSub $t6 "`r"
$ends6 = $t6.EndsWith("`n")
Write-Output ("path=" + $sbp)
Write-Output ("bytes=" + $len6 + " newline_chars=" + $nl6 + " cr_chars=" + $cr6 + " ends_with_newline=" + $ends6)
Write-Output ("contains 第空格42空格轮=" + $t6.Contains('第 42 轮') + " contains 第42轮=" + $t6.Contains('第42轮'))
$tail6 = @(@($t6 -split "`r?`n") | Select-Object -Last 3)
foreach ($l in $tail6) { Write-Output ("  tail| " + $l) }

Write-Output '=== ITEM 7 LEAD_LOCK ==='
$ll = Join-Path $root 'lead\LEAD_LOCK'
Write-Output ("path_exists=" + (Test-Path -LiteralPath $ll))
$len7 = FileLen $ll
$t7 = Read-Raw $ll
$bhRaw = CountSub $t7 '## BH ·'
$biRaw = CountSub $t7 '## BI ·'
$bhLines = @(@($t7 -split "`r?`n") | Where-Object { $_ -match '^## BH' })
$biLines = @(@($t7 -split "`r?`n") | Where-Object { $_ -match '^## BI' })
Write-Output ("bytes=" + $len7)
Write-Output ("raw_###BH_count=" + $bhRaw + " raw_###BI_count=" + $biRaw)
Write-Output ("line_start_BH=" + $bhLines.Count + " line_start_BI=" + $biLines.Count)
foreach ($l in $bhLines) { Write-Output ("  BH: " + $l) }
foreach ($l in $biLines) { Write-Output ("  BI: " + $l) }

Write-Output '=== ITEM 8 SUPERSEDED.md ==='
$sup = @(Get-ChildItem -LiteralPath $base -Recurse -Filter 'SUPERSEDED.md' -File -ErrorAction SilentlyContinue | Sort-Object FullName)
Write-Output ("total=" + $sup.Count)
$withArr = @()
$withoutArr = @()
foreach ($f in $sup) {
  $t = Read-Raw $f.FullName
  if ($t.Contains('R17_R77_FACTINDEX_V518')) { $withArr += $f.Directory.Name }
  else { $withoutArr += $f }
}
Write-Output ("with_v518=" + $withArr.Count)
Write-Output ("with_dirs=" + (($withArr | Sort-Object) -join ', '))
foreach ($f in $withoutArr) {
  Write-Output ("EXCEPT dir=" + $f.Directory.Name)
  $tl = @(@((Read-Raw $f.FullName) -split "`r?`n") | Where-Object { $_.Trim().Length -gt 0 })
  Write-Output ("nonempty_lines=" + $tl.Count)
  $shown = 0
  foreach ($l in $tl) { if ($shown -lt 10) { Write-Output ("  | " + $l); $shown = $shown + 1 } }
}
Write-Output '=== DONE ==='
