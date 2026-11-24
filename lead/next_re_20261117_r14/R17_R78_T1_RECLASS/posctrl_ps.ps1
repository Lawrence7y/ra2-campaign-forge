# posctrl_ps.ps1 — R43-T1 Q5 正控 · 法 1（PowerShell，独立实现）
# 目标量：A − C′ 的文件数（并同时复算 C′ 的 文件数/字节）。
# 刻意不复用 Python 裁决器的任何逻辑：这里只用 Get-Content 读清单、
# 用 hash set 求差集，字节用 [long] 累加。
$ErrorActionPreference = 'Stop'
$base = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
$A = Join-Path $base 'R17_R72_T1_CLEANSCALE\files_tier_A_snap2.tsv'
$Cp = Join-Path $base 'R17_R78_T1_RECLASS\files_tier_Cprime.tsv'

$relA = [System.Collections.Generic.HashSet[string]]::new()
$bytesA = [long]0
$nA = 0
foreach ($line in [System.IO.File]::ReadLines($A)) {
    if ($line.StartsWith('rel' + [char]9)) { continue }
    $f = $line.Split([char]9)
    if ($f.Length -lt 3) { continue }
    [void]$relA.Add($f[0])
    $bytesA += [long]$f[2]
    $nA++
}

$relC = [System.Collections.Generic.HashSet[string]]::new()
$bytesC = [long]0
$nC = 0
foreach ($line in [System.IO.File]::ReadLines($Cp)) {
    if ($line.StartsWith('rel' + [char]9)) { continue }
    $f = $line.Split([char]9)
    if ($f.Length -lt 3) { continue }
    [void]$relC.Add($f[0])
    $bytesC += [long]$f[2]
    $nC++
}

$diffN = 0
$diffB = [long]0
foreach ($line in [System.IO.File]::ReadLines($A)) {
    if ($line.StartsWith('rel' + [char]9)) { continue }
    $f = $line.Split([char]9)
    if ($f.Length -lt 3) { continue }
    if (-not $relC.Contains($f[0])) { $diffN++; $diffB += [long]$f[2] }
}

Write-Output ("PS  nA={0} sumA={1}  nCp={2} sumCp={3}  AminusCp_n={4} AminusCp_b={5}" -f $nA, $bytesA, $nC, $bytesC, $diffN, $diffB)
