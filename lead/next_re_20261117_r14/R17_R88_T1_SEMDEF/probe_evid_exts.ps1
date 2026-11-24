# probe_evid_exts.ps1 — 只读探查：EVIDENCE/ 下文件的扩展名分布（法2 语料）
$ErrorActionPreference = 'Stop'
$lead = 'D:\Project\ra2-campaign-forge\lead'
$ln = $lead.Length
$allow = @('.map', '.ini', '.shp', '.vxl', '.hva', '.tmp', '.yro')

$evdirs = Get-ChildItem -Directory -Recurse -Force $lead -ErrorAction SilentlyContinue |
    Where-Object { $_.Name -ieq 'EVIDENCE' }
"EVIDENCE_DIRS=$($evdirs.Count)"

$rows = New-Object System.Collections.Generic.List[object]
foreach ($d in $evdirs) {
    foreach ($f in (Get-ChildItem -File -Force $d.FullName -ErrorAction SilentlyContinue)) {
        $rel = $f.FullName.Substring($ln + 1).Replace('\', '/')
        $rows.Add([pscustomobject]@{ rel = $rel; b = [long]$f.Length })
    }
}
"FILES_IN_EVIDENCE=$($rows.Count)"
$sumB = 0L
foreach ($r in $rows) { $sumB += $r.b }
"BYTES_IN_EVIDENCE=$sumB"

$g = @{}
foreach ($r in $rows) {
    $e = '(none)'
    if ($r.rel -match '(\.[^./]+)$') { $e = $Matches[1].ToLower() }
    if (-not $g.ContainsKey($e)) { $g[$e] = 0 }
    $g[$e]++
}
"--- ext counts (top 18) ---"
$g.GetEnumerator() | Sort-Object -Property Value -Descending | Select-Object -First 18 |
    ForEach-Object { "{0}`t{1}" -f $_.Key, $_.Value }
"--- outside 6-ext, excluding allowlist ---"
$six = @('.md', '.txt', '.json', '.tsv', '.log', '.csv')
$odd = @($rows | Where-Object {
        $r = $_
        $e = ''
        if ($r.rel -match '(\.[^./]+)$') { $e = $Matches[1].ToLower() }
        ($six -notcontains $e) -and ($allow -notcontains $e)
    })
"ODD_COUNT=$($odd.Count)"
$s2 = 0L
foreach ($r in $odd) { $s2 += $r.b }
"ODD_BYTES=$s2"
$odd | Select-Object -First 20 | ForEach-Object { "ODD`t$($_.b)`t$($_.rel)" }
