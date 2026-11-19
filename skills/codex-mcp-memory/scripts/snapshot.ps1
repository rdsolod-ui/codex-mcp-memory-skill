param(
 [Parameter(Mandatory=$true)][ValidateRange(1,2147483647)][int]$RootPid,
 [Parameter(Mandatory=$true)][string]$OutputPath
)
$ErrorActionPreference='Stop'
# Read-only Windows inventory. Never persists command lines or environment values.
if(Test-Path -LiteralPath $OutputPath){throw 'Output already exists; choose a new evidence file'}
$all=@(Get-CimInstance Win32_Process)
$byId=@{};foreach($row in $all){$byId[[int]$row.ProcessId]=$row}
$root=$byId[$RootPid]
if(-not $root){throw 'Root PID not found'}
if($root.Name -notin @('ChatGPT.exe','Codex.exe','codex.exe')){throw 'Root must be an independently verified Codex Desktop/backend process'}
$selected=@{$RootPid=$true}
do{
 $added=$false
 foreach($row in $all){
  if($selected.ContainsKey([int]$row.ProcessId) -or -not $selected.ContainsKey([int]$row.ParentProcessId)){continue}
  $parent=$byId[[int]$row.ParentProcessId]
  if($parent.CreationDate -gt $row.CreationDate){continue} # Reused parent PID is not ancestry.
  $selected[[int]$row.ProcessId]=$true;$added=$true
 }
}while($added)
$rows=@();$skipped=0
foreach($row in $all){
 if(-not $selected.ContainsKey([int]$row.ProcessId)){continue}
 $p=Get-Process -Id $row.ProcessId -ErrorAction SilentlyContinue
 if(-not $p){$skipped++;continue}
 try{if([math]::Abs(($p.StartTime.ToUniversalTime()-$row.CreationDate.ToUniversalTime()).TotalMilliseconds) -gt 5){$skipped++;continue}}catch{$skipped++;continue}
 $cmd=[string]$row.CommandLine;$kind='other-descendant';$confidence='unclassified'
 if($row.ProcessId -eq $RootPid){$kind='codex-root';$confidence='explicit-root'}
 elseif($row.Name -eq 'ChatGPT.exe'){$kind='codex-ui';$confidence='executable-name'}
 elseif($row.Name -eq 'codex.exe'){$kind='codex-backend';$confidence='executable-name'}
 elseif($cmd -match 'node_repl|node-repl'){$kind='stateful-repl';$confidence='command-pattern'}
 elseif($cmd -match 'mcp-idle-proxy\.py|filesystem-idle-proxy\.py'){$kind='mcp-idle-proxy';$confidence='command-pattern'}
 elseif($cmd -match 'server-filesystem|server-memory|context7-mcp|sequential-thinking|playwright.*mcp|mcp.*playwright|@modelcontextprotocol|gitlab-mcp|mcp-server|kiosk\.py.*\bmcp\b'){$kind='mcp-candidate';$confidence='command-pattern'}
 $rows += [pscustomobject]@{pid=[int]$row.ProcessId;parent=[int]$row.ParentProcessId;createdUtc=$row.CreationDate.ToUniversalTime().ToString('o');name=$row.Name;kind=$kind;classification=$confidence;privateBytes=[long]$p.PrivateMemorySize64;workingSetBytes=[long]$p.WorkingSet64}
}
if(-not @($rows|Where-Object pid -eq $RootPid).Count){throw 'Root disappeared during sampling'}
$os=Get-CimInstance Win32_OperatingSystem
$report=[pscustomobject]@{schemaVersion=1;at=[datetime]::UtcNow.ToString('o');rootPid=$RootPid;rootCreatedUtc=$root.CreationDate.ToUniversalTime().ToString('o');samplingIsAtomic=$false;skippedProcesses=$skipped;systemTotalPhysicalBytes=[long]$os.TotalVisibleMemorySize*1024;systemFreePhysicalBytes=[long]$os.FreePhysicalMemory*1024;rows=$rows}
$full=[IO.Path]::GetFullPath($OutputPath);$dir=[IO.Path]::GetDirectoryName($full)
if(-not (Test-Path -LiteralPath $dir -PathType Container)){throw 'Evidence directory must already exist outside a public repository'}
$json=$report|ConvertTo-Json -Depth 5
$stream=[IO.File]::Open($full,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
try{$bytes=[Text.UTF8Encoding]::new($false).GetBytes($json);$stream.Write($bytes,0,$bytes.Length)}finally{$stream.Dispose()}
[pscustomobject]@{output=$full;processes=$rows.Count;privateMiB=[math]::Round(($rows|Measure-Object privateBytes -Sum).Sum/1MB,2);workingSetSumMiB=[math]::Round(($rows|Measure-Object workingSetBytes -Sum).Sum/1MB,2);systemFreePhysicalMiB=[math]::Round($report.systemFreePhysicalBytes/1MB,2);groups=@($rows|Group-Object kind|ForEach-Object {[pscustomobject]@{kind=$_.Name;count=$_.Count;privateMiB=[math]::Round(($_.Group|Measure-Object privateBytes -Sum).Sum/1MB,2);workingSetSumMiB=[math]::Round(($_.Group|Measure-Object workingSetBytes -Sum).Sum/1MB,2)}})}|ConvertTo-Json -Depth 5
