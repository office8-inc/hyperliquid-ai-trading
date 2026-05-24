param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Command,

  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$FreqtradeArgs
)

$ErrorActionPreference = "Stop"
$env:FREQTRADE_IMAGE = if ($env:FREQTRADE_IMAGE) { $env:FREQTRADE_IMAGE } else { "freqtradeorg/freqtrade:2026.4_freqai" }

& (Join-Path $PSScriptRoot "ftc.ps1") $Command @FreqtradeArgs
exit $LASTEXITCODE
