# R43-T3 追查2：台账 '## §' 标题锚点全景 + 文件尾部（只读）
$led = 'D:\Project\ra2-campaign-forge\lead\GOAL_THREE_TARGETS_20261018.md'

$heads = @(Select-String -LiteralPath $led -Pattern '^## §[0-9]+' )
Write-Output ("heading_count=" + $heads.Count)
$nums = @($heads | ForEach-Object { $_.Line.Substring(4).PadLeft(7, '0') })
$sortedPairs = @()
for ($i = 0; $i -lt $heads.Count; $i++) { $sortedPairs += ,@($nums[$i], $heads[$i].LineNumber, $heads[$i].Line) }
$byNum = @($sortedPairs | Sort-Object -Property @{Expression = { $_[0] }; Descending = $true })
Write-Output "-- top8 heading numbers (padded | line# | text) --"
for ($i = 0; $i -lt 8 -and $i -lt $byNum.Count; $i++) {
  $e = $byNum[$i]
  $t = $e[2]
  $cut = 80
  if ($t.Length -lt $cut) { $cut = $t.Length }
  Write-Output ("  " + $e[0] + " | line" + $e[1] + " | " + $t.Substring(0, $cut))
}
Write-Output "-- last10 headings in FILE ORDER (line# | text) --"
$tail = @($heads | Select-Object -Last 10)
foreach ($h in $tail) {
  $t = $h.Line
  $cut = 80
  if ($t.Length -lt $cut) { $cut = $t.Length }
  Write-Output ("  line" + $h.LineNumber + " | " + $t.Substring(0, $cut))
}
Write-Output "-- total lines & tail of file --"
$allLines = @(Get-Content -LiteralPath $led)
Write-Output ("total_lines_split=" + $allLines.Count)
$startIdx = 41688 - 1
if ($startIdx -lt 0) { $startIdx = 0 }
$endIdx = $allLines.Count - 1
Write-Output ("-- lines 41689..EOF shown (from §1083 heading area) --")
for ($i = $startIdx; $i -le $endIdx; $i++) {
  $l = $allLines[$i]
  $cut = 150
  if ($l.Length -lt $cut) { $cut = $l.Length }
  Write-Output ("  L" + ($i + 1) + ": " + $l.Substring(0, $cut))
}
