param(
    [Parameter(Mandatory=$true)][string]$Root,
    [Parameter(Mandatory=$true)][string]$Out
)
# Snapshot every file under $Root: "sha256  size  relative-path", sorted by path.
$rootFull = (Resolve-Path -LiteralPath $Root).Path.TrimEnd('\')
$files = Get-ChildItem -LiteralPath $rootFull -Recurse -File -Force | Sort-Object FullName
$lines = foreach ($f in $files) {
    $rel = $f.FullName.Substring($rootFull.Length).TrimStart('\')
    $sha = (Get-FileHash -LiteralPath $f.FullName -Algorithm SHA256).Hash.ToLower()
    '{0}  {1,8}  {2}' -f $sha, $f.Length, $rel
}
$lines | Set-Content -LiteralPath $Out -Encoding utf8
Write-Output "snapshot written: $Out ($($lines.Count) files)"
