# R42-T2-DRIFT classification for Q2/Q3 and Q4 decomposition
# Reads only intermediate lists produced by analyze.ps1 from the two source TSVs.
$ErrorActionPreference = 'Stop'
$base = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14'
$out  = Join-Path $base 'R17_R75_T2_DRIFT'

function Get-Sum([object[]]$rows, [string]$prop) {
    [long]$s = 0
    foreach ($r in $rows) { $s += [long]($r.$prop) }
    return $s
}

# ---------- Q2: classify the 47 added files ----------
$newRows = Import-Csv -Path (Join-Path $out 'q1_onlyA.tsv') -Delimiter "`t" -Encoding UTF8
$q2 = New-Object System.Collections.Generic.List[object]
foreach ($r in $newRows) {
    $rel = $r.rel; $b = [long]$r.bytes; $sk = $r.selfkind; $cat = ''; $rule = ''
    if ($sk -ne '') {
        $cat = 'SELF'; $rule = "selfkind=$sk"
    } elseif ($rel -match '\.log$' -or
              $rel -match 'R17_LEAD_BASELINE/.*\.before_' -or
              $rel -match 'SUPERSEDED\.md$' -or
              $rel -match '(python_re_probe|readback_check_today)\.json$' -or
              $rel -match '(detour_ascii_strings|anchor_check)\.txt$' -or
              $rel -match 'FACT_INDEX\.tsv$') {
        $cat = 'SELF'; $rule = 'filename-pattern'
    } elseif ($rel -match '_cards/R40-.*\.md$' -or
              $rel -match '/REPORT\.md$' -or
              $rel -match '/(CHANGES|README)\.md$') {
        $cat = 'FACT'; $rule = 'doc-pattern'
    } else {
        $cat = 'UNKNOWN'; $rule = 'none'
    }
    $q2.Add([pscustomobject]@{ rel=$rel; bytes=$b; selfkind=$sk; category=$cat; rule=$rule })
}
$q2Arr = $q2.ToArray()
$q2Arr | Sort-Object rel | Export-Csv -Path (Join-Path $out 'q2_classification.tsv') -Delimiter "`t" -NoTypeInformation -Encoding UTF8

$selfNew  = @($q2Arr | Where-Object category -eq 'SELF')
$factNew  = @($q2Arr | Where-Object category -eq 'FACT')
$unkNew   = @($q2Arr | Where-Object category -eq 'UNKNOWN')

# ---------- Q3: classify the 5 rewritten files ----------
$chgRows = Import-Csv -Path (Join-Path $out 'q1_changed.tsv') -Delimiter "`t" -Encoding UTF8
$q3 = New-Object System.Collections.Generic.List[object]
foreach ($r in $chgRows) {
    $rel = $r.rel; $delta = [long]$r.delta; $sk = $r.selfkind; $cat = ''; $rule = ''
    if ($sk -ne '') {
        $cat = 'SELF'; $rule = "selfkind=$sk"
    } elseif ($rel -match '^(GOAL_THREE_TARGETS_20261018\.md|next_re_20261117_r14/(BOARD_ARCHIVE|R14_COMMON|STATUS_BOARD)\.md)$') {
        $cat = 'FACT'; $rule = 'ledger/board/common-doc'
    } else {
        $cat = 'UNKNOWN'; $rule = 'none'
    }
    $q3.Add([pscustomobject]@{ rel=$rel; old_bytes=[long]$r.old_bytes; new_bytes=[long]$r.new_bytes; delta=$delta; selfkind=$sk; category=$cat; rule=$rule })
}
$q3Arr = $q3.ToArray()
$q3Arr | Sort-Object rel | Export-Csv -Path (Join-Path $out 'q3_classification.tsv') -Delimiter "`t" -NoTypeInformation -Encoding UTF8

$selfChg = @($q3Arr | Where-Object category -eq 'SELF')
$factChg = @($q3Arr | Where-Object category -eq 'FACT')
$unkChg  = @($q3Arr | Where-Object category -eq 'UNKNOWN')

# ---------- Q4 decomposition ----------
$selfFiles = $selfNew.Count + $selfChg.Count
$selfBytes = (Get-Sum $selfNew 'bytes') + (Get-Sum $selfChg 'delta')
$factFiles = $factNew.Count + $factChg.Count
$factBytes = (Get-Sum $factNew 'bytes') + (Get-Sum $factChg 'delta')
$unkFiles  = $unkNew.Count + $unkChg.Count
$unkBytes  = (Get-Sum $unkNew 'bytes') + (Get-Sum $unkChg 'delta')

$lines = @()
$lines += "METRIC`tVALUE`tSOURCE`tCOLUMN`tSCRIPT"
$lines += "Q2_selfNew_count`t$($selfNew.Count)`tq1_onlyA.tsv`tselfkind+filename`tscript:classify.ps1"
$lines += "Q2_selfNew_bytes`t$(Get-Sum $selfNew 'bytes')`tq1_onlyA.tsv`tbytes`tscript:classify.ps1"
$lines += "Q2_factNew_count`t$($factNew.Count)`tq1_onlyA.tsv`tselfkind+filename`tscript:classify.ps1"
$lines += "Q2_factNew_bytes`t$(Get-Sum $factNew 'bytes')`tq1_onlyA.tsv`tbytes`tscript:classify.ps1"
$lines += "Q2_unknownNew_count`t$($unkNew.Count)`tq1_onlyA.tsv`tselfkind+filename`tscript:classify.ps1"
$lines += "Q2_unknownNew_bytes`t$(Get-Sum $unkNew 'bytes')`tq1_onlyA.tsv`tbytes`tscript:classify.ps1"
$lines += "Q3_selfChg_count`t$($selfChg.Count)`tq1_changed.tsv`tselfkind+path`tscript:classify.ps1"
$lines += "Q3_selfChg_delta`t$(Get-Sum $selfChg 'delta')`tq1_changed.tsv`tdelta`tscript:classify.ps1"
$lines += "Q3_factChg_count`t$($factChg.Count)`tq1_changed.tsv`tselfkind+path`tscript:classify.ps1"
$lines += "Q3_factChg_delta`t$(Get-Sum $factChg 'delta')`tq1_changed.tsv`tdelta`tscript:classify.ps1"
$lines += "Q3_unknownChg_count`t$($unkChg.Count)`tq1_changed.tsv`tselfkind+path`tscript:classify.ps1"
$lines += "Q4_self_files`t$selfFiles`tQ2+Q3`tscript:classify.ps1"
$lines += "Q4_self_bytes_net`t$selfBytes`tQ2+Q3`tscript:classify.ps1"
$lines += "Q4_fact_files`t$factFiles`tQ2+Q3`tscript:classify.ps1"
$lines += "Q4_fact_bytes_net`t$factBytes`tQ2+Q3`tscript:classify.ps1"
$lines += "Q4_unknown_files`t$unkFiles`tQ2+Q3`tscript:classify.ps1"
$lines += "Q4_unknown_bytes_net`t$unkBytes`tQ2+Q3`tscript:classify.ps1"
$lines += "Q4_check_sum`t$($selfBytes+$factBytes+$unkBytes)`tQ2+Q3`tmust equal 3537570`tscript:classify.ps1"
$lines | Set-Content -Path (Join-Path $out 'q2q3q4_summary.tsv') -Encoding UTF8
$lines | ForEach-Object { Write-Output $_ }
