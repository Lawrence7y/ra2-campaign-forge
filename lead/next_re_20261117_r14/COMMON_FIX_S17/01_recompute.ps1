$ErrorActionPreference = 'Stop'
$cov = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\COVERAGE\coverage.tsv'
$atl = 'D:\Project\ra2-campaign-forge\lead\next_re_20261112_r10\W130_atlas\function_atlas.tsv'

$lines  = Get-Content $cov
$header = $lines[0]
$body   = $lines[1..($lines.Count - 1)]
Write-Output ("[COV] header : " + $header)
Write-Output ("[COV] data rows = " + $body.Count)

$atlasEntries = New-Object 'System.Collections.Generic.HashSet[string]'
$atlasRows = 0
Get-Content $atl | Select-Object -Skip 1 | ForEach-Object {
    $atlasRows++
    [void]$atlasEntries.Add((($_ -split "`t")[0]).ToLower())
}
Write-Output ("[ATL] data rows = " + $atlasRows + " ; unique entry set = " + $atlasEntries.Count)
Write-Output "[ATL] entry column is lowercase hex in file; comparison normalized to lowercase on both sides."
Write-Output ""

$s17 = @()
foreach ($l in $body) { $f = $l -split "`t"; if ($f[1] -eq 'S17') { $s17 += , $f } }
$inA = @(); $outA = @()
foreach ($f in $s17) { if ($atlasEntries.Contains($f[0].ToLower())) { $inA += , $f } else { $outA += , $f } }

Write-Output ("[S17] coverage rows with subsystem==S17 (all) = " + $s17.Count)
Write-Output ("[S17] ... of which entry in atlas            = " + $inA.Count + "   <= n")
Write-Output ("[S17] ... of which entry NOT in atlas        = " + $outA.Count)
foreach ($f in $outA) { Write-Output ("      outside-atlas: " + $f[0] + "  name=" + $f[2] + "  grade=" + $f[4]) }
Write-Output ""

$n        = $inA.Count
$empty    = @($inA | Where-Object { ([string]$_[2]).Trim() -eq '' })
$subForm  = @($inA | Where-Object { $_[2] -match '^sub_[0-9A-Fa-f]+$' })
$composite= @($inA | Where-Object { $_[2] -match '::sub_[0-9A-Fa-f]+$' })
$slotForm = @($inA | Where-Object { $_[2] -match '(?i)slot\d+' })
$namedL   = @($inA | Where-Object { ([string]$_[2]).Trim() -ne '' -and $_[2] -notmatch '^sub_[0-9A-Fa-f]+$' })
$namedS   = @($namedL | Where-Object { $_[2] -notmatch '::sub_[0-9A-Fa-f]+$' })
$namedSt  = @($namedS | Where-Object { $_[2] -notmatch '(?i)slot\d+' })
$thr = [math]::Ceiling(0.9 * $n)

Write-Output "---- metric recompute (named_L / named_S(R14) / named_strict) ----"
Write-Output ("n                                    = " + $n)
Write-Output ("name empty                           = " + $empty.Count)
Write-Output ("sub_ form  ^sub_[0-9A-Fa-f]+$        = " + $subForm.Count)
Write-Output ("::sub_ composite (excluded by S)     = " + $composite.Count)
Write-Output ("slotN form (counted in L and S)      = " + $slotForm.Count)
Write-Output ("named_L         = " + $namedL.Count + " / " + $n)
Write-Output ("named_S(R14)    = " + $namedS.Count + " / " + $n)
Write-Output ("named_strict    = " + $namedSt.Count + " / " + $n)
Write-Output ("threshold ceil(0.9*n)                = " + $thr)
Write-Output ("margin named_S(R14) = " + ($namedS.Count - $thr) + " ; margin named_strict = " + ($namedSt.Count - $thr))
Write-Output ("pct named_S(R14) = " + [math]::Round(100.0 * $namedS.Count / $n, 2) + "%")
Write-Output ("pct named_strict = " + [math]::Round(100.0 * $namedSt.Count / $n, 2) + "%")
Write-Output ""
Write-Output "---- the 8 sub_ form rows (still unnamed) ----"
foreach ($f in $subForm) { Write-Output ("  " + $f[0] + "`t" + $f[2]) }
Write-Output ""
Write-Output "---- M56 merged rows present on disk? ----"
foreach ($e in @('006CF430', '004A2990', '006CF240')) {
    $hit = @($body | Where-Object { ($_ -split "`t")[0] -eq $e })
    foreach ($h in $hit) {
        $f = $h -split "`t"
        Write-Output ("  " + $f[0] + "  sub=" + $f[1] + "  name=" + $f[2] + "  grade=" + $f[4])
    }
    if ($hit.Count -eq 0) { Write-Output ("  " + $e + "  <absent>") }
}
