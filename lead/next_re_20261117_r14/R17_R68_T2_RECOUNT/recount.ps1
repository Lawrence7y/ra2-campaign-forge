# R37-T2-RECOUNT / recount.ps1
# 只读源文件；不写任何产物。与 recount.py 互为第二独立读法。
$base = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'

function Buckets($path, $col) {
    $lines = Get-Content -LiteralPath $path
    $data = $lines[1..($lines.Count - 1)] | Where-Object { $_ -ne '' }
    $cnt = @{}
    foreach ($ln in $data) { $f = $ln -split "`t"; $k = $f[$col]; $cnt[$k] = 1 + [int]$cnt[$k] }
    return ,$data, $cnt
}

# Q1: R19 reconcile.tsv (header class_name/bucket/note)
$_, $c = Buckets "$base\R17_R19_RTTI_XCHECK\reconcile.tsv" 1
"Q1 reconcile.tsv bucket: BOTH=$($c['BOTH']) COVERAGE_ONLY=$($c['COVERAGE_ONLY']) RTTI_ONLY=$($c['RTTI_ONLY']) sum=$((($c.Values | Measure-Object -Sum).Sum))"

# Q1b/Q2: R24 reconcile_final.tsv (S_bucket col2, S_mechanism col3, C_bucket col4)
$_, $s  = Buckets "$base\R17_R24_RECON_FINAL\reconcile_final.tsv" 2
$_, $cb = Buckets "$base\R17_R24_RECON_FINAL\reconcile_final.tsv" 4
"Q1b S_bucket: BOTH=$($s['BOTH']) COVERAGE_ONLY=$($s['COVERAGE_ONLY'])"
"Q2  C_bucket: BOTH=$($cb['BOTH']) COVERAGE_ONLY=$($cb['COVERAGE_ONLY'])"

# Q5 法B: S BOTH 按 S_mechanism 分组求和
$mech = @{}
$data = (Get-Content -LiteralPath "$base\R17_R24_RECON_FINAL\reconcile_final.tsv")[1..429]
foreach ($ln in $data) { $f = $ln -split "`t"; if ($f[2] -eq 'BOTH') { $mech[$f[3]] = 1 + [int]$mech[$f[3]] } }
"Q5 法B S_mechanism(BOTH): $(($mech.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join ' ') sum=$((($mech.Values | Measure-Object -Sum).Sum))"

# Q3: reverse_map.tsv 0x004264C0
$rm = (Get-Content -LiteralPath "$base\R17_R17_SLOT73_MAP\reverse_map.tsv")[1..42]
$all = @($rm | Where-Object { ($_ -split "`t")[0] -eq '0x004264C0' })
$s107 = @($all | Where-Object { ($_ -split "`t")[3] -eq '107' })
"Q3 0x004264C0: allslot=$($all.Count) classes=$(@($all | ForEach-Object { ($_ -split "`t")[1] } | Sort-Object -Unique).Count) @107=$($s107.Count) classes@107=$(@($s107 | ForEach-Object { ($_ -split "`t")[1] } | Sort-Object -Unique).Count)"
