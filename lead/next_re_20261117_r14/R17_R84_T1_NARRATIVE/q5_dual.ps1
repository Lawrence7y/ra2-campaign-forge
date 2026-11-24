# Q5 · PowerShell 实现（法 2）

<#
  q5_dual.ps1 — R45-T1 Q5 正控（法 2：PowerShell）
  与法 1（q1_narrative.py / q2q3_types.py）**逐行独立重写**，不 import / 不调用任何 Python；
  只读同一批清单与前 8 KiB，输出 q5_ps.json。

  复算三件事：
    A. Q1 件数/字节 —— 判据与 Python 版逐字同：why==P0 ∧ 非空行(先截200行再丢空) 中含 CJK 行占比 >= 25%
       ∧ 行首VA占比 < 60%（且 VA 行数 < 3 时直接算未命中）∧ 不是表格事实表
    B. Q3 件数/字节 —— T1 名字闭集 + T2a(滚回标记且去标记名在 A 表) + T2b(内容簇非最大份)
       + T3(正文行首VA>=60% / 每行VA或TAB>=95% / 标题+地址流水)
    C. 交叉对账：与本目录 q1_py.json / q2q3_types.json 的集合**逐件**比对（不是只比总数）
#>

$ErrorActionPreference = 'Stop'
$LEAD = 'D:\Project\ra2-campaign-forge\lead'
$OUT  = $PSScriptRoot
$CP   = Join-Path $LEAD 'next_re_20261117_r14\R17_R78_T1_RECLASS\files_tier_Cprime.tsv'
$A    = Join-Path $LEAD 'next_re_20261117_r14\R17_R72_T1_CLEANSCALE\files_tier_A_snap2.tsv'

# ---------- 行首 VA 判定（与 Python 的两条正则等价，用 .NET 正则重写）
$rxVa1 = [regex]'^\s*(0x)?[0-9A-Fa-f]{6,8}\s*[:\t ]'
$rxVa2 = [regex]'^\s*0x[0-9A-Fa-f]{6,8}\s{2,}'
$rxCn  = [regex]'[\u4e00-\u9fff]'
$rxVaBody = [regex]'(?m)^\s*(0x)?[0-9A-Fa-f]{6,8}\s{2,}\S'
$rx0x  = [regex]'0x[0-9A-Fa-f]{4,8}'
$rxHdr = [regex]'^\s#{1,3}\s'
$rxRoll = New-Object System.Text.RegularExpressions.Regex('(\.before[._][^/]*|\.before$|_before_[^/]*|_bak(\.[^/]*)?$|\.bak$)', [System.Text.RegularExpressions.RegexOptions]::IgnoreCase)
$rxSbx = [regex]'(^|/)(_akv_own|_akv_pre|_akv_sbx)(/|$)'
$rxNums = [regex]'[0-9]+'

$T1 = @('disagree.md','unknowns.md','superseded.md','progress.md','pending_decisions.md','verdict.md','pending_and_signoffs.md')

function Base([string]$rel) { $i = $rel.LastIndexOf('/'); if ($i -lt 0) { return $rel } else { return $rel.Substring($i+1) } }

