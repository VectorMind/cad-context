param([Parameter(Mandatory=$true)][string]$PublicationRoot,[Parameter(Mandatory=$true)][string]$CacheRoot)
$ErrorActionPreference='Stop'
$pub=(Resolve-Path -LiteralPath $PublicationRoot).Path.TrimEnd('\')
$cache=(Resolve-Path -LiteralPath $CacheRoot).Path.TrimEnd('\')
if ((Split-Path $cache -Leaf) -ne '.cache' -or -not (Test-Path -LiteralPath (Join-Path (Split-Path $cache -Parent) 'pyproject.toml'))) {throw 'Not the workbench cache'}
$sourceManifest=Get-Content -LiteralPath (Join-Path $pub 'reference/source.json') -Raw | ConvertFrom-Json
$webManifest=Get-Content -LiteralPath (Join-Path $pub 'web/latest/manifest.json') -Raw | ConvertFrom-Json
$proof=Get-Content -LiteralPath (Join-Path $cache 'projects/animal-puzzle/rebuild.json') -Raw | ConvertFrom-Json
if ($sourceManifest.project_id -ne 'animal-puzzle' -or -not $proof.verified -or $sourceManifest.source_identity -ne $proof.source_identity -or $webManifest.source_identity -ne $proof.source_identity) {throw 'Publication/recovery proof does not match working source'}
$archiveHash=(Get-FileHash -LiteralPath (Join-Path $pub 'reference/source.zip') -Algorithm SHA256).Hash.ToLowerInvariant()
if ($archiveHash -ne $sourceManifest.archive_sha256) {throw 'Source archive checksum mismatch'}
$release=Join-Path $pub '3d-print/2026-10-25'
$releaseManifest=Get-Content -LiteralPath (Join-Path $release 'release.json') -Raw | ConvertFrom-Json
foreach($entry in $releaseManifest.files.PSObject.Properties) {
 if ([System.IO.Path]::GetFileName($entry.Name) -ne $entry.Name) {throw 'Invalid release path'}
 if ((Get-FileHash -LiteralPath (Join-Path $release $entry.Name) -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) {throw 'Legacy package changed'}
}
function Assert-Child([string]$Path,[string]$Root) {
 $full=[System.IO.Path]::GetFullPath($Path)
 if (-not $full.StartsWith($Root+[System.IO.Path]::DirectorySeparatorChar,[System.StringComparison]::OrdinalIgnoreCase)) {throw "Refusing out-of-scope removal: $full"}
 return $full
}
# Audit every final target before any deletion. Dependency environments are retained.
$pubTargets=@(Get-ChildItem -LiteralPath $pub -Force | Where-Object {$_.Name -notin @('web','reference','3d-print','README-publication.md','README.md','desktop.ini')} | ForEach-Object {Assert-Child $_.FullName $pub})
$cacheTargets=@()
foreach($name in @('cad','recovery-validation')) {if(Test-Path -LiteralPath (Join-Path $cache $name)) {$cacheTargets += Assert-Child (Join-Path $cache $name) $cache}}
$scratch=Join-Path $cache 'scratch'
foreach($entry in Get-ChildItem -LiteralPath $scratch -Force) {
 if($entry.PSIsContainer -and (Test-Path -LiteralPath (Join-Path $entry.FullName 'pyvenv.cfg'))) {continue}
 $cacheTargets += Assert-Child $entry.FullName $cache
}
$flatPrintTargets=@(Get-ChildItem -LiteralPath (Join-Path $pub '3d-print') -File -Force | ForEach-Object {Assert-Child $_.FullName $pub})
foreach($file in $flatPrintTargets) {
 if([System.IO.Path]::GetExtension($file) -eq '.3mf') {
  $name=[System.IO.Path]::GetFileName($file)
  if((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ne (Get-FileHash -LiteralPath (Join-Path $release $name) -Algorithm SHA256).Hash) {throw 'Flat print not safely archived'}
 }
}
if(Test-Path -LiteralPath (Join-Path $pub '3d-print/README.md')) {Copy-Item -LiteralPath (Join-Path $pub '3d-print/README.md') -Destination (Join-Path $release 'README.md') -Force}
Copy-Item -LiteralPath (Join-Path $pub 'README-publication.md') -Destination (Join-Path $pub 'README.md') -Force
$summary=@{source_identity=$proof.source_identity;source_archive_verified=$true;publication_targets=$pubTargets;cache_targets=$cacheTargets;legacy_print_files_preserved=@($releaseManifest.files.PSObject.Properties).Count;new_print_release_created=$false}
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $pub 'reference/storage-migration.json')
foreach($target in $pubTargets) {Remove-Item -LiteralPath $target -Recurse -Force}
foreach($target in $flatPrintTargets) {Remove-Item -LiteralPath $target -Force}
Remove-Item -LiteralPath (Join-Path $pub 'README-publication.md') -Force
foreach($target in $cacheTargets) {Remove-Item -LiteralPath $target -Recurse -Force}
# Keep only current project command summaries and final validation logs.
Get-ChildItem -LiteralPath (Join-Path $cache 'results') -File | Where-Object {$_.Name -notmatch '^(verify-animal-puzzle-|generate-animal-puzzle-|project-|info\.|generators\.|paths\.|web\.|last\.|storage-)'} | ForEach-Object {Remove-Item -LiteralPath (Assert-Child $_.FullName $cache) -Force}
Get-ChildItem -LiteralPath (Join-Path $cache 'reports') -File | Where-Object {$_.Name -notin @('web.log','publication-pytest-final.log','publication-contract-tests.log','publication-web-validation.log')} | ForEach-Object {Remove-Item -LiteralPath (Assert-Child $_.FullName $cache) -Force}
$summary | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $cache 'results/storage-migration.json')
Write-Output 'Removed obsolete Drive source/work exports and cache experiments; source snapshot and frozen print packages verified first.'

