$ErrorActionPreference='Stop'
$p="D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R72_T1_CLEANSCALE"
$a=Import-Csv (Join-Path $p "files_tier_A_snap2.tsv") -Delimiter "`t"
$c=Import-Csv (Join-Path $p "files_tier_C.tsv") -Delimiter "`t"

"=== [T0] baselines ==="
$ab=($a|Measure-Object bytes -Sum).Sum
$cb=($c|Measure-Object bytes -Sum).Sum
"A rows=$($a.Count) bytes=$ab"
"C rows=$($c.Count) bytes=$cb"
"excluded(baseline) = $($a.Count - $c.Count) / $($ab - $cb)"

"=== [T1] F24 cited self-documents present in tier C ==="
$cmap=@{}
foreach($r in $c){ $cmap[$r.rel]=$r.bytes }
$cands = @(
 "next_re_20261117_r14/R14_COMMON.md",
 "next_re_20261117_r14/STATUS_BOARD.md",
 "next_re_20261117_r14/BOARD_ARCHIVE.md",
 "next_re_20261117_r14/R16_AUDIT_EVID675/VERDICT.md",
 "next_re_20261117_r14/R17_DELIVERY/DELIVERY_SUMMARY.md"
)
foreach($x in $cands){ if($cmap.ContainsKey($x)){"IN-C     $x  $($cmap[$x]) B"} else {"NOT-IN-C $x"} }

"=== [T2] rollback/backup pattern rows STILL in tier C (rx identical to band_c_wide.py) ==="
$rxb=[regex]'(_before_|\.before|before_|_bak|backup/)'
$inCb=0; $inCn=0
foreach($r in $c){ if($rxb.IsMatch($r.rel)){ $inCn++; $inCb+=[int]$r.bytes } }
"rollback-pattern IN C: $inCn / $inCb B"

"=== [T3] Q5 four numbers ==="
$r5n=0; $r5b=0
foreach($r in $a){ if($r.selfkind -match 'C5_report_md'){ $r5n++; $r5b+=[int]$r.bytes } }
"+72 report: $r5n / $r5b B"
"ORIG = $($c.Count) / $cb"
"V1   = $($c.Count + $r5n) / $($cb + $r5b)"
"V2   = $($c.Count - $inCn) / $($cb - $inCb)"
"BOTH = $($c.Count + $r5n - $inCn) / $($cb + $r5b - $inCb)"
