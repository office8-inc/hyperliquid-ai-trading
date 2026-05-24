param(
  [Parameter(Mandatory = $true, Position = 0)]
  [string]$Command,

  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$FreqtradeArgs
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..")
$FreqtradeDir = Join-Path $RootDir "freqtrade"

Push-Location $FreqtradeDir
try {
  & docker compose run --rm freqtrade $Command `
    --config /freqtrade/user_data/config.json `
    --config /freqtrade/user_data/config-private.json `
    @FreqtradeArgs
  exit $LASTEXITCODE
}
finally {
  Pop-Location
}
