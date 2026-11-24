$ErrorActionPreference = 'Stop'
$base = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
$probe = Join-Path $base 'COVERAGE\probe_and_data_entries.tsv'

# Task 2: W177-C downgrades (address -> new grade). 00000030 already [未证] -> no change.
$t2 = @{}
foreach ($a in @('0000009C','000000A0','00A8EB50','00B0F724','00B0F730','000001AC','0087F7E8','00000520')) {
    $t2[[Convert]::ToUInt32($a,16)] = '[静态推断]'
}
foreach ($a in @('00886FA0','00886FA4')) {
    $t2[[Convert]::ToUInt32($a,16)] = '[未证]'
}
# Task 3: 15 non-standard bare "已证" tokens -> [已证] (byte-level instr evidence verified)
$t3 = @{}
foreach ($a in @('00482943','004DA560','0052BAD8','0052BAFA','006BEABD','0052F63E','005A922F','005A95A1','0077780E','00777CD6','00777D7E','006675B0','006677B3','0066BAA3','0066CFDC')) {
    $t3[[Convert]::ToUInt32($a,16)] = $true
}

$raw = [System.IO.File]::ReadAllText($probe)
$lines = $raw -split "`n"
$c2 = 0; $c3 = 0
for ($i=1; $i -lt $lines.Length; $i++) {
    if ($lines[$i] -eq '') { continue }
    $c = $lines[$i] -split "`t"
    $v = [Convert]::ToUInt32($c[0],16)
    if ($t2.ContainsKey($v) -and $c[4] -eq '[已证]') {
        "T2 $($c[0]) $($c[3]): [已证] -> $($t2[$v])"
        $c[4] = $t2[$v]
        $lines[$i] = $c -join "`t"
        $c2++
    } elseif ($t3.ContainsKey($v) -and $c[4] -eq '已证') {
        "T3 $($c[0]) $($c[3]): 已证 -> [已证]"
        $c[4] = '[已证]'
        $lines[$i] = $c -join "`t"
        $c3++
    }
}
if ($c2 -ne 10) { throw "expected 10 T2 changes got $c2" }
if ($c3 -ne 15) { throw "expected 15 T3 changes got $c3" }
[System.IO.File]::WriteAllText($probe, ([string]::Join("`n",$lines)), (New-Object System.Text.UTF8Encoding($false)))
$bytes = [System.IO.File]::ReadAllBytes($probe)
$lf=0; $crlf=0
for ($i=0;$i -lt $bytes.Length;$i++){ if($bytes[$i] -eq 10){$lf++; if($i -gt 0 -and $bytes[$i-1] -eq 13){$crlf++}} }
"probe bytes=$($bytes.Length) LF=$lf CRLF=$crlf  T2=$c2 T3=$c3"
