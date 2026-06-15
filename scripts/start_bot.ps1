param(
  [string]$Strategies = "ALL"
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root
trader start-bot --strategies $Strategies
