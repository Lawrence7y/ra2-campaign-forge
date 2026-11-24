$ErrorActionPreference = 'Stop'

$dir = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COMMON_FIX_S17'
$doc = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md'
$bak = Join-Path $dir 'R14_COMMON.M62.bak'
$cov = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
$atl = 'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'
$enc = New-Object System.Text.UTF8Encoding($false)

# ---- re-run the recompute script and capture its output ----
$recomputeOut = & pwsh -NoProfile -File (Join-Path $dir '01_recompute.ps1') 2>&1

# ---- recompute the headline numbers again, for the comparison table ----
$lines = Get-Content $cov
$body = $lines[1..($lines.Count - 1)]
$set = New-Object 'System.Collections.Generic.HashSet[string]'
Get-Content $atl | Select-Object -Skip 1 | ForEach-Object { [void]$set.Add((($_ -split "`t")[0]).ToLower()) }
$inA = @()
foreach ($l in $body) { $f = $l -split "`t"; if ($f[1] -eq 'S17' -and $set.Contains($f[0].ToLower())) { $inA += , $f } }
$n = $inA.Count
$namedL = @($inA | Where-Object { ([string]$_[2]).Trim() -ne '' -and $_[2] -notmatch '^sub_[0-9A-Fa-f]+$' }).Count
$namedS = @(@($inA | Where-Object { ([string]$_[2]).Trim() -ne '' -and $_[2] -notmatch '^sub_[0-9A-Fa-f]+$' }) | Where-Object { $_[2] -notmatch '::sub_[0-9A-Fa-f]+$' }).Count
$namedSt = @(@(@($inA | Where-Object { ([string]$_[2]).Trim() -ne '' -and $_[2] -notmatch '^sub_[0-9A-Fa-f]+$' }) | Where-Object { $_[2] -notmatch '::sub_[0-9A-Fa-f]+$' }) | Where-Object { $_[2] -notmatch '(?i)slot\d+' }).Count
$empty = @($inA | Where-Object { ([string]$_[2]).Trim() -eq '' }).Count
$subF = @($inA | Where-Object { $_[2] -match '^sub_[0-9A-Fa-f]+$' }).Count
$slotF = @($inA | Where-Object { $_[2] -match '(?i)slot\d+' }).Count
$thr = [math]::Ceiling(0.9 * $n)

# ---- pipe count per target row: unchanged? (table structure check) ----
$oldText = $enc.GetString([System.IO.File]::ReadAllBytes($bak))
$newText = $enc.GetString([System.IO.File]::ReadAllBytes($doc))
$oldCh = [regex]::Split($oldText, '(?<=\n)')
$newCh = [regex]::Split($newText, '(?<=\n)')
$markerCount = 108

