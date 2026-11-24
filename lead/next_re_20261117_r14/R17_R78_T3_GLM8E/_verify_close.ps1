# R43-T3 收尾核查（只读；临时探针文件只写本卡输出目录）
$root = 'D:\Project\ra2-campaign-forge'
$base = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
$out  = Join-Path $base 'R17_R78_T3_GLM8E'
$NL = "`n"
function Read-Raw([string]$p) { Get-Content -LiteralPath $p -Raw }

Write-Output '=== A. 台账标题编号干净重排（只取 § 后连续数字） ==='
$led = Join-Path $root 'lead\GOAL_THREE_TARGETS_20261018.md'
$heads = @(Select-String -LiteralPath $led -Pattern '^## §[0-9]+')
$pairs = @()
foreach ($h in $heads) {
  $tail = $h.Line.Substring(4)
  $d = ''
  for ($i = 0; $i -lt $tail.Length; $i++) {
    $c = $tail[$i]
    if ($c -ge '0' -and $c -le '9') { $d = $d + $c } else { break }
  }
  if ($d.Length -gt 0) { $pairs += ,@($d.PadLeft(7, '0'), $h.LineNumber) }
}
$byNum = @($pairs | Sort-Object -Property @{Expression = { $_[0] }; Descending = $true })
Write-Output ("heading_total=" + $heads.Count + " numeric_total=" + $pairs.Count)
for ($i = 0; $i -lt 5 -and $i -lt $byNum.Count; $i++) {
  Write-Output ("  top" + ($i + 1) + ": num=" + $byNum[$i][0] + " line=" + $byNum[$i][1])
}

Write-Output '=== B. 现盘 §1084 块字节数（自 ## §1084 行起至 EOF） ==='
$t5 = Read-Raw $led
$idx = $t5.IndexOf('## §1084' + $NL)
Write-Output ("idx_found=" + ($idx -ge 0))
if ($idx -ge 0) {
  $block = $t5.Substring($idx)
  $probe = Join-Path $out '_probe_1084_block.txt'
  Set-Content -LiteralPath $probe -Value $block -NoNewline -Encoding utf8
  $bl = (Get-Item -LiteralPath $probe).Length
  Write-Output ("block_bytes=" + $bl + " (ledger_now_minus_first_read=4506996-4502219=4777)")
}

Write-Output '=== C. 台账备份探测 ==='
$b1 = @(Get-ChildItem -LiteralPath (Join-Path $root 'lead') -File -Filter '*before*' -ErrorAction SilentlyContinue | Sort-Object LastWriteTime)
foreach ($f in $b1) {
  Write-Output ("  " + $f.Name + " bytes=" + $f.Length + " mtime=" + $f.LastWriteTime.ToString('yyyy-MM-dd HH:mm:ss'))
}
$cand = @($b1 | Where-Object { $_.Name -like 'LEDGER.before*' -and $_.LastWriteTime -lt (Get-Date '2026-11-22 13:24:47') } | Sort-Object LastWriteTime | Select-Object -Last 1)
if ($cand.Count -gt 0) {
  $bk = $cand[0]
  Write-Output ("  --> 选用备份: " + $bk.Name + " bytes=" + $bk.Length)
  $bh2 = @(Select-String -LiteralPath $bk.FullName -Pattern '^## §[0-9]+')
  $p2 = @()
  foreach ($h in $bh2) {
    $tail = $h.Line.Substring(4)
    $d = ''
    for ($i = 0; $i -lt $tail.Length; $i++) {
      $c = $tail[$i]
      if ($c -ge '0' -and $c -le '9') { $d = $d + $c } else { break }
    }
    if ($d.Length -gt 0) { $p2 += ,@($d.PadLeft(7, '0'), $h.LineNumber) }
  }
  $bn = @($p2 | Sort-Object -Property @{Expression = { $_[0] }; Descending = $true })
  Write-Output ("  backup_heading_total=" + $bh2.Count + " backup_max_num=" + $bn[0][0] + " at_line=" + $bn[0][1])
  $has82 = @($p2 | Where-Object { $_[0] -eq '0001082' }).Count
  $has83 = @($p2 | Where-Object { $_[0] -eq '0001083' }).Count
  $has84 = @($p2 | Where-Object { $_[0] -eq '0001084' }).Count
  Write-Output ("  backup_has_1082=" + ($has82 -gt 0) + " has_1083=" + ($has83 -gt 0) + " has_1084=" + ($has84 -gt 0))
} else {
  Write-Output '  --> 13:24:47 之前的 LEDGER.before* 备份：未取得'
}

Write-Output '=== D. SUPERSEDED 现指向 v5.19 实证 ==='
$sup = @(Get-ChildItem -LiteralPath $base -Recurse -Filter 'SUPERSEDED.md' -File -ErrorAction SilentlyContinue)
$c19 = 0
foreach ($f in $sup) {
  $t = Read-Raw $f.FullName
  if ($t.Contains('R17_R79_FACTINDEX_V519')) { $c19 = $c19 + 1 }
}
Write-Output ("total=" + $sup.Count + " containing_R17_R79_FACTINDEX_V519=" + $c19)
$v518sup = Join-Path $base 'R17_R77_FACTINDEX_V518\SUPERSEDED.md'
if (Test-Path -LiteralPath $v518sup) {
  Write-Output '  -- R17_R77_FACTINDEX_V518\SUPERSEDED.md 前 6 非空行 --'
  $tl = @(@((Read-Raw $v518sup) -split "`r?`n") | Where-Object { $_.Trim().Length -gt 0 } | Select-Object -First 6)
  foreach ($l in $tl) {
    $cut = 140
    if ($l.Length -lt $cut) { $cut = $l.Length }
    Write-Output ("  | " + $l.Substring(0, $cut))
  }
} else {
  Write-Output '  R17_R77_FACTINDEX_V518\SUPERSEDED.md 不存在'
}

Write-Output '=== E. LEAD_LOCK BJ 标题行 ==='
$bj = @(Select-String -LiteralPath (Join-Path $root 'lead\LEAD_LOCK') -Pattern '^## BJ' | Select-Object -First 1)
if ($bj.Count -gt 0) {
  $l = $bj[0].Line
  $cut = 120
  if ($l.Length -lt $cut) { $cut = $l.Length }
  Write-Output ("  L" + $bj[0].LineNumber + ": " + $l.Substring(0, $cut))
}
