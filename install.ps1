param([string]$Destination)
$ErrorActionPreference='Stop'
$source=Join-Path $PSScriptRoot 'skills/codex-mcp-memory'
if(-not $Destination){
 $base=if($env:CODEX_HOME){$env:CODEX_HOME}else{Join-Path $env:USERPROFILE '.codex'}
 $Destination=Join-Path $base 'skills/codex-mcp-memory'
}
$target=[IO.Path]::GetFullPath($Destination)
if(Test-Path -LiteralPath $target){throw 'Destination exists. Preserve local adaptations; use a new destination or a reviewed upgrade. No files changed.'}
if(-not (Test-Path -LiteralPath (Join-Path $source 'SKILL.md'))){throw 'Skill source missing'}
$items=@(Get-ChildItem -LiteralPath $source -Force -Recurse)
if(@($items|Where-Object {$_.Attributes -band [IO.FileAttributes]::ReparsePoint}).Count){throw 'Refusing reparse points in skill package'}
$parent=Split-Path -Parent $target
if(-not (Test-Path -LiteralPath $parent)){New-Item -ItemType Directory -Path $parent -Force|Out-Null}
$stage=Join-Path $parent ('.codex-mcp-memory-install-'+[guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage|Out-Null
# Staging stays recoverable on failure; never delete or overwrite another skill.
$files=@($items|Where-Object {-not $_.PSIsContainer -and $_.Extension -in @('.md','.yaml','.py','.ps1') -and $_.FullName -notmatch '[\\/]__pycache__[\\/]'})
$sourceHashes=@{}
foreach($file in $files){
 $relative=$file.FullName.Substring($source.Length).TrimStart('\','/')
 $copied=Join-Path $stage $relative
 $copyParent=Split-Path -Parent $copied
 if(-not (Test-Path -LiteralPath $copyParent)){New-Item -ItemType Directory -Path $copyParent -Force|Out-Null}
 $sourceHashes[$relative]=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
 Copy-Item -LiteralPath $file.FullName -Destination $copied
}
$manifest=@()
foreach($file in $files){
 $relative=$file.FullName.Substring($source.Length).TrimStart('\','/')
 $copied=Join-Path $stage $relative
 $hash=(Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash
 if($hash -ne $sourceHashes[$relative]){throw 'Source changed while installing; staging preserved'}
 if((Get-FileHash -LiteralPath $copied -Algorithm SHA256).Hash -ne $hash){throw 'Staged skill hash mismatch'}
 $manifest += [pscustomobject]@{path=$relative.Replace('\','/');sha256=$hash}
}
if(Test-Path -LiteralPath $target){throw 'Destination appeared during installation; staging preserved'}
# Directory.Move is non-overwriting on the same filesystem.
[IO.Directory]::Move($stage,$target)
[pscustomobject]@{version='0.1.0';destination=$target;files=$manifest;runtimeChanged=$false;note='Installed files only. Existing chats may not rediscover skills immediately.'}|ConvertTo-Json -Depth 5
