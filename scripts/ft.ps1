param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$FreqtradeArgs
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RootDir = Resolve-Path (Join-Path $ScriptDir "..")
$FreqtradeDir = Join-Path $RootDir "freqtrade"

Push-Location $FreqtradeDir
try {
  & docker compose run --rm freqtrade @FreqtradeArgs
  exit $LASTEXITCODE
}
finally {
  Pop-Location
}
