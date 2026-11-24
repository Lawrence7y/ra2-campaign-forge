$ErrorActionPreference = 'Stop'

$doc = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R14_COMMON.md'
$dir = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COMMON_FIX_S17'

# ---------- 1. snapshot before ----------
$oldBytes = [System.IO.File]::ReadAllBytes($doc)
$oldLen   = $oldBytes.Length
$oldSha   = (Get-FileHash $doc -Algorithm SHA256).Hash
Copy-Item -LiteralPath $doc -Destination (Join-Path $dir 'R14_COMMON.M62.bak') -Force
$oldText = [System.Text.Encoding]::UTF8.GetString($oldBytes)
Write-Output ("[BEFORE] bytes = " + $oldLen)
Write-Output ("[BEFORE] sha256 = " + $oldSha)
Write-Output ("[BEFORE] utf8 roundtrip lossless = " + ((New-Object System.Text.UTF8Encoding($false)).GetBytes($oldText).Length -eq $oldLen))

# ---------- 2. locate the three rows, verify their current wording ----------
$chunks = [regex]::Split($oldText, '(?<=\n)')
$starts = New-Object int[] $chunks.Count
$acc = 0
for ($i = 0; $i -lt $chunks.Count; $i++) { $starts[$i] = $acc; $acc += $chunks[$i].Length }

$marker = ' 〔M62 更正：该数为 §990 时点截面；M56/S17-PADD 之后 `named_S(R14)` 已为 **94/102 = 92.16%**，门槛 92，**余量 +2**，非零余量。见 §12.5。〕 '

$targets = @(775, 794, 812)
$inserts = @()
foreach ($ln in $targets) {
    $i    = $ln - 1
    $ch   = $chunks[$i]
    $core = $ch.TrimEnd("`r", "`n")
    if (-not $core.EndsWith('|')) { throw "line $ln does not end with a table pipe" }
    if ($core -notmatch '92/102 = 90\.20%') { throw "line $ln does not carry the 92/102 = 90.20% figure" }
    if ($core -notmatch '零余量') { throw "line $ln does not carry the zero-margin claim" }
    if ($core -match 'M62') { throw "line $ln already carries an M62 marker" }
    $pos = $starts[$i] + $core.Length - 1   # insert right before the closing '|'
    Write-Output ("[ANCHOR] line " + $ln + " charOffset=" + $pos + " eol=" + $(if ($ch.EndsWith("`r`n")) {'CRLF'} else {'LF'}) + " tail=" + $core.Substring([Math]::Max(0, $core.Length - 28)))
    $inserts += [pscustomobject]@{ Pos = $pos; Text = $marker; Id = ("line " + $ln) }
}

# ---------- 3. the §12.5 block ----------
$block = @'
### §12.5 S17 名字口径现态更正（M62）

§990 及后续三处「S17 存档」记 `named(S) = 92/102 = 90.20%`、判「零余量」，那是 §990 时点截面。
M56 并入 `006CF430` / `004A2990` 两个名字之后，盘上现值为：

| 口径 | 现值 | 门槛 `ceil(0.9 × 102)` | 判定 |
|---|---:|---:|---|
| `named_L` | 94 | 92 | 达标，余量 +2 |
| `named_S(R14)`（**DoD 判定列**） | 94 | 92 | 达标，余量 +2 |
| `named_strict` | 58 | 92 | 未达标 |

n = 102（S17 且 entry 在 atlas 内；atlas `entry` 为小写，比对已归一）。name 为空 0 行、`sub_` 形态 8 行、`slotN` 形态 36 行。
⇒ 引用 S17 名字余量时**不得再说「零余量」**；正确表述是「`named_S(R14)` 余量 **+2**，`named_strict` 仍差 34 行」。
'@
$block = $block -replace "`r`n", "`n"
$tailText = "`n" + $block + "`n"
$inserts += [pscustomobject]@{ Pos = $oldText.Length; Text = $tailText; Id = 'EOF §12.5' }
Write-Output ("[ANCHOR] EOF charOffset=" + $oldText.Length + " (tail append, LF)")

if ($oldText -match '§12\.5') { throw 'document already contains a §12.5 - abort' }

# ---------- 4. apply (descending offsets => coordinates of $oldText stay valid) ----------
$new = $oldText
foreach ($ins in ($inserts | Sort-Object Pos -Descending)) {
    $new = $new.Substring(0, $ins.Pos) + $ins.Text + $new.Substring($ins.Pos)
}

