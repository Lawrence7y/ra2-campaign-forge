param(
    [Parameter(Mandatory=$true)][string]$A,
    [Parameter(Mandatory=$true)][string]$B
)
# Unified diff of two snapshot files; exit code 1 when different, 0 when identical.
$la = Get-Content -LiteralPath $A
$lb = Get-Content -LiteralPath $B
$diff = Compare-Object -ReferenceObject $la -DifferenceObject $lb
if (-not $diff) {
    Write-Output "IDENTICAL: $A == $B"
    exit 0
}
Write-Output "DIFFER: $A vs $B"
$diff | Sort-Object { $_.InputObject -replace '^[0-9a-f]+\s+\d+\s+', '' }, @{e={$_.SideIndicator}} |
    ForEach-Object { '{0} {1}' -f ($_.SideIndicator -replace '<','ONLY-IN-A:' -replace '>','ONLY-IN-B:'), $_.InputObject }
exit 1
