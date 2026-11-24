






$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.Encoding]::UTF8
$OutputEncoding = [Text.Encoding]::UTF8

$C_OBJ = [string]([char]0x5BF9 + [char]0x8C61 + [char]0x6284 + [char]0x672C) # 
$C_PROC = [string]([char]0x8FC7 + [char]0x7A0B + [char]0x8F93 + [char]0x51FA) # 
$C_UND = [string]([char]0x65E0 + [char]0x6CD5 + [char]0x5224 + [char]0x5B9A) # 
$C_PERP = [string]([char]0x6C38 + [char]0x4E45 + [char]0x5224 + [char]0x4E0D + [char]0x4E86) # 
$C_SEP   = [string][char]0x0009
$C_OK = [string]([char]0x4E00 + [char]0x81F4) # 
$C_BAD = [string]([char]0x4E0D + [char]0x4E00 + [char]0x81F4) # 
$C_OLDNEW= [string]([char]0x65E7 + [char]0x005C + [char]0x65B0) # \ 
$C_SUM = [string]([char]0x5408 + [char]0x8BA1) # 
$C_O2P = [string]([char]0x5BF9 + [char]0x8C61 + [char]0x2192 + [char]0x8FC7 + [char]0x7A0B) # 
$C_P2O = [string]([char]0x8FC7 + [char]0x7A0B + [char]0x2192 + [char]0x5BF9 + [char]0x8C61) # 

$LEAD = 'D:\Project\ra2-campaign-forge\lead'
$R = Join-Path $LEAD 'next_re_20261117_r14'
$OUT = Join-Path $R 'R17_R92_T1_REJUDGE'


$ep = Import-Csv (Join-Path $R 'R17_R78_T1_RECLASS\files_excluded_prime.tsv') -Delimiter "`t"
$ud = Import-Csv (Join-Path $R 'R17_R81_T2_EVID\_undead_evid.tsv') -Delimiter "`t"
$vd = Import-Csv (Join-Path $R 'R17_R81_T2_EVID\_verdicts.tsv') -Delimiter "`t"

$bytesMap = @{}
foreach ($x in $ud) { $bytesMap[$x.rel] = [int64]$x.bytes }
$oldMap = @{}
foreach ($x in $vd) { $oldMap[$x.rel] = $x.verdict }

$base = @($ep | Where-Object { $_.label -eq 'UNDECIDED' -and $_.rel.ToUpper().Contains('EVIDENCE') })
Write-Host (" 2 = {0}" -f $base.Count)


function Get-Segments([string]$t) {
    $s = $t.Replace('}{', "}`n{").Replace("},`n{", "}`n{")
    $p = @($s.Split("`n") | Where-Object { $_.Trim().Length -gt 0 })
    if ($p.Count -le 1) {
        $p = @($s.Split(';') | Where-Object { $_.Trim().Length -gt 0 })
        if ($p.Count -le 1) { $p = @([regex]::Split($s, '"\s*,\s*"') | Where-Object { $_.Trim().Length -gt 0 }) }
    }
    return , $p
}