# ---------- 5. insert-only proof: remove exactly the inserted spans, must equal old ----------
# map each insertion from old coordinates to new coordinates
$cum = 0
$removals = @()
foreach ($ins in ($inserts | Sort-Object Pos)) {
    $removals += [pscustomobject]@{ OldPos = $ins.Pos; NewPos = $ins.Pos + $cum; Text = $ins.Text; Id = $ins.Id }
    $cum += $ins.Text.Length
}
# (a) each inserted span sits exactly where it should, with unchanged text on both sides
$CTX = 80
foreach ($r in $removals) {
    if ($new.Substring($r.NewPos, $r.Text.Length) -ne $r.Text) { throw ("insert span mismatch at " + $r.Id) }
    $bl = [Math]::Min($CTX, $r.OldPos)
    $beforeOld = $oldText.Substring($r.OldPos - $bl, $bl)
    $beforeNew = $new.Substring($r.NewPos - $bl, $bl)
    if ($beforeOld -cne $beforeNew) { throw ("before-context mismatch at " + $r.Id) }
    $al = [Math]::Min($CTX, $oldText.Length - $r.OldPos)
    $afterOld = $oldText.Substring($r.OldPos, $al)
    $afterNew = $new.Substring($r.NewPos + $r.Text.Length, $al)
    if ($afterOld -cne $afterNew) { throw ("after-context mismatch at " + $r.Id) }
    Write-Output ("[PROOF] " + $r.Id + ": span placed, " + $bl + "B before / " + $al + "B after identical to old = OK")
}
# (b) deleting exactly those spans must reproduce the old file
$rebuilt = $new
foreach ($r in ($removals | Sort-Object NewPos -Descending)) {
    $rebuilt = $rebuilt.Substring(0, $r.NewPos) + $rebuilt.Substring($r.NewPos + $r.Text.Length)
}
if ($rebuilt -cne $oldText) { throw 'reconstruction from new file !== old file' }
Write-Output "[PROOF] removing exactly the 4 inserted spans reproduces the old text character-for-character: MATCH"

# ---------- 6. write ----------
$enc = New-Object System.Text.UTF8Encoding($false)
[System.IO.File]::WriteAllBytes($doc, $enc.GetBytes($new))

$newBytes = [System.IO.File]::ReadAllBytes($doc)
$newLen   = $newBytes.Length
$newSha   = (Get-FileHash $doc -Algorithm SHA256).Hash
Write-Output ("[AFTER ] bytes = " + $newLen + "  (delta +" + ($newLen - $oldLen) + ")")
Write-Output ("[AFTER ] sha256 = " + $newSha)

# ---------- 7. prefix check ----------
$prefix = New-Object byte[] $oldLen
[Array]::Copy($newBytes, 0, $prefix, 0, $oldLen)
$sha256 = [System.Security.Cryptography.SHA256]::Create()
$prefixSha = (($sha256.ComputeHash($prefix)) | ForEach-Object { $_.ToString('X2') }) -join ''
Write-Output ("[PREFIX] old length = " + $oldLen)
Write-Output ("[PREFIX] sha256(new[0..oldLen)) = " + $prefixSha)
Write-Output ("[PREFIX] sha256(old, whole file) = " + $oldSha)
Write-Output ("[PREFIX] LITERAL equality (old file is byte-prefix of new file) = " + ($prefixSha -eq $oldSha))
$sha256.Dispose()

# per-insertion offset prefix equality in byte terms (only meaningful up to first insertion)
$firstPos = ($inserts | Sort-Object Pos | Select-Object -First 1).Pos
$lastByte = $enc.GetByteCount($oldText.Substring(0, $firstPos))
$a = New-Object byte[] $lastByte; [Array]::Copy($oldBytes, 0, $a, 0, $lastByte)
$b = New-Object byte[] $lastByte; [Array]::Copy($newBytes, 0, $b, 0, $lastByte)
$s2 = [System.Security.Cryptography.SHA256]::Create()
$ha = (($s2.ComputeHash($a)) | ForEach-Object { $_.ToString('X2') }) -join ''
$hb = (($s2.ComputeHash($b)) | ForEach-Object { $_.ToString('X2') }) -join ''
Write-Output ("[PREFIX] bytes before first insertion (" + $lastByte + " B): old=" + $ha)
Write-Output ("[PREFIX] bytes before first insertion (" + $lastByte + " B): new=" + $hb)
Write-Output ("[PREFIX] equal = " + ($ha -eq $hb))
$s2.Dispose()
