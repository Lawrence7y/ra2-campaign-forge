# R44-T2-EVID Q5 positive control: PowerShell independent implementation
$ErrorActionPreference = 'Stop'
$tsv = 'D:\Project\ra2-campaign-forge\lead\next_re_20261117_r14\R17_R78_T1_RECLASS\files_excluded_prime.tsv'
$rows = Import-Csv -LiteralPath $tsv -Delimiter "`t" -Encoding UTF8
$ue = @($rows | Where-Object { $_.label -eq 'UNDECIDED' -and $_.rel -match '(?i)evidence' })
Write-Output ("TOTAL=" + $ue.Count)
$g = @{ stdout=0; stderr=0; _out=0; report=0; result=0; OTHER=0 }
foreach ($r in $ue) {
  $bn = [System.IO.Path]::GetFileName($r.rel).ToLowerInvariant()
  if ($bn.Contains('stdout'))      { $g.stdout += 1 }
  elseif ($bn.Contains('stderr'))  { $g.stderr += 1 }
  elseif ($bn.Contains('_out'))    { $g._out += 1 }
  elseif ($bn.Contains('report'))  { $g.report += 1 }
  elseif ($bn.Contains('result'))  { $g.result += 1 }
  else                             { $g.OTHER += 1 }
}
foreach ($k in @('stdout','stderr','_out','report','result','OTHER')) {
  Write-Output ("{0}={1}" -f $k, $g[$k])
}
