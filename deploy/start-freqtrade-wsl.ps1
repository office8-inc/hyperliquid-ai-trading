param(
  [string]$Distro = "Ubuntu-24.04",
  [string]$Service = "freqtrade-wsl.service"
)

$ErrorActionPreference = "Stop"

& wsl.exe -d $Distro -u root -- systemctl start $Service
if ($LASTEXITCODE -ne 0) {
  exit $LASTEXITCODE
}

& wsl.exe -d $Distro -- systemctl is-active --quiet $Service
exit $LASTEXITCODE
