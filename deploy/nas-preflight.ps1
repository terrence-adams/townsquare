[CmdletBinding()]
param([Parameter(Mandatory)][string]$EvidencePath)
# Read-only probe: it does not SSH, write a NAS, inspect secrets, or run Docker.
$result=[ordered]@{
  schema=1; generated_utc=(Get-Date).ToUniversalTime().ToString('o')
  status='LOCAL_TEMPLATE_ONLY';
  required_checks=@('NAS-local SQLite data path','loopback-only published ports','no host network or Docker socket','Docker DNS validation','firewall allowlist/no DNAT/UPnP evidence','TLS/mTLS evidence required before any LAN bind')
  observations=@(); blockers=@('No NAS was accessed by this script. Execute approved read-only checks on the NAS and attach raw outputs.')
}
$dir=Split-Path -Parent $EvidencePath
if($dir){New-Item -ItemType Directory -Force -Path $dir | Out-Null}
$result | ConvertTo-Json -Depth 5 | Set-Content -NoNewline -Encoding utf8 $EvidencePath
Write-Output "Wrote template evidence only: $EvidencePath"