$RE_PREFIX = [regex]'0[xX][0-9A-Fa-f]{6,8}'
$RE_BARE = [regex]'(?<![0-9A-Za-z_])([0-9A-Fa-f]{6,8})(?![0-9A-Za-z_])'
$RE_SECHEAD = [regex]'^\s*=+[\s\w:/.,\-()\[\]#]*\b(disassembly|dump|hexdump|listing|bytes|instructions?)\b[\s\w:/.,\-()\[\]#]*=+\s*$|^\s*(disassembly|disasm|dump|hexdump|listing)\s+(of\s+)?(0x|[\w]+)[0-9A-Fa-fx]*\s*(\.\.|to|-)\s*(0x)?[0-9A-Fa-f]{3,}\s*[:=]?\s*$'
$RE_FRAME = [regex]'^\s*(RUN_ID|TASK|COMMAND|CWD|TIMESTAMP_LOCAL|TIMESTAMP|EXITCODE|EXIT_CODE|run_at\w*|python\s*=|RE-\w+\s+args\b|.*BEGIN RAW STDOUT)'
$RE_META = [regex]'^\s*\{\s*"sha(256)?"\s*:\s*"[0-9A-Fa-f]{32,}"'
$RE_VAL = [regex]'(\b[0-9A-Fa-f]{2}([ ][0-9A-Fa-f]{2}){3,}\b)|(b''(\\x[0-9a-f]{2}){2,})|(\?\?__?\w)|(\.\?A[VU])|([A-Za-z_]\w*(::\w+){1,})|(\[(esi|edi|eax|ebx|ecx|edx|ebp|esp|reg|v|this)\s*[+\-]\s*0x[0-9A-Fa-f]+\])|(slot\s*offset|vtable base|slot#)'
$RE_INSNREL = [regex]'^\s*\+\s*0x[0-9A-Fa-f]{2,8}\s{1,}[0-9A-Fa-f]{2,}(\s+[0-9A-Fa-f]{2,})*\s{1,}[a-z]{2,6}\b'
$RE_INSNHEX = [regex]'^\s*[0-9A-Fa-f]{4,}(\s+[0-9A-Fa-f]{2,})*\s{1,}[a-z]{2,6}\s'
$RE_KVSINGLE = [regex]'^\s*"?[A-Za-z_][A-Za-z0-9_ ]*"?\s*:\s*[-+]?\d+(\.\d+)?([eE][-+]?\d+)?,?\s*$'
$RE_BYTEDUMP = [regex]'^\s*(0x)?[0-9A-Fa-f]{3,8}\s{1,}([NCc+]|0x[0-9A-Fa-f]{2})\s{1,}[0-9A-Fa-f]{2}\b'
$RE_KEYADDR = [regex]'"\s*(0x)?[0-9A-Fa-f]{6,8}\s*"\s*:\s*[\[\{]'
$RE_PROC = [regex]'(sha256|sha1|md5|Get-FileHash|crc32\s*\(|\bhash\b)|(exit\s*code|exitcode|exit=|EXITCODE|returncode|\u9000\u51fa\u7801)|(20\d\d[-/]\d\d[-/]\d\d[T ]\d\d:\d\d|run_at|read_at|TIMESTAMP|mtime|ctime|\u8017\u65f6|elapsed|wall|cpu_ms)|(PASS|FAIL|VERIFIED|ASSERT|\[assert\]|identical\s*=\s*(True|False)|MATCH\s*=\s*(True|False))|([A-Za-z]:\\[^\s]{3,})|(differing|dSize|LCP|LCS|idxDiff|\u5dee\u5206|\u6bd4\u5bf9)'
$RE_STAT = [regex]'"[A-Za-z_][A-Za-z0-9_ ]*"\s*:\s*[-+]?\d+(\.\d+)?|(^|[\s{,(\[])(n|N|K|k|p|pool\w*|total|count\w*|rows?|sites?|hits?)\s*[=:]\s*[-+]?\d'
$RE_STATUSONLY = [regex]'^\s*(done|ok|finished|complete[d]?|wrote|written|saved|merged|copied|moved)\b|(done;|Wrote\s|merged into)'

function Test-BareAddr([string]$tok, [string]$pre) {
    $v = [Convert]::ToInt64($tok, 16)
    $hasAlpha = $tok -match '[A-Fa-f]'
    if (-not $hasAlpha) { return ($v -ge 0x400000 -and $v -le 0xB00000) }
    $uni = ($tok -ceq $tok.ToUpper()) -or ($tok -ceq $tok.ToLower())
    if (-not $uni) { return ($pre -match '[Hh][Ee][Xx]|[Bb][Yy][Tt][Ee][Ss]?|[Dd][Uu][Mm][Pp]|[Rr][Aa][Ww]|\u5b57\u8282') }
    if ($v -ge 0x400000 -and $v -le 0xB00000) { return $true }
    return ($pre -match '(?i)(entry|target|tgt|callee|call|site|jmp|va|rva|foff|off|ptr|base|addr|ret|loc|sub|at|slot)\s*[=:]?\s*$|[@\[]\s*$|\u5730\u5740|\u5165\u53e3|\u7ad9\u70b9')
}

function Get-Addrs([string]$seg) {
    $n = 0
    $n += $RE_PREFIX.Matches($seg).Count
    foreach ($m in $RE_BARE.Matches($seg)) {
        $pre = $seg.Substring([Math]::Max(0, $m.Index - 24), [Math]::Min(24, $m.Index))
        if (Test-BareAddr $m.Groups[1].Value $pre) { $n++ }
    }
    return $n
}

function Get-DecPairs([string]$seg) {
    $c = 0
    foreach ($m in [regex]::Matches($seg, '\[\s*(\d{7,8})\s*,\s*(\d{7,8})\s*\]')) {
        $a = [int64]$m.Groups[1].Value; $b = [int64]$m.Groups[2].Value
        if ($a -ge 4194304 -and $a -lt 11534336 -and $b -ge 4194304 -and $b -lt 11534336 -and $b -ge $a) { $c++ }
    }
    return $c
}

