# R51-T1-TIE152 / Q5 正控 · 法2（PowerShell）
# 与 q5_py.py 互不复用代码：Import-Csv 取表、[System.IO.FileInfo] 取字节、Where-Object 做集合差。
$ErrorActionPreference = 'Stop'
$LEAD = 'D:\Project\ra2-campaign-forge\lead'
$R    = Join-Path $LEAD 'next_re_20261117_r14'
$OUT  = Join-Path $R 'R17_R91_T1_TIE152'

function Sz([string]$rel) {
    (New-Object System.IO.FileInfo((Join-Path $LEAD ($rel -replace '/', '\')))).Length
}

# ---- 基线 1242 ----
$ep = Import-Csv (Join-Path $R 'R17_R78_T1_RECLASS\files_excluded_prime.tsv') -Delimiter "`t"
$base = @($ep | Where-Object { $_.label -eq 'UNDECIDED' -and $_.rel.ToLower().Contains('evidence') })
$baseN = $base.Count
$baseB = ($base | ForEach-Object { Sz $_.rel } | Measure-Object -Sum).Sum

# ---- R44 已裁 976 ----
$vd = Import-Csv (Join-Path $R 'R17_R81_T2_EVID\_verdicts.tsv') -Delimiter "`t"
$obj = @($vd | Where-Object { $_.verdict -eq '对象抄本' })
$prc = @($vd | Where-Object { $_.verdict -eq '过程输出' })
$tie = @($vd | Where-Object { $_.verdict -eq '无法判定' })
$objB = ($obj | ForEach-Object { Sz $_.rel } | Measure-Object -Sum).Sum
$prcB = ($prc | ForEach-Object { Sz $_.rel } | Measure-Object -Sum).Sum

# ---- 目录多数派（分母=已裁件，>=3 且同向>=75%）----
$dirO = @{}; $dirP = @{}
foreach ($r in $obj) { $d = Split-Path $r.rel -Parent; if (-not $dirO.ContainsKey($d)) { $dirO[$d] = 0; $dirP[$d] = 0 }; $dirO[$d]++ }
foreach ($r in $prc) { $d = Split-Path $r.rel -Parent; if (-not $dirO.ContainsKey($d)) { $dirO[$d] = 0; $dirP[$d] = 0 }; $dirP[$d]++ }

$r46 = @(); $left = @()
foreach ($r in $tie) {
    $d = Split-Path $r.rel -Parent
    $o = 0; $p = 0
    if ($dirO.ContainsKey($d)) { $o = $dirO[$d]; $p = $dirP[$d] }
    $n = $o + $p
    $take = ($n -ge 3) -and ($o -ne $p) -and (([Math]::Max($o, $p) / $n) -ge 0.75)
    if ($take) { $r46 += $r } else { $left += $r }
}
$r46B  = ($r46  | ForEach-Object { Sz $_.rel } | Measure-Object -Sum).Sum
$leftB = ($left | ForEach-Object { Sz $_.rel } | Measure-Object -Sum).Sum

$disk = Import-Csv (Join-Path $OUT 'tie152.tsv') -Delimiter "`t"
$diskB = ($disk | ForEach-Object { [int]$_.bytes } | Measure-Object -Sum).Sum
$same = (@(Compare-Object ($disk | ForEach-Object { $_.rel }) ($left | ForEach-Object { $_.rel }))).Count -eq 0

"法2 PowerShell 结果"
"  base1242      = {0} 件 / {1} B" -f $baseN, $baseB
"  R44 已裁      = {0} 件 / {1} B  (对象 {2}/{3} + 过程 {4}/{5})" -f ($obj.Count + $prc.Count), ($objB + $prcB), $obj.Count, $objB, $prc.Count, $prcB
"  1242-976      = {0} 件 / {1} B" -f ($baseN - $obj.Count - $prc.Count), ($baseB - $objB - $prcB)
"  R46 再裁      = {0} 件 / {1} B" -f $r46.Count, $r46B
"  1242-976-114  = {0} 件 / {1} B" -f ($baseN - $obj.Count - $prc.Count - $r46.Count), ($baseB - $objB - $prcB - $r46B)
"  落盘 tie152   = {0} 件 / {1} B ; 集合相同={2}" -f $disk.Count, $diskB, $same
"  字节算式闭合  = {0}" -f (($baseB - $objB - $prcB - $r46B) -eq $leftB -and $leftB -eq $diskB)

"法2: 152 件 / {0} B ; 1242-976-114 件 {1} ; 字节 {2}-{3}-{4}={5}" -f $leftB, $left.Count, $baseB, ($objB + $prcB), $r46B, ($baseB - $objB - $prcB - $r46B) |
    Out-File -FilePath (Join-Path $OUT 'q5_posctrl_ps.txt') -Encoding utf8
