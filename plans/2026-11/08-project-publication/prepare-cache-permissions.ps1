param([Parameter(Mandatory=$true)][string]$CacheRoot,[Parameter(Mandatory=$true)][string]$CleanupAccount)
$ErrorActionPreference='Stop'
$root=(Resolve-Path -LiteralPath $CacheRoot).Path.TrimEnd('\')
if((Split-Path $root -Leaf) -ne '.cache') {throw 'Not cache'}
$targets=@((Join-Path $root 'scratch'))
$targets+=@(Get-ChildItem -LiteralPath (Join-Path $root 'scratch') -Directory -Force | Where-Object {-not(Test-Path -LiteralPath (Join-Path $_.FullName 'pyvenv.cfg'))} | ForEach-Object {$_.FullName})
foreach($path in $targets) {
 $full=[System.IO.Path]::GetFullPath($path)
 if(-not $full.StartsWith($root+[System.IO.Path]::DirectorySeparatorChar,[System.StringComparison]::OrdinalIgnoreCase)) {throw 'Out of scope'}
 try {
  $old=Get-Acl -LiteralPath $full -ErrorAction Stop
  $security=New-Object System.Security.AccessControl.DirectorySecurity
  foreach($rule in $old.Access) {$null=$security.AddAccessRule($rule)}
  $null=$security.AddAccessRule((New-Object System.Security.AccessControl.FileSystemAccessRule($CleanupAccount,'FullControl','ContainerInherit,ObjectInherit','None','Allow')))
  $directory=New-Object System.IO.DirectoryInfo($full)
  $directory.SetAccessControl($security)
 } catch {Write-Output "Owned by other account; leave its existing permissions: $full"}
}
