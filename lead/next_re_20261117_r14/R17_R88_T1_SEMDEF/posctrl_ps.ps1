# posctrl_ps.ps1 — R46-T1 Q5 正控 · 法 1（PowerShell 7，自带解析器与分类谓词，零代码共享）
$ErrorActionPreference = 'Stop'
$R = 'D:\Project\ra2-campaign-forge\lead'
$R14 = Join-Path $R 'next_re_20261117_r14'
$TAB = [char]9

function Read-Tab([string]$path) {
    $lines = [System.IO.File]::ReadAllLines($path)
    $hdr = @($lines[0].Split($TAB) | ForEach-Object { $_.Trim() })
    $rows = @()
    for ($i = 1; $i -lt $lines.Length; $i++) {
        if ($lines[$i].Length -eq 0) { continue }
        $rows += , $lines[$i].Split($TAB)
    }
    return @{ hdr = $hdr; rows = $rows }
}

function Col([string[]]$hdr, [string]$name) {
    for ($j = 0; $j -lt $hdr.Length; $j++) { if ($hdr[$j] -eq $name) { return $j } }
    throw "no column $name"
}

$TA = Read-Tab (Join-Path $R14 'R17_R72_T1_CLEANSCALE\files_tier_A_snap2.tsv')
$TC = Read-Tab (Join-Path $R14 'R17_R78_T1_RECLASS\files_tier_Cprime.tsv')
$TV = Read-Tab (Join-Path $R14 'R17_R81_T2_EVID\_verdicts.tsv')
$TO = Read-Tab (Join-Path $R14 'R17_R72_T1_CLEANSCALE\files_tier_C.tsv')

$iAr = Col $TA.hdr 'rel'; $iAb = Col $TA.hdr 'bytes'
$iCr = Col $TC.hdr 'rel'; $iCw = Col $TC.hdr 'why'
$iVr = Col $TV.hdr 'rel'; $iVv = Col $TV.hdr 'verdict'
$iOr = Col $TO.hdr 'rel'

$mapA = @{}
$sumAB = [long]0
foreach ($f in $TA.rows) {
    $k = $f[$iAr].Trim(); $b = [long]$f[$iAb].Trim()
    $mapA[$k] = $b
    $sumAB = $sumAB + $b
}
$cp = @{}
foreach ($f in $TC.rows) { $cp[$f[$iCr].Trim()] = $f[$iCw].Trim() }
$vd = @{}
foreach ($f in $TV.rows) { $vd[$f[$iVr].Trim()] = $f[$iVv].Trim() }
$oldSet = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($f in $TO.rows) { [void]$oldSet.Add($f[$iOr].Trim()) }

# ---- 定义乙 KEEP = (C′ why 以 P1a 开头) ∪ (逐件内容判定 = 对象抄本)，再排自测量装置
$keep = New-Object 'System.Collections.Generic.HashSet[string]'
$nP1a = 0
foreach ($k in $cp.Keys) { if ($cp[$k].StartsWith('P1a')) { [void]$keep.Add($k); $nP1a++ } }
$nObj = 0
foreach ($k in $vd.Keys) { if ($vd[$k] -eq '对象抄本') { [void]$keep.Add($k); $nObj++ } }
$selfList = @('decide_semdef.py', 'posctrl_py.py', 'posctrl_ps.ps1', 'closure.py',
    'xcheck.py', 'audit_parts.py', 'probe_evid_exts.ps1', 'tier_final.tsv', 'semi_items.tsv',
    'excluded_final.tsv', 'other6_unknown.tsv', 'semdef.json',
    'run_decide.log', 'run_posctrl_py.log', 'run_posctrl_ps.log', 'run_closure.log', 'run_xcheck.log')
foreach ($s in $selfList) { [void]$keep.Remove('next_re_20261117_r14/R17_R88_T1_SEMDEF/' + $s) }
[void]$keep.Remove('next_re_20261117_r14/R17_R88_T1_SEMDEF/REPORT.md')
Write-Output ("PS P1A={0} OBJ={1} KEEP={2}" -f $nP1a, $nObj, $keep.Count)

