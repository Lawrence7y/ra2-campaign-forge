# R43-T3 追查：台账 §24026 token 的上下文与 token 分布（只读）
$led = 'D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md'

$toks = @(Select-String -LiteralPath $led -Pattern '§[0-9]+' -AllMatches | ForEach-Object { $_.Matches } | ForEach-Object { $_.Value })
$cnt = @{}
foreach ($t in $toks) {
  if (-not $cnt.ContainsKey($t)) { $cnt[$t] = 0 }
  $cnt[$t] = $cnt[$t] + 1
}
Write-Output ("total_tokens=" + $toks.Count + " distinct=" + $cnt.Count)
$distinct = @($cnt.Keys | ForEach-Object { $_.PadLeft(7, '0') } | Sort-Object -Descending)
Write-Output "-- raw distinct top12 (padded, unpadded=去前导0) --"
foreach ($d in @($distinct | Select-Object -First 12)) { Write-Output ("  " + $d) }
Write-Output "-- counts for suspicious big tokens --"
foreach ($k in @('§24026', '§2402', '§10000', '§9999')) {
  if ($cnt.ContainsKey($k)) { Write-Output ("  " + $k + " count=" + $cnt[$k]) } else { Write-Output ("  " + $k + " count=0") }
}
Write-Output "-- lines containing §24026 (first 6, 170 chars around) --"
$hits = @(Select-String -LiteralPath $led -Pattern '§24026' | Select-Object -First 6)
foreach ($h in $hits) {
  $l = $h.Line
  $pos = $l.IndexOf('§24026')
  $s = $pos - 60
  if ($s -lt 0) { $s = 0 }
  $len = 170
  if ($l.Length - $s -lt $len) { $len = $l.Length - $s }
  Write-Output ("  line" + $h.LineNumber + " …" + $l.Substring($s, $len).Replace("`t", "␉") + "…")
}
Write-Output "-- max among <=4-digit tokens --"
$small = @($cnt.Keys | Where-Object { $_.Length -le 5 } | ForEach-Object { $_.PadLeft(7, '0') } | Sort-Object -Descending)
Write-Output ("  top5<=4digit: " + ((@($small | Select-Object -First 5)) -join ','))
Write-Output "-- §1081/§1082/§1083 heading lines --"
$h2 = @(Select-String -LiteralPath $led -Pattern '^## §10[89][0-9]' | Select-Object -First 6)
foreach ($h in $h2) {
  $l = $h.Line
  $cut = 120
  if ($l.Length -lt $cut) { $cut = $l.Length }
  Write-Output ("  line" + $h.LineNumber + ": " + $l.Substring(0, $cut))
}
