# R42-T2-DRIFT main analysis (PowerShell, read-only on lead\; writes only into R17_R75_T2_DRIFT\)
# Source columns: rel, ext, bytes, mtime_ns [, selfkind]
$ErrorActionPreference = 'Stop'
$base = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
$fOld = Join-Path $base 'R17_R70_T1_REPRO\files_scale_today.tsv'
$fNew = Join-Path $base 'R17_R72_T1_CLEANSCALE\files_tier_A_snap2.tsv'
$out  = Join-Path $base 'R17_R75_T2_DRIFT'

function Get-Sum([object[]]$rows, [string]$prop) {
    [long]$s = 0
    foreach ($r in $rows) { $s += [long]($r.$prop) }
    return $s
}

$oldRows = Import-Csv -Path $fOld -Delimiter "`t" -Encoding UTF8
$newRows = Import-Csv -Path $fNew -Delimiter "`t" -Encoding UTF8

$old = @{}; $new = @{}
foreach ($r in $oldRows) { $old[$r.rel] = $r }
foreach ($r in $newRows) { $new[$r.rel] = $r }

$onlyA   = New-Object System.Collections.Generic.List[object]
$onlyOld = New-Object System.Collections.Generic.List[object]
$changed = New-Object System.Collections.Generic.List[object]
[long]$common = 0

foreach ($rel in $new.Keys) {
    $nr = $new[$rel]
    if (-not $old.ContainsKey($rel)) {
        $onlyA.Add([pscustomobject]@{ rel=$rel; ext=$nr.ext; bytes=[long]$nr.bytes; mtime_ns=[long]$nr.mtime_ns; selfkind=$nr.selfkind })
    } else {
        $common++
        $orr = $old[$rel]
        if ([long]$orr.bytes -ne [long]$nr.bytes) {
            $changed.Add([pscustomobject]@{ rel=$rel; old_bytes=[long]$orr.bytes; new_bytes=[long]$nr.bytes; delta=([long]$nr.bytes-[long]$orr.bytes); old_mtime_ns=[long]$orr.mtime_ns; new_mtime_ns=[long]$nr.mtime_ns; selfkind=$nr.selfkind })
        }
    }
}
foreach ($rel in $old.Keys) {
    if (-not $new.ContainsKey($rel)) {
        $orr = $old[$rel]
        $onlyOld.Add([pscustomobject]@{ rel=$rel; ext=$orr.ext; bytes=[long]$orr.bytes; mtime_ns=[long]$orr.mtime_ns })
    }
}

# Interval in Unix ns from snapshot file mtimes: 03:55:10Z -> 04:31:10Z on 2026-11-22
$t0 = ([DateTimeOffset]::Parse('2026-11-22T03:55:10Z').ToUnixTimeSeconds()) * 1000000000L
$t1 = ([DateTimeOffset]::Parse('2026-11-22T04:31:10Z').ToUnixTimeSeconds()) * 1000000000L
$newInInterval = 0
foreach ($r in $onlyA) { if ($r.mtime_ns -ge $t0 -and $r.mtime_ns -le $t1) { $newInInterval++ } }

$onlyAArr   = $onlyA.ToArray()
$onlyOldArr = $onlyOld.ToArray()
$changedArr = $changed.ToArray()

$onlyAArr   | Sort-Object rel | Export-Csv -Path (Join-Path $out 'q1_onlyA.tsv')   -Delimiter "`t" -NoTypeInformation -Encoding UTF8
$onlyOldArr | Sort-Object rel | Export-Csv -Path (Join-Path $out 'q1_onlyOld.tsv') -Delimiter "`t" -NoTypeInformation -Encoding UTF8
$changedArr | Sort-Object rel | Export-Csv -Path (Join-Path $out 'q1_changed.tsv') -Delimiter "`t" -NoTypeInformation -Encoding UTF8

$lines = @()
$lines += "METRIC`tVALUE`tSOURCE`tCOLUMN`tSCRIPT"
$lines += "old_rows`t$($oldRows.Count)`tfiles_scale_today.tsv`t(rel)`tanalyze.ps1"
$lines += "new_rows`t$($newRows.Count)`tfiles_tier_A_snap2.tsv`t(rel)`tanalyze.ps1"
$lines += "old_total_bytes`t$(Get-Sum $oldRows 'bytes')`tfiles_scale_today.tsv`tbytes`tanalyze.ps1"
$lines += "new_total_bytes`t$(Get-Sum $newRows 'bytes')`tfiles_tier_A_snap2.tsv`tbytes`tanalyze.ps1"
$lines += "distinct_rel_old`t$($old.Count)`tfiles_scale_today.tsv`trel`tanalyze.ps1"
$lines += "distinct_rel_new`t$($new.Count)`tfiles_tier_A_snap2.tsv`trel`tanalyze.ps1"
$lines += "common_rel`t$common`tBOTH`trel`tanalyze.ps1"
$lines += "Q1_onlyA_count`t$($onlyAArr.Count)`tBOTH(rel join)`trel/bytes`tanalyze.ps1"
$lines += "Q1_onlyA_bytes`t$(Get-Sum $onlyAArr 'bytes')`tfiles_tier_A_snap2.tsv`tbytes`tanalyze.ps1"
$lines += "Q1_onlyOld_count`t$($onlyOldArr.Count)`tBOTH(rel join)`trel/bytes`tanalyze.ps1"
$lines += "Q1_onlyOld_bytes`t$(Get-Sum $onlyOldArr 'bytes')`tfiles_scale_today.tsv`tbytes`tanalyze.ps1"
$lines += "Q1_changed_count`t$($changedArr.Count)`tBOTH(rel join)`tbytes`tanalyze.ps1"
$lines += "Q1_changed_old_bytes`t$(Get-Sum $changedArr 'old_bytes')`tfiles_scale_today.tsv`tbytes`tanalyze.ps1"
$lines += "Q1_changed_new_bytes`t$(Get-Sum $changedArr 'new_bytes')`tfiles_tier_A_snap2.tsv`tbytes`tanalyze.ps1"
$lines += "Q1_changed_delta_bytes`t$(Get-Sum $changedArr 'delta')`tBOTH`tdelta=new-old`tanalyze.ps1"
$lines += "Q1_onlyA_mtime_in_interval`t$newInInterval`ttier_A_snap2.tsv`tmtime_ns`tanalyze.ps1"
$lines += "Q1_interval_t0_ns`t$t0`tsnapshot_mtime`tmtime_ns`tanalyze.ps1"
$lines += "Q1_interval_t1_ns`t$t1`tsnapshot_mtime`tmtime_ns`tanalyze.ps1"
$lines | Set-Content -Path (Join-Path $out 'summary.tsv') -Encoding UTF8
$lines | ForEach-Object { Write-Output $_ }