$kB = [long]0
foreach ($k in $keep) { $kB += $mapA[$k] }
$kOld = 0; $kOldB = [long]0
foreach ($k in $keep) { if ($oldSet.Contains($k)) { $kOld++; $kOldB += $mapA[$k] } }
Write-Output ("PS YI KEEP={0}/{1}  oldC_in={2}/{3}  not_oldC={4}/{5}" -f `
        $keep.Count, $kB, $kOld, $kOldB, ($keep.Count - $kOld), ($kB - $kOldB))

# ---- 定义乙 分桶（KEEP / 过程 / 其余）
$proc = New-Object 'System.Collections.Generic.HashSet[string]'
foreach ($k in $vd.Keys) { if ($vd[$k] -eq '过程输出') { [void]$proc.Add($k) } }
$sumProc = [long]0
foreach ($k in $proc) { $sumProc += $mapA[$k] }
$sumRest = $sumAB - $kB - $sumProc
Write-Output ("PS YI proc={0}/{1}  rest={2}/{3}  A={4}/{5}" -f `
        $proc.Count, $sumProc, ($mapA.Count - $keep.Count - $proc.Count), $sumRest, $mapA.Count, $sumAB)
Write-Output ("PS IDENT KEEP+proc+rest == A ? {0}/{1}" -f `
        (($keep.Count + $proc.Count + $mapA.Count - $keep.Count - $proc.Count) -eq $mapA.Count), `
        (($kB + $sumProc + $sumRest) -eq $sumAB))

# ---- 定义甲：实盘 6 扩展名 − 过程 − 不在档 A 的
$six = @('.md', '.txt', '.json', '.tsv', '.log', '.csv')
$diskN = 0; $diskB = [long]0; $exN = 0; $exOB = [long]0; $notAN = 0; $notAB = [long]0
foreach ($f in (Get-ChildItem -File -Recurse -Force $R)) {
    if ($six -notcontains $f.Extension.ToLower()) { continue }
    $rel = $f.FullName.Substring($R.Length + 1).Replace('\', '/')
    $diskN++; $diskB += $f.Length
    if ($proc.Contains($rel)) { $exN++; $exOB += $f.Length; continue }
    if (-not $mapA.ContainsKey($rel)) { $notAN++; $notAB += $f.Length }
}
Write-Output ("PS JIA disk={0}/{1}  proc={2}/{3}  notA={4}/{5}  JIA={6}/{7}" -f `
        $diskN, $diskB, $exN, $exOB, $notAN, $notAB, ($diskN - $exN - $notAN), ($diskB - $exOB - $notAB))

# ---- 逐件核对 tier_final.tsv
$TT = Read-Tab (Join-Path $R14 'R17_R88_T1_SEMDEF\tier_final.tsv')
$iTr = Col $TT.hdr 'rel'; $iTb = Col $TT.hdr 'bytes'
$tfSet = New-Object 'System.Collections.Generic.HashSet[string]'
$tfB = [long]0
foreach ($f in $TT.rows) { [void]$tfSet.Add($f[$iTr].Trim()); $tfB += [long]$f[$iTb].Trim() }
$onlyFile = 0; foreach ($k in $tfSet) { if (-not $keep.Contains($k)) { $onlyFile++ } }
$onlyCalc = 0; foreach ($k in $keep) { if (-not $tfSet.Contains($k)) { $onlyCalc++ } }
Write-Output ("PS TIER files={0}/{1}  set_equal={2}  bytes_equal={3}" -f `
        $tfSet.Count, $tfB, ($onlyFile -eq 0 -and $onlyCalc -eq 0), ($tfB -eq $kB))
Write-Output ("PS GB={0} GiB={1}" -f [math]::Round($kB / 1e9, 6), [math]::Round($kB / [math]::Pow(2, 30), 6))