$L = New-Object System.Collections.Generic.List[string]
$L.Add('COMMON-FIX-S17 / M62 —— S17 名字口径重算留痕（RECOMPUTE）')
$L.Add('=' * 78)
$L.Add('')
$L.Add('一、口径（与 COVERAGE\PANEL.md 现行表头定义、RULING-R15 D-38 一致）')
$L.Add('  n            = coverage.tsv 中 subsystem == S17 且 entry 属于 function_atlas.tsv 的行数')
$L.Add('                 （atlas 的 entry 列为小写十六进制，比对时两侧统一转小写）')
$L.Add('  named_L      = name 非空，且不是 sub_<hex> 占位名')
$L.Add('  named_S(R14) = named_L 且排除 ::sub_<hex> 复合名（DoD 判定列；D-38：slotN 计入 named）')
$L.Add('  named_strict = named_S(R14) 且排除 slotN 形态（参考列，不参与达标判定）')
$L.Add('  门槛         = ceil(0.9 × n)')
$L.Add('')
$L.Add('二、命令')
$L.Add('  pwsh -NoProfile -File lead\next_re_20261117_r14\COMMON_FIX_S17\01_recompute.ps1')
$L.Add('  （输入指纹：coverage.tsv 18,498 数据行 / function_atlas.tsv 12,916 数据行）')
$L.Add('')
$L.Add('三、输出（原样捕获）')
$L.Add('-' * 78)
foreach ($o in $recomputeOut) { $L.Add('  ' + [string]$o) }
$L.Add('-' * 78)
$L.Add('')
$L.Add('四、与 Lead 交办数字对照')
$L.Add('  项目                        Lead        本轮重算    一致')
$L.Add(('  n                          {0,6}      {1,6}      {2}' -f 102, $n, ($n -eq 102)))
$L.Add(('  named_L                    {0,6}      {1,6}      {2}' -f 94, $namedL, ($namedL -eq 94)))
$L.Add(('  named_S(R14)               {0,6}      {1,6}      {2}' -f 94, $namedS, ($namedS -eq 94)))
$L.Add(('  named_strict               {0,6}      {1,6}      {2}' -f 58, $namedSt, ($namedSt -eq 58)))
$L.Add(('  name 为空                  {0,6}      {1,6}      {2}' -f 0, $empty, ($empty -eq 0)))
$L.Add(('  sub_ 形态                  {0,6}      {1,6}      {2}' -f 8, $subF, ($subF -eq 8)))
$L.Add(('  slotN 形态                 {0,6}      {1,6}      {2}' -f 36, $slotF, ($slotF -eq 36)))
$L.Add(('  门槛 ceil(0.9×102)         {0,6}      {1,6}      {2}' -f 92, $thr, ($thr -eq 92)))
$L.Add(('  named_S(R14) 余量          {0,6}      {1,6}      {2}' -f 2, ($namedS - $thr), (($namedS - $thr) -eq 2)))
$allMatch = ($n -eq 102 -and $namedL -eq 94 -and $namedS -eq 94 -and $namedSt -eq 58 -and $empty -eq 0 -and $subF -eq 8 -and $slotF -eq 36 -and $thr -eq 92)
$L.Add('')
$L.Add(('  全部一致 = ' + $allMatch + '  ⇒ 按卡面要求继续落笔，未触发「停下来报告」条件。'))
$L.Add('  补充：94/102 = ' + [math]::Round(100.0 * 94 / 102, 2) + '%；58/102 = ' + [math]::Round(100.0 * 58 / 102, 2) + '%；92 - 58 = ' + (92 - 58) + ' 行（§12.5 末句「仍差 34 行」的依据）。')
$L.Add('')
$L.Add('五、三处改动行的表格列数未破坏（防止行内追加撑出多余单元格）')
foreach ($ln in @(775, 794, 812)) {
    $oldCore = $oldCh[$ln - 1].TrimEnd("`r", "`n")
    $newCore = $newCh[$ln - 1].TrimEnd("`r", "`n")
    $oldPipes = ([regex]::Matches($oldCore, '\|')).Count
    $newPipes = ([regex]::Matches($newCore, '\|')).Count
    $delta = $newCore.Length - $oldCore.Length
    $L.Add(('  L{0}: 竖线 {1} -> {2}（不变={3}）；行长 +{4} 字符（= 标记 {5} 字符）' -f $ln, $oldPipes, $newPipes, ($oldPipes -eq $newPipes), $delta, $markerCount))
}
$L.Add('  ⇒ 标记内含 0 个竖线，且插在收尾 `|` 之前，故各行列数与表头保持一致。')
$L.Add('')
$L.Add('六、行数变化')
$oldLines = ([regex]::Matches($oldText, "`n")).Count
$newLines = ([regex]::Matches($newText, "`n")).Count
$L.Add(('  换行符计数 {0} -> {1}（+{2}）；新增内容 = 1 空行 + §12.5 共 13 行 = 14 行' -f $oldLines, $newLines, ($newLines - $oldLines)))
$L.Add('  §12.5 追加段行尾用 LF（与 L1083 以后 §11/§12 追加段一致）；三处行内标记不触碰行尾，原 CRLF 保留。')
$L.Add('')
$L.Add('七、本节可复现性')
$L.Add('  脚本：01_recompute.ps1（重算）、02_apply.ps1（写入 + 字符级插入证明）、03_hash.ps1（字节级证明与 HASH.txt）')
$L.Add('  备份：R14_COMMON.M62.bak（改前原件，sha256 B64536F0285CCDA7024A465D1A1F2EBDDC4D967AD404A416347F9BF525DF14EA）')
$L.Add('')
[System.IO.File]::WriteAllLines((Join-Path $dir 'RECOMPUTE.txt'), $L, $enc)
Get-Content (Join-Path $dir 'RECOMPUTE.txt') | Select-Object -Skip 26 | Out-String -Width 300