function Get-NewVerdict([string]$rel) {
    $p = Join-Path $LEAD ($rel.Replace('/', [IO.Path]::DirectorySeparatorChar))
    if (-not (Test-Path $p)) { return $C_PERP }
    $total = (Get-Item $p).Length
    $t = [IO.File]::ReadAllText($p, [Text.Encoding]::UTF8)
    $segs = Get-Segments $t
    if ($segs.Count -eq 0) { return $C_PROC }
    if ($RE_META.IsMatch($t)) { return $C_PROC }


    $last = $segs[$segs.Count - 1]
    $lastHasContent = ($RE_INSNREL.IsMatch($last) -or $RE_INSNHEX.IsMatch($last) -or $RE_VAL.IsMatch($last) -or $RE_BYTEDUMP.IsMatch($last) -or (Get-DecPairs $last) -gt 0)
    if ($RE_SECHEAD.IsMatch($last) -and -not $lastHasContent) { return $C_PERP }

    $nObj = 0; $nRev = 0; $nProc = 0; $nFrame = 0
    foreach ($s in $segs) {
        if ($RE_FRAME.IsMatch($s)) { $nFrame++; continue }
        $a = Get-Addrs $s
        $d = Get-DecPairs $s
        $relInsn = $RE_INSNREL.IsMatch($s)
        $byteDump = $RE_BYTEDUMP.IsMatch($s)
        $val = ($RE_VAL.IsMatch($s) -or $relInsn -or $RE_INSNHEX.IsMatch($s) -or $RE_KEYADDR.IsMatch($s) -or $byteDump)
        $isObj = ($a -gt 0) -or ($d -gt 0) -or $val
        $rev = ((($a -gt 0) -or ($d -gt 0)) -and ($val -or ($d -gt 0))) -or $relInsn -or $byteDump
        $kvs = [regex]::Matches($s, '"[A-Za-z_][A-Za-z0-9_]*(\[\d+\])?"\s*:\s*("|\{|\[|\d|true|false|null)').Count
        if ($kvs -ge 2 -and $RE_KEYADDR.IsMatch($s)) { $isObj = $true; $rev = $true }
        $isProc = ($RE_PROC.IsMatch($s) -or $RE_STAT.IsMatch($s) -or $RE_STATUSONLY.IsMatch($s))
        $kvSingle = $RE_KVSINGLE.IsMatch($s)
        $numStmt = ([regex]::Matches($s, '[A-Za-z_\u4e00-\u9fff][\w\- ]{0,30}\s*[=:]\s*\d{1,}')).Count
        $statOnly = (-not $val) -and ($a -eq 0) -and ($RE_STAT.IsMatch($s) -or $kvs -ge 3 -or $kvSingle -or $numStmt -ge 2)
        if ($statOnly) { $isObj = $false; $rev = $false }
        if ($isObj) { $nObj++ }
        if ($rev) { $nRev++ }
        if ($isProc) { $nProc++ }
    }
    $nEff = $segs.Count - $nFrame
    $dens = if ($nEff -gt 0) { $nObj / $nEff } else { 0 }
    if ($nObj -gt 0) {
        if ($nRev -ge 5 -and $nObj -gt $nProc -and $dens -ge 0.40) { return $C_OBJ }
        return $C_PROC
    }
    if ($nProc -gt 0) { return $C_PROC }
    return $C_PERP
}


$cnt = @{}; $byt = @{}; $script:dump = @(); $totB = [int64]0; $totN = 0
$i = 0
foreach ($b in $base) {
    $i++
    if ($i % 200 -eq 0) { Write-Host ("  ... {0}/{1}" -f $i, $base.Count) }
    $rel = $b.rel
    $old = $oldMap[$rel]
    $nw = Get-NewVerdict $rel
    $key = $old + $C_SEP + $nw
    if (-not $cnt.ContainsKey($key)) { $cnt[$key] = 0 }
    $cnt[$key] = $cnt[$key] + 1
    if (-not $byt.ContainsKey($key)) { $byt[$key] = [int64]0 }
    $byt[$key] = $byt[$key] + $bytesMap[$rel]
    $totB += $bytesMap[$rel]
    $script:dump += ($rel + $C_SEP + $(if ($old -eq $C_OBJ) {'0'} elseif ($old -eq $C_PROC) {'1'} elseif ($old -eq $C_UND) {'2'} else {'3'}) + $C_SEP + $(if ($nw -eq $C_OBJ) {'0'} elseif ($nw -eq $C_PROC) {'1'} elseif ($nw -eq $C_UND) {'2'} else {'3'}) + $C_SEP + [string]$bytesMap[$rel])
}

