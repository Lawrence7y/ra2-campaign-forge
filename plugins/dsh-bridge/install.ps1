param([string]$MarketplaceRoot = (Join-Path $env:USERPROFILE 'dsh-bridge-marketplace'))
$ErrorActionPreference = 'Stop'
$pluginSource = $PSScriptRoot
$pluginDestination = Join-Path $MarketplaceRoot 'plugins\dsh-bridge'
New-Item -ItemType Directory -Force -Path $pluginDestination | Out-Null
Get-ChildItem -LiteralPath $pluginSource -Force | Where-Object { $_.Name -ne '__pycache__' } |
    Copy-Item -Destination $pluginDestination -Recurse -Force
$catalogDirectory = Join-Path $MarketplaceRoot '.agents\plugins'
New-Item -ItemType Directory -Force -Path $catalogDirectory | Out-Null
$catalogPath = Join-Path $catalogDirectory 'marketplace.json'
if (Test-Path -LiteralPath $catalogPath) {
    $catalog = Get-Content -LiteralPath $catalogPath -Raw | ConvertFrom-Json
    if ($catalog.name -ne 'dsh-local-bridge') { throw 'Marketplace name mismatch; existing data preserved.' }
    Copy-Item -LiteralPath $catalogPath -Destination ($catalogPath + '.bak-' + (Get-Date -Format 'yyyyMMdd-HHmmss'))
} else {
    $catalog = [pscustomobject]@{ name = 'dsh-local-bridge'; interface = @{ displayName = 'DSH Bridge Local' }; plugins = @() }
}
if (@($catalog.plugins | Where-Object { $_.name -eq 'dsh-bridge' }).Count -eq 0) {
    $catalog.plugins = @($catalog.plugins) + @(@{
        name = 'dsh-bridge'; source = @{ source = 'local'; path = './plugins/dsh-bridge' }
        policy = @{ installation = 'AVAILABLE'; authentication = 'ON_INSTALL' }; category = 'Productivity'
    })
}
[System.IO.File]::WriteAllText($catalogPath, ($catalog | ConvertTo-Json -Depth 20), [System.Text.UTF8Encoding]::new($false))
$codexCandidates = @(Get-ChildItem -Path (Join-Path $env:LOCALAPPDATA 'OpenAI\Codex\bin\*\codex.exe') | Sort-Object LastWriteTime -Descending)
if ($codexCandidates.Count -eq 0) { throw 'Codex CLI not found; plugin source preserved.' }
$codexExe = $codexCandidates[0].FullName
$listed = & $codexExe plugin marketplace list --json
if ($LASTEXITCODE -ne 0) { throw 'Cannot read marketplaces.' }
$registered = $listed | ConvertFrom-Json
if (@($registered.marketplaces | Where-Object { $_.root -eq $MarketplaceRoot }).Count -eq 0) {
    & $codexExe plugin marketplace add $MarketplaceRoot
    if ($LASTEXITCODE -ne 0) { throw 'Marketplace registration failed.' }
}
& $codexExe plugin add 'dsh-bridge@dsh-local-bridge' --json
if ($LASTEXITCODE -ne 0) { throw 'Plugin installation failed; source preserved.' }
Write-Host 'Installed. Refresh plugins or open a new chat to discover dsh_* tools.'
