# Q5 正控 法2 (PowerShell)：独立实现，计算 Q1 的 266 与 Q4 的 _audit 件数/字节
# 与 posctrl_py.py 不共享代码：逐行 Split 解析，不用 Import-Csv
$R = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
$EP = Join-Path $R 'R17_R78_T1_RECLASS\files_excluded_prime.tsv'
$VD = Join-Path $R 'R17_R81_T2_EVID\_verdicts.tsv'
$CP = Join-Path $R 'R17_R78_T1_RECLASS\files_tier_Cprime.tsv'

# ---- Q1 ----
function Get-Cols([string]$path) {
  $lines = [System.IO.File]::ReadAllLines($path, [System.Text.Encoding]::UTF8)
  $hdr = $lines[0] -split "`t"
  $out = @()
  for ($i=1; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -eq '') { continue }
    $f = $lines[$i] -split "`t"
    $o = @{}
    for ($j=0; $j -lt $hdr.Count; $j++) { $o[$hdr[$j]] = $f[$j] }
    $out += ,$o
  }
  return $out
}
$ep = Get-Cols $EP
$n1242 = 0
foreach ($r in $ep) {
  if ($r['label'] -eq 'UNDECIDED' -and $r['rel'].ToLowerInvariant().Contains('evidence')) { $n1242++ }
}
$vd = Get-Cols $VD
$n976 = 0; $nTieDirect = 0; $nTieReason = 0
foreach ($r in $vd) {
  if ($r['verdict'] -eq '对象抄本' -or $r['verdict'] -eq '过程输出') { $n976++ }
  if ($r['verdict'] -eq '无法判定') { $nTieDirect++ }
  if ($r['why'] -eq 'tie' -or $r['reason'] -eq 'tie') { $nTieReason++ }
}
$diff = $n1242 - $n976
Write-Output ("Q1: n1242={0} n976={1} diff={2} direct={3} reason_tie={4}" -f $n1242,$n976,$diff,$nTieDirect,$nTieReason)

# ---- Q4 ----
$cp = Get-Cols $CP
$ac = 0; $ab = [int64]0; $pc = 0; $pb = [int64]0
foreach ($r in $cp) {
  $parts = $r['rel'].Replace('\','/') -split '/'
  $isAudit = $false
  foreach ($p in $parts) { if ($p -ceq '_audit') { $isAudit = $true; break } }
  if ($isAudit) {
    $b = [int64]$r['bytes']
    $ac++; $ab += $b
    if ($r['why'].StartsWith('P1a')) { $pc++; $pb += $b }
  }
}
$pctC = if ($ac -gt 0) { [math]::Round(100*$pc/$ac,2) } else { 0 }
$pctB = if ($ab -gt 0) { [math]::Round(100*$pb/$ab,2) } else { 0 }
Write-Output ("Q4: _audit count={0} bytes={1} P1a={2} P1abytes={3} pct_count={4} pct_bytes={5}" -f $ac,$ab,$pc,$pb,$pctC,$pctB)