$CLS = @($C_OBJ, $C_PROC, $C_UND, $C_PERP)
Write-Host ''
Write-Host '=== Q5 2 PowerShell ==='
Write-Host ("{0,-14}{1,12}{2,12}{3,12}{4,12}{5,12}" -f $C_OLDNEW, $CLS[0], $CLS[1], $CLS[2], $CLS[3], $C_SUM)
foreach ($o in $CLS) {
    $row = @(); $rs = 0
    foreach ($n in $CLS) { $k = $o + $C_SEP + $n; $v = if ($cnt.ContainsKey($k)) { $cnt[$k] } else { 0 }; $row += $v; $rs += $v }
    Write-Host ("{0,-14}{1,12}{2,12}{3,12}{4,12}{5,12}" -f $o, $row[0], $row[1], $row[2], $row[3], $rs)
    $totN += $rs
}
foreach ($n in $CLS) { $cs = 0; foreach ($o in $CLS) { $k = $o + $C_SEP + $n; if ($cnt.ContainsKey($k)) { $cs += $cnt[$k] } }; }
$k1 = $C_OBJ + $C_SEP + $C_PROC; $k2 = $C_PROC + $C_SEP + $C_OBJ
$obj2proc = if ($cnt.ContainsKey($k1)) { $cnt[$k1] } else { 0 }
$proc2obj = if ($cnt.ContainsKey($k2)) { $cnt[$k2] } else { 0 }
$obj2procB = if ($byt.ContainsKey($k1)) { $byt[$k1] } else { 0 }
$proc2objB = if ($byt.ContainsKey($k2)) { $byt[$k2] } else { 0 }

Write-Host ''
Write-Host (" 2 = {0}" -f $totN)
Write-Host ("F2-O2P = {0} / {1} B" -f $obj2proc, $obj2procB)
Write-Host ("F2-P2O = {0} / {1} B" -f $proc2obj, $proc2objB)


$m1 = Import-Csv (Join-Path $OUT 'q3_matrix.tsv') -Delimiter "`t"
$tot1 = ($m1 | Where-Object { $_.old -eq 'TOTAL' } | Select-Object -First 1)
$s1a = ($m1 | Where-Object { $_.old -eq 'SHIFT' -and $_.new -eq 'obj2proc' } | Select-Object -First 1)
$s1b = ($m1 | Where-Object { $_.old -eq 'SHIFT' -and $_.new -eq 'proc2obj' } | Select-Object -First 1)

Write-Host ''
Write-Host '=== Q5 1 vs 2 ==='
Write-Host (" 1 = {0} 2 = {1} {2}" -f $tot1.n, $totN, $(if ([int]$tot1.n -eq $totN) { $C_OK } else { $C_BAD }))
Write-Host (" 1 = {0} 2 = {1} {2}" -f $tot1.bytes, $totB, $(if ([int64]$tot1.bytes -eq $totB) { $C_OK } else { $C_BAD }))
Write-Host (" 1 {0} /{1}B 2 {2} /{3}B {4}" -f $s1a.n, $s1a.bytes, $obj2proc, $obj2procB, $(if (([int]$s1a.n -eq $obj2proc) -and ([int64]$s1a.bytes -eq $obj2procB)) { $C_OK } else { $C_BAD }))
Write-Host (" 1 {0} /{1}B 2 {2} /{3}B {4}" -f $s1b.n, $s1b.bytes, $proc2obj, $proc2objB, $(if (([int]$s1b.n -eq $proc2obj) -and ([int64]$s1b.bytes -eq $proc2objB)) { $C_OK } else { $C_BAD }))


$lines = @()
$lines += "=== Q5 2 PowerShell ==="
$lines += " 2 = $totN"
$lines += " 2 = $totB"
$lines += "F2-O2P = $obj2proc / $obj2procB B"
$lines += "F2-P2O = $proc2obj / $proc2objB B"
$lines += ""
$lines += " 1 = $($tot1.n) = $($tot1.bytes)"
$lines += " ( ) = $($tot1.n -eq $totN)"
$lines += " ( ) = $([int64]$tot1.bytes -eq $totB)"
$lines += " (obj2proc) = $(([int]$s1a.n -eq $obj2proc) -and ([int64]$s1a.bytes -eq $obj2procB))"
$lines += " (proc2obj) = $(([int]$s1b.n -eq $proc2obj) -and ([int64]$s1b.bytes -eq $proc2objB))"
[IO.File]::WriteAllLines((Join-Path $OUT 'q5_posctrl1_dump.tsv'), $script:dump, (New-Object Text.UTF8Encoding($false)))
$lines | Set-Content (Join-Path $OUT 'q5_posctrl1_ps.txt') -Encoding UTF8
