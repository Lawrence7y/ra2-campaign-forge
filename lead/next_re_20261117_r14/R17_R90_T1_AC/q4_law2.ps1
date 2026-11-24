# Q4 · 正控 法2（PowerShell/.NET，完全独立实现，不调用任何 Python）
# 只读 lead\ 下的既有清单；用 .NET 的 [System.IO.File]::ReadAllLines + String.Split 全量重算。
# 输出 A（同目录多数派可裁）与 C（126 件回滚标记件）的件数/字节，并复算两张清单文件的合计。
# 与法1 的差异：法1 用 csv.DictReader 迭代 + 字典；本法是逐行 Split + 哈希表，互不复用代码。

$ErrorActionPreference = 'Stop'
$LEAD = 'D:\Project\ra2-campaign-forge\lead'
$R14  = Join-Path $LEAD 'next_re_20261117_r14'
$EVID = Join-Path $R14 'R17_R81_T2_EVID'
$NAR  = Join-Path $R14 'R17_R84_T1_NARRATIVE'
$HERE = Join-Path $R14 'R17_R90_T1_AC'

function Get-Rows($path) {
    $lines = [System.IO.File]::ReadAllLines($path)
    $head = $lines[0].Split("`t")
    $idx = @{}
    for ($i = 0; $i -lt $head.Count; $i++) { $idx[$head[$i]] = $i }
    $out = New-Object System.Collections.Generic.List[object]
    for ($j = 1; $j -lt $lines.Count; $j++) {
        if ([string]::IsNullOrWhiteSpace($lines[$j])) { continue }
        $p = $lines[$j].Split("`t")
        $o = @{}
        foreach ($k in $idx.Keys) { $o[$k] = if ($idx[$k] -lt $p.Count) { $p[$idx[$k]] } else { '' } }
        $out.Add($o)
    }
    return ,$out
}

# ---------- A ----------
$und = Get-Rows (Join-Path $EVID '_undead_evid.tsv')
$bytesMap = @{}
foreach ($r in $und) { $bytesMap[($r['rel'] -replace '\\','/')] = [int64]$r['bytes'] }

$ver = Get-Rows (Join-Path $EVID '_verdicts.tsv')
$dirObj = @{}; $dirProc = @{}
foreach ($r in $ver) {
    if ($r['verdict'] -eq '对象抄本' -or $r['verdict'] -eq '过程输出') {
        $d = [System.IO.Path]::GetDirectoryName($r['rel'])
        if ($r['verdict'] -eq '对象抄本') { $dirObj[$d] = 1 + [int]($dirObj[$d]) }
        else { $dirProc[$d] = 1 + [int]($dirProc[$d]) }
    }
}
$AN = 0; $AB = [int64]0
foreach ($r in $ver) {
    if ($r['verdict'] -ne '无法判定') { continue }
    $d = [System.IO.Path]::GetDirectoryName($r['rel'])
    $o = [int]($dirObj[$d]); $pp = [int]($dirProc[$d])
    $n = $o + $pp
    if ($n -ge 3 -and $o -ne $pp) {
        $share = [double][Math]::Max($o, $pp) / $n
        if ($share -ge 0.75) { $AN = $AN + 1; $AB += $bytesMap[($r['rel'] -replace '\\','/')] }
    }
}

# ---------- C ----------
$cand = Get-Rows (Join-Path $NAR 'narrative_candidates.tsv')
$RE_RB = '(\.before[._][^/]*|\.before$|_before_[^/]*|_bak(\.[^/]*)?$|\.bak$)'
$CN = 0; $CB = [int64]0
foreach ($r in $cand) {
    $parts = $r['rel'].Split('/')
    $bn = $parts[$parts.Count - 1]
    if ($bn -imatch $RE_RB) { $CN = $CN + 1; $CB += [int64]$r['bytes'] }
}

# ---------- 清单自洽 ----------
function Get-TsvSum($p) {
    $rows = Get-Rows $p
    $n = $rows.Count; $b = [int64]0
    foreach ($r in $rows) { $b += [int64]$r['bytes'] }
    return @{ n = $n; bytes = $b }
}
$Atsv = Get-TsvSum (Join-Path $HERE 'majority_114.tsv')
$Ctsv = Get-TsvSum (Join-Path $HERE 'u1_126.tsv')

$res = [ordered]@{
    law             = 'pwsh_q4_posctrl.ps1'
    A_from_source   = @{ n = $AN; bytes = $AB }
    C_from_source   = @{ n = $CN; bytes = $CB }
    A_from_tsv      = @{ n = $Atsv.n; bytes = $Atsv.bytes }
    C_from_tsv      = @{ n = $Ctsv.n; bytes = $Ctsv.bytes }
}
$res | ConvertTo-Json -Depth 6
$res | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 (Join-Path $HERE 'q4_law2_ps.json')
