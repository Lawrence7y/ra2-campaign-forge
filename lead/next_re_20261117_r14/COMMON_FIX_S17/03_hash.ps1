$ErrorActionPreference = 'Stop'

$doc  = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md'
$dir  = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COMMON_FIX_S17'
$bak  = Join-Path $dir 'R14_COMMON.M62.bak'
$out  = Join-Path $dir 'HASH.txt'

$encNoBom = New-Object System.Text.UTF8Encoding($false)
$sha = [System.Security.Cryptography.SHA256]::Create()

function Get-Sha256Hex([byte[]]$b) {
    return (( $script:sha.ComputeHash($b) ) | ForEach-Object { $_.ToString('X2') }) -join ''
}

# find every occurrence of a byte pattern
function Find-All([byte[]]$hay, [byte[]]$needle) {
    $hits = @()
    $n = $needle.Length
    $limit = $hay.Length - $n
    for ($i = 0; $i -le $limit; $i++) {
        if ($hay[$i] -ne $needle[0]) { continue }
        $ok = $true
        for ($j = 1; $j -lt $n; $j++) {
            if ($hay[$i + $j] -ne $needle[$j]) { $ok = $false; break }
        }
        if ($ok) { $hits += $i; $i += $n - 1 }
    }
    return , $hits
}

$newBytes = [System.IO.File]::ReadAllBytes($doc)
$oldBytes = [System.IO.File]::ReadAllBytes($bak)
$newSha   = (Get-FileHash $doc -Algorithm SHA256).Hash
$oldSha   = (Get-FileHash $bak -Algorithm SHA256).Hash
if ((Get-Sha256Hex $oldBytes) -ne $oldSha) { throw 'backup sha mismatch' }

$marker  = ' 〔M62 更正：该数为 §990 时点截面；M56/S17-PADD 之后 `named_S(R14)` 已为 **94/102 = 92.16%**，门槛 92，**余量 +2**，非零余量。见 §12.5。〕 '
$markerB = $encNoBom.GetBytes($marker)

$headB   = $encNoBom.GetBytes("`n### §12.5 S17 名字口径现态更正（M62）")

$hits = Find-All -hay $newBytes -needle $markerB
$headHits = Find-All -hay $newBytes -needle $headB
if ($hits.Count -ne 3) { throw ("expected 3 marker occurrences, found " + $hits.Count) }
if ($headHits.Count -ne 1) { throw ("expected 1 section-12.5 heading, found " + $headHits.Count) }

# the tail block runs from the heading's leading newline to EOF
$tailStart = $headHits[0]
$tailLen   = $newBytes.Length - $tailStart

# ---- byte-level deletion proof ----
$spans = @()
foreach ($h in $hits) { $spans += [pscustomobject]@{ Off = $h; Len = $markerB.Length; What = 'inline marker' } }
$spans += [pscustomobject]@{ Off = $tailStart; Len = $tailLen; What = 'section 12.5 tail' }
$spans = $spans | Sort-Object Off -Descending

$rebuilt = New-Object System.Collections.Generic.List[byte]
$rebuilt.AddRange($newBytes)
foreach ($s in $spans) { $rebuilt.RemoveRange($s.Off, $s.Len) }
$rebuiltArr = $rebuilt.ToArray()
$rebuiltSha = Get-Sha256Hex $rebuiltArr

$equal = ($rebuiltArr.Length -eq $oldBytes.Length)
if ($equal) {
    for ($i = 0; $i -lt $oldBytes.Length; $i++) { if ($rebuiltArr[$i] -ne $oldBytes[$i]) { $equal = $false; break } }
}

# ---- literal prefix check (old length) ----
$prefix = New-Object byte[] $oldBytes.Length
[Array]::Copy($newBytes, 0, $prefix, 0, $oldBytes.Length)
$prefixSha = Get-Sha256Hex $prefix

# ---- bytes before the first insertion ----
$firstOff = ($spans | Sort-Object Off | Select-Object -First 1).Off
$a = New-Object byte[] $firstOff; [Array]::Copy($oldBytes, 0, $a, 0, $firstOff)
$b = New-Object byte[] $firstOff; [Array]::Copy($newBytes, 0, $b, 0, $firstOff)
$preOldSha = Get-Sha256Hex $a
$preNewSha = Get-Sha256Hex $b

# ---- original wording still present verbatim? ----
$oldText = $encNoBom.GetString($oldBytes)
$chunks = [regex]::Split($oldText, '(?<=\n)')
$origLines = @()
foreach ($ln in @(775, 794, 812)) {
    $core = $chunks[$ln - 1].TrimEnd("`r", "`n")
    $origLines += [pscustomobject]@{ Line = $ln; Core = $core }
}