function ReadHead([string]$rel, [int]$n = 8192) {
  $p = Join-Path $LEAD ($rel -replace '/', '\')
  try {
    $fs = [System.IO.File]::Open($p, 'Open', 'Read', 'ReadWrite')
    try {
      $buf = New-Object byte[] $n
      $read = $fs.Read($buf, 0, $n)
      if ($read -le 0) { return ,([byte[]]@()) }
      if ($read -lt $n) { $buf = $buf[0..($read-1)] }
      return ,$buf
    } finally { $fs.Dispose() }
  } catch { return $null }
}

function Dec([byte[]]$b) { return [System.Text.Encoding]::UTF8.GetString($b) }

function GetLines([string]$text) {
  # 照抄 Python：先 b"\n" 切、截 200 行、再丢 strip() 为空的行
  $all = $text.Split("`n")
  $take = if ($all.Length -gt 200) { $all[0..199] } else { $all }
  return @($take | Where-Object { $_.Trim().Length -gt 0 })
}

function Feat([string]$text) {
  $ls = GetLines $text
  $n = $ls.Count
  if ($n -eq 0) { $n = 1 }
  $va = 0; $tab = 0; $narr = 0
  foreach ($x in $ls) {
    if ($rxVa1.IsMatch($x) -or $rxVa2.IsMatch($x)) { $va++; continue }
    if (([regex]::Matches($x, "`t")).Count -ge 2) { $tab++; continue }
    if ($rxCn.IsMatch($x) -and $x.Trim().Length -ge 8) { $narr++ }
  }
  $first = if ($ls.Count -gt 0) { $ls[0] } else { '' }
  return [pscustomobject]@{
    n = $ls.Count; va = $va; tab = $tab; narr = $narr
    vaRatio = $va / $n; tabFrac = $tab / $n; narrFrac = $narr / $n
    n0x = $rx0x.Matches($text).Count
    first = if ($first.Length -gt 160) { $first.Substring(0,160) } else { $first }
    hdr = $rxHdr.IsMatch($first)
    # 近逐字节相等：把行拼回去再取"\n"切（Python 用 split('\n')）
    text2 = $text
  }
}

function Fingerprint([string]$text) {
  $ls = @(GetLines $text | Where-Object { -not ($rxVa1.IsMatch($_) -or $rxVa2.IsMatch($_)) } |
          Where-Object { ([regex]::Matches($_, "`t")).Count -lt 2 } |
          Where-Object { $rxCn.IsMatch($_) -and $_.Trim().Length -ge 8 })
  $take = if ($ls.Count -gt 40) { $ls[0..39] } else { $ls }
  $body = ($take | ForEach-Object { $rxNums.Replace($_, '#') }) -join ''
  return [pscustomobject]@{ fp = $body; fpN = $take.Count }
}

function StripRoll([string]$b) {
  $m = $rxRoll.Match($b)
  if (-not $m.Success) { return $null }
  $stem = $b.Substring(0, $m.Index)
  $tail = $b.Substring($m.Index + $m.Length)
  $ext = ''
  if ($tail.Contains('.')) { $ext = $tail.Substring($tail.IndexOf('.')) }
  if (-not $ext) { $m2 = [regex]::Match($b, '(\.[A-Za-z0-9]{1,5})$'); if ($m2.Success) { $ext = $m2.Groups[1].Value } }
  return "$stem$ext"
}

# ---------- 读清单
$peer = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($line in [System.IO.File]::ReadAllLines($A, [System.Text.Encoding]::UTF8) | Select-Object -Skip 1) {
  if ([string]::IsNullOrWhiteSpace($line)) { continue }
  [void]$peer.Add((Base ($line.Split("`t")[0])).ToLower())
}

$cpRows = @()
foreach ($line in [System.IO.File]::ReadAllLines($CP, [System.Text.Encoding]::UTF8) | Select-Object -Skip 1) {
  if ([string]::IsNullOrWhiteSpace($line)) { continue }
  $f = $line.Split("`t")
  $cpRows += [pscustomobject]@{ rel = $f[0]; ext = $f[1]; bytes = [int64]$f[2]; why = $f[5] }
}
$p0 = @($cpRows | Where-Object { $_.why -eq 'P0_未被排除判据命中' })

# ---------- A · Q1
$q1 = New-Object System.Collections.ArrayList
$q1Bytes = 0
foreach ($r in $p0) {
  $buf = ReadHead $r.rel
  if ($null -eq $buf) { continue }
  $t = Dec $buf
  $f = Feat $t
  if ($f.n -eq 0) { continue }
  if (-not ($f.va -ge 3 -and $f.vaRatio -ge 0.6)) {
    $isTab = $false
    if (($r.rel.ToLower().EndsWith('.tsv') -or $r.rel.ToLower().EndsWith('.csv')) -and $f.n -ge 5 -and $f.tabFrac -ge 0.7) { $isTab = $true }
    if (-not $isTab) {
      $cn = 0
      foreach ($x in (GetLines $t)) { if ($rxCn.IsMatch($x)) { $cn++ } }
      if (($cn / $f.n) -ge 0.25) { [void]$q1.Add($r); $q1Bytes += $r.bytes }
    }
  }
}

# ---------- B · Q3 分型
$cand = @($q1)
$info = @{}
$fpg = @{}
foreach ($r in $cand) {
  $buf = ReadHead $r.rel
  if ($null -eq $buf) { continue }
  $t = Dec $buf
  $f = Feat $t
  $fp = Fingerprint $t
  $info[$r.rel] = @{ f = $f; fp = $fp; t = $t }
  if ($fp.fpN -ge 10) {
    if (-not $fpg.ContainsKey($fp.fp)) { $fpg[$fp.fp] = New-Object 'System.Collections.Generic.List[object]' }
    $fpg[$fp.fp].Add($r)
  }
}
$fpMax = @{}
foreach ($k in $fpg.Keys) {
  if ($fpg[$k].Count -ge 3) {
    $mx = 0; foreach ($y in $fpg[$k]) { if ($y.bytes -gt $mx) { $mx = $y.bytes } }
    $fpMax[$k] = $mx
  }
}

$excl = New-Object System.Collections.ArrayList
$keep = 0; $undec = 0
foreach ($r in $cand) {
  $b = Base $r.rel; $low = $b.ToLower()
  $f = $info[$r.rel].f
  $fp = $info[$r.rel].fp
  # T3
  $t0 = @()
  if ($f.vaRatio -ge 0.60) { $t0 += 'T0a' }
  if (($f.va + $f.tab) / [math]::Max($f.n,1) -ge 0.95) { $t0 += 'T0b' }
  if ($f.vaRatio -ge 0.30 -and $f.hdr -and $f.n0x -ge 3) { $t0 += 'T0c' }
  if ($t0.Count -gt 0) { [void]$excl.Add([pscustomobject]@{rel=$r.rel;bytes=$r.bytes;type='T3'}); continue }
  # T1
  $isT1 = ($T1 -contains $low) -or ($low -match '^(pending[^/]*\.(md|txt)|[^/]*_signoffs\.md)$')
  if ($isT1) { [void]$excl.Add([pscustomobject]@{rel=$r.rel;bytes=$r.bytes;type='T1'}); continue }
  # T2
  $cur = StripRoll $b
  $peerHit = ($null -ne $cur) -and $peer.Contains($cur.ToLower())
  $dup = $false
  if ($fp.fpN -ge 10 -and $fpMax.ContainsKey($fp.fp)) {
    $mx = $fpMax[$fp.fp]
    $same = @($fpg[$fp.fp] | Where-Object { $_.bytes -eq $mx } | Sort-Object rel)
    if ($r.bytes -lt $mx) { $dup = $true }
    elseif ($same.Count -gt 0 -and $same[0].rel -ne $r.rel) { $dup = $true }
  }
  $effDup = $dup -and (-not $rxSbx.IsMatch($r.rel))
  if ($peerHit -or $effDup) { [void]$excl.Add([pscustomobject]@{rel=$r.rel;bytes=$r.bytes;type='T2'}); continue }
  # U1 / K1
  if ($null -ne $cur -and -not $dup) { $undec++; continue }
  $keep++
}

$exN = $excl.Count
$exB = 0; foreach ($x in $excl) { $exB += $x.bytes }
$byT = @{}
foreach ($x in $excl) { if (-not $byT.ContainsKey($x.type)) { $byT[$x.type] = @{n=0;b=0} }; $byT[$x.type].n++; $byT[$x.type].b += $x.bytes }

$res = [ordered]@{
  法 = '法2 PowerShell (q5_dual.ps1)'
  Q1_n = $q1.Count; Q1_b = $q1Bytes
  P0_n = $p0.Count
  Q3_n = $exN; Q3_b = $exB
  Q3_by_type = $byT
  K1_n = $keep; U1_n = $undec
}
$res | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath (Join-Path $OUT 'q5_ps.json') -Encoding utf8
$res | ConvertTo-Json -Depth 6

# ---------- C · 逐件集合对账（对法 1 的结果）
$pySets = Get-Content -LiteralPath (Join-Path $OUT 'q1_narrative.tsv.ref') -Encoding utf8 -ErrorAction SilentlyContinue
$pyCand = @([System.IO.File]::ReadAllLines((Join-Path $OUT 'narrative_candidates.tsv'), [System.Text.Encoding]::UTF8) | Select-Object -Skip 1 | ForEach-Object { ($_ -split "`t")[0] })
$pyEx   = @([System.IO.File]::ReadAllLines((Join-Path $OUT 'should_exclude.tsv'), [System.Text.Encoding]::UTF8) | Select-Object -Skip 1 | ForEach-Object { ($_ -split "`t")[0] })
$psCand = @($q1 | ForEach-Object { $_.rel })
$psEx   = @($excl | ForEach-Object { $_.rel })

$d1 = Compare-Object -ReferenceObject $pyCand -DifferenceObject $psCand
$d3 = Compare-Object -ReferenceObject $pyEx -DifferenceObject $psEx
[ordered]@{
  cand_py = $pyCand.Count; cand_ps = $psCand.Count; cand_diff = @($d1).Count
  excl_py = $pyEx.Count; excl_ps = $psEx.Count; excl_diff = @($d3).Count
  cand_diff_sample = @($d1 | Select-Object -First 10 | ForEach-Object { "$($_.SideIndicator) $($_.InputObject)" })
  excl_diff_sample = @($d3 | Select-Object -First 10 | ForEach-Object { "$($_.SideIndicator) $($_.InputObject)" })
} | ConvertTo-Json -Depth 4


