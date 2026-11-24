# R43-T3 追查3：记录原文定位 + v5.19 落盘路径检查（只读）
$root = 'D:\Project\ra2-campaign-forge'
$base = Join-Path $root 'lead\next_re_20261117_r14'

Write-Output '=== A. LEAD_LOCK 中含 4,502,219 / max §1083 / §1084 的行 ==='
$llLines = @(Select-String -LiteralPath (Join-Path $root 'lead\LEAD_LOCK') -Pattern '4,502,219|max §1083|§1084')
foreach ($h in $llLines) {
  $t = $h.Line
  $cut = 220
  if ($t.Length -lt $cut) { $cut = $t.Length }
  Write-Output ("  L" + $h.LineNumber + ": " + $t.Substring(0, $cut))
}
Write-Output '=== B. STATUS_BOARD 中含 4,502,219 / max §1083 的行 ==='
$sbLines = @(Select-String -LiteralPath (Join-Path $base 'STATUS_BOARD.md') -Pattern '4,502,219|max §1083|4,491,831')
foreach ($h in $sbLines) {
  $t = $h.Line
  $cut = 220
  if ($t.Length -lt $cut) { $cut = $t.Length }
  Write-Output ("  L" + $h.LineNumber + ": " + $t.Substring(0, $cut))
}
Write-Output '=== C. 台账 §1082/§1083 附近是否自述台账自身字节数 ==='
$ledLines = @(Select-String -LiteralPath (Join-Path $root 'lead\GOAL_THREE_TARGETS_20261018.md') -Pattern '4,502,219|4,491,831')
foreach ($h in $ledLines) {
  $t = $h.Line
  $cut = 220
  if ($t.Length -lt $cut) { $cut = $t.Length }
  Write-Output ("  L" + $h.LineNumber + ": " + $t.Substring(0, $cut))
}
Write-Output '=== D. v5.19 / T4 产物路径是否存在（仅路径检查） ==='
$p1 = Join-Path $base 'R17_R79_FACTINDEX_V519\FACT_INDEX.tsv'
$p2 = Join-Path $base 'R17_R78_T4_AUDIT30\REPORT.md'
$p3 = Join-Path $base 'R17_R79_FACTINDEX_V519'
Write-Output ("  R17_R79_FACTINDEX_V519 dir exists=" + (Test-Path -LiteralPath $p3))
Write-Output ("  R17_R79_FACTINDEX_V519\FACT_INDEX.tsv exists=" + (Test-Path -LiteralPath $p1))
Write-Output ("  R17_R78_T4_AUDIT30\REPORT.md exists=" + (Test-Path -LiteralPath $p2))