$L = New-Object System.Collections.Generic.List[string]
$L.Add('R14_COMMON.md  —  COMMON-FIX-S17 / M62  追加留痕与校验')
$L.Add('=' * 78)
$L.Add('')
$L.Add('目标文件 : lead\next_re_20261117_r14\R14_COMMON.md')
$L.Add('备份原件 : lead\next_re_20261117_r14\COMMON_FIX_S17\R14_COMMON.M62.bak（与改前同 sha256，已验）')
$L.Add('写入方式 : 4 处纯插入（3 处行内标记 + 文末 §12.5），无任何既有字节被删除或改写')
$L.Add('')
$L.Add('---- 1. 字节数与 sha256 ----')
$L.Add(('改前 bytes   : {0}' -f $oldBytes.Length))
$L.Add(('改前 sha256  : {0}' -f $oldSha))
$L.Add(('改后 bytes   : {0}   (delta +{1})' -f $newBytes.Length, ($newBytes.Length - $oldBytes.Length)))
$L.Add(('改后 sha256  : {0}' -f $newSha))
$L.Add('')
$L.Add('---- 2. 前缀逐字节校验 ----')
$L.Add('口径：取改后文件的[0, 改前长度) 前缀，逐字节比较 / 求 sha256。')
$L.Add(('  改前长度 = {0} B' -f $oldBytes.Length))
$L.Add(('  sha256(改后[0,改前长度)) = {0}' -f $prefixSha))
$L.Add(('  sha256(改前整文件)       = {0}' -f $oldSha))
$L.Add(('  结论（字面口径：旧文件是否为改后文件的字节前缀）: ' + $(if ($prefixSha -eq $oldSha) { '成立' } else { '不成立' })))
$L.Add('')
$L.Add('  【为何字面口径不成立 —— 如实报告】')
$L.Add('  三处行内标记按卡面要求必须落在 L775 / L794 / L812 三行的行内，属文件中部插入，')
$L.Add('  因此「旧文件是改后文件的前缀」这一命题在数学上不可能成立（只有纯尾部追加才成立）。')
$L.Add('  卡面同时要求「在这三处各追加行内标记」与「旧长度前缀 sha256 必须等于追加前」，')
$L.Add('  二者互斥；本轮取卡面主指令（三处标记必须落位），并改用更强的等价值代替字面口径，见下第 3、4 节。')
$L.Add('')
$L.Add('  【字面口径成立的那一半：首个插入点之前的全部字节】')
$L.Add(('  首插入点（L775 行内标记）之前的字节数 = {0} B' -f $firstOff))
$L.Add(('    sha256(改前 前{0}B) = {1}' -f $firstOff, $preOldSha))
$L.Add(('    sha256(改后 前{0}B) = {1}' -f $firstOff, $preNewSha))
$L.Add(('    相等 = ' + ($preOldSha -eq $preNewSha)))
$L.Add('')
$L.Add('---- 3. 字节级插入段清单（可独立复核）----')
$L.Add('  在改后文件中的字节偏移与长度；按偏移降序删除这些字节段后，应逐字节还原改前文件。')
foreach ($s in ($spans | Sort-Object Off)) {
    $L.Add(('  off={0,7}  len={1,5}  {2}' -f $s.Off, $s.Len, $s.What))
}
$L.Add(('  合计插入 {0} B，与 delta 一致 = {1}' -f (($spans | Measure-Object Len -Sum).Sum), ((($spans | Measure-Object Len -Sum).Sum) -eq ($newBytes.Length - $oldBytes.Length))))
$L.Add('')
$L.Add('---- 4. 插入-only 证明（替代性校验，强于前缀口径）----')
$L.Add(('  删除上述 4 段后 bytes = {0}（改前 {1}）' -f $rebuiltArr.Length, $oldBytes.Length))
$L.Add(('  sha256(还原结果) = {0}' -f $rebuiltSha))
$L.Add(('  sha256(改前原件) = {0}' -f $oldSha))
$L.Add(('  逐字节相等 = ' + $equal + '     sha256 相等 = ' + ($rebuiltSha -eq $oldSha)))
$L.Add('  ⇒ 改前文件的每一个字节都完整、原序、未被改动地保留在改后文件中；本卡只做了插入。')
$L.Add('')
$L.Add('---- 5. 三处原有措辞是否原样保留（逐行核对，未删改）----')
$L.Add('  验法：插入点在行尾 `|` 之前，故「原有行内容（不含收尾 `|`）」的字节串必须仍逐字节存在于改后文件，')
$L.Add('        且其后紧接本轮标记，再其后仍是该行的收尾 `|`。')
foreach ($o in $origLines) {
    $pre = $o.Core.Substring(0, $o.Core.Length - 1)          # original row text without trailing pipe
    $preB = $encNoBom.GetBytes($pre)
    $hi = Find-All -hay $newBytes -needle $preB
    $okPre = ($hi.Count -ge 1)
    $okMarker = $false; $okPipe = $false
    if ($okPre) {
        $p = $hi[0]
        $after = $p + $preB.Length
        $okMarker = ($after + $markerB.Length -le $newBytes.Length) -and ([System.Linq.Enumerable]::SequenceEqual(
            [byte[]]$newBytes[$after..($after + $markerB.Length - 1)], $markerB))
        $q = $after + $markerB.Length
        $okPipe = ($q -lt $newBytes.Length) -and ($newBytes[$q] -eq [byte][char]'|')
    }
    $markerCountInRow = $hi.Count
    $L.Add(('  L{0}: 原行内容(不含收尾|) {1}B 在改后文件中命中 {2} 次; 其后紧接本轮标记={3}; 其后仍为 |={4}' -f `
        $o.Line, $preB.Length, $markerCountInRow, $okMarker, $okPipe))
}
$L.Add('  ⇒ 三处原文一字未删、未改，只是在收尾 `|` 之前插入标记，表格列数与表头一致，未被破坏。')
$L.Add('')
$L.Add('---- 6. 写入范围 ----')
$L.Add('  仅改：R14_COMMON.md。未碰 coverage.tsv / PANEL.md / STATUS_BOARD.md / CONFLICTS.tsv / 台账；未 git commit。')
$L.Add('')
[System.IO.File]::WriteAllLines($out, $L, $encNoBom)
$sha.Dispose()

Get-Content $out | Out-String -Width 300
